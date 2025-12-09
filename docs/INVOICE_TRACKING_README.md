# Invoice Tracking System for POS Shift Report

## Tổng quan

Hệ thống tracking này cho phép theo dõi một invoice cụ thể qua toàn bộ luồng xử lý trong POS Shift Report system với logging chi tiết.

## Cách hoạt động

### 1. Luồng xử lý Invoice

```
Sales Invoice Creation
        ↓
validate_shift() → Set shift report reference
        ↓
on_submit() → update_shift_report_with_invoice("submit")
        ↓
Add invoice to shift report
        ↓
update_calculated_fields() → Tính toán totals
        ↓
get_payment_breakdown() → Tính toán payment methods
        ↓
Save & Commit changes
        ↓
on_cancel() → update_shift_report_with_invoice("cancel")
        ↓
Mark as cancelled & update calculations
```

### 2. Log Patterns

#### [INVOICE_TRACKING] - Invoice Processing
```
🔍 VALIDATE_SHIFT - Validate POS shift requirements
📤 ON_SUBMIT - Invoice submission start
🗑️ ON_CANCEL - Invoice cancellation start
🎯 UPDATE_SHIFT_REPORT - Main processing function
✅ UPDATE_SHIFT_REPORT - Successful completion
💥 UPDATE_SHIFT_REPORT - Error occurred
```

#### [SHIFT_REPORT_CALC] - Shift Report Calculations
```
🔢 UPDATE_CALCULATED_FIELDS - Start calculation
📊 UPDATE_CALCULATED_FIELDS - Processing invoices
💰 UPDATE_CALCULATED_FIELDS - Added to total_sales
💸 UPDATE_CALCULATED_FIELDS - Added to total_returns
✅ UPDATE_CALCULATED_FIELDS - Calculation completed
💳 GET_PAYMENT_BREAKDOWN - Payment processing
```

## Cách sử dụng

### 1. Monitor Logs Real-time

```bash
# Terminal 1: Monitor logs
chmod +x posawesome/monitor_invoice_logs.sh
./posawesome/monitor_invoice_logs.sh

# Terminal 2: Run invoice tracking
python posawesome/track_invoice_flow.py
```

### 2. Manual Log Checking

```bash
# Check recent logs
tail -f /home/frappe/frappe-bench/logs/frappe.log | grep INVOICE_TRACKING

# Check calculation logs
tail -f /home/frappe/frappe-bench/logs/frappe.log | grep SHIFT_REPORT_CALC

# Search for specific invoice
grep "INV-00123" /home/frappe/frappe-bench/logs/frappe.log
```

### 3. Test Scripts

```bash
# Track complete invoice flow
python posawesome/track_invoice_flow.py

# Test new calculation logic
python posawesome/test_new_shift_report_logic.py

# Debug shift report updates
python posawesome/debug_shift_report_updates.py
```

## Chi tiết từng bước

### Bước 1: Invoice Validation
```
[INVOICE_TRACKING] 🔍 VALIDATE_SHIFT - Invoice: INV-00123, Opening Shift: POSA-OS-25-0000106
[INVOICE_TRACKING] ✅ VALIDATE_SHIFT - Set shift report reference - Invoice: INV-00123, Shift Report: SHIFT-POSA-OS-25-0000106
```

### Bước 2: Invoice Submission
```
[INVOICE_TRACKING] 📤 ON_SUBMIT - Invoice: INV-00123, Status: Draft, Amount: 150.00
[INVOICE_TRACKING] 🔄 ON_SUBMIT - Calling update_shift_report_with_invoice
[INVOICE_TRACKING] 🎯 UPDATE_SHIFT_REPORT - Start - Invoice: INV-00123, Action: submit
[INVOICE_TRACKING] 💳 UPDATE_SHIFT_REPORT - Payment method detected - Method: Cash
[SHIFT_REPORT_CALC] 🔢 UPDATE_CALCULATED_FIELDS - Start
[SHIFT_REPORT_CALC] 📊 UPDATE_CALCULATED_FIELDS - Processing 1 invoices
[SHIFT_REPORT_CALC] 💰 UPDATE_CALCULATED_FIELDS - Added to total_sales: 150.00
[SHIFT_REPORT_CALC] ✅ UPDATE_CALCULATED_FIELDS - Completed - Count: 1, Sales: 150.00
[INVOICE_TRACKING] 🎉 UPDATE_SHIFT_REPORT - COMPLETED
```

### Bước 3: Invoice Cancellation
```
[INVOICE_TRACKING] 🗑️ ON_CANCEL - Invoice: INV-00123, Status: Paid, Amount: 150.00
[INVOICE_TRACKING] 🔄 ON_CANCEL - Calling update_shift_report_with_invoice
[INVOICE_TRACKING] 🎯 UPDATE_SHIFT_REPORT - Start - Invoice: INV-00123, Action: cancel
[INVOICE_TRACKING] ✅ UPDATE_SHIFT_REPORT - Marked as cancelled
[SHIFT_REPORT_CALC] 🔢 UPDATE_CALCULATED_FIELDS - Start
[SHIFT_REPORT_CALC] 📊 UPDATE_CALCULATED_FIELDS - Processing 1 invoices
[SHIFT_REPORT_CALC] 💸 UPDATE_CALCULATED_FIELDS - Added to total_returns: 150.00
[SHIFT_REPORT_CALC] ✅ UPDATE_CALCULATED_FIELDS - Completed - Count: 1, Returns: 150.00
[INVOICE_TRACKING] 🎉 UPDATE_SHIFT_REPORT - COMPLETED
```

## Logic tính toán

### invoice_count
- **Đếm tất cả invoices** (bao gồm Cancelled)
- Mục đích: Theo dõi tổng số transactions

### total_sales
- **Chỉ tính Paid invoices** (status == "Paid" && is_return == False)
- Mục đích: Doanh thu thực tế từ giao dịch thành công

### total_returns
- **Chỉ tính Cancelled invoices** (status == "Cancelled")
- Mục đích: Giá trị các giao dịch đã bị hủy

### payment_breakdown
- **Chỉ tính Paid invoices** (status == "Paid")
- Mục đích: Phân tích phương thức thanh toán từ giao dịch thực tế

## Troubleshooting

### Không thấy logs
```bash
# Check if logs are being written
ls -la /home/frappe/frappe-bench/logs/

# Check frappe log level
grep "log_level" /home/frappe/frappe-bench/sites/erp152-v1.vtcom.online/site_config.json
```

### Invoice không được track
```bash
# Check if invoice has shift report reference
SELECT name, posa_pos_opening_shift, pos_shift_report
FROM `tabSales Invoice`
WHERE name = 'INV-00123';
```

### Shift report không được update
```bash
# Check shift report exists
SELECT name, shift_report_id, invoice_count, total_sales, total_returns
FROM `tabPOS Shift Report`
WHERE name = 'SHIFT-XXX';
```

## Files được modify

1. `posawesome/posawesome/api/invoice.py` - Thêm logging cho invoice processing
2. `posawesome/posawesome/doctype/pos_shift_report/pos_shift_report.py` - Thêm logging cho calculations

## Files test/debug

1. `posawesome/track_invoice_flow.py` - Test complete invoice flow
2. `posawesome/monitor_invoice_logs.sh` - Monitor logs real-time
3. `posawesome/test_new_shift_report_logic.py` - Test calculation logic
4. `posawesome/debug_shift_report_updates.py` - Debug updates

## Kết luận

Hệ thống tracking này cung cấp visibility hoàn chỉnh vào việc xử lý invoice trong POS Shift Report system, giúp debug và monitor hiệu quả.