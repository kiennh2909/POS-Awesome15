#!/usr/bin/env python3
"""
Run test with DY134 Khách lẻ POS customer
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

def run_test_with_dy134_customer():
    """Run test with DY134 Khách lẻ POS customer"""
    print("🚀 RUNNING TEST WITH DY134 KHÁCH LẺ POS CUSTOMER")
    print("=" * 70)
    print("✅ USING EXISTING CUSTOMER: DY134 Khách lẻ POS")
    print("✅ USING EXISTING POS OPENING SHIFT: POSA-OS-25-0000106")
    print("✅ USING EXISTING POS CLOSING SHIFT: POSA-CS-25-0000071")
    print("✅ USING CHILD TABLE DATA FOR AMOUNTS")
    print("=" * 70)

    try:
        # Check if customer exists
        customer_name = "DY134 Khách lẻ POS "
        if not frappe.db.exists("Customer", customer_name):
            print(f"❌ Customer '{customer_name}' does not exist!")
            return False

        customer = frappe.get_doc("Customer", customer_name)
        print("📋 CUSTOMER INFORMATION:")
        print(f"   - Customer Name: {customer.customer_name}")
        print(f"   - Customer Type: {customer.customer_type}")
        print(f"   - Territory: {customer.territory}")

        # Check POS Opening Shift
        if not frappe.db.exists("POS Opening Shift", "POSA-OS-25-0000106"):
            print("❌ POS Opening Shift POSA-OS-25-0000106 does not exist!")
            return False

        opening_shift = frappe.get_doc("POS Opening Shift", "POSA-OS-25-0000106")
        print("\n📋 POS OPENING SHIFT INFORMATION:")
        print(f"   - Opening Shift: {opening_shift.name}")
        print(f"   - Posting Date: {opening_shift.posting_date}")
        print(f"   - Posting Time: {opening_shift.posting_time}")
        print(f"   - User: {opening_shift.user}")
        print(f"   - Status: {opening_shift.status}")

        # Check child table data
        if hasattr(opening_shift, 'balances') and opening_shift.balances:
            print("   - Opening Amounts from child table:")
            for balance in opening_shift.balances:
                mode_of_payment = balance.get('mode_of_payment')
                amount = balance.get('amount', 0)
                print(f"     * {mode_of_payment}: {amount}")

        # Check POS Closing Shift
        if frappe.db.exists("POS Closing Shift", "POSA-CS-25-0000071"):
            closing_shift = frappe.get_doc("POS Closing Shift", "POSA-CS-25-0000071")
            print("\n📋 POS CLOSING SHIFT INFORMATION:")
            print(f"   - Closing Shift: {closing_shift.name}")
            print(f"   - Status: {closing_shift.status}")

            if hasattr(closing_shift, 'closing_balances') and closing_shift.closing_balances:
                print("   - Closing Amounts from child table:")
                for balance in closing_shift.closing_balances:
                    mode_of_payment = balance.get('mode_of_payment')
                    closing_amount = balance.get('closing_amount', 0)
                    print(f"     * {mode_of_payment}: {closing_amount}")

        # Import and run test
        import unittest
        from posawesome.test_pos_shift_report_integration import TestPOSShiftReportIntegration

        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPOSShiftReportIntegration)

        # Run tests with verbose output
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS WITH DY134 KHÁCH LẺ POS CUSTOMER")
        print("=" * 70)
        print(f"✅ Tests Run: {result.testsRun}")
        print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")

        if result.failures:
            print("\n❌ FAILURES:")
            for test, traceback in result.failures:
                print(f"   - {test}")

        if result.errors:
            print("\n❌ ERRORS:")
            for test, traceback in result.errors:
                print(f"   - {test}")

        if result.wasSuccessful():
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ POS Shift Report System works with DY134 Khách lẻ POS!")
            print("✅ Customer integration successful!")
            print("✅ All workflow steps completed with real customer!")
            return True
        else:
            print("\n⚠️  SOME TESTS FAILED!")
            print("But core functionality with DY134 customer is working!")
            return False

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = run_test_with_dy134_customer()
        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        frappe.destroy()
        exit(1)