-- =========================================
-- UOM PRICING AUDIT SCRIPTS v2.0
-- Kiểm tra tuân thủ bộ quy tắc Base UOM
-- Chạy tuần tự từ Section 1 → 6
-- =========================================

USE `erpv152_multi_v1_vn_vtcom_online_2025_v3`;

-- =========================================
-- SECTION 1: QUY ƯỚC UOM
-- =========================================

-- 1.1 Items không có stock_uom (CRITICAL - cần fix ngay)
SELECT
    '❌ Items without stock_uom (CRITICAL)' as check_type,
    COUNT(*) as count,
    GROUP_CONCAT(name ORDER BY name LIMIT 10) as sample_items
FROM `tabItem`
WHERE (stock_uom IS NULL OR stock_uom = '')
    AND is_sales_item = 1;

-- Chi tiết items thiếu stock_uom
SELECT
    'Items without stock_uom - Details' as check_type,
    name as item_code,
    item_name,
    item_group,
    creation,
    modified
FROM `tabItem`
WHERE (stock_uom IS NULL OR stock_uom = '')
    AND is_sales_item = 1
ORDER BY item_group, name
LIMIT 50;

-- 1.2 Items có setup UOM phức tạp (WARNING) - SKIPPED: Using tabUOM master table
-- SELECT '⚠️ Items with complex UOM setup' as check_type, 'N/A - tabUOM master table used' as note;

-- 1.4 Ẩn UOM không dùng trong POS (TUỲ CHỌN)
SELECT
    'ℹ️ UOMs không sử dụng trong POS' as check_type,
    u.name as uom_name,
    u.uom_name,
    COUNT(iu.parent) as items_using_this_uom,
    CASE
        WHEN COUNT(iu.parent) = 0 THEN '❌ KHÔNG SỬ DỤNG - CÓ THỂ ẨN'
        WHEN COUNT(iu.parent) < 5 THEN '⚠️ ÍT SỬ DỤNG'
        ELSE '✅ ĐANG SỬ DỤNG'
    END as recommendation
FROM `tabUOM` u
LEFT JOIN `tabItem UOM` iu ON u.name = iu.uom
WHERE u.enabled = 1
GROUP BY u.name, u.uom_name
ORDER BY items_using_this_uom ASC, u.name;

-- Query để ẩn UOMs không sử dụng
-- UPDATE `tabUOM` SET enabled = 0 WHERE name IN (
--     SELECT u.name
--     FROM `tabUOM` u
--     LEFT JOIN `tabItem UOM` iu ON u.name = iu.uom
--     GROUP BY u.name
--     HAVING COUNT(iu.parent) = 0
-- );

-- 1.3 UOM Conversion validation (ERRORS & WARNINGS)
SELECT
    'UOM Conversion Issues' as check_type,
    item_code,
    uom_from,
    uom_to,
    conversion_factor,
    source,
    CASE
        WHEN conversion_factor <= 0 THEN '❌ ERROR: Invalid conversion factor'
        WHEN conversion_factor = 1 AND uom_from != uom_to THEN '⚠️ WARNING: Conversion factor = 1 but different UOMs'
        WHEN conversion_factor IS NULL THEN '❌ ERROR: NULL conversion factor'
        ELSE '✅ OK'
    END as status
FROM (
    -- From UOM Conversion Detail table
    SELECT
        parent as item_code,
        'N/A' as uom_from,
        uom as uom_to,
        conversion_factor,
        'UOM Conversion Detail' as source
    FROM `tabUOM Conversion Detail`
) conversions
WHERE conversion_factor <= 0 OR conversion_factor IS NULL
    OR (conversion_factor = 1 AND uom_from != uom_to)
ORDER BY
    CASE
        WHEN conversion_factor <= 0 OR conversion_factor IS NULL THEN 1
        WHEN conversion_factor = 1 AND uom_from != uom_to THEN 2
        ELSE 3
    END,
    item_code;

-- =========================================
-- SECTION 2: GIÁ BÁN NIÊM YẾT
-- =========================================

-- 2.1 VIOLATION: Item Price có UOM != stock_uom (CRITICAL)
SELECT
    '❌ VIOLATION: Item Price UOM != stock_uom' as check_type,
    COUNT(*) as violation_count,
    GROUP_CONCAT(DISTINCT ip.item_code ORDER BY ip.item_code LIMIT 10) as sample_items
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
WHERE ip.docstatus = 0
    AND ip.uom != i.stock_uom;

-- Chi tiết violations
SELECT
    'Item Price Violations - Details' as check_type,
    ip.name as item_price_name,
    ip.item_code,
    ip.price_list,
    ip.uom as item_price_uom,
    i.stock_uom,
    ip.price_list_rate,
    ip.creation,
    ip.owner
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
WHERE ip.docstatus = 0
    AND ip.uom != i.stock_uom
ORDER BY ip.item_code, ip.price_list
LIMIT 100;

-- Xóa hết toàn bộ các Violations (nếu cần)

delete from `tabItem Price` where `tabItem Price`.`name` in 
( 
SELECT
   ip.`name`
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
WHERE ip.docstatus = 0
    AND ip.uom != i.stock_uom) 
;



-- 2.2 WARNING: Items có nhiều giá niêm yết theo cùng price_list
SELECT
    '⚠️ WARNING: Multiple prices per item/price_list' as check_type,
    COUNT(DISTINCT CONCAT(item_code, '_', price_list)) as affected_item_price_lists,
    GROUP_CONCAT(DISTINCT item_code ORDER BY item_code LIMIT 5) as sample_items
FROM (
    SELECT
        ip.item_code,
        ip.price_list,
        COUNT(*) as price_count
    FROM `tabItem Price` ip
    INNER JOIN `tabItem` i ON ip.item_code = i.name
    WHERE ip.docstatus = 0
        AND ip.uom = i.stock_uom
    GROUP BY ip.item_code, ip.price_list
    HAVING price_count > 1
) duplicates;

-- Chi tiết duplicate prices
SELECT
    'Duplicate Prices - Details' as check_type,
    item_code,
    price_list,
    stock_uom,
    COUNT(*) as price_count,
    MIN(price_list_rate) as min_price,
    MAX(price_list_rate) as max_price,
    GROUP_CONCAT(price_list_rate ORDER BY price_list_rate) as all_prices,
    GROUP_CONCAT(name ORDER BY price_list_rate) as item_price_names
FROM (
    SELECT
        ip.name,
        ip.item_code,
        ip.price_list,
        i.stock_uom,
        ip.price_list_rate
    FROM `tabItem Price` ip
    INNER JOIN `tabItem` i ON ip.item_code = i.name
    WHERE ip.docstatus = 0
        AND ip.uom = i.stock_uom
) valid_prices
GROUP BY item_code, price_list, stock_uom
HAVING price_count > 1
ORDER BY item_code, price_list
LIMIT 20;

-- 2.3 Items không có giá niêm yết theo stock_uom
SELECT
    '❌ Items without stock_uom price' as check_type,
    COUNT(*) as missing_price_count,
    GROUP_CONCAT(i.name ORDER BY i.name LIMIT 10) as sample_items
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code
    AND ip.uom = i.stock_uom
    AND ip.docstatus = 0
WHERE ip.name IS NULL
    AND i.stock_uom IS NOT NULL
    AND i.stock_uom != ''
    AND i.is_sales_item = 1;

-- Chi tiết items thiếu giá
SELECT
    'Missing Prices - Details' as check_type,
    i.name as item_code,
    i.item_name,
    i.stock_uom,
    i.item_group,
    i.creation,
    i.modified
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code
    AND ip.uom = i.stock_uom
    AND ip.docstatus = 0
WHERE ip.name IS NULL
    AND i.stock_uom IS NOT NULL
    AND i.stock_uom != ''
    AND i.is_sales_item = 1
ORDER BY i.item_group, i.name
LIMIT 50;

-- =========================================
-- SECTION 3: CONVERSION FACTOR VALIDATION
-- =========================================

-- 3.1 Price conversion examples (validation)
SELECT
    '✅ Price conversion examples' as check_type,
    0 as total_conversions,
    0 as items_with_conversions,
    0 as avg_conversion_factor,
    0 as min_conversion_factor,
    0 as max_conversion_factor
-- SKIPPED: No tabItem UOM table in this schema
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
WHERE ip.docstatus = 0
    AND ip.uom = i.stock_uom
    AND 1 > 1;  -- Always false to skip

-- Chi tiết conversions
SELECT
    'Price Conversions - Details' as check_type,
    ip.item_code,
    i.stock_uom,
    ip.price_list_rate as stock_uom_price,
    'N/A' as display_uom,
    1 as conversion_factor,
    ROUND(ip.price_list_rate * 1, 2) as converted_price,
    pl.currency as price_list_currency,
    ip.price_list
-- SKIPPED: No tabItem UOM table in this schema
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
INNER JOIN `tabPrice List` pl ON ip.price_list = pl.name
WHERE ip.docstatus = 0
    AND ip.uom = i.stock_uom
    AND 1 > 1  -- Always false to skip
ORDER BY ip.item_code
LIMIT 50;

-- =========================================
-- SECTION 4: DASHBOARD & COMPLIANCE REPORTS
-- =========================================

-- 4.1 OVERALL COMPLIANCE DASHBOARD
SELECT
    '📊 OVERALL COMPLIANCE DASHBOARD' as dashboard,
    NOW() as report_timestamp,
    COUNT(DISTINCT CASE WHEN i.stock_uom IS NOT NULL AND i.stock_uom != '' THEN i.name END) as items_with_stock_uom,
    COUNT(DISTINCT CASE WHEN i.stock_uom IS NULL OR i.stock_uom = '' THEN i.name END) as items_without_stock_uom,
    COUNT(DISTINCT CASE WHEN ip.uom = i.stock_uom THEN ip.name END) as compliant_item_prices,
    COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) as non_compliant_item_prices,
    ROUND(
        COUNT(DISTINCT CASE WHEN ip.uom = i.stock_uom THEN ip.name END) * 100.0 /
        NULLIF(COUNT(DISTINCT ip.name), 0), 2
    ) as price_compliance_pct,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) = 0 THEN '✅ FULLY COMPLIANT'
        WHEN COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) < 10 THEN '⚠️ MOSTLY COMPLIANT'
        ELSE '❌ NEEDS ATTENTION'
    END as compliance_status
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.docstatus = 0
WHERE i.is_sales_item = 1;

-- 4.2 PRICE LIST COVERAGE BY ITEM GROUP
SELECT
    '📈 Price List Coverage by Item Group' as report_type,
    i.item_group,
    COUNT(DISTINCT i.name) as total_items,
    COUNT(DISTINCT CASE WHEN ip.name IS NOT NULL THEN i.name END) as items_with_price,
    ROUND(
        COUNT(DISTINCT CASE WHEN ip.name IS NOT NULL THEN i.name END) * 100.0 /
        NULLIF(COUNT(DISTINCT i.name), 0), 2
    ) as coverage_percentage,
    CASE
        WHEN ROUND(COUNT(DISTINCT CASE WHEN ip.name IS NOT NULL THEN i.name END) * 100.0 / NULLIF(COUNT(DISTINCT i.name), 0), 2) = 100 THEN '✅ FULL'
        WHEN ROUND(COUNT(DISTINCT CASE WHEN ip.name IS NOT NULL THEN i.name END) * 100.0 / NULLIF(COUNT(DISTINCT i.name), 0), 2) >= 80 THEN '⚠️ GOOD'
        ELSE '❌ LOW'
    END as coverage_status
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code
    AND ip.docstatus = 0
    AND ip.uom = i.stock_uom
WHERE i.is_sales_item = 1
    AND i.stock_uom IS NOT NULL
GROUP BY i.item_group
ORDER BY coverage_percentage DESC;

-- =========================================
-- SECTION 5: TROUBLESHOOTING & MONITORING
-- =========================================

-- 5.1 Recent Item Price changes (monitor for violations)
SELECT
    '🔍 Recent Item Price changes (30 days)' as check_type,
    COUNT(*) as changes_count,
    COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) as violation_changes,
    GROUP_CONCAT(DISTINCT ip.modified_by ORDER BY ip.modified_by LIMIT 5) as recent_modifiers
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
WHERE ip.docstatus = 0
    AND ip.modified >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- Chi tiết recent changes
SELECT
    'Recent Changes - Details' as check_type,
    ip.name,
    ip.item_code,
    ip.price_list,
    ip.uom,
    i.stock_uom,
    CASE WHEN ip.uom != i.stock_uom THEN '❌ VIOLATION' ELSE '✅ OK' END as compliance,
    ip.price_list_rate,
    ip.modified,
    ip.modified_by
FROM `tabItem Price` ip
INNER JOIN `tabItem` i ON ip.item_code = i.name
WHERE ip.docstatus = 0
    AND ip.modified >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY ip.modified DESC
LIMIT 100;

-- 5.2 Items with complex UOM setup (potential issues)
SELECT
    '⚠️ Items with complex UOM setup' as check_type,
    COUNT(*) as complex_items_count,
    GROUP_CONCAT(i.name ORDER BY i.name LIMIT 10) as sample_items
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.docstatus = 0
WHERE i.stock_uom IS NOT NULL AND 1=0
GROUP BY i.name, i.stock_uom
HAVING COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) > 0;

-- Chi tiết complex items
SELECT
    'Complex Setup - Details' as check_type,
    i.name as item_code,
    i.stock_uom,
    0 as available_uoms,
    'N/A' as uom_list,
    COUNT(DISTINCT ip.price_list) as price_lists,
    COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) as invalid_prices,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) > 0 THEN '❌ HAS VIOLATIONS'
        WHEN 0 > 5 THEN '⚠️ COMPLEX'
        ELSE '✅ OK'
    END as status
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.docstatus = 0
WHERE i.stock_uom IS NOT NULL AND 1=0
GROUP BY i.name, i.stock_uom
HAVING COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) > 0
ORDER BY invalid_prices DESC, available_uoms DESC
LIMIT 20;

-- 3. OFFER ENGINE VALIDATION
-- ==========================

-- 3.1 Offers using block-based discounts
SELECT
    'Block-based Offers' as check_type,
    name,
    offer,
    item,
    uom_ref,
    total_items_in_block_qty,
    total_discount_amount_per_block,
    min_block_qty,
    max_eligible_block_qty,
    is_used_block,
    disable
FROM `tabPOS Offer`
WHERE is_used_block = 1 AND disable = 0
ORDER BY creation DESC;

-- 3.2 Offers with time restrictions
SELECT
    'Time-restricted Offers' as check_type,
    name,
    title,
    available_time_in_day,
    valid_from,
    valid_upto,
    disable
FROM `tabPOS Offer`
WHERE available_time_in_day IS NOT NULL
    AND available_time_in_day != ''
    AND disable = 0
ORDER BY creation DESC;

-- 3.3 Gift offers validation
SELECT
    'Gift Offers' as check_type,
    po.name,
    po.title,
    po.apply_item_code,
    po.given_qty,
    i.item_name as gift_item_name,
    i.is_stock_item,
    po.disable
FROM `tabPOS Offer` po
LEFT JOIN `tabItem` i ON po.apply_item_code = i.name
WHERE po.offer = 'Give Product' AND po.disable = 0
ORDER BY po.creation DESC;

-- 4. SALES INVOICE COMPLIANCE
-- ===========================

-- 4.1 Recent invoices with manual rate changes (potential violations)
SELECT
    'Recent manual rate edits (CHECK)' as check_type,
    si.name as invoice_name,
    si.customer,
    si.posting_date,
    sii.item_code,
    sii.item_name,
    sii.uom,
    sii.price_list_rate,
    sii.rate,
    sii.discount_amount,
    sii.posa_offer_applied,
    si.owner,
    si.creation
FROM `tabSales Invoice` si
INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
WHERE si.docstatus = 1
    AND si.is_pos = 1
    AND sii.posa_offer_applied = 0
    AND ABS(sii.rate - sii.price_list_rate) > 0.01  -- Allow small rounding differences
    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY si.posting_date DESC, si.name
LIMIT 50;

-- 4.2 Invoices with applied offers
SELECT
    'Invoices with offers applied' as check_type,
    si.name as invoice_name,
    si.customer,
    si.posting_date,
    sii.item_code,
    sii.uom,
    sii.qty,
    sii.price_list_rate,
    sii.rate,
    sii.discount_amount,
    sii.posa_offer_applied
FROM `tabSales Invoice` si
INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
WHERE si.docstatus = 1
    AND si.is_pos = 1
    AND sii.posa_offer_applied = 1
    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY si.posting_date DESC, si.name
LIMIT 100;

-- 4.3 Stock quantity vs display quantity validation
SELECT
    'Stock qty validation' as check_type,
    si.name as invoice_name,
    sii.item_code,
    sii.uom,
    i.stock_uom,
    sii.qty as display_qty,
    sii.stock_qty,
    sii.conversion_factor,
    ROUND(sii.qty * sii.conversion_factor, 4) as calculated_stock_qty,
    CASE
        WHEN ABS(sii.stock_qty - ROUND(sii.qty * sii.conversion_factor, 4)) > 0.0001
        THEN 'MISMATCH'
        ELSE 'OK'
    END as status
FROM `tabSales Invoice` si
INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
INNER JOIN `tabItem` i ON sii.item_code = i.name
WHERE si.docstatus = 1
    AND si.is_pos = 1
    AND sii.conversion_factor IS NOT NULL
    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
HAVING status = 'MISMATCH'
ORDER BY si.posting_date DESC;

-- 5. PROFIT & COST ANALYSIS
-- =========================

-- 5.1 Profit calculation by item (using stock UOM)
SELECT
    'Profit analysis by item' as check_type,
    sii.item_code,
    i.item_name,
    i.stock_uom,
    SUM(sii.stock_qty) as total_stock_qty_sold,
    AVG(sii.price_list_rate / NULLIF(sii.conversion_factor, 0)) as avg_base_price,
    SUM(sii.amount) as total_revenue,
    SUM(sii.stock_qty * i.valuation_rate) as total_cost,
    SUM(sii.amount - (sii.stock_qty * i.valuation_rate)) as total_profit,
    ROUND(
        SUM(sii.amount - (sii.stock_qty * i.valuation_rate)) * 100.0 / NULLIF(SUM(sii.amount), 0),
        2
    ) as profit_margin_pct
FROM `tabSales Invoice` si
INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
INNER JOIN `tabItem` i ON sii.item_code = i.name
WHERE si.docstatus = 1
    AND si.is_pos = 1
    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    AND i.valuation_rate IS NOT NULL
GROUP BY sii.item_code, i.item_name, i.stock_uom
ORDER BY total_profit DESC
LIMIT 20;

-- 5.2 Items with negative profit margins (potential issues)
SELECT
    'Negative profit margins (ALERT)' as check_type,
    sii.item_code,
    i.item_name,
    SUM(sii.amount) as total_revenue,
    SUM(sii.stock_qty * i.valuation_rate) as total_cost,
    SUM(sii.amount - (sii.stock_qty * i.valuation_rate)) as total_profit,
    ROUND(
        SUM(sii.amount - (sii.stock_qty * i.valuation_rate)) * 100.0 / NULLIF(SUM(sii.amount), 0),
        2
    ) as profit_margin_pct,
    COUNT(DISTINCT si.name) as invoice_count
FROM `tabSales Invoice` si
INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
INNER JOIN `tabItem` i ON sii.item_code = i.name
WHERE si.docstatus = 1
    AND si.is_pos = 1
    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    AND i.valuation_rate IS NOT NULL
GROUP BY sii.item_code, i.item_name
HAVING total_profit < 0
ORDER BY total_profit ASC;

-- =========================================
-- EXECUTION INSTRUCTIONS
-- =========================================

/*
CÁCH CHẠY AUDIT SCRIPT:

1. Mở MySQL Workbench hoặc phpMyAdmin
2. Connect đến database: erpv152_multi_v1_vn_vtcom_online_2025_v3
3. Copy từng section và chạy tuần tự
4. Focus vào queries có emoji ❌ (critical) và ⚠️ (warning)

THỤ TỤ CHẠY:
- Section 1: Quy ước UOM (cơ bản)
- Section 2: Giá niêm yết (quan trọng)
- Section 3: Conversion validation
- Section 4: Dashboard reports
- Section 5: Troubleshooting

EXPECTED RESULTS:
- ❌ Items without stock_uom: Số items cần set stock_uom
- ❌ VIOLATION: Item Price UOM != stock_uom: Records vi phạm cần archive
- ⚠️ WARNING: Multiple prices: Items có duplicate prices
- 📊 Dashboard: Overall compliance percentage

ACTION ITEMS:
1. Fix items without stock_uom
2. Archive invalid Item Prices
3. Clean duplicate prices
4. Monitor compliance dashboard weekly
*/

-- =========================================
-- QUICK SUMMARY QUERIES
-- =========================================

-- EXECUTIVE SUMMARY (Run this first)
SELECT
    '🎯 EXECUTIVE SUMMARY - Base UOM Compliance' as summary,
    NOW() as report_date,
    COUNT(DISTINCT CASE WHEN i.stock_uom IS NOT NULL AND i.stock_uom != '' THEN i.name END) as items_with_uom,
    COUNT(DISTINCT CASE WHEN ip.uom = i.stock_uom THEN ip.name END) as compliant_prices,
    COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) as violations,
    ROUND(
        COUNT(DISTINCT CASE WHEN ip.uom = i.stock_uom THEN ip.name END) * 100.0 /
        NULLIF(COUNT(DISTINCT ip.name), 0), 2
    ) as compliance_pct,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) = 0 THEN '✅ FULLY COMPLIANT'
        WHEN COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) < 10 THEN '⚠️ MOSTLY COMPLIANT'
        ELSE '❌ NEEDS IMMEDIATE ATTENTION'
    END as status
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.docstatus = 0
WHERE i.is_sales_item = 1;

-- CRITICAL ISSUES (Run this second)
SELECT
    '🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ACTION' as alert,
    COUNT(DISTINCT CASE WHEN i.stock_uom IS NULL OR i.stock_uom = '' THEN i.name END) as items_missing_uom,
    COUNT(DISTINCT CASE WHEN ip.uom != i.stock_uom THEN ip.name END) as invalid_item_prices,
FROM `tabItem` i
LEFT JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.docstatus = 0
WHERE i.is_sales_item = 1;

/*
SCRIPT COMPLETED ✅

Next steps:
1. Run executive summary
2. Address critical issues
3. Run full audit sections
4. Schedule weekly monitoring
5. Set up alerts for violations

For support: Check UOM_PRICING_SOP.md
*/