#!/usr/bin/env python3
"""
Test script to verify credit limit calculation with the new database structure
"""

import frappe
from setup_customer_aggregated_fields import calculate_customer_aggregated_data


def test_credit_limit_calculation():
    """Test credit limit calculation for a sample customer"""

    print("🧪 Testing Credit Limit Calculation...")
    print("=" * 60)

    # Get a sample customer
    customers = frappe.get_all("Customer",
        fields=["name", "customer_name"],
        limit=1
    )

    if not customers:
        print("❌ No customers found")
        print("Creating test customer with credit limit...")
        create_test_credit_data()
        return

    customer = customers[0]
    customer_name = customer["name"]

    print(f"📋 Testing customer: {customer_name}")
    print(f"👤 Customer Name: {customer['customer_name']}")

    # Test calculation
    aggregated_data = calculate_customer_aggregated_data(customer_name)

    if not aggregated_data:
        print("❌ Failed to calculate aggregated data")
        return

    print("\n📊 Calculated Results:")
    print(f"💰 Total Credit Limit: {aggregated_data['total_credit_limit']}")
    print(f"📈 Total Outstanding: {aggregated_data['total_outstanding_amount']}")
    print(f"💳 Credit Balance: {aggregated_data['total_credit_balance']}")
    print(f"🏢 Credit Companies: {aggregated_data['credit_companies']}")

    # Verify with direct database queries
    print("\n🔍 Verification with Direct Queries:")

    # Check credit limit entries
    credit_entries = frappe.db.sql("""
        SELECT company, credit_limit, bypass_credit_limit_check
        FROM `tabCustomer Credit Limit`
        WHERE parent = %s AND parenttype = 'Customer'
    """, (customer_name,), as_dict=True)

    if credit_entries:
        print("📋 Credit Limit Entries:")
        total_from_entries = 0
        for entry in credit_entries:
            print(f"   🏢 {entry['company']}: {entry['credit_limit']} (Bypass: {entry['bypass_credit_limit_check']})")
            total_from_entries += entry['credit_limit']

        print(f"   💰 Total from entries: {total_from_entries}")
    else:
        print("❌ No credit limit entries found")

    # Check outstanding amount
    outstanding_invoices = frappe.db.sql("""
        SELECT SUM(outstanding_amount) as total_outstanding
        FROM `tabSales Invoice`
        WHERE customer = %s
        AND docstatus = 1
        AND outstanding_amount > 0
    """, (customer_name,), as_dict=True)

    outstanding_direct = outstanding_invoices[0]["total_outstanding"] if outstanding_invoices and outstanding_invoices[0]["total_outstanding"] else 0
    print(f"📈 Direct Outstanding: {outstanding_direct}")

    # Calculate expected balance
    expected_balance = aggregated_data['total_credit_limit'] - outstanding_direct
    print(f"💳 Expected Balance: {expected_balance}")

    # Compare results
    print("\n📊 Comparison:")
    print(f"✅ Credit Limit Match: {aggregated_data['total_credit_limit'] == total_from_entries if credit_entries else 'N/A'}")
    print(f"✅ Outstanding Match: {aggregated_data['total_outstanding_amount'] == outstanding_direct}")
    print(f"✅ Balance Match: {aggregated_data['total_credit_balance'] == expected_balance}")

    print("\n✅ Test completed!")


def create_test_credit_data():
    """Create test data for credit limit calculation testing"""

    print("🛠️ Creating test credit data...")

    try:
        # Get existing company
        companies = frappe.get_all("Company", limit=1)
        if not companies:
            print("❌ No company found, cannot create test data")
            return

        company_name = companies[0]["name"]

        # Create a test customer
        if not frappe.db.exists("Customer", "TEST-CUST-CREDIT"):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "name": "TEST-CUST-CREDIT",
                "customer_name": "Test Customer Credit",
                "customer_group": "All Customer Groups",
                "territory": "All Territories"
            })
            customer.insert()
            print("✅ Created Test Customer")

        # Create credit limit entries
        credit_limits = [
            {"company": company_name, "credit_limit": 100000, "bypass_credit_limit_check": 0},
            {"company": company_name, "credit_limit": 50000, "bypass_credit_limit_check": 1},
        ]

        for cl in credit_limits:
            # Check if entry already exists
            existing = frappe.db.exists("Customer Credit Limit", {
                "parent": "TEST-CUST-CREDIT",
                "parenttype": "Customer",
                "company": cl["company"]
            })

            if not existing:
                credit_entry = frappe.get_doc({
                    "doctype": "Customer Credit Limit",
                    "parent": "TEST-CUST-CREDIT",
                    "parenttype": "Customer",
                    "parentfield": "credit_limits",
                    "company": cl["company"],
                    "credit_limit": cl["credit_limit"],
                    "bypass_credit_limit_check": cl["bypass_credit_limit_check"]
                })
                credit_entry.insert()
                print(f"✅ Created Credit Limit Entry: {cl['company']} - {cl['credit_limit']}")

        # Create a test invoice with outstanding amount
        if not frappe.db.exists("Sales Invoice", "TEST-INV-001"):
            invoice = frappe.get_doc({
                "doctype": "Sales Invoice",
                "name": "TEST-INV-001",
                "customer": "TEST-CUST-CREDIT",
                "company": company_name,
                "posting_date": frappe.utils.today(),
                "due_date": frappe.utils.add_days(frappe.utils.today(), 30),
                "grand_total": 75000,
                "outstanding_amount": 75000,
                "items": [{
                    "item_code": "Test Item",
                    "qty": 1,
                    "rate": 75000,
                    "amount": 75000
                }]
            })
            invoice.insert()
            invoice.submit()
            print("✅ Created Test Invoice with outstanding amount")

        print("📊 Expected Results:")
        print("   Total Credit Limit: 150,000")
        print("   Total Outstanding: 75,000")
        print("   Credit Balance: 75,000")
        print("   Credit Companies: Company Name")

        # Test the calculation
        test_credit_limit_calculation()

    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    try:
        test_credit_limit_calculation()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()