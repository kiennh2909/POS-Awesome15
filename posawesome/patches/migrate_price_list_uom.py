import frappe
import csv
import os
from datetime import datetime

def execute():
    """
    Migration to archive Item Price records with UOM != stock_uom
    """
    print("🚀 Starting Item Price UOM Migration...")

    # Query Item Price records with uom != stock_uom
    query = """
    SELECT ip.name, ip.item_code, ip.price_list, ip.uom, ip.price_list_rate,
           i.stock_uom, ip.creation, ip.modified, ip.owner
    FROM `tabItem Price` ip
    INNER JOIN `tabItem` i ON ip.item_code = i.name
    WHERE ip.uom != i.stock_uom AND ip.docstatus = 0
    ORDER BY ip.item_code, ip.price_list
    """

    invalid_prices = frappe.db.sql(query, as_dict=True)

    if not invalid_prices:
        print("✅ No invalid Item Price records found. Migration complete.")
        return

    print(f"📊 Found {len(invalid_prices)} invalid Item Price records to migrate.")

    # Export to CSV
    export_path = os.path.join(frappe.get_site_path(), "private", "files", "item_price_uom_migration.csv")
    os.makedirs(os.path.dirname(export_path), exist_ok=True)

    with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'item_code', 'price_list', 'uom', 'price_list_rate',
                     'stock_uom', 'creation', 'modified', 'owner', 'action']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for price in invalid_prices:
            price['action'] = 'archived'
            writer.writerow(price)

    print(f"📄 Exported invalid records to: {export_path}")

    # Archive the records (set docstatus=2)
    archived_count = 0
    for price in invalid_prices:
        try:
            doc = frappe.get_doc("Item Price", price.name)
            doc.docstatus = 2  # Archived
            doc.save(ignore_permissions=True)
            archived_count += 1
            print(f"📦 Archived Item Price: {price.item_code} - {price.uom} (was {price.price_list_rate})")
        except Exception as e:
            print(f"❌ Error archiving {price.name}: {str(e)}")

    print(f"✅ Migration complete: {archived_count}/{len(invalid_prices)} records archived.")
    print(f"📋 Backup file: {export_path}")

    # Log the migration
    frappe.logger().info(f"Item Price UOM Migration: {archived_count} records archived")