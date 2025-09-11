#!/usr/bin/env python3
"""
Test script to verify object detection and handling in Vue component
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

def test_object_detection():
    """Test object detection and handling"""

    print("🔍 TESTING OBJECT DETECTION AND HANDLING")
    print("=" * 60)

    # Test data - simulate what Vue component might receive
    test_cases = [
        {
            "name": "String ID (correct)",
            "data": "SHIFT-POSA-OS-25-0000112",
            "expected": "SHIFT-POSA-OS-25-0000112"
        },
        {
            "name": "Object with shift_report_id",
            "data": {
                "name": "POSA-OS-25-0000112",
                "shift_report_id": "SHIFT-POSA-OS-25-0000112",
                "status": "Open"
            },
            "expected": "SHIFT-POSA-OS-25-0000112"
        },
        {
            "name": "Object with name only",
            "data": {
                "name": "f11lcjm94r",
                "status": "Open"
            },
            "expected": "f11lcjm94r"
        },
        {
            "name": "Full POS Opening Shift object",
            "data": {
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
            },
            "expected": "SHIFT-POSA-OS-25-0000112"
        }
    ]

    print("📋 Test Cases:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"   {i}. {test_case['name']}")
    print()

    # Simulate Vue component logic
    def simulate_vue_logic(shiftReportId):
        """Simulate the Vue component logic for object detection"""
        console_logs = []

        def console_log(msg):
            console_logs.append(msg)

        def console_error(msg):
            console_logs.append(f"ERROR: {msg}")

        console_log(f"[SHIFT_REPORT] Loading shift report data for footer: {shiftReportId}")
        console_log(f"[SHIFT_REPORT] shiftReportId type: {type(shiftReportId)}")

        # DETECT IF shiftReportId IS AN OBJECT INSTEAD OF STRING
        actualShiftReportId = shiftReportId

        if isinstance(shiftReportId, dict) and shiftReportId is not None:
            console_error("[SHIFT_REPORT] ERROR: shiftReportId is an object, not a string!")
            console_log(f"[SHIFT_REPORT] Object keys: {list(shiftReportId.keys())}")
            console_log(f"[SHIFT_REPORT] Object content: {json.dumps(shiftReportId, indent=2)}")

            # Try to extract the correct ID from the object
            if 'shift_report_id' in shiftReportId:
                console_log(f"[SHIFT_REPORT] Found shift_report_id in object: {shiftReportId['shift_report_id']}")
                actualShiftReportId = shiftReportId['shift_report_id']
            elif 'name' in shiftReportId:
                console_log(f"[SHIFT_REPORT] Found name in object: {shiftReportId['name']}")
                actualShiftReportId = shiftReportId['name']
            else:
                console_error("[SHIFT_REPORT] Cannot extract ID from object - using object as-is")
                actualShiftReportId = json.dumps(shiftReportId)

        console_log(f"[SHIFT_REPORT] Using custom API with ID: {actualShiftReportId}")

        return actualShiftReportId, console_logs

    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing: {test_case['name']}")
        print("-" * 40)

        # Simulate Vue logic
        result, logs = simulate_vue_logic(test_case['data'])

        # Print logs
        for log in logs:
            print(f"   {log}")

        # Check result
        if result == test_case['expected']:
            print(f"   ✅ PASS: Expected '{test_case['expected']}', got '{result}'")
        else:
            print(f"   ❌ FAIL: Expected '{test_case['expected']}', got '{result}'")

    print("\n" + "=" * 60)
    print("📊 OBJECT DETECTION TEST COMPLETE")

    # Test with actual API
    print("\n🔄 TESTING WITH ACTUAL API")
    print("=" * 60)

    # Test the problematic case from user's debug
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

    print("📋 Testing problematic object from user's debug:")
    print(f"   shift_report_id field: {problematic_object.get('shift_report_id')}")
    print(f"   name field: {problematic_object.get('name')}")

    # Simulate extraction
    if 'shift_report_id' in problematic_object:
        extracted_id = problematic_object['shift_report_id']
        print(f"   ✅ Extracted ID: {extracted_id}")
    else:
        extracted_id = problematic_object.get('name', 'N/A')
        print(f"   ⚠️  Fallback to name: {extracted_id}")

    # Test API call with extracted ID
    try:
        api_result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=extracted_id
        )
        print("   ✅ API call successful with extracted ID")
        print(f"   📄 Returned shift_report_id: {api_result.get('shift_report_id')}")
    except Exception as e:
        print(f"   ❌ API call failed: {e}")

    print("\n🎯 CONCLUSION:")
    print("   - Vue component should detect object input")
    print("   - Extract shift_report_id field when available")
    print("   - Fallback to name field if shift_report_id not available")
    print("   - API should handle both name and shift_report_id lookup")

if __name__ == "__main__":
    try:
        test_object_detection()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()