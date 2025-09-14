#!/usr/bin/env python3
"""
Debug script to test if hooks are working
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    # Test import
    print("🔍 Testing import...")
    from posawesome.posawesome.api.invoice import on_submit, on_cancel
    print("✅ Import successful")

    # Test function existence
    print("🔍 Testing function existence...")
    assert callable(on_submit), "on_submit is not callable"
    assert callable(on_cancel), "on_cancel is not callable"
    print("✅ Functions are callable")

    # Test hooks.py
    print("🔍 Testing hooks.py...")
    from posawesome.posawesome import hooks
    assert hasattr(hooks, 'doc_events'), "hooks.py missing doc_events"
    assert 'Sales Invoice' in hooks.doc_events, "Sales Invoice not in doc_events"
    assert 'on_submit' in hooks.doc_events['Sales Invoice'], "on_submit not in Sales Invoice hooks"
    print("✅ hooks.py configuration correct")

    print("🎉 All tests passed! Hooks should work.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()