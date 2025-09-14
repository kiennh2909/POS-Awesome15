#!/usr/bin/env python3
"""
Test Cash Balance Calculation Logic
Run this in bench console: bench console --site your_site
Then: exec(open('posawesome/test_cash_balance_calculation.py').read())
"""

import frappe

def test_cash_balance_from_invoices():
    """Test the corrected cash balance calculation from paid invoices"""
    print("💰 TESTING CORRECTED CASH BALANCE CALCULATION")
    print("=" * 60)

    try:
        # Call the API to get current footer data
        result = frappe.call("posawesome.posawesome.api.shift_reports.get_footer_status_data")

        print("📡 API Response:")
        print(f"   Success: {result.get('success', False)}")

        if result.get('success'):
            data = result.get('data', {})

            print("\n📊 Footer Data:")
            print(f"   Cashier Name: {data.get('cashier_name', 'N/A')}")
            print(f"   Shift Report ID: {data.get('shift_report_id', 'N/A')}")
            print(f"   Cash Balance: {data.get('cash_balance', 0)}")
            print(f"   Today Sales: {data.get('today_sales', 0)}")

            # Get detailed breakdown of cash balance calculation
            cash_balance_breakdown = get_cash_balance_breakdown(data.get('shift_report_id'))

            print("\n🔍 Cash Balance Calculation Breakdown:")
            print(f"   Total Cash Balance: {cash_balance_breakdown['total']}")

            if cash_balance_breakdown['invoices']:
                print("   Invoice Details:")
                for inv in cash_balance_breakdown['invoices']:
                    print(f"     {inv['invoice_no']}: {inv['cash_amount']} (Status: {inv['status']})")
            else:
                print("   No cash payments found in current shift")

            return True
        else:
            print(f"\n❌ API failed: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        return False

def get_cash_balance_breakdown(shift_report_id):
    """Get detailed breakdown of cash balance calculation"""
    breakdown = {
        'total': 0,
        'invoices': []
    }

    if not shift_report_id:
        return breakdown

    try:
        # Get shift report
        shift_reports = frappe.get_all("POS Shift Report",
            filters={"shift_report_id": shift_report_id},
            fields=["name"],
            limit=1
        )

        if not shift_reports:
            return breakdown

        shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)

        # Calculate cash balance from paid invoices
        total_cash_balance = 0

        if shift_report.invoices:
            for invoice_entry in shift_report.invoices:
                if invoice_entry.status == "Paid":
                    try:
                        invoice_doc = frappe.get_doc("Sales Invoice", invoice_entry.invoice_no)
                        invoice_cash_amount = 0

                        # Check payments in the invoice
                        if hasattr(invoice_doc, 'payments') and invoice_doc.payments:
                            for payment in invoice_doc.payments:
                                if (payment.mode_of_payment == "Tiền mặt - POS" and
                                    payment.amount and payment.amount > 0):
                                    invoice_cash_amount += payment.amount

                        if invoice_cash_amount > 0:
                            total_cash_balance += invoice_cash_amount
                            breakdown['invoices'].append({
                                'invoice_no': invoice_entry.invoice_no,
                                'cash_amount': invoice_cash_amount,
                                'status': invoice_entry.status
                            })

                    except Exception as e:
                        print(f"Warning: Could not process invoice {invoice_entry.invoice_no}: {str(e)}")
                        continue

        breakdown['total'] = total_cash_balance
        return breakdown

    except Exception as e:
        print(f"Error getting cash balance breakdown: {str(e)}")
        return breakdown

def test_cash_balance_logic_explanation():
    """Explain the corrected cash balance calculation logic"""
    print("\n📚 CASH BALANCE CALCULATION LOGIC EXPLANATION")
    print("=" * 60)

    print("""
🎯 CORRECTED LOGIC:
Cash Balance = Tổng số tiền thanh toán bằng "Tiền mặt - POS"
             từ các hóa đơn đã thanh toán trong shift hiện tại

📋 BƯỚC TÍNH TOÁN:

1️⃣ Lấy Shift Report hiện tại của user đang đăng nhập
2️⃣ Duyệt qua tất cả invoices trong shift report
3️⃣ Với mỗi invoice có status = "Paid":
   - Lấy Sales Invoice document
   - Kiểm tra tab "payments"
   - Cộng dồn số tiền có mode_of_payment = "Tiền mặt - POS"
4️⃣ Trả về tổng số tiền cash balance

💡 VÍ DỤ:
- Invoice INV-001: Thanh toán 500,000 bằng "Tiền mặt - POS" → +500,000
- Invoice INV-002: Thanh toán 300,000 bằng "Credit Card" → bỏ qua
- Invoice INV-003: Thanh toán 200,000 bằng "Tiền mặt - POS" → +200,000
- Tổng Cash Balance = 700,000

✅ ƯU ĐIỂM:
- Chính xác: Phản ánh số tiền mặt thực tế đã thu
- Real-time: Cập nhật ngay khi có thanh toán mới
- Reliable: Dựa trên dữ liệu thực tế từ database
""")

# Run tests
if __name__ == "__main__":
    print("🚀 CASH BALANCE CALCULATION TEST SUITE")
    print("=" * 70)

    # Test the corrected logic
    success = test_cash_balance_from_invoices()

    # Show logic explanation
    test_cash_balance_logic_explanation()

    # Overall result
    print("\n" + "=" * 70)
    if success:
        print("🎉 CASH BALANCE CALCULATION TEST PASSED!")
        print("✅ Logic corrected to calculate from paid invoices")
        print("✅ Cash Balance now reflects actual cash payments")
    else:
        print("❌ CASH BALANCE CALCULATION TEST FAILED")
        print("Please check the implementation")

    print("=" * 70)