// 🚨 EMERGENCY F3 FIX SCRIPT
// Run this in browser console to fix F3 freeze issue immediately

console.log('🚨 EMERGENCY F3 FIX SCRIPT');

// Function to disable F3 immediately
function disableF3Emergency() {
    console.log('🛑 DISABLING F3 EMERGENCY...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        return;
    }

    // Force disable F3
    vm.f3_enabled = false;

    // Force close any open popup
    vm.product_search_popup_visible = false;

    // Override F3 handler temporarily
    vm.handleF3SearchToggle = function () {
        console.warn('F3 temporarily disabled due to freeze issue');
        frappe.show_alert({
            message: 'F3 tạm thời bị vô hiệu hóa do lỗi',
            indicator: 'red'
        }, 3);
    };

    // Force update
    vm.$forceUpdate();

    console.log('✅ F3 disabled successfully');
    console.log('💡 You can now use the POS normally');
    console.log('💡 Run enableF3Emergency() to re-enable F3');
}

// Function to enable F3 with safe handler
function enableF3Emergency() {
    console.log('🔄 ENABLING F3 WITH SAFE HANDLER...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        return;
    }

    // Re-enable F3
    vm.f3_enabled = true;

    // Safe F3 handler that won't freeze
    vm.handleF3SearchToggle = function () {
        console.log('[SAFE F3] Opening simple search dialog...');

        // Simple prompt-based search as fallback
        const searchTerm = prompt('Nhập từ khóa tìm kiếm sản phẩm:');
        if (!searchTerm) return;

        // Show loading
        frappe.show_alert({
            message: 'Đang tìm kiếm...',
            indicator: 'blue'
        }, 2);

        // Simple API call
        frappe.call({
            method: "posawesome.posawesome.api.items.search_items_for_popup",
            args: {
                search_term: searchTerm,
                pos_profile: JSON.stringify(vm.pos_profile || {}),
                price_list: vm.active_price_list || 'Standard Selling',
                customer: vm.customer,
                limit: 10
            },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    // Show results in console for now
                    console.table(r.message);
                    frappe.show_alert({
                        message: `Tìm thấy ${r.message.length} sản phẩm. Xem console để chọn.`,
                        indicator: 'green'
                    }, 5);

                    // Simple selection
                    const itemNames = r.message.map((item, index) =>
                        `${index + 1}. ${item.item_name} (${item.item_code})`
                    ).join('\n');

                    const selection = prompt(`Chọn sản phẩm (nhập số):\n${itemNames}`);
                    const selectedIndex = parseInt(selection) - 1;

                    if (selectedIndex >= 0 && selectedIndex < r.message.length) {
                        const selectedItem = r.message[selectedIndex];
                        vm.add_item(selectedItem).then(() => {
                            frappe.show_alert({
                                message: `Đã thêm: ${selectedItem.item_name}`,
                                indicator: 'green'
                            }, 3);
                        });
                    }
                } else {
                    frappe.show_alert({
                        message: 'Không tìm thấy sản phẩm',
                        indicator: 'orange'
                    }, 3);
                }
            },
            error: (err) => {
                console.error('Search error:', err);
                frappe.show_alert({
                    message: 'Lỗi tìm kiếm sản phẩm',
                    indicator: 'red'
                }, 3);
            }
        });
    };

    console.log('✅ F3 enabled with safe handler');
    console.log('💡 F3 now uses simple prompt-based search');
}

// Function to check current status
function checkF3Status() {
    console.group('📊 F3 Status Check');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        console.groupEnd();
        return;
    }

    console.log('🔍 F3 enabled:', vm.f3_enabled);
    console.log('🔍 Popup visible:', vm.product_search_popup_visible);
    console.log('🔍 F3 handler type:', typeof vm.handleF3SearchToggle);

    // Check if popup component exists
    const hasPopupComponent = !!vm.$options.components.ProductSearchPopup;
    console.log('🔍 Popup component exists:', hasPopupComponent);

    console.groupEnd();
}

// Function to force refresh page if needed
function forceRefresh() {
    console.log('🔄 FORCE REFRESHING PAGE...');

    if (confirm('Bạn có chắc muốn refresh trang? Dữ liệu chưa lưu sẽ bị mất.')) {
        window.location.reload();
    }
}

// Function to restore original F3 handler
function restoreOriginalF3() {
    console.log('🔄 RESTORING ORIGINAL F3 HANDLER...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        return;
    }

    // Re-enable F3
    vm.f3_enabled = true;

    // Restore original handler (this might cause freeze again)
    vm.handleF3SearchToggle = function () {
        console.info('[F3] Opening Product Search Popup');

        // Hide any inline search results and popups
        vm.hideSearchResults();
        vm.hideProductConfirmation();

        // Open the product search popup
        vm.openProductSearchPopup();

        // Show feedback
        frappe.show_alert({
            message: 'F3: Mở popup tìm kiếm sản phẩm',
            indicator: 'orange'
        }, 2);
    };

    console.log('⚠️ Original F3 handler restored');
    console.log('⚠️ WARNING: This might cause freeze again');
}

// Export functions to global scope
window.disableF3Emergency = disableF3Emergency;
window.enableF3Emergency = enableF3Emergency;
window.checkF3Status = checkF3Status;
window.forceRefresh = forceRefresh;
window.restoreOriginalF3 = restoreOriginalF3;

// Auto-run status check
checkF3Status();

console.log('🚨 EMERGENCY F3 FIX FUNCTIONS AVAILABLE:');
console.log('   disableF3Emergency() - Disable F3 immediately');
console.log('   enableF3Emergency() - Enable F3 with safe handler');
console.log('   checkF3Status() - Check current F3 status');
console.log('   forceRefresh() - Force refresh page');
console.log('   restoreOriginalF3() - Restore original handler (risky)');
console.log('');
console.log('🛑 IF F3 IS CAUSING FREEZE:');
console.log('   1. Run: disableF3Emergency()');
console.log('   2. Continue using POS normally');
console.log('   3. Run: enableF3Emergency() for safe F3');
console.log('');
console.log('💡 RECOMMENDED: disableF3Emergency()');