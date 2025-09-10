#!/usr/bin/env python3
"""
Test script to verify shift report calculations (invoice_count, total_sales, total_returns)
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

def test_shift_report_calculations():
    """Test shift report calculations when invoices are created"""

    print("🧮 TESTING SHIFT REPORT CALCULATIONS")
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
        print(f"   - Initial invoice count: {shift_report.invoice_count}")
        print(f"   - Initial total sales: {shift_report.total_sales}")
        print(f"   - Initial total returns: {shift_report.total_returns}")

        # Step 2: Create multiple test invoices
        print("\n2. Creating test invoices...")

        # Get POS profile and company
        pos_profile = opening_shift.pos_profile
        company = opening_shift.company

        # Get customer and item
        customers = frappe.get_all("Customer", limit=1)
        items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=1)

        if not customers or not items:
            print("❌ Missing customer or item data")
            return False

        customer = customers[0].name
        item = items[0].name

        test_invoices = []

        # Create 3 sales invoices
        for i in range(3):
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
                    "rate": 100 + (i * 50)  # Different amounts: 100, 150, 200
                }]
            })

            invoice.insert()
            invoice.submit()
            frappe.db.commit()

            test_invoices.append(invoice)
            print(f"✅ Created invoice {i+1}: {invoice.name} - Amount: {invoice.grand_total}")

        # Step 3: Check shift report calculations after creating invoices
        print("\n3. Checking shift report calculations...")

        shift_report.reload()

        expected_invoice_count = 3
        expected_total_sales = sum(inv.grand_total for inv in test_invoices)
        expected_total_returns = 0

        print(f"   - Expected invoice count: {expected_invoice_count}")
        print(f"   - Actual invoice count: {shift_report.invoice_count}")
        print(f"   - Expected total sales: {expected_total_sales}")
        print(f"   - Actual total sales: {shift_report.total_sales}")
        print(f"   - Expected total returns: {expected_total_returns}")
        print(f"   - Actual total returns: {shift_report.total_returns}")

        # Verify calculations
        calculations_correct = (
            shift_report.invoice_count == expected_invoice_count and
            abs(shift_report.total_sales - expected_total_sales) < 0.01 and
            shift_report.total_returns == expected_total_returns
        )

        if calculations_correct:
            print("✅ All calculations are correct!")
        else:
            print("❌ Calculations are incorrect!")
            return False

        # Step 4: Create a return invoice
        print("\n4. Creating return invoice...")

        return_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": company,
            "pos_profile": pos_profile,
            "is_pos": 1,
            "is_return": 1,
            "posa_pos_opening_shift": opening_shift_name,
            "items": [{
                "item_code": item,
                "qty": -1,  # Return 1 item
                "rate": 100
            }]
        })

        return_invoice.insert()
        return_invoice.submit()
        frappe.db.commit()

        print(f"✅ Created return invoice: {return_invoice.name} - Amount: {return_invoice.grand_total}")

        # Step 5: Check calculations after return
        print("\n5. Checking calculations after return...")

        shift_report.reload()

        expected_invoice_count = 4  # 3 sales + 1 return
        expected_total_sales = sum(inv.grand_total for inv in test_invoices)  # Same as before
        expected_total_returns = return_invoice.grand_total  # Negative amount

        print(f"   - Expected invoice count: {expected_invoice_count}")
        print(f"   - Actual invoice count: {shift_report.invoice_count}")
        print(f"   - Expected total sales: {expected_total_sales}")
        print(f"   - Actual total sales: {shift_report.total_sales}")
        print(f"   - Expected total returns: {expected_total_returns}")
        print(f"   - Actual total returns: {shift_report.total_returns}")

        # Verify calculations after return
        return_calculations_correct = (
            shift_report.invoice_count == expected_invoice_count and
            abs(shift_report.total_sales - expected_total_sales) < 0.01 and
            abs(shift_report.total_returns - expected_total_returns) < 0.01
        )

        if return_calculations_correct:
            print("✅ Return calculations are correct!")
        else:
            print("❌ Return calculations are incorrect!")
            return False

        # Step 6: Cancel one invoice and check calculations
        print("\n6. Cancelling one invoice...")

        invoice_to_cancel = test_invoices[0]
        invoice_to_cancel.cancel()
        frappe.db.commit()

        print(f"✅ Cancelled invoice: {invoice_to_cancel.name}")

        # Step 7: Check calculations after cancellation
        print("\n7. Checking calculations after cancellation...")

        shift_report.reload()

        expected_invoice_count = 4  # Still 4, but one marked as cancelled
        expected_total_sales = sum(inv.grand_total for inv in test_invoices[1:])  # Exclude cancelled
        expected_total_returns = return_invoice.grand_total

        print(f"   - Expected invoice count: {expected_invoice_count}")
        print(f"   - Actual invoice count: {shift_report.invoice_count}")
        print(f"   - Expected total sales: {expected_total_sales}")
        print(f"   - Actual total sales: {shift_report.total_sales}")
        print(f"   - Expected total returns: {expected_total_returns}")
        print(f"   - Actual total returns: {shift_report.total_returns}")

        # Verify calculations after cancellation
        cancel_calculations_correct = (
            shift_report.invoice_count == expected_invoice_count and
            abs(shift_report.total_sales - expected_total_sales) < 0.01 and
            abs(shift_report.total_returns - expected_total_returns) < 0.01
        )

        if cancel_calculations_correct:
            print("✅ Cancellation calculations are correct!")
        else:
            print("❌ Cancellation calculations are incorrect!")
            return False

        # Cleanup
        print("\n8. Cleaning up test data...")
        try:
            # Cancel and delete all test invoices
            for inv in test_invoices + [return_invoice]:
                if inv.docstatus == 1:
                    inv.cancel()
                frappe.delete_doc("Sales Invoice", inv.name, force=True)

            frappe.db.commit()
            print("✅ Cleaned up all test invoices")

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
        success = test_shift_report_calculations()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED - Shift report calculations are working correctly!")
        else:
            print("❌ TEST FAILED - Issues with shift report calculations")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)