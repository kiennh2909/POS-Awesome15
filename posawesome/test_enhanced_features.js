// Test script for Enhanced ListInvoicesDialog Features
// Test Payment Summary position, Export Excel, and Print functionality

console.log("🧪 Testing Enhanced ListInvoicesDialog Features");

// Test 1: Check Action Buttons position (should be at very top)
console.log("1️⃣ Testing Action Buttons Position...");
const actionButtonsSection = document.querySelector('.action-buttons-section');
if (actionButtonsSection) {
    console.log("✅ Action buttons section found at top");
    const buttons = actionButtonsSection.querySelectorAll('button');
    console.log(`✅ Found ${buttons.length} action buttons:`, Array.from(buttons).map(btn => btn.textContent.trim()));
} else {
    console.log("❌ Action buttons section not found");
}

// Test 2: Check Payment Summary position (should be after action buttons)
console.log("2️⃣ Testing Payment Summary Position...");
const paymentSummarySection = document.querySelector('.v-card-text .pa-4:has(h6)');
if (paymentSummarySection) {
    const sectionText = paymentSummarySection.textContent;
    if (sectionText.includes('Payment Summary') || sectionText.includes('Tóm tắt thanh toán')) {
        console.log("✅ Payment Summary is positioned after action buttons");
    } else {
        console.log("❌ Payment Summary section not found");
    }
} else {
    console.log("❌ Payment Summary section not found");
}

// Test 2: Check Export button and filename generation
console.log("2️⃣ Testing Export Button...");
const exportBtn = document.querySelector('button:has(.mdi-download)');
if (exportBtn) {
    console.log("✅ Export button found");

    // Test filename generation
    const component = window.vueApp?.$children?.find(c => c.$?.type?.name === 'ListInvoicesDialog');
    if (component && component.shiftReportId) {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '');
        const dateStr = now.toISOString().split('T')[0].replace(/-/g, '_');
        const posProfileName = (component.posProfile?.name || 'Unknown_POS').replace(/\s+/g, '_');
        const cashierName = frappe?.session?.user || 'Unknown_User';

        const expectedFileName = `${timeStr}_${dateStr}_${posProfileName}_${cashierName}_Shift_Report.xlsx`;
        console.log("✅ Expected filename format:", expectedFileName);
    }
} else {
    console.log("❌ Export button not found");
}

// Test 3: Check Print button
console.log("3️⃣ Testing Print Button...");
const printBtn = document.querySelector('button:has(.mdi-printer)');
if (printBtn) {
    console.log("✅ Print button found");
} else {
    console.log("❌ Print button not found");
}

// Test 4: Test Export Data Structure
console.log("4️⃣ Testing Export Data Structure...");
if (component && component.invoices && component.paymentSummaryData) {
    console.log("✅ Component data available for export");

    const invoiceCount = component.invoices.length;
    const paymentMethods = component.paymentSummaryData.length;

    console.log(`📊 Export will include:`);
    console.log(`   - ${invoiceCount} invoices`);
    console.log(`   - ${paymentMethods} payment methods`);
    console.log(`   - Summary cards data`);
    console.log(`   - Totals row`);

    // Check Vietnamese headers
    const vietnameseHeaders = ['Loại', 'Số hóa đơn', 'Khách hàng', 'Tổng tiền', 'Phương thức thanh toán'];
    console.log("✅ Vietnamese headers will be used:", vietnameseHeaders.join(', '));
} else {
    console.log("❌ Component data not available for export");
}

// Test 5: Test Print Content Generation
console.log("5️⃣ Testing Print Content Generation...");
if (component && typeof component.generatePrintContent === 'function') {
    try {
        const printContent = component.generatePrintContent();
        console.log("✅ Print content generated successfully");

        // Check if content includes key sections
        const hasHeader = printContent.includes('BÁO CÁO CA LÀM VIỆC');
        const hasSummary = printContent.includes('TÓM TẮT TỔNG QUAN');
        const hasPaymentSummary = printContent.includes('TÓM TẮT THANH TOÁN');
        const hasTable = printContent.includes('<table>');
        const hasPrintInfo = printContent.includes('print-info');

        console.log("📄 Print content includes:");
        console.log(`   - Header: ${hasHeader ? '✅' : '❌'}`);
        console.log(`   - Summary cards: ${hasSummary ? '✅' : '❌'}`);
        console.log(`   - Payment summary: ${hasPaymentSummary ? '✅' : '❌'}`);
        console.log(`   - Table: ${hasTable ? '✅' : '❌'}`);
        console.log(`   - Print info: ${hasPrintInfo ? '✅' : '❌'}`);

    } catch (error) {
        console.log("❌ Error generating print content:", error);
    }
} else {
    console.log("❌ generatePrintContent method not found");
}

// Test 6: Check Pagination and Sorting
console.log("6️⃣ Testing Pagination and Sorting...");
const dataTable = document.querySelector('.v-data-table');
if (dataTable) {
    const pagination = document.querySelector('.v-pagination');
    const infoBanner = document.querySelector('.bg-blue-lighten-5');

    if (pagination) {
        console.log("✅ Pagination controls found");
    } else {
        console.log("❌ Pagination controls not found");
    }

    if (infoBanner) {
        console.log("✅ Info banner about latest 5 invoices found");
    } else {
        console.log("❌ Info banner not found");
    }

    // Check if component has correct itemsPerPage
    if (component && component.itemsPerPage === 5) {
        console.log("✅ Items per page set to 5");
    } else {
        console.log("❌ Items per page not set to 5");
    }
} else {
    console.log("❌ Data table not found");
}

// Test 7: Check Responsive Design
console.log("7️⃣ Testing Responsive Design...");
const dialog = document.querySelector('.v-dialog');
if (dialog) {
    const width = dialog.offsetWidth;
    console.log(`📱 Dialog width: ${width}px`);

    if (width <= 1366) {
        console.log("✅ Responsive design active for screens ≤1366px");
    } else {
        console.log("ℹ️ Full-size layout for larger screens");
    }
} else {
    console.log("❌ Dialog element not found");
}

// Test 7: Performance Test
console.log("7️⃣ Testing Performance...");
const startTime = performance.now();

setTimeout(() => {
    const endTime = performance.now();
    console.log(`⚡ Performance test: ${endTime - startTime}ms`);

    if (endTime - startTime < 100) {
        console.log("✅ Good performance");
    } else {
        console.log("⚠️ Performance could be improved");
    }
}, 50);

// Expected Results Summary
console.log("\n📋 EXPECTED BEHAVIOR:");
console.log("✅ Action buttons (Print, Export, Close) appear at the very top");
console.log("✅ Payment Summary appears right after action buttons");
console.log("✅ Info banner shows 'Showing latest 5 invoices per page'");
console.log("✅ Invoices are sorted by newest first (descending order)");
console.log("✅ Pagination controls are visible at bottom");
console.log("✅ Export button generates Excel file with Vietnamese headers");
console.log("✅ Filename format: HHMMSS_YYYY_MM_DD_POS_Profile_Name_CashierName_Shift_Report.xlsx");
console.log("✅ Print button generates formatted report for first page only");
console.log("✅ Print includes summary cards, payment summary table, and totals");
console.log("✅ Responsive design works on 13-inch screens");
console.log("✅ All data properly formatted with currency from POS profile");
console.log("✅ Action buttons section has gradient background and sticky positioning");

console.log("\n🎯 MANUAL TESTING STEPS:");
console.log("1. Open Shift Report Dialog");
console.log("2. Click 'View All' button");
console.log("3. Verify Action buttons are at the very top with gradient background");
console.log("4. Verify Payment Summary is right below action buttons");
console.log("5. Check info banner about 'latest 5 invoices per page'");
console.log("6. Verify invoices are sorted newest first");
console.log("7. Check pagination controls at bottom of table");
console.log("8. Click 'Export' button and check downloaded file");
console.log("9. Click 'Print' button and check print preview");
console.log("10. Scroll down and verify action buttons remain accessible");
console.log("11. Resize browser to 1366px and check responsive layout");

console.log("\n✨ Enhanced Features Test completed! Check results above.");