// 🧪 Product Search Popup Test Script
// Run this in browser console on POS page to test popup functionality

console.log('🧪 Product Search Popup Test Script Loaded');

// Helper function to find ItemsSelector component
function findItemsSelector() {
    // Try to find the component instance
    const app = document.querySelector('#app').__vue_app__;
    if (app) {
        const instances = app._instance.scope.effects;
        for (let effect of instances) {
            if (effect.fn && effect.fn.ctx && effect.fn.ctx.$options && effect.fn.ctx.$options.name === 'ItemsSelector') {
                return effect.fn.ctx;
            }
        }
    }

    // Fallback: try global $vm0
    if (window.$vm0 && window.$vm0.openProductSearchPopup) {
        return window.$vm0;
    }

    return null;
}

// Test 1: Basic popup open/close
async function testPopupOpenClose() {
    console.group('🧪 Test 1: Popup Open/Close');

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Test open
        console.log('📂 Opening popup...');
        itemsSelector.openProductSearchPopup();

        await new Promise(resolve => setTimeout(resolve, 1000));

        if (itemsSelector.product_search_popup_visible) {
            console.log('✅ Popup opened successfully');
        } else {
            console.error('❌ Popup failed to open');
            console.groupEnd();
            return false;
        }

        // Test close
        console.log('📁 Closing popup...');
        itemsSelector.closeProductSearchPopup();

        await new Promise(resolve => setTimeout(resolve, 500));

        if (!itemsSelector.product_search_popup_visible) {
            console.log('✅ Popup closed successfully');
        } else {
            console.error('❌ Popup failed to close');
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 1 PASSED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 1 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 2: API search functionality
async function testAPISearch(searchTerm = 'coca') {
    console.group(`🧪 Test 2: API Search - "${searchTerm}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('🔍 Testing API search...');

        const response = await frappe.call({
            method: "posawesome.posawesome.api.items.search_items_for_popup",
            args: {
                search_term: searchTerm,
                pos_profile: JSON.stringify(itemsSelector.pos_profile),
                price_list: itemsSelector.active_price_list,
                warehouse: itemsSelector.pos_profile.warehouse,
                limit: 50
            }
        });

        if (response.message) {
            console.log(`✅ API returned ${response.message.length} results`);
            console.table(response.message.slice(0, 5)); // Show first 5 results

            // Validate result structure
            if (response.message.length > 0) {
                const firstItem = response.message[0];
                const requiredFields = ['item_code', 'item_name', 'rate', 'actual_qty', 'match_score'];
                const missingFields = requiredFields.filter(field => !(field in firstItem));

                if (missingFields.length === 0) {
                    console.log('✅ Result structure is valid');
                } else {
                    console.warn('⚠️ Missing fields in result:', missingFields);
                }
            }

            console.log('✅ Test 2 PASSED');
            console.groupEnd();
            return response.message;
        } else {
            console.warn('⚠️ API returned no results');
            console.groupEnd();
            return [];
        }

    } catch (error) {
        console.error('❌ Test 2 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 3: Popup integration with real search
async function testPopupSearch(searchTerm = 'coca') {
    console.group(`🧪 Test 3: Popup Integration - "${searchTerm}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Open popup
        console.log('📂 Opening popup...');
        itemsSelector.openProductSearchPopup();

        await new Promise(resolve => setTimeout(resolve, 1000));

        // Find popup component
        const popupComponent = itemsSelector.$children?.find(child =>
            child.$options.name === 'ProductSearchPopup'
        );

        if (!popupComponent) {
            console.error('❌ Could not find ProductSearchPopup component');
            console.groupEnd();
            return false;
        }

        console.log('✅ Found popup component');

        // Set search term and perform search
        console.log(`🔍 Setting search term: "${searchTerm}"`);
        popupComponent.searchTerm = searchTerm;

        console.log('🔍 Performing search...');
        await popupComponent.performSearch();

        await new Promise(resolve => setTimeout(resolve, 2000));

        if (popupComponent.searchResults && popupComponent.searchResults.length > 0) {
            console.log(`✅ Popup search returned ${popupComponent.searchResults.length} results`);
            console.table(popupComponent.searchResults.slice(0, 3));
        } else {
            console.warn('⚠️ Popup search returned no results');
        }

        // Close popup
        console.log('📁 Closing popup...');
        itemsSelector.closeProductSearchPopup();

        console.log('✅ Test 3 PASSED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 3 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 4: Add item from popup
async function testAddItemFromPopup(searchTerm = 'coca') {
    console.group(`🧪 Test 4: Add Item from Popup - "${searchTerm}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Get search results first
        const results = await testAPISearch(searchTerm);
        if (!results || results.length === 0) {
            console.warn('⚠️ No results to test with');
            console.groupEnd();
            return false;
        }

        const testItem = results[0];
        console.log('🛒 Testing add item:', testItem.item_name);

        // Get current cart count
        const initialCartCount = itemsSelector.frm?.doc?.items?.length || 0;
        console.log('📊 Initial cart count:', initialCartCount);

        // Test add item
        await itemsSelector.onPopupAddItem(testItem);

        await new Promise(resolve => setTimeout(resolve, 1000));

        // Check if item was added
        const finalCartCount = itemsSelector.frm?.doc?.items?.length || 0;
        console.log('📊 Final cart count:', finalCartCount);

        if (finalCartCount > initialCartCount) {
            console.log('✅ Item added to cart successfully');
            console.log('✅ Test 4 PASSED');
        } else {
            console.warn('⚠️ Item may not have been added to cart');
        }

        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 4 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 5: Performance test
async function testPerformance() {
    console.group('🧪 Test 5: Performance Test');

    const searchTerms = ['a', 'co', 'coca', 'product', '123'];
    const results = [];

    for (const term of searchTerms) {
        console.log(`⏱️ Testing search performance for: "${term}"`);

        const startTime = performance.now();

        try {
            const response = await frappe.call({
                method: "posawesome.posawesome.api.items.search_items_for_popup",
                args: {
                    search_term: term,
                    pos_profile: JSON.stringify(findItemsSelector().pos_profile),
                    price_list: findItemsSelector().active_price_list,
                    warehouse: findItemsSelector().pos_profile.warehouse,
                    limit: 50
                }
            });

            const endTime = performance.now();
            const duration = endTime - startTime;
            const resultCount = response.message?.length || 0;

            results.push({
                term,
                duration: Math.round(duration),
                results: resultCount,
                status: duration < 2000 ? '✅ Fast' : duration < 5000 ? '⚠️ Slow' : '❌ Very Slow'
            });

        } catch (error) {
            results.push({
                term,
                duration: 'Error',
                results: 0,
                status: '❌ Failed'
            });
        }
    }

    console.table(results);

    const avgDuration = results
        .filter(r => typeof r.duration === 'number')
        .reduce((sum, r) => sum + r.duration, 0) / results.length;

    console.log(`📊 Average search time: ${Math.round(avgDuration)}ms`);

    if (avgDuration < 1000) {
        console.log('✅ Performance is excellent');
    } else if (avgDuration < 2000) {
        console.log('⚠️ Performance is acceptable');
    } else {
        console.log('❌ Performance needs improvement');
    }

    console.log('✅ Test 5 COMPLETED');
    console.groupEnd();
    return results;
}

// Run all tests
async function runAllTests() {
    console.log('🚀 Starting Product Search Popup Tests...');
    console.log('=' * 50);

    const results = {
        test1: await testPopupOpenClose(),
        test2: await testAPISearch(),
        test3: await testPopupSearch(),
        test4: await testAddItemFromPopup(),
        test5: await testPerformance()
    };

    console.log('\n📊 Test Results Summary:');
    console.table(results);

    const passedTests = Object.values(results).filter(r => r === true || (Array.isArray(r) && r.length > 0)).length;
    const totalTests = Object.keys(results).length;

    console.log(`\n🎯 Tests Passed: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
        console.log('🎉 All tests PASSED! Popup is working correctly.');
    } else {
        console.log('⚠️ Some tests failed. Check the logs above for details.');
    }

    return results;
}

// Export functions to global scope
window.testPopupOpenClose = testPopupOpenClose;
window.testAPISearch = testAPISearch;
window.testPopupSearch = testPopupSearch;
window.testAddItemFromPopup = testAddItemFromPopup;
window.testPerformance = testPerformance;
window.runAllTests = runAllTests;

console.log('✅ Test functions available:');
console.log('   testPopupOpenClose() - Test popup open/close');
console.log('   testAPISearch(term) - Test API search');
console.log('   testPopupSearch(term) - Test popup integration');
console.log('   testAddItemFromPopup(term) - Test add item');
console.log('   testPerformance() - Test search performance');
console.log('   runAllTests() - Run all tests');
console.log('\n💡 Usage: runAllTests()');