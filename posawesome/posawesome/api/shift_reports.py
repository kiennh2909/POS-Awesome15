import frappe
from frappe import _
from frappe.utils import nowdate, nowtime
import json
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("shift_reports")

@frappe.whitelist()
def create_shift_report(data):
	"""
	Create a new POS Shift Report

	Args:
		data (dict): Shift report data including:
			- pos_opening_shift: Opening shift name
			- opening_amounts: JSON string of opening amounts
			- shift_report_id: Optional custom ID

	Returns:
		dict: Created shift report data
	"""
	try:
		# Validate required fields
		if not data.get("pos_opening_shift"):
			frappe.throw(_("POS Opening Shift is required"))

		if not frappe.db.exists("POS Opening Shift", data.get("pos_opening_shift")):
			frappe.throw(_("POS Opening Shift not found"))

		# Check if shift report already exists
		existing = frappe.db.exists("POS Shift Report",
			{"pos_opening_shift": data.get("pos_opening_shift")}
		)
		if existing:
			frappe.throw(_("Shift report already exists for this opening shift"))

		# Get opening shift data
		opening_shift = frappe.get_doc("POS Opening Shift", data.get("pos_opening_shift"))

		# Create shift report
		shift_report = frappe.get_doc({
			"doctype": "POS Shift Report",
			"shift_report_id": data.get("shift_report_id") or f"SHIFT-{opening_shift.name}",
			"pos_opening_shift": opening_shift.name,
			"opening_date": opening_shift.posting_date,
			"opening_time": opening_shift.posting_time,
			"opened_by": opening_shift.owner,
			"opening_amounts": data.get("opening_amounts", "{}"),
			"status": "Open"
		})

		shift_report.insert()

		return {
			"success": True,
			"message": _("Shift report created successfully"),
			"data": {
				"name": shift_report.name,
				"shift_report_id": shift_report.shift_report_id,
				"status": shift_report.status
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Create Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_shift_report(shift_report_id):
	"""
	Get POS Shift Report by ID or shift_report_id field

	Args:
		shift_report_id (str): Shift report ID, shift_report_id field, or name

	Returns:
		dict: Shift report data (compatible with frappe.client.get format)
	"""
	log.info(f"[SHIFT_REPORT_API] 🎯 GET_SHIFT_REPORT - Start - Shift Report ID - THAM SO : {shift_report_id}")
	log.info(f"[SHIFT_REPORT_API] 📋 GET_SHIFT_REPORT - ID Type: {type(shift_report_id)}")

	# ✅ HANDLE JSON STRING OBJECT (Vue component sends object as JSON string)
	if isinstance(shift_report_id, str) and shift_report_id.startswith('{'):
		log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - Detected JSON string object, parsing...")

		try:
			parsed_obj = json.loads(shift_report_id)
			log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Parsed object successfully: {parsed_obj}")

			# Extract actual shift report ID from parsed object
			# Priority order: shift_report > shift_report_id > name > any string field
			if 'shift_report' in parsed_obj and parsed_obj['shift_report']:
				shift_report_id = parsed_obj['shift_report']
				log.info(f"[SHIFT_REPORT_API] 🎯 GET_SHIFT_REPORT - Extracted shift_report ID: {shift_report_id}")
			elif 'shift_report_id' in parsed_obj and parsed_obj['shift_report_id']:
				shift_report_id = parsed_obj['shift_report_id']
				log.info(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Extracted shift_report_id: {shift_report_id}")
			elif 'name' in parsed_obj and parsed_obj['name']:
				shift_report_id = parsed_obj['name']
				log.info(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Extracted name: {shift_report_id}")
			else:
				# Try to find any string field that might be the ID
				for key, value in parsed_obj.items():
					if isinstance(value, str) and value and len(value.strip()) > 0:
						shift_report_id = value.strip()
						log.info(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Extracted from field '{key}': {shift_report_id}")
						break
				else:
					log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - No valid ID found in parsed object: {parsed_obj}")
					frappe.throw(_("Invalid shift report ID format - no valid ID field found"))
		except json.JSONDecodeError as e:
			log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to parse JSON: {str(e)}")
			log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Original string: {shift_report_id}")
			frappe.throw(_("Invalid shift report ID format - JSON parsing failed"))
	if isinstance(shift_report_id, str):
		log.info(f"[SHIFT_REPORT_API]  GET_SHIFT_REPORT - Final ID Length: {len(shift_report_id)}")

	# ✅ HANDLE POS OPENING SHIFT OBJECT (when Vue component sends full object)
	if isinstance(shift_report_id, str) and not shift_report_id.startswith('{'):
		# Check if this is a POS Opening Shift ID that needs auto-creation
		if frappe.db.exists("POS Shift Report", shift_report_id):
			log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Found existing shift report: {shift_report_id}")
			shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
		else:
			# Check if it's a POS Opening Shift
			if frappe.db.exists("POS Opening Shift", shift_report_id):
				log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - POS Opening Shift detected, checking references: {shift_report_id}")
				opening_shift = frappe.get_doc("POS Opening Shift", shift_report_id)

				# Check both shift_report and shift_report_id fields
				has_shift_report_ref = hasattr(opening_shift, 'shift_report') and opening_shift.shift_report
				has_shift_report_id = hasattr(opening_shift, 'shift_report_id') and opening_shift.shift_report_id

				if has_shift_report_ref and has_shift_report_id:
					# Both references exist - check if shift report actually exists
					if frappe.db.exists("POS Shift Report", opening_shift.shift_report):
						log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Found existing shift report: {opening_shift.shift_report}")
						shift_report = frappe.get_doc("POS Shift Report", opening_shift.shift_report)
					else:
						# Data inconsistency - clean up and auto-create
						log.warning(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Data inconsistency detected: referenced shift report {opening_shift.shift_report} doesn't exist")
						log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - Cleaning up invalid references and auto-creating new shift report")

						# Clean up invalid references
						frappe.db.set_value("POS Opening Shift", opening_shift.name, {
							"shift_report": "",
							"shift_report_id": ""
						})

						# Auto-create new shift report
						try:
							create_result = create_shift_report({
								"pos_opening_shift": opening_shift.name,
								"opening_amounts": "{}"
							})

							if create_result.get("success"):
								new_shift_report_name = create_result["data"]["name"]
								new_shift_report_id = create_result["data"]["shift_report_id"]
								log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Auto-created shift report: {new_shift_report_name} (ID: {new_shift_report_id})")

								# Update opening shift with new references
								frappe.db.set_value("POS Opening Shift", opening_shift.name, {
									"shift_report": new_shift_report_name,
									"shift_report_id": new_shift_report_id
								})

								shift_report = frappe.get_doc("POS Shift Report", new_shift_report_name)
							else:
								log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to auto-create: {create_result.get('message')}")
								frappe.throw(_("Failed to create shift report automatically."))
						except Exception as e:
							log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Error auto-creating: {str(e)}")
							frappe.throw(_("Error creating shift report automatically."))
				elif has_shift_report_ref or has_shift_report_id:
					# Partial reference exists - clean up and auto-create
					log.warning(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Partial inconsistency: incomplete shift report references")
					log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - Cleaning up partial references and auto-creating shift report")

					# Clean up partial references
					frappe.db.set_value("POS Opening Shift", opening_shift.name, {
						"shift_report": "",
						"shift_report_id": ""
					})

					# Auto-create shift report
					try:
						create_result = create_shift_report({
							"pos_opening_shift": opening_shift.name,
							"opening_amounts": "{}"
						})

						if create_result.get("success"):
							new_shift_report_name = create_result["data"]["name"]
							new_shift_report_id = create_result["data"]["shift_report_id"]
							log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Auto-created shift report: {new_shift_report_name} (ID: {new_shift_report_id})")

							# Update opening shift with new references
							frappe.db.set_value("POS Opening Shift", opening_shift.name, {
								"shift_report": new_shift_report_name,
								"shift_report_id": new_shift_report_id
							})

							shift_report = frappe.get_doc("POS Shift Report", new_shift_report_name)
						else:
							log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to auto-create: {create_result.get('message')}")
							frappe.throw(_("Failed to create shift report automatically."))
					except Exception as e:
						log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Error auto-creating: {str(e)}")
						frappe.throw(_("Error creating shift report automatically."))
				else:
					# No references exist - auto-create shift report
					log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - No references found, auto-creating shift report for: {shift_report_id}")
					try:
						create_result = create_shift_report({
							"pos_opening_shift": opening_shift.name,
							"opening_amounts": "{}"
						})

						if create_result.get("success"):
							new_shift_report_name = create_result["data"]["name"]
							new_shift_report_id = create_result["data"]["shift_report_id"]
							log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Auto-created shift report: {new_shift_report_name} (ID: {new_shift_report_id})")

							# Update opening shift with both references
							frappe.db.set_value("POS Opening Shift", opening_shift.name, {
								"shift_report": new_shift_report_name,
								"shift_report_id": new_shift_report_id
							})

							shift_report = frappe.get_doc("POS Shift Report", new_shift_report_name)
						else:
							log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to auto-create: {create_result.get('message')}")
							frappe.throw(_("Failed to create shift report automatically."))

					except Exception as e:
						log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Error auto-creating: {str(e)}")
						frappe.throw(_("Error creating shift report automatically."))
			else:
				log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Not a valid shift report or opening shift ID: {shift_report_id}")
				frappe.throw(_("Shift report not found"))

	try:
		# First try direct name lookup
		log.info(f"[SHIFT_REPORT_API] 🔍 GET_SHIFT_REPORT - Trying direct name lookup: {shift_report_id}")
		if frappe.db.exists("POS Shift Report", shift_report_id):
			log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Found by direct name: {shift_report_id}")
			shift_report = frappe.get_doc("POS Shift Report", shift_report_id)
		else:
			# Try to find by shift_report_id field
			log.info(f"[SHIFT_REPORT_API] 🔍 GET_SHIFT_REPORT - Direct lookup failed, trying shift_report_id field: {shift_report_id}")
			shift_reports = frappe.get_all("POS Shift Report",
				filters={"shift_report_id": shift_report_id},
				fields=["name"],
				limit=1
			)

			if shift_reports:
				log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Found by shift_report_id field: {shift_reports[0].name}")
				shift_report = frappe.get_doc("POS Shift Report", shift_reports[0].name)
			else:
				# ✅ CHECK IF THIS IS A POS OPENING SHIFT THAT SHOULD HAVE A SHIFT REPORT
				log.info(f"[SHIFT_REPORT_API] 🔍 GET_SHIFT_REPORT - Not found, checking if it's a POS Opening Shift: {shift_report_id}")
				if frappe.db.exists("POS Opening Shift", shift_report_id):
					log.info(f"[SHIFT_REPORT_API] 📋 GET_SHIFT_REPORT - Found POS Opening Shift: {shift_report_id}")
					opening_shift = frappe.get_doc("POS Opening Shift", shift_report_id)

					# Check if opening shift has shift_report and shift_report_id fields set
					has_shift_report_ref = hasattr(opening_shift, 'shift_report') and opening_shift.shift_report
					has_shift_report_id = hasattr(opening_shift, 'shift_report_id') and opening_shift.shift_report_id

					if has_shift_report_ref and has_shift_report_id:
						# Opening shift has both references - check if shift report actually exists
						if frappe.db.exists("POS Shift Report", opening_shift.shift_report):
							log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Found existing shift report: {opening_shift.shift_report}")
							shift_report = frappe.get_doc("POS Shift Report", opening_shift.shift_report)
						else:
							# Data inconsistency - shift report reference exists but shift report doesn't exist
							log.warning(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Data inconsistency detected: POS Opening Shift {shift_report_id} references non-existent shift report {opening_shift.shift_report}")
							log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - Cleaning up invalid references and auto-creating new shift report")

							# Clean up invalid references
							frappe.db.set_value("POS Opening Shift", opening_shift.name, {
								"shift_report": "",
								"shift_report_id": ""
							})

							# Auto-create new shift report
							try:
								create_result = create_shift_report({
									"pos_opening_shift": opening_shift.name,
									"opening_amounts": "{}"
								})

								if create_result.get("success"):
									new_shift_report_name = create_result["data"]["name"]
									new_shift_report_id = create_result["data"]["shift_report_id"]
									log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Auto-created shift report: {new_shift_report_name} (ID: {new_shift_report_id})")

									# Update opening shift with new references
									frappe.db.set_value("POS Opening Shift", opening_shift.name, {
										"shift_report": new_shift_report_name,
										"shift_report_id": new_shift_report_id
									})

									shift_report = frappe.get_doc("POS Shift Report", new_shift_report_name)
								else:
									log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to auto-create shift report: {create_result.get('message')}")
									frappe.throw(_("Failed to create shift report automatically. Please contact administrator."))
							except Exception as create_error:
								log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Error auto-creating shift report: {str(create_error)}")
								frappe.throw(_("Error creating shift report automatically. Please contact administrator."))
					elif has_shift_report_ref or has_shift_report_id:
						# Partial reference exists - clean up and auto-create
						log.warning(f"[SHIFT_REPORT_API] ⚠️ GET_SHIFT_REPORT - Partial data inconsistency: POS Opening Shift {shift_report_id} has incomplete shift report references")
						log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - Cleaning up partial references and auto-creating shift report")

						# Clean up partial references
						frappe.db.set_value("POS Opening Shift", opening_shift.name, {
							"shift_report": "",
							"shift_report_id": ""
						})

						# Auto-create shift report
						try:
							create_result = create_shift_report({
								"pos_opening_shift": opening_shift.name,
								"opening_amounts": "{}"
							})

							if create_result.get("success"):
								new_shift_report_name = create_result["data"]["name"]
								new_shift_report_id = create_result["data"]["shift_report_id"]
								log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Auto-created shift report: {new_shift_report_name} (ID: {new_shift_report_id})")

								# Update opening shift with new references
								frappe.db.set_value("POS Opening Shift", opening_shift.name, {
									"shift_report": new_shift_report_name,
									"shift_report_id": new_shift_report_id
								})

								shift_report = frappe.get_doc("POS Shift Report", new_shift_report_name)
							else:
								log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to auto-create shift report: {create_result.get('message')}")
								frappe.throw(_("Failed to create shift report automatically. Please contact administrator."))
						except Exception as create_error:
							log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Error auto-creating shift report: {str(create_error)}")
							frappe.throw(_("Error creating shift report automatically. Please contact administrator."))
					else:
						# Opening shift exists but no shift_report references
						# Auto-create shift report for this opening shift
						log.info(f"[SHIFT_REPORT_API] 🔄 GET_SHIFT_REPORT - Auto-creating shift report for opening shift: {shift_report_id}")

						try:
							# Create shift report automatically
							create_result = create_shift_report({
								"pos_opening_shift": opening_shift.name,
								"opening_amounts": "{}"  # Default empty amounts
							})

							if create_result.get("success"):
								new_shift_report_name = create_result["data"]["name"]
								new_shift_report_id = create_result["data"]["shift_report_id"]
								log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - Auto-created shift report: {new_shift_report_name} (ID: {new_shift_report_id})")

								# Update opening shift with shift_report references
								frappe.db.set_value("POS Opening Shift", opening_shift.name, {
									"shift_report": new_shift_report_name,
									"shift_report_id": new_shift_report_id
								})

								# Get the newly created shift report
								shift_report = frappe.get_doc("POS Shift Report", new_shift_report_name)
							else:
								log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Failed to auto-create shift report: {create_result.get('message')}")
								frappe.throw(_("Failed to create shift report automatically. Please contact administrator."))

						except Exception as create_error:
							log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Error auto-creating shift report: {str(create_error)}")
							frappe.throw(_("Error creating shift report automatically. Please contact administrator."))
				else:
					# Not a POS Opening Shift name
					log.error(f"[SHIFT_REPORT_API] ❌ GET_SHIFT_REPORT - Shift report not found: {shift_report_id}")
					frappe.throw(_("Shift report not found"))

		# ✅ RETURN FORMAT COMPATIBLE WITH frappe.client.get
		# Vue component expects: shiftReportResponse.message (direct data)
		log.info(f"[SHIFT_REPORT_API] 📊 GET_SHIFT_REPORT - Preparing response data for: {shift_report.name}")
		log.info(f"[SHIFT_REPORT_API] 📈 GET_SHIFT_REPORT - Summary: Count={shift_report.invoice_count}, Sales={shift_report.total_sales}, Returns={shift_report.total_returns}")

		response_data = {
			"name": shift_report.name,
			"shift_report_id": shift_report.shift_report_id,
			"pos_opening_shift": shift_report.pos_opening_shift,
			"opening_date": shift_report.opening_date,
			"opening_time": shift_report.opening_time,
			"opened_by": shift_report.opened_by,
			"opening_amounts": json.loads(shift_report.opening_amounts or "{}"),
			"expected_closing_amounts": json.loads(shift_report.expected_closing_amounts or "{}"),
			"actual_closing_amounts": json.loads(shift_report.actual_closing_amounts or "{}"),
			"total_opening_amount": shift_report.total_opening_amount,
			"total_expected_closing": shift_report.total_expected_closing,
			"total_actual_closing": shift_report.total_actual_closing,
			"difference": shift_report.difference,
			"verification_status": shift_report.verification_status,
			"verification_date": shift_report.verification_date,
			"verified_by": shift_report.verified_by,
			"confirmation_date": shift_report.confirmation_date,
			"confirmed_by": shift_report.confirmed_by,
			"closing_date": shift_report.closing_date,
			"closed_by": shift_report.closed_by,
			"status": shift_report.status,
			"invoice_count": shift_report.invoice_count,
			"total_sales": shift_report.total_sales,
			"total_returns": shift_report.total_returns,
			"payment_breakdown": json.loads(shift_report.payment_breakdown or "{}"),
			"notes": shift_report.notes,
			"invoices": [
				{
					"invoice_no": invoice.invoice_no,
					"invoice_date": invoice.invoice_date,
					"invoice_time": invoice.invoice_time,
					"customer": invoice.customer,
					"total_amount": invoice.total_amount,
					"paid_amount": invoice.paid_amount,
					"tax_amount": invoice.tax_amount,
					"payment_method": invoice.payment_method,
					"is_return": invoice.is_return,
					"status": invoice.status
				} for invoice in shift_report.invoices
			] if shift_report.invoices else []
		}

		log.info(f"[SHIFT_REPORT_API] ✅ GET_SHIFT_REPORT - COMPLETED - Shift Report: {shift_report.name}, Invoices: {len(response_data['invoices'])}")
		return response_data

	except Exception as e:
		log.error(f"[SHIFT_REPORT_API] 💥 GET_SHIFT_REPORT - FAILED - Shift Report ID: {shift_report_id}, Error: {str(e)}")
		frappe.log_error(str(e), "Get Shift Report Error")
		# ✅ RETURN ERROR IN COMPATIBLE FORMAT
		frappe.throw(_("Error getting shift report: {0}").format(str(e)))

@frappe.whitelist()
def update_shift_report(shift_report_id, data):
	"""
	Update POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name
		data (dict): Updated data

	Returns:
		dict: Update result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Update allowed fields
		allowed_fields = [
			"expected_closing_amounts", "actual_closing_amounts",
			"verification_status", "notes"
		]

		for field in allowed_fields:
			if field in data:
				setattr(shift_report, field, data[field])

		shift_report.save()

		return {
			"success": True,
			"message": _("Shift report updated successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Update Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def delete_shift_report(shift_report_id):
	"""
	Delete POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Delete result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Only allow deletion of open reports
		if shift_report.status != "Open":
			frappe.throw(_("Cannot delete closed or submitted shift reports"))

		shift_report.delete()

		return {
			"success": True,
			"message": _("Shift report deleted successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Delete Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_footer_status_data():
	"""
	Get data for footer status bar
	Returns cashier info, shift report summary, and sales totals
	"""
	try:
		user = frappe.session.user
		current_time = frappe.utils.now_datetime()

		# Get current opening shift for user
		active_shift = frappe.get_all(
			"POS Opening Shift",
			filters={
				"owner": user,
				"docstatus": 1,
				"status": "Open"
			},
			fields=["name", "shift_report", "shift_report_id"],
			limit=1
		)

		# Get currency from POS Profile
		currency = "VND"  # Default
		if active_shift:
			try:
				opening_shift = frappe.get_doc("POS Opening Shift", active_shift[0].name)
				if opening_shift.pos_profile:
					pos_profile = frappe.get_doc("POS Profile", opening_shift.pos_profile)
					if pos_profile.currency:
						currency = pos_profile.currency
			except Exception as e:
				frappe.logger().warning(f"Could not get currency from POS Profile: {str(e)}")

		# Initialize result with default values
		result = {
			"cashier_name": frappe.session.user_fullname or frappe.session.user,
			"current_date": current_time.strftime("%Y-%m-%d"),
			"current_time": current_time.strftime("%H:%M:%S"),
			"currency": currency,  # Add currency to result
			"shift_report_id": "",
			"total_invoices": 0,
			"total_revenue": 0,
			"cash_balance": 0,
			"today_sales": 0,
			"last_invoice": ""
		}

		if not active_shift:
			# No active shift, return basic info
			return {
				"success": True,
				"data": result
			}

		shift_data = active_shift[0]
		result["shift_report_id"] = shift_data.shift_report_id or ""

		# Get shift report data if exists
		if shift_data.shift_report:
			shift_report = frappe.get_doc("POS Shift Report", shift_data.shift_report)
			result.update({
				"total_invoices": shift_report.invoice_count or 0,
				"total_revenue": (shift_report.total_sales or 0) - (shift_report.total_returns or 0),
				"today_sales": shift_report.total_sales or 0,  # Today's sales from shift report
			})

			# Get last invoice from shift report
			if shift_report.invoices and len(shift_report.invoices) > 0:
				last_invoice_data = shift_report.invoices[-1]
				result["last_invoice"] = last_invoice_data.invoice_no or ""

		# Calculate cash balance from paid invoices in current shift
		# Cash Balance = Total amount paid by "Tiền mặt - POS" in Sales Invoice Payment table
		if shift_data.shift_report:
			shift_report = frappe.get_doc("POS Shift Report", shift_data.shift_report)

			total_cash_balance = 0

			# Get all paid invoices from shift report
			if shift_report.invoices:
				for invoice_entry in shift_report.invoices:
					if invoice_entry.status == "Paid":
						# Get the actual Sales Invoice document
						try:
							invoice_doc = frappe.get_doc("Sales Invoice", invoice_entry.invoice_no)

							# Check payments in the invoice
							if hasattr(invoice_doc, 'payments') and invoice_doc.payments:
								for payment in invoice_doc.payments:
									if (payment.mode_of_payment == "Tiền mặt - POS" and
										payment.amount and payment.amount > 0):
										total_cash_balance += payment.amount

						except Exception as e:
							# Skip if invoice not found or error
							frappe.logger().warning(f"Could not get invoice {invoice_entry.invoice_no}: {str(e)}")
							continue

			result["cash_balance"] = total_cash_balance

		return {
			"success": True,
			"data": result
		}

	except Exception as e:
		frappe.logger().error(f"Error getting footer status data: {str(e)}")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_shift_reports(filters=None, limit_page_length=20, limit_start=0):
	"""
	Get list of POS Shift Reports

	Args:
		filters (dict): Filter criteria
		limit_page_length (int): Number of records per page
		limit_start (int): Starting record index

	Returns:
		dict: List of shift reports
	"""
	try:
		default_filters = {"docstatus": ["!=", 2]}  # Exclude cancelled
		if filters:
			default_filters.update(filters)

		shift_reports = frappe.get_all(
			"POS Shift Report",
			filters=default_filters,
			fields=[
				"name", "shift_report_id", "pos_opening_shift",
				"opening_date", "opening_time", "opened_by",
				"status", "verification_status", "invoice_count",
				"total_sales", "total_returns", "total_opening_amount",
				"total_expected_closing", "total_actual_closing", "difference"
			],
			order_by="creation desc",
			limit_page_length=limit_page_length,
			limit_start=limit_start
		)

		# Get total count
		total_count = frappe.db.count("POS Shift Report", filters=default_filters)

		return {
			"success": True,
			"data": shift_reports,
			"total_count": total_count
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Reports Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def get_current_shift_report():
	"""
	Get current shift report for logged-in user

	Returns:
		dict: Current shift report data
	"""
	try:
		user = frappe.session.user

		# Find active opening shift for current user
		active_shift = frappe.get_all(
			"POS Opening Shift",
			filters={
				"owner": user,
				"docstatus": 1,
				"status": "Open"
			},
			fields=["name"],
			limit=1
		)

		if not active_shift:
			return {
				"success": False,
				"message": _("No active opening shift found for current user")
			}

		# Find shift report for this opening shift
		shift_report = frappe.get_all(
			"POS Shift Report",
			filters={
				"pos_opening_shift": active_shift[0].name,
				"status": "Open"
			},
			fields=["name"],
			limit=1
		)

		if not shift_report:
			return {
				"success": False,
				"message": _("No active shift report found")
			}

		# Return full shift report data
		return get_shift_report(shift_report[0].name)

	except Exception as e:
		frappe.log_error(str(e), "Get Current Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def submit_shift_report(shift_report_id):
	"""
	Submit POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Submit result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Validate before submit
		if shift_report.verification_status != "Confirmed":
			frappe.throw(_("Shift report must be confirmed before submission"))

		shift_report.submit()

		return {
			"success": True,
			"message": _("Shift report submitted successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Submit Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def cancel_shift_report(shift_report_id):
	"""
	Cancel POS Shift Report

	Args:
		shift_report_id (str): Shift report ID or name

	Returns:
		dict: Cancel result
	"""
	try:
		if not frappe.db.exists("POS Shift Report", shift_report_id):
			frappe.throw(_("Shift report not found"))

		shift_report = frappe.get_doc("POS Shift Report", shift_report_id)

		# Only allow cancellation of open reports
		if shift_report.status != "Open":
			frappe.throw(_("Cannot cancel submitted shift reports"))

		shift_report.cancel()

		return {
			"success": True,
			"message": _("Shift report cancelled successfully")
		}

	except Exception as e:
		frappe.log_error(str(e), "Cancel Shift Report Error")
		return {
			"success": False,
			"message": str(e)
		}


@frappe.whitelist()
def get_shift_report_with_payment_summary(shift_report_id):
	"""
	Get POS Shift Report with Payment Summary data
	Simplified version - creates/updates payment summaries when called

	Args:
		shift_report_id (str): Shift report ID, shift_report_id field, or name

	Returns:
		dict: Shift report data with payment summary
	"""
	log.info(f"[SHIFT_REPORT_API] Tinh toan Summary Shift Report ID: {shift_report_id}")

	try:
		# 1. Get basic shift report data
		shift_report_data = get_shift_report(shift_report_id)

		# 2. Try to create/update payment summaries
		try:
			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import create_payment_summaries_for_shift
			log.info(f"[SHIFT_REPORT_API] Creating payment summaries for: {shift_report_data['name']}")
			payment_result = create_payment_summaries_for_shift(shift_report_data["name"])
		except ImportError as ie:
			log.error(f"[SHIFT_REPORT_API] Cannot import create_payment_summaries_for_shift: {str(ie)}")
			shift_report_data["payment_summaries"] = []
			return shift_report_data

		# 3. Check if payment summary creation was successful
		if not payment_result.get("success"):
			log.error(f"[SHIFT_REPORT_API] Payment summary creation failed: {payment_result.get('message')}")
			shift_report_data["payment_summaries"] = []
			return shift_report_data

		# 4. Get the created payment summaries
		try:
			from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import get_payment_summaries_for_shift
			payment_summaries_result = get_payment_summaries_for_shift(shift_report_data["name"])

			if payment_summaries_result.get("success"):
				shift_report_data["payment_summaries"] = payment_summaries_result["data"]
				log.info(f"[SHIFT_REPORT_API] Added {len(payment_summaries_result['data'])} payment summaries")
			else:
				log.warning(f"[SHIFT_REPORT_API] Could not get payment summaries: {payment_summaries_result.get('message')}")
				shift_report_data["payment_summaries"] = []
		except ImportError as ie:
			log.error(f"[SHIFT_REPORT_API] Cannot import get_payment_summaries_for_shift: {str(ie)}")
			shift_report_data["payment_summaries"] = []

		# 5. Return complete data
		log.info(f"[SHIFT_REPORT_API] Completed for shift report: {shift_report_data['name']}")
		return shift_report_data

	except Exception as e:
		log.error(f"[SHIFT_REPORT_API] FAILED - Shift Report ID: {shift_report_id}, Error: {str(e)}")
		frappe.log_error(str(e), "Get Shift Report With Payment Summary Error")
		frappe.throw(_("Error getting shift report with payment summary: {0}").format(str(e)))


@frappe.whitelist()
def initialize_payment_summaries(shift_report_name):
	"""
	Initialize payment summary records for a shift report
	Called when shift is opened and shift report is created

	Args:
		shift_report_name (str): Name of the POS Shift Report

	Returns:
		dict: Initialization result
	"""
	log.info(f"[SHIFT_REPORT_API] 🎯 INITIALIZE_PAYMENT_SUMMARIES - Start - Shift Report: {shift_report_name}")

	try:
		from posawesome.posawesome.doctype.pos_payment_summary.pos_payment_summary import initialize_payment_summaries_for_shift

		result = initialize_payment_summaries_for_shift(shift_report_name)

		log.info(f"[SHIFT_REPORT_API] ✅ INITIALIZE_PAYMENT_SUMMARIES - Completed: {result}")

		return result

	except Exception as e:
		log.error(f"[SHIFT_REPORT_API] 💥 INITIALIZE_PAYMENT_SUMMARIES - FAILED - Shift Report: {shift_report_name}, Error: {str(e)}")
		return {
			"success": False,
			"message": f"Error initializing payment summaries: {str(e)}"
		}