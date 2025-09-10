#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for POS Shift Report System
Tests database integrity, API functionality, and business logic
"""

import os
import sys
import json
import unittest
from datetime import datetime, date, time

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

class TestPOSShiftReportIntegration(unittest.TestCase):
    """Comprehensive integration tests for POS Shift Report System"""

    def setUp(self):
        """Set up test environment"""
        self.test_user = "test@example.com"
        self.test_customer = "Test Customer"
        self.test_pos_profile = "Test POS Profile"

        # Clean up any existing test data
        self.cleanup_test_data()

    def tearDown(self):
        """Clean up after tests"""
        self.cleanup_test_data()

    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Delete test shift reports
            test_reports = frappe.get_all("POS Shift Report",
                filters={"shift_report_id": ["like", "TEST-%"]})
            for report in test_reports:
                frappe.delete_doc("POS Shift Report", report.name, force=True)

            # Delete test opening shifts
            test_shifts = frappe.get_all("POS Opening Shift",
                filters={"name": ["like", "TEST-%"]})
            for shift in test_shifts:
                frappe.delete_doc("POS Opening Shift", shift.name, force=True)

            frappe.db.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def test_01_database_tables_exist(self):
        """Test that all required database tables exist"""
        print("🔍 Testing Database Tables...")

        # Test main DocTypes exist
        doctypes_to_check = [
            "POS Shift Report",
            "POS Shift Report Invoice"
        ]

        for doctype in doctypes_to_check:
            with self.subTest(doctype=doctype):
                self.assertTrue(frappe.db.exists("DocType", doctype),
                    f"DocType {doctype} does not exist")

                # ✅ FIX: Use correct table name with spaces
                # Frappe creates tables with spaces: "tabPOS Shift Report"
                table_name = f"tab{doctype}"
                self.assertTrue(frappe.db.has_table(table_name),
                    f"Table {table_name} does not exist")

        print("✅ All database tables exist")

    def test_02_doctypes_have_correct_fields(self):
        """Test that DocTypes have all required fields"""
        print("🔍 Testing DocType Fields...")

        # Test POS Shift Report fields
        shift_report_meta = frappe.get_meta("POS Shift Report")
        required_fields = [
            "shift_report_id", "pos_opening_shift", "opening_date", "opening_time",
            "opened_by", "opening_amounts", "total_opening_amount", "status",
            "verification_status", "invoices"
        ]

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIsNotNone(shift_report_meta.get_field(field),
                    f"Field {field} missing in POS Shift Report")

        # Test POS Shift Report Invoice fields
        invoice_meta = frappe.get_meta("POS Shift Report Invoice")
        invoice_fields = [
            "invoice_no", "invoice_date", "invoice_time", "customer",
            "total_amount", "paid_amount", "status"
        ]

        for field in invoice_fields:
            with self.subTest(field=field):
                self.assertIsNotNone(invoice_meta.get_field(field),
                    f"Field {field} missing in POS Shift Report Invoice")

        print("✅ All required fields exist")

    def test_03_custom_fields_exist(self):
        """Test that custom fields are properly created"""
        print("🔍 Testing Custom Fields...")

        custom_fields_to_check = [
            ("POS Opening Shift", "shift_report_id"),
            ("POS Opening Shift", "shift_report"),
            ("POS Closing Shift", "shift_report"),
            ("POS Closing Shift", "expected_amounts"),
            ("POS Closing Shift", "actual_amounts"),
            ("POS Closing Shift", "difference_amounts"),
            ("POS Closing Shift", "verification_status"),
            ("Sales Invoice", "pos_shift_report"),
            ("Sales Invoice", "shift_report_id")
        ]

        for doctype, fieldname in custom_fields_to_check:
            with self.subTest(doctype=doctype, fieldname=fieldname):
                custom_field = frappe.get_all("Custom Field",
                    filters={"dt": doctype, "fieldname": fieldname})
                self.assertTrue(len(custom_field) > 0,
                    f"Custom field {fieldname} missing in {doctype}")

        print("✅ All custom fields exist")

    def test_04_create_shift_report(self):
        """Test creating a new shift report"""
        print("🔍 Testing Shift Report Creation...")

        # Create test opening shift first
        opening_shift = frappe.get_doc({
            "doctype": "POS Opening Shift",
            "posting_date": date.today(),
            "posting_time": time(9, 0, 0),
            "pos_profile": self.test_pos_profile,
            "status": "Open"
        })
        opening_shift.insert()
        opening_shift.submit()
        frappe.db.commit()

        # Create shift report
        shift_report = frappe.get_doc({
            "doctype": "POS Shift Report",
            "shift_report_id": "TEST-SHIFT-001",
            "pos_opening_shift": opening_shift.name,
            "opening_date": date.today(),
            "opening_time": time(9, 0, 0),
            "opened_by": self.test_user,
            "opening_amounts": json.dumps({"Cash": 1000, "Card": 500}),
            "total_opening_amount": 1500,
            "status": "Open",
            "verification_status": "Pending"
        })

        shift_report.insert()
        shift_report.submit()
        frappe.db.commit()

        # Verify creation
        self.assertIsNotNone(shift_report.name)
        self.assertEqual(shift_report.shift_report_id, "TEST-SHIFT-001")
        self.assertEqual(shift_report.status, "Submitted")

        # Clean up
        frappe.delete_doc("POS Shift Report", shift_report.name, force=True)
        frappe.delete_doc("POS Opening Shift", opening_shift.name, force=True)
        frappe.db.commit()

        print("✅ Shift report creation works")

    def test_05_api_endpoints_work(self):
        """Test that all API endpoints work correctly"""
        print("🔍 Testing API Endpoints...")

        # Test shift reports API
        try:
            result = frappe.call("posawesome.posawesome.api.shift_reports.get_shift_reports")
            # API returns dict with success/data format
            self.assertIsInstance(result, dict)
            self.assertIn("data", result)
        except Exception as e:
            self.fail(f"get_shift_reports API failed: {e}")

        # Test shift verification API
        try:
            result = frappe.call("posawesome.posawesome.api.shift_verification.get_pending_verifications")
            self.assertIsInstance(result, list)
        except Exception as e:
            self.fail(f"get_pending_verifications API failed: {e}")

        # Test calculations API
        try:
            result = frappe.call("posawesome.posawesome.api.shift_calculations.calculate_expected_amounts",
                opening_amounts={"Cash": 1000}, sales_amount=500, returns_amount=50)
            self.assertIsInstance(result, dict)
            self.assertIn("expected_total", result)
        except Exception as e:
            self.fail(f"calculate_expected_amounts API failed: {e}")

        print("✅ All API endpoints work")

    def test_06_business_logic_calculations(self):
        """Test business logic calculations"""
        print("🔍 Testing Business Logic Calculations...")

        from posawesome.posawesome.api.shift_calculations import (
            calculate_expected_amounts,
            calculate_difference,
            validate_amounts
        )

        # Test expected amounts calculation
        opening = {"Cash": 1000, "Card": 500}
        sales = 750
        returns = 50

        expected = calculate_expected_amounts(opening, sales, returns)
        self.assertEqual(expected["expected_total"], 1200)  # 1000 + 500 + 750 - 50

        # Test difference calculation
        actual = {"Cash": 1100, "Card": 400}
        difference = calculate_difference(expected["breakdown"], actual)
        self.assertEqual(difference["total_difference"], -200)  # 1200 - (1100 + 400)

        # Test validation
        is_valid = validate_amounts(actual)
        self.assertTrue(is_valid)

        print("✅ Business logic calculations work")

    def test_07_workflow_transitions(self):
        """Test workflow state transitions"""
        print("🔍 Testing Workflow Transitions...")

        # Create test shift report
        shift_report = frappe.get_doc({
            "doctype": "POS Shift Report",
            "shift_report_id": "TEST-WORKFLOW-001",
            "pos_opening_shift": "TEST-OPEN-001",
            "opening_date": date.today(),
            "opening_time": time(9, 0, 0),
            "opened_by": self.test_user,
            "opening_amounts": json.dumps({"Cash": 1000}),
            "total_opening_amount": 1000,
            "status": "Open",
            "verification_status": "Pending"
        })
        shift_report.insert()
        frappe.db.commit()

        # Test status transitions
        initial_status = shift_report.verification_status
        self.assertEqual(initial_status, "Pending")

        # Update to Verified
        shift_report.verification_status = "Verified"
        shift_report.verification_date = date.today()
        shift_report.verified_by = self.test_user
        shift_report.save()
        frappe.db.commit()

        # Verify transition
        updated = frappe.get_doc("POS Shift Report", shift_report.name)
        self.assertEqual(updated.verification_status, "Verified")
        self.assertIsNotNone(updated.verification_date)

        # Clean up
        frappe.delete_doc("POS Shift Report", shift_report.name, force=True)
        frappe.db.commit()

        print("✅ Workflow transitions work")

    def test_08_data_integrity_constraints(self):
        """Test data integrity constraints"""
        print("🔍 Testing Data Integrity...")

        # Test unique constraint on shift_report_id
        shift_report1 = frappe.get_doc({
            "doctype": "POS Shift Report",
            "shift_report_id": "TEST-UNIQUE-001",
            "pos_opening_shift": "TEST-OPEN-001",
            "opening_date": date.today(),
            "opening_time": time(9, 0, 0),
            "opened_by": self.test_user,
            "opening_amounts": json.dumps({"Cash": 1000}),
            "total_opening_amount": 1000,
            "status": "Open"
        })
        shift_report1.insert()
        frappe.db.commit()

        # Try to create duplicate shift_report_id
        shift_report2 = frappe.get_doc({
            "doctype": "POS Shift Report",
            "shift_report_id": "TEST-UNIQUE-001",  # Same ID
            "pos_opening_shift": "TEST-OPEN-002",
            "opening_date": date.today(),
            "opening_time": time(10, 0, 0),
            "opened_by": self.test_user,
            "opening_amounts": json.dumps({"Cash": 1000}),
            "total_opening_amount": 1000,
            "status": "Open"
        })

        with self.assertRaises(Exception):
            shift_report2.insert()

        # Clean up
        frappe.delete_doc("POS Shift Report", shift_report1.name, force=True)
        frappe.db.commit()

        print("✅ Data integrity constraints work")

    def test_09_performance_basic(self):
        """Test basic performance metrics"""
        print("🔍 Testing Basic Performance...")

        import time

        # Test API response time
        start_time = time.time()
        result = frappe.call("posawesome.posawesome.api.shift_reports.get_shift_reports")
        end_time = time.time()

        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, "API response too slow")

        # Test database query performance
        start_time = time.time()
        count = frappe.db.count("POS Shift Report")
        end_time = time.time()

        query_time = end_time - start_time
        self.assertLess(query_time, 0.5, "Database query too slow")

        print(".2f")
        print(".3f")

    def test_10_error_handling(self):
        """Test error handling and edge cases"""
        print("🔍 Testing Error Handling...")

        # Test API with invalid parameters
        try:
            result = frappe.call("posawesome.posawesome.api.shift_reports.get_shift_report", shift_report_id="INVALID")
            # Should return None or empty result gracefully
            self.assertTrue(result is None or isinstance(result, dict))
        except Exception as e:
            # Should handle gracefully
            self.assertIn("not found", str(e).lower())

        # Test calculation with invalid data
        from posawesome.posawesome.api.shift_calculations import calculate_expected_amounts

        try:
            result = calculate_expected_amounts(None, None, None)
            # Should handle None values gracefully
            self.assertIsInstance(result, dict)
        except Exception as e:
            # Should handle gracefully
            self.assertIn("invalid", str(e).lower())

        print("✅ Error handling works")

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 RUNNING POS SHIFT REPORT INTEGRATION TESTS")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPOSShiftReportIntegration)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")

    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! POS Shift Report System is working correctly!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED! Please check the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = run_integration_tests()
        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)