#!/usr/bin/env python3
"""
Quick Test Script for POS Shift Report System
Run basic checks to ensure system is working
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

def test_database_tables():
    """Test database tables exist"""
    print("🔍 Checking Database Tables...")

    tables = ["POS Shift Report", "POS Shift Report Invoice"]
    for table in tables:
        exists = frappe.db.exists("DocType", table)
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")

    return all(frappe.db.exists("DocType", table) for table in tables)

def test_custom_fields():
    """Test custom fields exist"""
    print("🔍 Checking Custom Fields...")

    fields = [
        ("POS Opening Shift", "shift_report_id"),
        ("POS Closing Shift", "shift_report"),
        ("Sales Invoice", "pos_shift_report")
    ]

    for doctype, fieldname in fields:
        custom_field = frappe.get_all("Custom Field",
            filters={"dt": doctype, "fieldname": fieldname})
        exists = len(custom_field) > 0
        status = "✅" if exists else "❌"
        print(f"   {status} {doctype}.{fieldname}")

    return all(len(frappe.get_all("Custom Field",
        filters={"dt": doctype, "fieldname": fieldname})) > 0
        for doctype, fieldname in fields)

def test_api_endpoints():
    """Test API endpoints work"""
    print("🔍 Testing API Endpoints...")

    apis = [
        "posawesome.posawesome.api.shift_reports.get_shift_reports",
        "posawesome.posawesome.api.shift_verification.get_pending_verifications"
    ]

    for api in apis:
        try:
            result = frappe.call(api)
            status = "✅"
            print(f"   {status} {api}")
        except Exception as e:
            status = "❌"
            print(f"   {status} {api}: {str(e)}")

    # Test calculation API
    try:
        result = frappe.call("posawesome.posawesome.api.shift_calculations.calculate_expected_amounts",
            opening_amounts={"Cash": 1000}, sales_amount=500)
        status = "✅"
        print(f"   {status} posawesome.posawesome.api.shift_calculations.calculate_expected_amounts")
    except Exception as e:
        status = "❌"
        print(f"   {status} posawesome.posawesome.api.shift_calculations.calculate_expected_amounts: {str(e)}")

def test_create_sample_data():
    """Test creating sample shift report"""
    print("🔍 Testing Sample Data Creation...")

    try:
        # Create sample shift report
        shift_report = frappe.get_doc({
            "doctype": "POS Shift Report",
            "shift_report_id": "QUICK-TEST-001",
            "pos_opening_shift": "SAMPLE-OPEN-001",
            "opening_date": "2024-01-15",
            "opening_time": "09:00:00",
            "opened_by": "Administrator",
            "opening_amounts": '{"Cash": 1000}',
            "total_opening_amount": 1000,
            "status": "Open",
            "verification_status": "Pending"
        })

        shift_report.insert()
        frappe.db.commit()

        print("   ✅ Sample shift report created")

        # Clean up
        frappe.delete_doc("POS Shift Report", shift_report.name, force=True)
        frappe.db.commit()

        print("   ✅ Sample data cleanup successful")
        return True

    except Exception as e:
        print(f"   ❌ Sample data creation failed: {str(e)}")
        return False

def test_business_logic():
    """Test business logic functions"""
    print("🔍 Testing Business Logic...")

    try:
        from posawesome.posawesome.api.shift_calculations import calculate_expected_amounts

        result = calculate_expected_amounts(
            {"Cash": 1000, "Card": 500},
            750,  # sales
            50    # returns
        )

        expected_total = 1000 + 500 + 750 - 50  # 2200
        if result.get("expected_total") == expected_total:
            print("   ✅ Business logic calculations correct")
            return True
        else:
            print(f"   ❌ Calculation error: expected {expected_total}, got {result.get('expected_total')}")
            return False

    except Exception as e:
        print(f"   ❌ Business logic test failed: {str(e)}")
        return False

def main():
    """Run all quick tests"""
    print("🚀 QUICK TEST - POS SHIFT REPORT SYSTEM")
    print("=" * 50)

    tests = [
        ("Database Tables", test_database_tables),
        ("Custom Fields", test_custom_fields),
        ("API Endpoints", test_api_endpoints),
        ("Sample Data", test_create_sample_data),
        ("Business Logic", test_business_logic)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append(result)

    # Summary
    print("\n" + "=" * 50)
    print("📊 QUICK TEST RESULTS")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! POS Shift Report System is ready!")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED! Check the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        frappe.destroy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)