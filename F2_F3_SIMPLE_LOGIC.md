# Logic Đơn Giản F2 và F3

## 🎯 Yêu Cầu Đơn Giản

### F2: Barcode Mode + Focus
- **Chức năng**: Chuyển về chế độ Barcode và focus vào ô tìm kiếm
- **Kết quả**: Sẵn sàng quét/nhập barcode để thêm vào giỏ hàng

### F3: Text Search Mode (Chỉ Xem Kết Quả)
- **Chức năng**: Chuyển sang chế độ tìm kiếm text
- **Kết quả**: CHỈ XEM kết quả, KHÔNG cho phép thêm vào giỏ hàng
- **Mục đích**: Tránh nhầm lẫn, chỉ để tìm kiếm và xem thông tin

## 🔄 Luồng Hoạt Động Mới

### F2 - Barcode Mode
```
F2 → Barcode Mode → Focus → Quét/Nhập Barcode → Thêm Trực Tiếp Vào Giỏ Hàng
```

### F3 - Text Search Mode (With Confirmation)
```
F3 → Text Search Mode → Nhập Text → Enter → Hiển thị Kết Quả → Click Item → Product Confirmation Popup → Xác Nhận → Thêm Vào Giỏ Hàng
```

### Quay Về Bán Hàng
```
F2 → Barcode Mode → Sẵn sàng bán hàng
```

## 📋 Chi Tiết Implementation

### F2 Logic
```javascript
handleF2Reset() {
    // 1. Hide all popups and results
    this.hideSearchResults();
    this.hideProductConfirmation();
    
    // 2. ALWAYS switch to barcode mode
    this.search_mode = 'barcode';
    
    // 3. Clear search and focus
    this.clearSearch();
    this.focusSearchInput();
    
    // 4. Show feedback
    frappe.show_alert({
        message: 'F2: Chế độ Barcode + Focus',
        indicator: 'primary'
    }, 1);
}
```

### F3 Logic
```javascript
handleF3SearchToggle() {
    // 1. Hide all popups and results
    this.hideSearchResults();
    this.hideProductConfirmation();
    
    // 2. ALWAYS switch to text mode
    this.search_mode = 'text';
    
    // 3. Clear search and focus
    this.clearSearch();
    this.focusSearchInput();
    
    // 4. Show feedback
    frappe.show_alert({
        message: 'F3: Chế độ Tìm kiếm Text (click để chọn → xác nhận)',
        indicator: 'orange'
    }, 2);
}
```

### Text Search Logic (With Confirmation)
```javascript
handleTextSearchEnter() {
    const results = await this.searchItemsByText(searchTerm);
    
    if (results.length === 1) {
        // Single result - show confirmation popup directly
        this.showProductConfirmation(results[0]);
    } else if (results.length > 1) {
        // Multiple results - show list for selection
        this.showSearchResults(results, false); // false = allow selection
        frappe.show_alert({
            message: `Tìm thấy ${results.length} sản phẩm. Click để chọn.`,
            indicator: 'blue'
        }, 3);
    }
}
```

### Product Selection with Confirmation
```javascript
selectSearchResult(index) {
    // Always allow selection in Text Search mode
    this.selected_result_index = index;
    this.selectCurrentResult();
}

selectCurrentResult() {
    const selectedItem = this.search_results[this.selected_result_index];
    
    // Always show product confirmation popup when selecting from search results
    this.showProductConfirmation(selectedItem);
}
```

## 🎨 Visual Feedback

### F2 Mode (Barcode)
- **Border**: Blue (Primary)
- **Icon**: Barcode scan icon
- **Message**: "F2: Chế độ Barcode + Focus"
- **Behavior**: Thêm trực tiếp vào giỏ hàng

### F3 Mode (Text Search - With Confirmation)
- **Border**: Orange
- **Icon**: Search icon
- **Message**: "F3: Chế độ Tìm kiếm Text (click để chọn → xác nhận)"
- **Behavior**: Hiển thị kết quả → Click item → Product Confirmation Popup → Xác nhận → Thêm vào giỏ hàng

### Search Results in F3 Mode
- **Header**: "Tìm thấy X sản phẩm"
- **Background**: Normal (blue border)
- **Cursor**: Pointer (clickable)
- **Hint**: "Click để chọn • Esc: Đóng"

## 🚫 Ngăn Chặn Nhầm Lẫn

### 1. Visual Cues
- Màu sắc khác nhau (Blue vs Orange)
- Icon khác nhau (Barcode vs Search)
- Cursor not-allowed trong F3 mode

### 2. User Feedback
- Thông báo rõ ràng về chế độ hiện tại
- Hướng dẫn cách quay về chế độ bán hàng (F2)
- Ngăn chặn click vào kết quả trong F3 mode

### 3. Consistent Behavior
- F2 luôn về Barcode mode
- F3 luôn về Text search mode (view only)
- Không có toggle, chỉ có switch trực tiếp

## 📊 Comparison Table

| Phím | Chế Độ | Màu Sắc | Chức Năng | Thêm Vào Giỏ Hàng? |
|------|---------|----------|-----------|---------------------|
| F2 | Barcode | Blue | Quét/Nhập Barcode | ✅ Trực tiếp |
| F3 | Text Search | Orange | Tìm kiếm + Xem | ❌ Không được |

## 🎯 User Journey

### Scenario 1: Bán Hàng Bình Thường
1. **F2** → Barcode mode
2. Quét barcode → Thêm vào giỏ hàng
3. Tiếp tục quét → Thêm tiếp

### Scenario 2: Tìm Kiếm Thông Tin Sản Phẩm
1. **F3** → Text search mode
2. Nhập tên sản phẩm → Enter
3. Xem kết quả (không thêm được)
4. **F2** → Quay về bán hàng

### Scenario 3: Từ Tìm Kiếm Về Bán Hàng
1. Đang ở F3 mode (xem kết quả)
2. **F2** → Chuyển về Barcode mode
3. Sẵn sàng bán hàng

## ✅ Kết Quả Đạt Được

1. **Logic đơn giản**: F2 = Bán hàng, F3 = Tìm kiếm
2. **Không nhầm lẫn**: F3 chỉ xem, không thêm được vào giỏ hàng
3. **Workflow rõ ràng**: F2 để về bán hàng, F3 để tìm kiếm
4. **Visual feedback**: Màu sắc và icon khác nhau
5. **User guidance**: Thông báo rõ ràng về cách sử dụng