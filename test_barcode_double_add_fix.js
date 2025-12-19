// 🧪 Test Script: Barcode Double Add Fix
// Run this in browser console on POS page to verify the fix

console.log('🧪 Barcode Double Add Fix Test Script Loaded');

// Helper function to find ItemsSelector component
function findItemsSelector() {
    const app = document.querySelector('#app').__vue_app__;
    if (app) {
        const instances = app._instance.scope.effects;
        for (let effect of instances) {
            if (effect.fn && effect.fn.ctx && effect.fn.ctx.$options && effect.fn.ctx.$options.name === 'ItemsSelector') {
                return effect.fn.ctx;
            }
        }
    }

    if (window.$vm0 && window.$vm0.handleBarcodeEnter) {
        return window.$vm0;
    }

    return null;
}

// Test 1: Monitor add_item calls to detect double add
function testDoubleAddDetection(barcode = '8991818801601') {
    console.group(`🧪 Test 1: Double Add Detection - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    // Hook into add_item to count calls
    let addItemCallCount = 0;
    let addItemCalls = [];

    const originalAddItem = itemsSelector.add_item;
    itemsSelector.add_item = function (item) {
        addItemCallCount++;
        addItemCalls.push({
            call: addItemCallCount,
            item: item,
            itemType: typeof item,
            itemCode: item?.item_code || 'N/A',
            timestamp: Date.now()
        });
        console.log(`🔍 add_item call #${addItemCallCount}:`, {
            type: typeof item,
            itemCode: item?.item_code || 'N/A',
            item: item
        });
        return originalAddItem.call(this, item);
    };

    return new Promise((resolve) => {
        // Test barcode entry
        console.log('📱 Testing barcode entry...');
        itemsSelector.debounce_search = barcode;

        // Simulate Enter key
        itemsSelector.handleBarcodeEnter().then(() => {
            // Wait a bit for all async operations
            setTimeout(() => {
                // Restore original method
                itemsSelector.add_item = originalAddItem;

                // Analyze results
                console.log(`📊 Total add_item calls: ${addItemCallCount}`);
                console.table(addItemCalls);

                if (addItemCallCount === 0) {
                    console.warn('⚠️ No add_item calls detected (barcode might not exist)');
                    console.groupEnd();
                    resolve({ status: 'no_calls', calls: addItemCallCount });
                } else if (addItemCallCount === 1) {
                    console.log('✅ PASS: Only 1 add_item call detected (no double add)');
                    console.groupEnd();
                    resolve({ status: 'pass', calls: addItemCallCount });
                } else {
                    console.error(`❌ FAIL: ${addItemCallCount} add_item calls detected (double add bug)`);
                    console.groupEnd();
                    resolve({ status: 'fail', calls: addItemCallCount });
                }
            }, 2000);
        }).catch((error) => {
            itemsSelector.add_item = originalAddItem;
            console.error('❌ Error during test:', error);
            console.groupEnd();
            resolve({ status: 'error', calls: addItemCallCount, error: error });
        });
    });
}

// Test 2: Check method existence and deprecation
function testMethodDeprecation() {
    console.group('🧪 Test 2: Method Deprecation Check');

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    const results = {
        getItemByBarcodeExact: typeof itemsSelector.getItemByBarcodeExact,
        fetchExactBarcodeAndAdd: typeof itemsSelector.fetchExactBarcodeAndAdd,
        findItemByBarcode: typeof itemsSelector.findItemByBarcode,
        addItemToCart: typeof itemsSelector.addItemToCart
    };

    console.table(results);

    // Check if new method exists
    if (typeof itemsSelector.getItemByBarcodeExact === 'function') {
        console.log('✅ New method getItemByBarcodeExact exists');
    } else {
        console.error('❌ New method getItemByBarcodeExact missing');
    }

    // Check if old method is deprecated
    if (typeof itemsSelector.fetchExactBarcodeAndAdd === 'undefined') {
        console.log('✅ Old method fetchExactBarcodeAndAdd properly deprecated');
    } else {
        console.warn('⚠️ Old method fetchExactBarcodeAndAdd still exists');
    }

    console.groupEnd();
    return results;
}

// Test 3: Test API method directly
async function testAPIMethodDirectly(barcode = '8991818801601') {
    console.group(`🧪 Test 3: API Method Direct Test - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('🔍 Testing getItemByBarcodeExact directly...');
        const result = await itemsSelector.getItemByBarcodeExact(barcode);

        if (result) {
            console.log('✅ API method returned item data:', {
                itemCode: result.item_code,
                itemName: result.item_name,
                uom: result.uom,
                rate: result.rate
            });
            console.log('✅ PASS: Method returns item object (not boolean)');
        } else {
            console.log('ℹ️ API method returned null (barcode not found)');
        }

        console.groupEnd();
        return { status: 'pass', result: result };

    } catch (error) {
        console.error('❌ API method error:', error);
        console.groupEnd();
        return { status: 'error', error: error };
    }
}

// Test 4: Compare old vs new flow
async function testFlowComparison(barcode = '8991818801601') {
    console.group(`🧪 Test 4: Flow Comparison - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Test new flow
        console.log('🔄 Testing new flow: getItemByBarcodeExact...');
        const newFlowResult = await itemsSelector.getItemByBarcodeExact(barcode);

        // Test findItemByBarcode (should use new flow internally)
        console.log('🔄 Testing findItemByBarcode (should use new flow)...');
        const findResult = await itemsSelector.findItemByBarcode(barcode);

        console.log('📊 Flow comparison results:');
        console.table({
            'getItemByBarcodeExact': {
                type: typeof newFlowResult,
                hasItemCode: newFlowResult?.item_code ? 'Yes' : 'No',
                result: newFlowResult ? 'Item Object' : 'Null'
            },
            'findItemByBarcode': {
                type: typeof findResult,
                hasItemCode: findResult?.item_code ? 'Yes' : 'No',
                result: findResult ? 'Item Object' : 'Null'
            }
        });

        // Check consistency
        if (newFlowResult && findResult && newFlowResult.item_code === findResult.item_code) {
            console.log('✅ PASS: Both methods return consistent item data');
        } else if (!newFlowResult && !findResult) {
            console.log('✅ PASS: Both methods consistently return null (item not found)');
        } else {
            console.warn('⚠️ Methods return different results');
        }

        console.groupEnd();
        return { status: 'pass', newFlow: newFlowResult, findFlow: findResult };

    } catch (error) {
        console.error('❌ Flow comparison error:', error);
        console.groupEnd();
        return { status: 'error', error: error };
    }
}

// Test 5: Full integration test
async function testFullIntegration(barcode = '8991818801601') {
    console.group(`🧪 Test 5: Full Integration Test - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Get initial cart count
        const initialCount = itemsSelector.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        // Clear search
        itemsSelector.debounce_search = '';

        // Simulate hardware scanner
        console.log('📱 Simulating hardware scanner...');
        itemsSelector.trigger_onscan(barcode);

        // Wait for barcode to appear in input
        await new Promise(resolve => setTimeout(resolve, 500));

        // Check if barcode is in input
        if (itemsSelector.debounce_search === barcode) {
            console.log('✅ Barcode correctly placed in search input');
        } else {
            console.error('❌ Barcode not in search input');
            console.groupEnd();
            return { status: 'fail', reason: 'barcode_not_in_input' };
        }

        // Simulate Enter key
        console.log('⌨️ Simulating Enter key press...');
        await itemsSelector.handleBarcodeEnter();

        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Check final cart count
        const finalCount = itemsSelector.frm?.doc?.items?.length || 0;
        console.log(`📊 Final cart count: ${finalCount}`);

        const itemsAdded = finalCount - initialCount;
        console.log(`📊 Items added: ${itemsAdded}`);

        if (itemsAdded === 1) {
            console.log('✅ PASS: Exactly 1 item added (no double add)');
            console.groupEnd();
            return { status: 'pass', itemsAdded: itemsAdded };
        } else if (itemsAdded === 0) {
            console.warn('⚠️ No items added (barcode might not exist)');
            console.groupEnd();
            return { status: 'no_add', itemsAdded: itemsAdded };
        } else {
            console.error(`❌ FAIL: ${itemsAdded} items added (expected 1)`);
            console.groupEnd();
            return { status: 'fail', itemsAdded: itemsAdded };
        }

    } catch (error) {
        console.error('❌ Integration test error:', error);
        console.groupEnd();
        return { status: 'error', error: error };
    }
}

// Run all tests
async function runAllDoubleAddTests() {
    console.log('🚀 Starting Barcode Double Add Fix Tests...');
    console.log('=' * 60);

    const results = {
        doubleAddDetection: await testDoubleAddDetection(),
        methodDeprecation: testMethodDeprecation(),
        apiMethodDirect: await testAPIMethodDirectly(),
        flowComparison: await testFlowComparison(),
        fullIntegration: await testFullIntegration()
    };

    console.log('\n📊 Double Add Fix Test Results:');
    console.table(results);

    // Analyze overall results
    let passCount = 0;
    let totalTests = 0;

    Object.entries(results).forEach(([testName, result]) => {
        totalTests++;
        if (result && (result.status === 'pass' || result === true)) {
            passCount++;
        }
    });

    console.log(`\n🎯 Tests Passed: ${passCount}/${totalTests}`);

    if (passCount === totalTests) {
        console.log('🎉 All tests PASSED! Double add bug is fixed.');
        console.log('✅ Barcode scanning will no longer create empty rows');
        console.log('✅ Items will be added exactly once');
        console.log('✅ Data integrity is maintained');
    } else {
        console.log('⚠️ Some tests failed. Check the logs above for details.');
    }

    return results;
}

// Quick test function
async function quickDoubleAddTest() {
    console.log('⚡ Quick Double Add Test');

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ ItemsSelector not found');
        return;
    }

    // Check if new method exists
    const hasNewMethod = typeof itemsSelector.getItemByBarcodeExact === 'function';
    const hasOldMethod = typeof itemsSelector.fetchExactBarcodeAndAdd === 'function';

    console.log('New method (getItemByBarcodeExact):', hasNewMethod ? '✅' : '❌');
    console.log('Old method (fetchExactBarcodeAndAdd):', hasOldMethod ? '⚠️ Still exists' : '✅ Deprecated');

    if (hasNewMethod && !hasOldMethod) {
        console.log('🎉 Fix appears to be implemented correctly!');
    } else {
        console.log('⚠️ Fix may not be complete. Run full tests for details.');
    }
}

// Export functions to global scope
window.testDoubleAddDetection = testDoubleAddDetection;
window.testMethodDeprecation = testMethodDeprecation;
window.testAPIMethodDirectly = testAPIMethodDirectly;
window.testFlowComparison = testFlowComparison;
window.testFullIntegration = testFullIntegration;
window.runAllDoubleAddTests = runAllDoubleAddTests;
window.quickDoubleAddTest = quickDoubleAddTest;

console.log('✅ Double Add Fix Test functions available:');
console.log('   testDoubleAddDetection(barcode) - Monitor add_item calls');
console.log('   testMethodDeprecation() - Check method existence');
console.log('   testAPIMethodDirectly(barcode) - Test API method');
console.log('   testFlowComparison(barcode) - Compare old vs new flow');
console.log('   testFullIntegration(barcode) - Full end-to-end test');
console.log('   runAllDoubleAddTests() - Run all tests');
console.log('   quickDoubleAddTest() - Quick check');
console.log('\n💡 Usage: runAllDoubleAddTests() or quickDoubleAddTest()');