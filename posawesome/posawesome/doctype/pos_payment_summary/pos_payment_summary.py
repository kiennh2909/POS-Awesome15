# # -*- coding: utf-8 -*-
# # Copyright (c) 2025, Youssef Restom and contributors
# # For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe
# from frappe import _
# from frappe.model.document import Document
# from posawesome.posawesome.utils.logging import get_logger

# # Initialize logger
# log = get_logger("pos_payment_summary")


# class POSPaymentSummary(Document):
# 	def validate(self):
# 		"""Validate POS Payment Summary"""
# 		self.validate_amounts()
# 		self.calculate_difference()

# 	def validate_amounts(self):
# 		"""Validate amount fields"""
# 		# Ensure closing amount is calculated correctly
# 		expected_closing = self.opening_amount + self.transaction_amount
# 		if abs(self.closing_amount - expected_closing) > 0.01:  # Allow small rounding differences
# 			log.warning(f"[PAYMENT_SUMMARY] Closing amount mismatch for {self.payment_method} in shift {self.shift_report_id}")
# 			self.closing_amount = expected_closing

# 	def calculate_difference(self):
# 		"""Calculate difference between expected and actual closing amounts"""
# 		if self.expected_closing_amount:
# 			self.difference = self.closing_amount - self.expected_closing_amount
# 		else:
# 			self.difference = 0


# @frappe.whitelist()
# def create_payment_summaries_for_shift(shift_report_name):
    
# 	log.info(f"[PAYMENT_SUMMARY] Tao bang tong hop du lieu Shift Summary: {shift_report_name}")

# 	try:
# 		log.info(f"[PAYMENT_SUMMARY] 🚀 START: Creating payment summaries for shift: {shift_report_name}")

# 		# 1. Get shift report data
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 1: Retrieving shift report data")
# 		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 1: Found shift report: {shift_report.name} (ID: {shift_report.shift_report_id})")

# 		# 2. Get all invoices for this shift (optimized query)
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 2: Querying invoices from database")
# 		log.info(f"[PAYMENT_SUMMARY] 🔍 STEP 2: POS Opening Shift: {shift_report.pos_opening_shift}")

# 		invoices = frappe.get_all("Sales Invoice",
# 			filters={
# 				"posa_pos_opening_shift": shift_report.pos_opening_shift,
# 				"docstatus": 1
# 			},
# 			fields=["name", "grand_total", "is_return"]
# 		)

# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 2: Found {len(invoices)} submitted invoices")

# 		# Get payment methods from payments child table
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 3: Retrieving payment methods from child tables")
# 		invoice_payments = {}
# 		payment_methods_found = 0

# 		for invoice in invoices:
# 			payments = frappe.get_all("Sales Invoice Payment",
# 				filters={"parent": invoice.name},
# 				fields=["mode_of_payment", "amount"]
# 			)
# 			if payments:
# 				# Use primary payment method (first one)
# 				invoice_payments[invoice.name] = {
# 					"payment_method": payments[0].mode_of_payment or "Tiền mặt - POS",
# 					"amount": payments[0].amount or 0
# 				}
# 				payment_methods_found += 1
# 			else:
# 				# Fallback if no payments found
# 				invoice_payments[invoice.name] = {
# 					"payment_method": "Tiền mặt - POS",
# 					"amount": invoice.grand_total or 0
# 				}

# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 3: Retrieved payment methods for {payment_methods_found}/{len(invoices)} invoices")

# 		# 3. Get valid payment methods for validation
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 4: Getting valid payment methods for validation")
# 		valid_payment_methods = get_valid_payment_methods_for_shift(shift_report)

# 		# 4. Group and calculate payment methods with validation
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 5: Grouping and calculating payment methods with validation")
# 		payment_data = _calculate_payment_methods(invoices, invoice_payments, valid_payment_methods)
# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 5: Grouped into {len(payment_data)} payment methods")

# 		# Log payment method details
# 		for method, data in payment_data.items():
# 			log.info(f"[PAYMENT_SUMMARY] 📊 STEP 4: {method} - {data['transaction_count']} transactions, Amount: {data['transaction_amount']}")

# 		# 5. Get opening and expected amounts from POS Opening Shift Detail
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 6: Parsing opening and expected amounts from POS Opening Shift Detail")

# 		# Get opening amounts from POS Opening Shift Detail (balance_details)
# 		opening_amounts = {}
# 		try:
# 			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
# 			if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
# 				for detail in opening_shift.balance_details:
# 					opening_amounts[detail.mode_of_payment] = detail.amount or 0
# 				log.info(f"[PAYMENT_SUMMARY] ✅ STEP 6: Loaded {len(opening_amounts)} opening amounts from POS Opening Shift Detail")
# 			else:
# 				log.warning(f"[PAYMENT_SUMMARY] ⚠️ STEP 6: No balance_details found in POS Opening Shift")
# 		except Exception as e:
# 			log.error(f"[PAYMENT_SUMMARY] ❌ STEP 6: Error loading opening amounts from POS Opening Shift Detail: {str(e)}")

# 		# Get expected closing amounts (fallback to shift report if available)
# 		expected_closing = _parse_json_safe(shift_report.expected_closing_amounts, {})

# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 6: Opening amounts: {len(opening_amounts)} methods, Expected: {len(expected_closing)} methods")

# 		# 6. Initialize payment summaries for all opening shift methods first
# 		log.info(f"[PAYMENT_SUMMARY] 🎯 STEP 6: Initializing payment summaries for all opening shift methods")
# 		try:
# 			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import initialize_payment_summaries_for_shift
# 			init_result = initialize_payment_summaries_for_shift(shift_report.name)
	
# 			if init_result.get("success"):
# 				log.info(f"[PAYMENT_SUMMARY] ✅ STEP 6: Initialized {init_result['data']['initialized_count']} payment summary records")
# 			else:
# 				log.warning(f"[PAYMENT_SUMMARY] ⚠️ STEP 6: Failed to initialize payment summaries: {init_result.get('message')}")
# 		except Exception as init_error:
# 			log.error(f"[PAYMENT_SUMMARY] ❌ STEP 6: Error initializing payment summaries: {str(init_error)}")
# 			# Continue with processing even if initialization fails
	
# 		# 7. Create/update payment summaries from invoice data
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 7: Creating/updating payment summary records from invoices")
# 		log.info(f"[PAYMENT_SUMMARY] 📊 STEP 7: Processing {len(payment_data)} payment methods from invoices")
# 		payment_summaries = []
# 		created_count = 0
# 		updated_count = 0

# 		for method, data in payment_data.items():
# 			log.info(f"[PAYMENT_SUMMARY] 🔄 STEP 8: Processing payment method: '{method}'")
# 			log.info(f"[PAYMENT_SUMMARY] 📈 STEP 8: {method} - Transaction Count: {data['transaction_count']}, Amount: {data['transaction_amount']}")

# 			try:
# 				# Log opening amount info
# 				opening_amount = opening_amounts.get(method, 0)
# 				log.info(f"[PAYMENT_SUMMARY] 💰 STEP 8: {method} - Opening Amount: {opening_amount}")

# 				result = _create_or_update_payment_summary(
# 					shift_report, method, data, opening_amounts, expected_closing
# 				)

# 				if result and result["created"]:
# 					created_count += 1
# 					log.info(f"[PAYMENT_SUMMARY] ✅ STEP 8: CREATED payment summary for '{method}' (ID: {result['summary'].get('name', 'N/A')})")
# 				elif result:
# 					updated_count += 1
# 					log.info(f"[PAYMENT_SUMMARY] ✅ STEP 8: UPDATED payment summary for '{method}' (ID: {result['summary'].get('name', 'N/A')})")

# 				if result:
# 					payment_summaries.append(result["summary"])
# 					log.info(f"[PAYMENT_SUMMARY] 📊 STEP 8: {method} - Final Amount: {result['summary'].get('closing_amount', 0)}")
# 				else:
# 					log.warning(f"[PAYMENT_SUMMARY] ⚠️ STEP 8: FAILED to process payment method: '{method}' - No result returned")
# 			except Exception as e:
# 				log.error(f"[PAYMENT_SUMMARY] ❌ STEP 8: ERROR processing '{method}': {str(e)}")
# 				log.error(f"[PAYMENT_SUMMARY] ❌ STEP 8: {method} - Exception details: {type(e).__name__}")
# 				continue

# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 8: COMPLETED processing {len(payment_summaries)}/{len(payment_data)} payment methods")
# 		log.info(f"[PAYMENT_SUMMARY] 📈 STEP 8: SUMMARY - Created: {created_count}, Updated: {updated_count}, Failed: {len(payment_data) - len(payment_summaries)}")

# 		# 8. Validate data consistency
# 		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 9: Validating data consistency")
# 		try:
# 			validate_payment_summary_consistency(shift_report)
# 			log.info(f"[PAYMENT_SUMMARY] ✅ STEP 9: Data consistency validated")
# 		except Exception as e:
# 			log.error(f"[PAYMENT_SUMMARY] ❌ STEP 9: Data consistency validation failed: {str(e)}")
# 			return {
# 				"success": False,
# 				"message": f"Data consistency validation failed: {str(e)}"
# 			}

# 		# 9. Commit database changes
# 		log.info(f"[PAYMENT_SUMMARY] 💾 STEP 10: Committing database changes")
# 		frappe.db.commit()
# 		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 10: Database changes committed")

# 		# 10. Final summary and return
# 		log.info(f"[PAYMENT_SUMMARY] 🎉 COMPLETED: Successfully processed {len(payment_summaries)} payment methods for shift {shift_report_name}")

# 		return {
# 			"success": True,
# 			"message": f"Processed {len(payment_summaries)} payment methods with validation",
# 			"data": {
# 				"payment_summaries": payment_summaries,
# 				"created_count": created_count,
# 				"updated_count": updated_count,
# 				"total_methods": len(payment_summaries),
# 				"validation_passed": True
# 			}
# 		}

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error: {str(e)}")
# 		return {
# 			"success": False,
# 			"message": f"Error creating payment summaries: {str(e)}"
# 		}


# def _calculate_payment_methods(invoices, invoice_payments, valid_payment_methods=None):
# 	"""
# 	Calculate payment method totals from invoices and payments with validation

# 	Args:
# 		invoices: List of invoice documents
# 		invoice_payments: Dict of payment info per invoice
# 		valid_payment_methods: List of valid payment methods (optional)

# 	Returns:
# 		dict: Payment method totals
# 	"""
# 	payment_methods = {}

# 	# If valid_payment_methods provided, initialize with all valid methods
# 	if valid_payment_methods:
# 		for method in valid_payment_methods:
# 			payment_methods[method] = {
# 				"transaction_count": 0,
# 				"transaction_amount": 0,
# 				"sales_amount": 0,
# 				"returns_amount": 0
# 			}

# 	for invoice in invoices:
# 		# Get payment method from payments data
# 		payment_info = invoice_payments.get(invoice.name, {})
# 		method = payment_info.get("payment_method", "Tiền mặt - POS")
# 		amount = invoice.grand_total or 0

# 		# Validate payment method if validation list provided
# 		if valid_payment_methods and method not in valid_payment_methods:
# 			log.warning(f"[PAYMENT_SUMMARY] Skipping invalid payment method '{method}' for invoice {invoice.name}")
# 			continue

# 		# Initialize method if not exists
# 		if method not in payment_methods:
# 			payment_methods[method] = {
# 				"transaction_count": 0,
# 				"transaction_amount": 0,
# 				"sales_amount": 0,
# 				"returns_amount": 0
# 			}

# 		payment_methods[method]["transaction_count"] += 1

# 		if invoice.is_return:
# 			payment_methods[method]["returns_amount"] += abs(amount)
# 			payment_methods[method]["transaction_amount"] -= abs(amount)
# 		else:
# 			payment_methods[method]["sales_amount"] += amount
# 			payment_methods[method]["transaction_amount"] += amount

# 	return payment_methods


# def _parse_json_safe(json_string, default=None):
# 	"""Safely parse JSON string"""
# 	if not json_string:
# 		return default or {}

# 	try:
# 		return frappe.parse_json(json_string)
# 	except:
# 		log.warning(f"[PAYMENT_SUMMARY] Could not parse JSON: {json_string[:50]}...")
# 		return default or {}


# def _compose_datetime(date_part, time_part):
# 	"""Compose datetime from date and time parts with proper handling"""
# 	try:
# 		if not date_part:
# 			return None

# 		if time_part:
# 			# Combine date and time
# 			from frappe.utils import get_datetime
# 			return get_datetime(f"{date_part} {time_part}")
# 		else:
# 			# Use date only
# 			from frappe.utils import getdate
# 			return getdate(date_part)
# 	except Exception as e:
# 		log.warning(f"[PAYMENT_SUMMARY] Could not compose datetime from {date_part} {time_part}: {str(e)}")
# 		return None


# def _create_or_update_payment_summary(shift_report, method, data, opening_amounts, expected_closing):
# 	"""Create or update a single payment summary record"""
# 	try:
# 		# Defaults
# 		company = "NVL-DaiLoan"
# 		pos_profile = ""
# 		currency = "TWD"

# 		try:
# 			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
# 			if getattr(opening_shift, 'company', None):
# 				company = opening_shift.company
# 			if getattr(opening_shift, 'pos_profile', None):
# 				pos_profile = opening_shift.pos_profile

# 				# Lấy currency ưu tiên từ POS Profile
# 				try:
# 					cur = frappe.db.get_value("POS Profile", pos_profile, "currency")
# 					if cur:
# 						currency = cur
# 				except Exception as e:
# 					log.warning(f"[PAYMENT_SUMMARY] Cannot get currency from POS Profile: {str(e)}")
# 		except Exception as e:
# 			log.warning(f"[PAYMENT_SUMMARY] Cannot get company/pos_profile from opening shift: {str(e)}")

# 		shift_report_id = shift_report.shift_report_id

# 		log.info(f"[PAYMENT_SUMMARY] 🔍 Checking existing record for '{method}' in shift '{shift_report_id}' (profile='{pos_profile}')")

# 		existing = frappe.db.exists("POS Payment Summary", {
# 			"shift_report_id": shift_report_id,
# 			"payment_method": method,
# 			"pos_shift_report": shift_report.name,
# 			"pos_profile": pos_profile  # 🔒 thêm điều kiện pos_profile
# 		})

# 		opening_amount = frappe.utils.flt(opening_amounts.get(method, 0), 2)
# 		transaction_amount = frappe.utils.flt(data["transaction_amount"], 2)
# 		closing_amount = frappe.utils.flt(opening_amount + transaction_amount, 2)

# 		shift_start_time = _compose_datetime(getattr(shift_report, "opening_date", None),
# 		                                     getattr(shift_report, "opening_time", None))
# 		shift_end_time   = _compose_datetime(getattr(shift_report, "closing_date", None),
# 		                                     getattr(shift_report, "closing_time", None))

# 		if existing:
# 			payment_summary = frappe.get_doc("POS Payment Summary", existing)

# 			old_count = payment_summary.transaction_count or 0
# 			old_amt = payment_summary.transaction_amount or 0

# 			payment_summary.transaction_count = data["transaction_count"]
# 			payment_summary.transaction_amount = transaction_amount
# 			payment_summary.closing_amount = closing_amount
# 			payment_summary.expected_closing_amount = expected_closing.get(method, 0)
# 			payment_summary.difference = frappe.utils.flt(closing_amount - payment_summary.expected_closing_amount, 2)
# 			payment_summary.save()

# 			log.info(f"[PAYMENT_SUMMARY] ♻️ Updated '{method}': Count {old_count}->{data['transaction_count']}, Amount {old_amt}->{transaction_amount}")
# 			created = False
# 		else:
# 			payment_summary = frappe.get_doc({
# 				"doctype": "POS Payment Summary",
# 				"shift_report_id": shift_report_id,
# 				"pos_shift_report": shift_report.name,
# 				"pos_opening_shift": shift_report.pos_opening_shift,
# 				"posting_date": getattr(shift_report, "opening_date", None),
# 				"shift_start_time": shift_start_time,
# 				"shift_end_time": shift_end_time,
# 				"payment_method": method,
# 				"payment_method_type": get_payment_method_type(method),
# 				"currency": currency,
# 				"transaction_count": data["transaction_count"],
# 				"company": company,
# 				"pos_profile": pos_profile,
# 				"opening_amount": opening_amount,
# 				"transaction_amount": transaction_amount,
# 				"expected_closing_amount": expected_closing.get(method, 0),
# 				"closing_amount": closing_amount,
# 				"notes": f"Auto-generated from shift report {shift_report.name}"
# 			})
# 			payment_summary.insert()
# 			log.info(f"[PAYMENT_SUMMARY] ✅ Created '{method}' as {payment_summary.name}")

# 			created = True

# 		summary = {
# 			"payment_method": method,
# 			"opening_amount": opening_amount,
# 			"transaction_amount": transaction_amount,
# 			"closing_amount": closing_amount,
# 			"transaction_count": data["transaction_count"],
# 			"sales_amount": data["sales_amount"],
# 			"returns_amount": data["returns_amount"]
# 		}
# 		return {"created": created, "summary": summary}

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error processing {method}: {str(e)}")
# 		return None


# @frappe.whitelist()
# def get_payment_summaries_for_shift(shift_report_name):
# 	"""
# 	Get payment summaries for a shift report

# 	Args:
# 		shift_report_name (str): Name of the POS Shift Report

# 	Returns:
# 		dict: Payment summaries data
# 	"""
# 	log.info(f"[PAYMENT_SUMMARY] Getting payment summaries for shift report: {shift_report_name}")

# 	try:
# 		# Get all payment summaries for this shift report
# 		payment_summaries = frappe.get_all("POS Payment Summary",
# 			filters={
# 				"pos_shift_report": shift_report_name
# 			},
# 			fields=[
# 				"name", "payment_method", "payment_method_type",
# 				"opening_amount", "transaction_amount", "closing_amount",
# 				"expected_closing_amount", "difference", "transaction_count",
# 				"currency", "posting_date"
# 			],
# 			order_by="payment_method"
# 		)

# 		log.info(f"[PAYMENT_SUMMARY] Found {len(payment_summaries)} payment summaries")

# 		return {
# 			"success": True,
# 			"data": payment_summaries
# 		}

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error getting payment summaries: {str(e)}")
# 		return {
# 			"success": False,
# 			"message": f"Error getting payment summaries: {str(e)}"
# 		}


# def get_valid_payment_methods_for_shift(shift_report):
# 	"""
# 	Get list of valid payment methods for a shift from POS Payment Summary

# 	Args:
# 		shift_report: POS Shift Report document

# 	Returns:
# 		list: List of valid payment method names
# 	"""
# 	try:
# 		payment_summaries = frappe.get_all("POS Payment Summary",
# 			filters={
# 				"shift_report_id": shift_report.shift_report_id,
# 				"pos_shift_report": shift_report.name
# 			},
# 			fields=["payment_method"]
# 		)

# 		valid_methods = [ps.payment_method for ps in payment_summaries]
# 		log.info(f"[PAYMENT_SUMMARY] Found {len(valid_methods)} valid payment methods: {valid_methods}")
# 		return valid_methods

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error getting valid payment methods: {str(e)}")
# 		return []


# def validate_payment_summary_consistency(shift_report):
# 	"""
# 	Validate that POS Payment Summary records match POS Opening Shift Detail records

# 	Args:
# 		shift_report: POS Shift Report document

# 	Raises:
# 		frappe.ValidationError: If consistency check fails
# 	"""
# 	try:
# 		# 1. Get opening shift details count
# 		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
# 		opening_details_count = len(opening_shift.balance_details or [])

# 		# 2. Get payment summaries count
# 		payment_summaries_count = frappe.db.count("POS Payment Summary", {
# 			"shift_report_id": shift_report.shift_report_id,
# 			"pos_shift_report": shift_report.name
# 		})

# 		# 3. Validate counts match
# 		if payment_summaries_count != opening_details_count:
# 			error_msg = f"Tính nhất quán dữ liệu bị vi phạm: {payment_summaries_count} payment summaries vs {opening_details_count} opening details"
# 			log.error(f"[PAYMENT_SUMMARY] {error_msg}")
# 			frappe.throw(error_msg)

# 		# 4. Validate payment methods match
# 		opening_methods = [d.mode_of_payment for d in opening_shift.balance_details or []]
# 		summary_methods = frappe.get_all("POS Payment Summary",
# 			filters={
# 				"shift_report_id": shift_report.shift_report_id,
# 				"pos_shift_report": shift_report.name
# 			},
# 			fields=["payment_method"]
# 		)
# 		summary_methods = [ps.payment_method for ps in summary_methods]

# 		if set(opening_methods) != set(summary_methods):
# 			error_msg = f"Payment methods không khớp: Opening={opening_methods}, Summary={summary_methods}"
# 			log.error(f"[PAYMENT_SUMMARY] {error_msg}")
# 			frappe.throw(error_msg)

# 		log.info(f"[PAYMENT_SUMMARY] ✅ Data consistency validated: {payment_summaries_count} records match")

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error validating consistency: {str(e)}")
# 		if "Tính nhất quán dữ liệu" not in str(e):
# 			frappe.throw(f"Lỗi validate tính nhất quán: {str(e)}")


# def get_payment_method_type(payment_method):
# 	"""
# 	Determine payment method type based on Mode of Payment doctype

# 	Args:
# 		payment_method (str): Payment method name

# 	Returns:
# 		str: Payment method type from Mode of Payment doctype, mapped to allowed values
# 	"""
# 	try:
# 		# Query Mode of Payment doctype to get the type
# 		mode_of_payment = frappe.get_all("Mode of Payment",
# 			filters={
# 				"mode_of_payment": payment_method,
# 				"enabled": 1
# 			},
# 			fields=["type"],
# 			limit=1
# 		)

# 		if mode_of_payment and mode_of_payment[0].get("type"):
# 			db_type = mode_of_payment[0]["type"]

# 			# Map database values to allowed values
# 			type_mapping = {
# 				"Cash": "Cash",
# 				"Bank": "Bank",
# 				"General": "General",
# 				"Mobile Payment": "Mobile Payment"
# 			}

# 			# Return mapped value or default to "Cash"
# 			mapped_type = type_mapping.get(db_type, "Cash")
# 			return mapped_type
# 		else:
# 			log.warning(f"[PAYMENT_SUMMARY] Payment method '{payment_method}' not found in Mode of Payment or has no type")
# 			return "Cash"

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error getting payment method type for '{payment_method}': {str(e)}")
# 		return "Cash"


# @frappe.whitelist()
# def initialize_payment_summaries_for_shift(shift_report_name):
# 	log.info(f"[PAYMENT_SUMMARY] Initializing payment summaries for shift report: {shift_report_name}")

# 	try:
# 		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)

# 		# Get company, pos_profile, and currency from opening shift
# 		company = "NVL-DaiLoan"
# 		pos_profile = ""
# 		currency = "TWD"

# 		try:
# 			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
# 			if getattr(opening_shift, 'company', None):
# 				company = opening_shift.company
# 			if getattr(opening_shift, 'pos_profile', None):
# 				pos_profile = opening_shift.pos_profile

# 				# Lấy currency ưu tiên từ POS Profile
# 				try:
# 					cur = frappe.db.get_value("POS Profile", pos_profile, "currency")
# 					if cur:
# 						currency = cur
# 				except Exception as e:
# 					log.warning(f"[PAYMENT_SUMMARY] Cannot get currency from POS Profile: {str(e)}")
# 		except Exception as e:
# 			log.warning(f"[PAYMENT_SUMMARY] Cannot get company/pos_profile from opening shift: {str(e)}")

# 		# Get opening amounts from POS Opening Shift Detail (balance_details)
# 		opening_amounts = {}
# 		try:
# 			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
# 			if hasattr(opening_shift, 'balance_details') and opening_shift.balance_details:
# 				for detail in opening_shift.balance_details:
# 					opening_amounts[detail.mode_of_payment] = detail.amount or 0
# 				log.info(f"[PAYMENT_SUMMARY] Loaded {len(opening_amounts)} opening amounts from POS Opening Shift Detail")
# 			else:
# 				log.warning(f"[PAYMENT_SUMMARY] No balance_details found in POS Opening Shift")
# 		except Exception as e:
# 			log.error(f"[PAYMENT_SUMMARY] Error loading opening amounts from POS Opening Shift Detail: {str(e)}")

# 		# Clean up existing records first to ensure fresh initialization
# 		log.info(f"[PAYMENT_SUMMARY] 🧹 Cleaning up existing POS Payment Summary records for shift: {shift_report.name}")
# 		try:
# 			existing_records = frappe.get_all("POS Payment Summary",
# 				filters={
# 					"shift_report_id": shift_report.shift_report_id,
# 					"pos_shift_report": shift_report.name
# 				},
# 				fields=["name", "payment_method"]
# 			)

# 			log.info(f"[PAYMENT_SUMMARY] 📊 Found {len(existing_records)} existing records to clean up")

# 			for record in existing_records:
# 				log.info(f"[PAYMENT_SUMMARY] 🗑️ Deleting existing record: {record.name} ({record.payment_method})")
# 				frappe.delete_doc("POS Payment Summary", record.name, ignore_permissions=True)

# 			if existing_records:
# 				log.info(f"[PAYMENT_SUMMARY] ✅ Successfully cleaned up {len(existing_records)} existing records")
# 			else:
# 				log.info(f"[PAYMENT_SUMMARY] ℹ️ No existing records found - fresh initialization")

# 		except Exception as e:
# 			log.warning(f"[PAYMENT_SUMMARY] ⚠️ Could not clean up existing records: {str(e)}")
# 			log.warning(f"[PAYMENT_SUMMARY] ⚠️ Continuing with initialization despite cleanup failure")

# 		# Create payment summary records for each payment method
# 		# ALWAYS CREATE FRESH RECORDS - Don't check existing for initialization
# 		created_count = 0
# 		for method, opening_amount in opening_amounts.items():
# 			try:
# 				# Create datetime values for shift times
# 				shift_start_time = _compose_datetime(getattr(shift_report, "opening_date", None),
# 				                                     getattr(shift_report, "opening_time", None))
# 				shift_end_time   = _compose_datetime(getattr(shift_report, "closing_date", None),
# 				                                     getattr(shift_report, "closing_time", None))

# 				opening_amount_flt = frappe.utils.flt(opening_amount, 2)
# 				log.info(f"[PAYMENT_SUMMARY] 🆕 Creating record for '{method}': Opening={opening_amount_flt}, Transaction=0, Closing={opening_amount_flt}")
# 				payment_summary = frappe.get_doc({
# 					"doctype": "POS Payment Summary",
# 					"shift_report_id": shift_report.shift_report_id,  # Sử dụng shift_report_id chung
# 					"pos_shift_report": shift_report.name,
# 					"pos_opening_shift": shift_report.pos_opening_shift,
# 					"posting_date": shift_report.opening_date,
# 					"shift_start_time": shift_start_time,
# 					"shift_end_time": shift_end_time,
# 					"payment_method": method,
# 					"payment_method_type": get_payment_method_type(method),
# 					"currency": currency,
# 					"company": company,
# 					"pos_profile": pos_profile,
# 					"opening_amount": opening_amount_flt,
# 					"transaction_amount": 0,
# 					"closing_amount": opening_amount_flt,
# 					"transaction_count": 0,
# 					"notes": f"Initialized for shift report {shift_report.name}"
# 				})

# 				payment_summary.insert(ignore_permissions=True)
# 				created_count += 1
# 				log.info(f"[PAYMENT_SUMMARY] ✅ Initialized payment summary for {method}")

# 			except Exception as e:
# 				log.error(f"[PAYMENT_SUMMARY] ❌ Error initializing payment summary for {method}: {str(e)}")
# 				continue

# 		log.info(f"[PAYMENT_SUMMARY] ✅ Initialized {created_count} payment summary records (fresh initialization)")

# 		return {
# 			"success": True,
# 			"message": f"Initialized {created_count} payment summary records",
# 			"data": {
# 				"initialized_count": created_count
# 			}
# 		}

# 	except Exception as e:
# 		log.error(f"[PAYMENT_SUMMARY] Error initializing payment summaries: {str(e)}")
# 		return {
# 			"success": False,
# 			"message": f"Error initializing payment summaries: {str(e)}"
# 		}

# -*- coding: utf-8 -*-
# Copyright (c) 2025, Youssef Restom
# For license information, please see license.txt

from __future__ import unicode_literals
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, cstr, flt

from posawesome.posawesome.utils.logging import get_logger

# --------------------------------------------------------------------
# Logger
# --------------------------------------------------------------------
log = get_logger("pos_payment_summary")

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _compose_datetime(date_val, time_val=None):
	"""Ghép Date + Time thành Datetime (local). Nếu thiếu time => 00:00:00."""
	if date_val and time_val:
		return get_datetime(f"{date_val} {time_val}")
	if date_val:
		return get_datetime(f"{date_val} 00:00:00")
	return None


def _norm_mop(name: str) -> str:
	"""Chuẩn hoá tên Mode of Payment để so sánh an toàn (strip, collapse space, casefold)."""
	s = cstr(name or "").strip()
	s = re.sub(r"\s+", " ", s)
	return s.casefold()


# --------------------------------------------------------------------
# DocType: POS Payment Summary
# --------------------------------------------------------------------
class POSPaymentSummary(Document):
	def validate(self):
		"""Validate POS Payment Summary."""
		self.validate_amounts()
		self.calculate_difference()

	def validate_amounts(self):
		"""Đảm bảo closing_amount = opening_amount + transaction_amount (chấp nhận lệch 0.01)."""
		expected_closing = flt(self.opening_amount, 2) + flt(self.transaction_amount, 2)
		if abs(flt(self.closing_amount, 2) - expected_closing) > 0.01:
			log.warning(
				f"[PAYMENT_SUMMARY] Closing mismatch for {self.payment_method} in shift {self.shift_report_id}: "
				f"{self.closing_amount} -> {expected_closing}"
			)
			self.closing_amount = expected_closing

	def calculate_difference(self):
		"""difference = closing_amount - expected_closing_amount."""
		if self.expected_closing_amount:
			self.difference = flt(self.closing_amount, 2) - flt(self.expected_closing_amount, 2)
		else:
			self.difference = 0.0


# --------------------------------------------------------------------
# Core API
# --------------------------------------------------------------------
@frappe.whitelist()
def create_payment_summaries_for_shift(shift_report_name):
	"""
	Tổng hợp POS Payment Summary cho một ca (Shift Report).
	- Lấy invoices theo POS Opening Shift
	- Tổng hợp theo MOP (support split-tender)
	- Khởi tạo đầy đủ MOP từ Opening Shift (nếu thiếu)
	- Upsert từng dòng summary
	- Validate tính nhất quán (tự bù thiếu, throw nếu thừa)
	"""
	log.info(f"[PAYMENT_SUMMARY] 🚀 START create summaries: {shift_report_name}")

	try:
		# STEP 1. Shift Report
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 1: Shift report: {shift_report.name} (ID: {shift_report.shift_report_id})")

		# STEP 2. Invoices (đã Submit)
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"posa_pos_opening_shift": shift_report.pos_opening_shift, "docstatus": 1},
			fields=["name", "grand_total", "is_return"]
		)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 2: Found {len(invoices)} invoices")

		# STEP 3. Valid MOP từ Opening Shift (source of truth)
		valid_payment_methods = get_valid_payment_methods_for_shift(shift_report)

		# STEP 4. Group & calc theo MOP (support split-tender)
		payment_data = _calculate_payment_methods(invoices, None, valid_payment_methods)
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 4: Grouped {len(payment_data)} method(s) from invoices")

		# STEP 5. Load opening amounts & expected closing
		opening_amounts = {}
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
			if getattr(opening_shift, "balance_details", None):
				for detail in opening_shift.balance_details:
					opening_amounts[detail.mode_of_payment] = flt(detail.amount or 0, 2)
			log.info(f"[PAYMENT_SUMMARY] ✅ STEP 5: Opening amounts loaded: {len(opening_amounts)} method(s)")
		except Exception as e:
			log.error(f"[PAYMENT_SUMMARY] ❌ STEP 5: Cannot load opening amounts: {str(e)}")

		expected_closing = _parse_json_safe(getattr(shift_report, "expected_closing_amounts", None), {}) or {}
		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 5: Expected closing: {len(expected_closing)} method(s)")

		# STEP 6. Bảo đảm đủ MOP từ Opening Shift (kể cả không có giao dịch)
		for mop in (valid_payment_methods or []):
			if mop not in payment_data:
				payment_data[mop] = {
					"transaction_count": 0,
					"transaction_amount": 0.0,
					"sales_amount": 0.0,
					"returns_amount": 0.0
				}

		# STEP 7. Upsert từng MOP
		payment_summaries = []
		created_count, updated_count, error_count = 0, 0, 0

		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 7: Upserting {len(payment_data)} method(s)")
		for method, data in sorted(payment_data.items(), key=lambda kv: kv[0]):
			try:
				result = _create_or_update_payment_summary(
					shift_report=shift_report,
					method=method,
					data=data,
					opening_amounts=opening_amounts,
					expected_closing=expected_closing
				)
				if not result:
					log.warning(f"[PAYMENT_SUMMARY] ⚠️ STEP 7: No result for '{method}'")
					error_count += 1
					continue

				if result.get("created"):
					created_count += 1
				else:
					updated_count += 1

				payment_summaries.append(result["summary"])
			except Exception as e:
				error_count += 1
				log.error(f"[PAYMENT_SUMMARY] ❌ STEP 7: Error upserting '{method}': {str(e)}")

		log.info(f"[PAYMENT_SUMMARY] ✅ STEP 7: Done. Created={created_count}, Updated={updated_count}, Error={error_count}")

		# STEP 8. Validate consistency (auto-bù thiếu, throw nếu thừa)
		log.info(f"[PAYMENT_SUMMARY] 📋 STEP 8: Validating consistency")
		validate_payment_summary_consistency(shift_report)

		# STEP 9. Commit (giữ lại vì nhiều nơi gọi qua client). Tuỳ dự án có thể bỏ.
		frappe.db.commit()
		log.info(f"[PAYMENT_SUMMARY] 💾 STEP 9: Committed")

		# STEP 10. Return
		log.info(f"[PAYMENT_SUMMARY] 🎉 COMPLETED for shift {shift_report_name}")
		return {
			"success": True,
			"message": f"Processed {len(payment_summaries)} payment method(s) with validation",
			"data": {
				"payment_summaries": payment_summaries,
				"created_count": created_count,
				"updated_count": updated_count,
				"failed_count": error_count,
				"total_methods": len(payment_summaries),
				"validation_passed": True
			}
		}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error: {str(e)}")
		return {"success": False, "message": f"Error creating payment summaries: {str(e)}"}


def _calculate_payment_methods(invoices, _invoice_payments_unused=None, valid_payment_methods=None):
	"""
	Tổng hợp tiền theo MOP với split-tender:
	- Batch fetch tất cả Sales Invoice Payment cho list invoices (tránh N+1).
	- Nếu invoice không có dòng payment: fallback 'Tiền mặt - POS' = grand_total.
	"""
	payment_methods = {}

	# Init trước các MOP hợp lệ để luôn có key
	if valid_payment_methods:
		for m in valid_payment_methods:
			payment_methods[m] = {
				"transaction_count": 0,
				"transaction_amount": 0.0,
				"sales_amount": 0.0,
				"returns_amount": 0.0
			}

	if not invoices:
		return payment_methods

	inv_names = [inv.name for inv in invoices]
	p_rows = frappe.get_all(
		"Sales Invoice Payment",
		filters={"parent": ["in", inv_names]},
		fields=["parent", "mode_of_payment", "amount"]
	)

	# index payments theo invoice
	pay_by_inv = {}
	for r in p_rows:
		pay_by_inv.setdefault(r.parent, []).append(r)

	for inv in invoices:
		rows = pay_by_inv.get(inv.name, [])
		if not rows:
			rows = [{"mode_of_payment": "Tiền mặt - POS", "amount": inv.grand_total or 0}]

		for r in rows:
			method = (r.get("mode_of_payment") or "Tiền mặt - POS")
			if valid_payment_methods and method not in valid_payment_methods:
				log.warning(f"[PAYMENT_SUMMARY] Skip invalid MOP '{method}' for invoice {inv.name}")
				continue

			amt = flt(r.get("amount") or 0, 2)

			if method not in payment_methods:
				payment_methods[method] = {
					"transaction_count": 0,
					"transaction_amount": 0.0,
					"sales_amount": 0.0,
					"returns_amount": 0.0
				}

			# đếm theo dòng payment (hợp lý cho split-tender)
			payment_methods[method]["transaction_count"] += 1

			if inv.is_return:
				payment_methods[method]["returns_amount"] += abs(amt)
				payment_methods[method]["transaction_amount"] -= abs(amt)
			else:
				payment_methods[method]["sales_amount"] += amt
				payment_methods[method]["transaction_amount"] += amt

	return payment_methods


def _parse_json_safe(json_string, default=None):
	"""Parse JSON an toàn."""
	if not json_string:
		return default or {}
	try:
		return frappe.parse_json(json_string)
	except Exception:
		log.warning(f"[PAYMENT_SUMMARY] Could not parse JSON: {cstr(json_string)[:80]}...")
		return default or {}


def _get_company_profile_currency(shift_report):
	"""
	Lấy (company, pos_profile, currency) theo thứ tự ưu tiên:
	- company, pos_profile từ Opening Shift nếu có
	- currency từ POS Profile -> Company.default_currency -> 'USD'
	"""
	company = None
	pos_profile = None
	currency = None

	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		company = getattr(opening_shift, "company", None)
		pos_profile = getattr(opening_shift, "pos_profile", None)
	except Exception as e:
		log.warning(f"[PAYMENT_SUMMARY] Cannot get company/pos_profile from opening shift: {str(e)}")

	if pos_profile:
		try:
			currency = frappe.db.get_value("POS Profile", pos_profile, "currency")
		except Exception:
			pass

	if not currency and company:
		try:
			currency = frappe.get_cached_value("Company", company, "default_currency")
		except Exception:
			pass

	return company or "NVL-DaiLoan", pos_profile or "", currency or "USD"


def _create_or_update_payment_summary(shift_report, method, data, opening_amounts, expected_closing):
	"""Upsert 1 dòng POS Payment Summary cho 1 phương thức thanh toán."""
	try:
		company, pos_profile, currency = _get_company_profile_currency(shift_report)
		shift_report_id = shift_report.shift_report_id

		existing = frappe.db.exists(
			"POS Payment Summary",
			{
				"shift_report_id": shift_report_id,
				"payment_method": method,
				"pos_shift_report": shift_report.name,
			},
		)

		opening_amount = flt(opening_amounts.get(method, 0), 2)
		transaction_amount = flt(data["transaction_amount"], 2)
		closing_amount = flt(opening_amount + transaction_amount, 2)

		shift_start_time = _compose_datetime(
			getattr(shift_report, "opening_date", None),
			getattr(shift_report, "opening_time", None),
		)
		shift_end_time = _compose_datetime(
			getattr(shift_report, "closing_date", None),
			getattr(shift_report, "closing_time", None),
		)

		if existing:
			# Update
			doc = frappe.get_doc("POS Payment Summary", existing)
			doc.transaction_count = data["transaction_count"]
			doc.transaction_amount = transaction_amount
			doc.closing_amount = closing_amount
			doc.expected_closing_amount = expected_closing.get(method, 0)
			doc.difference = flt(closing_amount - doc.expected_closing_amount, 2)
			doc.save()
			created = False
			log.info(f"[PAYMENT_SUMMARY] ♻️ Updated '{method}' -> {doc.name}")
		else:
			# Create
			doc = frappe.get_doc(
				{
					"doctype": "POS Payment Summary",
					"shift_report_id": shift_report_id,
					"pos_shift_report": shift_report.name,
					"pos_opening_shift": shift_report.pos_opening_shift,
					"posting_date": getattr(shift_report, "opening_date", None),
					"shift_start_time": shift_start_time,
					"shift_end_time": shift_end_time,
					"payment_method": method,
					"payment_method_type": get_payment_method_type(method),
					"currency": currency,
					"transaction_count": data["transaction_count"],
					"company": company,
					"pos_profile": pos_profile,
					"opening_amount": opening_amount,
					"transaction_amount": transaction_amount,
					"expected_closing_amount": expected_closing.get(method, 0),
					"closing_amount": closing_amount,
					"notes": f"Auto-generated from shift report {shift_report.name}",
				}
			)
			doc.insert()
			created = True
			log.info(f"[PAYMENT_SUMMARY] ✅ Created '{method}' -> {doc.name}")

		summary = {
			"payment_method": method,
			"opening_amount": opening_amount,
			"transaction_amount": transaction_amount,
			"closing_amount": closing_amount,
			"transaction_count": data["transaction_count"],
			"sales_amount": data["sales_amount"],
			"returns_amount": data["returns_amount"],
		}
		return {"created": created, "summary": summary}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error processing '{method}': {str(e)}")
		return None


@frappe.whitelist()
def get_payment_summaries_for_shift(shift_report_name):
	"""Trả về danh sách POS Payment Summary cho 1 Shift Report."""
	log.info(f"[PAYMENT_SUMMARY] Fetch summaries for: {shift_report_name}")
	try:
		rows = frappe.get_all(
			"POS Payment Summary",
			filters={"pos_shift_report": shift_report_name},
			fields=[
				"name",
				"payment_method",
				"payment_method_type",
				"opening_amount",
				"transaction_amount",
				"closing_amount",
				"expected_closing_amount",
				"difference",
				"transaction_count",
				"currency",
				"posting_date",
				"pos_profile",
			],
			order_by="payment_method",
		)
		return {"success": True, "data": rows}
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error getting summaries: {str(e)}")
		return {"success": False, "message": f"Error: {str(e)}"}


def get_valid_payment_methods_for_shift(shift_report):
	"""Đọc danh sách Mode of Payment từ POS Opening Shift (balance_details)."""
	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		methods = [d.mode_of_payment for d in (opening_shift.balance_details or [])]
		log.info(f"[PAYMENT_SUMMARY] Valid MOP (Opening Shift): {methods}")
		return methods
	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error reading valid MOPs: {str(e)}")
		return []


def validate_payment_summary_consistency(shift_report):
	"""
	Đảm bảo Summary khớp Opening Shift:
	- Thiếu MOP trong Summary => auto-add record rỗng (opening_amount có sẵn).
	- Thừa MOP trong Summary (không có ở Opening) => THROW để sửa cấu hình.
	- Sau khi auto-bù: số lượng phải 1:1.
	"""
	try:
		opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
		pos_profile = getattr(opening_shift, "pos_profile", None) or getattr(shift_report, "pos_profile", None)
		company = getattr(opening_shift, "company", None)

		# currency ưu tiên POS Profile -> Company -> USD
		currency = None
		if pos_profile:
			currency = frappe.db.get_value("POS Profile", pos_profile, "currency")
		if not currency and company:
			currency = frappe.get_cached_value("Company", company, "default_currency")
		currency = currency or "USD"

		# Opening methods map
		open_map = {}
		for d in (opening_shift.balance_details or []):
			open_map[_norm_mop(d.mode_of_payment)] = (d.mode_of_payment, flt(d.amount or 0, 2))
		open_set = set(open_map.keys())

		filters = {
			"shift_report_id": shift_report.shift_report_id,
			"pos_shift_report": shift_report.name,
		}

		summ_rows = frappe.get_all(
			"POS Payment Summary",
			filters=filters,
			fields=["name", "payment_method"],
		)
		sum_map = {}
		for r in summ_rows:
			sum_map.setdefault(_norm_mop(r.payment_method), []).append(r.name)
		sum_set = set(sum_map.keys())

		missing = open_set - sum_set
		extra = sum_set - open_set

		# Auto-add missing with zero tx
		if missing:
			shift_start_time = _compose_datetime(getattr(shift_report, "opening_date", None), getattr(shift_report, "opening_time", None))
			shift_end_time = _compose_datetime(getattr(shift_report, "closing_date", None), getattr(shift_report, "closing_time", None))

			for norm in missing:
				orig, opening_amt = open_map[norm]
				try:
					doc = frappe.get_doc(
						{
							"doctype": "POS Payment Summary",
							"shift_report_id": shift_report.shift_report_id,
							"pos_shift_report": shift_report.name,
							"pos_opening_shift": shift_report.pos_opening_shift,
							"posting_date": getattr(shift_report, "opening_date", None),
							"shift_start_time": shift_start_time,
							"shift_end_time": shift_end_time,
							"payment_method": orig,
							"payment_method_type": get_payment_method_type(orig),
							"currency": currency,
							"company": company,
							"pos_profile": pos_profile,
							"opening_amount": opening_amt,
							"transaction_amount": 0.0,
							"closing_amount": opening_amt,
							"transaction_count": 0,
							"notes": f"Auto-added to ensure consistency for shift {shift_report.name}",
						}
					)
					doc.insert(ignore_permissions=True)
					log.info(f"[PAYMENT_SUMMARY] ➕ Auto-added missing MOP '{orig}'")
				except Exception as ie:
					log.error(f"[PAYMENT_SUMMARY] ❌ Cannot auto-add '{orig}': {str(ie)}")

		# Throw if extra exists
		if extra:
			readable = []
			for norm in extra:
				sample = (sum_map.get(norm) or [None])[0]
				mop = frappe.db.get_value("POS Payment Summary", sample, "payment_method") if sample else "(unknown)"
				readable.append(mop or "(unknown)")
			msg = f"Payment methods không khớp: Summary có phương thức không có ở Opening Shift: {readable}"
			log.error(f"[PAYMENT_SUMMARY] {msg}")
			frappe.throw(msg)

		# Recount after auto-bù
		count_sum = frappe.db.count("POS Payment Summary", filters)
		count_open = len(open_map)
		if count_sum != count_open:
			err = f"Tính nhất quán dữ liệu bị vi phạm: {count_sum} payment summaries vs {count_open} opening details"
			log.error(f"[PAYMENT_SUMMARY] {err}")
			frappe.throw(err)

		log.info(f"[PAYMENT_SUMMARY] ✅ Consistency OK: {count_sum} == {count_open}")

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Lỗi validate tính nhất quán: {str(e)}")
		raise


def _resolve_allowed_payment_types():
	"""Đọc danh sách payment method types cho phép từ DocType definition."""
	try:
		df = frappe.get_meta("POS Payment Summary").get_field("payment_method_type")
		raw = (df.options or "").split("\n")
		return [o.strip() for o in raw if o and o.strip()]
	except Exception as e:
		log.warning(f"[PAYMENT_SUMMARY] Cannot read field options for payment_method_type: {str(e)}")
		return ["Tiền mặt", "Card", "Digital", "Khác"]


def get_payment_method_type(payment_method):
	"""
	Smart mapping từ Mode of Payment type sang allowed values.
	Hỗ trợ multi-language và comprehensive fallbacks.
	"""
	allowed = _resolve_allowed_payment_types()
	allowed_set = set(allowed)

	def pick(*cands):
		"""Pick first candidate available in allowed set."""
		for c in cands:
			if c in allowed_set:
				return c
		return allowed[0] if allowed else "Tiền mặt"

	try:
		db_type = (frappe.db.get_value("Mode of Payment", payment_method, "type") or "").strip().casefold()

		if db_type in ("cash", "tiền mặt"):
			return pick("Tiền mặt", "Cash")

		if db_type in ("bank", "mobile payment", "wallet", "upi", "qr"):
			return pick("Bank", "Mobile Payment", "Digital")

		if db_type in ("card", "credit card", "debit card"):
			return pick("Card", "Bank")

		if db_type in ("general", "other", "khác"):
			return pick("Khác", "General")

		# Fallback for unrecognized types
		return pick("Khác", "General", "Tiền mặt")

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error getting type for '{payment_method}': {str(e)}")
		return pick("Tiền mặt", "Cash", "Khác")


@frappe.whitelist()
def initialize_payment_summaries_for_shift(shift_report_name):
	"""
	Khởi tạo "rỗng" toàn bộ POS Payment Summary theo Opening Shift (1:1 phương thức).
	- Xoá sạch record cũ của shift này (an toàn vì chỉ là bảng tổng hợp).
	- Tạo mới mỗi MOP với opening_amount & closing_amount = opening_amount.
	"""
	log.info(f"[PAYMENT_SUMMARY] Init summaries for: {shift_report_name}")
	try:
		shift_report = frappe.get_doc("POS Shift Report", shift_report_name)
		company, pos_profile, currency = _get_company_profile_currency(shift_report)

		# Opening amounts
		opening_amounts = {}
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", shift_report.pos_opening_shift)
			if getattr(opening_shift, "balance_details", None):
				for d in opening_shift.balance_details:
					opening_amounts[d.mode_of_payment] = flt(d.amount or 0, 2)
		except Exception as e:
			log.error(f"[PAYMENT_SUMMARY] Cannot read opening amounts: {str(e)}")

		# Cleanup old
		existing = frappe.get_all(
			"POS Payment Summary",
			filters={"shift_report_id": shift_report.shift_report_id, "pos_shift_report": shift_report.name},
			fields=["name", "payment_method"],
		)
		for row in existing:
			try:
				frappe.delete_doc("POS Payment Summary", row.name, ignore_permissions=True)
			except Exception as de:
				log.warning(f"[PAYMENT_SUMMARY] Cannot delete {row.name}: {str(de)}")

		# Create fresh
		created = 0
		shift_start_time = _compose_datetime(getattr(shift_report, "opening_date", None), getattr(shift_report, "opening_time", None))
		shift_end_time = _compose_datetime(getattr(shift_report, "closing_date", None), getattr(shift_report, "closing_time", None))

		for method, opening_amount in opening_amounts.items():
			try:
				doc = frappe.get_doc(
					{
						"doctype": "POS Payment Summary",
						"shift_report_id": shift_report.shift_report_id,
						"pos_shift_report": shift_report.name,
						"pos_opening_shift": shift_report.pos_opening_shift,
						"posting_date": getattr(shift_report, "opening_date", None),
						"shift_start_time": shift_start_time,
						"shift_end_time": shift_end_time,
						"payment_method": method,
						"payment_method_type": get_payment_method_type(method),
						"currency": currency,
						"company": company,
						"pos_profile": pos_profile,
						"opening_amount": opening_amount,
						"transaction_amount": 0.0,
						"closing_amount": opening_amount,
						"transaction_count": 0,
						"notes": f"Initialized for shift report {shift_report.name}",
					}
				)
				doc.insert(ignore_permissions=True)
				created += 1
			except Exception as ce:
				log.error(f"[PAYMENT_SUMMARY] Cannot init '{method}': {str(ce)}")

		log.info(f"[PAYMENT_SUMMARY] ✅ Initialized {created} record(s)")
		return {"success": True, "message": f"Initialized {created} records", "data": {"initialized_count": created}}

	except Exception as e:
		log.error(f"[PAYMENT_SUMMARY] Error initializing: {str(e)}")
		return {"success": False, "message": f"Error initializing: {str(e)}"}
