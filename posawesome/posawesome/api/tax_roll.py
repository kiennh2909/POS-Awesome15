
import frappe
from frappe import _
from datetime import datetime
import re

@frappe.whitelist()
def update_tax_roll(pos_profile, new_prefix, new_start_number, action="new_roll"):
    """
    Cập nhật thông tin cuộn hóa đơn thuế

    Args:
        pos_profile: Tên POS Profile
        new_prefix: Prefix mới (VD: PW, BZ, CZ)
        new_start_number: Số bắt đầu
        action: "new_roll" hoặc "update"
    """
    if not frappe.has_permission("POS Profile", "write"):
        frappe.throw(_("Không có quyền cập nhật POS Profile"))
    
    # Validate prefix format (exactly 2 uppercase letters)
    if not re.match(r'^[A-Z]{2}$', new_prefix):
        frappe.throw(_("Prefix phải là đúng 2 ký tự in hoa (VD: PW, BZ, CZ)"))
    
    # Validate start number
    try:
        start_num = int(new_start_number)
        if start_num < 1:
            frappe.throw(_("Số bắt đầu phải lớn hơn 0"))
    except (ValueError, TypeError):
        frappe.throw(_("Số bắt đầu không hợp lệ"))

    doc = frappe.get_doc("POS Profile", pos_profile)

    # Cập nhật thông tin
    doc.tax_roll_code = new_prefix
    doc.tax_start_number = start_num
    doc.tax_current_counter = start_num  # Reset về số bắt đầu
    doc.tax_roll_status = "Active"
    doc.tax_update_time = datetime.now()
    
    # Thêm trường để track ai cập nhật
    if hasattr(doc, 'tax_update_by_cashier'):
        doc.tax_update_by_cashier = frappe.session.user

    doc.save()
    frappe.db.commit()

    return {
        "success": True,
        "message": _("Đã cập nhật cuộn hóa đơn thuế thành công"),
        "tax_code_display": f"{new_prefix} {start_num}",
        "tax_roll_code": new_prefix,
        "tax_start_number": start_num,
        "tax_current_counter": start_num,
        "tax_roll_status": "Active",
        "tax_update_time": doc.tax_update_time.strftime("%Y-%m-%d %H:%M:%S") if doc.tax_update_time else None
    }


@frappe.whitelist()
def increment_tax_counter(pos_profile, invoice_name, tax_code):
    """
    Tăng counter sau khi in thành công
    
    Args:
        pos_profile: Tên POS Profile
        invoice_name: Tên hóa đơn
        tax_code: Mã thuế đã được in
    """
    if not frappe.has_permission("POS Profile", "write"):
        frappe.throw(_("Không có quyền cập nhật POS Profile"))

    doc = frappe.get_doc("POS Profile", pos_profile)
    
    # Tăng counter
    new_counter = doc.tax_current_counter + 1
    doc.tax_current_counter = new_counter
    doc.tax_update_time = datetime.now()
    
    doc.save()
    
    # Cập nhật tax_code cho Sales Invoice
    try:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
        invoice_doc.tax_code = tax_code
        invoice_doc.save()
    except frappe.DoesNotExistError:
        frappe.log_error(f"Invoice {invoice_name} not found for tax code update")
    
    frappe.db.commit()

    return {
        "success": True,
        "new_counter": new_counter,
        "next_display": f"{doc.tax_roll_code} {new_counter}",
        "message": _("Đã cập nhật tax counter thành công")
    }


@frappe.whitelist()
def get_tax_roll_status(pos_profile):
    """
    Lấy trạng thái hiện tại của cuộn hóa đơn thuế
    
    Args:
        pos_profile: Tên POS Profile
    """
    doc = frappe.get_doc("POS Profile", pos_profile)
    
    return {
        "tax_roll_code": doc.get("tax_roll_code"),
        "tax_start_number": doc.get("tax_start_number"),
        "tax_current_counter": doc.get("tax_current_counter"),
        "tax_roll_status": doc.get("tax_roll_status"),
        "tax_update_time": doc.get("tax_update_time"),
        "display": f"{doc.get('tax_roll_code', '')} {doc.get('tax_current_counter', '')}" if doc.get("tax_roll_code") else None
    }


@frappe.whitelist()
def validate_tax_roll_config(prefix, start_number):
    """
    Validate cấu hình cuộn hóa đơn thuế
    
    Args:
        prefix: Prefix cần validate
        start_number: Số bắt đầu cần validate
    """
    errors = []
    
    # Validate prefix
    if not prefix:
        errors.append("Prefix không được để trống")
    elif not re.match(r'^[A-Z]{2}$', prefix):
        errors.append("Prefix phải là đúng 2 ký tự in hoa (VD: PW, BZ, CZ)")
    
    # Validate start number
    try:
        start_num = int(start_number)
        if start_num < 1:
            errors.append("Số bắt đầu phải lớn hơn 0")
    except (ValueError, TypeError):
        errors.append("Số bắt đầu không hợp lệ")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "preview": f"{prefix} {start_number}" if len(errors) == 0 else None
    }


@frappe.whitelist()
def get_current_tax_info(pos_profile):
    """
    Lấy thông tin mã thuế hiện tại để hiển thị
    
    Args:
        pos_profile: Tên POS Profile
    """
    doc = frappe.get_doc("POS Profile", pos_profile)
    
    # Tạo mã thuế hiện tại
    current_tax_code = None
    if doc.get("tax_roll_code") and doc.get("tax_current_counter"):
        current_tax_code = f"{doc.get('tax_roll_code')} {doc.get('tax_current_counter')}"
    
    return {
        "tax_roll_code": doc.get("tax_roll_code"),
        "tax_start_number": doc.get("tax_start_number"),
        "tax_current_counter": doc.get("tax_current_counter"),
        "tax_roll_status": doc.get("tax_roll_status"),
        "tax_update_time": doc.get("tax_update_time"),
        "current_tax_code": current_tax_code,
        "display": current_tax_code
    }
