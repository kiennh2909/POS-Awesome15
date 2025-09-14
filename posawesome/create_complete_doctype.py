#!/usr/bin/env python3
"""
Complete script to create POS Payment Summary DocType
Run this in bench console: exec(open('posawesome/create_complete_doctype.py').read())
"""

import frappe
import json
import os

def create_complete_pos_payment_summary_doctype():
    """Create or recreate complete POS Payment Summary DocType"""

    print("🚀 CREATING COMPLETE POS PAYMENT SUMMARY DOCTYPE")
    print("=" * 60)

    doctype_name = "POS Payment Summary"

    try:
        # Check if DocType exists
        exists = frappe.db.exists("DocType", doctype_name)

        if exists:
            print(f"⚠️ DocType '{doctype_name}' already exists")

            # Ask user if they want to recreate
            recreate = input(f"Do you want to delete and recreate '{doctype_name}'? (y/n): ").lower().strip()

            if recreate == 'y':
                print(f"🗑️ Deleting existing DocType '{doctype_name}'...")

                # Delete existing DocType
                frappe.delete_doc("DocType", doctype_name, ignore_permissions=True, force=True)
                frappe.db.commit()

                print(f"✅ Deleted existing DocType '{doctype_name}'")
            else:
                print(f"⏭️ Keeping existing DocType '{doctype_name}'")
                return True

        print(f"📝 Creating new DocType '{doctype_name}'...")

        # Create complete DocType with all fields
        doctype_doc = frappe.get_doc({
            "doctype": "DocType",
            "name": doctype_name,
            "module": "POS Awesome",
            "custom": 0,
            "is_submittable": 0,
            "autoname": "field:shift_report_id",
            "naming_rule": "By fieldname",
            "title_field": "shift_report_id",
            "sort_field": "modified",
            "sort_order": "DESC",
            "track_changes": 1,
            "fields": [
                # Section Break - Shift Information
                {
                    "fieldname": "section_break_shift_info",
                    "fieldtype": "Section Break",
                    "label": "Shift Information"
                },

                # Basic shift information
                {
                    "fieldname": "shift_report_id",
                    "fieldtype": "Data",
                    "label": "Shift Report ID",
                    "reqd": 1,
                    "unique": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "pos_shift_report",
                    "fieldtype": "Link",
                    "label": "POS Shift Report",
                    "options": "POS Shift Report",
                    "reqd": 1
                },
                {
                    "fieldname": "pos_opening_shift",
                    "fieldtype": "Link",
                    "label": "POS Opening Shift",
                    "options": "POS Opening Shift",
                    "reqd": 1
                },

                # Column Break
                {
                    "fieldname": "column_break_1",
                    "fieldtype": "Column Break"
                },

                # Date/Time information
                {
                    "fieldname": "posting_date",
                    "fieldtype": "Date",
                    "label": "Posting Date",
                    "reqd": 1
                },
                {
                    "fieldname": "shift_start_time",
                    "fieldtype": "Datetime",
                    "label": "Shift Start Time"
                },
                {
                    "fieldname": "shift_end_time",
                    "fieldtype": "Datetime",
                    "label": "Shift End Time"
                },

                # Section Break - Payment Method Information
                {
                    "fieldname": "section_break_payment",
                    "fieldtype": "Section Break",
                    "label": "Payment Method Information"
                },

                # Payment method details
                {
                    "fieldname": "payment_method",
                    "fieldtype": "Data",
                    "label": "Payment Method",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "payment_method_type",
                    "fieldtype": "Select",
                    "label": "Payment Method Type",
                    "options": "Cash\nCard\nDigital\nOther",
                    "reqd": 1
                },
                {
                    "fieldname": "currency",
                    "fieldtype": "Link",
                    "label": "Currency",
                    "options": "Currency",
                    "reqd": 1
                },

                # Column Break
                {
                    "fieldname": "column_break_2",
                    "fieldtype": "Column Break"
                },

                # Statistics
                {
                    "fieldname": "transaction_count",
                    "fieldtype": "Int",
                    "label": "Transaction Count",
                    "default": "0"
                },
                {
                    "fieldname": "company",
                    "fieldtype": "Link",
                    "label": "Company",
                    "options": "Company",
                    "reqd": 1
                },
                {
                    "fieldname": "pos_profile",
                    "fieldtype": "Link",
                    "label": "POS Profile",
                    "options": "POS Profile",
                    "reqd": 1
                },

                # Section Break - Amount Details
                {
                    "fieldname": "section_break_amounts",
                    "fieldtype": "Section Break",
                    "label": "Amount Details"
                },

                # Amount fields
                {
                    "fieldname": "opening_amount",
                    "fieldtype": "Currency",
                    "label": "Opening Amount",
                    "reqd": 1,
                    "default": "0"
                },
                {
                    "fieldname": "transaction_amount",
                    "fieldtype": "Currency",
                    "label": "Transaction Amount",
                    "reqd": 1,
                    "default": "0"
                },
                {
                    "fieldname": "expected_closing_amount",
                    "fieldtype": "Currency",
                    "label": "Expected Closing Amount",
                    "default": "0"
                },

                # Column Break
                {
                    "fieldname": "column_break_3",
                    "fieldtype": "Column Break"
                },

                # Closing amounts
                {
                    "fieldname": "closing_amount",
                    "fieldtype": "Currency",
                    "label": "Closing Amount",
                    "reqd": 1,
                    "default": "0"
                },
                {
                    "fieldname": "difference",
                    "fieldtype": "Currency",
                    "label": "Difference",
                    "default": "0"
                },

                # Section Break - Additional Information
                {
                    "fieldname": "section_break_notes",
                    "fieldtype": "Section Break",
                    "label": "Additional Information"
                },

                # Notes
                {
                    "fieldname": "notes",
                    "fieldtype": "Small Text",
                    "label": "Notes"
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "export": 1,
                    "print": 1,
                    "report": 1,
                    "share": 1,
                    "email": 1
                },
                {
                    "role": "Sales Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "export": 1,
                    "print": 1,
                    "report": 1,
                    "share": 1,
                    "email": 1
                },
                {
                    "role": "Sales User",
                    "read": 1,
                    "write": 0,
                    "create": 0,
                    "delete": 0,
                    "export": 1,
                    "print": 1,
                    "report": 1,
                    "share": 0,
                    "email": 1
                }
            ]
        })

        # Insert DocType
        doctype_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        print(f"✅ DocType '{doctype_name}' created successfully!")
        print(f"📊 Total fields: {len(doctype_doc.fields)}")
        print(f"🔐 Total permissions: {len(doctype_doc.permissions)}")

        # List created fields
        print("\n📋 Created fields:")
        for i, field in enumerate(doctype_doc.fields[:10], 1):  # Show first 10
            print(f"   {i}. {field.fieldname} ({field.fieldtype}) - {'Required' if field.reqd else 'Optional'}")

        if len(doctype_doc.fields) > 10:
            print(f"   ... and {len(doctype_doc.fields) - 10} more fields")

        return True

    except Exception as e:
        print(f"❌ Error creating DocType: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_migration_after_creation():
    """Run migration after DocType creation"""

    print("\n🔄 RUNNING MIGRATION")
    print("=" * 30)

    try:
        from frappe.migrate import migrate
        print("🚀 Starting frappe migrate...")
        migrate()
        print("✅ Migration completed successfully")

        # Clear cache
        frappe.clear_cache()
        print("✅ Cache cleared")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False


def verify_creation():
    """Verify DocType creation and database table"""

    print("\n🔍 VERIFYING CREATION")
    print("=" * 30)

    doctype_name = "POS Payment Summary"

    try:
        # Check DocType exists
        exists = frappe.db.exists("DocType", doctype_name)
        print(f"DocType exists: {'✅' if exists else '❌'}")

        if exists:
            # Get DocType details
            doctype = frappe.get_doc("DocType", doctype_name)
            print(f"Fields count: {len(doctype.fields)}")
            print(f"Permissions count: {len(doctype.permissions)}")
            print(f"Module: {doctype.module}")
            print(f"Auto name: {doctype.autoname}")

            # Check database table
            try:
                table_check = frappe.db.sql(f"DESCRIBE `tab{doctype_name}`", as_dict=True)
                print(f"Database table: ✅ ({len(table_check)} columns)")

                # Show sample columns
                print("Sample columns:")
                for col in table_check[:5]:
                    print(f"   - {col['Field']} ({col['Type']})")

            except Exception as e:
                print(f"Database table: ❌ ({str(e)})")

            # Check permissions
            roles = [p.role for p in doctype.permissions]
            print(f"Assigned roles: {', '.join(roles)}")

            return True
        else:
            print("❌ DocType not found")
            return False

    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False


# Main execution
if __name__ == "__main__":
    print("🎯 POS PAYMENT SUMMARY DOCTYPE CREATION SCRIPT")
    print("=" * 50)

    # Create DocType
    creation_success = create_complete_pos_payment_summary_doctype()

    if creation_success:
        print("\n🎉 DOCTYPE CREATION SUCCESSFUL!")

        # Run migration
        migration_success = run_migration_after_creation()

        if migration_success:
            print("\n🎉 MIGRATION COMPLETED!")

        # Verify
        verification_success = verify_creation()

        if verification_success:
            print("\n🎉 VERIFICATION PASSED!")
            print("POS Payment Summary DocType is ready for use!")
        else:
            print("\n⚠️ VERIFICATION FAILED!")
            print("Please check the errors above")

    else:
        print("\n💥 DOCTYPE CREATION FAILED!")
        print("Check the error messages above")

    print("\n" + "=" * 50)
    print("Script execution completed")