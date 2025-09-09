import frappe
from frappe import _
from frappe.model.document import Document

class POSShiftReportInvoice(Document):
	def validate(self):
		"""Validate POS Shift Report Invoice"""
		self.validate_invoice_data()
		self.update_payment_method()

	def validate_invoice_data(self):
		"""Validate invoice data"""
		if not self.invoice_no:
			frappe.throw(_("Invoice No is required"))

		# Check if invoice exists
		if not frappe.db.exists("Sales Invoice", self.invoice_no):
			frappe.throw(_("Sales Invoice {0} not found").format(self.invoice_no))

		# Get invoice data
		invoice = frappe.get_doc("Sales Invoice", self.invoice_no)

		# Update fields from invoice
		self.invoice_date = invoice.posting_date
		self.invoice_time = invoice.posting_time
		self.customer = invoice.customer
		self.total_amount = invoice.grand_total
		self.paid_amount = invoice.paid_amount or 0
		self.is_return = invoice.is_return or False
		self.status = invoice.status

		# Calculate tax amount
		self.tax_amount = self.calculate_tax_amount(invoice)

	def update_payment_method(self):
		"""Update payment method from invoice payments"""
		if not self.invoice_no:
			return

		# Get payment entries for this invoice
		payments = frappe.get_all("Payment Entry Reference",
			filters={"reference_name": self.invoice_no},
			fields=["parent"]
		)

		if payments:
			payment_entry = frappe.get_doc("Payment Entry", payments[0].parent)
			if payment_entry.payment_type == "Receive":
				self.payment_method = payment_entry.mode_of_payment or "Cash"
			else:
				self.payment_method = "Cash"  # Default for returns
		else:
			self.payment_method = "Cash"  # Default

	def calculate_tax_amount(self, invoice):
		"""Calculate total tax amount from invoice"""
		total_tax = 0

		if invoice.taxes:
			for tax in invoice.taxes:
				total_tax += tax.tax_amount or 0

		return total_tax

	def before_save(self):
		"""Actions before saving"""
		# Ensure data is up to date with invoice
		if self.invoice_no and not self.invoice_date:
			self.validate_invoice_data()