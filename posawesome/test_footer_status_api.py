#!/usr/bin/env python3
"""
Test script for Footer Status API
Tests the get_footer_status_data API endpoint
"""

import frappe
from frappe import _

def test_footer_status_api():
    """Test the footer status API endpoint"""
    print("🧪 Testing Footer Status API")
    print("=" * 50)

    try:
        # Test the API call
        result = frappe.call("posawesome.posawesome.api.shift_reports.get_footer_status_data")

        print("📡 API Response:")
        print(f"   Success: {result.get('success', False)}")

        if result.get('success'):
            data = result.get('data', {})
            print("📊 Footer Data:")
            print(f"   Cashier Name: {data.get('cashier_name', 'N/A')}")
            print(f"   Current Date: {data.get('current_date', 'N/A')}")
            print(f"   Current Time: {data.get('current_time', 'N/A')}")
            print(f"   Shift Report ID: {data.get('shift_report_id', 'N/A')}")
            print(f"   Total Invoices: {data.get('total_invoices', 0)}")
            print(f"   Total Revenue: {data.get('total_revenue', 0)}")
            print(f"   Cash Balance: {data.get('cash_balance', 0)}")
            print(f"   Today Sales: {data.get('today_sales', 0)}")
            print(f"   Last Invoice: {data.get('last_invoice', 'N/A')}")

            # Check if all required fields are present
            required_fields = [
                'cashier_name', 'current_date', 'current_time',
                'shift_report_id', 'total_invoices', 'total_revenue',
                'cash_balance', 'today_sales', 'last_invoice'
            ]

            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)

            if missing_fields:
                print(f"❌ Missing fields: {', '.join(missing_fields)}")
                return False
            else:
                print("✅ All required fields are present")
                return True
        else:
            print(f"❌ API call failed: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        frappe.log_error(f"Footer Status API Test Error: {str(e)}", "Footer Status Test")
        return False

def test_footer_binding_layout():
    """Test if footer data matches the expected layout"""
    print("\n🎨 Testing Footer Layout Binding")
    print("=" * 50)

    try:
        result = frappe.call("posawesome.posawesome.api.shift_reports.get_footer_status_data")

        if result.get('success'):
            data = result.get('data', {})

            # Expected layout format
            expected_layout = "📅 {date} │ 🕐 {time} │ 🟢 {cashier} │ 💰 Cash: ${cash} │ 🧾 Last Invoice: {invoice} │ 📊 Today: ${sales}"

            formatted_layout = expected_layout.format(
                date=data.get('current_date', 'N/A'),
                time=data.get('current_time', 'N/A'),
                cashier=data.get('cashier_name', 'N/A'),
                cash=data.get('cash_balance', 0),
                invoice=data.get('last_invoice', 'N/A'),
                sales=data.get('today_sales', 0)
            )

            print("📋 Expected Footer Layout:")
            print(f"   {formatted_layout}")

            # Check if all data is available
            has_date = bool(data.get('current_date'))
            has_time = bool(data.get('current_time'))
            has_cashier = bool(data.get('cashier_name'))
            has_cash = data.get('cash_balance') is not None
            has_invoice = data.get('last_invoice') is not None
            has_sales = data.get('today_sales') is not None

            print("\n🔍 Data Availability:")
            print(f"   Date: {'✅' if has_date else '❌'}")
            print(f"   Time: {'✅' if has_time else '❌'}")
            print(f"   Cashier: {'✅' if has_cashier else '❌'}")
            print(f"   Cash Balance: {'✅' if has_cash else '❌'}")
            print(f"   Last Invoice: {'✅' if has_invoice else '❌'}")
            print(f"   Today Sales: {'✅' if has_sales else '❌'}")

            all_available = all([has_date, has_time, has_cashier, has_cash, has_invoice, has_sales])

            if all_available:
                print("✅ All footer data is available for binding")
                return True
            else:
                print("❌ Some footer data is missing")
                return False
        else:
            print("❌ Cannot test layout binding - API failed")
            return False

    except Exception as e:
        print(f"💥 Exception in layout test: {str(e)}")
        return False

    # This should not be reached, but just in case
    return False

if __name__ == "__main__":
    print("🚀 Footer Status API Test Suite")
    print("=" * 60)

    # Test API functionality
    api_test = test_footer_status_api()

    # Test layout binding
    layout_test = test_footer_binding_layout()

    # Overall result
    print("\n" + "=" * 60)
    if api_test and layout_test:
        print("🎉 ALL TESTS PASSED - Footer Status API is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please check the implementation")

    print("=" * 60)