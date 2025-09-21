from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("invoice")


# --------------------------------------------------------------------
# DocType: POS Payment Summary
# --------------------------------------------------------------------
class POSPaymentSummary(Document):
	def validate(self):
		"""Validate POS Payment Summary."""
		self.validate_amounts()
		self.calculate_difference()

	def validate_amounts(self):
		"""Đảm bảo expected_closing_amount = opening_amount + transaction_amount."""
		expected_closing = flt(self.opening_amount, 2) + flt(self.transaction_amount, 2)
		if abs(flt(self.expected_closing_amount, 2) - expected_closing) > 0.01:
			log.warning(
				f"[PAYMENT_SUMMARY] Expected closing mismatch for {self.payment_method} in shift {self.shift_report_id}: "
				f"{self.expected_closing_amount} -> {expected_closing}"
			)
			self.expected_closing_amount = expected_closing

	def calculate_difference(self):
		"""difference = closing_amount - expected_closing_amount."""
		if self.expected_closing_amount:
			self.difference = flt(self.closing_amount, 2) - flt(self.expected_closing_amount, 2)
		else:
			self.difference = 0.0

		log.info(f"[PAYMENT_SUMMARY] Calculated difference for {self.payment_method}: {self.difference}")


# --------------------------------------------------------------------
# Core API
# --------------------------------------------------------------------

@frappe.whitelist()
def update_payment_summary_on_invoice_submit(invoice_name):
	"""
	Cập nhật POS Payment Summary khi submit hoặc cancel invoice.
	Được gọi từ Sales Invoice hooks.
	"""
	try:
		invoice = frappe.get_doc("Sales Invoice", invoice_name)

		if not getattr(invoice, "posa_pos_opening_shift", None):
			return {"success": True, "message": "Not a POS invoice"}

		shift_reports = frappe.get_all("POS Shift Report",
			filters={"pos_opening_shift": invoice.posa_pos_opening_shift},
			fields=["name"]
		)

		if not shift_reports:
			return {"success": True, "message": "No shift report found"}

		shift_report_name = shift_reports[0].name

		# Cập nhật payment summaries và totals (totals được gọi tự động trong create_payment_summaries_for_shift)
		payment_result = create_payment_summaries_for_shift(shift_report_name)
		if not payment_result.get("success"):
			return payment_result

		log.info(f"[PAYMENT_SUMMARY] Successfully updated payment summary and totals for invoice {invoice_name}")
		return payment_result

	except Exception as e:
		log.error(f"Error updating payment summary on invoice submit: {str(e)}")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_payment_summaries_for_shift(shift_report_name):
	"""
	Tạo/cập nhật POS Payment Summary cho một ca làm việc.
	"""
	try:
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)

		if getattr(shift_report, 'verification_status', 'Pending') in ['Verified', 'Confirmed']:
			return {"success": True, "message": "Shift already verified"}

		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"posa_pos_opening_shift": shift_report.pos_opening_shift, "docstatus": 1},
			fields=["name", "grand_total", "is_return"]
		)

		valid_methods = get_valid_payment_methods_for_shift(shift_report)
		payment_data = _calculate_payment_methods(invoices, valid_methods)

		opening_amounts = {}
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
			for detail in opening_shift.balance_details or []:
				opening_amounts[detail.mode_of_payment] = flt(detail.amount or 0, 2)
		except:
			pass

		for method in valid_methods:
			if method not in payment_data:
				payment_data[method] = {
					"transaction_count": 0,
					"transaction_amount": 0.0,
					"sales_amount": 0.0,
					"returns_amount": 0.0
				}

		payment_summaries = []
		for method, data in payment_data.items():
			result = _create_or_update_payment_summary(shift_report, method, data, opening_amounts)
			if result:
				payment_summaries.append(result)

		frappe.db.commit()

		# Cập nhật shift report totals ngay khi payment summaries thành công
		update_shift_report_totals(shift_report_name)

		return {
			"success": True,
			"message": f"Updated {len(payment_summaries)} payment methods and shift totals",
			"data": {
				"payment_summaries": payment_summaries,
				"invoice_count": len(invoices)
			}
		}

	except Exception as e:
		log.error(f"Error creating payment summaries: {str(e)}")
		return {"success": False, "message": str(e)}


def update_shift_report_totals(shift_report_name):
	"""
	Cập nhật tổng số liệu trong POS Shift Report từ payment summaries.
	"""
	try:
		summaries = frappe.get_all("POS Payment Summary",
			filters={"pos_shift_report": shift_report_name},
			fields=["sales_amount", "returns_amount", "transaction_amount"]
		)

		total_sales = sum(flt(s.sales_amount or 0) for s in summaries)
		total_returns = sum(flt(s.returns_amount or 0) for s in summaries)

		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		shift_report.total_sales = total_sales
		shift_report.total_returns = total_returns
		shift_report.save(ignore_permissions=True)

		log.info(f"Updated shift report totals: Sales={total_sales}, Returns={total_returns}")

	except Exception as e:
		log.error(f"Error updating shift report totals: {str(e)}")


def _calculate_payment_methods(invoices, valid_payment_methods=None):
	"""Tổng hợp tiền theo MOP với split-tender."""
	from collections import defaultdict

	log.info(f"[PAYMENT_CALC] Starting calculation for {len(invoices)} invoices, valid_methods: {valid_payment_methods}")

	# Khởi tạo dict với default structure cho mỗi MOP
	payment_methods = defaultdict(lambda: {
		"transaction_count": 0,
		"transaction_amount": 0.0,
		"sales_amount": 0.0,
		"returns_amount": 0.0
	})

	# Khởi tạo các MOP hợp lệ nếu được chỉ định
	if valid_payment_methods:
		for method in valid_payment_methods:
			payment_methods[method]  # Trigger defaultdict
		log.info(f"[PAYMENT_CALC] Initialized {len(valid_payment_methods)} valid payment methods")

	if not invoices:
		log.info("[PAYMENT_CALC] No invoices to process, returning empty result")
		return dict(payment_methods)

	# Batch fetch tất cả payments
	inv_names = [inv.name for inv in invoices]
	log.debug(f"[PAYMENT_CALC] Processing invoices: {inv_names[:3]}{'...' if len(inv_names) > 3 else ''}")

	payments = frappe.get_all(
		"Sales Invoice Payment",
		filters={"parent": ["in", inv_names]},
		fields=["parent", "mode_of_payment", "amount"]
	)
	log.info(f"[PAYMENT_CALC] Found {len(payments)} payment records for {len(invoices)} invoices")

	# Group payments theo invoice
	pay_by_inv = defaultdict(list)
	for payment in payments:
		pay_by_inv[payment.parent].append(payment)

	fallback_count = 0
	processed_count = 0

	# Process từng invoice
	for inv in invoices:
		rows = pay_by_inv.get(inv.name, [])

		# Fallback nếu invoice không có payment detail
		if not rows:
			rows = [{"mode_of_payment": "CASH", "amount": inv.grand_total or 0}]
			fallback_count += 1
			log.debug(f"[PAYMENT_CALC] Using fallback for invoice {inv.name}: {inv.grand_total}")

		for row in rows:
			method = row.get("mode_of_payment") or "CASH"

			# Skip nếu method không hợp lệ
			if valid_payment_methods and method not in valid_payment_methods:
				log.debug(f"[PAYMENT_CALC] Skipping invalid method '{method}' for invoice {inv.name}")
				continue

			amt = flt(row.get("amount") or 0, 2)
			data = payment_methods[method]

			data["transaction_count"] += 1

			if inv.is_return:
				data["returns_amount"] += abs(amt)
				data["transaction_amount"] -= abs(amt)
				log.debug(f"[PAYMENT_CALC] Return: {method} -{abs(amt)} for invoice {inv.name}")
			else:
				data["sales_amount"] += amt
				data["transaction_amount"] += amt
				log.debug(f"[PAYMENT_CALC] Sale: {method} +{amt} for invoice {inv.name}")

		processed_count += 1

	log.info(f"[PAYMENT_CALC] Processed {processed_count} invoices, used fallback for {fallback_count}")

	# Log kết quả tổng hợp
	result = dict(payment_methods)
	for method, data in result.items():
		log.info(f"[PAYMENT_CALC] {method}: {data['transaction_count']} tx, Amount: {data['transaction_amount']}, Sales: {data['sales_amount']}, Returns: {data['returns_amount']}")

	log.info(f"[PAYMENT_CALC] Completed calculation for {len(result)} payment methods")
	return result


def _create_or_update_payment_summary(shift_report, method, data, opening_amounts):
	"""Upsert 1 dòng POS Payment Summary cho 1 phương thức thanh toán."""
	try:
		opening_amount = flt(opening_amounts.get(method, 0), 2)
		transaction_amount = flt(data["transaction_amount"], 2)
		expected_closing_amount = flt(opening_amount + transaction_amount, 2)

		existing = frappe.db.exists(
			"POS Payment Summary",
			{
				"shift_report_id": shift_report.shift_report_id,
				"payment_method": method,
				"pos_shift_report": shift_report.name,
			},
		)

		if existing:
			doc = frappe.get_doc("POS Payment Summary", existing)
			doc.transaction_count = data["transaction_count"]
			doc.transaction_amount = transaction_amount
			doc.expected_closing_amount = expected_closing_amount
			doc.sales_amount = data["sales_amount"]
			doc.returns_amount = data["returns_amount"]
			doc.difference = flt(doc.closing_amount - expected_closing_amount, 2)
			doc.save()
		else:
			doc = frappe.get_doc(
				{
					"doctype": "POS Payment Summary",
					"shift_report_id": shift_report.shift_report_id,
					"pos_shift_report": shift_report.name,
					"pos_opening_shift": shift_report.pos_opening_shift,
					"posting_date": getattr(shift_report, "opening_date", None),
					"payment_method": method,
					"currency": getattr(shift_report, "currency", "USD"),
					"company": getattr(shift_report, "company", ""),
					"pos_profile": getattr(shift_report, "pos_profile", ""),
					"opening_amount": opening_amount,
					"transaction_amount": transaction_amount,
					"expected_closing_amount": expected_closing_amount,
					"closing_amount": 0.0,
					"transaction_count": data["transaction_count"],
					"sales_amount": data["sales_amount"],
					"returns_amount": data["returns_amount"],
					"notes": f"Auto-generated from shift report {shift_report.name}",
				}
			)
			doc.insert(ignore_permissions=True)

		return {
			"payment_method": method,
			"opening_amount": opening_amount,
			"transaction_amount": transaction_amount,
			"expected_closing_amount": expected_closing_amount,
			"closing_amount": doc.closing_amount,
			"difference": flt(doc.closing_amount - expected_closing_amount, 2),
			"transaction_count": data["transaction_count"],
			"sales_amount": data["sales_amount"],
			"returns_amount": data["returns_amount"],
		}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error processing '{method}': {str(e)}")
		return None


def get_valid_payment_methods_for_shift(shift_report):
	"""Đọc danh sách Mode of Payment từ POS Opening Shift (balance_details)."""
	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		methods = [d.mode_of_payment for d in (opening_shift.balance_details or [])]
		return methods
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error reading valid MOPs: {str(e)}")
		return []
