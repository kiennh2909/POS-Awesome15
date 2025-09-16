#!/usr/bin/env python3
"""
Test script for pagination API endpoint
"""

import frappe
from posawesome.posawesome.api.shifts import get_shift_report_invoices

def test_pagination_api():
    """Test the pagination API endpoint"""
    print("🧪 Testing pagination API...")

    try:
        # Test with mock shift report ID
        result = get_shift_report_invoices(
            shift_report_id="SHIFT-001",
            page=1,
            page_size=5
        )

        print("✅ API Response:", result)

        if result.get("success"):
            print(f"📊 Total items: {result.get('total_count', 0)}")
            print(f"📄 Total pages: {result.get('total_pages', 0)}")
            print(f"📋 Invoices returned: {len(result.get('invoices', []))}")
        else:
            print("❌ API returned error:", result.get("message"))

    except Exception as e:
        print("💥 API Test Failed:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pagination_api()