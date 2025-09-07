# 🏦 Hướng Dẫn Thiết Lập Hệ Thống Credit (Công Nợ) Cho Khách Hàng

## 📋 Tổng Quan

Hệ thống credit cho phép khách hàng mua hàng mà không cần thanh toán ngay lập tức, tạo ra các **Outstanding Invoices** (hóa đơn chưa thanh toán). Đây là tính năng quan trọng cho doanh nghiệp B2B.

## 🎯 Cách Hoạt Động

### 1. **Quy Trình Cơ Bản:**
```
Khách hàng mua hàng → Tạo Sales Invoice → Submit → Tạo Outstanding Amount
                    ↓
Khách hàng thanh toán → Tạo Payment Entry → Cập nhật Outstanding Amount
```

### 2. **Các Thành Phần Chính:**

#### **Payment Terms (Điều Khoản Thanh Toán)**
- Xác định thời hạn thanh toán (Net 15, Net 30, Net 60 days)
- Tự động tính due date cho invoices

#### **Credit Limit (Hạn Mức Tín Dụng)**
- Giới hạn số tiền khách hàng có thể nợ
- Ngăn chặn bán hàng vượt quá hạn mức

#### **Outstanding Amount**
- Số tiền khách hàng còn nợ
- Tính từ: `Total Invoice - Payments Received`

## 🛠️ Thiết Lập Hệ Thống

### Bước 1: Tạo Payment Terms Template

#### **Cách 1: Qua UI (Khuyến nghị)**
```
Accounting > Payment Terms Template > New
```

**Tạo các template sau:**

1. **Net 15 Days**
   - Template Name: Net 15
   - Terms:
     - Payment Term: Net 15
     - Description: Payment due in 15 days
     - Credit Days: 15

2. **Net 30 Days**
   - Template Name: Net 30
   - Terms:
     - Payment Term: Net 30
     - Description: Payment due in 30 days
     - Credit Days: 30

3. **Net 60 Days**
   - Template Name: Net 60
   - Terms:
     - Payment Term: Net 60
     - Description: Payment due in 60 days
     - Credit Days: 60

#### **Cách 2: Qua Code**
```python
# Chạy script tạo payment terms
python posawesome/create_sample_outstanding_invoices.py
```

### Bước 2: Cấu Hình Customer Groups

```
Selling > Customer Group > All Customer Groups
```

**Settings:**
- ✅ Default Payment Terms Template: Net 30
- ✅ Credit Controller: (để trống)
- ✅ Account Manager: (để trống)

### Bước 3: Thiết Lập Customers Với Credit

#### **Cách 1: Tạo Customer Mới**
```
Selling > Customer > New
```

**Thông tin cơ bản:**
- Customer Name: Nguyễn Văn A
- Customer Group: All Customer Groups
- Territory: All Territories
- Customer Type: Individual/Company

**Credit Settings:**
- Payment Terms: Net 30
- Credit Limit: 50,000.00
- Credit Days: 30
- Currency: VND

#### **Cách 2: Cập Nhật Customer Hiện Tại**
```python
# Sử dụng script để tạo customers mẫu
python posawesome/create_sample_outstanding_invoices.py
```

### Bước 4: Thiết Lập POS Profile

```
POS > POS Profile > [Your POS Profile]
```

**Settings quan trọng:**
- ✅ Allow Sales Order: ✅
- ✅ Allow Draft Invoice: ✅
- ✅ Allow Return: ✅
- ✅ Update Stock: ✅ (tùy chọn)

## 💰 Tạo Outstanding Invoices

### Phương Pháp 1: Qua POS Interface

1. **Mở POS**
2. **Chọn Customer** có credit limit
3. **Thêm Items** vào giỏ hàng
4. **Submit Invoice** (không cần thanh toán ngay)
5. **Invoice được tạo** với Outstanding Amount = Grand Total

### Phương Pháp 2: Qua Sales Invoice

```
Accounts > Sales Invoice > New
```

**Settings:**
- Customer: [Customer với credit]
- Payment Terms: Net 30
- Due Date: Tự động tính
- Items: Thêm sản phẩm
- Submit: Tạo invoice với outstanding amount

### Phương Pháp 3: Sử Dụng Script

```bash
# Chạy script tạo dữ liệu mẫu
python posawesome/create_sample_outstanding_invoices.py
```

## 🔍 Kiểm Tra Outstanding Invoices

### 1. **Trong POS Payments**
- Mở tab **Payments**
- Chọn customer
- Click **Search** → Xem danh sách outstanding invoices

### 2. **Trong Database**
```sql
-- Xem tất cả outstanding invoices
SELECT name, customer, outstanding_amount, grand_total, posting_date, due_date
FROM `tabSales Invoice`
WHERE docstatus = 1
AND outstanding_amount > 0
ORDER BY posting_date DESC;

-- Xem theo customer
SELECT name, outstanding_amount, due_date
FROM `tabSales Invoice`
WHERE customer = 'CUST001'
AND outstanding_amount > 0;
```

### 3. **Trong Reports**
```
Accounts > Sales Invoice > Outstanding Invoices Report
```

## 💳 Thanh Toán Outstanding Invoices

### Phương Pháp 1: Qua POS Payments

1. **Mở POS > Payments**
2. **Chọn Customer**
3. **Click Search** → Xem outstanding invoices
4. **Chọn Invoice(s)** cần thanh toán
5. **Nhập số tiền thanh toán**
6. **Submit Payment**

### Phương Pháp 2: Qua Payment Entry

```
Accounts > Payment Entry > New
```

**Settings:**
- Payment Type: Receive
- Party Type: Customer
- Party: [Customer Name]
- References: Chọn outstanding invoices
- Paid Amount: Số tiền thanh toán

## 📊 Monitoring Credit

### 1. **Credit Limit Check**
Hệ thống tự động kiểm tra:
- Tổng outstanding amount của customer
- Credit limit đã set
- Cảnh báo khi vượt hạn mức

### 2. **Reports Quan Trọng**
```
- Accounts Receivable Summary
- Customer Credit Balance
- Aged Receivables
- Payment Terms Report
```

### 3. **Dashboard Widgets**
- Total Outstanding Amount
- Overdue Invoices
- Customer Credit Utilization

## ⚙️ Advanced Configuration

### 1. **Credit Controller**
```
Setup > User > [User] > Credit Controller
```
- User được phép approve credit vượt hạn mức

### 2. **Automatic Reminders**
```
Setup > Email Alert
```
- Tạo alerts cho overdue invoices
- Tự động gửi reminder cho customers

### 3. **Dunning Process**
```
Setup > Letter Head
```
- Tạo template cho dunning letters
- Tự động gửi khi quá hạn

## 🔧 Troubleshooting

### **Vấn đề: Outstanding Invoices không hiển thị**

**Nguyên nhân có thể:**
1. Customer không có payment terms
2. Invoice chưa được submit
3. Outstanding amount = 0
4. POS Profile không đúng

**Giải pháp:**
```bash
# Debug với script
python posawesome/test_outstanding_invoices.py
```

### **Vấn đề: Credit Limit không hoạt động**

**Kiểm tra:**
1. Customer có credit limit > 0
2. POS Profile cho phép credit sales
3. User có quyền tạo invoices

### **Vấn đề: Payment không cập nhật Outstanding**

**Nguyên nhân:**
1. Payment Entry chưa submit
2. Sai party account
3. Invoice references không đúng

## 📈 Best Practices

### 1. **Credit Policy**
- Xác định rõ credit terms cho từng customer group
- Định kỳ review credit limits
- Monitor payment patterns

### 2. **Risk Management**
- Set appropriate credit limits
- Regular credit checks
- Diversify customer base

### 3. **Collections**
- Send timely reminders
- Follow up on overdue accounts
- Consider collection agencies for chronic overdue

## 🎯 Kết Luận

Thiết lập hệ thống credit đúng cách sẽ:
- ✅ Tăng doanh số bán hàng
- ✅ Cải thiện cash flow
- ✅ Xây dựng mối quan hệ khách hàng lâu dài
- ✅ Giảm rủi ro bad debt

Sử dụng script `create_sample_outstanding_invoices.py` để tạo dữ liệu mẫu và test hệ thống ngay hôm nay! 🚀