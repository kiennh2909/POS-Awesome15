# 📱 **TỔNG QUAN LAYOUT ỨNG DỤNG POS-AWESOME**

## 🏗️ **Cấu Trúc Tổng Thể**

### **1. Root Component: Home.vue**
```javascript
<v-app class="container1">
  <v-main class="main-content">
    <Navbar />           // Navigation Bar
    <div class="page-content">
      <component v-bind:is="page" />  // Dynamic Page Content
    </div>
  </v-main>
</v-app>
```

---

## 🧭 **Navigation System (Navbar)**

### **Navbar.vue - Modular Structure:**
```javascript
<nav>
  <!-- App Bar với các thành phần -->
  <NavbarAppBar>
    <template #status-indicator>
      <StatusIndicator />      // Network/Server status
    </template>

    <template #cache-usage-meter>
      <CacheUsageMeter />      // Cache usage display
    </template>

    <template #menu>
      <NavbarMenu />          // Dropdown menu
    </template>
  </NavbarAppBar>

  <!-- Navigation Drawer -->
  <NavbarDrawer />

  <!-- Dialogs -->
  <AboutDialog />
  <OfflineInvoicesDialog />
</nav>
```

### **Navbar Components:**
- **NavbarAppBar**: Top app bar với logo, status, cache meter
- **NavbarDrawer**: Side navigation drawer
- **NavbarMenu**: Dropdown menu với các actions
- **StatusIndicator**: Network connectivity indicator
- **CacheUsageMeter**: Local storage usage meter

---

## 📄 **Main Pages (Dynamic Content)**

### **Available Pages:**
1. **POS** (Default) - Main POS interface
2. **Payments** - Payment management interface

### **Page Switching:**
```javascript
data: {
  page: "POS"  // or "Payments"
}
```

---

## 🏪 **POS Page Layout (Main Interface)**

### **Pos.vue - Two Column Layout:**
```javascript
<v-row dense class="ma-0 dynamic-main-row">
  <!-- Left Column (5/12) -->
  <v-col xl="5" lg="5" md="5" sm="5" cols="12">
    <!-- Dynamic Content Based on State -->
    <ItemsSelector />    // Default: Product selection
    <PosOffers />        // When offers active
    <PosCoupons />       // When coupons active
    <Payments />         // When payment active
  </v-col>

  <!-- Right Column (7/12) -->
  <v-col xl="7" lg="7" md="7" sm="7" cols="12">
    <Invoice />          // Invoice/Cart display
  </v-col>
</v-row>
```

### **POS Components:**
- **ItemsSelector**: Product catalog and search
- **Invoice**: Shopping cart and invoice details
- **Payments**: Payment processing interface
- **PosOffers**: Available offers and promotions
- **PosCoupons**: Coupon management

---

## 🛒 **Invoice/Cart Section (Right Panel)**

### **Invoice.vue Structure:**
```javascript
<div class="invoice-container">
  <!-- Customer Section -->
  <Customer />

  <!-- Items Table -->
  <div class="items-table-wrapper">
    <ItemsTable />
  </div>

  <!-- Invoice Summary -->
  <InvoiceSummary />

  <!-- Action Buttons -->
  <div class="invoice-actions">
    <SaveAndClearBtn />
    <PrintDraftBtn />
    <ReturnBtn />
    <SubmitBtn />
  </div>
</div>
```

### **Customer Component:**
```javascript
<div class="customer-input-wrapper">
  <div class="customer-input-row">
    <v-autocomplete />     // Customer dropdown
    <v-btn icon>👁️</v-btn> // View Details button
  </div>

  <!-- Modals -->
  <UpdateCustomer />      // Add/Edit customer
  <CustomerDetail />      // View customer details
</div>
```

---

## 📦 **Items Selection Section (Left Panel)**

### **ItemsSelector.vue Structure:**
```javascript
<div class="items-selector-container">
  <!-- Search and Filters -->
  <div class="search-section">
    <SearchBar />
    <CategoryFilters />
  </div>

  <!-- Items Grid/List -->
  <div class="items-grid">
    <ItemCard v-for="item in items" />
  </div>

  <!-- Pagination -->
  <PaginationControls />
</div>
```

---

## 💰 **Payments Page Layout**

### **Pay.vue - Three Section Layout:**
```javascript
<v-row>
  <!-- Left Panel: Outstanding Invoices & Payments -->
  <v-col md="8" cols="12">
    <Customer />           // Customer selection

    <!-- Outstanding Invoices Table -->
    <v-data-table :items="outstanding_invoices" />

    <!-- Unallocated Payments Table -->
    <v-data-table :items="unallocated_payments" />

    <!-- M-Pesa Payments -->
    <div v-if="pos_profile.posa_allow_mpesa_reconcile_payments">
      <MpesaPaymentsTable />
    </div>
  </v-col>

  <!-- Right Panel: Payment Summary & Actions -->
  <v-col md="4" cols="12">
    <div class="totals-section">
      <PaymentMethods />
      <DifferenceCalculator />
      <ActionButtons />
    </div>
  </v-col>
</v-row>
```

---

## 🎨 **UI Components & Modals**

### **Dialog System:**
- **OpeningDialog**: POS shift opening
- **ClosingDialog**: POS shift closing
- **Drafts**: Saved draft invoices
- **SalesOrders**: Sales order management
- **Returns**: Return invoice processing
- **NewAddress**: Address management
- **MpesaPayments**: M-Pesa payment processing
- **Variants**: Product variants selection
- **TaxRollDialog**: Tax calculations

### **Customer Detail Modal:**
```javascript
<v-dialog>
  <v-card class="customer-detail-dialog-card">
    <v-card-title>Customer Details</v-card-title>
    <v-card-text>
      <!-- Customer Information Table -->
      <v-data-table :items="customerInfoItems" />
    </v-card-text>
    <v-card-actions>
      <v-btn>Close</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

---

## 📱 **Responsive Design**

### **Breakpoint Strategy:**
```css
/* Extra Large (xl): 1200px+ */
<v-col xl="5" lg="5" md="5" sm="5" cols="12">

/* Large (lg): 992px - 1199px */
/* Medium (md): 768px - 991px */
/* Small (sm): 600px - 767px */
/* Extra Small (xs): <600px */
<v-col cols="12">
```

### **Mobile Optimizations:**
- **Single Column Layout** on small screens
- **Collapsible Navigation** drawer
- **Touch-Friendly** buttons and controls
- **Optimized Typography** for readability

---

## 🔄 **State Management & Communication**

### **Event Bus System:**
```javascript
// Component Communication
this.eventBus.emit("show_payment", true);
this.eventBus.emit("update_customer", customerData);
this.eventBus.emit("sync_invoices");

// Global State
this.eventBus.on("network-online", this.handleNetworkChange);
this.eventBus.on("server-online", this.handleServerChange);
```

### **Local Storage & Caching:**
- **IndexedDB**: Offline data storage
- **LocalStorage**: User preferences, settings
- **Cache Management**: Automatic cleanup and sync

---

## 🌐 **Network & Offline Support**

### **Connectivity Monitoring:**
```javascript
// Network Status Tracking
networkOnline: navigator.onLine
serverOnline: false
serverConnecting: false

// Auto-sync when online
watch: {
  networkOnline(newVal) {
    if (newVal) this.handleSyncInvoices();
  }
}
```

### **Offline Capabilities:**
- **Offline Invoice Creation**
- **Local Data Storage**
- **Background Sync**
- **Queue Management**

---

## 🎯 **Key Features Layout**

### **1. Customer Management:**
- Search and select customers
- View detailed customer information
- Add/edit customer details
- Credit limit management

### **2. Product Selection:**
- Category-based browsing
- Search and filter products
- Variant selection
- Stock level display

### **3. Cart Management:**
- Add/remove items
- Quantity adjustments
- Price calculations
- Discount applications

### **4. Payment Processing:**
- Multiple payment methods
- Outstanding invoice settlement
- Credit application
- Receipt generation

### **5. Offline Support:**
- Offline transaction creation
- Local data synchronization
- Network status monitoring
- Cache management

---

## 📊 **Layout Flow Summary**

```
┌─────────────────────────────────────────────────┐
│                    Navbar                       │
│  ┌─────────────────────────────────────────┐    │
│  │ App Bar | Status | Cache | Menu        │    │
│  └─────────────────────────────────────────┘    │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────┐ ┌─────────────────────┐    │
│  │   Left Panel    │ │    Right Panel      │    │
│  │                 │ │                     │    │
│  │ • Items         │ │ • Customer Info     │    │
│  │ • Categories    │ │ • Cart Items        │    │
│  │ • Search        │ │ • Invoice Summary   │    │
│  │ • Filters       │ │ • Action Buttons    │    │
│  │                 │ │                     │    │
│  └─────────────────┘ └─────────────────────┘    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │           Dialogs & Modals             │    │
│  │ • Customer Details • Opening Shift     │    │
│  │ • Payment Methods  • Draft Invoices    │    │
│  │ • Return Items     • Tax Calculations  │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

**🎉 Layout của POS-Awesome được thiết kế theo mô hình responsive, modular và user-friendly với khả năng hoạt động offline mạnh mẽ!**