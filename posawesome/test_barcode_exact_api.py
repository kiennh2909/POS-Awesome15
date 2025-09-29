#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for exact barcode API
Run with: python test_barcode_exact_api.py
"""

import json
import requests
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_exact_barcode_api():
    """Test the new exact barcode API"""

    # Test cases
    test_cases = [
        {
            "name": "Valid barcode (should exist)",
            "barcode": "089686386011",  # Example barcode - replace with real one
            "expected": "item_found"
        },
        {
            "name": "Invalid barcode (should not exist)",
            "barcode": "999999999999",
            "expected": "no_item"
        },
        {
            "name": "Empty barcode",
            "barcode": "",
            "expected": "no_item"
        },
        {
            "name": "Short barcode (< 6 chars)",
            "barcode": "123",
            "expected": "no_item"
        }
    ]

    print("🧪 Testing Exact Barcode API")
    print("=" * 50)

    # Try to get site config for API URL
    try:
        with open('site_config.json', 'r') as f:
            site_config = json.load(f)
            base_url = f"http://localhost:{site_config.get('port', 8000)}"
    except:
        base_url = "http://localhost:8000"

    print(f"📡 API Base URL: {base_url}")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Barcode: '{test_case['barcode']}'")

        try:
            # Make API call
            response = requests.post(
                f"{base_url}/api/method/posawesome.posawesome.api.items.get_item_by_barcode_exact",
                json={
                    "barcode": test_case['barcode'],
                    "pos_profile": json.dumps({
                        "name": "POS Profile 1",  # Replace with real POS profile
                        "warehouse": "Stores - TC",  # Replace with real warehouse
                        "company": "Your Company",  # Replace with real company
                        "selling_price_list": "Standard Selling",  # Replace with real price list
                        "currency": "VND"
                    }),
                    "price_list": "Standard Selling",
                    "customer": None
                },
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('message'):
                    print("   ✅ SUCCESS: Item found")
                    print(f"      Item Code: {result['message'].get('item_code')}")
                    print(f"      Item Name: {result['message'].get('item_name')}")
                    print(f"      Rate: {result['message'].get('rate')}")
                else:
                    print("   ❌ No item found (expected for invalid barcodes)")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"      Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request Error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")

    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    print("\n📝 Manual Testing Checklist:")
    print("1. Test with real barcodes from your Item Barcode doctype")
    print("2. Test with POS Profile that has item restrictions")
    print("3. Test with items that have zero stock (should be filtered)")
    print("4. Test with multi-currency setup")
    print("5. Test performance with many barcodes")

if __name__ == "__main__":
    test_exact_barcode_api()