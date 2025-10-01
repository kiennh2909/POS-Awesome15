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
        log.info(f"Found {len(self.valid_offers)} valid offers for profile '{self.pos_profile_name}'.")

    def _find_applicable_offers(self):
        for offer in self.valid_offers:
            if self._check_offer_conditions(offer):
                self.applicable_offers.append(offer)
        log.info(f"Found {len(self.applicable_offers)} applicable offers based on current cart.")

    def _check_offer_conditions(self, offer):
        if not self._check_coupon(offer):
            return False

        apply_on = offer.get("apply_on")
        
        if apply_on == "Item Code":
            return self._check_item_code_offer(offer)
        elif apply_on == "Item Group":
            return self._check_item_group_offer(offer)
        elif apply_on == "Brand":
            return self._check_brand_offer(offer)
        elif apply_on == "Transaction":
            return self._check_transaction_offer(offer)
            
        return False

    def _check_coupon(self, offer):
        if not offer.get("coupon_based"):
            return True
        is_valid = any(c.get("pos_offer") == offer.get("name") for c in self.coupons)
        if is_valid:
            log.info(f"Coupon valid for offer '{offer.name}'.")
        return is_valid

    def _check_item_code_offer(self, offer):
        for item in self.items:
            if item.get("item_code") == offer.get("item") and not item.get("posa_is_offer"):
                if self._check_qty_amount_conditions(offer, item.get("qty", 0), item.get("qty", 0) * item.get("price_list_rate", 0)):
                    offer["items"] = [item.get("posa_row_id")]
                    return True
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
        
        if self._check_qty_amount_conditions(offer, total_qty, total_amount):
            offer["items"] = [item.get("posa_row_id") for item in self.items]
            return True
        return False

    def _check_qty_amount_conditions(self, offer, qty, amount):
        conditions = []
        min_qty = offer.get("min_qty")
        max_qty = offer.get("max_qty")
        min_amt = offer.get("min_amt")
        max_amt = offer.get("max_amt")

        if min_qty is not None: conditions.append(qty >= min_qty)
        if max_qty is not None and max_qty > 0: conditions.append(qty <= max_qty)
        if min_amt is not None and min_amt > 0: conditions.append(amount >= min_amt)
        if max_amt is not None and max_amt > 0: conditions.append(amount <= max_amt)
        
        return all(conditions) if conditions else True

    def _apply_offers(self):
        # A real implementation should handle offer priorities, stacking rules, etc.
        # This simplified version applies the first applicable offer of each type.
        applied_grand_total = False
        for offer in self.applicable_offers:
            offer_type = offer.get("offer")
            log.info(f"Attempting to apply offer '{offer.name}' of type '{offer_type}'.")

            if offer_type == "Item Price":
                self._apply_item_price_offer(offer)
            
            elif offer_type == "Give Product":
                self._apply_give_product_offer(offer)

            elif offer_type == "Grand Total" and not applied_grand_total:
                self._apply_grand_total_offer(offer)
                applied_grand_total = True # Prevent multiple grand total offers
    
    # --- Nghiệp vụ giảm giá theo sản phẩm ---
    def _apply_item_price_offer(self, offer):
        log.debug(f"Executing _apply_item_price_offer for '{offer.name}'.")
        for item_row_id in offer.get("items", []):
            item = next((i for i in self.items if i.get("posa_row_id") == item_row_id), None)
            if not item or item.get("posa_offer_applied"):
                continue

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
            
            self._add_offer_to_item_log(item, offer)
        self.applied_offers.append(offer)
        log.info(f"Successfully applied 'Item Price' offer: '{offer.name}'.")

    # --- Nghiệp vụ tặng sản phẩm ---
    def _apply_give_product_offer(self, offer):
        log.debug(f"Executing _apply_give_product_offer for '{offer.name}'.")
        # This is a simplified logic. A full implementation would need to handle
        # 'replace_cheapest_item', fetching item details for the gifted item, etc.
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
        log.info(f"Successfully applied 'Give Product' offer: '{offer.name}', added item '{given_item_code}'.")

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
