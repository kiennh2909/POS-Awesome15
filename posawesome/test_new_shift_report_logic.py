#!/usr/bin/env python3
"""
Test script to verify the new shift report calculation logic:
- invoice_count: All invoices (including Cancelled)
- total_sales: Only Paid invoices
- total_returns: Only Cancelled invoices
- payment_breakdown: Only Paid invoices
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

def test_new_shift_report_logic():
    """Test the new shift report calculation logic"""

    print("🧮 TESTING NEW SHIFT REPORT CALCULATION LOGIC")
    print("=" * 60)
    print("New Logic:")
    print("✅ invoice_count = All invoices (including Cancelled)")
    print("✅ total_sales = Only Paid invoices")
    print("✅ total_returns = Only Cancelled invoices")
    print("✅ payment_breakdown = Only Paid invoices")
    print("=" * 60)

    try:
        # Step 1: Get existing opening shift
        opening_shifts = frappe.get_all("POS Opening Shift",
            filters={"docstatus": 1, "status": "Open"},
            limit=1
        )

        if not opening_shifts:
            print("❌ No open opening shifts found")
            return False

        opening_shift_name = opening_shifts[0].name
        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)

        if not hasattr(opening_shift, 'shift_report') or not opening_shift.shift_report:
            print("❌ Opening shift has no shift report")
            return False

        shift_report = frappe.get_doc("POS Shift Report", opening_shift.shift_report)
        print(f"✅ Using shift report: {shift_report.name}")

        # Get initial values
        initial_count = shift_report.invoice_count or 0
        initial_sales = shift_report.total_sales or 0
        initial_returns = shift_report.total_returns or 0

        print(f"📊 Initial values:")
        print(f"   - invoice_count: {initial_count}")
        print(f"   - total_sales: {initial_sales}")
        print(f"   - total_returns: {initial_returns}")

        # Step 2: Get customer and item
        customers = frappe.get_all("Customer", limit=1)
        items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=1)

        if not customers or not items:
            print("❌ Missing customer or item data")
            return False

        customer = customers[0].name
        item = items[0].name

        # Step 3: Create and submit first invoice (Paid)
        print("
📝 Creating first invoice (Paid)...")

        invoice1 = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": opening_shift.company,
            "pos_profile": opening_shift.pos_profile,
            "is_pos": 1,
            "posa_pos_opening_shift": opening_shift_name,
            "items": [{
                "item_code": item,
                "qty": 1,
                "rate": 100.00
            }],
            "payments": [{
                "mode_of_payment": "Cash",
                "amount": 100.00
            }]
        })

        invoice1.insert()
        invoice1.submit()
        frappe.db.commit()

        print(f"✅ Created Paid invoice: {invoice1.name} - Amount: {invoice1.grand_total}")

        # Check shift report after first invoice
        shift_report.reload()

        after_first_count = shift_report.invoice_count or 0
        after_first_sales = shift_report.total_sales or 0
        after_first_returns = shift_report.total_returns or 0

        print("
📊 After first Paid invoice:")
        print(f"   - invoice_count: {after_first_count} (was {initial_count})")
        print(f"   - total_sales: {after_first_sales} (was {initial_sales})")
        print(f"   - total_returns: {after_first_returns} (was {initial_returns})")

        # Verify first invoice
        first_count_correct = after_first_count == initial_count + 1
        first_sales_correct = abs(after_first_sales - (initial_sales + 100.00)) < 0.01
        first_returns_correct = after_first_returns == initial_returns

        print("
✅ First invoice verification:")
        print(f"   - Count correct: {first_count_correct}")
        print(f"   - Sales correct: {first_sales_correct}")
        print(f"   - Returns correct: {first_returns_correct}")

        # Step 4: Create and submit second invoice (Paid)
        print("
📝 Creating second invoice (Paid)...")

        invoice2 = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": opening_shift.company,
            "pos_profile": opening_shift.pos_profile,
            "is_pos": 1,
            "posa_pos_opening_shift": opening_shift_name,
            "items": [{
                "item_code": item,
                "qty": 1,
                "rate": 200.00
            }],
            "payments": [{
                "mode_of_payment": "Card",
                "amount": 200.00
            }]
        })

        invoice2.insert()
        invoice2.submit()
        frappe.db.commit()

        print(f"✅ Created second Paid invoice: {invoice2.name} - Amount: {invoice2.grand_total}")

        # Check shift report after second invoice
        shift_report.reload()

        after_second_count = shift_report.invoice_count or 0
        after_second_sales = shift_report.total_sales or 0
        after_second_returns = shift_report.total_returns or 0

        print("
📊 After second Paid invoice:")
        print(f"   - invoice_count: {after_second_count} (was {after_first_count})")
        print(f"   - total_sales: {after_second_sales} (was {after_first_sales})")
        print(f"   - total_returns: {after_second_returns} (was {after_first_returns})")

        # Verify second invoice
        second_count_correct = after_second_count == after_first_count + 1
        second_sales_correct = abs(after_second_sales - (after_first_sales + 200.00)) < 0.01
        second_returns_correct = after_second_returns == after_first_returns

        print("
✅ Second invoice verification:")
        print(f"   - Count correct: {second_count_correct}")
        print(f"   - Sales correct: {second_sales_correct}")
        print(f"   - Returns correct: {second_returns_correct}")

        # Step 5: Cancel first invoice to test total_returns
        print("
🔄 Cancelling first invoice to test total_returns...")

        invoice1.cancel()
        frappe.db.commit()

        print(f"✅ Cancelled invoice: {invoice1.name}")

        # Check shift report after cancellation
        shift_report.reload()

        after_cancel_count = shift_report.invoice_count or 0
        after_cancel_sales = shift_report.total_sales or 0
        after_cancel_returns = shift_report.total_returns or 0

        print("
📊 After cancelling first invoice:")
        print(f"   - invoice_count: {after_cancel_count} (was {after_second_count})")
        print(f"   - total_sales: {after_cancel_sales} (was {after_second_sales})")
        print(f"   - total_returns: {after_cancel_returns} (was {after_second_returns})")

        # Verify cancellation
        cancel_count_correct = after_cancel_count == after_second_count  # Count unchanged
        cancel_sales_correct = abs(after_cancel_sales - (after_second_sales - 100.00)) < 0.01  # Sales decreased
        cancel_returns_correct = abs(after_cancel_returns - (after_second_returns + 100.00)) < 0.01  # Returns increased

        print("
✅ Cancellation verification:")
        print(f"   - Count correct: {cancel_count_correct} (unchanged)")
        print(f"   - Sales correct: {cancel_sales_correct} (decreased by 100)")
        print(f"   - Returns correct: {cancel_returns_correct} (increased by 100)")

        # Step 6: Check payment breakdown
        print("
💳 Checking payment breakdown...")

        try:
            import json
            breakdown = json.loads(shift_report.payment_breakdown or "{}")
            print("   - Payment breakdown:")
            for method, amount in breakdown.items():
                print(f"     * {method}: {amount}")

            # Should only include the second invoice (Card: 200.00)
            # First invoice was cancelled, so Cash should not be included
            card_amount = breakdown.get("Card", 0)
            cash_amount = breakdown.get("Cash", 0)

            breakdown_correct = (
                abs(card_amount - 200.00) < 0.01 and  # Second invoice
                cash_amount == 0  # First invoice cancelled
            )

            print("
✅ Payment breakdown verification:")
            print(f"   - Card amount correct: {abs(card_amount - 200.00) < 0.01}")
            print(f"   - Cash amount correct: {cash_amount == 0}")
            print(f"   - Overall correct: {breakdown_correct}")

        except Exception as e:
            print(f"   - Error parsing payment breakdown: {e}")
            breakdown_correct = False

        # Overall verification
        all_correct = (
            first_count_correct and first_sales_correct and first_returns_correct and
            second_count_correct and second_sales_correct and second_returns_correct and
            cancel_count_correct and cancel_sales_correct and cancel_returns_correct and
            breakdown_correct
        )

        # Cleanup
        print("
🧹 Cleaning up test data...")

        try:
            # Cancel and delete invoices
            for inv in [invoice2]:  # invoice1 already cancelled
                if inv.docstatus == 1:
                    inv.cancel()
                frappe.delete_doc("Sales Invoice", inv.name, force=True)

            # Restore invoice1 (uncancel)
            if hasattr(invoice1, 'docstatus') and invoice1.docstatus == 2:
                invoice1.cancel()  # This will uncancel it
                frappe.delete_doc("Sales Invoice", invoice1.name, force=True)

            frappe.db.commit()
            print("✅ Cleaned up test invoices")

        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        return all_correct

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_new_shift_report_logic()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED - New shift report logic is working correctly!")
            print("\n📋 VERIFIED LOGIC:")
            print("   ✅ invoice_count = All invoices (including Cancelled)")
            print("   ✅ total_sales = Only Paid invoices")
            print("   ✅ total_returns = Only Cancelled invoices")
            print("   ✅ payment_breakdown = Only Paid invoices")
        else:
            print("❌ TEST FAILED - Issues with new shift report logic")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)