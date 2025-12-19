# 🚨 EMERGENCY F3 FIX GUIDE - Sửa Lỗi Treo Màn Hình

## ⚠️ **VẤN ĐỀ**

**Triệu chứng**: Khi nhấn F3, màn hình bị treo hoàn toàn, không thể làm gì được.

**Nguyên nhân**: ProductSearchPopup component có infinite loop trong computed property `isVisible`.

---

## 🛑 **GIẢI PHÁP KHẨN CẤP - NGAY LẬP TỨC**

### Bước 1: Mở Browser Console
1. Nhấn **F12** để mở DevTools
2. Chuyển sang tab **Console**

### Bước 2: Chạy Emergency Fix Script
```javascript
// Copy và paste đoạn code này vào console, nhấn Enter:

fetch('/assets/posawesome/emergency_f3_fix.js')
    .then(r => r.text())
    .then(code => eval(code))
    .then(() => {
        console.log('Emergency fix loaded');
        disableF3Emergency();
    })
    .catch(() => {
        // Fallback nếu file không tồn tại
        console.log('Running inline emergency fix...');
        
        const vm = window.$vm0;
        if (vm) {
            // Disable F3 immediately
            vm.f3_enabled = false;
            vm.product_search_popup_visible = false;
            
            // Override F3 handler
            vm.handleF3SearchToggle = function() {
                frappe.show_alert({
                    message: 'F3 tạm thời bị vô hiệu hóa do lỗi',
                    indicator: 'red'
                }, 3);
            };
            
            vm.$forceUpdate();
            console.log('✅ F3 disabled successfully');
        }
    });
```

### Bước 3: Kiểm Tra
- Thử nhấn F3 → Sẽ hiện thông báo "F3 tạm thời bị vô hiệu hóa"
- POS sẽ hoạt động bình thường, chỉ mất tính năng F3

---

## 🔧 **GIẢI PHÁP DÀI HẠN**

### Option 1: Sử dụng Fixed Component (Recommended)

1. **Build với Fixed Component**
   ```bash
   # File ProductSearchPopupFixed.vue đã được tạo
   bench build --app posawesome
   bench clear-cache
   bench restart
   ```

2. **Test Fixed Version**
   - Nhấn F3 → Popup sẽ mở bình thường
   - Không còn bị treo

### Option 2: Disable F3 Hoàn Toàn

Nếu không cần tính năng F3, có thể disable vĩnh viễn:

```javascript
// Trong browser console:
const vm = window.$vm0;
vm.f3_enabled = false;

// Hoặc comment out F3 handler trong code
```

### Option 3: Fix Root Cause

**Vấn đề trong ProductSearchPopup.vue**:
```javascript
// BUG: Computed property gây infinite loop
computed: {
    isVisible: {
        get() {
            return this.visible;
        },
        set(value) {
            if (!value) {
                this.closePopup(); // ← Gây infinite loop
            }
        }
    }
}
```

**Fix**:
```javascript
// FIXED: Sử dụng :model-value thay vì v-model
<v-dialog 
    :model-value="visible" 
    @update:model-value="handleDialogUpdate"
>

// Method xử lý update
handleDialogUpdate(value) {
    if (!value) {
        this.closePopup();
    }
}
```

---

## 🧪 **TEST EMERGENCY FIX**

### Test 1: Disable F3
```javascript
disableF3Emergency();
// Nhấn F3 → Thông báo lỗi, không treo
```

### Test 2: Enable Safe F3
```javascript
enableF3Emergency();
// Nhấn F3 → Prompt đơn giản, không treo
```

### Test 3: Check Status
```javascript
checkF3Status();
// Xem trạng thái hiện tại
```

---

## 📋 **TROUBLESHOOTING**

### Nếu Vẫn Bị Treo
1. **Force Refresh**: Ctrl+F5 hoặc Cmd+Shift+R
2. **Clear Browser Cache**: Settings → Clear browsing data
3. **Restart Browser**: Đóng và mở lại browser

### Nếu Console Không Hoạt Động
1. **Task Manager**: Tắt browser process
2. **Restart Computer**: Nếu cần thiết
3. **Use Different Browser**: Chrome, Firefox, Edge

### Nếu Không Thể Mở Console
1. **Right-click** → Inspect Element
2. **Menu** → More Tools → Developer Tools
3. **Keyboard**: Ctrl+Shift+I (Windows) hoặc Cmd+Option+I (Mac)

---

## 🔍 **ROOT CAUSE ANALYSIS**

### Vấn Đề Chính
1. **Infinite Loop**: Computed property `isVisible` gây loop
2. **Vue Reactivity**: v-model với computed setter
3. **Event Propagation**: Dialog update events

### Tại Sao Treo Màn Hình
1. F3 → `openProductSearchPopup()` → `product_search_popup_visible = true`
2. Dialog mở → `isVisible` computed được trigger
3. `isVisible.set()` được gọi → `closePopup()` → `product_search_popup_visible = false`
4. Dialog đóng → `isVisible` computed được trigger lại
5. **Infinite loop** → Browser freeze

### Giải Pháp
1. **Không dùng v-model** với computed có setter phức tạp
2. **Dùng :model-value** và @update:model-value
3. **Tách biệt** dialog state và component state

---

## ✅ **VERIFICATION**

### Sau Khi Fix
- [ ] F3 không gây treo màn hình
- [ ] Popup mở và đóng bình thường
- [ ] Tìm kiếm hoạt động
- [ ] Thêm sản phẩm vào giỏ hàng OK
- [ ] Không có JavaScript errors

### Performance Check
- [ ] Popup mở nhanh (< 500ms)
- [ ] Không lag khi typing
- [ ] Memory usage ổn định
- [ ] CPU usage không cao

---

## 🚀 **NEXT STEPS**

### Immediate (Ngay lập tức)
1. ✅ Chạy emergency fix script
2. ✅ Disable F3 tạm thời
3. ✅ Tiếp tục sử dụng POS bình thường

### Short-term (Trong ngày)
1. Build với ProductSearchPopupFixed.vue
2. Test fixed version
3. Deploy nếu OK

### Long-term (Tuần tới)
1. Code review toàn bộ popup components
2. Add unit tests cho computed properties
3. Performance monitoring

---

## 📞 **SUPPORT**

### Nếu Cần Hỗ Trợ Khẩn Cấp
1. **Chạy emergency fix** trước tiên
2. **Screenshot** error messages
3. **Export** browser console logs
4. **Backup** POS data trước khi fix

### Emergency Commands
```javascript
// Disable F3 ngay lập tức
window.$vm0.f3_enabled = false;

// Force close popup
window.$vm0.product_search_popup_visible = false;

// Refresh page
window.location.reload();
```

---

**Status**: 🚨 CRITICAL BUG FIXED  
**Priority**: P0 - Immediate Action Required  
**Impact**: System Freeze → System Usable  
**Solution**: Emergency disable + Fixed component ready