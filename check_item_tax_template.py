#!/usr/bin/env python3
"""
Script to check and fix Item Tax Template VAT5_ITEM configuration
"""

import frappe
import json

def check_item_tax_template():
    """Check Item Tax Template VAT5_ITEM configuration"""
    try:
        # Initialize Frappe
        frappe.init(site='site_config.json')
        frappe.connect()

        print("=== Checking Item Tax Template VAT5_ITEM ===")

        # Get the template
        template = frappe.get_doc('Item Tax Template', 'VAT5_ITEM')
        print(f"Template Name: {template.name}")
        print(f"Title: {template.title}")
        print(f"Company: {template.company}")

        print(f"\n=== Tax Details ({len(template.taxes)} entries) ===")
        has_valid_tax = False

        for i, tax in enumerate(template.taxes):
            print(f"Tax {i+1}:")
            print(f"  - tax_type: {tax.tax_type}")
            print(f"  - tax_rate: {tax.tax_rate}")
            print(f"  - account_head: {tax.account_head}")

            if tax.tax_rate > 0:
                has_valid_tax = True

        print(f"\nHas valid tax rate (>0): {has_valid_tax}")

        # Check if we need to fix the template
        if not has_valid_tax:
            print("\n⚠️  No valid tax rate found! Fixing VAT5_ITEM template...")

            # Clear existing taxes
            template.taxes = []

            # Add VAT 5% tax
            tax_account = frappe.get_value("Company", "NTP-Vietnam", "default_tax_account")
            if not tax_account:
                # Try to find a VAT account
                tax_accounts = frappe.get_all("Account",
                    filters={"account_type": "Tax", "company": "NTP-Vietnam"},
                    fields=["name"], limit=1)
                if tax_accounts:
                    tax_account = tax_accounts[0].name

            if tax_account:
                template.append("taxes", {
                    "tax_type": "VAT 5%",
                    "tax_rate": 5.0,
                    "account_head": tax_account
                })
                template.save()
                print("✅ Fixed VAT5_ITEM template with 5% tax rate")
            else:
                print("❌ Could not find tax account for NTP-Vietnam")

        # Check Item Tax table entry
        print("\n=== Checking Item Tax table for 8938549898111 ===")
        item_tax_entries = frappe.get_all('Item Tax',
            filters={'parent': '8938549898111'},
            fields=['item_tax_template', 'tax_category', 'valid_from']
        )

        if item_tax_entries:
            for entry in item_tax_entries:
                print(f"Item Tax Entry: {entry}")
        else:
            print("No Item Tax entries found for item 8938549898111")

        frappe.destroy()

    except Exception as e:
        print(f"Error: {e}")
        try:
            frappe.destroy()
        except:
            pass

if __name__ == "__main__":
    check_item_tax_template()