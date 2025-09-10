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
	shift_report_data = create_shift_report_automatically(
		new_pos_opening.name, balance_details
	)

	# Kiểm tra nếu tạo shift report thất bại
	if shift_report_data.get("status") == "error":
		frappe.log_error(f"Failed to create shift report: {shift_report_data.get('message')}", "Create Opening Voucher")
		# Throw error để frontend hiển thị cảnh báo nghiêm trọng
		frappe.throw(_("Critical Error: Failed to create Shift Report. Please contact administrator. Error: {0}").format(shift_report_data.get('message')))

	data["shift_report"] = shift_report_data

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
		# Debug logging
		frappe.logger().info(f"Starting create_shift_report_automatically for {opening_shift_name}")
		frappe.logger().info(f"Balance details: {balance_details}")

		# Kiểm tra xem Shift Report đã tồn tại chưa
		existing_report = frappe.db.exists("POS Shift Report",
			{"pos_opening_shift": opening_shift_name}
		)

		if existing_report:
			# Nếu đã tồn tại, trả về thông tin report hiện tại
			report = frappe.get_doc("POS Shift Report", existing_report)
			frappe.logger().info(f"Shift Report already exists: {existing_report}")
			return {
				"name": report.name,
				"shift_report_id": report.shift_report_id,
				"status": "existing"
			}

		# Lấy thông tin từ opening shift
		try:
			opening_shift = frappe.get_doc("POS Opening Shift", opening_shift_name)
			frappe.logger().info(f"Opening shift loaded: {opening_shift.name}")
		except frappe.DoesNotExistError:
			frappe.logger().error(f"POS Opening Shift not found: {opening_shift_name}")
			return {
				"status": "error",
				"message": f"POS Opening Shift not found: {opening_shift_name}"
			}

		# Validate opening shift data
		if not opening_shift.posting_date:
			frappe.logger().error("Opening shift missing posting_date")
			return {
				"status": "error",
				"message": "Opening shift missing posting date"
			}

		if not opening_shift.user:
			frappe.logger().error("Opening shift missing user")
			return {
				"status": "error",
				"message": "Opening shift missing user"
			}

		if not opening_shift.pos_profile:
			frappe.logger().error("Opening shift missing pos_profile")
			return {
				"status": "error",
				"message": "Opening shift missing POS profile"
			}

		if not opening_shift.company:
			frappe.logger().error("Opening shift missing company")
			return {
				"status": "error",
				"message": "Opening shift missing company"
			}

		# Tạo opening amounts dictionary từ balance_details
		opening_amounts = {}
		total_opening = 0

		if not balance_details:
			frappe.logger().error("No balance details provided")
			return {
				"status": "error",
				"message": "No balance details provided"
			}

		for detail in balance_details:
			if not isinstance(detail, dict):
				frappe.logger().error(f"Invalid balance detail format: {detail}")
				continue

			mode_of_payment = detail.get("mode_of_payment")
			amount = detail.get("amount", 0)

			# Validate required fields
			if not mode_of_payment:
				frappe.logger().error(f"Missing mode_of_payment in balance detail: {detail}")
				continue

			# Validate amount
			try:
				amount = float(amount) if amount else 0
			except (ValueError, TypeError):
				frappe.logger().error(f"Invalid amount for {mode_of_payment}: {detail.get('amount')}")
				continue

			if amount > 0:
				opening_amounts[mode_of_payment] = amount
				total_opening += amount

		if not opening_amounts:
			frappe.logger().error("No valid opening amounts found")
			return {
				"status": "error",
				"message": "No valid opening amounts found"
			}

		frappe.logger().info(f"Opening amounts: {opening_amounts}, Total: {total_opening}")

		# Tạo Shift Report ID duy nhất
		base_shift_report_id = f"SHIFT-{opening_shift_name}"
		shift_report_id = base_shift_report_id
		counter = 1

		# Kiểm tra và tạo ID duy nhất nếu cần
		while frappe.db.exists("POS Shift Report", {"shift_report_id": shift_report_id}):
			shift_report_id = f"{base_shift_report_id}-{counter}"
			counter += 1

		# Tạo Shift Report
		shift_report_data = {
			"doctype": "POS Shift Report",
			"shift_report_id": shift_report_id,
			"pos_opening_shift": opening_shift_name,
			"opening_date": opening_shift.posting_date,
			"opening_time": opening_shift.period_start_date.time() if opening_shift.period_start_date else frappe.utils.nowtime(),
			"opened_by": opening_shift.user,
			"opening_amounts": json.dumps(opening_amounts),
			"total_opening_amount": total_opening,
			"status": "Open",
			"verification_status": "Pending"
		}

		frappe.logger().info(f"Creating shift report with data: {shift_report_data}")

		try:
			shift_report = frappe.get_doc(shift_report_data)
			shift_report.insert(ignore_permissions=True)
			frappe.db.commit()  # Ensure the document is committed
			frappe.logger().info(f"Shift Report created successfully: {shift_report.name}")
		except frappe.DuplicateEntryError as dup_error:
			frappe.logger().error(f"Duplicate shift report ID: {str(dup_error)}")
			return {
				"status": "error",
				"message": f"Shift report ID already exists: {shift_report_data['shift_report_id']}"
			}
		except frappe.ValidationError as val_error:
			frappe.logger().error(f"Validation error creating shift report: {str(val_error)}")
			return {
				"status": "error",
				"message": f"Validation error: {str(val_error)}"
			}
		except Exception as insert_error:
			frappe.logger().error(f"Failed to insert shift report: {str(insert_error)}")
			return {
				"status": "error",
				"message": f"Failed to create shift report: {str(insert_error)}"
			}

		# Cập nhật opening shift với shift report reference
		try:
			frappe.db.set_value("POS Opening Shift", opening_shift_name, {
				"shift_report": shift_report.name,
				"shift_report_id": shift_report.shift_report_id
			})
			frappe.db.commit()
			frappe.logger().info(f"Opening shift updated with shift report reference")
		except Exception as update_error:
			frappe.logger().error(f"Failed to update opening shift: {str(update_error)}")
			# Don't return error here as shift report was created successfully
			# Just log the error

		return {
			"name": shift_report.name,
			"shift_report_id": shift_report.shift_report_id,
			"status": "created",
			"opening_amounts": opening_amounts,
			"total_opening_amount": total_opening
		}

	except Exception as e:
		frappe.logger().error(f"Error creating shift report automatically: {str(e)}")
		frappe.log_error(f"Error creating shift report automatically: {str(e)}", "Create Shift Report Automatically")
		# Return error dict thay vì throw để không làm gián đoạn việc tạo opening shift
		return {
			"status": "error",
			"message": str(e)
		}
