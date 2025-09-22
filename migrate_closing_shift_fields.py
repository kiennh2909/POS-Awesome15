#!/usr/bin/env python3
"""
Script to add new fields to POS Closing Shift doctype
Run this script to update the database schema without full migration
"""

import frappe

def migrate_closing_shift_fields():
    """Add new fields to POS Closing Shift doctype"""

    print("🚀 Starting POS Closing Shift fields migration...")

    try:
        # Reload the doctype to pick up JSON changes
        print("📋 Reloading POS Closing Shift doctype...")
        frappe.reload_doctype("POS Closing Shift")
        print("✅ Doctype reloaded successfully")

        # Verify the fields were added
        meta = frappe.get_meta("POS Closing Shift")
        new_fields = ["shift_report_id", "verification_date", "verified_by", "confirmation_date", "confirmed_by"]

        print("🔍 Checking if new fields were added...")
        for field in new_fields:
            if meta.has_field(field):
                print(f"✅ Field '{field}' exists")
            else:
                print(f"❌ Field '{field}' missing")

        print("🎉 Migration completed successfully!")
        print("You can now use the new fields in POS Closing Shift documents.")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_closing_shift_fields()