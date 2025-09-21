# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from posawesome.posawesome.utils.logging import get_logger
from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import _parse_json_safe

log = get_logger("shift_close")


class POSClosingShift(Document):
    def validate(self):
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
            shift_report = frappe.db.get_value("POS Shift Report", {"pos_opening_shift": self.pos_opening_shift}, "name")
            if shift_report:
                self.shift_report = shift_report
            else:
                frappe.throw(_("No shift report found for this opening shift. Please ensure shift report is created before closing shift."))

        self.update_payment_reconciliation()

    def update_payment_reconciliation(self):
        # update the difference values in Payment Reconciliation child table
        precision = frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        for d in self.payment_reconciliation:
            d.difference = flt(d.closing_amount, precision) - flt(d.expected_amount, precision)

    def on_submit(self):
        # Validate shift report verification status before submission
        if self.shift_report:
            shift_report_status = frappe.db.get_value("POS Shift Report", self.shift_report, "verification_status")
            if shift_report_status not in ["Verified", "Confirmed"]:
                frappe.throw(_("Shift must be verified before closing. Please verify the shift report first."))

        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        opening_entry.save()

        self.delete_draft_invoices()

        # Update shift report and payment summaries
        self.update_shift_report_and_summaries()

        # link invoices with this closing shift so ERPNext can block edits
        self._set_closing_entry_invoices()

        # POS Invoice consolidation removed - only use Sales Invoice

    def update_shift_report_and_summaries(self):
        """Update POS Shift Report and Payment Summaries with closing data"""
        if not self.shift_report:
            return

        shift_report = frappe.get_doc("POS Shift Report", self.shift_report)

        # Get payment summaries
        from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import get_payment_summaries_for_shift
        summaries_result = get_payment_summaries_for_shift(shift_report.name)

        if not summaries_result.get("success") or not summaries_result.get("data"):
            frappe.throw(_("No payment summaries found. Shift must be verified with payment summaries before closing."))

        summaries = summaries_result["data"]

        # Update closing amounts in payment summaries
        closing_amounts_map = {}
        for payment in self.payment_reconciliation:
            method = payment.get("mode_of_payment")
            closing_amount = flt(payment.get("closing_amount", 0))
            if method:
                closing_amounts_map[method] = closing_amount

        for summary in summaries:
            method = summary.get("payment_method")
            if method and method in closing_amounts_map:
                closing_amount = closing_amounts_map[method]
                frappe.db.set_value("POS Payment Summary",
                    {"shift_report_id": self.shift_report, "payment_method": method},
                    {
                        "closing_amount": closing_amount,
                        "difference": flt(summary.get("expected_closing_amount", 0)) - closing_amount,
                        "shift_end_time": self.period_end_date
                    }
                )

        # Update shift report
        total_actual_closing = sum(flt(s.get("closing_amount", 0)) for s in summaries)

        # Get existing expected amounts from shift report (already calculated during verification)
        existing_expected = _parse_json_safe(shift_report.expected_closing_amounts or "{}")
        total_expected_closing = sum(existing_expected.values())
        difference = total_actual_closing - total_expected_closing

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

        try:
            shift_report.save(ignore_permissions=True)
        except frappe.ValidationError as ve:
            if "Status cannot be" in str(ve) and "Paid" in str(ve):
                shift_report.flags.ignore_validate = True
                shift_report.save(ignore_permissions=True)
            else:
                raise

    def on_cancel(self):
        if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            if opening_entry.pos_closing_shift == self.name:
                opening_entry.pos_closing_shift = ""
                opening_entry.set_status()
                opening_entry.save()

        self._clear_closing_entry_invoices()

    def _clear_closing_entry_invoices(self):
        """Clear closing shift links, cancel merge logs and cancel consolidated sales invoices."""
        sales_invoices = set()
        for d in self.pos_transactions:
            pos_invoice = d.get("pos_invoice")
            sales_invoice = d.get("sales_invoice")
            if pos_invoice:
                if frappe.db.has_column("POS Invoice", "pos_closing_entry"):
                    frappe.db.set_value("POS Invoice", pos_invoice, "pos_closing_entry", None)

                merge_logs = frappe.get_all(
                    "POS Invoice Merge Log",
                    filters={"pos_invoice": pos_invoice},
                    pluck="name",
                )
                for log in merge_logs:
                    log_doc = frappe.get_doc("POS Invoice Merge Log", log)
                    for field in (
                        "consolidated_invoice",
                        "consolidated_credit_note",
                    ):
                        si = log_doc.get(field)
                        if si:
                            sales_invoices.add(si)
                    if log_doc.docstatus == 1:
                        log_doc.cancel()
                    frappe.delete_doc("POS Invoice Merge Log", log_doc.name, force=1)

                if frappe.db.has_column("POS Invoice", "consolidated_invoice"):
                    frappe.db.set_value("POS Invoice", pos_invoice, "consolidated_invoice", None)

                if frappe.db.has_column("POS Invoice", "status"):
                    pos_doc = frappe.get_doc("POS Invoice", pos_invoice)
                    pos_doc.set_status(update=True)

            if sales_invoice:
                if frappe.db.has_column("Sales Invoice", "pos_closing_entry"):
                    frappe.db.set_value("Sales Invoice", sales_invoice, "pos_closing_entry", None)
                sales_invoices.add(sales_invoice)

        for si in sales_invoices:
            if frappe.db.exists("Sales Invoice", si):
                si_doc = frappe.get_doc("Sales Invoice", si)
                if si_doc.docstatus == 1:
                    si_doc.cancel()

    def _set_closing_entry_invoices(self):
        """Set `pos_closing_entry` on linked invoices."""
        for d in self.pos_transactions:
            invoice = d.get("sales_invoice") or d.get("pos_invoice")
            if not invoice:
                continue
            doctype = "Sales Invoice" if d.get("sales_invoice") else "POS Invoice"
            if frappe.db.has_column(doctype, "pos_closing_entry"):
                frappe.db.set_value(doctype, invoice, "pos_closing_entry", self.name)

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            # Only handle Sales Invoice (POS Invoice logic removed)
            doctype = "Sales Invoice"
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

            for invoice in data:
                frappe.delete_doc(doctype, invoice.name, force=1)

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


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    opening_shift = json.loads(opening_shift)
    # Default to Sales Invoice (POS Invoice logic removed)
    doctype = "Sales Invoice"
    submit_printed_invoices(opening_shift.get("name"), doctype)
    closing_shift = frappe.new_doc("POS Closing Shift")
    closing_shift.pos_opening_shift = opening_shift.get("name")
    closing_shift.period_start_date = opening_shift.get("period_start_date")
    closing_shift.period_end_date = frappe.utils.get_datetime()
    closing_shift.pos_profile = opening_shift.get("pos_profile")
    closing_shift.user = opening_shift.get("user")
    closing_shift.company = opening_shift.get("company")
    closing_shift.grand_total = 0
    closing_shift.net_total = 0
    closing_shift.total_quantity = 0

    invoices = get_pos_invoices(opening_shift.get("name"), doctype)

    pos_transactions = []
    taxes = []
    payments = []
    pos_payments_table = []
    for detail in opening_shift.get("balance_details"):
        payments.append(
            frappe._dict(
                {
                    "mode_of_payment": detail.get("mode_of_payment"),
                    "opening_amount": detail.get("amount") or 0,
                    "expected_amount": detail.get("amount") or 0,
                }
            )
        )

    invoice_field = "pos_invoice" if doctype == "POS Invoice" else "sales_invoice"

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

        for p in d.payments:
            existing_pay = [pay for pay in payments if pay.mode_of_payment == p.mode_of_payment]
            if existing_pay:
                cash_mode_of_payment = frappe.get_value(
                    "POS Profile",
                    opening_shift.get("pos_profile"),
                    "posa_cash_mode_of_payment",
                )
                if not cash_mode_of_payment:
                    cash_mode_of_payment = "Cash"
                if existing_pay[0].mode_of_payment == cash_mode_of_payment:
                    amount = p.amount - d.change_amount
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

    pos_payments = get_payments_entries(opening_shift.get("name"))

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

    closing_shift.set("pos_transactions", pos_transactions)
    closing_shift.set("payment_reconciliation", payments)
    closing_shift.set("taxes", taxes)
    closing_shift.set("pos_payments", pos_payments_table)

    return closing_shift


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    closing_shift = json.loads(closing_shift)
    closing_shift_doc = frappe.get_doc(closing_shift)
    closing_shift_doc.flags.ignore_permissions = True
    closing_shift_doc.save()
    closing_shift_doc.submit()
    return closing_shift_doc.name


def submit_printed_invoices(pos_opening_shift, doctype):
    invoices_list = frappe.get_all(
        doctype,
        filters={
            "posa_pos_opening_shift": pos_opening_shift,
            "docstatus": 0,
            "posa_is_printed": 1,
        },
    )
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc(doctype, invoice.name)
        invoice_doc.submit()