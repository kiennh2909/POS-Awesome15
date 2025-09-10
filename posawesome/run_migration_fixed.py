#!/usr/bin/env python3
"""
Fixed Migration Script for POS Shift Report System
This script creates DocTypes in the correct order to avoid dependency issues.
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

def create_module_if_not_exists():
    """Create POS Awesome module if it doesn't exist"""
    print("🔍 Checking for POS Awesome module...")

    if frappe.db.exists("Module Def", "POS Awesome"):
        print("✅ Module POS Awesome already exists")
        return True

    print("❌ Module POS Awesome not found, creating...")

    try:
        from frappe import get_doc

        module = get_doc({
            "doctype": "Module Def",
            "module_name": "POS Awesome",
            "app_name": "posawesome"
        })

        module.insert()
        frappe.db.commit()

        print("✅ Module POS Awesome created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating module: {e}")
        return False

def create_child_table():
    """Create POS Shift Report Invoice child table first"""
    print("🔧 Creating POS Shift Report Invoice (Child Table)...")

    if frappe.db.exists("DocType", "POS Shift Report Invoice"):
        print("✅ POS Shift Report Invoice already exists")
        return True

    try:
        from frappe import get_doc

        pos_shift_report_invoice = {
            "doctype": "DocType",
            "name": "POS Shift Report Invoice",
            "module": "POSAwesome",
            "custom": 0,
            "is_submittable": 0,
            "istable": 1,
            "fields": [
                {
                    "fieldname": "invoice_no",
                    "fieldtype": "Link",
                    "label": "Invoice No",
                    "options": "Sales Invoice",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "invoice_date",
                    "fieldtype": "Date",
                    "label": "Invoice Date",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "invoice_time",
                    "fieldtype": "Time",
                    "label": "Invoice Time",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "customer",
                    "fieldtype": "Link",
                    "label": "Customer",
                    "options": "Customer",
                    "read_only": 1
                },
                {
                    "fieldname": "total_amount",
                    "fieldtype": "Currency",
                    "label": "Total Amount",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "paid_amount",
                    "fieldtype": "Currency",
                    "label": "Paid Amount",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "tax_amount",
                    "fieldtype": "Currency",
                    "label": "Tax Amount",
                    "read_only": 1
                },
                {
                    "fieldname": "payment_method",
                    "fieldtype": "Data",
                    "label": "Payment Method",
                    "read_only": 1
                },
                {
                    "fieldname": "is_return",
                    "fieldtype": "Check",
                    "label": "Is Return",
                    "read_only": 1
                },
                {
                    "fieldname": "status",
                    "fieldtype": "Select",
                    "label": "Status",
                    "options": "Submitted\nCancelled",
                    "default": "Submitted",
                    "read_only": 1
                }
            ],
            "sort_field": "invoice_date",
            "sort_order": "ASC"
        }

        doc = get_doc(pos_shift_report_invoice)
        doc.insert()
        frappe.db.commit()

        print("✅ POS Shift Report Invoice created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating child table: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_parent_table():
    """Create POS Shift Report parent table after child table"""
    print("🔧 Creating POS Shift Report (Parent Table)...")

    if frappe.db.exists("DocType", "POS Shift Report"):
        print("✅ POS Shift Report already exists")
        return True

    try:
        from frappe import get_doc

        pos_shift_report = {
            "doctype": "DocType",
            "name": "POS Shift Report",
            "module": "POSAwesome",
            "custom": 0,
            "is_submittable": 1,
            "track_changes": 1,
            "track_views": 1,
            "allow_copy": 0,
            "allow_rename": 0,
            "allow_import": 0,
            "quick_entry": 0,
            "fields": [
                {
                    "fieldname": "shift_report_id",
                    "fieldtype": "Data",
                    "label": "Shift Report ID",
                    "unique": 1,
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "pos_opening_shift",
                    "fieldtype": "Link",
                    "label": "POS Opening Shift",
                    "options": "POS Opening Shift",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "opening_date",
                    "fieldtype": "Date",
                    "label": "Opening Date",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "opening_time",
                    "fieldtype": "Time",
                    "label": "Opening Time",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "opened_by",
                    "fieldtype": "Link",
                    "label": "Opened By",
                    "options": "User",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "opening_amounts",
                    "fieldtype": "JSON",
                    "label": "Opening Amounts",
                    "reqd": 1
                },
                {
                    "fieldname": "expected_closing_amounts",
                    "fieldtype": "JSON",
                    "label": "Expected Closing Amounts"
                },
                {
                    "fieldname": "actual_closing_amounts",
                    "fieldtype": "JSON",
                    "label": "Actual Closing Amounts"
                },
                {
                    "fieldname": "total_opening_amount",
                    "fieldtype": "Currency",
                    "label": "Total Opening Amount",
                    "reqd": 1,
                    "read_only": 1
                },
                {
                    "fieldname": "total_expected_closing",
                    "fieldtype": "Currency",
                    "label": "Total Expected Closing",
                    "read_only": 1
                },
                {
                    "fieldname": "total_actual_closing",
                    "fieldtype": "Currency",
                    "label": "Total Actual Closing",
                    "read_only": 1
                },
                {
                    "fieldname": "difference",
                    "fieldtype": "Currency",
                    "label": "Difference",
                    "read_only": 1
                },
                {
                    "fieldname": "verification_status",
                    "fieldtype": "Select",
                    "label": "Verification Status",
                    "options": "Pending\nVerified\nConfirmed",
                    "default": "Pending"
                },
                {
                    "fieldname": "verification_date",
                    "fieldtype": "Date",
                    "label": "Verification Date",
                    "read_only": 1
                },
                {
                    "fieldname": "verified_by",
                    "fieldtype": "Link",
                    "label": "Verified By",
                    "options": "User",
                    "read_only": 1
                },
                {
                    "fieldname": "confirmation_date",
                    "fieldtype": "Date",
                    "label": "Confirmation Date",
                    "read_only": 1
                },
                {
                    "fieldname": "confirmed_by",
                    "fieldtype": "Link",
                    "label": "Confirmed By",
                    "options": "User",
                    "read_only": 1
                },
                {
                    "fieldname": "closing_date",
                    "fieldtype": "Date",
                    "label": "Closing Date",
                    "read_only": 1
                },
                {
                    "fieldname": "closed_by",
                    "fieldtype": "Link",
                    "label": "Closed By",
                    "options": "User",
                    "read_only": 1
                },
                {
                    "fieldname": "status",
                    "fieldtype": "Select",
                    "label": "Status",
                    "options": "Open\nClosed",
                    "default": "Open",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "invoice_count",
                    "fieldtype": "Int",
                    "label": "Invoice Count",
                    "read_only": 1,
                    "default": 0
                },
                {
                    "fieldname": "total_sales",
                    "fieldtype": "Currency",
                    "label": "Total Sales",
                    "read_only": 1,
                    "default": 0
                },
                {
                    "fieldname": "total_returns",
                    "fieldtype": "Currency",
                    "label": "Total Returns",
                    "read_only": 1,
                    "default": 0
                },
                {
                    "fieldname": "payment_breakdown",
                    "fieldtype": "JSON",
                    "label": "Payment Breakdown"
                },
                {
                    "fieldname": "notes",
                    "fieldtype": "Text",
                    "label": "Notes"
                },
                {
                    "fieldname": "invoices",
                    "fieldtype": "Table",
                    "label": "Invoices",
                    "options": "POS Shift Report Invoice",
                    "read_only": 1
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "submit": 1,
                    "cancel": 1,
                    "amend": 1
                },
                {
                    "role": "Sales Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "submit": 1,
                    "cancel": 1
                },
                {
                    "role": "Sales User",
                    "read": 1,
                    "write": 0,
                    "create": 0
                }
            ],
            "sort_field": "creation",
            "sort_order": "DESC"
        }

        doc = get_doc(pos_shift_report)
        doc.insert()
        frappe.db.commit()

        print("✅ POS Shift Report created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating parent table: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_custom_fields():
    """Create custom fields for existing DocTypes"""
    print("🔧 Creating custom fields...")

    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

        custom_fields = {
            "POS Opening Shift": [
                {
                    "fieldname": "shift_report_id",
                    "fieldtype": "Data",
                    "label": "Shift Report ID",
                    "unique": 1,
                    "read_only": 1,
                    "insert_after": "name"
                },
                {
                    "fieldname": "shift_report",
                    "fieldtype": "Link",
                    "label": "Shift Report",
                    "options": "POS Shift Report",
                    "read_only": 1,
                    "insert_after": "shift_report_id"
                }
            ],
            "POS Closing Shift": [
                {
                    "fieldname": "shift_report",
                    "fieldtype": "Link",
                    "label": "Shift Report",
                    "options": "POS Shift Report",
                    "reqd": 1,
                    "read_only": 1,
                    "insert_after": "pos_opening_shift"
                },
                {
                    "fieldname": "expected_amounts",
                    "fieldtype": "JSON",
                    "label": "Expected Amounts",
                    "read_only": 1,
                    "insert_after": "shift_report"
                },
                {
                    "fieldname": "actual_amounts",
                    "fieldtype": "JSON",
                    "label": "Actual Amounts",
                    "reqd": 1,
                    "insert_after": "expected_amounts"
                },
                {
                    "fieldname": "difference_amounts",
                    "fieldtype": "JSON",
                    "label": "Difference Amounts",
                    "read_only": 1,
                    "insert_after": "actual_amounts"
                },
                {
                    "fieldname": "verification_status",
                    "fieldtype": "Select",
                    "label": "Verification Status",
                    "options": "Pending\nVerified\nConfirmed",
                    "default": "Pending",
                    "insert_after": "difference_amounts"
                }
            ],
            "Sales Invoice": [
                {
                    "fieldname": "pos_shift_report",
                    "fieldtype": "Link",
                    "label": "POS Shift Report",
                    "options": "POS Shift Report",
                    "read_only": 1,
                    "insert_after": "pos_profile"
                },
                {
                    "fieldname": "shift_report_id",
                    "fieldtype": "Data",
                    "label": "Shift Report ID",
                    "read_only": 1,
                    "insert_after": "pos_shift_report"
                }
            ]
        }

        create_custom_fields(custom_fields)
        print("✅ Custom fields created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating custom fields: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_data():
    """Migrate existing data"""
    print("🔧 Migrating existing data...")

    try:
        # Get all submitted opening shifts without shift reports
        opening_shifts = frappe.get_all(
            "POS Opening Shift",
            filters={
                "docstatus": 1,
                "shift_report": ["is", "not set"]
            },
            fields=["name", "posting_date", "posting_time", "owner", "pos_profile"]
        )

        print(f"Found {len(opening_shifts)} opening shifts to migrate")

        for opening_shift in opening_shifts:
            try:
                # Create shift report for this opening shift
                shift_report = frappe.get_doc({
                    "doctype": "POS Shift Report",
                    "shift_report_id": f"SHIFT-{opening_shift.name}",
                    "pos_opening_shift": opening_shift.name,
                    "opening_date": opening_shift.posting_date,
                    "opening_time": opening_shift.posting_time,
                    "opened_by": opening_shift.owner,
                    "opening_amounts": "{}",
                    "total_opening_amount": 0,
                    "status": "Open",
                    "invoice_count": 0,
                    "total_sales": 0,
                    "total_returns": 0
                })

                shift_report.insert()
                shift_report.submit()

                # Update opening shift with shift report reference
                frappe.db.set_value(
                    "POS Opening Shift",
                    opening_shift.name,
                    {
                        "shift_report_id": shift_report.shift_report_id,
                        "shift_report": shift_report.name
                    }
                )

                print(f"✅ Created shift report {shift_report.name} for opening shift {opening_shift.name}")

            except Exception as e:
                print(f"❌ Failed to migrate opening shift {opening_shift.name}: {str(e)}")
                continue

        print("✅ Data migration completed")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("🚀 FIXED MIGRATION SCRIPT - POS SHIFT REPORT SYSTEM")
    print("=" * 60)

    success = True

    # Step 1: Create module
    if not create_module_if_not_exists():
        success = False

    # Step 2: Create child table first
    if success and not create_child_table():
        success = False

    # Step 3: Create parent table
    if success and not create_parent_table():
        success = False

    # Step 4: Create custom fields
    if success and not create_custom_fields():
        success = False

    # Step 5: Migrate data
    if success and not migrate_data():
        success = False

    # Final result
    if success:
        print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("✅ All DocTypes created")
        print("✅ All custom fields added")
        print("✅ Data migration completed")
        print("\n📋 Next steps:")
        print("1. Clear cache: bench clear-cache --site erp152-v1.vtcom.online")
        print("2. Restart services: sudo supervisorctl restart frappe-bench-web:")
        print("3. Test system: Access POS and create shift reports")
    else:
        print("\n❌ MIGRATION FAILED!")
        print("Check logs for details")

    return success

if __name__ == "__main__":
    success = main()
    frappe.destroy()
    exit(0 if success else 1)