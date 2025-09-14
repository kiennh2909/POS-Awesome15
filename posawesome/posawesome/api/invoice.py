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
	log.info(f"[INVOICE_VALIDATION] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}, Amount: {doc.grand_total}")

	validate_shift(doc)
	set_patient(doc)
	auto_set_delivery_charges(doc)
	calc_delivery_charges(doc)
	apply_tax_inclusive(doc)

	log.info(f"[INVOICE_VALIDATION] ✅ COMPLETED - Invoice: {doc.name}")


# def before_submit(doc, method):
# 	log.info(f"[BEFORE_SUBMIT] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}, Amount: {doc.grand_total}")

# 	add_loyalty_point(doc)
# 	create_sales_order(doc)
# 	update_coupon(doc, "used")

# 	log.info(f"[BEFORE_SUBMIT] ✅ COMPLETED - Invoice: {doc.name}")

def before_submit(doc, method):
	log.info(f"[BEFORE_SUBMIT] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}, Amount: {doc.grand_total}")
	log.info(f"[BEFORE_SUBMIT] ✅ COMPLETED - Invoice: {doc.name}")


def on_submit(doc, method):
	"""Update shift report when invoice is submitted"""
	log.info(f"[INVOICE_TRACKING] 📤 ON_SUBMIT - Invoice: {doc.name}, Status: {doc.status}, Amount: {doc.grand_total}, Shift Report: {getattr(doc, 'pos_shift_report', 'None')}")

	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
		log.info(f"[INVOICE_TRACKING] 🔄 ON_SUBMIT - Calling update_shift_report_with_invoice - Invoice: {doc.name}, Action: submit")
		update_shift_report_with_invoice(doc, "submit")  # Use correct action
	else:
		log.warning(f"[INVOICE_TRACKING] ⚠️ ON_SUBMIT - No shift report reference - Invoice: {doc.name}")

def on_cancel(doc, method):
	"""Update shift report when invoice is cancelled"""
	log.info(f"[INVOICE_TRACKING] 🗑️ ON_CANCEL - Invoice: {doc.name}, Status: {doc.status}, Amount: {doc.grand_total}, Shift Report: {getattr(doc, 'pos_shift_report', 'None')}")

	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
		log.info(f"[INVOICE_TRACKING] 🔄 ON_CANCEL - Calling update_shift_report_with_invoice - Invoice: {doc.name}, Action: cancel")
		update_shift_report_with_invoice(doc, "cancel")  # Use correct action
	else:
		log.warning(f"[INVOICE_TRACKING] ⚠️ ON_CANCEL - No shift report reference - Invoice: {doc.name}")

def before_cancel(doc, method):
	log.info(f"[BEFORE_CANCEL] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}, Amount: {doc.grand_total}")

	update_coupon(doc, "Cancelled")

	log.info(f"[BEFORE_CANCEL] ✅ COMPLETED - Invoice: {doc.name}")

def add_loyalty_point(invoice_doc):
	log.info(f"[LOYALTY_POINTS] 🎯 START - Invoice: {invoice_doc.name}, Customer: {invoice_doc.customer}")

	loyalty_points_added = 0
	for offer in invoice_doc.posa_offers:
		if offer.offer == "Loyalty Point":
			log.info(f"[LOYALTY_POINTS] 🎫 Processing offer: {offer.offer_name}")
			original_offer = frappe.get_doc("POS Offer", offer.offer_name)
			if original_offer.loyalty_points > 0:
				loyalty_program = frappe.get_value("Customer", invoice_doc.customer, "loyalty_program")
				if not loyalty_program:
					loyalty_program = original_offer.loyalty_program

				log.info(f"[LOYALTY_POINTS] 💰 Adding {original_offer.loyalty_points} points to program: {loyalty_program}")

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
				loyalty_points_added += original_offer.loyalty_points
				log.info(f"[LOYALTY_POINTS] ✅ Added loyalty points entry: {doc.name}")

	log.info(f"[LOYALTY_POINTS] 🎉 COMPLETED - Total points added: {loyalty_points_added}")


def create_sales_order(doc):
	log.info(f"[SALES_ORDER] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}")

	# Check conditions for creating sales order
	conditions_met = (
		doc.posa_pos_opening_shift
		and doc.pos_profile
		and doc.is_pos
		and doc.posa_delivery_date
		and not doc.update_stock
		and frappe.get_value("POS Profile", doc.pos_profile, "posa_allow_sales_order")
	)

	log.info(f"[SALES_ORDER] 🔍 Conditions check - Opening Shift: {bool(doc.posa_pos_opening_shift)}, POS Profile: {bool(doc.pos_profile)}, Is POS: {bool(doc.is_pos)}, Delivery Date: {bool(doc.posa_delivery_date)}, Update Stock: {bool(doc.update_stock)}, Allow Sales Order: {bool(frappe.get_value('POS Profile', doc.pos_profile, 'posa_allow_sales_order'))}")

	if conditions_met:
		log.info(f"[SALES_ORDER] ✅ Conditions met, creating sales order")
		sales_order_doc = make_sales_order(doc.name)
		if sales_order_doc:
			log.info(f"[SALES_ORDER] 📋 Sales order created: {sales_order_doc.name}")
			sales_order_doc.posa_notes = doc.posa_notes
			sales_order_doc.flags.ignore_permissions = True
			sales_order_doc.flags.ignore_account_permission = True
			sales_order_doc.save()
			log.info(f"[SALES_ORDER] 💾 Sales order saved: {sales_order_doc.name}")

			sales_order_doc.submit()
			log.info(f"[SALES_ORDER] ✅ Sales order submitted: {sales_order_doc.name}")

			url = frappe.utils.get_url_to_form(sales_order_doc.doctype, sales_order_doc.name)
			msgprint = "Sales Order Created at <a href='{0}'>{1}</a>".format(url, sales_order_doc.name)
			frappe.msgprint(_(msgprint), title="Sales Order Created", indicator="green", alert=True)

			i = 0
			for item in sales_order_doc.items:
				doc.items[i].sales_order = sales_order_doc.name
				doc.items[i].so_detail = item.name
				i += 1

			log.info(f"[SALES_ORDER] 🔗 Linked {i} items to sales order")
		else:
			log.warning(f"[SALES_ORDER] ⚠️ Failed to create sales order for invoice: {doc.name}")
	else:
		log.info(f"[SALES_ORDER] ℹ️ Conditions not met, skipping sales order creation")

	log.info(f"[SALES_ORDER] 🎉 COMPLETED - Invoice: {doc.name}")


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
	log.info(f"[COUPON_UPDATE] 🎯 START - Invoice: {doc.name}, Transaction Type: {transaction_type}")

	coupons_updated = 0
	for coupon in doc.posa_coupons:
		if not coupon.applied:
			log.debug(f"[COUPON_UPDATE] ⏭️ Skipping unapplied coupon: {coupon.coupon}")
			continue

		log.info(f"[COUPON_UPDATE] 🎫 Updating coupon: {coupon.coupon}")
		update_coupon_code_count(coupon.coupon, transaction_type)
		coupons_updated += 1

	log.info(f"[COUPON_UPDATE] ✅ COMPLETED - Updated {coupons_updated} coupons")


def set_patient(doc):
	log.info(f"[PATIENT_SETUP] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}")

	domain = get_company_domain(doc.company)
	log.info(f"[PATIENT_SETUP] 🏥 Company domain: {domain}")

	if domain != "Healthcare":
		log.info(f"[PATIENT_SETUP] ℹ️ Not healthcare domain, skipping patient setup")
		return

	log.info(f"[PATIENT_SETUP] 🔍 Looking for patient linked to customer: {doc.customer}")
	patient_list = frappe.get_all("Patient", filters={"customer": doc.customer}, page_length=1)

	if len(patient_list) > 0:
		doc.patient = patient_list[0].name
		log.info(f"[PATIENT_SETUP] ✅ Patient set: {doc.patient}")
	else:
		log.info(f"[PATIENT_SETUP] ℹ️ No patient found for customer: {doc.customer}")

	log.info(f"[PATIENT_SETUP] 🎉 COMPLETED - Invoice: {doc.name}")


def auto_set_delivery_charges(doc):
	log.info(f"[DELIVERY_CHARGES] 🎯 START - Invoice: {doc.name}, POS Profile: {doc.pos_profile}")

	if not doc.pos_profile:
		log.info(f"[DELIVERY_CHARGES] ℹ️ No POS profile, skipping delivery charges setup")
		return

	auto_set_enabled = frappe.get_cached_value("POS Profile", doc.pos_profile, "posa_auto_set_delivery_charges")
	log.info(f"[DELIVERY_CHARGES] 🔧 Auto set delivery charges enabled: {bool(auto_set_enabled)}")

	if not auto_set_enabled:
		log.info(f"[DELIVERY_CHARGES] ℹ️ Auto set delivery charges disabled, skipping")
		return

	log.info(f"[DELIVERY_CHARGES] 🔍 Getting applicable delivery charges")
	delivery_charges = get_applicable_delivery_charges(
		doc.company,
		doc.pos_profile,
		doc.customer,
		doc.shipping_address_name,
		doc.posa_delivery_charges,
		restrict=True,
	)

	log.info(f"[DELIVERY_CHARGES] 📋 Found {len(delivery_charges)} applicable delivery charges")

	if doc.posa_delivery_charges:
		log.info(f"[DELIVERY_CHARGES] 📦 Delivery charges already set: {doc.posa_delivery_charges}")
		if doc.posa_delivery_charges_rate:
			log.info(f"[DELIVERY_CHARGES] 💰 Delivery charges rate already set: {doc.posa_delivery_charges_rate}")
			return
		else:
			if len(delivery_charges) > 0:
				doc.posa_delivery_charges_rate = delivery_charges[0].rate
				log.info(f"[DELIVERY_CHARGES] ✅ Set delivery charges rate: {delivery_charges[0].rate}")
			else:
				log.info(f"[DELIVERY_CHARGES] ℹ️ No applicable delivery charges found")
	else:
		if len(delivery_charges) > 0:
			doc.posa_delivery_charges = delivery_charges[0].name
			doc.posa_delivery_charges_rate = delivery_charges[0].rate
			log.info(f"[DELIVERY_CHARGES] ✅ Set delivery charges: {delivery_charges[0].name} at rate {delivery_charges[0].rate}")
		else:
			doc.posa_delivery_charges = None
			doc.posa_delivery_charges_rate = None
			log.info(f"[DELIVERY_CHARGES] ℹ️ No delivery charges applicable, set to None")

	log.info(f"[DELIVERY_CHARGES] 🎉 COMPLETED - Invoice: {doc.name}")


def calc_delivery_charges(doc):
	log.info(f"[CALC_DELIVERY_CHARGES] 🎯 START - Invoice: {doc.name}, POS Profile: {doc.pos_profile}")

	if not doc.pos_profile:
		log.info(f"[CALC_DELIVERY_CHARGES] ℹ️ No POS profile, skipping calculation")
		return

	old_doc = None
	calculate_taxes_and_totals = False

	if not doc.is_new():
		old_doc = doc.get_doc_before_save()
		log.info(f"[CALC_DELIVERY_CHARGES] 📝 Existing document, checking for changes")
		if not doc.posa_delivery_charges and not old_doc.posa_delivery_charges:
			log.info(f"[CALC_DELIVERY_CHARGES] ℹ️ No delivery charges in both old and new, skipping")
			return
	else:
		log.info(f"[CALC_DELIVERY_CHARGES] 🆕 New document")
		if not doc.posa_delivery_charges:
			log.info(f"[CALC_DELIVERY_CHARGES] ℹ️ No delivery charges set, skipping")
			return

	if not doc.posa_delivery_charges:
		doc.posa_delivery_charges_rate = 0
		log.info(f"[CALC_DELIVERY_CHARGES] ℹ️ No delivery charges, set rate to 0")

	charges_doc = None
	if doc.posa_delivery_charges:
		log.info(f"[CALC_DELIVERY_CHARGES] 📦 Loading delivery charges document: {doc.posa_delivery_charges}")
		charges_doc = frappe.get_cached_doc("Delivery Charges", doc.posa_delivery_charges)
		doc.posa_delivery_charges_rate = charges_doc.default_rate
		log.info(f"[CALC_DELIVERY_CHARGES] 💰 Set default rate: {charges_doc.default_rate}")

		charges_profile = next((i for i in charges_doc.profiles if i.pos_profile == doc.pos_profile), None)
		if charges_profile:
			doc.posa_delivery_charges_rate = charges_profile.rate
			log.info(f"[CALC_DELIVERY_CHARGES] ✅ Applied profile-specific rate: {charges_profile.rate}")
		else:
			log.info(f"[CALC_DELIVERY_CHARGES] ℹ️ No profile-specific rate found, using default")

	# Remove old delivery charges from taxes if changed
	if old_doc and old_doc.posa_delivery_charges:
		log.info(f"[CALC_DELIVERY_CHARGES] 🔄 Checking for old delivery charges to remove")
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
			log.info(f"[CALC_DELIVERY_CHARGES] 🗑️ Removed old delivery charges from taxes")

	# Add new delivery charges to taxes
	if doc.posa_delivery_charges:
		log.info(f"[CALC_DELIVERY_CHARGES] ➕ Adding delivery charges to taxes")
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
		log.info(f"[CALC_DELIVERY_CHARGES] ✅ Added delivery charges to taxes: {doc.posa_delivery_charges_rate}")

	if calculate_taxes_and_totals:
		log.info(f"[CALC_DELIVERY_CHARGES] 🧮 Recalculating taxes and totals")
		doc.calculate_taxes_and_totals()
		log.info(f"[CALC_DELIVERY_CHARGES] ✅ Taxes and totals recalculated")

	log.info(f"[CALC_DELIVERY_CHARGES] 🎉 COMPLETED - Invoice: {doc.name}")


def apply_tax_inclusive(doc):
	"""Mark taxes as inclusive based on POS Profile setting."""
	log.info(f"[TAX_INCLUSIVE] 🎯 START - Invoice: {doc.name}, POS Profile: {doc.pos_profile}")

	if not doc.pos_profile:
		log.info(f"[TAX_INCLUSIVE] ℹ️ No POS profile, skipping tax inclusive setup")
		return

	try:
		tax_inclusive = frappe.get_cached_value("POS Profile", doc.pos_profile, "posa_tax_inclusive")
		log.info(f"[TAX_INCLUSIVE] 🔧 Tax inclusive setting: {bool(tax_inclusive)}")
	except Exception as e:
		tax_inclusive = 0
		log.warning(f"[TAX_INCLUSIVE] ⚠️ Failed to get tax inclusive setting: {str(e)}")

	if not tax_inclusive:
		log.info(f"[TAX_INCLUSIVE] ℹ️ Tax inclusive disabled, skipping")
		return

	log.info(f"[TAX_INCLUSIVE] 📊 Processing {len(doc.get('taxes', []))} tax entries")
	has_changes = False
	changes_count = 0

	for tax in doc.get("taxes", []):
		if not tax.included_in_print_rate:
			log.debug(f"[TAX_INCLUSIVE] 🔄 Setting tax inclusive for: {tax.description}")
			tax.included_in_print_rate = 1
			has_changes = True
			changes_count += 1

	log.info(f"[TAX_INCLUSIVE] ✅ Made {changes_count} tax entries inclusive")

	if has_changes:
		log.info(f"[TAX_INCLUSIVE] 🧮 Recalculating taxes and totals")
		doc.calculate_taxes_and_totals()
		log.info(f"[TAX_INCLUSIVE] ✅ Taxes and totals recalculated")

	log.info(f"[TAX_INCLUSIVE] 🎉 COMPLETED - Invoice: {doc.name}")


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
	Optimized version: Direct database operations with minimal queries

	Args:
		invoice_doc: Sales Invoice document
		action: "submit" or "cancel"
	"""
	log.info(f"[INVOICE_TRACKING] 🎯 UPDATE_SHIFT_REPORT - Start - Invoice: {invoice_doc.name}, Action: {action}")

	# FIX: Validate action parameter
	if action not in ["submit", "cancel"]:
		log.error(f"[INVOICE_TRACKING] ❌ UPDATE_SHIFT_REPORT - Invalid action: {action}")
		return

	try:
		if not hasattr(invoice_doc, 'pos_shift_report') or not invoice_doc.pos_shift_report:
			log.warning(f"[INVOICE_TRACKING] ❌ UPDATE_SHIFT_REPORT - No shift report reference - Invoice: {invoice_doc.name}")
			return

		shift_report_name = invoice_doc.pos_shift_report
		invoice_amount = invoice_doc.grand_total or 0

		log.info(f"[INVOICE_TRACKING] 📋 UPDATE_SHIFT_REPORT - Processing: {shift_report_name}, Amount: {invoice_amount}")

		# FIX: Use manual transaction management for older Frappe versions
		needs_totals_update = False  # Track if we need to update totals

		if action == "submit":
			log.info(f"[INVOICE_TRACKING] ➕ UPDATE_SHIFT_REPORT - Processing SUBMIT")

			# Check if invoice already exists (optimized query)
			existing_count = frappe.db.count("POS Shift Report Invoice", {
				"parent": shift_report_name,
				"invoice_no": invoice_doc.name
			})

			if existing_count > 0:
				log.info(f"[INVOICE_TRACKING] ⚠️ UPDATE_SHIFT_REPORT - Invoice already exists, will update totals")
				needs_totals_update = True  # Still need to update totals
			else:
				# Get payment method
				payment_method = get_invoice_payment_method(invoice_doc)

				# FIX: Generate name for child table row
				child_name = frappe.generate_hash(length=10)

				# FIX: Normalize boolean to tinyint (0/1)
				is_return_value = 1 if (invoice_doc.is_return or False) else 0

				# FIX: Use actual invoice status instead of hardcoded "Paid"
				status_value = invoice_doc.status or "Paid"
				log.info(f"[INVOICE_TRACKING] 📊 UPDATE_SHIFT_REPORT - Using invoice status: {status_value}")

				# FIX: Handle race condition with INSERT ... ON DUPLICATE KEY UPDATE
				try:
					frappe.db.sql("""
						INSERT INTO `tabPOS Shift Report Invoice`
						(name, parent, parenttype, parentfield, invoice_no, invoice_date, invoice_time,
						 customer, total_amount, paid_amount, tax_amount, payment_method,
						 is_return, status, creation, modified, modified_by, owner)
						VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)
						ON DUPLICATE KEY UPDATE
							status = VALUES(status),
							modified = NOW(),
							modified_by = VALUES(modified_by)
					""", (
						child_name, shift_report_name, "POS Shift Report", "invoices",
						invoice_doc.name, invoice_doc.posting_date, invoice_doc.posting_time,
						invoice_doc.customer, invoice_amount, invoice_doc.paid_amount or 0,
						invoice_doc.total_taxes_and_charges or 0, payment_method,
						is_return_value, status_value,  # Use actual status
						frappe.session.user, frappe.session.user
					))

					log.info(f"[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - Added invoice to shift report with status: {status_value}")
					needs_totals_update = True

				except Exception as insert_error:
					log.warning(f"[INVOICE_TRACKING] ⚠️ UPDATE_SHIFT_REPORT - Insert failed (duplicate?): {str(insert_error)}")
					needs_totals_update = True  # Still need to update totals

		elif action == "cancel":
			log.info(f"[INVOICE_TRACKING] ❌ UPDATE_SHIFT_REPORT - Processing CANCEL")

			# FIX: Check affected rows properly
			before_count = frappe.db.count("POS Shift Report Invoice", {
				"parent": shift_report_name,
				"invoice_no": invoice_doc.name,
				"status": ["!=", "Cancelled"]
			})

			# OPTIMIZED: Direct update without select
			frappe.db.sql("""
				UPDATE `tabPOS Shift Report Invoice`
				SET status = 'Cancelled', modified = NOW(), modified_by = %s
				WHERE parent = %s AND invoice_no = %s AND status != 'Cancelled'
			""", (frappe.session.user, shift_report_name, invoice_doc.name))

			after_count = frappe.db.count("POS Shift Report Invoice", {
				"parent": shift_report_name,
				"invoice_no": invoice_doc.name,
				"status": ["!=", "Cancelled"]
			})

			affected_rows = before_count - after_count

			if affected_rows > 0:
				log.info(f"[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - Marked invoice as cancelled ({affected_rows} rows)")
				needs_totals_update = True
			else:
				log.warning(f"[INVOICE_TRACKING] ⚠️ UPDATE_SHIFT_REPORT - Invoice not found or already cancelled")

		# FIX: Always recalculate totals if needed
		if needs_totals_update:
			log.info(f"[INVOICE_TRACKING] 🔢 UPDATE_SHIFT_REPORT - Recalculating totals")

			totals_result = frappe.db.sql("""
				SELECT
					COALESCE(SUM(CASE WHEN status = 'Paid' AND is_return = 0
						THEN total_amount ELSE 0 END), 0) as total_sales,
					COALESCE(SUM(CASE WHEN (status = 'Paid' AND is_return = 1) OR status = 'Cancelled'
						THEN total_amount ELSE 0 END), 0) as total_returns,
					COUNT(*) as invoice_count
				FROM `tabPOS Shift Report Invoice`
				WHERE parent = %s AND parenttype = 'POS Shift Report'
			""", (shift_report_name,), as_dict=True)

			if totals_result and len(totals_result) > 0:
				new_sales = float(totals_result[0].total_sales or 0)
				new_returns = float(totals_result[0].total_returns or 0)
				new_count = int(totals_result[0].invoice_count or 0)

				log.info(f"[INVOICE_TRACKING] 📊 UPDATE_SHIFT_REPORT - Totals: Sales={new_sales}, Returns={new_returns}, Count={new_count}")

				# OPTIMIZED: Single update for all fields
				frappe.db.set_value("POS Shift Report", shift_report_name, {
					"invoice_count": new_count,
					"total_sales": new_sales,
					"total_returns": new_returns
				})

				log.info(f"[INVOICE_TRACKING] 💾 UPDATE_SHIFT_REPORT - Updated shift report successfully")
			else:
				log.warning(f"[INVOICE_TRACKING] ⚠️ UPDATE_SHIFT_REPORT - No data found for recalculation")
		else:
			log.info(f"[INVOICE_TRACKING] ℹ️ UPDATE_SHIFT_REPORT - No totals update needed")

		log.info(f"[INVOICE_TRACKING] 🎉 UPDATE_SHIFT_REPORT - COMPLETED - Invoice: {invoice_doc.name}, Action: {action}")

	except Exception as e:
		log.error(f"[INVOICE_TRACKING] 💥 UPDATE_SHIFT_REPORT - FAILED - Invoice: {invoice_doc.name}, Action: {action}, Error: {str(e)}")
		# Don't raise error to prevent invoice submission/cancellation failure
  
