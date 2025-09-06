#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Performance: Bin vs Stock Ledger Entry
"""

import time
import frappe
from posawesome.posawesome.api.items import (
    get_stock_from_bin,
    get_stock_availability_from_ledger,
    get_stock_unified
)

def test_performance():
    """Test performance giữa Bin và Stock Ledger Entry"""

    # Test data
    test_items = [
        "ITEM-001",
        "ITEM-002",
        "ITEM-003",
        "ITEM-004",
        "ITEM-005"
    ]
    warehouse = "Main Warehouse"

    print("🚀 Testing Stock Retrieval Performance")
    print("=" * 50)

    # Test Bin Performance
    print("\n📊 Testing Bin Performance:")
    start_time = time.time()
    bin_results = []
    for item in test_items:
        qty = get_stock_from_bin(item, warehouse)
        bin_results.append(qty)
        print(f"  {item}: {qty}")

    bin_time = time.time() - start_time
    print(".4f")

    # Test Stock Ledger Entry Performance
    print("\n📊 Testing Stock Ledger Entry Performance:")
    start_time = time.time()
    ledger_results = []
    for item in test_items:
        qty = get_stock_availability_from_ledger(item, warehouse)
        ledger_results.append(qty)
        print(f"  {item}: {qty}")

    ledger_time = time.time() - start_time
    print(".4f")

    # Compare Results
    print("\n📈 Performance Comparison:")
    print(f"  Bin Time:        {bin_time:.4f}s")
    print(f"  Ledger Time:     {ledger_time:.4f}s")
    print(".1f")

    if ledger_time > 0:
        print(".0f")

    # Verify Results Match
    print("\n✅ Results Verification:")
    matches = 0
    for i, (bin_qty, ledger_qty) in enumerate(zip(bin_results, ledger_results)):
        if abs(bin_qty - ledger_qty) < 0.01:  # Allow small floating point differences
            matches += 1
            print(f"  {test_items[i]}: ✓ Match ({bin_qty})")
        else:
            print(f"  {test_items[i]}: ⚠️  Mismatch (Bin: {bin_qty}, Ledger: {ledger_qty})")

    print(f"\n📊 Summary: {matches}/{len(test_items)} items matched")

    return {
        "bin_time": bin_time,
        "ledger_time": ledger_time,
        "speedup": ledger_time / bin_time if bin_time > 0 else 0,
        "matches": matches
    }

def test_unified_function():
    """Test hàm unified"""
    print("\n🔄 Testing Unified Function:")

    item_code = "ITEM-001"
    warehouse = "Main Warehouse"

    # Test different sources
    sources = ["bin", "stock_ledger", "auto"]

    for source in sources:
        qty = get_stock_unified(item_code, warehouse, source)
        print(f"  Source '{source}': {qty}")

if __name__ == "__main__":
    # Initialize Frappe (nếu cần)
    try:
        frappe.init(site="your-site-name")
        frappe.connect()

        # Run tests
        results = test_performance()
        test_unified_function()

        print("\n🎉 Performance Test Completed!")
        print(f"   Speed improvement: {results['speedup']:.1f}x faster")
        print(f"   Data accuracy: {results['matches']}/5 items matched")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        frappe.destroy()