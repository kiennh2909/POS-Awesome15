from __future__ import unicode_literals

import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("invoice")


def _parse_json_safe(json_str, default=None):
    """
    Safely parse JSON string with fallback to default value

    Args:
        json_str (str): JSON string to parse
        default: Default value to return if parsing fails

    Returns:
        Parsed JSON object or default value
    """
    try:
        if json_str and isinstance(json_str, str):
            return json.loads(json_str)
        return default or {}
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        log.warning(f"[PAYMENT_SUMMARY] Failed to parse JSON: {str(e)}, returning default")
        return default or {}


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
				data["returns_amount"] -= abs(amt)
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

		# Lấy thông tin company và pos_profile từ POS Opening Shift
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		company = opening_shift.company
		pos_profile = opening_shift.pos_profile

		# Xác định payment_method_type dựa trên payment method
		payment_method_type = _get_payment_method_type(method)

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
					"payment_method_type": payment_method_type,
					"currency": getattr(shift_report, "currency", "USD"),
					"company": company,
					"pos_profile": pos_profile,
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


@frappe.whitelist()
def get_payment_summaries_for_shift(shift_report_name):
	"""
	Lấy danh sách POS Payment Summary cho một shift report.

	Args:
		shift_report_name (str): Tên của POS Shift Report

	Returns:
		dict: Danh sách payment summaries
	"""
	try:
		log.info(f"[GET_PAYMENT_SUMMARIES] 📊 Getting payment summaries for shift: {shift_report_name}")

		# Kiểm tra shift report tồn tại
		if not frappe.db.exists("POS Shift Report", shift_report_name):
			log.error(f"[GET_PAYMENT_SUMMARIES] ❌ Shift report not found: {shift_report_name}")
			return {
				"success": False,
				"message": "Shift report not found"
			}

		# Lấy tất cả payment summaries cho shift report này
		payment_summaries = frappe.get_all("POS Payment Summary",
			filters={"pos_shift_report": shift_report_name},
			fields=[
				"payment_method", "opening_amount", "transaction_amount",
				"expected_closing_amount", "closing_amount", "difference",
				"transaction_count", "sales_amount", "returns_amount",
				"currency", "company", "pos_profile"
			],
			order_by="payment_method"
		)

		log.info(f"[GET_PAYMENT_SUMMARIES] ✅ Found {len(payment_summaries)} payment summaries for shift: {shift_report_name}")

		# Log chi tiết từng payment method
		for summary in payment_summaries:
			log.debug(f"[GET_PAYMENT_SUMMARIES] {summary.payment_method}: Opening={summary.opening_amount}, Transactions={summary.transaction_amount}, Expected={summary.expected_closing_amount}, Actual={summary.closing_amount}, Diff={summary.difference}")

		return {
			"success": True,
			"message": f"Found {len(payment_summaries)} payment summaries",
			"data": payment_summaries
		}

	except Exception as e:
		log.error(f"[GET_PAYMENT_SUMMARIES] 💥 Error getting payment summaries for shift {shift_report_name}: {str(e)}")
		return {
			"success": False,
			"message": str(e)
		}


def get_valid_payment_methods_for_shift(shift_report):
	"""Đọc danh sách Mode of Payment từ POS Opening Shift (balance_details)."""
	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		methods = [d.mode_of_payment for d in (opening_shift.balance_details or [])]
		return methods
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error reading valid MOPs: {str(e)}")
		return []


def _get_payment_method_type(payment_method):
	"""Xác định loại phương thức thanh toán dựa trên tên."""
	try:
		# Chuyển về uppercase để so sánh
		method = payment_method.upper()

		# Mapping các loại payment method
		if method in ["CASH", "TIỀN MẶT"]:
			return "Cash"
		elif method in ["CARD", "CREDIT CARD", "DEBIT CARD", "THẺ TÍN DỤNG", "THẺ GHI NỢ"]:
			return "Card"
		elif "M-PESA" in method or "MPESA" in method or "MOBILE" in method or "DI ĐỘNG" in method:
			return "Mobile Payment"
		elif "BANK" in method or "NGÂN HÀNG" in method:
			return "Bank"
		else:
			return "Other"
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error determining payment method type for '{payment_method}': {str(e)}")
		return "Other"


@frappe.whitelist()
def initialize_payment_summaries_for_shift(shift_report_name):
	"""
	Khởi tạo POS Payment Summary records cho một shift report mới.
	Được gọi tự động khi tạo Shift Report.

	Args:
		shift_report_name (str): Tên của POS Shift Report

	Returns:
		dict: Kết quả khởi tạo
	"""
	try:
		log.info(f"[INIT_PAYMENT_SUMMARIES] 🚀 START - Shift Report: {shift_report_name}")

		# Kiểm tra shift report tồn tại
		if not frappe.db.exists("POS Shift Report", shift_report_name):
			log.error(f"[INIT_PAYMENT_SUMMARIES] ❌ Shift report not found: {shift_report_name}")
			return {
				"success": False,
				"message": "Shift report not found"
			}

		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		log.info(f"[INIT_PAYMENT_SUMMARIES] 📋 Shift Report details - ID: {shift_report.shift_report_id}, Opening Shift: {shift_report.pos_opening_shift}")

		# Lấy danh sách payment methods từ POS Opening Shift
		valid_methods = get_valid_payment_methods_for_shift(shift_report)
		if not valid_methods:
			log.warning(f"[INIT_PAYMENT_SUMMARIES] ⚠️ No valid payment methods found for shift report: {shift_report_name}")
			return {
				"success": True,
				"message": "No payment methods to initialize",
				"data": {"initialized_count": 0}
			}

		log.info(f"[INIT_PAYMENT_SUMMARIES] 💳 Found {len(valid_methods)} payment methods: {valid_methods}")

		# Lấy opening amounts từ POS Opening Shift
		opening_amounts = {}
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
			for detail in opening_shift.balance_details or []:
				opening_amounts[detail.mode_of_payment] = flt(detail.amount or 0, 2)
		except Exception as e:
			log.warning(f"[INIT_PAYMENT_SUMMARIES] ⚠️ Could not load opening amounts: {str(e)}")

		# Khởi tạo payment summaries với opening amounts
		initialized_count = 0
		for method in valid_methods:
			try:
				opening_amount = flt(opening_amounts.get(method, 0), 2)
				expected_closing_amount = opening_amount  # Ban đầu chỉ có opening amount

				# Lấy thông tin company và pos_profile từ POS Opening Shift
				company = opening_shift.company
				pos_profile = opening_shift.pos_profile
				payment_method_type = _get_payment_method_type(method)

				# Kiểm tra xem đã tồn tại chưa
				existing = frappe.db.exists(
					"POS Payment Summary",
					{
						"shift_report_id": shift_report.shift_report_id,
						"payment_method": method,
						"pos_shift_report": shift_report.name,
					},
				)

				if existing:
					log.debug(f"[INIT_PAYMENT_SUMMARIES] ⏭️ Payment summary already exists for {method}, skipping")
					continue

				# Tạo POS Payment Summary record
				doc = frappe.get_doc({
					"doctype": "POS Payment Summary",
					"shift_report_id": shift_report.shift_report_id,
					"pos_shift_report": shift_report.name,
					"pos_opening_shift": shift_report.pos_opening_shift,
					"posting_date": getattr(shift_report, "opening_date", None),
					"payment_method": method,
					"payment_method_type": payment_method_type,
					"currency": getattr(shift_report, "currency", "USD"),
					"company": company,
					"pos_profile": pos_profile,
					"opening_amount": opening_amount,
					"transaction_amount": 0.0,  # Sẽ được cập nhật khi có giao dịch
					"expected_closing_amount": expected_closing_amount,
					"closing_amount": 0.0,  # Sẽ được cập nhật khi đóng ca
					"transaction_count": 0,
					"sales_amount": 0.0,
					"returns_amount": 0.0,
					"notes": f"Auto-initialized for shift report {shift_report.name}",
				})

				doc.insert(ignore_permissions=True)
				initialized_count += 1
				log.debug(f"[INIT_PAYMENT_SUMMARIES] ✅ Created payment summary for {method}: opening={opening_amount}")

			except Exception as method_error:
				log.error(f"[INIT_PAYMENT_SUMMARIES] ❌ Failed to create payment summary for {method}: {str(method_error)}")
				continue

		log.info(f"[INIT_PAYMENT_SUMMARIES] 🎉 COMPLETED - Initialized {initialized_count} payment summaries for shift report {shift_report_name}")
		return {
			"success": True,
			"message": f"Successfully initialized {initialized_count} payment summaries",
			"data": {"initialized_count": initialized_count}
		}

	except Exception as e:
		log.error(f"[INIT_PAYMENT_SUMMARIES] 💥 FAILED - Shift Report: {shift_report_name}, Error: {str(e)}")
		return {
			"success": False,
			"message": str(e)
		}
