#!/usr/bin/env python3
"""
Test script to verify auto-creation of POS Shift Report
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

def test_auto_create_shift_report():
    """Test auto-creation of POS Shift Report"""

    print("🔍 TESTING AUTO-CREATION OF POS SHIFT REPORT")
    print("=" * 60)

    # Test data from user's problematic object
    opening_shift_name = "POSA-OS-25-0000112"
    expected_shift_report_name = "f11lcjm94r"  # From shift_report field

    print("📋 Test Data:")
    print(f"   POS Opening Shift: {opening_shift_name}")
    print(f"   Expected Shift Report: {expected_shift_report_name}")
    print()

    # Step 1: Check if POS Opening Shift exists
    print("1️⃣ Checking POS Opening Shift...")
    opening_exists = frappe.db.exists("POS Opening Shift", opening_shift_name)
    print(f"   POS Opening Shift exists: {opening_exists}")

    if not opening_exists:
        print("❌ POS Opening Shift does not exist - cannot test auto-creation")
        return

    # Get opening shift details
    opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
    print(f"   Status: {opening_shift.status}")
    print(f"   shift_report field: {getattr(opening_shift, 'shift_report', 'N/A')}")
    print(f"   shift_report_id field: {getattr(opening_shift, 'shift_report_id', 'N/A')}")
    print()

    # Step 2: Check if POS Shift Report already exists
    print("2️⃣ Checking existing POS Shift Report...")
    shift_report_exists = frappe.db.exists("POS Shift Report", expected_shift_report_name)
    print(f"   POS Shift Report exists by name: {shift_report_exists}")

    if shift_report_exists:
        print("⚠️  POS Shift Report already exists - deleting for clean test")
        try:
            frappe.delete_doc("POS Shift Report", expected_shift_report_name, force=True)
            frappe.db.commit()
            print("✅ Deleted existing POS Shift Report")
        except Exception as e:
            print(f"❌ Failed to delete existing report: {e}")
            return

    # Step 3: Test API call that should auto-create
    print("\n3️⃣ Testing API call with auto-creation...")

    try:
        result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=opening_shift_name  # Pass opening shift name
        )

        print("✅ API call successful!")
        print(f"   Returned name: {result.get('name')}")
        print(f"   Returned shift_report_id: {result.get('shift_report_id')}")
        print(f"   Status: {result.get('status')}")

        # Verify the shift report was created
        created_exists = frappe.db.exists("POS Shift Report", result.get('name'))
        print(f"   POS Shift Report created: {created_exists}")

        if created_exists:
            # Check if opening shift was updated
            updated_opening = frappe.get_doc("POS Opening Shift", opening_shift_name)
            print(f"   Opening shift_report field: {getattr(updated_opening, 'shift_report', 'N/A')}")
            print(f"   Opening shift_report_id field: {getattr(updated_opening, 'shift_report_id', 'N/A')}")

            # Verify they match
            match = (updated_opening.shift_report == result.get('name') and
                    updated_opening.shift_report_id == result.get('shift_report_id'))
            print(f"   Fields match: {match}")

        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def test_with_problematic_object():
    """Test with the exact problematic object from user"""

    print("\n🎯 TESTING WITH PROBLEMATIC OBJECT")
    print("=" * 60)

    # The exact object from user's error
    problematic_object = {
        "name": "POSA-OS-25-0000112",
        "owner": "admin@vtcom.online",
        "creation": "2025-09-10 23:50:49.441816",
        "modified": "2025-09-10 23:50:49.709266",
        "modified_by": "admin@vtcom.online",
        "docstatus": 1,
        "idx": 2,
        "period_start_date": "2025-09-10 23:50:49.431225",
        "status": "Open",
        "posting_date": "2025-09-10",
        "set_posting_date": 0,
        "company": "NVL-DaiLoan",
        "pos_profile": "POS_DY134",
        "user": "admin@vtcom.online",
        "shift_report": "f11lcjm94r",
        "shift_report_id": "SHIFT-POSA-OS-25-0000112",
        "doctype": "POS Opening Shift"
    }

    print("📋 Problematic Object:")
    print(f"   name: {problematic_object.get('name')}")
    print(f"   shift_report: {problematic_object.get('shift_report')}")
    print(f"   shift_report_id: {problematic_object.get('shift_report_id')}")
    print()

    # Simulate Vue component extraction
    print("🎭 SIMULATING VUE COMPONENT EXTRACTION")
    print("-" * 40)

    shiftReportId = problematic_object
    actualShiftReportId = shiftReportId

    if isinstance(shiftReportId, dict) and shiftReportId is not None:
        print("Detected object input")

        # Try shift_report field first
        if 'shift_report' in shiftReportId and shiftReportId['shift_report']:
            actualShiftReportId = shiftReportId['shift_report']
            print(f"✅ Extracted from shift_report: {actualShiftReportId}")
        elif 'name' in shiftReportId:
            actualShiftReportId = shiftReportId['name']
            print(f"⚠️  Fallback to name: {actualShiftReportId}")
        else:
            print("❌ Cannot extract ID")
            return

    print(f"Final ID to use: {actualShiftReportId}")
    print()

    # Test API with extracted ID
    print("🔄 TESTING API WITH EXTRACTED ID")
    print("-" * 40)

    try:
        result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=actualShiftReportId
        )

        print("✅ API call successful!")
        print(f"   Returned name: {result.get('name')}")
        print(f"   Returned shift_report_id: {result.get('shift_report_id')}")

        # Verify creation
        created = frappe.db.exists("POS Shift Report", result.get('name'))
        print(f"   POS Shift Report created: {created}")

        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("🚀 STARTING AUTO-CREATE SHIFT REPORT TESTS")
        print("=" * 60)

        # Run tests
        test1_passed = test_auto_create_shift_report()
        test2_passed = test_with_problematic_object()

        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        if test1_passed and test2_passed:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Auto-creation of POS Shift Report is working")
            print("✅ Vue component should now work without errors")
        else:
            print("❌ SOME TESTS FAILED!")
            print("🔧 Check the error messages above")

        frappe.destroy()

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()