from __future__ import unicode_literals
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, cstr, flt
from frappe.installer import migrate_app

from posawesome.posawesome.utils.logging import get_logger

# --------------------------------------------------------------------
# Logger (will be initialized per POS Profile)
# --------------------------------------------------------------------

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _compose_datetime(date_val, time_val=None):
	"""Ghép Date + Time thành Datetime (local). Nếu thiếu time => 00:00:00."""
	if date_val and time_val:
		return get_datetime(f"{date_val} {time_val}")
	if date_val:
		return get_datetime(f"{date_val} 00:00:00")
	return None


def _norm_mop(name: str) -> str:
	"""Chuẩn hoá tên Mode of Payment để so sánh an toàn (strip, collapse space, casefold)."""
	s = cstr(name or "").strip()
	s = re.sub(r"\s+", " ", s)
	return s.casefold()


# --------------------------------------------------------------------
# DocType: POS Payment Summary
# --------------------------------------------------------------------
class POSPaymentSummary(Document):
	def validate(self):
		"""Validate POS Payment Summary."""
		self.validate_amounts()
		self.calculate_difference()

	def validate_amounts(self):
		"""Đảm bảo closing_amount = opening_amount + transaction_amount (chấp nhận lệch 0.01)."""
		expected_closing = flt(self.opening_amount, 2) + flt(self.transaction_amount, 2)
		if abs(flt(self.closing_amount, 2) - expected_closing) > 0.01:
			# Get POS Profile for logging
			pos_profile = getattr(self, "pos_profile", None)
			log = get_logger(pos_profile or "POSProfile")

			log.warning(
				f"[PAYMENT_SUMMARY] Closing mismatch for {self.payment_method} in shift {self.shift_report_id}: "
				f"{self.closing_amount} -> {expected_closing}"
			)
			self.closing_amount = expected_closing

	def calculate_difference(self):
		"""difference = closing_amount - expected_closing_amount."""
		if self.expected_closing_amount:
			self.difference = flt(self.closing_amount, 2) - flt(self.expected_closing_amount, 2)
		else:
			self.difference = 0.0

		# Get POS Profile for logging
		pos_profile = getattr(self, "pos_profile", None)
		log = get_logger(pos_profile or "POSProfile")

		log.info(f"[PAYMENT_SUMMARY] Calculated difference for {self.payment_method}: {self.difference}")


# --------------------------------------------------------------------
# Core API
# --------------------------------------------------------------------
@frappe.whitelist()
def create_payment_summaries_for_shift(shift_report_name):
	"""
	Tổng hợp POS Payment Summary cho một ca (Shift Report).
	- Lấy invoices theo POS Opening Shift
	- Tổng hợp theo MOP (support split-tender)
	- Khởi tạo đầy đủ MOP từ Opening Shift (nếu thiếu)
	- Upsert từng dòng summary
	- Validate tính nhất quán (tự bù thiếu, throw nếu thừa)
	"""
	try:
		# STEP 1. Shift Report
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		company, pos_profile, currency = _get_company_profile_currency(shift_report)

		# Initialize logger with POS Profile name
		log = get_logger(pos_profile or "POSProfile")

		log.info(f"[PAYMENT_SUMMARY] 🚀 START create summaries: {shift_report_name}")
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 1: Shift report: {shift_report.name} (ID: {shift_report.shift_report_id})")

		# STEP 2. Invoices (đã Submit)
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"posa_pos_opening_shift": shift_report.pos_opening_shift, "docstatus": 1},
			fields=["name", "grand_total", "is_return"]
		)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 2: Found {len(invoices)} invoices")

		# STEP 3. Valid MOP từ Opening Shift (source of truth)
		valid_payment_methods = get_valid_payment_methods_for_shift(shift_report)

		# STEP 4. Group & calc theo MOP (support split-tender)
		payment_data = _calculate_payment_methods(invoices, None, valid_payment_methods)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 4: Grouped {len(payment_data)} method(s) from invoices")

		# STEP 5. Load opening amounts & expected closing
		opening_amounts = {}
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
			if getattr(opening_shift, "balance_details", None):
				for detail in opening_shift.balance_details:
					opening_amounts[detail.mode_of_payment] = flt(detail.amount or 0, 2)
			log.info(f"[PAYMENT_SUMMARY] ✅ STEP 5: Opening amounts loaded: {len(opening_amounts)} method(s)")
		except Exception as e:
			log.error(f"[PAYMENT_SUMMARY] ❌ STEP 5: Cannot load opening amounts: {str(e)}")

		expected_closing = _parse_json_safe(getattr(shift_report, "expected_closing_amounts", None), {}) or {}
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 5: Expected closing: {len(expected_closing)} method(s)")

		# STEP 6. Bảo đảm đủ MOP từ Opening Shift (kể cả không có giao dịch)
		for mop in (valid_payment_methods or []):
			if mop not in payment_data:
				payment_data[mop] = {
					"transaction_count": 0,
					"transaction_amount": 0.0,
					"sales_amount": 0.0,
					"returns_amount": 0.0
				}

		# STEP 7. Upsert từng MOP
		payment_summaries = []
		created_count, updated_count, error_count = 0, 0, 0

		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 7: Upserting {len(payment_data)} method(s)")
		for method, data in sorted(payment_data.items(), key=lambda kv: kv[0]):
			try:
				result = _create_or_update_payment_summary(
					shift_report=shift_report,
					method=method,
					data=data,
					opening_amounts=opening_amounts,
					expected_closing=expected_closing
				)
				if not result:
					log.warning(f"[PAYMENT_SUMMARY] ⚠️ STEP 7: No result for '{method}'")
					error_count += 1
					continue

				if result.get("created"):
					created_count += 1
				else:
					updated_count += 1

				payment_summaries.append(result["summary"])
			except Exception as e:
				error_count += 1
				log.error(f"[PAYMENT_SUMMARY] ❌ STEP 7: Error upserting '{method}': {str(e)}")

		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 7: Done. Created={created_count}, Updated={updated_count}, Error={error_count}")

		# STEP 8. Validate consistency (auto-bù thiếu, throw nếu thừa)
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 8: Validating consistency")
		validate_payment_summary_consistency(shift_report)

		# STEP 9. Commit (giữ lại vì nhiều nơi gọi qua client). Tuỳ dự án có thể bỏ.
		frappe.db.commit()
		log.info(f"[PAYMENT_SUMMARY] 💾 STEP 9: Committed")

		# STEP 10. Return
		log.info(f"[PAYMENT_SUMMARY] 🎉 COMPLETED for shift {shift_report_name}")
		return {
			"success": True,
			"message": f"Processed {len(payment_summaries)} payment method(s) with validation",
			"data": {
				"payment_summaries": payment_summaries,
				"created_count": created_count,
				"updated_count": updated_count,
				"failed_count": error_count,
				"total_methods": len(payment_summaries),
				"validation_passed": True
			}
		}

	except Exception as e:
		# Fallback logger if initialization failed
		fallback_log = get_logger("pos_payment_summary")
		fallback_log.error(f"[PAYMENT_SUMMARY] Error: {str(e)}")
		return {"success": False, "message": f"Error creating payment summaries: {str(e)}"}


def _calculate_payment_methods(invoices, _invoice_payments_unused=None, valid_payment_methods=None):
	"""
	Tổng hợp tiền theo MOP với split-tender:
	- Batch fetch tất cả Sales Invoice Payment cho list invoices (tránh N+1).
	- Nếu invoice không có dòng payment: fallback 'Tiền mặt - POS' = grand_total.
	"""
	payment_methods = {}

	# Init trước các MOP hợp lệ để luôn có key
	if valid_payment_methods:
		for m in valid_payment_methods:
			payment_methods[m] = {
				"transaction_count": 0,
				"transaction_amount": 0.0,
				"sales_amount": 0.0,
				"returns_amount": 0.0
			}

	if not invoices:
		return payment_methods

	inv_names = [inv.name for inv in invoices]
	p_rows = frappe.get_all(
		"Sales Invoice Payment",
		filters={"parent": ["in", inv_names]},
		fields=["parent", "mode_of_payment", "amount"]
	)

	# index payments theo invoice
	pay_by_inv = {}
	for r in p_rows:
		pay_by_inv.setdefault(r.parent, []).append(r)

	for inv in invoices:
		rows = pay_by_inv.get(inv.name, [])
		if not rows:
			rows = [{"mode_of_payment": "Tiền mặt - POS", "amount": inv.grand_total or 0}]

		for r in rows:
			method = (r.get("mode_of_payment") or "Tiền mặt - POS")
			if valid_payment_methods and method not in valid_payment_methods:
				log.warning(f"[PAYMENT_SUMMARY] Skip invalid MOP '{method}' for invoice {inv.name}")
				continue

			amt = flt(r.get("amount") or 0, 2)

			if method not in payment_methods:
				payment_methods[method] = {
					"transaction_count": 0,
					"transaction_amount": 0.0,
					"sales_amount": 0.0,
					"returns_amount": 0.0
				}

			# đếm theo dòng payment (hợp lý cho split-tender)
			payment_methods[method]["transaction_count"] += 1

			if inv.is_return:
				payment_methods[method]["returns_amount"] += abs(amt)
				payment_methods[method]["transaction_amount"] -= abs(amt)
			else:
				payment_methods[method]["sales_amount"] += amt
				payment_methods[method]["transaction_amount"] += amt

	return payment_methods


def _parse_json_safe(json_string, default=None):
	"""Parse JSON an toàn."""
	if not json_string:
		return default or {}
	try:
		return frappe.parse_json(json_string)
	except Exception:
		log.warning(f"[PAYMENT_SUMMARY] Could not parse JSON: {cstr(json_string)[:80]}...")
		return default or {}


def _get_company_profile_currency(shift_report):
	"""
	Lấy (company, pos_profile, currency) theo thứ tự ưu tiên:
	- company, pos_profile từ Opening Shift nếu có
	- currency từ POS Profile -> Company.default_currency -> 'USD'
	"""
	company = None
	pos_profile = None
	currency = None

	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		company = getattr(opening_shift, "company", None)
		pos_profile = getattr(opening_shift, "pos_profile", None)
	except Exception as e:
		log.warning(f"[PAYMENT_SUMMARY] Cannot get company/pos_profile from opening shift: {str(e)}")

	if pos_profile:
		try:
			currency = frappe.db.get_value("POS Profile", pos_profile, "currency")
		except Exception:
			pass

	if not currency and company:
		try:
			currency = frappe.get_cached_value("Company", company, "default_currency")
		except Exception:
			pass

	return company or "NVL-DaiLoan", pos_profile or "", currency or "USD"


def _create_or_update_payment_summary(shift_report, method, data, opening_amounts, expected_closing):
	"""Upsert 1 dòng POS Payment Summary cho 1 phương thức thanh toán."""
	try:
		company, pos_profile, currency = _get_company_profile_currency(shift_report)
		shift_report_id = shift_report.shift_report_id

		existing = frappe.db.exists(
			"POS Payment Summary",
			{
				"shift_report_id": shift_report_id,
				"payment_method": method,
				"pos_shift_report": shift_report.name,
			},
		)

		opening_amount = flt(opening_amounts.get(method, 0), 2)
		transaction_amount = flt(data["transaction_amount"], 2)
		closing_amount = flt(opening_amount + transaction_amount, 2)

		shift_start_time = _compose_datetime(
			getattr(shift_report, "opening_date", None),
			getattr(shift_report, "opening_time", None),
		)
		shift_end_time = _compose_datetime(
			getattr(shift_report, "closing_date", None),
			getattr(shift_report, "closing_time", None),
		)

		if existing:
			# Update
			doc = frappe.get_doc("POS Payment Summary", existing)
			doc.transaction_count = data["transaction_count"]
			doc.transaction_amount = transaction_amount
			doc.closing_amount = closing_amount
			doc.expected_closing_amount = expected_closing.get(method, 0)
			doc.difference = flt(closing_amount - doc.expected_closing_amount, 2)
			doc.save()
			created = False
			log.info(f"[PAYMENT_SUMMARY] ♻️ Updated '{method}' -> {doc.name}")
		else:
			# Create with autoname
			doc = frappe.get_doc(
				{
					"doctype": "POS Payment Summary",
					"shift_report_id": shift_report_id,
					"pos_shift_report": shift_report.name,
					"pos_opening_shift": shift_report.pos_opening_shift,
					"posting_date": getattr(shift_report, "opening_date", None),
					"shift_start_time": shift_start_time,
					"shift_end_time": shift_end_time,
					"payment_method": method,
					"payment_method_type": get_payment_method_type(method),
					"currency": currency,
					"transaction_count": data["transaction_count"],
					"company": company,
					"pos_profile": pos_profile,
					"opening_amount": opening_amount,
					"transaction_amount": transaction_amount,
					"expected_closing_amount": expected_closing.get(method, 0),
					"closing_amount": closing_amount,
					"notes": f"Auto-generated from shift report {shift_report.name}",
				}
			)

			# Debug autoname
			expected_name = f"{shift_report_id}-{method.replace(' ', '_').replace('-', '_')}"
			log.info(f"[PAYMENT_SUMMARY] 📝 Creating '{method}' with expected name: {expected_name}")

			doc.insert()
			created = True
			log.info(f"[PAYMENT_SUMMARY] ✅ Created '{method}' -> {doc.name}")

		summary = {
			"payment_method": method,
			"opening_amount": opening_amount,
			"transaction_amount": transaction_amount,
			"closing_amount": closing_amount,
			"transaction_count": data["transaction_count"],
			"sales_amount": data["sales_amount"],
			"returns_amount": data["returns_amount"],
		}
		return {"created": created, "summary": summary}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error processing '{method}': {str(e)}")
		return None


@frappe.whitelist()
def get_payment_summaries_for_shift(shift_report_name):
	"""Trả về danh sách POS Payment Summary cho 1 Shift Report."""
	try:
		# Get POS Profile from shift report for logging
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		company, pos_profile, currency = _get_company_profile_currency(shift_report)
		log = get_logger(pos_profile or "POSProfile")

		log.info(f"[PAYMENT_SUMMARY] Fetch summaries for: {shift_report_name}")
		rows = frappe.get_all(
			"POS Payment Summary",
			filters={"pos_shift_report": shift_report_name},
			fields=[
				"name",
				"payment_method",
				"payment_method_type",
				"opening_amount",
				"transaction_amount",
				"closing_amount",
				"expected_closing_amount",
				"difference",
				"transaction_count",
				"currency",
				"posting_date",
				"pos_profile",
			],
			order_by="payment_method",
		)
		return {"success": True, "data": rows}
	except Exception as e:
		# Fallback logger
		fallback_log = get_logger("pos_payment_summary")
		fallback_log.error(f"[PAYMENT_SUMMARY] Error getting summaries: {str(e)}")
		return {"success": False, "message": f"Error: {str(e)}"}


def get_valid_payment_methods_for_shift(shift_report):
	"""Đọc danh sách Mode of Payment từ POS Opening Shift (balance_details)."""
	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		methods = [d.mode_of_payment for d in (opening_shift.balance_details or [])]

		# Get POS Profile for logging
		pos_profile = getattr(opening_shift, "pos_profile", None)
		log = get_logger(pos_profile or "POSProfile")

		log.info(f"[PAYMENT_SUMMARY] Valid MOP (Opening Shift): {methods}")
		return methods
	except Exception as e:
		# Fallback logger
		fallback_log = get_logger("pos_payment_summary")
		fallback_log.error(f"[PAYMENT_SUMMARY] Error reading valid MOPs: {str(e)}")
		return []


def validate_payment_summary_consistency(shift_report):
	"""
	Đảm bảo Summary khớp Opening Shift:
	- Thiếu MOP trong Summary => auto-add record rỗng (opening_amount có sẵn).
	- Thừa MOP trong Summary (không có ở Opening) => THROW để sửa cấu hình.
	- Sau khi auto-bù: số lượng phải 1:1.
	"""
	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		pos_profile = getattr(opening_shift, "pos_profile", None) or getattr(shift_report, "pos_profile", None)
		company = getattr(opening_shift, "company", None)

		# Initialize logger with POS Profile name
		log = get_logger(pos_profile or "POSProfile")

		# currency ưu tiên POS Profile -> Company -> USD
		currency = None
		if pos_profile:
			currency = frappe.db.get_value("POS Profile", pos_profile, "currency")
		if not currency and company:
			currency = frappe.get_cached_value("Company", company, "default_currency")
		currency = currency or "USD"

		# Opening methods map
		open_map = {}
		for d in (opening_shift.balance_details or []):
			open_map[_norm_mop(d.mode_of_payment)] = (d.mode_of_payment, flt(d.amount or 0, 2))
		open_set = set(open_map.keys())

		filters = {
			"shift_report_id": shift_report.shift_report_id,
			"pos_shift_report": shift_report.name,
		}

		summ_rows = frappe.get_all(
			"POS Payment Summary",
			filters=filters,
			fields=["name", "payment_method"],
		)
		sum_map = {}
		for r in summ_rows:
			sum_map.setdefault(_norm_mop(r.payment_method), []).append(r.name)
		sum_set = set(sum_map.keys())

		missing = open_set - sum_set
		extra = sum_set - open_set

		# Auto-add missing with zero tx
		if missing:
			shift_start_time = _compose_datetime(getattr(shift_report, "opening_date", None), getattr(shift_report, "opening_time", None))
			shift_end_time = _compose_datetime(getattr(shift_report, "closing_date", None), getattr(shift_report, "closing_time", None))

			for norm in missing:
				orig, opening_amt = open_map[norm]
				try:
					doc = frappe.get_doc(
						{
							"doctype": "POS Payment Summary",
							"shift_report_id": shift_report.shift_report_id,
							"pos_shift_report": shift_report.name,
							"pos_opening_shift": shift_report.pos_opening_shift,
							"posting_date": getattr(shift_report, "opening_date", None),
							"shift_start_time": shift_start_time,
							"shift_end_time": shift_end_time,
							"payment_method": orig,
							"payment_method_type": get_payment_method_type(orig),
							"currency": currency,
							"company": company,
							"pos_profile": pos_profile,
							"opening_amount": opening_amt,
							"transaction_amount": 0.0,
							"closing_amount": opening_amt,
							"transaction_count": 0,
							"notes": f"Auto-added to ensure consistency for shift {shift_report.name}",
						}
					)
					doc.insert(ignore_permissions=True)
					log.info(f"[PAYMENT_SUMMARY] ➕ Auto-added missing MOP '{orig}'")
				except Exception as ie:
					log.error(f"[PAYMENT_SUMMARY] ❌ Cannot auto-add '{orig}': {str(ie)}")

		# Throw if extra exists
		if extra:
			readable = []
			for norm in extra:
				sample = (sum_map.get(norm) or [None])[0]
				mop = frappe.db.get_value("POS Payment Summary", sample, "payment_method") if sample else "(unknown)"
				readable.append(mop or "(unknown)")
			msg = f"Payment methods không khớp: Summary có phương thức không có ở Opening Shift: {readable}"
			log.error(f"[PAYMENT_SUMMARY] {msg}")
			frappe.throw(msg)

		# Recount after auto-bù
		count_sum = frappe.db.count("POS Payment Summary", filters)
		count_open = len(open_map)
		if count_sum != count_open:
			err = f"Tính nhất quán dữ liệu bị vi phạm: {count_sum} payment summaries vs {count_open} opening details"
			log.error(f"[PAYMENT_SUMMARY] {err}")
			frappe.throw(err)

		log.info(f"[PAYMENT_SUMMARY] ✅ Consistency OK: {count_sum} == {count_open}")

	except Exception as e:
		# Fallback logger if initialization failed
		fallback_log = get_logger("pos_payment_summary")
		fallback_log.error(f"[PAYMENT_SUMMARY] Lỗi validate tính nhất quán: {str(e)}")
		raise


def _resolve_allowed_payment_types():
	"""Đọc danh sách payment method types cho phép từ DocType definition."""
	try:
		df = frappe.get_meta("POS Payment Summary").get_field("payment_method_type")
		raw = (df.options or "").split("\n")
		return [o.strip() for o in raw if o and o.strip()]
	except Exception as e:
		log.warning(f"[PAYMENT_SUMMARY] Cannot read field options for payment_method_type: {str(e)}")
		return ["Tiền mặt", "Card", "Digital", "Khác"]


def get_payment_method_type(payment_method):
	"""
	Direct mapping từ Mode of Payment name sang Type theo chuẩn hệ thống.
	Sử dụng mapping cố định thay vì dựa vào database type.
	"""
	allowed = _resolve_allowed_payment_types()
	allowed_set = set(allowed)

	def pick(*cands):
		"""Pick first candidate available in allowed set."""
		for c in cands:
			if c in allowed_set:
				return c
		return allowed[0] if allowed else "Tiền mặt"

	# Direct mapping từ Mode of Payment name sang Type
	payment_method_mapping = {
		# Standard mappings theo yêu cầu
		"BANK": "Bank",
		"CASH": "Cash",
		"MPOS": "Bank",
		"POINT": "Cash",
		"QRPAY": "Bank",
		"WALLET": "Bank",

		# Case-insensitive variants
		"bank": "Bank",
		"cash": "Cash",
		"mpos": "Bank",
		"point": "Cash",
		"qrpay": "Bank",
		"wallet": "Bank",

		# Common variations
		"Tiền mặt": "Cash",
		"Cash": "Cash",
		"Bank Transfer": "Bank",
		"Credit Card": "Bank",
		"Debit Card": "Bank",
		"Mobile Payment": "Bank",
		"Digital Wallet": "Bank",
		"QR Payment": "Bank",
	}

	try:
		# Normalize payment method name for matching
		normalized_method = payment_method.strip().upper() if payment_method else ""

		# Try direct mapping first
		if normalized_method in payment_method_mapping:
			mapped_type = payment_method_mapping[normalized_method]
			# Validate against allowed types
			if mapped_type in allowed_set:
				return mapped_type

		# Fallback to database type if direct mapping fails
		try:
			db_type = (frappe.db.get_value("Mode of Payment", payment_method, "type") or "").strip().casefold()

			if db_type in ("cash", "tiền mặt"):
				return pick("Tiền mặt", "Cash")

			if db_type in ("bank", "mobile payment", "wallet", "upi", "qr"):
				return pick("Bank", "Mobile Payment", "Digital")

			if db_type in ("card", "credit card", "debit card"):
				return pick("Card", "Bank")

			if db_type in ("general", "other", "khác"):
				return pick("Khác", "General")
		except Exception:
			pass  # Continue to final fallback

		# Final fallback
		return pick("Tiền mặt", "Cash", "Khác")

	except Exception as e:
		# Fallback logger
		fallback_log = get_logger("pos_payment_summary")
		fallback_log.error(f"[PAYMENT_SUMMARY] Error getting type for '{payment_method}': {str(e)}")
		return pick("Tiền mặt", "Cash", "Khác")


def run_pos_payment_summary_migration():
	"""
	Migration script để cập nhật POS Payment Summary DocType.
	Chạy trong bench console để áp dụng thay đổi autoname và unique constraint.
	"""
	print("🚀 POS PAYMENT SUMMARY MIGRATION SCRIPT")
	print("=" * 50)

	try:
		# STEP 1: Check current state
		print("📋 STEP 1: Checking current DocType state...")
		meta = frappe.get_meta("POS Payment Summary")
		print(f"   Current autoname: {meta.autoname}")

		field = meta.get_field("shift_report_id")
		if field:
			unique = getattr(field, 'unique', False)
			print(f"   shift_report_id unique: {unique}")

		# STEP 2: Run migration
		print("\n⚙️ STEP 2: Running migration for posawesome app...")
		migrate_app("posawesome")
		print("   ✅ Migration completed")

		# STEP 3: Verify changes
		print("\n✅ STEP 3: Verifying changes...")
		meta_after = frappe.get_meta("POS Payment Summary")
		print(f"   New autoname: {meta_after.autoname}")

		field_after = meta_after.get_field("shift_report_id")
		if field_after:
			unique_after = getattr(field_after, 'unique', False)
			print(f"   shift_report_id unique: {unique_after}")

		# STEP 4: Test autoname
		print("\n🧪 STEP 4: Testing autoname generation...")
		test_doc = frappe.get_doc({
			"doctype": "POS Payment Summary",
			"shift_report_id": "MIGRATION-TEST-001",
			"payment_method": "Tiền mặt - POS"
		})

		autoname_result = test_doc.get_autoname()
		print(f"   Test autoname: {autoname_result}")

		# STEP 5: Clear cache
		print("\n🧹 STEP 5: Clearing cache...")
		frappe.clear_cache()
		print("   ✅ Cache cleared")

		print("\n🎉 MIGRATION SUCCESSFUL!")
		print("=" * 50)
		print("📊 Summary:")
		print(f"   • Autoname: {meta_after.autoname}")
		print(f"   • Unique removed: {not unique_after if 'unique_after' in locals() else 'N/A'}")
		print(f"   • Test autoname works: {autoname_result}")

		return {
			"success": True,
			"autoname": meta_after.autoname,
			"test_autoname": autoname_result
		}

	except Exception as e:
		print(f"\n💥 MIGRATION FAILED: {str(e)}")
		import traceback
		traceback.print_exc()

		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def initialize_payment_summaries_for_shift(shift_report_name):
	"""
	Khởi tạo "rỗng" toàn bộ POS Payment Summary theo Opening Shift (1:1 phương thức).
	- Xoá sạch record cũ của shift này (an toàn vì chỉ là bảng tổng hợp).
	- Tạo mới mỗi MOP với opening_amount & closing_amount = opening_amount.
	"""
	try:
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		company, pos_profile, currency = _get_company_profile_currency(shift_report)

		# Initialize logger with POS Profile name
		log = get_logger(pos_profile or "POSProfile")

		log.info(f"[PAYMENT_SUMMARY] Init summaries for: {shift_report_name}")

		# Opening amounts
		opening_amounts = {}
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
			if getattr(opening_shift, "balance_details", None):
				for d in opening_shift.balance_details:
					opening_amounts[d.mode_of_payment] = flt(d.amount or 0, 2)
		except Exception as e:
			log.error(f"[PAYMENT_SUMMARY] Cannot read opening amounts: {str(e)}")

		# Cleanup old
		existing = frappe.get_all(
			"POS Payment Summary",
			filters={"shift_report_id": shift_report.shift_report_id, "pos_shift_report": shift_report.name},
			fields=["name", "payment_method"],
		)
		for row in existing:
			try:
				frappe.delete_doc("POS Payment Summary", row.name, ignore_permissions=True)
			except Exception as de:
				log.warning(f"[PAYMENT_SUMMARY] Cannot delete {row.name}: {str(de)}")

		# Create fresh
		created = 0
		shift_start_time = _compose_datetime(getattr(shift_report, "opening_date", None), getattr(shift_report, "opening_time", None))
		shift_end_time = _compose_datetime(getattr(shift_report, "closing_date", None), getattr(shift_report, "closing_time", None))

		for method, opening_amount in opening_amounts.items():
			try:
				doc = frappe.get_doc(
					{
						"doctype": "POS Payment Summary",
						"shift_report_id": shift_report.shift_report_id,
						"pos_shift_report": shift_report.name,
						"pos_opening_shift": shift_report.pos_opening_shift,
						"posting_date": getattr(shift_report, "opening_date", None),
						"shift_start_time": shift_start_time,
						"shift_end_time": shift_end_time,
						"payment_method": method,
						"payment_method_type": get_payment_method_type(method),
						"currency": currency,
						"company": company,
						"pos_profile": pos_profile,
						"opening_amount": opening_amount,
						"transaction_amount": 0.0,
						"closing_amount": opening_amount,
						"transaction_count": 0,
						"notes": f"Initialized for shift report {shift_report.name}",
					}
				)
				doc.insert(ignore_permissions=True)
				created += 1
			except Exception as ce:
				log.error(f"[PAYMENT_SUMMARY] Cannot init '{method}': {str(ce)}")

		log.info(f"[PAYMENT_SUMMARY] ✅ Initialized {created} record(s)")
		return {"success": True, "message": f"Initialized {created} records", "data": {"initialized_count": created}}

	except Exception as e:
		# Fallback logger if initialization failed
		fallback_log = get_logger("pos_payment_summary")
		fallback_log.error(f"[PAYMENT_SUMMARY] Error initializing: {str(e)}")
		return {"success": False, "message": f"Error initializing: {str(e)}"}
