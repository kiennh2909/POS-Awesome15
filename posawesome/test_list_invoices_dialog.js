// Test script for ListInvoicesDialog API integration
// Run this in browser console when ListInvoicesDialog is open

console.log("🧪 Testing ListInvoicesDialog API Integration");

// Test 1: Check if component is properly bound
console.log("1️⃣ Testing component binding...");
const dialogElement = document.querySelector('.v-dialog');
if (dialogElement) {
    console.log("✅ Dialog element found");
} else {
    console.log("❌ Dialog element not found");
}

// Test 2: Check if shiftReportId is passed
console.log("2️⃣ Testing shiftReportId prop...");
if (window.posReportId) {
    console.log("✅ shiftReportId found:", window.posReportId);
} else {
    console.log("❌ shiftReportId not found");
}

// Test 3: Test API call manually
console.log("3️⃣ Testing API call...");
async function testApiCall() {
    try {
        const response = await frappe.call({
            method: "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.get_pos_invoices",
            args: {
                pos_opening_shift: window.posReportId || "POSA-OS-25-000001"
            }
        });

        console.log("✅ API Response:", response);

        if (response.message && Array.isArray(response.message)) {
            console.log(`✅ Found ${response.message.length} invoices`);
            response.message.forEach((invoice, index) => {
                console.log(`${index + 1}. ${invoice.name} - ${invoice.grand_total} - ${invoice.customer}`);
            });
        } else {
            console.log("❌ Invalid API response format");
        }
    } catch (error) {
        console.error("❌ API call failed:", error);
    }
}

testApiCall();

// Test 4: Check data mapping
console.log("4️⃣ Testing data mapping...");
function testDataMapping(apiInvoice) {
    const mappedInvoice = {
        invoice_no: apiInvoice.name,
        invoice_date: apiInvoice.posting_date,
        invoice_time: "00:00:00", // Will be formatted by formatTime()
        customer: apiInvoice.customer || "-",
        total_amount: apiInvoice.grand_total || 0,
        paid_amount: apiInvoice.paid_amount || 0,
        tax_amount: apiInvoice.total_taxes_and_charges || 0,
        payment_method: "Cash", // Will be determined by getPaymentMethod()
        is_return: apiInvoice.is_return || false,
        status: apiInvoice.docstatus === 1 ? "Submitted" : "Draft"
    };

    console.log("✅ Mapped invoice:", mappedInvoice);
    return mappedInvoice;
}

// Instructions for manual testing
console.log("\n📋 MANUAL TESTING INSTRUCTIONS:");
console.log("1. Open Shift Report Dialog");
console.log("2. Click 'View All' button");
console.log("3. Check browser console for API calls");
console.log("4. Verify data is loaded in table");
console.log("5. Test filters and export functionality");

console.log("\n🎯 EXPECTED BEHAVIOR:");
console.log("- API call to get_pos_invoices should be made");
console.log("- Real invoice data should be displayed");
console.log("- Summary cards should show correct totals");
console.log("- Export should work with real data");

console.log("\n🔍 DEBUGGING TIPS:");
console.log("- Check Network tab for API calls");
console.log("- Look for console errors");
console.log("- Verify shiftReportId is not null/undefined");
console.log("- Check if API returns expected data structure");

console.log("\n✨ Test completed! Check results above.");