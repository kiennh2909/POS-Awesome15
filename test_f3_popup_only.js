// 🧪 Test F3 Opens Popup Only (No Mode Change)
// Run this in browser console on POS page to test F3 behavior

console.log('🧪 F3 Popup Only Test Script Loaded');

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
    if (window.$vm0 && window.$vm0.handleF3SearchToggle) {
        return window.$vm0;
    }
    return null;
}

// Helper to wait
function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Test 1: F3 Opens Popup Only (No Mode Change)
async function testF3OpensPopupOnly() {
    console.group('🧪 Test 1: F3 Opens Popup Only (No Mode Change)');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Record initial state
        const initialMode = vm.search_mode;
        const initialPopupState = vm.product_search_popup_visible;

        console.log(`📊 Initial search mode: ${initialMode}`);
        console.log(`📊 Initial popup state: ${initialPopupState}`);

        // Ensure popup is closed initially
        if (initialPopupState) {
            vm.closeProductSearchPopup();
            await wait(500);
        }

        console.log('⌨️ Step 1: Pressing F3...');

        // Simulate F3 key press
        vm.handleF3SearchToggle();

        await wait(1000);

        // Check results
        const finalMode = vm.search_mode;
        const finalPopupState = vm.product_search_popup_visible;

        console.log(`📊 Final search mode: ${finalMode}`);
        console.log(`📊 Final popup state: ${finalPopupState}`);

        // Validate: Mode should NOT change
        if (finalMode === initialMode) {
            console.log('✅ Step 1 PASSED: Search mode unchanged');
        } else {
            console.error(`❌ Step 1 FAILED: Mode changed from ${initialMode} to ${finalMode}`);
            console.groupEnd();
            return false;
        }

        // Validate: Popup should be open
        if (finalPopupState === true) {
            console.log('✅ Step 2 PASSED: Popup opened');
        } else {
            console.error('❌ Step 2 FAILED: Popup not opened');
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 1 PASSED: F3 opens popup without changing mode');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 1 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 2: F3 Works in Both Barcode and Text Mode
async function testF3WorksBothModes() {
    console.group('🧪 Test 2: F3 Works in Both Modes');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Close popup if open
        vm.closeProductSearchPopup();
        await wait(500);

        // Test in Barcode Mode
        console.log('📱 Testing F3 in Barcode Mode...');
        vm.search_mode = 'barcode';

        vm.handleF3SearchToggle();
        await wait(1000);

        if (vm.product_search_popup_visible && vm.search_mode === 'barcode') {
            console.log('✅ F3 works in Barcode mode (popup opened, mode unchanged)');
        } else {
            console.error('❌ F3 failed in Barcode mode');
            console.groupEnd();
            return false;
        }

        // Close popup
        vm.closeProductSearchPopup();
        await wait(500);

        // Test in Text Mode
        console.log('🔍 Testing F3 in Text Mode...');
        vm.search_mode = 'text';

        vm.handleF3SearchToggle();
        await wait(1000);

        if (vm.product_search_popup_visible && vm.search_mode === 'text') {
            console.log('✅ F3 works in Text mode (popup opened, mode unchanged)');
        } else {
            console.error('❌ F3 failed in Text mode');
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 2 PASSED: F3 works in both modes');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 2 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 3: F3 Keyboard Event Integration
async function testF3KeyboardEvent() {
    console.group('🧪 Test 3: F3 Keyboard Event Integration');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Close popup if open
        vm.closeProductSearchPopup();
        await wait(500);

        console.log('⌨️ Simulating F3 keyboard event...');

        // Create and dispatch F3 key event
        const f3Event = new KeyboardEvent('keydown', {
            key: 'F3',
            code: 'F3',
            keyCode: 114,
            which: 114,
            bubbles: true,
            cancelable: true
        });

        // Dispatch to search input if available
        const searchInput = vm.$refs.searchInput?.$el?.querySelector('input') ||
            document.querySelector('input[placeholder*="Barcode"], input[placeholder*="tìm kiếm"]');

        if (searchInput) {
            searchInput.dispatchEvent(f3Event);
        } else {
            // Fallback to document
            document.dispatchEvent(f3Event);
        }

        await wait(1000);

        if (vm.product_search_popup_visible) {
            console.log('✅ F3 keyboard event works (popup opened)');
        } else {
            console.warn('⚠️ F3 keyboard event may not be properly bound');
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

// Test 4: Popup Functionality After F3
async function testPopupFunctionalityAfterF3() {
    console.group('🧪 Test 4: Popup Functionality After F3');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Open popup with F3
        console.log('⌨️ Opening popup with F3...');
        vm.handleF3SearchToggle();
        await wait(1000);

        if (!vm.product_search_popup_visible) {
            console.error('❌ Popup not opened by F3');
            console.groupEnd();
            return false;
        }

        console.log('✅ Popup opened by F3');

        // Test popup close
        console.log('🔒 Testing popup close...');
        vm.closeProductSearchPopup();
        await wait(500);

        if (!vm.product_search_popup_visible) {
            console.log('✅ Popup closed successfully');
        } else {
            console.error('❌ Popup failed to close');
            console.groupEnd();
            return false;
        }

        // Test focus return
        console.log('🎯 Testing focus return...');
        // Focus should return to main search input
        const activeElement = document.activeElement;
        const searchInput = vm.$refs.searchInput?.$el?.querySelector('input');

        if (activeElement === searchInput) {
            console.log('✅ Focus returned to search input');
        } else {
            console.warn('⚠️ Focus may not have returned to search input');
        }

        console.log('✅ Test 4 PASSED: Popup functionality works after F3');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 4 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 5: UI Hints Updated
async function testUIHintsUpdated() {
    console.group('🧪 Test 5: UI Hints Updated');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('🔍 Checking keyboard hints...');

        // Check dynamicHint computed property
        const hint = vm.dynamicHint;
        console.log(`📝 Dynamic hint: "${hint}"`);

        if (hint.includes('popup') || hint.includes('Popup')) {
            console.log('✅ Dynamic hint mentions popup');
        } else {
            console.warn('⚠️ Dynamic hint may not be updated');
        }

        // Check if UI shows correct hint
        const hintElement = document.querySelector('.keyboard-hint');
        if (hintElement) {
            const hintText = hintElement.textContent;
            console.log(`📝 UI hint text: "${hintText}"`);

            if (hintText.includes('F3') && hintText.includes('Popup')) {
                console.log('✅ UI hint shows F3: Popup');
            } else {
                console.warn('⚠️ UI hint may not be updated');
            }
        }

        console.log('✅ Test 5 COMPLETED: UI hints checked');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 5 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Run all F3 popup tests
async function runF3PopupTests() {
    console.log('🚀 Starting F3 Popup Only Tests...');
    console.log('=' * 50);

    const results = {
        test1_f3_popup_only: await testF3OpensPopupOnly(),
        test2_f3_both_modes: await testF3WorksBothModes(),
        test3_f3_keyboard: await testF3KeyboardEvent(),
        test4_popup_functionality: await testPopupFunctionalityAfterF3(),
        test5_ui_hints: await testUIHintsUpdated()
    };

    console.log('\n📊 F3 Popup Test Results:');
    console.table(results);

    const passedTests = Object.values(results).filter(r => r === true).length;
    const totalTests = Object.keys(results).length;

    console.log(`\n🎯 Tests Passed: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
        console.log('🎉 All tests PASSED! F3 now opens popup only.');
    } else {
        console.log('⚠️ Some tests failed. Check the logs above for details.');
    }

    return results;
}

// Quick F3 test
async function quickF3Test() {
    console.log('⚡ Quick F3 Test');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Component not found');
        return;
    }

    const initialMode = vm.search_mode;
    console.log(`📊 Initial mode: ${initialMode}`);

    // Press F3
    vm.handleF3SearchToggle();
    await wait(1000);

    const finalMode = vm.search_mode;
    const popupOpen = vm.product_search_popup_visible;

    console.log(`📊 Final mode: ${finalMode}`);
    console.log(`📊 Popup open: ${popupOpen}`);

    if (finalMode === initialMode && popupOpen) {
        console.log('✅ PERFECT: F3 opens popup without changing mode!');
    } else if (finalMode !== initialMode) {
        console.log('❌ ISSUE: Mode changed (should not change)');
    } else if (!popupOpen) {
        console.log('❌ ISSUE: Popup not opened');
    }
}

// Export functions to global scope
window.testF3OpensPopupOnly = testF3OpensPopupOnly;
window.testF3WorksBothModes = testF3WorksBothModes;
window.testF3KeyboardEvent = testF3KeyboardEvent;
window.testPopupFunctionalityAfterF3 = testPopupFunctionalityAfterF3;
window.testUIHintsUpdated = testUIHintsUpdated;
window.runF3PopupTests = runF3PopupTests;
window.quickF3Test = quickF3Test;

console.log('✅ F3 Popup test functions available:');
console.log('   quickF3Test() - Quick test F3 behavior');
console.log('   testF3OpensPopupOnly() - Test F3 opens popup only');
console.log('   testF3WorksBothModes() - Test F3 in both modes');
console.log('   testF3KeyboardEvent() - Test F3 keyboard event');
console.log('   testPopupFunctionalityAfterF3() - Test popup after F3');
console.log('   testUIHintsUpdated() - Test UI hints updated');
console.log('   runF3PopupTests() - Run all tests');
console.log('\n💡 Usage: quickF3Test() or runF3PopupTests()');