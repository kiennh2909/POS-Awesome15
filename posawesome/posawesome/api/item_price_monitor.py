import frappe
from frappe import _

def alert_invalid_uom(doc, method):
    """
    Alert when Item Price is created with UOM != stock_uom
    """
    try:
        # Get item stock_uom
        stock_uom = frappe.db.get_value("Item", doc.item_code, "stock_uom")

        if not stock_uom:
            frappe.logger().warning(f"Item {doc.item_code} has no stock_uom defined")
            return

        if doc.uom != stock_uom:
            # Log the violation
            frappe.logger().warning(f"Item Price violation: {doc.item_code} - UOM {doc.uom} != stock_uom {stock_uom}")

            # Send alert email/Slack (implement based on your notification system)
            alert_message = f"""
⚠️ Item Price UOM Violation Detected

Item: {doc.item_code}
Price List: {doc.price_list}
UOM Used: {doc.uom}
Stock UOM: {stock_uom}
Price: {doc.price_list_rate}

This violates the base UOM pricing policy. Only stock_uom prices should be in Price List.
Please review and correct this entry.

Created by: {doc.owner}
            """

            # Send email alert (configure recipients as needed)
            frappe.sendmail(
                recipients=["admin@yourcompany.com"],  # Configure your alert recipients
                subject=_("Item Price UOM Policy Violation"),
                message=alert_message,
                header=_("POSAwesome Alert")
            )

            # Also create a notification in Frappe
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": _("Item Price UOM Violation"),
                "email_content": alert_message,
                "document_type": "Item Price",
                "document_name": doc.name,
                "from_user": "System",
                "type": "Alert"
            }).insert(ignore_permissions=True)

    except Exception as e:
        frappe.logger().error(f"Error in item_price_monitor.alert_invalid_uom: {str(e)}")
        frappe.log_error(f"Item Price Monitor Error: {e}")