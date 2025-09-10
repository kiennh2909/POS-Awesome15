#!/usr/bin/env python3
"""
Debug script to check if shift report fields are updated when invoices are created
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

def debug_shift_report_updates():
    """Debug shift report updates when invoice is created"""

    print("🔍 DEBUGGING SHIFT REPORT UPDATES")
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
        print(f"   - payment_breakdown: {shift_report.payment_breakdown}")

        # Step 2: Get customer and item
        customers = frappe.get_all("Customer", limit=1)
        items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=1)

        if not customers or not items:
            print("❌ Missing customer or item data")
            return False

        customer = customers[0].name
        item = items[0].name

        # Step 3: Create and submit invoice
        print("
📝 Creating test invoice...")

        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": opening_shift.company,
            "pos_profile": opening_shift.pos_profile,
            "is_pos": 1,
            "posa_pos_opening_shift": opening_shift_name,
            "items": [{
                "item_code": item,
                "qty": 1,
                "rate": 150.00
            }],
            "payments": [{
                "mode_of_payment": "Cash",
                "amount": 150.00
            }]
        })

        print(f"   - Invoice amount: {invoice.grand_total}")
        print(f"   - Payment method: Cash")

        # Check values before submit
        print("\n🔍 Before submit:")
        print(f"   - pos_shift_report: {getattr(invoice, 'pos_shift_report', 'None')}")
        print(f"   - shift_report_id: {getattr(invoice, 'shift_report_id', 'None')}")

        # Submit invoice
        invoice.insert()
        invoice.submit()
        frappe.db.commit()

        print(f"✅ Created and submitted invoice: {invoice.name}")

        # Step 4: Check shift report after invoice creation
        print("\n📊 After invoice creation:")

        shift_report.reload()

        final_count = shift_report.invoice_count or 0
        final_sales = shift_report.total_sales or 0
        final_returns = shift_report.total_returns or 0

        print(f"   - invoice_count: {final_count} (was {initial_count})")
        print(f"   - total_sales: {final_sales} (was {initial_sales})")
        print(f"   - total_returns: {final_returns} (was {initial_returns})")
        print(f"   - payment_breakdown: {shift_report.payment_breakdown}")

        # Check if values were updated correctly
        expected_count = initial_count + 1
        expected_sales = initial_sales + 150.00
        expected_returns = initial_returns

        print("
✅ Expected vs Actual:")
        print(f"   - invoice_count: expected {expected_count}, got {final_count}")
        print(f"   - total_sales: expected {expected_sales}, got {final_sales}")
        print(f"   - total_returns: expected {expected_returns}, got {final_returns}")

        # Verify updates according to new logic:
        # - invoice_count: all invoices (including cancelled)
        # - total_sales: only Paid invoices
        # - total_returns: only Cancelled invoices
        count_updated = final_count == expected_count
        sales_updated = abs(final_sales - expected_sales) < 0.01  # Only Paid invoices
        returns_updated = final_returns == 0  # No cancelled invoices yet

        print(f"   - Count updated: {count_updated} ({final_count} == {expected_count})")
        print(f"   - Sales updated: {sales_updated} ({final_sales} == {expected_sales}) - Only Paid")
        print(f"   - Returns updated: {returns_updated} ({final_returns} == 0) - No cancelled yet")

        print("
🎯 Update Status:")
        print(f"   - invoice_count updated: {'✅' if count_updated else '❌'}")
        print(f"   - total_sales updated: {'✅' if sales_updated else '❌'}")
        print(f"   - total_returns updated: {'✅' if returns_updated else '❌'}")

        # Check payment breakdown
        try:
            breakdown = frappe.parse_json(shift_report.payment_breakdown or "{}")
            cash_amount = breakdown.get("Cash", 0)
            print(f"   - Cash in payment breakdown: {cash_amount}")
            breakdown_updated = abs(cash_amount - 150.00) < 0.01
            print(f"   - payment_breakdown updated: {'✅' if breakdown_updated else '❌'}")
        except:
            print("   - payment_breakdown: Error parsing JSON")
            breakdown_updated = False

        # Overall result
        all_updated = count_updated and sales_updated and returns_updated and breakdown_updated

        # Step 5: Cancel invoice and check updates
        print("
🔄 Testing cancellation...")

        invoice.cancel()
        frappe.db.commit()

        shift_report.reload()

        cancel_count = shift_report.invoice_count or 0
        cancel_sales = shift_report.total_sales or 0
        cancel_returns = shift_report.total_returns or 0

        print(f"   - After cancel - invoice_count: {cancel_count}")
        print(f"   - After cancel - total_sales: {cancel_sales}")
        print(f"   - After cancel - total_returns: {cancel_returns}")

        # After cancel, count should remain the same, but sales should decrease
        cancel_correct = (
            cancel_count == final_count and  # Count unchanged
            abs(cancel_sales - initial_sales) < 0.01 and  # Sales back to initial
            abs(cancel_returns - initial_returns) < 0.01  # Returns unchanged
        )

        print(f"   - Cancellation handling: {'✅' if cancel_correct else '❌'}")

        # Cleanup
        try:
            if invoice.docstatus == 1:
                invoice.cancel()
            frappe.delete_doc("Sales Invoice", invoice.name, force=True)
            frappe.db.commit()
            print("
✅ Cleaned up test invoice")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        return all_updated and cancel_correct

    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = debug_shift_report_updates()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("🎉 DEBUG PASSED - Shift report updates are working correctly!")
        else:
            print("❌ DEBUG FAILED - Issues with shift report updates")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Debug execution failed: {e}")
        frappe.destroy()
        exit(1)