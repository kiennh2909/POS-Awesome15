#!/usr/bin/env python3
"""
Test script to verify Shift Report creation logic
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
    """Test the shift report creation logic"""
    print("🧪 Testing Shift Report Creation Logic...")

    try:
        # Test data - Use existing POS Profile
        test_pos_profile = "POS_DY134"  # Existing POS Profile
        test_company = "DY134 Company"  # Existing Company
        test_balance_details = [
            {"mode_of_payment": "Cash", "amount": 1000.00, "currency": "VND"},
            {"mode_of_payment": "Card", "amount": 500.00, "currency": "VND"}
        ]

        print("📝 Test Data:")
        print(f"   POS Profile: {test_pos_profile}")
        print(f"   Company: {test_company}")
        print(f"   Balance Details: {test_balance_details}")

        # First check if POS Profile exists
        if not frappe.db.exists("POS Profile", test_pos_profile):
            print(f"❌ POS Profile {test_pos_profile} does not exist")
            return

        # Check if Company exists
        if not frappe.db.exists("Company", test_company):
            print(f"❌ Company {test_company} does not exist")
            return

        print("✅ POS Profile and Company exist")

        # Call the API
        print("🔄 Calling create_opening_voucher API...")
        result = frappe.call("posawesome.posawesome.api.shifts.create_opening_voucher", {
            "pos_profile": test_pos_profile,
            "company": test_company,
            "balance_details": json.dumps(test_balance_details)
        })

        print("📋 API Response:")
        print(json.dumps(result, indent=2, default=str))

        if result and result.get("message"):
            message = result.get("message")
            print("✅ Opening Shift Created Successfully!")
            print(f"   Opening Shift: {message.get('pos_opening_shift', {}).get('name')}")

            if message.get("shift_report"):
                shift_report = message.get("shift_report")
                print("✅ Shift Report Data Found!")
                print(f"   Shift Report: {shift_report.get('name')}")
                print(f"   Status: {shift_report.get('status')}")
                print(f"   Opening Amounts: {shift_report.get('opening_amounts')}")
                print(f"   Total Opening: {shift_report.get('total_opening_amount')}")

                # Verify the shift report exists in database
                if frappe.db.exists("POS Shift Report", shift_report.get('name')):
                    print("✅ Shift Report verified in database")

                    # Get the actual shift report from database
                    db_report = frappe.get_doc("POS Shift Report", shift_report.get('name'))
                    print(f"   DB Status: {db_report.status}")
                    print(f"   DB Opening Amounts: {db_report.opening_amounts}")
                    print(f"   DB Total Opening: {db_report.total_opening_amount}")
                else:
                    print("❌ Shift Report not found in database")
            else:
                print("❌ No Shift Report data in response")
                print("   Available keys in response:", list(message.keys()))
        else:
            print("❌ API call failed or returned no message")
            if result:
                print("   Result keys:", list(result.keys()))

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_shift_report_creation()