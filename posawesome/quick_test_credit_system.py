#!/usr/bin/env python3
"""
Quick test script để verify credit system hoạt động
Chạy sau khi đã tạo dữ liệu mẫu
"""

import frappe
from frappe.utils import nowdate

def test_credit_system():
    """Test nhanh hệ thống credit"""

    print("🧪 TESTING CREDIT SYSTEM")
    print("=" * 50)

    try:
        frappe.init(site="your-site-name")  # Thay bằng site name thực tế
        frappe.connect()

        # 1. Kiểm tra customers có credit limit
        print("\n1️⃣ KIỂM TRA CUSTOMERS VỚI CREDIT:")
        customers = frappe.get_all("Customer",
            fields=["name", "customer_name", "credit_limit", "payment_terms"],
            filters={"credit_limit": (">", 0)}
        )

        if customers:
            for cust in customers:
                print(f"✅ {cust.name}: {cust.customer_name}")
                print(f"   Credit Limit: {cust.credit_limit:,.0f}")
                print(f"   Payment Terms: {cust.payment_terms}")
        else:
            print("⚠️  Không tìm thấy customer nào có credit limit")

        # 2. Kiểm tra outstanding invoices
        print("\n2️⃣ KIỂM TRA OUTSTANDING INVOICES:")
        outstanding = frappe.get_all("Sales Invoice",
            filters={
                "docstatus": 1,
                "outstanding_amount": (">", 0),
                "is_return": 0
            },
            fields=["name", "customer", "outstanding_amount", "grand_total", "posting_date"],
            order_by="posting_date desc",
            limit=5
        )

        if outstanding:
            total_outstanding = sum(inv.outstanding_amount for inv in outstanding)
            print(f"✅ Tìm thấy {len(outstanding)} outstanding invoices")
            print(f"💰 Tổng outstanding: {total_outstanding:,.0f}")

            for inv in outstanding:
                print(f"   📄 {inv.name}: {inv.customer} - {inv.outstanding_amount:,.0f}")
        else:
            print("⚠️  Không tìm thấy outstanding invoices nào")

        # 3. Test API get_outstanding_invoices
        print("\n3️⃣ TEST API GET_OUTSTANDING_INVOICES:")

        if customers:
            test_customer = customers[0].name
            print(f"🧪 Test với customer: {test_customer}")

            try:
                from posawesome.posawesome.api.payment_entry import get_outstanding_invoices

                # Lấy company đầu tiên
                company = frappe.get_all("Company", limit=1)
                company_name = company[0].name if company else None

                result = get_outstanding_invoices(
                    customer=test_customer,
                    company=company_name,
                    currency="VND"
                )

                print(f"✅ API trả về {len(result)} invoices")
                if result:
                    print("📋 Sample invoice:")
                    print(f"   Name: {result[0].get('voucher_no')}")
                    print(f"   Outstanding: {result[0].get('outstanding_amount')}")
                    print(f"   Total: {result[0].get('invoice_amount')}")

            except Exception as e:
                print(f"❌ API test failed: {str(e)}")
        else:
            print("⚠️  Bỏ qua API test (không có customer)")

        # 4. Kiểm tra payment terms
        print("\n4️⃣ KIỂM TRA PAYMENT TERMS:")
        payment_terms = frappe.get_all("Payment Terms Template",
            fields=["name", "template_name"]
        )

        if payment_terms:
            print(f"✅ Tìm thấy {len(payment_terms)} payment terms:")
            for pt in payment_terms:
                print(f"   📋 {pt.name}")
        else:
            print("⚠️  Không tìm thấy payment terms nào")

        # Summary
        print("\n" + "=" * 50)
        print("📊 TÓM TẮT TEST RESULTS:")
        print("=" * 50)

        status = {
            "customers": len(customers) > 0,
            "outstanding": len(outstanding) > 0,
            "api": False,  # Will be set below
            "payment_terms": len(payment_terms) > 0
        }

        # Test API result
        if customers:
            try:
                from posawesome.posawesome.api.payment_entry import get_outstanding_invoices
                company = frappe.get_all("Company", limit=1)
                company_name = company[0].name if company else None
                api_result = get_outstanding_invoices(
                    customer=customers[0].name,
                    company=company_name,
                    currency="VND"
                )
                status["api"] = len(api_result) >= 0  # API works if no exception
            except:
                status["api"] = False

        print(f"👥 Customers với credit: {'✅' if status['customers'] else '❌'}")
        print(f"🧾 Outstanding invoices: {'✅' if status['outstanding'] else '❌'}")
        print(f"🔌 API hoạt động: {'✅' if status['api'] else '❌'}")
        print(f"📋 Payment terms: {'✅' if status['payment_terms'] else '❌'}")

        all_good = all(status.values())
        print(f"\n🎯 Overall status: {'✅ HỆ THỐNG HOẠT ĐỘNG TỐT' if all_good else '⚠️  CẦN KIỂM TRA LẠI'}")

        if not all_good:
            print("\n💡 Khuyến nghị:")
            if not status['customers']:
                print("   - Tạo customers với credit limit")
            if not status['outstanding']:
                print("   - Tạo outstanding invoices")
            if not status['api']:
                print("   - Kiểm tra API get_outstanding_invoices")
            if not status['payment_terms']:
                print("   - Tạo payment terms templates")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            frappe.destroy()
        except:
            pass

if __name__ == "__main__":
    test_credit_system()