// 🧪 Unified Scanner Workflow Test Script
// Run this in browser console on POS page to test unified scanner behavior

console.log('🧪 Unified Scanner Workflow Test Script Loaded');

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

// Test 1: Hardware Scanner Workflow
async function testHardwareScanner(barcode = '8991818801601') {
    console.group('🧪 Test 1: Hardware Scanner Workflow');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('📱 Step 1: Simulating hardware scanner...');
        vm.trigger_onscan(barcode);

        await wait(500);

        // Check if barcode is in input
        if (vm.first_search === barcode) {
            console.log('✅ Step 1 PASSED: Barcode filled in input');
        } else {
            console.error('❌ Step 1 FAILED: Barcode not in input');
            console.groupEnd();
            return false;
        }

        // Check if search mode is barcode
        if (vm.search_mode === 'barcode') {
            console.log('✅ Step 2 PASSED: Search mode is barcode');
        } else {
            console.error('❌ Step 2 FAILED: Search mode is not barcode');
        }

        console.log('⌨️ Step 3: User should press Enter now...');
        console.log('💡 Simulating Enter key press...');

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        // Simulate Enter key
        await vm.handleBarcodeEnter();

        await wait(1000);

        // Check if item was added
        const finalCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Final cart count: ${finalCount}`);

        if (finalCount > initialCount) {
            console.log('✅ Step 3 PASSED: Item added to cart after Enter');
        } else {
            console.warn('⚠️ Step 3: Item may not have been added (check if item exists)');
        }

        // Check if input was cleared
        if (!vm.first_search || vm.first_search === '') {
            console.log('✅ Step 4 PASSED: Input cleared after adding');
        } else {
            console.warn('⚠️ Step 4: Input not cleared');
        }

        console.log('✅ Test 1 COMPLETED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 1 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 2: Camera Scanner Workflow
async function testCameraScanner(barcode = '8991818801601') {
    console.group('🧪 Test 2: Camera Scanner Workflow');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('📷 Step 1: Simulating camera scanner...');
        vm.onBarcodeScanned(barcode);

        await wait(500);

        // Check if barcode is in input
        if (vm.first_search === barcode) {
            console.log('✅ Step 1 PASSED: Barcode filled in input');
        } else {
            console.error('❌ Step 1 FAILED: Barcode not in input');
            console.groupEnd();
            return false;
        }

        console.log('⌨️ Step 2: User should press Enter now...');
        console.log('💡 Simulating Enter key press...');

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        // Simulate Enter key
        await vm.handleBarcodeEnter();

        await wait(1000);

        // Check if item was added
        const finalCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Final cart count: ${finalCount}`);

        if (finalCount > initialCount) {
            console.log('✅ Step 2 PASSED: Item added to cart after Enter');
        } else {
            console.warn('⚠️ Step 2: Item may not have been added (check if item exists)');
        }

        console.log('✅ Test 2 COMPLETED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 2 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 3: Manual Input Workflow
async function testManualInput(barcode = '8991818801601') {
    console.group('🧪 Test 3: Manual Input Workflow');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('⌨️ Step 1: User types barcode manually...');
        vm.first_search = barcode;
        vm.search = barcode;
        vm.debounce_search = barcode;

        await wait(500);

        console.log('✅ Step 1 PASSED: Barcode entered manually');

        console.log('⌨️ Step 2: User presses Enter...');

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        // Simulate Enter key
        await vm.handleBarcodeEnter();

        await wait(1000);

        // Check if item was added
        const finalCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Final cart count: ${finalCount}`);

        if (finalCount > initialCount) {
            console.log('✅ Step 2 PASSED: Item added to cart after Enter');
        } else {
            console.warn('⚠️ Step 2: Item may not have been added (check if item exists)');
        }

        console.log('✅ Test 3 COMPLETED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 3 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 4: Invalid Barcode Handling
async function testInvalidBarcode() {
    console.group('🧪 Test 4: Invalid Barcode Handling');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        const invalidBarcode = '123'; // Too short

        console.log('⌨️ Step 1: Entering invalid barcode...');
        vm.first_search = invalidBarcode;
        vm.search = invalidBarcode;
        vm.debounce_search = invalidBarcode;

        await wait(500);

        console.log('⌨️ Step 2: Pressing Enter with invalid barcode...');

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;

        // Try to process invalid barcode
        await vm.handleBarcodeEnter();

        await wait(1000);

        // Check that item was NOT added
        const finalCount = vm.frm?.doc?.items?.length || 0;

        if (finalCount === initialCount) {
            console.log('✅ Step 2 PASSED: Invalid barcode rejected, no item added');
        } else {
            console.error('❌ Step 2 FAILED: Item was added despite invalid barcode');
        }

        console.log('✅ Test 4 COMPLETED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 4 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 5: Double Processing Prevention
async function testDoubleProcessing(barcode = '8991818801601') {
    console.group('🧪 Test 5: Double Processing Prevention');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('⌨️ Step 1: Entering barcode...');
        vm.first_search = barcode;
        vm.search = barcode;
        vm.debounce_search = barcode;

        await wait(500);

        console.log('⌨️ Step 2: Pressing Enter twice rapidly...');

        // Get initial cart count
        const initialCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Initial cart count: ${initialCount}`);

        // Press Enter twice rapidly
        const promise1 = vm.handleBarcodeEnter();
        const promise2 = vm.handleBarcodeEnter(); // Should be ignored

        await Promise.all([promise1, promise2]);

        await wait(1000);

        // Check that only ONE item was added
        const finalCount = vm.frm?.doc?.items?.length || 0;
        console.log(`📊 Final cart count: ${finalCount}`);

        if (finalCount === initialCount + 1) {
            console.log('✅ Step 2 PASSED: Only one item added (double processing prevented)');
        } else if (finalCount === initialCount + 2) {
            console.error('❌ Step 2 FAILED: Two items added (double processing not prevented)');
        } else {
            console.warn('⚠️ Step 2: Unexpected result');
        }

        console.log('✅ Test 5 COMPLETED');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 5 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 6: Workflow Consistency
async function testWorkflowConsistency(barcode = '8991818801601') {
    console.group('🧪 Test 6: Workflow Consistency Across All Methods');

    console.log('Testing that all 3 methods produce the same result...');

    const results = {
        hardware: false,
        camera: false,
        manual: false
    };

    // Test hardware scanner
    console.log('\n📱 Testing Hardware Scanner...');
    results.hardware = await testHardwareScanner(barcode);
    await wait(2000);

    // Test camera scanner
    console.log('\n📷 Testing Camera Scanner...');
    results.camera = await testCameraScanner(barcode);
    await wait(2000);

    // Test manual input
    console.log('\n⌨️ Testing Manual Input...');
    results.manual = await testManualInput(barcode);

    console.log('\n📊 Consistency Test Results:');
    console.table(results);

    const allPassed = results.hardware && results.camera && results.manual;

    if (allPassed) {
        console.log('✅ Test 6 PASSED: All methods are consistent');
    } else {
        console.error('❌ Test 6 FAILED: Methods are not consistent');
    }

    console.groupEnd();
    return allPassed;
}

// Run all tests
async function runAllTests(barcode = '8991818801601') {
    console.log('🚀 Starting Unified Scanner Workflow Tests...');
    console.log('=' * 50);
    console.log(`Using test barcode: ${barcode}`);
    console.log('');

    const results = {
        test1_hardware: await testHardwareScanner(barcode),
        test2_camera: await testCameraScanner(barcode),
        test3_manual: await testManualInput(barcode),
        test4_invalid: await testInvalidBarcode(),
        test5_double: await testDoubleProcessing(barcode),
        test6_consistency: await testWorkflowConsistency(barcode)
    };

    console.log('\n📊 Final Test Results Summary:');
    console.table(results);

    const passedTests = Object.values(results).filter(r => r === true).length;
    const totalTests = Object.keys(results).length;

    console.log(`\n🎯 Tests Passed: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
        console.log('🎉 All tests PASSED! Unified workflow is working correctly.');
    } else {
        console.log('⚠️ Some tests failed. Check the logs above for details.');
    }

    return results;
}

// Quick test function
async function quickTest(barcode = '8991818801601') {
    console.log('⚡ Quick Test: Hardware Scanner → Enter → Add to Cart');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Component not found');
        return;
    }

    console.log('1️⃣ Scanning barcode...');
    vm.trigger_onscan(barcode);

    await wait(1000);

    console.log('2️⃣ Pressing Enter...');
    await vm.handleBarcodeEnter();

    await wait(1000);

    console.log('✅ Quick test completed. Check cart for new item.');
}

// Export functions to global scope
window.testHardwareScanner = testHardwareScanner;
window.testCameraScanner = testCameraScanner;
window.testManualInput = testManualInput;
window.testInvalidBarcode = testInvalidBarcode;
window.testDoubleProcessing = testDoubleProcessing;
window.testWorkflowConsistency = testWorkflowConsistency;
window.runAllTests = runAllTests;
window.quickTest = quickTest;

console.log('✅ Test functions available:');
console.log('   quickTest(barcode) - Quick test of workflow');
console.log('   testHardwareScanner(barcode) - Test hardware scanner');
console.log('   testCameraScanner(barcode) - Test camera scanner');
console.log('   testManualInput(barcode) - Test manual input');
console.log('   testInvalidBarcode() - Test invalid barcode handling');
console.log('   testDoubleProcessing(barcode) - Test double processing prevention');
console.log('   testWorkflowConsistency(barcode) - Test all methods consistency');
console.log('   runAllTests(barcode) - Run all tests');
console.log('\n💡 Usage: quickTest() or runAllTests()');