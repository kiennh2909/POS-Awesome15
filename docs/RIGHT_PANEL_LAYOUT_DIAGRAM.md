# 📐 **CHI TIẾT LAYOUT DIAGRAM - RIGHT PANEL**

## 🎨 **Visual Layout Structure**

```
┌─────────────────────────────────────────────────────────────┐
│                    📄 RIGHT PANEL                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                🏗️ MAIN INVOICE CARD                 │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │         👤 CUSTOMER SECTION                     │ │    │
│  │  │  ┌─────────────────────────────────────────┐    │ │    │
│  │  │  │  🔍 Customer Dropdown + 👁️ View Details │    │ │    │
│  │  │  └─────────────────────────────────────────┘    │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │     📅 POSTING DATE & CUSTOMER BALANCE          │ │    │
│  │  │  ┌─────────────┐ ┌─────────────────────────┐    │ │    │
│  │  │  │ 📅 Date & Time  │ │ 💰 Balance: $1,250.00│    │ │    │
│  │  │  │ 2024-01-15     │ │ (Credit/Due Display) │    │ │    │
│  │  │  │ 14:30:25       │ │                     │    │ │    │
│  │  │  │ (Read Only)    │ │                     │    │ │    │
│  │  │  └─────────────┘ └─────────────────────────┘    │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │                    [5px spacing]                        │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │        💱 MULTI-CURRENCY SECTION (Optional)     │ │    │
│  │  │  ┌─────────────┐ ┌─────────────────────────┐    │ │    │
│  │  │  │ 💱 Currency │ │ 📊 Exchange Rate: 1.5   │    │ │    │
│  │  │  │ USD ▼       │ │ (Auto-fetched)          │    │ │    │
│  │  │  └─────────────┘ └─────────────────────────┘    │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │           📋 ITEMS TABLE SECTION                 │ │    │
│  │  │  ┌─────────────────────────────────────────┐    │ │    │
│  │  │  │ ⚙️ Column Selector Button (Top-Right)   │    │ │    │
│  │  │  └─────────────────────────────────────────┘    │ │    │
│  │  │                                                 │ │    │
│  │  │  ┌─────────────────────────────────────────┐    │ │    │
│  │  │  │ 📊 ITEMS DATA TABLE                       │    │ │    │
│  │  │  │ ┌─────┬─────┬─────┬─────┬─────┬─────┐    │ │    │
│  │  │  │ │Name │QTY  │UOM  │Rate │Disc │Amt  │    │ │    │
│  │  │  │ ├─────┼─────┼─────┼─────┼─────┼─────┤    │ │    │
│  │  │  │ │iPad │  2  │Each │$500 │ 5%  │$950 │    │ │    │
│  │  │  │ │iPho │  1  │Each │$800 │ 0%  │$800 │    │ │    │
│  │  │  │ │MacB │  3  │Each │$200 │10%  │$540 │    │ │    │
│  │  │  │ └─────┴─────┴─────┴─────┴─────┴─────┘    │ │    │
│  │  │  │ 📄 Pagination (if many items)           │    │ │    │
│  │  │  └─────────────────────────────────────────┘    │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │        🎨 COLUMN SELECTOR DIALOG (Modal)        │ │    │
│  │  │  ┌─────────────────────────────────────────┐    │ │    │
│  │  │  │ 📋 Select Columns to Display             │    │ │    │
│  │  │  │                                         │    │ │    │
│  │  │  │ ☑️ Name (Required)                       │    │ │    │
│  │  │  │ ☑️ QTY (Required)                        │    │ │    │
│  │  │  │ ☐ UOM                                   │    │ │    │
│  │  │  │ ☑️ Rate (Required)                       │    │ │    │
│  │  │  │ ☐ Discount %                            │    │ │    │
│  │  │  │ ☐ Discount Amount                       │    │ │    │
│  │  │  │ ☑️ Amount (Required)                     │    │ │    │
│  │  │  │ ☐ Offer?                                │    │ │    │
│  │  │  │                                         │    │ │    │
│  │  │  │ [Cancel] [Apply]                        │    │ │    │
│  │  │  └─────────────────────────────────────────┘    │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           💰 INVOICE SUMMARY & ACTIONS              │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │ 📊 SUMMARY CARDS                                │ │    │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │    │
│  │  │  │ 🛒 Total     │ │ 💰 Subtotal  │ │ 🧾 Tax      │ │ │    │
│  │  │  │ Items: 6    │ │ $2,290.00   │ │ $229.00     │ │ │    │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │ 💸 DISCOUNT SECTION                             │ │    │
│  │  │  ┌─────────────────────────────────────────┐    │ │    │
│  │  │  │ Additional Discount: ________ %         │    │ │    │
│  │  │  │ Additional Discount: $_______           │    │ │    │
│  │  │  └─────────────────────────────────────────┘    │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │ 🎯 ACTION BUTTONS                               │ │    │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │ │    │
│  │  │  │💾   │ │💰   │ │🖨️   │ │🔄   │ │❌   │       │ │    │
│  │  │  │Save │ │Pay  │ │Print│ │Draft│ │Cancel│       │ │    │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 **Mobile Layout (Responsive)**

```
┌─────────────────────────────────────┐
│          📱 MOBILE LAYOUT           │
│  ┌─────────────────────────────┐    │
│  │        🏗️ INVOICE CARD       │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │     👤 CUSTOMER          │ │    │
│  │  │  🔍 Customer + 👁️       │ │    │
│  │  └─────────────────────────┘ │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ 📅 DATE & 💰 BALANCE     │ │    │
│  │  │ 📅 Date & Time:         │ │    │
│  │  │ 2024-01-15 14:30:25     │ │    │
│  │  │ (Read Only)             │ │    │
│  │  │ 💰 Balance: $1,250.00   │ │    │
│  │  └─────────────────────────┘ │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ 📋 ITEMS TABLE (Scroll) │ │    │
│  │  │ ┌─────┬─────┬─────┐     │ │    │
│  │  │ │Name │QTY  │Amt  │     │ │    │
│  │  │ ├─────┼─────┼─────┤     │ │    │
│  │  │ │iPad │  2  │$950 │     │ │    │
│  │  │ │iPho │  1  │$800 │     │ │    │
│  │  │ │MacB │  3  │$540 │     │ │    │
│  │  │ └─────┴─────┴─────┘     │ │    │
│  │  │ ◄ Scroll Horizontal ►   │ │    │
│  │  └─────────────────────────┘ │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ 💰 SUMMARY CARDS        │ │    │
│  │  │ 🛒 Items: 6             │ │    │
│  │  │ 💰 Total: $2,519.00     │ │    │
│  │  └─────────────────────────┘ │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ 🎯 ACTION BUTTONS       │ │    │
│  │  │ 💾 Save │ 💰 Pay │ 🖨️ Print │ │    │
│  │  │ (Stacked vertically)    │ │    │
│  │  └─────────────────────────┘ │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

---

## 🎨 **Component Hierarchy**

```
Invoice.vue (Main Container)
├── Customer.vue
│   ├── v-autocomplete (Customer selection)
│   ├── v-btn (👁️ View Details)
│   ├── UpdateCustomer.vue (Modal)
│   └── CustomerDetail.vue (Modal)
│
├── PostingDateRow.vue
│   ├── v-text-field (Date picker)
│   └── Balance Display
│
├── MultiCurrencyRow.vue (Conditional)
│   ├── v-select (Currency dropdown)
│   └── v-text-field (Exchange rate)
│
├── ItemsTable.vue
│   ├── Column Selector Button
│   ├── v-data-table
│   │   ├── Custom Templates (per column)
│   │   └── Pagination
│   └── ColumnSelectorDialog.vue (Modal)
│
└── InvoiceSummary.vue
    ├── Summary Cards
    ├── Discount Section
    └── Action Buttons
```

---

## 🔄 **Data Flow & State Management**

```
┌─────────────────────────────────────┐
│         📊 STATE MANAGEMENT         │
│  ┌─────────────────────────────┐    │
│  │        🔄 REACTIVE DATA      │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ pos_profile: {           │ │    │
│  │  │   name: "Main POS",      │ │    │
│  │  │   currency: "USD",       │ │    │
│  │  │   ...                    │ │    │
│  │  │ }                        │ │    │
│  │  └─────────────────────────┘ │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ invoice_doc: {           │ │    │
│  │  │   name: "INV-001",       │ │    │
│  │  │   customer: "CUST-001",  │ │    │
│  │  │   items: [...],          │ │    │
│  │  │   ...                    │ │    │
│  │  │ }                        │ │    │
│  │  └─────────────────────────┘ │    │
│  │                                 │    │
│  │  ┌─────────────────────────┐ │    │
│  │  │ items: [                  │ │    │
│  │  │   {                       │ │    │
│  │  │     item_name: "iPad",    │ │    │
│  │  │     qty: 2,               │ │    │
│  │  │     rate: 500,            │ │    │
│  │  │     amount: 950           │ │    │
│  │  │   },                      │ │    │
│  │  │   ...                     │ │    │
│  │  │ ]                         │ │    │
│  │  └─────────────────────────┘ │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │      📡 EVENT BUS FLOW         │ │
│  │  ┌─────────────────────────┐    │ │
│  │  │ Component A ──emit───▶ │    │ │
│  │  │                        │    │ │
│  │  │ Event Bus (Central)     │    │ │
│  │  │                        │    │ │
│  │  │ Component B ◀──listen── │    │ │
│  │  └─────────────────────────┘    │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 🎯 **User Interaction Flow**

```
┌─────────────────────────────────────┐
│       🎯 USER WORKFLOW             │
│  ┌─────────────────────────────┐    │
│  │ 1. 👤 SELECT CUSTOMER        │    │
│  │    ↓                         │    │
│  │ 2. 📅 SET POSTING DATE       │    │
│  │    ↓                         │    │
│  │ 3. 💱 CHOOSE CURRENCY        │    │
│  │    ↓                         │    │
│  │ 4. 🛒 ADD ITEMS              │    │
│  │    ↓                         │    │
│  │ 5. 🔢 EDIT QUANTITIES        │    │
│  │    ↓                         │    │
│  │ 6. 💰 APPLY DISCOUNTS        │    │
│  │    ↓                         │    │
│  │ 7. 💳 PROCESS PAYMENT        │    │
│  │    ↓                         │    │
│  │ 8. 🖨️ SUBMIT & PRINT         │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

---

## 📐 **Detailed Component Layouts**

### **1. Customer Section Layout:**
```
┌─────────────────────────────────────┐
│         👤 CUSTOMER SECTION         │
├─────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────┐ │
│ │ 🔍 Customer     │ │ 👁️ Details  │ │
│ │ Dropdown        │ │ Button      │ │
│ │ ▼               │ │             │ │
│ └─────────────────┘ └─────────────┘ │
│                                     │
│ 💰 Customer Balance: $1,250.00      │
└─────────────────────────────────────┘
```

### **2. Items Table Layout:**
```
┌─────────────────────────────────────┐
│        📋 ITEMS TABLE               │
├─────────────────────────────────────┤
│ ⚙️ Columns [Top-Right Button]       │
├─────────────────────────────────────┤
│ ┌─────┬─────┬─────┬─────┬─────┐     │
│ │Name │QTY  │Rate │Disc │Amt  │     │
│ ├─────┼─────┼─────┼─────┼─────┤     │
│ │iPad │[2]  │$500 │5%  │$950 │     │
│ │iPho │[1]  │$800 │0%  │$800 │     │
│ │MacB │[3]  │$200 │10% │$540 │     │
│ └─────┴─────┴─────┴─────┴─────┘     │
│                                     │
│ 📄 1-3 of 3 items                   │
└─────────────────────────────────────┘
```

### **3. Summary & Actions Layout:**
```
┌─────────────────────────────────────┐
│    💰 SUMMARY & ACTIONS             │
├─────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│ │ 🛒 6     │ │ 💰 $2,290│ │ 🧾 $229 │ │
│ │ Items   │ │ Subtotal│ │ Tax     │ │
│ └─────────┘ └─────────┘ └─────────┘ │
├─────────────────────────────────────┤
│ 💸 Additional Discount: _________  │
├─────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
│ │💾   │ │💰   │ │🖨️   │ │🔄   │     │
│ │Save │ │Pay  │ │Print│ │Draft│     │
│ └─────┘ └─────┘ └─────┘ └─────┘     │
└─────────────────────────────────────┘
```

---

## 🎨 **CSS Grid & Flexbox Layout**

### **Main Container:**
```css
.invoice-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}
```

### **Customer Section:**
```css
.customer-input-wrapper {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}

.customer-input-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

/* Fixed spacing between Customer and Date sections */
.customer-section {
  margin-bottom: 5px;
}

.date-balance-section {
  margin-top: 5px;
}
```

### **Items Table:**
```css
.items-table-wrapper {
  flex: 1;
  overflow: auto;
  position: relative;
}

.column-selector-container {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 10;
}
```

### **Summary Cards:**
```css
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}
```

### **Action Buttons:**
```css
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  flex-wrap: wrap;
}
```

---

## 📱 **Responsive Breakpoints**

### **Desktop (xl/lg/md):**
- Full layout with all sections visible
- Items table with all columns
- Side-by-side customer input
- Horizontal action buttons

### **Tablet (sm):**
- Condensed layout
- Items table with essential columns only
- Stacked customer input
- Horizontal action buttons

### **Mobile (xs):**
- Single column layout
- Items table with horizontal scroll
- Stacked customer input
- Vertical action buttons
- Simplified summary cards

---

## 🎯 **Key Layout Features**

### ✅ **Visual Hierarchy:**
- **Headers** with distinct styling
- **Sections** with clear separation (5px spacing)
- **Color coding** for different data types
- **Typography scale** for importance
- **Fixed positioning** for Customer & Date sections

### ✅ **Interactive Elements:**
- **Hover states** for buttons
- **Focus indicators** for inputs
- **Loading states** for async operations
- **Error states** for validation

### ✅ **Accessibility:**
- **Keyboard navigation** support
- **Screen reader** compatibility
- **High contrast** mode support
- **Touch targets** minimum size

### ✅ **Performance:**
- **Virtual scrolling** for large tables
- **Lazy loading** for heavy components
- **Debounced inputs** for search
- **Optimized re-renders**

---

## 🚀 **Advanced Layout Features**

### **Dynamic Resizing:**
```javascript
// Invoice card height persistence
saveInvoiceHeight() {
  if (this.$refs.invoiceCard) {
    this.invoiceHeight = this.$refs.invoiceCard.clientHeight + "px";
    localStorage.setItem("posawesome_invoice_height", this.invoiceHeight);
  }
}
```

### **Column Customization:**
```javascript
// Save user column preferences
saveColumnPreferences() {
  localStorage.setItem("posawesome_selected_columns", JSON.stringify(this.selected_columns));
}
```

### **Theme Adaptation:**
```css
/* Dark theme adjustments */
:deep(.dark-theme) .cards {
  background-color: #121212 !important;
}

:deep(.dark-theme) .summary-card {
  background-color: #1e1e1e;
  border-color: #333;
}
```

---

## 🎉 **Layout Summary:**

**Right Panel Layout** được thiết kế với:

### ✅ **Structure:**
- **Modular Components** với clear separation
- **Responsive Grid** cho mọi screen size
- **Flexible Layout** với dynamic content
- **Consistent Spacing** và alignment
- **Fixed positioning** cho Customer & Date sections
- **5px spacing** giữa các sections chính
- **Read-only Date Picker** với thời gian đầy đủ

### ✅ **User Experience:**
- **Intuitive Flow** từ top to bottom
- **Progressive Disclosure** với modals
- **Contextual Actions** based on state
- **Visual Feedback** cho all interactions

### ✅ **Technical Excellence:**
- **Performance Optimized** với virtual scrolling
- **Accessibility Compliant** với ARIA support
- **Theme Agnostic** với CSS variables
- **Mobile First** responsive design

**Đây là layout hoàn hảo cho POS system với khả năng xử lý complex invoice workflows!** 🎯