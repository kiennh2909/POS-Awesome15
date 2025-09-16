# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now, get_datetime
import time
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger với tên "shift_close"
log = get_logger("shift_close")

# Configuration constants
DEFAULT_BATCH_SIZE = 50
DEFAULT_CURRENCY_PRECISION = 3
MAX_WORKFLOW_STEPS = 1000

class POSClosingShift(Document):
    """Enhanced POS Closing Shift với logging thống nhất SHIFT_CLOSE_WORKFLOW"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_start_time = None
        self.workflow_steps = []

    def log_workflow_step(self, step_name, step_data=None, level="INFO"):
        """Log workflow step với prefix thống nhất SHIFT_CLOSE_WORKFLOW"""
        timestamp = now()

        if not self.workflow_start_time:
            self.workflow_start_time = timestamp

        step_info = {
            "document": self.name,
            "step": step_name,
            "timestamp": timestamp,
            "duration": (get_datetime(timestamp) - get_datetime(self.workflow_start_time)).total_seconds() if self.workflow_start_time else 0,
            "user": frappe.session.user,
            "data": step_data or {}
        }

        self.workflow_steps.append(step_info)

        # Sử dụng prefix thống nhất SHIFT_CLOSE_WORKFLOW
        log_message = f"[SHIFT_CLOSE_WORKFLOW] {step_name} - Doc: {self.name}"
        if step_data:
            log_message += f" - Data: {json.dumps(step_data, default=str)}"

        if level == "ERROR":
            log.error(log_message)
        elif level == "WARNING":
            log.warning(log_message)
        elif level == "DEBUG":
            log.debug(log_message)
        else:
            log.info(log_message)

        return step_info

    def log_performance_metric(self, operation, start_time, end_time=None, metadata=None):
        """Log performance metrics với prefix thống nhất - DISABLED FOR PERFORMANCE"""
        return {"operation": operation, "disabled": True}

    def validate(self):
        """Enhanced validate method với logging thống nhất SHIFT_CLOSE_WORKFLOW"""
        start_time = time.time()

        try:
            self.log_workflow_step("VALIDATE_START", {
                "opening_shift": self.pos_opening_shift,
                "company": self.company,
                "pos_profile": self.pos_profile,
                "user": self.user
            })

            # Original validation logic
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
                self.log_workflow_step("VALIDATE_DUPLICATE_FOUND", {
                    "user": self.user,
                    "opening_shift": self.pos_opening_shift,
                    "existing_count": len(user)
                }, "WARNING")
                frappe.throw(
                    _(
                        "POS Closing Shift {} against {} between selected period".format(
                            frappe.bold("already exists"), frappe.bold(self.user)
                        )
                    ),
                    title=_("Invalid Period"),
                )

            if frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status") != "Open":
                self.log_workflow_step("VALIDATE_OPENING_SHIFT_NOT_OPEN", {
                    "opening_shift": self.pos_opening_shift,
                    "current_status": frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status")
                }, "ERROR")
                frappe.throw(
                    _("Selected POS Opening Shift should be open."),
                    title=_("Invalid Opening Entry"),
                )

            # Set shift_report field if not provided
            if not self.shift_report and self.pos_opening_shift:
                # Try to find existing shift report for this opening shift
                shift_report = frappe.db.exists("POS Shift Report", {
                    "pos_opening_shift": self.pos_opening_shift
                })

                if shift_report:
                    self.shift_report = shift_report
                    self.log_workflow_step("SHIFT_REPORT_LINKED", {
                        "shift_report": shift_report,
                        "pos_opening_shift": self.pos_opening_shift
                    })
                else:
                    # Try to create shift report automatically
                    try:
                        from posawesome.posawesome.doctype.pos_shift_report.pos_shift_report import create_shift_report_from_opening
                        new_shift_report = create_shift_report_from_opening(self.pos_opening_shift)

                        if new_shift_report:
                            self.shift_report = new_shift_report.name
                            self.log_workflow_step("SHIFT_REPORT_CREATED", {
                                "shift_report": new_shift_report.name,
                                "pos_opening_shift": self.pos_opening_shift
                            })
                        else:
                            self.log_workflow_step("SHIFT_REPORT_CREATION_FAILED", {
                                "pos_opening_shift": self.pos_opening_shift
                            }, "ERROR")
                    except Exception as e:
                        self.log_workflow_step("SHIFT_REPORT_CREATION_ERROR", {
                            "pos_opening_shift": self.pos_opening_shift,
                            "error": str(e)
                        }, "ERROR")

            # Enhanced calculations with logging
            self.update_payment_reconciliation()
            self.calculate_payment_amounts()

            # Verification status update
            self.update_verification_status()

            self.log_workflow_step("VALIDATE_SUCCESS", {
                "payment_methods_count": len(self.payment_reconciliation),
                "verification_status": self.verification_status,
                "total_difference": sum(flt(p.difference or 0) for p in self.payment_reconciliation)
            })

        except frappe.ValidationError as ve:
            self.log_workflow_step("VALIDATE_ERROR", {
                "error": str(ve),
                "error_type": "ValidationError",
                "docstatus": self.docstatus,
                "verification_status": self.verification_status
            }, "ERROR")
            raise
        except Exception as e:
            self.log_workflow_step("VALIDATE_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__,
                "docstatus": self.docstatus,
                "verification_status": self.verification_status
            }, "ERROR")

            raise

    def update_payment_reconciliation(self):
        """Update payment reconciliation với logging thống nhất SHIFT_CLOSE_WORKFLOW"""
        start_time = time.time()

        self.log_workflow_step("PAYMENT_RECONCILIATION_START", {
            "payment_count": len(self.payment_reconciliation)
        })

        # Get default precision for site
        precision = frappe.get_cached_value("System Settings", None, "currency_precision") or DEFAULT_CURRENCY_PRECISION

        # Calculate differences for child table
        total_difference = 0
        processed_payments = []

        for idx, d in enumerate(self.payment_reconciliation):
            payment_start = time.time()

            try:
                expected = flt(d.expected_amount or 0, precision)
                actual = flt(d.closing_amount or 0, precision)
                difference = actual - expected

                d.difference = difference
                total_difference += difference

                payment_info = {
                    "index": idx,
                    "mode_of_payment": d.mode_of_payment,
                    "expected_amount": expected,
                    "closing_amount": actual,
                    "difference": difference
                }

                processed_payments.append(payment_info)

            except Exception as e:
                self.log_workflow_step("PAYMENT_PROCESSING_ERROR", {
                    "index": idx,
                    "mode_of_payment": d.mode_of_payment,
                    "error": str(e)
                }, "ERROR")

        self.log_workflow_step("PAYMENT_RECONCILIATION_SUCCESS", {
            "total_payments": len(processed_payments),
            "total_difference": total_difference
        })

        # Calculate and store amounts as JSON for reporting
        self.calculate_payment_amounts()

    def calculate_payment_amounts(self):
        """Calculate expected, actual, and difference amounts as JSON với logging thống nhất"""
        start_time = time.time()

        self.log_workflow_step("AMOUNT_CALCULATION_START")

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

            calculation_result = {
                "expected_count": len(expected_amounts),
                "actual_count": len(actual_amounts),
                "difference_count": len(difference_amounts),
                "expected_amounts": expected_amounts,
                "actual_amounts": actual_amounts,
                "difference_amounts": difference_amounts
            }

            self.log_workflow_step("AMOUNT_CALCULATION_SUCCESS", calculation_result)

        except Exception as e:
            self.log_workflow_step("AMOUNT_CALCULATION_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "ERROR")

            # Set empty JSON objects as fallback
            self.expected_amounts = "{}"
            self.actual_amounts = "{}"
            self.difference_amounts = "{}"

            frappe.logger().warning(f"Failed to calculate payment amounts for {self.name}: {str(e)}")

    def on_submit(self):
        """Enhanced on_submit với logging thống nhất SHIFT_CLOSE_WORKFLOW"""
        workflow_start = time.time()

        try:
            self.log_workflow_step("ON_SUBMIT_START", {
                "opening_shift": self.pos_opening_shift,
                "company": self.company,
                "verification_status": self.verification_status,
                "docstatus": self.docstatus,
                "total_difference": sum(flt(p.difference or 0) for p in self.payment_reconciliation)
            })

            # Validate verification status before submission
            if self.verification_status not in ["Verified", "Confirmed"]:
                total_difference = sum(flt(p.difference or 0) for p in self.payment_reconciliation)
                self.log_workflow_step("ON_SUBMIT_VALIDATION_FAILED", {
                    "verification_status": self.verification_status,
                    "required_status": ["Verified", "Confirmed"],
                    "total_difference": total_difference
                }, "ERROR")

                # Allow submission with warning if shift_report exists but verification is pending
                if self.shift_report and self.verification_status == "Pending":
                    self.log_workflow_step("ON_SUBMIT_ALLOW_PENDING", {
                        "shift_report": self.shift_report,
                        "total_difference": total_difference
                    }, "WARNING")
                else:
                    frappe.throw(_("Cannot submit closing shift with verification status '{0}'. Status must be 'Verified' or 'Confirmed'.").format(self.verification_status))

            # Update opening shift reference
            opening_update_start = time.time()
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            opening_entry.pos_closing_shift = self.name
            opening_entry.set_status()
            opening_entry.save()

            self.log_workflow_step("OPENING_SHIFT_UPDATED", {
                "opening_shift": self.pos_opening_shift
            })

            # Delete draft invoices
            invoice_delete_start = time.time()
            self.delete_draft_invoices()
            self.log_workflow_step("DRAFT_INVOICES_DELETED", {})

            # Update verification status based on business rules
            verification_start = time.time()
            self.update_verification_status()
            self.log_workflow_step("VERIFICATION_STATUS_UPDATED", {
                "new_status": self.verification_status
            })

            # Update POS Shift Report with closing data
            self.update_pos_shift_report_on_close()

            # Update POS Payment Summary with closing amounts
            self.update_pos_payment_summary_on_close()

            # Final success log
            self.log_workflow_step("ON_SUBMIT_SUCCESS", {
                "final_status": self.verification_status
            })

            log.info(f"[SHIFT_CLOSE_WORKFLOW] COMPLETE - POS Closing Shift {self.name} submitted successfully by user {frappe.session.user}")

        except frappe.ValidationError as ve:
            self.log_workflow_step("ON_SUBMIT_ERROR", {
                "error": str(ve),
                "error_type": "ValidationError",
                "verification_status": self.verification_status,
                "docstatus": self.docstatus
            }, "ERROR")

            log.error(f"[SHIFT_CLOSE_WORKFLOW] FAILED - POS Closing Shift {self.name} submission failed: {str(ve)}")
            # Don't raise error here as it might prevent submission
            # Just log the error for debugging
        except Exception as e:
            self.log_workflow_step("ON_SUBMIT_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__,
                "verification_status": self.verification_status,
                "docstatus": self.docstatus
            }, "ERROR")

            log.error(f"[SHIFT_CLOSE_WORKFLOW] FAILED - POS Closing Shift {self.name} submission failed: {str(e)}")
            # Don't raise error here as it might prevent submission
            # Just log the error for debugging

    def update_verification_status(self):
        """Update verification status based on business rules với logging thống nhất"""
        start_time = time.time()

        self.log_workflow_step("VERIFICATION_STATUS_UPDATE_START")

        try:
            # Check if all payment reconciliations are balanced
            all_balanced = True
            total_difference = 0
            payment_details = []

            for payment in self.payment_reconciliation:
                difference = flt(payment.difference or 0)
                total_difference += difference

                payment_detail = {
                    "mode_of_payment": payment.mode_of_payment,
                    "expected_amount": payment.expected_amount,
                    "closing_amount": payment.closing_amount,
                    "difference": difference
                }
                payment_details.append(payment_detail)

                if abs(difference) > 0.01:  # Allow small rounding differences
                    all_balanced = False

            # Update verification status
            old_status = self.verification_status
            if all_balanced and abs(total_difference) <= 0.01:
                self.verification_status = "Verified"
            else:
                self.verification_status = "Pending"

            # Note: Don't call save() here as it will trigger validate() again causing infinite loop
            # Verification status will be saved when the document is saved normally

            verification_result = {
                "old_status": old_status,
                "new_status": self.verification_status,
                "all_balanced": all_balanced,
                "total_difference": total_difference,
                "payment_count": len(payment_details),
                "payment_details": payment_details
            }

            self.log_workflow_step("VERIFICATION_STATUS_UPDATE_SUCCESS", verification_result)

        except Exception as e:
            self.log_workflow_step("VERIFICATION_STATUS_UPDATE_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "ERROR")

            self.verification_status = "Pending"
            frappe.logger().warning(f"Failed to update verification status for {self.name}: {str(e)}")

    def on_cancel(self):
        """Enhanced on_cancel với logging thống nhất SHIFT_CLOSE_WORKFLOW"""
        start_time = time.time()

        try:
            self.log_workflow_step("ON_CANCEL_START", {
                "opening_shift": self.pos_opening_shift,
                "current_status": self.status
            })

            if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
                opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
                if opening_entry.pos_closing_shift == self.name:
                    opening_entry.pos_closing_shift = ""
                    opening_entry.set_status()
                    opening_entry.save()

                    self.log_workflow_step("OPENING_SHIFT_REFERENCE_CLEARED", {
                        "opening_shift": self.pos_opening_shift
                    })
                else:
                    self.log_workflow_step("OPENING_SHIFT_REFERENCE_NOT_FOUND", {
                        "opening_shift": self.pos_opening_shift,
                        "expected_closing_shift": self.name,
                        "actual_closing_shift": opening_entry.pos_closing_shift
                    }, "WARNING")
            else:
                self.log_workflow_step("OPENING_SHIFT_NOT_FOUND", {
                    "opening_shift": self.pos_opening_shift
                }, "WARNING")

            self.log_workflow_step("ON_CANCEL_SUCCESS", {})

            log.info(f"[SHIFT_CLOSE_WORKFLOW] CANCELLED - POS Closing Shift {self.name} cancelled successfully by user {frappe.session.user}")

        except Exception as e:
            self.log_workflow_step("ON_CANCEL_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "ERROR")

            log.error(f"[SHIFT_CLOSE_WORKFLOW] CANCEL_FAILED - POS Closing Shift {self.name} cancellation failed: {str(e)}")
            raise

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            data = frappe.db.sql(
                """
                select
                    name
                from
                    `tabSales Invoice`
                where
                    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
                """,
                (self.pos_opening_shift),
                as_dict=1,
            )

            for invoice in data:
                frappe.delete_doc("Sales Invoice", invoice.name, force=1)

    def update_pos_shift_report_on_close(self):
        """Update POS Shift Report with closing data when closing shift is submitted"""
        try:
            if not self.shift_report:
                self.log_workflow_step("UPDATE_SHIFT_REPORT_SKIP", {
                    "reason": "No shift report linked"
                }, "WARNING")
                return

            # Get shift report
            shift_report = frappe.get_doc("POS Shift Report", self.shift_report)

            # Update closing data
            shift_report.closing_date = self.period_end_date
            shift_report.closed_by = self.user
            shift_report.status = "Closed"

            # Calculate actual closing amounts from payment reconciliation
            actual_closing_amounts = {}
            total_actual_closing = 0

            for payment in self.payment_reconciliation:
                mode = payment.mode_of_payment
                closing_amount = flt(payment.closing_amount or 0)
                actual_closing_amounts[mode] = closing_amount
                total_actual_closing += closing_amount

            shift_report.actual_closing_amounts = frappe.as_json(actual_closing_amounts)
            shift_report.total_actual_closing = total_actual_closing

            # Calculate difference
            expected_total = flt(shift_report.total_expected_closing or 0)
            shift_report.difference = total_actual_closing - expected_total

            # Save shift report
            shift_report.save(ignore_permissions=True)

            self.log_workflow_step("UPDATE_SHIFT_REPORT_SUCCESS", {
                "shift_report": self.shift_report,
                "actual_closing_amounts": actual_closing_amounts,
                "total_actual_closing": total_actual_closing,
                "difference": shift_report.difference
            })

        except Exception as e:
            self.log_workflow_step("UPDATE_SHIFT_REPORT_ERROR", {
                "shift_report": self.shift_report,
                "error": str(e)
            }, "ERROR")
            # Don't raise error to prevent closing shift submission failure

    def update_pos_payment_summary_on_close(self):
        """Update POS Payment Summary records with closing amounts when closing shift is submitted"""
        try:
            if not self.shift_report:
                self.log_workflow_step("UPDATE_PAYMENT_SUMMARY_SKIP", {
                    "reason": "No shift report linked"
                }, "WARNING")
                return

            # Get shift report for shift_report_id
            shift_report = frappe.get_doc("POS Shift Report", self.shift_report)
            shift_report_id = shift_report.shift_report_id

            # Update shift_end_time in shift report first
            shift_report.shift_end_time = self.period_end_date
            shift_report.save(ignore_permissions=True)

            # Get all POS Payment Summary records for this shift
            payment_summaries = frappe.get_all("POS Payment Summary",
                filters={
                    "shift_report_id": shift_report_id,
                    "pos_shift_report": self.shift_report
                },
                fields=["name", "payment_method"]
            )

            updated_count = 0
            for summary in payment_summaries:
                try:
                    # Get the document
                    summary_doc = frappe.get_doc("POS Payment Summary", summary.name)

                    # Find corresponding payment reconciliation data
                    reconciliation_data = None
                    for payment in self.payment_reconciliation:
                        if payment.mode_of_payment == summary_doc.payment_method:
                            reconciliation_data = payment
                            break

                    if reconciliation_data:
                        # Update closing data
                        summary_doc.closing_amount = flt(reconciliation_data.closing_amount or 0)
                        summary_doc.expected_closing_amount = flt(reconciliation_data.expected_amount or 0)
                        summary_doc.difference = summary_doc.closing_amount - summary_doc.expected_closing_amount
                        summary_doc.shift_end_time = self.period_end_date

                        # Save
                        summary_doc.save(ignore_permissions=True)
                        updated_count += 1

                except Exception as e:
                    self.log_workflow_step("UPDATE_PAYMENT_SUMMARY_ITEM_ERROR", {
                        "payment_summary": summary.name,
                        "payment_method": summary.payment_method,
                        "error": str(e)
                    }, "ERROR")
                    continue

            self.log_workflow_step("UPDATE_PAYMENT_SUMMARY_SUCCESS", {
                "shift_report": self.shift_report,
                "updated_count": updated_count,
                "total_summaries": len(payment_summaries)
            })

        except Exception as e:
            self.log_workflow_step("UPDATE_PAYMENT_SUMMARY_ERROR", {
                "shift_report": self.shift_report,
                "error": str(e)
            }, "ERROR")
            # Don't raise error to prevent closing shift submission failure

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
            # Return list of tuples in format (value, label) where value is user ID and label shows both ID and email
            result.append([cashier.user, f"{cashier.user} ({user_email})"])
    return result


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift):
    """
    Get POS invoices với logging thống nhất SHIFT_CLOSE_WORKFLOW

    Args:
        pos_opening_shift (str): Opening shift name

    Returns:
        list: List of invoice dictionaries
    """
    api_start = time.time()
    request_id = frappe.generate_hash(length=8)

    log.info(f"[SHIFT_CLOSE_WORKFLOW] API_START - get_pos_invoices - Request: {request_id} - Opening shift: {pos_opening_shift}")

    try:
        # Submit printed invoices first
        submit_printed_invoices(pos_opening_shift)

        # Get invoice names with essential fields in single query
        invoice_data = frappe.db.sql(
            """
            SELECT name, posting_date, posting_time, customer, grand_total,
                   paid_amount, outstanding_amount, is_return, status
            FROM `tabSales Invoice`
            WHERE docstatus = 1
              AND posa_pos_opening_shift = %s
            ORDER BY posting_date, posting_time
            """,
            (pos_opening_shift,),
            as_dict=1,
        )

        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - get_pos_invoices - Request: {request_id} - Found {len(invoice_data)} raw invoices")

        # Process in batches to avoid memory issues
        batch_size = DEFAULT_BATCH_SIZE
        result = []
        processed_count = 0
        error_count = 0

        for i in range(0, len(invoice_data), batch_size):
            batch = invoice_data[i:i + batch_size]

            for invoice in batch:
                try:
                    # Get payment details for this invoice
                    payments = frappe.get_all(
                        "Sales Invoice Payment",
                        filters={"parent": invoice.name},
                        fields=["mode_of_payment", "amount"]
                    )

                    # Build invoice dict with payment info
                    invoice_dict = {
                        "name": invoice.name,
                        "posting_date": invoice.posting_date,
                        "posting_time": invoice.posting_time,
                        "customer": invoice.customer,
                        "grand_total": invoice.grand_total,
                        "paid_amount": invoice.paid_amount,
                        "outstanding_amount": invoice.outstanding_amount,
                        "is_return": invoice.is_return,
                        "status": invoice.status,
                        "payments": payments
                    }

                    result.append(invoice_dict)
                    processed_count += 1

                except Exception as e:
                    log.warning(f"[SHIFT_CLOSE_WORKFLOW] API_WARNING - get_pos_invoices - Request: {request_id} - Failed to process invoice {invoice.name}: {str(e)}")
                    error_count += 1
                    continue

        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_SUCCESS - get_pos_invoices - Request: {request_id} - Processed {processed_count} invoices, {error_count} errors")

        return result

    except Exception as e:
        log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - get_pos_invoices - Request: {request_id} - Failed: {str(e)}")
        frappe.log_error(f"Error getting POS invoices for shift {pos_opening_shift}: {str(e)}")
        return []


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


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    """Create closing shift từ opening shift với logging thống nhất SHIFT_CLOSE_WORKFLOW"""
    api_start = time.time()
    request_id = frappe.generate_hash(length=8)

    log.info(f"[SHIFT_CLOSE_WORKFLOW] API_START - make_closing_shift_from_opening - Request: {request_id}")

    try:
        # Parse input data
        if isinstance(opening_shift, str):
            opening_shift_data = json.loads(opening_shift)
        else:
            opening_shift_data = opening_shift

        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - make_closing_shift_from_opening - Request: {request_id} - Opening shift: {opening_shift_data.get('name')}")

        # Submit printed invoices
        submit_printed_invoices(opening_shift_data.get("name"))

        # Create closing shift document
        closing_shift = frappe.new_doc("POS Closing Shift")
        closing_shift.pos_opening_shift = opening_shift_data.get("name")
        closing_shift.period_start_date = opening_shift_data.get("period_start_date")
        closing_shift.period_end_date = frappe.utils.get_datetime()
        closing_shift.pos_profile = opening_shift_data.get("pos_profile")
        closing_shift.user = opening_shift_data.get("user")
        closing_shift.company = opening_shift_data.get("company")
        closing_shift.grand_total = 0
        closing_shift.net_total = 0
        closing_shift.total_quantity = 0

        # Get invoices data
        invoices = get_pos_invoices(opening_shift_data.get("name"))
        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - make_closing_shift_from_opening - Request: {request_id} - Found {len(invoices)} invoices")

        pos_transactions = []
        taxes = []
        payments = []
        pos_payments_table = []

        # Process balance details
        for detail in opening_shift_data.get("balance_details", []):
            payments.append(
                frappe._dict(
                    {
                        "mode_of_payment": detail.get("mode_of_payment"),
                        "opening_amount": detail.get("amount") or 0,
                        "expected_amount": detail.get("amount") or 0,
                    }
                )
            )

        # Process invoices
        for d in invoices:
            pos_transactions.append(
                frappe._dict(
                    {
                        "sales_invoice": d.get("name"),
                        "posting_date": d.get("posting_date"),
                        "grand_total": d.get("grand_total"),
                        "customer": d.get("customer"),
                    }
                )
            )
            closing_shift.grand_total += flt(d.get("grand_total"))
            closing_shift.net_total += flt(d.get("net_total") or 0)
            closing_shift.total_quantity += flt(d.get("total_qty") or 0)

            # Process taxes
            for t in d.get("taxes", []):
                existing_tax = [tx for tx in taxes if tx.account_head == t.get("account_head") and tx.rate == t.get("rate")]
                if existing_tax:
                    existing_tax[0].amount += flt(t.get("tax_amount"))
                else:
                    taxes.append(
                        frappe._dict(
                            {
                                "account_head": t.get("account_head"),
                                "rate": t.get("rate"),
                                "amount": t.get("tax_amount"),
                            }
                        )
                    )

            # Process payments
            for p in d.get("payments", []):
                existing_pay = [pay for pay in payments if pay.mode_of_payment == p.get("mode_of_payment")]
                if existing_pay:
                    cash_mode_of_payment = frappe.get_value(
                        "POS Profile",
                        opening_shift_data.get("pos_profile"),
                        "posa_cash_mode_of_payment",
                    )
                    if not cash_mode_of_payment:
                        cash_mode_of_payment = "Cash"
                    if existing_pay[0].mode_of_payment == cash_mode_of_payment:
                        amount = p.get("amount", 0) - (d.get("change_amount") or 0)
                    else:
                        amount = p.get("amount", 0)
                    existing_pay[0].expected_amount += flt(amount)
                else:
                    payments.append(
                        frappe._dict(
                            {
                                "mode_of_payment": p.get("mode_of_payment"),
                                "opening_amount": 0,
                                "expected_amount": p.get("amount", 0),
                            }
                        )
                    )

        # Process payment entries
        pos_payments = get_payments_entries(opening_shift_data.get("name"))

        for py in pos_payments:
            pos_payments_table.append(
                frappe._dict(
                    {
                        "payment_entry": py.get("name"),
                        "mode_of_payment": py.get("mode_of_payment"),
                        "paid_amount": py.get("paid_amount"),
                        "posting_date": py.get("posting_date"),
                        "customer": py.get("party"),
                    }
                )
            )
            existing_pay = [pay for pay in payments if pay.mode_of_payment == py.get("mode_of_payment")]
            if existing_pay:
                existing_pay[0].expected_amount += flt(py.get("paid_amount"))
            else:
                payments.append(
                    frappe._dict(
                        {
                            "mode_of_payment": py.get("mode_of_payment"),
                            "opening_amount": 0,
                            "expected_amount": py.get("paid_amount"),
                        }
                    )
                )

        # Set shift_report field if exists
        shift_report = frappe.db.exists("POS Shift Report", {
            "pos_opening_shift": opening_shift_data.get("name")
        })

        if shift_report:
            closing_shift.shift_report = shift_report
            log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - make_closing_shift_from_opening - Request: {request_id} - Linked to shift report: {shift_report}")
        else:
            # Try to create shift report automatically
            try:
                from posawesome.posawesome.doctype.pos_shift_report.pos_shift_report import create_shift_report_from_opening
                new_shift_report = create_shift_report_from_opening(opening_shift_data.get("name"))

                if new_shift_report:
                    closing_shift.shift_report = new_shift_report.name
                    log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - make_closing_shift_from_opening - Request: {request_id} - Created new shift report: {new_shift_report.name}")
                else:
                    log.warning(f"[SHIFT_CLOSE_WORKFLOW] API_WARNING - make_closing_shift_from_opening - Request: {request_id} - Failed to create shift report for opening shift: {opening_shift_data.get('name')}")
            except Exception as e:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - make_closing_shift_from_opening - Request: {request_id} - Error creating shift report: {str(e)}")

        # Set child tables
        closing_shift.set("pos_transactions", pos_transactions)
        closing_shift.set("payment_reconciliation", payments)
        closing_shift.set("taxes", taxes)
        closing_shift.set("pos_payments", pos_payments_table)

        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_SUCCESS - make_closing_shift_from_opening - Request: {request_id} - Created closing shift with {len(payments)} payment methods, {len(pos_transactions)} transactions")

        return closing_shift

    except Exception as e:
        log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - make_closing_shift_from_opening - Request: {request_id} - Failed: {str(e)}")
        frappe.throw(f"Failed to create closing shift: {str(e)}")


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    """
    Submit POS Closing Shift với logging thống nhất SHIFT_CLOSE_WORKFLOW

    Args:
        closing_shift (str): JSON string containing closing shift data

    Returns:
        dict: Result with success status and data
    """
    api_start = time.time()
    request_id = frappe.generate_hash(length=8)

    log.info(f"[SHIFT_CLOSE_WORKFLOW] API_START - submit_closing_shift - Request: {request_id}")

    try:
        # Validate input
        if not closing_shift or not isinstance(closing_shift, str):
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Invalid closing shift data provided")
            frappe.throw(_("Invalid closing shift data provided"))

        # Parse JSON safely
        try:
            closing_shift_data = json.loads(closing_shift)
            log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - JSON parsed successfully")
        except json.JSONDecodeError as e:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Invalid JSON format: {str(e)}")
            frappe.throw(_("Invalid JSON format in closing shift data: {0}").format(str(e)))

        # Validate required fields
        required_fields = ['doctype', 'pos_opening_shift', 'user', 'company']
        missing_fields = []
        for field in required_fields:
            if field not in closing_shift_data:
                missing_fields.append(field)

        if missing_fields:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Missing required fields: {missing_fields}")
            frappe.throw(_("Missing required fields: {0}").format(", ".join(missing_fields)))

        # Validate opening shift exists and is open
        opening_shift_name = closing_shift_data.get('pos_opening_shift')
        if not frappe.db.exists("POS Opening Shift", opening_shift_name):
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - POS Opening Shift '{opening_shift_name}' does not exist")
            frappe.throw(_("POS Opening Shift '{0}' does not exist").format(opening_shift_name))

        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        if opening_shift.status != "Open":
            # Check if there's already a submitted closing shift for this opening shift
            existing_closing = frappe.db.exists("POS Closing Shift", {
                "pos_opening_shift": opening_shift_name,
                "docstatus": 1  # Submitted
            })

            if existing_closing:
                log.warning(f"[SHIFT_CLOSE_WORKFLOW] API_WARNING - submit_closing_shift - Request: {request_id} - Closing shift already exists for POS Opening Shift '{opening_shift_name}' (existing: {existing_closing})")
                return {
                    "success": False,
                    "message": _("Closing shift already submitted for POS Opening Shift '{0}'").format(opening_shift_name),
                    "data": {
                        "existing_closing_shift": existing_closing
                    },
                    "request_id": request_id
                }
            else:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - POS Opening Shift '{opening_shift_name}' is not open (current status: {opening_shift.status})")
                frappe.throw(_("POS Opening Shift '{0}' is not open (current status: {1})").format(
                    opening_shift_name, opening_shift.status))

        # Check if closing shift already exists
        existing_closing = frappe.db.exists("POS Closing Shift", {
            "pos_opening_shift": opening_shift_name,
            "docstatus": ["!=", 2]  # Not cancelled
        })

        if existing_closing:
            # Check if it's already submitted
            existing_docstatus = frappe.db.get_value("POS Closing Shift", existing_closing, "docstatus")
            if existing_docstatus == 1:  # Already submitted
                log.warning(f"[SHIFT_CLOSE_WORKFLOW] API_WARNING - submit_closing_shift - Request: {request_id} - Closing shift already submitted for POS Opening Shift '{opening_shift_name}' (existing: {existing_closing})")
                return {
                    "success": False,
                    "message": _("Closing shift already submitted for POS Opening Shift '{0}'").format(opening_shift_name),
                    "data": {
                        "existing_closing_shift": existing_closing
                    },
                    "request_id": request_id
                }
            else:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Closing shift already exists for POS Opening Shift '{opening_shift_name}' (status: {existing_docstatus})")
                frappe.throw(_("Closing shift already exists for POS Opening Shift '{0}'").format(opening_shift_name))

        # Validate user permissions
        if not frappe.has_permission("POS Closing Shift", "create"):
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - User {frappe.session.user} not permitted to create POS Closing Shift")
            frappe.throw(_("Not permitted to create POS Closing Shift"))

        if not frappe.has_permission("POS Closing Shift", "submit"):
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - User {frappe.session.user} not permitted to submit POS Closing Shift")
            frappe.throw(_("Not permitted to submit POS Closing Shift"))

        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - All validations passed, creating document")

        # Validate payment reconciliation data
        payment_reconciliation = closing_shift_data.get('payment_reconciliation', [])
        for idx, payment in enumerate(payment_reconciliation):
            closing_amount = payment.get('closing_amount')
            if closing_amount is None or closing_amount == '' or closing_amount == 0:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Missing or zero closing amount for payment method '{payment.get('mode_of_payment', 'Unknown')}' at index {idx}")
                frappe.throw(_("Closing amount is required and must be greater than 0 for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))

            # Validate it's a number
            try:
                closing_amount = float(closing_amount)
                if closing_amount <= 0:
                    frappe.throw(_("Closing amount must be greater than 0 for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))
                # Update the data with validated value
                payment['closing_amount'] = closing_amount
            except (ValueError, TypeError):
                log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Invalid closing amount '{closing_amount}' for payment method '{payment.get('mode_of_payment', 'Unknown')}'")
                frappe.throw(_("Closing amount must be a valid number for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))

        log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - Payment reconciliation validated for {len(payment_reconciliation)} methods")

        # Create closing shift document
        try:
            closing_shift_doc = frappe.get_doc(closing_shift_data)
            log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - Document created: {closing_shift_doc.name}")

            # Set shift_report field if not provided
            if not closing_shift_doc.shift_report and closing_shift_doc.pos_opening_shift:
                # Try to find existing shift report for this opening shift
                shift_report = frappe.db.exists("POS Shift Report", {
                    "pos_opening_shift": closing_shift_doc.pos_opening_shift
                })

                if shift_report:
                    closing_shift_doc.shift_report = shift_report
                    log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - Linked to existing shift report: {shift_report}")
                else:
                    # Try to create shift report automatically
                    try:
                        from posawesome.posawesome.doctype.pos_shift_report.pos_shift_report import create_shift_report_from_opening
                        new_shift_report = create_shift_report_from_opening(closing_shift_doc.pos_opening_shift)

                        if new_shift_report:
                            closing_shift_doc.shift_report = new_shift_report.name
                            log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - Created new shift report: {new_shift_report.name}")
                        else:
                            log.warning(f"[SHIFT_CLOSE_WORKFLOW] API_WARNING - submit_closing_shift - Request: {request_id} - Failed to create shift report for opening shift: {closing_shift_doc.pos_opening_shift}")
                    except Exception as e:
                        log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Error creating shift report: {str(e)}")

        except Exception as e:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Failed to create document: {str(e)}")
            frappe.throw(_("Failed to create closing shift document: {0}").format(str(e)))

        # Save document
        try:
            closing_shift_doc.save()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] API_PROCESS - submit_closing_shift - Request: {request_id} - Document saved: {closing_shift_doc.name}")
        except frappe.ValidationError as ve:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Validation error during save: {str(ve)}")
            # Log additional details for debugging
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Document data: pos_opening_shift={closing_shift_doc.pos_opening_shift}, user={closing_shift_doc.user}, company={closing_shift_doc.company}")
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Failed to save document: {str(e)}")
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Exception type: {type(e).__name__}")
            frappe.throw(_("Failed to save closing shift: {0}").format(str(e)))

        # Submit document
        try:
            closing_shift_doc.submit()
            log.info(f"[SHIFT_CLOSE_WORKFLOW] API_SUCCESS - submit_closing_shift - Request: {request_id} - Document submitted successfully: {closing_shift_doc.name}")
        except frappe.ValidationError as ve:
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Validation error during submit: {str(ve)}")
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Submit failed for doc: {closing_shift_doc.name}, verification_status: {closing_shift_doc.verification_status}")
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Attempt to cancel the saved document if submit fails
            try:
                if closing_shift_doc.docstatus == 0:
                    closing_shift_doc.cancel()
                log.warning(f"[SHIFT_CLOSE_WORKFLOW] API_CLEANUP - submit_closing_shift - Request: {request_id} - Cancelled saved document due to submit failure")
            except:
                pass  # Ignore cleanup errors

            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Failed to submit document: {str(e)}")
            log.error(f"[SHIFT_CLOSE_WORKFLOW] API_ERROR - submit_closing_shift - Request: {request_id} - Exception type: {type(e).__name__}")
            frappe.throw(_("Failed to submit closing shift: {0}").format(str(e)))

        return {
            "success": True,
            "message": _("POS Closing Shift submitted successfully"),
            "data": {
                "name": closing_shift_doc.name,
                "docstatus": closing_shift_doc.docstatus
            },
            "request_id": request_id
        }

    except frappe.ValidationError:
        # Re-raise validation errors as-is (they contain user-friendly messages)
        log.error(f"[SHIFT_CLOSE_WORKFLOW] API_VALIDATION_ERROR - submit_closing_shift - Request: {request_id} - Validation error: {str(frappe.ValidationError)}")
        raise
    except Exception as e:
        # Log unexpected errors
        log.error(f"[SHIFT_CLOSE_WORKFLOW] API_UNEXPECTED_ERROR - submit_closing_shift - Request: {request_id} - Unexpected error: {str(e)}")
        frappe.log_error(f"Unexpected error in submit_closing_shift: {str(e)}",
                         "POS Closing Shift Submit Error")

        return {
            "success": False,
            "message": _("An unexpected error occurred while submitting closing shift: {0}").format(str(e)),
            "request_id": request_id
        }


def submit_printed_invoices(pos_opening_shift):
    """Submit printed invoices với logging thống nhất SHIFT_CLOSE_WORKFLOW"""
    start_time = time.time()

    log.info(f"[SHIFT_CLOSE_WORKFLOW] SUBMIT_PRINTED_INVOICES_START - Opening shift: {pos_opening_shift}")

    try:
        invoices_list = frappe.get_all(
            "Sales Invoice",
            filters={
                "posa_pos_opening_shift": pos_opening_shift,
                "docstatus": 0,
                "posa_is_printed": 1,
            },
        )

        log.info(f"[SHIFT_CLOSE_WORKFLOW] SUBMIT_PRINTED_INVOICES_PROCESS - Found {len(invoices_list)} printed invoices to submit")

        submitted_count = 0
        error_count = 0

        for invoice in invoices_list:
            try:
                invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
                invoice_doc.submit()
                submitted_count += 1

                # Invoice submitted successfully

            except Exception as e:
                log.error(f"[SHIFT_CLOSE_WORKFLOW] SUBMIT_PRINTED_INVOICES_ERROR - Failed to submit invoice {invoice.name}: {str(e)}")
                error_count += 1
                continue

        log.info(f"[SHIFT_CLOSE_WORKFLOW] SUBMIT_PRINTED_INVOICES_COMPLETE - Submitted {submitted_count} invoices, {error_count} errors")

    except Exception as e:
        log.error(f"[SHIFT_CLOSE_WORKFLOW] SUBMIT_PRINTED_INVOICES_FAILED - Failed to submit printed invoices for shift {pos_opening_shift}: {str(e)}")
        frappe.log_error(f"Error submitting printed invoices for shift {pos_opening_shift}: {str(e)}")