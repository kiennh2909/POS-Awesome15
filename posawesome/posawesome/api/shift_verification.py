import frappe
from frappe import _
from frappe.utils import nowdate, nowtime

@frappe.whitelist()
def verify_shift_report(shift_report_id, notes=None):
	"""
	Verify POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name
		notes (str): Optional verification notes

	Returns:
		dict: Verification result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Check permissions
		if not frappe.has_permission("POS Shift Report", "write"):
			frappe.throw(_("Not permitted to verify shift reports"))

		# Validate current status
		if shift_report.verification_status != "Pending":
			frappe.throw(_("Shift report is already {0}").format(shift_report.verification_status))

		# Update verification details
		shift_report.verification_status = "Verified"
		shift_report.verification_date = nowdate()
		shift_report.verified_by = frappe.session.user

		if notes:
			current_notes = shift_report.notes or ""
			shift_report.notes = f"{current_notes}\n\n[VERIFIED {nowdate()} by {frappe.session.user}]\n{notes}".strip()

		shift_report.save()

		# Log activity
		frappe.logger().info(f"Shift report {shift_report_id} verified by {frappe.session.user}")

		return {
			"success": True,
			"message": _("Shift report verified successfully"),
			"data": {
				"verification_status": shift_report.verification_status,
				"verification_date": shift_report.verification_date,
				"verified_by": shift_report.verified_by
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Verify Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def confirm_shift_report(shift_report_id, notes=None):
	"""
	Confirm POS Shift Report (Final approval)

	Args:
		shift_report_id (str): Shift report ID or name
		notes (str): Optional confirmation notes

	Returns:
		dict: Confirmation result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Check permissions
		if not frappe.has_permission("POS Shift Report", "submit"):
			frappe.throw(_("Not permitted to confirm shift reports"))

		# Validate current status
		if shift_report.verification_status != "Verified":
			frappe.throw(_("Shift report must be verified before confirmation"))

		# Update confirmation details
		shift_report.verification_status = "Confirmed"
		shift_report.confirmation_date = nowdate()
		shift_report.confirmed_by = frappe.session.user

		if notes:
			current_notes = shift_report.notes or ""
			shift_report.notes = f"{current_notes}\n\n[CONFIRMED {nowdate()} by {frappe.session.user}]\n{notes}".strip()

		shift_report.save()

		# Log activity
		frappe.logger().info(f"Shift report {shift_report_id} confirmed by {frappe.session.user}")

		return {
			"success": True,
			"message": _("Shift report confirmed successfully"),
			"data": {
				"verification_status": shift_report.verification_status,
				"confirmation_date": shift_report.confirmation_date,
				"confirmed_by": shift_report.confirmed_by
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Confirm Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def reject_shift_report(shift_report_id, reason):
	"""
	Reject POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name
		reason (str): Reason for rejection

	Returns:
		dict: Rejection result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		if not reason or not reason.strip():
			frappe.throw(_("Rejection reason is required"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Check permissions
		if not frappe.has_permission("POS Shift Report", "write"):
			frappe.throw(_("Not permitted to reject shift reports"))

		# Reset verification status
		shift_report.verification_status = "Pending"
		shift_report.verification_date = None
		shift_report.verified_by = None
		shift_report.confirmation_date = None
		shift_report.confirmed_by = None

		# Add rejection notes
		current_notes = shift_report.notes or ""
		shift_report.notes = f"{current_notes}\n\n[REJECTED {nowdate()} by {frappe.session.user}]\nReason: {reason}".strip()

		shift_report.save()

		# Log activity
		frappe.logger().info(f"Shift report {shift_report_id} rejected by {frappe.session.user}: {reason}")

		return {
			"success": True,
			"message": _("Shift report rejected successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Reject Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_shift_report_verification_history(shift_report_id):
	"""
	Get verification history for shift report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Verification history
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		history = []

		if shift_report.verification_date:
			history.append({
				"action": "Verified",
				"date": shift_report.verification_date,
				"user": shift_report.verified_by,
				"status": "Verified"
			})

		if shift_report.confirmation_date:
			history.append({
				"action": "Confirmed",
				"date": shift_report.confirmation_date,
				"user": shift_report.confirmed_by,
				"status": "Confirmed"
			})

		return {
			"success": True,
			"data": {
				"current_status": shift_report.verification_status,
				"history": history
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Verification History Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def bulk_verify_shift_reports(shift_report_ids, notes=None):
	"""
	Bulk verify multiple shift reports

	Args:
		shift_report_ids (list): List of shift report IDs
		notes (str): Optional verification notes

	Returns:
		dict: Bulk verification result
	"""
	try:
		if not shift_report_ids or not isinstance(shift_report_ids, list):
			frappe.throw(_("Shift report IDs list is required"))

		results = []
		success_count = 0
		error_count = 0

		for shift_report_id in shift_report_ids:
			try:
				result = verify_shift_report(shift_report_id, notes)
				if result["success"]:
					success_count += 1
				else:
					error_count += 1
				results.append({
					"shift_report_id": shift_report_id,
					"success": result["success"],
					"message": result["message"]
				})
			except Exception as e:
				error_count += 1
				results.append({
					"shift_report_id": shift_report_id,
					"success": False,
					"message": str(e)
				})

		return {
			"success": True,
			"message": _("Bulk verification completed: {0} success, {1} errors").format(success_count, error_count),
			"data": {
				"total_processed": len(shift_report_ids),
				"success_count": success_count,
				"error_count": error_count,
				"results": results
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Bulk Verify Shift Reports Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_pending_verifications():
	"""
	Get shift reports pending verification

	Returns:
		dict: List of pending shift reports
	"""
	try:
		# Get shift reports that need verification
		pending_reports = frappe.get_all(
			"POS Shift Report",
			filters={
				"verification_status": "Pending",
				"status": "Open",
				"docstatus": 0
			},
			fields=[
				"name", "shift_report_id", "pos_opening_shift",
				"opening_date", "opened_by", "total_sales",
				"creation", "modified"
			],
			order_by="creation desc"
		)

		return {
			"success": True,
			"data": pending_reports,
			"count": len(pending_reports)
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Pending Verifications Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_verification_summary():
	"""
	Get verification status summary

	Returns:
		dict: Verification summary statistics
	"""
	try:
		# Count by verification status
		status_counts = frappe.db.sql("""
			SELECT verification_status, COUNT(*) as count
			FROM `tabPOS Shift Report`
			WHERE docstatus = 0
			GROUP BY verification_status
		""", as_dict=True)

		# Count by status
		report_status_counts = frappe.db.sql("""
			SELECT status, COUNT(*) as count
			FROM `tabPOS Shift Report`
			WHERE docstatus = 0
			GROUP BY status
		""", as_dict=True)

		# Recent verifications (last 7 days)
		recent_verifications = frappe.db.sql("""
			SELECT COUNT(*) as count
			FROM `tabPOS Shift Report`
			WHERE verification_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
			AND verification_status IN ('Verified', 'Confirmed')
		""", as_dict=True)

		return {
			"success": True,
			"data": {
				"verification_status": {item["verification_status"]: item["count"] for item in status_counts},
				"report_status": {item["status"]: item["count"] for item in report_status_counts},
				"recent_verifications": recent_verifications[0]["count"] if recent_verifications else 0
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Verification Summary Error")
		return {
			"success": False,
			"message": str(e)
		}