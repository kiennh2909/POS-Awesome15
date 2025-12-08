# 🛒 PHÂN TÍCH CHI TIẾT LUỒNG BÁN HÀNG - POS AWESOME

**Ngày phân tích:** 7 tháng 12, 2025  
**Phạm vi:** Bán hàng → Tạo hóa đơn → In hóa đơn → Gửi MeInvoice → Cập nhật → Tổng hợp ca  
**Góc độ:** Service Layer, API, và Business Logic

---

## 📋 MỤC LỤC

1. [Tổng quan luồng bán hàng](#tổng-quan-luồng-bán-hàng)
2. [Bước 1: Thêm sản phẩm vào giỏ](#bước-1-thêm-sản-phẩm-vào-giỏ)
3. [Bước 2: Tính toán giá và khuyến mãi](#bước-2-tính-toán-giá-và-khuyến-mãi)
4. [Bước 3: Xử lý thanh toán](#bước-3-xử-lý-thanh-toán)
5. [Bước 4: Tạo và submit hóa đơn](#bước-4-tạo-và-submit-hóa-đơn)
6. [Bước 5: In hóa đơn](#bước-5-in-hóa-đơn)
7. [Bước 6: Gửi MeInvoice (VN Tax)](#bước-6-gửi-meinvoice-vn-tax)
8. [Bước 7: Cập nhật Shift Report](#bước-7-cập-nhật-shift-report)
9. [Bước 8: Tổng hợp ca](#bước-8-tổng-hợp-ca)
10. [Sơ đồ tổng thể](#sơ-đồ-tổng-thể)
11. [Checklist cải tiến](#checklist-cải-tiến)

---

## 🎯 TỔNG QUAN LUỒNG BÁN HÀNG

### Sơ đồ tổng thể (High-level)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SALES WORKFLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ADD ITEMS TO CART                                           │
│     ├─ Search/Select items                                      │
│     ├─ Add to cart (with UOM, qty)                              │
│     └─ Update cart display                                      │
│                                                                 │
│  2. CALCULATE DISCOUNTS & OFFERS                                │
│     ├─ Call discount calculator API                             │
│     ├─ Apply item/group/brand offers                            │
│     ├─ Apply coupons                                            │
│     └─ Update prices                                            │
│                                                                 │
│  3. PROCESS PAYMENT                                             │
│     ├─ Select payment methods                                   │
│     ├─ Calculate change                                         │
│     ├─ Handle credit/advance                                    │
│     └─ Validate payment                                         │
│                                                                 │
│  4. CREATE & SUBMIT INVOICE                                     │
│     ├─ Build invoice document                                   │
│     ├─ Calculate taxes                                          │
│     ├─ Calculate stock_qty                                      │
│     ├─ Submit to ERPNext                                        │
│     └─ Update stock                                             │
│                                                                 │
│  5. PRINT INVOICE                                               │
│     ├─ Standard print (Frappe)                                  │
│     └─ Tax print (optional)                                     │
│                                                                 │
│  6. SEND TO MEINVOICE (VN TAX)                                  │
│     ├─ Prepare invoice data                                     │
│     ├─ Call MISA API                                            │
│     ├─ Get response (ReqID)                                     │
│     └─ Update invoice status                                    │
│                                                                 │
│  7. UPDATE SHIFT REPORT                                         │
│     ├─ Add invoice to shift report                              │
│     ├─ Update payment breakdown                                 │
│     ├─ Update totals                                            │
│     └─ Update payment summaries                                 │
│                                                                 │
│  8. SHIFT SUMMARY                                               │
│     ├─ Calculate shift totals                                   │
│     ├─ Payment reconciliation                                   │
│     └─ Generate reports                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 BƯỚC 1: THÊM SẢN PHẨM VÀO GIỎ

### 1.1 Frontend Flow

**Component:** `ItemsSelector.vue` + `Invoice.vue`

**File:** `posawesome/public/js/posapp/components/pos/invoiceItemMethods.js`


```javascript
// Step 1.1: User clicks on item or scans barcode
add_item(item) {
    console.log(`[ADD_ITEM] 🛒 Adding item: ${item.item_code}`);
    
    // Step 1.2: Create new item object
    const new_item = this.get_new_item(item);
    
    // Step 1.3: Check if should merge with existing item
    const existing_idx = this.findExistingItemIndex(new_item);
    
    if (existing_idx !== -1 && this.shouldMergeItem(new_item)) {
        // Merge with existing item
        this.items[existing_idx].qty += new_item.qty;
        this.update_item_detail(this.items[existing_idx], false);
    } else {
        // Add as new line
        this.items.push(new_item);
        this.update_item_detail(new_item, true);
    }
    
    // Step 1.4: Apply UOM conversion if needed
    if (new_item.uom !== new_item.stock_uom) {
        this.applyImmediateUomConversion(new_item);
    }
    
    // Step 1.5: Trigger discount calculation
    this.calculateDiscountsDebounced();
}

// Step 1.6: Get new item with default values
get_new_item(item) {
    return {
        posa_row_id: this.generate_row_id(),
        item_code: item.item_code,
        item_name: item.item_name,
        qty: 1,
        uom: item.stock_uom,
        stock_uom: item.stock_uom,
        conversion_factor: 1,
        rate: item.price_list_rate || 0,
        price_list_rate: item.price_list_rate || 0,
        base_price_list_rate: item.price_list_rate || 0,
        amount: item.price_list_rate || 0,
        warehouse: this.pos_profile.warehouse,
        // ... other fields
    };
}
```

### 1.2 Key Methods

**Method:** `update_item_detail(item, is_new_item)`

```javascript
update_item_detail(item, is_new_item) {
    // Call ERPNext API to get item details
    frappe.call({
        method: "posawesome.posawesome.api.items.get_items_details",
        args: {
            pos_profile: JSON.stringify(this.pos_profile),
            items_data: JSON.stringify([{
                item_code: item.item_code,
                qty: item.qty,
                uom: item.uom
            }])
        },
        callback: (r) => {
            if (r.message && r.message.length > 0) {
                const item_detail = r.message[0];
                // Update item with details from server
                Object.assign(item, item_detail);
            }
        }
    });
}
```

### 1.3 UOM Conversion

**Method:** `applyImmediateUomConversion(item)`

```javascript
applyImmediateUomConversion(item) {
    if (item._converted_once) return; // Prevent double conversion
    
    const cf = item.conversion_factor || 1;
    
    if (cf > 1) {
        // Convert price from stock UOM to selected UOM
        item.rate = item.base_price_list_rate * cf;
        item.price_list_rate = item.rate;
        item.amount = item.rate * item.qty;
        
        item._converted_once = true;
        console.log(`[UOM_CONVERT] ✅ Converted: ${item.item_code}, CF: ${cf}, New Rate: ${item.rate}`);
    }
}
```

### 1.4 Service Layer

**Status:** ❌ **THIẾU** - Không có dedicated cart service

**Đề xuất tạo:** `cartService.js`

```javascript
class CartService {
    async addItem(itemCode, qty, uom) {
        // Validate item
        // Get item details
        // Add to cart
        // Calculate totals
    }
    
    async updateItemQty(rowId, newQty) {
        // Update quantity
        // Recalculate
    }
    
    async removeItem(rowId) {
        // Remove from cart
        // Recalculate
    }
    
    async clearCart() {
        // Clear all items
    }
}
```

---

## 💰 BƯỚC 2: TÍNH TOÁN GIÁ VÀ KHUYẾN MÃI

### 2.1 Frontend Flow

**Component:** `Invoice.vue`

```javascript
// Step 2.1: Debounced calculation trigger
calculateDiscountsDebounced() {
    clearTimeout(this.discountCalculationTimer);
    this.discountCalculationTimer = setTimeout(() => {
        this.calculateDiscounts();
    }, 500); // Wait 500ms after last change
}

// Step 2.2: Call discount calculator API
async calculateDiscounts() {
    console.log(`[DISCOUNT_CALC] 🎯 Calculating discounts for ${this.items.length} items`);
    
    const invoiceData = {
        items: this.items,
        customer: this.customer_info?.name,
        pos_profile: this.pos_profile.name,
        coupons: this.applied_coupons || []
    };
    
    const r = await frappe.call({
        method: "posawesome.posawesome.api.discount_calculator.calculate_discounts",
        args: {
            invoice_data: JSON.stringify(invoiceData)
        }
    });
    
    if (r.message && r.message.status === "success") {
        // Step 2.3: Update items with calculated prices
        this.items = r.message.updated_items;
        this.applied_offers = r.message.applied_offers;
        
        // Step 2.4: Recalculate totals
        this.calculate_totals();
    }
}
```

### 2.2 Backend API

**Endpoint:** `calculate_discounts`

**File:** `posawesome/posawesome/api/discount_calculator.py`

```python
@frappe.whitelist()
def calculate_discounts(invoice_data):
    """Master function to calculate all discounts"""
    try:
        log.info("[DISCOUNT_CALC] 🎯 START")
        data = json.loads(invoice_data)
        
        calculator = DiscountCalculator(data)
        result = calculator.process()
        
        log.info(f"[DISCOUNT_CALC] ✅ COMPLETED - Applied {len(result.get('applied_offers', []))} offers")
        return result
        
    except Exception as e:
        log.error(f"[DISCOUNT_CALC] ❌ ERROR: {str(e)}")
        frappe.throw(str(e))

class DiscountCalculator:
    def process(self):
        # Step 1: Coalesce identical items
        self._coalesce_identical_items()
        
        # Step 2: Validate coupons
        self._validate_coupons()
        
        # Step 3: Reset prices to original
        self._reset_item_prices()
        
        # Step 4: Get valid offers
        self._get_valid_offers()
        
        # Step 5: Find applicable offers
        self._find_applicable_offers()
        
        # Step 6: Apply offers
        self._apply_offers()
        
        # Step 7: Calculate totals
        self._calculate_totals()
        
        return {
            "status": "success",
            "updated_items": self.items,
            "applied_offers": self.applied_offers,
            "totals": self.totals
        }
```

### 2.3 Offer Types

**1. Item Code Offers:**
```python
def _check_item_code_offer(self, offer):
    matching_items = []
    total_qty = 0
    
    for item in self.items:
        if item.get("item_code") == offer.get("item") and not item.get("posa_is_offer"):
            matching_items.append(item)
            total_qty += item.get("qty", 0)
    
    # Check min/max qty conditions
    if offer.get("min_qty") and total_qty < offer.get("min_qty"):
        return False
    
    # Apply discount
    if offer.get("discount_type") == "Rate":
        for item in matching_items:
            item["rate"] = offer.get("rate")
    elif offer.get("discount_type") == "Percentage":
        for item in matching_items:
            discount = item["rate"] * (offer.get("discount_percentage") / 100)
            item["rate"] = item["rate"] - discount
    
    return True
```

**2. Block-based Offers:**
```python
def _check_item_code_offer(self, offer):
    if offer.get("is_used_block"):
        uom_ref = offer.get("uom_ref")
        items_per_block = int(offer.get("total_items_in_block_qty") or 0)
        min_blocks = int(offer.get("min_block_qty") or 1)
        
        # Convert to stock units
        eligible_units = 0
        for item in matching_items:
            qty = item.get("qty", 0)
            cf = float(item.get("conversion_factor") or 1)
            
            if item.get("uom") == item.get("stock_uom"):
                eligible_units += qty
            else:
                eligible_units += qty * cf
        
        total_blocks = eligible_units // items_per_block
        
        if total_blocks < min_blocks:
            return False
    
    return True
```

### 2.4 Service Layer

**Status:** ✅ **CÓ** - Nhưng không có frontend service wrapper

**Đề xuất tạo:** `discountService.js`

```javascript
class DiscountService {
    async calculateDiscounts(invoiceData) {
        return this.apiCall("discount_calculator.calculate_discounts", {
            invoice_data: JSON.stringify(invoiceData)
        });
    }
    
    async validateCoupon(couponCode, customer, company) {
        return this.apiCall("pos_coupon.check_coupon_code", {
            coupon_code: couponCode,
            customer: customer,
            company: company
        });
    }
    
    async getAvailableOffers(posProfile, customer) {
        return this.apiCall("offers.get_available_offers", {
            pos_profile: posProfile,
            customer: customer
        });
    }
}
```

---

## 💳 BƯỚC 3: XỬ LÝ THANH TOÁN

### 3.1 Frontend Flow

**Component:** `Payments.vue`

```javascript
// Step 3.1: User enters payment amounts
set_full_amount(idx) {
    const totalAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
    
    // Calculate remaining amount
    const paidSoFar = this.invoice_doc.payments
        .filter((p, i) => i !== idx)
        .reduce((sum, p) => sum + (p.amount || 0), 0);
    
    const remaining = totalAmount - paidSoFar;
    
    // Set amount for this payment method
    this.invoice_doc.payments[idx].amount = remaining;
    
    // Recalculate change
    this.calculate_change();
}

// Step 3.2: Calculate change
calculate_change() {
    const totalAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
    const totalPaid = this.invoice_doc.payments.reduce((sum, p) => sum + (p.amount || 0), 0);
    
    this.total_change = totalPaid - totalAmount;
    
    if (this.total_change > 0) {
        // Ask user: paid change or credit change?
        this.show_change_dialog = true;
    }
}

// Step 3.3: Submit payment
async submit_payment(print, tax) {
    console.log(`[SUBMIT_PAYMENT] 🎯 START - Print: ${print}, Tax: ${tax}`);
    
    // Validate payment
    if (!this.validate_payment()) {
        return;
    }
    
    // Submit invoice
    this.loading = true;
    this.submit_invoice(print, tax);
}
```

### 3.2 Payment Validation

```javascript
validate_payment() {
    const totalAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
    const totalPaid = this.invoice_doc.payments.reduce((sum, p) => sum + (p.amount || 0), 0);
    
    // Check if paid enough
    if (totalPaid < totalAmount && !this.pos_profile.posa_allow_partial_payment) {
        frappe.msgprint(__("Payment amount is less than invoice total"));
        return false;
    }
    
    // Check payment methods
    for (const payment of this.invoice_doc.payments) {
        if (!payment.mode_of_payment) {
            frappe.msgprint(__("Please select payment method"));
            return false;
        }
        
        if (payment.amount <= 0) {
            frappe.msgprint(__("Payment amount must be greater than 0"));
            return false;
        }
    }
    
    return true;
}
```

### 3.3 Service Layer

**Status:** ❌ **THIẾU** - Không có payment service

**Đề xuất tạo:** `paymentService.js`

```javascript
class PaymentService {
    async processPayment(invoiceData, paymentData) {
        // Validate payment
        // Process payment
        // Handle change
        // Create payment entry
    }
    
    async validatePaymentMethods(payments, posProfile) {
        // Validate each payment method
        // Check limits
        // Check permissions
    }
    
    async calculateChange(totalAmount, payments) {
        // Calculate change
        // Determine paid/credit change
    }
    
    async createAdvancePayment(customer, amount, modeOfPayment) {
        // Create advance payment entry
    }
}
```

---

## 📄 BƯỚC 4: TẠO VÀ SUBMIT HÓA ĐƠN

### 4.1 Frontend Flow

**Component:** `Payments.vue`

```javascript
async submit_invoice(print, tax) {
    console.log(`[SUBMIT_INVOICE] 🎯 START`);
    
    // Step 4.1: Prepare invoice data
    const invoice_doc = this.get_invoice_doc();
    
    // Step 4.2: Prepare submit data
    const data = {
        total_change: this.total_change,
        paid_change: this.paid_change,
        credit_change: this.credit_change,
        redeemed_customer_credit: this.redeemed_customer_credit,
        customer_credit_dict: this.customer_credit_dict,
        is_cashback: this.is_cashback,
        posa_is_printed: print ? 1 : 0,
        tax_report: tax ? 1 : 0,
        due_date: this.due_date
    };
    
    // Step 4.3: Call submit API
    const r = await frappe.call({
        method: "posawesome.posawesome.api.invoices.submit_invoice",
        args: {
            invoice: JSON.stringify(invoice_doc),
            data: JSON.stringify(data)
        }
    });
    
    if (r.message) {
        console.log(`[SUBMIT_INVOICE] ✅ SUCCESS - Invoice: ${r.message.name}`);
        
        // Step 4.4: Handle post-submit actions
        this.handle_post_submit(r.message, print, tax);
    }
}
```

### 4.2 Backend API

**Endpoint:** `submit_invoice`

**File:** `posawesome/posawesome/api/invoices.py`

```python
@frappe.whitelist()
def submit_invoice(invoice, data):
    log.info(f"[SUBMIT_INVOICE] 🎯 START")
    
    data = json.loads(data)
    invoice = json.loads(invoice)
    invoice_name = invoice.get("name")
    
    # STEP 1: Create or update invoice
    if not invoice_name or not frappe.db.exists("Sales Invoice", invoice_name):
        log.info(f"[SUBMIT_INVOICE] 🆕 Creating new invoice")
        created = update_invoice(json.dumps(invoice))
        invoice_name = created.get("name")
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
    else:
        log.info(f"[SUBMIT_INVOICE] 📝 Updating existing invoice: {invoice_name}")
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
        invoice_doc.update(invoice)
    
    # STEP 2: Calculate stock_qty for all items
    log.info(f"[SUBMIT_INVOICE] 📦 Calculating stock_qty for {len(invoice_doc.items)} items")
    for item in invoice_doc.items:
        qty = flt(item.qty)
        conversion_factor = flt(item.conversion_factor)
        
        if conversion_factor > 0:
            item.stock_qty = qty * conversion_factor
        else:
            item.stock_qty = qty
    
    # STEP 3: Handle advance payment (credit change)
    if data.get("credit_change"):
        log.info(f"[SUBMIT_INVOICE] 💳 Creating advance payment: {data.get('credit_change')}")
        advance_payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "mode_of_payment": "Cash",
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": invoice_doc.get("customer"),
            "paid_amount": data.get("credit_change"),
            "received_amount": data.get("credit_change"),
            "company": invoice_doc.get("company")
        })
        advance_payment_entry.save()
        advance_payment_entry.submit()
    
    # STEP 4: Handle customer credit redemption
    if data.get("redeemed_customer_credit"):
        log.info(f"[SUBMIT_INVOICE] 🎫 Processing customer credit redemption")
        for row in data.get("customer_credit_dict"):
            if row["type"] == "Advance" and row["credit_to_redeem"]:
                advance = frappe.get_doc("Payment Entry", row["credit_origin"])
                
                advance_payment = {
                    "reference_type": "Payment Entry",
                    "reference_name": advance.name,
                    "advance_amount": advance.unallocated_amount,
                    "allocated_amount": row["credit_to_redeem"]
                }
                
                invoice_doc.append("advances", advance_payment)
                invoice_doc.is_pos = 0
    
    # STEP 5: Attach customer tax ID
    log.info(f"[SUBMIT_INVOICE] 🆔 Attaching customer tax ID")
    if invoice_doc.get("customer"):
        cust_tax_id = frappe.db.get_value("Customer", invoice_doc.customer, "tax_id")
        if cust_tax_id:
            if invoice_doc.meta.has_field("tax_id"):
                invoice_doc.tax_id = cust_tax_id
            if invoice_doc.meta.has_field("customer_tax_id"):
                invoice_doc.customer_tax_id = cust_tax_id
    
    # STEP 6: Save invoice
    invoice_doc.save()
    
    # STEP 7: Submit invoice
    if frappe.get_value("POS Profile", invoice_doc.pos_profile, 
                        "posa_allow_submissions_in_background_job"):
        # Queue for background submission
        log.info(f"[SUBMIT_INVOICE] 🔄 Queuing for background submission")
        enqueue(method=submit_in_background_job, ...)
    else:
        # Submit immediately
        log.info(f"[SUBMIT_INVOICE] ⚡ Submitting immediately")
        _set_item_level_discount_totals(invoice_doc)
        invoice_doc.submit()
        
        # Redeem customer credit
        redeeming_customer_credit(invoice_doc, data, ...)
    
    log.info(f"[SUBMIT_INVOICE] 🎉 COMPLETED - Invoice: {invoice_doc.name}")
    return {"name": invoice_doc.name, "status": invoice_doc.docstatus}
```

### 4.3 Tax Calculation

**File:** `posawesome/posawesome/api/invoices.py`

```python
def calculate_taxes(invoice_doc, data):
    """Calculate taxes for each item"""
    log.info(f"[TAX_CALC] 🧮 Calculating taxes")
    
    tax_entries = {}
    
    for item in invoice_doc.items:
        # Get item tax template
        tax_template = item.get("item_tax_template")
        if not tax_template:
            continue
        
        # Get tax rate
        tax_rate = get_tax_rate_from_template(tax_template)
        
        # Calculate tax amount on net_amount
        tax_amount = flt(item.net_amount) * tax_rate / 100
        
        # Add to tax entries
        key = f"{tax_template}_{tax_rate}"
        if key not in tax_entries:
            tax_entries[key] = {
                "charge_type": "Actual",
                "account_head": get_tax_account(tax_template),
                "description": f"Tax {tax_rate}%",
                "rate": tax_rate,
                "tax_amount": 0
            }
        
        tax_entries[key]["tax_amount"] += tax_amount
    
    # Update invoice taxes
    invoice_doc.taxes = []
    for tax_entry in tax_entries.values():
        invoice_doc.append("taxes", tax_entry)
    
    log.info(f"[TAX_CALC] ✅ Calculated {len(tax_entries)} tax entries")
```

### 4.4 Service Layer

**Status:** ❌ **THIẾU** - Không có invoice service

**Đề xuất tạo:** `invoiceService.js`

```javascript
class InvoiceService {
    async createInvoice(invoiceData) {
        return this.apiCall("invoices.update_invoice", {
            data: JSON.stringify(invoiceData)
        });
    }
    
    async submitInvoice(invoice, submitData) {
        return this.apiCall("invoices.submit_invoice", {
            invoice: JSON.stringify(invoice),
            data: JSON.stringify(submitData)
        });
    }
    
    async getInvoice(invoiceName) {
        return frappe.db.get_doc("Sales Invoice", invoiceName);
    }
    
    async deleteInvoice(invoiceName) {
        return this.apiCall("invoices.delete_invoice", {
            invoice: invoiceName
        });
    }
}
```

---

## 🖨️ BƯỚC 5: IN HÓA ĐƠN

### 5.1 Standard Print

**Component:** `Payments.vue`

```javascript
load_print_page(invoice_to_print) {
    console.log(`[PRINT] 🖨️ Printing invoice: ${invoice_to_print.name}`);
    
    // Validate invoice
    if (!invoice_to_print || !invoice_to_print.name) {
        console.error("[PRINT] ❌ Invalid invoice object");
        frappe.msgprint("Không thể in: Dữ liệu hóa đơn không hợp lệ");
        return;
    }
    
    // Get print settings
    const print_format = this.pos_profile.print_format_for_online || 
                        this.pos_profile.print_format;
    const letter_head = this.pos_profile.letter_head || 0;
    
    // Build print URL
    const url = frappe.urllib.get_base_url() +
        "/printview?doctype=Sales%20Invoice&name=" +
        invoice_to_print.name +
        "&trigger_print=1" +
        "&format=" + print_format +
        "&no_letterhead=" + letter_head;
    
    // Print
    if (this.pos_profile.posa_silent_print) {
        silentPrint(url);
    } else {
        const printWindow = window.open(url, "Print");
        if (printWindow) {
            printWindow.addEventListener("load", function() {
                printWindow.print();
            }, { once: true });
        } else {
            frappe.msgprint("Trình duyệt đã chặn cửa sổ in");
        }
    }
}
```

### 5.2 Tax Print (Taiwan)

**Component:** `Payments.vue`

```javascript
async load_print_page_tax(invoice_or_name) {
    try {
        console.log(`[TAX_PRINT] 🖨️ Tax printing invoice`);
        
        // Step 1: Get fresh invoice from server
        const invoice_name = typeof invoice_or_name === 'string' ? 
            invoice_or_name : invoice_or_name.name;
        
        const invoice_to_print = await frappe.db.get_doc("Sales Invoice", invoice_name);
        
        // Step 2: Verify tax_id
        const resolvedTaxId = String(
            invoice_to_print.tax_id || 
            invoice_to_print.customer_tax_id || 
            ""
        ).trim();
        
        if (!resolvedTaxId) {
            console.warn("[TAX_PRINT] ⚠️ No tax_id found");
        }
        
        // Step 3: Determine country and call appropriate handler
        const country = this.pos_profile?.country || "TW";
        
        if (country === "VN") {
            // Vietnam: Send to MISA
            await handleVietnamTaxPrint(
                invoice_to_print,
                this.pos_profile,
                (result) => {
                    console.log("[TAX_PRINT] ✅ Vietnam Success:", result);
                },
                (error) => {
                    console.error("[TAX_PRINT] ❌ Vietnam Error:", error);
                    frappe.msgprint({
                        title: "Lỗi Gửi Hóa Đơn MISA",
                        message: `Không thể gửi hóa đơn: ${error.message}`,
                        indicator: "red"
                    });
                }
            );
        } else {
            // Taiwan: Print locally
            await handleTaxPrint(
                invoice_to_print,
                this.pos_profile,
                (result) => {
                    console.log("[TAX_PRINT] ✅ Taiwan Success:", result);
                },
                (error) => {
                    console.error("[TAX_PRINT] ❌ Taiwan Error:", error);
                    frappe.msgprint({
                        title: "Lỗi In Hóa Đơn Thuế",
                        message: `Không thể in: ${error.message}`,
                        indicator: "red"
                    });
                }
            );
        }
        
    } catch (error) {
        console.error("[TAX_PRINT] ❌ Unexpected error:", error);
        frappe.msgprint({
            title: "Lỗi Hệ Thống In",
            message: `Có lỗi không mong đợi: ${error.message}`,
            indicator: "red"
        });
        throw error;
    }
}
```

---

## 🇻🇳 BƯỚC 6: GỬI MEINVOICE (VN TAX)

### 6.1 Frontend Flow

**File:** `posawesome/public/js/posapp/components/pos/taxPrintHandler.js`
