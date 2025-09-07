# 🎯 Hướng Dẫn Hoàn Chỉnh: Thiết Lập & Debug Outstanding Invoices

## 📋 Tổng Quan

Bộ công cụ này giúp bạn:
- ✅ Debug vấn đề Outstanding Invoices không load
- ✅ Thiết lập hệ thống credit cho khách hàng
- ✅ Tạo dữ liệu mẫu để test
- ✅ Monitor và maintain credit system

## 🚀 Quick Start

### 1. Thiết Lập Hệ Thống Credit

```bash
# 1. Tạo dữ liệu mẫu (customers, items, invoices)
python posawesome/create_sample_outstanding_invoices.py

# 2. Test hệ thống
python posawesome/quick_test_credit_system.py
```

### 2. Debug Outstanding Invoices

```bash
# Test API và database
python posawesome/test_outstanding_invoices.py
```

## 📁 Files Overview

| File | Mục đích | Cách sử dụng |
|------|----------|--------------|
| `create_sample_outstanding_invoices.py` | Tạo dữ liệu mẫu | `python create_sample_outstanding_invoices.py` |
| `quick_test_credit_system.py` | Test nhanh hệ thống | `python quick_test_credit_system.py` |
| `test_outstanding_invoices.py` | Debug chi tiết | `python test_outstanding_invoices.py` |
| `CREDIT_SYSTEM_SETUP.md` | Hướng dẫn setup | Đọc và làm theo |
| `DEBUG_OUTSTANDING_INVOICES.md` | Hướng dẫn debug | Đọc khi gặp lỗi |

## 🎯 Workflow Hoàn Chỉnh

### Bước 1: Thiết Lập Credit System
```
1. Đọc CREDIT_SYSTEM_SETUP.md
2. Tạo Payment Terms Templates
3. Cấu hình Customer Groups
4. Setup Customers với credit limits
```

### Bước 2: Tạo Dữ Liệu Mẫu
```bash
# Tạo tất cả data mẫu
python create_sample_outstanding_invoices.py
```

### Bước 3: Test Hệ Thống
```bash
# Test nhanh
python quick_test_credit_system.py

# Output expected:
✅ Customers với credit: ✅
✅ Outstanding invoices: ✅
✅ API hoạt động: ✅
✅ Payment terms: ✅
🎯 Overall status: ✅ HỆ THỐNG HOẠT ĐỘNG TỐT
```

### Bước 4: Test Trong POS
```
1. Mở POS > Payments
2. Chọn customer có credit
3. Click "Search" → Xem outstanding invoices
4. Test thanh toán
```

### Bước 5: Debug Nếu Có Lỗi
```bash
# Chạy debug script
python test_outstanding_invoices.py

# Kiểm tra logs trong:
# - Browser Console (F12)
# - Server logs: tail -f logs/frappe.log
```

## 🔧 Modified Files

### Frontend Changes
- `posawesome/public/js/posapp/components/payments/Pay.vue`
  - ✅ Thêm logging chi tiết
  - ✅ Thêm nút "Refresh"
  - ✅ Methods `refreshOutstandingInvoices()` và `reloadOutstandingInvoices()`

### Backend Changes
- `posawesome/posawesome/api/payment_entry.py`
  - ✅ Thêm logging chi tiết trong `get_outstanding_invoices()`
  - ✅ Better error handling
  - ✅ Parameter validation

## 📊 Monitoring & Maintenance

### Daily Checks
```bash
# Chạy test hàng ngày
python quick_test_credit_system.py
```

### Weekly Reports
```sql
-- Outstanding summary
SELECT
    customer,
    COUNT(*) as invoice_count,
    SUM(outstanding_amount) as total_outstanding,
    AVG(DATEDIFF(CURDATE(), posting_date)) as avg_age
FROM `tabSales Invoice`
WHERE outstanding_amount > 0
    AND docstatus = 1
GROUP BY customer
ORDER BY total_outstanding DESC;
```

### Monthly Reviews
- Review credit limits
- Update payment terms
- Clean up old data

## 🚨 Troubleshooting

### Lỗi Thường Gặp

#### 1. "Outstanding Invoices không hiển thị"
```bash
# Debug steps:
python test_outstanding_invoices.py
# Check browser console logs
# Verify customer has credit limit
```

#### 2. "API call failed"
```bash
# Check:
# - Customer exists
# - Company is set
# - POS Profile has currency
# - Network connection
```

#### 3. "No data in database"
```bash
# Run:
python create_sample_outstanding_invoices.py
```

#### 4. "Credit limit not working"
```bash
# Verify:
# - Customer credit limit > 0
# - POS Profile allows credit sales
# - User permissions
```

## 📈 Best Practices

### 1. **Data Management**
- Regular cleanup of old invoices
- Archive completed transactions
- Backup before major changes

### 2. **Security**
- Limit credit controller roles
- Audit credit limit changes
- Monitor payment patterns

### 3. **Performance**
- Index database tables
- Cache frequently used data
- Monitor API response times

## 🎯 Success Metrics

### KPIs Quan Trọng
- ✅ Outstanding Invoices load trong < 2 giây
- ✅ API response time < 500ms
- ✅ Credit utilization < 80%
- ✅ Payment collection rate > 95%

### Monitoring Commands
```bash
# API Performance
time python -c "
from posawesome.posawesome.api.payment_entry import get_outstanding_invoices
result = get_outstanding_invoices(customer='CUST001', company='Your Company', currency='VND')
print(f'Found {len(result)} invoices')
"

# Database Health
mysql -e "
SELECT
    COUNT(*) as total_invoices,
    SUM(outstanding_amount) as total_outstanding,
    AVG(outstanding_amount) as avg_invoice
FROM tabSales_Invoice
WHERE outstanding_amount > 0 AND docstatus = 1;
"
```

## 📞 Support

### Quick Debug Checklist
- [ ] Browser Console có errors?
- [ ] Server logs có exceptions?
- [ ] Database có data?
- [ ] API parameters đúng?
- [ ] Network connection ổn?

### Emergency Contacts
- Check `DEBUG_OUTSTANDING_INVOICES.md` for detailed troubleshooting
- Run `python test_outstanding_invoices.py` for comprehensive diagnostics
- Review `CREDIT_SYSTEM_SETUP.md` for configuration issues

---

## 🎉 Kết Luận

Với bộ công cụ này, bạn có thể:
- 🚀 Thiết lập credit system nhanh chóng
- 🔍 Debug issues chuyên nghiệp
- 📊 Monitor performance hiệu quả
- 💰 Tối ưu cash flow doanh nghiệp

**Bắt đầu ngay:** `python create_sample_outstanding_invoices.py` 🚀