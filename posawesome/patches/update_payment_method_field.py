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
            # Get the DocType meta
            meta = frappe.get_meta("POS Shift Report Invoice")

            # Find the payment_method field
            payment_field = None
            for field in meta.fields:
                if field.fieldname == "payment_method":
                    payment_field = field
                    break

            if payment_field and payment_field.fieldtype == "Data":
                # Update field type to JSON using the correct table
                frappe.db.sql("""
                    UPDATE `tabDocType Field`
                    SET fieldtype = 'JSON', label = 'Payment Method Breakdown'
                    WHERE parent = 'POS Shift Report Invoice'
                    AND fieldname = 'payment_method'
                """)

                frappe.logger().info("Updated payment_method field to JSON type in POS Shift Report Invoice")

        # Clear cache to ensure changes take effect
        frappe.clear_cache(doctype="POS Shift Report Invoice")

        frappe.logger().info("Payment method field migration completed successfully")

    except Exception as e:
        frappe.log_error(str(e), "Payment Method Field Migration Error")
        raise