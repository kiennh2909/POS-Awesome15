# 📡 TÀI LIỆU API ENDPOINTS - POS AWESOME

**Phiên bản:** 1.0  
**Ngày:** 7 tháng 12, 2025

---

## 📋 TỔNG QUAN

Tài liệu này mô tả tất cả các API endpoints được expose trong hệ thống POS Awesome thông qua decorator `@frappe.whitelist()`.

**Tổng số endpoints:** 40+

---

## 🛒 INVOICE MANAGEMENT APIs

### Module: `posawesome.posawesome.api.invoices`

#### 1. `validate_return_items`
```python
@frappe.whitelist()
def validate_return_items(original_invoice_name, return_items)
```
**Mục đích:** Validate các items được return từ invoice gốc  
**Parameters:**
- `original_invoice_name` (str): Tên invoice gốc
- `return_items` (list): Danh sách items cần return

**Returns:** Validation result

---

#### 2. `update_invoice`
```python
@frappe.whitelist()
def update_invoice(data)
```
**Mục đích:** Cập nhật invoice với data mới  
**Parameters:**
- `data` (json): Invoice data cần update

**Returns:** Updated invoice document

---

#### 3. `submit_invoice` (2 versions)
```python
@frappe.whitelist()
def submit_invoice(invoice, data)
```
**Mục đích:** Submit invoice và xử lý payment  
**Parameters:**
- `invoice` (str): Invoice name
- `data` (json): Invoice data với payments

**Returns:** Submitted invoice result

**Workflow:**
1. Validate invoice data
2. Calculate taxes
3. Process payments
4. Submit document
5. Update shift report
6. Enqueue background jobs (nếu enabled)

---

#### 4. `delete_invoice`
```python
@frappe.whitelist()
def delete_invoice(invoice)
```
**Mục đích:** Xóa invoice (draft hoặc cancelled)  
**Parameters:**
- `invoice` (str): Invoice name

**Returns:** Success message

**Security:** Kiểm tra `posa_allow_delete` trong POS Profile

---

#### 5. `get_draft_invoices`
```python
@frappe.whitelist()
def get_draft_invoices(pos_opening_shift)
```
**Mục đích:** Lấy danh sách draft invoices của shift  
**Parameters:**
- `pos_opening_shift` (str): Opening shift name

**Returns:** List of draft invoices

---

#### 6. `search_invoices_for_return`
```python
@frappe.whitelist()
def search_invoices_for_return(invoice_name, customer, company, ...)
```
**Mục đích:** Tìm kiếm invoices để tạo return  
**Parameters:**
- `invoice_name` (str): Invoice name to search
- `customer` (str): Customer name
- `company` (str): Company name
- Additional filters

**Returns:** List of matching invoices

---

#### 7. `create_sales_invoice_from_order`
```python
@frappe.whitelist()
def create_sales_invoice_from_order(sales_order)
```
**Mục đích:** Tạo Sales Invoice từ Sales Order  
**Parameters:**
- `sales_order` (str): Sales Order name

**Returns:** New Sales Invoice document

---

#### 8. `delete_sales_invoice`
```python
@frappe.whitelist()
def delete_sales_invoice(sales_invoice)
```
**Mục đích:** Xóa Sales Invoice  
**Parameters:**
- `sales_invoice` (str): Sales Invoice name

**Returns:** Success message

---

#### 9. `get_sales_invoice_child_table`
```python
@frappe.whitelist()
def get_sales_invoice_child_table(sales_invoice, sales_invoice_item)
```
**Mục đích:** Lấy child table item từ invoice  
**Parameters:**
- `sales_invoice` (str): Parent invoice name
- `sales_invoice_item` (str): Child item name

**Returns:** Child table item data

---

#### 10. `update_invoice_from_order`
```python
@frappe.whitelist()
def update_invoice_from_order(data)
```
**Mục đích:** Update invoice từ sales order data  
**Parameters:**
- `data` (json): Order data

**Returns:** Updated invoice

---

#### 11. `get_available_currencies`
```python
@frappe.whitelist()
def get_available_currencies()
```
**Mục đích:** Lấy danh sách currencies có sẵn  
**Parameters:** None

**Returns:** List of currency codes

---

#### 12. `fetch_exchange_rate`
```python
@frappe.whitelist()
def fetch_exchange_rate(currency: str, company: str, posting_date: str = None)
```
**Mục đích:** Lấy exchange rate cho currency  
**Parameters:**
- `currency` (str): Currency code
- `company` (str): Company name
- `posting_date` (str, optional): Date for rate

**Returns:** Exchange rate and date

---

#### 13. `fetch_exchange_rate_pair`
```python
@frappe.whitelist()
def fetch_exchange_rate_pair(from_currency: str, to_currency: str, posting_date: str = None)
```
**Mục đích:** Lấy exchange rate giữa 2 currencies  
**Parameters:**
- `from_currency` (str): Source currency
- `to_currency` (str): Target currency
- `posting_date` (str, optional): Date for rate

**Returns:** Exchange rate between currencies

---

#### 14. `get_price_list_currency`
```python
@frappe.whitelist()
def get_price_list_currency(price_list: str) -> str
```
**Mục đích:** Lấy currency của Price List  
**Parameters:**
- `price_list` (str): Price List name

**Returns:** Currency code

---

#### 15. `get_item_vat_rate`
```python
@frappe.whitelist()
def get_item_vat_rate(item_code: str) -> float
```
**Mục đích:** Lấy VAT rate cho item (MISA integration)  
**Parameters:**
- `item_code` (str): Item code

**Returns:** VAT rate (float)

**Logic:**
1. Check Item Tax Template
2. Extract VAT rate from template
3. Return rate or 0

---

#### 16. `get_invoice_items_for_misa`
```python
@frappe.whitelist()
def get_invoice_items_for_misa(invoice_name: str) -> list
```
**Mục đích:** Lấy invoice items formatted cho MISA API  
**Parameters:**
- `invoice_name` (str): Invoice name

**Returns:** List of items với VATRate

**Format:**
```json
{
  "Category": "CATEGORY-NAME",
  "DiscountRate": "0",
  "ExciseTaxRate": "0",
  "InventoryItemType": "0",
  "Name": "Item Name",
  "Price": "294069",
  "Qty": "2",
  "ServiceFeeRate": "0",
  "UnitName": "Unit",
  "VATRate": "5",
  "WarehouseCode": "WH-CODE"
}
```

---

## 👥 CUSTOMER MANAGEMENT APIs

### Module: `posawesome.posawesome.api.customers`

#### 17. `get_customer_names`
```python
@frappe.whitelist()
def get_customer_names(pos_profile)
```
**Mục đích:** Lấy danh sách customer names cho POS Profile  
**Parameters:**
- `pos_profile` (json): POS Profile data

**Returns:** List of customer names

---

#### 18. `get_customer_info`
```python
@frappe.whitelist()
def get_customer_info(customer)
```
**Mục đích:** Lấy thông tin chi tiết customer  
**Parameters:**
- `customer` (str): Customer name

**Returns:** Customer info object

**Includes:**
- Basic info (name, email, phone)
- Credit limit
- Outstanding amount
- Loyalty points
- Addresses
- Contacts

---

#### 19. `create_customer`
```python
@frappe.whitelist()
def create_customer(customer_name, tax_id, email, mobile, ...)
```
**Mục đích:** Tạo customer mới  
**Parameters:**
- `customer_name` (str): Customer name
- `tax_id` (str): Tax ID
- `email` (str): Email
- `mobile` (str): Mobile number
- Additional fields

**Returns:** New customer document

---

#### 20. `set_customer_info`
```python
@frappe.whitelist()
def set_customer_info(customer, fieldname, value="")
```
**Mục đích:** Update customer field  
**Parameters:**
- `customer` (str): Customer name
- `fieldname` (str): Field to update
- `value` (str): New value

**Returns:** Success message

---

#### 21. `get_customer_addresses`
```python
@frappe.whitelist()
def get_customer_addresses(customer)
```
**Mục đích:** Lấy danh sách addresses của customer  
**Parameters:**
- `customer` (str): Customer name

**Returns:** List of addresses

---

#### 22. `make_address`
```python
@frappe.whitelist()
def make_address(args)
```
**Mục đích:** Tạo address mới cho customer  
**Parameters:**
- `args` (json): Address data

**Returns:** New address document

---

#### 23. `get_sales_person_names`
```python
@frappe.whitelist()
def get_sales_person_names()
```
**Mục đích:** Lấy danh sách sales persons  
**Parameters:** None

**Returns:** List of sales person names

---

#### 24. `get_customer_detailed_info`
```python
@frappe.whitelist()
def get_customer_detailed_info(customer)
```
**Mục đích:** Lấy thông tin customer chi tiết (enhanced version)  
**Parameters:**
- `customer` (str): Customer name

**Returns:** Detailed customer info

---

### Module: `posawesome.posawesome.api.customer`

#### 25. `get_customer_balance`
```python
@frappe.whitelist()
def get_customer_balance(customer)
```
**Mục đích:** Lấy balance của customer  
**Parameters:**
- `customer` (str): Customer name

**Returns:** Balance amount

---

#### 26. `create_customer` (wrapper)
```python
@frappe.whitelist()
def create_customer(*args, **kwargs)
```
**Mục đích:** Backward compatible wrapper  
**Parameters:** Same as customers.create_customer

**Returns:** New customer document

---

## 📦 ITEM MANAGEMENT APIs

### Module: `posawesome.posawesome.api.items`

#### 27. `get_stock_unified`
```python
@frappe.whitelist()
def get_stock_unified(item_code, warehouse, source="bin")
```
**Mục đích:** Lấy stock quantity unified  
**Parameters:**
- `item_code` (str): Item code
- `warehouse` (str): Warehouse name
- `source` (str): "bin" or "ledger"

**Returns:** Stock quantity

---

#### 28. `get_items`
```python
@frappe.whitelist()
def get_items(pos_profile: str, price_list: str = None, ...)
```
**Mục đích:** Lấy danh sách items cho POS  
**Parameters:**
- `pos_profile` (str): POS Profile name
- `price_list` (str): Price List name
- `item_group` (str): Filter by group
- `search_term` (str): Search keyword
- `page_length` (int): Items per page
- `start` (int): Pagination start

**Returns:** List of items với prices, stock, images

**Features:**
- Pagination
- Search
- Filtering
- Price calculation
- Stock checking
- Image URLs
- UOM conversion

---

#### 29. `get_items_groups`
```python
@frappe.whitelist()
def get_items_groups()
```
**Mục đích:** Lấy danh sách item groups  
**Parameters:** None

**Returns:** List of item groups

---

#### 30. `get_items_details`
```python
@frappe.whitelist()
def get_items_details(pos_profile, items_data, price_list=None)
```
**Mục đích:** Lấy chi tiết cho multiple items  
**Parameters:**
- `pos_profile` (json): POS Profile data
- `items_data` (json): List of item codes
- `price_list` (str): Price List name

**Returns:** Detailed item info for each item

---

#### 31. `get_item_tax_info`
```python
@frappe.whitelist()
def get_item_tax_info(item_code, price_list=None, pos_profile=None)
```
**Mục đích:** Lấy tax info cho MISA API  
**Parameters:**
- `item_code` (str): Item code
- `price_list` (str): Price List name
- `pos_profile` (str): POS Profile name

**Returns:** Tax information

---

## 💰 DISCOUNT & OFFERS APIs

### Module: `posawesome.posawesome.api.discount_calculator`

#### 32. `calculate_discounts`
```python
@frappe.whitelist()
def calculate_discounts(invoice_data)
```
**Mục đích:** Calculate tất cả discounts và offers  
**Parameters:**
- `invoice_data` (json): Complete invoice state

**Returns:** Updated invoice với applied offers

**Process:**
1. Parse invoice data
2. Validate coupons
3. Reset item prices
4. Find applicable offers
5. Apply offers (Item Code, Item Group, Brand, Transaction)
6. Calculate totals
7. Return updated items

**Offer Types:**
- Item Code offers
- Item Group offers
- Brand offers
- Transaction offers
- Block-based discounts
- Time slot restrictions
- Coupon-based offers

---

## 🔄 SHIFT MANAGEMENT APIs

### Module: `posawesome.posawesome.api.shifts`

#### 33. `get_cashiers`
```python
@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters)
```
**Mục đích:** Lấy danh sách cashiers cho POS Profile  
**Parameters:** Standard Frappe query parameters

**Returns:** List of cashiers

---

#### 34. `get_pos_invoices`
```python
@frappe.whitelist()
def get_pos_invoices(pos_opening_shift, doctype=None)
```
**Mục đích:** Lấy invoices của shift  
**Parameters:**
- `pos_opening_shift` (str): Opening shift name
- `doctype` (str): Optional doctype filter

**Returns:** List of invoices

---

#### 35. `get_payments_entries`
```python
@frappe.whitelist()
def get_payments_entries(pos_opening_shift)
```
**Mục đích:** Lấy payment entries của shift  
**Parameters:**
- `pos_opening_shift` (str): Opening shift name

**Returns:** List of payment entries

---

#### 36. `make_closing_shift_from_opening`
```python
@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift)
```
**Mục đích:** Tạo closing shift từ opening shift  
**Parameters:**
- `opening_shift` (str): Opening shift name

**Returns:** New closing shift document

**Workflow:**
1. Get opening shift data
2. Calculate totals
3. Get invoices
4. Get payments
5. Create closing shift
6. Link to opening shift

---

#### 37. `submit_closing_shift_v2`
```python
@frappe.whitelist()
def submit_closing_shift_v2(closing_shift)
```
**Mục đích:** Submit closing shift (version 2)  
**Parameters:**
- `closing_shift` (json): Closing shift data

**Returns:** Submitted shift result

---

#### 38. `perform_user_logout`
```python
@frappe.whitelist()
def perform_user_logout(user)
```
**Mục đích:** Logout user sau khi đóng shift  
**Parameters:**
- `user` (str): User name

**Returns:** Success message

---

### Module: `posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift`

#### 39. `get_payment_reconciliation_details`
```python
@frappe.whitelist()
def get_payment_reconciliation_details(self)
```
**Mục đích:** Lấy chi tiết reconciliation  
**Parameters:** None (method on document)

**Returns:** Reconciliation details

---

## 📊 SHIFT REPORT APIs

### Module: `posawesome.posawesome.doctype.pos_shift_report.pos_shift_report`

#### 40. `create_shift_report_from_opening`
```python
@frappe.whitelist()
def create_shift_report_from_opening(opening_shift_name)
```
**Mục đích:** Tạo shift report từ opening shift  
**Parameters:**
- `opening_shift_name` (str): Opening shift name

**Returns:** New shift report document

---

### Module: `posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary`

#### 41. `update_payment_summary_on_invoice_submit`
```python
@frappe.whitelist()
def update_payment_summary_on_invoice_submit(invoice_name)
```
**Mục đích:** Update payment summary khi invoice submit  
**Parameters:**
- `invoice_name` (str): Invoice name

**Returns:** Success message

---

#### 42. `create_payment_summaries_for_shift`
```python
@frappe.whitelist()
def create_payment_summaries_for_shift(shift_report_name)
```
**Mục đích:** Tạo payment summaries cho shift  
**Parameters:**
- `shift_report_name` (str): Shift report name

**Returns:** Created summaries

---

#### 43. `get_payment_summaries_for_shift`
```python
@frappe.whitelist()
def get_payment_summaries_for_shift(shift_report_name)
```
**Mục đích:** Lấy payment summaries của shift  
**Parameters:**
- `shift_report_name` (str): Shift report name

**Returns:** List of payment summaries

---

#### 44. `initialize_payment_summaries_for_shift`
```python
@frappe.whitelist()
def initialize_payment_summaries_for_shift(shift_report_name)
```
**Mục đích:** Initialize payment summaries  
**Parameters:**
- `shift_report_name` (str): Shift report name

**Returns:** Initialized summaries

---

## 🎟️ COUPON APIs

### Module: `posawesome.posawesome.doctype.pos_coupon.pos_coupon`

#### 45. `get_coupon_analytics`
```python
@frappe.whitelist()
def get_coupon_analytics(filters=None)
```
**Mục đích:** Lấy analytics cho coupons  
**Parameters:**
- `filters` (json): Filter criteria

**Returns:** Coupon analytics data

---

## 🔐 INVOICE HOOKS

### Module: `posawesome.posawesome.api.invoice`

#### 46. `mark_invoice_as_submitted_vntax`
```python
@frappe.whitelist()
def mark_invoice_as_submitted_vntax(invoice_name, response_data)
```
**Mục đích:** Mark invoice as submitted to VN Tax system  
**Parameters:**
- `invoice_name` (str): Invoice name
- `response_data` (json): Response from tax system

**Returns:** Success message

---

## 📝 USAGE EXAMPLES

### Example 1: Get Items for POS
```javascript
frappe.call({
    method: "posawesome.posawesome.api.items.get_items",
    args: {
        pos_profile: "POS-PROFILE-001",
        price_list: "Standard Selling",
        search_term: "rice",
        page_length: 20,
        start: 0
    },
    callback: function(r) {
        console.log("Items:", r.message);
    }
});
```

### Example 2: Calculate Discounts
```javascript
frappe.call({
    method: "posawesome.posawesome.api.discount_calculator.calculate_discounts",
    args: {
        invoice_data: JSON.stringify({
            items: [...],
            customer: "CUST-001",
            pos_profile: "POS-PROFILE-001",
            coupons: [...]
        })
    },
    callback: function(r) {
        console.log("Updated items:", r.message.updated_items);
        console.log("Applied offers:", r.message.applied_offers);
    }
});
```

### Example 3: Submit Invoice
```javascript
frappe.call({
    method: "posawesome.posawesome.api.invoices.submit_invoice",
    args: {
        invoice: "SINV-001",
        data: JSON.stringify({
            items: [...],
            payments: [...],
            customer: "CUST-001"
        })
    },
    callback: function(r) {
        console.log("Invoice submitted:", r.message);
    }
});
```

### Example 4: Create Customer
```javascript
frappe.call({
    method: "posawesome.posawesome.api.customers.create_customer",
    args: {
        customer_name: "John Doe",
        email: "john@example.com",
        mobile: "0123456789",
        customer_group: "Individual",
        territory: "All Territories"
    },
    callback: function(r) {
        console.log("Customer created:", r.message);
    }
});
```

---

## 🔒 SECURITY CONSIDERATIONS

### Permission Checks
Tất cả endpoints nên implement permission checks:

```python
@frappe.whitelist()
def sensitive_operation(data):
    # Check permissions
    if not frappe.has_permission("DocType", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Verify user role
    if "POS User" not in frappe.get_roles():
        frappe.throw(_("POS User role required"))
    
    # Proceed with operation
    ...
```

### Rate Limiting
Cân nhắc implement rate limiting cho các endpoints:
- Search endpoints
- Report generation
- Bulk operations

### Input Validation
Luôn validate input data:

```python
@frappe.whitelist()
def process_data(data):
    # Validate JSON
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        frappe.throw(_("Invalid JSON data"))
    
    # Validate required fields
    required_fields = ["customer", "items"]
    for field in required_fields:
        if field not in data:
            frappe.throw(_(f"Missing required field: {field}"))
    
    # Sanitize inputs
    ...
```

---

## 📈 PERFORMANCE TIPS

### 1. Use Caching
```python
@frappe.whitelist()
def get_items(pos_profile):
    cache_key = f"pos_items_{pos_profile}"
    cached = frappe.cache().get_value(cache_key)
    
    if cached:
        return cached
    
    items = fetch_items(pos_profile)
    frappe.cache().set_value(cache_key, items, expires_in_sec=3600)
    return items
```

### 2. Batch Queries
```python
# Bad - N+1 queries
for item_code in item_codes:
    item = frappe.get_doc("Item", item_code)

# Good - Single query
items = frappe.get_all("Item",
    filters={"name": ["in", item_codes]},
    fields=["*"])
```

### 3. Pagination
```python
@frappe.whitelist()
def get_large_dataset(start=0, page_length=20):
    return frappe.get_all("DocType",
        limit_start=start,
        limit_page_length=page_length)
```

---

## 🧪 TESTING

### Unit Test Example
```python
import unittest
from posawesome.posawesome.api.discount_calculator import calculate_discounts

class TestDiscountAPI(unittest.TestCase):
    def test_calculate_discounts(self):
        invoice_data = json.dumps({
            "items": [{"item_code": "ITEM-001", "qty": 5}],
            "customer": "CUST-001",
            "pos_profile": "POS-PROFILE-001"
        })
        
        result = calculate_discounts(invoice_data)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("updated_items", result)
```

---

## 📞 SUPPORT

**Issues:** https://github.com/defendicon/POS-Awesome-V15/issues  
**Wiki:** https://github.com/yrestom/POS-Awesome/wiki

---

**Tài liệu được tạo bởi:** Kiro AI  
**Ngày:** 7 tháng 12, 2025  
**Phiên bản:** 1.0
