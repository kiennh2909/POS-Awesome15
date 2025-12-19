# 🔢 Item Edit NumPad - Hướng Dẫn Tích Hợp

## 📋 Tổng Quan

Tính năng **Item Edit NumPad** cho phép người dùng click vào một item trong giỏ hàng và sử dụng NumPad popup để chỉnh sửa:
- **Số lượng (QTY)**
- **Đơn giá (RATE)**
- **Chiết khấu (DISCOUNT %)**

## 🎯 Hành Vi Theo Yêu Cầu

### 1. Click vào Item = Chọn Context
- Click vào dòng item → Item được SELECT
- Các dòng khác bỏ highlight
- NumPad popup mở ra

### 2. Auto-Focus Trường Mặc Định
- **Mặc định**: Focus vào QTY (Số lượng)
- Lý do: 80-90% thao tác là chỉnh số lượng
- Thu ngân không phải nghĩ

### 3. NumPad Hoạt Động
- Mọi phím NumPad (UI & vật lý) nhập trực tiếp vào field đang chọn
- Hỗ trợ keyboard shortcuts

### 4. Nhập Số Mới
- Bấm số (0-9) → Ghi đè toàn bộ giá trị cũ
- Không append (tránh nhầm)
- Ví dụ: QTY = 5, bấm 2 → QTY = 2 (không phải 52)

### 5. Phím +/-
- `+` → Tăng 1 (hoặc step cấu hình)
- `-` → Giảm 1
- Không xuống dưới 0

### 6. Enter
- Xác nhận giá trị
- Giữ SELECT item
- NumPad vẫn active (có thể chỉnh tiếp)

### 7. Chuyển Context Trong Cùng Item
- Click vào field khác trong cùng dòng
- NumPad tác động vào field được click
- Không auto chuyển field

### 8. Click Liên Tiếp Nhiều Item
- Click item A → NumPad gắn A
- Click item B → NumPad NGẮT A – GẮN B
- Không giữ giá trị tạm của item cũ

### 9. ESC & CLEAR
- **ESC**: Đóng NumPad
- **CLEAR**: Reset field về giá trị trước đó
- **Backspace**: Xóa từng ký tự

### 10. Visual Feedback
- Dòng item: highlight rõ, có border/nền khác
- Field đang nhập: focus state rõ ràng
- Tổng tiền update realtime

## 📁 Files Đã Tạo

### 1. ItemEditNumPad.vue
**Path**: `posawesome/public/js/posapp/components/pos/ItemEditNumPad.vue`

**Features**:
- ✅ NumPad UI với layout đẹp
- ✅ Field selection (QTY, RATE, DISCOUNT)
- ✅ Keyboard support (0-9, +, -, Enter, ESC, Backspace)
- ✅ Validation (số lượng > 0, chiết khấu 0-100%)
- ✅ Visual feedback (error states, current values)
- ✅ Responsive design

**Props**:
```javascript
{
    visible: Boolean,           // Show/hide popup
    selectedItem: Object,       // Item đang chỉnh sửa
    initialField: String        // Field mặc định ('qty', 'rate', 'discount_percentage')
}
```

**Events**:
```javascript
@update-field  // { field, value, item }
@delete-item   // item
@close         // void
```

## 🔧 Tích Hợp Vào ItemsTable.vue

### ✅ HOÀN THÀNH - Integration Completed

**Status**: ✅ **DONE** - ItemEditNumPad đã được tích hợp hoàn toàn vào ItemsTable.vue

**Changes Made**:
1. ✅ Import ItemEditNumPad component
2. ✅ Add component to components section
3. ✅ Add @click:row event handler to v-data-table-virtual
4. ✅ Add NumPad component to template
5. ✅ Add NumPad state to data()
6. ✅ Add all NumPad methods (handleRowClick, handleUpdateField, etc.)
7. ✅ Add visual feedback CSS for selected rows
8. ✅ Add hover effects and click indicators

### Bước 1: Import Component ✅

```vue
<script>
import ItemEditNumPad from './ItemEditNumPad.vue';

export default {
    name: 'ItemsTable',
    components: {
        ItemEditNumPad
    },
    // ...
}
</script>
```

### Bước 2: Thêm Data State

```javascript
data() {
    return {
        // ... existing data ...
        
        // 🆕 NumPad State
        numpadVisible: false,
        selectedItemForEdit: null,
        initialEditField: 'qty'
    };
}
```

### Bước 3: Thêm Component Vào Template

```vue
<template>
    <div class="items-table-container">
        <!-- Existing v-data-table-virtual -->
        <v-data-table-virtual
            :headers="headers"
            :items="items"
            @click:row="handleRowClick"
            <!-- ... other props ... -->
        >
            <!-- ... existing templates ... -->
        </v-data-table-virtual>
        
        <!-- 🆕 Item Edit NumPad -->
        <ItemEditNumPad
            :visible="numpadVisible"
            :selected-item="selectedItemForEdit"
            :initial-field="initialEditField"
            @update-field="handleUpdateField"
            @delete-item="handleDeleteItem"
            @close="closeNumPad"
        />
    </div>
</template>
```

### Bước 4: Thêm Methods

```javascript
methods: {
    // ... existing methods ...
    
    // 🆕 Handle row click to open NumPad
    handleRowClick(event, { item }) {
        console.log('[ItemsTable] Row clicked:', item.item_code);
        this.selectedItemForEdit = item;
        this.initialEditField = 'qty'; // Default to quantity
        this.numpadVisible = true;
    },
    
    // 🆕 Handle field update from NumPad
    handleUpdateField({ field, value, item }) {
        console.log('[ItemsTable] Updating field:', field, 'to:', value);
        
        switch (field) {
            case 'qty':
                this.updateItemQty(item, value);
                break;
            case 'rate':
                this.updateItemRate(item, value);
                break;
            case 'discount_percentage':
                this.updateItemDiscount(item, value);
                break;
        }
        
        // Keep NumPad open for further edits
        // User can close with ESC or click close button
    },
    
    // 🆕 Update item quantity
    updateItemQty(item, newQty) {
        // Use existing setFormatedQty method
        this.setFormatedQty(item, 'qty', null, false, newQty);
        this.calcStockQty(item, newQty);
        
        // Trigger discount calculation
        if (!this.$parent.isApplyingDiscount) {
            this.$parent.$nextTick(() => {
                setTimeout(() => {
                    this.$parent.calculateDiscountsDebounced();
                }, 10);
            });
        }
        
        this.$forceUpdate();
    },
    
    // 🆕 Update item rate
    updateItemRate(item, newRate) {
        this.setFormatedCurrency(item, 'rate', newRate);
        this.calcPrices(item);
        this.$forceUpdate();
    },
    
    // 🆕 Update item discount
    updateItemDiscount(item, newDiscount) {
        item.discount_percentage = newDiscount;
        this.calcPrices(item);
        this.$forceUpdate();
    },
    
    // 🆕 Handle delete item from NumPad
    handleDeleteItem(item) {
        console.log('[ItemsTable] Deleting item:', item.item_code);
        this.removeItem(item);
        this.closeNumPad();
    },
    
    // 🆕 Close NumPad
    closeNumPad() {
        this.numpadVisible = false;
        this.selectedItemForEdit = null;
    }
}
```

### Bước 5: Thêm Visual Feedback (Optional)

```vue
<style scoped>
/* Highlight selected row */
.v-data-table-virtual ::v-deep .v-data-table__tr--selected {
    background-color: rgba(25, 118, 210, 0.08) !important;
    border-left: 4px solid #1976d2 !important;
}

/* Hover effect */
.v-data-table-virtual ::v-deep .v-data-table__tr:hover {
    background-color: rgba(0, 0, 0, 0.04);
    cursor: pointer;
}
</style>
```

## 🎨 UI/UX Features

### NumPad Layout
```
┌─────────────────────────────────────────┐
│  Chỉnh Sửa Sản Phẩm                  ✕ │
│  Product Name                           │
├─────────────────────────────────────────┤
│  Left Panel    │  Right Panel (NumPad)  │
│  - Item Info   │  ┌──────────────────┐  │
│  - Field Sel   │  │  Display: 5.00   │  │
│  - Current Val │  └──────────────────┘  │
│                │  [DEL] [-] [+] [⌫]     │
│  [QTY]         │  [7]  [8]  [9]         │
│  [RATE]        │  [4]  [5]  [6]         │
│  [DISCOUNT]    │  [1]  [2]  [3]         │
│                │  [0]  [.]  [000] [CLR] │
│                │  [    ENTER - OK    ]  │
└─────────────────────────────────────────┘
```

### Color Coding
- **Primary (Blue)**: Number buttons
- **Success (Green)**: +, ENTER
- **Warning (Orange)**: -, CLEAR
- **Error (Red)**: DELETE
- **Grey**: Backspace

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| 0-9 | Nhập số |
| . | Thập phân |
| + | Tăng giá trị |
| - | Giảm giá trị |
| Backspace | Xóa 1 ký tự |
| Delete | Clear |
| Enter | Xác nhận |
| Escape | Đóng |
| Tab | Chuyển field |

## 🧪 Testing

### Test Cases

**1. Click Item Opens NumPad**
```javascript
// Click vào item
$vm0.$refs.itemsTable.handleRowClick(null, { item: items[0] });
// Kiểm tra: numpadVisible = true
```

**2. Update Quantity**
```javascript
// Mở NumPad
// Nhập số 5
// Nhấn Enter
// Kiểm tra: item.qty = 5
```

**3. Update Rate**
```javascript
// Chọn field RATE
// Nhập 50000
// Nhấn Enter
// Kiểm tra: item.rate = 50000
```

**4. Update Discount**
```javascript
// Chọn field DISCOUNT
// Nhập 10
// Nhấn Enter
// Kiểm tra: item.discount_percentage = 10
```

**5. Delete Item**
```javascript
// Click DELETE button
// Kiểm tra: item removed from list
```

**6. Keyboard Input**
```javascript
// Nhấn phím 1, 2, 3
// Kiểm tra: displayValue = "123"
```

**7. Validation**
```javascript
// Nhập số âm cho QTY
// Kiểm tra: hasError = true
// Kiểm tra: ENTER button disabled
```

## 📊 Performance Considerations

### Optimization
- ✅ Debouncing cho rapid clicks
- ✅ Event.stopPropagation() để tránh conflicts
- ✅ $forceUpdate() chỉ khi cần thiết
- ✅ Keyboard event handling efficient

### Memory Management
- ✅ Cleanup timers on close
- ✅ Clear selectedItem on close
- ✅ No memory leaks

## 🚨 Known Issues & Solutions

### Issue 1: NumPad không mở khi click row
**Solution**: Kiểm tra @click:row event có được bind đúng không

### Issue 2: Keyboard không hoạt động
**Solution**: Kiểm tra @keydown event và event.stopPropagation()

### Issue 3: Giá trị không update
**Solution**: Kiểm tra emit event và parent methods

### Issue 4: Visual feedback không rõ
**Solution**: Thêm CSS cho selected row state

## 🔄 Future Enhancements

1. **Multi-field Edit**: Cho phép chỉnh nhiều field cùng lúc
2. **History**: Undo/Redo changes
3. **Batch Edit**: Chỉnh nhiều items cùng lúc
4. **Templates**: Save/Load common values
5. **Gestures**: Swipe to change fields
6. **Voice Input**: Voice commands for hands-free
7. **Barcode Scanner**: Scan to select item
8. **Quick Actions**: Preset buttons (x2, x3, etc.)

## ✅ Checklist Triển Khai

- [x] ✅ Tạo ItemEditNumPad.vue component
- [x] ✅ Implement NumPad UI
- [x] ✅ Implement keyboard support
- [x] ✅ Implement validation
- [x] ✅ Implement field switching
- [x] ✅ Tích hợp vào ItemsTable.vue
- [x] ✅ Added @click:row event handler
- [x] ✅ Added NumPad component to template
- [x] ✅ Added handleUpdateField methods
- [x] ✅ Added visual feedback CSS
- [ ] Test click row opens NumPad
- [ ] Test update quantity
- [ ] Test update rate
- [ ] Test update discount
- [ ] Test delete item
- [ ] Test keyboard shortcuts
- [ ] Test validation
- [ ] Test visual feedback
- [ ] Test on mobile
- [ ] User acceptance testing

## 📚 References

- **Vuetify 3 Dialog**: https://vuetifyjs.com/en/components/dialogs/
- **Vuetify 3 Buttons**: https://vuetifyjs.com/en/components/buttons/
- **Keyboard Events**: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-19  
**Status**: ✅ Component Created, Pending Integration  
**Author**: Kiro AI Assistant
