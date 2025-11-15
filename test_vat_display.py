#!/usr/bin/env python3
"""
Test script to verify VAT display functionality
"""

def test_vat_display_logic():
    """Test the VAT display logic"""

    # Test case 1: Item with VAT rate
    print("=== Test Case 1: Item with VAT 8% ===")
    item = {
        "rate": 17500,
        "custom_vat_rate": 8,
        "custom_price_list_rate_after_vat": 19125  # 17500 * 1.08
    }

    # Display logic: show custom_price_list_rate_after_vat if available, else rate
    display_price = item.get("custom_price_list_rate_after_vat") or item.get("rate")
    vat_rate = item.get("custom_vat_rate")

    print(f"Original rate: {item['rate']}")
    print(f"Display price: {display_price}")
    print(f"VAT rate: {vat_rate}%")
    print(f"Display text: {display_price} (VAT {vat_rate}%)")

    # Test case 2: Item without custom fields (fallback)
    print("\n=== Test Case 2: Item without custom VAT fields ===")
    item2 = {
        "rate": 40500,
        "custom_vat_rate": None,
        "custom_price_list_rate_after_vat": None
    }

    display_price2 = item2.get("custom_price_list_rate_after_vat") or item2.get("rate")
    vat_rate2 = item2.get("custom_vat_rate")

    print(f"Original rate: {item2['rate']}")
    print(f"Display price: {display_price2}")
    if vat_rate2:
        print(f"Display text: {display_price2} (VAT {vat_rate2}%)")
    else:
        print(f"Display text: {display_price2}")

    # Test case 3: Item with VAT 5%
    print("\n=== Test Case 3: Item with VAT 5% ===")
    item3 = {
        "rate": 40500,
        "custom_vat_rate": 5,
        "custom_price_list_rate_after_vat": 42525  # 40500 * 1.05
    }

    display_price3 = item3.get("custom_price_list_rate_after_vat") or item3.get("rate")
    vat_rate3 = item3.get("custom_vat_rate")

    print(f"Original rate: {item3['rate']}")
    print(f"Display price: {display_price3}")
    print(f"VAT rate: {vat_rate3}%")
    print(f"Display text: {display_price3} (VAT {vat_rate3}%)")

if __name__ == "__main__":
    test_vat_display_logic()