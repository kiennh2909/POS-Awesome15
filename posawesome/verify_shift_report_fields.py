#!/usr/bin/env python3
"""
Script to verify that shift report custom fields exist in database
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

def verify_custom_fields():
    """Verify that custom fields for shift report exist"""

    print("🔍 VERIFYING SHIFT REPORT CUSTOM FIELDS")
    print("=" * 60)

    # Check custom fields in Sales Invoice
    required_fields = [
        ("Sales Invoice", "pos_shift_report"),
        ("Sales Invoice", "shift_report_id"),
        ("POS Opening Shift", "shift_report"),
        ("POS Opening Shift", "shift_report_id"),
        ("POS Closing Shift", "shift_report")
    ]

    all_fields_exist = True

    for doctype, fieldname in required_fields:
        try:
            # Check if custom field exists
            custom_field = frappe.get_all("Custom Field",
                filters={"dt": doctype, "fieldname": fieldname}
            )

            if custom_field:
                print(f"✅ Custom field {fieldname} exists in {doctype}")
            else:
                print(f"❌ Custom field {fieldname} MISSING in {doctype}")
                all_fields_exist = False

        except Exception as e:
            print(f"❌ Error checking {fieldname} in {doctype}: {str(e)}")
            all_fields_exist = False

    # Check DocTypes exist
    doctypes_to_check = ["POS Shift Report", "POS Shift Report Invoice"]

    print("\n📋 CHECKING DOCTYPES:")
    for doctype in doctypes_to_check:
        if frappe.db.exists("DocType", doctype):
            print(f"✅ DocType {doctype} exists")
        else:
            print(f"❌ DocType {doctype} MISSING")
            all_fields_exist = False

    # Check database tables
    print("\n📋 CHECKING DATABASE TABLES:")
    table_names = [f"tab{doctype}" for doctype in doctypes_to_check]

    for table_name in table_names:
        if frappe.db.has_table(table_name):
            print(f"✅ Table {table_name} exists")
        else:
            print(f"❌ Table {table_name} MISSING")
            all_fields_exist = False

    return all_fields_exist

def check_sample_data():
    """Check if there's sample data to test with"""

    print("\n📋 CHECKING SAMPLE DATA:")

    # Check for open opening shifts
    open_shifts = frappe.get_all("POS Opening Shift",
        filters={"docstatus": 1, "status": "Open"}
    )
    print(f"✅ Open POS Opening Shifts: {len(open_shifts)}")

    # Check for shift reports
    shift_reports = frappe.get_all("POS Shift Report")
    print(f"✅ POS Shift Reports: {len(shift_reports)}")

    # Check for sales invoices with POS
    pos_invoices = frappe.get_all("Sales Invoice",
        filters={"is_pos": 1, "docstatus": 1}
    )
    print(f"✅ POS Sales Invoices: {len(pos_invoices)}")

    return len(open_shifts) > 0 and len(shift_reports) > 0

if __name__ == "__main__":
    try:
        fields_ok = verify_custom_fields()
        data_ok = check_sample_data()

        frappe.destroy()

        print("\n" + "=" * 60)
        print("📊 VERIFICATION RESULTS:")
        print("=" * 60)

        if fields_ok:
            print("✅ All required custom fields exist")
        else:
            print("❌ Some custom fields are missing")

        if data_ok:
            print("✅ Sample data available for testing")
        else:
            print("⚠️  Limited sample data - testing may be restricted")

        if fields_ok and data_ok:
            print("\n🎉 SYSTEM READY FOR TESTING!")
        else:
            print("\n⚠️  SYSTEM NEEDS ATTENTION BEFORE TESTING")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        frappe.destroy()
        exit(1)