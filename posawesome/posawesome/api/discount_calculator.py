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
        log.info("--- Starting Discount Calculation ---")
        data = json.loads(invoice_data)
        calculator = DiscountCalculator(data)
        result = calculator.process()
        log.info("--- Finished Discount Calculation ---")
        return result

    except Exception as e:
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
                original_rate = item.get("price_list_rate", 0)
                log.info(f"Resetting item {item.get('item_code')}: current_rate={current_rate}, original_rate={original_rate}")

                # Reset to original price list rate
                item["rate"] = original_rate
                item["amount"] = original_rate * item.get("qty", 0)

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
                log.info(f"Item code matches! Checking qty/amount conditions...")

                # For block-based discounts and tiered pricing, skip min_qty and max_qty checks
                # The block/tiered calculation will handle quantity logic
                if offer.get("is_used_block") or offer.get("is_used_tiered_pricing"):
                    log.info(f"✅ Block-based or tiered pricing offer, skipping min_qty/max_qty checks")
                    offer["items"] = [item.get("posa_row_id")]
                    # Store original qty for discount calculation
                    offer["original_qty"] = qty
                    log.info(f"✅ Block-based or tiered Item Code offer applicable, items: {offer['items']}, original_qty: {qty}")
                    return True

                # Special logic for max_qty: offer applies to max_qty items, excess pays normal price
                min_qty = offer.get("min_qty")
                max_qty = offer.get("max_qty")

                # Check minimum quantity requirement
                if min_qty and qty < min_qty:
                    log.info(f"❌ Qty {qty} < min_qty {min_qty}, offer not applicable")
                    continue

                # For max_qty logic: if qty > max_qty, still apply offer to max_qty items
                # The excess quantity will be calculated at normal price
                if max_qty and max_qty > 0:
                    # Offer is applicable as long as qty >= min_qty
                    # The actual discount calculation will handle max_qty limit
                    condition_result = True
                    log.info(f"✅ Qty {qty} >= min_qty {min_qty}, offer applicable (max_qty {max_qty} will limit discount)")
                else:
                    # No max_qty restriction, check normal conditions
                    condition_result = self._check_qty_amount_conditions(offer, qty, amount)

                log.info(f"Qty/amount condition result: {condition_result}")
                if condition_result:
                    offer["items"] = [item.get("posa_row_id")]
                    # Store original qty for discount calculation
                    offer["original_qty"] = qty
                    log.info(f"✅ Item Code offer applicable, items: {offer['items']}, original_qty: {qty}")
                    return True
            else:
                log.info(f"❌ Item code does not match or is offer item")
        log.info(f"❌ No matching items found for Item Code offer")
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
        """Apply block-based discount with UOM validation"""
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
        
        # Calculate total eligible items for this offer
        eligible_items = []
        total_eligible_qty = 0
        
        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item or item.get("posa_offer_applied"):
                continue
                
            # Validate UOM conversion (simplified - you may need more complex logic)
            item_uom = item.get("uom", item.get("stock_uom"))
            if item_uom != uom_ref:
                log.warning(f"Item {item.get('item_code')} UOM {item_uom} != block UOM {uom_ref}")
                continue
                
            eligible_items.append(item)
            total_eligible_qty += item.get("qty", 0)
        
        if not eligible_items:
            log.info(f"No eligible items for block discount in offer '{offer.name}'")
            return
            
        # Calculate blocks
        total_blocks = total_eligible_qty // items_per_block
        eligible_blocks = min(total_blocks, max_blocks) if max_blocks > 0 else total_blocks
        eligible_blocks = max(eligible_blocks, min_blocks)
        
        if eligible_blocks < min_blocks:
            log.info(f"Insufficient blocks: {eligible_blocks} < {min_blocks} for offer '{offer.name}'")
            return
            
        total_discount = eligible_blocks * discount_per_block
        
        log.info(f"Calculated: total_qty={total_eligible_qty}, blocks={eligible_blocks}, total_discount={total_discount}")
        
        # Distribute discount proportionally
        total_eligible_amount = sum(item.get("price_list_rate", 0) * item.get("qty", 0) for item in eligible_items)
        
        for item in eligible_items:
            if total_eligible_amount == 0:
                continue
                
            item_amount = item.get("price_list_rate", 0) * item.get("qty", 0)
            item_discount = (item_amount / total_eligible_amount) * total_discount
            
            item["posa_offer_applied"] = 1
            item["discount_amount"] = item_discount
            item["discount_percentage"] = (item_discount / item_amount * 100) if item_amount else 0
            item["rate"] = item.get("price_list_rate", 0) - (item_discount / item.get("qty", 1))
            item["amount"] = item["rate"] * item.get("qty", 1)
            
            self._add_offer_to_item_log(item, offer)
            log.info(f"Applied block discount to {item.get('item_code')}: discount={item_discount}")
        
        self.applied_offers.append(offer)
        log.info(f"Successfully applied block-based discount: '{offer.name}'")

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
        eligible_blocks = max(eligible_blocks, min_blocks)
        
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
