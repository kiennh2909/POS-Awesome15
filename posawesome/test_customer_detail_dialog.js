// Test script for Customer Detail Dialog
// Run this in browser console to test the dialog behavior

console.log('=== Customer Detail Dialog Test ===');

// Test 1: Check if CustomerDetail component exists
const customerDetailComponent = document.querySelector('.customer-detail-dialog-card');
console.log('CustomerDetail component found:', !!customerDetailComponent);

// Test 2: Check if View Details button exists
const viewDetailsBtn = document.querySelector('.view-details-btn');
console.log('View Details button found:', !!viewDetailsBtn);

// Test 3: Simulate button click
if (viewDetailsBtn) {
    console.log('Clicking View Details button...');
    viewDetailsBtn.click();

    // Check if dialog opens after a short delay
    setTimeout(() => {
        const dialogAfterClick = document.querySelector('.customer-detail-dialog-card');
        console.log('Dialog opened after click:', !!dialogAfterClick);

        if (dialogAfterClick) {
            // Test 4: Try to close dialog
            const closeBtn = dialogAfterClick.querySelector('.close-btn');
            console.log('Close button found:', !!closeBtn);

            if (closeBtn) {
                console.log('Clicking close button...');
                closeBtn.click();

                // Check if dialog closes
                setTimeout(() => {
                    const dialogAfterClose = document.querySelector('.customer-detail-dialog-card');
                    console.log('Dialog closed after close button:', !dialogAfterClose);
                }, 500);
            }
        }
    }, 1000);
} else {
    console.log('❌ View Details button not found. Make sure a customer is selected.');
}

console.log('=== Test Complete ===');