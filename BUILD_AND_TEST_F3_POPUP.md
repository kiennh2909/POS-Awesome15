# 🚀 Build và Test F3 Popup - Hướng Dẫn Chi Tiết

## 📋 **Chuẩn Bị**

### Kiểm Tra Files Đã Có
- ✅ `posawesome/public/js/posapp/components/pos/ProductSearchPopup.vue`
- ✅ `posawesome/posawesome/api/items.py` (có method `search_items_for_popup`)
- ✅ `posawesome/public/js/posapp/components/pos/ItemsSelector.vue` (đã integrate)

---

## 🔧 **BƯỚC 1: Build Frontend**

### Option 1: Build Production
```bash
# Navigate to frappe-bench directory
cd /path/to/frappe-bench

# Build posawesome app
bench build --app posawesome

# Wait for build to complete (may take 2-5 minutes)
```

### Option 2: Watch Mode (Recommended for Development)
```bash
# Start watch mode for faster development
bench watch

# Keep this running in a separate terminal
# It will auto-rebuild when files change
```

---

## 🧹 **BƯỚC 2: Clear Cache**

```bash
# Clear all caches
bench clear-cache

# Clear website cache
bench clear-website-cache

# Optional: Clear Redis cache
bench redis-cache-clear
```

---

## 🔄 **BƯỚC 3: Restart Services**

```bash
# Restart all services
bench restart

# Or restart specific services
bench restart web
bench restart worker
```

---

## 🌐 **BƯỚC 4: Access POS Page**

1. Open browser
2. Navigate to your Frappe site
3. Go to POS module
4. Open POS interface

---

## 🧪 **BƯỚC 5: Test F3 Popup**

### 5.1. Quick Visual Test

1. **Press F3 key**
   - ✅ Popup should open
   - ✅ Should see "Tìm Kiếm Sản Phẩm" title
   - ✅ Should see search input field

2. **Test Search**
   - Type "test" in search input
   - Press Enter or click "Tìm kiếm"
   - ✅ Should see loading indicator
   - ✅ Should see results or "no results" message

3. **Test Close**
   - Click X button or press Esc
   - ✅ Popup should close

### 5.2. Browser Console Test

Open browser DevTools (F12) and run:

```javascript
// Load test script
fetch('/assets/posawesome/test_f3_popup_simple.js')
    .then(r => r.text())
    .then(code => eval(code))
    .then(() => {
        console.log('Test script loaded');
        runAllTests();
    });
```

### 5.3. Manual Console Test

```javascript
// Check if popup works
console.log('Testing F3 popup...');

// Test 1: Check component exists
console.log('Component exists:', !!$vm0.$options.components.ProductSearchPopup);

// Test 2: Test open popup
$vm0.openProductSearchPopup();
console.log('Popup visible:', $vm0.product_search_popup_visible);

// Test 3: Test F3 key
$vm0.handleF3SearchToggle();

// Test 4: Test API
frappe.call({
    method: "posawesome.posawesome.api.items.search_items_for_popup",
    args: {
        search_term: "test",
        pos_profile: JSON.stringify($vm0.pos_profile),
        price_list: $vm0.active_price_list,
        customer: null,
        limit: 5
    },
    callback: (r) => console.log('API result:', r)
});
```

---

## 🐛 **TROUBLESHOOTING**

### Issue 1: Popup không mở khi nhấn F3

**Possible Causes:**
- Frontend chưa được build
- Component chưa được load
- F3 bị disable

**Solutions:**
```bash
# Rebuild frontend
bench build --app posawesome

# Clear cache
bench clear-cache

# Restart
bench restart
```

**Console Debug:**
```javascript
// Check F3 handler
console.log('F3 enabled:', $vm0.f3_enabled);
console.log('F3 method exists:', typeof $vm0.handleF3SearchToggle);

// Force enable F3
$vm0.f3_enabled = true;

// Test F3 manually
$vm0.handleF3SearchToggle();
```

### Issue 2: Popup mở nhưng bị treo

**Possible Causes:**
- Props không được truyền đúng
- API chưa sẵn sàng
- JavaScript errors

**Solutions:**
```javascript
// Check props
console.log('pos_profile:', $vm0.pos_profile);
console.log('price_list:', $vm0.active_price_list);

// Force close and reopen
$vm0.product_search_popup_visible = false;
setTimeout(() => {
    $vm0.product_search_popup_visible = true;
    $vm0.$forceUpdate();
}, 500);
```

### Issue 3: API không hoạt động

**Possible Causes:**
- Method chưa được load
- Permission issues
- Server chưa restart

**Solutions:**
```bash
# Restart server
bench restart

# Check logs
bench logs
```

**Console Debug:**
```javascript
// Test API directly
frappe.call({
    method: "posawesome.posawesome.api.items.search_items_for_popup",
    args: {
        search_term: "test",
        pos_profile: "{}",
        price_list: "Standard Selling",
        limit: 5
    },
    callback: (r) => console.log('Success:', r),
    error: (e) => console.error('Error:', e)
});
```

### Issue 4: Search không trả về kết quả

**Possible Causes:**
- Không có data trong database
- Price list không đúng
- Warehouse không có stock

**Solutions:**
```javascript
// Check data
console.log('Items count:', $vm0.items?.length);
console.log('Price list:', $vm0.active_price_list);

// Test with different search terms
// Try: "item", "product", or actual item codes from your system
```

### Issue 5: Component không được load

**Possible Causes:**
- Import path sai
- Component registration sai
- Build lỗi

**Solutions:**
```bash
# Check build logs
bench build --app posawesome --verbose

# Check for JavaScript errors in browser console
```

**Console Debug:**
```javascript
// Check component registration
console.log('Components:', Object.keys($vm0.$options.components));
console.log('ProductSearchPopup:', $vm0.$options.components.ProductSearchPopup);
```

---

## ✅ **SUCCESS CRITERIA**

### Minimum Working Requirements

1. **F3 Key Works**
   - Press F3 → Popup opens
   - No JavaScript errors in console

2. **Popup Displays Correctly**
   - Title: "Tìm Kiếm Sản Phẩm"
   - Search input field visible
   - "Tìm kiếm" button visible

3. **Search Functions**
   - Type search term → Press Enter
   - Loading indicator shows
   - Results display (or "no results" message)

4. **Close Functions**
   - Click X → Popup closes
   - Press Esc → Popup closes

### Full Feature Requirements

1. **Search Results Display**
   - Table with columns: CHỌN, TÊN SẢN PHẨM, SL, ĐVT, ĐƠN GIÁ, CHIẾT KHẤU, THÀNH TIỀN
   - Click "CHỌN" → Item added to cart
   - Popup closes after adding item

2. **Error Handling**
   - Invalid search terms → Error message
   - API errors → User-friendly error message
   - Empty results → "Không tìm thấy sản phẩm"

3. **Performance**
   - Popup opens quickly (< 500ms)
   - Search results load quickly (< 2s)
   - No lag or freezing

---

## 📊 **TESTING CHECKLIST**

### Basic Functionality
- [ ] F3 opens popup
- [ ] Popup displays correctly
- [ ] Search input works
- [ ] Search button works
- [ ] Close button works
- [ ] Esc key closes popup

### Search Functionality
- [ ] Valid search returns results
- [ ] Invalid search shows error
- [ ] Empty search shows validation
- [ ] Loading indicator works
- [ ] Results display in table format

### Add to Cart
- [ ] Click "CHỌN" adds item
- [ ] Success message shows
- [ ] Popup closes after adding
- [ ] Item appears in cart

### Error Handling
- [ ] API errors show user message
- [ ] Network errors handled gracefully
- [ ] Invalid props don't crash app

### Performance
- [ ] Popup opens quickly
- [ ] Search is responsive
- [ ] No memory leaks
- [ ] Works on mobile

---

## 🎯 **EXPECTED RESULT**

After successful implementation:

1. **User presses F3** → Popup opens instantly
2. **User types search term** → Auto-search or manual search
3. **Results display** → Table with product information
4. **User clicks CHỌN** → Item added to cart, popup closes
5. **Smooth workflow** → No errors, fast performance

---

## 📞 **SUPPORT**

If you encounter issues:

1. **Check browser console** for JavaScript errors
2. **Check network tab** for API call failures
3. **Run test script** to diagnose specific issues
4. **Check server logs** for backend errors

**Test Script Command:**
```javascript
fetch('/assets/posawesome/test_f3_popup_simple.js')
    .then(r => r.text())
    .then(code => eval(code))
    .then(() => runAllTests());
```

---

**Last Updated**: 2024-12-19  
**Status**: Ready for Build and Test  
**Next Action**: Run `bench build --app posawesome`