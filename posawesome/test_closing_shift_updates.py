"""
Test script to verify POS Shift Report and POS Payment Summary updates during closing shift
"""
import frappe
import json
from datetime import datetime

def test_closing_shift_updates():
    """Test that closing shift properly updates POS Shift Report and POS Payment Summary"""
    print("🧪 Testing Closing Shift Updates")
    print("=" * 50)

    try:
        # Find a recent closing shift
        closing_shifts = frappe.get_all("POS Closing Shift",
            filters={"docstatus": 1},
            fields=["name", "shift_report", "pos_opening_shift", "period_end_date", "user"],
            order_by="creation desc",
            limit=1
        )

        if not closing_shifts:
            print("❌ No submitted closing shifts found")
            return False

        closing_shift = closing_shifts[0]
        print(f"📋 Testing with Closing Shift: {closing_shift.name}")
        print(f"   - Shift Report: {closing_shift.shift_report}")
        print(f"   - Opening Shift: {closing_shift.pos_opening_shift}")

        # Test 1: Check POS Shift Report updates
        print("\n1️⃣ Testing POS Shift Report Updates...")

        if not closing_shift.shift_report:
            print("⚠️  No shift report linked to closing shift")
        else:
            shift_report = frappe.get_doc("POS Shift Report", closing_shift.shift_report)

            # Check required fields
            checks = {
                "closing_date": shift_report.closing_date,
                "closed_by": shift_report.closed_by,
                "status": shift_report.status,
                "actual_closing_amounts": shift_report.actual_closing_amounts,
                "total_actual_closing": shift_report.total_actual_closing,
                "difference": shift_report.difference
            }

            print("   📊 POS Shift Report Fields:")
            for field, value in checks.items():
                status = "✅" if value is not None and value != "" else "❌"
                print(f"   {status} {field}: {value}")

            # Verify closing_date matches
            if shift_report.closing_date == closing_shift.period_end_date:
                print("   ✅ closing_date matches closing shift period_end_date")
            else:
                print(f"   ❌ closing_date mismatch: {shift_report.closing_date} vs {closing_shift.period_end_date}")

            # Verify closed_by matches
            if shift_report.closed_by == closing_shift.user:
                print("   ✅ closed_by matches closing shift user")
            else:
                print(f"   ❌ closed_by mismatch: {shift_report.closed_by} vs {closing_shift.user}")

            # Verify status is Closed
            if shift_report.status == "Closed":
                print("   ✅ status is 'Closed'")
            else:
                print(f"   ❌ status is '{shift_report.status}', expected 'Closed'")

        # Test 2: Check POS Payment Summary updates
        print("\n2️⃣ Testing POS Payment Summary Updates...")

        if not closing_shift.shift_report:
            print("⚠️  Cannot test payment summaries without shift report")
        else:
            shift_report = frappe.get_doc("POS Shift Report", closing_shift.shift_report)

            payment_summaries = frappe.get_all("POS Payment Summary",
                filters={
                    "shift_report_id": shift_report.shift_report_id,
                    "pos_shift_report": closing_shift.shift_report
                },
                fields=["name", "payment_method", "closing_amount", "difference", "shift_end_time", "expected_closing_amount"]
            )

            print(f"   📊 Found {len(payment_summaries)} POS Payment Summary records")

            for summary in payment_summaries:
                print(f"\n   💳 Payment Method: {summary.payment_method}")
                checks = {
                    "closing_amount": summary.closing_amount,
                    "difference": summary.difference,
                    "shift_end_time": summary.shift_end_time,
                    "expected_closing_amount": summary.expected_closing_amount
                }

                for field, value in checks.items():
                    status = "✅" if value is not None else "❌"
                    print(f"     {status} {field}: {value}")

                # Verify shift_end_time matches
                if summary.shift_end_time == closing_shift.period_end_date:
                    print("     ✅ shift_end_time matches closing shift period_end_date")
                else:
                    print(f"     ❌ shift_end_time mismatch: {summary.shift_end_time} vs {closing_shift.period_end_date}")

        print("\n🎉 Test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_closing_shift_updates()