#!/usr/bin/env python3
"""
Test script to verify loyalty points calculation with the new database structure
"""

import frappe
from setup_customer_aggregated_fields import calculate_customer_aggregated_data


def test_loyalty_calculation():
    """Test loyalty points calculation for a sample customer"""

    print("🧪 Testing Loyalty Points Calculation...")
    print("=" * 60)

    # Get a sample customer with loyalty program
    customers_with_loyalty = frappe.get_all("Customer",
        filters={"loyalty_program": ["!=", ""]},
        fields=["name", "customer_name", "loyalty_program"],
        limit=1
    )

    if not customers_with_loyalty:
        print("❌ No customers with loyalty program found")
        print("Creating a test customer with loyalty program...")

        # Create test data
        create_test_loyalty_data()
        return

    customer = customers_with_loyalty[0]
    customer_name = customer["name"]

    print(f"📋 Testing customer: {customer_name}")
    print(f"👤 Customer Name: {customer['customer_name']}")
    print(f"⭐ Loyalty Program: {customer['loyalty_program']}")

    # Test calculation
    aggregated_data = calculate_customer_aggregated_data(customer_name)

    if not aggregated_data:
        print("❌ Failed to calculate aggregated data")
        return

    print("\n📊 Calculated Results:")
    print(f"💰 Total Credit Limit: {aggregated_data['total_credit_limit']}")
    print(f"📈 Total Outstanding: {aggregated_data['total_outstanding_amount']}")
    print(f"💳 Credit Balance: {aggregated_data['total_credit_balance']}")
    print(f"⭐ Total Loyalty Points: {aggregated_data['total_loyalty_points']}")
    print(f"🔻 Points Used: {aggregated_data['total_loyalty_points_used']}")
    print(f"📊 Points Balance: {aggregated_data['total_loyalty_points_balance']}")
    print(f"🔄 Conversion Factor: {aggregated_data['conversion_factor']}")

    # Verify with direct database queries
    print("\n🔍 Verification with Direct Queries:")

    # Check loyalty program details
    lp_details = frappe.db.get_value("Loyalty Program", customer["loyalty_program"],
        ["conversion_factor", "loyalty_program_name"], as_dict=True)
    if lp_details:
        print(f"📋 Program Name: {lp_details['loyalty_program_name']}")
        print(f"🔄 DB Conversion Factor: {lp_details['conversion_factor']}")

    # Check loyalty point entries
    earned_points = frappe.db.sql("""
        SELECT SUM(loyalty_points) as earned
        FROM `tabLoyalty Point Entry`
        WHERE customer = %s AND loyalty_points > 0
    """, (customer_name,), as_dict=True)

    used_points = frappe.db.sql("""
        SELECT SUM(ABS(loyalty_points)) as used
        FROM `tabLoyalty Point Entry`
        WHERE customer = %s AND loyalty_points < 0
    """, (customer_name,), as_dict=True)

    print(f"💰 Direct Query - Earned: {earned_points[0]['earned'] if earned_points[0]['earned'] else 0}")
    print(f"🔻 Direct Query - Used: {used_points[0]['used'] if used_points[0]['used'] else 0}")

    # Check redemption entries
    redemption_points = frappe.db.sql("""
        SELECT SUM(redeemed_points) as redeemed
        FROM `tabLoyalty Point Entry Redemption`
        WHERE parent IN (
            SELECT name FROM `tabLoyalty Point Entry`
            WHERE customer = %s
        )
    """, (customer_name,), as_dict=True)

    print(f"🎁 Redemption Points: {redemption_points[0]['redeemed'] if redemption_points[0]['redeemed'] else 0}")

    print("\n✅ Test completed!")


def create_test_loyalty_data():
    """Create test data for loyalty calculation testing"""

    print("🛠️ Creating test loyalty data...")

    try:
        # Create a test loyalty program
        if not frappe.db.exists("Loyalty Program", "Test Loyalty Program"):
            lp = frappe.get_doc({
                "doctype": "Loyalty Program",
                "loyalty_program_name": "Test Loyalty Program",
                "loyalty_program_type": "Single Tier",
                "conversion_factor": 0.1,  # 10 points per 100 VND
                "from_date": "2024-01-01",
                "to_date": "2024-12-31",
                "company": frappe.get_all("Company", limit=1)[0]["name"]
            })
            lp.insert()
            print("✅ Created Test Loyalty Program")

        # Create a test customer
        if not frappe.db.exists("Customer", "TEST-CUST-LOYALTY"):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "name": "TEST-CUST-LOYALTY",
                "customer_name": "Test Customer Loyalty",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "loyalty_program": "Test Loyalty Program"
            })
            customer.insert()
            print("✅ Created Test Customer")

        # Create some loyalty point entries
        entries = [
            {"loyalty_points": 100, "purchase_amount": 1000},  # Earned
            {"loyalty_points": 50, "purchase_amount": 500},    # Earned
            {"loyalty_points": -25, "purchase_amount": 0},     # Used
        ]

        for i, entry in enumerate(entries):
            lpe = frappe.get_doc({
                "doctype": "Loyalty Point Entry",
                "loyalty_program": "Test Loyalty Program",
                "customer": "TEST-CUST-LOYALTY",
                "loyalty_points": entry["loyalty_points"],
                "purchase_amount": entry["purchase_amount"],
                "posting_date": frappe.utils.today(),
                "company": frappe.get_all("Company", limit=1)[0]["name"]
            })
            lpe.insert()

            # Create redemption entry for used points
            if entry["loyalty_points"] < 0:
                redemption = frappe.get_doc({
                    "doctype": "Loyalty Point Entry Redemption",
                    "parent": lpe.name,
                    "parenttype": "Loyalty Point Entry",
                    "parentfield": "redemption",
                    "redeemed_points": abs(entry["loyalty_points"]),
                    "redemption_date": frappe.utils.today()
                })
                redemption.insert()

        print("✅ Created Test Loyalty Point Entries")
        print("📊 Expected Results:")
        print("   Total Earned: 150 points")
        print("   Total Used: 25 points")
        print("   Balance: 125 points")
        print("   Conversion Factor: 0.1")

        # Test the calculation
        test_loyalty_calculation()

    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")


def main():
    """Main function"""
    try:
        test_loyalty_calculation()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()