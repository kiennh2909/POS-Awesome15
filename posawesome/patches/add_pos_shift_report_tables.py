import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """
    Migration script to add POS Shift Report tables and related custom fields
    This script creates:
    1. POS Shift Report DocType
    2. POS Shift Report Invoice Child Table
    3. Custom fields for existing tables
    4. Migration of existing data
    """
    print("🚀 STARTING POS Shift Report Migration...")

    try:
        print("📋 Step 1: Creating POS Shift Report DocTypes...")
        # Create new DocTypes
        create_pos_shift_report_doctypes()

        print("📋 Step 2: Adding custom fields...")
        # Add custom fields to existing tables
        create_shift_report_custom_fields()

        print("📋 Step 3: Migrating existing data...")
        # Migrate existing data if any
        migrate_existing_shift_data()

        print("💾 Committing changes...")
        frappe.db.commit()

        print("🎉 POS Shift Report migration completed successfully!")
        frappe.logger().info("POS Shift Report migration completed successfully")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()

        frappe.log_error(str(e), "POS Shift Report Migration Error")
        raise

def create_pos_shift_report_doctypes():
    """Create POS Shift Report and related DocTypes"""
    print("🔧 Creating POS Shift Report DocTypes...")

    # IMPORTANT: Create CHILD TABLE first, then PARENT TABLE
    # This prevents WrongOptionsDoctypeLinkError

    # 1. POS Shift Report Invoice Child Table (Create FIRST)
    print("📋 Checking POS Shift Report Invoice DocType...")
    exists = frappe.db.exists("DocType", "POS Shift Report Invoice")
    print(f"   POS Shift Report Invoice exists: {exists}")

    if not exists:
        # Create new DocType
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
                    "fieldtype": "JSON",
                    "label": "Payment Method Breakdown",
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
                },
                {
                    "fieldname": "invoice_status",
                    "fieldtype": "Select",
                    "label": "Invoice Status",
                    "options": "Paid\nUnpaid\nPartly Paid\nReturn\nCancelled",
                    "read_only": 1
                }
            ],
            "sort_field": "invoice_date",
            "sort_order": "ASC"
        }

        frappe.get_doc(pos_shift_report_invoice).insert()
        frappe.logger().info("✅ Created POS Shift Report Invoice DocType")

    else:
        # DocType exists, check if invoice_status field exists
        print("ℹ️ POS Shift Report Invoice DocType already exists, checking fields...")

        meta = frappe.get_meta("POS Shift Report Invoice")
        invoice_status_field = meta.get_field("invoice_status")
        print(f"   invoice_status field: {invoice_status_field}")
        print(f"   invoice_status field type: {type(invoice_status_field)}")
        print(f"   invoice_status field is None: {invoice_status_field is None}")
        print(f"   invoice_status field bool: {bool(invoice_status_field)}")

        if not invoice_status_field:
            # Add missing invoice_status field
            print("⚠️ invoice_status field missing, adding it...")

            try:
                field_doc = frappe.get_doc({
                    "doctype": "DocField",
                    "parent": "POS Shift Report Invoice",
                    "parenttype": "DocType",
                    "parentfield": "fields",
                    "fieldname": "invoice_status",
                    "fieldtype": "Select",
                    "label": "Invoice Status",
                    "options": "Paid\nUnpaid\nPartly Paid\nReturn\nCancelled",
                    "read_only": 1,
                    "insert_after": "status"
                })

                print("📝 Creating field document...")
                field_doc.insert()
                print("✅ Added invoice_status field to existing DocType")

                # Clear cache to ensure field is recognized
                frappe.clear_cache()
                print("🧹 Cache cleared")

            except Exception as field_error:
                print(f"❌ Failed to add invoice_status field: {str(field_error)}")
                import traceback
                print("Field creation traceback:")
                traceback.print_exc()

        else:
            print("✅ invoice_status field already exists")

    # 2. POS Shift Report DocType (Create AFTER child table)
    print("📋 Checking POS Shift Report DocType...")
    exists = frappe.db.exists("DocType", "POS Shift Report")
    print(f"   POS Shift Report exists: {exists}")

    if not exists:
        # Create new DocType
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

        frappe.get_doc(pos_shift_report).insert()
        frappe.logger().info("✅ Created POS Shift Report DocType")

    else:
        # DocType exists, check for any missing critical fields
        print("ℹ️ POS Shift Report DocType already exists")
        # Could add field validation here if needed

    print("✅ POS Shift Report DocTypes creation completed")

def create_shift_report_custom_fields():
    """Add custom fields to existing DocTypes"""
    print("🔧 Adding custom fields to existing DocTypes...")

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
    print("✅ Custom fields creation completed")

def migrate_existing_shift_data():
    """Migrate existing opening/closing shifts to shift reports"""
    print("🔄 Migrating existing shift data...")

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

        frappe.logger().info(f"Found {len(opening_shifts)} opening shifts to migrate")

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

                frappe.logger().info(f"Created shift report {shift_report.name} for opening shift {opening_shift.name}")

            except Exception as e:
                frappe.logger().error(f"Failed to migrate opening shift {opening_shift.name}: {str(e)}")
                continue

        print("✅ Migration of existing shift data completed")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        frappe.logger().error(f"Migration failed: {str(e)}")
        # Don't raise error to prevent migration failure