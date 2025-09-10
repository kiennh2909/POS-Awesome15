# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.utils import nowdate
from frappe import _
from .utilities import get_version


@frappe.whitelist()
def get_opening_dialog_data():
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

	# Derive companies from accessible POS Profiles
	company_names = []
	for profile in pos_profiles_data:
		if profile.company and profile.company not in company_names:
			company_names.append(profile.company)
	data["companies"] = [{"name": c} for c in company_names]

	pos_profiles_list = []
	for i in data["pos_profiles_data"]:
		pos_profiles_list.append(i.name)

	payment_method_table = "POS Payment Method" if get_version() == 13 else "Sales Invoice Payment"
	data["payments_method"] = frappe.get_list(
		payment_method_table,
		filters={"parent": ["in", pos_profiles_list]},
		fields=["*"],
		limit_page_length=0,
		order_by="parent",
		ignore_permissions=True,
	)
	# set currency from pos profile
	for mode in data["payments_method"]:
		mode["currency"] = frappe.get_cached_value("POS Profile", mode["parent"], "currency")

	return data


@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
	balance_details = json.loads(balance_details)

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

	data = {}
	data["pos_opening_shift"] = new_pos_opening.as_dict()
	update_opening_shift_data(data, new_pos_opening.pos_profile)

	# Tự động tạo Shift Report ngay sau khi tạo Opening Shift thành công
	try:
		shift_report_data = create_shift_report_automatically(
			new_pos_opening.name, balance_details
		)
		data["shift_report"] = shift_report_data
	except Exception as e:
		frappe.log_error(f"Failed to create shift report: {str(e)}", "Create Opening Voucher")
		# Throw error để frontend hiển thị cảnh báo nghiêm trọng
		frappe.throw(_("Critical Error: Failed to create Shift Report. Please contact administrator. Error: {0}").format(str(e)))

	return data


@frappe.whitelist()
def check_opening_shift(user):
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
	data = ""
	if len(open_vouchers) > 0:
		data = {}
		data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", open_vouchers[0]["name"])
		update_opening_shift_data(data, open_vouchers[0]["pos_profile"])
	return data


def update_opening_shift_data(data, pos_profile):
	data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile)
	if data["pos_profile"].get("posa_language"):
		frappe.local.lang = data["pos_profile"].posa_language
	data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
	allow_negative_stock = frappe.get_value("Stock Settings", None, "allow_negative_stock")
	data["stock_settings"] = {}
	data["stock_settings"].update({"allow_negative_stock": allow_negative_stock})


def create_shift_report_automatically(opening_shift_name, balance_details):
	"""
	Tự động tạo Shift Report ngay sau khi tạo Opening Shift thành công

	Args:
		opening_shift_name (str): Tên của POS Opening Shift vừa tạo
		balance_details (list): Danh sách balance details từ opening shift

	Returns:
		dict: Thông tin Shift Report vừa tạo
	"""
	try:
		# Kiểm tra xem Shift Report đã tồn tại chưa
		existing_report = frappe.db.exists("POS Shift Report",
			{"pos_opening_shift": opening_shift_name}
		)

		if existing_report:
			# Nếu đã tồn tại, trả về thông tin report hiện tại
			report = frappe.get_doc("POS Shift Report", existing_report)
			return {
				"name": report.name,
				"shift_report_id": report.shift_report_id,
				"status": "existing"
			}

		# Lấy thông tin từ opening shift
		opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)

		# Tạo opening amounts dictionary từ balance_details
		opening_amounts = {}
		total_opening = 0

		for detail in balance_details:
			mode_of_payment = detail.get("mode_of_payment")
			amount = detail.get("amount", 0)
			if mode_of_payment and amount:
				opening_amounts[mode_of_payment] = amount
				total_opening += amount

		# Tạo Shift Report
		shift_report = frappe.get_doc({
			"doctype": "POS Shift Report",
			"shift_report_id": f"SHIFT-{opening_shift_name}",
			"pos_opening_shift": opening_shift_name,
			"opening_date": opening_shift.posting_date,
			"opening_time": opening_shift.period_start_date,
			"opened_by": opening_shift.user,
			"opening_amounts": json.dumps(opening_amounts),
			"total_opening_amount": total_opening,
			"status": "Open",
			"verification_status": "Pending"
		})

		shift_report.insert(ignore_permissions=True)

		# Cập nhật opening shift với shift report reference
		frappe.db.set_value("POS Opening Shift", opening_shift_name, {
			"shift_report": shift_report.name,
			"shift_report_id": shift_report.shift_report_id
		})

		frappe.db.commit()

		return {
			"name": shift_report.name,
			"shift_report_id": shift_report.shift_report_id,
			"status": "created",
			"opening_amounts": opening_amounts,
			"total_opening_amount": total_opening
		}

	except Exception as e:
		frappe.log_error(f"Error creating shift report automatically: {str(e)}", "Create Shift Report Automatically")
		# Không throw error để không làm gián đoạn việc tạo opening shift
		return {
			"status": "error",
			"message": str(e)
		}
