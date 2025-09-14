# -*- coding: utf-8 -*-
# Copyright (c) 2025, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("pos_payment_summary")


class POSPaymentSummary(Document):
	def validate(self):
		"""Validate POS Payment Summary"""
		self.validate_amounts()
		self.calculate_difference()

	def validate_amounts(self):
		"""Validate amount fields"""
		# Ensure closing amount is calculated correctly
		expected_closing = self.opening_amount + self.transaction_amount
		if abs(self.closing_amount - expected_closing) > 0.01:  # Allow small rounding differences
			log.warning(f"[PAYMENT_SUMMARY] Closing amount mismatch for {self.payment_method} in shift {self.shift_report_id}")
			self.closing_amount = expected_closing

	def calculate_difference(self):
		"""Calculate difference between expected and actual closing amounts"""
		if self.expected_closing_amount:
			self.difference = self.closing_amount - self.expected_closing_amount
		else:
			self.difference = 0


@frappe.whitelist()
def create_payment_summaries_for_shift(shift_report_name):
    
	log.info(f"[PAYMENT_SUMMARY] Tao bang tong hop du lieu Shift Summary: {shift_report_name}")

	try:
		log.info(f"[PAYMENT_SUMMARY] 🚀 START: Creating payment summaries for shift: {shift_report_name}")

		# 1. Get shift report data
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 1: Retrieving shift report data")
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 1: Found shift report: {shift_report.name} (ID: {shift_report.shift_report_id})")

		# 2. Get all invoices for this shift (optimized query)
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 2: Querying invoices from database")
		log.info(f"[PAYMENT_SUMMARY] 🔍 STEP 2: POS Opening Shift: {shift_report.pos_opening_shift}")

		invoices = frappe.get_all("Sales Invoice",
			filters={
				"posa_pos_opening_shift": shift_report.pos_opening_shift,
				"docstatus": 1
			},
			fields=["name", "grand_total", "is_return"]
		)

		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 2: Found {len(invoices)} submitted invoices")

		# Get payment methods from payments child table
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 3: Retrieving payment methods from child tables")
		invoice_payments = {}
		payment_methods_found = 0

		for invoice in invoices:
			payments = frappe.get_all("Sales Invoice Payment",
				filters={"parent": invoice.name},
				fields=["mode_of_payment", "amount"]
			)
			if payments:
				# Use primary payment method (first one)
				invoice_payments[invoice.name] = {
					"payment_method": payments[0].mode_of_payment or "Cash",
					"amount": payments[0].amount or 0
				}
				payment_methods_found += 1
			else:
				# Fallback if no payments found
				invoice_payments[invoice.name] = {
					"payment_method": "Cash",
					"amount": invoice.grand_total or 0
				}

		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 3: Retrieved payment methods for {payment_methods_found}/{len(invoices)} invoices")

		# 3. Group and calculate payment methods (optimized)
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 4: Grouping and calculating payment methods")
		payment_data = _calculate_payment_methods(invoices, invoice_payments)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 4: Grouped into {len(payment_data)} payment methods")

		# Log payment method details
		for method, data in payment_data.items():
			log.info(f"[PAYMENT_SUMMARY] 📊 STEP 4: {method} - {data['transaction_count']} transactions, Amount: {data['transaction_amount']}")

		# 4. Get opening and expected amounts
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 5: Parsing opening and expected amounts")
		opening_amounts = _parse_json_safe(shift_report.opening_amounts, {})
		expected_closing = _parse_json_safe(shift_report.expected_closing_amounts, {})

		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 5: Opening amounts: {len(opening_amounts)} methods, Expected: {len(expected_closing)} methods")

		# 5. Create/update payment summaries
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 6: Creating/updating payment summary records")
		payment_summaries = []
		created_count = 0
		updated_count = 0

		for method, data in payment_data.items():
			log.info(f"[PAYMENT_SUMMARY] 🔄 STEP 6: Processing payment method: {method}")
			try:
				result = _create_or_update_payment_summary(
					shift_report, method, data, opening_amounts, expected_closing
				)

				if result and result["created"]:
					created_count += 1
					log.info(f"[PAYMENT_SUMMARY] ✅ Created payment summary for {method}")
				elif result:
					updated_count += 1
					log.info(f"[PAYMENT_SUMMARY] ✅ Updated payment summary for {method}")

				if result:
					payment_summaries.append(result["summary"])
				else:
					log.warning(f"[PAYMENT_SUMMARY] ⚠️ Failed to process payment method: {method}")
			except Exception as e:
				log.error(f"[PAYMENT_SUMMARY] ❌ Error processing {method}: {str(e)}")
				continue

		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 6: Processed {len(payment_summaries)} payment methods")
		log.info(f"[PAYMENT_SUMMARY] 📈 STEP 6: Summary - Created: {created_count}, Updated: {updated_count}")

		# 7. Commit database changes
		log.info(f"[PAYMENT_SUMMARY] 💾 STEP 7: Committing database changes")
		frappe.db.commit()
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 7: Database changes committed")

		# 8. Final summary and return
		log.info(f"[PAYMENT_SUMMARY] 🎉 COMPLETED: Successfully processed {len(payment_summaries)} payment methods for shift {shift_report_name}")

		return {
			"success": True,
			"message": f"Processed {len(payment_summaries)} payment methods",
			"data": {
				"payment_summaries": payment_summaries,
				"created_count": created_count,
				"updated_count": updated_count,
				"total_methods": len(payment_summaries)
			}
		}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error: {str(e)}")
		return {
			"success": False,
			"message": f"Error creating payment summaries: {str(e)}"
		}


def _calculate_payment_methods(invoices, invoice_payments):
	"""Calculate payment method totals from invoices and payments"""
	payment_methods = {}

	for invoice in invoices:
		# Get payment method from payments data
		payment_info = invoice_payments.get(invoice.name, {})
		method = payment_info.get("payment_method", "Cash")
		amount = invoice.grand_total or 0

		if method not in payment_methods:
			payment_methods[method] = {
				"transaction_count": 0,
				"transaction_amount": 0,
				"sales_amount": 0,
				"returns_amount": 0
			}

		payment_methods[method]["transaction_count"] += 1

		if invoice.is_return:
			payment_methods[method]["returns_amount"] += abs(amount)
			payment_methods[method]["transaction_amount"] -= abs(amount)
		else:
			payment_methods[method]["sales_amount"] += amount
			payment_methods[method]["transaction_amount"] += amount

	return payment_methods


def _parse_json_safe(json_string, default=None):
	"""Safely parse JSON string"""
	if not json_string:
		return default or {}

	try:
		return frappe.parse_json(json_string)
	except:
		log.warning(f"[PAYMENT_SUMMARY] Could not parse JSON: {json_string[:50]}...")
		return default or {}


def _create_or_update_payment_summary(shift_report, method, data, opening_amounts, expected_closing):
	"""Create or update a single payment summary record"""
	try:
		# Check if exists
		shift_report_id = f"{shift_report.shift_report_id}_{method}"
		existing = frappe.db.exists("POS Payment Summary", {
			"shift_report_id": shift_report_id,
			"pos_shift_report": shift_report.name
		})

		opening_amount = opening_amounts.get(method, 0)
		transaction_amount = data["transaction_amount"]
		closing_amount = opening_amount + transaction_amount

		if existing:
			# Update existing
			payment_summary = frappe.get_doc("POS Payment Summary", existing)
			payment_summary.transaction_count = data["transaction_count"]
			payment_summary.transaction_amount = transaction_amount
			payment_summary.closing_amount = closing_amount
			payment_summary.expected_closing_amount = expected_closing.get(method, 0)
			payment_summary.difference = closing_amount - payment_summary.expected_closing_amount
			payment_summary.save()

			log.info(f"[PAYMENT_SUMMARY] Updated: {method}")
			created = False
		else:
			# Create new
			payment_summary = frappe.get_doc({
				"doctype": "POS Payment Summary",
				"shift_report_id": shift_report_id,
				"pos_shift_report": shift_report.name,
				"pos_opening_shift": shift_report.pos_opening_shift,
				"posting_date": shift_report.opening_date,
				"shift_start_time": shift_report.opening_time,
				"shift_end_time": shift_report.closing_date,
				"payment_method": method,
				"payment_method_type": get_payment_method_type(method),
				"currency": "VND",
				"transaction_count": data["transaction_count"],
				"company": shift_report.company or "Default Company",
				"pos_profile": shift_report.pos_profile,
				"opening_amount": opening_amount,
				"transaction_amount": transaction_amount,
				"expected_closing_amount": expected_closing.get(method, 0),
				"closing_amount": closing_amount,
				"notes": f"Auto-generated from shift report {shift_report.name}"
			})

			payment_summary.insert()
			log.info(f"[PAYMENT_SUMMARY] Created: {method}")
			created = True

		summary = {
			"payment_method": method,
			"opening_amount": opening_amount,
			"transaction_amount": transaction_amount,
			"closing_amount": closing_amount,
			"transaction_count": data["transaction_count"],
			"sales_amount": data["sales_amount"],
			"returns_amount": data["returns_amount"]
		}

		return {"created": created, "summary": summary}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error processing {method}: {str(e)}")
		return None


@frappe.whitelist()
def get_payment_summaries_for_shift(shift_report_name):
	"""
	Get payment summaries for a shift report

	Args:
		shift_report_name (str): Name of the POS Shift Report

	Returns:
		dict: Payment summaries data
	"""
	log.info(f"[PAYMENT_SUMMARY] Getting payment summaries for shift report: {shift_report_name}")

	try:
		# Get all payment summaries for this shift report
		payment_summaries = frappe.get_all("POS Payment Summary",
			filters={
				"pos_shift_report": shift_report_name
			},
			fields=[
				"name", "payment_method", "payment_method_type",
				"opening_amount", "transaction_amount", "closing_amount",
				"expected_closing_amount", "difference", "transaction_count",
				"currency", "posting_date"
			],
			order_by="payment_method"
		)

		log.info(f"[PAYMENT_SUMMARY] Found {len(payment_summaries)} payment summaries")

		return {
			"success": True,
			"data": payment_summaries
		}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error getting payment summaries: {str(e)}")
		return {
			"success": False,
			"message": f"Error getting payment summaries: {str(e)}"
		}


def get_payment_method_type(payment_method):
	"""
	Determine payment method type based on payment method name

	Args:
		payment_method (str): Payment method name

	Returns:
		str: Payment method type
	"""
	method_lower = payment_method.lower()

	if "cash" in method_lower:
		return "Cash"
	elif any(card_type in method_lower for card_type in ["card", "visa", "master", "amex"]):
		return "Card"
	elif any(digital_type in method_lower for digital_type in ["m-pesa", "mpesa", "mobile", "digital"]):
		return "Digital"
	else:
		return "Other"


@frappe.whitelist()
def initialize_payment_summaries_for_shift(shift_report_name):
	"""
	Initialize payment summary records when shift is opened
	This creates empty records that will be populated when List Invoice is clicked

	Args:
		shift_report_name (str): Name of the POS Shift Report

	Returns:
		dict: Result
	"""
	log.info(f"[PAYMENT_SUMMARY] Initializing payment summaries for shift report: {shift_report_name}")

	try:
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)

		# Get opening amounts to determine payment methods
		opening_amounts = {}
		if shift_report.opening_amounts:
			try:
				opening_amounts = frappe.parse_json(shift_report.opening_amounts)
			except:
				log.warning(f"[PAYMENT_SUMMARY] Could not parse opening amounts for initialization")

		# Create payment summary records for each payment method
		created_count = 0
		for method, opening_amount in opening_amounts.items():
			try:
				# Check if already exists
				existing = frappe.db.exists("POS Payment Summary", {
					"shift_report_id": f"{shift_report.shift_report_id}_{method}",
					"pos_shift_report": shift_report.name
				})

				if not existing:
					payment_summary = frappe.get_doc({
						"doctype": "POS Payment Summary",
						"shift_report_id": f"{shift_report.shift_report_id}_{method}",
						"pos_shift_report": shift_report.name,
						"pos_opening_shift": shift_report.pos_opening_shift,
						"posting_date": shift_report.opening_date,
						"shift_start_time": shift_report.opening_time,
						"payment_method": method,
						"payment_method_type": get_payment_method_type(method),
						"currency": "VND",
						"company": shift_report.company or "Default Company",
						"pos_profile": shift_report.pos_profile,
						"opening_amount": opening_amount,
						"transaction_amount": 0,
						"closing_amount": opening_amount,
						"transaction_count": 0,
						"notes": f"Initialized for shift report {shift_report.name}"
					})

					payment_summary.insert()
					created_count += 1
					log.info(f"[PAYMENT_SUMMARY] Initialized payment summary for {method}")

			except Exception as e:
				log.error(f"[PAYMENT_SUMMARY] Error initializing payment summary for {method}: {str(e)}")
				continue

		log.info(f"[PAYMENT_SUMMARY] Initialized {created_count} payment summary records")

		return {
			"success": True,
			"message": f"Initialized {created_count} payment summary records",
			"data": {
				"initialized_count": created_count
			}
		}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error initializing payment summaries: {str(e)}")
		return {
			"success": False,
			"message": f"Error initializing payment summaries: {str(e)}"
		}