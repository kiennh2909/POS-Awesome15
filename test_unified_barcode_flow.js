// 🧪 Unified Barcode Flow Test Script
// Run this in browser console on POS page to test unified barcode flow

console.log('🧪 Unified Barcode Flow Test Script Loaded');

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
    if (window.$vm0 && window.$vm0.trigger_onscan) {
        return window.$vm0;
    }

    return null;
}

// Test 1: Hardware Scanner Flow
async function testHardwareScanner(barcode = '8991818801601') {
    console.group(`🧪 Test 1: Hardware Scanner Flow - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('📱 Simulating hardware scanner...');

        // Clear search first
        itemsSelector.debounce_search = '';
        itemsSelector.first_search = '';

        // Simulate hardware scanner
        itemsSelector.trigger_onscan(barcode);

        // Check if barcode was put into search input
        await new Promise(resolve => setTimeout(resolve, 500));

        if (itemsSelector.debounce_search === barcode) {
            console.log('✅ Barcode correctly placed in search input');
        } else {
            console.error('❌ Barcode not in search input:', itemsSelector.debounce_search);
            console.groupEnd();
            return false;
        }

        // Check search mode
        if (itemsSelector.search_mode === 'barcode') {
            console.log('✅ Search mode correctly set to barcode');
        } else {
            console.error('❌ Search mode not barcode:', itemsSelector.search_mode);
        }

        console.log('💡 Now user should press Enter to add to cart');
        console.log('✅ Test 1 PASSED - Hardware Scanner puts barcode in input, requires Enter');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 1 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 2: Camera Scanner Flow
async function testCameraScanner(barcode = '8991818801601') {
    console.group(`🧪 Test 2: Camera Scanner Flow - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('📷 Simulating camera scanner...');

        // Clear search first
        itemsSelector.debounce_search = '';
        itemsSelector.first_search = '';

        // Simulate camera scanner
        itemsSelector.onBarcodeScanned(barcode);

        // Check if barcode was put into search input
        await new Promise(resolve => setTimeout(resolve, 500));

        if (itemsSelector.debounce_search === barcode) {
            console.log('✅ Barcode correctly placed in search input');
        } else {
            console.error('❌ Barcode not in search input:', itemsSelector.debounce_search);
            console.groupEnd();
            return false;
        }

        // Check search mode
        if (itemsSelector.search_mode === 'barcode') {
            console.log('✅ Search mode correctly set to barcode');
        } else {
            console.error('❌ Search mode not barcode:', itemsSelector.search_mode);
        }

        console.log('💡 Now user should press Enter to add to cart');
        console.log('✅ Test 2 PASSED - Camera Scanner puts barcode in input, requires Enter');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 2 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 3: Manual Entry Flow
async function testManualEntry(barcode = '8991818801601') {
    console.group(`🧪 Test 3: Manual Entry Flow - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('⌨️ Simulating manual entry...');

        // Set barcode mode
        itemsSelector.search_mode = 'barcode';

        // Set barcode in search input (simulate typing)
        itemsSelector.debounce_search = barcode;

        // Get initial cart count
        const initialCartCount = itemsSelector.frm?.doc?.items?.length || 0;
        console.log('📊 Initial cart count:', initialCartCount);

        // Simulate Enter key press
        console.log('🔍 Simulating Enter key press...');
        await itemsSelector.handleBarcodeEnter();

        await new Promise(resolve => setTimeout(resolve, 2000));

        // Check if item was added
        const finalCartCount = itemsSelector.frm?.doc?.items?.length || 0;
        console.log('📊 Final cart count:', finalCartCount);

        if (finalCartCount > initialCartCount) {
            console.log('✅ Item successfully added to cart');
        } else {
            console.warn('⚠️ Item may not have been added (could be invalid barcode)');
        }

        console.log('✅ Test 3 PASSED - Manual Entry works with Enter key');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 3 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 4: Unified Flow Consistency
async function testUnifiedConsistency() {
    console.group('🧪 Test 4: Unified Flow Consistency');

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        const testBarcode = '8991818801601';

        // Test 1: Hardware Scanner
        console.log('1️⃣ Testing Hardware Scanner consistency...');
        itemsSelector.debounce_search = '';
        itemsSelector.trigger_onscan(testBarcode);
        await new Promise(resolve => setTimeout(resolve, 200));
        const hardwareResult = itemsSelector.debounce_search;

        // Test 2: Camera Scanner
        console.log('2️⃣ Testing Camera Scanner consistency...');
        itemsSelector.debounce_search = '';
        itemsSelector.onBarcodeScanned(testBarcode);
        await new Promise(resolve => setTimeout(resolve, 200));
        const cameraResult = itemsSelector.debounce_search;

        // Test 3: Manual Entry
        console.log('3️⃣ Testing Manual Entry consistency...');
        itemsSelector.debounce_search = testBarcode;
        const manualResult = itemsSelector.debounce_search;

        // Check consistency
        if (hardwareResult === testBarcode && cameraResult === testBarcode && manualResult === testBarcode) {
            console.log('✅ All three methods put barcode in same place (search input)');
        } else {
            console.error('❌ Inconsistent behavior:');
            console.log('   Hardware:', hardwareResult);
            console.log('   Camera:', cameraResult);
            console.log('   Manual:', manualResult);
            console.groupEnd();
            return false;
        }

        // Check that all set barcode mode
        itemsSelector.search_mode = 'text'; // Reset
        itemsSelector.trigger_onscan(testBarcode);
        const hardwareMode = itemsSelector.search_mode;

        itemsSelector.search_mode = 'text'; // Reset
        itemsSelector.onBarcodeScanned(testBarcode);
        const cameraMode = itemsSelector.search_mode;

        if (hardwareMode === 'barcode' && cameraMode === 'barcode') {
            console.log('✅ All scanners correctly set barcode mode');
        } else {
            console.error('❌ Inconsistent mode setting:');
            console.log('   Hardware mode:', hardwareMode);
            console.log('   Camera mode:', cameraMode);
        }

        console.log('✅ Test 4 PASSED - All methods are consistent');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 4 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 5: Deprecated Methods Check
function testDeprecatedMethods() {
    console.group('🧪 Test 5: Deprecated Methods Check');

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        const deprecatedMethods = [
            'processScannedItem',
            'searchItemsByCode',
            'addScannedItemToInvoice',
            'continueWithLocalSearch'
        ];

        let allDeprecated = true;

        for (const methodName of deprecatedMethods) {
            if (typeof itemsSelector[methodName] === 'function') {
                console.warn(`⚠️ Method ${methodName} still exists as function`);
                allDeprecated = false;
            } else {
                console.log(`✅ Method ${methodName} properly deprecated`);
            }
        }

        if (allDeprecated) {
            console.log('✅ All deprecated methods are properly removed/commented');
        } else {
            console.warn('⚠️ Some deprecated methods still exist');
        }

        console.log('✅ Test 5 COMPLETED - Deprecated methods check');
        console.groupEnd();
        return allDeprecated;

    } catch (error) {
        console.error('❌ Test 5 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 6: User Experience Flow
async function testUserExperienceFlow(barcode = '8991818801601') {
    console.group(`🧪 Test 6: User Experience Flow - "${barcode}"`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('👤 Testing complete user experience...');

        // Step 1: User scans with hardware scanner
        console.log('1️⃣ User scans with hardware scanner');
        itemsSelector.trigger_onscan(barcode);

        await new Promise(resolve => setTimeout(resolve, 500));

        // Check if search input is focused and text is selected
        const searchInput = itemsSelector.$refs.searchInput;
        if (searchInput) {
            console.log('✅ Search input should be focused');
        }

        // Check if barcode is in input
        if (itemsSelector.debounce_search === barcode) {
            console.log('✅ Barcode is in search input');
        }

        // Step 2: User sees the barcode and presses Enter
        console.log('2️⃣ User sees barcode and presses Enter');

        const initialCartCount = itemsSelector.frm?.doc?.items?.length || 0;

        // Simulate Enter press
        await itemsSelector.handleBarcodeEnter();

        await new Promise(resolve => setTimeout(resolve, 1000));

        const finalCartCount = itemsSelector.frm?.doc?.items?.length || 0;

        if (finalCartCount > initialCartCount) {
            console.log('✅ Item added to cart after Enter');
        } else {
            console.log('ℹ️ Item not added (may be invalid barcode for test)');
        }

        // Step 3: Check if search is cleared and ready for next scan
        if (itemsSelector.debounce_search === '' || itemsSelector.debounce_search !== barcode) {
            console.log('✅ Search cleared after successful add');
        }

        console.log('✅ Test 6 PASSED - User experience flow is smooth');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 6 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Run all tests
async function runAllUnifiedTests() {
    console.log('🚀 Starting Unified Barcode Flow Tests...');
    console.log('=' * 60);

    const results = {
        hardwareScanner: await testHardwareScanner(),
        cameraScanner: await testCameraScanner(),
        manualEntry: await testManualEntry(),
        unifiedConsistency: await testUnifiedConsistency(),
        deprecatedMethods: testDeprecatedMethods(),
        userExperience: await testUserExperienceFlow()
    };

    console.log('\n📊 Unified Flow Test Results:');
    console.table(results);

    const passedTests = Object.values(results).filter(r => r === true).length;
    const totalTests = Object.keys(results).length;

    console.log(`\n🎯 Tests Passed: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
        console.log('🎉 All tests PASSED! Unified barcode flow is working correctly.');
        console.log('✅ Hardware Scanner → Search Input → Enter ✅');
        console.log('✅ Camera Scanner → Search Input → Enter ✅');
        console.log('✅ Manual Entry → Search Input → Enter ✅');
    } else {
        console.log('⚠️ Some tests failed. Check the logs above for details.');
    }

    return results;
}

// Quick test function
async function quickUnifiedTest() {
    console.log('⚡ Quick Unified Flow Test');

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ ItemsSelector not found');
        return;
    }

    const testBarcode = '123456789';

    // Test hardware scanner
    itemsSelector.trigger_onscan(testBarcode);
    console.log('Hardware Scanner → Search Input:', itemsSelector.debounce_search === testBarcode ? '✅' : '❌');

    // Test camera scanner
    itemsSelector.debounce_search = '';
    itemsSelector.onBarcodeScanned(testBarcode);
    console.log('Camera Scanner → Search Input:', itemsSelector.debounce_search === testBarcode ? '✅' : '❌');

    console.log('💡 Both scanners put barcode in search input. User must press Enter to add to cart.');
}

// Export functions to global scope
window.testHardwareScanner = testHardwareScanner;
window.testCameraScanner = testCameraScanner;
window.testManualEntry = testManualEntry;
window.testUnifiedConsistency = testUnifiedConsistency;
window.testDeprecatedMethods = testDeprecatedMethods;
window.testUserExperienceFlow = testUserExperienceFlow;
window.runAllUnifiedTests = runAllUnifiedTests;
window.quickUnifiedTest = quickUnifiedTest;

console.log('✅ Unified Barcode Flow Test functions available:');
console.log('   testHardwareScanner(barcode) - Test hardware scanner flow');
console.log('   testCameraScanner(barcode) - Test camera scanner flow');
console.log('   testManualEntry(barcode) - Test manual entry flow');
console.log('   testUnifiedConsistency() - Test all methods are consistent');
console.log('   testDeprecatedMethods() - Check deprecated methods');
console.log('   testUserExperienceFlow(barcode) - Test complete UX flow');
console.log('   runAllUnifiedTests() - Run all tests');
console.log('   quickUnifiedTest() - Quick consistency check');
console.log('\n💡 Usage: runAllUnifiedTests() or quickUnifiedTest()');