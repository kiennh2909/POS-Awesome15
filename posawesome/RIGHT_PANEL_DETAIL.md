# 📄 **CHI TIẾT RIGHT PANEL (INVOICE COMPONENT)**

## 🏗️ **Cấu Trúc Tổng Quan**

### **Invoice.vue - Main Container:**
```javascript
<v-card class="cards my-0 py-0 mt-3 resizable">
  <div class="dynamic-padding">
    <!-- Customer Section -->
    <Customer />

    <!-- Posting Date & Balance -->
    <PostingDateRow />

    <!-- Multi-Currency (if enabled) -->
    <MultiCurrencyRow />

    <!-- Items Table -->
    <div class="items-table-wrapper">
      <ItemsTable />
    </div>
  </div>
</v-card>

<!-- Invoice Summary & Actions -->
<InvoiceSummary />
```

---

## 👤 **1. CUSTOMER SECTION**

### **Customer.vue Component:**
```javascript
<div class="customer-input-wrapper">
  <div class="customer-input-row">
    <!-- Customer Autocomplete -->
    <v-autocomplete
      v-model="customer_name"
      :items="customers"
      label="Select Customer"
      @update:modelValue="updateCustomer"
    />

    <!-- View Details Button -->
    <v-btn icon @click="showCustomerDetails">
      👁️
    </v-btn>
  </div>

  <!-- Modals -->
  <UpdateCustomer />      <!-- ➕ Add/Edit Customer -->
  <CustomerDetail />      <!-- 📊 Customer Details -->
</div>
```

### **Customer Features:**
- **🔍 Search & Select**: Autocomplete với danh sách customers
- **➕ Add New**: Tạo customer mới
- **👁️ View Details**: Popup hiển thị thông tin chi tiết
- **💰 Balance Display**: Hiển thị số dư credit
- **📱 Responsive**: Tự động điều chỉnh trên mobile

---

## 📅 **2. POSTING DATE & CUSTOMER BALANCE**

### **PostingDateRow.vue Component:**
```javascript
<v-row align="center">
  <!-- Posting Date Picker -->
  <v-col cols="6">
    <v-text-field
      v-model="posting_date_display"
      label="Posting Date"
      type="date"
    />
  </v-col>

  <!-- Customer Balance Display -->
  <v-col cols="6" class="text-right">
    <div class="balance-field">
      <span>Balance:</span>
      <span class="balance-value">
        {{ currencySymbol }}{{ formatCurrency(customer_balance) }}
      </span>
    </div>
  </v-col>
</v-row>
```

### **Features:**
- **📅 Date Selection**: Chọn ngày posting cho invoice
- **💰 Balance Display**: Hiển thị số dư hiện tại của customer
- **🎨 Color Coding**: Balance âm = đỏ, dương = xanh
- **🔄 Auto Update**: Cập nhật khi đổi customer

---

## 💱 **3. MULTI-CURRENCY SECTION**

### **MultiCurrencyRow.vue Component:**
```javascript
<v-row v-if="pos_profile.posa_allow_multi_currency">
  <!-- Currency Selector -->
  <v-col cols="6">
    <v-select
      v-model="selected_currency"
      :items="available_currencies"
      label="Currency"
      @update:modelValue="update_currency"
    />
  </v-col>

  <!-- Exchange Rate Display -->
  <v-col cols="6">
    <v-text-field
      v-model="exchange_rate"
      label="Exchange Rate"
      type="number"
      @input="update_exchange_rate"
    />
  </v-col>
</v-row>
```

### **Multi-Currency Features:**
- **💱 Currency Selection**: Dropdown chọn currency
- **📊 Exchange Rate**: Hiển thị tỷ giá
- **🔄 Auto Conversion**: Tự động chuyển đổi giá
- **📅 Rate Date**: Hiển thị ngày áp dụng tỷ giá
- **⚠️ Rate Warnings**: Cảnh báo nếu rate cũ

---

## 📋 **4. ITEMS TABLE SECTION**

### **ItemsTable.vue Component:**
```javascript
<div class="items-table-wrapper">
  <!-- Column Selector -->
  <div class="column-selector-container">
    <v-btn @click="toggleColumnSelection">
      <v-icon>mdi-cog-outline</v-icon>
      Columns
    </v-btn>
  </div>

  <!-- Data Table -->
  <v-data-table
    :headers="items_headers"
    :items="items"
    :items-per-page="itemsPerPage"
    class="modern-items-table"
  >
    <!-- Custom Templates for Each Column -->
    <template #item.item_name="{ item }">
      <!-- Item Name with Image -->
    </template>

    <template #item.qty="{ item }">
      <!-- Quantity Input -->
    </template>

    <template #item.rate="{ item }">
      <!-- Rate Input -->
    </template>

    <!-- More column templates... -->
  </v-data-table>
</div>
```

### **Items Table Features:**
- **📊 Customizable Columns**: Chọn ẩn/hiện cột
- **🔢 Inline Editing**: Sửa số lượng, giá trực tiếp
- **🎨 Drag & Drop**: Kéo thả để reorder items
- **📱 Touch Friendly**: Responsive trên mobile
- **⚡ Real-time Updates**: Tự động tính toán
- **🔍 Search & Filter**: Tìm kiếm trong bảng

### **Available Columns:**
```javascript
const available_columns = [
  { title: "Name", key: "item_name", required: true },
  { title: "QTY", key: "qty", required: true },
  { title: "UOM", key: "uom", required: false },
  { title: "Rate", key: "rate", required: true },
  { title: "Discount %", key: "discount_value", required: false },
  { title: "Discount Amount", key: "discount_amount", required: false },
  { title: "Amount", key: "amount", required: true },
  { title: "Offer?", key: "posa_is_offer", align: "center", required: false }
];
```

---

## 💰 **5. INVOICE SUMMARY & ACTIONS**

### **InvoiceSummary.vue Component:**
```javascript
<div class="invoice-summary">
  <!-- Summary Cards -->
  <v-row>
    <v-col cols="6">
      <v-card class="summary-card">
        <div class="summary-label">Total Items</div>
        <div class="summary-value">{{ total_qty }}</div>
      </v-card>
    </v-col>

    <v-col cols="6">
      <v-card class="summary-card">
        <div class="summary-label">Subtotal</div>
        <div class="summary-value">{{ formatCurrency(subtotal) }}</div>
      </v-card>
    </v-col>
  </v-row>

  <!-- Discount Section -->
  <div class="discount-section">
    <v-text-field
      v-model="additional_discount"
      label="Additional Discount"
      type="number"
    />
  </div>

  <!-- Action Buttons -->
  <div class="action-buttons">
    <v-btn @click="save_and_clear_invoice">
      💾 Save & Clear
    </v-btn>

    <v-btn @click="show_payment">
      💰 Payment
    </v-btn>

    <v-btn @click="submit_invoice">
      🖨️ Submit
    </v-btn>
  </div>
</div>
```

### **Summary Features:**
- **📊 Real-time Calculations**: Tự động tính tổng
- **💰 Discount Management**: Áp dụng giảm giá
- **🎯 Action Buttons**: Save, Payment, Submit
- **🧾 Tax Display**: Hiển thị thuế (nếu có)
- **📱 Responsive Layout**: Điều chỉnh trên mobile

---

## 🎨 **6. SPECIAL FEATURES**

### **Return Invoice Mode:**
```javascript
.return-mode {
  border: 2px solid rgb(var(--v-theme-error)) !important;
  position: relative;
}

.return-mode::before {
  content: "RETURN";
  position: absolute;
  top: 0;
  right: 0;
  background-color: rgb(var(--v-theme-error));
  color: white;
  padding: 4px 12px;
  font-weight: bold;
}
```

### **Drag & Drop Support:**
```javascript
// Handle item dropped from ItemsSelector
handleItemDrop(item) {
  this.add_item(item);
  this.eventBus.emit("show_message", {
    title: `Item ${item.item_name} added to invoice`,
    color: "success"
  });
}
```

### **Keyboard Shortcuts:**
```javascript
// Global shortcuts
created() {
  document.addEventListener("keydown", this.shortOpenPayment.bind(this));
  document.addEventListener("keydown", this.shortDeleteFirstItem.bind(this));
  document.addEventListener("keydown", this.shortOpenFirstItem.bind(this));
  document.addEventListener("keydown", this.shortSelectDiscount.bind(this));
}
```

---

## 📱 **7. RESPONSIVE DESIGN**

### **Mobile Optimizations:**
```css
@media (max-width: 768px) {
  .dynamic-padding {
    padding: var(--dynamic-xs);
  }

  .customer-input-row {
    flex-direction: column;
  }

  .items-table-wrapper {
    overflow-x: auto;
  }
}

@media (max-width: 480px) {
  .action-buttons {
    flex-direction: column;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }
}
```

### **Tablet Layout:**
```css
@media (min-width: 769px) and (max-width: 1024px) {
  .customer-input-row {
    gap: 12px;
  }

  .items-table {
    font-size: 0.9rem;
  }
}
```

---

## 🔧 **8. ADVANCED FEATURES**

### **Column Customization:**
```javascript
// Save/Load column preferences
saveColumnPreferences() {
  localStorage.setItem("posawesome_selected_columns", JSON.stringify(this.selected_columns));
}

loadColumnPreferences() {
  const saved = localStorage.getItem("posawesome_selected_columns");
  if (saved) {
    this.selected_columns = JSON.parse(saved);
  }
}
```

### **Invoice Height Persistence:**
```javascript
saveInvoiceHeight() {
  if (this.$refs.invoiceCard) {
    this.invoiceHeight = this.$refs.invoiceCard.clientHeight + "px";
    localStorage.setItem("posawesome_invoice_height", this.invoiceHeight);
  }
}
```

### **Multi-Currency Support:**
```javascript
async update_currency_and_rate() {
  // Fetch exchange rates from server
  const r = await frappe.call({
    method: "posawesome.posawesome.api.invoices.fetch_exchange_rate_pair",
    args: {
      from_currency: priceListCurrency,
      to_currency: this.selected_currency
    }
  });

  if (r && r.message) {
    this.exchange_rate = r.message.exchange_rate;
    this.update_item_rates();
  }
}
```

---

## 🎯 **9. USER INTERACTION FLOW**

### **Typical Invoice Creation:**
1. **👤 Select Customer** → Autocomplete dropdown
2. **📅 Set Posting Date** → Date picker (optional)
3. **💱 Choose Currency** → Currency selector (if enabled)
4. **🛒 Add Items** → Drag from left panel or search
5. **🔢 Adjust Quantities** → Inline editing
6. **💰 Apply Discounts** → Discount inputs
7. **💳 Process Payment** → Payment button
8. **🖨️ Submit Invoice** → Print/save

### **Return Invoice Flow:**
1. **🔄 Select Return Mode** → Type selector
2. **📋 Load Original Invoice** → Search returns
3. **🔢 Set Return Quantities** → Negative values
4. **💰 Calculate Refunds** → Auto calculation
5. **🖨️ Submit Return** → Process return

---

## 📊 **10. DATA FLOW & STATE MANAGEMENT**

### **Event Bus Communication:**
```javascript
// Component Communication
this.eventBus.emit("add_item", item);
this.eventBus.emit("update_customer", customer);
this.eventBus.emit("show_payment", true);
this.eventBus.emit("clear_invoice");

// Global State Updates
this.eventBus.on("register_pos_profile", (data) => {
  this.pos_profile = data.pos_profile;
  this.initializeItemsHeaders();
});
```

### **Reactive Data Properties:**
```javascript
data() {
  return {
    // Core Data
    pos_profile: {},
    invoice_doc: {},
    customer: "",
    items: [],

    // UI State
    invoiceType: "Invoice",
    selected_currency: "",
    exchange_rate: 1,

    // Table Config
    items_headers: [],
    selected_columns: [],
    show_column_selector: false,

    // Features
    tax_print_loading: false,
    invoiceHeight: null
  };
}
```

---

## 🎨 **11. STYLING & THEMES**

### **Dynamic Theming:**
```css
.cards {
  background-color: var(--surface-secondary) !important;
}

:deep(.dark-theme) .cards {
  background-color: #121212 !important;
}

.return-mode {
  border: 2px solid rgb(var(--v-theme-error)) !important;
}
```

### **Custom Scrollbars:**
```css
.items-table-wrapper::-webkit-scrollbar {
  width: 6px;
}

.items-table-wrapper::-webkit-scrollbar-thumb {
  background: var(--primary-start);
  border-radius: 3px;
}
```

---

## 🚀 **12. PERFORMANCE OPTIMIZATIONS**

### **Lazy Loading:**
- **Items Table**: Virtual scrolling for large datasets
- **Customer List**: Paginated loading
- **Currency Rates**: Cached exchange rates

### **Memory Management:**
- **Event Cleanup**: Proper event listener removal
- **Component Unmounting**: Clear intervals and listeners
- **Local Storage**: Persistent user preferences

### **Real-time Updates:**
- **Debounced Calculations**: Prevent excessive recalculations
- **Batch Updates**: Group multiple changes
- **Optimistic UI**: Immediate feedback for better UX

---

## 📱 **13. MOBILE & TOUCH OPTIMIZATIONS**

### **Touch Gestures:**
- **Swipe to Delete**: Remove items with swipe
- **Tap to Edit**: Quick edit mode
- **Drag to Reorder**: Touch-friendly reordering

### **Mobile UI Adjustments:**
```css
@media (max-width: 768px) {
  .customer-input-row {
    flex-direction: column;
    gap: 8px;
  }

  .action-buttons {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .items-table {
    font-size: 0.875rem;
  }
}
```

---

## 🎉 **Kết Luận:**

**Right Panel (Invoice Component)** là **trái tim** của hệ thống POS với các tính năng:

### ✅ **Core Features:**
- **👤 Customer Management** với autocomplete và details
- **📋 Dynamic Items Table** với customizable columns
- **💰 Real-time Calculations** cho totals và discounts
- **💱 Multi-currency Support** với exchange rates
- **🔄 Return Invoice Processing** với negative values

### ✅ **Advanced Features:**
- **🎨 Drag & Drop** từ left panel
- **⚡ Keyboard Shortcuts** cho productivity
- **📱 Responsive Design** cho mọi thiết bị
- **🌙 Dark Theme Support** 
- **💾 Local Storage** cho preferences

### ✅ **User Experience:**
- **🎯 Intuitive Workflow** từ customer → items → payment
- **⚡ Fast Performance** với optimizations
- **🔧 Highly Customizable** với column selection
- **📊 Real-time Feedback** với event system

**Right Panel là nơi diễn ra hầu hết các tương tác chính của người dùng trong quy trình bán hàng!** 🎯