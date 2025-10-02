#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POS Offer Template Creator
Creates comprehensive test templates for all new discount features

Usage: bench console < create_pos_offer_templates.py
"""

import frappe
import json
from datetime import datetime, timedelta

def create_pos_offer_templates():
    """Create comprehensive POS Offer templates for testing all new features"""

    print("🎯 Creating POS Offer Templates for Testing")
    print("=" * 60)

    # Use specific company and POS profile as requested
    company = "NVL-DaiLoan"
    pos_profile_name = "POS_DY134"
    warehouse = "DY134"

    # Verify POS profile exists
    if not frappe.db.exists("POS Profile", pos_profile_name):
        print(f"❌ POS Profile '{pos_profile_name}' not found. Please create it first.")
        return

    pos_profile = frappe.get_doc("POS Profile", pos_profile_name)

    print(f"📍 Using Company: {company}")
    print(f"📍 Using POS Profile: {pos_profile_name}")
    print(f"📍 Using Warehouse: {warehouse}")

    # Template configurations
    templates = [
        # ===== TIME-BASED TEMPLATES =====
        {
            "title": "01 - TIME - CHIẾT_KHUYẾN_MÃI_SÁNG - Giảm giá sáng 8:00-12:00 các ngày trong tuần",
            "description": "Mẫu: Giảm giá sáng 8:00-12:00 các ngày trong tuần. Áp dụng cho Item Code, giảm 10% giá gốc. Thời gian: 8:00-12:00 từ thứ 2 đến thứ 6. Không áp dụng cuối tuần.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Code",
            "item": "8936136169170",  # Real item code
            "discount_type": "Discount Percentage",
            "discount_percentage": 1,
            "warehouse": warehouse5
            "available_time_in_day": json.dumps([{
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "08:00:00",
                "end_time": "12:00:00",
                "is_overnight": False
            }]),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "02 - TIME - CHIẾT_KHUYẾN_MÃI_HAPPY_HOUR - Khuyến mãi giờ vàng 17:00-19:00 hàng ngày ",
            "description": "Mẫu: Khuyến mãi giờ vàng 17:00-19:00 hàng ngày. Áp dụng cho Item Group, giảm 15% giá gốc. Thời gian: 17:00-19:00 tất cả các ngày trong tuần.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Group",
            "item_group": "VT007",  # Real item group
            "discount_type": "Discount Percentage",
            "discount_percentage": 10,
            "warehouse": warehouse,
            "available_time_in_day": json.dumps([{
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "start_time": "17:00:00",
                "end_time": "19:00:00",
                "is_overnight": False
            }]),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "03 - TIME - CHIẾT_KHUYẾN_MÃI_KHUYA - Khuyến mãi khuya 22:00-02:00 cuối tuần",
            "description": "Mẫu: Khuyến mãi khuya 22:00-02:00 (qua đêm) cuối tuần. Áp dụng cho toàn bộ hóa đơn, giảm 25k. Thời gian: 22:00 tối thứ 6 đến 02:00 sáng chủ nhật.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Transaction",
            "discount_type": "Discount Amount",
            "discount_amount": 25,
            "warehouse": warehouse,
            "available_time_in_day": json.dumps([{
                "days_of_week": ["friday", "saturday"],
                "start_time": "22:00:00",
                "end_time": "02:00:00",
                "is_overnight": True
            }]),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },

        # ===== BLOCK-BASED DISCOUNT TEMPLATES =====
        {
            "title": "04 - BLOCK_DISCOUNT - KHUYẾN_MÃI_BLOCK_BIA - Mua 24 chai bia giảm 50k/thùng",
            "description": "Mẫu: Mua 24 chai bia (1 thùng), giảm 50k/thùng. UOM: THÙNG-30, 24 chai = 1 block, giảm 50k. Tối thiểu 1 thùng, tối đa 3 thùng.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Code",
            "item": "4711588341053",  # Beer item
            "is_used_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 24,
            "min_block_qty": 1,
            "max_eligible_block_qty": 3,
            "total_discount_amount_per_block": 50,
            "warehouse": warehouse,
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "05 - BLOCK_DISCOUNT - KHUYẾN_MÃI_BLOCK_NƯỚC - Mua 12 chai nước giảm 30k/hộp",
            "description": "Mẫu: Mua 12 chai nước (1 hộp), giảm 30k/hộp. UOM: THÙNG-30, 12 chai = 1 block, giảm 30k. Tối thiểu 2 hộp, tối đa 5 hộp.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Group",
            "item_group": "VT007",  # Beverages group
            "is_used_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 12,
            "min_block_qty": 2,
            "max_eligible_block_qty": 5,
            "total_discount_amount_per_block": 30,
            "warehouse": warehouse,
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "06 - BLOCK_DISCOUNT - KHUYẾN_MÃI_BLOCK_HON_HOP - Khuyến mãi hỗn hợp theo thương hiệu",
            "description": "Mẫu: Khuyến mãi hỗn hợp theo thương hiệu, giảm 20k/block. UOM: THÙNG-30, 10 sản phẩm bất kỳ = 1 block. Không giới hạn số block.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Brand",
            "brand": "BEIAN",  # Real brand
            "is_used_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 10,
            "min_block_qty": 1,
            "max_eligible_block_qty": 0,  # Unlimited
            "total_discount_amount_per_block": 20,
            "warehouse": warehouse,
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },

        # ===== BLOCK-BASED GIFT TEMPLATES =====
        {
            "title": "07 - BLOCK_GIFT - TẶNG_QUÀ_BLOCK_BUY3_GET1 - Mua 3 đồ uống tặng 1",
            "description": "Mẫu: Mua 3 đồ uống tặng 1. UOM: THÙNG-30, 3 sản phẩm = 1 block, tặng 1 quà. Tối đa 3 quà. Không có quà bonus.",
            "is_template": 1,
            "offer": "Give Product",
            "apply_on": "Item Group",
            "item_group": "VT007",  # Beverages group
            "is_used_gift_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 3,
            "min_block_qty": 1,
            "max_eligible_block_qty": 3,
            "gift_per_block_qty": 1,
            "gift_item_code": "8936136169170",  # Real item code for testing
            "warehouse": warehouse,
            "bonus_gift_per_block": json.dumps({
                "enabled": False,
                "extra_gifts": []
            }),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "08 - BLOCK_GIFT - TẶNG_QUÀ_BLOCK_BONUS - Mua 5 sản phẩm tặng 1 + quà bonus",
            "description": "Mẫu: Mua 5 sản phẩm tặng 1 + quà bonus. UOM: THÙNG-30, 5 sản phẩm = 1 block. Từ 3 block trở lên tặng thêm quà bonus.",
            "is_template": 1,
            "offer": "Give Product",
            "apply_on": "Transaction",
            "is_used_gift_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 5,
            "min_block_qty": 2,
            "max_eligible_block_qty": 4,
            "gift_per_block_qty": 1,
            "gift_item_code": "8936136169170",
            "warehouse": warehouse,
            "bonus_gift_per_block": json.dumps({
                "enabled": True,
                "extra_gifts": [
                    {"item_code": "8936136169170", "qty": 1, "min_blocks": 3}
                ]
            }),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },

        # ===== TIERED PRICING TEMPLATES =====
        {
            "title": "09 - TIERED_PRICING - BƯỚC GIÁ  - Giảm giá theo số lượng",
            "description": "Mẫu: Giảm giá theo số lượng - 1-5: 0%, 6-10: 5%, 11+: 10%. Áp dụng cho Item Code, giảm % theo số lượng mua.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Code",
            "item": "8936136169170",  # Real item code
            "is_used_tiered_pricing": 1,
            "warehouse": warehouse,
            "tiered_pricing_json": json.dumps({
                "tiers": [
                    {"min_qty": 1, "max_qty": 5, "type": "discount_percentage", "value": 0},
                    {"min_qty": 6, "max_qty": 10, "type": "discount_percentage", "value": 5},
                    {"min_qty": 11, "max_qty": 999, "type": "discount_percentage", "value": 10}
                ]
            }),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "10 - TIERED_PRICING - ĐIỆN_TỔNG_GIÁ_CỐ_ĐỊNH - Giá cố định theo số lượng",
            "description": "Mẫu: Giá cố định theo số lượng - 1-9: 100k, 10-49: 90k, 50+: 80k. Áp dụng cho Item Group, giá giảm theo số lượng.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Group",
            "item_group": "VT007",  # Real item group
            "is_used_tiered_pricing": 1,
            "warehouse": warehouse,
            "tiered_pricing_json": json.dumps({
                "tiers": [
                    {"min_qty": 1, "max_qty": 9, "type": "fixed_rate", "value": 100},
                    {"min_qty": 10, "max_qty": 49, "type": "fixed_rate", "value": 90},
                    {"min_qty": 50, "max_qty": 999, "type": "fixed_rate", "value": 80}
                ]
            }),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },

        # ===== COMBINED SCENARIOS =====
        {
            "title": "11 - COMBINED - KẾT_HỢP_SÁNG_BLOCK - Sáng + Block discount",
            "description": "Mẫu: Sáng + Block discount - 6:00-10:00 từ T2-T6, mua 20 sản phẩm giảm 100k/block. UOM: THÙNG-30, tối đa 2 block.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Brand",
            "brand": "BEIAN",  # Real brand
            "is_used_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 20,
            "min_block_qty": 1,
            "max_eligible_block_qty": 2,
            "total_discount_amount_per_block": 100,
            "warehouse": warehouse,
            "available_time_in_day": json.dumps([{
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "06:00:00",
                "end_time": "10:00:00",
                "is_overnight": False
            }]),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "12 - COMBINED - KẾT_HỢP_CUỐI_TUẦN_QUÀ - Cuối tuần + Block quà",
            "description": "Mẫu: Cuối tuần + Block quà - 12:00-18:00 T7-CN, mua 50 sản phẩm tặng 1 quà. UOM: THÙNG-30, tối đa 1 quà.",
            "is_template": 1,
            "offer": "Give Product",
            "apply_on": "Transaction",
            "is_used_gift_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 50,
            "min_block_qty": 1,
            "max_eligible_block_qty": 1,
            "gift_per_block_qty": 1,
            "gift_item_code": "8936136169170",
            "warehouse": warehouse,
            "available_time_in_day": json.dumps([{
                "days_of_week": ["saturday", "sunday"],
                "start_time": "12:00:00",
                "end_time": "18:00:00",
                "is_overnight": False
            }]),
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },

        # ===== EDGE CASES =====
        {
            "title": "13 - EDGE_CASE - CẠNH_TRƯỜNG_BLOCK_TỐI_THIỂU - Test block tối thiểu",
            "description": "Mẫu: Test block tối thiểu - Cần ít nhất 3 block (15 sản phẩm) mới áp dụng. UOM: THÙNG-30, 5 sản phẩm = 1 block.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Code",
            "item": "8936136169170",  # Real item code
            "is_used_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 5,
            "min_block_qty": 3,  # Require at least 3 blocks (15 items)
            "max_eligible_block_qty": 0,
            "total_discount_amount_per_block": 25,
            "warehouse": warehouse,
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "14 - EDGE_CASE - CẠNH_TRƯỜNG_BLOCK_TỐI_ĐA - Test block tối đa",
            "description": "Mẫu: Test block tối đa - Tối đa 2 quà tặng. UOM: THÙNG-30, 6 sản phẩm = 1 block, tặng 1 quà.",
            "is_template": 1,
            "offer": "Give Product",
            "apply_on": "Item Group",
            "item_group": "VT007",  # Beverages group
            "is_used_gift_block": 1,
            "uom_ref": "THÙNG-30",
            "total_items_in_block_qty": 6,
            "min_block_qty": 1,
            "max_eligible_block_qty": 2,  # Max 2 gifts
            "gift_per_block_qty": 1,
            "gift_item_code": "8936136169170",
            "warehouse": warehouse,
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        },
        {
            "title": "15 - EDGE_CASE - CẠNH_TRƯỜNG_UOM_KHÔNG_KHỚP - Test UOM validation",
            "description": "Mẫu: Test UOM validation - Sử dụng UOM 'Kg' khác với 'THÙNG-30', không áp dụng discount. Dùng để test validation.",
            "is_template": 1,
            "offer": "Item Price",
            "apply_on": "Item Code",
            "item": "8936136169170",  # Real item code
            "is_used_block": 1,
            "uom_ref": "Kg",  # Different UOM
            "total_items_in_block_qty": 10,
            "min_block_qty": 1,
            "max_eligible_block_qty": 0,
            "total_discount_amount_per_block": 40,
            "warehouse": warehouse,
            "valid_from": "2025-10-01",
            "valid_upto": "2025-12-31"
        }
    ]

    created_count = 0
    skipped_count = 0

    for template_data in templates:
        try:
            # Check if template already exists
            existing = frappe.db.exists("POS Offer", {"title": template_data["title"]})
            if existing:
                print(f"⚠️  Template '{template_data['title']}' already exists - skipping")
                skipped_count += 1
                continue

            # Create new template
            doc = frappe.get_doc({
                "doctype": "POS Offer",
                "company": company,
                "pos_profile": pos_profile_name,
                **template_data
            })

            doc.insert(ignore_permissions=True)
            created_count += 1
            print(f"✅ Created template: {template_data['title']}")

        except Exception as e:
            print(f"❌ Failed to create template '{template_data['title']}': {e}")
            continue

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEMPLATE CREATION SUMMARY")
    print("=" * 60)
    print(f"✅ Created: {created_count} templates")
    print(f"⚠️  Skipped: {skipped_count} templates (already exist)")
    print(f"📈 Total processed: {created_count + skipped_count} templates")

    if created_count > 0:
        print("\n🎯 Next Steps:")
        print("   1. Review created templates in POS Offer list")
        print("   2. Test discount calculations with sample data")
        print("   3. Duplicate templates for production use (set is_template=0)")

    print("\n📋 Template Categories:")
    print("   🕐 Time-based: 3 templates")
    print("   📦 Block Discount: 3 templates")
    print("   🎁 Block Gift: 2 templates")
    print("   📊 Tiered Pricing: 2 templates")
    print("   🔗 Combined: 2 templates")
    print("   ⚠️  Edge Cases: 3 templates")
    print(f"   📊 Total: {len(templates)} templates")

    return created_count

# Main execution
if __name__ == "__main__":
    try:
        created = create_pos_offer_templates()
        if created > 0:
            print("\n🎉 Template creation completed successfully!")
            print("🚀 Ready for Phase 3: Validation & Testing")
        else:
            print("\n⚠️  No new templates created")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        frappe.log_error(f"POS Offer Template Creation Failed: {e}")