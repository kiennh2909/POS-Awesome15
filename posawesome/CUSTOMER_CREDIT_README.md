# 🎯 Hướng Dẫn Hoàn Chỉnh: "Use Customer Credit" Option

## 📋 Tổng Quan

**"Use Customer Credit"** là tính năng cho phép khách hàng sử dụng **credit/tín dụng** có sẵn để thanh toán hóa đơn trong POS-Awesome. Đây là công cụ quan trọng để tối ưu hóa cash flow và tăng customer satisfaction.

## 🚀 Quick Start

### 1. Kích Hoạt Tính Năng
```javascript
// Trong POS Profile
{
  "use_customer_credit": true
}
```

### 2. Tạo Demo Data
```bash
cd /path/to/posawesome
python demo_customer_credit.py
```

### 3. Test Trong POS
```
1. Mở POS > Chọn Customer có credit
2. Tạo invoice mới
3. Bật "Use Customer Credit" switch
4. Xem credit khả dụng và redeem
5. Submit invoice
```

## 📁 Files Overview

| File | Mục đích | Cách sử dụng |
|------|----------|--------------|
| `USE_CUSTOMER_CREDIT_ANALYSIS.md` | Phân tích chi tiết | Đọc để hiểu cách hoạt động |
| `demo_customer_credit.py` | Tạo demo scenario | `python demo_customer_credit.py` |
| `create_sample_outstanding_invoices.py` | Tạo data mẫu | `python create_sample_outstanding_invoices.py` |
| `quick_test_credit_system.py` | Test nhanh | `python quick_test_credit_system.py` |

## 🎯 Cách Hoạt Động

### Luồng Cơ Bản
```
Customer có Outstanding Invoice/Advance Payment
                    ↓
POS thu ngân bật "Use Customer Credit"
                    ↓
Hệ thống hiển thị credit khả dụng
                    ↓
Auto-allocate credit cho invoice
                    ↓
Customer chỉ trả phần còn lại
```

### Các Loại Credit

#### 1. **Invoice Credit** (Từ hóa đơn chưa thanh toán)
```javascript
{
  type: "Invoice",
  credit_origin: "INV-2024-001",
  total_credit: 50000,
  credit_to_redeem: 30000
}
```

#### 2. **Advance Credit** (Từ thanh toán trước)
```javascript
{
  type: "Advance",
  credit_origin: "PAY-2024-001",
  total_credit: 100000,
  credit_to_redeem: 50000
}
```

#### 3. **M-Pesa Credit** (Từ mobile money)
```javascript
{
  type: "Advance",
  credit_origin: "MPESA-001",
  total_credit: 25000,
  credit_to_redeem: 25000
}
```

## 🎨 Giao Diện Người Dùng

### 1. Switch Kích Hoạt
```vue
<v-switch
  v-model="redeem_customer_credit"
  label="Use Customer Credit"
  @update:model-value="get_available_credit(redeem_customer_credit)"
/>
```

### 2. Hiển Thị Credit
```vue
<!-- Credit khả dụng -->
<v-text-field
  label="You can redeem credit up to"
  :model-value="formatCurrency(available_customer_credit)"
  readonly
/>

<!-- Credit đã redeem -->
<v-text-field
  label="Redeemed Customer Credit"
  :model-value="formatCurrency(redeemed_customer_credit)"
  readonly
/>
```

### 3. Chi Tiết Credit Entries
```vue
<v-row v-for="(row, idx) in customer_credit_dict">
  <v-col cols="4">{{ row.credit_origin }}</v-col>
  <v-col cols="4">
    <v-text-field label="Available" :model-value="formatCurrency(row.total_credit)" readonly />
  </v-col>
  <v-col cols="4">
    <v-text-field
      label="Redeem"
      :model-value="formatCurrency(row.credit_to_redeem)"
      @change="setFormatedCurrency(row, 'credit_to_redeem')"
    />
  </v-col>
</v-row>
```

## 🔧 Cấu Hình

### 1. POS Profile Setup
```javascript
// Trong POS Profile
{
  "use_customer_credit": true,  // Bật tính năng
  "company": "Your Company",
  "cost_center": "Main",        // Cần thiết cho journal entries
  "currency": "VND"
}
```

### 2. Customer Setup
```javascript
// Customer với credit
{
  "credit_limit": 200000,
  "payment_terms": "Net 30"
}
```

### 3. ERPNext Settings
```
Setup > POS Profile > [Your Profile]
✅ Use Customer Credit: Enabled
✅ Cost Center: Set
✅ Currency: VND
```

## 💰 Business Logic

### Auto-Allocation Algorithm
```javascript
allocate_credit_automatically() {
  const invoiceAmount = this.invoice_doc.grand_total;
  let remainAmount = invoiceAmount;

  // Ưu tiên invoice cũ nhất
  this.customer_credit_dict
    .sort((a, b) => new Date(a.posting_date) - new Date(b.posting_date))
    .forEach((row) => {
      if (remainAmount > 0) {
        if (remainAmount >= row.total_credit) {
          row.credit_to_redeem = row.total_credit;
          remainAmount -= row.total_credit;
        } else {
          row.credit_to_redeem = remainAmount;
          remainAmount = 0;
        }
      } else {
        row.credit_to_redeem = 0;
      }
    });
}
```

### Validation Rules
```javascript
// 1. Không vượt quá available credit
if (newVal > this.available_customer_credit) {
  this.redeemed_customer_credit = this.available_customer_credit;
}

// 2. Không vượt quá invoice total
if (this.redeemed_customer_credit > this.invoice_doc.grand_total) {
  // Error message
}

// 3. Không dùng cho return invoices
if (this.invoice_doc.is_return) {
  // Disable credit redemption
}
```

## 🔄 Backend Processing

### 1. API: get_available_credit
```python
@frappe.whitelist()
def get_available_credit(customer, company):
    """Lấy credit khả dụng của customer"""

    # Outstanding invoices
    invoices = frappe.get_all("Sales Invoice",
        filters={
            "customer": customer,
            "company": company,
            "outstanding_amount": (">", 0),
            "docstatus": 1
        },
        fields=["name", "outstanding_amount", "posting_date"]
    )

    # Advance payments
    advances = frappe.get_all("Payment Entry",
        filters={
            "party_type": "Customer",
            "party": customer,
            "unallocated_amount": (">", 0),
            "docstatus": 1
        },
        fields=["name", "unallocated_amount", "posting_date"]
    )

    return [
        {
            "type": "Invoice",
            "credit_origin": inv.name,
            "total_credit": inv.outstanding_amount,
            "posting_date": inv.posting_date
        } for inv in invoices
    ] + [
        {
            "type": "Advance",
            "credit_origin": adv.name,
            "total_credit": adv.unallocated_amount,
            "posting_date": adv.posting_date
        } for adv in advances
    ]
```

### 2. Submit Invoice với Credit
```python
@frappe.whitelist()
def submit_invoice(invoice, data):
    data = json.loads(data)

    # Xử lý credit redemption
    if data.get("redeemed_customer_credit"):
        redeeming_customer_credit(invoice_doc, data)

    # Submit invoice
    invoice_doc.submit()
```

### 3. Journal Entry Creation
```python
def redeeming_customer_credit(invoice_doc, data):
    """Tạo journal entry cho credit redemption"""

    for row in data.get("customer_credit_dict", []):
        if row["credit_to_redeem"] > 0:
            # Tạo journal voucher
            create_credit_journal_entry(invoice_doc, row)
```

## 📊 Monitoring & Reporting

### Credit Utilization Report
```sql
SELECT
    c.customer_name,
    c.credit_limit,
    SUM(si.outstanding_amount) as used_credit,
    ROUND(SUM(si.outstanding_amount) / c.credit_limit * 100, 2) as utilization_percent
FROM `tabCustomer` c
LEFT JOIN `tabSales Invoice` si ON c.name = si.customer
WHERE si.outstanding_amount > 0
    AND si.docstatus = 1
GROUP BY c.name, c.customer_name, c.credit_limit
ORDER BY utilization_percent DESC;
```

### Credit Aging Report
```sql
SELECT
    customer,
    SUM(CASE WHEN datediff(curdate(), posting_date) <= 30 THEN outstanding_amount ELSE 0 END) as current,
    SUM(CASE WHEN datediff(curdate(), posting_date) BETWEEN 31 AND 60 THEN outstanding_amount ELSE 0 END) as overdue_30,
    SUM(CASE WHEN datediff(curdate(), posting_date) BETWEEN 61 AND 90 THEN outstanding_amount ELSE 0 END) as overdue_60,
    SUM(CASE WHEN datediff(curdate(), posting_date) > 90 THEN outstanding_amount ELSE 0 END) as overdue_90
FROM `tabSales Invoice`
WHERE outstanding_amount > 0 AND docstatus = 1
GROUP BY customer;
```

## 🎯 Best Practices

### 1. **Credit Policy Setup**
```javascript
const creditPolicies = {
  "New Customer": { limit: 50000, terms: "Net 15" },
  "Regular Customer": { limit: 100000, terms: "Net 30" },
  "VIP Customer": { limit: 500000, terms: "Net 60" }
};
```

### 2. **Auto-Allocation Strategy**
```javascript
// Prioritize by age (oldest first)
const creditPriority = [
  "Invoice",  // Outstanding invoices
  "Advance",  // Advance payments
  "M-Pesa"    // Mobile money
];
```

### 3. **Risk Management**
- Set appropriate credit limits
- Regular credit reviews
- Monitor payment patterns
- Have collection procedures

## 🚨 Troubleshooting

### Vấn Đề Thường Gặp

#### 1. **Credit Không Hiển Thị**
```javascript
// Debug steps
console.log("Customer:", this.invoice_doc.customer);
console.log("POS Profile:", this.pos_profile.use_customer_credit);
console.log("Available Credit:", this.available_customer_credit);
```

**Solutions:**
- ✅ Kiểm tra POS Profile có `use_customer_credit = true`
- ✅ Kiểm tra customer có outstanding invoices/advance payments
- ✅ Kiểm tra network connection

#### 2. **Redeem Credit Failed**
```javascript
// Check validation
if (this.redeemed_customer_credit > this.available_customer_credit) {
  console.error("Redeemed amount exceeds available credit");
}
```

**Solutions:**
- ✅ Validate redeemed amount ≤ available credit
- ✅ Validate redeemed amount ≤ invoice total
- ✅ Check for return invoices (not allowed)

#### 3. **Journal Entry Errors**
```python
# Check cost center
cost_center = frappe.get_value("POS Profile", invoice_doc.pos_profile, "cost_center")
if not cost_center:
  frappe.throw(_("Cost Center is not set in POS Profile"))
```

**Solutions:**
- ✅ Set cost center in POS Profile
- ✅ Check user permissions
- ✅ Verify accounting setup

## 🎉 Demo Scenario

### Tạo Demo Data
```bash
python demo_customer_credit.py
```

### Expected Output
```
🎬 TẠO SCENARIO DEMO CUSTOMER CREDIT
===============================================

1️⃣ TẠO CUSTOMER VỚI CREDIT:
✅ Tạo customer: CUST-DEMO-001
   Credit Limit: 200,000 VND
   Payment Terms: Net 30

2️⃣ TẠO ITEMS MẪU:
✅ Tạo item: DEMO001 - Cà phê đen Demo
✅ Tạo item: DEMO002 - Bánh mì thịt Demo
✅ Tạo item: DEMO003 - Nước ngọt Demo

3️⃣ TẠO OUTSTANDING INVOICE ĐẦU TIÊN:
✅ Tạo invoice: INV-2024-00001
   Tổng tiền: 95,000 VND
   Outstanding: 95,000 VND

4️⃣ TẠO ADVANCE PAYMENT:
✅ Tạo advance payment: PAY-2024-00001
   Số tiền: 50,000 VND

5️⃣ TẠO INVOICE THỨ HAI (SỬ DỤNG CREDIT):
✅ Tạo invoice draft: INV-2024-00002
   Tổng tiền: 59,000 VND

6️⃣ TÍNH TOÁN CREDIT CÓ SẴN:
✅ Total Available Credit: 145,000 VND
   📄 INV-2024-00001: 95,000 VND (Invoice)
   📄 PAY-2024-00001: 50,000 VND (Advance)

7️⃣ SIMULATE CREDIT REDEMPTION:
💰 Redeemed Credit: 50,000 VND
📋 Credit Breakdown:
   Invoice INV-2024-00001: 30,000 VND
   Advance PAY-2024-00001: 20,000 VND
```

### Test Trong POS
```
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
```

## 🎯 Kết Luận

**"Use Customer Credit"** là tính năng mạnh mẽ giúp:

- ✅ **Tối ưu cash flow** - Thu tiền trước, giao hàng sau
- ✅ **Tăng customer satisfaction** - Linh hoạt thanh toán
- ✅ **Xây dựng loyalty** - Khuyến khích mua hàng nhiều hơn
- ✅ **Tự động hóa quy trình** - Auto-allocate credit
- ✅ **Hỗ trợ đa dạng** - Multiple credit types và currencies

### Khuyến Nghị Triển Khai:

1. **Bắt Đầu Nhỏ**: Test với customers đáng tin cậy
2. **Set Clear Policies**: Xác định credit limits và terms
3. **Monitor Regularly**: Theo dõi credit utilization
4. **Train Staff**: Đào tạo sử dụng tính năng hiệu quả

### Next Steps:
- [ ] Cấu hình POS Profile với `use_customer_credit = true`
- [ ] Test với customer có outstanding invoices
- [ ] Monitor credit utilization
- [ ] Adjust credit policies dựa trên performance

---

**🚀 Tính năng này sẽ mang lại giá trị kinh doanh đáng kể khi được sử dụng đúng cách!**