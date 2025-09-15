#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script for POS Payment Summary Creation Issue

This script helps debug why only 1 POS Payment Summary is created
instead of 2 (matching the number of POS Opening Shift Detail records)
"""

import frappe
from frappe import _
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("debug_payment_summary")

def debug_payment_summary_creation(shift_report_name=None):
    """
    Debug the POS Payment Summary creation process

    Args:
        shift_report_name: Name of the shift report to debug (optional)
    """
    print("=" * 80)
    print("🔍 DEBUGGING POS PAYMENT SUMMARY CREATION")
    print("=" * 80)

    try:
        # 1. Find the latest shift report if not provided
        if not shift_report_name:
            shift_reports = frappe.get_all("POS Shift Report",
                filters={"status": "Open"},
                fields=["name", "shift_report_id", "pos_opening_shift"],
                order_by="creation desc",
                limit=1
            )

            if not shift_reports:
                print("❌ No open shift reports found")
                return False

            shift_report_name = shift_reports[0].name
            print(f"📋 Using latest shift report: {shift_report_name}")

        # 2. Get shift report details
        shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
        print(f"📊 Shift Report: {shift_report.name}")
        print(f"📊 Shift Report ID: {shift_report.shift_report_id}")
        print(f"📊 POS Opening Shift: {shift_report.pos_opening_shift}")

        # 3. Check POS Opening Shift Detail
        print("\n" + "=" * 50)
        print("📋 STEP 1: CHECKING POS OPENING SHIFT DETAIL")
        print("=" * 50)

        opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
        print(f"🏪 Opening Shift: {opening_shift.name}")
        print(f"🏪 Status: {opening_shift.status}")
        print(f"🏪 Posting Date: {opening_shift.posting_date}")

        if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
            print(f"✅ Found {len(opening_shift.balance_details)} balance details:")
            opening_amounts = {}

            for i, detail in enumerate(opening_shift.balance_details, 1):
                print(f"   {i}. Mode of Payment: '{detail.mode_of_payment}'")
                print(f"      Amount: {detail.amount}")
                print(f"      Detail Name: {detail.name}")
                opening_amounts[detail.mode_of_payment] = detail.amount or 0
                print()

            print(f"📊 Opening Amounts Dict: {opening_amounts}")
        else:
            print("❌ No balance_details found in POS Opening Shift")
            return False

        # 4. Check existing POS Payment Summary records
        print("\n" + "=" * 50)
        print("📋 STEP 2: CHECKING EXISTING POS PAYMENT SUMMARY RECORDS")
        print("=" * 50)

        existing_summaries = frappe.get_all("POS Payment Summary",
            filters={
                "shift_report_id": shift_report.shift_report_id,
                "pos_shift_report": shift_report.name
            },
            fields=["name", "payment_method", "opening_amount", "transaction_amount", "closing_amount"]
        )

        print(f"📊 Found {len(existing_summaries)} existing POS Payment Summary records:")

        for i, summary in enumerate(existing_summaries, 1):
            print(f"   {i}. Name: {summary.name}")
            print(f"      Payment Method: '{summary.payment_method}'")
            print(f"      Opening Amount: {summary.opening_amount}")
            print(f"      Transaction Amount: {summary.transaction_amount}")
            print(f"      Closing Amount: {summary.closing_amount}")
            print()

        # 5. Simulate the creation process
        print("\n" + "=" * 50)
        print("📋 STEP 3: SIMULATING CREATION PROCESS")
        print("=" * 50)

        created_count = 0
        skipped_count = 0

        for method, opening_amount in opening_amounts.items():
            print(f"\n🔄 Processing payment method: '{method}'")

            # Check if exists
            existing = frappe.db.exists("POS Payment Summary", {
                "shift_report_id": shift_report.shift_report_id,
                "payment_method": method,
                "pos_shift_report": shift_report.name
            })

            if existing:
                print(f"   ⚠️  EXISTS: Record already exists for '{method}' (ID: {existing})")
                skipped_count += 1
            else:
                print(f"   ✅ CREATE: Would create new record for '{method}'")
                print(f"      Opening Amount: {opening_amount}")

                # Try to create (but don't actually save)
                try:
                    payment_summary = frappe.get_doc({
                        "doctype": "POS Payment Summary",
                        "shift_report_id": shift_report.shift_report_id,
                        "pos_shift_report": shift_report.name,
                        "pos_opening_shift": shift_report.pos_opening_shift,
                        "posting_date": shift_report.opening_date,
                        "payment_method": method,
                        "payment_method_type": "Cash",  # Default
                        "currency": "VND",
                        "opening_amount": opening_amount,
                        "transaction_amount": 0,
                        "closing_amount": opening_amount,
                        "transaction_count": 0,
                        "notes": f"Debug: Auto-generated for {shift_report.name}"
                    })

                    # Validate the document
                    payment_summary.validate()
                    print(f"      ✅ VALIDATION PASSED for '{method}'")

                    created_count += 1

                except Exception as e:
                    print(f"      ❌ VALIDATION FAILED for '{method}': {str(e)}")

        print("
📊 SIMULATION RESULTS:"        print(f"   - Would create: {created_count} records")
        print(f"   - Would skip: {skipped_count} records")
        print(f"   - Total expected: {len(opening_amounts)} records")

        # 6. Check consistency
        print("\n" + "=" * 50)
        print("📋 STEP 4: CONSISTENCY CHECK")
        print("=" * 50)

        opening_details_count = len(opening_shift.balance_details or [])
        payment_summaries_count = len(existing_summaries)

        print(f"🏪 Opening Shift Details: {opening_details_count}")
        print(f"📊 Payment Summaries: {payment_summaries_count}")

        if payment_summaries_count == opening_details_count:
            print("✅ CONSISTENCY: Counts match!")
        else:
            print("❌ CONSISTENCY: Counts don't match!")
            print(f"   Expected: {opening_details_count}, Got: {payment_summaries_count}")

        # 7. Detailed analysis
        print("\n" + "=" * 50)
        print("📋 STEP 5: DETAILED ANALYSIS")
        print("=" * 50)

        opening_methods = [d.mode_of_payment for d in opening_shift.balance_details or []]
        summary_methods = [ps.payment_method for ps in existing_summaries]

        print(f"🏪 Opening Methods: {opening_methods}")
        print(f"📊 Summary Methods: {summary_methods}")

        missing_methods = set(opening_methods) - set(summary_methods)
        extra_methods = set(summary_methods) - set(opening_methods)

        if missing_methods:
            print(f"❌ MISSING: These methods exist in opening but not in summary: {list(missing_methods)}")

        if extra_methods:
            print(f"⚠️  EXTRA: These methods exist in summary but not in opening: {list(extra_methods)}")

        # 8. Test the actual initialization function
        print("\n" + "=" * 50)
        print("📋 STEP 6: TESTING INITIALIZE FUNCTION")
        print("=" * 50)

        print("🔄 Calling initialize_payment_summaries_for_shift()...")

        try:
            from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import initialize_payment_summaries_for_shift

            init_result = initialize_payment_summaries_for_shift(shift_report.name)

            if init_result.get("success"):
                print(f"✅ Initialize successful: {init_result}")
            else:
                print(f"❌ Initialize failed: {init_result}")

        except Exception as e:
            print(f"💥 Initialize error: {str(e)}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 80)
        print("🎯 DEBUG COMPLETED")
        print("=" * 80)

        return payment_summaries_count == opening_details_count

    except Exception as e:
        print(f"💥 DEBUG ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run debug
    success = debug_payment_summary_creation()
    print(f"\n🔍 Debug result: {'✅ PASSED' if success else '❌ FAILED'}")
    exit(0 if success else 1)