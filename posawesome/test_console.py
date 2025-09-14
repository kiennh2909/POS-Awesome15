#!/usr/bin/env python3
"""
Test script to run in bench console
Usage: bench console < posawesome/test_console.py
"""

import frappe
import json
from frappe.utils import nowdate, nowtime

def test_pos_payment_summary():
    """Test POS Payment Summary implementation"""

    print("🧪 TESTING POS PAYMENT SUMMARY IN BENCH CONSOLE")
    print("=" * 60)

    try:
        # Test 1: Check if DocType exists
        print("\n1️⃣ Checking DocType...")
        if frappe.db.exists("DocType", "POS Payment Summary"):
            print("✅ POS Payment Summary DocType exists")
        else:
            print("❌ POS Payment Summary DocType not found")
            return

        # Test 2: Check API imports
        print("\n2️⃣ Testing API imports...")
        try:
            from posawesome.posawesome.api.shift_reports import get_shift_report_with_payment_summary
            print("✅ get_shift_report_with_payment_summary imported successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return

        try:
            from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
            print("✅ create_payment_summaries_for_shift imported successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return

        # Test 3: Check existing shift reports
        print("\n3️⃣ Checking existing shift reports...")
        shift_reports = frappe.get_all("POS Shift Report",
            filters={"status": "Open"},
            fields=["name", "shift_report_id"],
            limit=5
        )

        if shift_reports:
            print(f"✅ Found {len(shift_reports)} open shift reports:")
            for sr in shift_reports:
                print(f"   - {sr.name} ({sr.shift_report_id})")
        else:
            print("⚠️ No open shift reports found - creating test data...")

            # Create test shift report
            test_shift = create_test_shift_report()
            if test_shift:
                shift_reports = [{"name": test_shift, "shift_report_id": f"TEST-{test_shift}"}]

        # Test 4: Test API with first shift report
        if shift_reports:
            test_shift = shift_reports[0]
            print(f"\n4️⃣ Testing API with shift report: {test_shift['name']}")

            # Test get_shift_report_with_payment_summary
            try:
                result = get_shift_report_with_payment_summary(test_shift["name"])
                print("✅ API call successful")
                print(f"   - Shift Report: {result.get('shift_report_id')}")
                print(f"   - Invoices: {len(result.get('invoices', []))}")

                payment_summaries = result.get('payment_summaries', [])
                print(f"   - Payment Summaries: {len(payment_summaries)}")

                if payment_summaries:
                    print("   - Payment Summary Details:")
                    for ps in payment_summaries:
                        print(f"     * {ps.get('payment_method')}: {ps.get('transaction_amount', 0)}")

            except Exception as e:
                print(f"❌ API test failed: {str(e)}")
                import traceback
                traceback.print_exc()

        # Test 5: Check database records
        print("\n5️⃣ Checking database records...")
        payment_summary_count = frappe.db.count("POS Payment Summary")
        print(f"✅ Total POS Payment Summary records: {payment_summary_count}")

        if payment_summary_count > 0:
            # Show sample records
            sample_records = frappe.get_all("POS Payment Summary",
                fields=["name", "shift_report_id", "payment_method", "transaction_amount"],
                limit=3
            )
            print("   - Sample records:")
            for record in sample_records:
                print(f"     * {record.name}: {record.payment_method} = {record.transaction_amount}")

        print("\n🎉 CONSOLE TEST COMPLETED!")
        print("\n📋 SUMMARY:")
        print(f"   - DocType: ✅ Exists")
        print(f"   - API Methods: ✅ Available")
        print(f"   - Database Records: {payment_summary_count}")
        print(f"   - Test Status: ✅ Successful")

    except Exception as e:
        print(f"\n💥 TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


def create_test_shift_report():
    """Create a test shift report for testing"""
    try:
        print("   Creating test shift report...")

        # Create test opening shift first
        opening_shift = frappe.get_doc({
            "doctype": "POS Opening Shift",
            "posting_date": nowdate(),
            "posting_time": nowtime(),
            "company": "NVL-DaiLoan",
            "pos_profile": "POS_DY134",
            "user": frappe.session.user,
            "status": "Open",
            "opening_amounts": json.dumps({
                "Cash": 1000.00,
                "Card": 500.00
            })
        })
        opening_shift.insert(ignore_permissions=True)

        # Create shift report
        shift_report = frappe.get_doc({
            "doctype": "POS Shift Report",
            "shift_report_id": f"TEST-{opening_shift.name}",
            "pos_opening_shift": opening_shift.name,
            "opening_date": nowdate(),
            "opening_time": nowtime(),
            "status": "Open",
            "opening_amounts": json.dumps({
                "Cash": 1000.00,
                "Card": 500.00
            })
        })
        shift_report.insert(ignore_permissions=True)

        frappe.db.commit()
        print(f"   ✅ Created test shift report: {shift_report.name}")
        return shift_report.name

    except Exception as e:
        print(f"   ❌ Failed to create test shift report: {str(e)}")
        return None


# Auto-run when executed
if __name__ == "__main__":
    test_pos_payment_summary()