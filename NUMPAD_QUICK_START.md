# 🔢 NumPad Quick Start Guide

## 🎯 Tính Năng Mới: NumPad Chỉnh Sửa Giỏ Hàng

### Cách Sử Dụng

#### 1. Mở NumPad
```
Click vào bất kỳ dòng sản phẩm nào trong giỏ hàng
→ NumPad popup sẽ mở ra
→ Tự động focus vào trường Số Lượng (QTY)
```

#### 2. Chỉnh Sửa Số Lượng (Mặc Định)
```
Gõ số trực tiếp: 1, 2, 3, 4, 5...
→ Số cũ sẽ bị ghi đè (không cộng thêm)
→ Ví dụ: SL hiện tại = 5, gõ 2 → SL = 2 (không phải 52)

Hoặc dùng nút +/-:
→ + : Tăng 1
→ - : Giảm 1
```

#### 3. Chỉnh Sửa Đơn Giá hoặc Chiết Khấu
```
Click vào nút [Đơn Giá] hoặc [Chiết Khấu]
→ NumPad sẽ chuyển sang chỉnh sửa trường đó
→ Gõ số mới
```

#### 4. Xác Nhận Thay Đổi
```
Nhấn nút [ENTER] hoặc phím Enter trên bàn phím
→ Giá trị được lưu
→ NumPad vẫn mở để tiếp tục chỉnh sửa
```

#### 5. Đóng NumPad
```
Nhấn nút [X] ở góc trên phải
Hoặc nhấn phím ESC
→ NumPad đóng lại
```

### ⌨️ Phím Tắt

| Phím | Chức Năng |
|------|-----------|
| **0-9** | Nhập số |
| **.** | Dấu thập phân |
| **+** | Tăng giá trị |
| **-** | Giảm giá trị |
| **Backspace** | Xóa 1 ký tự |
| **Delete** | Xóa toàn bộ |
| **Enter** | Xác nhận |
| **ESC** | Đóng NumPad |
| **Tab** | Chuyển trường (QTY → RATE → DISCOUNT) |

### 🎨 Giao Diện NumPad

```
┌─────────────────────────────────────────┐
│  Chỉnh Sửa Sản Phẩm                  ✕ │
│  Tên Sản Phẩm                           │
├─────────────────────────────────────────┤
│  Thông Tin SP    │  NumPad              │
│  ─────────────   │  ┌──────────────┐    │
│  Mã: ABC123      │  │ Nhập: 5.00   │    │
│  Tên: Product    │  └──────────────┘    │
│  ĐVT: Cái        │                      │
│                  │  [DEL] [-] [+] [⌫]   │
│  Chọn Trường:    │  [7]  [8]  [9]       │
│  [Số Lượng]      │  [4]  [5]  [6]       │
│  [Đơn Giá]       │  [1]  [2]  [3]       │
│  [Chiết Khấu]    │  [0]  [.]  [000][CLR]│
│                  │  [   ENTER - OK   ]  │
│  Giá trị hiện:   │                      │
│  5.00            │                      │
└─────────────────────────────────────────┘
```

### 🎯 Các Trường Chỉnh Sửa

#### 1. Số Lượng (QTY)
- **Mặc định**: Tự động focus khi mở NumPad
- **Phạm vi**: > 0
- **Bước tăng/giảm**: 1
- **Ví dụ**: 1, 2, 3, 5, 10, 100

#### 2. Đơn Giá (RATE)
- **Phạm vi**: >= 0
- **Bước tăng/giảm**: 1,000
- **Ví dụ**: 10000, 25000, 50000

#### 3. Chiết Khấu (DISCOUNT %)
- **Phạm vi**: 0% - 100%
- **Bước tăng/giảm**: 5%
- **Ví dụ**: 5%, 10%, 15%, 20%

### ✅ Validation (Kiểm Tra Lỗi)

NumPad sẽ tự động kiểm tra và ngăn chặn:
- ❌ Số lượng <= 0
- ❌ Đơn giá < 0
- ❌ Chiết khấu < 0% hoặc > 100%

Khi có lỗi:
- Nút ENTER sẽ bị vô hiệu hóa
- Hiển thị thông báo lỗi màu đỏ
- Không thể xác nhận cho đến khi sửa lỗi

### 🎨 Visual Feedback

#### Dòng Được Chọn
- Highlight màu xanh
- Border trái màu xanh dương
- Icon NumPad 🔢 ở bên trái

#### Hover Effect
- Dòng sản phẩm sẽ nổi lên khi di chuột
- Con trỏ chuột thay đổi thành pointer
- Shadow nhẹ xuất hiện

#### Cập Nhật Realtime
- Tổng tiền tự động cập nhật
- Giá trị hiển thị ngay lập tức
- Không cần reload trang

### 🚀 Tips & Tricks

#### 1. Chỉnh Số Lượng Nhanh
```
Click dòng → Gõ số → Enter
(Không cần click vào trường QTY vì đã auto-focus)
```

#### 2. Tăng/Giảm Nhanh
```
Click dòng → Nhấn + hoặc - nhiều lần → Enter
```

#### 3. Nhập Số Lớn
```
Click dòng → Gõ 1 → Nhấn [000] → Nhấn [000] → Enter
(Kết quả: 1,000,000)
```

#### 4. Chỉnh Nhiều Trường
```
Click dòng → Chỉnh QTY → Enter
→ Click [Đơn Giá] → Chỉnh giá → Enter
→ Click [Chiết Khấu] → Chỉnh CK → Enter
→ ESC để đóng
```

#### 5. Xóa Item
```
Click dòng → Nhấn nút [DELETE] màu đỏ
→ Item sẽ bị xóa khỏi giỏ hàng
```

### ⚠️ Lưu Ý Quan Trọng

1. **Ghi Đè, Không Cộng Thêm**
   - Khi gõ số mới, số cũ sẽ bị thay thế hoàn toàn
   - Ví dụ: SL = 5, gõ 2 → SL = 2 (không phải 52)

2. **NumPad Vẫn Mở Sau Enter**
   - Sau khi nhấn Enter, NumPad không tự đóng
   - Cho phép chỉnh sửa tiếp các trường khác
   - Nhấn ESC để đóng khi hoàn tất

3. **Validation Tự Động**
   - Hệ thống sẽ ngăn chặn giá trị không hợp lệ
   - Không thể nhập số âm cho số lượng
   - Chiết khấu không thể > 100%

4. **Keyboard vs Mouse**
   - Có thể dùng hoàn toàn bằng bàn phím (nhanh hơn)
   - Hoặc dùng chuột click các nút (trực quan hơn)
   - Kết hợp cả hai để tối ưu tốc độ

### 🐛 Troubleshooting

#### NumPad Không Mở
- ✅ Kiểm tra đã click đúng vào dòng sản phẩm chưa
- ✅ Thử refresh trang và thử lại
- ✅ Kiểm tra console log có lỗi không

#### Keyboard Không Hoạt Động
- ✅ Kiểm tra NumPad đã mở chưa
- ✅ Click vào trong NumPad để focus
- ✅ Thử dùng chuột click các nút số

#### Giá Trị Không Cập Nhật
- ✅ Kiểm tra đã nhấn Enter chưa
- ✅ Kiểm tra có lỗi validation không
- ✅ Xem thông báo lỗi màu đỏ

### 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Console log (F12 → Console)
2. File: `test_numpad_integration.js` để test
3. Documentation: `ITEM_EDIT_NUMPAD_INTEGRATION_GUIDE.md`

---

**Version**: 1.0.0  
**Last Updated**: December 19, 2024  
**Status**: ✅ Production Ready