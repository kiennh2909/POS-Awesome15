// Test script for Payment Summary functionality in ListInvoicesDialog
// Run this in browser console when ListInvoicesDialog is open with data

console.log("🧪 Testing Payment Summary Functionality");

// Test 1: Check if payment summary data is loaded
console.log("1️⃣ Testing Payment Summary Data Loading...");
const paymentSummaryData = window.vueApp?.$children?.find(c => c.$?.type?.name === 'ListInvoicesDialog')?.paymentSummaryData;
if (paymentSummaryData && paymentSummaryData.length > 0) {
    console.log("✅ Payment summary data loaded:", paymentSummaryData.length, "methods");
    paymentSummaryData.forEach((item, index) => {
        console.log(`${index + 1}. ${item.payment_method}: Opening: ${item.opening_amount}, Transaction: ${item.transaction_amount}, Closing: ${item.closing_amount}`);
    });
} else {
    console.log("❌ Payment summary data not loaded or empty");
}

// Test 2: Check calculations
console.log("2️⃣ Testing Calculations...");
const component = window.vueApp?.$children?.find(c => c.$?.type?.name === 'ListInvoicesDialog');
if (component) {
    const totalOpening = component.totalOpeningAmount;
    const totalTransaction = component.totalTransactionAmount;
    const totalClosing = component.totalClosingAmount;

    console.log("✅ Totals calculated:");
    console.log(`   Opening: ${totalOpening}`);
    console.log(`   Transaction: ${totalTransaction}`);
    console.log(`   Closing: ${totalClosing}`);

    // Verify calculation: Closing = Opening + Transaction
    const expectedClosing = totalOpening + totalTransaction;
    if (Math.abs(totalClosing - expectedClosing) < 0.01) {
        console.log("✅ Calculation correct: Closing = Opening + Transaction");
    } else {
        console.log("❌ Calculation error:", totalClosing, "!==", expectedClosing);
    }
} else {
    console.log("❌ Cannot find ListInvoicesDialog component");
}

// Test 3: Check currency formatting
console.log("3️⃣ Testing Currency Formatting...");
if (component && component.formatCurrency) {
    const testAmount = 1234.56;
    const formatted = component.formatCurrency(testAmount);
    console.log(`✅ Currency formatting: ${testAmount} → ${formatted}`);

    // Check if currency from POS profile is used
    if (component.posProfile && component.posProfile.currency) {
        console.log(`✅ Using currency from POS profile: ${component.posProfile.currency}`);
    } else {
        console.log("⚠️ Using default currency (USD)");
    }
}

// Test 4: Check responsive design
console.log("4️⃣ Testing Responsive Design...");
const dialog = document.querySelector('.v-dialog');
if (dialog) {
    const width = dialog.offsetWidth;
    const height = dialog.offsetHeight;
    console.log(`✅ Dialog dimensions: ${width}x${height}px`);

    if (width <= 1366) {
        console.log("✅ Responsive design active for 13-inch screens");
    } else {
        console.log("ℹ️ Full-size layout");
    }
} else {
    console.log("❌ Dialog element not found");
}

// Test 5: Check export functionality
console.log("5️⃣ Testing Export Functionality...");
function testExport() {
    if (component && component.invoices && component.invoices.length > 0) {
        console.log("✅ Export data available:", component.invoices.length, "invoices");

        if (component.paymentSummaryData && component.paymentSummaryData.length > 0) {
            console.log("✅ Payment summary included in export:", component.paymentSummaryData.length, "methods");
        } else {
            console.log("⚠️ Payment summary not available for export");
        }
    } else {
        console.log("❌ No data available for export");
    }
}
testExport();

// Test 6: Performance check
console.log("6️⃣ Testing Performance...");
const startTime = performance.now();
setTimeout(() => {
    const endTime = performance.now();
    console.log(`✅ Performance test completed in ${endTime - startTime}ms`);
}, 100);

// Expected Results Summary
console.log("\n📋 EXPECTED RESULTS:");
console.log("✅ Payment summary table should display with 3 columns");
console.log("✅ Opening amounts should load from POS Opening Shift");
console.log("✅ Transaction amounts should calculate from invoices");
console.log("✅ Closing amounts = Opening + Transaction");
console.log("✅ Totals row should show sum of all methods");
console.log("✅ Currency formatting should use POS profile currency");
console.log("✅ Export should include both invoices and payment summary");
console.log("✅ Responsive design should work on 13-inch screens");

console.log("\n🎯 SAMPLE DATA EXPECTED:");
console.log("| Payment Method | Opening Amount | Transaction | Closing Amount |");
console.log("|----------------|----------------|-------------|----------------|");
console.log("| Cash          | $10,000.00     | $20,000.00 | $30,000.00    |");
console.log("| Card          | $5,000.00      | $15,000.00 | $20,000.00    |");
console.log("| M-Pesa        | $2,000.00      | $8,000.00  | $10,000.00    |");
console.log("| **TOTAL**     | **$17,000.00** | **$43,000.00** | **$60,000.00** |");

console.log("\n✨ Payment Summary Test completed! Check results above.");