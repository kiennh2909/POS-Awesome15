#!/usr/bin/env python3
"""
Test script for Outstanding Invoices API
Run this script to debug outstanding invoices loading issues
"""

import frappe
import json
from frappe.utils import nowdate

def test_outstanding_invoices_api():
    """Test the get_outstanding_invoices API directly"""

    print("=" * 60)
    print("TESTING OUTSTANDING INVOICES API")
    print("=" * 60)

    # Test parameters
    test_params = [
        {
            "customer": "Test Customer",
            "company": "Test Company",
            "currency": "USD",
            "pos_profile": None
        },
        {
            "customer": None,  # Test with no customer
            "company": "Test Company",
            "currency": "USD",
            "pos_profile": None
        }
    ]

    for i, params in enumerate(test_params, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Parameters: {params}")

        try:
            # Import the function
            from posawesome.posawesome.api.payment_entry import get_outstanding_invoices

            # Call the function
            result = get_outstanding_invoices(**params)

            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result) if isinstance(result, list) else 'N/A'}")

            if isinstance(result, list) and len(result) > 0:
                print("First invoice sample:")
                print(json.dumps(result[0], indent=2, default=str))
            elif isinstance(result, list):
                print("No invoices found")
            else:
                print(f"Unexpected result: {result}")

        except Exception as e:
            print(f"ERROR: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()

def check_database_data():
    """Check if there are any outstanding invoices in the database"""

    print("\n" + "=" * 60)
    print("CHECKING DATABASE FOR OUTSTANDING INVOICES")
    print("=" * 60)

    try:
        # Check total sales invoices
        total_invoices = frappe.db.count("Sales Invoice")
        print(f"Total Sales Invoices: {total_invoices}")

        # Check submitted invoices
        submitted_invoices = frappe.db.count("Sales Invoice", {"docstatus": 1})
        print(f"Submitted Sales Invoices: {submitted_invoices}")

        # Check invoices with outstanding amount > 0
        outstanding_count = frappe.db.count("Sales Invoice", {
            "docstatus": 1,
            "outstanding_amount": (">", 0),
            "is_return": 0
        })
        print(f"Invoices with outstanding amount > 0: {outstanding_count}")

        if outstanding_count > 0:
            # Get sample outstanding invoices
            sample_invoices = frappe.get_all("Sales Invoice",
                filters={
                    "docstatus": 1,
                    "outstanding_amount": (">", 0),
                    "is_return": 0
                },
                fields=["name", "customer", "customer_name", "outstanding_amount", "grand_total", "posting_date"],
                limit=5
            )

            print("\nSample outstanding invoices:")
            for inv in sample_invoices:
                print(f"- {inv.name}: Customer={inv.customer}, Outstanding={inv.outstanding_amount}, Total={inv.grand_total}")

        # Check customers
        customers = frappe.get_all("Customer", fields=["name", "customer_name"], limit=10)
        print(f"\nTotal Customers: {len(customers)}")
        if customers:
            print("Sample customers:")
            for cust in customers[:5]:
                print(f"- {cust.name}: {cust.customer_name}")

        # Check companies
        companies = frappe.get_all("Company", fields=["name"], limit=5)
        print(f"\nCompanies: {[c.name for c in companies]}")

    except Exception as e:
        print(f"Database check error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_party_account():
    """Test party account retrieval"""

    print("\n" + "=" * 60)
    print("TESTING PARTY ACCOUNT RETRIEVAL")
    print("=" * 60)

    try:
        from posawesome.posawesome.api.payment_entry import get_party_account

        test_customers = ["Test Customer", "Default Customer", ""]

        for customer in test_customers:
            try:
                account = get_party_account("Customer", customer, "Test Company")
                print(f"Customer '{customer}' -> Party Account: {account}")
            except Exception as e:
                print(f"Customer '{customer}' -> Error: {str(e)}")

    except Exception as e:
        print(f"Party account test error: {str(e)}")

if __name__ == "__main__":
    # Initialize Frappe (if not already initialized)
    try:
        frappe.init(site="your-site-name")  # Replace with your actual site name
        frappe.connect()
        frappe.db.connect()

        print("Starting Outstanding Invoices Debug Test...")
        print(f"Current date: {nowdate()}")

        # Run tests
        check_database_data()
        test_party_account()
        test_outstanding_invoices_api()

        print("\n" + "=" * 60)
        print("DEBUG TEST COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"Test initialization error: {str(e)}")
        print("Make sure you're running this from a proper Frappe environment")
    finally:
        try:
            frappe.destroy()
        except:
            pass