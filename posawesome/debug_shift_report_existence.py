#!/usr/bin/env python3
"""
Debug script to check if POS Shift Report exists and verify ID extraction
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

def debug_shift_report_existence():
    """Debug POS Shift Report existence and ID extraction"""

    print("🔍 DEBUGGING SHIFT REPORT EXISTENCE")
    print("=" * 60)

    # Test data from user's error
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

    print("📋 Problematic Object from User:")
    print(f"   name: {problematic_object.get('name')}")
    print(f"   shift_report: {problematic_object.get('shift_report')}")
    print(f"   shift_report_id: {problematic_object.get('shift_report_id')}")
    print()

    # Simulate Vue component logic
    print("🎭 SIMULATING VUE COMPONENT LOGIC")
    print("-" * 40)

    shiftReportId = problematic_object
    print(f"shiftReportId: {shiftReportId}")
    print(f"shiftReportId type: {type(shiftReportId)}")

    # DETECT IF shiftReportId IS AN OBJECT INSTEAD OF STRING
    actualShiftReportId = shiftReportId

    if isinstance(shiftReportId, dict) and shiftReportId is not None:
        print("ERROR: shiftReportId is an object, not a string!")
        print(f"Object keys: {list(shiftReportId.keys())}")

        # PRIORITY: Try shift_report_id first (most reliable)
        if 'shift_report_id' in shiftReportId:
            print(f"✅ Found shift_report_id in object: {shiftReportId['shift_report_id']}")
            actualShiftReportId = shiftReportId['shift_report_id']
        # SECOND: Try name field
        elif 'name' in shiftReportId:
            print(f"⚠️  shift_report_id not found, using name: {shiftReportId['name']}")
            actualShiftReportId = shiftReportId['name']
        # LAST RESORT: Cannot extract
        else:
            print("❌ Cannot extract ID from object - no shift_report_id or name field")
            print(f"Available fields: {list(shiftReportId.keys())}")
            return

    # VALIDATE FINAL ID
    if not actualShiftReportId or actualShiftReportId.strip() == '':
        print(f"❌ Final shiftReportId is empty or invalid: {actualShiftReportId}")
        return

    print(f"✅ Final shiftReportId to use: {actualShiftReportId}")
    print()

    # Test with extracted ID
    extracted_id = actualShiftReportId
    print("🔍 TESTING WITH EXTRACTED ID")
    print("-" * 40)
    print(f"Extracted ID: {extracted_id}")
    print()

    # Test 1: Check if POS Shift Report exists by name
    print("1️⃣ Checking if POS Shift Report exists by name...")
    exists_by_name = frappe.db.exists("POS Shift Report", extracted_id)
    print(f"   Exists by name '{extracted_id}': {exists_by_name}")

    if exists_by_name:
        print("   ✅ POS Shift Report found by name!")
        shift_report = frappe.get_doc("POS Shift Report", extracted_id)
        print(f"   📄 shift_report_id field: {shift_report.shift_report_id}")
        print(f"   📄 status: {shift_report.status}")
        print(f"   📄 pos_opening_shift: {shift_report.pos_opening_shift}")
    else:
        print("   ❌ POS Shift Report NOT found by name")

    # Test 2: Check if POS Shift Report exists by shift_report_id field
    print("\n2️⃣ Checking if POS Shift Report exists by shift_report_id field...")
    exists_by_field = frappe.get_all("POS Shift Report",
        filters={"shift_report_id": extracted_id},
        fields=["name", "shift_report_id", "status"],
        limit=1
    )
    print(f"   Found by shift_report_id field '{extracted_id}': {len(exists_by_field) > 0}")

    if exists_by_field:
        print("   ✅ POS Shift Report found by shift_report_id field!")
        found = exists_by_field[0]
        print(f"   📄 name: {found.name}")
        print(f"   📄 shift_report_id: {found.shift_report_id}")
        print(f"   📄 status: {found.status}")

        # Test API call with correct name
        correct_name = found.name
        print(f"\n3️⃣ Testing API call with correct name: {correct_name}")
        try:
            api_result = frappe.call(
                "posawesome.posawesome.api.shift_reports.get_shift_report",
                shift_report_id=correct_name
            )
            print("   ✅ API call successful!")
            print(f"   📄 Returned shift_report_id: {api_result.get('shift_report_id')}")
            print(f"   📄 Returned name: {api_result.get('name')}")
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
    else:
        print("   ❌ POS Shift Report NOT found by shift_report_id field")

    # Test 3: Check all POS Shift Reports
    print("\n4️⃣ Checking all POS Shift Reports...")
    all_reports = frappe.get_all("POS Shift Report",
        fields=["name", "shift_report_id", "status", "pos_opening_shift"],
        limit=10
    )

    print(f"   Total POS Shift Reports: {len(all_reports)}")
    for i, report in enumerate(all_reports, 1):
        print(f"   {i}. Name: {report.name}")
        print(f"      shift_report_id: {report.shift_report_id}")
        print(f"      pos_opening_shift: {report.pos_opening_shift}")
        print(f"      status: {report.status}")
        print()

    # Test 4: Check if the referenced POS Opening Shift exists
    print("5️⃣ Checking referenced POS Opening Shift...")
    opening_shift_name = problematic_object.get('shift_report')  # This should be the POS Opening Shift name
    print(f"   POS Opening Shift name from object: {opening_shift_name}")

    exists_opening = frappe.db.exists("POS Opening Shift", opening_shift_name)
    print(f"   POS Opening Shift exists: {exists_opening}")

    if exists_opening:
        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        print(f"   📄 Opening shift status: {opening_shift.status}")
        print(f"   📄 Opening shift shift_report: {getattr(opening_shift, 'shift_report', 'N/A')}")
        print(f"   📄 Opening shift shift_report_id: {getattr(opening_shift, 'shift_report_id', 'N/A')}")

    print("\n" + "=" * 60)
    print("🎯 ANALYSIS:")
    print("=" * 60)

    if exists_by_name:
        print("✅ POS Shift Report exists by name - API should work")
    elif exists_by_field:
        print("⚠️  POS Shift Report exists by shift_report_id field but not by name")
        print("   → Vue component should extract the correct name from the found record")
    else:
        print("❌ POS Shift Report does not exist with the extracted ID")
        print("   → Check if the POS Opening Shift has a valid shift_report reference")

    if exists_opening:
        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        if hasattr(opening_shift, 'shift_report') and opening_shift.shift_report:
            print(f"✅ POS Opening Shift has shift_report: {opening_shift.shift_report}")
        else:
            print("❌ POS Opening Shift does not have shift_report field or it's empty")
    else:
        print("❌ Referenced POS Opening Shift does not exist")

if __name__ == "__main__":
    try:
        debug_shift_report_existence()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Debug execution failed: {e}")
        frappe.destroy()