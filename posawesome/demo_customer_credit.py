#!/usr/bin/env python3
"""
Demo script để test tính năng "Use Customer Credit"
Tạo scenario thực tế và demo cách hoạt động
"""

import frappe
from frappe.utils import nowdate, add_days
import json

def create_demo_scenario():
    """Tạo scenario demo cho customer credit"""

    print("🎬 TẠO SCENARIO DEMO CUSTOMER CREDIT")
    print("=" * 50)

    try:
        frappe.init(site="your-site-name")  # Thay bằng site name thực tế
        frappe.connect()

        # 1. Tạo Customer với Credit
        print("\n1️⃣ TẠO CUSTOMER VỚI CREDIT:")
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Nguyễn Văn Demo",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
            "customer_type": "Individual"
        })
        customer.insert(ignore_permissions=True)

        # Set credit limit và payment terms
        customer.db_set("credit_limit", 200000)
        customer.db_set("payment_terms", "Net 30")

        print(f"✅ Tạo customer: {customer.name}")
        print(f"   Credit Limit: 200,000 VND")
        print(f"   Payment Terms: Net 30")

        # 2. Tạo Items mẫu
        print("\n2️⃣ TẠO ITEMS MẪU:")
        items = [
            {"item_code": "DEMO001", "item_name": "Cà phê đen Demo", "rate": 35000},
            {"item_code": "DEMO002", "item_name": "Bánh mì thịt Demo", "rate": 25000},
            {"item_code": "DEMO003", "item_name": "Nước ngọt Demo", "rate": 12000}
        ]

        for item_data in items:
            if not frappe.db.exists("Item", item_data["item_code"]):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": item_data["item_code"],
                    "item_name": item_data["item_name"],
                    "item_group": "Products",
                    "is_stock_item": 1,
                    "standard_rate": item_data["rate"]
                })
                item.insert(ignore_permissions=True)
                print(f"✅ Tạo item: {item.item_code} - {item.item_name}")

        # 3. Tạo Outstanding Invoice đầu tiên
        print("\n3️⃣ TẠO OUTSTANDING INVOICE ĐẦU TIÊN:")
        invoice1 = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "company": "Your Company",  # Thay bằng company thực tế
            "posting_date": nowdate(),
            "due_date": add_days(nowdate(), 30),
            "currency": "VND",
            "items": [
                {
                    "item_code": "DEMO001",
                    "qty": 2,
                    "rate": 35000,
                    "amount": 70000
                },
                {
                    "item_code": "DEMO002",
                    "qty": 1,
                    "rate": 25000,
                    "amount": 25000
                }
            ],
            "payments": [
                {
                    "mode_of_payment": "Cash",
                    "amount": 95000,
                    "default": 1
                }
            ]
        })
        invoice1.insert(ignore_permissions=True)
        invoice1.submit()

        print(f"✅ Tạo invoice: {invoice1.name}")
        print(f"   Tổng tiền: {invoice1.grand_total:,.0f} VND")
        print(f"   Outstanding: {invoice1.outstanding_amount:,.0f} VND")

        # 4. Tạo Advance Payment
        print("\n4️⃣ TẠO ADVANCE PAYMENT:")
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": customer.name,
            "company": "Your Company",
            "paid_amount": 50000,
            "received_amount": 50000,
            "mode_of_payment": "Cash",
            "posting_date": nowdate()
        })
        payment_entry.insert(ignore_permissions=True)
        payment_entry.submit()

        print(f"✅ Tạo advance payment: {payment_entry.name}")
        print(f"   Số tiền: {payment_entry.paid_amount:,.0f} VND")

        # 5. Tạo Invoice thứ hai (sẽ sử dụng credit)
        print("\n5️⃣ TẠO INVOICE THỨ HAI (SỬ DỤNG CREDIT):")
        invoice2 = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "company": "Your Company",
            "posting_date": nowdate(),
            "due_date": add_days(nowdate(), 30),
            "currency": "VND",
            "items": [
                {
                    "item_code": "DEMO001",
                    "qty": 1,
                    "rate": 35000,
                    "amount": 35000
                },
                {
                    "item_code": "DEMO003",
                    "qty": 2,
                    "rate": 12000,
                    "amount": 24000
                }
            ],
            "payments": [
                {
                    "mode_of_payment": "Cash",
                    "amount": 59000,
                    "default": 1
                }
            ]
        })
        invoice2.insert(ignore_permissions=True)
        # Không submit ngay - để demo redeem credit

        print(f"✅ Tạo invoice draft: {invoice2.name}")
        print(f"   Tổng tiền: {invoice2.grand_total:,.0f} VND")

        # 6. Demo Credit Calculation
        print("\n6️⃣ TÍNH TOÁN CREDIT CÓ SẴN:")
        from posawesome.posawesome.api.payments import get_available_credit

        credit_entries = get_available_credit(customer.name, "Your Company")

        total_available_credit = sum(entry["total_credit"] for entry in credit_entries)
        print(f"✅ Total Available Credit: {total_available_credit:,.0f} VND")

        for entry in credit_entries:
            print(f"   📄 {entry['credit_origin']}: {entry['total_credit']:,.0f} VND ({entry['type']})")

        # 7. Simulate Credit Redemption
        print("\n7️⃣ SIMULATE CREDIT REDEMPTION:")

        # Giả sử redeem 30,000 VND từ invoice đầu và 20,000 VND từ advance
        redemption_data = {
            "redeemed_customer_credit": 50000,
            "customer_credit_dict": [
                {
                    "type": "Invoice",
                    "credit_origin": invoice1.name,
                    "total_credit": invoice1.outstanding_amount,
                    "credit_to_redeem": 30000
                },
                {
                    "type": "Advance",
                    "credit_origin": payment_entry.name,
                    "total_credit": payment_entry.unallocated_amount,
                    "credit_to_redeem": 20000
                }
            ]
        }

        print(f"💰 Redeemed Credit: {redemption_data['redeemed_customer_credit']:,.0f} VND")
        print("📋 Credit Breakdown:")
        for entry in redemption_data["customer_credit_dict"]:
            print(f"   {entry['type']} {entry['credit_origin']}: {entry['credit_to_redeem']:,.0f} VND")

        # 8. Summary
        print("\n" + "=" * 50)
        print("🎯 DEMO SCENARIO SUMMARY:")
        print("=" * 50)
        print(f"👤 Customer: {customer.name}")
        print(f"💳 Credit Limit: {customer.credit_limit:,.0f} VND")
        print(f"📄 Invoice 1: {invoice1.name} - Outstanding: {invoice1.outstanding_amount:,.0f} VND")
        print(f"💰 Advance Payment: {payment_entry.name} - Unallocated: {payment_entry.unallocated_amount:,.0f} VND")
        print(f"📄 Invoice 2 (Draft): {invoice2.name} - Total: {invoice2.grand_total:,.0f} VND")
        print(f"🎁 Available Credit: {total_available_credit:,.0f} VND")
        print(f"🔄 Redeemed in Demo: {redemption_data['redeemed_customer_credit']:,.0f} VND")

        print("\n✅ Demo setup completed successfully!")
        print("\n💡 Next Steps:")
        print("1. Mở POS và chọn customer này")
        print("2. Tạo invoice mới hoặc load invoice draft")
        print("3. Bật 'Use Customer Credit' switch")
        print("4. Xem credit khả dụng và redeem")
        print("5. Submit invoice để test credit redemption")

        return {
            "customer": customer.name,
            "invoice1": invoice1.name,
            "invoice2": invoice2.name,
            "payment": payment_entry.name,
            "credit_available": total_available_credit
        }

    except Exception as e:
        print(f"❌ Demo setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        try:
            frappe.destroy()
        except:
            pass

def demo_credit_redemption():
    """Demo cách redeem credit trong POS"""

    print("\n🎬 DEMO CREDIT REDEMPTION PROCESS")
    print("=" * 50)

    print("""
🛒 SCENARIO: Khách hàng Nguyễn Văn Demo đến cửa hàng

📋 Tình hình hiện tại:
- Có 1 invoice chưa thanh toán: 95,000 VND
- Có advance payment: 50,000 VND
- Tổng credit khả dụng: 145,000 VND

🛍️ Khách hàng mua thêm:
- 1 Cà phê đen: 35,000 VND
- 2 Nước ngọt: 24,000 VND
- Tổng: 59,000 VND

💡 Quy trình thanh toán với credit:

1️⃣ POS thu ngân:
   - Tạo invoice mới: 59,000 VND
   - Bật "Use Customer Credit" switch
   - Hệ thống hiển thị credit khả dụng: 145,000 VND

2️⃣ Tự động allocate credit:
   - Từ invoice cũ: 30,000 VND
   - Từ advance payment: 20,000 VND
   - Tổng redeem: 50,000 VND

3️⃣ Thanh toán còn lại:
   - Tổng invoice: 59,000 VND
   - Credit redeemed: 50,000 VND
   - Còn phải trả: 9,000 VND

4️⃣ Kết quả:
   - Invoice được thanh toán hoàn toàn
   - Credit balance giảm 50,000 VND
   - Outstanding invoice giảm 30,000 VND
   - Advance payment giảm 20,000 VND

🎉 Khách hàng chỉ cần trả 9,000 VND tiền mặt!
    """)

if __name__ == "__main__":
    # Tạo demo scenario
    result = create_demo_scenario()

    if result:
        # Hiển thị demo process
        demo_credit_redemption()

        print(f"\n🎯 Demo data created successfully!")
        print(f"Customer: {result['customer']}")
        print(f"Available Credit: {result['credit_available']:,.0f} VND")
    else:
        print("❌ Failed to create demo scenario")