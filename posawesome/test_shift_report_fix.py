#!/usr/bin/env python3
"""
Test script to verify the shift report creation fix
"""

import os
import sys
import json

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

def test_shift_report_creation():
    """Test the fixed shift report creation function"""

    print("🧪 TESTING SHIFT REPORT CREATION FIX")
    print("=" * 60)

    try:
        # Test with sample data similar to the error case
        opening_shift_name = "POSA-OS-25-0000112"
        balance_details = [
            {"mode_of_payment": "Tiền mặt - POS", "amount": 10},
            {"mode_of_payment": "Chuyển khoản ngân hàng - POS", "amount": 20}
        ]

        print(f"Testing with opening shift: {opening_shift_name}")
        print(f"Balance details: {balance_details}")

        # Import the function
        from posawesome.posawesome.api.shifts import create_shift_report_automatically

        # Test the function
        result = create_shift_report_automatically(opening_shift_name, balance_details)

        print(f"Result: {result}")

        if result.get("status") == "error":
            print(f"❌ Error: {result.get('message')}")
            return False
        else:
            print(f"✅ Success: {result}")
            return True

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_shift_report_creation()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED - Shift report creation fix is working!")
        else:
            print("❌ TEST FAILED - There are still issues with shift report creation")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)