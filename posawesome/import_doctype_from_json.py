#!/usr/bin/env python3
"""
Script to import POS Payment Summary DocType from JSON file
Run this in bench console: exec(open('posawesome/import_doctype_from_json.py').read())
"""

import json
import frappe
import os

def import_pos_payment_summary_doctype():
    """Import POS Payment Summary DocType from JSON file"""

    print("📄 IMPORTING POS PAYMENT SUMMARY DOCTYPE FROM JSON")
    print("=" * 60)

    try:
        # Try different possible paths
        possible_paths = [
            'posawesome/posawesome/doctype/pos_payment_summary/pos_payment_summary.json',
            '/home/frappe/frappe-bench/apps/posawesome/posawesome/doctype/pos_payment_summary/pos_payment_summary.json',
            './posawesome/doctype/pos_payment_summary/pos_payment_summary.json',
            'apps/posawesome/posawesome/doctype/pos_payment_summary/pos_payment_summary.json'
        ]

        json_file = None
        for path in possible_paths:
            if os.path.exists(path):
                json_file = path
                print(f"✅ Found JSON file at: {path}")
                break

        if not json_file:
            print("❌ JSON file not found in any of these locations:")
            for path in possible_paths:
                print(f"   - {path}")
            return False

        # Check file size
        file_size = os.path.getsize(json_file)
        print(f"📊 JSON file size: {file_size} bytes")

        if file_size == 0:
            print("❌ JSON file is empty!")
            return False

        # Read and parse JSON
        print("📖 Reading JSON file...")
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📄 First 200 characters: {content[:200]}")

            # Parse JSON
            doctype_data = json.loads(content)

        print(f"✅ Successfully parsed JSON: {doctype_data.get('name')}")

        # Check if DocType already exists
        doctype_name = doctype_data.get('name')
        if frappe.db.exists("DocType", doctype_name):
            print(f"⚠️ DocType '{doctype_name}' already exists")

            # Option to update existing
            update_existing = input("Update existing DocType? (y/n): ").lower().strip()
            if update_existing == 'y':
                print("📝 Updating existing DocType...")
                existing_doc = frappe.get_doc("DocType", doctype_name)

                # Update fields
                for field in doctype_data.get("fields", []):
                    # Find existing field
                    existing_field = None
                    for ef in existing_doc.fields:
                        if ef.fieldname == field["fieldname"]:
                            existing_field = ef
                            break

                    if existing_field:
                        # Update existing field
                        for key, value in field.items():
                            if hasattr(existing_field, key):
                                setattr(existing_field, key, value)
                    else:
                        # Add new field
                        existing_doc.append("fields", field)

                existing_doc.save(ignore_permissions=True)
                print("✅ DocType updated successfully")
            else:
                print("⏭️ Skipping DocType creation")

        else:
            print(f"📝 Creating new DocType: {doctype_name}")

            # Create new DocType
            doc = frappe.get_doc(doctype_data)
            doc.insert(ignore_permissions=True)
            print("✅ DocType created successfully")

        # Commit changes
        frappe.db.commit()

        # Verify DocType
        if frappe.db.exists("DocType", doctype_name):
            print("✅ DocType verification passed")

            # Get DocType details
            doctype_doc = frappe.get_doc("DocType", doctype_name)
            fields_count = len(doctype_doc.fields)
            print(f"📊 Fields count: {fields_count}")

            # List some fields
            if fields_count > 0:
                print("📋 Sample fields:")
                for i, field in enumerate(doctype_doc.fields[:5]):
                    print(f"   {i+1}. {field.fieldname} ({field.fieldtype})")

            return True
        else:
            print("❌ DocType verification failed")
            return False

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print("Check the JSON file syntax")
        return False

    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_migration_after_import():
    """Run migration after DocType import"""

    print("\n🔄 RUNNING MIGRATION")
    print("=" * 30)

    try:
        # Try frappe migrate
        from frappe.migrate import migrate
        print("🚀 Starting frappe migrate...")
        migrate()
        print("✅ Migration completed")

        # Clear cache
        frappe.clear_cache()
        print("✅ Cache cleared")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False


# Main execution
if __name__ == "__main__":
    print("🚀 POS PAYMENT SUMMARY DOCTYPE IMPORT SCRIPT")
    print("=" * 50)

    # Import DocType
    import_success = import_pos_payment_summary_doctype()

    if import_success:
        print("\n🎉 DOCTYPE IMPORT SUCCESSFUL!")

        # Ask to run migration
        run_migrate = input("Run migration now? (y/n): ").lower().strip()
        if run_migrate == 'y':
            migration_success = run_migration_after_import()

            if migration_success:
                print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
                print("POS Payment Summary is ready to use!")
            else:
                print("\n⚠️ MIGRATION FAILED!")
                print("Please run 'bench migrate' manually")
        else:
            print("\n⏭️ Skipping migration")
            print("Remember to run 'bench migrate' later")

    else:
        print("\n💥 DOCTYPE IMPORT FAILED!")
        print("Check the error messages above")

    print("\n" + "=" * 50)
    print("Script execution completed")