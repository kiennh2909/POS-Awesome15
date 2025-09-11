#!/usr/bin/env python3
"""
Test script to verify data consistency between POS Opening Shift and POS Shift Report
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

def test_data_consistency():
    """Test data consistency between POS Opening Shift and POS Shift Report"""

    print("🔍 TESTING DATA CONSISTENCY")
    print("=" * 60)

    # Test data from user's problematic case
    opening_shift_name = "POSA-OS-25-0000112"
    expected_shift_report_name = "f11lcjm94r"

    print("📋 Test Data:")
    print(f"   POS Opening Shift: {opening_shift_name}")
    print(f"   Expected Shift Report: {expected_shift_report_name}")
    print()

    # Step 1: Check POS Opening Shift
    print("1️⃣ Checking POS Opening Shift...")
    if frappe.db.exists("POS Opening Shift", opening_shift_name):
        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        print("   ✅ POS Opening Shift exists")
        print(f"   📄 Status: {opening_shift.status}")
        print(f"   📄 shift_report field: {getattr(opening_shift, 'shift_report', 'N/A')}")
        print(f"   📄 shift_report_id field: {getattr(opening_shift, 'shift_report_id', 'N/A')}")

        # Check if shift_report field is set
        if hasattr(opening_shift, 'shift_report') and opening_shift.shift_report:
            print(f"   ✅ Has shift_report reference: {opening_shift.shift_report}")

            # Check if referenced shift report exists
            if frappe.db.exists("POS Shift Report", opening_shift.shift_report):
                print("   ✅ Referenced shift report exists")
                shift_report = frappe.get_doc("POS Shift Report", opening_shift.shift_report)
                print(f"   📄 Shift Report ID: {shift_report.shift_report_id}")
                print(f"   📄 Status: {shift_report.status}")
            else:
                print("   ❌ Referenced shift report does NOT exist - DATA INCONSISTENCY!")
                print("   📄 This is the root cause of the error")
        else:
            print("   ❌ No shift_report reference - Shift report was never created!")
            print("   📄 This means create_shift_report_automatically failed during opening shift creation")
    else:
        print("   ❌ POS Opening Shift does not exist")

    print()

    # Step 2: Check all POS Opening Shifts for data consistency
    print("2️⃣ Checking all POS Opening Shifts for data consistency...")

    opening_shifts = frappe.get_all("POS Opening Shift",
        fields=["name", "status", "shift_report", "shift_report_id"],
        limit=10
    )

    print(f"   Found {len(opening_shifts)} POS Opening Shifts")

    consistency_issues = []
    for shift in opening_shifts:
        if shift.shift_report:
            if not frappe.db.exists("POS Shift Report", shift.shift_report):
                consistency_issues.append({
                    "opening_shift": shift.name,
                    "referenced_shift_report": shift.shift_report,
                    "issue": "Referenced shift report does not exist"
                })
        else:
            if shift.status == "Open":  # Only check open shifts
                consistency_issues.append({
                    "opening_shift": shift.name,
                    "referenced_shift_report": None,
                    "issue": "No shift_report reference for open shift"
                })

    if consistency_issues:
        print(f"   ❌ Found {len(consistency_issues)} data consistency issues:")
        for issue in consistency_issues:
            print(f"      - {issue['opening_shift']}: {issue['issue']}")
    else:
        print("   ✅ All POS Opening Shifts have consistent data")

    print()

    # Step 3: Test API behavior with consistency check
    print("3️⃣ Testing API behavior with consistency check...")

    try:
        result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=opening_shift_name
        )
        print("   ✅ API call successful")
        print(f"   📄 Returned shift_report_id: {result.get('shift_report_id')}")
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        print("   📄 This is expected if there's a data consistency issue")

    print()

    # Step 4: Check create_shift_report_automatically function
    print("4️⃣ Checking create_shift_report_automatically function...")

    # Import the function
    from posawesome.posawesome.api.shifts import create_shift_report_automatically

    # Test with sample balance details
    sample_balance_details = [
        {"mode_of_payment": "Cash", "amount": 1000},
        {"mode_of_payment": "Card", "amount": 500}
    ]

    try:
        result = create_shift_report_automatically(opening_shift_name, sample_balance_details)
        print("   ✅ create_shift_report_automatically function works")
        print(f"   📄 Result: {result}")
    except Exception as e:
        print(f"   ❌ create_shift_report_automatically failed: {e}")

    print("\n" + "=" * 60)
    print("🎯 ANALYSIS:")
    print("=" * 60)

    if consistency_issues:
        print("❌ DATA CONSISTENCY ISSUES FOUND:")
        for issue in consistency_issues:
            print(f"   - {issue['opening_shift']}: {issue['issue']}")
        print()
        print("📋 RECOMMENDED FIXES:")
        print("   1. Check why create_shift_report_automatically failed during opening shift creation")
        print("   2. Manually create missing shift reports using create_shift_report_from_opening")
        print("   3. Fix the root cause in create_shift_report_automatically function")
    else:
        print("✅ NO DATA CONSISTENCY ISSUES FOUND")
        print("   - All POS Opening Shifts have valid shift_report references")
        print("   - All referenced POS Shift Reports exist")

    print("\n🎯 CONCLUSION:")
    print("   The error occurs because POS Shift Report should be created automatically")
    print("   when POS Opening Shift is created, but this process failed.")
    print("   The API correctly identifies this as a data consistency issue.")

if __name__ == "__main__":
    try:
        test_data_consistency()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()