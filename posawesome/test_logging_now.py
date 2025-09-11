#!/usr/bin/env python3
"""
Quick test to send log messages and check if they're written
"""

import os
import sys

# Setup environment
os.environ['FRAPPE_SITE'] = 'erp152-v1.vtcom.online'

# Add paths
sys.path.insert(0, '/home/frappe/frappe-bench')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/erpnext')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/posawesome')

# Initialize Frappe
import frappe
frappe.init(site='erp152-v1.vtcom.online')
frappe.connect()

def test_logging_immediately():
    """Test logging immediately"""

    print("🚀 TESTING LOGGING IMMEDIATELY")
    print("=" * 50)

    # Send test messages
    print("📤 Sending test log messages...")

    frappe.logger().info("[TEST_LOGGING] ℹ️ INFO: Test info message")
    frappe.logger().warning("[TEST_LOGGING] ⚠️ WARNING: Test warning message")
    frappe.logger().error("[TEST_LOGGING] ❌ ERROR: Test error message")
    frappe.logger().debug("[TEST_LOGGING] 🔍 DEBUG: Test debug message")

    # Force commit
    frappe.db.commit()

    print("✅ Messages sent!")

    # Check log file immediately
    log_file = '/home/frappe/frappe-bench/logs/frappe.log'

    print("
🔍 Checking log file..."    print(f"Log file: {log_file}")

    if os.path.exists(log_file):
        print("✅ Log file exists")

        # Read last 20 lines
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"📄 Log file has {len(lines)} lines")

                # Show last 10 lines
                print("\n📋 Last 10 lines:")
                for line in lines[-10:]:
                    if '[TEST_LOGGING]' in line:
                        print(f"   🎯 {line.strip()}")
                    else:
                        print(f"   {line.strip()}")

        except Exception as e:
            print(f"❌ Error reading log file: {e}")

    else:
        print("❌ Log file does not exist!")

    # Check site config
    site_config_file = '/home/frappe/frappe-bench/sites/erp152-v1.vtcom.online/site_config.json'
    print("
⚙️ Checking site config..."    print(f"Config file: {site_config_file}")

    if os.path.exists(site_config_file):
        try:
            import json
            with open(site_config_file, 'r') as f:
                config = json.load(f)

            log_level = config.get('log_level', 'INFO')
            print(f"✅ Current log_level: {log_level}")

            if log_level not in ['DEBUG', 'INFO']:
                print("⚠️  WARNING: log_level might be too high!")
                print("   Recommended: DEBUG or INFO")
                print("   Current: " + log_level)

        except Exception as e:
            print(f"❌ Error reading config: {e}")
    else:
        print("❌ Site config file not found!")

    print("
💡 TROUBLESHOOTING:"    print("1. If no logs appear, check log_level in site_config.json")
    print("2. Should be 'DEBUG' or 'INFO' to see info messages")
    print("3. Restart services after changing config:")
    print("   sudo supervisorctl restart frappe-bench-web:")
    print("   sudo supervisorctl restart frappe-bench-worker:")

if __name__ == "__main__":
    try:
        test_logging_immediately()
        frappe.destroy()
    except Exception as e:
        print(f"❌ Error: {e}")
        frappe.destroy()
        exit(1)