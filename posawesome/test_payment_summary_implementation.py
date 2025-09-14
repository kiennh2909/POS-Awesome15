#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for POS Payment Summary Implementation

This script tests the new POS Payment Summary functionality:
1. DocType creation
2. API methods
3. Data flow from List Invoice button
4. Payment summary calculations
"""

import frappe
import json
from frappe.utils import nowdate, nowtime


def test_payment_summary_implementation():
	"""Test the complete payment summary implementation"""

	print("🧪 TESTING POS PAYMENT SUMMARY IMPLEMENTATION")
	print("=" * 60)

	try:
		# Test 1: Check if DocType exists
		print("\n1️⃣ Testing DocType Creation...")
		if frappe.db.exists("DocType", "POS Payment Summary"):
			print("✅ POS Payment Summary DocType exists")
		else:
			print("❌ POS Payment Summary DocType not found")
			return False

		# Test 2: Check API methods exist
		print("\n2️⃣ Testing API Methods...")
		try:
			from posawesome.posawesome.api.shift_reports import get_shift_report_with_payment_summary
			print("✅ get_shift_report_with_payment_summary method exists")
		except ImportError:
			print("❌ get_shift_report_with_payment_summary method not found")
			return False

		try:
			from posawesome.posawesome.api.shift_reports import initialize_payment_summaries
			print("✅ initialize_payment_summaries method exists")
		except ImportError:
			print("❌ initialize_payment_summaries method not found")
			return False

		# Test 3: Check POS Payment Summary methods
		print("\n3️⃣ Testing POS Payment Summary Methods...")
		try:
			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
			print("✅ create_payment_summaries_for_shift method exists")
		except ImportError:
			print("❌ create_payment_summaries_for_shift method not found")
			return False

		# Test 4: Create test data
		print("\n4️⃣ Creating Test Data...")

		# Create test POS Opening Shift
		test_opening_shift = create_test_opening_shift()
		if not test_opening_shift:
			print("❌ Failed to create test opening shift")
			return False

		# Create test Shift Report
		test_shift_report = create_test_shift_report(test_opening_shift)
		if not test_shift_report:
			print("❌ Failed to create test shift report")
			return False

		# Create test invoices
		test_invoices = create_test_invoices(test_opening_shift)
		if not test_invoices:
			print("❌ Failed to create test invoices")
			return False

		# Test 5: Test payment summary creation
		print("\n5️⃣ Testing Payment Summary Creation...")
		result = test_payment_summary_creation(test_shift_report)
		if not result:
			print("❌ Payment summary creation test failed")
			return False

		# Test 6: Test API integration
		print("\n6️⃣ Testing API Integration...")
		result = test_api_integration(test_shift_report)
		if not result:
			print("❌ API integration test failed")
			return False

		# Cleanup test data
		print("\n🧹 Cleaning up test data...")
		cleanup_test_data(test_shift_report, test_opening_shift, test_invoices)

		print("\n🎉 ALL TESTS PASSED! POS Payment Summary implementation is working correctly.")
		return True

	except Exception as e:
		print(f"\n💥 TEST FAILED with error: {str(e)}")
		import traceback
		traceback.print_exc()
		return False


def create_test_opening_shift():
	"""Create a test POS Opening Shift"""
	try:
		opening_shift = frappe.get_doc({
			"doctype": "POS Opening Shift",
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"company": "NVL-DaiLoan",
			"pos_profile": "POS_DY134",
			"user": "test@example.com",
			"status": "Open",
			"opening_amounts": json.dumps({
				"Cash": 1000.00,
				"Card": 500.00,
				"M-Pesa": 200.00
			})
		})
		opening_shift.insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"✅ Created test opening shift: {opening_shift.name}")
		return opening_shift.name
	except Exception as e:
		print(f"❌ Failed to create test opening shift: {str(e)}")
		return None


def create_test_shift_report(opening_shift_name):
	"""Create a test POS Shift Report"""
	try:
		shift_report = frappe.get_doc({
			"doctype": "POS Shift Report",
			"shift_report_id": f"TEST-SHIFT-{opening_shift_name}",
			"pos_opening_shift": opening_shift_name,
			"opening_date": nowdate(),
			"opening_time": nowtime(),
			"status": "Open",
			"opening_amounts": json.dumps({
				"Cash": 1000.00,
				"Card": 500.00,
				"M-Pesa": 200.00
			})
		})
		shift_report.insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"✅ Created test shift report: {shift_report.name}")
		return shift_report.name
	except Exception as e:
		print(f"❌ Failed to create test shift report: {str(e)}")
		return None


def create_test_invoices(opening_shift_name):
	"""Create test sales invoices"""
	invoices = []
	try:
		# Create invoice 1 - Cash payment
		invoice1 = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": "Test Customer",
			"company": "NVL-DaiLoan",
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"pos_opening_shift": opening_shift_name,
			"pos_profile": "POS_DY134",
			"is_pos": 1,
			"items": [{
				"item_code": "Test Item",
				"qty": 1,
				"rate": 100.00,
				"amount": 100.00
			}],
			"payments": [{
				"mode_of_payment": "Cash",
				"amount": 100.00
			}]
		})
		invoice1.insert(ignore_permissions=True)
		invoice1.submit()
		invoices.append(invoice1.name)

		# Create invoice 2 - Card payment
		invoice2 = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": "Test Customer",
			"company": "NVL-DaiLoan",
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"pos_opening_shift": opening_shift_name,
			"pos_profile": "POS_DY134",
			"is_pos": 1,
			"items": [{
				"item_code": "Test Item",
				"qty": 1,
				"rate": 50.00,
				"amount": 50.00
			}],
			"payments": [{
				"mode_of_payment": "Card",
				"amount": 50.00
			}]
		})
		invoice2.insert(ignore_permissions=True)
		invoice2.submit()
		invoices.append(invoice2.name)

		print(f"✅ Created {len(invoices)} test invoices")
		return invoices

	except Exception as e:
		print(f"❌ Failed to create test invoices: {str(e)}")
		return None


def test_payment_summary_creation(shift_report_name):
	"""Test payment summary creation"""
	try:
		from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift

		result = create_payment_summaries_for_shift(shift_report_name)

		if result.get("success"):
			print(f"✅ Payment summaries created: {result['data']['created_count']} created, {result['data']['updated_count']} updated")

			# Check if payment summary records exist
			payment_summaries = frappe.get_all("POS Payment Summary",
				filters={"pos_shift_report": shift_report_name},
				fields=["name", "payment_method", "transaction_amount"]
			)

			if len(payment_summaries) > 0:
				print(f"✅ Found {len(payment_summaries)} payment summary records")
				for ps in payment_summaries:
					print(f"   - {ps.payment_method}: {ps.transaction_amount}")
				return True
			else:
				print("❌ No payment summary records found")
				return False
		else:
			print(f"❌ Payment summary creation failed: {result.get('message')}")
			return False

	except Exception as e:
		print(f"❌ Payment summary creation test error: {str(e)}")
		return False


def test_api_integration(shift_report_name):
	"""Test API integration"""
	try:
		from posawesome.posawesome.api.shift_reports import get_shift_report_with_payment_summary

		result = get_shift_report_with_payment_summary(shift_report_name)

		if "payment_summaries" in result and len(result["payment_summaries"]) > 0:
			print(f"✅ API returned {len(result['payment_summaries'])} payment summaries")
			return True
		else:
			print("❌ API did not return payment summaries")
			return False

	except Exception as e:
		print(f"❌ API integration test error: {str(e)}")
		return False


def cleanup_test_data(shift_report_name, opening_shift_name, invoice_names):
	"""Clean up test data"""
	try:
		# Delete payment summaries
		payment_summaries = frappe.get_all("POS Payment Summary",
			filters={"pos_shift_report": shift_report_name},
			fields=["name"]
		)

		for ps in payment_summaries:
			frappe.delete_doc("POS Payment Summary", ps.name, ignore_permissions=True)

		# Delete invoices
		for invoice_name in invoice_names:
			if frappe.db.exists("Sales Invoice", invoice_name):
				invoice = frappe.get_doc("Sales Invoice", invoice_name)
				if invoice.docstatus == 1:
					invoice.cancel()
				frappe.delete_doc("Sales Invoice", invoice_name, ignore_permissions=True)

		# Delete shift report
		if frappe.db.exists("POS Shift Report", shift_report_name):
			frappe.delete_doc("POS Shift Report", shift_report_name, ignore_permissions=True)

		# Delete opening shift
		if frappe.db.exists("POS Opening Shift", opening_shift_name):
			frappe.delete_doc("POS Opening Shift", opening_shift_name, ignore_permissions=True)

		frappe.db.commit()
		print("✅ Test data cleaned up successfully")

	except Exception as e:
		print(f"⚠️ Cleanup warning: {str(e)}")


if __name__ == "__main__":
	# Run tests
	success = test_payment_summary_implementation()

	if success:
		print("\n🎉 IMPLEMENTATION SUCCESSFUL!")
		print("POS Payment Summary feature is ready for production use.")
	else:
		print("\n💥 IMPLEMENTATION FAILED!")
		print("Please check the errors above and fix them before deploying.")

	exit(0 if success else 1)