# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


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
		self.update_payment_reconciliation()

	def update_payment_reconciliation(self):
		"""Update payment reconciliation with enhanced calculations"""
		# Get default precision for site
		precision = frappe.get_cached_value("System Settings", None, "currency_precision") or 3

		# Calculate differences for child table
		for d in self.payment_reconciliation:
			d.difference = flt(d.closing_amount, precision) - flt(d.expected_amount, precision)

		# Calculate and store amounts as JSON for reporting
		self.calculate_payment_amounts()

	def calculate_payment_amounts(self):
		"""Calculate expected, actual, and difference amounts as JSON"""
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
			frappe.logger().warning(f"Failed to calculate payment amounts for {self.name}: {str(e)}")
			# Set empty JSON objects as fallback
			self.expected_amounts = "{}"
			self.actual_amounts = "{}"
			self.difference_amounts = "{}"

	def on_submit(self):
		"""Enhanced on_submit with Shift Report integration"""
		try:
			# Update opening shift reference
			opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
			opening_entry.pos_closing_shift = self.name
			opening_entry.set_status()
			opening_entry.save()

			# Delete draft invoices
			self.delete_draft_invoices()

			# Update verification status based on business rules
			self.update_verification_status()

			# Log successful submission
			frappe.logger().info(f"POS Closing Shift {self.name} submitted successfully")

		except Exception as e:
			frappe.logger().error(f"Error in POS Closing Shift on_submit for {self.name}: {str(e)}")
			# Don't raise error here as it might prevent submission
			# Just log the error for debugging

	def update_verification_status(self):
		"""Update verification status based on business rules"""
		try:
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

			# Save the verification status
			self.save(ignore_permissions=True)

		except Exception as e:
			frappe.logger().warning(f"Failed to update verification status for {self.name}: {str(e)}")
			self.verification_status = "Pending"

	def on_cancel(self):
		if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
			opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
			if opening_entry.pos_closing_shift == self.name:
				opening_entry.pos_closing_shift = ""
				opening_entry.set_status()
				opening_entry.save()

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
	Get POS invoices with optimized queries and batch processing

	Args:
		pos_opening_shift (str): Opening shift name

	Returns:
		list: List of invoice dictionaries
	"""
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
		batch_size = 50
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
					frappe.logger().warning(f"Failed to process invoice {invoice.name}: {str(e)}")
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
	opening_shift = json.loads(opening_shift)
	submit_printed_invoices(opening_shift.get("name"))
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

	invoices = get_pos_invoices(opening_shift.get("name"))

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

	for d in invoices:
		pos_transactions.append(
			frappe._dict(
				{
					"sales_invoice": d.name,
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
	"""
	Submit POS Closing Shift with comprehensive error handling and validation

	Args:
		closing_shift (str): JSON string containing closing shift data

	Returns:
		dict: Result with success status and data
	"""
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
			frappe.throw(_("POS Opening Shift '{0}' is not open (current status: {1})").format(
				opening_shift_name, opening_shift.status))

		# Check if closing shift already exists
		existing_closing = frappe.db.exists("POS Closing Shift", {
			"pos_opening_shift": opening_shift_name,
			"docstatus": ["!=", 2]  # Not cancelled
		})

		if existing_closing:
			frappe.throw(_("Closing shift already exists for POS Opening Shift '{0}'").format(opening_shift_name))

		# Validate user permissions (without ignore_permissions)
		if not frappe.has_permission("POS Closing Shift", "create"):
			frappe.throw(_("Not permitted to create POS Closing Shift"))

		if not frappe.has_permission("POS Closing Shift", "submit"):
			frappe.throw(_("Not permitted to submit POS Closing Shift"))

		# Create closing shift document
		try:
			closing_shift_doc = frappe.get_doc(closing_shift_data)
		except Exception as e:
			frappe.throw(_("Failed to create closing shift document: {0}").format(str(e)))

		# Save document (without ignore_permissions for security)
		try:
			closing_shift_doc.save()
		except frappe.ValidationError:
			# Re-raise validation errors as-is
			raise
		except Exception as e:
			frappe.throw(_("Failed to save closing shift: {0}").format(str(e)))

		# Submit document
		try:
			closing_shift_doc.submit()
		except frappe.ValidationError:
			# Re-raise validation errors as-is
			raise
		except Exception as e:
			# Attempt to cancel the saved document if submit fails
			try:
				if closing_shift_doc.docstatus == 0:
					closing_shift_doc.cancel()
			except:
				pass  # Ignore cleanup errors

			frappe.throw(_("Failed to submit closing shift: {0}").format(str(e)))

		# Log success
		frappe.logger().info(f"POS Closing Shift {closing_shift_doc.name} submitted successfully by user {frappe.session.user}")

		return {
			"success": True,
			"message": _("POS Closing Shift submitted successfully"),
			"data": {
				"name": closing_shift_doc.name,
				"status": closing_shift_doc.status
			}
		}

	except frappe.ValidationError:
		# Re-raise validation errors as-is (they contain user-friendly messages)
		raise
	except Exception as e:
		# Log unexpected errors
		frappe.log_error(f"Unexpected error in submit_closing_shift: {str(e)}",
						"POS Closing Shift Submit Error")

		return {
			"success": False,
			"message": _("An unexpected error occurred while submitting closing shift: {0}").format(str(e))
		}


def submit_printed_invoices(pos_opening_shift):
	invoices_list = frappe.get_all(
		"Sales Invoice",
		filters={
			"posa_pos_opening_shift": pos_opening_shift,
			"docstatus": 0,
			"posa_is_printed": 1,
		},
	)
	for invoice in invoices_list:
		invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
		invoice_doc.submit()
