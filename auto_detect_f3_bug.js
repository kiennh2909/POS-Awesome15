// 🤖 Auto Detect F3 Bug Script
// This script automatically detects and fixes F3 freeze issues

console.log('🤖 Auto Detect F3 Bug Script');

// Function to detect potential F3 bug
function detectF3Bug() {
    console.group('🔍 Detecting F3 Bug...');

    const vm = window.$vm0;
    if (!vm) {
        console.error('❌ $vm0 not found');
        console.groupEnd();
        return { hasBug: false, reason: 'No $vm0' };
    }

    const issues = [];

    // Check 1: F3 enabled but popup component problematic
    if (vm.f3_enabled) {
        const popupComponent = vm.$options.components.ProductSearchPopup;
        if (popupComponent) {
            // Try to detect computed property issues
            try {
                const componentDef = popupComponent.options || popupComponent;
                if (componentDef.computed && componentDef.computed.isVisible) {
                    const isVisibleComputed = componentDef.computed.isVisible;
                    if (typeof isVisibleComputed === 'object' && isVisibleComputed.set) {
                        issues.push('Computed isVisible has setter - potential infinite loop');
                    }
                }
            } catch (e) {
                issues.push('Error analyzing component: ' + e.message);
            }
        }
    }

    // Check 2: Popup state inconsistency
    if (vm.product_search_popup_visible === true) {
        issues.push('Popup is currently visible - might be stuck');
    }

    // Check 3: Console errors related to popup
    const hasConsoleErrors = window.console._errors &&
        window.console._errors.some(err =>
            err.includes('ProductSearchPopup') ||
            err.includes('isVisible') ||
            err.includes('infinite')
        );

    if (hasConsoleErrors) {
        issues.push('Console errors detected related to popup');
    }

    console.log('🔍 Issues found:', issues);
    console.groupEnd();

    return {
        hasBug: issues.length > 0,
        issues: issues,
        severity: issues.length > 2 ? 'critical' : issues.length > 0 ? 'warning' : 'ok'
    };
}

// Function to auto-fix detected issues
function autoFixF3Bug() {
    console.group('🔧 Auto-fixing F3 Bug...');

    const detection = detectF3Bug();

    if (!detection.hasBug) {
        console.log('✅ No F3 bug detected');
        console.groupEnd();
        return { fixed: false, reason: 'No bug detected' };
    }

    const vm = window.$vm0;
    const fixes = [];

    // Fix 1: Disable F3 if critical issues
    if (detection.severity === 'critical') {
        vm.f3_enabled = false;
        fixes.push('Disabled F3 due to critical issues');
    }

    // Fix 2: Force close stuck popup
    if (vm.product_search_popup_visible) {
        vm.product_search_popup_visible = false;
        fixes.push('Closed stuck popup');
    }

    // Fix 3: Replace F3 handler with safe version
    const originalHandler = vm.handleF3SearchToggle;
    vm.handleF3SearchToggle = function () {
        console.warn('[SAFE F3] Using safe F3 handler due to bug detection');

        // Simple alert instead of popup
        const searchTerm = prompt('Tìm kiếm sản phẩm (F3 an toàn):');
        if (!searchTerm) return;

        frappe.show_alert({
            message: 'Đang tìm kiếm...',
            indicator: 'blue'
        }, 2);

        // Direct API call without popup
        frappe.call({
            method: "posawesome.posawesome.api.items.search_items_for_popup",
            args: {
                search_term: searchTerm,
                pos_profile: JSON.stringify(vm.pos_profile || {}),
                price_list: vm.active_price_list || 'Standard Selling',
                customer: vm.customer,
                limit: 5
            },
            callback: (r) => {
                if (r.message && r.message.length > 0) {
                    console.table(r.message);
                    const itemList = r.message.map((item, i) =>
                        `${i + 1}. ${item.item_name} (${item.item_code})`
                    ).join('\n');

                    const choice = prompt(`Chọn sản phẩm:\n${itemList}\n\nNhập số:`);
                    const index = parseInt(choice) - 1;

                    if (index >= 0 && index < r.message.length) {
                        vm.add_item(r.message[index]);
                        frappe.show_alert({
                            message: `Đã thêm: ${r.message[index].item_name}`,
                            indicator: 'green'
                        }, 3);
                    }
                } else {
                    frappe.show_alert({
                        message: 'Không tìm thấy sản phẩm',
                        indicator: 'orange'
                    }, 3);
                }
            },
            error: (err) => {
                frappe.show_alert({
                    message: 'Lỗi tìm kiếm',
                    indicator: 'red'
                }, 3);
            }
        });
    };

    fixes.push('Replaced F3 handler with safe version');

    // Fix 4: Force component update
    vm.$forceUpdate();
    fixes.push('Forced component update');

    console.log('🔧 Fixes applied:', fixes);
    console.groupEnd();

    return {
        fixed: true,
        fixes: fixes,
        originalHandler: originalHandler
    };
}

// Function to monitor F3 usage and auto-fix if needed
function monitorF3Usage() {
    console.log('👁️ Starting F3 monitoring...');

    const vm = window.$vm0;
    if (!vm) return;

    // Override F3 handler with monitoring
    const originalHandler = vm.handleF3SearchToggle;

    vm.handleF3SearchToggle = function () {
        console.log('🔍 F3 pressed - checking for issues...');

        // Quick bug detection
        const detection = detectF3Bug();

        if (detection.hasBug && detection.severity === 'critical') {
            console.warn('🚨 Critical F3 bug detected - auto-fixing...');
            autoFixF3Bug();
            return;
        }

        // Try original handler with timeout protection
        const timeoutId = setTimeout(() => {
            console.error('🚨 F3 handler timeout - applying emergency fix');
            autoFixF3Bug();
        }, 3000); // 3 second timeout

        try {
            originalHandler.call(this);
            clearTimeout(timeoutId);
        } catch (error) {
            clearTimeout(timeoutId);
            console.error('🚨 F3 handler error:', error);
            autoFixF3Bug();
        }
    };

    console.log('✅ F3 monitoring active');
}

// Function to restore original F3 functionality
function restoreOriginalF3() {
    console.log('🔄 Restoring original F3...');

    const vm = window.$vm0;
    if (!vm) return;

    // Re-enable F3
    vm.f3_enabled = true;

    // Restore original handler
    vm.handleF3SearchToggle = function () {
        console.info('[F3] Opening Product Search Popup');
        vm.hideSearchResults();
        vm.hideProductConfirmation();
        vm.openProductSearchPopup();
        frappe.show_alert({
            message: 'F3: Mở popup tìm kiếm sản phẩm',
            indicator: 'orange'
        }, 2);
    };

    console.log('⚠️ Original F3 restored - monitor for issues');
}

// Auto-run detection on load
const initialDetection = detectF3Bug();
if (initialDetection.hasBug) {
    console.warn('🚨 F3 bug detected on load:', initialDetection.issues);

    if (initialDetection.severity === 'critical') {
        console.log('🔧 Auto-applying fix...');
        autoFixF3Bug();
    }
}

// Export functions
window.detectF3Bug = detectF3Bug;
window.autoFixF3Bug = autoFixF3Bug;
window.monitorF3Usage = monitorF3Usage;
window.restoreOriginalF3 = restoreOriginalF3;

console.log('🤖 Auto F3 Bug Detection Functions:');
console.log('   detectF3Bug() - Detect potential F3 issues');
console.log('   autoFixF3Bug() - Auto-fix detected issues');
console.log('   monitorF3Usage() - Monitor F3 and auto-fix if needed');
console.log('   restoreOriginalF3() - Restore original F3 (risky)');
console.log('');

if (initialDetection.hasBug) {
    console.log('🚨 RECOMMENDATION: Run autoFixF3Bug() or monitorF3Usage()');
} else {
    console.log('✅ No F3 issues detected - system appears healthy');
}