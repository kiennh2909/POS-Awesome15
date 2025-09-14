import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime, get_datetime
import json
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("shift_report")

class POSShiftReport(Document):
	def validate(self):
		"""Validate POS Shift Report"""
		self.validate_shift_report_id()
		self.validate_dates()
		self.validate_amounts()
		self.update_calculated_fields()

	def before_submit(self):
		"""Actions before submitting the document"""
		if self.verification_status != "Confirmed":
			frappe.throw(_("Shift report must be confirmed before submission"))

		self.status = "Closed"
		self.closing_date = nowdate()
		self.closed_by = frappe.session.user

	def on_submit(self):
		"""Actions after submitting the document"""
		# Update related opening shift
		if self.pos_opening_shift:
			frappe.db.set_value("POS Opening Shift", self.pos_opening_shift, {
				"shift_report": self.name,
				"shift_report_id": self.shift_report_id
			})

		# Update related closing shift if exists
		closing_shifts = frappe.get_all("POS Closing Shift",
			filters={"pos_opening_shift": self.pos_opening_shift, "docstatus": 1}
		)
		if closing_shifts:
			frappe.db.set_value("POS Closing Shift", closing_shifts[0].name, {
				"shift_report": self.name
			})

	def validate_shift_report_id(self):
		"""Validate shift report ID format"""
		if not self.shift_report_id:
			self.shift_report_id = f"SHIFT-{self.pos_opening_shift}"

		# Check uniqueness
		existing = frappe.db.exists("POS Shift Report",
			{"shift_report_id": self.shift_report_id, "name": ["!=", self.name]}
		)
		if existing:
			frappe.throw(_("Shift Report ID {0} already exists").format(self.shift_report_id))

	def validate_dates(self):
		"""Validate date fields"""
		if self.opening_date and self.closing_date:
			if get_datetime(self.closing_date) < get_datetime(self.opening_date):
				frappe.throw(_("Closing date cannot be before opening date"))

	def validate_amounts(self):
		"""Validate amount fields"""
		# Validate opening amounts
		if self.opening_amounts:
			try:
				amounts = json.loads(self.opening_amounts)
				total = sum(float(amount) for amount in amounts.values() if amount)
				self.total_opening_amount = total
			except (json.JSONDecodeError, ValueError, TypeError):
				frappe.throw(_("Invalid opening amounts format"))

		# Validate expected closing amounts
		if self.expected_closing_amounts:
			try:
				amounts = json.loads(self.expected_closing_amounts)
				total = sum(float(amount) for amount in amounts.values() if amount)
				self.total_expected_closing = total
			except (json.JSONDecodeError, ValueError, TypeError):
				frappe.throw(_("Invalid expected closing amounts format"))

		# Validate actual closing amounts
		if self.actual_closing_amounts:
			try:
				amounts = json.loads(self.actual_closing_amounts)
				total = sum(float(amount) for amount in amounts.values() if amount)
				self.total_actual_closing = total
			except (json.JSONDecodeError, ValueError, TypeError):
				frappe.throw(_("Invalid actual closing amounts format"))

		# Calculate difference
		if self.total_expected_closing and self.total_actual_closing:
			self.difference = self.total_actual_closing - self.total_expected_closing

	def update_calculated_fields(self):
		"""Update calculated fields"""
		log.info(f"[SHIFT_REPORT_CALC] 🔢 UPDATE_CALCULATED_FIELDS - Start - Shift Report: {self.name}")

		# Update invoice count and totals from child table
		if self.invoices:
			self.invoice_count = len(self.invoices)
			total_sales = 0
			total_returns = 0

			log.info(f"[SHIFT_REPORT_CALC] 📊 UPDATE_CALCULATED_FIELDS - Processing {len(self.invoices)} invoices - Shift Report: {self.name}")

			for invoice in self.invoices:
				log.info(f"[SHIFT_REPORT_CALC] 📋 UPDATE_CALCULATED_FIELDS - Processing invoice: {invoice.invoice_no}, Status: {invoice.status}, Amount: {invoice.total_amount}, Is Return: {invoice.is_return}")

				# total_sales: only count Paid invoices (successful sales)
				if invoice.status == "Paid" and not invoice.is_return:
					total_sales += invoice.total_amount or 0
					log.info(f"[SHIFT_REPORT_CALC] 💰 UPDATE_CALCULATED_FIELDS - Added to total_sales: {invoice.total_amount} - Invoice: {invoice.invoice_no}")

				# total_returns: only count Cancelled invoices (cancelled transactions)
				if invoice.status == "Cancelled":
					total_returns += invoice.total_amount or 0
					log.info(f"[SHIFT_REPORT_CALC] 💸 UPDATE_CALCULATED_FIELDS - Added to total_returns: {invoice.total_amount} - Invoice: {invoice.invoice_no}")

			self.total_sales = total_sales
			self.total_returns = total_returns

			log.info(f"[SHIFT_REPORT_CALC] ✅ UPDATE_CALCULATED_FIELDS - Completed - Shift Report: {self.name}, Count: {self.invoice_count}, Sales: {self.total_sales}, Returns: {self.total_returns}")
		else:
			log.info(f"[SHIFT_REPORT_CALC] ⚠️ UPDATE_CALCULATED_FIELDS - No invoices found - Shift Report: {self.name}")

	def verify_report(self, verified_by=None):
		"""Mark report as verified"""
		if self.verification_status == "Pending":
			self.verification_status = "Verified"
			self.verification_date = nowdate()
			self.verified_by = verified_by or frappe.session.user
			self.save()

	def confirm_report(self, confirmed_by=None):
		"""Mark report as confirmed"""
		if self.verification_status == "Verified":
			self.verification_status = "Confirmed"
			self.confirmation_date = nowdate()
			self.confirmed_by = confirmed_by or frappe.session.user
			self.save()

	def get_payment_breakdown(self):
		"""Get payment method breakdown from invoices"""
		log.info(f"[SHIFT_REPORT_CALC] 💳 GET_PAYMENT_BREAKDOWN - Start - Shift Report: {self.name}")

		breakdown = {}

		if self.invoices:
			log.info(f"[SHIFT_REPORT_CALC] 💳 GET_PAYMENT_BREAKDOWN - Processing {len(self.invoices)} invoices - Shift Report: {self.name}")

			for invoice in self.invoices:
				# Only count Paid invoices for payment breakdown (exclude Cancelled)
				if invoice.status == "Paid":
					payment_method = invoice.payment_method or "Cash"
					amount = invoice.paid_amount or 0

					if payment_method in breakdown:
						breakdown[payment_method] += amount
					else:
						breakdown[payment_method] = amount

					log.info(f"[SHIFT_REPORT_CALC] 💳 GET_PAYMENT_BREAKDOWN - Added payment: {payment_method} = {amount} - Invoice: {invoice.invoice_no}")
				else:
					log.info(f"[SHIFT_REPORT_CALC] 🚫 GET_PAYMENT_BREAKDOWN - Skipped invoice (not Paid): {invoice.invoice_no}, Status: {invoice.status}")

		self.payment_breakdown = json.dumps(breakdown)

		log.info(f"[SHIFT_REPORT_CALC] ✅ GET_PAYMENT_BREAKDOWN - Completed - Shift Report: {self.name}, Breakdown: {breakdown}")

		return breakdown

	def update_from_invoices(self):
		"""Update report data from linked invoices"""
		if not self.pos_opening_shift:
			return

		# Get all invoices linked to this opening shift
		invoices = frappe.get_all("Sales Invoice",
			filters={
				"pos_opening_shift": self.pos_opening_shift,
				"docstatus": 1
			},
			fields=[
				"name", "posting_date", "posting_time", "customer",
				"grand_total", "paid_amount", "outstanding_amount",
				"is_return", "status"
			]
		)

		# Clear existing invoice entries
		self.invoices = []

		# Add invoice entries
		for invoice in invoices:
			self.append("invoices", {
				"invoice_no": invoice.name,
				"invoice_date": invoice.posting_date,
				"invoice_time": invoice.posting_time,
				"customer": invoice.customer,
				"total_amount": invoice.grand_total,
				"paid_amount": invoice.paid_amount,
				"tax_amount": 0,  # Will be calculated from invoice taxes
				"payment_method": "Cash",  # Default, will be updated from payments
				"is_return": invoice.is_return or False,
				"status": invoice.status
			})

		# Update calculated fields
		self.update_calculated_fields()
		self.get_payment_breakdown()

@frappe.whitelist()
def create_shift_report_from_opening(opening_shift_name):
	"""Create shift report from opening shift"""
	if not frappe.db.exists("POS Opening Shift", opening_shift_name):
		frappe.throw(_("Opening shift not found"))

	opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)

	# Check if shift report already exists
	existing_report = frappe.db.exists("POS Shift Report",
		{"pos_opening_shift": opening_shift_name}
	)

	if existing_report:
		frappe.throw(_("Shift report already exists for this opening shift"))

	# Create new shift report
	shift_report = frappe.get_doc({
		"doctype": "POS Shift Report",
		"shift_report_id": f"SHIFT-{opening_shift_name}",
		"pos_opening_shift": opening_shift_name,
		"opening_date": opening_shift.posting_date,
		"opening_time": opening_shift.posting_time,
		"opened_by": opening_shift.owner,
		"opening_amounts": "{}",
		"total_opening_amount": 0,
		"status": "Open"
	})

	shift_report.insert()
	return shift_report

@frappe.whitelist()
def get_shift_report_summary(shift_report_id):
	"""Get summary of shift report"""
	if not frappe.db.exists("POS Shift Report", shift_report_id):
		frappe.throw(_("Shift report not found"))

	report = frappe.get_doc("POS Shift Report", shift_report_id)

	return {
		"shift_report_id": report.shift_report_id,
		"status": report.status,
		"opening_date": report.opening_date,
		"opening_time": report.opening_time,
		"closing_date": report.closing_date,
		"total_opening_amount": report.total_opening_amount,
		"total_expected_closing": report.total_expected_closing,
		"total_actual_closing": report.total_actual_closing,
		"difference": report.difference,
		"invoice_count": report.invoice_count,
		"total_sales": report.total_sales,
		"total_returns": report.total_returns,
		"verification_status": report.verification_status,
		"payment_breakdown": json.loads(report.payment_breakdown or "{}")
	}