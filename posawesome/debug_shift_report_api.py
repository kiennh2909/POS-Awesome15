#!/usr/bin/env python3
"""
Debug script for POS Shift Report API
Run this in bench console: exec(open('posawesome/debug_shift_report_api.py').read())
"""

import frappe
import json

def debug_shift_report_api():
    """Debug the shift report API to identify parsing issues"""

    print("🔍 DEBUGGING SHIFT REPORT API")
    print("=" * 50)

    try:
        # Test 1: Check if DocType exists
        print("\n1️⃣ Checking DocType...")
        doctype_exists = frappe.db.exists("DocType", "POS Shift Report")
        print(f"   POS Shift Report DocType: {'✅' if doctype_exists else '❌'}")

        # Test 2: Get sample shift report
        print("\n2️⃣ Getting sample shift report...")
        sample_reports = frappe.get_all("POS Shift Report",
            fields=["name", "shift_report_id"],
            limit=1
        )

        if not sample_reports:
            print("   ❌ No shift reports found")
            return

        sample_report = sample_reports[0]
        print(f"   Sample report: {sample_report}")

        # Test 3: Test API with different input formats
        print("\n3️⃣ Testing API with different formats...")

        # Format 1: Direct name
        print("   Testing with direct name...")
        try:
            result1 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": sample_report.name
                }
            })
            print("   ✅ Direct name: SUCCESS")
        except Exception as e:
            print(f"   ❌ Direct name: {str(e)}")

        # Format 2: shift_report_id field
        print("   Testing with shift_report_id field...")
        try:
            result2 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": sample_report.shift_report_id
                }
            })
            print("   ✅ shift_report_id: SUCCESS")
        except Exception as e:
            print(f"   ❌ shift_report_id: {str(e)}")

        # Format 3: JSON object with shift_report
        print("   Testing with JSON object (shift_report)...")
        try:
            json_obj = json.dumps({
                "shift_report": sample_report.name,
                "shift_report_id": sample_report.shift_report_id
            })
            result3 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": json_obj
                }
            })
            print("   ✅ JSON object (shift_report): SUCCESS")
        except Exception as e:
            print(f"   ❌ JSON object (shift_report): {str(e)}")

        # Format 4: JSON object with only shift_report_id
        print("   Testing with JSON object (shift_report_id only)...")
        try:
            json_obj = json.dumps({
                "shift_report_id": sample_report.shift_report_id
            })
            result4 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": json_obj
                }
            })
            print("   ✅ JSON object (shift_report_id only): SUCCESS")
        except Exception as e:
            print(f"   ❌ JSON object (shift_report_id only): {str(e)}")

        # Format 5: JSON object with unknown field
        print("   Testing with JSON object (unknown field)...")
        try:
            json_obj = json.dumps({
                "some_field": sample_report.name,
                "another_field": "test"
            })
            result5 = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": json_obj
                }
            })
            print("   ✅ JSON object (unknown field): SUCCESS")
        except Exception as e:
            print(f"   ❌ JSON object (unknown field): {str(e)}")

        # Test 4: Check payment summary creation
        print("\n4️⃣ Testing payment summary creation...")
        try:
            from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
            payment_result = create_payment_summaries_for_shift(sample_report.name)
            print(f"   Payment summary creation: {'✅' if payment_result.get('success') else '❌'}")
            if not payment_result.get('success'):
                print(f"   Error: {payment_result.get('message')}")
        except Exception as e:
            print(f"   ❌ Payment summary creation failed: {str(e)}")

        # Test 5: Check if payment summaries exist
        print("\n5️⃣ Checking payment summaries...")
        payment_summaries = frappe.get_all("POS Payment Summary",
            filters={"pos_shift_report": sample_report.name},
            fields=["name", "payment_method", "opening_amount", "transaction_amount"]
        )
        print(f"   Payment summaries found: {len(payment_summaries)}")
        if payment_summaries:
            print("   Sample payment summary:")
            print(f"     - {payment_summaries[0]}")

    except Exception as e:
        print(f"💥 DEBUG FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

def test_vue_component_simulation():
    """Simulate what Vue component might send"""

    print("\n🎭 SIMULATING VUE COMPONENT INPUTS")
    print("=" * 40)

    # Get sample data
    sample_reports = frappe.get_all("POS Shift Report",
        fields=["name", "shift_report_id"],
        limit=1
    )

    if not sample_reports:
        print("❌ No sample data available")
        return

    sample = sample_reports[0]

    # Test different object formats that Vue might send
    test_objects = [
        {
            "name": "Object with shift_report",
            "data": {"shift_report": sample.name}
        },
        {
            "name": "Object with shift_report_id",
            "data": {"shift_report_id": sample.shift_report_id}
        },
        {
            "name": "Object with name field",
            "data": {"name": sample.name}
        },
        {
            "name": "Object with random string field",
            "data": {"random_id": sample.name, "other": "value"}
        },
        {
            "name": "Object with multiple string fields",
            "data": {"id": sample.name, "code": sample.shift_report_id, "type": "shift"}
        }
    ]

    for test_case in test_objects:
        print(f"\n🧪 Testing: {test_case['name']}")
        try:
            json_str = json.dumps(test_case['data'])
            result = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": json_str
                }
            })
            print("   ✅ SUCCESS")
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")

# Main execution
if __name__ == "__main__":
    debug_shift_report_api()
    test_vue_component_simulation()

    print("\n" + "=" * 50)
    print("🎯 DEBUG COMPLETE")
    print("Check the output above to identify the issue")