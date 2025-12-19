// 🐛 Debug Product Search Popup Issue
// Run this in browser console to debug popup problems

console.log('🐛 Debugging Product Search Popup Issue');

// Check if popup is visible
function checkPopupState() {
    console.group('📊 Popup State Check');

    const itemsSelector = window.$vm0;
    if (!itemsSelector) {
        console.error('❌ ItemsSelector not found ($vm0)');
        console.groupEnd();
        return;
    }

    console.log('✅ ItemsSelector found');
    console.log('🔍 product_search_popup_visible:', itemsSelector.product_search_popup_visible);
    console.log('🔍 pos_profile:', itemsSelector.pos_profile);
    console.log('🔍 active_price_list:', itemsSelector.active_price_list);
    console.log('🔍 customer:', itemsSelector.customer);

    console.groupEnd();
}

// Check if ProductSearchPopup component is loaded
function checkPopupComponent() {
    console.group('🧩 Component Check');

    const itemsSelector = window.$vm0;
    if (!itemsSelector) {
        console.error('❌ ItemsSelector not found');
        console.groupEnd();
        return;
    }

    console.log('🔍 Components:', Object.keys(itemsSelector.$options.components));
    console.log('🔍 ProductSearchPopup component:', itemsSelector.$options.components.ProductSearchPopup);

    // Check if popup component instance exists
    const popupComponent = itemsSelector.$children?.find(child =>
        child.$options.name === 'ProductSearchPopup'
    );

    if (popupComponent) {
        console.log('✅ ProductSearchPopup component instance found');
        console.log('🔍 Popup props:', {
            visible: popupComponent.visible,
            posProfile: popupComponent.posProfile,
            priceList: popupComponent.priceList,
            customer: popupComponent.customer
        });
        console.log('🔍 Popup data:', {
            searchTerm: popupComponent.searchTerm,
            searchResults: popupComponent.searchResults,
            isSearching: popupComponent.isSearching,
            hasSearched: popupComponent.hasSearched,
            errorMessage: popupComponent.errorMessage
        });
    } else {
        console.error('❌ ProductSearchPopup component instance not found');
    }

    console.groupEnd();
}

// Check frappe availability
function checkFrappeAPI() {
    console.group('🌐 Frappe API Check');

    console.log('🔍 frappe object:', typeof frappe);
    console.log('🔍 frappe.call:', typeof frappe?.call);

    if (typeof frappe === 'undefined') {
        console.error('❌ frappe object not available');
        console.groupEnd();
        return;
    }

    console.log('✅ frappe object available');

    // Test API method exists
    console.log('🔍 Testing API method...');
    frappe.call({
        method: "posawesome.posawesome.api.items.search_items_for_popup",
        args: {
            search_term: "test",
            pos_profile: JSON.stringify(window.$vm0?.pos_profile || {}),
            price_list: window.$vm0?.active_price_list || "Standard Selling",
            customer: null,
            limit: 5
        },
        callback: (r) => {
            if (r.message) {
                console.log('✅ API method works, returned:', r.message.length, 'items');
            } else {
                console.warn('⚠️ API method returned no data');
            }
        },
        error: (err) => {
            console.error('❌ API method failed:', err);
        }
    });

    console.groupEnd();
}

// Test popup open/close
function testPopupOpenClose() {
    console.group('🔄 Popup Open/Close Test');

    const itemsSelector = window.$vm0;
    if (!itemsSelector) {
        console.error('❌ ItemsSelector not found');
        console.groupEnd();
        return;
    }

    console.log('📂 Opening popup...');
    itemsSelector.openProductSearchPopup();

    setTimeout(() => {
        console.log('🔍 Popup state after open:', itemsSelector.product_search_popup_visible);

        console.log('📁 Closing popup...');
        itemsSelector.closeProductSearchPopup();

        setTimeout(() => {
            console.log('🔍 Popup state after close:', itemsSelector.product_search_popup_visible);
            console.groupEnd();
        }, 500);
    }, 1000);
}

// Check console errors
function checkConsoleErrors() {
    console.group('🚨 Console Errors Check');

    console.log('💡 Check browser console for any JavaScript errors');
    console.log('💡 Look for:');
    console.log('   - Component compilation errors');
    console.log('   - Import/export errors');
    console.log('   - API call errors');
    console.log('   - Vue.js warnings');

    console.groupEnd();
}

// Fix popup if stuck
function fixStuckPopup() {
    console.group('🔧 Fix Stuck Popup');

    const itemsSelector = window.$vm0;
    if (!itemsSelector) {
        console.error('❌ ItemsSelector not found');
        console.groupEnd();
        return;
    }

    console.log('🔧 Attempting to fix stuck popup...');

    // Force close popup
    itemsSelector.product_search_popup_visible = false;

    // Wait a bit then try to open again
    setTimeout(() => {
        console.log('🔧 Reopening popup...');
        itemsSelector.product_search_popup_visible = true;

        // Force update
        itemsSelector.$forceUpdate();

        console.log('✅ Popup fix attempted');
        console.groupEnd();
    }, 500);
}

// Run all checks
function runAllChecks() {
    console.log('🚀 Running all popup debug checks...');
    console.log('=' * 50);

    checkPopupState();
    checkPopupComponent();
    checkFrappeAPI();
    checkConsoleErrors();

    console.log('\n🔧 Available fix functions:');
    console.log('   fixStuckPopup() - Fix stuck popup');
    console.log('   testPopupOpenClose() - Test open/close');
}

// Export functions to global scope
window.checkPopupState = checkPopupState;
window.checkPopupComponent = checkPopupComponent;
window.checkFrappeAPI = checkFrappeAPI;
window.testPopupOpenClose = testPopupOpenClose;
window.fixStuckPopup = fixStuckPopup;
window.runAllChecks = runAllChecks;

console.log('✅ Debug functions available:');
console.log('   runAllChecks() - Run all debug checks');
console.log('   checkPopupState() - Check popup state');
console.log('   checkPopupComponent() - Check component');
console.log('   checkFrappeAPI() - Check API');
console.log('   fixStuckPopup() - Fix stuck popup');
console.log('   testPopupOpenClose() - Test functionality');
console.log('\n💡 Usage: runAllChecks()');