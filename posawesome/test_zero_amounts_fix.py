#!/usr/bin/env python3
"""
Test script to verify the fix for zero amounts in shift report creation
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

def test_zero_amounts_fix():
    """Test the fix for zero amounts in shift report creation"""

    print("🧪 TESTING ZERO AMOUNTS FIX")
    print("=" * 60)

    # Test data - simulate zero amounts scenario
    opening_shift_name = "POSA-OS-25-0000112"
    zero_balance_details = [
        {"mode_of_payment": "Cash", "amount": 0},
        {"mode_of_payment": "Card", "amount": 0}
    ]

    print("📋 Test Data:")
    print(f"   POS Opening Shift: {opening_shift_name}")
    print(f"   Balance Details: {zero_balance_details}")
    print()

    # Import the function
    from posawesome.posawesome.api.shifts import create_shift_report_automatically

    print("1️⃣ Testing create_shift_report_automatically with zero amounts...")
    print("-" * 50)

    try:
        result = create_shift_report_automatically(opening_shift_name, zero_balance_details)
        print("✅ Function executed successfully")
        print(f"   📄 Result: {result}")

        if result.get("status") == "created":
            print("   ✅ Shift report created with zero amounts!")
            print(f"   📄 Name: {result.get('name')}")
            print(f"   📄 shift_report_id: {result.get('shift_report_id')}")
            print(f"   📄 opening_amounts: {result.get('opening_amounts')}")
            print(f"   📄 total_opening_amount: {result.get('total_opening_amount')}")

            # Verify the shift report was created correctly
            if result.get('opening_amounts') == {"Cash": 0}:
                print("   ✅ Default zero amounts applied correctly")
            else:
                print(f"   ❌ Unexpected opening_amounts: {result.get('opening_amounts')}")

            if result.get('total_opening_amount') == 0:
                print("   ✅ Total opening amount is 0 as expected")
            else:
                print(f"   ❌ Unexpected total_opening_amount: {result.get('total_opening_amount')}")

        elif result.get("status") == "existing":
            print("   ✅ Existing shift report found")
            print(f"   📄 Existing name: {result.get('name')}")
        elif result.get("status") == "error":
            print("   ❌ Function returned error")
            print(f"   📄 Error message: {result.get('message')}")
            return False

    except Exception as e:
        print(f"   ❌ Function threw exception: {e}")
        return False

    print()

    # Test 2: Test with empty balance details
    print("2️⃣ Testing with empty balance details...")
    print("-" * 50)

    try:
        result2 = create_shift_report_automatically(opening_shift_name, [])
        print("✅ Function executed with empty balance details")
        print(f"   📄 Result: {result2}")

        if result2.get("status") == "error" and "No balance details provided" in result2.get("message", ""):
            print("   ✅ Correctly rejected empty balance details")
        else:
            print("   ❌ Unexpected result for empty balance details")

    except Exception as e:
        print(f"   ❌ Function threw exception with empty balance details: {e}")

    print()

    # Test 3: Test with invalid balance details format
    print("3️⃣ Testing with invalid balance details format...")
    print("-" * 50)

    invalid_balance_details = [
        {"mode_of_payment": "Cash", "amount": "invalid"},
        {"mode_of_payment": "", "amount": 100},  # Missing mode_of_payment
        {"invalid": "format"}  # Invalid format
    ]

    try:
        result3 = create_shift_report_automatically(opening_shift_name, invalid_balance_details)
        print("✅ Function handled invalid balance details")
        print(f"   📄 Result: {result3}")

        if result3.get("status") == "created":
            print("   ✅ Shift report created despite invalid details")
            print(f"   📄 opening_amounts: {result3.get('opening_amounts')}")
        elif result3.get("status") == "existing":
            print("   ✅ Existing shift report found")
        else:
            print("   ❌ Unexpected result for invalid balance details")

    except Exception as e:
        print(f"   ❌ Function threw exception with invalid balance details: {e}")

    print()

    # Test 4: Verify POS Opening Shift update
    print("4️⃣ Verifying POS Opening Shift update...")
    print("-" * 50)

    if result.get("status") == "created":
        try:
            # Check if opening shift was updated
            opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
            shift_report_ref = getattr(opening_shift, 'shift_report', None)
            shift_report_id_ref = getattr(opening_shift, 'shift_report_id', None)

            print(f"   📄 Opening shift shift_report: {shift_report_ref}")
            print(f"   📄 Opening shift shift_report_id: {shift_report_id_ref}")

            if shift_report_ref == result.get('name'):
                print("   ✅ Opening shift updated with correct shift_report reference")
            else:
                print("   ❌ Opening shift shift_report reference not updated correctly")

            if shift_report_id_ref == result.get('shift_report_id'):
                print("   ✅ Opening shift updated with correct shift_report_id reference")
            else:
                print("   ❌ Opening shift shift_report_id reference not updated correctly")

        except Exception as e:
            print(f"   ❌ Error checking opening shift update: {e}")

    print()

    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 60)

    success_count = 0
    total_tests = 4

    # Test 1: Zero amounts
    if result.get("status") in ["created", "existing"]:
        print("✅ Test 1 (Zero amounts): PASSED")
        success_count += 1
    else:
        print("❌ Test 1 (Zero amounts): FAILED")

    # Test 2: Empty balance details
    if result2.get("status") == "error" and "No balance details provided" in result2.get("message", ""):
        print("✅ Test 2 (Empty balance): PASSED")
        success_count += 1
    else:
        print("❌ Test 2 (Empty balance): FAILED")

    # Test 3: Invalid balance details
    if result3.get("status") in ["created", "existing"]:
        print("✅ Test 3 (Invalid balance): PASSED")
        success_count += 1
    else:
        print("❌ Test 3 (Invalid balance): FAILED")

    # Test 4: Opening shift update
    if result.get("status") == "created":
        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        if (getattr(opening_shift, 'shift_report', None) == result.get('name') and
            getattr(opening_shift, 'shift_report_id', None) == result.get('shift_report_id')):
            print("✅ Test 4 (Opening shift update): PASSED")
            success_count += 1
        else:
            print("❌ Test 4 (Opening shift update): FAILED")
    else:
        print("⚠️  Test 4 (Opening shift update): SKIPPED (no new shift report created)")

    print(f"\n🎯 OVERALL RESULT: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! Zero amounts fix is working correctly.")
        return True
    else:
        print("❌ SOME TESTS FAILED. Please check the implementation.")
        return False

if __name__ == "__main__":
    try:
        success = test_zero_amounts_fix()
        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)