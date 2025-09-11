import frappe
from frappe import _
from frappe.utils import nowdate, nowtime
import json

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
	Get POS Shift Report by ID or shift_report_id field

	Args:
		shift_report_id (str): Shift report ID, shift_report_id field, or name

	Returns:
		dict: Shift report data (compatible with frappe.client.get format)
	"""
	try:
		# First try direct name lookup
		if frappe.db.exists("POS Shift Report", shift_report_id):
			shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
		else:
			# Try to find by shift_report_id field
			shift_reports = frappe.get_all("POS Shift Report",
				filters={"shift_report_id": shift_report_id},
				fields=["name"],
				limit=1
			)

			if not shift_reports:
				frappe.throw(_("Shift report not found"))

			shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)

		# ✅ RETURN FORMAT COMPATIBLE WITH frappe.client.get
		# Vue component expects: shiftReportResponse.message (direct data)
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
					"status": invoice.status
				} for invoice in shift_report.invoices
			] if shift_report.invoices else []
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Report Error")
		# ✅ RETURN ERROR IN COMPATIBLE FORMAT
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
def delete_shift_report(shift_report_id):
	"""
	Delete POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Delete result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Only allow deletion of open reports
		if shift_report.status != "Open":
			frappe.throw(_("Cannot delete closed or submitted shift reports"))

		shift_report.delete()

		return {
			"success": True,
			"message": _("Shift report deleted successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Delete Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_footer_status_data():
	"""
	Get data for footer status bar
	Returns cashier info, shift report summary, and sales totals
	"""
	try:
		user = frappe.session.user

		# Get current opening shift for user
		active_shift = frappe.get_all(
			"POS Opening Shift",
			filters={
				"owner": user,
				"docstatus": 1,
				"status": "Open"
			},
			fields=["name", "shift_report", "shift_report_id"],
			limit=1
		)

		if not active_shift:
			return {
				"success": False,
				"message": "No active opening shift found"
			}

		shift_data = active_shift[0]
		result = {
			"cashier_name": frappe.session.user_fullname or frappe.session.user,
			"shift_report_id": shift_data.shift_report_id or "",
			"total_invoices": 0,
			"total_revenue": 0,
			"last_invoice": ""
		}

		# Get shift report data if exists
		if shift_data.shift_report:
			shift_report = frappe.get_doc("POS Shift Report", shift_data.shift_report)
			result.update({
				"total_invoices": shift_report.invoice_count or 0,
				"total_revenue": (shift_report.total_sales or 0) - (shift_report.total_returns or 0),
			})

			# Get last invoice from shift report
			if shift_report.invoices and len(shift_report.invoices) > 0:
				last_invoice_data = shift_report.invoices[-1]
				result["last_invoice"] = last_invoice_data.invoice_no or ""

		return {
			"success": True,
			"data": result
		}

	except Exception as e:
		frappe.logger().error(f"Error getting footer status data: {str(e)}")
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
def get_current_shift_report():
	"""
	Get current shift report for logged-in user

	Returns:
		dict: Current shift report data
	"""
	try:
		user = frappe.session.user

		# Find active opening shift for current user
		active_shift = frappe.get_all(
			"POS Opening Shift",
			filters={
				"owner": user,
				"docstatus": 1,
				"status": "Open"
			},
			fields=["name"],
			limit=1
		)

		if not active_shift:
			return {
				"success": False,
				"message": _("No active opening shift found for current user")
			}

		# Find shift report for this opening shift
		shift_report = frappe.get_all(
			"POS Shift Report",
			filters={
				"pos_opening_shift": active_shift[0].name,
				"status": "Open"
			},
			fields=["name"],
			limit=1
		)

		if not shift_report:
			return {
				"success": False,
				"message": _("No active shift report found")
			}

		# Return full shift report data
		return get_shift_report(shift_report[0].name)

	except Exception as e:
		frappe.log_error(str(e), "Get Current Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def submit_shift_report(shift_report_id):
	"""
	Submit POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Submit result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Validate before submit
		if shift_report.verification_status != "Confirmed":
			frappe.throw(_("Shift report must be confirmed before submission"))

		shift_report.submit()

		return {
			"success": True,
			"message": _("Shift report submitted successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Submit Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def cancel_shift_report(shift_report_id):
	"""
	Cancel POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Cancel result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Only allow cancellation of open reports
		if shift_report.status != "Open":
			frappe.throw(_("Cannot cancel submitted shift reports"))

		shift_report.cancel()

		return {
			"success": True,
			"message": _("Shift report cancelled successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Cancel Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}