// 🧪 Test Popup Freeze Fix
// Run this in browser console to test if popup freeze is fixed

console.log('🧪 Popup Freeze Fix Test Script Loaded');

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
    if (window.$vm0 && window.$vm0.openProductSearchPopup) {
        return window.$vm0;
    }
    return null;
}

// Helper to wait
function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Test 1: Basic Popup Open/Close (No Freeze)
async function testPopupNoFreeze() {
    console.group('🧪 Test 1: Popup Open/Close (No Freeze)');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('📂 Step 1: Opening popup...');

        // Monitor for infinite loops
        let openCallCount = 0;
        const originalOpen = vm.openProductSearchPopup;
        vm.openProductSearchPopup = function () {
            openCallCount++;
            if (openCallCount > 5) {
                console.error('❌ INFINITE LOOP DETECTED in openProductSearchPopup');
                return false;
            }
            return originalOpen.call(this);
        };

        // Open popup
        vm.openProductSearchPopup();

        await wait(2000); // Wait to see if it freezes

        if (vm.product_search_popup_visible) {
            console.log('✅ Step 1 PASSED: Popup opened without freeze');
        } else {
            console.error('❌ Step 1 FAILED: Popup not opened');
            console.groupEnd();
            return false;
        }

        console.log('📁 Step 2: Closing popup...');

        // Monitor for infinite loops in close
        let closeCallCount = 0;
        const originalClose = vm.closeProductSearchPopup;
        vm.closeProductSearchPopup = function () {
            closeCallCount++;
            if (closeCallCount > 5) {
                console.error('❌ INFINITE LOOP DETECTED in closeProductSearchPopup');
                return false;
            }
            return originalClose.call(this);
        };

        // Close popup
        vm.closeProductSearchPopup();

        await wait(1000);

        if (!vm.product_search_popup_visible) {
            console.log('✅ Step 2 PASSED: Popup closed without freeze');
        } else {
            console.error('❌ Step 2 FAILED: Popup not closed');
            console.groupEnd();
            return false;
        }

        // Restore original methods
        vm.openProductSearchPopup = originalOpen;
        vm.closeProductSearchPopup = originalClose;

        console.log(`📊 Open calls: ${openCallCount}, Close calls: ${closeCallCount}`);

        if (openCallCount <= 2 && closeCallCount <= 2) {
            console.log('✅ No infinite loops detected');
        } else {
            console.warn('⚠️ Suspicious call counts - possible loops');
        }

        console.log('✅ Test 1 PASSED: No freeze detected');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 1 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 2: F3 Key No Freeze
async function testF3NoFreeze() {
    console.group('🧪 Test 2: F3 Key No Freeze');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        // Ensure popup is closed
        if (vm.product_search_popup_visible) {
            vm.closeProductSearchPopup();
            await wait(500);
        }

        console.log('⌨️ Step 1: Pressing F3...');

        // Monitor for freeze
        const startTime = Date.now();

        // Press F3
        vm.handleF3SearchToggle();

        await wait(2000);

        const endTime = Date.now();
        const duration = endTime - startTime;

        console.log(`⏱️ F3 processing time: ${duration}ms`);

        if (duration > 5000) {
            console.error('❌ F3 took too long - possible freeze');
            console.groupEnd();
            return false;
        }

        if (vm.product_search_popup_visible) {
            console.log('✅ Step 1 PASSED: F3 opened popup without freeze');
        } else {
            console.error('❌ Step 1 FAILED: F3 did not open popup');
            console.groupEnd();
            return false;
        }

        console.log('✅ Test 2 PASSED: F3 works without freeze');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 2 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 3: Multiple Open/Close Cycles
async function testMultipleCycles() {
    console.group('🧪 Test 3: Multiple Open/Close Cycles');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('🔄 Testing 5 open/close cycles...');

        for (let i = 1; i <= 5; i++) {
            console.log(`🔄 Cycle ${i}/5`);

            // Open
            const openStart = Date.now();
            vm.openProductSearchPopup();
            await wait(500);
            const openEnd = Date.now();

            if (openEnd - openStart > 2000) {
                console.error(`❌ Cycle ${i} open took too long: ${openEnd - openStart}ms`);
                console.groupEnd();
                return false;
            }

            if (!vm.product_search_popup_visible) {
                console.error(`❌ Cycle ${i} failed to open popup`);
                console.groupEnd();
                return false;
            }

            // Close
            const closeStart = Date.now();
            vm.closeProductSearchPopup();
            await wait(500);
            const closeEnd = Date.now();

            if (closeEnd - closeStart > 2000) {
                console.error(`❌ Cycle ${i} close took too long: ${closeEnd - closeStart}ms`);
                console.groupEnd();
                return false;
            }

            if (vm.product_search_popup_visible) {
                console.error(`❌ Cycle ${i} failed to close popup`);
                console.groupEnd();
                return false;
            }

            console.log(`✅ Cycle ${i} completed successfully`);
        }

        console.log('✅ Test 3 PASSED: All cycles completed without freeze');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 3 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Test 4: Browser Responsiveness During Popup
async function testBrowserResponsiveness() {
    console.group('🧪 Test 4: Browser Responsiveness');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Could not find ItemsSelector component');
        console.groupEnd();
        return false;
    }

    try {
        console.log('📱 Testing browser responsiveness during popup...');

        // Open popup
        vm.openProductSearchPopup();
        await wait(1000);

        // Test if browser is responsive
        const testStart = Date.now();

        // Try to interact with DOM
        const testDiv = document.createElement('div');
        testDiv.id = 'responsiveness-test';
        testDiv.textContent = 'Test';
        document.body.appendChild(testDiv);

        // Try to query the element
        const foundDiv = document.getElementById('responsiveness-test');

        // Clean up
        document.body.removeChild(testDiv);

        const testEnd = Date.now();
        const responseTime = testEnd - testStart;

        console.log(`⏱️ DOM interaction time: ${responseTime}ms`);

        if (responseTime > 1000) {
            console.error('❌ Browser seems unresponsive');
            console.groupEnd();
            return false;
        }

        if (foundDiv && foundDiv.textContent === 'Test') {
            console.log('✅ Browser is responsive during popup');
        } else {
            console.error('❌ DOM interaction failed');
            console.groupEnd();
            return false;
        }

        // Close popup
        vm.closeProductSearchPopup();

        console.log('✅ Test 4 PASSED: Browser remains responsive');
        console.groupEnd();
        return true;

    } catch (error) {
        console.error('❌ Test 4 FAILED:', error);
        console.groupEnd();
        return false;
    }
}

// Run all freeze tests
async function runFreezeTests() {
    console.log('🚀 Starting Popup Freeze Fix Tests...');
    console.log('=' * 50);

    const results = {
        test1_no_freeze: await testPopupNoFreeze(),
        test2_f3_no_freeze: await testF3NoFreeze(),
        test3_multiple_cycles: await testMultipleCycles(),
        test4_responsiveness: await testBrowserResponsiveness()
    };

    console.log('\n📊 Freeze Fix Test Results:');
    console.table(results);

    const passedTests = Object.values(results).filter(r => r === true).length;
    const totalTests = Object.keys(results).length;

    console.log(`\n🎯 Tests Passed: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
        console.log('🎉 All tests PASSED! Popup freeze is FIXED!');
    } else {
        console.log('⚠️ Some tests failed. Freeze issue may still exist.');
    }

    return results;
}

// Quick freeze test
async function quickFreezeTest() {
    console.log('⚡ Quick Freeze Test');

    const vm = findItemsSelector();
    if (!vm) {
        console.error('❌ Component not found');
        return;
    }

    console.log('📂 Opening popup...');
    const startTime = Date.now();

    vm.openProductSearchPopup();

    await wait(2000);

    const endTime = Date.now();
    const duration = endTime - startTime;

    console.log(`⏱️ Duration: ${duration}ms`);
    console.log(`📊 Popup visible: ${vm.product_search_popup_visible}`);

    if (duration < 3000 && vm.product_search_popup_visible) {
        console.log('✅ SUCCESS: Popup opens without freeze!');
    } else if (duration >= 3000) {
        console.log('❌ FREEZE: Took too long to open');
    } else {
        console.log('❌ FAILED: Popup not visible');
    }

    // Close popup
    vm.closeProductSearchPopup();
}

// Export functions to global scope
window.testPopupNoFreeze = testPopupNoFreeze;
window.testF3NoFreeze = testF3NoFreeze;
window.testMultipleCycles = testMultipleCycles;
window.testBrowserResponsiveness = testBrowserResponsiveness;
window.runFreezeTests = runFreezeTests;
window.quickFreezeTest = quickFreezeTest;

console.log('✅ Freeze fix test functions available:');
console.log('   quickFreezeTest() - Quick test for freeze');
console.log('   testPopupNoFreeze() - Test popup open/close');
console.log('   testF3NoFreeze() - Test F3 key');
console.log('   testMultipleCycles() - Test multiple cycles');
console.log('   testBrowserResponsiveness() - Test browser response');
console.log('   runFreezeTests() - Run all tests');
console.log('\n💡 Usage: quickFreezeTest() or runFreezeTests()');