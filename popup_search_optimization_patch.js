// 🔍 POPUP SEARCH OPTIMIZATION PATCH
// Apply this patch to ItemsSelector.vue to use optimized backend API

// =====================================================
// 1. REPLACE searchItemsByText METHOD
// =====================================================

// 🔍 OPTIMIZED: Search items by text using backend API
async searchItemsByText(searchTerm) {
    const term = searchTerm.toLowerCase();
    const originalTerm = searchTerm.trim();

    // 🐛 Debug: Log search parameters
    console.info('[Search] Using optimized API for term:', originalTerm);

    try {
        // 🚀 NEW: Use optimized backend API
        const response = await frappe.call({
            method: "posawesome.posawesome.api.items.search_items_for_popup",
            args: {
                search_term: originalTerm,
                pos_profile: JSON.stringify(this.pos_profile),
                price_list: this.active_price_list,
                warehouse: this.pos_profile.warehouse,
                limit: 100
            }
        });

        if (response.message && response.message.length > 0) {
            console.info('[Search] ✅ API returned', response.message.length, 'results');

            // Results are already sorted by match_score from backend
            // No need for frontend sorting
            return response.message;
        }

        console.info('[Search] ❌ API returned no results');
        return [];

    } catch (error) {
        console.warn('[Search] 🔄 API failed, using local fallback:', error);

        // 🔄 FALLBACK: Use existing local search logic
        return this.searchItemsByTextLocal(originalTerm);
    }
},

// 🔄 FALLBACK: Keep existing local search as backup
async searchItemsByTextLocal(searchTerm) {
    const term = searchTerm.toLowerCase();
    const originalTerm = searchTerm.trim();

    console.info('[Search] Using local fallback for term:', originalTerm);

    const results = [];

    this.items.forEach(item => {
        let matchScore = 0;
        let matchType = '';

        // 1️⃣ Exact barcode match (highest priority)
        if (item.item_barcode && item.item_barcode.some(bc => bc.barcode === originalTerm)) {
            matchScore = 100;
            matchType = 'barcode_exact';
        }
        // 2️⃣ Partial barcode match
        else if (item.item_barcode && item.item_barcode.some(bc => bc.barcode.includes(originalTerm))) {
            matchScore = 90;
            matchType = 'barcode_partial';
        }
        // 3️⃣ SKU starts-with (exact case)
        else if (item.item_code.toLowerCase().startsWith(term)) {
            matchScore = 80;
            matchType = 'sku_starts';
        }
        // 4️⃣ SKU contains
        else if (item.item_code.toLowerCase().includes(term)) {
            matchScore = 70;
            matchType = 'sku_contains';
        }
        // 5️⃣ Name exact match
        else if (item.item_name.toLowerCase() === term) {
            matchScore = 60;
            matchType = 'name_exact';
        }
        // 6️⃣ Name contains (starts-with gets higher score)
        else if (item.item_name.toLowerCase().startsWith(term)) {
            matchScore = 50;
            matchType = 'name_starts';
        }
        // 7️⃣ Name contains anywhere
        else if (item.item_name.toLowerCase().includes(term)) {
            matchScore = 40;
            matchType = 'name_contains';
        }

        if (matchScore > 0) {
            results.push({
                ...item,
                _matchScore: matchScore,
                _matchType: matchType
            });
        }
    });

    // Sort by match score (highest first), then by name
    return results
        .sort((a, b) => {
            if (b._matchScore !== a._matchScore) {
                return b._matchScore - a._matchScore;
            }
            return a.item_name.localeCompare(b.item_name);
        })
        .slice(0, 100);
},

// =====================================================
// 2. REPLACE getItemByBarcodeExact METHOD
// =====================================================

// 🔍 OPTIMIZED: Get item by exact barcode using backend API
async getItemByBarcodeExact(barcode, abortSignal = null) {
    try {
        console.info("[ItemsSelector] 🔍 Using optimized API for exact barcode:", barcode);

        // Check cancellation before API call
        if (abortSignal && abortSignal.aborted) {
            throw new Error("Search cancelled");
        }

        // 🚀 NEW: Use optimized backend API
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
            // Check cancellation before returning item
            if (abortSignal && abortSignal.aborted) {
                throw new Error("Search cancelled");
            }

            const item = response.message;
            console.info("[ItemsSelector] ✅ Optimized API found:", item.item_code, item.item_name);

            // Validate required fields
            if (!item.uom) {
                throw new Error(`Item ${item.item_name} missing UOM`);
            }

            return item;
        } else {
            console.info("[ItemsSelector] ❌ Optimized API: No exact barcode match for:", barcode);
            return null;
        }

    } catch (error) {
        if (error.name === "AbortError" || error.message === "Search cancelled") {
            throw error; // Re-throw cancellation errors
        }

        console.warn('[ItemsSelector] 🔄 Optimized API failed, using fallback:', error);

        // 🔄 FALLBACK: Use existing API
        return this.getItemByBarcodeExactFallback(barcode, abortSignal);
    }
},

// 🔄 FALLBACK: Keep existing API as backup
async getItemByBarcodeExactFallback(barcode, abortSignal = null) {
    try {
        console.info("[ItemsSelector] 🔄 Using fallback API for exact barcode:", barcode);

        const response = await frappe.call({
            method: "posawesome.posawesome.api.items.get_item_by_barcode_exact",
            args: {
                barcode: barcode,
                pos_profile: JSON.stringify(this.pos_profile),
                price_list: this.active_price_list,
                customer: this.customer,
            },
            signal: abortSignal,
        });

        if (response.message) {
            const item = response.message;
            console.info("[ItemsSelector] ✅ Fallback API found:", item.item_code);

            // Validate UOM
            if (!item.uom) {
                throw new Error(`Item ${item.item_name} missing UOM`);
            }

            return item;
        }

        return null;

    } catch (error) {
        console.error("[ItemsSelector] ❌ Fallback API also failed:", error);
        throw error;
    }
},

// =====================================================
// 3. ADD NEW DEBUG METHODS
// =====================================================

// 🐛 DEBUG: Get popup search statistics
async getPopupSearchStats() {
    try {
        console.info('[Debug] Getting popup search statistics...');

        const response = await frappe.call({
            method: "posawesome.posawesome.api.items.get_popup_search_stats",
            args: {
                pos_profile: JSON.stringify(this.pos_profile),
                price_list: this.active_price_list,
                warehouse: this.pos_profile.warehouse
            }
        });

        if (response.message) {
            console.group('📊 Popup Search Statistics');
            console.table(response.message);
            console.groupEnd();
            return response.message;
        }

        return null;

    } catch (error) {
        console.error('Failed to get popup search stats:', error);
        return null;
    }
},

// 🐛 DEBUG: Test optimized search performance
async testOptimizedSearch(searchTerm = 'test') {
    console.group(`🔍 Testing Optimized Search: ${searchTerm}`);

    const startTime = performance.now();

    try {
        // Test API search
        console.info('1️⃣ Testing API search...');
        const apiResults = await this.searchItemsByText(searchTerm);
        const apiTime = performance.now() - startTime;

        console.info(`✅ API Results: ${apiResults.length} items in ${apiTime.toFixed(2)}ms`);

        // Test local search for comparison
        console.info('2️⃣ Testing local search...');
        const localStartTime = performance.now();
        const localResults = await this.searchItemsByTextLocal(searchTerm);
        const localTime = performance.now() - localStartTime;

        console.info(`✅ Local Results: ${localResults.length} items in ${localTime.toFixed(2)}ms`);

        // Performance comparison
        const speedup = localTime / apiTime;
        console.info(`📈 Performance: ${speedup > 1 ? 'API is ' + speedup.toFixed(2) + 'x faster' : 'Local is ' + (1 / speedup).toFixed(2) + 'x faster'}`);

        console.groupEnd();

        return {
            searchTerm,
            apiResults: apiResults.length,
            localResults: localResults.length,
            apiTime: apiTime.toFixed(2),
            localTime: localTime.toFixed(2),
            speedup: speedup.toFixed(2)
        };

    } catch (error) {
        console.error('Test failed:', error);
        console.groupEnd();
        return null;
    }
},

// 🐛 DEBUG: Test barcode search performance
async testBarcodeSearchPerformance(barcode = '8991818801601') {
    console.group(`🔍 Testing Barcode Search: ${barcode}`);

    try {
        // Test optimized API
        console.info('1️⃣ Testing optimized API...');
        const apiStartTime = performance.now();
        const apiResult = await this.getItemByBarcodeExact(barcode);
        const apiTime = performance.now() - apiStartTime;

        console.info(`✅ API Result: ${apiResult ? apiResult.item_code : 'Not found'} in ${apiTime.toFixed(2)}ms`);

        // Test fallback API
        console.info('2️⃣ Testing fallback API...');
        const fallbackStartTime = performance.now();
        const fallbackResult = await this.getItemByBarcodeExactFallback(barcode);
        const fallbackTime = performance.now() - fallbackStartTime;

        console.info(`✅ Fallback Result: ${fallbackResult ? fallbackResult.item_code : 'Not found'} in ${fallbackTime.toFixed(2)}ms`);

        // Performance comparison
        const speedup = fallbackTime / apiTime;
        console.info(`📈 Performance: ${speedup > 1 ? 'Optimized is ' + speedup.toFixed(2) + 'x faster' : 'Fallback is ' + (1 / speedup).toFixed(2) + 'x faster'}`);

        console.groupEnd();

        return {
            barcode,
            apiFound: !!apiResult,
            fallbackFound: !!fallbackResult,
            apiTime: apiTime.toFixed(2),
            fallbackTime: fallbackTime.toFixed(2),
            speedup: speedup.toFixed(2)
        };

    } catch (error) {
        console.error('Barcode test failed:', error);
        console.groupEnd();
        return null;
    }
},

// =====================================================
// 4. INTEGRATION INSTRUCTIONS
// =====================================================

/*
CÁCH TÍCH HỢP:

1. 📁 Backend Setup:
   - Copy optimized_popup_search_api.py vào app của bạn
   - Add methods vào items.py hoặc tạo file mới
   - Restart Frappe server

2. 🔧 Frontend Integration:
   - Replace methods trong ItemsSelector.vue với code trên
   - Keep existing methods as fallback
   - Test với browser console

3. 🧪 Testing:
   - Run: $vm0.getPopupSearchStats()
   - Run: $vm0.testOptimizedSearch('test')
   - Run: $vm0.testBarcodeSearchPerformance('8991818801601')

4. 📊 Performance Monitoring:
   - Check console logs for API vs Local performance
   - Monitor network requests in DevTools
   - Verify search accuracy and speed

5. 🔄 Rollback Plan:
   - If issues occur, methods will automatically fallback
   - Can disable API calls by commenting out frappe.call
   - Original local search logic is preserved

EXPECTED BENEFITS:
- ⚡ Faster search with database indexes
- 🎯 Better match prioritization from backend
- 📊 Reduced frontend processing load
- 🔍 More accurate barcode matching
- 📈 Scalable for large product catalogs
*/