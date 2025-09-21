import frappe
from frappe import _
from frappe.utils import flt
import json
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("shift_reports")

@frappe.whitelist()
def create_shift_report(data):
	"""
	Create a new POS Shift Report

	Args:
		data (dict): Shift report data including:
			- pos_opening_shift: Opening shift name
			- opening_amounts: JSON string of opening amounts
			- shift_report_id: Optional custom ID

	Returns:
		dict: Created shift report data
	"""
	try:
		# Validate required fields
		if not data.get("pos_opening_shift"):
			frappe.throw(_("POS Opening Shift is required"))

		if not frappe.db.exists("POS Opening Shift", data.get("pos_opening_shift")):
			frappe.throw(_("POS Opening Shift not found"))

		# Check if shift report already exists
		existing = frappe.db.exists("POS Shift Report",
			{"pos_opening_shift": data.get("pos_opening_shift")}
		)
		if existing:
			frappe.throw(_("Shift report already exists for this opening shift"))

		# Get opening shift data
		opening_shift = frappe.get_doc("POS Opening Shift", data.get("pos_opening_shift"))

		# Create shift report
		shift_report = frappe.get_doc({
			"doctype": "POS Shift Report",
			"shift_report_id": data.get("shift_report_id") or f"SHIFT-{opening_shift.name}",
			"pos_opening_shift": opening_shift.name,
			"opening_date": opening_shift.posting_date,
			"opening_time": opening_shift.posting_time,
			"opened_by": opening_shift.owner,
			"opening_amounts": data.get("opening_amounts", "{}"),
			"status": "Open"
		})

		shift_report.insert()

		# ✅ AUTO-CREATE POS PAYMENT SUMMARY RECORDS
		log.info(f"[SHIFT_REPORT_API] 🔄 CREATE_SHIFT_REPORT - Auto-creating POS Payment Summary records for: {shift_report.name}")
		try:
			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import initialize_payment_summaries_for_shift

			init_result = initialize_payment_summaries_for_shift(shift_report.name)

			if init_result.get("success"):
				log.info(f"[SHIFT_REPORT_API] ✅ CREATE_SHIFT_REPORT - Auto-created {init_result['data']['initialized_count']} POS Payment Summary records")
			else:
				log.warning(f"[SHIFT_REPORT_API] ⚠️ CREATE_SHIFT_REPORT - Failed to auto-create POS Payment Summary: {init_result.get('message')}")

		except Exception as init_error:
			log.error(f"[SHIFT_REPORT_API] ❌ CREATE_SHIFT_REPORT - Error auto-creating POS Payment Summary: {str(init_error)}")
			# Don't fail the entire operation if payment summary creation fails
			# Just log the error and continue

		return {
			"success": True,
			"message": _("Shift report created successfully"),
			"data": {
				"name": shift_report.name,
				"shift_report_id": shift_report.shift_report_id,
				"status": shift_report.status
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Create Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_shift_report(shift_report_id):
	"""
	Get POS Shift Report by shift_report_id field

	Args:
		shift_report_id (str): Shift report ID (string only)

	Returns:
		dict: Shift report data
	"""
	try:
		# Find shift report by shift_report_id field
		shift_reports = frappe.get_all("POS Shift Report",
			filters={"shift_report_id": shift_report_id},
			fields=["name"],
			limit=1
		)

		if not shift_reports:
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)

		# Return formatted data
		return {
			"name": shift_report.name,
			"shift_report_id": shift_report.shift_report_id,
			"pos_opening_shift": shift_report.pos_opening_shift,
			"opening_date": shift_report.opening_date,
			"opening_time": shift_report.opening_time,
			"opened_by": shift_report.opened_by,
			"opening_amounts": json.loads(shift_report.opening_amounts or "{}"),
			"expected_closing_amounts": json.loads(shift_report.expected_closing_amounts or "{}"),
			"actual_closing_amounts": json.loads(shift_report.actual_closing_amounts or "{}"),
			"total_opening_amount": shift_report.total_opening_amount,
			"total_expected_closing": shift_report.total_expected_closing,
			"total_actual_closing": shift_report.total_actual_closing,
			"difference": shift_report.difference,
			"verification_status": shift_report.verification_status,
			"verification_date": shift_report.verification_date,
			"verified_by": shift_report.verified_by,
			"confirmation_date": shift_report.confirmation_date,
			"confirmed_by": shift_report.confirmed_by,
			"closing_date": shift_report.closing_date,
			"closed_by": shift_report.closed_by,
			"status": shift_report.status,
			"invoice_count": shift_report.invoice_count,
			"total_sales": shift_report.total_sales,
			"total_returns": shift_report.total_returns,
			"payment_breakdown": json.loads(shift_report.payment_breakdown or "{}"),
			"notes": shift_report.notes,
			"invoices": [
				{
					"invoice_no": invoice.invoice_no,
					"invoice_date": invoice.invoice_date,
					"invoice_time": invoice.invoice_time,
					"customer": invoice.customer,
					"total_amount": invoice.total_amount,
					"paid_amount": invoice.paid_amount,
					"tax_amount": invoice.tax_amount,
					"payment_method": invoice.payment_method,
					"is_return": invoice.is_return,
					"status": invoice.status,
					"invoice_status": getattr(invoice, 'invoice_status', invoice.status)
				} for invoice in shift_report.invoices
			] if shift_report.invoices else []
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Report Error")
		frappe.throw(_("Error getting shift report: {0}").format(str(e)))

@frappe.whitelist()
def update_shift_report(shift_report_id, data):
	"""
	Update POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name
		data (dict): Updated data

	Returns:
		dict: Update result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Update allowed fields
		allowed_fields = [
			"expected_closing_amounts", "actual_closing_amounts",
			"verification_status", "notes"
		]

		for field in allowed_fields:
			if field in data:
				setattr(shift_report, field, data[field])

		shift_report.save()

		return {
			"success": True,
			"message": _("Shift report updated successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Update Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}



@frappe.whitelist()
def get_shift_reports(filters=None, limit_page_length=20, limit_start=0):
	"""
	Get list of POS Shift Reports

	Args:
		filters (dict): Filter criteria
		limit_page_length (int): Number of records per page
		limit_start (int): Starting record index

	Returns:
		dict: List of shift reports
	"""
	try:
		default_filters = {"docstatus": ["!=", 2]}  # Exclude cancelled
		if filters:
			default_filters.update(filters)

		shift_reports = frappe.get_all(
			"POS Shift Report",
			filters=default_filters,
			fields=[
				"name", "shift_report_id", "pos_opening_shift",
				"opening_date", "opening_time", "opened_by",
				"status", "verification_status", "invoice_count",
				"total_sales", "total_returns", "total_opening_amount",
				"total_expected_closing", "total_actual_closing", "difference"
			],
			order_by="creation desc",
			limit_page_length=limit_page_length,
			limit_start=limit_start
		)

		# Get total count
		total_count = frappe.db.count("POS Shift Report", filters=default_filters)

		return {
			"success": True,
			"data": shift_reports,
			"total_count": total_count
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Reports Error")
		return {
			"success": False,
			"message": str(e)
		}




@frappe.whitelist()
def get_shift_report_with_payment_summary(shift_report_id):
	"""
	Get POS Shift Report with Payment Summary data

	Args:
		shift_report_id (str): Shift report ID (string only)

	Returns:
		dict: Shift report data with payment summary
	"""
	try:
		# Get basic shift report data
		shift_report_data = get_shift_report(shift_report_id)

		# Recalculate totals if not verified
		shift_report_doc = frappe.get_doc("POS Shift Report", shift_report_data["name"])
		if getattr(shift_report_doc, 'verification_status', 'Pending') in ['Pending', None, '']:
			_recalculate_shift_totals(shift_report_doc, shift_report_data)

		# Create/update payment summaries
		try:
			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
			payment_result = create_payment_summaries_for_shift(shift_report_data["name"])

			if payment_result.get("success"):
				from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import get_payment_summaries_for_shift
				payment_summaries_result = get_payment_summaries_for_shift(shift_report_data["name"])

				if payment_summaries_result.get("success"):
					shift_report_data["payment_summaries"] = payment_summaries_result["data"]
				else:
					shift_report_data["payment_summaries"] = []
			else:
				shift_report_data["payment_summaries"] = []
		except Exception:
			shift_report_data["payment_summaries"] = []

		return shift_report_data

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Report With Payment Summary Error")
		return {
			"success": False,
			"message": _("Error getting shift report: {0}").format(str(e))
		}


def _recalculate_shift_totals(shift_report_doc, shift_report_data):
	"""Recalculate invoice totals for unverified shifts"""
	if not shift_report_doc.invoices:
		return

	total_sales = 0
	total_returns = 0
	invoice_count = len(shift_report_doc.invoices)

	for invoice in shift_report_doc.invoices:
		if invoice.status == "Paid" and not invoice.is_return:
			total_sales += invoice.total_amount or 0
		if invoice.status == "Cancelled" or invoice.is_return:
			total_returns += invoice.total_amount or 0

	# Update document
	shift_report_doc.invoice_count = invoice_count
	shift_report_doc.total_sales = total_sales
	shift_report_doc.total_returns = total_returns
	shift_report_doc.save(ignore_permissions=True)

	# Update response data
	shift_report_data["invoice_count"] = invoice_count
	shift_report_data["total_sales"] = total_sales
	shift_report_data["total_returns"] = total_returns




# ===== SHIFT VERIFICATION FUNCTIONS =====

@frappe.whitelist()
def verify_shift_report(shift_report_id):
	"""
	Verify a shift report with permission checks and validation

	Args:
		shift_report_id: The ID of the shift report to verify

	Returns:
		dict: Success/error response
	"""
	try:
		# Permission checks
		if not frappe.has_permission("POS Shift Report", "write"):
			return {
				"success": False,
				"message": _("Not permitted to verify shift reports")
			}

		# Validate input
		if not shift_report_id:
			return {
				"success": False,
				"message": _("Shift report ID is required")
			}

		# Find shift report
		shift_reports = frappe.get_all("POS Shift Report",
			filters={"shift_report_id": shift_report_id},
			fields=["name"],
			limit=1
		)

		if not shift_reports:
			return {
				"success": False,
				"message": _("Shift report not found")
			}

		shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)

		# Check current verification status
		current_status = getattr(shift_report, 'verification_status', 'Pending')
		if current_status in ['Verified', 'Confirmed']:
			return {
				"success": False,
				"message": _("Shift report is already verified")
			}

		# Validate shift report data
		validation_result = _validate_shift_report_data(shift_report)
		if not validation_result["valid"]:
			return {
				"success": False,
				"message": validation_result["message"]
			}

		# Update verification status
		shift_report.verification_status = "Verified"
		shift_report.verified_by = frappe.session.user
		shift_report.verified_at = frappe.utils.now()
		shift_report.save(ignore_permissions=True)

		# Log verification activity
		try:
			_log_verification_activity(shift_report)
		except Exception:
			# Don't fail verification if logging fails
			pass

		return {
			"success": True,
			"message": _("Shift report verified successfully"),
			"data": {
				"shift_report_id": shift_report_id,
				"verification_status": "Verified",
				"verified_by": frappe.session.user,
				"verified_at": frappe.utils.now()
			}
		}

	except Exception as e:
		frappe.log_error(f"Unexpected error in verify_shift_report: {str(e)}",
						"Shift Verification Error")
		return {
			"success": False,
			"message": _("An unexpected error occurred while verifying the shift report")
		}


def _validate_shift_report_data(shift_report):
	"""
	Validate shift report data before verification

	Args:
		shift_report: POS Shift Report document

	Returns:
		dict: Validation result
	"""
	try:
		# Check if shift has invoices
		invoice_count = getattr(shift_report, 'invoice_count', 0)
		if invoice_count == 0:
			return {
				"valid": False,
				"message": _("Cannot verify shift report with no invoices")
			}

		# Check if shift is closed
		if getattr(shift_report, 'status', '') == 'Closed':
			return {
				"valid": False,
				"message": _("Cannot verify a closed shift report")
			}

		return {"valid": True}

	except Exception as e:
		return {
			"valid": False,
			"message": _("Error validating shift report data")
		}


def _log_verification_activity(shift_report):
	"""
	Log verification activity for audit trail

	Args:
		shift_report: POS Shift Report document
	"""
	try:
		# Create activity log entry
		activity_doc = frappe.get_doc({
			"doctype": "Activity Log",
			"user": frappe.session.user,
			"reference_doctype": "POS Shift Report",
			"reference_name": shift_report.name,
			"action": "Verify",
			"subject": f"Shift Report {shift_report.shift_report_id} verified",
			"content": f"Verified by {frappe.session.user} at {frappe.utils.now()}"
		})
		activity_doc.insert(ignore_permissions=True)

	except Exception:
		# Don't raise error if activity logging fails
		pass


# ===== SHIFT CALCULATIONS FUNCTIONS =====

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


# ===== SHIFT ANALYTICS FUNCTIONS =====

@frappe.whitelist()
def get_shift_analytics(filters=None):
	"""
	Get comprehensive shift analytics

	Args:
		filters (dict): Filter criteria

	Returns:
		dict: Analytics data
	"""
	try:
		default_filters = {
			"docstatus": 1,
			"status": "Closed"
		}

		if filters:
			default_filters.update(filters)

		# Get shift reports
		shift_reports = frappe.get_all(
			"POS Shift Report",
			filters=default_filters,
			fields=[
				"name", "shift_report_id", "opening_date", "opening_time",
				"total_opening_amount", "total_expected_closing", "total_actual_closing",
				"difference", "invoice_count", "total_sales", "total_returns",
				"opened_by", "verification_status"
			],
			order_by="opening_date desc, opening_time desc"
		)

		analytics = {
			"summary": _calculate_analytics_summary(shift_reports),
			"trends": _calculate_trends(shift_reports),
			"performance": _calculate_performance_metrics(shift_reports),
			"variances": _calculate_variance_analysis(shift_reports),
			"top_performers": _get_top_performers(shift_reports)
		}

		return {
			"success": True,
			"data": analytics
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Analytics Error")
		return {
			"success": False,
			"message": str(e)
		}


def _calculate_analytics_summary(shift_reports):
	"""Calculate summary statistics"""
	if not shift_reports:
		return {}

	total_shifts = len(shift_reports)
	total_sales = sum(report.get("total_sales", 0) for report in shift_reports)
	total_returns = sum(report.get("total_returns", 0) for report in shift_reports)
	total_opening = sum(report.get("total_opening_amount", 0) for report in shift_reports)
	total_difference = sum(report.get("difference", 0) for report in shift_reports)

	avg_sales_per_shift = total_sales / total_shifts if total_shifts > 0 else 0
	avg_invoices_per_shift = sum(report.get("invoice_count", 0) for report in shift_reports) / total_shifts if total_shifts > 0 else 0

	return {
		"total_shifts": total_shifts,
		"total_sales": total_sales,
		"total_returns": total_returns,
		"net_sales": total_sales + total_returns,
		"total_opening_amount": total_opening,
		"total_variance": total_difference,
		"average_sales_per_shift": avg_sales_per_shift,
		"average_invoices_per_shift": avg_invoices_per_shift,
		"variance_percentage": (total_difference / total_opening * 100) if total_opening > 0 else 0
	}


def _calculate_trends(shift_reports):
	"""Calculate sales trends over time"""
	trends = {}
	daily_sales = {}
	daily_invoices = {}

	for report in shift_reports:
		date = report.get("opening_date")
		if date:
			if date not in daily_sales:
				daily_sales[date] = 0
				daily_invoices[date] = 0

			daily_sales[date] += report.get("total_sales", 0)
			daily_invoices[date] += report.get("invoice_count", 0)

	# Sort by date
	sorted_dates = sorted(daily_sales.keys())

	trends["daily_sales"] = [{"date": date, "amount": daily_sales[date]} for date in sorted_dates]
	trends["daily_invoices"] = [{"date": date, "count": daily_invoices[date]} for date in sorted_dates]

	return trends


def _calculate_performance_metrics(shift_reports):
	"""Calculate performance metrics"""
	performance = {
		"best_shift": None,
		"worst_shift": None,
		"most_efficient": None,
		"highest_variance": None
	}

	if not shift_reports:
		return performance

	best_sales = 0
	worst_sales = float('inf')
	highest_variance = 0
	most_efficient = 0

	for report in shift_reports:
		sales = report.get("total_sales", 0)
		variance = abs(report.get("difference", 0))
		invoices = report.get("invoice_count", 0)

		# Best performing shift by sales
		if sales > best_sales:
			best_sales = sales
			performance["best_shift"] = report

		# Worst performing shift
		if sales < worst_sales and sales > 0:
			worst_sales = sales
			performance["worst_shift"] = report

		# Highest variance
		if variance > highest_variance:
			highest_variance = variance
			performance["highest_variance"] = report

		# Most efficient (sales per invoice)
		if invoices > 0:
			efficiency = sales / invoices
			if efficiency > most_efficient:
				most_efficient = efficiency
				performance["most_efficient"] = report

	return performance


def _calculate_variance_analysis(shift_reports):
	"""Analyze variances in shift reports"""
	variances = {
		"within_tolerance": 0,
		"over_tolerance": 0,
		"under_tolerance": 0,
		"variance_ranges": {
			"0-10": 0,
			"10-50": 0,
			"50-100": 0,
			"100+": 0
		}
	}

	tolerance = 10  # Default tolerance

	for report in shift_reports:
		difference = report.get("difference", 0)
		variance_abs = abs(difference)

		# Categorize by tolerance
		if variance_abs <= tolerance:
			variances["within_tolerance"] += 1
		elif difference > 0:
			variances["over_tolerance"] += 1
		else:
			variances["under_tolerance"] += 1

		# Categorize by variance range
		if variance_abs <= 10:
			variances["variance_ranges"]["0-10"] += 1
		elif variance_abs <= 50:
			variances["variance_ranges"]["10-50"] += 1
		elif variance_abs <= 100:
			variances["variance_ranges"]["50-100"] += 1
		else:
			variances["variance_ranges"]["100+"] += 1

	return variances


def _get_top_performers(shift_reports):
	"""Get top performing users and shifts"""
	performers = {
		"top_sales_users": [],
		"top_invoice_users": [],
		"top_efficient_users": []
	}

	user_stats = {}

	# Aggregate by user
	for report in shift_reports:
		user = report.get("opened_by")
		if not user:
			continue

		if user not in user_stats:
			user_stats[user] = {
				"total_sales": 0,
				"total_invoices": 0,
				"shift_count": 0
			}

		user_stats[user]["total_sales"] += report.get("total_sales", 0)
		user_stats[user]["total_invoices"] += report.get("invoice_count", 0)
		user_stats[user]["shift_count"] += 1

	# Calculate averages and find top performers
	for user, stats in user_stats.items():
		avg_sales = stats["total_sales"] / stats["shift_count"] if stats["shift_count"] > 0 else 0
		avg_invoices = stats["total_invoices"] / stats["shift_count"] if stats["shift_count"] > 0 else 0
		efficiency = avg_sales / avg_invoices if avg_invoices > 0 else 0

		performers["top_sales_users"].append({
			"user": user,
			"avg_sales": avg_sales,
			"total_sales": stats["total_sales"],
			"shift_count": stats["shift_count"]
		})

		performers["top_invoice_users"].append({
			"user": user,
			"avg_invoices": avg_invoices,
			"total_invoices": stats["total_invoices"],
			"shift_count": stats["shift_count"]
		})

		performers["top_efficient_users"].append({
			"user": user,
			"efficiency": efficiency,
			"avg_sales": avg_sales,
			"avg_invoices": avg_invoices
		})

	# Sort and get top 5
	for key in performers:
		if key == "top_sales_users":
			performers[key].sort(key=lambda x: x["avg_sales"], reverse=True)
		elif key == "top_invoice_users":
			performers[key].sort(key=lambda x: x["avg_invoices"], reverse=True)
		else:  # top_efficient_users
			performers[key].sort(key=lambda x: x["efficiency"], reverse=True)

		performers[key] = performers[key][:5]

	return performers


@frappe.whitelist()
def get_shift_report_invoices(shift_report_id, page=1, page_size=10):
	"""
	Get paginated invoices for a shift report

	Args:
		shift_report_id (str): Shift report ID
		page (int): Page number (1-based)
		page_size (int): Number of items per page

	Returns:
		dict: Paginated invoice data
	"""
	try:
		# Validate inputs
		if not shift_report_id:
			return {
				"success": False,
				"message": "Shift report ID is required"
			}

		# Get shift report document
		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
		if not shift_report:
			return {
				"success": False,
				"message": "Shift report not found"
			}

		# Validate and sanitize inputs with better error handling
		try:
			page = int(page) if page else 1
			page_size = int(page_size) if page_size else 10

			# Ensure valid ranges
			if page < 1:
				page = 1
			if page_size < 1 or page_size > 100:  # Max 100 items per page
				page_size = 10
		except (ValueError, TypeError):
			page = 1
			page_size = 10

		# Calculate pagination with validation
		offset = (page - 1) * page_size
		if offset < 0:
			offset = 0

		# Get total count with error handling
		try:
			total_count = frappe.db.count("POS Shift Report Invoice", {
				"parent": shift_report.name,
				"parenttype": "POS Shift Report"
			})
		except Exception as count_error:
			frappe.log_error(f"Error counting invoices: {str(count_error)}", "Get Shift Report Invoices")
			total_count = 0

		# Calculate total pages safely
		total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

		# Adjust page if it exceeds total pages
		if page > total_pages and total_pages > 0:
			page = total_pages
			offset = (page - 1) * page_size

		# Get paginated invoices with error handling
		try:
			invoices = frappe.get_all(
				"POS Shift Report Invoice",
				filters={
					"parent": shift_report.name,
					"parenttype": "POS Shift Report"
				},
				fields=[
					"invoice_no",
					"invoice_date",
					"customer",
					"total_amount",
					"is_return",
					"status"
				],
				order_by="invoice_date desc, creation desc",
				limit=page_size,
				limit_start=offset
			)
		except Exception as query_error:
			frappe.log_error(f"Error querying invoices: {str(query_error)}", "Get Shift Report Invoices")
			invoices = []

		# Format invoice data for frontend with safe handling
		formatted_invoices = []
		for invoice in invoices:
			try:
				formatted_invoices.append({
					"invoice_no": invoice.invoice_no or "",
					"invoice_date": invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "",
					"customer": invoice.customer or "Walk-in Customer",
					"total_amount": float(invoice.total_amount or 0),
					"is_return": bool(invoice.is_return or False),
					"status": invoice.status or "Paid"
				})
			except Exception as format_error:
				frappe.log_error(f"Error formatting invoice {invoice.invoice_no}: {str(format_error)}", "Get Shift Report Invoices")
				continue

		return {
			"success": True,
			"invoices": formatted_invoices,
			"total_count": total_count,
			"total_pages": total_pages,
			"page": page,
			"page_size": page_size,
			"has_next": page < total_pages,
			"has_prev": page > 1
		}

	except Exception as e:
		frappe.log_error(f"Unexpected error in get_shift_report_invoices: {str(e)}", "Get Shift Report Invoices")
		return {
			"success": False,
			"message": f"Unexpected error: {str(e)}"
		}



