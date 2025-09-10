#!/usr/bin/env python3
"""
Script to check actual status values of Sales Invoices in database
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

def check_invoice_status_values():
    """Check actual status values of Sales Invoices"""

    print("🔍 CHECKING SALES INVOICE STATUS VALUES")
    print("=" * 60)

    try:
        # Get distinct status values from Sales Invoice table
        status_query = """
            SELECT DISTINCT status, docstatus, COUNT(*) as count
            FROM `tabSales Invoice`
            GROUP BY status, docstatus
            ORDER BY status, docstatus
        """

        status_results = frappe.db.sql(status_query, as_dict=True)

        print("📊 Sales Invoice Status Values in Database:")
        print("-" * 50)
        for row in status_results:
            print(f"Status: '{row.status}' | DocStatus: {row.docstatus} | Count: {row.count}")

        # Check POS invoices specifically
        pos_status_query = """
            SELECT DISTINCT si.status, si.docstatus, COUNT(*) as count
            FROM `tabSales Invoice` si
            WHERE si.is_pos = 1
            GROUP BY si.status, si.docstatus
            ORDER BY si.status, si.docstatus
        """

        pos_status_results = frappe.db.sql(pos_status_query, as_dict=True)

        print("\n📊 POS Sales Invoice Status Values:")
        print("-" * 50)
        for row in pos_status_results:
            print(f"Status: '{row.status}' | DocStatus: {row.docstatus} | Count: {row.count}")

        # Check a few sample POS invoices
        print("\n📋 Sample POS Invoices:")
        print("-" * 50)

        sample_invoices = frappe.get_all("Sales Invoice",
            filters={"is_pos": 1, "docstatus": ["!=", 2]},
            fields=["name", "status", "docstatus", "grand_total"],
            limit=5
        )

        for inv in sample_invoices:
            print(f"Invoice: {inv.name} | Status: '{inv.status}' | DocStatus: {inv.docstatus} | Amount: {inv.grand_total}")

        # Check what happens when we cancel an invoice
        print("\n🔄 Testing Invoice Cancellation:")

        # Get a test invoice to cancel
        test_invoice = frappe.get_all("Sales Invoice",
            filters={"is_pos": 1, "docstatus": 1, "status": "Paid"},
            limit=1
        )

        if test_invoice:
            inv_name = test_invoice[0].name
            print(f"Testing with invoice: {inv_name}")

            # Get status before cancel
            inv_before = frappe.get_doc("Sales Invoice", inv_name)
            print(f"Before cancel - Status: '{inv_before.status}' | DocStatus: {inv_before.docstatus}")

            # Cancel the invoice
            inv_before.cancel()
            frappe.db.commit()

            # Get status after cancel
            inv_after = frappe.get_doc("Sales Invoice", inv_name)
            print(f"After cancel - Status: '{inv_after.status}' | DocStatus: {inv_after.docstatus}")

            # Restore the invoice
            inv_after.cancel()  # This will uncancel it
            frappe.db.commit()

            print(f"After uncancel - Status: '{inv_after.status}' | DocStatus: {inv_after.docstatus}")

        else:
            print("No suitable test invoice found")

        return True

    except Exception as e:
        print(f"❌ Error during status check: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = check_invoice_status_values()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("✅ Status check completed successfully!")
        else:
            print("❌ Status check failed")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Status check execution failed: {e}")
        frappe.destroy()
        exit(1)