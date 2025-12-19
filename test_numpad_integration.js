/**
 * 🔢 Test NumPad Integration
 * 
 * Test cases for ItemEditNumPad integration with ItemsTable.vue
 * Run in browser console when POS is loaded
 */

console.log('🔢 [NUMPAD_TEST] Starting NumPad Integration Tests...');

// Test 1: Check if NumPad component is loaded
function testNumPadComponentLoaded() {
    console.log('📋 [TEST 1] Checking NumPad component...');

    const itemsTable = document.querySelector('.items-table-container');
    if (!itemsTable) {
        console.error('❌ [TEST 1] ItemsTable container not found');
        return false;
    }

    // Check if Vue component has NumPad
    const vueInstance = itemsTable.__vue__;
    if (!vueInstance) {
        console.error('❌ [TEST 1] Vue instance not found');
        return false;
    }

    if (vueInstance.$options.components && vueInstance.$options.components.ItemEditNumPad) {
        console.log('✅ [TEST 1] ItemEditNumPad component is loaded');
        return true;
    } else {
        console.error('❌ [TEST 1] ItemEditNumPad component not found in components');
        return false;
    }
}

// Test 2: Check if click handler is attached
function testClickHandlerAttached() {
    console.log('📋 [TEST 2] Checking click handler...');

    const dataTable = document.querySelector('.v-data-table-virtual');
    if (!dataTable) {
        console.error('❌ [TEST 2] Data table not found');
        return false;
    }

    const vueInstance = dataTable.__vue__;
    if (vueInstance && vueInstance.$listeners && vueInstance.$listeners['click:row']) {
        console.log('✅ [TEST 2] Click handler is attached');
        return true;
    } else {
        console.error('❌ [TEST 2] Click handler not found');
        return false;
    }
}

// Test 3: Simulate row click
function testRowClick() {
    console.log('📋 [TEST 3] Simulating row click...');

    const firstRow = document.querySelector('.v-data-table-virtual tbody tr');
    if (!firstRow) {
        console.error('❌ [TEST 3] No table rows found');
        return false;
    }

    // Simulate click event
    const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
    });

    firstRow.dispatchEvent(clickEvent);

    // Check if NumPad opened
    setTimeout(() => {
        const numpadDialog = document.querySelector('.item-edit-numpad');
        if (numpadDialog) {
            console.log('✅ [TEST 3] NumPad opened successfully');
            return true;
        } else {
            console.error('❌ [TEST 3] NumPad did not open');
            return false;
        }
    }, 100);
}

// Test 4: Test NumPad keyboard input
function testNumPadKeyboard() {
    console.log('📋 [TEST 4] Testing NumPad keyboard...');

    const numpadDialog = document.querySelector('.item-edit-numpad');
    if (!numpadDialog) {
        console.error('❌ [TEST 4] NumPad not open, run testRowClick() first');
        return false;
    }

    // Simulate number key press
    const keyEvent = new KeyboardEvent('keydown', {
        key: '5',
        code: 'Digit5',
        bubbles: true
    });

    numpadDialog.dispatchEvent(keyEvent);

    // Check if display updated
    setTimeout(() => {
        const displayField = numpadDialog.querySelector('.display-field input');
        if (displayField && displayField.value.includes('5')) {
            console.log('✅ [TEST 4] Keyboard input working');
            return true;
        } else {
            console.error('❌ [TEST 4] Keyboard input not working');
            return false;
        }
    }, 100);
}

// Test 5: Test field switching
function testFieldSwitching() {
    console.log('📋 [TEST 5] Testing field switching...');

    const rateButton = document.querySelector('.field-toggle .v-btn[value="rate"]');
    if (!rateButton) {
        console.error('❌ [TEST 5] Rate button not found');
        return false;
    }

    rateButton.click();

    setTimeout(() => {
        const displayField = document.querySelector('.display-field input');
        const label = displayField?.getAttribute('label') || '';

        if (label.includes('Đơn Giá')) {
            console.log('✅ [TEST 5] Field switching working');
            return true;
        } else {
            console.error('❌ [TEST 5] Field switching not working');
            return false;
        }
    }, 100);
}

// Test 6: Test Enter confirmation
function testEnterConfirmation() {
    console.log('📋 [TEST 6] Testing Enter confirmation...');

    const enterButton = document.querySelector('.enter-btn');
    if (!enterButton) {
        console.error('❌ [TEST 6] Enter button not found');
        return false;
    }

    // Check if button is enabled
    if (enterButton.disabled) {
        console.error('❌ [TEST 6] Enter button is disabled');
        return false;
    }

    enterButton.click();

    console.log('✅ [TEST 6] Enter confirmation triggered');
    return true;
}

// Test 7: Test ESC close
function testEscClose() {
    console.log('📋 [TEST 7] Testing ESC close...');

    const numpadDialog = document.querySelector('.item-edit-numpad');
    if (!numpadDialog) {
        console.error('❌ [TEST 7] NumPad not open');
        return false;
    }

    // Simulate ESC key
    const escEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        code: 'Escape',
        bubbles: true
    });

    numpadDialog.dispatchEvent(escEvent);

    setTimeout(() => {
        const numpadAfter = document.querySelector('.item-edit-numpad');
        if (!numpadAfter) {
            console.log('✅ [TEST 7] ESC close working');
            return true;
        } else {
            console.error('❌ [TEST 7] ESC close not working');
            return false;
        }
    }, 100);
}

// Run all tests
function runAllTests() {
    console.log('🚀 [NUMPAD_TEST] Running all NumPad integration tests...');

    const tests = [
        testNumPadComponentLoaded,
        testClickHandlerAttached,
        testRowClick,
        // testNumPadKeyboard,  // Requires NumPad to be open
        // testFieldSwitching,  // Requires NumPad to be open
        // testEnterConfirmation, // Requires NumPad to be open
        // testEscClose         // Requires NumPad to be open
    ];

    let passed = 0;
    let total = tests.length;

    tests.forEach((test, index) => {
        try {
            if (test()) {
                passed++;
            }
        } catch (error) {
            console.error(`❌ [TEST ${index + 1}] Error:`, error);
        }
    });

    console.log(`📊 [NUMPAD_TEST] Results: ${passed}/${total} tests passed`);

    if (passed === total) {
        console.log('🎉 [NUMPAD_TEST] All tests passed! NumPad integration is working correctly.');
    } else {
        console.log('⚠️ [NUMPAD_TEST] Some tests failed. Check the integration.');
    }
}

// Manual test functions for interactive testing
window.numpadTests = {
    runAll: runAllTests,
    testComponent: testNumPadComponentLoaded,
    testClick: testRowClick,
    testKeyboard: testNumPadKeyboard,
    testFields: testFieldSwitching,
    testEnter: testEnterConfirmation,
    testEsc: testEscClose
};

console.log('🔢 [NUMPAD_TEST] Test functions loaded. Run numpadTests.runAll() to start testing.');
console.log('🔢 [NUMPAD_TEST] Individual tests: numpadTests.testComponent(), numpadTests.testClick(), etc.');

// Auto-run basic tests
runAllTests();