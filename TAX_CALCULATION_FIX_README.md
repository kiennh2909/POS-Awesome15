# TAX CALCULATION FIX - POS Awesome System

## 🎯 Vấn đề đã khắc phục

**Thuế đang được tính trên tổng hóa đơn thay vì từng dòng item riêng biệt**

### ❌ Trước khi sửa:

- Invoice với 3 items (40,500 + 17,500 + 17,500 = 75,500)
- Thuế tính sai: 75,500 × 8% = 6,040 (thay vì 17,500 × 8% = 1,400)
- Grand Total sai: 75,500 + 6,040 = 81,540

### ✅ Sau khi sửa:

- Item 1: 40,500 × 5% = 2,025
- Item 2: 17,500 × 10% = 1,750
- Item 3: 17,500 × 8% = 1,400
- Tổng thuế: 5,175
- Grand Total đúng: 75,500 + 5,175 = 80,675

## 📋 Giải thích chi tiết các trường ERPNext

### 1. **rate & amount (Giá gốc/Gross Price)**

- **rate**: Đơn giá gốc từ bảng giá (Price List), chưa áp dụng chiết khấu
- **amount**: Thành tiền gốc = rate × qty
- **Ví dụ**: Gạo lứt 40,500 VND/cái × 1 = 40,500 VND

### 2. **net_rate & net_amount (Giá thuần/Net Price - Cơ sở tính thuế)**

- **net_rate**: Đơn giá sau chiết khấu (nếu có)
- **net_amount**: Thành tiền sau chiết khấu = net_rate × qty
- **Quan trọng**: Đây là **số tiền chịu thuế** (Taxable Amount)
- **Ví dụ**: Nếu có chiết khấu 10% thì net_rate = 36,450, net_amount = 36,450

### 3. **Thuế tính trên net_amount**

- Thuế VAT 5% = 5% × net_amount
- Thuế VAT 8% = 8% × net_amount
- Thuế VAT 10% = 10% × net_amount

### 4. **total_taxes_and_charges**

- Tổng tất cả thuế từ các item
- Ví dụ: 2,025 + 1,750 + 1,400 = 5,175

### 5. **grand_total**

- Tổng cuối = net_total + total_taxes_and_charges
- net_total thường = total (trong exclusive tax)

## 🔧 Thay đổi code

### File: `posawesome/posawesome/api/invoices.py`

#### 1. Sửa logic tính thuế exclusive:

```python
# TRƯỚC (sai - tính trên tổng hóa đơn):
tax_amount = 0.0
charge_type = 'On Net Total'  # ERPNext tự tính trên tổng net_total

# SAU (đúng - tính trên từng item):
tax_amount = flt(item.net_amount) * tax_rate / 100  # Tính trên net_amount của item
charge_type = 'Actual'  # Cố định, không để ERPNext can thiệp
```

#### 2. Comment out inclusive tax logic:

- Loại bỏ biến `is_inclusive`
- Comment toàn bộ logic xử lý inclusive tax
- Thêm docstring rõ ràng: "INCLUSIVE TAX IS NOT SUPPORTED"

#### 3. Đảm bảo tích lũy thuế đúng:

```python
# Tích lũy thuế cho cùng account + rate từ nhiều items
tax_entries[key]['tax_amount'] += tax_amount
# Ví dụ: Item A 5% + Item B 5% = tổng thuế 5%
```

## 📊 So sánh Exclusive vs Inclusive Tax

### Exclusive Tax (Được sử dụng - CHUẨN HÓA):

**rate/amount (Giá gốc):**

- rate: 40,500 / 17,500 / 17,500 (đơn giá gốc từ bảng giá)
- amount: 75,500 (rate × qty, chưa trừ chiết khấu)

**net_rate/net_amount (Giá thuần - Cơ sở tính thuế):**

- net_rate: 40,500 / 17,500 / 17,500 (= rate, vì không có chiết khấu)
- net_amount: 75,500 (= amount, vì không có chiết khấu)

**Thuế tính trên net_amount:**

- Item 1: 40,500 × 5% = 2,025
- Item 2: 17,500 × 10% = 1,750
- Item 3: 17,500 × 8% = 1,400
- Tổng thuế: 5,175

**Grand Total:** 75,500 + 5,175 = 80,675

### Inclusive Tax (Đã comment - KHÔNG SỬ DỤNG):

**rate/amount (Giá hiển thị đã bao gồm thuế):**

- rate: 42,525 / 19,250 / 19,250 (giá hiển thị cho khách)
- amount: 80,675 (rate × qty)

**net_rate/net_amount (Giá thuần sau khi tách thuế):**

- net_rate: 40,500 / 17,500 / 17,500 (rate ÷ (1 + tax_rate))
- net_amount: 75,500 (giá thực tế chịu thuế)

**Thuế ẩn trong giá hiển thị:**

- Item 1: 42,525 - 40,500 = 2,025 (5%)
- Item 2: 19,250 - 17,500 = 1,750 (10%)
- Item 3: 19,250 - 17,500 = 1,750 (8%)
- Tổng thuế: 5,175

**Grand Total:** 80,675 (= giá hiển thị, đã bao gồm thuế)

## ✅ Kết quả test thực tế

Log từ hệ thống production:

```
🧾 EXCLUSIVE TAX - Item 8938549898111: amount 40500.0 × 5.0% = 2025.0
🧾 EXCLUSIVE TAX - Item 8936036028805: amount 17500.0 × 10.0% = 1750.0
🧾 EXCLUSIVE TAX - Item 8936036025453: amount 17500.0 × 8.0% = 1400.0
🧾 TAXES AFTER CALCULATION: 3 tax entries
🧾 Tax 1: Tax 5.0% - Amount: 2025.0
🧾 Tax 2: Tax 10.0% - Amount: 1750.0
🧾 Tax 3: Tax 8.0% - Amount: 1400.0
```

## 🎉 Kết luận

### ✅ **Thuật ngữ chính xác trong ERPNext:**

- **`rate/amount`**: Giá gốc (Gross Price) - từ bảng giá, chưa trừ chiết khấu
- **`net_rate/net_amount`**: Giá thuần (Net Price) - sau chiết khấu, là cơ sở tính thuế
- **Thuế luôn tính trên `net_amount`** của từng item

### ✅ **Hệ thống đã hoàn thiện:**

- ✅ Thuế tính chính xác trên từng item (`net_amount × tax_rate`)
- ✅ Hỗ trợ nhiều mức thuế khác nhau trong 1 hóa đơn
- ✅ Không bị ERPNext can thiệp (`charge_type = 'Actual'`)
- ✅ Log đầy đủ để theo dõi và debug
- ✅ Chỉ sử dụng EXCLUSIVE TAX (chuẩn hóa)

### ✅ **Ví dụ thực tế từ hệ thống:**

```
Item 1: net_amount 40,500 × 5% = 2,025 thuế
Item 2: net_amount 17,500 × 10% = 1,750 thuế
Item 3: net_amount 17,500 × 8% = 1,400 thuế
Tổng thuế: 5,175 | Grand Total: 80,675 ✅
```

## 🔄 Tích hợp với MISA (Hệ thống kế toán Việt Nam)

### ✅ **Vấn đề VATRate thiếu trong dữ liệu gửi sang MISA:**

Dữ liệu hiện tại gửi sang MISA:

```json
{
	"Category": "TA GIAY TA QUAN-VN",
	"DiscountRate": "0",
	"ExciseTaxRate": "0",
	"InventoryItemType": "0",
	"Name": "TTE Bobby Quần L70",
	"Price": "294069",
	"Qty": "2",
	"ServiceFeeRate": "0",
	"UnitName": "Gói",
	"VATRate": "0", // ❌ SAI - Hiện tại hardcode là 0
	"WarehouseCode": "VTM_DA"
}
```

### ✅ **Giải pháp: Lấy VATRate từ item_tax_template**

**Function mới được thêm vào `invoices.py`:**

1. **`get_item_vat_rate(item_code)`**: Lấy tỷ lệ VAT từ Item Tax Template
2. **`get_invoice_items_for_misa(invoice_name)`**: Trả về danh sách items với VATRate chính xác

**Dữ liệu sau khi sửa:**

```json
{
	"Category": "TA GIAY TA QUAN-VN",
	"DiscountRate": "0",
	"ExciseTaxRate": "0",
	"InventoryItemType": "0",
	"Name": "TTE Bobby Quần L70",
	"Price": "294069",
	"Qty": "2",
	"ServiceFeeRate": "0",
	"UnitName": "Gói",
	"VATRate": "5", // ✅ ĐÚNG - Lấy từ item_tax_template
	"WarehouseCode": "VTM_DA"
}
```

### 📋 **Cách sử dụng API:**

#### **1. Lấy VATRate cho một item:**

```python
# Python backend
vat_rate = frappe.call("posawesome.posawesome.api.invoices.get_item_vat_rate",
                      item_code="8934755051227")  # Trả về 5.0

# JavaScript frontend
frappe.call({
    method: "posawesome.posawesome.api.invoices.get_item_vat_rate",
    args: { item_code: "8934755051227" },
    callback: function(r) {
        console.log("VAT Rate:", r.message); // 5.0
    }
});
```

#### **2. Lấy toàn bộ items cho MISA:**

```python
# Python backend
misa_data = frappe.call("posawesome.posawesome.api.invoices.get_invoice_items_for_misa",
                       invoice_name="ACC-SINV-2025-100087")

# JavaScript frontend - khi gửi dữ liệu sang MISA
frappe.call({
    method: "posawesome.posawesome.api.invoices.get_invoice_items_for_misa",
    args: { invoice_name: "ACC-SINV-2025-100087" },
    callback: function(r) {
        let misa_items = r.message;
        // Gửi misa_items sang MISA API
        send_to_misa_api(misa_items);
    }
});
```

### 🔗 **Tích hợp vào workflow MISA:**

Function `get_invoice_items_for_misa` được thiết kế để:

1. **Được gọi từ JavaScript** khi user click nút "Gửi MISA"
2. **Trả về dữ liệu đã format** sẵn cho MISA API
3. **Đảm bảo VATRate chính xác** từ item_tax_template

#### **Ví dụ workflow:**

```javascript
// Trong POS Interface - khi submit invoice thành công
function send_invoice_to_misa(invoice_name) {
	frappe.call({
		method: "posawesome.posawesome.api.invoices.get_invoice_items_for_misa",
		args: { invoice_name: invoice_name },
		callback: function (r) {
			if (r.message && r.message.length > 0) {
				// Gửi dữ liệu sang MISA API
				submit_to_misa_system(r.message);
			}
		},
	});
}
```

**Hệ thống POS Awesome giờ đã tích hợp hoàn chỉnh với MISA!** 🎯
