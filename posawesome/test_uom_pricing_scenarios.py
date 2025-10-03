#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test scenarios for UOM pricing implementation
Tests the 8 QA scenarios from the checklist
"""

import frappe
import json
from posawesome.posawesome.api.discount_calculator import DiscountCalculator

def test_scenario_1_stock_uom_no_offer():
    """
    Case 1: Mua theo Stock UOM (lon) – không offer ⇒ giá = base, không discount.
    """
    print("🧪 Testing Scenario 1: Stock UOM, no offer")

    # Mock invoice data
    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 10,
                "uom": "LON",  # Stock UOM
                "stock_uom": "LON",
                "conversion_factor": 1,
                "base_price_list_rate": 30000,  # 30,000 VND per LON
                "price_list_rate": 30000,
                "rate": 30000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    result = calculator.process()

    item = result["updated_items"][0]

    # Assertions
    assert item["rate"] == 30000, f"Expected rate 30000, got {item['rate']}"
    assert item["discount_amount"] == 0, f"Expected discount 0, got {item['discount_amount']}"
    assert item["posa_offer_applied"] == 0, f"Expected posa_offer_applied 0, got {item['posa_offer_applied']}"

    print("✅ Scenario 1 passed")
    return True

def test_scenario_2_block_discount_thung():
    """
    Case 2: Mua 1 thùng (UOM thùng) – offer giảm theo block ⇒ discount đúng số tiền/block, rate tính đúng.
    """
    print("🧪 Testing Scenario 2: Block discount for Thung")

    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 1,
                "uom": "THUNG-24",  # Block UOM
                "stock_uom": "LON",
                "conversion_factor": 24,
                "base_price_list_rate": 30000,  # 30,000 VND per LON
                "price_list_rate": 720000,  # 24 * 30,000
                "rate": 720000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    # Mock offer data
    calculator = DiscountCalculator(invoice_data)
    # Manually add applicable offer for testing
    calculator.applicable_offers = [
        {
            "name": "TEST_BLOCK_OFFER",
            "offer": "Item Price",
            "is_used_block": 1,
            "uom_ref": "THUNG-24",
            "total_items_in_block_qty": 24,
            "total_discount_amount_per_block": 40000,
            "min_block_qty": 1,
            "max_eligible_block_qty": 10,
            "items": ["ROW_1"],
            "original_qty": 1
        }
    ]

    result = calculator.process()
    item = result["updated_items"][0]

    # Expected: 1 block, discount 40,000, rate = 720,000 - 40,000 = 680,000
    expected_rate = 720000 - 40000
    expected_discount = 40000

    assert item["rate"] == expected_rate, f"Expected rate {expected_rate}, got {item['rate']}"
    assert item["discount_amount"] == expected_discount, f"Expected discount {expected_discount}, got {item['discount_amount']}"
    assert item["posa_offer_applied"] == 1, f"Expected posa_offer_applied 1, got {item['posa_offer_applied']}"

    print("✅ Scenario 2 passed")
    return True

def test_scenario_3_mixed_qty():
    """
    Case 3: 2 thùng + 5 lon lẻ: Thùng ăn block discount; lon lẻ không ăn block.
    """
    print("🧪 Testing Scenario 3: Mixed qty - 2 Thung + 5 Lon")

    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 2,
                "uom": "THUNG-24",
                "stock_uom": "LON",
                "conversion_factor": 24,
                "base_price_list_rate": 30000,
                "price_list_rate": 720000,
                "rate": 720000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            },
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 5,
                "uom": "LON",
                "stock_uom": "LON",
                "conversion_factor": 1,
                "base_price_list_rate": 30000,
                "price_list_rate": 30000,
                "rate": 30000,
                "posa_row_id": "ROW_2",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    calculator.applicable_offers = [
        {
            "name": "TEST_BLOCK_OFFER",
            "offer": "Item Price",
            "is_used_block": 1,
            "uom_ref": "THUNG-24",
            "total_items_in_block_qty": 24,
            "total_discount_amount_per_block": 40000,
            "min_block_qty": 1,
            "max_eligible_block_qty": 10,
            "items": ["ROW_1"],
            "original_qty": 2
        }
    ]

    result = calculator.process()

    # Find items
    thung_item = next(i for i in result["updated_items"] if i["posa_row_id"] == "ROW_1")
    lon_item = next(i for i in result["updated_items"] if i["posa_row_id"] == "ROW_2")

    # Thung: 2 blocks, discount 80,000, rate = 720,000 - 80,000 = 640,000
    expected_thung_rate = 720000 - 80000
    expected_thung_discount = 80000

    assert thung_item["rate"] == expected_thung_rate, f"Thung expected rate {expected_thung_rate}, got {thung_item['rate']}"
    assert thung_item["discount_amount"] == expected_thung_discount, f"Thung expected discount {expected_thung_discount}, got {thung_item['discount_amount']}"

    # Lon: No discount
    assert lon_item["rate"] == 30000, f"Lon expected rate 30000, got {lon_item['rate']}"
    assert lon_item["discount_amount"] == 0, f"Lon expected discount 0, got {lon_item['discount_amount']}"

    print("✅ Scenario 3 passed")
    return True

def test_scenario_4_max_block_limit():
    """
    Case 4: Vượt max block (VD max 3 thùng, mua 5): 3 thùng ăn discount, 2 thùng tính base convert.
    """
    print("🧪 Testing Scenario 4: Max block limit")

    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 5,
                "uom": "THUNG-24",
                "stock_uom": "LON",
                "conversion_factor": 24,
                "base_price_list_rate": 30000,
                "price_list_rate": 720000,
                "rate": 720000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    calculator.applicable_offers = [
        {
            "name": "TEST_BLOCK_OFFER",
            "offer": "Item Price",
            "is_used_block": 1,
            "uom_ref": "THUNG-24",
            "total_items_in_block_qty": 24,
            "total_discount_amount_per_block": 40000,
            "min_block_qty": 1,
            "max_eligible_block_qty": 3,  # Max 3 blocks
            "items": ["ROW_1"],
            "original_qty": 5
        }
    ]

    result = calculator.process()
    item = result["updated_items"][0]

    # 3 blocks discounted (120,000 discount), 2 blocks at full price
    # Weighted rate = (3 * 680,000 + 2 * 720,000) / 5 = (2,040,000 + 1,440,000) / 5 = 696,000
    expected_rate = (3 * (720000 - 40000) + 2 * 720000) / 5
    expected_discount = 3 * 40000  # Only 3 blocks get discount

    assert abs(item["rate"] - expected_rate) < 1, f"Expected rate ~{expected_rate}, got {item['rate']}"
    assert item["discount_amount"] == expected_discount, f"Expected discount {expected_discount}, got {item['discount_amount']}"

    print("✅ Scenario 4 passed")
    return True

def test_scenario_5_gift_offer():
    """
    Case 5: Gift (VD 1 thùng tặng 2 lon): Quà vào hàng posa_is_offer=1, rate = 0.
    """
    print("🧪 Testing Scenario 5: Gift offer")

    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 1,
                "uom": "THUNG-24",
                "stock_uom": "LON",
                "conversion_factor": 24,
                "base_price_list_rate": 30000,
                "price_list_rate": 720000,
                "rate": 720000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    calculator.applicable_offers = [
        {
            "name": "TEST_GIFT_OFFER",
            "offer": "Give Product",
            "is_used_gift_block": 1,
            "uom_ref": "THUNG-24",
            "total_items_in_block_qty": 24,
            "gift_per_block_qty": 2,
            "gift_item_code": "TEST_GIFT_ITEM",
            "min_block_qty": 1,
            "max_eligible_block_qty": 10,
            "items": ["ROW_1"],
            "original_qty": 1
        }
    ]

    result = calculator.process()

    # Should have 2 items: original + gift
    assert len(result["updated_items"]) == 2, f"Expected 2 items, got {len(result['updated_items'])}"

    gift_item = next((i for i in result["updated_items"] if i.get("posa_is_offer")), None)
    assert gift_item, "Gift item not found"
    assert gift_item["item_code"] == "TEST_GIFT_ITEM", f"Expected gift item TEST_GIFT_ITEM, got {gift_item['item_code']}"
    assert gift_item["qty"] == 2, f"Expected gift qty 2, got {gift_item['qty']}"
    assert gift_item["rate"] == 0, f"Expected gift rate 0, got {gift_item['rate']}"
    assert gift_item["posa_is_offer"] == 1, f"Expected posa_is_offer 1, got {gift_item['posa_is_offer']}"

    print("✅ Scenario 5 passed")
    return True

def test_scenario_6_return():
    """
    Case 6: Return/đổi trả: Qty, rate, discount đảo dấu hợp lý; không "ghi giá" ngược về Price List.
    """
    print("🧪 Testing Scenario 6: Return")

    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "is_return": True,
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": -10,  # Return qty negative
                "uom": "LON",
                "stock_uom": "LON",
                "conversion_factor": 1,
                "base_price_list_rate": 30000,
                "price_list_rate": 30000,
                "rate": 30000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    result = calculator.process()

    item = result["updated_items"][0]

    # For returns, amounts should be negative
    assert item["qty"] == -10, f"Expected qty -10, got {item['qty']}"
    assert item["rate"] == 30000, f"Expected rate 30000, got {item['rate']}"
    assert item["amount"] == -300000, f"Expected amount -300000, got {item['amount']}"  # -10 * 30000

    print("✅ Scenario 6 passed")
    return True

def test_scenario_7_multi_currency():
    """
    Case 7: Multi-currency: convert = chuẩn, discount tính trên post-conversion.
    """
    print("🧪 Testing Scenario 7: Multi-currency")

    # Mock multi-currency scenario
    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "currency": "USD",
        "conversion_rate": 23000,  # 1 USD = 23,000 VND
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 1,
                "uom": "LON",
                "stock_uom": "LON",
                "conversion_factor": 1,
                "base_price_list_rate": 30000,  # Base in VND
                "price_list_rate": 1.30,  # ~30,000 VND in USD
                "rate": 1.30,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    result = calculator.process()

    item = result["updated_items"][0]

    # Should maintain USD pricing
    assert item["rate"] == 1.30, f"Expected rate 1.30 USD, got {item['rate']}"
    assert item["currency"] == "USD", f"Expected currency USD, got {item.get('currency')}"

    print("✅ Scenario 7 passed")
    return True

def test_scenario_8_tax_inclusive():
    """
    Case 8: Tax inclusive: Kiểm tra discount áp trước/ sau thuế theo policy; hoá đơn in khớp.
    """
    print("🧪 Testing Scenario 8: Tax inclusive")

    invoice_data = {
        "customer": "Test Customer",
        "pos_profile": "Test POS Profile",
        "items": [
            {
                "item_code": "TEST_ITEM_1",
                "item_name": "Test Item 1",
                "qty": 10,
                "uom": "LON",
                "stock_uom": "LON",
                "conversion_factor": 1,
                "base_price_list_rate": 30000,
                "price_list_rate": 30000,
                "rate": 30000,
                "posa_row_id": "ROW_1",
                "posa_offer_applied": 0,
                "applied_offers": []
            }
        ],
        "taxes": [
            {
                "account_head": "VAT 10%",
                "charge_type": "On Net Total",
                "rate": 10,
                "included_in_print_rate": 1  # Tax inclusive
            }
        ],
        "coupons": []
    }

    calculator = DiscountCalculator(invoice_data)
    result = calculator.process()

    item = result["updated_items"][0]

    # With tax inclusive, the printed rate should include tax
    # Base rate 30,000, tax 10% = printed rate should be ~27,273 (so 30,000 * 1.1 = 33,000 total)
    # But discount calculation should work correctly
    assert item["rate"] == 30000, f"Expected rate 30000, got {item['rate']}"
    assert item["discount_amount"] == 0, f"Expected discount 0, got {item['discount_amount']}"

    print("✅ Scenario 8 passed")
    return True

def run_all_tests():
    """Run all test scenarios"""
    print("🚀 Starting UOM Pricing Test Scenarios")

    tests = [
        test_scenario_1_stock_uom_no_offer,
        test_scenario_2_block_discount_thung,
        test_scenario_3_mixed_qty,
        test_scenario_4_max_block_limit,
        test_scenario_5_gift_offer,
        test_scenario_6_return,
        test_scenario_7_multi_currency,
        test_scenario_8_tax_inclusive
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {str(e)}")
            failed += 1

    print(f"\n📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")

    return failed == 0

if __name__ == "__main__":
    frappe.init(site=frappe.local.site)
    frappe.connect()

    try:
        success = run_all_tests()
        exit(0 if success else 1)
    finally:
        frappe.destroy()