#!/usr/bin/env python3
"""
Script to track a specific invoice through the complete POS Shift Report flow
This demonstrates the logging and tracking capabilities
"""

import os
import sys
import time

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

def track_invoice_flow():
    """Track a specific invoice through the complete flow"""

    print("🔍 TRACKING INVOICE FLOW THROUGH POS SHIFT REPORT SYSTEM")
    print("=" * 80)
    print("This script will:")
    print("1. Create a Sales Invoice")
    print("2. Submit the invoice (trigger shift report update)")
    print("3. Cancel the invoice (trigger shift report update)")
    print("4. Show the complete flow with detailed logging")
    print("=" * 80)

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
        print(f"📊 Initial state - Count: {shift_report.invoice_count}, Sales: {shift_report.total_sales}, Returns: {shift_report.total_returns}")

        # Step 2: Get customer and item
        customers = frappe.get_all("Customer", limit=1)
        items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=1)

        if not customers or not items:
            print("❌ Missing customer or item data")
            return False

        customer = customers[0].name
        item = items[0].name

        # Step 3: Create invoice
        print("
📝 STEP 1: Creating Sales Invoice..."        print("=" * 50)

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

        invoice.insert()
        print(f"✅ Created invoice: {invoice.name}")
        print(f"   Status: {invoice.status}")
        print(f"   Amount: {invoice.grand_total}")
        print(f"   POS Opening Shift: {invoice.posa_pos_opening_shift}")
        print(f"   Shift Report: {getattr(invoice, 'pos_shift_report', 'None')}")

        # Step 4: Submit invoice
        print("
📤 STEP 2: Submitting Invoice..."        print("=" * 50)

        print("🔍 Check logs now - you should see [INVOICE_TRACKING] logs")
        time.sleep(2)  # Give time to check logs

        invoice.submit()
        frappe.db.commit()

        print(f"✅ Submitted invoice: {invoice.name}")
        print(f"   New Status: {invoice.status}")

        # Check shift report after submit
        shift_report.reload()
        print("
📊 Shift Report after Submit:"        print(f"   Invoice Count: {shift_report.invoice_count}")
        print(f"   Total Sales: {shift_report.total_sales}")
        print(f"   Total Returns: {shift_report.total_returns}")
        print(f"   Payment Breakdown: {shift_report.payment_breakdown}")

        # Step 5: Cancel invoice
        print("
🗑️ STEP 3: Cancelling Invoice..."        print("=" * 50)

        print("🔍 Check logs now - you should see cancellation tracking")
        time.sleep(2)  # Give time to check logs

        invoice.cancel()
        frappe.db.commit()

        print(f"✅ Cancelled invoice: {invoice.name}")
        print(f"   New Status: {invoice.status}")

        # Check shift report after cancel
        shift_report.reload()
        print("
📊 Shift Report after Cancel:"        print(f"   Invoice Count: {shift_report.invoice_count}")
        print(f"   Total Sales: {shift_report.total_sales}")
        print(f"   Total Returns: {shift_report.total_returns}")
        print(f"   Payment Breakdown: {shift_report.payment_breakdown}")

        # Step 6: Cleanup
        print("
🧹 STEP 4: Cleanup..."        print("=" * 50)

        # Restore invoice (uncancel)
        if hasattr(invoice, 'docstatus') and invoice.docstatus == 2:
            invoice.cancel()  # This will uncancel it
            frappe.delete_doc("Sales Invoice", invoice.name, force=True)
            frappe.db.commit()
            print("✅ Cleaned up test invoice")

        # Summary
        print("
🎉 TRACKING COMPLETE!"        print("=" * 80)
        print("📋 LOG PATTERNS TO LOOK FOR:")
        print("   🔍 [INVOICE_TRACKING] - Invoice processing steps")
        print("   🔢 [SHIFT_REPORT_CALC] - Shift report calculations")
        print("   📊 UPDATE_CALCULATED_FIELDS - Field updates")
        print("   💳 GET_PAYMENT_BREAKDOWN - Payment processing")
        print("=" * 80)
        print("💡 To see logs in real-time:")
        print("   tail -f /home/frappe/frappe-bench/logs/frappe.log | grep INVOICE_TRACKING")
        print("   tail -f /home/frappe/frappe-bench/logs/frappe.log | grep SHIFT_REPORT_CALC")

        return True

    except Exception as e:
        print(f"❌ Error during tracking: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = track_invoice_flow()
        frappe.destroy()
        print("\n" + "=" * 80)
        if success:
            print("✅ INVOICE FLOW TRACKING COMPLETED SUCCESSFULLY!")
            print("🔍 Check the logs above to see the complete tracking flow")
        else:
            print("❌ INVOICE FLOW TRACKING FAILED")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Tracking execution failed: {e}")
        frappe.destroy()
        exit(1)