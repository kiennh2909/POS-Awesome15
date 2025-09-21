import frappe
from frappe import _
from frappe.utils import flt
import json
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("shift_report")

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
		log.info(f"[SHIFT_REPORT_API] 🚀 START create_shift_report - Data: {data}")

		# STEP 1: Validate required fields
		log.info(f"[SHIFT_REPORT_API] 📋 STEP 1: Validating required fields")
		if not data.get("pos_opening_shift"):
			log.error(f"[SHIFT_REPORT_API] ❌ STEP 1: POS Opening Shift is required")
			frappe.throw(_("POS Opening Shift is required"))

		pos_opening_shift = data.get("pos_opening_shift")
		log.info(f"[SHIFT_REPORT_API] ✅ STEP 1: POS Opening Shift provided: {pos_opening_shift}")

		# STEP 2: Check if POS Opening Shift exists
		log.info(f"[SHIFT_REPORT_API] 🔍 STEP 2: Checking if POS Opening Shift exists: {pos_opening_shift}")
		if not frappe.db.exists("POS Opening Shift", pos_opening_shift):
			log.error(f"[SHIFT_REPORT_API] ❌ STEP 2: POS Opening Shift not found: {pos_opening_shift}")
			frappe.throw(_("POS Opening Shift not found"))

		log.info(f"[SHIFT_REPORT_API] ✅ STEP 2: POS Opening Shift exists: {pos_opening_shift}")

		# STEP 3: Check if shift report already exists
		log.info(f"[SHIFT_REPORT_API] 🔍 STEP 3: Checking if shift report already exists for opening shift: {pos_opening_shift}")
		existing = frappe.db.exists("POS Shift Report",
			{"pos_opening_shift": pos_opening_shift}
		)
		if existing:
			log.warning(f"[SHIFT_REPORT_API] ⚠️ STEP 3: Shift report already exists for opening shift: {pos_opening_shift}")
			frappe.throw(_("Shift report already exists for this opening shift"))

		log.info(f"[SHIFT_REPORT_API] ✅ STEP 3: No existing shift report found")

		# STEP 4: Get opening shift data
		log.info(f"[SHIFT_REPORT_API] 📥 STEP 4: Loading POS Opening Shift data: {pos_opening_shift}")
		opening_shift = frappe.get_doc("POS Opening Shift", pos_opening_shift)
		log.info(f"[SHIFT_REPORT_API] ✅ STEP 4: Loaded opening shift - Date: {opening_shift.posting_date}, User: {opening_shift.owner}")

		# STEP 5: Create shift report document
		log.info(f"[SHIFT_REPORT_API] 📝 STEP 5: Creating POS Shift Report document")
		shift_report_id = data.get("shift_report_id") or f"SHIFT-{opening_shift.name}"
		opening_time = frappe.utils.get_time(opening_shift.period_start_date)

		shift_report = frappe.get_doc({
			"doctype": "POS Shift Report",
			"shift_report_id": shift_report_id,
			"pos_opening_shift": opening_shift.name,
			"opening_date": opening_shift.posting_date,
			"opening_time": opening_time,
			"opened_by": opening_shift.owner,
			"opening_amounts": data.get("opening_amounts", "{}"),
			"status": "Open"
		})

		log.info(f"[SHIFT_REPORT_API] 📋 STEP 5: Shift report data prepared - ID: {shift_report_id}, Opening Time: {opening_time}")
		shift_report.insert()
		log.info(f"[SHIFT_REPORT_API] ✅ STEP 5: POS Shift Report created successfully: {shift_report.name}")

		# STEP 6: Auto-create POS Payment Summary records
		log.info(f"[SHIFT_REPORT_API] 🔄 STEP 6: Auto-creating POS Payment Summary records for: {shift_report.name}")
		try:
			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import initialize_payment_summaries_for_shift

			init_result = initialize_payment_summaries_for_shift(shift_report.name)

			if init_result.get("success"):
				initialized_count = init_result['data']['initialized_count']
				log.info(f"[SHIFT_REPORT_API] ✅ STEP 6: Auto-created {initialized_count} POS Payment Summary records")
			else:
				log.warning(f"[SHIFT_REPORT_API] ⚠️ STEP 6: Failed to auto-create POS Payment Summary: {init_result.get('message')}")

		except Exception as init_error:
			log.error(f"[SHIFT_REPORT_API] ❌ STEP 6: Error auto-creating POS Payment Summary: {str(init_error)}")
			# Don't fail the entire operation if payment summary creation fails
			# Just log the error and continue

		log.info(f"[SHIFT_REPORT_API] 🎉 COMPLETED create_shift_report successfully - Shift Report: {shift_report.name} (ID: {shift_report_id})")
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
		log.error(f"[SHIFT_REPORT_API] 💥 FAILED create_shift_report - Error: {str(e)}")
		frappe.log_error(str(e), "Create Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_shift_report(shift_report_id):
	"""
	Get POS Shift Report by shift_report_id field or name

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Shift report data
	"""
	try:
		# Try to find shift report by shift_report_id field first
		shift_reports = frappe.get_all("POS Shift Report",
			filters={"shift_report_id": shift_report_id},
			fields=["name"],
			limit=1
		)

		# If not found by shift_report_id, try by name
		if not shift_reports:
			if frappe.db.exists("POS Shift Report", shift_report_id):
				shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
			else:
				frappe.throw(_("Shift report not found"))
		else:
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

@frappe.whitelist()
def get_shift_report_verification_status(shift_report_id):
	"""
	Get verification status of a shift report

	Args:
		shift_report_id: The ID of the shift report

	Returns:
		dict: Verification status information
	"""
	try:
		log.info(f"[SHIFT_VERIFICATION] 📊 GET STATUS - Shift Report ID: {shift_report_id}")

		# Permission check
		if not frappe.has_permission("POS Shift Report", "read"):
			return {
				"success": False,
				"message": _("Not permitted to view shift report verification status")
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

		# Return verification status
		return {
			"success": True,
			"data": {
				"shift_report_id": shift_report_id,
				"verification_status": getattr(shift_report, 'verification_status', 'Pending'),
				"verified_by": getattr(shift_report, 'verified_by', None),
				"verified_at": getattr(shift_report, 'verified_at', None),
				"can_verify": _can_user_verify_shift_report(shift_report)
			}
		}

	except Exception as e:
		log.error(f"[SHIFT_VERIFICATION] 💥 UNEXPECTED ERROR - {str(e)}")
		return {
			"success": False,
			"message": _("An unexpected error occurred")
		}

def _can_user_verify_shift_report(shift_report):
	"""
	Check if current user can verify the shift report

	Args:
		shift_report: POS Shift Report document

	Returns:
		bool: True if user can verify
	"""
	try:
		# Check permissions
		if not frappe.has_permission("POS Shift Report", "write"):
			return False

		# Check if already verified
		current_status = getattr(shift_report, 'verification_status', 'Pending')
		if current_status in ['Verified', 'Confirmed']:
			return False

		# Check if user is shift owner or has admin role
		shift_user = getattr(shift_report, 'user', None)
		current_user = frappe.session.user

		# Allow verification if user is the shift owner or has admin role
		if shift_user == current_user:
			return True

		# Check for admin roles
		user_roles = frappe.get_roles(current_user)
		admin_roles = ['System Manager', 'Administrator', 'POS Admin']

		for role in admin_roles:
			if role in user_roles:
				return True

		return False

	except Exception as e:
		log.error(f"[SHIFT_VERIFICATION] ❌ PERMISSION CHECK ERROR - {str(e)}")
		return False

@frappe.whitelist()
def get_footer_status_data():
	"""
	Get footer status data for POS interface

	Returns:
		dict: Footer status information
	"""
	try:
		log.info("[FOOTER_STATUS] 📊 GET FOOTER STATUS DATA")

		# Get current user info
		cashier_name = frappe.session.user_fullname or frappe.session.user or "Unknown"

		# Get current date/time
		from frappe.utils import now, getdate, get_datetime
		current_datetime = get_datetime()
		current_date = current_datetime.strftime("%Y-%m-%d")
		current_time = current_datetime.strftime("%H:%M:%S")

		# Get current opening shift for user
		opening_shifts = frappe.get_all("POS Opening Shift",
			filters={
				"user": frappe.session.user,
				"status": "Open",
				"docstatus": 1
			},
			fields=["name", "shift_report", "shift_report_id"],
			order_by="creation desc",
			limit=1
		)

		shift_report_id = ""
		cash_balance = 0
		last_invoice = ""
		today_sales = 0
		total_revenue = 0
		currency = "USD"  # Default

		if opening_shifts:
			opening_shift = opening_shifts[0]
			shift_report_id = opening_shift.shift_report_id or ""

			# Get shift report data if exists
			if opening_shift.shift_report:
				try:
					shift_report = frappe.get_doc("POS Shift Report", opening_shift.shift_report)
					today_sales = shift_report.total_sales or 0
					total_revenue = (shift_report.total_sales or 0) + (shift_report.total_returns or 0)

					# Get last invoice
					if shift_report.invoices and len(shift_report.invoices) > 0:
						last_invoice = shift_report.invoices[-1].invoice_no or ""

					# Get currency from POS Profile
					if shift_report.pos_opening_shift:
						pos_profile = frappe.db.get_value("POS Opening Shift", shift_report.pos_opening_shift, "pos_profile")
						if pos_profile:
							currency = frappe.db.get_value("POS Profile", pos_profile, "currency") or "USD"

				except Exception as e:
					log.warning(f"[FOOTER_STATUS] Could not load shift report data: {str(e)}")

		return {
			"success": True,
			"data": {
				"cashier_name": cashier_name,
				"current_date": current_date,
				"current_time": current_time,
				"shift_report_id": shift_report_id,
				"cash_balance": cash_balance,
				"last_invoice": last_invoice,
				"today_sales": today_sales,
				"total_revenue": total_revenue,
				"currency": currency
			}
		}

	except Exception as e:
		log.error(f"[FOOTER_STATUS] 💥 ERROR - {str(e)}")
		return {
			"success": False,
			"message": str(e)
		}
