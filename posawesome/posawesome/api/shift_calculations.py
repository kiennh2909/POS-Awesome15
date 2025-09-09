import frappe
from frappe import _
from frappe.utils import nowdate, nowtime, get_datetime, flt
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def calculate_expected_closing_amounts(shift_report_id):
	"""
	Calculate expected closing amounts based on opening amounts and invoices

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Calculated expected amounts
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Get opening amounts
		opening_amounts = json.loads(shift_report.opening_amounts or "{}")

		# Calculate total opening amount
		total_opening = sum(flt(amount) for amount in opening_amounts.values())

		# Get all invoices for this shift
		invoices = frappe.get_all("Sales Invoice",
			filters={
				"pos_opening_shift": shift_report.pos_opening_shift,
				"docstatus": 1,
				"is_return": 0
			},
			fields=["grand_total", "paid_amount", "outstanding_amount"]
		)

		# Calculate total sales
		total_sales = sum(flt(inv.grand_total or 0) for inv in invoices)
		total_paid = sum(flt(inv.paid_amount or 0) for inv in invoices)

		# Calculate expected closing amounts
		expected_closing = total_opening + total_paid

		# Calculate payment method breakdown
		payment_breakdown = calculate_payment_breakdown(shift_report.pos_opening_shift)

		result = {
			"total_opening_amount": total_opening,
			"total_sales": total_sales,
			"total_paid": total_paid,
			"expected_closing_amount": expected_closing,
			"payment_breakdown": payment_breakdown,
			"invoice_count": len(invoices)
		}

		# Update shift report with calculated values
		shift_report.total_expected_closing = expected_closing
		shift_report.expected_closing_amounts = json.dumps(payment_breakdown)
		shift_report.invoice_count = len(invoices)
		shift_report.total_sales = total_sales
		shift_report.save()

		return {
			"success": True,
			"data": result
		}

	except Exception as e:
		frappe.log_error(str(e), "Calculate Expected Closing Amounts Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def calculate_payment_breakdown(opening_shift_id):
	"""
	Calculate payment method breakdown for a shift

	Args:
		opening_shift_id (str): POS Opening Shift ID

	Returns:
		dict: Payment breakdown by method
	"""
	try:
		breakdown = {}

		# Get all payments for invoices in this shift
		payments = frappe.db.sql("""
			SELECT
				pe.mode_of_payment,
				SUM(per.allocated_amount) as amount
			FROM `tabPayment Entry` pe
			JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
			JOIN `tabSales Invoice` si ON per.reference_name = si.name
			WHERE si.pos_opening_shift = %s
			AND si.docstatus = 1
			AND pe.docstatus = 1
			GROUP BY pe.mode_of_payment
		""", (opening_shift_id,), as_dict=True)

		# Convert to dictionary
		for payment in payments:
			breakdown[payment.mode_of_payment or "Cash"] = flt(payment.amount)

		# Ensure we have at least Cash entry
		if not breakdown:
			breakdown["Cash"] = 0

		return breakdown

	except Exception as e:
		frappe.log_error(str(e), "Calculate Payment Breakdown Error")
		return {"Cash": 0}

@frappe.whitelist()
def validate_closing_amounts(shift_report_id, actual_amounts):
	"""
	Validate actual closing amounts against expected amounts

	Args:
		shift_report_id (str): Shift report ID or name
		actual_amounts (dict): Actual amounts entered by user

	Returns:
		dict: Validation result with differences
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Parse actual amounts
		if isinstance(actual_amounts, str):
			actual_amounts = json.loads(actual_amounts)

		# Get expected amounts
		expected_amounts = json.loads(shift_report.expected_closing_amounts or "{}")

		# Calculate differences
		differences = {}
		total_expected = 0
		total_actual = 0

		# Check all payment methods
		all_methods = set(list(expected_amounts.keys()) + list(actual_amounts.keys()))

		for method in all_methods:
			expected = flt(expected_amounts.get(method, 0))
			actual = flt(actual_amounts.get(method, 0))
			difference = actual - expected

			differences[method] = {
				"expected": expected,
				"actual": actual,
				"difference": difference,
				"variance_percent": (difference / expected * 100) if expected != 0 else 0
			}

			total_expected += expected
			total_actual += actual

		total_difference = total_actual - total_expected

		# Determine validation status
		tolerance = flt(frappe.db.get_single_value("POS Profile",
			"closing_amount_tolerance") or 10)  # Default 10 currency units

		is_within_tolerance = abs(total_difference) <= tolerance

		result = {
			"total_expected": total_expected,
			"total_actual": total_actual,
			"total_difference": total_difference,
			"is_within_tolerance": is_within_tolerance,
			"tolerance_limit": tolerance,
			"breakdown": differences,
			"validation_status": "valid" if is_within_tolerance else "warning"
		}

		# Update shift report with actual amounts and differences
		shift_report.actual_closing_amounts = json.dumps(actual_amounts)
		shift_report.total_actual_closing = total_actual
		shift_report.difference = total_difference
		shift_report.save()

		return {
			"success": True,
			"data": result
		}

	except Exception as e:
		frappe.log_error(str(e), "Validate Closing Amounts Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def generate_shift_report_summary(shift_report_id):
	"""
	Generate comprehensive shift report summary

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Comprehensive shift report summary
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Get opening shift details
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)

		# Get invoice statistics
		invoice_stats = get_invoice_statistics(shift_report.pos_opening_shift)

		# Get payment method breakdown
		payment_breakdown = calculate_payment_breakdown(shift_report.pos_opening_shift)

		# Calculate time duration
		opening_datetime = get_datetime(f"{opening_shift.posting_date} {opening_shift.posting_time}")
		closing_datetime = get_datetime(nowdate() + " " + nowtime())
		duration_hours = (closing_datetime - opening_datetime).total_seconds() / 3600

		summary = {
			"shift_report_id": shift_report.shift_report_id,
			"opening_info": {
				"date": opening_shift.posting_date,
				"time": opening_shift.posting_time,
				"opened_by": opening_shift.owner,
				"pos_profile": opening_shift.pos_profile
			},
			"closing_info": {
				"date": nowdate(),
				"time": nowtime(),
				"duration_hours": round(duration_hours, 2)
			},
			"financial_summary": {
				"opening_amount": shift_report.total_opening_amount,
				"expected_closing": shift_report.total_expected_closing,
				"actual_closing": shift_report.total_actual_closing,
				"difference": shift_report.difference,
				"payment_breakdown": payment_breakdown
			},
			"invoice_summary": invoice_stats,
			"verification_info": {
				"status": shift_report.verification_status,
				"verified_by": shift_report.verified_by,
				"verified_date": shift_report.verification_date,
				"confirmed_by": shift_report.confirmed_by,
				"confirmed_date": shift_report.confirmation_date
			}
		}

		return {
			"success": True,
			"data": summary
		}

	except Exception as e:
		frappe.log_error(str(e), "Generate Shift Report Summary Error")
		return {
			"success": False,
			"message": str(e)
		}

def get_invoice_statistics(opening_shift_id):
	"""
	Get comprehensive invoice statistics for a shift

	Args:
		opening_shift_id (str): POS Opening Shift ID

	Returns:
		dict: Invoice statistics
	"""
	try:
		# Get all invoices for the shift
		invoices = frappe.get_all("Sales Invoice",
			filters={
				"pos_opening_shift": opening_shift_id,
				"docstatus": 1
			},
			fields=[
				"name", "grand_total", "paid_amount", "outstanding_amount",
				"is_return", "customer", "posting_date", "posting_time"
			]
		)

		stats = {
			"total_invoices": len(invoices),
			"sales_invoices": 0,
			"return_invoices": 0,
			"total_sales": 0,
			"total_returns": 0,
			"total_paid": 0,
			"total_outstanding": 0,
			"average_invoice_value": 0,
			"customer_count": 0
		}

		customers = set()

		for invoice in invoices:
			if invoice.is_return:
				stats["return_invoices"] += 1
				stats["total_returns"] += flt(invoice.grand_total)
			else:
				stats["sales_invoices"] += 1
				stats["total_sales"] += flt(invoice.grand_total)

			stats["total_paid"] += flt(invoice.paid_amount)
			stats["total_outstanding"] += flt(invoice.outstanding_amount)

			if invoice.customer:
				customers.add(invoice.customer)

		stats["customer_count"] = len(customers)

		# Calculate average invoice value
		if stats["total_invoices"] > 0:
			stats["average_invoice_value"] = (stats["total_sales"] - stats["total_returns"]) / stats["total_invoices"]

		return stats

	except Exception as e:
		frappe.log_error(str(e), "Get Invoice Statistics Error")
		return {}

@frappe.whitelist()
def get_shift_performance_metrics(shift_report_id):
	"""
	Get performance metrics for shift analysis

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Performance metrics
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Calculate hourly sales rate
		opening_datetime = get_datetime(f"{shift_report.opening_date} {shift_report.opening_time}")
		closing_datetime = get_datetime(nowdate() + " " + nowtime())
		hours_worked = (closing_datetime - opening_datetime).total_seconds() / 3600

		hourly_rate = shift_report.total_sales / hours_worked if hours_worked > 0 else 0

		# Calculate invoice per hour
		invoices_per_hour = shift_report.invoice_count / hours_worked if hours_worked > 0 else 0

		# Calculate average transaction value
		avg_transaction_value = shift_report.total_sales / shift_report.invoice_count if shift_report.invoice_count > 0 else 0

		# Calculate variance percentage
		variance_percent = 0
		if shift_report.total_expected_closing and shift_report.total_expected_closing != 0:
			variance_percent = (shift_report.difference / shift_report.total_expected_closing) * 100

		metrics = {
			"hours_worked": round(hours_worked, 2),
			"hourly_sales_rate": round(hourly_rate, 2),
			"invoices_per_hour": round(invoices_per_hour, 2),
			"average_transaction_value": round(avg_transaction_value, 2),
			"variance_amount": shift_report.difference,
			"variance_percentage": round(variance_percent, 2),
			"sales_efficiency": "high" if hourly_rate > 100 else "medium" if hourly_rate > 50 else "low",
			"invoice_efficiency": "high" if invoices_per_hour > 10 else "medium" if invoices_per_hour > 5 else "low"
		}

		return {
			"success": True,
			"data": metrics
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Performance Metrics Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def auto_calculate_shift_report(shift_report_id):
	"""
	Automatically calculate all shift report values

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Auto-calculation result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Calculate expected closing amounts
		expected_result = calculate_expected_closing_amounts(shift_report_id)
		if not expected_result["success"]:
			return expected_result

		# Update invoice details
		shift_report.update_from_invoices()

		# Calculate performance metrics
		metrics_result = get_shift_performance_metrics(shift_report_id)

		return {
			"success": True,
			"message": _("Shift report auto-calculated successfully"),
			"data": {
				"expected_amounts": expected_result["data"],
				"performance_metrics": metrics_result.get("data", {}) if metrics_result["success"] else {}
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Auto Calculate Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}