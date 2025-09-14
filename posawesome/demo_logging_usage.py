# -*- coding: utf-8 -*-
"""
Demo: Cách sử dụng POS Awesome Logging Helper

File này minh họa cách sử dụng helper get_logger để chuẩn hóa logging trong ứng dụng.
"""

import frappe
from posawesome.posawesome.utils.logging import get_logger, invoice_log, shift_report_log

def demo_basic_usage():
    """Demo cách sử dụng cơ bản"""
    print("=== DEMO BASIC USAGE ===")

    # Cách 1: Tạo logger riêng cho module
    log = get_logger("demo_module")
    log.info("Đây là log info từ demo_module")
    log.warning("Đây là log warning từ demo_module")
    log.error("Đây là log error từ demo_module")

    # Cách 2: Sử dụng pre-configured loggers
    invoice_log.info("Log từ invoice module")
    shift_report_log.info("Log từ shift report module")

def demo_invoice_processing():
    """Demo xử lý invoice với logging chuẩn"""
    print("\n=== DEMO INVOICE PROCESSING ===")

    # Giả lập xử lý invoice
    invoice_data = {
        "name": "INV-2025-0001",
        "customer": "CUST-001",
        "grand_total": 150.00,
        "status": "Paid"
    }

    invoice_log.info(f"[INVOICE_PROCESSING] 🏁 Bắt đầu xử lý invoice: {invoice_data['name']}")
    invoice_log.info(f"[INVOICE_PROCESSING] 👤 Khách hàng: {invoice_data['customer']}")
    invoice_log.info(f"[INVOICE_PROCESSING] 💰 Tổng tiền: {invoice_data['grand_total']}")
    invoice_log.info(f"[INVOICE_PROCESSING] 📊 Trạng thái: {invoice_data['status']}")

    # Giả lập cập nhật shift report
    shift_report_log.info(f"[SHIFT_UPDATE] 🔄 Cập nhật shift report cho invoice: {invoice_data['name']}")
    shift_report_log.info(f"[SHIFT_UPDATE] ✅ Hoàn thành cập nhật shift report")

    invoice_log.info(f"[INVOICE_PROCESSING] 🎉 Hoàn thành xử lý invoice: {invoice_data['name']}")

def demo_error_handling():
    """Demo xử lý lỗi với logging"""
    print("\n=== DEMO ERROR HANDLING ===")

    try:
        # Giả lập lỗi
        result = 1 / 0
    except Exception as e:
        invoice_log.error(f"[ERROR_HANDLING] 💥 Lỗi không mong muốn: {str(e)}")
        invoice_log.error(f"[ERROR_HANDLING] 📍 Chi tiết lỗi: {frappe.get_traceback()}")

if __name__ == "__main__":
    print("🚀 POS Awesome Logging Demo")
    print("=" * 50)

    demo_basic_usage()
    demo_invoice_processing()
    demo_error_handling()

    print("\n" + "=" * 50)
    print("✅ Demo hoàn thành!")
    print("\n📝 Log files sẽ được tạo tại:")
    print("   - sites/{site}/logs/demo_module.log")
    print("   - sites/{site}/logs/invoice.log")
    print("   - sites/{site}/logs/shift_report.log")