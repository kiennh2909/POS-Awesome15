# 🎨 Customer Detail Format Preview

## 📋 **THÔNG TIN CƠ BẢN**
| Section | Field | Value |
|---------|-------|-------|
| 📋 **THÔNG TIN CƠ BẢN** | 📋 ID Customer | **CUST-001** |
| | 👤 Customer Name | Nguyễn Văn Test |
| | 📞 Mobile No | +84 123 456 789 |
| | ✉️ Email | test@example.com |
| | 🏷️ Tax ID | 123456789 |
| | 🏙️ City | Hồ Chí Minh |

## 🏷️ **THÔNG TIN PHÂN LOẠI**
| Section | Field | Value |
|---------|-------|-------|
| 🏷️ **THÔNG TIN PHÂN LOẠI** | 👥 Customer Type | Individual |
| | 👨‍👩‍👧‍👦 Customer Group | VIP Customers |
| | 🗺️ Territory | South Vietnam |
| | ⚧️ Gender | Male |

## 💳 **THÔNG TIN VỀ CREDIT**
| Section | Field | Value |
|---------|-------|-------|
| 💳 **THÔNG TIN VỀ CREDIT** | 📊 Calculated Results | |
| | 💰 Total Credit Limit | **150,000 VND** |
| | 📈 Total Outstanding | **75,000 VND** |
| | 💳 Credit Balance | **75,000 VND** |
| | 🏢 Credit Companies | ABC Company, XYZ Corp |
| | 🔍 Verification | |
| | 📋 Credit Limit Entries | 🏢 ABC Company: 100,000 (Bypass: 0)<br>🏢 XYZ Corp: 50,000 (Bypass: 1)<br>💰 Total from entries: 150,000 |
| | 📈 Direct Outstanding | 75,000 VND |
| | 💳 Expected Balance | 75,000 VND |
| | ⏰ Payment Terms | Net 30 |

## ⭐ **THÔNG TIN LOYALTY**
| Section | Field | Value |
|---------|-------|-------|
| ⭐ **THÔNG TIN LOYALTY** | 🎯 Loyalty Program | Gold Member |
| | 🔢 Total Points | **2,500** |
| | 📉 Points Used | 500 |
| | 💰 Points Balance | **2,000** |

## 💰 **THÔNG TIN CÔNG NỢ**
| Section | Field | Value |
|---------|-------|-------|
| 💰 **THÔNG TIN CÔNG NỢ** | 📊 Total Debt Generated | 500,000 VND |
| | ✅ Total Paid | 425,000 VND |
| | ⚠️ Remaining Debt | **75,000 VND** |

## 📈 **THỐNG KÊ KHÁCH HÀNG**
| Section | Field | Value |
|---------|-------|-------|
| 📈 **THỐNG KÊ KHÁCH HÀNG** | 🛒 Total Orders | **25** |
| | 💵 Total GMV | **2,500,000 VND** |
| | ✅ Paid Orders | 20 |
| | ↩️ Return Orders | 2 |
| | 📊 Avg Order Value | 100,000 VND |
| | 📅 Last Order Date | 2024-01-15 |

---

## 🎨 **Features của Format Mới:**

### ✅ **Visual Improvements:**
- **Emoji icons** cho từng loại thông tin
- **Color coding** cho các giá trị quan trọng
- **Section headers** với background gradient
- **Bold formatting** cho thông tin chính
- **Hierarchical display** với indentation

### ✅ **Information Organization:**
- **📋 THÔNG TIN CƠ BẢN**: ID, tên, liên hệ
- **🏷️ THÔNG TIN PHÂN LOẠI**: Loại khách, nhóm, khu vực
- **💳 THÔNG TIN VỀ CREDIT**: Giới hạn, nợ, công ty
- **⭐ THÔNG TIN LOYALTY**: Điểm tích lũy
- **💰 THÔNG TIN CÔNG NỢ**: Nợ phải trả
- **📈 THỐNG KÊ**: Lịch sử mua hàng

### ✅ **Color Scheme:**
- 🔵 **Primary**: Thông tin cơ bản (ID, tên)
- 🟢 **Success**: Số dư dương, đã thanh toán
- 🟠 **Warning**: Nợ chưa thanh toán
- 🔴 **Error**: Nợ quá hạn, lỗi
- 🟣 **Purple**: Loyalty points

---

## 🚀 **Cách Test:**

```javascript
// 1. Mở POS App
// 2. Chọn customer từ dropdown
// 3. Click nút 👁️ View Details
// 4. Xem popup với format mới
```

**🎉 Format mới giúp hiển thị thông tin customer một cách rõ ràng và chuyên nghiệp hơn!**