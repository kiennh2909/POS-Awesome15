# 🔍 OPTIMIZED POPUP SEARCH API
# Tối ưu cho F3 Product Search Popup trong ItemsSelector.vue

import frappe
import json
from frappe import _

@frappe.whitelist()
def search_items_for_popup(search_term, pos_profile, price_list=None, warehouse=None, limit=100):
    """
    Optimized search for F3 popup - replaces searchItemsByText() method
    
    Args:
        search_term: Search query from user
        pos_profile: POS Profile name or JSON string
        price_list: Price list to search in
        warehouse: Warehouse for stock info
        limit: Maximum results to return
    
    Returns:
        List of items with match scoring and prioritization
    """
    
    # Validate inputs
    if not search_term or len(search_term.strip()) < 2:
        return []
    
    search_term = search_term.strip()
    
    # Parse POS Profile if JSON string
    if isinstance(pos_profile, str) and pos_profile.startswith('{'):
        try:
            pos_profile_data = json.loads(pos_profile)
            pos_profile_name = pos_profile_data.get('name')
            warehouse = warehouse or pos_profile_data.get('warehouse')
            price_list = price_list or pos_profile_data.get('selling_price_list')
        except:
            pos_profile_name = pos_profile
    else:
        pos_profile_name = pos_profile
        
    # Get POS Profile data if needed
    if not warehouse or not price_list:
        profile_doc = frappe.get_doc('POS Profile', pos_profile_name)
        warehouse = warehouse or profile_doc.warehouse
        price_list = price_list or profile_doc.selling_price_list
    
    # Optimized query with match scoring
    query = """
        SELECT 
            ip.item_code,
            ip.item_name,
            ip.price_list_rate as rate,
            ip.currency,
            ip.uom as stock_uom,
            ip.custom_vat_rate,
            ip.custom_price_list_rate_after_vat,
            
            -- Barcode array (JSON format for frontend)
            CASE 
                WHEN COUNT(ib.barcode) > 0 THEN
                    CONCAT('[', 
                        GROUP_CONCAT(
                            DISTINCT CONCAT(
                                '{"barcode":"', ib.barcode, 
                                '","posa_uom":"', IFNULL(ib.posa_uom, ip.uom), '"}'
                            )
                            ORDER BY ib.barcode SEPARATOR ','
                        ), 
                    ']')
                ELSE '[]'
            END as item_barcode,
            
            -- Stock info
            IFNULL(b.actual_qty, 0) as actual_qty,
            IFNULL(b.reserved_qty, 0) as reserved_qty,
            (IFNULL(b.actual_qty, 0) - IFNULL(b.reserved_qty, 0)) as available_qty,
            b.warehouse,
            
            -- Match scoring for prioritization (as per spec)
            CASE 
                -- 1️⃣ Exact barcode match (score 100)
                WHEN EXISTS (
                    SELECT 1 FROM `tabItem Barcode` ib2 
                    WHERE ib2.parent = ip.item_code 
                    AND ib2.barcode = %(search_term)s
                ) THEN 100
                
                -- 2️⃣ Partial barcode match (score 90)
                WHEN EXISTS (
                    SELECT 1 FROM `tabItem Barcode` ib2 
                    WHERE ib2.parent = ip.item_code 
                    AND ib2.barcode LIKE %(search_pattern)s
                ) THEN 90
                
                -- 3️⃣ SKU starts-with (score 80)
                WHEN ip.item_code LIKE %(search_start)s THEN 80
                
                -- 4️⃣ SKU contains (score 70)
                WHEN ip.item_code LIKE %(search_pattern)s THEN 70
                
                -- 5️⃣ Name exact match (score 60)
                WHEN LOWER(ip.item_name) = LOWER(%(search_term)s) THEN 60
                
                -- 6️⃣ Name starts-with (score 50)
                WHEN LOWER(ip.item_name) LIKE %(search_start_lower)s THEN 50
                
                -- 7️⃣ Name contains (score 40)
                WHEN LOWER(ip.item_name) LIKE %(search_pattern_lower)s THEN 40
                
                ELSE 0
            END as match_score,
            
            -- Match type for debugging
            CASE 
                WHEN EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode = %(search_term)s) THEN 'barcode_exact'
                WHEN EXISTS (SELECT 1 FROM `tabItem Barcode` ib2 WHERE ib2.parent = ip.item_code AND ib2.barcode LIKE %(search_pattern)s) THEN 'barcode_partial'
                WHEN ip.item_code LIKE %(search_start)s THEN 'sku_starts'
                WHEN ip.item_code LIKE %(search_pattern)s THEN 'sku_contains'
                WHEN LOWER(ip.item_name) = LOWER(%(search_term)s) THEN 'name_exact'
                WHEN LOWER(ip.item_name) LIKE %(search_start_lower)s THEN 'name_starts'
                WHEN LOWER(ip.item_name) LIKE %(search_pattern_lower)s THEN 'name_contains'
                ELSE 'no_match'
            END as _matchType,
            
            -- Status for popup display
            CASE 
                WHEN IFNULL(b.actual_qty, 0) <= 0 THEN 'Hết tồn'
                ELSE 'Có sẵn'
            END as status_text,
            
            CASE 
                WHEN IFNULL(b.actual_qty, 0) <= 0 THEN 'warning'
                ELSE 'success'
            END as status_color,
            
            -- Variant info for popup table
            CASE 
                WHEN ip.item_code != ip.item_name THEN ip.item_code
                ELSE ''
            END as variant_info

        FROM `tabItem Price` ip

        -- LEFT JOIN để lấy barcode (không bắt buộc)
        LEFT JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent

        -- LEFT JOIN để lấy tồn kho (không bắt buộc)
        LEFT JOIN `tabBin` b ON ip.item_code = b.item_code 
            AND b.warehouse = %(warehouse)s

        WHERE 
            -- ✅ Bỏ tất cả validation restrictions theo yêu cầu
            -- Chỉ filter theo Price List và search term
            ip.price_list = %(price_list)s
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
                        ib2.barcode = %(search_term)s 
                        OR ib2.barcode LIKE %(search_pattern)s
                    )
                )
                
                -- SKU search
                OR ip.item_code LIKE %(search_pattern)s
                
                -- Name search (case insensitive)
                OR LOWER(ip.item_name) LIKE %(search_pattern_lower)s
            )

        GROUP BY 
            ip.item_code, ip.item_name, ip.price_list_rate, ip.currency, 
            ip.uom, ip.custom_vat_rate, ip.custom_price_list_rate_after_vat,
            b.actual_qty, b.reserved_qty, b.warehouse

        HAVING match_score > 0  -- Chỉ lấy items có match

        ORDER BY 
            match_score DESC,  -- Ưu tiên theo score
            ip.item_name ASC   -- Sau đó sort theo tên

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
        'limit': int(limit)
    }
    
    try:
        # Execute query
        results = frappe.db.sql(query, params, as_dict=True)
        
        # Process results
        for item in results:
            # Parse barcode JSON
            try:
                item['item_barcode'] = json.loads(item['item_barcode'] or '[]')
            except:
                item['item_barcode'] = []
            
            # Ensure required fields
            item['rate'] = item.get('rate', 0)
            item['actual_qty'] = item.get('actual_qty', 0)
            
            # Add original currency info
            item['original_currency'] = item.get('currency')
            item['original_rate'] = item.get('rate')
            
        return results
        
    except Exception as e:
        frappe.log_error(f"Popup search error: {str(e)}", "Popup Search API")
        return []


@frappe.whitelist()
def get_item_by_barcode_exact_optimized(barcode, pos_profile, price_list=None, warehouse=None, customer=None):
    """
    Optimized exact barcode search - replaces getItemByBarcodeExact() method
    
    Args:
        barcode: Exact barcode to search for
        pos_profile: POS Profile name or JSON string
        price_list: Price list to search in
        warehouse: Warehouse for stock info
        customer: Customer for pricing (optional)
    
    Returns:
        Single item dict or None
    """
    
    if not barcode or not barcode.strip():
        return None
        
    barcode = barcode.strip()
    
    # Parse POS Profile if JSON string
    if isinstance(pos_profile, str) and pos_profile.startswith('{'):
        try:
            pos_profile_data = json.loads(pos_profile)
            pos_profile_name = pos_profile_data.get('name')
            warehouse = warehouse or pos_profile_data.get('warehouse')
            price_list = price_list or pos_profile_data.get('selling_price_list')
        except:
            pos_profile_name = pos_profile
    else:
        pos_profile_name = pos_profile
        
    # Get POS Profile data if needed
    if not warehouse or not price_list:
        profile_doc = frappe.get_doc('POS Profile', pos_profile_name)
        warehouse = warehouse or profile_doc.warehouse
        price_list = price_list or profile_doc.selling_price_list
    
    # Optimized exact barcode query
    query = """
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
            IFNULL(b.reserved_qty, 0) as reserved_qty,
            b.warehouse,
            
            -- Item UOMs (JSON format)
            CONCAT('[{"uom":"', IFNULL(ib.posa_uom, ip.uom), '","conversion_factor":1.0}]') as item_uoms,
            
            -- Additional fields for compatibility
            ip.uom as stock_uom,
            ip.item_name as item_name,
            
            -- Pricing fields
            ip.price_list_rate as price_list_rate,
            ip.price_list_rate as base_price_list_rate,
            ip.currency as original_currency,
            ip.price_list_rate as original_rate

        FROM `tabItem Price` ip

        -- INNER JOIN vì cần có barcode
        INNER JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent

        -- LEFT JOIN cho stock
        LEFT JOIN `tabBin` b ON ip.item_code = b.item_code 
            AND b.warehouse = %(warehouse)s

        WHERE 
            ib.barcode = %(barcode)s  -- Exact match
            AND ip.price_list = %(price_list)s
            AND ip.selling = 1
            AND ip.valid_from <= CURDATE()
            AND (ip.valid_upto IS NULL OR ip.valid_upto >= CURDATE())

        LIMIT 1
    """
    
    try:
        result = frappe.db.sql(query, {
            'barcode': barcode,
            'price_list': price_list,
            'warehouse': warehouse
        }, as_dict=True)
        
        if result:
            item = result[0]
            
            # Process item_uoms JSON
            try:
                item['item_uoms'] = json.loads(item['item_uoms'] or '[]')
            except:
                item['item_uoms'] = [{"uom": item.get('uom', 'Nos'), "conversion_factor": 1.0}]
            
            # Ensure required fields
            item['rate'] = item.get('rate', 0)
            item['actual_qty'] = item.get('actual_qty', 0)
            
            # Validate UOM
            if not item.get('uom'):
                frappe.throw(_("Item {0} missing UOM").format(item['item_name']))
            
            # Validate UOM exists in item_uoms
            if item['item_uoms']:
                uom_exists = any(uom.get('uom') == item['uom'] for uom in item['item_uoms'])
                if not uom_exists:
                    frappe.throw(_("Invalid UOM for item {0}").format(item['item_name']))
            
            return item
        
        return None
        
    except Exception as e:
        frappe.log_error(f"Exact barcode search error: {str(e)}", "Exact Barcode API")
        return None


@frappe.whitelist()
def get_popup_search_stats(pos_profile, price_list=None, warehouse=None):
    """
    Get statistics for popup search debugging
    
    Returns:
        Dict with counts and performance info
    """
    
    # Parse POS Profile if JSON string
    if isinstance(pos_profile, str) and pos_profile.startswith('{'):
        try:
            pos_profile_data = json.loads(pos_profile)
            warehouse = warehouse or pos_profile_data.get('warehouse')
            price_list = price_list or pos_profile_data.get('selling_price_list')
        except:
            pass
    
    # Get POS Profile data if needed
    if not warehouse or not price_list:
        try:
            profile_doc = frappe.get_doc('POS Profile', pos_profile)
            warehouse = warehouse or profile_doc.warehouse
            price_list = price_list or profile_doc.selling_price_list
        except:
            pass
    
    stats = {}
    
    try:
        # Total items in price list
        stats['total_items'] = frappe.db.count('Item Price', {
            'price_list': price_list,
            'selling': 1
        })
        
        # Items with barcodes
        barcode_query = """
            SELECT COUNT(DISTINCT ip.item_code) as count
            FROM `tabItem Price` ip
            INNER JOIN `tabItem Barcode` ib ON ip.item_code = ib.parent
            WHERE ip.price_list = %s AND ip.selling = 1
        """
        barcode_result = frappe.db.sql(barcode_query, [price_list], as_dict=True)
        stats['items_with_barcodes'] = barcode_result[0]['count'] if barcode_result else 0
        
        # Items with stock
        stock_query = """
            SELECT COUNT(DISTINCT ip.item_code) as count
            FROM `tabItem Price` ip
            INNER JOIN `tabBin` b ON ip.item_code = b.item_code
            WHERE ip.price_list = %s AND ip.selling = 1 
            AND b.warehouse = %s AND b.actual_qty > 0
        """
        stock_result = frappe.db.sql(stock_query, [price_list, warehouse], as_dict=True)
        stats['items_with_stock'] = stock_result[0]['count'] if stock_result else 0
        
        # Total barcodes
        stats['total_barcodes'] = frappe.db.count('Item Barcode')
        
        stats['price_list'] = price_list
        stats['warehouse'] = warehouse
        
    except Exception as e:
        stats['error'] = str(e)
    
    return stats


# 🔧 INTEGRATION HELPER FUNCTIONS

def integrate_popup_search_api():
    """
    Helper function to integrate optimized search into ItemsSelector.vue
    
    This function provides the JavaScript code to update the frontend
    """
    
    js_integration = """
    // 🔍 INTEGRATION CODE FOR ITEMSSELECTOR.VUE
    
    // 1. Update searchItemsByText method to use optimized API
    async searchItemsByText(searchTerm) {
        try {
            console.info('[Popup] Using optimized API search for:', searchTerm);
            
            const response = await frappe.call({
                method: "posawesome.posawesome.api.items.search_items_for_popup",
                args: {
                    search_term: searchTerm,
                    pos_profile: JSON.stringify(this.pos_profile),
                    price_list: this.active_price_list,
                    warehouse: this.pos_profile.warehouse,
                    limit: 100
                }
            });
            
            if (response.message) {
                console.info('[Popup] API returned', response.message.length, 'results');
                // Results are already sorted by match_score
                return response.message;
            }
            
            return [];
            
        } catch (error) {
            console.warn('[Popup] API search failed, using fallback:', error);
            // Fallback to existing local search
            return this.searchItemsByTextLocal(searchTerm);
        }
    },
    
    // 2. Update getItemByBarcodeExact method to use optimized API
    async getItemByBarcodeExact(barcode, abortSignal = null) {
        try {
            console.info("[ItemsSelector] 🔍 Using optimized API for exact barcode:", barcode);
            
            const response = await frappe.call({
                method: "posawesome.posawesome.api.items.get_item_by_barcode_exact_optimized",
                args: {
                    barcode: barcode,
                    pos_profile: JSON.stringify(this.pos_profile),
                    price_list: this.active_price_list,
                    warehouse: this.pos_profile.warehouse,
                    customer: this.customer
                },
                signal: abortSignal,
            });

            if (response.message) {
                const item = response.message;
                console.info("[ItemsSelector] ✅ Optimized API found:", item.item_code);
                return item;
            }
            
            return null;
            
        } catch (error) {
            console.warn('[ItemsSelector] Optimized API failed, using fallback:', error);
            // Fallback to existing API
            return this.getItemByBarcodeExactFallback(barcode, abortSignal);
        }
    },
    
    // 3. Add debug method for popup search stats
    async getPopupSearchStats() {
        try {
            const response = await frappe.call({
                method: "posawesome.posawesome.api.items.get_popup_search_stats",
                args: {
                    pos_profile: JSON.stringify(this.pos_profile),
                    price_list: this.active_price_list,
                    warehouse: this.pos_profile.warehouse
                }
            });
            
            console.table(response.message);
            return response.message;
            
        } catch (error) {
            console.error('Failed to get popup search stats:', error);
            return null;
        }
    }
    """
    
    return js_integration


if __name__ == "__main__":
    # Print integration instructions
    print("🔍 OPTIMIZED POPUP SEARCH API")
    print("=" * 50)
    print("\n1. Add these methods to your Frappe app:")
    print("   - search_items_for_popup()")
    print("   - get_item_by_barcode_exact_optimized()")
    print("   - get_popup_search_stats()")
    print("\n2. Update ItemsSelector.vue with integration code")
    print("\n3. Test with browser console:")
    print("   - $vm0.getPopupSearchStats()")
    print("   - $vm0.searchItemsByText('test')")
    print("\n4. Monitor performance improvements")