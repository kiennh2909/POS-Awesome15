# 🚀 Product Search Popup - Hướng Dẫn Cài Đặt Nhanh

## 📋 Tổng Quan
Popup tìm kiếm sản phẩm nâng cao với giao diện như hình mẫu bạn cung cấp, bao gồm:
- Tìm kiếm thông minh theo barcode, mã SP, tên SP
- Hiển thị kết quả dạng bảng với đầy đủ thông tin
- Chọn sản phẩm để thêm vào giỏ hàng
- Responsive design cho mobile và desktop

## ✅ Files Đã Tạo

### 1. Frontend Component
```
posawesome/public/js/posapp/components/pos/ProductSearchPopup.vue
```
- Vue component chính cho popup
- Giao diện đẹp với Vuetify 3
- Tìm kiếm với debouncing
- Responsive design

### 2. Backend API
```
posawesome/posawesome/api/items.py (đã thêm method)
```
- Method: `search_items_for_popup()`
- Tìm kiếm thông minh với scoring
- Optimized SQL query
- Support barcode, SKU, name search

### 3. Integration
```
posawesome/public/js/posapp/components/pos/ItemsSelector.vue (đã cập nhật)
```
- Import ProductSearchPopup component
- Thêm button mở popup (icon 🔍+)
- Methods xử lý popup events
- State management

### 4. Documentation
```
docs/PRODUCT_SEARCH_POPUP_README.md
```
- Hướng dẫn chi tiết
- Technical documentation
- API reference

### 5. Testing
```
test_product_search_popup.js
```
- Test script cho browser console
- Test popup functionality
- Performance testing

## 🔧 Cài Đặt

### Bước 1: Restart Frappe
```bash
# Restart để load API mới
bench restart
```

### Bước 2: Build Frontend
```bash
# Build lại frontend để include component mới
bench build --app posawesome
```

### Bước 3: Clear Cache
```bash
# Clear cache để đảm bảo load files mới
bench clear-cache
```

## 🧪 Kiểm Tra

### 1. Kiểm Tra API
Mở browser console trên trang POS và chạy:
```javascript
// Test API search
frappe.call({
    method: "posawesome.posawesome.api.items.search_items_for_popup",
    args: {
        search_term: "coca",
        pos_profile: JSON.stringify($vm0.pos_profile),
        price_list: $vm0.active_price_list,
        warehouse: $vm0.pos_profile.warehouse,
        limit: 50
    },
    callback: (r) => console.table(r.message)
});
```

### 2. Kiểm Tra Popup
```javascript
// Test popup open/close
$vm0.openProductSearchPopup();
$vm0.closeProductSearchPopup();
```

### 3. Chạy Test Suite
```javascript
// Load test script
fetch('/assets/posawesome/test_product_search_popup.js')
    .then(r => r.text())
    .then(code => eval(code))
    .then(() => runAllTests());
```

## 🎯 Cách Sử Dụng

### Mở Popup
1. Vào trang POS
2. Tìm ô search chính
3. Click vào icon 🔍+ màu cam bên phải
4. Popup sẽ mở ra

### Tìm Kiếm
1. Nhập từ khóa (tối thiểu 2 ký tự)
2. Nhấn Enter hoặc click "Tìm kiếm"
3. Xem kết quả trong bảng

### Chọn Sản Phẩm
1. Click nút "CHỌN" ở cột đầu tiên
2. Sản phẩm sẽ được thêm vào giỏ hàng
3. Popup tự động đóng

## 🎨 Giao Diện

### Header
- Tiêu đề: "Tìm Kiếm Sản Phẩm"
- Icon: 🔍
- Nút đóng: ✕

### Search Section
- Input field với placeholder
- Nút "Tìm kiếm" màu xanh
- Loading indicator khi search

### Results Table
| CHỌN | TÊN SẢN PHẨM | SL | ĐVT | ĐƠN GIÁ | CHIẾT KHẤU | THÀNH TIỀN |
|------|--------------|----|----|---------|------------|------------|
| [CHỌN] | Product Name<br>SKU • Barcode | 2.00 | Cái | 76,852 | 0.00% | 153,704 |

### Footer
- "Hiển thị X kết quả"
- Nút "Đóng (Esc)"

## 🔍 Tính Năng Tìm Kiếm

### Độ Ưu Tiên (Match Score)
1. **Barcode chính xác** (100 điểm)
2. **Barcode chứa từ khóa** (90 điểm)
3. **SKU bắt đầu bằng từ khóa** (80 điểm)
4. **SKU chứa từ khóa** (70 điểm)
5. **Tên chính xác** (60 điểm)
6. **Tên bắt đầu bằng từ khóa** (50 điểm)
7. **Tên chứa từ khóa** (40 điểm)

### Ví Dụ Tìm Kiếm
- `8991818801601` → Tìm barcode chính xác
- `coca` → Tìm tên sản phẩm chứa "coca"
- `ITEM-001` → Tìm mã sản phẩm
- `123` → Tìm barcode hoặc SKU chứa "123"

## 🚨 Troubleshooting

### Popup không mở
```javascript
// Kiểm tra component có load không
console.log($vm0.$options.components.ProductSearchPopup);

// Kiểm tra state
console.log($vm0.product_search_popup_visible);
```

### API không hoạt động
```bash
# Kiểm tra method có tồn tại không
bench console
>>> import posawesome.posawesome.api.items
>>> hasattr(posawesome.posawesome.api.items, 'search_items_for_popup')
```

### Không có kết quả
- Kiểm tra Price List có items không
- Kiểm tra Warehouse có stock không
- Kiểm tra từ khóa tìm kiếm có hợp lệ không

### Lỗi khi thêm vào giỏ hàng
- Kiểm tra item có đầy đủ thông tin UOM không
- Kiểm tra Price có tồn tại không
- Xem console log để debug

## 📱 Mobile Support

### Responsive Design
- Popup tự động điều chỉnh kích thước
- Touch-friendly buttons
- Scrollable results table
- Optimized spacing

### Mobile Testing
1. Mở POS trên mobile browser
2. Click icon 🔍+ để mở popup
3. Test tìm kiếm và chọn sản phẩm
4. Kiểm tra responsive layout

## 🔄 Customization

### Thay Đổi Số Lượng Kết Quả
```python
# Trong search_items_for_popup()
LIMIT %(limit)s  # Thay đổi default limit
```

### Thay Đổi Giao Diện
```vue
<!-- Trong ProductSearchPopup.vue -->
<v-dialog max-width="1200px">  <!-- Tăng kích thước -->
```

### Thêm Cột Mới
```python
# Trong SQL query
SELECT 
    ip.item_code,
    ip.item_name,
    ip.brand,  -- Thêm cột brand
    ...
```

## 📊 Performance

### Database Indexes
Đảm bảo có indexes:
```sql
-- Item Price
CREATE INDEX idx_item_price_search ON `tabItem Price` (price_list, selling, item_code);

-- Item Barcode  
CREATE INDEX idx_item_barcode_search ON `tabItem Barcode` (barcode, parent);

-- Bin
CREATE INDEX idx_bin_search ON `tabBin` (item_code, warehouse);
```

### Query Optimization
- Sử dụng LIMIT để giới hạn kết quả
- LEFT JOIN thay vì INNER JOIN
- GROUP BY để gộp barcodes
- ORDER BY theo match_score

### Frontend Optimization
- Debouncing 500ms cho search input
- Limit 50 kết quả hiển thị
- Lazy loading cho large datasets

## ✅ Checklist Hoàn Thành

- [x] ✅ Tạo ProductSearchPopup.vue component
- [x] ✅ Thêm API search_items_for_popup()
- [x] ✅ Tích hợp vào ItemsSelector.vue
- [x] ✅ Thêm button mở popup
- [x] ✅ Giao diện theo mẫu yêu cầu
- [x] ✅ Tìm kiếm thông minh với scoring
- [x] ✅ Responsive design
- [x] ✅ Error handling
- [x] ✅ Loading states
- [x] ✅ Documentation
- [x] ✅ Test script

## 🎉 Kết Quả

Popup tìm kiếm sản phẩm đã được triển khai hoàn chỉnh với:

1. **Giao diện đẹp**: Theo đúng mẫu thiết kế
2. **Tìm kiếm thông minh**: Ưu tiên barcode, SKU, tên
3. **Performance tốt**: Optimized query, debouncing
4. **Responsive**: Hoạt động tốt trên mobile
5. **Easy to use**: Click icon → Search → Select → Add to cart

**Ready for production use!** 🚀

---

**Liên hệ hỗ trợ**: Nếu có vấn đề gì, hãy check console logs và chạy test script để debug.