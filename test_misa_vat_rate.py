#!/usr/bin/env python3
"""
Test script to verify VATRate calculation for MISA integration
"""

def test_misa_vat_rate():
    """Test the VATRate calculation for MISA"""

    # Test data from the log
    test_items = [
        {
            "item_code": "8934755051227",
            "item_name": "TTE Bobby Quần L70",
            "rate": 294069,
            "qty": 2,
            "amount": 588138,
            "uom": "Gói",
            "warehouse": "VTM_DA",
            "expected_vat_rate": 5  # Assuming this item has 5% VAT
        },
        {
            "item_code": "8935012400116",
            "item_name": "Some other item",
            "rate": 10000,
            "qty": 2,
            "amount": 20000,
            "uom": "Gói",
            "warehouse": "VTM_DA",
            "expected_vat_rate": 8  # Assuming this item has 8% VAT
        }
    ]

    print("=== Testing MISA VATRate Calculation ===")
    print()

    for item in test_items:
        print(f"Item: {item['item_code']} - {item['item_name']}")
        print(f"  Rate: {item['rate']}, Qty: {item['qty']}, Amount: {item['amount']}")
        print(f"  Expected VATRate: {item['expected_vat_rate']}%")
        print()

        # Expected MISA format
        misa_item = {
            "Category": "TA GIAY TA QUAN-VN",
            "DiscountRate": "0",
            "ExciseTaxRate": "0",
            "InventoryItemType": "0",
            "Name": item["item_name"],
            "Price": str(item["rate"]),
            "Qty": str(item["qty"]),
            "ServiceFeeRate": "0",
            "UnitName": item["uom"],
            "VATRate": str(item["expected_vat_rate"]),  # This should come from item_tax_template
            "WarehouseCode": item["warehouse"]
        }

        print("Expected MISA format:")
        for key, value in misa_item.items():
            print(f"  {key}: {value}")
        print()

        print("Current issue: VATRate is hardcoded as '0'")
        print("Solution: Get VATRate from item_tax_template")
        print("-" * 50)

if __name__ == "__main__":
    test_misa_vat_rate()