#!/usr/bin/env python3
"""
Test script to verify tax calculation per item vs total invoice
"""

def test_tax_calculation():
    """Test the tax calculation logic"""

    # Test case 1: Single item with 5% tax
    print("=== Test Case 1: Single item 40500 with 5% tax ===")
    item_amount = 40500
    tax_rate = 5.0

    # Old logic (wrong): tax on total
    old_tax = item_amount * tax_rate / 100
    print(f"Per-item tax (correct): {old_tax}")

    # Test case 2: Two items with different tax rates
    print("\n=== Test Case 2: Two items totaling 35000 with 8% and 10% tax ===")
    items = [
        {"amount": 17500, "rate": 8.0},
        {"amount": 17500, "rate": 10.0}
    ]

    total_amount = sum(item["amount"] for item in items)
    print(f"Total amount: {total_amount}")

    # Old logic (wrong): tax on total
    old_tax_8 = total_amount * 8.0 / 100
    old_tax_10 = total_amount * 10.0 / 100
    print(f"Old logic - Tax 8%: {old_tax_8}, Tax 10%: {old_tax_10}")
    print(f"Old logic - Total tax: {old_tax_8 + old_tax_10}")

    # New logic (correct): tax per item
    new_tax_8 = items[0]["amount"] * items[0]["rate"] / 100
    new_tax_10 = items[1]["amount"] * items[1]["rate"] / 100
    print(f"New logic - Tax 8%: {new_tax_8}, Tax 10%: {new_tax_10}")
    print(f"New logic - Total tax: {new_tax_8 + new_tax_10}")

    # Grand totals
    old_grand_total = total_amount + old_tax_8 + old_tax_10
    new_grand_total = total_amount + new_tax_8 + new_tax_10
    print(f"Old grand total: {old_grand_total}")
    print(f"New grand total: {new_grand_total}")

    print("\n=== Verification ===")
    print(f"Item 1 (17500 * 8%): {17500 * 0.08} = {new_tax_8}")
    print(f"Item 2 (17500 * 10%): {17500 * 0.10} = {new_tax_10}")
    print(f"Total tax should be: {1400 + 1750} = {3150}")
    print(f"Grand total should be: {35000 + 3150} = {38150}")

if __name__ == "__main__":
    test_tax_calculation()