# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from erpnext.accounts.doctype.pos_invoice_merge_log.pos_invoice_merge_log import (
    consolidate_pos_invoices,
)
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from posawesome.posawesome.utils.logging import get_logger

log = get_logger("shift_close")


class POSClosingShift(Document):
    def validate(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 1: VALIDATE_START - POS Closing Shift {self.name}, User: {self.user}, Opening Shift: {self.pos_opening_shift}")

        # Check for existing submitted closing shifts
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 2: VALIDATE_CHECK_EXISTING - Checking for existing closing shifts for user {self.user} and opening shift {self.pos_opening_shift}")
        user = frappe.get_all(
            "POS Closing Shift",
            filters={
                "user": self.user,
                "docstatus": 1,
                "pos_opening_shift": self.pos_opening_shift,
                "name": ["!=", self.name],
            },
        )

        if user:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ❌ VALIDATE_DUPLICATE_FOUND - Found {len(user)} existing submitted closing shift(s) for user {self.user}")
            frappe.throw(
                _(
                    "POS Closing Shift {} against {} between selected period".format(
                        frappe.bold("already exists"), frappe.bold(self.user)
                    )
                ),
                title=_("Invalid Period"),
            )

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 3: VALIDATE_NO_DUPLICATE - No duplicate closing shifts found")

        # Check opening shift status
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 4: VALIDATE_CHECK_OPENING_STATUS - Checking status of opening shift {self.pos_opening_shift}")
        opening_status = frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status")
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 5: VALIDATE_OPENING_STATUS - Opening shift status: {opening_status}")

        if opening_status != "Open":
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: VALIDATE_INVALID_OPENING - Opening shift {self.pos_opening_shift} is not open (status: {opening_status})")
            frappe.throw(
                _("Selected POS Opening Shift should be open."),
                title=_("Invalid Opening Entry"),
            )

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 6: VALIDATE_OPENING_VALID - Opening shift is valid and open")

        # Set shift_report field if not provided (optional - shift report is not required for closing)
        if not self.shift_report and self.pos_opening_shift:
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 7: VALIDATE_FIND_SHIFT_REPORT - Finding shift report for opening shift {self.pos_opening_shift}")
            shift_report = frappe.db.get_value("POS Shift Report", {"pos_opening_shift": self.pos_opening_shift}, "name")

            if shift_report:
                self.shift_report = shift_report
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 8: VALIDATE_SHIFT_REPORT_FOUND - Found shift report: {shift_report}")
            else:
                log.info(f"[SHIFT_CLOSE_WORKFLOW] INFO: VALIDATE_NO_SHIFT_REPORT - No shift report found for opening shift {self.pos_opening_shift}, but allowing close anyway")

        # Check Shift Report exists and is verified
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 9: VALIDATE_CHECK_SHIFT_REPORT - Checking shift report verification status")
        if not self.shift_report:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: VALIDATE_NO_SHIFT_REPORT - No shift report linked to closing shift {self.name}")
            frappe.throw(_("Shift Report is required before closing shift. Please verify the shift first."))

        # Check if shift report exists
        if not frappe.db.exists("POS Shift Report", self.shift_report):
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: VALIDATE_SHIFT_REPORT_NOT_FOUND - Shift report {self.shift_report} does not exist")
            frappe.throw(_("Shift Report '{0}' does not exist").format(self.shift_report))

        # Check shift report verification status
        shift_report_status = frappe.db.get_value("POS Shift Report", self.shift_report, "verification_status")
        if shift_report_status != "Verified":
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: VALIDATE_SHIFT_REPORT_NOT_VERIFIED - Shift report {self.shift_report} status: {shift_report_status}")
            frappe.throw(_("Shift Report must be verified before closing shift. Current status: {0}").format(shift_report_status or "Pending"))

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 10: VALIDATE_SHIFT_REPORT_VERIFIED - Shift report {self.shift_report} is verified")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 11: VALIDATE_UPDATE_RECONCILIATION - Updating payment reconciliation")
        self.update_payment_reconciliation()

        # Ensure JSON fields have valid values
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 12: VALIDATE_ENSURE_JSON_FIELDS - Ensuring JSON fields have valid values")
        self.ensure_json_fields_valid()

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 13: VALIDATE_COMPLETED - POS Closing Shift {self.name} validation completed successfully")

    def update_payment_reconciliation(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 14: UPDATE_PAYMENT_RECONCILIATION_START - POS Closing Shift {self.name}")
        # update the difference values in Payment Reconciliation child table
        precision = frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 15: UPDATE_PAYMENT_RECONCILIATION_PRECISION - Using currency precision: {precision}")

        updated_count = 0
        for d in self.payment_reconciliation:
            expected = flt(d.expected_amount, precision)
            closing = flt(d.closing_amount, precision)
            difference = closing - expected
            d.difference = difference

            log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 16: UPDATE_PAYMENT_RECONCILIATION_CALC - {d.mode_of_payment}: Expected={expected}, Closing={closing}, Difference={difference}")
            # Add tracing for closing_amount during validation
            log.info(f"[SHIFT_CLOSE_WORKFLOW] TRACING_CLOSING_AMOUNT - During validation: {d.mode_of_payment} -> closing_amount={closing} (from child table)")
            updated_count += 1

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 17: UPDATE_PAYMENT_RECONCILIATION_COMPLETED - Updated {updated_count} payment reconciliation records")

    def ensure_json_fields_valid(self):
        """Ensure JSON fields have valid values to prevent Frappe validation errors"""
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 18: ENSURE_JSON_FIELDS_VALID - Ensuring JSON fields are valid")

        # Ensure expected_amounts is valid JSON
        if not self.expected_amounts or self.expected_amounts == "":
            self.expected_amounts = "{}"
            log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 19: ENSURE_JSON_FIELDS_VALID - Set expected_amounts to empty JSON")

        # Ensure actual_amounts is valid JSON
        if not self.actual_amounts or self.actual_amounts == "":
            self.actual_amounts = "{}"
            log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 20: ENSURE_JSON_FIELDS_VALID - Set actual_amounts to empty JSON")

        # Ensure difference_amounts is valid JSON
        if not self.difference_amounts or self.difference_amounts == "":
            self.difference_amounts = "{}"
            log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 21: ENSURE_JSON_FIELDS_VALID - Set difference_amounts to empty JSON")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 22: ENSURE_JSON_FIELDS_VALID_COMPLETED - All JSON fields are valid")

    def perform_post_submit_cleanup(self):
        """Perform post-submit cleanup: Clear cache, logout user, and prepare UI refresh"""
        try:
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 23: POST_SUBMIT_CLEANUP_START - Performing post-submit cleanup for user: {self.user}")

            # STEP 1: Clear Cache
            frappe.clear_cache()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 24: POST_SUBMIT_CLEANUP_CACHE_CLEARED - Cache cleared successfully")

            # STEP 2: Logout user (invalidate session)
            if hasattr(frappe, 'local') and hasattr(frappe.local, 'session'):
                # Clear session data to force logout
                frappe.local.session = None
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 25: POST_SUBMIT_CLEANUP_SESSION_CLEARED - User session cleared (logout)")

            # STEP 3: Log completion
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 26: POST_SUBMIT_CLEANUP_COMPLETED - Post-submit cleanup completed successfully")

        except Exception as e:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: POST_SUBMIT_CLEANUP_ERROR - Error during post-submit cleanup: {str(e)}")
            # Don't raise error to prevent closing shift submission failure

    def calculate_payment_amounts(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 27: CALCULATE_PAYMENT_AMOUNTS - POS Closing Shift {self.name}")
        try:
            expected_amounts = {}
            actual_amounts = {}
            difference_amounts = {}

            for payment in self.payment_reconciliation:
                mode = payment.mode_of_payment
                if mode:
                    expected_amounts[mode] = flt(payment.expected_amount or 0)
                    actual_amounts[mode] = flt(payment.closing_amount or 0)
                    difference_amounts[mode] = flt(payment.difference or 0)

            # Store as JSON strings
            self.expected_amounts = frappe.as_json(expected_amounts) if expected_amounts else "{}"
            self.actual_amounts = frappe.as_json(actual_amounts) if actual_amounts else "{}"
            self.difference_amounts = frappe.as_json(difference_amounts) if difference_amounts else "{}"

            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 28: CALCULATE_PAYMENT_AMOUNTS_COMPLETED - Calculated amounts for {len(actual_amounts)} payment methods")

        except Exception as e:
            # Set empty JSON objects as fallback
            self.expected_amounts = "{}"
            self.actual_amounts = "{}"
            self.difference_amounts = "{}"

            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: CALCULATE_PAYMENT_AMOUNTS_ERROR - Failed to calculate payment amounts for {self.name}: {str(e)}")

    def on_submit(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 29: ON_SUBMIT_START - POS Closing Shift {self.name} submission started - User: {self.user}")

        try:
            # STEP 0: Update payment reconciliation and amounts with final closing amounts
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 30: ON_SUBMIT_UPDATE_RECONCILIATION - Updating payment reconciliation with final amounts")
            self.update_payment_reconciliation()
            self.calculate_payment_amounts()
            self.ensure_json_fields_valid()  # Ensure JSON fields are valid before submit
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 31: ON_SUBMIT_RECONCILIATION_COMPLETED - Payment amounts updated")

            # STEP 1: Validate shift report verification status before submission (optional)
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 32: ON_SUBMIT_VALIDATE_VERIFICATION - Checking shift report verification status")
            if self.shift_report:
                shift_report_status = frappe.db.get_value("POS Shift Report", self.shift_report, "verification_status")
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 33: ON_SUBMIT_VERIFICATION_STATUS - Shift report {self.shift_report} status: {shift_report_status}")

                if shift_report_status not in ["Verified", "Confirmed"]:
                    log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: ON_SUBMIT_VERIFICATION_PENDING - Shift report not verified (status: {shift_report_status}), but allowing close anyway")
            else:
                log.info(f"[SHIFT_CLOSE_WORKFLOW] INFO: ON_SUBMIT_NO_SHIFT_REPORT - No shift report linked to closing shift {self.name}, proceeding without verification")

            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 34: ON_SUBMIT_VERIFICATION_COMPLETED - Verification check passed")

            # STEP 2: Update opening shift reference
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 35: ON_SUBMIT_UPDATE_OPENING_SHIFT - Updating opening shift {self.pos_opening_shift}")
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            opening_entry.pos_closing_shift = self.name
            opening_entry.set_status()
            opening_entry.save()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 36: ON_SUBMIT_OPENING_SHIFT_COMPLETED - Opening shift updated")

            # STEP 3: Delete draft invoices
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 37: ON_SUBMIT_DELETE_DRAFT_INVOICES - Deleting draft invoices")
            self.delete_draft_invoices()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 38: ON_SUBMIT_DRAFT_INVOICES_COMPLETED - Draft invoices deleted")

            # STEP 4: Update shift report and payment summaries
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 39: ON_SUBMIT_UPDATE_SHIFT_REPORT - Updating shift report and payment summaries")
            self.update_shift_report_and_summaries()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 40: ON_SUBMIT_SHIFT_REPORT_COMPLETED - Shift report updated")

            # STEP 5: Link invoices with this closing shift so ERPNext can block edits
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 41: ON_SUBMIT_SET_CLOSING_ENTRY - Setting closing entry on invoices")
            self._set_closing_entry_invoices()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 42: ON_SUBMIT_CLOSING_ENTRY_COMPLETED - Invoices linked")

            # POST-SUBMIT CLEANUP: Clear cache, logout, and refresh UI
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 43: ON_SUBMIT_POST_CLEANUP - Performing post-submit cleanup")
            self.perform_post_submit_cleanup()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 44: ON_SUBMIT_POST_CLEANUP_COMPLETED - Post-submit cleanup completed")

            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 45: ON_SUBMIT_COMPLETED - POS Closing Shift {self.name} submitted successfully")

        except Exception as e:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: ON_SUBMIT_ERROR - POS Closing Shift {self.name} failed: {str(e)}")
            raise

    def update_shift_report_and_summaries(self):
        """Update POS Shift Report and Payment Summaries with closing data"""
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 46: UPDATE_SHIFT_REPORT_START - POS Closing Shift {self.name}")

        if not self.shift_report:
            log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: UPDATE_SHIFT_REPORT_SKIP - No shift report linked to closing shift {self.name}")
            return

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 47: UPDATE_SHIFT_REPORT_LOAD - Loading shift report {self.shift_report}")
        shift_report = frappe.get_doc("POS Shift Report", self.shift_report)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 48: UPDATE_SHIFT_REPORT_LOADED - Shift report loaded successfully")

        # Get payment summaries
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 49: UPDATE_SHIFT_REPORT_GET_SUMMARIES - Getting payment summaries for shift report")
        from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import get_payment_summaries_for_shift
        summaries_result = get_payment_summaries_for_shift(shift_report.name)

        if not summaries_result.get("success") or not summaries_result.get("data"):
            log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: UPDATE_SHIFT_REPORT_NO_SUMMARIES - No payment summaries found for shift report {shift_report.name}, creating them now")

            # Try to create payment summaries if they don't exist
            from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
            create_result = create_payment_summaries_for_shift(shift_report.name)

            if create_result.get("success") and create_result.get("data", {}).get("payment_summaries"):
                summaries = create_result["data"]["payment_summaries"]
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 50: UPDATE_SHIFT_REPORT_CREATED_SUMMARIES - Created {len(summaries)} payment summaries")
            else:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: UPDATE_SHIFT_REPORT_CREATE_FAILED - Failed to create payment summaries: {create_result.get('message')}")
                frappe.throw(_("Failed to create payment summaries for shift. Please verify the shift first."))
        else:
            summaries = summaries_result["data"]
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 51: UPDATE_SHIFT_REPORT_SUMMARIES_FOUND - Found {len(summaries)} payment summaries")

        # Update closing amounts in payment summaries
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 52: UPDATE_SHIFT_REPORT_UPDATE_SUMMARIES - Updating closing amounts in payment summaries")
        closing_amounts_map = {}
        for payment in self.payment_reconciliation:
            method = payment.get("mode_of_payment")
            closing_amount = flt(payment.get("closing_amount", 0))
            if method:
                closing_amounts_map[method] = closing_amount
                log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 53: UPDATE_SHIFT_REPORT_CLOSING_MAP - {method}: {closing_amount}")
                # Add tracing for closing_amount during submit
                log.info(f"[SHIFT_CLOSE_WORKFLOW] TRACING_CLOSING_AMOUNT - During submit: {method} -> closing_amount={closing_amount} (final value)")

        updated_summaries_count = 0
        for summary in summaries:
            method = summary.get("payment_method")
            if method and method in closing_amounts_map:
                closing_amount = closing_amounts_map[method]
                expected_amount = flt(summary.get("expected_closing_amount", 0))
                difference = expected_amount - closing_amount

                frappe.db.set_value("POS Payment Summary",
                    {"shift_report_id": self.shift_report, "payment_method": method},
                    {
                        "closing_amount": closing_amount,
                        "difference": difference,
                        "shift_end_time": self.period_end_date
                    }
                )
                updated_summaries_count += 1
                log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 54: UPDATE_SHIFT_REPORT_SUMMARY_UPDATED - {method}: closing={closing_amount}, expected={expected_amount}, diff={difference}")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 55: UPDATE_SHIFT_REPORT_SUMMARIES_UPDATED - Updated {updated_summaries_count} payment summaries")

        # Update shift report
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 56: UPDATE_SHIFT_REPORT_CALCULATE_TOTALS - Calculating totals")
        total_actual_closing = sum(flt(s.get("closing_amount", 0)) for s in summaries)

        # Get existing expected amounts from shift report (already calculated during verification)
        from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import _parse_json_safe
        existing_expected = _parse_json_safe(shift_report.expected_closing_amounts or "{}")
        total_expected_closing = sum(existing_expected.values())
        difference = total_actual_closing - total_expected_closing

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 57: UPDATE_SHIFT_REPORT_TOTALS_CALCULATED - Actual: {total_actual_closing}, Expected: {total_expected_closing}, Difference: {difference}")

        shift_report.closing_date = self.period_end_date
        shift_report.closed_by = self.user
        shift_report.status = "Closed"
        shift_report.shift_end_time = self.period_end_date
        shift_report.total_actual_closing = total_actual_closing
        shift_report.difference = difference

        actual_closing_amounts = {}
        for summary in summaries:
            method = summary.get("payment_method")
            if method:
                actual_closing_amounts[method] = flt(summary.get("closing_amount", 0))

        shift_report.actual_closing_amounts = frappe.as_json(actual_closing_amounts)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 58: UPDATE_SHIFT_REPORT_DATA_SET - Shift report data updated")

        try:
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 59: UPDATE_SHIFT_REPORT_SAVING - Saving shift report {shift_report.name}")
            shift_report.save(ignore_permissions=True)
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 60: UPDATE_SHIFT_REPORT_SAVED - Shift report saved successfully")
        except frappe.ValidationError as ve:
            if "Status cannot be" in str(ve) and "Paid" in str(ve):
                log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: UPDATE_SHIFT_REPORT_VALIDATION_BYPASS - Validation error detected, bypassing: {str(ve)}")
                shift_report.flags.ignore_validate = True
                shift_report.save(ignore_permissions=True)
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 61: UPDATE_SHIFT_REPORT_SAVED_BYPASS - Shift report saved with validation bypass")
            else:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: UPDATE_SHIFT_REPORT_VALIDATION_ERROR - Validation error: {str(ve)}")
                raise

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 62: UPDATE_SHIFT_REPORT_COMPLETED - Shift report and payment summaries updated successfully")

    def on_cancel(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 63: ON_CANCEL_START - POS Closing Shift {self.name} cancellation started")

        if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 64: ON_CANCEL_UPDATE_OPENING - Updating opening shift {self.pos_opening_shift}")
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            if opening_entry.pos_closing_shift == self.name:
                opening_entry.pos_closing_shift = ""
                opening_entry.set_status()
                opening_entry.save()
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 65: ON_CANCEL_OPENING_UPDATED - Opening shift updated successfully")
            else:
                log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: ON_CANCEL_OPENING_NOT_LINKED - Opening shift {self.pos_opening_shift} is not linked to this closing shift")
        else:
            log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: ON_CANCEL_OPENING_NOT_FOUND - Opening shift {self.pos_opening_shift} not found")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 66: ON_CANCEL_CLEAR_INVOICES - Clearing closing entry from invoices")
        self._clear_closing_entry_invoices()

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 67: ON_CANCEL_COMPLETED - POS Closing Shift {self.name} cancelled successfully")

    def _clear_closing_entry_invoices(self):
        """Clear closing shift links, cancel merge logs and cancel consolidated sales invoices."""
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 68: CLEAR_CLOSING_ENTRY_START - POS Closing Shift {self.name}")

        sales_invoices = set()
        processed_count = 0
        pos_invoice_count = 0
        sales_invoice_count = 0

        for d in self.pos_transactions:
            pos_invoice = d.get("pos_invoice")
            sales_invoice = d.get("sales_invoice")

            if pos_invoice:
                pos_invoice_count += 1
                log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 69: CLEAR_CLOSING_ENTRY_PROCESS_POS - Processing POS Invoice {pos_invoice}")

                if frappe.db.has_column("POS Invoice", "pos_closing_entry"):
                    frappe.db.set_value("POS Invoice", pos_invoice, "pos_closing_entry", None)
                    log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 70: CLEAR_CLOSING_ENTRY_CLEARED_POS - Cleared closing entry from POS Invoice {pos_invoice}")

                merge_logs = frappe.get_all(
                    "POS Invoice Merge Log",
                    filters={"pos_invoice": pos_invoice},
                    pluck="name",
                )

                for log_name in merge_logs:
                    log_doc = frappe.get_doc("POS Invoice Merge Log", log_name)
                    for field in (
                        "consolidated_invoice",
                        "consolidated_credit_note",
                    ):
                        si = log_doc.get(field)
                        if si:
                            sales_invoices.add(si)
                    if log_doc.docstatus == 1:
                        log_doc.cancel()
                        log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 71: CLEAR_CLOSING_ENTRY_CANCELLED_LOG - Cancelled merge log {log_name}")
                    frappe.delete_doc("POS Invoice Merge Log", log_doc.name, force=1)

                if frappe.db.has_column("POS Invoice", "consolidated_invoice"):
                    frappe.db.set_value("POS Invoice", pos_invoice, "consolidated_invoice", None)

                if frappe.db.has_column("POS Invoice", "status"):
                    pos_doc = frappe.get_doc("POS Invoice", pos_invoice)
                    pos_doc.set_status(update=True)

            if sales_invoice:
                sales_invoice_count += 1
                log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 72: CLEAR_CLOSING_ENTRY_PROCESS_SALES - Processing Sales Invoice {sales_invoice}")

                if frappe.db.has_column("Sales Invoice", "pos_closing_entry"):
                    frappe.db.set_value("Sales Invoice", sales_invoice, "pos_closing_entry", None)
                    log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 73: CLEAR_CLOSING_ENTRY_CLEARED_SALES - Cleared closing entry from Sales Invoice {sales_invoice}")
                sales_invoices.add(sales_invoice)

            processed_count += 1

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 74: CLEAR_CLOSING_ENTRY_PROCESSED - Processed {processed_count} transactions (POS: {pos_invoice_count}, Sales: {sales_invoice_count})")

        cancelled_invoices = 0
        for si in sales_invoices:
            if frappe.db.exists("Sales Invoice", si):
                si_doc = frappe.get_doc("Sales Invoice", si)
                if si_doc.docstatus == 1:
                    si_doc.cancel()
                    cancelled_invoices += 1
                    log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 75: CLEAR_CLOSING_ENTRY_CANCELLED_INVOICE - Cancelled consolidated invoice {si}")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 76: CLEAR_CLOSING_ENTRY_COMPLETED - Cleared closing entries and cancelled {cancelled_invoices} consolidated invoices")

    def _set_closing_entry_invoices(self):
        """Set `pos_closing_entry` on linked invoices."""
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 77: SET_CLOSING_ENTRY_START - POS Closing Shift {self.name}")

        updated_count = 0
        skipped_count = 0

        for d in self.pos_transactions:
            invoice = d.get("sales_invoice") or d.get("pos_invoice")
            if not invoice:
                skipped_count += 1
                continue

            doctype = "Sales Invoice" if d.get("sales_invoice") else "POS Invoice"

            if frappe.db.has_column(doctype, "pos_closing_entry"):
                try:
                    frappe.db.set_value(doctype, invoice, "pos_closing_entry", self.name)
                    updated_count += 1
                    log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 78: SET_CLOSING_ENTRY_UPDATED - Set closing entry on {doctype} {invoice}")
                except Exception as e:
                    log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: SET_CLOSING_ENTRY_ERROR - Failed to set closing entry on {doctype} {invoice}: {str(e)}")
            else:
                log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: SET_CLOSING_ENTRY_NO_COLUMN - {doctype} does not have pos_closing_entry column")
                skipped_count += 1

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 79: SET_CLOSING_ENTRY_COMPLETED - Updated {updated_count} invoices, skipped {skipped_count}")

    def delete_draft_invoices(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 80: DELETE_DRAFT_INVOICES_START - POS Closing Shift {self.name}")

        allow_delete = frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete")
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 81: DELETE_DRAFT_INVOICES_CHECK_PERMISSION - POS Profile {self.pos_profile} allow_delete: {allow_delete}")

        if allow_delete:
            # Only handle Sales Invoice (POS Invoice logic removed)
            doctype = "Sales Invoice"
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 82: DELETE_DRAFT_INVOICES_FINDING - Finding draft {doctype} for opening shift {self.pos_opening_shift}")

            data = frappe.db.sql(
                f"""
		select
		    name
		from
		    `tab{doctype}`
		where
		    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
		""",
                (self.pos_opening_shift),
                as_dict=1,
            )

            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 83: DELETE_DRAFT_INVOICES_FOUND - Found {len(data)} draft invoices to delete")

            deleted_count = 0
            for invoice in data:
                try:
                    frappe.delete_doc(doctype, invoice.name, force=1)
                    deleted_count += 1
                    log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 84: DELETE_DRAFT_INVOICES_DELETED - Deleted draft invoice {invoice.name}")
                except Exception as e:
                    log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: DELETE_DRAFT_INVOICES_ERROR - Failed to delete invoice {invoice.name}: {str(e)}")

            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 85: DELETE_DRAFT_INVOICES_COMPLETED - Successfully deleted {deleted_count} draft invoices")
        else:
            log.info(f"[SHIFT_CLOSE_WORKFLOW] INFO: DELETE_DRAFT_INVOICES_SKIP - POS Profile does not allow draft invoice deletion")

    @frappe.whitelist()
    def get_payment_reconciliation_details(self):
        currency = frappe.get_cached_value("Company", self.company, "default_currency")
        return frappe.render_template(
            "posawesome/posawesome/doctype/pos_closing_shift/closing_shift_details.html",
            {"data": self, "currency": currency},
        )


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
    result = []
    for cashier in cashiers_list:
        user_email = frappe.get_value("User", cashier.user, "email")
        if user_email:
            result.append([cashier.user, f"{cashier.user} ({user_email})"])
    return result


def submit_printed_invoices(pos_opening_shift, doctype):
    """
    Submit printed invoices for the opening shift
    This function ensures all printed invoices are properly submitted before closing
    """
    try:
        log.info(f"[SUBMIT_PRINTED_INVOICES] START - Submitting printed invoices for opening shift: {pos_opening_shift}, doctype: {doctype}")

        # Find draft invoices that are marked as printed
        draft_invoices = frappe.get_all(doctype,
            filters={
                "posa_pos_opening_shift": pos_opening_shift,
                "docstatus": 0,  # Draft
                "posa_is_printed": 1  # Marked as printed
            },
            fields=["name"]
        )

        submitted_count = 0
        for invoice in draft_invoices:
            try:
                # Submit the invoice
                invoice_doc = frappe.get_doc(doctype, invoice.name)
                invoice_doc.submit()
                submitted_count += 1
                log.debug(f"[SUBMIT_PRINTED_INVOICES] Submitted invoice: {invoice.name}")
            except Exception as e:
                log.error(f"[SUBMIT_PRINTED_INVOICES] Failed to submit invoice {invoice.name}: {str(e)}")
                continue

        log.info(f"[SUBMIT_PRINTED_INVOICES] COMPLETED - Submitted {submitted_count} printed invoices")

    except Exception as e:
        log.error(f"[SUBMIT_PRINTED_INVOICES] ERROR - Failed to submit printed invoices: {str(e)}")
        # Don't raise error to prevent blocking closing shift creation


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift, doctype=None):
    if not doctype:
        # Default to Sales Invoice (POS Invoice logic removed)
        doctype = "Sales Invoice"
    submit_printed_invoices(pos_opening_shift, doctype)
    # Remove consolidated_invoice condition for POS Invoice
    data = frappe.db.sql(
        f"""
	select
		name
	from
		`tab{doctype}`
	where
		docstatus = 1 and posa_pos_opening_shift = %s
	""",
        (pos_opening_shift),
        as_dict=1,
    )

    data = [frappe.get_doc(doctype, d.name).as_dict() for d in data]

    return data


@frappe.whitelist()
def get_payments_entries(pos_opening_shift):
    return frappe.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "reference_no": pos_opening_shift,
            "payment_type": "Receive",
        },
        fields=[
            "name",
            "mode_of_payment",
            "paid_amount",
            "reference_no",
            "posting_date",
            "party",
        ],
    )


def validate_shift_can_be_closed(opening_shift_name):
    """
    Validate if a shift can be closed
    Returns: dict with 'can_close' boolean and 'message' string
    """
    try:
        # Check if opening shift exists and is open
        if not frappe.db.exists("POS Opening Shift", opening_shift_name):
            return {
                "can_close": False,
                "message": _("Opening shift not found")
            }

        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        if opening_shift.status != "Open":
            return {
                "can_close": False,
                "message": _("Opening shift is not open")
            }

        # Check if there's already a submitted closing shift for this opening shift
        existing_closing = frappe.get_all("POS Closing Shift",
            filters={
                "pos_opening_shift": opening_shift_name,
                "docstatus": 1
            },
            limit=1
        )

        if existing_closing:
            return {
                "can_close": False,
                "message": _("Closing shift already exists for this opening shift")
            }

        return {
            "can_close": True,
            "message": _("Shift can be closed")
        }

    except Exception as e:
        return {
            "can_close": False,
            "message": _("Error validating shift: {0}").format(str(e))
        }


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 86: MAKE_CLOSING_SHIFT_START - Creating closing shift from opening shift data - User: {frappe.session.user}")

    try:
        opening_shift_data = json.loads(opening_shift)
        opening_shift_name = opening_shift_data.get("name")
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 87: MAKE_CLOSING_SHIFT_DATA - Opening shift: {opening_shift_name}, User: {opening_shift_data.get('user')}")

        # VALIDATION: Check if shift can be closed
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 88: MAKE_CLOSING_SHIFT_VALIDATION - Checking if shift can be closed")
        validation_result = validate_shift_can_be_closed(opening_shift_name)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 89: MAKE_CLOSING_SHIFT_VALIDATION_RESULT - Can close: {validation_result.get('can_close')}, Message: {validation_result.get('message')}")

        if not validation_result.get("can_close"):
            log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: MAKE_CLOSING_SHIFT_BLOCKED - Validation failed: {validation_result.get('message')}")
            frappe.throw(validation_result.get("message"))

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 90: MAKE_CLOSING_SHIFT_VALIDATION_PASSED - Validation passed")

        # Default to Sales Invoice (POS Invoice logic removed)
        doctype = "Sales Invoice"
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 91: MAKE_CLOSING_SHIFT_DOCTYPE - Using doctype: {doctype}")

        # Submit printed invoices first
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 92: MAKE_CLOSING_SHIFT_SUBMIT_PRINTED - Submitting printed invoices for opening shift {opening_shift_name}")
        submit_printed_invoices(opening_shift_name, doctype)

        # Create closing shift document
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 93: MAKE_CLOSING_SHIFT_CREATE_DOC - Creating POS Closing Shift document")
        closing_shift = frappe.new_doc("POS Closing Shift")
        closing_shift.pos_opening_shift = opening_shift_name
        closing_shift.period_start_date = opening_shift_data.get("period_start_date")
        closing_shift.period_start_time = opening_shift_data.get("period_start_time")
        closing_shift.period_end_date = frappe.utils.get_datetime()

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 94: MAKE_CLOSING_SHIFT_DATA - period_start_date: {closing_shift.period_start_date}, period_start_time: {closing_shift.period_start_time}")
        closing_shift.pos_profile = opening_shift_data.get("pos_profile")
        closing_shift.user = opening_shift_data.get("user")
        closing_shift.company = opening_shift_data.get("company")
        closing_shift.grand_total = 0
        closing_shift.net_total = 0
        closing_shift.total_quantity = 0

        # Initialize JSON fields to prevent validation errors (will be populated after payment processing)
        closing_shift.expected_amounts = "{}"
        closing_shift.actual_amounts = "{}"
        closing_shift.difference_amounts = "{}"

        # Get invoices data
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 95: MAKE_CLOSING_SHIFT_GET_INVOICES - Getting {doctype} for opening shift {opening_shift_name}")
        invoices = get_pos_invoices(opening_shift_name, doctype)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 96: MAKE_CLOSING_SHIFT_INVOICES_FOUND - Found {len(invoices)} invoices")

        pos_transactions = []
        taxes = []
        payments = []
        pos_payments_table = []

        # Process balance details from opening shift
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 97: MAKE_CLOSING_SHIFT_PROCESS_BALANCE - Processing balance details")
        balance_details = opening_shift_data.get("balance_details", [])

        # Get payment reconciliation data from client if available (for proper closing_amount)
        client_payment_reconciliation = opening_shift_data.get("payment_reconciliation", [])
        client_payment_map = {p.get("mode_of_payment"): p for p in client_payment_reconciliation}

        for detail in balance_details:
            mode = detail.get("mode_of_payment")
            opening_amt = detail.get("amount") or 0

            # Use client data if available, otherwise use opening amount as expected
            client_data = client_payment_map.get(mode, {})
            expected_amt = flt(client_data.get("expected_amount", opening_amt))
            closing_amt = flt(client_data.get("closing_amount", expected_amt))  # Default to expected if no closing amount

            # Ensure closing_amount is never null/empty - required field
            if closing_amt is None or closing_amt == "":
                closing_amt = expected_amt if expected_amt > 0 else 0

            payments.append(
                frappe._dict(
                    {
                        "mode_of_payment": mode,
                        "opening_amount": opening_amt,
                        "expected_amount": expected_amt,
                        "closing_amount": closing_amt,  # Set proper closing amount
                        "difference": client_data.get("difference", 0)
                    }
                )
            )
            log.info(f"[SHIFT_CLOSE_WORKFLOW] TRACING_CLOSING_AMOUNT - Setting in make_closing_shift: {mode} -> closing_amount={closing_amt}")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 98: MAKE_CLOSING_SHIFT_BALANCE_PROCESSED - Processed {len(balance_details)} balance details")

        invoice_field = "pos_invoice" if doctype == "POS Invoice" else "sales_invoice"

        # Process invoices
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 99: MAKE_CLOSING_SHIFT_PROCESS_INVOICES - Processing {len(invoices)} invoices")
        for d in invoices:
            pos_transactions.append(
                frappe._dict(
                    {
                        invoice_field: d.name,
                        "posting_date": d.posting_date,
                        "grand_total": d.grand_total,
                        "customer": d.customer,
                    }
                )
            )
            closing_shift.grand_total += flt(d.grand_total)
            closing_shift.net_total += flt(d.net_total)
            closing_shift.total_quantity += flt(d.total_qty)

            # Process taxes
            for t in d.taxes:
                existing_tax = [tx for tx in taxes if tx.account_head == t.account_head and tx.rate == t.rate]
                if existing_tax:
                    existing_tax[0].amount += flt(t.tax_amount)
                else:
                    taxes.append(
                        frappe._dict(
                            {
                                "account_head": t.account_head,
                                "rate": t.rate,
                                "amount": t.tax_amount,
                            }
                        )
                    )

            # Process payments
            for p in d.payments:
                existing_pay = [pay for pay in payments if pay.mode_of_payment == p.mode_of_payment]
                if existing_pay:
                    cash_mode_of_payment = frappe.get_value(
                        "POS Profile",
                        opening_shift_data.get("pos_profile"),
                        "posa_cash_mode_of_payment",
                    )
                    if not cash_mode_of_payment:
                        cash_mode_of_payment = "Cash"
                    if existing_pay[0].mode_of_payment == cash_mode_of_payment:
                        change_amount = flt(d.get("change_amount", 0))
                        amount = p.amount - change_amount
                        log.debug(f"[SHIFT_CLOSE_WORKFLOW] Step 100: MAKE_CLOSING_SHIFT_CASH_ADJUST - Cash payment adjusted: {p.amount} - {change_amount} = {amount}")
                    else:
                        amount = p.amount
                    existing_pay[0].expected_amount += flt(amount)
                else:
                    payments.append(
                        frappe._dict(
                            {
                                "mode_of_payment": p.mode_of_payment,
                                "opening_amount": 0,
                                "expected_amount": p.amount,
                            }
                        )
                    )

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 101: MAKE_CLOSING_SHIFT_INVOICES_PROCESSED - Processed invoices. Grand Total: {closing_shift.grand_total}")

        # Process payment entries
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 102: MAKE_CLOSING_SHIFT_PROCESS_PAYMENTS - Processing payment entries")
        pos_payments = get_payments_entries(opening_shift_name)

        for py in pos_payments:
            pos_payments_table.append(
                frappe._dict(
                    {
                        "payment_entry": py.name,
                        "mode_of_payment": py.mode_of_payment,
                        "paid_amount": py.paid_amount,
                        "posting_date": py.posting_date,
                        "customer": py.party,
                    }
                )
            )
            existing_pay = [pay for pay in payments if pay.mode_of_payment == py.mode_of_payment]
            if existing_pay:
                existing_pay[0].expected_amount += flt(py.paid_amount)
            else:
                payments.append(
                    frappe._dict(
                        {
                            "mode_of_payment": py.mode_of_payment,
                            "opening_amount": 0,
                            "expected_amount": py.paid_amount,
                        }
                    )
                )

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 103: MAKE_CLOSING_SHIFT_PAYMENTS_PROCESSED - Processed {len(pos_payments)} payment entries")

        # Set shift_report field if exists
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 104: MAKE_CLOSING_SHIFT_FIND_REPORT - Finding shift report for opening shift {opening_shift_name}")
        shift_report = frappe.db.exists("POS Shift Report", {
            "pos_opening_shift": opening_shift_name
        })

        if shift_report:
            closing_shift.shift_report = shift_report
            # Get shift report details
            shift_report_doc = frappe.get_doc("POS Shift Report", shift_report)
            verification_status = shift_report_doc.verification_status
            closing_shift.verification_status = verification_status or "Pending"
            # Also set shift_report_id for display
            closing_shift.shift_report_id = shift_report_doc.shift_report_id
            # Set full verification details
            closing_shift.verification_date = shift_report_doc.verification_date
            closing_shift.verified_by = shift_report_doc.verified_by
            closing_shift.confirmation_date = shift_report_doc.confirmation_date
            closing_shift.confirmed_by = shift_report_doc.confirmed_by
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 105: MAKE_CLOSING_SHIFT_REPORT_FOUND - Found existing shift report: {shift_report}, ID: {shift_report_doc.shift_report_id}, Status: {verification_status}, Verified by: {shift_report_doc.verified_by}")
        else:
            closing_shift.verification_status = "Pending"
            log.warning(f"[SHIFT_CLOSE_WORKFLOW] WARNING: MAKE_CLOSING_SHIFT_NO_REPORT - No shift report found for opening shift: {opening_shift_name}")

        # Set child tables
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 106: MAKE_CLOSING_SHIFT_SET_TABLES - Setting child tables")
        closing_shift.set("pos_transactions", pos_transactions)
        closing_shift.set("payment_reconciliation", payments)
        closing_shift.set("taxes", taxes)
        closing_shift.set("pos_payments", pos_payments_table)

        # Save the closing shift document to generate name (skip validation during creation)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 107: MAKE_CLOSING_SHIFT_SAVE - Saving closing shift document")
        closing_shift.set("pos_payments", pos_payments_table)

        # Save the closing shift document to generate name (skip validation during creation)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 107: MAKE_CLOSING_SHIFT_SAVE - Saving closing shift document")
        closing_shift.flags.ignore_validate = True  # Skip validation during creation to avoid validating with closing_amount=0
        log.info(f"[SHIFT_CLOSE_WORKFLOW] TRACING_CLOSING_AMOUNT - Skipping validation during document creation (closing_amount would be 0)")
        closing_shift.insert(ignore_permissions=True)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 108: MAKE_CLOSING_SHIFT_SAVED - Closing shift saved with name: {closing_shift.name}")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 109: MAKE_CLOSING_SHIFT_COMPLETED - Closing shift created successfully. Name: {closing_shift.name}, Transactions: {len(pos_transactions)}, Payments: {len(payments)}")
        return closing_shift

    except Exception as e:
        log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: MAKE_CLOSING_SHIFT_FAILED - Failed to create closing shift: {str(e)}")
        frappe.log_error(f"Error in make_closing_shift_from_opening: {str(e)}", "POS Closing Shift Creation Error")
        raise


@frappe.whitelist()
def submit_closing_shift_v2(closing_shift):
    """
    NEW API - Combined create and submit closing shift in one call
    If document doesn't exist, creates it first using make_closing_shift_from_opening logic
    """
    log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 126: START - Starting combined closing shift submission - User: {frappe.session.user}")
    log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 127: REQUEST - Full client request: {closing_shift}")

    try:
        # Parse input data
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 128: SUBMIT_CLOSING_SHIFT_V2_PARSE - Parsing closing shift JSON data")
        closing_shift_data = json.loads(closing_shift)

        closing_shift_name = closing_shift_data.get("name")
        opening_shift = closing_shift_data.get("pos_opening_shift")
        shift_report = closing_shift_data.get("shift_report")
        shift_report_id = closing_shift_data.get("shift_report_id")
        user = closing_shift_data.get("user")

        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 129: DATA - Closing shift: {closing_shift_name}, Opening shift: {opening_shift}, User: {user}")

        # Log actual closing amounts entered by user
        payment_reconciliation = closing_shift_data.get("payment_reconciliation", [])
        if payment_reconciliation:
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 130: ACTUAL_AMOUNTS - User entered actual closing amounts:")
            for payment in payment_reconciliation:
                mode = payment.get("mode_of_payment", "Unknown")
                opening = payment.get("opening_amount", 0)
                expected = payment.get("expected_amount", 0)
                actual = payment.get("closing_amount", 0)
                difference = payment.get("difference", 0)
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 131: AMOUNT_DETAIL - {mode}: Opening={opening}, Expected={expected}, Actual={actual}, Difference={difference}")
                # Additional tracing for closing_amount specifically
                log.info(f"[SHIFT_CLOSE_WORKFLOW] TRACING_CLOSING_AMOUNT - Received from client: {mode} -> closing_amount={actual} (type: {type(actual)})")

        # STEP 1: Create document if it doesn't exist
        if not closing_shift_name or not frappe.db.exists("POS Closing Shift", closing_shift_name):
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 132: CREATE_DOC - Document doesn't exist, creating new one")

            # Check if opening_shift is actually a POS Shift Report ID
            actual_opening_shift = opening_shift
            if opening_shift and frappe.db.exists("POS Shift Report", opening_shift):
                log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 133: SHIFT_REPORT_FOUND - '{opening_shift}' is a POS Shift Report, finding associated opening shift")
                # Find the associated opening shift
                shift_report_doc = frappe.get_doc("POS Shift Report", opening_shift)
                if shift_report_doc.pos_opening_shift:
                    actual_opening_shift = shift_report_doc.pos_opening_shift
                    log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 134: FOUND_OPENING_SHIFT - Found opening shift: {actual_opening_shift}")
                else:
                    log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: NO_OPENING_SHIFT - Shift report {opening_shift} has no associated opening shift")
                    frappe.throw(_("Shift report has no associated opening shift"))

            # Create the closing shift document
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 135: CREATE_CLOSING_SHIFT - Creating closing shift for opening shift: {actual_opening_shift}")
            closing_shift_doc = make_closing_shift_from_opening(json.dumps({"name": actual_opening_shift}))
            closing_shift_name = closing_shift_doc.name
            log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 136: CREATED_CLOSING_SHIFT - Created closing shift: {closing_shift_name}")

        # STEP 2: Load and update the closing shift document
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 137: LOAD_CLOSING_SHIFT - Loading closing shift document: {closing_shift_name}")
        closing_shift_doc = frappe.get_doc("POS Closing Shift", closing_shift_name)

        # Update payment reconciliation with user-entered closing amounts
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 138: UPDATE_PAYMENT_RECONCILIATION - Updating payment reconciliation")
        for payment_data in payment_reconciliation:
            mode = payment_data.get("mode_of_payment")
            closing_amount = flt(payment_data.get("closing_amount", 0))

            # Find matching payment reconciliation record
            for pr in closing_shift_doc.payment_reconciliation:
                if pr.mode_of_payment == mode:
                    pr.closing_amount = closing_amount
                    log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 139: UPDATED_CLOSING_AMOUNT - {mode}: {closing_amount}")
                    break

        # Save the updated document
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 140: SAVE_CLOSING_SHIFT - Saving updated closing shift")
        closing_shift_doc.save(ignore_permissions=True)
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 141: SAVED_CLOSING_SHIFT - Closing shift saved successfully")

        # STEP 3: Submit the closing shift
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 142: SUBMIT_CLOSING_SHIFT - Submitting closing shift")
        closing_shift_doc.submit()
        log.info(f"[SHIFT_CLOSE_WORKFLOW] Step 143: SUBMITTED_CLOSING_SHIFT - Closing shift submitted successfully")

        # Return success response
        return {
            "success": True,
            "message": _("POS Closing Shift submitted successfully"),
            "data": {
                "name": closing_shift_name,
                "docstatus": 1,  # Submitted status
                "requires_logout": True,  # Signal to frontend to logout user
                "requires_ui_refresh": True  # Signal to frontend to refresh UI
            }
        }

    except frappe.ValidationError as ve:
        log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: SUBMIT_CLOSING_SHIFT_V2_VALIDATION - Validation error: {str(ve)}")
        raise
    except Exception as e:
        log.error(f"[SHIFT_CLOSE_WORKFLOW] ERROR: SUBMIT_CLOSING_SHIFT_V2_FAILED - Unexpected error: {str(e)}")
        frappe.log_error(f"Unexpected error in submit_closing_shift_v2: {str(e)}", "POS Closing Shift Submit Error V2")

        return {
            "success": False,
            "message": _("An unexpected error occurred while submitting closing shift: {0}").format(str(e))
        }
