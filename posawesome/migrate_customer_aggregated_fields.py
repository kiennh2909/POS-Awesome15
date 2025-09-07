#!/usr/bin/env python3
"""
Migration script to update existing customers with aggregated field values
This script should be run after setting up the custom fields
"""

import frappe
from setup_customer_aggregated_fields import calculate_customer_aggregated_data


def migrate_customer_aggregated_fields():
    """Migrate existing customers to use aggregated fields"""

    print("🚀 Starting Customer Aggregated Fields Migration...")
    print("=" * 60)

    try:
        # Get all customers
        customers = frappe.get_all("Customer",
            fields=["name", "customer_name"],
            limit_page_length=0
        )

        if not customers:
            print("❌ No customers found to migrate")
            return

        print(f"📊 Found {len(customers)} customers to migrate")

        migrated_count = 0
        error_count = 0

        for customer in customers:
            try:
                customer_name = customer["name"]
                customer_display_name = customer["customer_name"] or customer_name

                # Calculate aggregated data
                aggregated_data = calculate_customer_aggregated_data(customer_name)

                if aggregated_data:
                    # Update customer with aggregated data
                    customer_doc = frappe.get_doc("Customer", customer_name)

                    # Use db_set for each field to ensure proper saving
                    customer_doc.db_set("total_credit_limit", aggregated_data["total_credit_limit"])
                    customer_doc.db_set("total_outstanding_amount", aggregated_data["total_outstanding_amount"])
                    customer_doc.db_set("total_credit_balance", aggregated_data["total_credit_balance"])
                    customer_doc.db_set("total_loyalty_points", aggregated_data["total_loyalty_points"])
                    customer_doc.db_set("total_loyalty_points_used", aggregated_data["total_loyalty_points_used"])
                    customer_doc.db_set("total_loyalty_points_balance", aggregated_data["total_loyalty_points_balance"])
                    customer_doc.db_set("aggregated_fields_last_updated", frappe.utils.now())

                    migrated_count += 1

                    if migrated_count % 50 == 0:
                        print(f"✅ Migrated {migrated_count} customers...")
                        frappe.db.commit()  # Commit every 50 records

                else:
                    print(f"⚠️  No data calculated for customer: {customer_display_name}")
                    error_count += 1

            except Exception as e:
                print(f"❌ Error migrating customer {customer_display_name}: {str(e)}")
                error_count += 1
                continue

        # Final commit
        frappe.db.commit()

        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED!")
        print("=" * 60)
        print(f"✅ Successfully migrated: {migrated_count} customers")
        print(f"❌ Errors: {error_count} customers")
        print(f"📊 Total processed: {len(customers)} customers")

        # Show summary statistics
        print("\n📈 Migration Summary:")

        # Get some statistics
        customers_with_credit = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabCustomer`
            WHERE total_credit_limit > 0
        """, as_dict=True)

        customers_with_loyalty = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabCustomer`
            WHERE total_loyalty_points > 0
        """, as_dict=True)

        total_credit_limit = frappe.db.sql("""
            SELECT SUM(total_credit_limit) as total
            FROM `tabCustomer`
        """, as_dict=True)

        total_loyalty_points = frappe.db.sql("""
            SELECT SUM(total_loyalty_points) as total
            FROM `tabCustomer`
        """, as_dict=True)

        print(f"💰 Customers with credit limit: {customers_with_credit[0]['count'] if customers_with_credit else 0}")
        print(f"⭐ Customers with loyalty points: {customers_with_loyalty[0]['count'] if customers_with_loyalty else 0}")
        print(f"💵 Total credit limit across all customers: {total_credit_limit[0]['total'] if total_credit_limit and total_credit_limit[0]['total'] else 0:,.0f}")
        print(f"🎁 Total loyalty points across all customers: {total_loyalty_points[0]['total'] if total_loyalty_points and total_loyalty_points[0]['total'] else 0:,.0f}")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        frappe.log_error(f"Customer aggregated fields migration failed: {str(e)}", "POS Awesome Migration")
        return False

    return True


def verify_migration():
    """Verify that migration was successful"""

    print("\n🔍 Verifying Migration...")

    try:
        # Check if custom fields exist
        custom_fields = [
            "total_credit_limit",
            "total_outstanding_amount",
            "total_credit_balance",
            "total_loyalty_points",
            "total_loyalty_points_used",
            "total_loyalty_points_balance",
            "aggregated_fields_last_updated"
        ]

        missing_fields = []
        for fieldname in custom_fields:
            if not frappe.db.exists("Custom Field", {
                "dt": "Customer",
                "fieldname": fieldname
            }):
                missing_fields.append(fieldname)

        if missing_fields:
            print(f"❌ Missing custom fields: {', '.join(missing_fields)}")
            return False

        print("✅ All custom fields exist")

        # Check if data was populated
        customers_with_data = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabCustomer`
            WHERE aggregated_fields_last_updated IS NOT NULL
        """, as_dict=True)

        if customers_with_data and customers_with_data[0]['count'] > 0:
            print(f"✅ {customers_with_data[0]['count']} customers have aggregated data")
        else:
            print("⚠️  No customers have aggregated data yet")

        # Sample verification
        sample_customer = frappe.get_all("Customer",
            fields=["name", "customer_name"],
            limit=1
        )

        if sample_customer:
            customer_name = sample_customer[0]["name"]
            customer_data = frappe.db.get_value("Customer", customer_name, [
                "total_credit_limit",
                "total_outstanding_amount",
                "total_credit_balance",
                "total_loyalty_points",
                "total_loyalty_points_used",
                "total_loyalty_points_balance",
                "aggregated_fields_last_updated"
            ], as_dict=True)

            if customer_data:
                print(f"\n📋 Sample customer data ({customer_name}):")
                for key, value in customer_data.items():
                    if key == "aggregated_fields_last_updated" and value:
                        print(f"   {key}: {value}")
                    elif isinstance(value, (int, float)) and value != 0:
                        print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False


def main():
    """Main migration function"""

    print("🛠️  POS Awesome - Customer Aggregated Fields Migration")
    print("=" * 60)

    # Step 1: Run migration
    success = migrate_customer_aggregated_fields()

    if success:
        # Step 2: Verify migration
        verify_migration()

        print("\n" + "=" * 60)
        print("🎉 MIGRATION SUCCESSFUL!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("1. Test the customer detail feature in POS")
        print("2. Monitor performance improvements")
        print("3. Set up scheduled job for regular updates")
        print("4. Consider setting up real-time updates for critical fields")

        print("\n📖 For more information, see: CUSTOMER_DETAIL_FEATURE_README.md")

    else:
        print("\n❌ Migration failed. Please check the error messages above.")


if __name__ == "__main__":
    main()