#!/bin/bash

# Script to monitor invoice tracking logs in real-time
# Usage: ./monitor_invoice_logs.sh

echo "🔍 MONITORING INVOICE TRACKING LOGS"
echo "===================================="
echo "This script monitors logs for invoice processing through POS Shift Report system"
echo "Press Ctrl+C to stop monitoring"
echo ""
echo "📋 LOG PATTERNS BEING MONITORED:"
echo "   🔍 [INVOICE_TRACKING] - Invoice processing steps"
echo "   🔢 [SHIFT_REPORT_CALC] - Shift report calculations"
echo "   📊 UPDATE_CALCULATED_FIELDS - Field updates"
echo "   💳 GET_PAYMENT_BREAKDOWN - Payment processing"
echo "===================================="
echo ""

# Monitor frappe logs for invoice tracking patterns
tail -f /home/frappe/frappe-bench/logs/frappe.log | grep -E "(INVOICE_TRACKING|SHIFT_REPORT_CALC)" | while read line; do
    # Add timestamp for better tracking
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $line"
done