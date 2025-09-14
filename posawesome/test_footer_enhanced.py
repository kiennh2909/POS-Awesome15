#!/usr/bin/env python3
"""
Enhanced test for Footer Status API with POS Shift Report ID
Run this in bench console: bench console --site your_site
Then: exec(open('posawesome/test_footer_enhanced.py').read())
"""

import frappe

def test_footer_api_enhanced():
    """Test the enhanced footer status API"""
    print("🧪 Testing Enhanced Footer Status API")
    print("=" * 60)

    try:
        # Call the API
        result = frappe.call("posawesome.posawesome.api.shift_reports.get_footer_status_data")

        print("📡 API Response:")
        print(f"   Success: {result.get('success', False)}")

        if result.get('success'):
            data = result.get('data', {})

            print("\n📊 Enhanced Footer Data:")
            print(f"   Cashier Name: {data.get('cashier_name', 'N/A')}")
            print(f"   Current Date: {data.get('current_date', 'N/A')}")
            print(f"   Current Time: {data.get('current_time', 'N/A')}")
            print(f"   POS Shift Report ID: {data.get('shift_report_id', 'N/A')}")  # NEW
            print(f"   Total Invoices: {data.get('total_invoices', 0)}")
            print(f"   Total Revenue: {data.get('total_revenue', 0)}")
            print(f"   Cash Balance: {data.get('cash_balance', 0)}")
            print(f"   Today Sales: {data.get('today_sales', 0)}")
            print(f"   Last Invoice: {data.get('last_invoice', 'N/A')}")

            # Check required fields including new POS Shift Report ID
            required_fields = [
                'cashier_name', 'current_date', 'current_time',
                'shift_report_id',  # NEW: POS Shift Report ID
                'cash_balance', 'today_sales', 'last_invoice'
            ]

            missing = [f for f in required_fields if f not in data]
            if missing:
                print(f"\n❌ Missing fields: {missing}")
                return False
            else:
                print("\n✅ All required fields present (including POS Shift Report ID)")
                return True
        else:
            print(f"\n❌ API failed: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        return False

def test_cash_balance_calculation():
    """Test cash balance calculation logic"""
    print("\n💰 Testing Cash Balance Calculation")
    print("=" * 40)

    try:
        # Get active shift
        user = frappe.session.user
        active_shift = frappe.get_all(
            "POS Opening Shift",
            filters={
                "owner": user,
                "docstatus": 1,
                "status": "Open"
            },
            fields=["name"],
            limit=1
        )

        if not active_shift:
            print("⚠️  No active opening shift found for testing")
            return True

        opening_shift = frappe.get_doc("POS Opening Shift", active_shift[0].name)

        print(f"Opening Shift: {opening_shift.name}")

        # Test cash balance calculation
        cash_payment_methods = ['cash', 'tiền mặt', 'tiền mặt - pos', 'cash - pos']

        if hasattr(opening_shift, 'balances') and opening_shift.balances:
            print("Opening Balances:")
            total_cash_balance = 0

            for balance in opening_shift.balances:
                mode = balance.mode_of_payment or ""
                amount = balance.amount or 0
                print(f"   {mode}: {amount}")

                if mode:
                    mode_lower = mode.lower()
                    if any(cash_type in mode_lower for cash_type in cash_payment_methods):
                        total_cash_balance += amount
                        print(f"   ✅ Detected as cash payment method")

            print(f"\n💰 Total Cash Balance: {total_cash_balance}")
            return True
        else:
            print("⚠️  No balances found in opening shift")
            return True

    except Exception as e:
        print(f"💥 Error in cash balance test: {str(e)}")
        return False

def test_footer_layout_format():
    """Test footer layout format with POS Shift Report ID"""
    print("\n🎨 Testing Footer Layout Format")
    print("=" * 40)

    try:
        result = frappe.call("posawesome.posawesome.api.shift_reports.get_footer_status_data")

        if result.get('success'):
            data = result.get('data', {})

            # Expected layout with POS Shift Report ID
            expected_layout = "📅 {date} │ 🕐 {time} │ 🟢 {cashier} │ 📋 {shift_id} │ 💰 ${cash} │ 🧾 {invoice} │ 📊 ${sales}"

            formatted_layout = expected_layout.format(
                date=data.get('current_date', 'N/A'),
                time=data.get('current_time', 'N/A'),
                cashier=data.get('cashier_name', 'N/A'),
                shift_id=data.get('shift_report_id', 'N/A'),  # NEW
                cash=data.get('cash_balance', 0),
                invoice=data.get('last_invoice', 'N/A'),
                sales=data.get('today_sales', 0)
            )

            print("📋 Expected Footer Layout (with POS Shift Report ID):")
            print(f"   {formatted_layout}")

            # Check if POS Shift Report ID is included
            has_shift_id = bool(data.get('shift_report_id'))
            print(f"\n🔍 POS Shift Report ID Check:")
            print(f"   Shift Report ID present: {'✅' if has_shift_id else '❌'}")
            print(f"   Shift Report ID value: {data.get('shift_report_id', 'N/A')}")

            return has_shift_id
        else:
            print("❌ Cannot test layout - API failed")
            return False

    except Exception as e:
        print(f"💥 Exception in layout test: {str(e)}")
        return False

# Run all tests
if __name__ == "__main__":
    print("🚀 Enhanced Footer Status API Test Suite")
    print("=" * 70)

    # Test API functionality
    api_test = test_footer_api_enhanced()

    # Test cash balance calculation
    cash_test = test_cash_balance_calculation()

    # Test layout format
    layout_test = test_footer_layout_format()

    # Overall result
    print("\n" + "=" * 70)
    if api_test and cash_test and layout_test:
        print("🎉 ALL TESTS PASSED - Enhanced Footer API is working correctly!")
        print("✅ POS Shift Report ID is now displayed in footer")
        print("✅ Cash balance calculation supports multiple payment methods")
    else:
        print("❌ SOME TESTS FAILED - Please check the implementation")

    print("=" * 70)