#!/usr/bin/env python3
"""
Test script to verify import fix for payment summary functions
Run this in bench console: exec(open('posawesome/test_import_fix.py').read())
"""

import frappe

def test_import_and_call():
    """Test importing and calling payment summary functions"""

    print("🧪 TESTING IMPORT AND FUNCTION CALL")
    print("=" * 50)

    try:
        # Test 1: Direct import
        print("\n1️⃣ Testing direct import...")
        try:
            from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
            print("   ✅ Direct import successful")
        except ImportError as e:
            print(f"   ❌ Direct import failed: {str(e)}")
            return

        # Test 2: Check if function exists
        print("\n2️⃣ Testing function existence...")
        import posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary as ps_module
        functions = [name for name in dir(ps_module) if not name.startswith('_')]
        print(f"   Available functions: {functions}")

        if 'create_payment_summaries_for_shift' in functions:
            print("   ✅ Function exists in module")
        else:
            print("   ❌ Function not found in module")
            return

        # Test 3: Get sample shift report
        print("\n3️⃣ Getting sample shift report...")
        sample_reports = frappe.get_all("POS Shift Report",
            fields=["name", "shift_report_id"],
            limit=1
        )

        if not sample_reports:
            print("   ❌ No shift reports found")
            return

        sample_report = sample_reports[0]
        print(f"   Sample report: {sample_report}")

        # Test 4: Call function
        print("\n4️⃣ Testing function call...")
        try:
            result = create_payment_summaries_for_shift(sample_report.name)
            print("   ✅ Function call successful")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   ❌ Function call failed: {str(e)}")
            import traceback
            traceback.print_exc()

        # Test 5: Test API call
        print("\n5️⃣ Testing API call...")
        try:
            api_result = frappe.call({
                "method": "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
                "args": {
                    "shift_report_id": sample_report.name
                }
            })
            print("   ✅ API call successful")
            print(f"   Has payment_summaries: {'payment_summaries' in api_result}")
        except Exception as e:
            print(f"   ❌ API call failed: {str(e)}")

    except Exception as e:
        print(f"💥 TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

def test_module_reload():
    """Test module reload to ensure changes are picked up"""

    print("\n🔄 TESTING MODULE RELOAD")
    print("=" * 30)

    try:
        # Clear module cache
        import sys
        modules_to_clear = [
            'posawesome.posawesome.doctype.pos_payment_summary',
            'posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary'
        ]

        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
                print(f"   Cleared module cache: {module}")

        # Try import again
        print("\n   Retrying import after cache clear...")
        from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
        print("   ✅ Import successful after cache clear")

    except Exception as e:
        print(f"   ❌ Import still failed: {str(e)}")

# Main execution
if __name__ == "__main__":
    test_import_and_call()
    test_module_reload()

    print("\n" + "=" * 50)
    print("🎯 IMPORT TEST COMPLETE")
    print("If all tests pass, the import issue is resolved!")