# -*- coding: utf-8 -*-
# Copyright (c) 2023, POSAwesome and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import nowdate
from posawesome.posawesome.utils.logging import get_logger

log = get_logger("discount")

@frappe.whitelist()
def calculate_discounts(invoice_data):
    """
    Master function to calculate all applicable discounts for a given invoice state.
    :param invoice_data: JSON string representing the current invoice (items, customer, etc.)
    :return: A dictionary with the updated invoice state.
    """
    try:
        log.info("[DISCOUNT_CALC] 🎯 START - POS Discount Calculation")
        log.info(f"[DISCOUNT_CALC] 📥 RAW DATA RECEIVED: {invoice_data[:500]}...")  # Log first 500 chars

        data = json.loads(invoice_data)

        log.info(f"[DISCOUNT_CALC] 📋 REQUEST DETAILS:")
        log.info(f"[DISCOUNT_CALC] 📋   - Customer: {data.get('customer', 'N/A')}")
        log.info(f"[DISCOUNT_CALC] 📋   - POS Profile: {data.get('pos_profile', 'N/A')}")
        log.info(f"[DISCOUNT_CALC] 📋   - Items Count: {len(data.get('items', []))}")
        log.info(f"[DISCOUNT_CALC] 📋   - Coupons Count: {len(data.get('coupons', []))}")

        if data.get('items'):
            log.info(f"[DISCOUNT_CALC] 📦 ITEMS IN REQUEST:")
            for i, item in enumerate(data['items'][:3]):  # Log first 3 items
                log.info(f"[DISCOUNT_CALC] 📦   - Item {i+1}: {item.get('item_code')} (qty: {item.get('qty')}, rate: {item.get('rate')})")

        calculator = DiscountCalculator(data)
        result = calculator.process()

        log.info(f"[DISCOUNT_CALC] ✅ COMPLETED - Applied {len(result.get('applied_offers', []))} offers")
        log.info(f"[DISCOUNT_CALC] 📤 RESPONSE: {len(result.get('updated_items', []))} items updated")

        return result

    except Exception as e:
        log.error(f"[DISCOUNT_CALC] ❌ ERROR - POS Discount Calculation failed: {str(e)}")
        log.error({"title": "POS Discount Calculation Error", "traceback": frappe.get_traceback()})
        frappe.throw(str(e))

class DiscountCalculator:
    def __init__(self, invoice_data):
        log.info(f"Initializing DiscountCalculator for customer: {invoice_data.get('customer')}")
        self.items = invoice_data.get("items", [])
        self.customer = invoice_data.get("customer")
        self.pos_profile_name = invoice_data.get("pos_profile")
        self.pos_profile = frappe.get_doc("POS Profile", self.pos_profile_name)
        self.coupons = invoice_data.get("coupons", [])
        self.applicable_offers = []
        self.applied_offers = []
        self.totals = {"grand_total": 0, "net_total": 0}

    def _reset_item_prices(self):
        """Reset all items to their original prices before applying new offers."""
        log.info("Resetting all items to original prices.")
        for item in self.items:
            if not item.get("posa_is_offer"):  # Don't reset gift items
                # Log current state
                current_rate = item.get("rate", 0)
                base_price_list_rate = item.get("base_price_list_rate", 0)
                conversion_factor = item.get("conversion_factor", 1)
                uom = item.get("uom")
                stock_uom = item.get("stock_uom")

                log.info(f"Resetting item {item.get('item_code')}: current_rate={current_rate}, base_price_list_rate={base_price_list_rate}, uom={uom}, stock_uom={stock_uom}, conversion_factor={conversion_factor}")

                # Reset to base price list rate (always in stock UOM) converted to display UOM
                if uom == stock_uom:
                    reset_rate = base_price_list_rate
                else:
                    reset_rate = base_price_list_rate * conversion_factor

                item["rate"] = reset_rate
                item["amount"] = reset_rate * item.get("qty", 0)

                # Reset discount fields
                item["discount_amount"] = 0
                item["discount_percentage"] = 0
                item["posa_offer_applied"] = 0

                # Clear applied offers log
                item["applied_offers"] = []

                log.info(f"Item {item.get('item_code')} reset: new_rate={item['rate']}, amount={item['amount']}")

        log.info("All items reset to original prices.")

    def process(self):
        # Reset all items to original prices before applying new offers
        self._reset_item_prices()
        self._get_valid_offers()
        self._find_applicable_offers()
        self._apply_offers()
        self._calculate_totals()

        log.info(f"Process finished. Applied {len(self.applied_offers)} offers.")
        applied_offer_names = [f"{o.get('name')} ({o.get('offer')})" for o in self.applied_offers]
        log.info(f"Applied offers details: {applied_offer_names}")

        # Log final item states
        for item in self.items:
            log.info(f"Final item {item.get('item_code')}: qty={item.get('qty')}, rate={item.get('rate')}, amount={item.get('amount')}, discount_amount={item.get('discount_amount')}, posa_offer_applied={item.get('posa_offer_applied')}")

        return {
            "status": "success",
            "updated_items": self.items,
            "applied_offers": self.applied_offers,
            "totals": self.totals
        }

    def _get_valid_offers(self):
        date = nowdate()
        self.valid_offers = frappe.db.sql(
            """
            SELECT * FROM `tabPOS Offer`
            WHERE
                disable = 0 AND
                is_template = 0 AND
                company = %(company)s AND
                (pos_profile IS NULL OR pos_profile = '' OR pos_profile = %(pos_profile)s) AND
                (valid_from IS NULL OR valid_from = '' OR valid_from <= %(date)s) AND
                (valid_upto IS NULL OR valid_upto = '' OR valid_upto >= %(date)s)
            ORDER BY creation DESC
            """,
            {
                "company": self.pos_profile.company,
                "pos_profile": self.pos_profile_name,
                "date": date,
            },
            as_dict=1,
        )
        log.info(f"Found {len(self.valid_offers)} valid offers for profile '{self.pos_profile_name}' (templates excluded).")

    def _find_applicable_offers(self):
        log.info(f"Checking {len(self.valid_offers)} valid offers for applicability...")
        for offer in self.valid_offers:
            log.info(f"Checking offer '{offer.name}' of type '{offer.get('offer')}' with apply_on='{offer.get('apply_on')}'")
            if self._check_offer_conditions(offer):
                self.applicable_offers.append(offer)
                log.info(f"✅ Offer '{offer.name}' is applicable")
            else:
                log.info(f"❌ Offer '{offer.name}' is NOT applicable")
        log.info(f"Found {len(self.applicable_offers)} applicable offers based on current cart.")

    def _check_offer_conditions(self, offer):
        if not self._check_coupon(offer):
            log.info(f"❌ Coupon check failed for offer '{offer.name}'")
            return False

        apply_on = offer.get("apply_on")
        log.info(f"Checking apply_on='{apply_on}' for offer '{offer.name}'")

        if apply_on == "Item Code":
            result = self._check_item_code_offer(offer)
            log.info(f"Item Code check result for '{offer.name}': {result}")
            return result
        elif apply_on == "Item Group":
            result = self._check_item_group_offer(offer)
            log.info(f"Item Group check result for '{offer.name}': {result}")
            return result
        elif apply_on == "Brand":
            result = self._check_brand_offer(offer)
            log.info(f"Brand check result for '{offer.name}': {result}")
            return result
        elif apply_on == "Transaction":
            result = self._check_transaction_offer(offer)
            log.info(f"Transaction check result for '{offer.name}': {result}")
            return result

        log.info(f"❌ Unknown apply_on='{apply_on}' for offer '{offer.name}'")
        return False

    def _check_coupon(self, offer):
        if not offer.get("coupon_based"):
            return True
        is_valid = any(c.get("pos_offer") == offer.get("name") for c in self.coupons)
        if is_valid:
            log.info(f"Coupon valid for offer '{offer.name}'.")
        return is_valid

    def is_offer_active_in_time_slots(self, offer):
        """Check if offer is active in current time slot based on JSON configuration"""
        time_slots_json = offer.get("available_time_in_day")
        if not time_slots_json:
            log.info(f"Offer '{offer.get('name')}' has no time restrictions - always active")
            return True  # No time restriction = always active
        
        try:
            time_slots = json.loads(time_slots_json)
            log.info(f"Offer '{offer.get('name')}' has {len(time_slots)} time slots configured")
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in available_time_in_day for offer '{offer.get('name')}': {e}")
            return False  # Invalid JSON = inactive
        
        current_time = frappe.utils.nowtime()  # HH:MM:SS format
        current_day = frappe.utils.getdate().strftime('%A').lower()  # monday, tuesday, etc.
        
        log.info(f"Checking time slots for offer '{offer.get('name')}' - Current: {current_day} {current_time}")
        
        for slot in time_slots:
            days_of_week = slot.get("days_of_week", [])
            start_time = slot.get("start_time")
            end_time = slot.get("end_time")
            is_overnight = slot.get("is_overnight", False)
            
            # Check if current day is in allowed days
            if current_day not in [day.lower() for day in days_of_week]:
                continue  # Not active on this day
            
            # Check time range
            if is_overnight:
                # Handle overnight offers (e.g., 22:00 - 02:00)
                if end_time < start_time:
                    # Overnight: current time >= start OR current time <= end
                    if current_time >= start_time or current_time <= end_time:
                        log.info(f"✅ Offer '{offer.get('name')}' active (overnight slot: {start_time}-{end_time})")
                        return True
                else:
                    # Normal overnight handling
                    if current_time >= start_time or current_time <= end_time:
                        log.info(f"✅ Offer '{offer.get('name')}' active (overnight slot: {start_time}-{end_time})")
                        return True
            else:
                # Normal time range
                if start_time <= current_time <= end_time:
                    log.info(f"✅ Offer '{offer.get('name')}' active (slot: {start_time}-{end_time})")
                    return True
        
        log.info(f"❌ Offer '{offer.get('name')}' not active in any time slot")
        return False

    def _check_item_code_offer(self, offer):
        log.info(f"Checking Item Code offer: offer.item='{offer.get('item')}', offer conditions: min_qty={offer.get('min_qty')}, max_qty={offer.get('max_qty')}")

        # Collect all items with matching item_code (for per-item discount logic)
        matching_items = []
        total_qty = 0
        total_amount = 0

        for item in self.items:
            item_code = item.get("item_code")
            qty = item.get("qty", 0)
            price_list_rate = item.get("price_list_rate", 0)
            amount = qty * price_list_rate
            is_offer = item.get("posa_is_offer", 0)

            log.info(f"Checking item: code='{item_code}', qty={qty}, price_list_rate={price_list_rate}, amount={amount}, is_offer={is_offer}")
            log.info(f"Comparing: item_code == offer.item: '{item_code}' == '{offer.get('item')}' -> {item_code == offer.get('item')}")
            log.info(f"Conditions: not is_offer: {not is_offer}")

            if item_code == offer.get("item") and not is_offer:
                matching_items.append(item)
                total_qty += qty
                total_amount += amount
                log.info(f"✅ Found matching item: {item.get('posa_row_id')}, UOM: {item.get('uom')}")

        if not matching_items:
            log.info(f"❌ No matching items found for Item Code offer")
            return False

        log.info(f"Found {len(matching_items)} matching items, total_qty={total_qty}, total_amount={total_amount}")

        # For block-based discounts and tiered pricing, collect all matching items
        # The block/tiered calculation will handle per-item UOM validation
        if offer.get("is_used_block") or offer.get("is_used_tiered_pricing"):
            log.info(f"✅ Block-based or tiered pricing offer, collecting all matching items")
            offer["items"] = [item.get("posa_row_id") for item in matching_items]
            offer["original_qty"] = total_qty  # Total qty across all matching items
            log.info(f"✅ Block-based or tiered Item Code offer applicable, items: {offer['items']}, total_original_qty: {total_qty}")
            return True

        # For regular offers, check total qty/amount conditions across all matching items
        min_qty = offer.get("min_qty")
        max_qty = offer.get("max_qty")

        # Check minimum quantity requirement
        if min_qty and total_qty < min_qty:
            log.info(f"❌ Total qty {total_qty} < min_qty {min_qty}, offer not applicable")
            return False

        # For max_qty logic: offer applies to max_qty items total, excess pays normal price
        if max_qty and max_qty > 0:
            condition_result = True
            log.info(f"✅ Total qty {total_qty} >= min_qty {min_qty}, offer applicable (max_qty {max_qty} will limit discount)")
        else:
            # No max_qty restriction, check normal conditions
            condition_result = self._check_qty_amount_conditions(offer, total_qty, total_amount)

        log.info(f"Total qty/amount condition result: {condition_result}")
        if condition_result:
            offer["items"] = [item.get("posa_row_id") for item in matching_items]
            offer["original_qty"] = total_qty
            log.info(f"✅ Item Code offer applicable, items: {offer['items']}, total_original_qty: {total_qty}")
            return True

        log.info(f"❌ Item Code offer not applicable")
        return False

    def _check_item_group_offer(self, offer):
        group_items_rows = []
        total_qty = 0
        total_amount = 0
        for item in self.items:
            if item.get("item_group") == offer.get("item_group") and not item.get("posa_is_offer"):
                group_items_rows.append(item.get("posa_row_id"))
                total_qty += item.get("qty", 0)
                total_amount += item.get("qty", 0) * item.get("price_list_rate", 0)
        
        if self._check_qty_amount_conditions(offer, total_qty, total_amount):
            offer["items"] = group_items_rows
            return True
        return False

    def _check_brand_offer(self, offer):
        brand_items_rows = []
        total_qty = 0
        total_amount = 0
        for item in self.items:
            if item.get("brand") == offer.get("brand") and not item.get("posa_is_offer"):
                brand_items_rows.append(item.get("posa_row_id"))
                total_qty += item.get("qty", 0)
                total_amount += item.get("qty", 0) * item.get("price_list_rate", 0)

        if self._check_qty_amount_conditions(offer, total_qty, total_amount):
            offer["items"] = brand_items_rows
            return True
        return False

    def _check_transaction_offer(self, offer):
        total_qty = sum(item.get("qty", 0) for item in self.items if not item.get("posa_is_offer"))
        total_amount = sum(item.get("qty", 0) * item.get("price_list_rate", 0) for item in self.items if not item.get("posa_is_offer"))

        log.info(f"Transaction offer '{offer.name}': total_qty={total_qty}, total_amount={total_amount}")
        log.info(f"Transaction offer conditions: min_qty={offer.get('min_qty')}, max_qty={offer.get('max_qty')}, min_amt={offer.get('min_amt')}, max_amt={offer.get('max_amt')}")

        condition_result = self._check_qty_amount_conditions(offer, total_qty, total_amount)
        log.info(f"Transaction offer condition check result: {condition_result}")

        if condition_result:
            offer["items"] = [item.get("posa_row_id") for item in self.items]
            log.info(f"Transaction offer '{offer.name}' applicable, items: {offer['items']}")
            return True
        return False

    def _check_qty_amount_conditions(self, offer, qty, amount):
        log.info(f"Checking qty/amount conditions: qty={qty}, amount={amount}")

        conditions = []
        results = []
        min_qty = offer.get("min_qty")
        max_qty = offer.get("max_qty")
        min_amt = offer.get("min_amt")
        max_amt = offer.get("max_amt")

        if min_qty is not None:
            result = qty >= min_qty
            conditions.append(result)
            results.append(f"min_qty: {qty} >= {min_qty} -> {result}")
            log.info(f"  {results[-1]}")

        if max_qty is not None and max_qty > 0:
            result = qty <= max_qty
            conditions.append(result)
            results.append(f"max_qty: {qty} <= {max_qty} -> {result}")
            log.info(f"  {results[-1]}")

        if min_amt is not None and min_amt > 0:
            result = amount >= min_amt
            conditions.append(result)
            results.append(f"min_amt: {amount} >= {min_amt} -> {result}")
            log.info(f"  {results[-1]}")

        if max_amt is not None and max_amt > 0:
            result = amount <= max_amt
            conditions.append(result)
            results.append(f"max_amt: {amount} <= {max_amt} -> {result}")
            log.info(f"  {results[-1]}")

        final_result = all(conditions) if conditions else True
        log.info(f"  Final condition result: {final_result} (all conditions must be True)")

        return final_result

    def _apply_offers(self):
        # A real implementation should handle offer priorities, stacking rules, etc.
        # This simplified version applies the first applicable offer of each type.
        log.info(f"Starting to apply {len(self.applicable_offers)} offers...")
        applied_grand_total = False
        for offer in self.applicable_offers:
            offer_type = offer.get("offer")
            log.info(f"Attempting to apply offer '{offer.name}' of type '{offer_type}'.")
            log.info(f"Offer details: items={offer.get('items', [])}, discount_type={offer.get('discount_type')}")

            if offer_type == "Item Price":
                log.info(f"Applying Item Price offer '{offer.name}'")
                self._apply_item_price_offer(offer)

            elif offer_type == "Give Product":
                log.info(f"Applying Give Product offer '{offer.name}'")
                self._apply_give_product_offer(offer)

            elif offer_type == "Quantity Discount Per Item":
                log.info(f"Applying Quantity Discount Per Item offer '{offer.name}'")
                self._apply_quantity_discount_per_item_offer(offer)

            elif offer_type == "Grand Total" and not applied_grand_total:
                log.info(f"Applying Grand Total offer '{offer.name}'")
                self._apply_grand_total_offer(offer)
                applied_grand_total = True # Prevent multiple grand total offers
            else:
                log.warning(f"Unknown or already applied offer type '{offer_type}' for '{offer.name}'")
    
    def _apply_block_based_discount(self, offer):
        """Apply block-based discount per item with UOM validation and auto-pack optimization"""
        log.info(f"Executing _apply_block_based_discount for '{offer.name}'")

        # Validate UOM configuration
        uom_ref = offer.get("uom_ref")
        if not uom_ref:
            log.error(f"Offer '{offer.name}' missing uom_ref for block-based discount")
            return

        items_per_block = offer.get("total_items_in_block_qty", 0)
        if items_per_block <= 0:
            log.error(f"Offer '{offer.name}' invalid items_per_block: {items_per_block}")
            return

        discount_per_block = offer.get("total_discount_amount_per_block", 0)
        min_blocks = offer.get("min_block_qty", 1)
        max_blocks = offer.get("max_eligible_block_qty", 0)

        log.info(f"Block config: UOM={uom_ref}, items_per_block={items_per_block}, discount_per_block={discount_per_block}")

        # Check if any items match the required UOM
        has_matching_uom = False
        total_eligible_qty = 0

        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item or item.get("posa_offer_applied"):
                continue

            item_uom = item.get("uom", item.get("stock_uom"))
            item_qty = item.get("qty", 0)

            if item_uom == uom_ref:
                has_matching_uom = True
                total_eligible_qty += item_qty
                log.info(f"✅ Found matching UOM item {item.get('item_code')}: UOM={item_uom}, qty={item_qty}")
            else:
                log.info(f"ℹ️ Item {item.get('item_code')} has different UOM: {item_uom} vs required {uom_ref}")

        # If no items match the required UOM, try pack optimization
        log.info(f"Block discount check: has_matching_uom={has_matching_uom}, total_eligible_qty={total_eligible_qty}, items_per_block={items_per_block}")
        if not has_matching_uom:
            log.info(f"🚀 No items match required UOM {uom_ref}, attempting pack optimization for offer '{offer.name}'")
            try:
                pack_opt_result = self._try_pack_optimization_for_offer(offer)
                log.info(f"Pack optimization result: {pack_opt_result}")
                if pack_opt_result:
                    # Re-run the discount application after pack optimization
                    log.info(f"🔄 Re-applying block discount after pack optimization for '{offer.name}'")
                    return self._apply_block_based_discount(offer)
                else:
                    log.info(f"❌ Pack optimization failed or not beneficial for offer '{offer.name}'")
            except Exception as e:
                log.error(f"❌ Error during pack optimization for offer '{offer.name}': {e}")
                log.error({"title": "Pack Optimization Error", "traceback": frappe.get_traceback()})

        # Apply discount per item - check UOM for each item individually
        applied_items = []

        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item or item.get("posa_offer_applied"):
                continue

            # Validate UOM for this specific item
            item_uom = item.get("uom", item.get("stock_uom"))
            item_qty = item.get("qty", 0)

            log.info(f"Checking item {item.get('item_code')}: UOM={item_uom}, qty={item_qty}")

            if item_uom != uom_ref:
                log.info(f"❌ Item {item.get('item_code')} UOM {item_uom} != block UOM {uom_ref} - skipping")
                continue

            # Calculate blocks for this item - special logic for block UOM
            if item_uom == uom_ref:
                # Item qty directly represents number of blocks
                # e.g., UOM=THÙNG-24, qty=1 means 1 block (24 items)
                item_blocks = item_qty
                log.info(f"✅ Item UOM matches block UOM - qty {item_qty} = {item_qty} blocks")
            else:
                # For other UOMs, calculate blocks based on conversion
                item_blocks = item_qty // items_per_block
                log.info(f"ℹ️ Item UOM different from block UOM - calculated {item_blocks} blocks from qty {item_qty}")

            # Tính số block theo thực tế
            eligible_blocks = min(item_blocks, max_blocks) if max_blocks > 0 else item_blocks

            # Nếu không đủ min_blocks thì bỏ qua
            if eligible_blocks < min_blocks:
                log.info(f"❌ Item {item.get('item_code')} only {eligible_blocks} blocks < min_blocks {min_blocks}")
                continue

            # Apply discount to this item
            item_discount = eligible_blocks * discount_per_block
            original_rate = item.get("price_list_rate", 0)
            item_amount = original_rate * item_qty

            # Calculate new rate after discount
            if item_qty > 0:
                discount_per_unit = item_discount / item_qty
                new_rate = original_rate - discount_per_unit
            else:
                new_rate = original_rate

            item["posa_offer_applied"] = 1
            item["discount_amount"] = item_discount
            item["discount_percentage"] = (item_discount / item_amount * 100) if item_amount else 0
            item["rate"] = new_rate
            item["amount"] = new_rate * item_qty

            self._add_offer_to_item_log(item, offer)
            applied_items.append(item)

            log.info(f"✅ Applied block discount to {item.get('item_code')}: blocks={eligible_blocks}, discount={item_discount}, new_rate={new_rate}")

        if applied_items:
            self.applied_offers.append(offer)
            log.info(f"Successfully applied block-based discount to {len(applied_items)} items: '{offer.name}'")
        else:
            log.info(f"No items qualified for block discount in offer '{offer.name}'")

    def _try_pack_optimization_for_offer(self, offer):
        """Try to optimize packs for block-based offers when UOM doesn't match"""
        log.info(f"🚀 Attempting pack optimization for offer '{offer.name}'")

        uom_ref = offer.get("uom_ref")
        items_per_block = offer.get("total_items_in_block_qty", 0)

        log.info(f"Offer config: uom_ref={uom_ref}, items_per_block={items_per_block}")

        if not uom_ref or items_per_block <= 0:
            log.error(f"Invalid offer configuration for pack optimization: uom_ref={uom_ref}, items_per_block={items_per_block}")
            return False

        # Find items that could be optimized
        optimizable_items = []
        total_qty = 0

        log.info(f"Checking {len(offer.get('items', []))} items for optimization")
        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item or item.get("posa_offer_applied"):
                log.info(f"Skipping item {item_row_id}: not found or already applied")
                continue

            item_uom = item.get("uom", item.get("stock_uom"))
            item_qty = item.get("qty", 0)

            log.info(f"Item {item.get('item_code')}: uom={item_uom}, stock_uom={item.get('stock_uom')}, qty={item_qty}")

            # Only consider items with stock UOM (individual units)
            if item_uom == item.get("stock_uom"):
                optimizable_items.append(item)
                total_qty += item_qty
                log.info(f"📦 Found optimizable item {item.get('item_code')}: qty={item_qty}, uom={item_uom}")
            else:
                log.info(f"❌ Item {item.get('item_code')} has different UOM: {item_uom} vs {item.get('stock_uom')}")

        log.info(f"Total optimizable items: {len(optimizable_items)}, total_qty: {total_qty}, required: {items_per_block}")

        if not optimizable_items:
            log.info(f"❌ No optimizable items found")
            return False

        if total_qty < items_per_block:
            log.info(f"❌ Not enough quantity for pack optimization: total_qty={total_qty}, required={items_per_block}")
            return False

        # Get available packs for this item
        item_code = optimizable_items[0].get("item_code")  # Assume all items are the same
        log.info(f"Getting available packs for item: {item_code}")
        available_packs = self._get_available_packs_for_item(item_code)

        if not available_packs:
            log.info(f"❌ No packs available for item {item_code}")
            return False

        # Find optimal pack combination
        log.info(f"Finding optimal combination for qty: {total_qty}")
        optimal_combo = self._find_optimal_pack_combination(total_qty, available_packs, uom_ref)

        if not optimal_combo:
            log.info(f"❌ No optimal combo found")
            return False

        current_total_cost = optimal_combo.get("total", 0)
        base_price = optimizable_items[0].get("price_list_rate", 0)
        regular_cost = total_qty * base_price

        log.info(f"Cost comparison: optimal={current_total_cost}, regular={regular_cost}")

        # Calculate discount benefit of pack optimization
        discount_benefit = self._calculate_pack_optimization_discount_benefit(
            optimal_combo, offer, available_packs, total_qty
        )

        # For pack optimization to be beneficial, it should:
        # 1. Be cheaper than regular cost, OR
        # 2. Enable block discounts that provide net benefit, OR
        # 3. Enable required UOM for block discounts
        is_cost_beneficial = current_total_cost < regular_cost
        is_discount_beneficial = discount_benefit > 0

        # Check if the optimal combo includes the required UOM for the offer
        has_required_uom = optimal_combo.get(str(int(items_per_block))) and optimal_combo.get(str(int(items_per_block))) > 0

        # Special case: If all packs have same unit price, optimization is still beneficial
        # if it enables larger pack sizes for potential discounts
        all_same_unit_price = self._check_all_packs_same_unit_price(available_packs, base_price)

        if not is_cost_beneficial and not is_discount_beneficial and not has_required_uom and not all_same_unit_price:
            log.info(f"❌ Pack optimization not beneficial: cost={current_total_cost}>={regular_cost}, discount_benefit={discount_benefit}, no required UOM")
            return False

        if is_discount_beneficial:
            log.info(f"✅ Pack optimization provides discount benefit: {discount_benefit}")
        elif has_required_uom:
            log.info(f"✅ Pack optimization enables required UOM {uom_ref} for block discount")
        elif is_cost_beneficial:
            log.info(f"✅ Pack optimization is cost beneficial: {current_total_cost} < {regular_cost}")
        elif all_same_unit_price:
            log.info(f"✅ Pack optimization beneficial for same unit price scenario - enables larger pack sizes")

        # Apply pack optimization by splitting items
        log.info(f"✅ Applying pack optimization: {optimal_combo}")
        self._apply_pack_optimization_to_items(optimizable_items, optimal_combo, available_packs)

        return True

    def _check_all_packs_same_unit_price(self, available_packs, base_price):
        """Check if all packs have the same unit price (calculated from stock_uom * conversion_factor)"""
        if not available_packs or len(available_packs) <= 1:
            return False

        for pack in available_packs:
            expected_price = base_price * pack["size"]
            if abs(pack["price"] - expected_price) > 0.01:  # Allow small floating point differences
                return False

        log.info(f"All packs have same unit price {base_price} - optimization beneficial for enabling larger pack sizes")
        return True

    def _calculate_pack_optimization_discount_benefit(self, optimal_combo, offer, available_packs, total_qty):
        """Calculate the discount benefit of pack optimization for block-based offers"""
        try:
            uom_ref = offer.get("uom_ref")
            items_per_block = offer.get("total_items_in_block_qty", 0)
            discount_per_block = offer.get("total_discount_amount_per_block", 0)

            if not uom_ref or items_per_block <= 0 or discount_per_block <= 0:
                return 0

            # Count how many blocks of the required UOM we get from optimal combo
            required_pack = next((p for p in available_packs if p["uom"] == uom_ref), None)
            if not required_pack:
                return 0

            blocks_from_combo = optimal_combo.get(str(required_pack["size"]), 0)
            discount_benefit = blocks_from_combo * discount_per_block

            log.info(f"Pack optimization discount benefit: {blocks_from_combo} blocks × {discount_per_block} = {discount_benefit}")
            return discount_benefit

        except Exception as e:
            log.error(f"Error calculating pack optimization discount benefit: {e}")
            return 0

    def _get_available_packs_for_item(self, item_code):
        """Get available pack options for an item from UOM conversions"""
        try:
            # Get UOM conversions for this item
            uom_conversions = frappe.get_all(
                "UOM Conversion Detail",
                filters={"parent": item_code},
                fields=["uom", "conversion_factor"]
            )

            # Get base price from item (this is the price per stock UOM unit)
            item_doc = frappe.get_doc("Item", item_code)
            stock_uom = item_doc.stock_uom

            # Get base price from Item Price doctype for stock UOM
            base_price = frappe.db.get_value(
                "Item Price",
                {
                    "item_code": item_code,
                    "price_list": self.pos_profile.selling_price_list,
                    "uom": stock_uom,
                    "selling": 1
                },
                "price_list_rate"
            ) or 0

            packs = [{
                "size": 1,
                "uom": stock_uom,
                "price": base_price
            }]

            # Add other UOMs as packs - price is for the entire pack
            for uom_conv in uom_conversions:
                if uom_conv.conversion_factor > 1:  # Only consider pack UOMs
                    pack_size = int(uom_conv.conversion_factor)
                    # For packs, we need to get the price for the entire pack UOM
                    pack_price = frappe.db.get_value(
                        "Item Price",
                        {
                            "item_code": item_code,
                            "price_list": self.pos_profile.selling_price_list,
                            "uom": uom_conv.uom,
                            "selling": 1
                        },
                        "price_list_rate"
                    )

                    # If no specific pack price, calculate from base price
                    if not pack_price:
                        pack_price = base_price * pack_size

                    packs.append({
                        "size": pack_size,
                        "uom": uom_conv.uom,
                        "price": pack_price
                    })

            # Sort by size ascending for DP algorithm
            packs.sort(key=lambda x: x["size"])
            log.info(f"Available packs for {item_code}: {packs}")
            return packs

        except Exception as e:
            log.error(f"Error getting available packs for {item_code}: {e}")
            return []

    def _find_optimal_pack_combination(self, total_qty, packs, required_uom=None):
        """DP algorithm to find optimal pack combination, prioritizing required UOM when costs are equal"""
        if not packs or len(packs) == 0:
            return {"1": total_qty, "total": total_qty * packs[0]["price"] if packs else 0}

        # Initialize DP
        dp = [float('inf')] * (total_qty + 1)
        choices = [None] * (total_qty + 1)
        dp[0] = 0

        # Fill DP table
        for qty in range(1, total_qty + 1):
            for pack in packs:
                if qty >= pack["size"] and dp[qty - pack["size"]] + pack["price"] < dp[qty]:
                    dp[qty] = dp[qty - pack["size"]] + pack["price"]
                    choices[qty] = {"pack": pack, "prev": qty - pack["size"]}
                elif qty >= pack["size"] and dp[qty - pack["size"]] + pack["price"] == dp[qty]:
                    # Same cost - prefer required UOM if specified
                    if required_uom and pack["uom"] == required_uom:
                        dp[qty] = dp[qty - pack["size"]] + pack["price"]
                        choices[qty] = {"pack": pack, "prev": qty - pack["size"]}
                        log.info(f"Preferred required UOM {required_uom} for qty {qty}")

        # Reconstruct optimal combination
        result = {"total": dp[total_qty]}
        current = total_qty

        while current > 0 and choices[current]:
            choice = choices[current]
            pack_size = choice["pack"]["size"]
            result[str(pack_size)] = result.get(str(pack_size), 0) + 1
            current = choice["prev"]

        # Handle remainder
        if current > 0:
            # Prefer required UOM for remainder if possible
            remainder_pack = None
            if required_uom:
                remainder_pack = next((p for p in packs if p["uom"] == required_uom and p["size"] <= current), None)

            if not remainder_pack:
                remainder_pack = min(packs, key=lambda x: x["size"])

            result[str(remainder_pack["size"])] = result.get(str(remainder_pack["size"]), 0) + current // remainder_pack["size"]

        log.info(f"Optimal pack combination for qty {total_qty} (required_uom: {required_uom}): {result}")
        return result

    def _apply_pack_optimization_to_items(self, items, optimal_combo, available_packs):
        """Apply pack optimization by replacing items with optimal pack combination"""
        log.info(f"Applying pack optimization to {len(items)} items")

        # Remove original items
        original_item_codes = {item["posa_row_id"] for item in items}
        self.items = [item for item in self.items if item["posa_row_id"] not in original_item_codes]

        # Create new items based on optimal combo
        base_item = items[0].copy()  # Use first item as template

        # Lấy base_price (giá/đơn vị stock_uom) để set base_price_list_rate
        base_pack_1 = next((p for p in available_packs if p["size"] == 1), None)
        base_unit_price = 0
        if base_pack_1:
            base_unit_price = base_pack_1["price"]  # giá theo stock_uom (1 đơn vị)
        else:
            base_unit_price = base_item.get("base_price_list_rate") or base_item.get("price_list_rate", 0)

        for pack_size_str, qty in optimal_combo.items():
            if pack_size_str == "total" or qty <= 0:
                continue

            pack_size = int(pack_size_str)
            pack_info = next((p for p in available_packs if p["size"] == pack_size), None)

            if pack_info:
                new_item = base_item.copy()
                new_item["posa_row_id"] = f"PACK-{frappe.generate_hash(length=8)}"
                new_item["qty"] = qty
                new_item["uom"] = pack_info["uom"]
                new_item["conversion_factor"] = pack_size

                if pack_size == 1:
                    # Single units - use base price
                    new_item["rate"] = base_item.get("price_list_rate", 0)
                    new_item["price_list_rate"] = new_item["rate"]
                else:
                    # PACK UOM: rate = GIÁ/PACK (không chia pack_size)
                    new_item["rate"] = pack_info["price"]  # ví dụ: 720/thùng, 180/lốc
                    new_item["price_list_rate"] = new_item["rate"]

                # amount theo UOM của dòng: rate * số pack
                new_item["amount"] = new_item["rate"] * qty

                # tồn kho tính theo stock_uom
                new_item["stock_qty"] = qty * pack_size

                # Set base_price_list_rate cho mọi dòng mới (kể cả pack)
                new_item["base_price_list_rate"] = base_unit_price  # giá/stock_uom để reset chuẩn

                # Reset offer flags for new items
                new_item["posa_offer_applied"] = 0
                new_item["discount_amount"] = 0
                new_item["discount_percentage"] = 0
                new_item["applied_offers"] = []

                self.items.append(new_item)
                log.info(f"Created optimized pack: {pack_size} x {qty} packs, uom={pack_info['uom']}, rate={new_item['rate']}, amount={new_item['amount']}, stock_qty={new_item['stock_qty']}")

        log.info(f"Pack optimization completed: {len(self.items)} items after optimization")

    def _apply_block_based_gift_offer(self, offer):
        """Apply block-based gift offer with bonus gifts"""
        log.info(f"Executing _apply_block_based_gift_offer for '{offer.name}'")
        
        # Validate configuration
        uom_ref = offer.get("uom_ref")
        items_per_block = offer.get("total_items_in_block_qty", 0)
        gift_per_block = offer.get("gift_per_block_qty", 0)
        gift_item_code = offer.get("gift_item_code")
        min_blocks = offer.get("min_block_qty", 1)
        max_blocks = offer.get("max_eligible_block_qty", 0)
        
        if not all([uom_ref, items_per_block > 0, gift_per_block > 0, gift_item_code]):
            log.error(f"Invalid block gift config for offer '{offer.name}'")
            return
            
        # Check if gift item already in cart
        if any(i.get("item_code") == gift_item_code and i.get("posa_is_offer") for i in self.items):
            log.info(f"Gift item '{gift_item_code}' already in cart for offer '{offer.name}'")
            return
            
        # Calculate eligible blocks
        total_eligible_qty = 0
        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if item and not item.get("posa_offer_applied"):
                item_uom = item.get("uom", item.get("stock_uom"))
                if item_uom == uom_ref:
                    total_eligible_qty += item.get("qty", 0)

        total_blocks = total_eligible_qty // items_per_block
        eligible_blocks = min(total_blocks, max_blocks) if max_blocks > 0 else total_blocks

        if eligible_blocks < min_blocks:
            log.info(f"Insufficient blocks for gift: {eligible_blocks} < {min_blocks}")
            return
            
        # Calculate total gifts
        total_gifts = eligible_blocks * gift_per_block
        
        # Parse bonus gifts JSON if available
        bonus_gifts_json = offer.get("bonus_gift_per_block")
        if bonus_gifts_json:
            try:
                bonus_config = json.loads(bonus_gifts_json)
                # Add bonus logic here based on your JSON structure
                log.info(f"Bonus gifts config: {bonus_config}")
            except json.JSONDecodeError:
                log.error(f"Invalid bonus gifts JSON for offer '{offer.name}'")
        
        log.info(f"Gift calculation: blocks={eligible_blocks}, gifts_per_block={gift_per_block}, total_gifts={total_gifts}")
        
        # Add gift items
        try:
            gift_item_doc = frappe.get_doc("Item", gift_item_code)
            gift_item = {
                "item_code": gift_item_code,
                "item_name": gift_item_doc.item_name,
                "qty": total_gifts,
                "rate": 0,
                "price_list_rate": 0,
                "amount": 0,
                "discount_amount": 0,
                "discount_percentage": 100,
                "posa_is_offer": 1,
                "is_free_item": 1,
                "posa_row_id": f"GIFT-{frappe.generate_hash(length=8)}",
            }
            self._add_offer_to_item_log(gift_item, offer)
            self.items.append(gift_item)
            self.applied_offers.append(offer)
            log.info(f"Successfully applied block-based gift: '{offer.name}', added {total_gifts} x '{gift_item_code}'")
            
        except Exception as e:
            log.error(f"Failed to add gift item for offer '{offer.name}': {e}")

    def _apply_tiered_pricing(self, offer):
        """Apply tiered pricing based on JSON configuration"""
        log.info(f"Executing _apply_tiered_pricing for '{offer.name}'")
        
        tiered_json = offer.get("tiered_pricing_json")
        if not tiered_json:
            log.error(f"Offer '{offer.name}' missing tiered_pricing_json")
            return
            
        try:
            tiered_config = json.loads(tiered_json)
            log.info(f"Parsed tiered config: {tiered_config}")
        except json.JSONDecodeError as e:
            log.error(f"Invalid tiered pricing JSON for offer '{offer.name}': {e}")
            return
            
        # Apply tiered pricing to eligible items
        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item or item.get("posa_offer_applied"):
                continue
                
            qty = item.get("qty", 0)
            original_rate = item.get("price_list_rate", 0)
            
            # Find applicable tier based on quantity
            applicable_tier = None
            for tier in tiered_config.get("tiers", []):
                min_qty = tier.get("min_qty", 0)
                max_qty = tier.get("max_qty", float('inf'))
                if min_qty <= qty <= max_qty:
                    applicable_tier = tier
                    break
            
            if not applicable_tier:
                log.info(f"No applicable tier for item {item.get('item_code')} qty {qty}")
                continue
                
            # Apply tier pricing
            tier_type = applicable_tier.get("type", "fixed_rate")
            tier_value = applicable_tier.get("value", 0)
            
            if tier_type == "fixed_rate":
                new_rate = tier_value
            elif tier_type == "discount_percentage":
                new_rate = original_rate * (1 - tier_value / 100)
            elif tier_type == "discount_amount":
                new_rate = original_rate - tier_value
            else:
                log.warning(f"Unknown tier type: {tier_type}")
                continue
                
            discount_amount = original_rate - new_rate
            
            item["posa_offer_applied"] = 1
            item["rate"] = new_rate
            item["discount_amount"] = discount_amount
            item["discount_percentage"] = (discount_amount / original_rate * 100) if original_rate else 0
            item["amount"] = new_rate * qty
            
            self._add_offer_to_item_log(item, offer)
            log.info(f"Applied tiered pricing to {item.get('item_code')}: tier={tier_type}, new_rate={new_rate}")
        
        self.applied_offers.append(offer)
        log.info(f"Successfully applied tiered pricing: '{offer.name}'")

    # --- Nghiệp vụ giảm giá theo sản phẩm ---
    def _apply_item_price_offer(self, offer):
        log.debug(f"Executing _apply_item_price_offer for '{offer.name}'.")
        
        # Check time-based restrictions first
        if not self.is_offer_active_in_time_slots(offer):
            log.info(f"Offer '{offer.name}' not active in current time slot")
            return
            
        # Route to appropriate method based on offer configuration
        if offer.get("is_used_block"):
            log.info(f"Routing to block-based discount for '{offer.name}'")
            self._apply_block_based_discount(offer)
        elif offer.get("is_used_tiered_pricing"):
            log.info(f"Routing to tiered pricing for '{offer.name}'")
            self._apply_tiered_pricing(offer)
        else:
            # Original logic for regular item price offers
            for item_row_id in offer.get("items", []):
                item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
                if not item or item.get("posa_offer_applied"):
                    continue

                original_qty = offer.get("original_qty", item.get("qty", 0))
                max_qty = offer.get("max_qty", 0)
                actual_qty = item.get("qty", 0)

                log.info(f"Applying discount for item {item.get('item_code')}: original_qty={original_qty}, max_qty={max_qty}, actual_qty={actual_qty}")

                # Handle max_qty logic: discount applies only to max_qty items, excess pays normal price
                if max_qty and max_qty > 0 and actual_qty > max_qty:
                    # Split calculation: max_qty items at discounted price, excess at normal price
                    discounted_qty = max_qty
                    excess_qty = actual_qty - max_qty

                    log.info(f"Max qty exceeded: discounted_qty={discounted_qty}, excess_qty={excess_qty}")

                    # Calculate rates for discounted and excess portions
                    original_rate = item.get("price_list_rate", 0)
                    discount_type = offer.get("discount_type")

                    if discount_type == "Rate":
                        discounted_rate = offer.get("rate", 0)
                        discount_amount_per_item = original_rate - discounted_rate
                    elif discount_type == "Discount Percentage":
                        discount_percentage = offer.get("discount_percentage", 0)
                        discount_amount_per_item = original_rate * (discount_percentage / 100.0)
                        discounted_rate = original_rate - discount_amount_per_item
                    else:
                        log.warning(f"Unknown discount_type: {discount_type}")
                        continue

                    # Calculate weighted average rate
                    discounted_amount = discounted_qty * discounted_rate
                    excess_amount = excess_qty * original_rate
                    total_amount = discounted_amount + excess_amount
                    weighted_rate = total_amount / actual_qty

                    # Calculate total discount for the discounted portion
                    total_discount_amount = discount_amount_per_item * discounted_qty

                    item["posa_offer_applied"] = 1
                    item["rate"] = weighted_rate
                    item["discount_amount"] = total_discount_amount
                    item["discount_percentage"] = (total_discount_amount / (original_rate * actual_qty) * 100) if (original_rate * actual_qty) else 0
                    item["amount"] = total_amount

                    log.info(f"Applied max_qty logic: weighted_rate={weighted_rate}, total_discount={total_discount_amount}, total_amount={total_amount}")

                else:
                    # Normal discount application for entire quantity
                    item["posa_offer_applied"] = 1
                    original_rate = item.get("price_list_rate", 0)
                    new_rate = original_rate
                    discount_type = offer.get("discount_type")

                    if discount_type == "Rate":
                        new_rate = offer.get("rate", 0)
                        item["discount_amount"] = original_rate - new_rate
                        item["discount_percentage"] = (item["discount_amount"] / original_rate * 100) if original_rate else 0

                    elif discount_type == "Discount Percentage":
                        discount_percentage = offer.get("discount_percentage", 0)
                        discount_amount = original_rate * (discount_percentage / 100.0)
                        new_rate = original_rate - discount_amount
                        item["discount_amount"] = discount_amount
                        item["discount_percentage"] = discount_percentage

                    item["rate"] = new_rate
                    item["amount"] = new_rate * item.get("qty", 0)

                    log.info(f"Applied normal discount: rate={new_rate}, discount_amount={item['discount_amount']}")

                self._add_offer_to_item_log(item, offer)
            
            self.applied_offers.append(offer)
            log.info(f"Successfully applied regular 'Item Price' offer: '{offer.name}'.")

    # --- Nghiệp vụ tặng sản phẩm ---
    def _apply_give_product_offer(self, offer):
        log.debug(f"Executing _apply_give_product_offer for '{offer.name}'.")
        
        # Check time-based restrictions
        if not self.is_offer_active_in_time_slots(offer):
            log.info(f"Gift offer '{offer.name}' not active in current time slot")
            return
            
        # Route to block-based gift if configured
        if offer.get("is_used_gift_block"):
            log.info(f"Routing to block-based gift for '{offer.name}'")
            self._apply_block_based_gift_offer(offer)
            return
            
        # Original gift logic
        given_item_code = offer.get("apply_item_code") or offer.get("give_item")
        if not given_item_code:
            log.warning(f"Offer '{offer.name}' is 'Give Product' but has no item to give.")
            return

        # Check if gifted item is already in cart
        if any(i.get("item_code") == given_item_code and i.get("posa_is_offer") for i in self.items):
            log.info(f"Gift item '{given_item_code}' already in cart for offer '{offer.name}'. Skipping.")
            return

        item_doc = frappe.get_doc("Item", given_item_code)
        new_item = {
            "item_code": given_item_code,
            "item_name": item_doc.item_name,
            "qty": offer.get("given_qty", 1),
            "rate": 0,
            "price_list_rate": 0,
            "amount": 0,
            "discount_amount": 0,
            "discount_percentage": 100,
            "posa_is_offer": 1,
            "is_free_item": 1,
            "posa_row_id": f"GIFT-{frappe.generate_hash(length=8)}",
        }
        self._add_offer_to_item_log(new_item, offer)
        self.items.append(new_item)
        self.applied_offers.append(offer)
        log.info(f"Successfully applied regular 'Give Product' offer: '{offer.name}', added item '{given_item_code}'.")

    # --- Nghiệp vụ giảm giá theo số lượng mỗi sản phẩm ---
    def _apply_quantity_discount_per_item_offer(self, offer):
        log.info(f"Executing _apply_quantity_discount_per_item_offer for '{offer.name}'.")
        qty_discount_per_item = offer.get("qty_discount_per_item", 0)
        log.info(f"qty_discount_per_item = {qty_discount_per_item}")

        if qty_discount_per_item <= 0:
            log.warning(f"Offer '{offer.name}' has invalid qty_discount_per_item: {qty_discount_per_item}")
            return

        log.info(f"Processing {len(offer.get('items', []))} items for offer '{offer.name}'")
        for item_row_id in offer.get("items", []):
            log.info(f"Processing item_row_id: {item_row_id}")
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item:
                log.warning(f"Item with row_id {item_row_id} not found")
                continue
            if item.get("posa_offer_applied"):
                log.info(f"Item {item.get('item_code')} already has offer applied, skipping")
                continue

            item["posa_offer_applied"] = 1
            qty = item.get("qty", 0)
            original_rate = item.get("price_list_rate", 0)

            log.info(f"Item {item.get('item_code')}: qty={qty}, original_rate={original_rate}")

            # Calculate discount: qty_discount_per_item * quantity
            discount_amount = qty_discount_per_item * qty
            new_rate = original_rate - qty_discount_per_item  # Rate sau khi trừ discount per item

            log.info(f"Calculated: discount_amount={discount_amount}, new_rate={new_rate}")

            # Ensure discount doesn't exceed original price
            if discount_amount > original_rate * qty:
                log.warning(f"Discount amount {discount_amount} exceeds total price {original_rate * qty}, capping discount")
                discount_amount = original_rate * qty
                new_rate = 0

            item["discount_amount"] = discount_amount
            item["discount_percentage"] = (discount_amount / (original_rate * qty) * 100) if (original_rate * qty) else 0
            item["rate"] = new_rate
            item["amount"] = new_rate * qty

            log.info(f"Applied to item {item.get('item_code')}: discount_amount={discount_amount}, discount_percentage={item['discount_percentage']}, rate={new_rate}, amount={item['amount']}")

            self._add_offer_to_item_log(item, offer)

        self.applied_offers.append(offer)
        log.info(f"Successfully applied 'Quantity Discount Per Item' offer: '{offer.name}'.")

    # --- Nghiệp vụ giảm giá trên tổng hóa đơn ---
    def _apply_grand_total_offer(self, offer):
        log.debug(f"Executing _apply_grand_total_offer for '{offer.name}'.")
        # This will be a separate field in the totals, not affecting item prices directly.
        self.applied_offers.append(offer)
        log.info(f"Successfully noted 'Grand Total' offer: '{offer.name}'. Will be applied at total calculation.")

    def _add_offer_to_item_log(self, item, offer):
        if "applied_offers" not in item:
            item["applied_offers"] = []
        item["applied_offers"].append(offer.get("name"))

    def _calculate_totals(self):
        net_total = sum(item.get("amount", 0) for item in self.items)
        grand_total = net_total

        # Apply Grand Total offer if present
        for offer in self.applied_offers:
            if offer.get("offer") == "Grand Total":
                discount_type = offer.get("discount_type")
                discount_amount = 0
                if discount_type == "Discount Percentage":
                    discount_percentage = offer.get("discount_percentage", 0)
                    discount_amount = net_total * (discount_percentage / 100.0)
                elif discount_type == "Discount Amount":
                    discount_amount = offer.get("discount_amount", 0)
                
                grand_total -= discount_amount
                log.info(f"Applied Grand Total discount of {discount_amount} from offer '{offer.name}'.")
                break # Apply only one
        
        self.totals["net_total"] = net_total
        self.totals["grand_total"] = grand_total
        log.info(f"Final totals calculated: Net Total = {net_total}, Grand Total = {grand_total}.")
