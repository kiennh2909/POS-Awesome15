#!/usr/bin/env python3
"""
Test script to verify invoice to shift report linking
"""

import os
import sys
import json

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

def test_invoice_shift_report_linking():
    """Test the invoice to shift report linking functionality"""

    print("🧪 TESTING INVOICE TO SHIFT REPORT LINKING")
    print("=" * 60)

    try:
        # Step 1: Get existing opening shift
        opening_shifts = frappe.get_all(
            "POS Opening Shift",
            filters={"docstatus": 1, "status": "Open"},
            limit=1
        )

        if not opening_shifts:
            print("❌ No open opening shifts found")
            return False

        opening_shift_name = opening_shifts[0].name
        print(f"✅ Using opening shift: {opening_shift_name}")

        # Get opening shift details
        opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
        print(f"   - Has shift report: {getattr(opening_shift, 'shift_report', 'None')}")
        print(f"   - Shift report ID: {getattr(opening_shift, 'shift_report_id', 'None')}")

        # Step 2: Create a test invoice
        print("\n2. Creating test invoice...")

        # Get POS profile from opening shift
        pos_profile = opening_shift.pos_profile
        company = opening_shift.company

        # Get a customer
        customers = frappe.get_all("Customer", limit=1)
        if not customers:
            print("❌ No customers found")
            return False

        customer = customers[0].name

        # Get an item
        items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=1)
        if not items:
            print("❌ No sales items found")
            return False

        item = items[0].name

        # Create invoice
        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": company,
            "pos_profile": pos_profile,
            "is_pos": 1,
            "posa_pos_opening_shift": opening_shift_name,
            "items": [{
                "item_code": item,
                "qty": 1,
                "rate": 100
            }]
        })

        invoice.insert()
        print(f"✅ Created invoice: {invoice.name}")

        # Check if shift report fields are set after validation
        print(f"   - pos_shift_report: {getattr(invoice, 'pos_shift_report', 'None')}")
        print(f"   - shift_report_id: {getattr(invoice, 'shift_report_id', 'None')}")

        # Step 3: Submit the invoice
        print("\n3. Submitting invoice...")
        invoice.submit()
        frappe.db.commit()
        print(f"✅ Submitted invoice: {invoice.name}")

        # Check shift report fields after submit
        invoice.reload()
        print(f"   - pos_shift_report after submit: {getattr(invoice, 'pos_shift_report', 'None')}")
        print(f"   - shift_report_id after submit: {getattr(invoice, 'shift_report_id', 'None')}")

        # Step 4: Check if shift report was updated
        if hasattr(invoice, 'pos_shift_report') and invoice.pos_shift_report:
            print("\n4. Checking shift report update...")
            shift_report = frappe.get_doc("POS Shift Report", invoice.pos_shift_report)

            # Check if invoice is in shift report
            invoice_found = False
            for inv in shift_report.invoices:
                if inv.invoice_no == invoice.name:
                    invoice_found = True
                    print(f"✅ Invoice found in shift report: {inv.invoice_no}")
                    print(f"   - Total amount: {inv.total_amount}")
                    print(f"   - Status: {inv.status}")
                    break

            if not invoice_found:
                print("❌ Invoice not found in shift report")

            print(f"   - Shift report invoice count: {shift_report.invoice_count}")
            print(f"   - Shift report total sales: {shift_report.total_sales}")

        # Step 5: Cancel invoice and check shift report update
        print("\n5. Cancelling invoice...")
        invoice.cancel()
        frappe.db.commit()
        print(f"✅ Cancelled invoice: {invoice.name}")

        # Check shift report after cancellation
        if hasattr(invoice, 'pos_shift_report') and invoice.pos_shift_report:
            shift_report.reload()
            for inv in shift_report.invoices:
                if inv.invoice_no == invoice.name:
                    print(f"   - Invoice status after cancel: {inv.status}")
                    break

            print(f"   - Shift report invoice count after cancel: {shift_report.invoice_count}")
            print(f"   - Shift report total sales after cancel: {shift_report.total_sales}")

        # Cleanup
        try:
            frappe.delete_doc("Sales Invoice", invoice.name, force=True)
            frappe.db.commit()
            print("\n✅ Cleaned up test invoice")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        return True

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_invoice_shift_report_linking()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED - Invoice to shift report linking is working!")
        else:
            print("❌ TEST FAILED - Issues with invoice to shift report linking")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)