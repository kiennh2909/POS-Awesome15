#!/usr/bin/env python3
"""
Setup script to add aggregated fields to Customer doctype
This script adds custom fields to store calculated values for better performance
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def setup_customer_aggregated_fields():
    """Add aggregated fields to Customer doctype for better performance"""

    print("🚀 Setting up Customer aggregated fields...")

    # Define the custom fields to add
    custom_fields = [
        # Credit related fields
        {
            "dt": "Customer",
            "fieldname": "total_credit_limit",
            "label": "Total Credit Limit",
            "fieldtype": "Currency",
            "precision": "2",
            "default": "0",
            "read_only": 1,
            "description": "Total credit limit from Customer Credit Limit table",
            "insert_after": "payment_terms",
        },
        {
            "dt": "Customer",
            "fieldname": "total_outstanding_amount",
            "label": "Total Outstanding Amount",
            "fieldtype": "Currency",
            "precision": "2",
            "default": "0",
            "read_only": 1,
            "description": "Total outstanding amount from all invoices",
            "insert_after": "total_credit_limit",
        },
        {
            "dt": "Customer",
            "fieldname": "total_credit_balance",
            "label": "Total Credit Balance",
            "fieldtype": "Currency",
            "precision": "2",
            "default": "0",
            "read_only": 1,
            "description": "Total available credit balance",
            "insert_after": "total_outstanding_amount",
        },

        # Loyalty related fields
        {
            "dt": "Customer",
            "fieldname": "total_loyalty_points",
            "label": "Total Loyalty Points",
            "fieldtype": "Float",
            "precision": "2",
            "default": "0",
            "read_only": 1,
            "description": "Total loyalty points earned",
            "insert_after": "loyalty_program_tier",
        },
        {
            "dt": "Customer",
            "fieldname": "total_loyalty_points_used",
            "label": "Total Loyalty Points Used",
            "fieldtype": "Float",
            "precision": "2",
            "default": "0",
            "read_only": 1,
            "description": "Total loyalty points redeemed/used",
            "insert_after": "total_loyalty_points",
        },
        {
            "dt": "Customer",
            "fieldname": "total_loyalty_points_balance",
            "label": "Total Loyalty Points Balance",
            "fieldtype": "Float",
            "precision": "2",
            "default": "0",
            "read_only": 1,
            "description": "Current loyalty points balance",
            "insert_after": "total_loyalty_points_used",
        },

        # Last updated timestamp
        {
            "dt": "Customer",
            "fieldname": "aggregated_fields_last_updated",
            "label": "Aggregated Fields Last Updated",
            "fieldtype": "Datetime",
            "read_only": 1,
            "description": "Last time aggregated fields were updated",
            "insert_after": "total_loyalty_points_balance",
        },
    ]

    # Create custom fields
    for field_config in custom_fields:
        try:
            # Check if field already exists
            existing_field = frappe.db.exists("Custom Field", {
                "dt": field_config["dt"],
                "fieldname": field_config["fieldname"]
            })

            if existing_field:
                print(f"✅ Field {field_config['fieldname']} already exists, skipping...")
                continue

            # Create the custom field
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": field_config["dt"],
                "fieldname": field_config["fieldname"],
                "label": field_config["label"],
                "fieldtype": field_config["fieldtype"],
                "precision": field_config.get("precision", ""),
                "default": field_config.get("default", ""),
                "read_only": field_config.get("read_only", 0),
                "description": field_config.get("description", ""),
                "insert_after": field_config.get("insert_after", ""),
            })

            custom_field.insert(ignore_permissions=True)
            print(f"✅ Created custom field: {field_config['fieldname']}")

        except Exception as e:
            print(f"❌ Error creating field {field_config['fieldname']}: {str(e)}")
            continue

    print("🎉 Custom fields setup completed!")


def update_customer_aggregated_fields(customer_name=None):
    """
    Update aggregated fields for a specific customer or all customers

    Args:
        customer_name (str): Specific customer name, if None, update all customers
    """

    print(f"🔄 Updating aggregated fields for {'all customers' if not customer_name else f'customer: {customer_name}'}...")

    # Get customers to update
    if customer_name:
        customers = [customer_name]
    else:
        customers = frappe.get_all("Customer", fields=["name"], limit_page_length=0)

    updated_count = 0

    for customer_data in customers:
        try:
            customer_name = customer_data if isinstance(customer_data, str) else customer_data["name"]

            # Calculate aggregated values
            aggregated_data = calculate_customer_aggregated_data(customer_name)

            if aggregated_data:
                # Update customer with aggregated data using db_set_value for each field
                customer_doc = frappe.get_doc("Customer", customer_name)

                customer_doc.db_set("total_credit_limit", aggregated_data["total_credit_limit"])
                customer_doc.db_set("total_outstanding_amount", aggregated_data["total_outstanding_amount"])
                customer_doc.db_set("total_credit_balance", aggregated_data["total_credit_balance"])
                customer_doc.db_set("total_loyalty_points", aggregated_data["total_loyalty_points"])
                customer_doc.db_set("total_loyalty_points_used", aggregated_data["total_loyalty_points_used"])
                customer_doc.db_set("total_loyalty_points_balance", aggregated_data["total_loyalty_points_balance"])
                customer_doc.db_set("aggregated_fields_last_updated", frappe.utils.now())

                updated_count += 1

                if updated_count % 10 == 0:
                    print(f"✅ Updated {updated_count} customers...")

        except Exception as e:
            print(f"❌ Error updating customer {customer_name}: {str(e)}")
            continue

    print(f"🎉 Updated aggregated fields for {updated_count} customers")


def calculate_customer_aggregated_data(customer_name):
    """
    Calculate all aggregated values for a customer

    Args:
        customer_name (str): Customer name

    Returns:
        dict: Aggregated data
    """

    try:
        # 1. Credit related calculations
        # Get credit limit from Customer Credit Limit table (child table of Customer)
        credit_limits = frappe.db.sql("""
            SELECT
                SUM(credit_limit) as total_credit_limit,
                GROUP_CONCAT(DISTINCT company SEPARATOR ', ') as companies
            FROM `tabCustomer Credit Limit`
            WHERE parent = %s
            AND parenttype = 'Customer'
        """, (customer_name,), as_dict=True)

        total_credit_limit = credit_limits[0]["total_credit_limit"] if credit_limits and credit_limits[0]["total_credit_limit"] else 0
        credit_companies = credit_limits[0]["companies"] if credit_limits and credit_limits[0]["companies"] else ""

        # Get outstanding amount from invoices
        outstanding_invoices = frappe.db.sql("""
            SELECT SUM(outstanding_amount) as total_outstanding
            FROM `tabSales Invoice`
            WHERE customer = %s
            AND docstatus = 1
            AND outstanding_amount > 0
        """, (customer_name,), as_dict=True)

        total_outstanding = outstanding_invoices[0]["total_outstanding"] if outstanding_invoices and outstanding_invoices[0]["total_outstanding"] else 0

        # Calculate credit balance
        total_credit_balance = total_credit_limit - total_outstanding

        # 2. Loyalty related calculations
        # Get loyalty program info first
        customer_loyalty_program = frappe.db.get_value("Customer", customer_name, "loyalty_program")

        if customer_loyalty_program:
            # Get conversion factor from Loyalty Program table
            conversion_factor = frappe.db.get_value("Loyalty Program", customer_loyalty_program, "conversion_factor") or 0

            # Get total loyalty points earned (positive entries)
            loyalty_points_earned = frappe.db.sql("""
                SELECT SUM(loyalty_points) as total_earned
                FROM `tabLoyalty Point Entry`
                WHERE customer = %s
                AND loyalty_points > 0
                AND loyalty_program = %s
            """, (customer_name, customer_loyalty_program), as_dict=True)

            total_loyalty_points = loyalty_points_earned[0]["total_earned"] if loyalty_points_earned and loyalty_points_earned[0]["total_earned"] else 0

            # Get total loyalty points used (negative entries or redemption entries)
            loyalty_points_used = frappe.db.sql("""
                SELECT
                    SUM(ABS(loyalty_points)) as points_used,
                    SUM(ABS(redemption.redeemed_points)) as points_redeemed
                FROM `tabLoyalty Point Entry` lpe
                LEFT JOIN `tabLoyalty Point Entry Redemption` redemption
                    ON lpe.name = redemption.parent
                WHERE lpe.customer = %s
                AND lpe.loyalty_program = %s
                AND (lpe.loyalty_points < 0 OR redemption.redeemed_points > 0)
            """, (customer_name, customer_loyalty_program), as_dict=True)

            total_loyalty_points_used = 0
            if loyalty_points_used and loyalty_points_used[0]:
                points_used = loyalty_points_used[0]["points_used"] or 0
                points_redeemed = loyalty_points_used[0]["points_redeemed"] or 0
                total_loyalty_points_used = points_used + points_redeemed

            # Calculate loyalty points balance
            total_loyalty_points_balance = total_loyalty_points - total_loyalty_points_used
        else:
            # No loyalty program assigned
            total_loyalty_points = 0
            total_loyalty_points_used = 0
            total_loyalty_points_balance = 0
            conversion_factor = 0

        return {
            "total_credit_limit": total_credit_limit,
            "total_outstanding_amount": total_outstanding,
            "total_credit_balance": total_credit_balance,
            "credit_companies": credit_companies,
            "total_loyalty_points": total_loyalty_points,
            "total_loyalty_points_used": total_loyalty_points_used,
            "total_loyalty_points_balance": total_loyalty_points_balance,
            "conversion_factor": conversion_factor,
        }

    except Exception as e:
        print(f"❌ Error calculating aggregated data for {customer_name}: {str(e)}")
        return None


def main():
    """Main function to run the setup"""
    try:
        # Setup custom fields
        setup_customer_aggregated_fields()

        # Update aggregated fields for all customers
        update_customer_aggregated_fields()

        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Check that custom fields were created in Customer doctype")
        print("2. Verify that aggregated data was calculated correctly")
        print("3. Update the API to use these pre-calculated fields")

    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        frappe.log_error(f"Customer aggregated fields setup failed: {str(e)}", "POS Awesome Setup")


if __name__ == "__main__":
    main()