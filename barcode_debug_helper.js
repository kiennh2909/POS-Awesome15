// Barcode Debug Helper
// Run this in browser console on POS page to debug barcode issues

console.log('🔍 Barcode Debug Helper Loaded');

// Helper function to find ItemsSelector component
function findItemsSelector() {
    // Try to find the component instance
    const app = document.querySelector('#app').__vue_app__;
    if (app) {
        const instances = app._instance.scope.effects;
        for (let effect of instances) {
            if (effect.fn && effect.fn.ctx && effect.fn.ctx.$options && effect.fn.ctx.$options.name === 'ItemsSelector') {
                return effect.fn.ctx;
            }
        }
    }

    // Fallback: try global $vm0
    if (window.$vm0 && window.$vm0.testBarcodeSearch) {
        return window.$vm0;
    }

    return null;
}

// Main debug function
async function debugBarcode(barcode = '8991818801601') {
    console.group(`🔍 Debugging Barcode: ${barcode}`);

    const itemsSelector = findItemsSelector();
    if (!itemsSelector) {
        console.error('❌ Could not find ItemsSelector component');
        console.log('💡 Try: Open POS interface and run this again');
        console.groupEnd();
        return;
    }

    console.log('✅ Found ItemsSelector component');

    // Test 1: Basic validation
    console.log('\n1️⃣ Testing barcode validation...');
    const looksLike = itemsSelector.looksLikeBarcode(barcode);
    const isValid = itemsSelector.isValidBarcode(barcode);
    console.log(`   looksLikeBarcode: ${looksLike}`);
    console.log(`   isValidBarcode: ${isValid}`);

    // Test 2: Items loaded
    console.log('\n2️⃣ Checking items data...');
    console.log(`   Total items loaded: ${itemsSelector.items?.length || 0}`);
    const itemsWithBarcodes = itemsSelector.items?.filter(item =>
        item.item_barcode && item.item_barcode.length > 0
    ) || [];
    console.log(`   Items with barcodes: ${itemsWithBarcodes.length}`);

    // Test 3: Local search
    console.log('\n3️⃣ Testing local search...');
    const localMatch = itemsSelector.items?.find(item =>
        item.item_barcode && item.item_barcode.some(bc => bc.barcode === barcode)
    );
    console.log(`   Local exact match: ${localMatch ? localMatch.item_code : 'Not found'}`);

    // Test 4: API search
    console.log('\n4️⃣ Testing API search...');
    try {
        const apiResult = await itemsSelector.getItemByBarcodeExact(barcode);
        console.log(`   API result: ${apiResult ? apiResult.item_code : 'Not found'}`);
        if (apiResult) {
            console.log(`   Item name: ${apiResult.item_name}`);
            console.log(`   UOM: ${apiResult.uom}`);
            console.log(`   Rate: ${apiResult.rate}`);
        }
    } catch (error) {
        console.error(`   API error: ${error.message}`);
    }

    // Test 5: Full barcode processing
    console.log('\n5️⃣ Testing full barcode processing...');
    try {
        const result = await itemsSelector.findItemByBarcode(barcode);
        console.log(`   findItemByBarcode result: ${result ? result.item_code : 'Not found'}`);
    } catch (error) {
        console.error(`   findItemByBarcode error: ${error.message}`);
    }

    console.groupEnd();

    return {
        looksLike,
        isValid,
        totalItems: itemsSelector.items?.length || 0,
        itemsWithBarcodes: itemsWithBarcodes.length,
        localMatch: localMatch?.item_code || null,
        component: itemsSelector
    };
}

// Test specific barcode
async function testBarcode8991818801601() {
    return await debugBarcode('8991818801601');
}

// Test the testBarcodeSearch method if available
function testBarcodeSearchMethod(barcode = '8991818801601') {
    const itemsSelector = findItemsSelector();
    if (itemsSelector && itemsSelector.testBarcodeSearch) {
        console.log('🔍 Running testBarcodeSearch method...');
        return itemsSelector.testBarcodeSearch(barcode);
    } else {
        console.error('❌ testBarcodeSearch method not found');
        return null;
    }
}

// Export functions to global scope
window.debugBarcode = debugBarcode;
window.testBarcode8991818801601 = testBarcode8991818801601;
window.testBarcodeSearchMethod = testBarcodeSearchMethod;

console.log('✅ Debug functions available:');
console.log('   debugBarcode(barcode) - Full debug test');
console.log('   testBarcode8991818801601() - Test specific barcode');
console.log('   testBarcodeSearchMethod(barcode) - Test component method');
console.log('\n💡 Usage: debugBarcode("8991818801601")');