#!/usr/bin/env python3
"""
Debug script to check if API method exists and works
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

def debug_api_method():
    """Debug the API method issue"""

    print("🔍 DEBUGGING API METHOD ISSUE")
    print("=" * 60)

    # Test data
    test_shift_report_id = "f11lcjm94r"

    # Test 1: Check if shift report exists
    print("1️⃣ Checking if shift report exists...")
    exists = frappe.db.exists("POS Shift Report", test_shift_report_id)
    print(f"   Exists: {exists}")

    if not exists:
        print("❌ Shift report does not exist!")
        return

    # Test 2: Try to import the API module
    print("\n2️⃣ Testing API module import...")
    try:
        from posawesome.posawesome.api.shift_reports import get_shift_report
        print("✅ API module imported successfully")
        print(f"   Function exists: {callable(get_shift_report)}")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return

    # Test 3: Test direct function call
    print("\n3️⃣ Testing direct function call...")
    try:
        result = get_shift_report(test_shift_report_id)
        print("✅ Direct function call successful")
        print(f"   Result type: {type(result)}")
        print(f"   Has shift_report_id: {'shift_report_id' in result}")
        print(f"   shift_report_id: {result.get('shift_report_id')}")
    except Exception as e:
        print(f"❌ Direct function call failed: {e}")
        return

    # Test 4: Test frappe.call method
    print("\n4️⃣ Testing frappe.call method...")
    try:
        result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_shift_report_id
        )
        print("✅ frappe.call successful")
        print(f"   Result type: {type(result)}")
        print(f"   Has shift_report_id: {'shift_report_id' in result}")
        print(f"   shift_report_id: {result.get('shift_report_id')}")
    except Exception as e:
        print(f"❌ frappe.call failed: {e}")
        print(f"   Error type: {type(e)}")
        return

    # Test 5: Compare with generic API
    print("\n5️⃣ Comparing with generic API...")
    try:
        generic_result = frappe.get_doc("POS Shift Report", test_shift_report_id)
        custom_result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_shift_report_id
        )

        print("✅ Both APIs successful")
        print(f"   Generic shift_report_id: {generic_result.shift_report_id}")
        print(f"   Custom shift_report_id: {custom_result.get('shift_report_id')}")
        print(f"   Match: {generic_result.shift_report_id == custom_result.get('shift_report_id')}")

    except Exception as e:
        print(f"❌ Comparison failed: {e}")

    print("\n✅ DEBUG COMPLETE")
    print("🎯 If all tests pass, the API method should work in Vue component")

if __name__ == "__main__":
    try:
        debug_api_method()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Debug execution failed: {e}")
        frappe.destroy()