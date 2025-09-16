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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] VALIDATE_START - POS Closing Shift {self.name}")
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
            frappe.throw(
                _(
                    "POS Closing Shift {} against {} between selected period".format(
                        frappe.bold("already exists"), frappe.bold(self.user)
                    )
                ),
                title=_("Invalid Period"),
            )

        if frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status") != "Open":
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
            else:
                # Try to create shift report automatically
                try:
                    from posawesome.posawesome.doctype.pos_shift_report.pos_shift_report import create_shift_report_from_opening
                    new_shift_report = create_shift_report_from_opening(self.pos_opening_shift)

                    if new_shift_report:
                        self.shift_report = new_shift_report.name
                except Exception as e:
                    pass

        # Enhanced calculations with logging
        self.update_payment_reconciliation()
        self.calculate_payment_amounts()

        # Verification status update
        self.update_verification_status()

    def update_payment_reconciliation(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] UPDATE_PAYMENT_RECONCILIATION - POS Closing Shift {self.name}")
        # Get default precision for site
        precision = frappe.get_cached_value("System Settings", None, "currency_precision") or DEFAULT_CURRENCY_PRECISION

        # Calculate differences for child table
        for d in self.payment_reconciliation:
            expected = flt(d.expected_amount or 0, precision)
            actual = flt(d.closing_amount or 0, precision)
            difference = actual - expected
            d.difference = difference

        # Calculate and store amounts as JSON for reporting
        self.calculate_payment_amounts()

    def calculate_payment_amounts(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] CALCULATE_PAYMENT_AMOUNTS - POS Closing Shift {self.name}")
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

        except Exception as e:
            # Set empty JSON objects as fallback
            self.expected_amounts = "{}"
            self.actual_amounts = "{}"
            self.difference_amounts = "{}"

            frappe.logger().warning(f"Failed to calculate payment amounts for {self.name}: {str(e)}")

    def on_submit(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] ON_SUBMIT_START - POS Closing Shift {self.name}")
        # Validate verification status before submission
        if self.verification_status not in ["Verified", "Confirmed"]:
            total_difference = sum(flt(p.difference or 0) for p in self.payment_reconciliation)

            # Allow submission with warning if shift_report exists but verification is pending
            if self.shift_report and self.verification_status == "Pending":
                pass
            else:
                frappe.throw(_("Cannot submit closing shift with verification status '{0}'. Status must be 'Verified' or 'Confirmed'.").format(self.verification_status))

        # Update opening shift reference
        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        opening_entry.save()

        # Delete draft invoices
        self.delete_draft_invoices()

        # Update verification status based on business rules
        self.update_verification_status()

        # Update POS Shift Report with closing data
        log.info(f"[SHIFT_CLOSE_WORKFLOW] CALL_UPDATE_SHIFT_REPORT - POS Closing Shift {self.name}")
        self.update_pos_shift_report_on_close()

        # Update POS Payment Summary with closing amounts
        log.info(f"[SHIFT_CLOSE_WORKFLOW] CALL_UPDATE_PAYMENT_SUMMARY - POS Closing Shift {self.name}")
        self.update_pos_payment_summary_on_close()

    def update_verification_status(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] UPDATE_VERIFICATION_STATUS - POS Closing Shift {self.name}")
        # Check if all payment reconciliations are balanced
        all_balanced = True
        total_difference = 0

        for payment in self.payment_reconciliation:
            difference = flt(payment.difference or 0)
            total_difference += difference

            if abs(difference) > 0.01:  # Allow small rounding differences
                all_balanced = False

        # Update verification status
        if all_balanced and abs(total_difference) <= 0.01:
            self.verification_status = "Verified"
        else:
            self.verification_status = "Pending"

        # Note: Don't call save() here as it will trigger validate() again causing infinite loop
        # Verification status will be saved when the document is saved normally

    def on_cancel(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] ON_CANCEL_START - POS Closing Shift {self.name}")
        if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            if opening_entry.pos_closing_shift == self.name:
                opening_entry.pos_closing_shift = ""
                opening_entry.set_status()
                opening_entry.save()

    def delete_draft_invoices(self):
        log.info(f"[SHIFT_CLOSE_WORKFLOW] DELETE_DRAFT_INVOICES - POS Closing Shift {self.name}")
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
        log.info(f"[SHIFT_CLOSE_WORKFLOW] UPDATE_POS_SHIFT_REPORT_ON_CLOSE - POS Closing Shift {self.name}")
        try:
            if not self.shift_report:
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

        except Exception as e:
            # Don't raise error to prevent closing shift submission failure
            pass

    def update_pos_payment_summary_on_close(self):
        """Update POS Payment Summary records with closing amounts when closing shift is submitted"""
        log.info(f"[SHIFT_CLOSE_WORKFLOW] UPDATE_POS_PAYMENT_SUMMARY_ON_CLOSE - POS Closing Shift {self.name}")
        try:
            if not self.shift_report:
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

                except Exception as e:
                    continue

        except Exception as e:
            # Don't raise error to prevent closing shift submission failure
            pass

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
    log.info(f"[SHIFT_CLOSE_WORKFLOW] GET_POS_INVOICES_START - Opening shift: {pos_opening_shift}")
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

        # Process in batches to avoid memory issues
        batch_size = DEFAULT_BATCH_SIZE
        result = []

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

                except Exception as e:
                    continue

        return result

    except Exception as e:
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
    log.info(f"[SHIFT_CLOSE_WORKFLOW] MAKE_CLOSING_SHIFT_FROM_OPENING_START")
    try:
        # Parse input data
        if isinstance(opening_shift, str):
            opening_shift_data = json.loads(opening_shift)
        else:
            opening_shift_data = opening_shift

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
        else:
            # Try to create shift report automatically
            try:
                from posawesome.posawesome.doctype.pos_shift_report.pos_shift_report import create_shift_report_from_opening
                new_shift_report = create_shift_report_from_opening(opening_shift_data.get("name"))

                if new_shift_report:
                    closing_shift.shift_report = new_shift_report.name
            except Exception as e:
                pass

        # Set child tables
        closing_shift.set("pos_transactions", pos_transactions)
        closing_shift.set("payment_reconciliation", payments)
        closing_shift.set("taxes", taxes)
        closing_shift.set("pos_payments", pos_payments_table)

        return closing_shift

    except Exception as e:
        frappe.throw(f"Failed to create closing shift: {str(e)}")


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    log.info(f"[SHIFT_CLOSE_WORKFLOW] SUBMIT_CLOSING_SHIFT_START")
    try:
        # Validate input
        if not closing_shift or not isinstance(closing_shift, str):
            frappe.throw(_("Invalid closing shift data provided"))

        # Parse JSON safely
        try:
            closing_shift_data = json.loads(closing_shift)
        except json.JSONDecodeError as e:
            frappe.throw(_("Invalid JSON format in closing shift data: {0}").format(str(e)))

        # Validate required fields
        required_fields = ['doctype', 'pos_opening_shift', 'user', 'company']
        missing_fields = []
        for field in required_fields:
            if field not in closing_shift_data:
                missing_fields.append(field)

        if missing_fields:
            frappe.throw(_("Missing required fields: {0}").format(", ".join(missing_fields)))

        # Validate opening shift exists and is open
        opening_shift_name = closing_shift_data.get('pos_opening_shift')
        if not frappe.db.exists("POS Opening Shift", opening_shift_name):
            frappe.throw(_("POS Opening Shift '{0}' does not exist").format(opening_shift_name))

        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        if opening_shift.status != "Open":
            # Check if there's already a submitted closing shift for this opening shift
            existing_closing = frappe.db.exists("POS Closing Shift", {
                "pos_opening_shift": opening_shift_name,
                "docstatus": 1  # Submitted
            })

            if existing_closing:
                return {
                    "success": False,
                    "message": _("Closing shift already submitted for POS Opening Shift '{0}'").format(opening_shift_name),
                    "data": {
                        "existing_closing_shift": existing_closing
                    }
                }
            else:
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
                return {
                    "success": False,
                    "message": _("Closing shift already submitted for POS Opening Shift '{0}'").format(opening_shift_name),
                    "data": {
                        "existing_closing_shift": existing_closing
                    }
                }
            else:
                frappe.throw(_("Closing shift already exists for POS Opening Shift '{0}'").format(opening_shift_name))

        # Validate user permissions
        if not frappe.has_permission("POS Closing Shift", "create"):
            frappe.throw(_("Not permitted to create POS Closing Shift"))

        if not frappe.has_permission("POS Closing Shift", "submit"):
            frappe.throw(_("Not permitted to submit POS Closing Shift"))

        # Validate payment reconciliation data
        payment_reconciliation = closing_shift_data.get('payment_reconciliation', [])
        for idx, payment in enumerate(payment_reconciliation):
            closing_amount = payment.get('closing_amount')
            opening_amount = payment.get('opening_amount', 0)
            expected_amount = payment.get('expected_amount', 0)

            # Check if transactions occurred (expected_amount != opening_amount), then closing amount cannot be 0
            if flt(expected_amount) != flt(opening_amount):
                if flt(closing_amount) == 0:
                    frappe.throw(_("Closing amount cannot be 0 when transactions occurred for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))

            if closing_amount is None or closing_amount == '' or closing_amount == 0:
                frappe.throw(_("Closing amount is required and must be greater than 0 for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))

            # Validate it's a number
            try:
                closing_amount = float(closing_amount)
                if closing_amount <= 0:
                    frappe.throw(_("Closing amount must be greater than 0 for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))
                # Update the data with validated value
                payment['closing_amount'] = closing_amount
            except (ValueError, TypeError):
                frappe.throw(_("Closing amount must be a valid number for payment method '{0}'").format(payment.get('mode_of_payment', 'Unknown')))

        # Create and submit closing shift document
        closing_shift_doc = frappe.get_doc(closing_shift_data)
        closing_shift_doc.submit()

        return {
            "success": True,
            "message": _("POS Closing Shift submitted successfully"),
            "data": {
                "name": closing_shift_doc.name,
                "docstatus": closing_shift_doc.docstatus
            }
        }

    except frappe.ValidationError:
        raise
    except Exception as e:
        frappe.log_error(f"Unexpected error in submit_closing_shift: {str(e)}",
                         "POS Closing Shift Submit Error")

        return {
            "success": False,
            "message": _("An unexpected error occurred while submitting closing shift: {0}").format(str(e))
        }


def submit_printed_invoices(pos_opening_shift):
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

        for invoice in invoices_list:
            try:
                invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
                invoice_doc.submit()
            except Exception as e:
                continue

    except Exception as e:
        frappe.log_error(f"Error submitting printed invoices for shift {pos_opening_shift}: {str(e)}")