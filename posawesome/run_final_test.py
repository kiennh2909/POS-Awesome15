#!/usr/bin/env python3
"""
Final test runner for POS Shift Report System
Run all tests with fixes applied
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

def run_final_test():
    """Run the final integration test"""
    print("🚀 RUNNING FINAL POS SHIFT REPORT INTEGRATION TEST")
    print("=" * 60)

    try:
        # Import and run test
        import unittest
        from posawesome.test_pos_shift_report_integration import TestPOSShiftReportIntegration

        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPOSShiftReportIntegration)

        # Run tests with verbose output
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS SUMMARY")
        print("=" * 60)
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
            print("\n🎉 ALL TESTS PASSED! POS Shift Report System is working correctly!")
            print("✅ Database tables exist")
            print("✅ DocType fields correct")
            print("✅ Custom fields exist")
            print("✅ API endpoints work")
            print("✅ Business logic works")
            print("✅ Error handling works")
            return True
        else:
            print("\n❌ SOME TESTS FAILED! Check the issues above.")
            return False

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_system_status():
    """Check overall system status"""
    print("\n🔍 SYSTEM STATUS CHECK")
    print("-" * 30)

    # Check database tables
    tables = frappe.db.sql("SHOW TABLES LIKE 'tabPOS%'", as_dict=False)
    print(f"✅ Database tables: {len(tables)} found")
    for table in tables:
        print(f"   - {table[0]}")

    # Check DocTypes
    doctypes = frappe.get_all("DocType", filters={"module": "POSAwesome"})
    print(f"✅ DocTypes: {len(doctypes)} found")
    for dt in doctypes:
        print(f"   - {dt.name}")

    # Check custom fields
    custom_fields = frappe.get_all("Custom Field", filters={"dt": ["in", ["POS Opening Shift", "POS Closing Shift"]]})
    print(f"✅ Custom fields: {len(custom_fields)} found")

    # Check POS Profile
    pos_profile = frappe.db.exists("POS Profile", "POS_DY134")
    print(f"✅ POS Profile 'POS_DY134': {'Exists' if pos_profile else 'Not found'}")

if __name__ == "__main__":
    try:
        # Check system status first
        check_system_status()

        # Run final test
        success = run_final_test()

        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        frappe.destroy()
        exit(1)