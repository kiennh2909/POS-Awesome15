# Debug Guide: Outstanding Invoices Loading Issue

## 🚨 Vấn đề: Outstanding Invoices không load được

### 🔍 **Các bước debug:**

## 1. Frontend Debug (Browser Console)

### Mở Developer Tools (F12) và kiểm tra Console:

```javascript
// Trong browser console, chạy:
console.log("[DEBUG] Current state:", {
    customer_name: "check_customer_name_here",
    company: "check_company_here",
    pos_profile: "check_pos_profile_here",
    isOffline: "check_offline_status"
});
```

### Các log cần tìm:
- `[DEBUG] get_outstanding_invoices called`
- `[DEBUG] Current state:`
- `[DEBUG] Calling API with params:`
- `[DEBUG] API response received:`
- `[OUTSTANDING_INVOICES] Starting fetch`

## 2. Backend Debug (Server Logs)

### Kiểm tra server logs:
```bash
# Trong terminal, chạy:
tail -f logs/frappe.log | grep -i outstanding
```

### Hoặc kiểm tra logs trong Frappe:
```bash
bench --site your-site-name doctor
```

## 3. Database Debug

### Chạy script test:
```bash
cd /path/to/your/site
python posawesome/test_outstanding_invoices.py
```

### Hoặc kiểm tra database trực tiếp:
```sql
-- Kiểm tra invoices có outstanding amount
SELECT name, customer, outstanding_amount, grand_total, posting_date
FROM `tabSales Invoice`
WHERE docstatus = 1
AND outstanding_amount > 0
AND is_return = 0
ORDER BY posting_date DESC
LIMIT 10;

-- Kiểm tra customers
SELECT name, customer_name FROM `tabCustomer` LIMIT 10;

-- Kiểm tra companies
SELECT name FROM `tabCompany`;
```

## 4. API Test Trực tiếp

### Test API qua browser:
```
GET /api/method/posawesome.posawesome.api.payment_entry.get_outstanding_invoices?customer=CustomerName&company=CompanyName&currency=USD
```

### Hoặc qua Python console:
```python
import frappe
from posawesome.posawesome.api.payment_entry import get_outstanding_invoices

result = get_outstanding_invoices(
    customer="CustomerName",
    company="CompanyName",
    currency="USD"
)
print(result)
```

## 🔧 **Các nguyên nhân phổ biến và cách fix:**

### 1. **Không có customer được chọn**
```
Log: [DEBUG] No customer selected, cannot fetch outstanding invoices
```
**Fix:** Đảm bảo đã chọn customer trước khi load invoices

### 2. **Không có company được set**
```
Log: [DEBUG] No company set, cannot fetch outstanding invoices
```
**Fix:** Kiểm tra POS Profile có company hợp lệ

### 3. **Không có currency trong POS Profile**
```
Log: [DEBUG] No currency set in POS profile, cannot fetch outstanding invoices
```
**Fix:** Thêm currency vào POS Profile

### 4. **Không có data trong database**
```
Log: [OUTSTANDING_INVOICES] Found 0 outstanding invoices
```
**Fix:** Tạo một số Sales Invoices với outstanding amount > 0

### 5. **API call thất bại**
```
Log: [DEBUG] API call failed: Network Error
```
**Fix:** Kiểm tra network connection và server status

### 6. **Party Account không tồn tại**
```
Log: [OUTSTANDING_INVOICES] Party account for customer X: None
```
**Fix:** Tạo Party Account cho customer trong company

## 📋 **Checklist Debug:**

- [ ] Mở Browser Console (F12)
- [ ] Click nút "Search" trong Outstanding Invoices
- [ ] Kiểm tra logs trong Console
- [ ] Kiểm tra server logs
- [ ] Chạy test script
- [ ] Verify database có data
- [ ] Test API trực tiếp
- [ ] Kiểm tra network connection

## 🛠️ **Quick Fixes:**

### 1. Force Refresh:
```javascript
// Trong browser console:
vm.reloadOutstandingInvoices()
```

### 2. Clear Cache:
```javascript
// Trong browser console:
localStorage.clear()
location.reload()
```

### 3. Test với data mẫu:
```sql
-- Tạo customer mẫu
INSERT INTO `tabCustomer` (name, customer_name, customer_group, territory, customer_type)
VALUES ('TEST001', 'Test Customer', 'All Customer Groups', 'All Territories', 'Individual');

-- Tạo invoice mẫu
INSERT INTO `tabSales Invoice` (name, customer, posting_date, grand_total, outstanding_amount, docstatus, is_return)
VALUES ('TEST-INV-001', 'TEST001', CURDATE(), 100.00, 100.00, 1, 0);
```

## 📞 **Nếu vẫn không hoạt động:**

1. **Restart server:**
```bash
bench restart
```

2. **Clear all cache:**
```bash
bench --site your-site-name clear-cache
```

3. **Rebuild assets:**
```bash
bench --site your-site-name build
```

4. **Check permissions:**
- Đảm bảo user có quyền đọc Sales Invoice
- Đảm bảo user có quyền truy cập API

## 📝 **Logs quan trọng cần check:**

### Frontend Logs:
- `[DEBUG] get_outstanding_invoices called`
- `[DEBUG] API response received:`
- `[DEBUG] outstanding_invoices set to:`

### Backend Logs:
- `[OUTSTANDING_INVOICES] Starting fetch`
- `[OUTSTANDING_INVOICES] Found X outstanding invoices`
- `[OUTSTANDING_INVOICES] Error in get_outstanding_invoices`

### Database Logs:
- Số lượng invoices
- Số lượng customers
- Party accounts

---

## 🎯 **Kết luận:**

Với logging chi tiết đã được thêm vào, bạn có thể dễ dàng xác định nguyên nhân tại sao Outstanding Invoices không load được. Các bước debug trên sẽ giúp bạn tìm ra và fix vấn đề một cách có hệ thống.