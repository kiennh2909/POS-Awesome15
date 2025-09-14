#!/usr/bin/env python3
"""
Test script to verify the fix for POS Opening Shift object parsing
Run this in bench console: exec(open('posawesome/test_fix_verification.py').read())
"""

import frappe
import json

def test_opening_shift_parsing():
    """Test parsing of POS Opening Shift object"""

    print("🧪 TESTING POS OPENING SHIFT OBJECT PARSING")
    print("=" * 50)

    try:
        # Get a sample POS Opening Shift
        opening_shifts = frappe.get_all("POS Opening Shift",
            filters={"docstatus": 1, "status": "Open"},
            fields=["name", "shift_report", "shift_report_id"],
            limit=1
        )

        if not opening_shifts:
            print("❌ No active opening shifts found")
            return

        opening_shift = opening_shifts[0]
        print(f"📋 Sample Opening Shift: {opening_shift}")

        # Get full opening shift object
        full_opening_shift = frappe.get_doc("POS Opening Shift", opening_shift.name)
        opening_shift_dict = full_opening_shift.as_dict()

        print(f"📊 Opening Shift has shift_report: {opening_shift_dict.get('shift_report')}")
        print(f"📊 Opening Shift has shift_report_id: {opening_shift_dict.get('shift_report_id')}")

        # Test 1: Opening shift without shift report
        print("\n1️⃣ Testing Opening Shift without shift report...")
        test_obj_1 = opening_shift_dict.copy()
        test_obj_1['shift_report'] = None
        test_obj_1['shift_report_id'] = None

        json_str_1 = json.dumps(test_obj_1)
        try:
            result1 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {"shift_report_id": json_str_1}
            })
            print("   ❌ Should have failed but succeeded")
        except Exception as e:
            if "No shift report found for this opening shift" in str(e):
                print("   ✅ Correctly handled: No shift report found")
            else:
                print(f"   ⚠️ Unexpected error: {str(e)}")

        # Test 2: Opening shift with shift report
        if opening_shift.shift_report:
            print("\n2️⃣ Testing Opening Shift with shift report...")

            # Make sure shift_report field is set
            test_obj_2 = opening_shift_dict.copy()
            test_obj_2['shift_report'] = opening_shift.shift_report

            json_str_2 = json.dumps(test_obj_2)
            try:
                result2 = frappe.call({
                    "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                    "args": {"shift_report_id": json_str_2}
                })
                print("   ✅ Successfully parsed opening shift with shift report")
            except Exception as e:
                print(f"   ❌ Failed to parse opening shift with shift report: {str(e)}")

        # Test 3: Direct shift report object
        if opening_shift.shift_report:
            print("\n3️⃣ Testing Direct Shift Report object...")

            shift_report = frappe.get_doc("POS Shift Report", opening_shift.shift_report)
            shift_report_dict = shift_report.as_dict()

            json_str_3 = json.dumps(shift_report_dict)
            try:
                result3 = frappe.call({
                    "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                    "args": {"shift_report_id": json_str_3}
                })
                print("   ✅ Successfully parsed direct shift report object")
            except Exception as e:
                print(f"   ❌ Failed to parse direct shift report object: {str(e)}")

        # Test 4: Unknown object type
        print("\n4️⃣ Testing Unknown object type...")
        unknown_obj = {
            "doctype": "Unknown DocType",
            "name": "TEST-123",
            "some_field": "test_value"
        }

        json_str_4 = json.dumps(unknown_obj)
        try:
            result4 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {"shift_report_id": json_str_4}
            })
            print("   ✅ Successfully parsed unknown object type")
        except Exception as e:
            print(f"   ❌ Failed to parse unknown object type: {str(e)}")

    except Exception as e:
        print(f"💥 TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

def simulate_vue_component():
    """Simulate what Vue component should send"""

    print("\n🎭 SIMULATING VUE COMPONENT BEHAVIOR")
    print("=" * 40)

    try:
        # Get sample data
        opening_shifts = frappe.get_all("POS Opening Shift",
            filters={"docstatus": 1},
            fields=["name", "shift_report"],
            limit=1
        )

        if not opening_shifts:
            print("❌ No opening shifts found")
            return

        opening_shift = opening_shifts[0]

        # Simulate Vue component sending opening shift object
        print("📤 Vue Component sends: POS Opening Shift object")

        opening_shift_doc = frappe.get_doc("POS Opening Shift", opening_shift.name)
        vue_payload = opening_shift_doc.as_dict()

        print(f"📊 Payload doctype: {vue_payload.get('doctype')}")
        print(f"📊 Payload has shift_report: {vue_payload.get('shift_report')}")
        print(f"📊 Payload name: {vue_payload.get('name')}")

        # Test the API call
        json_payload = json.dumps(vue_payload)
        try:
            result = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {"shift_report_id": json_payload}
            })
            print("🎉 SUCCESS: Vue component simulation worked!")
            print(f"📊 Result has payment_summaries: {'payment_summaries' in result}")
            if 'payment_summaries' in result:
                print(f"📊 Number of payment summaries: {len(result['payment_summaries'])}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")

    except Exception as e:
        print(f"💥 SIMULATION FAILED: {str(e)}")

# Main execution
if __name__ == "__main__":
    test_opening_shift_parsing()
    simulate_vue_component()

    print("\n" + "=" * 50)
    print("🎯 VERIFICATION COMPLETE")
    print("If all tests pass, the fix is working correctly!")