# SOP Triển Khai Base UOM + Offer Engine

## Mục Tiêu
- Chỉ có 1 giá gốc theo Stock UOM trên Price List
- Khuyến mại/giảm giá hoàn toàn từ Offer engine
- Tính toán quy đổi về Stock UOM khi xử lý

## 1. Chuẩn Hóa Master Data

### Item & UOM
- Mỗi Item phải có Stock UOM chuẩn (đơn vị lưu kho)
- Bảng UOM Conversion phải chính xác (VD: 1 THÙNG-24 = 24 LON)
- Item stockable: Maintain Stock = 1
- Item quà tặng: Non-stock, tách riêng

### Quy Trình
- IT kiểm tra và cập nhật Stock UOM cho tất cả Item
- Marketing báo cáo nếu có UOM mơ hồ
- POS không scan UOM không dùng (ẩn trong Item)

## 2. Pricing (Price List = chỉ Stock UOM)

### Quy Tắc
- ❌ KHÔNG nhập giá theo thùng/lốc trên Price List
- ✅ Chỉ nhập giá theo Stock UOM (VD: LON = 30,000đ)

### Quy Trình Marketing
1. Xác định giá gốc theo Stock UOM
2. Nhập vào Price List theo Stock UOM
3. Khuyến mại thiết lập trong POS Offer (không phải Item Price)

### Quy Trình IT
- Server Script chặn tạo/sửa Item Price UOM ≠ stock_uom
- Alert email khi phát hiện vi phạm

## 3. POS / Sales Invoice

### Hành Vi Giá
- Rate ban đầu = base_price * conversion_factor
- Amount = rate * qty
- Lưu original_base_rate để audit

### Quy Trình POS
- ❌ KHÔNG sửa rate tay (POS Profile: allow_user_to_edit_rate = 0)
- ✅ Chỉ dùng discount % hoặc additional discount
- ✅ Scan theo UOM KH muốn (hệ thống tự quy đổi)

### Quy Trình IT
- Hook validate: Reset price về base trước áp Offer
- Log: original_rate_base, discount_amount, offer_applied

## 4. Offer Engine

### Cấu Hình Offer
- uom_ref: UOM khối (VD: THÙNG-24)
- total_items_in_block_qty: Số đơn vị base trong 1 block (VD: 24)
- total_discount_amount_per_block: Giảm tiền/block
- min_block_qty / max_eligible_block_qty

### Quy Trình Marketing
1. Xác định UOM khuyến mại (thùng/lốc)
2. Thiết lập Offer theo block
3. Test với IT trước deploy

### Bonus Quà
- Dùng Give Product theo block
- Item quà: posa_is_offer=1, rate=0

## 5. Guardrails

### Server Scripts
- Block Item Price UOM ≠ stock_uom
- Block giảm rate tay trên Sales Invoice

### Background Jobs
- Tắt jobs đồng bộ giá từ Offer về Price List
- Disable Pricing Rule đụng chạm

## 6. Migration

### Quy Trình
1. Export Item Price UOM ≠ stock_uom
2. Archive/xóa records sai
3. Disable Pricing Rule cũ
4. Test batch recalc

### Quy Trình IT
- Chạy patch migration
- Verify không còn Item Price sai
- Backup data trước khi xóa

## 7. Kiểm Thử

### Test Cases Bắt Buộc
1. Stock UOM không offer
2. Block discount theo thùng
3. Mixed qty (thùng + lẻ)
4. Vượt max block
5. Gift offer
6. Return/đổi trả
7. Multi-currency
8. Tax inclusive

### Quy Trình
- IT viết unit tests
- Test trên staging trước
- Marketing test scenarios thực tế

## 8. Vận Hành & Monitor

### Logging
- Log khi reset price về base
- Log khi áp offer
- Log khi rate thay đổi

### Báo Cáo Đối Soát
```sql
SELECT
    item_code,
    stock_uom,
    base_price,
    SUM(qty_base) as qty_base,
    SUM(discount_total) as discount_total,
    SUM(final_amount) as final_amount,
    GROUP_CONCAT(DISTINCT offers_applied) as offers_applied
FROM sales_invoice_analysis
WHERE posting_date = CURDATE()
GROUP BY item_code, stock_uom, base_price
```

### Alert
- Email/Slack khi Item Price mới UOM ≠ stock_uom
- Recipients: IT Team, Marketing Lead

### SOP Marketing
1. Giá gốc chỉ nhập theo Stock UOM
2. Khuyến mại thiết lập trong POS Offer
3. Test offer trước deploy production
4. Báo IT nếu cần thay đổi UOM

### SOP POS
1. Không sửa rate tay
2. Scan theo UOM KH muốn
3. Dùng coupon/offer cho giảm giá
4. Báo IT nếu giá hiển thị sai

## 9. Troubleshooting

### Giá "nhảy múa"
- Check _reset_item_prices() có chạy đúng
- Verify base_price_list_rate theo stock_uom
- Check conversion_factor chính xác

### Offer không áp dụng
- Check time slots
- Verify UOM match uom_ref
- Check min/max qty conditions

### Stock không khớp
- Verify stock_qty = qty * conversion_factor
- Check stock_uom trong Item

## 10. Rollback Plan

### Nếu có lỗi nghiêm trọng
1. Disable Server Scripts block
2. Restore Item Price từ backup
3. Re-enable Pricing Rule cũ
4. Rollback code changes

### Monitoring
- Alert nếu >5% invoices có discount sai
- Daily report giá trung bình/item
- Weekly audit stock variance