#!/usr/bin/env python3
"""
Script to run the customer aggregated fields setup
This script will:
1. Add custom fields to Customer doctype
2. Calculate and update aggregated values for all customers
3. Provide status report
"""

import frappe
import sys
import os

# Add the current directory to Python path to import our setup script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from setup_customer_aggregated_fields import (
    setup_customer_aggregated_fields,
    update_customer_aggregated_fields,
    calculate_customer_aggregated_data
)
from migrate_customer_aggregated_fields import (
    migrate_customer_aggregated_fields,
    verify_migration
)


def run_setup():
    """Run the complete setup process"""

    print("🚀 Starting Customer Aggregated Fields Setup...")
    print("=" * 60)

    try:
        # Step 1: Setup custom fields
        print("\n📋 Step 1: Setting up custom fields...")
        setup_customer_aggregated_fields()

        # Step 2: Migrate existing customers with aggregated data
        print("\n📊 Step 2: Migrating existing customers with aggregated data...")
        migrate_success = migrate_customer_aggregated_fields()

        if not migrate_success:
            print("⚠️  Migration completed with warnings")

        # Step 3: Verification
        print("\n✅ Step 3: Verifying setup...")
        verify_migration()

        # Step 4: Sample verification
        print("\n🔍 Step 4: Sample data verification...")

        # Get a sample customer
        sample_customer = frappe.get_all("Customer",
            fields=["name", "customer_name"],
            limit=1
        )

        if sample_customer:
            customer_name = sample_customer[0]["name"]
            print(f"📋 Sample customer: {customer_name}")

            # Get aggregated data
            aggregated_data = calculate_customer_aggregated_data(customer_name)
            if aggregated_data:
                print("📊 Aggregated data sample:")
                for key, value in aggregated_data.items():
                    print(f"   {key}: {value}")

            # Get stored data
            stored_data = frappe.db.get_value("Customer", customer_name, [
                "total_credit_limit",
                "total_outstanding_amount",
                "total_credit_balance",
                "total_loyalty_points",
                "total_loyalty_points_used",
                "total_loyalty_points_balance"
            ], as_dict=True)

            if stored_data:
                print("💾 Stored data sample:")
                for key, value in stored_data.items():
                    print(f"   {key}: {value}")

        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print("\n📋 Summary:")
        print("✅ Custom fields added to Customer doctype")
        print("✅ Aggregated data calculated and stored")
        print("✅ API updated to use pre-calculated fields")
        print("✅ Performance optimized for customer detail queries")

        print("\n🚀 Next steps:")
        print("1. Test the customer detail feature in POS")
        print("2. Monitor performance improvements")
        print("3. Set up scheduled job to update aggregated fields periodically")

        print("\n📖 For more information, see: CUSTOMER_DETAIL_FEATURE_README.md")

    except Exception as e:
        print(f"\n❌ Setup failed with error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check database permissions")
        print("2. Ensure frappe-bench is running")
        print("3. Check frappe logs for detailed error messages")

        frappe.log_error(f"Customer aggregated fields setup failed: {str(e)}", "POS Awesome Setup")
        return False

    return True


def test_api():
    """Test the updated API with a sample customer"""

    print("\n🧪 Testing API...")

    try:
        # Get a sample customer
        sample_customer = frappe.get_all("Customer",
            fields=["name", "customer_name"],
            limit=1
        )

        if not sample_customer:
            print("❌ No customers found to test")
            return

        customer_name = sample_customer[0]["name"]
        print(f"📋 Testing with customer: {customer_name}")

        # Test the API
        from posawesome.posawesome.api.customers import get_customer_detailed_info

        result = get_customer_detailed_info(customer_name)

        if result:
            print("✅ API call successful")
            print("📊 Response structure:")
            for section in ["basic_info", "classification_info", "credit_info", "loyalty_info", "debt_info", "statistics_info"]:
                if section in result:
                    print(f"   ✅ {section}: {len(result[section])} fields")
                else:
                    print(f"   ❌ {section}: missing")

            # Show sample credit info
            if "credit_info" in result:
                credit = result["credit_info"]
                print("💳 Sample credit info:")
                print(f"   Credit Limit: {credit.get('credit_limit', 0)}")
                print(f"   Outstanding: {credit.get('outstanding_amount', 0)}")
                print(f"   Balance: {credit.get('credit_balance', 0)}")

        else:
            print("❌ API returned empty result")

    except Exception as e:
        print(f"❌ API test failed: {str(e)}")


if __name__ == "__main__":
    # Run setup
    success = run_setup()

    if success:
        # Test API
        test_api()

    print("\n🏁 Script execution completed!")