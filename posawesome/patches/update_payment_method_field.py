import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Migration to update payment_method field in POS Shift Report Invoice
    from Data type to JSON type to support multiple payment methods
    """
    try:
        # Update the field type for existing installations
        if frappe.db.exists("DocType", "POS Shift Report Invoice"):
            # Get the existing field
            field = frappe.get_doc("DocType", "POS Shift Report Invoice").get_field("payment_method")

            if field and field.fieldtype == "Data":
                # Update field type to JSON
                frappe.db.set_value("DocType Field", field.name, "fieldtype", "JSON")
                frappe.db.set_value("DocType Field", field.name, "label", "Payment Method Breakdown")

                frappe.logger().info("Updated payment_method field to JSON type in POS Shift Report Invoice")

        # Clear cache to ensure changes take effect
        frappe.clear_cache(doctype="POS Shift Report Invoice")

        frappe.logger().info("Payment method field migration completed successfully")

    except Exception as e:
        frappe.log_error(str(e), "Payment Method Field Migration Error")
        raise