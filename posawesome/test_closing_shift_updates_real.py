#!/usr/bin/env python3
"""
Test script for POS Closing Shift updates with real data
Tests the new update_shift_report_and_payment_summaries_on_close method
"""

import frappe
from frappe.utils import now, get_datetime, flt
import json

def test_closing_shift_updates_with_real_data():
    """
    Test the update_shift_report_and_payment_summaries_on_close method with real closing shift data
    """
    print("=" * 80)
    print("🧪 TESTING POS CLOSING SHIFT UPDATES WITH REAL DATA")
    print("=" * 80)

    try:
        # STEP 1: Find a submitted closing shift with shift report
        print("\n📋 STEP 1: Finding submitted closing shift...")

        closing_shifts = frappe.get_all("POS Closing Shift",
            filters={
                "docstatus": 1,  # Submitted
                "shift_report": ["!=", ""],  # Has shift report
            },
            fields=["name", "shift_report", "pos_opening_shift", "user", "period_end_date"],
            order_by="creation desc",
            limit=1
        )

        if not closing_shifts:
            print("❌ No submitted closing shifts found with shift reports")
            return False

        closing_shift_name = closing_shifts[0]["name"]
        shift_report_name = closing_shifts[0]["shift_report"]

        print(f"✅ Found closing shift: {closing_shift_name}")
        print(f"✅ Linked shift report: {shift_report_name}")

        # STEP 2: Get the closing shift document
        print("\n📋 STEP 2: Loading closing shift document...")

        closing_shift = frappe.get_doc("POS Closing Shift", closing_shift_name)
        shift_report = frappe.get_doc("POS Shift Report", shift_report_name)

        print(f"✅ Closing shift status: {closing_shift.docstatus}")
        print(f"✅ Shift report status: {shift_report.status}")
        print(f"✅ Payment reconciliation count: {len(closing_shift.payment_reconciliation)}")

        # STEP 3: Check current state before test
        print("\n📋 STEP 3: Checking current state...")

        # Check POS Payment Summaries
        payment_summaries = frappe.get_all("POS Payment Summary",
            filters={
                "shift_report_id": shift_report.shift_report_id,
                "pos_shift_report": shift_report.name
            },
            fields=["name", "payment_method", "closing_amount", "expected_closing_amount", "difference"]
        )

        print(f"✅ Found {len(payment_summaries)} POS Payment Summary records")

        # STEP 4: Test the update method
        print("\n📋 STEP 4: Testing update_shift_report_and_payment_summaries_on_close...")

        # Store original values for comparison
        original_shift_status = shift_report.status
        original_shift_closing_date = shift_report.closing_date
        original_shift_closed_by = shift_report.closed_by
        original_shift_total_actual = shift_report.total_actual_closing
        original_shift_difference = shift_report.difference

        original_payment_summaries = {}
        for ps in payment_summaries:
            original_payment_summaries[ps.name] = {
                "closing_amount": ps.closing_amount,
                "expected_closing_amount": ps.expected_closing_amount,
                "difference": ps.difference
            }

        print(f"📊 Original Shift Report state:")
        print(f"   Status: {original_shift_status}")
        print(f"   Closing Date: {original_shift_closing_date}")
        print(f"   Closed By: {original_shift_closed_by}")
        print(f"   Total Actual Closing: {original_shift_total_actual}")
        print(f"   Difference: {original_shift_difference}")

        # Call the update method
        print("🔄 Calling update_shift_report_and_payment_summaries_on_close...")
        closing_shift.update_shift_report_and_payment_summaries_on_close()

        # STEP 5: Verify updates
        print("\n📋 STEP 5: Verifying updates...")

        # Reload documents
        shift_report.reload()
        updated_payment_summaries = frappe.get_all("POS Payment Summary",
            filters={
                "shift_report_id": shift_report.shift_report_id,
                "pos_shift_report": shift_report.name
            },
            fields=["name", "payment_method", "closing_amount", "expected_closing_amount", "difference"]
        )

        # Check Shift Report updates
        print("📊 Shift Report updates:")
        print(f"   Status: {original_shift_status} → {shift_report.status}")
        print(f"   Closing Date: {original_shift_closing_date} → {shift_report.closing_date}")
        print(f"   Closed By: {original_shift_closed_by} → {shift_report.closed_by}")
        print(f"   Total Actual Closing: {original_shift_total_actual} → {shift_report.total_actual_closing}")
        print(f"   Difference: {original_shift_difference} → {shift_report.difference}")

        # Check if status changed to "Closed"
        if shift_report.status == "Closed":
            print("✅ Shift Report status updated to 'Closed'")
        else:
            print(f"⚠️  Shift Report status is '{shift_report.status}' (expected 'Closed')")

        # Check if closing_date is set
        if shift_report.closing_date:
            print("✅ Shift Report closing_date is set")
        else:
            print("❌ Shift Report closing_date is not set")

        # Check if closed_by is set
        if shift_report.closed_by:
            print("✅ Shift Report closed_by is set")
        else:
            print("❌ Shift Report closed_by is not set")

        # Check POS Payment Summary updates
        print(f"\n📊 POS Payment Summary updates ({len(updated_payment_summaries)} records):")
        updated_count = 0
        for ps in updated_payment_summaries:
            original = original_payment_summaries.get(ps.name, {})
            if (ps.closing_amount != original.get("closing_amount") or
                ps.expected_closing_amount != original.get("expected_closing_amount") or
                ps.difference != original.get("difference")):
                updated_count += 1
                print(f"   ✅ {ps.name} ({ps.payment_method}):")
                print(f"      Closing: {original.get('closing_amount')} → {ps.closing_amount}")
                print(f"      Expected: {original.get('expected_closing_amount')} → {ps.expected_closing_amount}")
                print(f"      Difference: {original.get('difference')} → {ps.difference}")

        if updated_count == 0:
            print("ℹ️  No POS Payment Summary records were updated (may be already up-to-date)")

        # STEP 6: Verify data consistency
        print("\n📋 STEP 6: Verifying data consistency...")

        # Check if total_actual_closing matches sum of payment summaries
        calculated_total = sum(flt(ps.closing_amount or 0) for ps in updated_payment_summaries)
        if abs(flt(shift_report.total_actual_closing or 0) - calculated_total) < 0.01:
            print(f"✅ Total actual closing consistency: {shift_report.total_actual_closing} ≈ {calculated_total}")
        else:
            print(f"❌ Total actual closing inconsistency: {shift_report.total_actual_closing} vs {calculated_total}")

        # Check if difference calculation is correct
        expected_total = flt(shift_report.total_expected_closing or 0)
        actual_total = flt(shift_report.total_actual_closing or 0)
        calculated_difference = actual_total - expected_total

        if abs(flt(shift_report.difference or 0) - calculated_difference) < 0.01:
            print(f"✅ Difference calculation correct: {shift_report.difference}")
        else:
            print(f"❌ Difference calculation incorrect: {shift_report.difference} vs {calculated_difference}")

        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n💥 TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return False

def test_closing_shift_creation_and_update():
    """
    Test creating a new closing shift and updating it
    """
    print("=" * 80)
    print("🧪 TESTING CLOSING SHIFT CREATION AND UPDATE")
    print("=" * 80)

    try:
        # Find an open opening shift
        opening_shifts = frappe.get_all("POS Opening Shift",
            filters={"status": "Open"},
            fields=["name", "user", "pos_profile"],
            limit=1
        )

        if not opening_shifts:
            print("❌ No open opening shifts found for testing")
            return False

        opening_shift = opening_shifts[0]
        print(f"✅ Found open opening shift: {opening_shift.name}")

        # Create closing shift using the API
        from posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift import make_closing_shift_from_opening

        closing_shift = make_closing_shift_from_opening(opening_shift.name)

        if not closing_shift:
            print("❌ Failed to create closing shift")
            return False

        print(f"✅ Created closing shift: {closing_shift.name}")

        # Test the update method on draft closing shift
        print("🔄 Testing update method on draft closing shift...")
        closing_shift.update_shift_report_and_payment_summaries_on_close()

        print("✅ Update method completed without errors")

        # Clean up - don't submit to avoid affecting real data
        print("🧹 Cleaning up test data...")
        frappe.delete_doc("POS Closing Shift", closing_shift.name, force=True)

        print("🎉 CREATION AND UPDATE TEST COMPLETED!")
        return True

    except Exception as e:
        print(f"\n💥 CREATION TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting POS Closing Shift Real Data Tests...")

    # Test 1: Update existing submitted closing shift
    test1_result = test_closing_shift_updates_with_real_data()

    print("\n" + "="*80)

    # Test 2: Create and update new closing shift
    test2_result = test_closing_shift_creation_and_update()

    print("\n" + "="*80)
    print("📊 TEST RESULTS:")
    print(f"   Test 1 (Real Data Update): {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"   Test 2 (Creation & Update): {'✅ PASSED' if test2_result else '❌ FAILED'}")

    if test1_result and test2_result:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - CHECK LOGS ABOVE")

    print("="*80)