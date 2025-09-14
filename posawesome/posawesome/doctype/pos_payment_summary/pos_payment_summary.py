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
	"""
	Create payment summary records for a shift report
	This is called when user clicks "List Invoice" button

	Args:
		shift_report_name (str): Name of the POS Shift Report

	Returns:
		dict: Result with success status and data
	"""
	log.info(f"[PAYMENT_SUMMARY] Creating payment summaries for shift report: {shift_report_name}")

	try:
		# Get shift report
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		log.info(f"[PAYMENT_SUMMARY] Found shift report: {shift_report.name}")

		# Get all invoices for this shift
		invoices = frappe.get_all("Sales Invoice",
			filters={
				"pos_opening_shift": shift_report.pos_opening_shift,
				"docstatus": 1  # Only submitted invoices
			},
			fields=[
				"name", "payment_method", "grand_total", "paid_amount",
				"is_return", "status", "posting_date", "posting_time"
			]
		)

		log.info(f"[PAYMENT_SUMMARY] Found {len(invoices)} invoices for shift report")

		# Group invoices by payment method
		payment_methods = {}

		for invoice in invoices:
			method = invoice.payment_method or "Cash"
			amount = invoice.grand_total or 0

			if method not in payment_methods:
				payment_methods[method] = {
					"transaction_count": 0,
					"transaction_amount": 0,
					"sales_amount": 0,
					"returns_amount": 0
				}

			payment_methods[method]["transaction_count"] += 1

			# Handle returns (negative amounts)
			if invoice.is_return:
				payment_methods[method]["returns_amount"] += abs(amount)
				payment_methods[method]["transaction_amount"] -= abs(amount)
			else:
				payment_methods[method]["sales_amount"] += amount
				payment_methods[method]["transaction_amount"] += amount

		# Get opening amounts from shift report
		opening_amounts = {}
		if shift_report.opening_amounts:
			try:
				opening_amounts = frappe.parse_json(shift_report.opening_amounts)
			except:
				log.warning(f"[PAYMENT_SUMMARY] Could not parse opening amounts for shift {shift_report.name}")

		# Get expected closing amounts
		expected_closing = {}
		if shift_report.expected_closing_amounts:
			try:
				expected_closing = frappe.parse_json(shift_report.expected_closing_amounts)
			except:
				log.warning(f"[PAYMENT_SUMMARY] Could not parse expected closing amounts for shift {shift_report.name}")

		# Create payment summary records
		payment_summaries = []
		created_count = 0
		updated_count = 0

		for method, data in payment_methods.items():
			try:
				# Check if payment summary already exists
				existing = frappe.db.exists("POS Payment Summary", {
					"shift_report_id": f"{shift_report.shift_report_id}_{method}",
					"pos_shift_report": shift_report.name
				})

				if existing:
					# Update existing record
					payment_summary = frappe.get_doc("POS Payment Summary", existing)
					payment_summary.transaction_count = data["transaction_count"]
					payment_summary.transaction_amount = data["transaction_amount"]
					payment_summary.closing_amount = (opening_amounts.get(method, 0) + data["transaction_amount"])
					payment_summary.expected_closing_amount = expected_closing.get(method, 0)
					payment_summary.difference = payment_summary.closing_amount - payment_summary.expected_closing_amount
					payment_summary.save()
					updated_count += 1
					log.info(f"[PAYMENT_SUMMARY] Updated payment summary for {method}")
				else:
					# Create new record
					payment_summary = frappe.get_doc({
						"doctype": "POS Payment Summary",
						"shift_report_id": f"{shift_report.shift_report_id}_{method}",
						"pos_shift_report": shift_report.name,
						"pos_opening_shift": shift_report.pos_opening_shift,
						"posting_date": shift_report.posting_date or shift_report.opening_date,
						"shift_start_time": shift_report.opening_time,
						"shift_end_time": shift_report.closing_date,
						"payment_method": method,
						"payment_method_type": get_payment_method_type(method),
						"currency": "VND",  # Default, can be updated from POS Profile
						"transaction_count": data["transaction_count"],
						"company": shift_report.company,
						"pos_profile": shift_report.pos_profile,
						"opening_amount": opening_amounts.get(method, 0),
						"transaction_amount": data["transaction_amount"],
						"expected_closing_amount": expected_closing.get(method, 0),
						"closing_amount": opening_amounts.get(method, 0) + data["transaction_amount"],
						"notes": f"Auto-generated from shift report {shift_report.name}"
					})

					payment_summary.insert()
					created_count += 1
					log.info(f"[PAYMENT_SUMMARY] Created payment summary for {method}")

				payment_summaries.append({
					"payment_method": method,
					"opening_amount": opening_amounts.get(method, 0),
					"transaction_amount": data["transaction_amount"],
					"closing_amount": opening_amounts.get(method, 0) + data["transaction_amount"],
					"transaction_count": data["transaction_count"],
					"sales_amount": data["sales_amount"],
					"returns_amount": data["returns_amount"]
				})

			except Exception as e:
				log.error(f"[PAYMENT_SUMMARY] Error creating payment summary for {method}: {str(e)}")
				continue

		log.info(f"[PAYMENT_SUMMARY] Completed: Created {created_count}, Updated {updated_count} payment summaries")

		return {
			"success": True,
			"message": f"Payment summaries processed successfully. Created: {created_count}, Updated: {updated_count}",
			"data": {
				"payment_summaries": payment_summaries,
				"created_count": created_count,
				"updated_count": updated_count,
				"total_methods": len(payment_summaries)
			}
		}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error creating payment summaries: {str(e)}")
		return {
			"success": False,
			"message": f"Error creating payment summaries: {str(e)}"
		}


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
						"posting_date": shift_report.posting_date or shift_report.opening_date,
						"shift_start_time": shift_report.opening_time,
						"payment_method": method,
						"payment_method_type": get_payment_method_type(method),
						"currency": "VND",
						"company": shift_report.company,
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