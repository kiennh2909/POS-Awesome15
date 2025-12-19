// 🚀 Quick Popup Fix Script
// Run this in browser console to fix popup issues immediately

console.log('🚀 Quick Popup Fix Script');

// Function to fix popup immediately
function quickFixPopup() {
    console.log('🔧 Attempting quick popup fix...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        return;
    }

    // Force close popup first
    vm.product_search_popup_visible = false;

    // Check props
    console.log('📋 Checking props...');
    console.log('pos_profile:', vm.pos_profile);
    console.log('active_price_list:', vm.active_price_list);
    console.log('customer:', vm.customer);

    // Wait a bit then reopen
    setTimeout(() => {
        console.log('📂 Reopening popup with proper props...');
        vm.product_search_popup_visible = true;

        // Force Vue to update
        vm.$forceUpdate();

        console.log('✅ Popup reopened');

        // Test search after popup opens
        setTimeout(() => {
            testPopupSearch();
        }, 1000);

    }, 500);
}

// Function to test popup search
function testPopupSearch() {
    console.log('🧪 Testing popup search...');

    // Try to find popup component
    const vm = window.$vm0;
    const popupComponent = vm.$children?.find(child =>
        child.$options.name === 'ProductSearchPopup'
    );

    if (!popupComponent) {
        console.error('❌ Popup component not found');
        return;
    }

    console.log('✅ Popup component found');

    // Set test search term
    popupComponent.searchTerm = 'test';

    // Trigger search
    popupComponent.performSearch().then(() => {
        console.log('✅ Test search completed');
    }).catch(error => {
        console.error('❌ Test search failed:', error);
    });
}

// Function to manually test API
function testAPI() {
    console.log('🌐 Testing API directly...');

    const vm = window.$vm0;

    frappe.call({
        method: "posawesome.posawesome.api.items.search_items_for_popup",
        args: {
            search_term: "test",
            pos_profile: JSON.stringify(vm.pos_profile),
            price_list: vm.active_price_list,
            customer: vm.customer,
            limit: 5
        },
        callback: (r) => {
            console.log('✅ API test successful:', r);
            if (r.message) {
                console.log('📊 Returned', r.message.length, 'items');
                console.table(r.message.slice(0, 3));
            }
        },
        error: (err) => {
            console.error('❌ API test failed:', err);
        }
    });
}

// Function to check all popup requirements
function checkRequirements() {
    console.group('📋 Checking Popup Requirements');

    // Check frappe
    console.log('🔍 frappe available:', typeof frappe !== 'undefined');

    // Check $vm0
    console.log('🔍 $vm0 available:', typeof window.$vm0 !== 'undefined');

    if (window.$vm0) {
        const vm = window.$vm0;
        console.log('🔍 pos_profile:', !!vm.pos_profile);
        console.log('🔍 active_price_list:', !!vm.active_price_list);
        console.log('🔍 ProductSearchPopup component:', !!vm.$options.components.ProductSearchPopup);
    }

    console.groupEnd();
}

// Function to force reload popup component
function reloadPopupComponent() {
    console.log('🔄 Attempting to reload popup component...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        return;
    }

    // Close popup
    vm.product_search_popup_visible = false;

    // Force component re-render
    vm.$forceUpdate();

    // Reopen after delay
    setTimeout(() => {
        vm.product_search_popup_visible = true;
        vm.$forceUpdate();
        console.log('✅ Component reloaded');
    }, 1000);
}

// Export functions
window.quickFixPopup = quickFixPopup;
window.testPopupSearch = testPopupSearch;
window.testAPI = testAPI;
window.checkRequirements = checkRequirements;
window.reloadPopupComponent = reloadPopupComponent;

// Auto-run checks
checkRequirements();

console.log('✅ Quick fix functions available:');
console.log('   quickFixPopup() - Fix popup immediately');
console.log('   testAPI() - Test API directly');
console.log('   checkRequirements() - Check all requirements');
console.log('   reloadPopupComponent() - Reload component');
console.log('\n🚀 Run: quickFixPopup()');