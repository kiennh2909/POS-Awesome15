# -*- coding: utf-8 -*-
# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("shift_verification")


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
		log.info(f"[SHIFT_VERIFICATION] 🎯 START - Shift Report ID: {shift_report_id}")

		# ✅ PERMISSION CHECKS
		if not frappe.has_permission("POS Shift Report", "write"):
			log.error(f"[SHIFT_VERIFICATION] ❌ PERMISSION DENIED - User: {frappe.session.user}")
			return {
				"success": False,
				"message": _("Not permitted to verify shift reports")
			}

		# ✅ VALIDATE INPUT
		if not shift_report_id:
			log.error("[SHIFT_VERIFICATION] ❌ INVALID INPUT - No shift_report_id provided")
			return {
				"success": False,
				"message": _("Shift report ID is required")
			}

		# ✅ FIND SHIFT REPORT
		shift_report = None
		try:
			# Try to find by name first
			if frappe.db.exists("POS Shift Report", shift_report_id):
				shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
			else:
				# Try to find by shift_report_id field
				shift_reports = frappe.get_all("POS Shift Report",
					filters={"shift_report_id": shift_report_id},
					limit=1
				)
				if shift_reports:
					shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)
		except Exception as e:
			log.error(f"[SHIFT_VERIFICATION] ❌ DATABASE ERROR - Could not find shift report: {str(e)}")
			return {
				"success": False,
				"message": _("Shift report not found")
			}

		if not shift_report:
			log.error(f"[SHIFT_VERIFICATION] ❌ NOT FOUND - Shift report {shift_report_id} not found")
			return {
				"success": False,
				"message": _("Shift report not found")
			}

		# ✅ CHECK CURRENT VERIFICATION STATUS
		current_status = getattr(shift_report, 'verification_status', 'Pending')
		log.info(f"[SHIFT_VERIFICATION] 📊 CURRENT STATUS - {current_status}")

		if current_status in ['Verified', 'Confirmed']:
			log.warning(f"[SHIFT_VERIFICATION] ⚠️ ALREADY VERIFIED - Status: {current_status}")
			return {
				"success": False,
				"message": _("Shift report is already verified")
			}

		# ✅ VALIDATE SHIFT REPORT DATA
		validation_result = _validate_shift_report_data(shift_report)
		if not validation_result["valid"]:
			log.error(f"[SHIFT_VERIFICATION] ❌ VALIDATION FAILED - {validation_result['message']}")
			return {
				"success": False,
				"message": validation_result["message"]
			}

		# ✅ UPDATE VERIFICATION STATUS
		try:
			shift_report.verification_status = "Verified"
			shift_report.verified_by = frappe.session.user
			shift_report.verified_at = frappe.utils.now()
			shift_report.save(ignore_permissions=True)

			log.info(f"[SHIFT_VERIFICATION] ✅ STATUS UPDATED - Verified by {frappe.session.user}")

		except Exception as e:
			log.error(f"[SHIFT_VERIFICATION] ❌ SAVE ERROR - Could not update verification status: {str(e)}")
			return {
				"success": False,
				"message": _("Failed to update verification status")
			}

		# ✅ LOG VERIFICATION ACTIVITY
		try:
			_log_verification_activity(shift_report)
		except Exception as e:
			log.warning(f"[SHIFT_VERIFICATION] ⚠️ LOG ERROR - Could not log activity: {str(e)}")
			# Don't fail the verification if logging fails

		log.info(f"[SHIFT_VERIFICATION] 🎉 COMPLETED - Shift Report {shift_report_id} verified successfully")

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
		log.error(f"[SHIFT_VERIFICATION] 💥 UNEXPECTED ERROR - {str(e)}")
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
		log.info("[SHIFT_VERIFICATION] 🔍 VALIDATING SHIFT REPORT DATA")

		# ✅ CHECK IF SHIFT HAS INVOICES
		invoice_count = getattr(shift_report, 'invoice_count', 0)
		if invoice_count == 0:
			return {
				"valid": False,
				"message": _("Cannot verify shift report with no invoices")
			}

		# ✅ CHECK IF SHIFT IS CLOSED
		if getattr(shift_report, 'status', '') == 'Closed':
			return {
				"valid": False,
				"message": _("Cannot verify a closed shift report")
			}

		# ✅ CHECK PAYMENT SUMMARY CONSISTENCY
		if hasattr(shift_report, 'payment_summaries'):
			total_calculated = 0
			for summary in shift_report.payment_summaries:
				total_calculated += getattr(summary, 'closing_amount', 0)

			total_expected = getattr(shift_report, 'total_expected_closing', 0)
			difference = abs(total_calculated - total_expected)

			# Allow small rounding differences (0.01)
			if difference > 0.01:
				log.warning(f"[SHIFT_VERIFICATION] ⚠️ PAYMENT MISMATCH - Calculated: {total_calculated}, Expected: {total_expected}, Difference: {difference}")
				# Don't fail validation for payment mismatches, just log warning

		log.info("[SHIFT_VERIFICATION] ✅ VALIDATION PASSED")
		return {"valid": True}

	except Exception as e:
		log.error(f"[SHIFT_VERIFICATION] ❌ VALIDATION ERROR - {str(e)}")
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

		log.info(f"[SHIFT_VERIFICATION] 📝 ACTIVITY LOGGED - {activity_doc.name}")

	except Exception as e:
		log.warning(f"[SHIFT_VERIFICATION] ⚠️ ACTIVITY LOG ERROR - {str(e)}")
		# Don't raise error if activity logging fails


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

		# ✅ PERMISSION CHECK
		if not frappe.has_permission("POS Shift Report", "read"):
			return {
				"success": False,
				"message": _("Not permitted to view shift report verification status")
			}

		# ✅ FIND SHIFT REPORT
		shift_report = None
		try:
			if frappe.db.exists("POS Shift Report", shift_report_id):
				shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
			else:
				shift_reports = frappe.get_all("POS Shift Report",
					filters={"shift_report_id": shift_report_id},
					limit=1
				)
				if shift_reports:
					shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)
		except Exception as e:
			log.error(f"[SHIFT_VERIFICATION] ❌ DATABASE ERROR - {str(e)}")
			return {
				"success": False,
				"message": _("Error retrieving shift report")
			}

		if not shift_report:
			return {
				"success": False,
				"message": _("Shift report not found")
			}

		# ✅ RETURN VERIFICATION STATUS
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
		# ✅ CHECK PERMISSIONS
		if not frappe.has_permission("POS Shift Report", "write"):
			return False

		# ✅ CHECK IF ALREADY VERIFIED
		current_status = getattr(shift_report, 'verification_status', 'Pending')
		if current_status in ['Verified', 'Confirmed']:
			return False

		# ✅ CHECK IF USER IS SHIFT OWNER OR HAS ADMIN ROLE
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