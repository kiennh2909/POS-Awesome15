#!/usr/bin/env python3
"""
Script to check and configure Frappe logging settings
"""

import os
import sys
import json

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

def check_log_configuration():
    """Check current logging configuration"""

    print("🔍 CHECKING FRAPPE LOG CONFIGURATION")
    print("=" * 60)

    # Check site config
    site_config_path = '/home/frappe/frappe-bench/sites/erp152-v1.vtcom.online/site_config.json'

    try:
        with open(site_config_path, 'r') as f:
            site_config = json.load(f)

        print("📄 Site Configuration:")
        print(f"   File: {site_config_path}")

        # Check log level
        log_level = site_config.get('log_level', 'INFO')
        print(f"   log_level: {log_level}")

        # Check other logging settings
        logging_settings = {k: v for k, v in site_config.items() if 'log' in k.lower()}
        if logging_settings:
            print("   Other logging settings:")
            for key, value in logging_settings.items():
                print(f"     {key}: {value}")
        else:
            print("   No other logging settings found")

    except FileNotFoundError:
        print(f"❌ Site config file not found: {site_config_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing site config: {e}")
        return False

    # Check log directory
    log_dir = '/home/frappe/frappe-bench/logs'
    print("
📁 Log Directory:"    print(f"   Path: {log_dir}")

    if os.path.exists(log_dir):
        print("   ✅ Directory exists")

        # List log files
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if log_files:
            print("   Log files found:")
            for log_file in sorted(log_files):
                file_path = os.path.join(log_dir, log_file)
                size = os.path.getsize(file_path)
                print(f"     📄 {log_file} ({size} bytes)")
        else:
            print("   ⚠️  No log files found")
    else:
        print("   ❌ Directory does not exist")

    # Check frappe.log specifically
    frappe_log_path = '/home/frappe/frappe-bench/logs/frappe.log'
    print("
📋 Frappe Main Log:"    print(f"   Path: {frappe_log_path}")

    if os.path.exists(frappe_log_path):
        size = os.path.getsize(frappe_log_path)
        print(f"   ✅ File exists ({size} bytes)")

        # Show last few lines
        try:
            with open(frappe_log_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    print("   Last 5 lines:")
                    for line in lines[-5:]:
                        print(f"     {line.strip()}")
                else:
                    print("   ⚠️  Log file is empty")
        except Exception as e:
            print(f"   ❌ Error reading log file: {e}")
    else:
        print("   ❌ File does not exist")

    return True

def configure_logging():
    """Configure logging settings"""

    print("
🔧 CONFIGURING LOGGING SETTINGS"    print("=" * 60)

    site_config_path = '/home/frappe/frappe-bench/sites/erp152-v1.vtcom.online/site_config.json'

    try:
        # Read current config
        with open(site_config_path, 'r') as f:
            site_config = json.load(f)

        # Update log level to DEBUG
        old_log_level = site_config.get('log_level', 'INFO')
        site_config['log_level'] = 'DEBUG'

        # Write back
        with open(site_config_path, 'w') as f:
            json.dump(site_config, f, indent=4)

        print("✅ Updated site configuration:"        print(f"   log_level: {old_log_level} → DEBUG")

        print("
🔄 RESTART REQUIRED:"        print("   To apply changes, restart Frappe:")
        print("   sudo supervisorctl restart frappe-bench-web:")
        print("   sudo supervisorctl restart frappe-bench-worker:")

    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

    return True

def test_logging():
    """Test logging functionality"""

    print("
🧪 TESTING LOGGING FUNCTIONALITY"    print("=" * 60)

    try:
        # Test different log levels
        frappe.logger().debug("[TEST] Debug message")
        frappe.logger().info("[TEST] Info message")
        frappe.logger().warning("[TEST] Warning message")
        frappe.logger().error("[TEST] Error message")

        print("✅ Test messages sent to logger")

        # Check if they appear in log file
        frappe_log_path = '/home/frappe/frappe-bench/logs/frappe.log'

        print("
⏳ Waiting 2 seconds for logs to be written..."        import time
        time.sleep(2)

        if os.path.exists(frappe_log_path):
            with open(frappe_log_path, 'r') as f:
                content = f.read()

            test_messages = [
                "[TEST] Debug message",
                "[TEST] Info message",
                "[TEST] Warning message",
                "[TEST] Error message"
            ]

            found_messages = []
            for msg in test_messages:
                if msg in content:
                    found_messages.append(msg)

            if found_messages:
                print("✅ Found test messages in log file:")
                for msg in found_messages:
                    print(f"   ✓ {msg}")
            else:
                print("❌ No test messages found in log file")
                print("💡 This might be because:")
                print("   - Log level is set too high (should be DEBUG or INFO)")
                print("   - Log file is being written to a different location")
                print("   - Frappe needs to be restarted")
        else:
            print("❌ Log file does not exist")

    except Exception as e:
        print(f"❌ Error testing logging: {e}")

def show_log_commands():
    """Show useful log monitoring commands"""

    print("
📋 USEFUL LOG MONITORING COMMANDS"    print("=" * 60)

    commands = [
        "# Monitor logs in real-time",
        "tail -f /home/frappe/frappe-bench/logs/frappe.log",
        "",
        "# Monitor specific patterns",
        "tail -f /home/frappe/frappe-bench/logs/frappe.log | grep INVOICE_TRACKING",
        "tail -f /home/frappe/frappe-bench/logs/frappe.log | grep SHIFT_REPORT_CALC",
        "",
        "# Search for specific invoice",
        "grep 'INV-00123' /home/frappe/frappe-bench/logs/frappe.log",
        "",
        "# Show recent errors",
        "tail -f /home/frappe/frappe-bench/logs/frappe.log | grep ERROR",
        "",
        "# Monitor with timestamps",
        "tail -f /home/frappe/frappe-bench/logs/frappe.log | while read line; do echo \"$(date '+%Y-%m-%d %H:%M:%S') | $line\"; done",
        "",
        "# Check log file size and rotation",
        "ls -la /home/frappe/frappe-bench/logs/",
        "du -h /home/frappe/frappe-bench/logs/*",
    ]

    for cmd in commands:
        if cmd.startswith("#"):
            print(f"\033[92m{cmd}\033[0m")  # Green color for comments
        else:
            print(f"   {cmd}")

def main():
    """Main function"""

    print("🔍 FRAPPE LOGGING DIAGNOSTIC TOOL")
    print("=" * 60)

    # Check current configuration
    check_log_configuration()

    # Ask user what to do
    print("
🎯 WHAT WOULD YOU LIKE TO DO?"    print("1. Configure logging (set log_level to DEBUG)")
    print("2. Test logging functionality")
    print("3. Show monitoring commands")
    print("4. Do all of the above")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice in ['1', '4']:
        configure_logging()

    if choice in ['2', '4']:
        test_logging()

    if choice in ['3', '4']:
        show_log_commands()

    print("
🎉 DIAGNOSTIC COMPLETE!"    print("If you're still not seeing logs, try:")
    print("1. Restart Frappe services")
    print("2. Check file permissions on log directory")
    print("3. Verify the log file path is correct")

if __name__ == "__main__":
    try:
        main()
        frappe.destroy()
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        frappe.destroy()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        frappe.destroy()
        exit(1)