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
    try:
        # Create new DocTypes
        create_pos_shift_report_doctypes()

        # Add custom fields to existing tables
        create_shift_report_custom_fields()

        # Migrate existing data if any
        migrate_existing_shift_data()

        frappe.db.commit()
        frappe.logger().info("POS Shift Report migration completed successfully")

    except Exception as e:
        frappe.log_error(str(e), "POS Shift Report Migration Error")
        raise

def create_pos_shift_report_doctypes():
    """Create POS Shift Report and related DocTypes"""

    # POS Shift Report DocType
    if not frappe.db.exists("DocType", "POS Shift Report"):
        pos_shift_report = {
            "doctype": "DocType",
            "name": "POS Shift Report",
            "module": "POS Awesome",
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

    # POS Shift Report Invoice Child Table
    if not frappe.db.exists("DocType", "POS Shift Report Invoice"):
        pos_shift_report_invoice = {
            "doctype": "DocType",
            "name": "POS Shift Report Invoice",
            "module": "POS Awesome",
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

        frappe.get_doc(pos_shift_report_invoice).insert()

def create_shift_report_custom_fields():
    """Add custom fields to existing DocTypes"""

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

def migrate_existing_shift_data():
    """Migrate existing opening/closing shifts to shift reports"""

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

        frappe.logger().info("Migration of existing shift data completed")

    except Exception as e:
        frappe.logger().error(f"Migration failed: {str(e)}")
        # Don't raise error to prevent migration failure