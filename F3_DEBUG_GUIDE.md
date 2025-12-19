# Hướng Dẫn Debug Vấn Đề F3

## Vấn Đề
F3 thỉnh thoảng không chuyển sang chế độ Text Search, thỉnh thoảng lại hoạt động bình thường.

## Nguyên Nhân Có Thể
1. **Method trùng lặp** - Đã được fix bởi Kiro IDE autofix
2. **Biến f3_enabled bị conflict** - Đã kiểm tra, chỉ có 1 nơi khởi tạo
3. **Event listener bị conflict** - Cần kiểm tra
4. **NumPad disable/enable không đúng** - Đã thêm debug log

## Debug Logs Đã Thêm

### 1. Global Key Handler
```javascript
// Log khi F3 được nhấn
if (event.key === 'F3') {
    console.info('[Global] F3 pressed, numpad_visible:', this.numpad_visible, 
        'product_numpad_visible:', this.product_numpad_visible,
        'product_confirmation_visible:', this.product_confirmation_visible);
}
```

### 2. Handle Key Down
```javascript
// Log khi F3 được xử lý
if (event.key === 'F3') {
    console.info('[handleKeyDown] F3 pressed');
}

case 'F3':
    console.info('[handleKeyDown] Calling handleF3SearchToggle');
    this.handleF3SearchToggle();
    break;
```

### 3. Handle F3 Search Toggle
```javascript
handleF3SearchToggle() {
    console.info('[F3] handleF3SearchToggle called, f3_enabled:', this.f3_enabled);
    if (!this.f3_enabled) {
        console.warn('[F3] F3 is disabled, ignoring');
        return;
    }
    
    console.info('[F3] Toggling search mode from:', this.search_mode);
    // ... rest of method
}
```

### 4. NumPad Show/Hide
```javascript
showNumPad() {
    console.info('[NumPad] Disabling F2/F3, before - f3_enabled:', this.f3_enabled);
    this.f3_enabled = false;
    console.info('[NumPad] After disable - f3_enabled:', this.f3_enabled);
}

hideNumPad() {
    console.info('[NumPad] Re-enabling F2/F3, before - f3_enabled:', this.f3_enabled);
    this.f3_enabled = true;
    console.info('[NumPad] After enable - f3_enabled:', this.f3_enabled);
}
```

## Cách Test

### 1. Test Cơ Bản
1. Mở Developer Console (F12)
2. Nhấn F3 nhiều lần
3. Quan sát console logs:
   - `[Global] F3 pressed` - F3 được detect
   - `[handleKeyDown] F3 pressed` - F3 được route đúng
   - `[handleKeyDown] Calling handleF3SearchToggle` - Method được gọi
   - `[F3] handleF3SearchToggle called, f3_enabled: true` - Method chạy
   - `[F3] Toggling search mode from: barcode` - Mode được toggle

### 2. Test Với NumPad
1. Click vào QTY input để mở NumPad
2. Quan sát: `[NumPad] After disable - f3_enabled: false`
3. Nhấn F3 → Sẽ thấy: `[F3] F3 is disabled, ignoring`
4. Đóng NumPad
5. Quan sát: `[NumPad] After enable - f3_enabled: true`
6. Nhấn F3 → Sẽ hoạt động bình thường

### 3. Test Với Product Confirmation
1. Tìm kiếm sản phẩm → Chọn sản phẩm → Mở popup xác nhận
2. Nhấn F3 → Sẽ thấy log về product_confirmation_visible
3. Đóng popup
4. Nhấn F3 → Sẽ hoạt động bình thường

## Các Trường Hợp F3 Bị Disable

### 1. Khi NumPad Mở
- `this.numpad_visible = true`
- `this.f3_enabled = false`
- F3 sẽ bị ignore

### 2. Khi Product NumPad Mở  
- `this.product_numpad_visible = true`
- F3 sẽ được handle bởi `handleNumPadKeyboard()`

### 3. Khi Product Confirmation Mở
- `this.product_confirmation_visible = true`
- F3 sẽ được handle bởi product confirmation logic

## Giải Pháp Nếu Vẫn Có Vấn Đề

### 1. Kiểm tra Event Listener Trùng Lặp
```javascript
// Thêm vào mounted()
console.info('[Mounted] Adding global keyboard listener');

// Thêm vào beforeUnmount()
console.info('[Unmount] Removing global keyboard listener');
```

### 2. Kiểm tra Focus State
```javascript
// Thêm vào handleF3SearchToggle()
console.info('[F3] Current focus element:', document.activeElement);
console.info('[F3] Search input ref:', this.$refs.searchInput);
```

### 3. Force Enable F3
```javascript
// Thêm method debug
forceEnableF3() {
    console.info('[Debug] Force enabling F3');
    this.f3_enabled = true;
    this.f2_enabled = true;
}
```

## Kết Quả Mong Đợi
Sau khi thêm debug logs, sẽ thấy rõ:
- F3 có được detect không
- f3_enabled có đúng trạng thái không  
- Method handleF3SearchToggle có được gọi không
- Search mode có được toggle không

Nếu vẫn có vấn đề, debug logs sẽ chỉ ra chính xác bước nào bị lỗi.