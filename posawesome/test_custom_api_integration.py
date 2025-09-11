#!/usr/bin/env python3
"""
Test script to verify custom API integration works correctly
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

def test_custom_api_integration():
    """Test the custom get_shift_report API integration"""

    print("🧪 TESTING CUSTOM API INTEGRATION")
    print("=" * 60)

    # Test data
    test_shift_report_id = "f11lcjm94r"  # From user's example

    print(f"📋 Test Data:")
    print(f"   Shift Report ID: {test_shift_report_id}")
    print()

    # Test 1: Check if shift report exists
    print("1️⃣ Checking if shift report exists...")
    exists = frappe.db.exists("POS Shift Report", test_shift_report_id)
    print(f"   Exists: {exists}")

    if not exists:
        print("❌ Shift report does not exist - cannot test API")
        return False

    # Test 2: Call custom API
    print("\n2️⃣ Calling custom API: get_shift_report...")
    try:
        result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_shift_report_id
        )

        print("✅ API call successful")
        print(f"   Response type: {type(result)}")

        # Test 3: Check response format
        print("\n3️⃣ Checking response format...")

        if isinstance(result, dict):
            print("✅ Response is dictionary")

            # Check expected fields
            expected_fields = [
                "name", "shift_report_id", "invoice_count",
                "total_sales", "total_returns", "status"
            ]

            missing_fields = []
            for field in expected_fields:
                if field not in result:
                    missing_fields.append(field)

            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False
            else:
                print("✅ All expected fields present")

            # Test 4: Check data values
            print("\n4️⃣ Checking data values...")
            print(f"   Name: {result.get('name')}")
            print(f"   Shift Report ID: {result.get('shift_report_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Invoice Count: {result.get('invoice_count')}")
            print(f"   Total Sales: {result.get('total_sales')}")
            print(f"   Total Returns: {result.get('total_returns')}")

            # Test 5: Check invoices array
            invoices = result.get('invoices', [])
            print(f"   Invoices: {len(invoices)} items")

            if invoices:
                print("   Sample invoice:")
                sample = invoices[0]
                print(f"     Invoice No: {sample.get('invoice_no')}")
                print(f"     Amount: {sample.get('total_amount')}")
                print(f"     Status: {sample.get('status')}")

            print("\n✅ CUSTOM API INTEGRATION TEST PASSED!")
            print("🎉 Vue component should now work with custom API")

            return True

        else:
            print(f"❌ Response is not dictionary: {type(result)}")
            return False

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def compare_with_generic_api():
    """Compare custom API with generic frappe.client.get"""

    print("\n🔄 COMPARING CUSTOM VS GENERIC API")
    print("=" * 60)

    test_shift_report_id = "f11lcjm94r"

    # Test generic API
    print("📋 Generic API (frappe.client.get):")
    try:
        generic_result = frappe.get_doc("POS Shift Report", test_shift_report_id)
        print("✅ Generic API successful")
        print(f"   Name: {generic_result.name}")
        print(f"   Invoice Count: {generic_result.invoice_count}")
    except Exception as e:
        print(f"❌ Generic API failed: {e}")
        return

    # Test custom API
    print("\n📋 Custom API (get_shift_report):")
    try:
        custom_result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_shift_report_id
        )
        print("✅ Custom API successful")
        print(f"   Name: {custom_result.get('name')}")
        print(f"   Invoice Count: {custom_result.get('invoice_count')}")
    except Exception as e:
        print(f"❌ Custom API failed: {e}")
        return

    # Compare results
    print("\n⚖️ Comparison:")
    generic_name = getattr(generic_result, 'name', None)
    custom_name = custom_result.get('name')

    if generic_name == custom_name:
        print("✅ Names match")
    else:
        print(f"❌ Names don't match: Generic={generic_name}, Custom={custom_name}")

    generic_count = getattr(generic_result, 'invoice_count', 0)
    custom_count = custom_result.get('invoice_count', 0)

    if generic_count == custom_count:
        print("✅ Invoice counts match")
    else:
        print(f"❌ Invoice counts don't match: Generic={generic_count}, Custom={custom_count}")

def test_vue_component_simulation():
    """Simulate how Vue component will use the API"""

    print("\n🎭 VUE COMPONENT SIMULATION")
    print("=" * 60)

    test_shift_report_id = "f11lcjm94r"

    print("📱 Simulating Vue component API call...")

    try:
        # Simulate frappe.call from Vue
        api_result = frappe.call(
            "posawesome.posawesome.api.shift_reports.get_shift_report",
            shift_report_id=test_shift_report_id
        )

        shiftReportResponse = {
            "message": api_result
        }

        print("✅ Simulated frappe.call successful")

        # Simulate Vue component logic
        if shiftReportResponse["message"]:
            shiftReportData = shiftReportResponse["message"]

            print("✅ Vue component would extract data successfully")
            print(f"   shift_report_id: {shiftReportData.get('shift_report_id')}")
            print(f"   total_invoices: {shiftReportData.get('invoice_count')}")
            print(f"   total_revenue: {(shiftReportData.get('total_sales') or 0) - (shiftReportData.get('total_returns') or 0)}")

            # Simulate event emission
            last_invoice = ""
            invoices = shiftReportData.get('invoices', [])
            if invoices and len(invoices) > 0:
                last_invoice = invoices[-1].get('invoice_no', '')

            print(f"   last_invoice: {last_invoice}")

            print("✅ Vue component simulation successful!")
            return True
        else:
            print("❌ Vue component simulation failed - no message")
            return False

    except Exception as e:
        print(f"❌ Vue component simulation failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("🚀 STARTING CUSTOM API INTEGRATION TESTS")
        print("=" * 60)

        # Run tests
        test1_passed = test_custom_api_integration()
        compare_with_generic_api()
        test2_passed = test_vue_component_simulation()

        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        if test1_passed and test2_passed:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Custom API integration is working correctly")
            print("✅ Vue component should work with the updated API")
        else:
            print("❌ SOME TESTS FAILED!")
            print("🔧 Please check the error messages above")

        frappe.destroy()

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)