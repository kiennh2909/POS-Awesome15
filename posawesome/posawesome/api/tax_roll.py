
import frappe
from frappe import _
from datetime import datetime

@frappe.whitelist()
def update_tax_roll(pos_profile, new_prefix, new_start_number, action="new_roll"):
    """
    Cập nhật thông tin cuộn hóa đơn thuế
    
    Args:
        pos_profile: Tên POS Profile
        new_prefix: Prefix mới (VD: PW, BZ)
        new_start_number: Số bắt đầu
        action: "new_roll" hoặc "update"
    """
    if not frappe.has_permission("POS Profile", "write"):
        frappe.throw(_("Không có quyền cập nhật POS Profile"))
    
    doc = frappe.get_doc("POS Profile", pos_profile)
    
    # Cập nhật thông tin
    doc.tax_roll_code = new_prefix
    doc.tax_start_number = int(new_start_number)
    doc.tax_current_counter = int(new_start_number)  # Reset về số bắt đầu
    doc.tax_roll_status = "Active"
    doc.tax_update_time = datetime.now()
    doc.tax_update_by_cashier = frappe.session.user
    
    doc.save()
    frappe.db.commit()
    
    return {
        "success": True,
        "message": _("Đã cập nhật cuộn hóa đơn thuế thành công"),
        "tax_code_display": f"{new_prefix} {new_start_number}"
    }

@frappe.whitelist()
def get_current_tax_info(pos_profile):
    """
    Lấy thông tin cuộn hóa đơn thuế hiện tại
    """
    doc = frappe.get_doc("POS Profile", pos_profile)
    
    return {
        "tax_roll_code": doc.get("tax_roll_code"),
        "tax_start_number": doc.get("tax_start_number"),
        "tax_current_counter": doc.get("tax_current_counter"),
        "tax_roll_status": doc.get("tax_roll_status"),
        "tax_update_time": doc.get("tax_update_time"),
        "tax_update_by_cashier": doc.get("tax_update_by_cashier"),
        "current_display": f"{doc.get('tax_roll_code', '')} {doc.get('tax_current_counter', '')}" if doc.get("tax_roll_code") else ""
    }

@frappe.whitelist()
def increment_tax_counter(pos_profile, invoice_name, tax_code):
    """
    Tăng bộ đếm sau khi in thành công
    """
    if not frappe.has_permission("POS Profile", "write"):
        frappe.throw(_("Không có quyền cập nhật POS Profile"))
    
    # Cập nhật POS Profile
    doc = frappe.get_doc("POS Profile", pos_profile)
    doc.tax_current_counter = doc.tax_current_counter + 1
    doc.tax_update_time = datetime.now()
    doc.tax_update_by_cashier = frappe.session.user
    doc.save()
    
    # Cập nhật Sales Invoice
    if invoice_name:
        frappe.db.set_value("Sales Invoice", invoice_name, "tax_code", tax_code)
    
    frappe.db.commit()
    
    return {
        "success": True,
        "new_counter": doc.tax_current_counter,
        "next_display": f"{doc.tax_roll_code} {doc.tax_current_counter}"
    }
