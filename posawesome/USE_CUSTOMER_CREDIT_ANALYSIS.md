# 🔍 Phân Tích Chi Tiết: "Use Customer Credit" Option Trong POS Profile

## 📋 Tổng Quan

**"Use Customer Credit"** là một tính năng quan trọng trong POS-Awesome cho phép khách hàng sử dụng **credit/tín dụng** có sẵn để thanh toán hóa đơn. Đây là một phần của hệ thống **Customer Credit Management**.

## 🎯 Cách Hoạt Động

### 1. **Kiến Trúc Tổng Quan**

```
POS Profile Setting → Customer Credit Toggle → Credit Redemption UI → Payment Processing
```

### 2. **Luồng Hoạt Động Chi Tiết**

#### **Bước 1: Kích Hoạt Tính Năng**
```javascript
// Trong POS Profile
{
  "use_customer_credit": true  // Cho phép sử dụng credit
}
```

#### **Bước 2: Hiển Thị UI**
```vue
<!-- Switch để bật/tắt redeem credit -->
<v-col cols="6" v-if="!invoice_doc.is_return && pos_profile.use_customer_credit">
  <v-switch
    v-model="redeem_customer_credit"
    flat
    label="Use Customer Credit"
    @update:model-value="get_available_credit(redeem_customer_credit)"
  />
</v-col>
```

#### **Bước 3: Lấy Credit Khả Dụng**
```javascript
get_available_credit(use_credit) {
  if (use_credit) {
    frappe.call({
      method: "posawesome.posawesome.api.payments.get_available_credit",
      args: {
        customer: this.invoice_doc.customer,
        company: this.pos_profile.company
      }
    }).then((r) => {
      this.customer_credit_dict = r.message;
      // Tự động allocate credit cho invoice
      this.allocate_credit_automatically();
    });
  }
}
```

#### **Bước 4: Xử Lý Thanh Toán**
```javascript
// Trong submit_invoice
const data = {
  redeemed_customer_credit: this.redeemed_customer_credit,
  customer_credit_dict: this.customer_credit_dict,
  // ... other payment data
};
```

## 🔧 Cấu Hình POS Profile

### **Cách 1: Qua ERPNext UI**
```
Setup > POS Profile > [Your POS Profile]
```
- ✅ **Use Customer Credit**: Enable/disable tính năng

### **Cách 2: Qua Database**
```sql
UPDATE `tabPOS Profile`
SET use_customer_credit = 1
WHERE name = 'Your POS Profile';
```

### **Cách 3: Qua Code**
```javascript
// Trong POS Profile object
pos_profile.use_customer_credit = true;
```

## 💰 Các Loại Credit

### **1. Invoice Credit (Credit từ hóa đơn)**
```javascript
{
  type: "Invoice",
  credit_origin: "INV-2024-001",
  total_credit: 50000,
  credit_to_redeem: 30000
}
```

### **2. Advance Credit (Credit từ thanh toán trước)**
```javascript
{
  type: "Advance",
  credit_origin: "PAY-2024-001",
  total_credit: 100000,
  credit_to_redeem: 50000
}
```

### **3. M-Pesa Credit (Credit từ M-Pesa)**
```javascript
{
  type: "Advance",
  credit_origin: "MPESA-001",
  total_credit: 25000,
  credit_to_redeem: 25000
}
```

## 🎨 Giao Diện Người Dùng

### **1. Switch Kích Hoạt**
```vue
<v-switch
  v-model="redeem_customer_credit"
  label="Use Customer Credit"
  @update:model-value="get_available_credit(redeem_customer_credit)"
/>
```

### **2. Hiển Thị Credit Khả Dụng**
```vue
<v-text-field
  label="You can redeem credit up to"
  :model-value="formatCurrency(available_customer_credit)"
  readonly
/>
```

### **3. Input Số Tiền Redeem**
```vue
<v-text-field
  label="Redeemed Customer Credit"
  :model-value="formatCurrency(redeemed_customer_credit)"
  readonly
/>
```

### **4. Chi Tiết Credit Entries**
```vue
<v-row v-for="(row, idx) in customer_credit_dict">
  <v-col cols="4">{{ row.credit_origin }}</v-col>
  <v-col cols="4">
    <v-text-field
      label="Available Credit"
      :model-value="formatCurrency(row.total_credit)"
      readonly
    />
  </v-col>
  <v-col cols="4">
    <v-text-field
      label="Redeem Credit"
      :model-value="formatCurrency(row.credit_to_redeem)"
      @change="setFormatedCurrency(row, 'credit_to_redeem')"
    />
  </v-col>
</v-row>
```

## 🔄 Backend Processing

### **1. API: get_available_credit**
```python
@frappe.whitelist()
def get_available_credit(customer, company):
    """Lấy danh sách credit khả dụng của customer"""

    # Lấy outstanding invoices
    outstanding_invoices = frappe.get_all("Sales Invoice",
        filters={
            "customer": customer,
            "company": company,
            "docstatus": 1,
            "outstanding_amount": (">", 0)
        },
        fields=["name", "outstanding_amount", "posting_date"]
    )

    # Lấy advance payments
    advance_payments = frappe.get_all("Payment Entry",
        filters={
            "party_type": "Customer",
            "party": customer,
            "company": company,
            "docstatus": 1,
            "unallocated_amount": (">", 0)
        },
        fields=["name", "unallocated_amount", "posting_date"]
    )

    # Combine và return
    credit_entries = []

    # Invoice credits
    for inv in outstanding_invoices:
        credit_entries.append({
            "type": "Invoice",
            "credit_origin": inv.name,
            "total_credit": inv.outstanding_amount,
            "credit_to_redeem": 0
        })

    # Advance credits
    for pay in advance_payments:
        credit_entries.append({
            "type": "Advance",
            "credit_origin": pay.name,
            "total_credit": pay.unallocated_amount,
            "credit_to_redeem": 0
        })

    return credit_entries
```

### **2. Xử Lý Redeem Credit**
```python
@frappe.whitelist()
def submit_invoice(invoice, data):
    data = json.loads(data)
    invoice = json.loads(invoice)

    # Xử lý redeemed customer credit
    if data.get("redeemed_customer_credit"):
        # Tạo journal entry để ghi nhận việc sử dụng credit
        redeeming_customer_credit(invoice_doc, data, is_payment_entry, total_cash, cash_account, payments)

    # Submit invoice như bình thường
    invoice_doc.submit()
```

### **3. Function redeeming_customer_credit**
```python
def redeeming_customer_credit(invoice_doc, data, is_payment_entry, total_cash, cash_account, payments):
    """Xử lý việc redeem customer credit"""

    if data.get("redeemed_customer_credit"):
        # Tạo journal voucher để ghi nhận
        cost_center = frappe.get_value("POS Profile", invoice_doc.pos_profile, "cost_center")

        for row in data.get("customer_credit_dict"):
            if row["type"] == "Invoice" and row["credit_to_redeem"]:
                # Xử lý invoice credit
                create_journal_for_invoice_credit(invoice_doc, row, cost_center)

            elif row["type"] == "Advance" and row["credit_to_redeem"]:
                # Xử lý advance credit
                create_journal_for_advance_credit(invoice_doc, row, cost_center)
```

## 📊 Validation & Business Rules

### **1. Validation Rules**
```javascript
// Validate redeemed credit không vượt quá available credit
if (newVal > this.available_customer_credit) {
  this.redeemed_customer_credit = this.available_customer_credit;
  this.eventBus.emit("show_message", {
    title: `You can redeem customer credit up to ${this.available_customer_credit}`,
    color: "error"
  });
}

// Validate không redeem quá tổng tiền invoice
if (this.redeemed_customer_credit > (this.invoice_doc.rounded_total || this.invoice_doc.grand_total)) {
  this.eventBus.emit("show_message", {
    title: `Cannot redeem customer credit more than invoice total`,
    color: "error"
  });
}
```

### **2. Business Rules**
- ✅ Credit chỉ có thể sử dụng cho cùng customer
- ✅ Credit phải còn hạn sử dụng
- ✅ Không thể redeem credit cho return invoices
- ✅ Credit được ưu tiên từ invoice cũ nhất
- ✅ Tự động allocate credit khi bật switch

## 🔄 Auto-Allocation Logic

### **1. Thuật Toán Allocate**
```javascript
allocate_credit_automatically() {
  const invoiceAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
  let remainAmount = invoiceAmount;

  // Sort by posting date (oldest first)
  this.customer_credit_dict.sort((a, b) =>
    new Date(a.posting_date) - new Date(b.posting_date)
  );

  // Allocate from oldest to newest
  this.customer_credit_dict.forEach((row) => {
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

### **2. Multi-Currency Support**
```javascript
// Handle currency conversion
if (this.invoice_doc.currency !== this.pos_profile.currency) {
  // Convert credit amount to invoice currency
  const convertedCredit = this.redeemed_customer_credit / (this.invoice_doc.conversion_rate || 1);
  total += this.flt(convertedCredit, this.currency_precision);
} else {
  total += parseFloat(this.redeemed_customer_credit) || 0;
}
```

## 🎯 Ưu & Nhược Điểm

### **✅ Ưu Điểm**

1. **Tăng Doanh Số**: Khuyến khích khách hàng mua nhiều hơn
2. **Cải Thiện Cash Flow**: Thu tiền trước, giao hàng sau
3. **Xây Dựng Loyalty**: Tạo mối quan hệ lâu dài với khách hàng
4. **Tự Động Hóa**: Auto-allocate credit, giảm công việc thủ công
5. **Flexible**: Hỗ trợ multiple credit types và currencies

### **⚠️ Nhược Điểm**

1. **Rủi Ro Bad Debt**: Khách hàng có thể không thanh toán
2. **Phức Tạp Accounting**: Cần theo dõi credit balances
3. **Credit Control**: Cần policy rõ ràng về credit limits
4. **Performance**: Query phức tạp khi có nhiều credit entries

### **🔧 Khuyến Nghị**

1. **Set Credit Limits**: Xác định hạn mức credit cho từng customer
2. **Regular Monitoring**: Theo dõi credit utilization định kỳ
3. **Clear Policies**: Có chính sách credit rõ ràng
4. **Training**: Đào tạo nhân viên về cách sử dụng tính năng

## 🚀 Best Practices

### **1. Credit Policy Setup**
```javascript
// Recommended credit limits
const creditPolicies = {
  "New Customer": { limit: 50000, terms: "Net 15" },
  "Regular Customer": { limit: 100000, terms: "Net 30" },
  "VIP Customer": { limit: 500000, terms: "Net 60" }
};
```

### **2. Auto-Allocation Strategy**
```javascript
// Prioritize credit types
const creditPriority = [
  "Invoice",  // Oldest invoices first
  "Advance",  // Advance payments
  "M-Pesa"    // Mobile money
];
```

### **3. Monitoring Dashboard**
```sql
-- Credit utilization report
SELECT
  customer,
  credit_limit,
  SUM(outstanding_amount) as used_credit,
  (SUM(outstanding_amount) / credit_limit * 100) as utilization_percent
FROM `tabCustomer` c
LEFT JOIN `tabSales Invoice` si ON c.name = si.customer
WHERE si.outstanding_amount > 0
GROUP BY customer, credit_limit
ORDER BY utilization_percent DESC;
```

## 🔧 Troubleshooting

### **Vấn Đề Thường Gặp**

#### **1. Credit Không Hiển Thị**
```javascript
// Debug steps
console.log("Customer:", this.invoice_doc.customer);
console.log("POS Profile:", this.pos_profile.use_customer_credit);
console.log("Available Credit:", this.available_customer_credit);
```

#### **2. Redeem Credit Failed**
```javascript
// Check validation
if (this.redeemed_customer_credit > this.available_customer_credit) {
  console.error("Redeemed amount exceeds available credit");
}
```

#### **3. Journal Entry Errors**
```python
# Check cost center
cost_center = frappe.get_value("POS Profile", invoice_doc.pos_profile, "cost_center")
if not cost_center:
  frappe.throw(_("Cost Center is not set in POS Profile"))
```

## 🎉 Kết Luận

**"Use Customer Credit"** là một tính năng mạnh mẽ giúp:

- ✅ **Tối ưu hóa cash flow** của doanh nghiệp
- ✅ **Tăng customer satisfaction** và loyalty
- ✅ **Tự động hóa quy trình** thanh toán
- ✅ **Hỗ trợ multiple credit types** linh hoạt

### **Khuyến Nghị Triển Khai:**

1. **Bắt Đầu Nhỏ**: Test với một số customers đáng tin cậy
2. **Set Clear Policies**: Xác định credit limits và terms rõ ràng
3. **Monitor Regularly**: Theo dõi credit utilization và aging
4. **Train Staff**: Đào tạo nhân viên sử dụng tính năng hiệu quả

### **Next Steps:**
- [ ] Cấu hình POS Profile với `use_customer_credit = true`
- [ ] Test với customer có outstanding invoices
- [ ] Monitor credit utilization
- [ ] Adjust credit policies based on performance

---

**Tính năng này khi được sử dụng đúng cách sẽ mang lại giá trị kinh doanh đáng kể! 🚀**