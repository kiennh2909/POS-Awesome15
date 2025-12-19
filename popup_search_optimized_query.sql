-- 🔍 POPUP SEARCH OPTIMIZED QUERY
-- Tối ưu cho F3 Product Search Popup trong ItemsSelector.vue

-- =====================================================
-- 1. QUERY CHÍNH CHO POPUP SEARCH
-- =====================================================

-- Query này được tối ưu cho searchItemsByText() method
-- Hỗ trợ tìm kiếm theo: Tên sản phẩm, SKU, Barcode (exact/partial)
-- Với prioritization theo spec popup

SELECT 
    -- Thông tin cơ bản
    ip.item_code,
    ip.item_name,
    ip.price_list_rate as rate,
    ip.currency,
    ip.uom as stock_uom,
    ip.custom_vat_rate,
    ip.custom_price_list_rate_after_vat,
    
    -- Thông tin barcode (JSON array cho frontend)
    CONCAT('[', 
        GROUP_CONCAT(
            DISTINCT CONCAT('{"barcode":"', ib.barcode, '","posa_uom":"', IFNULL(ib.posa_uom, ip.uom), '"}')
            ORDER BY ib.barcode
            SEPARATOR ','
        ), 
    ']') as item_barcode,
    
    -- Thông tin tồn kho
    IFNULL(b.actual_qty, 0) as actual_qty,
    IFNULL(b.reserved_qty, 0) as reserved_qty,
    (IFNULL(b.actual_qty, 0) - IFNULL(b.reserved_qty, 0)) as available_qty,
    b.warehouse,
    
    -- Match scoring cho prioritization
    CASE 
        -- 1️⃣ Exact barcode match (highest priority - score 100)
        WHEN EXISTS (
            SELECT 1 FROM `tabItem Barcode` ib2 
            WHERE ib2.parent = ip.item_code 
            AND ib2.barcode = :search_term
        ) THEN 100
        
        -- 2️⃣ Partial barcode match (score 90)
        WHEN EXISTS (
            SELECT 1 FROM `tabItem Barcode` ib2 
            WHERE ib2.parent = ip.item_code 
            AND ib2.barcode LIKE CONCAT('%', :search_term, '%')
        ) THEN 90
        
        -- 3️⃣ SKU starts-with (score 80)
        WHEN ip.item_code LIKE CONCAT(:search_term, '%') THEN 80
        
        -- 4️⃣ SKU contains (score 70)
        WHEN ip.item_code LIKE CONCAT('%', :search_term, '%') THEN 70
        
        -- 5️⃣ Name exact match (score 60)
        WHEN LOWER(ip.item_name) = LOWER(:search_term) THEN 60
        
        -- 6️⃣ Name starts-with (score 50)
        WHEN LOWER(ip.item_name) LIKE CONCAT(LOWER(:search_term), '%') THEN 50
        
        -- 7️⃣ Name contains (score 40)
        WHEN LOWER(ip.item_name) LIKE CONCAT('%', LOWER(:search_term), '%') THEN 40
        
        ELSE 0
    END as match_score,
    
    -- Match type for debugging
    CASE 
        WHEN EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode = :search_term) THEN 'barcode_exact'
        WHEN EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode LIKE CONCAT('%', :search_term, '%')) THEN 'barcode_partial'
        WHEN ip.item_code LIKE CONCAT(:search_term, '%') THEN 'sku_starts'
        WHEN ip.item_code LIKE CONCAT('%', :search_term, '%') THEN 'sku_contains'
        WHEN LOWER(ip.item_name) = LOWER(:search_term) THEN 'name_exact'
        WHEN LOWER(ip.item_name) LIKE CONCAT(LOWER(:search_term), '%') THEN 'name_starts'
        WHEN LOWER(ip.item_name) LIKE CONCAT('%', LOWER(:search_term), '%') THEN 'name_contains'
        ELSE 'no_match'
    END as match_type,
    
    -- Additional fields for popup display
    CASE 
        WHEN IFNULL(b.actual_qty, 0) <= 0 THEN 'Hết tồn'
        ELSE 'Có sẵn'
    END as status_text,
    
    CASE 
        WHEN IFNULL(b.actual_qty, 0) <= 0 THEN 'warning'
        ELSE 'success'
    END as status_color

FROM `tabItem Price` ip

-- LEFT JOIN để lấy barcode (không bắt buộc)
LEFT JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent

-- LEFT JOIN để lấy tồn kho (không bắt buộc)
LEFT JOIN `tabBin` b ON ip.item_code = b.item_code 
    AND b.warehouse = :warehouse  -- Sẽ được thay bằng warehouse từ POS Profile

WHERE 
    -- ✅ Bỏ tất cả validation restrictions theo yêu cầu
    -- Chỉ filter theo Price List và search term
    ip.price_list = :price_list
    AND ip.selling = 1
    AND ip.valid_from <= CURDATE()
    AND (ip.valid_upto IS NULL OR ip.valid_upto >= CURDATE())
    
    -- Search conditions (OR logic)
    AND (
        -- Barcode search (exact và partial)
        EXISTS (
            SELECT 1 FROM `tabItem Barcode` ib2 
            WHERE ib2.parent = ip.item_code 
            AND (
                ib2.barcode = :search_term 
                OR ib2.barcode LIKE CONCAT('%', :search_term, '%')
            )
        )
        
        -- SKU search
        OR ip.item_code LIKE CONCAT('%', :search_term, '%')
        
        -- Name search (case insensitive)
        OR LOWER(ip.item_name) LIKE CONCAT('%', LOWER(:search_term), '%')
    )

GROUP BY 
    ip.item_code, ip.item_name, ip.price_list_rate, ip.currency, 
    ip.uom, ip.custom_vat_rate, ip.custom_price_list_rate_after_vat,
    b.actual_qty, b.reserved_qty, b.warehouse

HAVING match_score > 0  -- Chỉ lấy items có match

ORDER BY 
    match_score DESC,  -- Ưu tiên theo score
    ip.item_name ASC   -- Sau đó sort theo tên

LIMIT 100;  -- Tăng limit lên 100 theo yêu cầu

-- =====================================================
-- 2. QUERY CHO EXACT BARCODE SEARCH (API)
-- =====================================================

-- Dành cho getItemByBarcodeExact() method
SELECT 
    ip.item_code,
    ip.item_name,
    ip.price_list_rate as rate,
    ip.currency,
    ib.posa_uom as uom,  -- Ưu tiên UOM từ barcode
    ip.custom_vat_rate,
    ip.custom_price_list_rate_after_vat,
    
    -- Barcode info
    ib.barcode,
    ib.posa_uom,
    
    -- Stock info
    IFNULL(b.actual_qty, 0) as actual_qty,
    b.warehouse,
    
    -- Item UOMs (JSON format)
    CONCAT('[{"uom":"', ib.posa_uom, '","conversion_factor":1.0}]') as item_uoms

FROM `tabItem Price` ip

-- INNER JOIN vì cần có barcode
INNER JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent

-- LEFT JOIN cho stock
LEFT JOIN `tabBin` b ON ip.item_code = b.item_code 
    AND b.warehouse = :warehouse

WHERE 
    ib.barcode = :barcode  -- Exact match
    AND ip.price_list = :price_list
    AND ip.selling = 1
    AND ip.valid_from <= CURDATE()
    AND (ip.valid_upto IS NULL OR ip.valid_upto >= CURDATE())

LIMIT 1;

-- =====================================================
-- 3. QUERY KIỂM TRA PERFORMANCE
-- =====================================================

-- 3.1 Test search performance với different terms
EXPLAIN SELECT COUNT(*) 
FROM `tabItem Price` ip
LEFT JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent
WHERE 
    ip.price_list = 'Standard Selling'
    AND ip.selling = 1
    AND (
        EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode LIKE '%test%')
        OR ip.item_code LIKE '%test%'
        OR LOWER(ip.item_name) LIKE '%test%'
    );

-- 3.2 Test exact barcode performance
EXPLAIN SELECT * 
FROM `tabItem Price` ip
INNER JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent
WHERE ib.barcode = 'test_barcode';

-- =====================================================
-- 4. INDEXES ĐỀ XUẤT CHO PERFORMANCE
-- =====================================================

-- Indexes cần thiết để tối ưu query:

-- 4.1 Index cho Item Price
/*
CREATE INDEX idx_item_price_search ON `tabItem Price` (price_list, selling, valid_from, valid_upto);
CREATE INDEX idx_item_price_item_code ON `tabItem Price` (item_code);
CREATE INDEX idx_item_price_item_name ON `tabItem Price` (item_name);
*/

-- 4.2 Index cho Item Barcode  
/*
CREATE INDEX idx_item_barcode_search ON `tabItem Barcode` (barcode, parent);
CREATE INDEX idx_item_barcode_parent ON `tabItem Barcode` (parent);
*/

-- 4.3 Index cho Bin
/*
CREATE INDEX idx_bin_search ON `tabBin` (item_code, warehouse, actual_qty);
*/

-- =====================================================
-- 5. PYTHON API IMPLEMENTATION TEMPLATE
-- =====================================================

/*
# Template cho API method trong Frappe

@frappe.whitelist()
def search_items_for_popup(search_term, pos_profile, price_list, warehouse, limit=100):
    """
    Optimized search for F3 popup
    """
    
    # Validate inputs
    if not search_term or len(search_term.strip()) < 2:
        return []
    
    search_term = search_term.strip()
    
    # Use the optimized query above
    query = """
        SELECT 
            ip.item_code, ip.item_name, ip.price_list_rate as rate,
            ip.currency, ip.uom as stock_uom, ip.custom_vat_rate,
            ip.custom_price_list_rate_after_vat,
            
            -- Barcode array
            CONCAT('[', 
                GROUP_CONCAT(
                    DISTINCT CONCAT('{"barcode":"', ib.barcode, '","posa_uom":"', IFNULL(ib.posa_uom, ip.uom), '"}')
                    ORDER BY ib.barcode SEPARATOR ','
                ), 
            ']') as item_barcode,
            
            -- Stock info
            IFNULL(b.actual_qty, 0) as actual_qty,
            
            -- Match scoring
            CASE 
                WHEN EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode = %(search_term)s) THEN 100
                WHEN EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode LIKE %(search_pattern)s) THEN 90
                WHEN ip.item_code LIKE %(search_start)s THEN 80
                WHEN ip.item_code LIKE %(search_pattern)s THEN 70
                WHEN LOWER(ip.item_name) = LOWER(%(search_term)s) THEN 60
                WHEN LOWER(ip.item_name) LIKE %(search_start_lower)s THEN 50
                WHEN LOWER(ip.item_name) LIKE %(search_pattern_lower)s THEN 40
                ELSE 0
            END as match_score
            
        FROM `tabItem Price` ip
        LEFT JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent
        LEFT JOIN `tabBin` b ON ip.item_code = b.item_code AND b.warehouse = %(warehouse)s
        
        WHERE 
            ip.price_list = %(price_list)s
            AND ip.selling = 1
            AND ip.valid_from <= CURDATE()
            AND (ip.valid_upto IS NULL OR ip.valid_upto >= CURDATE())
            AND (
                EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND (ib2.barcode = %(search_term)s OR ib2.barcode LIKE %(search_pattern)s))
                OR ip.item_code LIKE %(search_pattern)s
                OR LOWER(ip.item_name) LIKE %(search_pattern_lower)s
            )
            
        GROUP BY ip.item_code, ip.item_name, ip.price_list_rate, ip.currency, ip.uom, ip.custom_vat_rate, ip.custom_price_list_rate_after_vat, b.actual_qty
        HAVING match_score > 0
        ORDER BY match_score DESC, ip.item_name ASC
        LIMIT %(limit)s
    """
    
    # Parameters
    params = {
        'search_term': search_term,
        'search_pattern': f'%{search_term}%',
        'search_start': f'{search_term}%',
        'search_pattern_lower': f'%{search_term.lower()}%',
        'search_start_lower': f'{search_term.lower()}%',
        'price_list': price_list,
        'warehouse': warehouse,
        'limit': limit
    }
    
    # Execute query
    results = frappe.db.sql(query, params, as_dict=True)
    
    # Process barcode JSON
    for item in results:
        try:
            item['item_barcode'] = json.loads(item['item_barcode'] or '[]')
        except:
            item['item_barcode'] = []
    
    return results

@frappe.whitelist()
def get_item_by_barcode_exact_optimized(barcode, pos_profile, price_list, warehouse):
    """
    Optimized exact barcode search
    """
    query = """
        SELECT 
            ip.item_code, ip.item_name, ip.price_list_rate as rate,
            ip.currency, ib.posa_uom as uom, ip.custom_vat_rate,
            ip.custom_price_list_rate_after_vat, ib.barcode, ib.posa_uom,
            IFNULL(b.actual_qty, 0) as actual_qty, b.warehouse,
            CONCAT('[{"uom":"', ib.posa_uom, '","conversion_factor":1.0}]') as item_uoms
            
        FROM `tabItem Price` ip
        INNER JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent
        LEFT JOIN `tabBin` b ON ip.item_code = b.item_code AND b.warehouse = %(warehouse)s
        
        WHERE 
            ib.barcode = %(barcode)s
            AND ip.price_list = %(price_list)s
            AND ip.selling = 1
            AND ip.valid_from <= CURDATE()
            AND (ip.valid_upto IS NULL OR ip.valid_upto >= CURDATE())
            
        LIMIT 1
    """
    
    result = frappe.db.sql(query, {
        'barcode': barcode,
        'price_list': price_list,
        'warehouse': warehouse
    }, as_dict=True)
    
    if result:
        item = result[0]
        try:
            item['item_uoms'] = json.loads(item['item_uoms'] or '[]')
        except:
            item['item_uoms'] = []
        return item
    
    return None
*/

-- =====================================================
-- 6. HƯỚNG DẪN TÍCH HỢP VÀO ITEMSSELECTOR.VUE
-- =====================================================

/*
CÁCH TÍCH HỢP:

1. Tạo API methods mới trong Python (template ở section 5)

2. Update searchItemsByText() method trong ItemsSelector.vue:
   - Gọi API search_items_for_popup thay vì search local
   - Sử dụng kết quả có sẵn match_score để sort
   - Không cần xử lý prioritization ở frontend

3. Update getItemByBarcodeExact() method:
   - Gọi API get_item_by_barcode_exact_optimized
   - Kết quả đã có đầy đủ thông tin cần thiết

4. Performance benefits:
   - Giảm tải cho frontend
   - Search nhanh hơn với database indexes
   - Kết quả đã được sort theo priority
   - Hỗ trợ search term phức tạp

5. Backward compatibility:
   - Giữ nguyên fallback logic hiện tại
   - Chỉ thay đổi khi API available
*/