#!/usr/bin/env python3
"""
Test script to verify payment breakdown calculations in shift reports
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

def test_payment_breakdown():
    """Test payment breakdown calculations in shift reports"""

    print("💳 TESTING PAYMENT BREAKDOWN CALCULATIONS")
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

        # Get POS profile to check available payment methods
        pos_profile = frappe.get_doc("POS Profile", opening_shift.pos_profile)
        print(f"✅ POS Profile: {pos_profile.name}")

        # Get available payment methods
        payment_methods = []
        if hasattr(pos_profile, 'payments') and pos_profile.payments:
            for payment in pos_profile.payments:
                payment_methods.append(payment.mode_of_payment)
                print(f"   - Available payment method: {payment.mode_of_payment}")

        if not payment_methods:
            print("❌ No payment methods configured in POS Profile")
            return False

        # Step 2: Create test invoices with different payment methods
        print("\n2. Creating test invoices with different payment methods...")

        # Get customer and item
        customers = frappe.get_all("Customer", limit=1)
        items = frappe.get_all("Item", filters={"is_sales_item": 1}, limit=1)

        if not customers or not items:
            print("❌ Missing customer or item data")
            return False

        customer = customers[0].name
        item = items[0].name

        test_invoices = []

        # Create invoices with different payment methods
        for i, payment_method in enumerate(payment_methods[:3]):  # Use up to 3 payment methods
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
                    "rate": 100 + (i * 50)  # Different amounts
                }],
                "payments": [{
                    "mode_of_payment": payment_method,
                    "amount": 100 + (i * 50)
                }]
            })

            invoice.insert()
            invoice.submit()
            frappe.db.commit()

            test_invoices.append({
                "invoice": invoice,
                "payment_method": payment_method,
                "amount": invoice.grand_total
            })

            print(f"✅ Created invoice: {invoice.name} - Payment: {payment_method} - Amount: {invoice.grand_total}")

        # Step 3: Check payment breakdown in shift report
        print("\n3. Checking payment breakdown in shift report...")

        shift_report.reload()

        # Get payment breakdown from shift report
        payment_breakdown = {}
        if hasattr(shift_report, 'payment_breakdown') and shift_report.payment_breakdown:
            try:
                payment_breakdown = json.loads(shift_report.payment_breakdown)
            except:
                payment_breakdown = {}

        print("   - Payment breakdown from shift report:")
        for method, amount in payment_breakdown.items():
            print(f"     * {method}: {amount}")

        # Calculate expected payment breakdown
        expected_breakdown = {}
        for test_inv in test_invoices:
            method = test_inv["payment_method"]
            amount = test_inv["amount"]
            if method in expected_breakdown:
                expected_breakdown[method] += amount
            else:
                expected_breakdown[method] = amount

        print("   - Expected payment breakdown:")
        for method, amount in expected_breakdown.items():
            print(f"     * {method}: {amount}")

        # Verify payment breakdown
        breakdown_correct = True
        for method, expected_amount in expected_breakdown.items():
            actual_amount = payment_breakdown.get(method, 0)
            if abs(actual_amount - expected_amount) > 0.01:
                print(f"❌ Payment method {method}: expected {expected_amount}, got {actual_amount}")
                breakdown_correct = False
            else:
                print(f"✅ Payment method {method}: {actual_amount} ✓")

        # Check for unexpected payment methods
        for method, amount in payment_breakdown.items():
            if method not in expected_breakdown:
                print(f"❌ Unexpected payment method {method}: {amount}")
                breakdown_correct = False

        if breakdown_correct:
            print("✅ Payment breakdown calculations are correct!")
        else:
            print("❌ Payment breakdown calculations are incorrect!")
            return False

        # Step 4: Test with return invoice
        print("\n4. Creating return invoice...")

        return_payment_method = payment_methods[0] if payment_methods else "Cash"

        return_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": opening_shift.company,
            "pos_profile": opening_shift.pos_profile,
            "is_pos": 1,
            "is_return": 1,
            "posa_pos_opening_shift": opening_shift_name,
            "items": [{
                "item_code": item,
                "qty": -1,
                "rate": 100
            }],
            "payments": [{
                "mode_of_payment": return_payment_method,
                "amount": -100  # Negative for return
            }]
        })

        return_invoice.insert()
        return_invoice.submit()
        frappe.db.commit()

        print(f"✅ Created return invoice: {return_invoice.name} - Amount: {return_invoice.grand_total}")

        # Step 5: Check payment breakdown after return
        print("\n5. Checking payment breakdown after return...")

        shift_report.reload()

        # Get updated payment breakdown
        updated_breakdown = {}
        if hasattr(shift_report, 'payment_breakdown') and shift_report.payment_breakdown:
            try:
                updated_breakdown = json.loads(shift_report.payment_breakdown)
            except:
                updated_breakdown = {}

        print("   - Updated payment breakdown:")
        for method, amount in updated_breakdown.items():
            print(f"     * {method}: {amount}")

        # Expected breakdown should include return (negative amount)
        expected_updated_breakdown = expected_breakdown.copy()
        return_amount = return_invoice.grand_total
        if return_payment_method in expected_updated_breakdown:
            expected_updated_breakdown[return_payment_method] += return_amount
        else:
            expected_updated_breakdown[return_payment_method] = return_amount

        print("   - Expected updated breakdown:")
        for method, amount in expected_updated_breakdown.items():
            print(f"     * {method}: {amount}")

        # Verify updated breakdown
        updated_breakdown_correct = True
        for method, expected_amount in expected_updated_breakdown.items():
            actual_amount = updated_breakdown.get(method, 0)
            if abs(actual_amount - expected_amount) > 0.01:
                print(f"❌ Payment method {method}: expected {expected_amount}, got {actual_amount}")
                updated_breakdown_correct = False
            else:
                print(f"✅ Payment method {method}: {actual_amount} ✓")

        if updated_breakdown_correct:
            print("✅ Payment breakdown after return is correct!")
        else:
            print("❌ Payment breakdown after return is incorrect!")
            return False

        # Cleanup
        print("\n6. Cleaning up test data...")
        try:
            # Cancel and delete all test invoices
            for test_inv in test_invoices:
                inv = test_inv["invoice"]
                if inv.docstatus == 1:
                    inv.cancel()
                frappe.delete_doc("Sales Invoice", inv.name, force=True)

            # Cancel and delete return invoice
            if return_invoice.docstatus == 1:
                return_invoice.cancel()
            frappe.delete_doc("Sales Invoice", return_invoice.name, force=True)

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
        success = test_payment_breakdown()
        frappe.destroy()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED - Payment breakdown calculations are working correctly!")
        else:
            print("❌ TEST FAILED - Issues with payment breakdown calculations")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        frappe.destroy()
        exit(1)