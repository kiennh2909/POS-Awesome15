#!/usr/bin/env python3
"""
Script để tạo dữ liệu mẫu Outstanding Invoices cho testing
Tạo customers với credit terms và invoices chưa thanh toán đầy đủ
"""

import frappe
import json
from frappe.utils import nowdate, add_days, getdate
from decimal import Decimal

def create_sample_customers():
    """Tạo customers mẫu với credit terms"""

    print("🔄 Tạo customers mẫu...")

    customers_data = [
        {
            "name": "CUST001",
            "customer_name": "Nguyễn Văn A",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "customer_type": "Individual",
            "credit_limit": 50000.00,
            "payment_terms": "Net 30"
        },
        {
            "name": "CUST002",
            "customer_name": "Trần Thị B",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "customer_type": "Individual",
            "credit_limit": 30000.00,
            "payment_terms": "Net 15"
        },
        {
            "name": "CUST003",
            "customer_name": "Công ty TNHH ABC",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "customer_type": "Company",
            "credit_limit": 100000.00,
            "payment_terms": "Net 60"
        }
    ]

    created_customers = []

    for cust_data in customers_data:
        try:
            # Kiểm tra customer đã tồn tại chưa
            if frappe.db.exists("Customer", cust_data["name"]):
                print(f"⚠️  Customer {cust_data['name']} đã tồn tại, bỏ qua...")
                continue

            # Tạo customer
            customer = frappe.get_doc({
                "doctype": "Customer",
                "name": cust_data["name"],
                "customer_name": cust_data["customer_name"],
                "customer_group": cust_data["customer_group"],
                "territory": cust_data["territory"],
                "customer_type": cust_data["customer_type"]
            })

            customer.insert(ignore_permissions=True)

            # Set credit limit và payment terms
            customer.db_set("credit_limit", cust_data["credit_limit"])
            customer.db_set("payment_terms", cust_data["payment_terms"])

            created_customers.append(customer.name)
            print(f"✅ Tạo customer: {customer.name} - {customer.customer_name}")

        except Exception as e:
            print(f"❌ Lỗi tạo customer {cust_data['name']}: {str(e)}")

    return created_customers

def create_sample_items():
    """Tạo items mẫu"""

    print("\n🔄 Tạo items mẫu...")

    items_data = [
        {
            "name": "ITEM001",
            "item_name": "Cà phê đen",
            "item_group": "Products",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "valuation_rate": 25.00,
            "standard_rate": 30.00,
            "selling_price": 35.00
        },
        {
            "name": "ITEM002",
            "item_name": "Bánh mì thịt",
            "item_group": "Products",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "valuation_rate": 15.00,
            "standard_rate": 20.00,
            "selling_price": 25.00
        },
        {
            "name": "ITEM003",
            "item_name": "Nước ngọt",
            "item_group": "Products",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "valuation_rate": 8.00,
            "standard_rate": 10.00,
            "selling_price": 12.00
        }
    ]

    created_items = []

    for item_data in items_data:
        try:
            # Kiểm tra item đã tồn tại chưa
            if frappe.db.exists("Item", item_data["name"]):
                print(f"⚠️  Item {item_data['name']} đã tồn tại, bỏ qua...")
                continue

            # Tạo item
            item = frappe.get_doc({
                "doctype": "Item",
                "name": item_data["name"],
                "item_name": item_data["item_name"],
                "item_group": item_data["item_group"],
                "stock_uom": item_data["stock_uom"],
                "is_stock_item": item_data["is_stock_item"],
                "valuation_rate": item_data["valuation_rate"],
                "standard_rate": item_data["standard_rate"]
            })

            item.insert(ignore_permissions=True)

            # Tạo Item Price
            item_price = frappe.get_doc({
                "doctype": "Item Price",
                "item_code": item.name,
                "price_list": "Standard Selling",
                "price_list_rate": item_data["selling_price"],
                "currency": "VND"
            })

            item_price.insert(ignore_permissions=True)

            created_items.append(item.name)
            print(f"✅ Tạo item: {item.name} - {item.item_name}")

        except Exception as e:
            print(f"❌ Lỗi tạo item {item_data['name']}: {str(e)}")

    return created_items

def create_outstanding_invoices(customers, items):
    """Tạo invoices với outstanding amount"""

    print("\n🔄 Tạo outstanding invoices...")

    # Lấy company đầu tiên
    company = frappe.get_all("Company", limit=1)
    if not company:
        print("❌ Không tìm thấy company nào!")
        return []

    company_name = company[0].name
    print(f"📍 Sử dụng company: {company_name}")

    # Lấy POS Profile đầu tiên
    pos_profile = frappe.get_all("POS Profile", limit=1)
    pos_profile_name = pos_profile[0].name if pos_profile else None

    invoices_data = [
        {
            "customer": customers[0] if customers else "CUST001",
            "items": [
                {"item_code": items[0] if items else "ITEM001", "qty": 2, "rate": 35000},
                {"item_code": items[1] if items else "ITEM002", "qty": 1, "rate": 25000}
            ],
            "outstanding_percent": 100,  # Thanh toán 100% - chưa thanh toán gì
            "posting_date": add_days(nowdate(), -5)
        },
        {
            "customer": customers[1] if len(customers) > 1 else "CUST002",
            "items": [
                {"item_code": items[2] if len(items) > 2 else "ITEM003", "qty": 5, "rate": 12000}
            ],
            "outstanding_percent": 60,  # Thanh toán 40% - còn nợ 60%
            "posting_date": add_days(nowdate(), -3)
        },
        {
            "customer": customers[2] if len(customers) > 2 else "CUST003",
            "items": [
                {"item_code": items[0] if items else "ITEM001", "qty": 10, "rate": 35000},
                {"item_code": items[1] if items else "ITEM002", "qty": 5, "rate": 25000},
                {"item_code": items[2] if len(items) > 2 else "ITEM003", "qty": 8, "rate": 12000}
            ],
            "outstanding_percent": 80,  # Thanh toán 20% - còn nợ 80%
            "posting_date": add_days(nowdate(), -1)
        }
    ]

    created_invoices = []

    for i, inv_data in enumerate(invoices_data, 1):
        try:
            # Tạo Sales Invoice
            invoice = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": inv_data["customer"],
                "company": company_name,
                "posting_date": inv_data["posting_date"],
                "due_date": add_days(inv_data["posting_date"], 30),
                "currency": "VND",
                "conversion_rate": 1.0,
                "selling_price_list": "Standard Selling",
                "pos_profile": pos_profile_name,
                "is_pos": 1,
                "update_stock": 0
            })

            # Thêm items
            total_amount = 0
            for item_data in inv_data["items"]:
                item_amount = item_data["qty"] * item_data["rate"]
                total_amount += item_amount

                invoice.append("items", {
                    "item_code": item_data["item_code"],
                    "qty": item_data["qty"],
                    "rate": item_data["rate"],
                    "amount": item_amount,
                    "uom": "Nos",
                    "conversion_factor": 1.0
                })

            # Set totals
            invoice.grand_total = total_amount
            invoice.base_grand_total = total_amount
            invoice.outstanding_amount = (total_amount * inv_data["outstanding_percent"]) / 100

            # Insert và submit
            invoice.insert(ignore_permissions=True)
            invoice.submit()

            created_invoices.append({
                "name": invoice.name,
                "customer": invoice.customer,
                "total": total_amount,
                "outstanding": invoice.outstanding_amount
            })

            print(f"✅ Tạo invoice: {invoice.name}")
            print(f"   Customer: {invoice.customer}")
            print(f"   Total: {total_amount:,.0f} VND")
            print(f"   Outstanding: {invoice.outstanding_amount:,.0f} VND")

        except Exception as e:
            print(f"❌ Lỗi tạo invoice {i}: {str(e)}")
            import traceback
            traceback.print_exc()

    return created_invoices

def setup_credit_system():
    """Thiết lập hệ thống credit"""

    print("\n🔄 Thiết lập hệ thống credit...")

    try:
        # Tạo Payment Terms nếu chưa có
        payment_terms_data = [
            {"name": "Net 15", "credit_days": 15, "credit_months": 0},
            {"name": "Net 30", "credit_days": 30, "credit_months": 0},
            {"name": "Net 60", "credit_days": 60, "credit_months": 0}
        ]

        for pt_data in payment_terms_data:
            if not frappe.db.exists("Payment Terms Template", pt_data["name"]):
                pt = frappe.get_doc({
                    "doctype": "Payment Terms Template",
                    "name": pt_data["name"],
                    "template_name": pt_data["name"]
                })

                pt.append("terms", {
                    "payment_term": pt_data["name"],
                    "description": f"Payment due in {pt_data['credit_days']} days",
                    "credit_days": pt_data["credit_days"],
                    "credit_months": pt_data["credit_months"]
                })

                pt.insert(ignore_permissions=True)
                print(f"✅ Tạo Payment Terms: {pt.name}")
            else:
                print(f"⚠️  Payment Terms {pt_data['name']} đã tồn tại")

        # Tạo Price List nếu chưa có
        if not frappe.db.exists("Price List", "Standard Selling"):
            pl = frappe.get_doc({
                "doctype": "Price List",
                "name": "Standard Selling",
                "price_list_name": "Standard Selling",
                "selling": 1,
                "currency": "VND"
            })
            pl.insert(ignore_permissions=True)
            print("✅ Tạo Price List: Standard Selling")

        print("✅ Hệ thống credit đã được thiết lập!")

    except Exception as e:
        print(f"❌ Lỗi thiết lập credit system: {str(e)}")

def main():
    """Main function"""

    print("=" * 60)
    print("🚀 TẠO DỮ LIỆU MẪU OUTSTANDING INVOICES")
    print("=" * 60)

    try:
        # Khởi tạo Frappe
        frappe.init(site="your-site-name")  # Thay bằng site name thực tế
        frappe.connect()

        # Thiết lập credit system
        setup_credit_system()

        # Tạo customers
        customers = create_sample_customers()

        # Tạo items
        items = create_sample_items()

        # Tạo outstanding invoices
        invoices = create_outstanding_invoices(customers, items)

        # Summary
        print("\n" + "=" * 60)
        print("📊 TÓM TẮT DỮ LIỆU ĐÃ TẠO")
        print("=" * 60)

        print(f"👥 Customers: {len(customers)}")
        for cust in customers:
            print(f"   - {cust}")

        print(f"\n📦 Items: {len(items)}")
        for item in items:
            print(f"   - {item}")

        print(f"\n🧾 Outstanding Invoices: {len(invoices)}")
        total_outstanding = sum(inv["outstanding"] for inv in invoices)
        print(f"💰 Tổng outstanding: {total_outstanding:,.0f} VND")

        for inv in invoices:
            print(f"   - {inv['name']}: {inv['customer']} - {inv['outstanding']:,.0f} VND")

        print("\n✅ Hoàn thành! Bạn có thể test Outstanding Invoices trong POS.")
        print("💡 Mẹo: Sử dụng nút 'Refresh' trong UI để load lại data.")

    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            frappe.destroy()
        except:
            pass

if __name__ == "__main__":
    main()