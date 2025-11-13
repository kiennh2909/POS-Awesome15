#!/usr/bin/env python3
"""
Test script to verify inclusive tax calculation logic
"""

def test_inclusive_tax_calculation():
    """Test the inclusive tax calculation logic"""

    print("=== Test Inclusive Tax Calculation ===")

    # Test case: Item with price 17500 including 8% tax
    item_price = 17500  # Price including tax
    tax_rate = 8.0

    print(f"Item price (including tax): {item_price}")
    print(f"Tax rate: {tax_rate}%")

    # Calculate tax amount: price * rate / (100 + rate)
    tax_amount = item_price * tax_rate / (100 + tax_rate)
    net_amount = item_price - tax_amount

    print(f"Calculated tax amount: {tax_amount:.2f}")
    print(f"Calculated net amount: {net_amount:.2f}")
    print(f"Verification: {net_amount:.2f} + {tax_amount:.2f} = {net_amount + tax_amount:.2f}")

    # Test with multiple tax rates
    print("\n=== Test Multiple Tax Rates ===")
    item_price_2 = 17500  # Price including tax
    tax_rates = [8.0, 10.0]  # Multiple rates

    total_rate = sum(tax_rates)
    print(f"Item price: {item_price_2}")
    print(f"Tax rates: {tax_rates}")
    print(f"Total tax rate: {total_rate}%")

    # Calculate total tax
    total_tax = item_price_2 * total_rate / (100 + total_rate)
    net_amount_2 = item_price_2 - total_tax

    print(f"Total tax: {total_tax:.2f}")
    print(f"Net amount: {net_amount_2:.2f}")

    # Calculate proportional tax for each rate
    tax_8 = total_tax * (8.0 / total_rate)
    tax_10 = total_tax * (10.0 / total_rate)

    print(f"Tax 8%: {tax_8:.2f}")
    print(f"Tax 10%: {tax_10:.2f}")
    print(f"Sum of taxes: {tax_8 + tax_10:.2f}")
    print(f"Grand total: {net_amount_2 + tax_8 + tax_10:.2f}")

    # Manual verification
    print("\n=== Manual Verification ===")
    print("Formula: tax = price * rate / (100 + rate)")
    print(f"Tax 8% = 17500 * 8 / (100 + 8) = {17500 * 8 / 108:.2f}")
    print(f"Tax 10% = 17500 * 10 / (100 + 10) = {17500 * 10 / 110:.2f}")
    print(f"Total tax = {17500 * 18 / 118:.2f}")
    print(f"Net = 17500 - {17500 * 18 / 118:.2f} = {17500 - (17500 * 18 / 118):.2f}")

if __name__ == "__main__":
    test_inclusive_tax_calculation()