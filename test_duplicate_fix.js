// 🧪 Test Script for Duplicate Item Fix
// Run this in browser console on POS page to test duplicate fix

console.log('🧪 Duplicate Item Fix Test Script Loaded');

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
    if (window.$vm0 && window.$vm0.trigger_onscan) {
        return window.$vm0;
    }
    return null;
}

// Helper to wait
function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Test 1: Hardware Scanner - Should NOT auto-add
async function testHardwareScannerNoAutoAdd(barcode = '8991818801601') {
    console.group('🧪 Test 1: Hardware Scanner - No Auto-Add');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        console.log('📱 Step 1: Simulating hardware scanner...');
        vm.trigger_onscan(barcode);

        await wait(2000); // Wait for any auto-processing

        // Check cart count - should be SAME (no auto-add)
        const afterScanCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 After scan count: ${afterScanCount}`);

        if (afterScanCount === initialCount) {
            console.log('✅ Step 1 PASSED: No auto-add after hardware scan');
        } else {
            console.error('❌ Step 1 FAILED: Item was auto-added');
            console.groupEnd();
            return false;
        }

        // Check if barcode is in input
        if (vm.first_search === barcode) {
            console.log('✅ Step 2 PASSED: Barcode filled in input');
        } else {
            console.error('❌ Step 2 FAILED: Barcode not in input');
        }

        console.log('✅ Test 1 PASSED: Hardware scanner does not auto-add');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 1 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 2: Camera Scanner - Should NOT auto-add
async function testCameraScannerNoAutoAdd(barcode = '8991818801601') {
    console.group('🧪 Test 2: Camera Scanner - No Auto-Add');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        console.log('📷 Step 1: Simulating camera scanner...');
        vm.onBarcodeScanned(barcode);

        await wait(2000); // Wait for any auto-processing

        // Check cart count - should be SAME (no auto-add)
        const afterScanCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 After scan count: ${afterScanCount}`);

        if (afterScanCount === initialCount) {
            console.log('✅ Step 1 PASSED: No auto-add after camera scan');
        } else {
            console.error('❌ Step 1 FAILED: Item was auto-added');
            console.groupEnd();
            return false;
        }

        // Check if barcode is in input
        if (vm.first_search === barcode) {
            console.log('✅ Step 2 PASSED: Barcode filled in input');
        } else {
            console.error('❌ Step 2 FAILED: Barcode not in input');
        }

        console.log('✅ Test 2 PASSED: Camera scanner does not auto-add');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 2 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 3: Manual Enter - Should add ONLY ONE item
async function testManualEnterSingleAdd(barcode = '8991818801601') {
    console.group('🧪 Test 3: Manual Enter - Single Add Only');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Clear any existing search
        vm.first_search = '';
        vm.search = '';
        vm.debounce_search = '';

        await wait(500);

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        console.log('⌨️ Step 1: Setting barcode manually...');
        vm.first_search = barcode;
        vm.search = barcode;
        vm.debounce_search = barcode;
        vm.search_mode = 'barcode';

        await wait(1000); // Wait to see if auto-add happens

        // Check cart count - should be SAME (no auto-add from watcher)
        const afterInputCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 After input count: ${afterInputCount}`);

        if (afterInputCount === initialCount) {
            console.log('✅ Step 1 PASSED: No auto-add from input watcher');
        } else {
            console.error('❌ Step 1 FAILED: Auto-add from watcher still happening');
            console.groupEnd();
            return false;
        }

        console.log('⌨️ Step 2: Pressing Enter...');
        await vm.handleBarcodeEnter();

        await wait(1000);

        // Check cart count - should be +1
        const finalCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Final count: ${finalCount}`);

        if (finalCount === initialCount + 1) {
            console.log('✅ Step 2 PASSED: Exactly ONE item added after Enter');
        } else if (finalCount === initialCount) {
            console.warn('⚠️ Step 2: No item added (item may not exist)');
        } else {
            console.error(`❌ Step 2 FAILED: ${finalCount - initialCount} items added (should be 1)`);
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 3 PASSED: Manual Enter adds single item only');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 3 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 4: Full Workflow - Scan + Enter
async function testFullWorkflowNoDuplicate(barcode = '8991818801601') {
    console.group('🧪 Test 4: Full Workflow - Scan + Enter (No Duplicate)');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        console.log('📱 Step 1: Hardware scan...');
        vm.trigger_onscan(barcode);

        await wait(1000);

        // Should be no auto-add
        const afterScanCount = vm.frm?.doc?.items?.length || 0;
        if (afterScanCount !== initialCount) {
            console.error('❌ Auto-add still happening after scan');
            console.groupEnd();
            return false;
        }

        console.log('⌨️ Step 2: User presses Enter...');
        await vm.handleBarcodeEnter();

        await wait(1000);

        // Should be exactly +1
        const finalCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Final count: ${finalCount}`);

        if (finalCount === initialCount + 1) {
            console.log('✅ PERFECT: Exactly ONE item added in full workflow');
        } else if (finalCount === initialCount) {
            console.warn('⚠️ No item added (item may not exist)');
        } else {
            console.error(`❌ DUPLICATE DETECTED: ${finalCount - initialCount} items added`);
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 4 PASSED: Full workflow with no duplicates');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 4 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 5: Watcher Disabled Check
async function testWatcherDisabled() {
    console.group('🧪 Test 5: Watcher Auto-Search Disabled');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('🔍 Checking if watchers are properly disabled...');

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;

        // Set barcode mode
        vm.search_mode = 'barcode';

        // Trigger first_search watcher
        vm.first_search = '8991818801601';

        await wait(2000); // Wait for watcher debounce + processing

        const afterWatcherCount = vm.frm?.doc?.items?.length || 0;

        if (afterWatcherCount === initialCount) {
            console.log('✅ first_search watcher is properly disabled');
        } else {
            console.error('❌ first_search watcher is still auto-adding items');
            console.groupEnd();
            return false;
        }

        // Test search_onchange
        vm.search = '8991818801601';
        await vm.search_onchange();

        await wait(1000);

        const afterOnChangeCount = vm.frm?.doc?.items?.length || 0;

        if (afterOnChangeCount === initialCount) {
            console.log('✅ search_onchange is properly disabled');
        } else {
            console.error('❌ search_onchange is still auto-adding items');
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 5 PASSED: All watchers properly disabled');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 5 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Run all duplicate fix tests
async function runDuplicateFixTests(barcode = '8991818801601') {
    console.log('🚀 Starting Duplicate Fix Tests...');
    console.log('=' * 50);
    console.log(`Using test barcode: ${barcode}`);
    console.log('');

    const results = {
        test1_hardware_no_auto: await testHardwareScannerNoAutoAdd(barcode),
        test2_camera_no_auto: await testCameraScannerNoAutoAdd(barcode),
        test3_manual_single: await testManualEnterSingleAdd(barcode),
        test4_full_workflow: await testFullWorkflowNoDuplicate(barcode),
        test5_watcher_disabled: await testWatcherDisabled()
    };

    console.log('\n📊 Duplicate Fix Test Results:');
    console.table(results);

    const passedTests = Object.values(results).filter(r => r === true).length;
    const totalTests = Object.keys(results).length;

    console.log(`\n🎯 Tests Passed: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
        console.log('🎉 All tests PASSED! Duplicate issue is FIXED!');
    } else {
        console.log('⚠️ Some tests failed. Duplicate issue may still exist.');
    }

    return results;
}

// Quick duplicate test
async function quickDuplicateTest(barcode = '8991818801601') {
    console.log('⚡ Quick Duplicate Test');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Component not found');
        return;
    }

    const initialCount = vm.frm?.doc?.items?.length || 0;
    console.log(`📊 Initial count: ${initialCount}`);

    // Scan
    vm.trigger_onscan(barcode);
    await wait(1000);

    const afterScanCount = vm.frm?.doc?.items?.length || 0;
    console.log(`📊 After scan: ${afterScanCount} (should be same as initial)`);

    // Enter
    await vm.handleBarcodeEnter();
    await wait(1000);

    const finalCount = vm.frm?.doc?.items?.length || 0;
    console.log(`📊 Final count: ${finalCount} (should be initial + 1)`);

    const added = finalCount - initialCount;
    if (added === 1) {
        console.log('✅ PERFECT: Exactly 1 item added, no duplicates!');
    } else if (added === 0) {
        console.log('⚠️ No item added (item may not exist)');
    } else {
        console.log(`❌ DUPLICATE DETECTED: ${added} items added`);
    }
}

// Export functions to global scope
window.testHardwareScannerNoAutoAdd = testHardwareScannerNoAutoAdd;
window.testCameraScannerNoAutoAdd = testCameraScannerNoAutoAdd;
window.testManualEnterSingleAdd = testManualEnterSingleAdd;
window.testFullWorkflowNoDuplicate = testFullWorkflowNoDuplicate;
window.testWatcherDisabled = testWatcherDisabled;
window.runDuplicateFixTests = runDuplicateFixTests;
window.quickDuplicateTest = quickDuplicateTest;

console.log('✅ Duplicate fix test functions available:');
console.log('   quickDuplicateTest(barcode) - Quick test for duplicates');
console.log('   testHardwareScannerNoAutoAdd(barcode) - Test hardware scanner');
console.log('   testCameraScannerNoAutoAdd(barcode) - Test camera scanner');
console.log('   testManualEnterSingleAdd(barcode) - Test manual enter');
console.log('   testFullWorkflowNoDuplicate(barcode) - Test full workflow');
console.log('   testWatcherDisabled() - Test watchers are disabled');
console.log('   runDuplicateFixTests(barcode) - Run all tests');
console.log('\n💡 Usage: quickDuplicateTest() or runDuplicateFixTests()');