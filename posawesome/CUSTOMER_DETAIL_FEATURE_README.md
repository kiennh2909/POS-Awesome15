# 🎯 Hướng Dẫn: Tính Năng Hiển Thị Thông Tin Chi Tiết Khách Hàng

## 📋 Tổng Quan

Tính năng **Customer Detail** cho phép xem toàn bộ thông tin chi tiết về khách hàng khi chọn từ dropdown trong POS. Đây là công cụ quan trọng giúp nhân viên POS hiểu rõ hơn về khách hàng và đưa ra quyết định bán hàng phù hợp.

## 🚀 Cách Sử Dụng

### 1. Truy Cập Tính Năng
```
1. Mở POS Application
2. Nhấn vào dropdown Customer
3. Tìm và chọn khách hàng
4. Nhấn nút 👁️ (View Details) bên cạnh tên khách hàng
```

### 2. Giao Diện Hiển Thị

#### **Dropdown với nút View Details:**
```
┌─────────────────────────────────────────────────┐
│ Customer Name                      👁️ [View]   │
│ ID: CUST-001                                    │
│ TAX ID: 123456789                               │
│ Email: customer@email.com                       │
│ Mobile: +84 123 456 789                         │
└─────────────────────────────────────────────────┘
```

#### **Dialog Chi Tiết Customer:**
```
┌─ Customer Details ──────────────────────────────┐
│                                                │
│ 1️⃣ BASIC INFORMATION                          │
│ ┌─────────────────────────────────────────┐    │
│ │ Customer ID: CUST-DEMO-001             │    │
│ │ Customer Name: Nguyễn Văn Demo         │    │
│ │ Mobile No: 0123456789                  │    │
│ │ Email: demo@email.com                  │    │
│ │ Tax ID: 123456789                      │    │
│ │ City: Hồ Chí Minh                      │    │
│ └─────────────────────────────────────────┘    │
│                                                │
│ 2️⃣ CLASSIFICATION                             │
│ ┌─────────────────────────────────────────┐    │
│ │ Customer Type: Individual              │    │
│ │ Customer Group: Khách lẻ POS           │    │
│ │ Territory: Đài Loan                    │    │
│ │ Gender: Male                           │    │
│ └─────────────────────────────────────────┘    │
│                                                │
│ 3️⃣ CREDIT INFORMATION                        │
│ ┌─────────────────────────────────────────┐    │
│ │ Credit Limit: 200,000 VND              │    │
│ │ Outstanding Amount: 95,000 VND         │    │
│ │ Credit Balance: 105,000 VND            │    │
│ │ Payment Terms: Net 30                  │    │
│ └─────────────────────────────────────────┘    │
│                                                │
│ 4️⃣ LOYALTY POINTS                            │
│ ┌─────────────────────────────────────────┐    │
│ │ Loyalty Program: Standard Program      │    │
│ │ Total Points: 1,250                    │    │
│ │ Points Used: 300                       │    │
│ │ Points Balance: 950                    │    │
│ └─────────────────────────────────────────┘    │
│                                                │
│ 5️⃣ DEBT INFORMATION                          │
│ ┌─────────────────────────────────────────┐    │
│ │ Total Debt Generated: 350,000 VND      │    │
│ │ Total Paid: 255,000 VND                │    │
│ │ Remaining Debt: 95,000 VND             │    │
│ └─────────────────────────────────────────┘    │
│                                                │
│ 6️⃣ CUSTOMER STATISTICS                      │
│ ┌─────────────────────────────────────────┐    │
│ │ Total Orders: 15                        │    │
│ │ Total GMV: 2,450,000 VND               │    │
│ │ Paid Orders: 12                         │    │
│ │ Return Orders: 1                        │    │
│ │ Avg Order Value: 163,333 VND           │    │
│ │ Last Order Date: 2024-01-15            │    │
│ └─────────────────────────────────────────┘    │
│                                                │
│                    [Close]                     │
└────────────────────────────────────────────────┘
```

## 📁 Files Implementation

| File | Mục Đích | Chi Tiết |
|------|-----------|----------|
| `posawesome/posawesome/api/customers.py` | API Backend | `get_customer_detailed_info()` |
| `posawesome/public/js/posapp/components/pos/CustomerDetail.vue` | UI Component | Dialog hiển thị chi tiết |
| `posawesome/public/js/posapp/components/pos/Customer.vue` | Integration | Tích hợp nút View Details |

## 🔧 API Backend: get_customer_detailed_info

### **Cấu Trúc Response:**
```json
{
  "basic_info": {
    "customer_id": "CUST-001",
    "customer_name": "Nguyễn Văn Demo",
    "mobile_no": "0123456789",
    "email_id": "demo@email.com",
    "tax_id": "123456789",
    "city": "Hồ Chí Minh",
    "territory": "Đài Loan",
    "customer_group": "Khách lẻ POS",
    "customer_type": "Individual",
    "gender": "Male",
    "birthday": "1990-01-01"
  },
  "classification_info": {
    "customer_type": "Individual",
    "customer_group": "Khách lẻ POS",
    "territory": "Đài Loan",
    "gender": "Male"
  },
  "credit_info": {
    "credit_limit": 200000,
    "outstanding_amount": 95000,
    "credit_balance": 105000,
    "payment_terms": "Net 30"
  },
  "loyalty_info": {
    "loyalty_program": "Standard Program",
    "loyalty_points": 1250,
    "loyalty_points_used": 300,
    "loyalty_points_balance": 950,
    "conversion_factor": 1.0
  },
  "debt_info": {
    "total_debt_generated": 350000,
    "total_paid": 255000,
    "remaining_debt": 95000
  },
  "statistics_info": {
    "total_orders": 15,
    "total_gmv": 2450000,
    "total_paid_orders": 12,
    "total_return_orders": 1,
    "avg_order_value": 163333,
    "last_order_date": "2024-01-15"
  },
  "last_updated": "2024-01-15 10:30:00"
}
```

### **Queries Sử Dụng:**

#### **1. Thông Tin Cơ Bản:**
```sql
SELECT name, customer_name, mobile_no, email_id, tax_id
FROM `tabCustomer`
WHERE name = %s
```

#### **2. Địa Chỉ:**
```sql
SELECT city, state, country
FROM `tabAddress` address
INNER JOIN `tabDynamic Link` link ON address.name = link.parent
WHERE link.link_doctype = 'Customer'
AND link.link_name = %s
AND address.is_primary_address = 1
```

#### **3. Credit Information:**
```sql
SELECT SUM(outstanding_amount) as total_outstanding
FROM `tabSales Invoice`
WHERE customer = %s
AND docstatus = 1
AND outstanding_amount > 0
```

#### **4. Loyalty Points:**
```sql
-- Total points
SELECT loyalty_points
FROM `tabLoyalty Point Entry`
WHERE customer = %s
AND loyalty_points > 0

-- Used points
SELECT SUM(loyalty_points) as used
FROM `tabLoyalty Point Entry`
WHERE customer = %s
AND loyalty_points < 0
```

#### **5. Debt Information:**
```sql
-- Total generated
SELECT SUM(grand_total) as total_generated
FROM `tabSales Invoice`
WHERE customer = %s
AND docstatus = 1

-- Total paid
SELECT SUM(paid_amount) as total_paid
FROM `tabPayment Entry`
WHERE party_type = 'Customer'
AND party = %s
AND docstatus = 1
AND payment_type = 'Receive'
```

#### **6. Statistics:**
```sql
SELECT
    COUNT(*) as total_orders,
    SUM(grand_total) as total_gmv,
    SUM(CASE WHEN outstanding_amount = 0 THEN 1 ELSE 0 END) as paid_orders,
    SUM(CASE WHEN is_return = 1 THEN 1 ELSE 0 END) as return_orders,
    AVG(grand_total) as avg_order_value,
    MAX(posting_date) as last_order_date
FROM `tabSales Invoice`
WHERE customer = %s
AND docstatus = 1
```

## 🎨 UI Components

### **1. Customer.vue - Dropdown Integration**
```vue
<!-- Nút View Details trong dropdown -->
<template #item="{ props, item }">
  <v-list-item v-bind="props">
    <template #append>
      <v-btn
        icon
        size="small"
        variant="text"
        @click.stop="viewCustomerDetails(item.raw.name)"
      >
        <v-icon size="16">mdi-eye</v-icon>
      </v-btn>
    </template>
    <!-- Customer info display -->
  </v-list-item>
</template>
```

### **2. CustomerDetail.vue - Main Dialog**
```vue
<v-card>
  <v-card-title class="primary white--text">
    <span class="text-h5">{{ __("Customer Details") }}</span>
  </v-card-title>

  <v-card-text>
    <!-- 6 sections hiển thị thông tin -->
  </v-card-text>
</v-card>
```

## 📊 Business Value

### **1. Credit Management:**
- ✅ Xem credit limit và outstanding amount
- ✅ Đánh giá rủi ro tín dụng
- ✅ Quyết định bán hàng phù hợp

### **2. Customer Insights:**
- ✅ Hiểu hành vi mua hàng
- ✅ Xem loyalty points
- ✅ Tùy chỉnh dịch vụ

### **3. Sales Optimization:**
- ✅ Cross-selling opportunities
- ✅ Up-selling dựa trên lịch sử
- ✅ Personalized recommendations

### **4. Risk Assessment:**
- ✅ Outstanding amount monitoring
- ✅ Payment pattern analysis
- ✅ Credit utilization tracking

## 🔧 Customization

### **Thêm Fields Mới:**
```python
# Trong get_customer_detailed_info()
additional_info = {
    "custom_field_1": customer_doc.custom_field_1,
    "custom_field_2": customer_doc.custom_field_2,
    # ...
}
result["additional_info"] = additional_info
```

### **Tùy Chỉnh UI:**
```vue
<!-- Thêm section mới trong CustomerDetail.vue -->
<v-col cols="12" md="6">
  <v-card class="mb-4">
    <v-card-title class="teal white--text">
      <v-icon left>mdi-plus</v-icon>
      {{ __("Additional Information") }}
    </v-card-title>
    <!-- Custom content -->
  </v-card>
</v-col>
```

## 🚨 Troubleshooting

### **Vấn Đề Thường Gặp:**

#### **1. API Không Trả Về Data:**
```javascript
// Check console for errors
console.log("Customer ID:", this.customerId);
console.log("API Response:", response);

// Verify customer exists
frappe.db.exists("Customer", customerId)
```

#### **2. Dialog Không Mở:**
```javascript
// Check component props
console.log("CustomerDetail props:", {
  modelValue: this.dialog,
  customerId: this.customerId
});
```

#### **3. Data Không Hiển Thị:**
```javascript
// Check data structure
console.log("Customer Data:", this.customerData);
console.log("Basic Info:", this.customerData?.basic_info);
```

## 📈 Performance Optimization

### **1. Caching Strategy:**
```python
@redis_cache(ttl=300)  # Cache 5 minutes
def get_customer_detailed_info(customer):
    # Heavy calculations here
    pass
```

### **2. Lazy Loading:**
```javascript
// Load sections on demand
async loadCreditInfo() {
  if (!this.creditLoaded) {
    // Load credit data
    this.creditLoaded = true;
  }
}
```

### **3. Data Pagination:**
```python
# For large datasets
def get_customer_orders_paginated(customer, page=1, page_size=50):
    start = (page - 1) * page_size
    return frappe.get_all("Sales Invoice",
        filters={"customer": customer},
        fields=["name", "grand_total", "posting_date"],
        limit_start=start,
        limit_page_length=page_size
    )
```

## 🎯 Best Practices

### **1. User Experience:**
- ✅ Load data asynchronously
- ✅ Show loading states
- ✅ Handle error gracefully
- ✅ Responsive design

### **2. Data Security:**
- ✅ Check user permissions
- ✅ Sanitize sensitive data
- ✅ Log access for audit

### **3. Performance:**
- ✅ Cache frequently accessed data
- ✅ Optimize database queries
- ✅ Use pagination for large datasets

## 📋 Implementation Checklist

- [x] ✅ Tạo API `get_customer_detailed_info`
- [x] ✅ Tạo component `CustomerDetail.vue`
- [x] ✅ Tích hợp nút View Details vào dropdown
- [x] ✅ Test với data mẫu
- [x] ✅ Handle error cases
- [x] ✅ Responsive design
- [x] ✅ Performance optimization

## 🎉 Kết Luận

Tính năng **Customer Detail** cung cấp:

- 📊 **360° Customer View** - Toàn bộ thông tin khách hàng
- 💰 **Credit Intelligence** - Thông tin tín dụng chi tiết
- 🎯 **Sales Insights** - Dữ liệu để tối ưu bán hàng
- 📈 **Business Analytics** - Thống kê và xu hướng
- 🔒 **Risk Management** - Đánh giá rủi ro tín dụng

---

**🚀 Tính năng này giúp POS trở thành công cụ bán hàng thông minh và hiệu quả!**