# 🚀 SHIFT_CLOSE_WORKFLOW Logging System

Hệ thống logging cơ bản cho việc theo dõi quy trình đóng ca POS (Point of Sale).

## 📋 Tổng quan

Hệ thống logging này được thiết kế để:
- Theo dõi các bước quan trọng trong quy trình đóng ca POS
- Ghi lại thông tin debug và error
- Cải thiện khả năng troubleshooting

## 🏗️ Kiến trúc hệ thống

```
SHIFT_CLOSE_WORKFLOW Logging System
├── 📊 Vue Components (Frontend)
│   ├── Payments.vue - Logging cho payment operations
│   └── Pos.vue - Logging cho POS operations
├── 🔧 Python Backend
│   ├── API Endpoints - Logging cho API calls
│   ├── DocTypes - Logging cho database operations
│   └── Business Logic - Logging cho quy trình nghiệp vụ
└── 📁 Log Files
    ├── shift_close_workflow.log - Main log file
    └── frappe.log - Frappe system logs
```

## 🚀 Hướng dẫn sử dụng

### Kiểm tra logs

```bash
# Xem logs real-time
tail -f /home/frappe/frappe-bench/logs/shift_close_workflow.log

# Tìm logs liên quan đến SHIFT_CLOSE_WORKFLOW
grep "SHIFT_CLOSE_WORKFLOW" /home/frappe/frappe-bench/logs/shift_close_workflow.log
```

## 📊 Log Format & Messages

### Log Message Format
```
[timestamp] [level] [SHIFT_CLOSE_WORKFLOW] [ACTION] - Details: value, User: username
```

### Các loại actions chính

#### Vue Component Actions
- `VUE_SUBMIT_PAYMENT_START` - Bắt đầu submit payment
- `VUE_SUBMIT_PAYMENT_SUCCESS` - Submit payment thành công
- `VUE_SUBMIT_INVOICE_START` - Bắt đầu submit invoice
- `VUE_SUBMIT_INVOICE_SUCCESS` - Submit invoice thành công
- `VUE_SET_FULL_AMOUNT_START` - Bắt đầu set full amount
- `VUE_GET_CLOSING_DATA_SUCCESS` - Lấy closing data thành công

#### API Actions
- `API_GET_CLOSING_DATA_START` - API bắt đầu lấy closing data
- `API_SUBMIT_CLOSING_POS_SUCCESS` - API submit closing POS thành công
- `API_LOAD_SHIFT_REPORT_SUCCESS` - API load shift report thành công

#### Error Actions
- `API_SUBMIT_CLOSING_SHIFT_ERROR` - Lỗi submit closing shift
- `VUE_PAYMENT_VALIDATION_ERROR` - Lỗi validation payment
- `SYSTEM_NETWORK_ERROR` - Lỗi network

## 🛠️ Troubleshooting

### Log không hiển thị
```bash
# Kiểm tra quyền file log
ls -la /home/frappe/frappe-bench/logs/

# Restart services
bench restart
```

## 📋 Best Practices

### 1. Log Levels
- **DEBUG**: Chi tiết cho development
- **INFO**: Thông tin quan trọng về workflow
- **WARNING**: Cảnh báo không nghiêm trọng
- **ERROR**: Lỗi cần attention

### 2. Log Message Format
```javascript
// ✅ Good
console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_INVOICE_SUCCESS - Invoice: ${invoice.name}, User: ${frappe.session.user}`);

// ❌ Bad
console.log("Invoice submitted successfully");
```

### 3. Performance Considerations
- Sử dụng structured logging
- Tránh log trong loops
- Regular log rotation

### 4. Security
- Không log sensitive data (passwords, tokens)
- Sanitize user inputs in logs
- Access control for log files

---

*For technical support, please contact the development team.*