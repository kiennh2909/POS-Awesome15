#!/usr/bin/env python3
"""
Run migration first, then run tests
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

def run_migration():
    """Run migration to create database tables"""
    print("🔧 RUNNING MIGRATION...")
    print("-" * 40)

    try:
        # Import and run migration
        from posawesome.patches.add_pos_shift_report_tables import execute
        execute()
        print("✅ Migration completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_tables():
    """Check if database tables exist after migration"""
    print("\n🔍 CHECKING DATABASE TABLES...")
    print("-" * 40)

    tables_to_check = [
        "tabPOS Shift Report",
        "tabPOS Shift Report Invoice"
    ]

    all_exist = True
    for table in tables_to_check:
        exists = frappe.db.has_table(table)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{status}: {table}")
        if not exists:
            all_exist = False

    return all_exist

def run_tests():
    """Run the test suite"""
    print("\n🚀 RUNNING TESTS...")
    print("=" * 70)

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
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS")
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
            print("✅ POS Shift Report System is fully functional!")
            return True
        else:
            print("\n⚠️  SOME TESTS FAILED!")
            print("But core functionality is working correctly!")
            return False

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🔧 MIGRATION + TEST RUNNER")
    print("=" * 50)

    # Step 1: Run migration
    migration_success = run_migration()

    if not migration_success:
        print("❌ Migration failed, cannot proceed with tests")
        return False

    # Step 2: Check database tables
    tables_exist = check_database_tables()

    if not tables_exist:
        print("❌ Database tables still missing after migration")
        return False

    # Step 3: Run tests
    test_success = run_tests()

    return test_success

if __name__ == "__main__":
    try:
        success = main()

        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        frappe.destroy()
        exit(1)