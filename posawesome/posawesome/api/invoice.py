# -*- coding: utf-8 -*-
# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, add_days
from posawesome.posawesome.doctype.pos_coupon.pos_coupon import update_coupon_code_count
from posawesome.posawesome.api.utilities import get_company_domain  # Updated import
from posawesome.posawesome.doctype.delivery_charges.delivery_charges import (
	get_applicable_delivery_charges,
)
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("invoice")


def validate(doc, method):
	validate_shift(doc)
	set_patient(doc)
	auto_set_delivery_charges(doc)
	calc_delivery_charges(doc)
	apply_tax_inclusive(doc)
	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
		log.info(f"[INVOICE_TRACKING] 🔄 ON_SUBMIT - Calling update_shift_report_with_invoice - Invoice: {doc.name}, Action: submit")
		update_shift_report_with_invoice(doc, "Paid")
	else:
		log.warning(f"[INVOICE_TRACKING] ⚠️ ON_SUBMIT - No shift report reference - Invoice: {doc.name}")

	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
		log.info(f"[INVOICE_TRACKING] 🔄 ON_CANCEL - Calling update_shift_report_with_invoice - Invoice: {doc.name}, Action: cancel")
		update_shift_report_with_invoice(doc, "Cancelled")
	else:
		log.warning(f"[INVOICE_TRACKING] ⚠️ ON_CANCEL - No shift report reference - Invoice: {doc.name}")


def before_submit(doc, method):
	add_loyalty_point(doc)
	create_sales_order(doc)
	update_coupon(doc, "used")


# def on_submit(doc, method):
# 	"""Update shift report when invoice is submitted"""
# 	# DEBUG: Add multiple log levels to ensure visibility
# 	log.debug(f"🔥 ON SUBMIT on_submit called for {doc.name}")
# 	print(f"🔥 DEBUG PRINT: on_submit called for {doc.name}")
# 	log.debug(f"[INVOICE_TRACKING] 🔍 DEBUG - on_submit called - Method: {method}")
# 	log.info(f"[INVOICE_TRACKING] 📤 ON_SUBMIT - Invoice: {doc.name}, Status: {doc.status}, Amount: {doc.grand_total}, Shift Report: {getattr(doc, 'pos_shift_report', 'None')}")
# 	log.warning(f"[INVOICE_TRACKING] ⚠️ WARNING - on_submit executed for invoice {doc.name}")

# 	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
# 		log.info(f"[INVOICE_TRACKING] 🔄 ON_SUBMIT - Calling update_shift_report_with_invoice - Invoice: {doc.name}, Action: submit")
# 		update_shift_report_with_invoice(doc, "Paid")
# 	else:
# 		log.warning(f"[INVOICE_TRACKING] ⚠️ ON_SUBMIT - No shift report reference - Invoice: {doc.name}")

# def on_cancel(doc, method):
# 	"""Update shift report when invoice is cancelled"""
# 	log.info(f"[INVOICE_TRACKING] 🗑️ ON_CANCEL - Invoice: {doc.name}, Status: {doc.status}, Amount: {doc.grand_total}, Shift Report: {getattr(doc, 'pos_shift_report', 'None')}")

# 	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
# 		log.info(f"[INVOICE_TRACKING] 🔄 ON_CANCEL - Calling update_shift_report_with_invoice - Invoice: {doc.name}, Action: cancel")
# 		update_shift_report_with_invoice(doc, "Cancelled")
# 	else:
# 		log.warning(f"[INVOICE_TRACKING] ⚠️ ON_CANCEL - No shift report reference - Invoice: {doc.name}")

def before_cancel(doc, method):
	update_coupon(doc, "Cancelled")

def add_loyalty_point(invoice_doc):
	for offer in invoice_doc.posa_offers:
		if offer.offer == "Loyalty Point":
			original_offer = frappe.get_doc("POS Offer", offer.offer_name)
			if original_offer.loyalty_points > 0:
				loyalty_program = frappe.get_value("Customer", invoice_doc.customer, "loyalty_program")
				if not loyalty_program:
					loyalty_program = original_offer.loyalty_program
				doc = frappe.get_doc(
					{
						"doctype": "Loyalty Point Entry",
						"loyalty_program": loyalty_program,
						"loyalty_program_tier": original_offer.name,
						"customer": invoice_doc.customer,
						"invoice_type": "Sales Invoice",
						"invoice": invoice_doc.name,
						"loyalty_points": original_offer.loyalty_points,
						"expiry_date": add_days(invoice_doc.posting_date, 10000),
						"posting_date": invoice_doc.posting_date,
						"company": invoice_doc.company,
					}
				)
				doc.insert(ignore_permissions=True)


def create_sales_order(doc):
	if (
		doc.posa_pos_opening_shift
		and doc.pos_profile
		and doc.is_pos
		and doc.posa_delivery_date
		and not doc.update_stock
		and frappe.get_value("POS Profile", doc.pos_profile, "posa_allow_sales_order")
	):
		sales_order_doc = make_sales_order(doc.name)
		if sales_order_doc:
			sales_order_doc.posa_notes = doc.posa_notes
			sales_order_doc.flags.ignore_permissions = True
			sales_order_doc.flags.ignore_account_permission = True
			sales_order_doc.save()
			sales_order_doc.submit()
			url = frappe.utils.get_url_to_form(sales_order_doc.doctype, sales_order_doc.name)
			msgprint = "Sales Order Created at <a href='{0}'>{1}</a>".format(url, sales_order_doc.name)
			frappe.msgprint(_(msgprint), title="Sales Order Created", indicator="green", alert=True)
			i = 0
			for item in sales_order_doc.items:
				doc.items[i].sales_order = sales_order_doc.name
				doc.items[i].so_detail = item.name
				i += 1


def make_sales_order(source_name, target_doc=None, ignore_permissions=True):
	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)
		target.delivery_date = obj.posa_delivery_date or source_parent.posa_delivery_date

	doclist = get_mapped_doc(
		"Sales Invoice",
		source_name,
		{
			"Sales Invoice": {
				"doctype": "Sales Order",
			},
			"Sales Invoice Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					"cost_center": "cost_center",
					"Warehouse": "warehouse",
					"delivery_date": "posa_delivery_date",
					"posa_notes": "posa_notes",
				},
				"postprocess": update_item,
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"add_if_empty": True,
			},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
			"Payment Schedule": {"doctype": "Payment Schedule", "add_if_empty": True},
		},
		target_doc,
		set_missing_values,
		ignore_permissions=ignore_permissions,
	)

	return doclist


def update_coupon(doc, transaction_type):
	for coupon in doc.posa_coupons:
		if not coupon.applied:
			continue
		update_coupon_code_count(coupon.coupon, transaction_type)


def set_patient(doc):
	domain = get_company_domain(doc.company)
	if domain != "Healthcare":
		return
	patient_list = frappe.get_all("Patient", filters={"customer": doc.customer}, page_length=1)
	if len(patient_list) > 0:
		doc.patient = patient_list[0].name


def auto_set_delivery_charges(doc):
	if not doc.pos_profile:
		return
	if not frappe.get_cached_value("POS Profile", doc.pos_profile, "posa_auto_set_delivery_charges"):
		return

	delivery_charges = get_applicable_delivery_charges(
		doc.company,
		doc.pos_profile,
		doc.customer,
		doc.shipping_address_name,
		doc.posa_delivery_charges,
		restrict=True,
	)

	if doc.posa_delivery_charges:
		if doc.posa_delivery_charges_rate:
			return
		else:
			if len(delivery_charges) > 0:
				doc.posa_delivery_charges_rate = delivery_charges[0].rate
	else:
		if len(delivery_charges) > 0:
			doc.posa_delivery_charges = delivery_charges[0].name
			doc.posa_delivery_charges_rate = delivery_charges[0].rate
		else:
			doc.posa_delivery_charges = None
			doc.posa_delivery_charges_rate = None


def calc_delivery_charges(doc):
	if not doc.pos_profile:
		return

	old_doc = None
	calculate_taxes_and_totals = False
	if not doc.is_new():
		old_doc = doc.get_doc_before_save()
		if not doc.posa_delivery_charges and not old_doc.posa_delivery_charges:
			return
	else:
		if not doc.posa_delivery_charges:
			return
	if not doc.posa_delivery_charges:
		doc.posa_delivery_charges_rate = 0

	charges_doc = None
	if doc.posa_delivery_charges:
		charges_doc = frappe.get_cached_doc("Delivery Charges", doc.posa_delivery_charges)
		doc.posa_delivery_charges_rate = charges_doc.default_rate
		charges_profile = next((i for i in charges_doc.profiles if i.pos_profile == doc.pos_profile), None)
		if charges_profile:
			doc.posa_delivery_charges_rate = charges_profile.rate

	if old_doc and old_doc.posa_delivery_charges:
		old_charges = next(
			(
				i
				for i in doc.taxes
				if i.charge_type == "Actual" and i.description == old_doc.posa_delivery_charges
			),
			None,
		)
		if old_charges:
			doc.taxes.remove(old_charges)
			calculate_taxes_and_totals = True

	if doc.posa_delivery_charges:
		doc.append(
			"taxes",
			{
				"charge_type": "Actual",
				"description": doc.posa_delivery_charges,
				"tax_amount": doc.posa_delivery_charges_rate,
				"cost_center": charges_doc.cost_center,
				"account_head": charges_doc.shipping_account,
			},
		)
		calculate_taxes_and_totals = True

	if calculate_taxes_and_totals:
		doc.calculate_taxes_and_totals()


def apply_tax_inclusive(doc):
	"""Mark taxes as inclusive based on POS Profile setting."""
	if not doc.pos_profile:
		return
	try:
		tax_inclusive = frappe.get_cached_value("POS Profile", doc.pos_profile, "posa_tax_inclusive")
	except Exception:
		tax_inclusive = 0

	if not tax_inclusive:
		return

	has_changes = False
	for tax in doc.get("taxes", []):
		if not tax.included_in_print_rate:
			tax.included_in_print_rate = 1
			has_changes = True

	if has_changes:
		doc.calculate_taxes_and_totals()


def get_invoice_payment_method(invoice_doc):
	"""
	Get primary payment method from invoice payments

	Args:
		invoice_doc: Sales Invoice document

	Returns:
		str: Payment method name
	"""
	try:
		# Check if invoice has payments
		if hasattr(invoice_doc, 'payments') and invoice_doc.payments:
			# Get the first payment method (primary payment)
			for payment in invoice_doc.payments:
				if payment.amount > 0:
					return payment.mode_of_payment or "Cash"

		# Fallback: Check payment entries linked to this invoice
		payment_entries = frappe.get_all("Payment Entry Reference",
			filters={"reference_name": invoice_doc.name, "reference_doctype": "Sales Invoice"},
			fields=["parent"]
		)

		if payment_entries:
			payment_entry = frappe.get_doc("Payment Entry", payment_entries[0].parent)
			if payment_entry.payment_type == "Receive" and payment_entry.paid_amount > 0:
				return payment_entry.mode_of_payment or "Cash"

		# Default fallback
		return "Cash"

	except Exception as e:
		log.error(f"Error getting payment method for invoice {invoice_doc.name}: {str(e)}")
		return "Cash"


def validate_shift(doc):
	if doc.posa_pos_opening_shift and doc.pos_profile and doc.is_pos:
		# LOG: Start validation
		log.info(f"[INVOICE_TRACKING] 🔍 VALIDATE_SHIFT - Invoice: {doc.name}, Opening Shift: {doc.posa_pos_opening_shift}")

		# check if shift is open
		shift = frappe.get_cached_doc("POS Opening Shift", doc.posa_pos_opening_shift)
		if shift.status != "Open":
			log.error(f"[INVOICE_TRACKING] ❌ VALIDATE_SHIFT - Shift not open - Invoice: {doc.name}, Shift: {shift.name}, Status: {shift.status}")
			frappe.throw(_("POS Shift {0} is not open").format(shift.name))

		# check if shift is for the same profile
		if shift.pos_profile != doc.pos_profile:
			log.error(f"[INVOICE_TRACKING] ❌ VALIDATE_SHIFT - Profile mismatch - Invoice: {doc.name}, Invoice Profile: {doc.pos_profile}, Shift Profile: {shift.pos_profile}")
			frappe.throw(_("POS Opening Shift {0} is not for the same POS Profile").format(shift.name))

		# check if shift is for the same company
		if shift.company != doc.company:
			log.error(f"[INVOICE_TRACKING] ❌ VALIDATE_SHIFT - Company mismatch - Invoice: {doc.name}, Invoice Company: {doc.company}, Shift Company: {shift.company}")
			frappe.throw(_("POS Opening Shift {0} is not for the same company").format(shift.name))

		# Set shift report reference if available
		if hasattr(shift, 'shift_report') and shift.shift_report:
			doc.pos_shift_report = shift.shift_report
			doc.shift_report_id = shift.shift_report_id
			log.info(f"[INVOICE_TRACKING] ✅ VALIDATE_SHIFT - Set shift report reference - Invoice: {doc.name}, Shift Report: {shift.shift_report}, Shift Report ID: {shift.shift_report_id}")
		else:
			log.warning(f"[INVOICE_TRACKING] ⚠️ VALIDATE_SHIFT - No shift report found - Invoice: {doc.name}, Opening Shift: {doc.posa_pos_opening_shift}")
			log.info(f"[INVOICE_TRACKING] ℹ️ VALIDATE_SHIFT - Shift details - Name: {shift.name}, Status: {shift.status}, Has shift_report attr: {hasattr(shift, 'shift_report')}")


def update_shift_report_with_invoice(invoice_doc, action):
	"""
	Update shift report when invoice is submitted or cancelled

	Args:
		invoice_doc: Sales Invoice document
		action: "Paid" or "Cancelled"
	"""
	# LOG: Start update process
	log.info(f"[INVOICE_TRACKING] 🎯 UPDATE_SHIFT_REPORT - Start - Invoice: {invoice_doc.name}, Action: {action}, Status: {invoice_doc.status}, Amount: {invoice_doc.grand_total}")

	try:
		if not hasattr(invoice_doc, 'pos_shift_report') or not invoice_doc.pos_shift_report:
			log.warning(f"[INVOICE_TRACKING] ❌ UPDATE_SHIFT_REPORT - No shift report reference - Invoice: {invoice_doc.name}")
			return

		log.info(f"[INVOICE_TRACKING] 📋 UPDATE_SHIFT_REPORT - Getting shift report - Invoice: {invoice_doc.name}, Shift Report: {invoice_doc.pos_shift_report}")

		# Get shift report
		shift_report = frappe.get_doc("POS Shift Report", invoice_doc.pos_shift_report)

		log.info(f"[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - Got shift report - Invoice: {invoice_doc.name}, Shift Report: {shift_report.name}, Current Count: {shift_report.invoice_count}, Current Sales: {shift_report.total_sales}, Current Returns: {shift_report.total_returns}")

		if action == "Paid":
			log.info(f"[INVOICE_TRACKING] ➕ UPDATE_SHIFT_REPORT - Processing SUBMIT - Invoice: {invoice_doc.name}")

			# Add invoice to shift report
			existing_invoice = None
			for inv in shift_report.invoices:
				if inv.invoice_no == invoice_doc.name:
					existing_invoice = inv
					break

			if existing_invoice:
				log.info(f"[INVOICE_TRACKING] ⚠️ UPDATE_SHIFT_REPORT - Invoice already exists in shift report - Invoice: {invoice_doc.name}, Existing Status: {existing_invoice.status}")
			else:
				# Get payment method from invoice payments
				payment_method = get_invoice_payment_method(invoice_doc)
				log.info(f"[INVOICE_TRACKING] 💳 UPDATE_SHIFT_REPORT - Payment method detected - Invoice: {invoice_doc.name}, Method: {payment_method}")

				# Add new invoice entry
				shift_report.append("invoices", {
					"invoice_no": invoice_doc.name,
					"invoice_date": invoice_doc.posting_date,
					"invoice_time": invoice_doc.posting_time,
					"customer": invoice_doc.customer,
					"total_amount": invoice_doc.grand_total,
					"paid_amount": invoice_doc.paid_amount or 0,
					"tax_amount": invoice_doc.total_taxes_and_charges or 0,
					"payment_method": payment_method,
					"is_return": invoice_doc.is_return or False,
					"status": "Paid"
				})
				log.info(f"[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - Added invoice to shift report - Invoice: {invoice_doc.name}, Shift Report: {shift_report.name}, Payment Method: {payment_method}, Amount: {invoice_doc.grand_total}")

		elif action == "Cancelled":
			log.info(f"[INVOICE_TRACKING] ❌ UPDATE_SHIFT_REPORT - Processing CANCEL - Invoice: {invoice_doc.name}")

			# Remove invoice from shift report or mark as cancelled
			found = False
			for inv in shift_report.invoices:
				if inv.invoice_no == invoice_doc.name:
					old_status = inv.status
					inv.status = "Cancelled"
					found = True
					log.info(f"[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - Marked invoice as cancelled - Invoice: {invoice_doc.name}, Shift Report: {shift_report.name}, Old Status: {old_status}, New Status: Cancelled")
					break

			if not found:
				log.warning(f"[INVOICE_TRACKING] ⚠️ UPDATE_SHIFT_REPORT - Invoice not found in shift report - Invoice: {invoice_doc.name}, Shift Report: {shift_report.name}")

		# Update calculated fields
		log.info(f"[INVOICE_TRACKING] 🔢 UPDATE_SHIFT_REPORT - Updating calculated fields - Invoice: {invoice_doc.name}, Shift Report: {shift_report.name}")
		log.info(f"[INVOICE_TRACKING] 📊 UPDATE_SHIFT_REPORT - Before update_calculated_fields - Invoice: {invoice_doc.name}, Count: {shift_report.invoice_count}, Sales: {shift_report.total_sales}, Returns: {shift_report.total_returns}")
		shift_report.update_calculated_fields()
		# log.info(f"[INVOICE_TRACKING] 📊 UPDATE_SHIFT_REPORT - After update_calculated_fields - Invoice: {invoice_doc.name}, Count: {shift_report.invoice_count}, Sales: {shift_report.total_sales}, Returns: {shift_report.total_returns}")

		# shift_report.get_payment_breakdown()
		# log.info(f"[INVOICE_TRACKING] 💰 UPDATE_SHIFT_REPORT - After get_payment_breakdown - Invoice: {invoice_doc.name}, Breakdown: {shift_report.payment_breakdown}")

		# Save shift report
		log.info(f"[INVOICE_TRACKING] 💾 UPDATE_SHIFT_REPORT - Saving shift report - Invoice: {invoice_doc.name}, Shift Report: {shift_report.name}")
		shift_report.save()
		frappe.db.commit()

		# Verify the changes were saved
		shift_report.reload()
		final_count = len(shift_report.invoices) if shift_report.invoices else 0
		log.info(f"[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - After save and reload - Invoice: {invoice_doc.name}, Final Count: {final_count}, Sales: {shift_report.total_sales}, Returns: {shift_report.total_returns}")

		log.info(f"[INVOICE_TRACKING] 🎉 UPDATE_SHIFT_REPORT - COMPLETED - Invoice: {invoice_doc.name}, Action: {action}, Shift Report: {shift_report.name}")

	except Exception as e:
		log.error(f"[INVOICE_TRACKING] 💥 UPDATE_SHIFT_REPORT - FAILED - Invoice: {invoice_doc.name}, Action: {action}, Error: {str(e)}")
		# Don't raise error to prevent invoice submission/cancellation failure
