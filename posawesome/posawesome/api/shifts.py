# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe import _
from posawesome.posawesome.utils.logging import get_logger

# Initialize logger
log = get_logger("shifts")


@frappe.whitelist()
def get_opening_dialog_data():
	log.info(f"[SHIFTS] 📋 Get opening dialog data for user: {frappe.session.user}")
	data = {}

	# Get only POS Profiles where current user is defined in POS Profile User table
	pos_profiles_data = frappe.db.sql(
		"""
        SELECT DISTINCT p.name, p.company, p.currency
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
        WHERE p.disabled = 0 AND u.user = %s
        ORDER BY p.name
    """,
		frappe.session.user,
		as_dict=1,
	)

	data["pos_profiles_data"] = pos_profiles_data
	log.info(f"[SHIFTS] ✅ Found {len(pos_profiles_data)} accessible POS profiles")

	# Derive companies from accessible POS Profiles
	company_names = []
	for profile in pos_profiles_data:
		if profile.company and profile.company not in company_names:
			company_names.append(profile.company)
	data["companies"] = [{"name": c} for c in company_names]
	log.info(f"[SHIFTS] ✅ Found {len(company_names)} accessible companies: {company_names}")

	pos_profiles_list = []
	for i in data["pos_profiles_data"]:
		pos_profiles_list.append(i.name)

	# Use POS Payment Method table (default for current version)
	data["payments_method"] = frappe.get_list(
		"POS Payment Method",
		filters={"parent": ["in", pos_profiles_list]},
		fields=["*"],
		limit_page_length=0,
		order_by="parent",
		ignore_permissions=True,
	)
	# set currency from pos profile
	for mode in data["payments_method"]:
		mode["currency"] = frappe.get_cached_value("POS Profile", mode["parent"], "currency")

	log.info(f"[SHIFTS] ✅ Found {len(data['payments_method'])} payment methods across {len(pos_profiles_list)} POS profiles")
	return data


@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
	log.info(f"[SHIFTS] 🚀 START create opening voucher - POS Profile: {pos_profile}, Company: {company}, User: {frappe.session.user}")

	balance_details = json.loads(balance_details)
	log.info(f"[SHIFTS] 📊 Balance details: {len(balance_details)} payment methods")

	# STEP 1: Create POS Opening Shift
	log.info(f"[SHIFTS] 📝 STEP 1: Creating POS Opening Shift document")
	new_pos_opening = frappe.get_doc(
		{
			"doctype": "POS Opening Shift",
			"period_start_date": frappe.utils.get_datetime(),
			"posting_date": frappe.utils.getdate(),
			"user": frappe.session.user,
			"pos_profile": pos_profile,
			"company": company,
			"docstatus": 1,
		}
	)
	new_pos_opening.set("balance_details", balance_details)
	new_pos_opening.insert(ignore_permissions=True)
	log.info(f"[SHIFTS] ✅ STEP 1: Created POS Opening Shift: {new_pos_opening.name}")

	# STEP 2: Prepare response data
	data = {}
	data["pos_opening_shift"] = new_pos_opening.as_dict()
	update_opening_shift_data(data, new_pos_opening.pos_profile)
	log.info(f"[SHIFTS] 📋 STEP 2: Prepared response data with POS profile and company info")

	# STEP 3: Auto-create Shift Report
	log.info(f"[SHIFTS] 🔄 STEP 3: Auto-creating Shift Report for opening shift: {new_pos_opening.name}")
	try:
		from posawesome.posawesome.api.shift_reports import create_shift_report

		# Convert balance_details list to dict for opening_amounts
		opening_amounts_dict = {item["mode_of_payment"]: item["amount"] for item in balance_details}
		log.info(f"[SHIFTS] 📊 Converted balance_details to dict: {opening_amounts_dict}")

		shift_report_data = create_shift_report({
			"pos_opening_shift": new_pos_opening.name,
			"opening_amounts": json.dumps(opening_amounts_dict)
		})

		if not shift_report_data.get("success"):
			log.error(f"[SHIFTS] ❌ STEP 3: Failed to create shift report: {shift_report_data.get('message')}")
			frappe.log_error(f"Failed to create shift report: {shift_report_data.get('message')}", "Create Opening Voucher")
			# Throw error để frontend hiển thị cảnh báo nghiêm trọng
			frappe.throw(_("Critical Error: Failed to create Shift Report. Please contact administrator. Error: {0}").format(shift_report_data.get('message')))

		data["shift_report"] = shift_report_data.get("data", {})
		log.info(f"[SHIFTS] ✅ STEP 3: Successfully created Shift Report: {shift_report_data.get('data', {}).get('shift_report_id')}")

		# STEP 4: Update POS Opening Shift with shift report reference
		log.info(f"[SHIFTS] 🔗 STEP 4: Updating POS Opening Shift {new_pos_opening.name} with shift report reference")
		try:
			frappe.db.set_value("POS Opening Shift", new_pos_opening.name, {
				"shift_report": shift_report_data.get("data", {}).get("name"),
				"shift_report_id": shift_report_data.get("data", {}).get("shift_report_id")
			})
			log.info(f"[SHIFTS] ✅ STEP 4: Successfully updated POS Opening Shift with shift report reference")
		except Exception as update_error:
			log.error(f"[SHIFTS] ❌ STEP 4: Failed to update POS Opening Shift with shift report reference: {str(update_error)}")
			# Don't fail the entire operation if this update fails

	except Exception as shift_error:
		log.error(f"[SHIFTS] 💥 STEP 3: Exception creating shift report: {str(shift_error)}")
		frappe.log_error(f"Error creating shift report: {str(shift_error)}", "Create Opening Voucher")
		frappe.throw(_("Critical Error: Failed to create Shift Report. Please contact administrator. Error: {0}").format(str(shift_error)))

	log.info(f"[SHIFTS] 🎉 COMPLETED create opening voucher successfully")
	return data


@frappe.whitelist()
def check_opening_shift(user):
	log.info(f"[SHIFTS] 🔍 Check opening shift for user: {user}")

	open_vouchers = frappe.db.get_all(
		"POS Opening Shift",
		filters={
			"user": user,
			"pos_closing_shift": ["in", ["", None]],
			"docstatus": 1,
			"status": "Open",
		},
		fields=["name", "pos_profile"],
		order_by="period_start_date desc",
	)

	log.info(f"[SHIFTS] 📊 Found {len(open_vouchers)} open shifts for user {user}")

	data = ""
	if len(open_vouchers) > 0:
		latest_shift = open_vouchers[0]
		log.info(f"[SHIFTS] ✅ Using latest open shift: {latest_shift['name']} (POS Profile: {latest_shift['pos_profile']})")

		data = {}
		data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", latest_shift["name"])
		update_opening_shift_data(data, latest_shift["pos_profile"])

		log.info(f"[SHIFTS] 📋 Loaded complete shift data with POS profile and company info")
	else:
		log.info(f"[SHIFTS] ⚠️ No open shifts found for user {user}")

	return data


def update_opening_shift_data(data, pos_profile):
	log.debug(f"[SHIFTS] 🔧 Update opening shift data for POS Profile: {pos_profile}")

	data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile)
	if data["pos_profile"].get("posa_language"):
		frappe.local.lang = data["pos_profile"].posa_language
		log.debug(f"[SHIFTS] 🌐 Set language to: {data['pos_profile'].posa_language}")

	data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
	log.debug(f"[SHIFTS] 🏢 Loaded company: {data['company'].name}")

	allow_negative_stock = frappe.get_value("Stock Settings", None, "allow_negative_stock")
	data["stock_settings"] = {}
	data["stock_settings"].update({"allow_negative_stock": allow_negative_stock})

	log.debug(f"[SHIFTS] ⚙️ Stock settings - Allow negative stock: {allow_negative_stock}")




