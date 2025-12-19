// 🧪 Simple F3 Popup Test Script
// Run this in browser console to test F3 popup step by step

console.log('🧪 Simple F3 Popup Test Script');

// Step 1: Check if everything is loaded
function step1_checkBasics() {
    console.group('📋 Step 1: Check Basics');

    // Check frappe
    const frappeOK = typeof frappe !== 'undefined';
    console.log('✅ frappe available:', frappeOK);

    // Check $vm0
    const vm0OK = typeof window.$vm0 !== 'undefined';
    console.log('✅ $vm0 available:', vm0OK);

    if (!vm0OK) {
        console.error('❌ $vm0 not found. Make sure you are on POS page.');
        console.groupEnd();
        return false;
    }

    // Check component
    const componentOK = !!window.$vm0.$options.components.ProductSearchPopup;
    console.log('✅ ProductSearchPopup component:', componentOK);

    // Check data
    const dataOK = 'product_search_popup_visible' in window.$vm0;
    console.log('✅ popup data property:', dataOK);

    // Check methods
    const methodsOK = typeof window.$vm0.openProductSearchPopup === 'function';
    console.log('✅ popup methods:', methodsOK);

    console.groupEnd();
    return frappeOK && vm0OK && componentOK && dataOK && methodsOK;
}

// Step 2: Test F3 key
function step2_testF3() {
    console.group('🔑 Step 2: Test F3 Key');

    const vm = window.$vm0;

    console.log('🔍 Current popup state:', vm.product_search_popup_visible);
    console.log('🔍 F3 enabled:', vm.f3_enabled);

    // Simulate F3 key press
    console.log('⌨️ Simulating F3 key press...');
    vm.handleF3SearchToggle();

    setTimeout(() => {
        console.log('🔍 Popup state after F3:', vm.product_search_popup_visible);
        if (vm.product_search_popup_visible) {
            console.log('✅ F3 opened popup successfully');
        } else {
            console.error('❌ F3 failed to open popup');
        }
        console.groupEnd();
    }, 500);
}

// Step 3: Test popup manually
function step3_testPopupManual() {
    console.group('👆 Step 3: Test Popup Manually');

    const vm = window.$vm0;

    console.log('📂 Opening popup manually...');
    vm.openProductSearchPopup();

    setTimeout(() => {
        console.log('🔍 Popup state:', vm.product_search_popup_visible);

        if (vm.product_search_popup_visible) {
            console.log('✅ Manual open successful');

            // Try to close
            setTimeout(() => {
                console.log('📁 Closing popup...');
                vm.closeProductSearchPopup();

                setTimeout(() => {
                    console.log('🔍 Popup state after close:', vm.product_search_popup_visible);
                    console.groupEnd();
                }, 500);
            }, 1000);
        } else {
            console.error('❌ Manual open failed');
            console.groupEnd();
        }
    }, 500);
}

// Step 4: Test API directly
function step4_testAPI() {
    console.group('🌐 Step 4: Test API');

    const vm = window.$vm0;

    console.log('📡 Testing API call...');
    console.log('🔍 pos_profile:', vm.pos_profile);
    console.log('🔍 active_price_list:', vm.active_price_list);

    frappe.call({
        method: "posawesome.posawesome.api.items.search_items_for_popup",
        args: {
            search_term: "test",
            pos_profile: JSON.stringify(vm.pos_profile || {}),
            price_list: vm.active_price_list || "Standard Selling",
            customer: vm.customer,
            limit: 5
        },
        callback: (r) => {
            console.log('✅ API call successful');
            console.log('📊 Response:', r);
            if (r.message) {
                console.log('📦 Items returned:', r.message.length);
                if (r.message.length > 0) {
                    console.table(r.message.slice(0, 3));
                }
            }
            console.groupEnd();
        },
        error: (err) => {
            console.error('❌ API call failed:', err);
            console.groupEnd();
        }
    });
}

// Step 5: Full integration test
function step5_fullTest() {
    console.group('🎯 Step 5: Full Integration Test');

    const vm = window.$vm0;

    console.log('🚀 Starting full integration test...');

    // 1. Open popup
    console.log('1️⃣ Opening popup...');
    vm.openProductSearchPopup();

    setTimeout(() => {
        if (!vm.product_search_popup_visible) {
            console.error('❌ Popup failed to open');
            console.groupEnd();
            return;
        }

        console.log('✅ Popup opened');

        // 2. Find popup component
        const popupComponent = vm.$children?.find(child =>
            child.$options.name === 'ProductSearchPopup'
        );

        if (!popupComponent) {
            console.error('❌ Popup component not found');
            console.groupEnd();
            return;
        }

        console.log('✅ Popup component found');

        // 3. Test search
        console.log('2️⃣ Testing search...');
        popupComponent.searchTerm = 'test';

        popupComponent.performSearch().then(() => {
            console.log('✅ Search completed');
            console.log('📊 Results:', popupComponent.searchResults.length);

            // 4. Close popup
            setTimeout(() => {
                console.log('3️⃣ Closing popup...');
                vm.closeProductSearchPopup();

                setTimeout(() => {
                    if (!vm.product_search_popup_visible) {
                        console.log('✅ Full integration test PASSED');
                    } else {
                        console.error('❌ Popup failed to close');
                    }
                    console.groupEnd();
                }, 500);
            }, 2000);

        }).catch(error => {
            console.error('❌ Search failed:', error);
            console.groupEnd();
        });

    }, 1000);
}

// Run all tests
function runAllTests() {
    console.log('🚀 Running All F3 Popup Tests...');
    console.log('=' * 50);

    if (!step1_checkBasics()) {
        console.error('❌ Basic checks failed. Cannot continue.');
        return;
    }

    setTimeout(() => step2_testF3(), 1000);
    setTimeout(() => step3_testPopupManual(), 3000);
    setTimeout(() => step4_testAPI(), 6000);
    setTimeout(() => step5_fullTest(), 9000);
}

// Quick fix function
function quickFix() {
    console.log('🔧 Quick Fix: Force popup open...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        return;
    }

    // Force close first
    vm.product_search_popup_visible = false;

    // Force update
    vm.$forceUpdate();

    // Reopen
    setTimeout(() => {
        vm.product_search_popup_visible = true;
        vm.$forceUpdate();
        console.log('✅ Quick fix applied');
    }, 500);
}

// Export functions
window.step1_checkBasics = step1_checkBasics;
window.step2_testF3 = step2_testF3;
window.step3_testPopupManual = step3_testPopupManual;
window.step4_testAPI = step4_testAPI;
window.step5_fullTest = step5_fullTest;
window.runAllTests = runAllTests;
window.quickFix = quickFix;

console.log('✅ Test functions available:');
console.log('   runAllTests() - Run all tests sequentially');
console.log('   step1_checkBasics() - Check if everything is loaded');
console.log('   step2_testF3() - Test F3 key');
console.log('   step3_testPopupManual() - Test manual open/close');
console.log('   step4_testAPI() - Test API call');
console.log('   step5_fullTest() - Full integration test');
console.log('   quickFix() - Quick fix if popup stuck');
console.log('\n🚀 Usage: runAllTests()');