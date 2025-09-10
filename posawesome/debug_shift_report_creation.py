#!/usr/bin/env python3
"""
Debug script to test POS Shift Report creation
"""

import os
import sys
import json
import traceback

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

def debug_shift_report_creation():
    """Debug the shift report creation process"""

    print("🔍 DEBUGGING POS SHIFT REPORT CREATION")
    print("=" * 60)

    try:
        # Test with the problematic opening shift
        opening_shift_id = "POSA-OS-25-0000112"

        print(f"1. Checking if opening shift exists: {opening_shift_id}")
        if not frappe.db.exists("POS Opening Shift", opening_shift_id):
            print(f"❌ Opening shift {opening_shift_id} does not exist!")
            return

        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_id)
        print(f"✅ Opening shift found: {opening_shift.name}")
        print(f"   - Status: {opening_shift.status}")
        print(f"   - User: {opening_shift.user}")
        print(f"   - Posting Date: {opening_shift.posting_date}")
        print(f"   - Period Start Date: {opening_shift.period_start_date}")

        # Check balance details
        if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
            print(f"   - Balance details count: {len(opening_shift.balance_details)}")
            for detail in opening_shift.balance_details:
                print(f"     * Mode: {detail.mode_of_payment}, Amount: {detail.amount}")
        else:
            print("   - No balance details found!")

        # Check if shift report already exists
        print("\n2. Checking if shift report already exists")
        existing_report = frappe.db.exists("POS Shift Report",
            {"pos_opening_shift": opening_shift_id}
        )
        if existing_report:
            print(f"✅ Shift report already exists: {existing_report}")
            report = frappe.get_doc("POS Shift Report", existing_report)
            print(f"   - Shift Report ID: {report.shift_report_id}")
            print(f"   - Status: {report.status}")
            return

        print("❌ No shift report found for this opening shift")

        # Try to create shift report manually
        print("\n3. Attempting to create shift report manually")

        # Prepare balance details
        balance_details = []
        if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
            for detail in opening_shift.balance_details:
                balance_details.append({
                    "mode_of_payment": detail.mode_of_payment,
                    "amount": detail.amount
                })

        print(f"Balance details for creation: {balance_details}")

        # Call the create_shift_report_automatically function
        from posawesome.posawesome.api.shifts import create_shift_report_automatically

        result = create_shift_report_automatically(opening_shift_id, balance_details)
        print(f"Creation result: {result}")

        if result.get("status") == "error":
            print(f"❌ Error creating shift report: {result.get('message')}")
        else:
            print(f"✅ Shift report created successfully: {result}")

    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        debug_shift_report_creation()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        frappe.destroy()
        exit(1)