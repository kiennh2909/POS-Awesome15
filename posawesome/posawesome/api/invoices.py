# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

import json
from typing import Dict, List

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.setup.utils import get_exchange_rate
from erpnext.stock.doctype.batch.batch import (
	get_batch_no,
)  # This should be from erpnext directly
from frappe import _
from frappe.utils import cint, cstr, flt, getdate, money_in_words, nowdate
from frappe.utils.background_jobs import enqueue

from posawesome.posawesome.api.payments import (
	redeeming_customer_credit,
)  # Updated import
from posawesome.posawesome.api.utilities import (
	ensure_child_doctype,
	set_batch_nos_for_bundels,
)  # Updated imports
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("invoice")
def _set_item_level_discount_totals(inv):
    """Gán posa_discount_total (và per-unit nếu có) cho từng dòng invoice."""
    for it in inv.items:
        # bỏ qua dòng quà/tặng
        if getattr(it, "posa_is_offer", 0) or getattr(it, "is_free_item", 0):
            # Nếu muốn ghi rõ 0:
            if it.meta.has_field("posa_discount_total"):
                it.posa_discount_total = 0
            if it.meta.has_field("posa_discount_per_unit"):
                it.posa_discount_per_unit = 0
            continue

        qty  = flt(getattr(it, "qty", 0))
        rate = flt(getattr(it, "rate", 0))
        plr  = flt(getattr(it, "price_list_rate", 0))  # đã được reset về giá gốc theo UOM hiện tại

        # Tính theo chênh lệch giá × số lượng (không âm, không vượt quá giá gốc)
        per_unit_disc = max(0, plr - rate)
        line_total_disc = per_unit_disc * qty

        # Chặn trần: tổng giảm không vượt tổng giá gốc
        max_allowed = max(0, plr * qty)
        if line_total_disc > max_allowed:
            line_total_disc = max_allowed
            per_unit_disc = max_allowed / qty if qty else 0

        # Ghi vào custom field nếu có, không có thì bỏ qua (không lỗi)
        if it.meta.has_field("posa_discount_total"):
            it.posa_discount_total = flt(line_total_disc, it.precision("amount"))
        if it.meta.has_field("posa_discount_per_unit"):
            it.posa_discount_per_unit = flt(per_unit_disc, it.precision("rate"))


def _sum_item_level_discount(inv):
    total = 0
    for it in inv.items:
        if getattr(it, "posa_is_offer", 0) or getattr(it, "is_free_item", 0):
            continue
        plr  = flt(getattr(it, "price_list_rate", 0))
        rate = flt(getattr(it, "rate", 0))
        qty  = flt(getattr(it, "qty", 0))
        total += max(0, plr - rate) * qty
    return flt(total, inv.precision("grand_total"))


def get_latest_rate(from_currency: str, to_currency: str):
	"""Return the most recent Currency Exchange rate and its date."""
	rate_doc = frappe.get_all(
		"Currency Exchange",
		filters={"from_currency": from_currency, "to_currency": to_currency},
		fields=["exchange_rate", "date"],
		order_by="date desc, creation desc",
		limit=1,
	)
	if rate_doc:
		return flt(rate_doc[0].exchange_rate), rate_doc[0].date
	rate = get_exchange_rate(from_currency, to_currency, nowdate())
	return flt(rate), nowdate()


@frappe.whitelist()
def validate_return_items(original_invoice_name, return_items):
	"""
	Ensure that return items do not exceed the quantity from the original invoice.
	"""
	original_invoice = frappe.get_doc("Sales Invoice", original_invoice_name)
	original_item_qty = {}

	for item in original_invoice.items:
		original_item_qty[item.item_code] = original_item_qty.get(item.item_code, 0) + item.qty

	returned_items = frappe.get_all(
		"Sales Invoice",
		filters={
			"return_against": original_invoice_name,
			"docstatus": 1,
			"is_return": 1,
		},
		fields=["name"],
	)

	for returned_invoice in returned_items:
		ret_doc = frappe.get_doc("Sales Invoice", returned_invoice.name)
		for item in ret_doc.items:
			if item.item_code in original_item_qty:
				original_item_qty[item.item_code] -= abs(item.qty)

	for item in return_items:
		item_code = item.get("item_code")
		return_qty = abs(item.get("qty", 0))
		if item_code in original_item_qty and return_qty > original_item_qty[item_code]:
			return {
				"valid": False,
				"message": _("You are trying to return more quantity for item {0} than was sold.").format(
					item_code
				),
			}

	return {"valid": True}


@frappe.whitelist()
def update_invoice(data):
	log.info(f"[UPDATE_INVOICE] 🎯 START - Processing invoice update")

	# Debug log: Raw data received from client
	log.info(f"[VAT_TRACE] BACKEND RECEIVE - Step 5: Raw data received from client")
	log.info(f"[VAT_TRACE] BACKEND RECEIVE - Invoice data: {data}")
	for i, item in enumerate(data.get('items', [])):
		log.info(f"[VAT_TRACE] BACKEND RECEIVE - Item {i+1} ({item.get('item_code')}): custom_vat_applicable={item.get('custom_vat_applicable')}, custom_vat_rate={item.get('custom_vat_rate')}, custom_inventory_type={item.get('custom_inventory_type')}")

	# Log request metadata
	log.info(f"[UPDATE_INVOICE] 📊 REQUEST METADATA:")
	log.info(f"[UPDATE_INVOICE] 📊   - Content-Type: {frappe.local.request.headers.get('Content-Type', 'N/A')}")
	log.info(f"[UPDATE_INVOICE] 📊   - User: {frappe.session.user}")
	log.info(f"[UPDATE_INVOICE] 📊   - Method: {frappe.local.request.method}")
	log.info(f"[UPDATE_INVOICE] 📊   - Timestamp: {frappe.utils.now()}")

	data = json.loads(data)
	invoice_name = data.get("name")

	log.info(f"[UPDATE_INVOICE] 📋 BASIC INVOICE INFO:")
	log.info(f"[UPDATE_INVOICE] 📋   - Name: {invoice_name}")
	log.info(f"[UPDATE_INVOICE] 📋   - Customer: {data.get('customer', 'N/A')}")
	log.info(f"[UPDATE_INVOICE] 📋   - Company: {data.get('company', 'N/A')}")
	log.info(f"[UPDATE_INVOICE] 📋   - POS Profile: {data.get('pos_profile', 'N/A')}")
	log.info(f"[UPDATE_INVOICE] 📋   - Currency: {data.get('currency', 'N/A')}")
	log.info(f"[UPDATE_INVOICE] 📋   - Grand Total: {data.get('grand_total', 0)}")
	log.info(f"[UPDATE_INVOICE] 📋   - Is Return: {data.get('is_return', False)}")
	log.info(f"[UPDATE_INVOICE] 📋   - Posting Date: {data.get('posting_date', 'N/A')}")

	# Debug log: Parsed data structure
	log.info(f"[UPDATE_INVOICE] 📋 PARSED DATA STRUCTURE:")
	log.info(f"[UPDATE_INVOICE] 📋   - Total Keys: {len(data)}")
	log.info(f"[UPDATE_INVOICE] 📋   - Keys: {sorted(list(data.keys()))}")

	# Log items details
	if 'items' in data and data['items']:
		items = data['items']
		log.info(f"[UPDATE_INVOICE] 📦 ITEMS DETAILS:")
		log.info(f"[UPDATE_INVOICE] 📦   - Items Count: {len(items)}")
		for i, item in enumerate(items[:3]):  # Log first 3 items with full details
			log.info(f"[UPDATE_INVOICE] 📦   - Item {i+1}:")
			log.info(f"[UPDATE_INVOICE] 📦     * item_code: {item.get('item_code')}")
			log.info(f"[UPDATE_INVOICE] 📦     * item_name: {item.get('item_name')}")
			log.info(f"[UPDATE_INVOICE] 📦     * qty: {item.get('qty')}")
			log.info(f"[UPDATE_INVOICE] 📦     * rate: {item.get('rate')}")
			log.info(f"[UPDATE_INVOICE] 📦     * amount: {item.get('amount')}")
			log.info(f"[UPDATE_INVOICE] 📦     * uom: {item.get('uom')}")
			log.info(f"[UPDATE_INVOICE] 📦     * posa_row_id: {item.get('posa_row_id')}")
			log.info(f"[UPDATE_INVOICE] 📦     * posa_offers: {item.get('posa_offers')} (type: {type(item.get('posa_offers'))})")
			log.info(f"[UPDATE_INVOICE] 📦     * posa_offer_applied: {item.get('posa_offer_applied')}")
			log.info(f"[UPDATE_INVOICE] 📦     * discount_amount: {item.get('discount_amount')}")
			log.info(f"[UPDATE_INVOICE] 📦     * discount_percentage: {item.get('discount_percentage')}")

		if len(items) > 3:
			log.info(f"[UPDATE_INVOICE] 📦   - ... and {len(items) - 3} more items")
	else:
		log.info(f"[UPDATE_INVOICE] 📦 No items found in invoice data")

	# Log payments details
	if 'payments' in data and data['payments']:
		payments = data['payments']
		log.info(f"[UPDATE_INVOICE] 💳 PAYMENTS DETAILS:")
		log.info(f"[UPDATE_INVOICE] 💳   - Payments Count: {len(payments)}")
		for i, payment in enumerate(payments):
			log.info(f"[UPDATE_INVOICE] 💳   - Payment {i+1}:")
			log.info(f"[UPDATE_INVOICE] 💳     * mode_of_payment: {payment.get('mode_of_payment')}")
			log.info(f"[UPDATE_INVOICE] 💳     * amount: {payment.get('amount')}")
			log.info(f"[UPDATE_INVOICE] 💳     * base_amount: {payment.get('base_amount')}")
			log.info(f"[UPDATE_INVOICE] 💳     * type: {payment.get('type')}")
	else:
		log.info(f"[UPDATE_INVOICE] 💳 No payments found in invoice data")

	# Log offers details
	if 'posa_offers' in data and data['posa_offers']:
		offers = data['posa_offers']
		log.info(f"[UPDATE_INVOICE] 🎫 POS OFFERS DETAILS:")
		log.info(f"[UPDATE_INVOICE] 🎫   - Offers Count: {len(offers)}")
		for i, offer in enumerate(offers[:2]):  # Log first 2 offers
			log.info(f"[UPDATE_INVOICE] 🎫   - Offer {i+1}:")
			log.info(f"[UPDATE_INVOICE] 🎫     * name: {offer.get('name')}")
			log.info(f"[UPDATE_INVOICE] 🎫     * title: {offer.get('title')}")
			log.info(f"[UPDATE_INVOICE] 🎫     * discount_type: {offer.get('discount_type')}")
			log.info(f"[UPDATE_INVOICE] 🎫     * rate: {offer.get('rate')}")
			log.info(f"[UPDATE_INVOICE] 🎫     * discount_percentage: {offer.get('discount_percentage')}")
			log.info(f"[UPDATE_INVOICE] 🎫     * items: {offer.get('items')}")

		if len(offers) > 2:
			log.info(f"[UPDATE_INVOICE] 🎫   - ... and {len(offers) - 2} more offers")
	else:
		log.info(f"[UPDATE_INVOICE] 🎫 No POS offers found in invoice data")

	# Log taxes if present
	if 'taxes' in data and data['taxes']:
		log.info(f"[UPDATE_INVOICE] 🧾 TAXES: {len(data['taxes'])} tax entries")
	else:
		log.info(f"[UPDATE_INVOICE] 🧾 No taxes found in invoice data")

	log.info(f"[UPDATE_INVOICE] ✅ REQUEST LOGGING COMPLETED - Processing invoice: {invoice_name}")

	# Clean up posa_offers before processing (convert lists to JSON strings)
	if 'posa_offers' in data and data['posa_offers']:
		log.info(f"[UPDATE_INVOICE] 🧹 Cleaning up posa_offers before processing")
		for offer in data['posa_offers']:
			# Convert items list to JSON string if it exists
			if 'items' in offer and isinstance(offer['items'], list):
				offer['items'] = json.dumps(offer['items'])
				log.info(f"[UPDATE_INVOICE] ✅ Converted posa_offers items to JSON string")

	if data.get("name"):
		log.info(f"[UPDATE_INVOICE] 📝 Loading existing invoice: {invoice_name}")
		invoice_doc = frappe.get_doc("Sales Invoice", data.get("name"))
		invoice_doc.update(data)
		log.info(f"[UPDATE_INVOICE] ✅ Existing invoice loaded and updated: {invoice_name}")
	else:
		log.info(f"[UPDATE_INVOICE] 🆕 Creating new invoice document")
		invoice_doc = frappe.get_doc(data)
		log.info(f"[UPDATE_INVOICE] ✅ New invoice document created")

	# Set currency from data before set_missing_values
	# Validate return items if this is a return invoice
	if (data.get("is_return") or invoice_doc.is_return) and invoice_doc.get("return_against"):
		log.info(f"[UPDATE_INVOICE] 🔍 Validating return items for invoice: {invoice_doc.get('return_against')}")
		validation = validate_return_items(
			invoice_doc.return_against, [d.as_dict() for d in invoice_doc.items]
		)
		if not validation.get("valid"):
			log.error(f"[UPDATE_INVOICE] ❌ Return validation failed: {validation.get('message')}")
			frappe.throw(validation.get("message"))
		log.info(f"[UPDATE_INVOICE] ✅ Return validation passed")

	selected_currency = data.get("currency")
	price_list_currency = data.get("price_list_currency")

	log.info(f"[UPDATE_INVOICE] 💱 Currency setup - Selected: {selected_currency}, Price List: {price_list_currency}")

	if not price_list_currency and invoice_doc.get("selling_price_list"):
		price_list_currency = frappe.db.get_value("Price List", invoice_doc.selling_price_list, "currency")
		log.info(f"[UPDATE_INVOICE] 📋 Price list currency resolved from selling_price_list: {price_list_currency}")

	# Ensure customer exists before setting missing values
	customer_name = invoice_doc.get("customer")
	log.info(f"[UPDATE_INVOICE] 👤 Customer validation - Name: {customer_name}")

	if customer_name and not frappe.db.exists("Customer", customer_name):
		log.info(f"[UPDATE_INVOICE] 🆕 Customer not found, creating new customer: {customer_name}")
		try:
			cust = frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": customer_name,
					"customer_group": "All Customer Groups",
					"territory": "All Territories",
					"customer_type": "Individual",
				}
			)
			cust.flags.ignore_permissions = True
			cust.insert()
			invoice_doc.customer = cust.name
			invoice_doc.customer_name = cust.customer_name
			log.info(f"[UPDATE_INVOICE] ✅ Customer created successfully: {cust.name}")
		except Exception as e:
			log.error(f"[UPDATE_INVOICE] ❌ Failed to create customer {customer_name}: {str(e)}")
			frappe.log_error(f"Failed to create customer {customer_name}: {e}")
	else:
		log.info(f"[UPDATE_INVOICE] ✅ Customer exists: {customer_name}")

	# === LOG VAT INFO TRƯỚC KHI SET_MISSING_VALUES ===
	log.info(f"[VAT_TRACE] BEFORE SET_MISSING_VALUES - Step 6: Invoice: {invoice_doc.name}")
	for i, item in enumerate(invoice_doc.items):
		log.info(f"[VAT_TRACE] BEFORE SET_MISSING_VALUES - Item {i+1} ({item.item_code}): custom_vat_applicable={item.custom_vat_applicable}, custom_vat_rate={item.custom_vat_rate}, custom_inventory_type={item.custom_inventory_type}")

	# Set missing values first
	log.info(f"[UPDATE_INVOICE] 🔧 Setting missing values for invoice")
	invoice_doc.set_missing_values()
	log.info(f"[UPDATE_INVOICE] ✅ Missing values set")

	# === LOG VAT INFO SAU KHI SET_MISSING_VALUES ===
	log.info(f"[VAT_TRACE] AFTER SET_MISSING_VALUES - Step 7: Invoice: {invoice_doc.name}")
	for i, item in enumerate(invoice_doc.items):
		log.info(f"[VAT_TRACE] AFTER SET_MISSING_VALUES - Item {i+1} ({item.item_code}): custom_vat_applicable={item.custom_vat_applicable}, custom_vat_rate={item.custom_vat_rate}, custom_inventory_type={item.custom_inventory_type}")

	# Calculate stock_qty for all items (critical for inventory management)
	log.info(f"[UPDATE_INVOICE] 📦 Calculating stock_qty for {len(invoice_doc.items)} items")
	for i, item in enumerate(invoice_doc.items):
		# Ensure stock_qty is calculated correctly: stock_qty = qty * conversion_factor
		if hasattr(item, 'qty') and hasattr(item, 'conversion_factor'):
			original_stock_qty = getattr(item, 'stock_qty', None)
			qty = flt(item.qty)
			conversion_factor = flt(item.conversion_factor)

			if conversion_factor > 0:
				calculated_stock_qty = qty * conversion_factor
				item.stock_qty = calculated_stock_qty
				log.info(f"[UPDATE_INVOICE] 📦 Item {i+1} ({item.item_code}): stock_qty = {qty} × {conversion_factor} = {calculated_stock_qty}")
			else:
				# Fallback: if no conversion_factor, stock_qty = qty
				item.stock_qty = qty
				log.warning(f"[UPDATE_INVOICE] ⚠️ Item {i+1} ({item.item_code}): conversion_factor is 0 or invalid, setting stock_qty = qty = {qty}")

			# Log the change if stock_qty was different
			if original_stock_qty is not None and original_stock_qty != item.stock_qty:
				log.info(f"[UPDATE_INVOICE] 📦 Item {i+1} ({item.item_code}): stock_qty changed from {original_stock_qty} to {item.stock_qty}")
		else:
			log.error(f"[UPDATE_INVOICE] ❌ Item {i+1} ({item.item_code}): missing qty or conversion_factor fields")

	log.info(f"[UPDATE_INVOICE] ✅ Stock quantities calculated for all items")

	# Ensure selected currency is preserved after set_missing_values
	if selected_currency:
		log.info(f"[UPDATE_INVOICE] 💱 Processing currency conversion setup")
		invoice_doc.currency = selected_currency
		company_currency = frappe.get_cached_value("Company", invoice_doc.company, "default_currency")
		price_list_currency = price_list_currency or company_currency

		log.info(f"[UPDATE_INVOICE] 💱 Currency details - Invoice: {selected_currency}, Company: {company_currency}, Price List: {price_list_currency}")

		conversion_rate = 1
		exchange_rate_date = invoice_doc.posting_date
		if invoice_doc.currency != company_currency:
			log.info(f"[UPDATE_INVOICE] 🔄 Getting exchange rate: {invoice_doc.currency} -> {company_currency}")
			conversion_rate, exchange_rate_date = get_latest_rate(
				invoice_doc.currency,
				company_currency,
			)
			if not conversion_rate:
				log.error(f"[UPDATE_INVOICE] ❌ No exchange rate found: {invoice_doc.currency} -> {company_currency}")
				frappe.throw(
					_(
						"Unable to find exchange rate for {0} to {1}. Please create a Currency Exchange record manually"
					).format(invoice_doc.currency, company_currency)
				)
			log.info(f"[UPDATE_INVOICE] ✅ Exchange rate found: {conversion_rate} (Date: {exchange_rate_date})")

		plc_conversion_rate = 1
		if price_list_currency != invoice_doc.currency:
			log.info(f"[UPDATE_INVOICE] 🔄 Getting price list exchange rate: {price_list_currency} -> {invoice_doc.currency}")
			plc_conversion_rate, _ignored = get_latest_rate(
				price_list_currency,
				invoice_doc.currency,
			)
			if not plc_conversion_rate:
				log.error(f"[UPDATE_INVOICE] ❌ No price list exchange rate found: {price_list_currency} -> {invoice_doc.currency}")
				frappe.throw(
					_(
						"Unable to find exchange rate for {0} to {1}. Please create a Currency Exchange record manually"
					).format(price_list_currency, invoice_doc.currency)
				)
			log.info(f"[UPDATE_INVOICE] ✅ Price list exchange rate found: {plc_conversion_rate}")

		invoice_doc.conversion_rate = conversion_rate
		invoice_doc.plc_conversion_rate = plc_conversion_rate
		invoice_doc.price_list_currency = price_list_currency
		log.info(f"[UPDATE_INVOICE] ✅ Currency rates set - Conversion: {conversion_rate}, PLC: {plc_conversion_rate}")
	else:
		log.info(f"[UPDATE_INVOICE] 💱 No currency conversion needed")

		# Update rates and amounts for all items using multiplication
		log.info(f"[UPDATE_INVOICE] 📊 Updating item rates and amounts for {len(invoice_doc.items)} items")
		for item in invoice_doc.items:
			if item.price_list_rate:
				old_rate = item.base_price_list_rate
				item.base_price_list_rate = flt(
					item.price_list_rate * (conversion_rate / plc_conversion_rate),
					item.precision("base_price_list_rate"),
				)
				log.debug(f"[UPDATE_INVOICE] 📊 Item {item.item_code}: base_price_list_rate {old_rate} -> {item.base_price_list_rate}")

			if item.rate:
				old_rate = item.base_rate
				item.base_rate = flt(item.rate * conversion_rate, item.precision("base_rate"))
				log.debug(f"[UPDATE_INVOICE] 📊 Item {item.item_code}: base_rate {old_rate} -> {item.base_rate}")

			if item.amount:
				old_amount = item.base_amount
				item.base_amount = flt(item.amount * conversion_rate, item.precision("base_amount"))
				log.debug(f"[UPDATE_INVOICE] 📊 Item {item.item_code}: base_amount {old_amount} -> {item.base_amount}")

		# Update payment amounts
		log.info(f"[UPDATE_INVOICE] 💰 Updating payment amounts for {len(invoice_doc.payments)} payments")
		for payment in invoice_doc.payments:
			old_amount = payment.base_amount
			payment.base_amount = flt(payment.amount * conversion_rate, payment.precision("base_amount"))
			log.debug(f"[UPDATE_INVOICE] 💰 Payment {payment.mode_of_payment}: base_amount {old_amount} -> {payment.base_amount}")

		# Update invoice level amounts
		log.info(f"[UPDATE_INVOICE] 🧮 Updating invoice level amounts")
		invoice_doc.base_total = flt(invoice_doc.total * conversion_rate, invoice_doc.precision("base_total"))
		invoice_doc.base_net_total = flt(
			invoice_doc.net_total * conversion_rate,
			invoice_doc.precision("base_net_total"),
		)
		invoice_doc.base_grand_total = flt(
			invoice_doc.grand_total * conversion_rate,
			invoice_doc.precision("base_grand_total"),
		)
		invoice_doc.base_rounded_total = flt(
			invoice_doc.rounded_total * conversion_rate,
			invoice_doc.precision("base_rounded_total"),
		)
		invoice_doc.base_in_words = money_in_words(invoice_doc.base_rounded_total, company_currency)

		log.info(f"[UPDATE_INVOICE] ✅ Invoice amounts updated - Grand Total: {invoice_doc.base_grand_total}")

		# Update data to be sent back to frontend
		data["conversion_rate"] = conversion_rate
		data["plc_conversion_rate"] = plc_conversion_rate
		data["exchange_rate_date"] = exchange_rate_date
		log.info(f"[UPDATE_INVOICE] 📤 Updated response data with currency rates")

	log.info(f"[UPDATE_INVOICE] 💾 Preparing to save invoice")

	# --- DEBUG: Tìm field ko phải Table nhưng đang là list ---
	meta = invoice_doc.meta
	for k, v in invoice_doc.as_dict().items():
		df = meta.get_field(k)
		if isinstance(v, list) and (not df or df.fieldtype != "Table"):
			log.error(f"[UPDATE_INVOICE] 🚫 Field `{k}` is list but fieldtype is `{df.fieldtype if df else 'N/A'}`")

	invoice_doc.flags.ignore_permissions = True
	frappe.flags.ignore_account_permission = True
	invoice_doc.docstatus = 0

	log.info(f"[UPDATE_INVOICE] 💾 Saving invoice: {invoice_doc.name}")

	# Debug logging for invoice structure before save
	log.info(f"[UPDATE_INVOICE] 🔍 DEBUG - Invoice items type: {type(invoice_doc.items)}")
	log.info(f"[UPDATE_INVOICE] 🔍 DEBUG - Invoice items length: {len(invoice_doc.items) if hasattr(invoice_doc.items, '__len__') else 'N/A'}")
	if hasattr(invoice_doc.items, '__iter__') and not isinstance(invoice_doc.items, (str, dict)):
		for i, item in enumerate(invoice_doc.items[:3]):  # Log first 3 items
			log.info(f"[UPDATE_INVOICE] 🔍 DEBUG - Item {i}: type={type(item)}, keys={list(item.keys()) if hasattr(item, 'keys') else 'no keys'}")
			if hasattr(item, 'get'):
				log.info(f"[UPDATE_INVOICE] 🔍 DEBUG - Item {i} data: item_code={item.get('item_code')}, qty={item.get('qty')}, rate={item.get('rate')}")
				# Check for problematic fields that might contain lists
				for field_name in ['applied_offers', 'posa_offers']:
					if hasattr(item, field_name):
						field_value = getattr(item, field_name)
						if isinstance(field_value, list):
							log.error(f"[UPDATE_INVOICE] ❌ ERROR - Item {i} has {field_name} as list: {field_value}")
							# Remove or convert the problematic field
							setattr(item, field_name, json.dumps(field_value) if field_value else '[]')
							log.info(f"[UPDATE_INVOICE] ✅ Fixed {field_name} for item {i}")

	# Check if items is a list of dicts (which would cause the error)
	if isinstance(invoice_doc.items, list) and len(invoice_doc.items) > 0 and isinstance(invoice_doc.items[0], dict):
		log.error(f"[UPDATE_INVOICE] ❌ ERROR - Items is a list of dicts instead of child table objects!")
		log.error(f"[UPDATE_INVOICE] ❌ ERROR - This will cause 'Value for Items cannot be a list' error")
		# Try to fix by converting to proper child table format
		log.info(f"[UPDATE_INVOICE] 🔧 Attempting to fix items structure...")
		try:
			# Clear existing items
			invoice_doc.items = []
			# Add items properly
			for item_data in data.get("items", []):
				item = invoice_doc.append("items", item_data)
				log.info(f"[UPDATE_INVOICE] ✅ Added item: {item.item_code}")
		except Exception as fix_error:
			log.error(f"[UPDATE_INVOICE] ❌ Failed to fix items structure: {str(fix_error)}")
			frappe.throw(f"Failed to process invoice items: {str(fix_error)}")

	# === LOG VAT INFO TRƯỚC KHI SAVE ===
	log.info(f"[VAT_TRACE] BEFORE SAVE - Step 8: Invoice: {invoice_doc.name}")
	for i, item in enumerate(invoice_doc.items):
		log.info(f"[VAT_TRACE] BEFORE SAVE - Item {i+1} ({item.item_code}): custom_vat_applicable={item.custom_vat_applicable}, custom_vat_rate={item.custom_vat_rate}, custom_inventory_type={item.custom_inventory_type}")

	_set_item_level_discount_totals(invoice_doc)
	invoice_doc.save()
	log.info(f"[UPDATE_INVOICE] ✅ Invoice saved successfully: {invoice_doc.name}")

	# === LOG VAT INFO SAU KHI SAVE ===
	log.info(f"[VAT_TRACE] AFTER SAVE - Step 9: Invoice: {invoice_doc.name}")
	for i, item in enumerate(invoice_doc.items):
		log.info(f"[VAT_TRACE] AFTER SAVE - Item {i+1} ({item.item_code}): custom_vat_applicable={item.custom_vat_applicable}, custom_vat_rate={item.custom_vat_rate}, custom_inventory_type={item.custom_inventory_type}")

	# Calculate and set total item discount if field exists
	if hasattr(invoice_doc, 'posa_total_item_discount'):
		from posawesome.posawesome.api.invoice import _sum_item_level_discount
		invoice_doc.posa_total_item_discount = _sum_item_level_discount(invoice_doc)
		invoice_doc.save()
		log.info(f"[UPDATE_INVOICE] Total item discount updated: {invoice_doc.posa_total_item_discount}")

	# Return both the invoice doc and the updated data
	log.info(f"[VAT_TRACE] RESPONSE TO CLIENT - Step 10: Invoice: {invoice_doc.name}")
	for i, item in enumerate(invoice_doc.items):
		log.info(f"[VAT_TRACE] RESPONSE TO CLIENT - Item {i+1} ({item.item_code}): custom_vat_applicable={item.custom_vat_applicable}, custom_vat_rate={item.custom_vat_rate}, custom_inventory_type={item.custom_inventory_type}")

	log.info(f"[UPDATE_INVOICE] 📤 Preparing response data")
	response = invoice_doc.as_dict()
	response["conversion_rate"] = invoice_doc.conversion_rate
	response["plc_conversion_rate"] = invoice_doc.plc_conversion_rate
	response["exchange_rate_date"] = exchange_rate_date

	log.info(f"[UPDATE_INVOICE] 🎉 COMPLETED - Invoice: {invoice_doc.name}, Grand Total: {invoice_doc.grand_total}")
	return response


@frappe.whitelist()
def submit_invoice(invoice, data):
	log.info(f"[SUBMIT_INVOICE] 🎯 START - Processing invoice submission")

	# Log raw data received
	log.info(f"[SUBMIT_INVOICE] 📥 RAW INVOICE DATA: {invoice[:500]}...")
	log.info(f"[SUBMIT_INVOICE] 📥 RAW SUBMIT DATA: {data[:500]}...")

	data = json.loads(data)
	invoice = json.loads(invoice)
	invoice_name = invoice.get("name")

	log.info(f"[SUBMIT_INVOICE] 📋 BASIC INFO:")
	log.info(f"[SUBMIT_INVOICE] 📋   - Invoice Name: {invoice_name}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Customer: {invoice.get('customer', 'N/A')}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Grand Total: {invoice.get('grand_total', 0)}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Items Count: {len(invoice.get('items', []))}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Payments Count: {len(invoice.get('payments', []))}")

	log.info(f"[SUBMIT_INVOICE] 📋 SUBMIT PARAMETERS:")
	log.info(f"[SUBMIT_INVOICE] 📋   - Total Change: {data.get('total_change', 0)}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Paid Change: {data.get('paid_change', 0)}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Credit Change: {data.get('credit_change', 0)}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Redeemed Credit: {data.get('redeemed_customer_credit', 0)}")
	log.info(f"[SUBMIT_INVOICE] 📋   - Is Cashback: {data.get('is_cashback', False)}")

	# Clean up posa_offers before processing (convert lists to JSON strings)
	if 'posa_offers' in invoice and invoice['posa_offers']:
		log.info(f"[SUBMIT_INVOICE] 🧹 Cleaning up posa_offers before submit")
		for offer in invoice['posa_offers']:
			# Convert items list to JSON string if it exists
			if 'items' in offer and isinstance(offer['items'], list):
				offer['items'] = json.dumps(offer['items'])
				log.info(f"[SUBMIT_INVOICE] ✅ Converted posa_offers items to JSON string for submit")

	if not invoice_name or not frappe.db.exists("Sales Invoice", invoice_name):
		log.info(f"[SUBMIT_INVOICE] 🆕 Creating new invoice")
		created = update_invoice(json.dumps(invoice))
		invoice_name = created.get("name")
		invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
		log.info(f"[SUBMIT_INVOICE] ✅ New invoice created: {invoice_name}")
	else:
		log.info(f"[SUBMIT_INVOICE] 📝 Updating existing invoice: {invoice_name}")
		invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
		invoice_doc.update(invoice)
		log.info(f"[SUBMIT_INVOICE] ✅ Invoice updated: {invoice_name}")
	if invoice.get("posa_delivery_date"):
		invoice_doc.update_stock = 0
		log.info(f"[SUBMIT_INVOICE] 📅 Delivery date set - disabling stock update")

	mop_cash_list = [
		i.mode_of_payment
		for i in invoice_doc.payments
		if "cash" in i.mode_of_payment.lower() and i.type == "Cash"
	]
	log.info(f"[SUBMIT_INVOICE] 💰 Cash payment methods found: {len(mop_cash_list)}")

	if len(mop_cash_list) > 0:
		cash_account = get_bank_cash_account(mop_cash_list[0], invoice_doc.company)
		log.info(f"[SUBMIT_INVOICE] 🏦 Cash account resolved: {cash_account.get('account', 'N/A')}")
	else:
		cash_account = {"account": frappe.get_value("Company", invoice_doc.company, "default_cash_account")}
		log.info(f"[SUBMIT_INVOICE] 🏦 Using default cash account: {cash_account.get('account', 'N/A')}")

	# Update remarks with items details
	items = []
	for item in invoice_doc.items:
		if item.item_name and item.rate and item.qty:
			total = item.rate * item.qty
			items.append(f"{item.item_name} - Rate: {item.rate}, Qty: {item.qty}, Amount: {total}")

	# Add the grand total at the end of remarks
	grand_total = f"\nGrand Total: {invoice_doc.grand_total}"
	items.append(grand_total)

	invoice_doc.remarks = "\n".join(items)

	# Calculate stock_qty for all items before submit (ensure inventory accuracy)
	log.info(f"[SUBMIT_INVOICE] 📦 Calculating stock_qty for {len(invoice_doc.items)} items before submit")
	for i, item in enumerate(invoice_doc.items):
		if hasattr(item, 'qty') and hasattr(item, 'conversion_factor'):
			original_stock_qty = getattr(item, 'stock_qty', None)
			qty = flt(item.qty)
			conversion_factor = flt(item.conversion_factor)

			if conversion_factor > 0:
				calculated_stock_qty = qty * conversion_factor
				item.stock_qty = calculated_stock_qty
				log.info(f"[SUBMIT_INVOICE] 📦 Item {i+1} ({item.item_code}): stock_qty = {qty} × {conversion_factor} = {calculated_stock_qty}")
			else:
				item.stock_qty = qty
				log.warning(f"[SUBMIT_INVOICE] ⚠️ Item {i+1} ({item.item_code}): conversion_factor is 0, setting stock_qty = qty = {qty}")

			if original_stock_qty is not None and original_stock_qty != item.stock_qty:
				log.info(f"[SUBMIT_INVOICE] 📦 Item {i+1} ({item.item_code}): stock_qty updated from {original_stock_qty} to {item.stock_qty}")
		else:
			log.error(f"[SUBMIT_INVOICE] ❌ Item {i+1} ({item.item_code}): missing qty or conversion_factor")

	log.info(f"[SUBMIT_INVOICE] ✅ Stock quantities calculated for submit")

	# Clean up problematic fields that contain lists before saving
	log.info(f"[SUBMIT_INVOICE] 🧹 Cleaning up item fields before save")
	for item in invoice_doc.items:
		for field_name in ['applied_offers', 'posa_offers']:
			if hasattr(item, field_name):
				field_value = getattr(item, field_name)
				if isinstance(field_value, list):
					log.info(f"[SUBMIT_INVOICE] 🔧 Converting {field_name} list to JSON string for item {item.item_code}")
					setattr(item, field_name, json.dumps(field_value) if field_value else '[]')

	# creating advance payment
	if data.get("credit_change"):
		log.info(f"[SUBMIT_INVOICE] 💳 Creating advance payment - Amount: {data.get('credit_change')}")
		advance_payment_entry = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"mode_of_payment": "Cash",
				"paid_to": cash_account["account"],
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": invoice_doc.get("customer"),
				"paid_amount": invoice_doc.get("credit_change"),
				"received_amount": invoice_doc.get("credit_change"),
				"company": invoice_doc.get("company"),
			}
		)

		advance_payment_entry.flags.ignore_permissions = True
		frappe.flags.ignore_account_permission = True
		advance_payment_entry.save()
		advance_payment_entry.submit()
		log.info(f"[SUBMIT_INVOICE] ✅ Advance payment created: {advance_payment_entry.name}")
	else:
		log.info(f"[SUBMIT_INVOICE] 💸 No credit change - skipping advance payment")

	# calculating cash
	total_cash = 0
	if data.get("redeemed_customer_credit"):
		total_cash = invoice_doc.total - float(data.get("redeemed_customer_credit"))
		log.info(f"[SUBMIT_INVOICE] 💰 Calculated total cash after credit redemption: {total_cash}")

	is_payment_entry = 0
	if data.get("redeemed_customer_credit"):
		log.info(f"[SUBMIT_INVOICE] 🎫 Processing customer credit redemption")
		for row in data.get("customer_credit_dict"):
			if row["type"] == "Advance" and row["credit_to_redeem"]:
				log.info(f"[SUBMIT_INVOICE] 🔄 Processing advance credit: {row['credit_origin']}, Amount: {row['credit_to_redeem']}")
				advance = frappe.get_doc("Payment Entry", row["credit_origin"])

				advance_payment = {
					"reference_type": "Payment Entry",
					"reference_name": advance.name,
					"remarks": advance.remarks,
					"advance_amount": advance.unallocated_amount,
					"allocated_amount": row["credit_to_redeem"],
				}

				advance_row = invoice_doc.append("advances", {})
				advance_row.update(advance_payment)
				ensure_child_doctype(invoice_doc, "advances", "Sales Invoice Advance")
				invoice_doc.is_pos = 0
				is_payment_entry = 1
				log.info(f"[SUBMIT_INVOICE] ✅ Advance credit processed: {advance.name}")
	else:
		log.info(f"[SUBMIT_INVOICE] 🎫 No customer credit redemption")

	payments = invoice_doc.payments

	# if frappe.get_value("POS Profile", invoice_doc.pos_profile, "posa_auto_set_batch"):
	#     set_batch_nos(invoice_doc, "warehouse", throw=True)
	set_batch_nos_for_bundels(invoice_doc, "warehouse", throw=True)

	invoice_doc.flags.ignore_permissions = True
	frappe.flags.ignore_account_permission = True
	# invoice_doc.posa_is_printed = 1
	if data.get("posa_is_printed") is not None:
		invoice_doc.posa_is_printed = data.get("posa_is_printed")
	if data.get("tax_report") is not None:
		invoice_doc.tax_report = data.get("tax_report")

# === Attach Customer Tax ID to Invoice (simple mode, corrected) ===
	log.info(f"[UPDATE_INVOICE] 🆔 Attaching customer tax ID")
	try:
		if invoice_doc.get("customer"):
			cust_tax_id = frappe.db.get_value("Customer", invoice_doc.customer, "tax_id")
			log.info(f"[UPDATE_INVOICE] 🆔 Customer tax ID: {cust_tax_id}")

			if cust_tax_id:
				has_tax_id = invoice_doc.meta.has_field("tax_id")
				has_customer_tax_id = invoice_doc.meta.has_field("customer_tax_id")

				log.info(f"[UPDATE_INVOICE] 🆔 Field availability - tax_id: {has_tax_id}, customer_tax_id: {has_customer_tax_id}")

				# Ưu tiên set vào đúng tên trường
				if has_tax_id:
					invoice_doc.tax_id = cust_tax_id
					log.info(f"[UPDATE_INVOICE] ✅ Set tax_id field: {cust_tax_id}")
				if has_customer_tax_id:
					invoice_doc.customer_tax_id = cust_tax_id
					log.info(f"[UPDATE_INVOICE] ✅ Set customer_tax_id field: {cust_tax_id}")

				# Nếu không có field nào trên Invoice → fallback ghi vào remarks
				if not (has_tax_id or has_customer_tax_id):
					line = f"Tax ID: {cust_tax_id}"
					current = (invoice_doc.remarks or "")
					if line not in current:
						invoice_doc.remarks = (current + "\n" if current else "") + line
						log.info(f"[UPDATE_INVOICE] ✅ Added tax ID to remarks: {cust_tax_id}")
			else:
				log.info(f"[UPDATE_INVOICE] ℹ️ No tax ID found for customer: {invoice_doc.customer}")
		else:
			log.info(f"[UPDATE_INVOICE] ℹ️ No customer specified for tax ID attachment")
	except Exception as e:
		log.error(f"[UPDATE_INVOICE] ❌ Failed to attach customer tax_id to invoice {invoice_doc.name}: {str(e)}")
		frappe.log_error(f"[POSA] Failed to attach customer tax_id to invoice {invoice_doc.name}: {e}")

	invoice_doc.save()

	if data.get("due_date"):
		frappe.db.set_value(
			"Sales Invoice",
			invoice_doc.name,
			"due_date",
			data.get("due_date"),
			update_modified=False,
		)

	if frappe.get_value(
		"POS Profile",
		invoice_doc.pos_profile,
		"posa_allow_submissions_in_background_job",
	):
		log.info(f"[SUBMIT_INVOICE] 🔄 Background job enabled - queuing invoices")
		invoices_list = frappe.get_all(
			"Sales Invoice",
			filters={
				"posa_pos_opening_shift": invoice_doc.posa_pos_opening_shift,
				"docstatus": 0,
				"posa_is_printed": 1,
			},
		)
		log.info(f"[SUBMIT_INVOICE] 📋 Found {len(invoices_list)} invoices for background processing")

		for invoice in invoices_list:
			log.info(f"[SUBMIT_INVOICE] ⏳ Queuing invoice: {invoice.name}")
			enqueue(
				method=submit_in_background_job,
				queue="short",
				timeout=1000,
				is_async=True,
				kwargs={
					"invoice": invoice.name,
					"data": data,
					"is_payment_entry": is_payment_entry,
					"total_cash": total_cash,
					"cash_account": cash_account,
					"payments": payments,
				},
			)
		log.info(f"[SUBMIT_INVOICE] ✅ All invoices queued for background processing")
	else:
		log.info(f"[SUBMIT_INVOICE] ⚡ Call Submitting invoice immediately - Directly Mode")

		_set_item_level_discount_totals(invoice_doc)
		invoice_doc.submit()
  
		log.info(f"[SUBMIT_INVOICE] ✅ Invoice submitted successfully: {invoice_doc.name}")

		redeeming_customer_credit(invoice_doc, data, is_payment_entry, total_cash, cash_account, payments)
		log.info(f"[SUBMIT_INVOICE] ✅ Customer credit redeemed")

	result = {"name": invoice_doc.name, "status": invoice_doc.docstatus}
	log.info(f"[SUBMIT_INVOICE] 🎉 COMPLETED - Invoice: {invoice_doc.name}, Status: {invoice_doc.docstatus}")
	return result


def submit_in_background_job(kwargs):
	log.info(f"[BACKGROUND_JOB] 🎯 START - Processing invoice in background: {kwargs.get('invoice')}")

	invoice = kwargs.get("invoice")
	invoice_doc = kwargs.get("invoice_doc")
	data = kwargs.get("data")
	is_payment_entry = kwargs.get("is_payment_entry")
	total_cash = kwargs.get("total_cash")
	cash_account = kwargs.get("cash_account")
	payments = kwargs.get("payments")

	log.info(f"[BACKGROUND_JOB] 📋 Loading invoice document: {invoice}")
	invoice_doc = frappe.get_doc("Sales Invoice", invoice)
	log.info(f"[BACKGROUND_JOB] ✅ Invoice loaded: {invoice_doc.name}")

	# Clean up posa_offers in background job (convert lists to JSON strings)
	if hasattr(invoice_doc, 'posa_offers') and invoice_doc.posa_offers:
		log.info(f"[BACKGROUND_JOB] 🧹 Cleaning up posa_offers in background job")
		for offer in invoice_doc.posa_offers:
			# Convert items list to JSON string if it exists
			if hasattr(offer, 'items') and isinstance(offer.items, list):
				offer.items = json.dumps(offer.items)
				log.info(f"[BACKGROUND_JOB] ✅ Converted posa_offers items to JSON string in background")

	# Calculate stock_qty for background job items
	log.info(f"[BACKGROUND_JOB] 📦 Calculating stock_qty for {len(invoice_doc.items)} items in background")
	for i, item in enumerate(invoice_doc.items):
		if hasattr(item, 'qty') and hasattr(item, 'conversion_factor'):
			qty = flt(item.qty)
			conversion_factor = flt(item.conversion_factor)

			if conversion_factor > 0:
				calculated_stock_qty = qty * conversion_factor
				item.stock_qty = calculated_stock_qty
				log.info(f"[BACKGROUND_JOB] 📦 Item {i+1} ({item.item_code}): stock_qty = {qty} × {conversion_factor} = {calculated_stock_qty}")
			else:
				item.stock_qty = qty
				log.warning(f"[BACKGROUND_JOB] ⚠️ Item {i+1} ({item.item_code}): conversion_factor is 0, setting stock_qty = qty = {qty}")

	log.info(f"[BACKGROUND_JOB] ✅ Stock quantities calculated for background job")

	# Update remarks with items details for background job
	items = []
	for item in invoice_doc.items:
		if item.item_name and item.rate and item.qty:
			total = item.rate * item.qty
			items.append(f"{item.item_name} - Rate: {item.rate}, Qty: {item.qty}, Amount: {total}")

	# Add the grand total at the end of remarks
	grand_total = f"\nGrand Total: {invoice_doc.grand_total}"
	items.append(grand_total)

	invoice_doc.remarks = "\n".join(items)
	# === Attach Customer Tax ID to Invoice (simple mode) ===
	try:
		if invoice_doc.get("customer"):
			cust_tax_id = frappe.db.get_value("Customer", invoice_doc.customer, "tax_id")
			if cust_tax_id:
				has_tax_id = invoice_doc.meta.has_field("tax_id")
				has_customer_tax_id = invoice_doc.meta.has_field("customer_tax_id")

				# Ưu tiên set vào đúng tên trường
				if has_tax_id:
					invoice_doc.tax_id = cust_tax_id
				if has_customer_tax_id:
					invoice_doc.customer_tax_id = cust_tax_id

				# Nếu không có field nào trên Invoice → fallback ghi vào remarks
				if not (has_tax_id or has_customer_tax_id):
					line = f"Tax ID: {cust_tax_id}"
					current = (invoice_doc.remarks or "")
					if line not in current:
						invoice_doc.remarks = (current + "\n" if current else "") + line
	except Exception as e:
		frappe.log_error(f"[POSA] Failed to attach customer tax_id to invoice {invoice_doc.name}: {e}")

	invoice_doc.save()
	log.info(f"[BACKGROUND_JOB] 💾 Invoice saved: {invoice_doc.name}")

	_set_item_level_discount_totals(invoice_doc)
	invoice_doc.save()
	invoice_doc.submit()
	log.info(f"[BACKGROUND_JOB] ✅ Invoice submitted: {invoice_doc.name}")

	redeeming_customer_credit(invoice_doc, data, is_payment_entry, total_cash, cash_account, payments)
	log.info(f"[BACKGROUND_JOB] ✅ Customer credit redeemed for: {invoice_doc.name}")

	log.info(f"[BACKGROUND_JOB] 🎉 COMPLETED - Background processing finished for: {invoice_doc.name}")


@frappe.whitelist()
def delete_invoice(invoice):
	# Check if invoice exists
	if not frappe.db.exists("Sales Invoice", invoice):
		frappe.throw(_("Invoice {0} not found").format(invoice))

	# Get invoice details
	docstatus = frappe.get_value("Sales Invoice", invoice, "docstatus")
	posa_is_printed = frappe.get_value("Sales Invoice", invoice, "posa_is_printed")

	# Check if already submitted
	if docstatus == 1:
		frappe.throw(_("Cannot delete submitted invoice {0}").format(invoice))

	# Check if already printed
	if posa_is_printed:
		frappe.throw(_("This invoice {0} cannot be deleted because it has been printed").format(invoice))

	# Check user permissions
	if not frappe.has_permission("Sales Invoice", "delete"):
		frappe.throw(_("User not allowed to delete Sales Invoice: {0}").format(invoice))

	# Attempt to delete
	try:
		frappe.delete_doc("Sales Invoice", invoice, force=1)
		return _("Invoice {0} Deleted").format(invoice)
	except Exception as e:
		log.error(f"Failed to delete invoice {invoice}: {str(e)}")
		frappe.throw(_("Failed to delete invoice {0}: {1}").format(invoice, str(e)))


@frappe.whitelist()
def get_draft_invoices(pos_opening_shift):
	invoices_list = frappe.get_list(
		"Sales Invoice",
		filters={
			"posa_pos_opening_shift": pos_opening_shift,
			"docstatus": 0,
			"posa_is_printed": 0,
		},
		fields=["name"],
		limit_page_length=0,
		order_by="modified desc",
	)
	data = []
	for invoice in invoices_list:
		data.append(frappe.get_cached_doc("Sales Invoice", invoice["name"]))
	return data


@frappe.whitelist()
def search_invoices_for_return(
	invoice_name,
	company,
	customer_name=None,
	customer_id=None,
	mobile_no=None,
	tax_id=None,
	from_date=None,
	to_date=None,
	min_amount=None,
	max_amount=None,
	page=1,
):
	"""
	Search for invoices that can be returned with separate customer search fields and pagination

	Args:
	    invoice_name: Invoice ID to search for
	    company: Company to search in
	    customer_name: Customer name to search for
	    customer_id: Customer ID to search for
	    mobile_no: Mobile number to search for
	    tax_id: Tax ID to search for
	    from_date: Start date for filtering
	    to_date: End date for filtering
	    min_amount: Minimum invoice amount to filter by
	    max_amount: Maximum invoice amount to filter by
	    page: Page number for pagination (starts from 1)

	Returns:
	    Dictionary with:
	        - invoices: List of invoice documents
	        - has_more: Boolean indicating if there are more invoices to load
	"""
	# Start with base filters
	filters = {
		"company": company,
		"docstatus": 1,
		"is_return": 0,
	}

	# Convert page to integer if it's a string
	if page and isinstance(page, str):
		page = int(page)
	else:
		page = 1  # Default to page 1

	# Items per page - can be adjusted based on performance requirements
	page_length = 100
	start = (page - 1) * page_length

	# Add invoice name filter if provided
	if invoice_name:
		filters["name"] = ["like", f"%{invoice_name}%"]

	# Add date range filters if provided
	if from_date:
		filters["posting_date"] = [">=", from_date]

	if to_date:
		if "posting_date" in filters:
			filters["posting_date"] = ["between", [from_date, to_date]]
		else:
			filters["posting_date"] = ["<=", to_date]

	# Add amount filters if provided
	if min_amount:
		filters["grand_total"] = [">=", float(min_amount)]

	if max_amount:
		if "grand_total" in filters:
			# If min_amount was already set, change to between
			filters["grand_total"] = ["between", [float(min_amount), float(max_amount)]]
		else:
			filters["grand_total"] = ["<=", float(max_amount)]

	# If any customer search criteria is provided, find matching customers
	customer_ids = []
	if customer_name or customer_id or mobile_no or tax_id:
		conditions = []
		params = {}

		if customer_name:
			conditions.append("customer_name LIKE %(customer_name)s")
			params["customer_name"] = f"%{customer_name}%"

		if customer_id:
			conditions.append("name LIKE %(customer_id)s")
			params["customer_id"] = f"%{customer_id}%"

		if mobile_no:
			conditions.append("mobile_no LIKE %(mobile_no)s")
			params["mobile_no"] = f"%{mobile_no}%"

		if tax_id:
			conditions.append("tax_id LIKE %(tax_id)s")
			params["tax_id"] = f"%{tax_id}%"

		# Build the WHERE clause for the query
		where_clause = " OR ".join(conditions)
		customer_query = f"""
            SELECT name 
            FROM `tabCustomer`
            WHERE {where_clause}
            LIMIT 100
        """

		customers = frappe.db.sql(customer_query, params, as_dict=True)
		customer_ids = [c.name for c in customers]

		# If we found matching customers, add them to the filter
		if customer_ids:
			filters["customer"] = ["in", customer_ids]
		# If customer search criteria provided but no matches found, return empty
		elif any([customer_name, customer_id, mobile_no, tax_id]):
			return {"invoices": [], "has_more": False}

	# Count total invoices matching the criteria (for has_more flag)
	total_count_query = frappe.get_list(
		"Sales Invoice",
		filters=filters,
		fields=["count(name) as total_count"],
		as_list=False,
	)
	total_count = total_count_query[0].total_count if total_count_query else 0

	# Get invoices matching all criteria with pagination
	invoices_list = frappe.get_list(
		"Sales Invoice",
		filters=filters,
		fields=["name"],
		limit_start=start,
		limit_page_length=page_length,
		order_by="posting_date desc, name desc",
	)

	# Process and return the results
	data = []

	# Process invoices and check for returns
	for invoice in invoices_list:
		invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)

		# Check if any items have already been returned
		has_returns = frappe.get_all(
			"Sales Invoice",
			filters={"return_against": invoice.name, "docstatus": 1},
			fields=["name"],
		)

		if has_returns:
			# Calculate returned quantity per item_code
			returned_qty = {}
			for ret_inv in has_returns:
				ret_doc = frappe.get_doc("Sales Invoice", ret_inv.name)
				for item in ret_doc.items:
					returned_qty[item.item_code] = returned_qty.get(item.item_code, 0) + abs(item.qty)

			# Filter items with remaining qty
			filtered_items = []
			for item in invoice_doc.items:
				remaining_qty = item.qty - returned_qty.get(item.item_code, 0)
				if remaining_qty > 0:
					new_item = item.as_dict().copy()
					new_item["qty"] = remaining_qty
					new_item["amount"] = remaining_qty * item.rate
					if item.get("stock_qty"):
						new_item["stock_qty"] = (
							item.stock_qty / item.qty * remaining_qty if item.qty else remaining_qty
						)
					filtered_items.append(frappe._dict(new_item))

			if filtered_items:
				# Create a copy of invoice with filtered items
				filtered_invoice = frappe.get_doc("Sales Invoice", invoice.name)
				filtered_invoice.items = filtered_items
				data.append(filtered_invoice)
		else:
			data.append(invoice_doc)

	# Check if there are more results
	has_more = (start + page_length) < total_count

	return {"invoices": data, "has_more": has_more}


@frappe.whitelist()
def create_sales_invoice_from_order(sales_order):
	sales_invoice = make_sales_invoice(sales_order, ignore_permissions=True)
	sales_invoice.save()
	return sales_invoice


@frappe.whitelist()
def delete_sales_invoice(sales_invoice):
	frappe.delete_doc("Sales Invoice", sales_invoice)


@frappe.whitelist()
def get_sales_invoice_child_table(sales_invoice, sales_invoice_item):
	parent_doc = frappe.get_doc("Sales Invoice", sales_invoice)
	child_doc = frappe.get_doc("Sales Invoice Item", {"parent": parent_doc.name, "name": sales_invoice_item})
	return child_doc


@frappe.whitelist()
def update_invoice_from_order(data):
	data = json.loads(data)
	invoice_doc = frappe.get_doc("Sales Invoice", data.get("name"))
	invoice_doc.update(data)
	invoice_doc.save()
	return invoice_doc


@frappe.whitelist()
def get_available_currencies():
	"""Get list of available currencies from ERPNext"""
	return frappe.get_all(
		"Currency",
		fields=["name", "currency_name"],
		filters={"enabled": 1},
		order_by="currency_name",
	)


@frappe.whitelist()
def fetch_exchange_rate(currency: str, company: str, posting_date: str = None):
	"""Return latest exchange rate and its date."""
	company_currency = frappe.get_cached_value("Company", company, "default_currency")
	rate, date = get_latest_rate(currency, company_currency)
	return {"exchange_rate": rate, "date": date}


@frappe.whitelist()
def fetch_exchange_rate_pair(from_currency: str, to_currency: str, posting_date: str = None):
	"""Return latest exchange rate between two currencies along with rate date."""
	rate, date = get_latest_rate(from_currency, to_currency)
	return {"exchange_rate": rate, "date": date}


@frappe.whitelist()
def get_price_list_currency(price_list: str) -> str:
	"""Return the currency of the given Price List."""
	if not price_list:
		return None
	return frappe.db.get_value("Price List", price_list, "currency")
