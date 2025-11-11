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
	log.info(f"[INVOICE_VALIDATION] START - Invoice: {doc.name}, Amount: {doc.grand_total}")

	# Log Item Prices before invoice creation
	log.info(f"[ITEM_PRICE_LOG] 📝 BEFORE INVOICE CREATION - Invoice: {doc.name}, Selling Price List: {doc.selling_price_list}")
	for item in doc.items:
		# Get Item Price from database
		price_list = doc.selling_price_list or "Standard Selling"
		item_price_data = frappe.db.get_value("Item Price",
			{"item_code": item.item_code, "price_list": price_list},
			["price_list_rate", "currency"], as_dict=True)
		item_price_rate = item_price_data.price_list_rate if item_price_data else 0
		item_price_currency = item_price_data.currency if item_price_data else "N/A"

		log.info(f"[ITEM_PRICE_LOG] 📝 Item: {item.item_code}, Qty: {item.qty}, Rate: {item.rate}, Amount: {item.amount}, Discount: {item.discount_amount}")
		log.info(f"[ITEM_PRICE_LOG] 📝 Item Price Table: {item.item_code}, Price List: {price_list}, Price List Rate: {item_price_rate}, Currency: {item_price_currency}")

	validate_shift(doc)
	set_patient(doc)
	auto_set_delivery_charges(doc)
	calc_delivery_charges(doc)
	apply_tax_inclusive(doc)

	log.info(f"[INVOICE_VALIDATION] COMPLETED - Invoice: {doc.name}")


def _sum_item_level_discount(inv):
	"""Calculate total discount from all items in the invoice"""
	total = 0
	for it in inv.items:
		# Nếu đã có posa_discount_total thì dùng
		if hasattr(it, "posa_discount_total") and it.posa_discount_total:
			total += flt(it.posa_discount_total)
		else:
			# fallback: per-unit * qty
			unit_disc = (flt(it.price_list_rate) - flt(it.rate)) if (it.price_list_rate and it.rate) else flt(it.discount_amount or 0)
			total += unit_disc * flt(it.qty or 0)
	return flt(total, inv.precision("grand_total"))

# def before_submit(doc, method):
# 	log.info(f"[BEFORE_SUBMIT] 🎯 START - Invoice: {doc.name}, Customer: {doc.customer}, Amount: {doc.grand_total}")

# 	add_loyalty_point(doc)
# 	create_sales_order(doc)
# 	update_coupon(doc, "used")

# 	log.info(f"[BEFORE_SUBMIT] ✅ COMPLETED - Invoice: {doc.name}")

def before_submit(doc, method):
	log.info(f"[BEFORE_SUBMIT] START - Invoice: {doc.name}")

	# Calculate and set total item discount
	doc.posa_total_item_discount = _sum_item_level_discount(doc)
	log.info(f"[BEFORE_SUBMIT] Total item discount calculated: {doc.posa_total_item_discount}")


def on_submit(doc, method):
	"""Update shift report and payment summary when invoice is submitted"""
	log.info(f"[INVOICE_TRACKING] ON_SUBMIT - Trigger on - Invoice: {doc.name}, Amount: {doc.grand_total}")

	# Log Item Prices after successful invoice creation
	log.info(f"[ITEM_PRICE_LOG] ✅ AFTER INVOICE CREATION SUCCESS - Invoice: {doc.name}, Selling Price List: {doc.selling_price_list}")
	for item in doc.items:
		# Get Item Price from database
		price_list = doc.selling_price_list or "Standard Selling"
		item_price_data = frappe.db.get_value("Item Price",
			{"item_code": item.item_code, "price_list": price_list},
			["price_list_rate", "currency"], as_dict=True)
		item_price_rate = item_price_data.price_list_rate if item_price_data else 0
		item_price_currency = item_price_data.currency if item_price_data else "N/A"

		log.info(f"[ITEM_PRICE_LOG] ✅ Item: {item.item_code}, Qty: {item.qty}, Rate: {item.rate}, Amount: {item.amount}, Discount: {item.discount_amount}")
		log.info(f"[ITEM_PRICE_LOG] ✅ Item Price Table: {item.item_code}, Price List: {price_list}, Price List Rate: {item_price_rate}, Currency: {item_price_currency}")

	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
		update_shift_report_with_invoice(doc, "submit")
	else:
		log.warning(f"[INVOICE_TRACKING] No shift report reference - Invoice: {doc.name}")

	# Update POS Payment Summary
	try:
		from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import update_payment_summary_on_invoice_submit
		result = update_payment_summary_on_invoice_submit(doc.name)
		if not result.get("success"):
			log.warning(f"[PAYMENT_SUMMARY] Failed to update payment summary for invoice: {doc.name}")
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error updating payment summary for invoice {doc.name}: {str(e)}")

def on_cancel(doc, method):
	"""Update shift report and payment summary when invoice is cancelled"""
	log.info(f"[INVOICE_TRACKING] ON_CANCEL - Trigger on - Invoice: {doc.name}, Amount: {doc.grand_total}")

	if hasattr(doc, 'pos_shift_report') and doc.pos_shift_report:
		update_shift_report_with_invoice(doc, "cancel")
	else:
		log.warning(f"[INVOICE_TRACKING] No shift report reference - Invoice: {doc.name}")

	# Update POS Payment Summary
	try:
		from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import update_payment_summary_on_invoice_submit
		result = update_payment_summary_on_invoice_submit(doc.name)
		if not result.get("success"):
			log.warning(f"[PAYMENT_SUMMARY] Failed to update payment summary for cancelled invoice: {doc.name}")
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error updating payment summary for cancelled invoice {doc.name}: {str(e)}")

def before_cancel(doc, method):
	log.info(f"[BEFORE_CANCEL] START - Invoice: {doc.name}")

	update_coupon(doc, "Cancelled")

	log.info(f"[BEFORE_CANCEL] COMPLETED - Invoice: {doc.name}")

def add_loyalty_point(invoice_doc):
	log.info(f"[LOYALTY_POINTS] START - Invoice: {invoice_doc.name}")

	loyalty_points_added = 0
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
				loyalty_points_added += original_offer.loyalty_points

	log.info(f"[LOYALTY_POINTS] COMPLETED - Total points added: {loyalty_points_added}")


def create_sales_order(doc):
	log.info(f"[SALES_ORDER] START - Invoice: {doc.name}")

	# Check conditions for creating sales order
	conditions_met = (
		doc.posa_pos_opening_shift
		and doc.pos_profile
		and doc.is_pos
		and doc.posa_delivery_date
		and not doc.update_stock
		and frappe.get_value("POS Profile", doc.pos_profile, "posa_allow_sales_order")
	)

	if conditions_met:
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

			log.info(f"[SALES_ORDER] COMPLETED - Sales order created: {sales_order_doc.name}")
		else:
			log.warning(f"[SALES_ORDER] Failed to create sales order for invoice: {doc.name}")
	else:
		log.info(f"[SALES_ORDER] Conditions not met, skipping sales order creation")


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
	log.info(f"[COUPON_UPDATE] START - Invoice: {doc.name}, Type: {transaction_type}")

	coupons_updated = 0
	for coupon in doc.posa_coupons:
		if coupon.applied:
			update_coupon_code_count(coupon.coupon, transaction_type)
			coupons_updated += 1

	log.info(f"[COUPON_UPDATE] COMPLETED - Updated {coupons_updated} coupons")


def set_patient(doc):
	domain = get_company_domain(doc.company)
	if domain == "Healthcare":
		patient_list = frappe.get_all("Patient", filters={"customer": doc.customer}, page_length=1)
		if len(patient_list) > 0:
			doc.patient = patient_list[0].name
			log.info(f"[PATIENT_SETUP] Patient set: {doc.patient}")


def auto_set_delivery_charges(doc):
	if not doc.pos_profile:
		return

	auto_set_enabled = frappe.get_cached_value("POS Profile", doc.pos_profile, "posa_auto_set_delivery_charges")
	if not auto_set_enabled:
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
		if not doc.posa_delivery_charges_rate and len(delivery_charges) > 0:
			doc.posa_delivery_charges_rate = delivery_charges[0].rate
	else:
		if len(delivery_charges) > 0:
			doc.posa_delivery_charges = delivery_charges[0].name
			doc.posa_delivery_charges_rate = delivery_charges[0].rate
			log.info(f"[DELIVERY_CHARGES] Set delivery charges: {delivery_charges[0].name}")


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

	# Remove old delivery charges from taxes if changed
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

	# Add new delivery charges to taxes
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
	except Exception as e:
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
	Get complete payment method breakdown from invoice payments

	Returns full payment breakdown as JSON structure:
	{"Credit Card": 100, "Cash": 50, "Bank Transfer": 25}

	This allows storing complete payment information in shift reports
	instead of just the primary payment method.

	Based on tabSales Invoice Payment table structure:
	- mode_of_payment: Payment method (Credit Card, Cash, Bank Transfer, etc.)
	- amount: Payment amount
	- default: Default payment flag
	- parent: Linked to Sales Invoice

	Args:
		invoice_doc: Sales Invoice document

	Returns:
		dict: Complete payment breakdown {payment_method: total_amount, ...}
	"""
	try:
		breakdown = {}

		# Check if invoice has payments child table
		if hasattr(invoice_doc, 'payments') and invoice_doc.payments:
			for payment in invoice_doc.payments:
				if payment.amount > 0:
					method = payment.mode_of_payment or "Cash"
					if method in breakdown:
						breakdown[method] += payment.amount
					else:
						breakdown[method] = payment.amount

			if breakdown:
				return breakdown

		# Fallback: Check payment entries linked to this invoice
		payment_entries = frappe.get_all("Payment Entry Reference",
			filters={"reference_name": invoice_doc.name, "reference_doctype": "Sales Invoice"},
			fields=["parent"]
		)

		if payment_entries:
			for entry_ref in payment_entries:
				payment_entry = frappe.get_doc("Payment Entry", entry_ref.parent)
				if payment_entry.payment_type == "Receive" and payment_entry.paid_amount > 0:
					method = payment_entry.mode_of_payment or "Cash"
					if method in breakdown:
						breakdown[method] += payment_entry.paid_amount
					else:
						breakdown[method] = payment_entry.paid_amount

		# Default fallback
		if not breakdown:
			breakdown = {"Cash": invoice_doc.grand_total or 0}

		return breakdown

	except Exception as e:
		log.error(f"[PAYMENT_METHOD] Error getting payment method for invoice {invoice_doc.name}: {str(e)}")
		return {"Cash": invoice_doc.grand_total or 0}




def validate_shift(doc):
	if doc.posa_pos_opening_shift and doc.pos_profile and doc.is_pos:
		# check if shift is open
		shift = frappe.get_cached_doc("POS Opening Shift", doc.posa_pos_opening_shift)
		if shift.status != "Open":
			frappe.throw(_("POS Shift {0} is not open").format(shift.name))

		# check if shift is for the same profile
		if shift.pos_profile != doc.pos_profile:
			frappe.throw(_("POS Opening Shift {0} is not for the same POS Profile").format(shift.name))

		# check if shift is for the same company
		if shift.company != doc.company:
			frappe.throw(_("POS Opening Shift {0} is not for the same company").format(shift.name))

		# Set shift report reference - Try multiple approaches
		shift_report_found = False

		# Approach 1: Check if POS Opening Shift has shift_report field
		if hasattr(shift, 'shift_report') and shift.shift_report:
			doc.pos_shift_report = shift.shift_report
			doc.shift_report_id = shift.shift_report_id
			shift_report_found = True

		# Approach 2: If not found, query shift report directly by pos_opening_shift
		if not shift_report_found:
			try:
				shift_reports = frappe.get_all("POS Shift Report",
					filters={
						"pos_opening_shift": doc.posa_pos_opening_shift,
						"status": ["in", ["Open", "In Progress"]]
					},
					fields=["name", "shift_report_id"],
					limit=1
				)

				if shift_reports:
					doc.pos_shift_report = shift_reports[0].name
					doc.shift_report_id = shift_reports[0].shift_report_id
					shift_report_found = True
			except Exception as query_error:
				log.error(f"[INVOICE_TRACKING] Error querying shift report: {str(query_error)}")

		if not shift_report_found:
			log.warning(f"[INVOICE_TRACKING] No shift report reference set - Invoice: {doc.name}")


def update_shift_report_with_invoice(invoice_doc, action):
    """
    Update shift report when invoice is submitted or cancelled
    Optimized version: Direct database operations with minimal queries

    Args:
        invoice_doc: Sales Invoice document
        action: "submit" or "cancel"
    """
    if action not in ["submit", "cancel"]:
        log.error(f"[INVOICE_TRACKING] Invalid action: {action}")
        return

    if not hasattr(invoice_doc, 'pos_shift_report') or not invoice_doc.pos_shift_report:
        log.warning(f"[INVOICE_TRACKING] No shift report reference - Invoice: {invoice_doc.name}")
        return

    try:
        shift_report_name = invoice_doc.pos_shift_report

        if action == "submit":
            # Check if invoice already exists
            existing_count = frappe.db.count("POS Shift Report Invoice", {
                "parent": shift_report_name,
                "invoice_no": invoice_doc.name
            })

            if existing_count > 0:
                log.info(f"[INVOICE_TRACKING] Invoice already exists in shift report: {invoice_doc.name}")
                return

            # Get payment breakdown and insert new record
            payment_breakdown = get_invoice_payment_method(invoice_doc)
            payment_method_json = frappe.as_json(payment_breakdown)

            child_name = frappe.generate_hash(length=10)
            is_return_value = 1 if invoice_doc.is_return else 0
            invoice_status_value = invoice_doc.status or "Paid"

            frappe.db.sql("""
                INSERT INTO `tabPOS Shift Report Invoice`
                (name, parent, parenttype, parentfield, invoice_no, invoice_date, invoice_time,
                 customer, total_amount, paid_amount, tax_amount, payment_method,
                 is_return, status, invoice_status, creation, modified, modified_by, owner)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)
                ON DUPLICATE KEY UPDATE
                	status = VALUES(status),
                	invoice_status = VALUES(invoice_status),
                	modified = NOW(),
                	modified_by = VALUES(modified_by)
            """, (
                child_name, shift_report_name, "POS Shift Report", "invoices",
                invoice_doc.name, invoice_doc.posting_date, invoice_doc.posting_time,
                invoice_doc.customer, invoice_doc.grand_total or 0,
                invoice_doc.paid_amount or 0, invoice_doc.total_taxes_and_charges or 0,
                payment_method_json, is_return_value, "Submitted", invoice_status_value,
                frappe.session.user, frappe.session.user
            ))

            log.info(f"[INVOICE_TRACKING] Added invoice to shift report: {invoice_doc.name}")

        elif action == "cancel":
            # Update existing records to cancelled status
            result = frappe.db.sql("""
                UPDATE `tabPOS Shift Report Invoice`
                SET status = 'Cancelled', invoice_status = %s, modified = NOW(), modified_by = %s
                WHERE parent = %s AND invoice_no = %s AND status != 'Cancelled'
            """, (invoice_doc.status or "Cancelled", frappe.session.user, shift_report_name, invoice_doc.name))

            affected_rows = frappe.db.sql("SELECT ROW_COUNT()")[0][0]
            if affected_rows > 0:
                log.info(f"[INVOICE_TRACKING] Cancelled invoice in shift report: {invoice_doc.name} ({affected_rows} rows)")
            else:
                log.warning(f"[INVOICE_TRACKING] Invoice not found or already cancelled: {invoice_doc.name}")

    except Exception as e:
        log.error(f"[INVOICE_TRACKING] Failed to update shift report for invoice {invoice_doc.name}: {str(e)}")
        # Don't raise error to prevent invoice submission/cancellation failure


@frappe.whitelist()
def mark_invoice_as_submitted_vntax(invoice_name, response_data):
    """
    Mark invoice as submitted for Vietnam tax (VNTAX) processing.
    Updates custom fields: custom_misa_status, custom_misa_ref_id
    And maintains separate counter for Vietnam tax codes.

    Args:
        invoice_name: Name of the sales invoice
        response_data: JSON response from MISA API

    Returns:
        dict: Status and counter information
    """
    try:
        log.info(f"[VNTAX_MARK_SUBMITTED] START - Invoice: {invoice_name}")

        # Get invoice document
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
        if not invoice_doc:
            raise frappe.ValidationError(f"Invoice {invoice_name} not found")

        # Get POS Profile to access tax counters
        if not invoice_doc.pos_profile:
            raise frappe.ValidationError(f"No POS Profile found for invoice {invoice_name}")

        pos_profile = frappe.get_doc("POS Profile", invoice_doc.pos_profile)

        # Increment Vietnam tax counter (separate from Taiwan counter)
        current_counter = pos_profile.get("tax_current_counter") or 0
        new_counter = current_counter + 1

        # Generate next display for Vietnam (different format from Taiwan)
        tax_roll_code = pos_profile.get("tax_roll_code") or "VN"
        next_display = f"{tax_roll_code}{new_counter}"

        # Parse response data to extract req_id
        req_id = None
        try:
            if response_data:
                response_json = frappe.parse_json(response_data)
                req_id = response_json.get("req_id") or response_json.get("requestId") or response_json.get("id")
        except Exception as e:
            log.warning(f"[VNTAX_MARK_SUBMITTED] Could not parse response data: {str(e)}")

        # Check if already submitted to prevent duplicate submissions
        current_status = invoice_doc.get("custom_misa_status")
        log.info(f"[VNTAX_MARK_SUBMITTED] Current MISA status for invoice {invoice_name}: '{current_status}'")

        if current_status == "Submitted":
            log.warning(f"[VNTAX_MARK_SUBMITTED] Invoice {invoice_name} already submitted to MISA (status: {current_status})")
            return {
                "success": True,
                "message": "Invoice already marked as submitted for Vietnam tax",
                "req_id": invoice_doc.get("custom_misa_ref_id"),
                "new_counter": current_counter,
                "next_display": next_display
            }

        # Update invoice custom fields
        log.info(f"[VNTAX_MARK_SUBMITTED] Updating invoice {invoice_name} - setting status to 'Submitted', req_id: {req_id}")
        invoice_doc.custom_misa_status = "Submitted"
        invoice_doc.custom_misa_ref_id = req_id or f"VN-{invoice_name}"

        # Save invoice with custom fields - use db_set_value to bypass validation completely
        try:
            # Use db_set_value to update custom fields directly without triggering validation
            frappe.db.set_value("Sales Invoice", invoice_name, {
                "custom_misa_status": "Submitted",
                "custom_misa_ref_id": req_id or f"VN-{invoice_name}"
            })
            frappe.db.commit()
            log.info(f"[VNTAX_MARK_SUBMITTED] Successfully updated invoice {invoice_name} with MISA status using db_set_value")
        except Exception as save_error:
            log.error(f"[VNTAX_MARK_SUBMITTED] Failed to update invoice {invoice_name} using db_set_value: {str(save_error)}")
            raise save_error

        # Update POS Profile counter
        pos_profile.tax_current_counter = new_counter
        pos_profile.save(ignore_permissions=True)

        log.info(f"[VNTAX_MARK_SUBMITTED] SUCCESS - Invoice: {invoice_name}, ReqID: {req_id}, New Counter: {new_counter}")

        return {
            "success": True,
            "message": "Invoice marked as submitted for Vietnam tax",
            "req_id": req_id,
            "new_counter": new_counter,
            "next_display": next_display
        }

    except Exception as e:
        log.error(f"[VNTAX_MARK_SUBMITTED] ERROR - Invoice: {invoice_name}, Error: {str(e)}")
        frappe.throw(f"Failed to mark invoice as submitted for Vietnam tax: {str(e)}")
  
