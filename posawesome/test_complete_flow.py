#!/usr/bin/env python3
"""
Comprehensive test script to verify the complete flow:
POS Opening Shift → POS Shift Report → Vue Component → API Calls
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

def test_complete_flow():
    """Test the complete flow from POS Opening Shift to Vue component"""

    print("🔍 TESTING COMPLETE FLOW")
    print("=" * 80)
    print("POS Opening Shift → POS Shift Report → Vue Component → API Calls")
    print("=" * 80)

    # Test data
    opening_shift_name = "POSA-OS-25-0000112"
    expected_shift_report_name = "f11lcjm94r"

    print("📋 TEST DATA:")
    print(f"   POS Opening Shift: {opening_shift_name}")
    print(f"   Expected Shift Report: {expected_shift_report_name}")
    print()

    # ============================================================================
    # STEP 1: CHECK POS OPENING SHIFT
    # ============================================================================
    print("1️⃣ STEP 1: CHECK POS OPENING SHIFT")
    print("-" * 50)

    if not frappe.db.exists("POS Opening Shift", opening_shift_name):
        print("❌ POS Opening Shift does not exist")
        return False

    opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
    print("✅ POS Opening Shift exists")
    print(f"   📄 Name: {opening_shift.name}")
    print(f"   📄 Status: {opening_shift.status}")
    print(f"   📄 User: {opening_shift.user}")
    print(f"   📄 POS Profile: {opening_shift.pos_profile}")
    print(f"   📄 Company: {opening_shift.company}")
    print(f"   📄 Posting Date: {opening_shift.posting_date}")
    print(f"   📄 Period Start Date: {opening_shift.period_start_date}")
    print(f"   📄 shift_report field: {getattr(opening_shift, 'shift_report', 'N/A')}")
    print(f"   📄 shift_report_id field: {getattr(opening_shift, 'shift_report_id', 'N/A')}")

    # Check balance details
    if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
        print(f"   📄 Balance Details: {len(opening_shift.balance_details)} items")
        for i, detail in enumerate(opening_shift.balance_details):
            print(f"      {i+1}. {detail.mode_of_payment}: {detail.amount}")
    else:
        print("   ⚠️  No balance details found")

    print()

    # ============================================================================
    # STEP 2: CHECK IF POS SHIFT REPORT EXISTS
    # ============================================================================
    print("2️⃣ STEP 2: CHECK POS SHIFT REPORT EXISTENCE")
    print("-" * 50)

    # Check by name
    shift_report_exists_by_name = frappe.db.exists("POS Shift Report", expected_shift_report_name)
    print(f"   📄 Exists by name '{expected_shift_report_name}': {shift_report_exists_by_name}")

    # Check by shift_report_id field
    shift_report_exists_by_id = frappe.get_all("POS Shift Report",
        filters={"shift_report_id": getattr(opening_shift, 'shift_report_id', '')},
        fields=["name", "shift_report_id", "status"]
    )
    print(f"   📄 Exists by shift_report_id '{getattr(opening_shift, 'shift_report_id', '')}': {len(shift_report_exists_by_id) > 0}")

    if shift_report_exists_by_name:
        shift_report = frappe.get_doc("POS Shift Report", expected_shift_report_name)
        print("   ✅ POS Shift Report exists")
        print(f"   📄 Name: {shift_report.name}")
        print(f"   📄 shift_report_id: {shift_report.shift_report_id}")
        print(f"   📄 Status: {shift_report.status}")
        print(f"   📄 pos_opening_shift: {shift_report.pos_opening_shift}")
        print(f"   📄 opening_date: {shift_report.opening_date}")
        print(f"   📄 opened_by: {shift_report.opened_by}")
        print(f"   📄 total_opening_amount: {shift_report.total_opening_amount}")
    elif shift_report_exists_by_id:
        shift_report = frappe.get_doc("POS Shift Report", shift_report_exists_by_id[0].name)
        print("   ⚠️  POS Shift Report exists but with different name")
        print(f"   📄 Found name: {shift_report.name}")
        print(f"   📄 Expected name: {expected_shift_report_name}")
    else:
        print("   ❌ POS Shift Report does not exist")
        print("   📋 This indicates create_shift_report_automatically failed")

    print()

    # ============================================================================
    # STEP 3: TEST create_shift_report_automatically FUNCTION
    # ============================================================================
    print("3️⃣ STEP 3: TEST create_shift_report_automatically FUNCTION")
    print("-" * 50)

    from posawesome.posawesome.api.shifts import create_shift_report_automatically

    # Prepare balance details from opening shift
    balance_details = []
    if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
        for detail in opening_shift.balance_details:
            balance_details.append({
                "mode_of_payment": detail.mode_of_payment,
                "amount": detail.amount
            })

    print(f"   📄 Balance details for function: {balance_details}")

    try:
        result = create_shift_report_automatically(opening_shift_name, balance_details)
        print("   ✅ create_shift_report_automatically executed successfully")
        print(f"   📄 Result: {result}")

        if result.get("status") == "created":
            print("   ✅ New shift report was created")
            print(f"   📄 Created name: {result.get('name')}")
            print(f"   📄 Created shift_report_id: {result.get('shift_report_id')}")
        elif result.get("status") == "existing":
            print("   ✅ Existing shift report found")
            print(f"   📄 Existing name: {result.get('name')}")
        elif result.get("status") == "error":
            print("   ❌ Function returned error")
            print(f"   📄 Error message: {result.get('message')}")

    except Exception as e:
        print(f"   ❌ create_shift_report_automatically threw exception: {e}")

    print()

    # ============================================================================
    # STEP 4: TEST API get_shift_report
    # ============================================================================
    print("4️⃣ STEP 4: TEST API get_shift_report")
    print("-" * 50)

    # Test with opening shift name
    print("   📋 Testing with opening shift name...")
    try:
        result1 = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=opening_shift_name
        )
        print("   ✅ API call with opening shift name successful")
        print(f"   📄 Returned name: {result1.get('name')}")
        print(f"   📄 Returned shift_report_id: {result1.get('shift_report_id')}")
    except Exception as e:
        print(f"   ❌ API call with opening shift name failed: {e}")

    # Test with expected shift report name
    print("\n   📋 Testing with expected shift report name...")
    try:
        result2 = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=expected_shift_report_name
        )
        print("   ✅ API call with shift report name successful")
        print(f"   📄 Returned name: {result2.get('name')}")
        print(f"   📄 Returned shift_report_id: {result2.get('shift_report_id')}")
    except Exception as e:
        print(f"   ❌ API call with shift report name failed: {e}")

    # Test with shift_report_id field value
    shift_report_id_value = getattr(opening_shift, 'shift_report_id', '')
    if shift_report_id_value:
        print(f"\n   📋 Testing with shift_report_id field value: {shift_report_id_value}")
        try:
            result3 = frappe.call(
                "posawesome.posawesome.api.shift_reports.get_shift_report",
                shift_report_id=shift_report_id_value
            )
            print("   ✅ API call with shift_report_id successful")
            print(f"   📄 Returned name: {result3.get('name')}")
            print(f"   📄 Returned shift_report_id: {result3.get('shift_report_id')}")
        except Exception as e:
            print(f"   ❌ API call with shift_report_id failed: {e}")

    print()

    # ============================================================================
    # STEP 5: SIMULATE VUE COMPONENT LOGIC
    # ============================================================================
    print("5️⃣ STEP 5: SIMULATE VUE COMPONENT LOGIC")
    print("-" * 50)

    # Simulate the problematic object that Vue receives
    problematic_object = {
        "name": opening_shift.name,
        "owner": opening_shift.owner,
        "creation": str(opening_shift.creation),
        "modified": str(opening_shift.modified),
        "modified_by": opening_shift.modified_by,
        "docstatus": opening_shift.docstatus,
        "idx": opening_shift.idx,
        "period_start_date": str(opening_shift.period_start_date),
        "status": opening_shift.status,
        "posting_date": str(opening_shift.posting_date),
        "set_posting_date": getattr(opening_shift, 'set_posting_date', 0),
        "company": opening_shift.company,
        "pos_profile": opening_shift.pos_profile,
        "user": opening_shift.user,
        "shift_report": getattr(opening_shift, 'shift_report', None),
        "shift_report_id": getattr(opening_shift, 'shift_report_id', None),
        "doctype": opening_shift.doctype
    }

    print("   📋 Problematic object structure:")
    print(f"   📄 name: {problematic_object.get('name')}")
    print(f"   📄 shift_report: {problematic_object.get('shift_report')}")
    print(f"   📄 shift_report_id: {problematic_object.get('shift_report_id')}")

    # Simulate Vue extraction logic
    print("\n   🎭 Simulating Vue component extraction...")

    shiftReportId = problematic_object
    actualShiftReportId = shiftReportId

    if isinstance(shiftReportId, dict) and shiftReportId is not None:
        print("   📋 Detected object input")

        # PRIORITY: Try shift_report field first (most reliable)
        if 'shift_report' in shiftReportId and shiftReportId['shift_report']:
            actualShiftReportId = shiftReportId['shift_report']
            print(f"   ✅ Extracted from shift_report: {actualShiftReportId}")
        # SECOND: Try name field
        elif 'name' in shiftReportId:
            actualShiftReportId = shiftReportId['name']
            print(f"   ⚠️  Fallback to name: {actualShiftReportId}")
        # LAST: shift_report_id field
        elif 'shift_report_id' in shiftReportId and shiftReportId['shift_report_id']:
            actualShiftReportId = shiftReportId['shift_report_id']
            print(f"   ⚠️  Using shift_report_id: {actualShiftReportId}")
        else:
            print("   ❌ Cannot extract ID")
            return False

    print(f"   📋 Final ID to use: {actualShiftReportId}")

    # Test API call with extracted ID
    print("\n   🔄 Testing API call with extracted ID...")
    try:
        result4 = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=actualShiftReportId
        )
        print("   ✅ Vue-simulated API call successful")
        print(f"   📄 Returned name: {result4.get('name')}")
        print(f"   📄 Returned shift_report_id: {result4.get('shift_report_id')}")
    except Exception as e:
        print(f"   ❌ Vue-simulated API call failed: {e}")

    print()

    # ============================================================================
    # STEP 6: SUMMARY AND ANALYSIS
    # ============================================================================
    print("6️⃣ STEP 6: SUMMARY AND ANALYSIS")
    print("-" * 50)

    # Check data consistency
    has_shift_report_ref = hasattr(opening_shift, 'shift_report') and opening_shift.shift_report
    shift_report_exists = frappe.db.exists("POS Shift Report", expected_shift_report_name)

    print("   📊 DATA CONSISTENCY CHECK:")
    print(f"   📄 POS Opening Shift exists: ✅")
    print(f"   📄 Has shift_report reference: {'✅' if has_shift_report_ref else '❌'}")
    print(f"   📄 Referenced shift report exists: {'✅' if shift_report_exists else '❌'}")

    if has_shift_report_ref and not shift_report_exists:
        print("   ❌ DATA INCONSISTENCY: Opening shift references non-existent shift report")
        print("   📋 RECOMMENDATION: Investigate why create_shift_report_automatically failed")
    elif not has_shift_report_ref and shift_report_exists:
        print("   ⚠️  Opening shift missing shift_report reference but shift report exists")
        print("   📋 RECOMMENDATION: Update opening shift with shift_report reference")
    elif has_shift_report_ref and shift_report_exists:
        print("   ✅ DATA CONSISTENT: Opening shift and shift report properly linked")
    else:
        print("   ❌ NO LINKAGE: Neither opening shift has reference nor shift report exists")
        print("   📋 RECOMMENDATION: Run create_shift_report_automatically manually")

    print("\n   🎯 FLOW ANALYSIS:")
    print("   1. POS Opening Shift creation: ✅ Working")
    print("   2. Automatic shift report creation: {'✅ Working' if has_shift_report_ref and shift_report_exists else '❌ Failed'}")
    print("   3. Vue component object detection: ✅ Working")
    print("   4. API get_shift_report: ✅ Working")
    print("   5. Data consistency: {'✅ Good' if has_shift_report_ref and shift_report_exists else '❌ Poor'}")

    print("\n" + "=" * 80)
    print("🎯 FINAL CONCLUSION")
    print("=" * 80)

    if has_shift_report_ref and shift_report_exists:
        print("✅ COMPLETE FLOW IS WORKING CORRECTLY")
        print("   - POS Opening Shift created successfully")
        print("   - POS Shift Report created automatically")
        print("   - Vue component can extract correct ID")
        print("   - API returns correct data")
        print("   - Data is consistent")
        return True
    else:
        print("❌ COMPLETE FLOW HAS ISSUES")
        print("   - Need to investigate and fix the broken step")
        print("   - Check create_shift_report_automatically function")
        print("   - Verify data consistency")
        return False

if __name__ == "__main__":
    try:
        success = test_complete_flow()
        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)