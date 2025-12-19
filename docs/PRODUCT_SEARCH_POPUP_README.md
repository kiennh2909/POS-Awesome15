# 🔍 Product Search Popup - Hướng Dẫn Sử Dụng

## 📋 Tổng Quan

Product Search Popup là một tính năng tìm kiếm sản phẩm nâng cao, cho phép người dùng:
- Tìm kiếm sản phẩm theo mã, tên hoặc barcode
- Xem danh sách kết quả chi tiết với đầy đủ thông tin
- Chọn sản phẩm để thêm vào giỏ hàng
- Hiển thị thông tin tồn kho, giá, chiết khấu

## 🎯 Tính Năng Chính

### 1. Giao Diện Popup
- **Header**: Tiêu đề "Tìm Kiếm Sản Phẩm" với nút đóng
- **Search Input**: Ô tìm kiếm với placeholder hướng dẫn
- **Search Button**: Nút "Tìm kiếm" để thực hiện tìm kiếm
- **Results Table**: Bảng kết quả với các cột:
  - CHỌN: Nút chọn sản phẩm
  - TÊN SẢN PHẨM: Tên và mã sản phẩm
  - SL: Số lượng tồn kho
  - ĐVT: Đơn vị tính
  - ĐƠN GIÁ: Giá bán
  - CHIẾT KHẤU: Phần trăm chiết khấu
  - THÀNH TIỀN: Tổng tiền sau chiết khấu

### 2. Tìm Kiếm Thông Minh
- **Exact Barcode Match**: Ưu tiên barcode chính xác (score 100)
- **Partial Barcode Match**: Barcode chứa từ khóa (score 90)
- **SKU Starts-with**: Mã sản phẩm bắt đầu bằng từ khóa (score 80)
- **SKU Contains**: Mã sản phẩm chứa từ khóa (score 70)
- **Name Exact Match**: Tên sản phẩm chính xác (score 60)
- **Name Starts-with**: Tên bắt đầu bằng từ khóa (score 50)
- **Name Contains**: Tên chứa từ khóa (score 40)

### 3. Hiển Thị Kết Quả
- **Sắp xếp**: Theo điểm match_score giảm dần, sau đó theo tên
- **Giới hạn**: Tối đa 50 kết quả
- **Highlight**: Item được chọn có border màu xanh
- **Hover Effect**: Shadow và transform khi hover
- **Responsive**: Tự động điều chỉnh theo màn hình

## 🚀 Cách Sử Dụng

### Mở Popup
1. **Từ Search Input**: Click vào icon 🔍+ (magnify-plus-outline) màu cam
2. **Keyboard Shortcut**: Có thể thêm phím tắt (ví dụ: Ctrl+F)

### Tìm Kiếm
1. Nhập từ khóa vào ô tìm kiếm (tối thiểu 2 ký tự)
2. Nhấn Enter hoặc click nút "Tìm kiếm"
3. Chờ kết quả hiển thị (có loading indicator)

### Chọn Sản Phẩm
1. **Click vào nút "CHỌN"**: Thêm sản phẩm vào giỏ hàng
2. **Click vào row**: Highlight item (chuẩn bị chọn)
3. **Keyboard**: Có thể dùng ↑↓ để navigate (tùy chọn)

### Đóng Popup
1. **Click nút X**: Đóng popup
2. **Nhấn Esc**: Đóng popup
3. **Sau khi chọn sản phẩm**: Tự động đóng

## 🔧 Technical Implementation

### Frontend Component
**File**: `posawesome/public/js/posapp/components/pos/ProductSearchPopup.vue`

**Props**:
- `visible`: Boolean - Hiển thị/ẩn popup
- `posProfile`: Object - POS Profile hiện tại
- `priceList`: String - Price list đang dùng
- `customer`: String - Khách hàng (optional)

**Events**:
- `@close`: Đóng popup
- `@add-item`: Thêm sản phẩm vào giỏ hàng

**Methods**:
- `performSearch()`: Thực hiện tìm kiếm
- `searchProducts()`: Gọi API tìm kiếm
- `selectItem()`: Chọn item trong list
- `addToCart()`: Thêm item vào giỏ hàng
- `formatCurrency()`: Format tiền tệ
- `formatNumber()`: Format số
- `formatPercent()`: Format phần trăm

### Backend API
**File**: `posawesome/posawesome/api/items.py`

**Method**: `search_items_for_popup()`

**Parameters**:
- `search_term`: Từ khóa tìm kiếm
- `pos_profile`: POS Profile (JSON string hoặc name)
- `price_list`: Price list name
- `warehouse`: Warehouse name
- `limit`: Số lượng kết quả tối đa (default: 50)

**Returns**: List of items với các field:
```python
{
    "item_code": "ITEM-001",
    "item_name": "Product Name",
    "rate": 100000,
    "currency": "VND",
    "stock_uom": "Cái",
    "uom": "Cái",
    "actual_qty": 10,
    "available_qty": 8,
    "discount_percentage": 5.0,
    "item_barcode": [
        {"barcode": "8991818801601", "posa_uom": "Cái"}
    ],
    "match_score": 100,
    "custom_vat_rate": 10,
    "custom_price_list_rate_after_vat": 110000
}
```

### Integration với ItemsSelector
**File**: `posawesome/public/js/posapp/components/pos/ItemsSelector.vue`

**Import**:
```javascript
import ProductSearchPopup from "./ProductSearchPopup.vue";
```

**Component Registration**:
```javascript
components: {
    CameraScanner,
    ProductSearchPopup,
}
```

**Data**:
```javascript
product_search_popup_visible: false,
```

**Methods**:
```javascript
openProductSearchPopup() {
    this.product_search_popup_visible = true;
}

closeProductSearchPopup() {
    this.product_search_popup_visible = false;
    this.focusSearchInput();
}

async onPopupAddItem(item) {
    await this.add_item(item);
    frappe.show_alert({
        message: `Đã thêm: ${item.item_name}`,
        indicator: 'green'
    }, 2);
}
```

**Template**:
```vue
<ProductSearchPopup
    :visible="product_search_popup_visible"
    :pos-profile="pos_profile"
    :price-list="active_price_list"
    :customer="customer"
    @close="closeProductSearchPopup"
    @add-item="onPopupAddItem"
/>
```

## 📊 Database Query Optimization

### Query Features
- **LEFT JOIN**: Không bắt buộc barcode và stock
- **GROUP BY**: Gộp các barcode của cùng item
- **HAVING**: Filter theo match_score > 0
- **ORDER BY**: Sắp xếp theo score và tên
- **LIMIT**: Giới hạn kết quả

### Performance
- **Index**: Đảm bảo index trên:
  - `tabItem Price`: (price_list, selling, item_code)
  - `tabItem Barcode`: (barcode, parent)
  - `tabBin`: (item_code, warehouse)
- **Caching**: Có thể cache kết quả tìm kiếm
- **Debouncing**: Frontend debounce 500ms

## 🎨 UI/UX Design

### Colors
- **Primary**: Blue (#1976d2) - Nút chọn, border selected
- **Orange**: Orange - Icon popup button
- **Grey**: Grey lighten-5 - Header background
- **Success**: Green - Thông báo thành công
- **Error**: Red - Thông báo lỗi

### Typography
- **Header**: text-h6 (20px)
- **Product Name**: font-weight-medium (0.95rem)
- **Product Code**: text-caption (0.8rem)
- **Numbers**: font-weight-medium (0.9rem)

### Spacing
- **Card Padding**: 16px (pa-4)
- **Row Margin**: 8px (mb-2)
- **Column Padding**: 12px (pa-3)

### Responsive
- **Desktop**: Max-width 900px
- **Mobile**: Margin 16px, max-height 300px

## 🧪 Testing

### Manual Testing
1. **Tìm kiếm barcode chính xác**: Nhập barcode → Kết quả đầu tiên
2. **Tìm kiếm tên sản phẩm**: Nhập tên → Nhiều kết quả
3. **Tìm kiếm mã sản phẩm**: Nhập SKU → Kết quả chính xác
4. **Không có kết quả**: Nhập từ khóa không tồn tại → Thông báo
5. **Chọn sản phẩm**: Click CHỌN → Thêm vào giỏ hàng
6. **Đóng popup**: Esc hoặc X → Đóng và focus về search input

### Browser Console Testing
```javascript
// Test API directly
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

// Test popup open/close
$vm0.openProductSearchPopup();
$vm0.closeProductSearchPopup();
```

## 🚨 Troubleshooting

### Popup không mở
- Kiểm tra `product_search_popup_visible` state
- Kiểm tra component đã import đúng chưa
- Kiểm tra console có lỗi không

### Không có kết quả
- Kiểm tra API có trả về data không
- Kiểm tra Price List có items không
- Kiểm tra Warehouse có stock không
- Kiểm tra search_term có hợp lệ không

### Lỗi khi thêm vào giỏ hàng
- Kiểm tra item có đầy đủ thông tin không
- Kiểm tra UOM có hợp lệ không
- Kiểm tra Price có tồn tại không
- Xem console log để debug

### Performance chậm
- Giảm limit kết quả
- Thêm index vào database
- Cache kết quả tìm kiếm
- Optimize query

## 📝 Future Enhancements

1. **Keyboard Navigation**: ↑↓ để navigate, Enter để chọn
2. **Image Preview**: Hiển thị ảnh sản phẩm
3. **Quick Add**: Double-click để thêm nhanh
4. **Recent Searches**: Lưu lịch sử tìm kiếm
5. **Filters**: Filter theo nhóm hàng, brand, etc.
6. **Export**: Export kết quả ra Excel
7. **Barcode Scanner**: Scan barcode trong popup
8. **Multi-select**: Chọn nhiều sản phẩm cùng lúc

## ✅ Checklist Triển Khai

- [x] Tạo ProductSearchPopup.vue component
- [x] Thêm API search_items_for_popup()
- [x] Tích hợp vào ItemsSelector.vue
- [x] Thêm button mở popup
- [x] Thêm methods xử lý popup
- [x] Test tìm kiếm cơ bản
- [ ] Test trên mobile
- [ ] Test performance với nhiều items
- [ ] Thêm keyboard shortcuts
- [ ] Thêm unit tests
- [ ] Cập nhật user documentation

## 📚 References

- **Frappe Framework**: https://frappeframework.com/
- **Vuetify 3**: https://vuetifyjs.com/
- **POS Awesome**: https://github.com/yrestom/POS-Awesome

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-19  
**Author**: Kiro AI Assistant
