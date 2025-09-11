#!/usr/bin/env python3
"""
Test script to verify shift report lookup by shift_report_id field
"""

import os
import sys

# Setup environment
os.environ['FRAPPE_SITE'] = 'erp152-v1.vtcom.online'

# Add paths
sys.path.insert(0, '/home/frappe/frappe-bench')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/erpnext')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/posawesome')

# Initialize Frappe
import frappe
frappe.init(site='erp152-v1.vtcom.online')
frappe.connect()

def test_shift_report_lookup():
    """Test shift report lookup functionality"""

    print("🔍 TESTING SHIFT REPORT LOOKUP")
    print("=" * 60)

    # Test data - from user's example
    test_shift_report_id = "SHIFT-POSA-OS-25-0000112"  # This is the shift_report_id field
    test_name = "f11lcjm94r"  # This is the name

    print(f"📋 Test Data:")
    print(f"   shift_report_id field: {test_shift_report_id}")
    print(f"   name: {test_name}")
    print()

    # Test 1: Check if shift report exists by name
    print("1️⃣ Testing lookup by name...")
    exists_by_name = frappe.db.exists("POS Shift Report", test_name)
    print(f"   Exists by name '{test_name}': {exists_by_name}")

    # Test 2: Check if shift report exists by shift_report_id field
    print("\n2️⃣ Testing lookup by shift_report_id field...")
    exists_by_id = frappe.get_all("POS Shift Report",
        filters={"shift_report_id": test_shift_report_id},
        fields=["name", "shift_report_id"],
        limit=1
    )
    print(f"   Found by shift_report_id '{test_shift_report_id}': {len(exists_by_id) > 0}")
    if exists_by_id:
        print(f"   Actual name: {exists_by_id[0].name}")
        print(f"   Actual shift_report_id: {exists_by_id[0].shift_report_id}")

    # Test 3: Test updated API function
    print("\n3️⃣ Testing updated get_shift_report API...")

    # Test with name
    try:
        result1 = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_name
        )
        print("✅ API call with name successful")
        print(f"   Returned shift_report_id: {result1.get('shift_report_id')}")
    except Exception as e:
        print(f"❌ API call with name failed: {e}")

    # Test with shift_report_id field
    try:
        result2 = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_shift_report_id
        )
        print("✅ API call with shift_report_id successful")
        print(f"   Returned shift_report_id: {result2.get('shift_report_id')}")
        print(f"   Returned name: {result2.get('name')}")
    except Exception as e:
        print(f"❌ API call with shift_report_id failed: {e}")

    # Test 4: Compare results
    print("\n4️⃣ Comparing results...")
    if 'result1' in locals() and 'result2' in locals():
        match = (result1.get('name') == result2.get('name') and
                result1.get('shift_report_id') == result2.get('shift_report_id'))
        print(f"   Results match: {match}")

        if match:
            print("✅ Both lookup methods return same data")
        else:
            print("❌ Lookup methods return different data")
            print(f"   By name: {result1.get('name')} - {result1.get('shift_report_id')}")
            print(f"   By ID: {result2.get('name')} - {result2.get('shift_report_id')}")

    # Test 5: Test invalid ID
    print("\n5️⃣ Testing invalid shift_report_id...")
    try:
        result3 = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id="INVALID-ID"
        )
        print("❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly failed for invalid ID: {type(e).__name__}")

    print("\n✅ SHIFT REPORT LOOKUP TEST COMPLETE")

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   - Name lookup: {'✅' if exists_by_name else '❌'}")
    print(f"   - shift_report_id lookup: {'✅' if exists_by_id else '❌'}")
    print(f"   - API with name: {'✅' if 'result1' in locals() else '❌'}")
    print(f"   - API with shift_report_id: {'✅' if 'result2' in locals() else '❌'}")

    if exists_by_name and exists_by_id and 'result1' in locals() and 'result2' in locals():
        print("🎉 ALL TESTS PASSED - Fix should work!")
    else:
        print("❌ SOME TESTS FAILED - Need further debugging")

if __name__ == "__main__":
    try:
        test_shift_report_lookup()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()