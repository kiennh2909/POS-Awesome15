#!/usr/bin/env python3
"""
Complete test suite for POS Shift Report System
Tests all aspects: creation, linking, calculations, and payment breakdown
"""

import os
import sys
import subprocess

# Setup environment
os.environ['FRAPPE_SITE'] = 'erp152-v1.vtcom.online'

def run_test_script(script_name, description):
    """Run a test script and return result"""
    print(f"\n{'='*60}")
    print(f"🧪 RUNNING: {description}")
    print('='*60)

    try:
        result = subprocess.run([
            sys.executable,
            f'posawesome/{script_name}'
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"✅ PASSED: {description}")
            print(result.stdout.split('\n')[-3])  # Last success message
            return True
        else:
            print(f"❌ FAILED: {description}")
            print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            print("STDERR:", result.stderr[-500:])  # Last 500 chars
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description}")
        return False
    except Exception as e:
        print(f"💥 ERROR running {description}: {e}")
        return False

def main():
    """Run complete test suite"""

    print("🚀 POS SHIFT REPORT SYSTEM - COMPLETE TEST SUITE")
    print("=" * 80)
    print("This test suite will verify:")
    print("1. ✅ Custom fields and database structure")
    print("2. ✅ Shift report creation from opening shift")
    print("3. ✅ Invoice to shift report linking")
    print("4. ✅ Calculated fields (invoice_count, total_sales, total_returns)")
    print("5. ✅ Payment breakdown calculations")
    print("=" * 80)

    test_results = []

    # Test 1: Verify custom fields
    test_results.append(run_test_script(
        'verify_shift_report_fields.py',
        'Custom Fields & Database Structure Verification'
    ))

    # Test 2: Shift report creation
    test_results.append(run_test_script(
        'test_shift_report_fix.py',
        'Shift Report Creation from Opening Shift'
    ))

    # Test 3: Invoice linking
    test_results.append(run_test_script(
        'test_invoice_shift_report_link.py',
        'Invoice to Shift Report Linking'
    ))

    # Test 4: Calculations
    test_results.append(run_test_script(
        'test_shift_report_calculations.py',
        'Calculated Fields (invoice_count, total_sales, total_returns)'
    ))

    # Test 5: Payment breakdown
    test_results.append(run_test_script(
        'test_payment_breakdown.py',
        'Payment Breakdown Calculations'
    ))

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUITE RESULTS SUMMARY")
    print("=" * 80)

    passed = sum(test_results)
    total = len(test_results)

    print(f"✅ Tests Passed: {passed}/{total}")
    print(f"❌ Tests Failed: {total - passed}/{total}")
    print(".1f")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ POS Shift Report System is working correctly!")
        print("\n📋 VERIFIED FUNCTIONALITY:")
        print("   • Shift reports are created automatically from opening shifts")
        print("   • Sales invoices are properly linked to shift reports")
        print("   • Calculated fields are updated correctly (invoice_count, total_sales, total_returns)")
        print("   • Payment breakdown is calculated accurately")
        print("   • System handles returns and cancellations properly")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️  Please check the failed tests above and fix any issues.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test suite interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test suite execution failed: {e}")
        exit(1)