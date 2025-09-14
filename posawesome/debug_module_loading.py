#!/usr/bin/env python3
"""
Debug script to identify module loading issues
Run this in bench console: exec(open('posawesome/debug_module_loading.py').read())
"""

import sys
import importlib

def debug_module_loading():
    """Debug module loading and function availability"""

    print("🔍 DEBUGGING MODULE LOADING")
    print("=" * 50)

    module_path = "posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary"

    try:
        # Clear module cache first
        print("\n1️⃣ Clearing module cache...")
        if module_path in sys.modules:
            del sys.modules[module_path]
            print(f"   ✅ Cleared cache for: {module_path}")

        # Try to import the module
        print("\n2️⃣ Importing module...")
        ps_module = importlib.import_module(module_path)
        print("   ✅ Module imported successfully")

        # Check what's available in the module
        print("\n3️⃣ Checking module contents...")
        all_items = dir(ps_module)
        print(f"   Total items in module: {len(all_items)}")

        # Separate functions and classes
        functions = []
        classes = []
        others = []

        for item in all_items:
            if not item.startswith('_'):
                obj = getattr(ps_module, item)
                if callable(obj):
                    if hasattr(obj, '__doc__') and obj.__doc__ and 'class' in obj.__doc__.lower():
                        classes.append(item)
                    else:
                        functions.append(item)
                else:
                    others.append(item)

        print(f"   Functions: {functions}")
        print(f"   Classes: {classes}")
        print(f"   Others: {others}")

        # Check if our function exists
        print("\n4️⃣ Checking specific function...")
        if hasattr(ps_module, 'create_payment_summaries_for_shift'):
            func = getattr(ps_module, 'create_payment_summaries_for_shift')
            print("   ✅ Function exists")
            print(f"   Function type: {type(func)}")
            print(f"   Function doc: {func.__doc__[:100] if func.__doc__ else 'No doc'}")
        else:
            print("   ❌ Function does not exist")

        # Try direct import
        print("\n5️⃣ Testing direct import...")
        try:
            from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
            print("   ✅ Direct import successful")
        except ImportError as e:
            print(f"   ❌ Direct import failed: {str(e)}")
        except Exception as e:
            print(f"   ⚠️ Direct import error: {str(e)}")

        # Check file path
        print("\n6️⃣ Checking file path...")
        file_path = ps_module.__file__
        print(f"   Module file: {file_path}")

        # Check if file exists and is readable
        import os
        if os.path.exists(file_path):
            print("   ✅ File exists")
            file_size = os.path.getsize(file_path)
            print(f"   File size: {file_size} bytes")

            # Try to read first few lines
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = []
                    for i, line in enumerate(f):
                        if i < 10:
                            first_lines.append(f"{i+1:2d}: {line.rstrip()}")
                        else:
                            break
                print("   First 10 lines:")
                for line in first_lines:
                    print(f"     {line}")
            except Exception as e:
                print(f"   ❌ Cannot read file: {str(e)}")
        else:
            print("   ❌ File does not exist")

    except Exception as e:
        print(f"💥 DEBUG FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

def test_syntax_check():
    """Check if the file has syntax errors"""

    print("\n🔍 CHECKING SYNTAX")
    print("=" * 30)

    file_path = "/home/frappe/frappe-bench/apps/posawesome/posawesome/posawesome/doctype/pos_payment_summary/pos_payment_summary.py"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("✅ File read successfully")
        print(f"Content length: {len(content)} characters")

        # Try to compile the code
        compile(content, file_path, 'exec')
        print("✅ Syntax check passed")

    except SyntaxError as e:
        print(f"❌ Syntax error: {str(e)}")
        print(f"Line {e.lineno}: {e.text}")
    except Exception as e:
        print(f"❌ Error reading/compiling file: {str(e)}")

def test_function_execution():
    """Test if we can execute the function directly"""

    print("\n🚀 TESTING FUNCTION EXECUTION")
    print("=" * 35)

    try:
        # Import and test
        import posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary as ps

        if hasattr(ps, 'create_payment_summaries_for_shift'):
            func = ps.create_payment_summaries_for_shift
            print("✅ Function found in module")

            # Get sample shift report
            import frappe
            sample_reports = frappe.get_all("POS Shift Report",
                fields=["name"],
                limit=1
            )

            if sample_reports:
                sample_name = sample_reports[0].name
                print(f"Testing with shift report: {sample_name}")

                # Try to call the function
                result = func(sample_name)
                print("✅ Function executed successfully")
                print(f"Result: {result}")
            else:
                print("❌ No sample shift reports found")
        else:
            print("❌ Function not found in module")

    except Exception as e:
        print(f"❌ Function execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

# Main execution
if __name__ == "__main__":
    debug_module_loading()
    test_syntax_check()
    test_function_execution()

    print("\n" + "=" * 50)
    print("🎯 MODULE LOADING DEBUG COMPLETE")
    print("Check the output above to identify the issue!")