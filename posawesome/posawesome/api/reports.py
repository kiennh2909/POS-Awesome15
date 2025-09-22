import frappe
from frappe import _
from frappe.utils import getdate, nowdate, get_datetime
from frappe.utils.logger import get_logger
import json
from functools import reduce

log = get_logger("pos_report")

@frappe.whitelist()
def get_shift_report(company=None, pos_profile=None, from_date=None, to_date=None):
	"""Get comprehensive shift report data with sales, payments and cash reconciliation"""
	try:
		# Validate required parameters
		if not company:
			return {"error": "Company is required"}
		if not from_date or not to_date:
			return {"error": "Date range is required"}

		user = frappe.session.user
		user_roles = frappe.get_roles(user)

		# Build invoice filters
		invoice_filters = {
			"company": company,
			"posting_date": ["between", [from_date, to_date]],
			"docstatus": 1,  # Only submitted invoices
			"is_pos": 1
		}

		if pos_profile:
			invoice_filters["pos_profile"] = pos_profile

		# If not Sales Manager, only show user's invoices
		if "Sales Manager" not in user_roles:
			invoice_filters["owner"] = user

		# Get all POS invoices in date range
		invoices = frappe.get_all(
			"Sales Invoice",
			filters=invoice_filters,
			fields=[
				"name", "posting_date", "is_return", "base_grand_total", "grand_total",
				"pos_profile", "owner", "currency"
			]
		)

		# Group data by date
		daily_data = {}

		# Process invoices
		for invoice in invoices:
			date_key = invoice.posting_date

			if date_key not in daily_data:
				daily_data[date_key] = {
					"date": date_key,
					"sale_invoice_count": 0,
					"return_invoice_count": 0,
					"sale_amount": 0,
					"return_amount": 0,
					"net_amount": 0,
					"cash_amount": 0,
					"bank_amount": 0,
					"qrpay_amount": 0,
					"card_amount": 0,
					"other_amount": 0,
					"cash_submitted": 0,
					"difference": 0,
					"currency": invoice.currency
				}

			# Count invoices and amounts
			if invoice.is_return:
				daily_data[date_key]["return_invoice_count"] += 1
				daily_data[date_key]["return_amount"] += abs(float(invoice.base_grand_total or invoice.grand_total))
			else:
				daily_data[date_key]["sale_invoice_count"] += 1
				daily_data[date_key]["sale_amount"] += float(invoice.base_grand_total or invoice.grand_total)

		# Get payment details for each invoice
		invoice_names = [inv.name for inv in invoices]
		if invoice_names:
			payments = frappe.db.sql("""
				SELECT
					sip.parent as invoice_no,
					si.posting_date,
					sip.mode_of_payment,
					COALESCE(sip.base_amount, sip.amount) as amount
				FROM `tabSales Invoice Payment` sip
				JOIN `tabSales Invoice` si ON sip.parent = si.name
				WHERE sip.parent IN ({})
			""".format(','.join(['%s'] * len(invoice_names))), invoice_names, as_dict=True)

			# Process payments
			for payment in payments:
				date_key = payment.posting_date
				if date_key in daily_data:
					amount = float(payment.amount)
					mode = payment.mode_of_payment.lower()

					# Map payment modes to categories
					if 'cash' in mode:
						daily_data[date_key]["cash_amount"] += amount
					elif 'bank' in mode or 'transfer' in mode:
						daily_data[date_key]["bank_amount"] += amount
					elif 'qr' in mode or 'qrcode' in mode:
						daily_data[date_key]["qrpay_amount"] += amount
					elif 'card' in mode or 'credit' in mode or 'debit' in mode:
						daily_data[date_key]["card_amount"] += amount
					else:
						daily_data[date_key]["other_amount"] += amount

		# Get POS closing shifts for cash submitted amounts
		shift_filters = {
			"company": company,
			"period_start_date": ["between", [from_date, to_date]],
			"docstatus": 1
		}

		if pos_profile:
			shift_filters["pos_profile"] = pos_profile

		if "Sales Manager" not in user_roles:
			shift_filters["user"] = user

		closing_shifts = frappe.get_all(
			"POS Closing Shift",
			filters=shift_filters,
			fields=[
				"name", "period_start_date", "cash_to_deposit",
				"pos_profile", "user"
			]
		)

		# Process closing shifts
		for shift in closing_shifts:
			date_key = shift.period_start_date
			if date_key in daily_data:
				daily_data[date_key]["cash_submitted"] += float(shift.get("cash_to_deposit", 0))

		# Calculate NET amounts and differences
		for date_key, data in daily_data.items():
			data["net_amount"] = data["sale_amount"] - data["return_amount"]
			data["difference"] = data["cash_submitted"] - data["cash_amount"]

		# Convert to list and sort by date
		report_data = list(daily_data.values())
		report_data.sort(key=lambda x: x["date"])

		# Calculate grand totals
		grand_total = {
			"date": "TOTAL",
			"sale_invoice_count": sum(d["sale_invoice_count"] for d in report_data),
			"return_invoice_count": sum(d["return_invoice_count"] for d in report_data),
			"sale_amount": sum(d["sale_amount"] for d in report_data),
			"return_amount": sum(d["return_amount"] for d in report_data),
			"net_amount": sum(d["net_amount"] for d in report_data),
			"cash_amount": sum(d["cash_amount"] for d in report_data),
			"bank_amount": sum(d["bank_amount"] for d in report_data),
			"qrpay_amount": sum(d["qrpay_amount"] for d in report_data),
			"card_amount": sum(d["card_amount"] for d in report_data),
			"other_amount": sum(d["other_amount"] for d in report_data),
			"cash_submitted": sum(d["cash_submitted"] for d in report_data),
			"difference": sum(d["difference"] for d in report_data),
			"currency": report_data[0]["currency"] if report_data else "VND",
			"isTotalRow": True
		}

		# Add grand total to the end
		report_data.append(grand_total)

		# Define headers
		headers = [
			{ "title": _("Ngày"), "key": "date", "width": "100px" },
			{ "title": _("Hóa đơn bán hàng"), "key": "sale_invoice_count", "width": "120px", "align": "end" },
			{ "title": _("Hóa đơn hoàn"), "key": "return_invoice_count", "width": "100px", "align": "end" },
			{ "title": _("Tổng doanh số (SALE)"), "key": "sale_amount", "width": "140px", "align": "end" },
			{ "title": _("Số tiền hoàn (RETURN)"), "key": "return_amount", "width": "140px", "align": "end" },
			{ "title": _("Số tiền NET"), "key": "net_amount", "width": "120px", "align": "end" },
			{ "title": _("CASH"), "key": "cash_amount", "width": "100px", "align": "end" },
			{ "title": _("BANK"), "key": "bank_amount", "width": "100px", "align": "end" },
			{ "title": _("QRPAY"), "key": "qrpay_amount", "width": "100px", "align": "end" },
			{ "title": _("CARD"), "key": "card_amount", "width": "100px", "align": "end" },
			{ "title": _("OTHER"), "key": "other_amount", "width": "100px", "align": "end" },
			{ "title": _("Nộp cuối ca"), "key": "cash_submitted", "width": "120px", "align": "end" },
			{ "title": _("Chênh lệch"), "key": "difference", "width": "100px", "align": "end" },
			{ "title": _("Tiền tệ"), "key": "currency", "width": "80px" }
		]

		# Summary for cards
		summary = {
			"total_sale_invoices": grand_total["sale_invoice_count"],
			"total_return_invoices": grand_total["return_invoice_count"],
			"total_sale_amount": grand_total["sale_amount"],
			"total_return_amount": grand_total["return_amount"],
			"total_net_amount": grand_total["net_amount"],
			"total_cash_amount": grand_total["cash_amount"],
			"total_bank_amount": grand_total["bank_amount"],
			"total_qrpay_amount": grand_total["qrpay_amount"],
			"total_card_amount": grand_total["card_amount"],
			"total_other_amount": grand_total["other_amount"],
			"total_cash_submitted": grand_total["cash_submitted"],
			"total_difference": grand_total["difference"]
		}

		return {
			"data": report_data,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting shift report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_item_report(date=None, pos_profile=None):
	"""Get item sales report for a specific date"""
	try:
		if not date:
			date = nowdate()

		# Get all invoices for the date
		invoice_filters = {
			"posting_date": date,
			"docstatus": 1,
			"is_pos": 1
		}

		if pos_profile:
			invoice_filters["pos_profile"] = pos_profile

		invoices = frappe.get_all(
			"Sales Invoice",
			filters=invoice_filters,
			fields=["name"]
		)

		if not invoices:
			return {
				"data": [],
				"summary": {"total_items": 0, "total_quantity": 0, "total_amount": 0},
				"headers": []
			}

		invoice_names = [inv.name for inv in invoices]

		# Get item details from Sales Invoice Item
		item_data = frappe.db.sql("""
			SELECT
				sii.item_code,
				sii.item_name,
				sii.item_group,
				SUM(sii.qty) as quantity,
				SUM(sii.amount) as total_amount,
				COUNT(DISTINCT sii.parent) as invoice_count
			FROM `tabSales Invoice Item` sii
			WHERE sii.parent IN ({})
			GROUP BY sii.item_code, sii.item_name, sii.item_group
			ORDER BY total_amount DESC
		""".format(','.join(['%s'] * len(invoice_names))), invoice_names, as_dict=True)

		# Calculate summary
		summary = {
			"total_items": len(item_data),
			"total_quantity": sum(float(item.get("quantity", 0)) for item in item_data),
			"total_amount": sum(float(item.get("total_amount", 0)) for item in item_data)
		}

		headers = [
			{ "title": _("Item Code"), "key": "item_code", "width": "120px" },
			{ "title": _("Item Name"), "key": "item_name", "width": "200px" },
			{ "title": _("Category"), "key": "item_group", "width": "120px" },
			{ "title": _("Quantity Sold"), "key": "quantity", "width": "100px", "align": "end" },
			{ "title": _("Total Amount"), "key": "total_amount", "width": "120px", "align": "end" }
		]

		return {
			"data": item_data,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting item report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_tax_report(date=None, pos_profile=None):
	"""Get tax report for a specific date"""
	try:
		if not date:
			date = nowdate()

		# Get all invoices for the date
		invoice_filters = {
			"posting_date": date,
			"docstatus": 1,
			"is_pos": 1
		}

		if pos_profile:
			invoice_filters["pos_profile"] = pos_profile

		invoices = frappe.get_all(
			"Sales Invoice",
			filters=invoice_filters,
			fields=["name", "posting_date", "customer", "total", "total_taxes_and_charges"]
		)

		# Calculate tax amounts
		for invoice in invoices:
			invoice["tax_amount"] = float(invoice.get("total_taxes_and_charges", 0))

		# Calculate summary
		summary = {
			"total_invoices": len(invoices),
			"total_amount": sum(float(inv.get("total", 0)) for inv in invoices),
			"total_tax": sum(float(inv.get("tax_amount", 0)) for inv in invoices)
		}

		headers = [
			{ "title": _("Invoice No"), "key": "name", "width": "120px" },
			{ "title": _("Date"), "key": "posting_date", "width": "100px" },
			{ "title": _("Customer"), "key": "customer", "width": "150px" },
			{ "title": _("Tax Amount"), "key": "tax_amount", "width": "120px", "align": "end" },
			{ "title": _("Total Amount"), "key": "total", "width": "120px", "align": "end" }
		]

		return {
			"data": invoices,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting tax report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_inventory_report(date=None, pos_profile=None):
	"""Get inventory/stock report"""
	try:
		# Get all items with stock information
		items = frappe.db.sql("""
			SELECT
				i.item_code,
				i.item_name,
				i.item_group,
				b.actual_qty as stock_qty,
				COALESCE(r.reserved_qty, 0) as reserved_qty,
				(b.actual_qty - COALESCE(r.reserved_qty, 0)) as available_qty
			FROM `tabItem` i
			LEFT JOIN `tabBin` b ON i.item_code = b.item_code
			LEFT JOIN (
				SELECT item_code, SUM(reserved_qty) as reserved_qty
				FROM `tabBin`
				GROUP BY item_code
			) r ON i.item_code = r.item_code
			WHERE i.is_sales_item = 1
				AND i.disabled = 0
			ORDER BY i.item_code
		""", as_dict=True)

		# Calculate summary
		summary = {
			"total_items": len(items),
			"total_stock": sum(float(item.get("stock_qty", 0)) for item in items),
			"total_reserved": sum(float(item.get("reserved_qty", 0)) for item in items),
			"total_available": sum(float(item.get("available_qty", 0)) for item in items)
		}

		headers = [
			{ "title": _("Item Code"), "key": "item_code", "width": "120px" },
			{ "title": _("Item Name"), "key": "item_name", "width": "200px" },
			{ "title": _("Stock Qty"), "key": "stock_qty", "width": "100px", "align": "end" },
			{ "title": _("Reserved Qty"), "key": "reserved_qty", "width": "100px", "align": "end" },
			{ "title": _("Available Qty"), "key": "available_qty", "width": "100px", "align": "end" }
		]

		return {
			"data": items,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting inventory report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_price_report(date=None, pos_profile=None):
	"""Get price change report for a specific date"""
	try:
		if not date:
			date = nowdate()

		# Get items with price changes on the specified date
		price_changes = frappe.db.sql("""
			SELECT
				ip.item_code,
				i.item_name,
				ip.price_list_rate as new_price,
				ip.modified,
				ip.modified_by
			FROM `tabItem Price` ip
			JOIN `tabItem` i ON ip.item_code = i.item_code
			WHERE DATE(ip.modified) = %s
			ORDER BY ip.modified DESC
		""", (date,), as_dict=True)

		# Get previous prices for comparison
		for item in price_changes:
			# Get the price before this change
			previous_price = frappe.db.sql("""
				SELECT price_list_rate
				FROM `tabItem Price`
				WHERE item_code = %s
					AND modified < %s
				ORDER BY modified DESC
				LIMIT 1
			""", (item.item_code, item.modified), as_scalar=True)

			item["old_price"] = float(previous_price) if previous_price else 0
			item["changed_date"] = item.modified.strftime("%Y-%m-%d %H:%M:%S")

		# Calculate summary
		summary = {
			"total_changes": len(price_changes),
			"average_change": 0
		}

		if price_changes:
			total_change = sum(float(item.get("new_price", 0) - item.get("old_price", 0)) for item in price_changes)
			summary["average_change"] = total_change / len(price_changes)

		headers = [
			{ "title": _("Item Code"), "key": "item_code", "width": "120px" },
			{ "title": _("Item Name"), "key": "item_name", "width": "200px" },
			{ "title": _("Old Price"), "key": "old_price", "width": "100px", "align": "end" },
			{ "title": _("New Price"), "key": "new_price", "width": "100px", "align": "end" },
			{ "title": _("Changed Date"), "key": "changed_date", "width": "120px" }
		]

		return {
			"data": price_changes,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting price report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_employee_report(date=None, pos_profile=None):
	"""Get employee performance report for a month"""
	try:
		if not date:
			date = nowdate()

		# Get month start and end
		date_obj = getdate(date)
		month_start = date_obj.replace(day=1)
		month_end = date_obj

		user = frappe.session.user
		user_roles = frappe.get_roles(user)

		# Get shifts for the month
		shift_filters = {
			"posting_date": ["between", [month_start, month_end]],
			"docstatus": 1
		}

		# If not Sales Manager, only show user's shifts
		if "Sales Manager" not in user_roles:
			shift_filters["owner"] = user

		if pos_profile:
			shift_filters["pos_profile"] = pos_profile

		shifts = frappe.get_all(
			"POS Shift Report",
			filters=shift_filters,
			fields=["owner", "total_sales", "total_returns", "net_sales"],
			group_by="owner"
		)

		# Aggregate by employee
		employee_data = {}
		for shift in shifts:
			employee = shift.owner
			if employee not in employee_data:
				employee_data[employee] = {
					"employee_id": employee,
					"employee_name": frappe.db.get_value("User", employee, "full_name") or employee,
					"shifts_count": 0,
					"total_sales": 0,
					"total_returns": 0,
					"net_sales": 0
				}

			employee_data[employee]["shifts_count"] += 1
			employee_data[employee]["total_sales"] += float(shift.get("total_sales", 0))
			employee_data[employee]["total_returns"] += float(shift.get("total_returns", 0))
			employee_data[employee]["net_sales"] += float(shift.get("net_sales", 0))

		# Calculate performance rating
		employees_list = list(employee_data.values())
		for emp in employees_list:
			avg_sales_per_shift = emp["total_sales"] / emp["shifts_count"] if emp["shifts_count"] > 0 else 0
			if avg_sales_per_shift > 1000000:  # High performer
				emp["performance"] = "Excellent"
			elif avg_sales_per_shift > 500000:  # Good performer
				emp["performance"] = "Good"
			elif avg_sales_per_shift > 100000:  # Average performer
				emp["performance"] = "Average"
			else:  # Low performer
				emp["performance"] = "Needs Improvement"

		# Calculate summary
		summary = {
			"total_employees": len(employees_list),
			"total_shifts": sum(emp["shifts_count"] for emp in employees_list),
			"total_sales": sum(emp["total_sales"] for emp in employees_list),
			"average_sales_per_employee": 0
		}

		if summary["total_employees"] > 0:
			summary["average_sales_per_employee"] = summary["total_sales"] / summary["total_employees"]

		headers = [
			{ "title": _("Employee ID"), "key": "employee_id", "width": "120px" },
			{ "title": _("Employee Name"), "key": "employee_name", "width": "150px" },
			{ "title": _("Shifts Count"), "key": "shifts_count", "width": "100px", "align": "end" },
			{ "title": _("Total Sales"), "key": "total_sales", "width": "120px", "align": "end" },
			{ "title": _("Performance"), "key": "performance", "width": "100px" }
		]

		return {
			"data": employees_list,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting employee report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_promotion_report(date=None, pos_profile=None):
	"""Get promotion usage report"""
	try:
		# Get all active promotions
		promotions = frappe.get_all(
			"POS Offer",
			filters={
				"disabled": 0,
				"docstatus": 1
			},
			fields=["name", "title", "offer", "offer_type"]
		)

		promotion_data = []
		for promo in promotions:
			# Count usage (this is a simplified version - you might need to track actual usage)
			usage_count = frappe.db.count("Sales Invoice", {
				"posa_offer_applied": promo.name,
				"docstatus": 1
			})

			# Calculate total discount given
			total_discount = frappe.db.sql("""
				SELECT SUM(si.posa_total_discount)
				FROM `tabSales Invoice` si
				WHERE si.posa_offer_applied = %s
					AND si.docstatus = 1
			""", (promo.name,), as_scalar=True) or 0

			promotion_data.append({
				"promotion_code": promo.name,
				"promotion_name": promo.title,
				"type": promo.offer,
				"usage_count": usage_count,
				"total_discount": float(total_discount)
			})

		# Calculate summary
		summary = {
			"total_promotions": len(promotion_data),
			"total_usage": sum(p["usage_count"] for p in promotion_data),
			"total_discount": sum(p["total_discount"] for p in promotion_data)
		}

		headers = [
			{ "title": _("Promotion Code"), "key": "promotion_code", "width": "120px" },
			{ "title": _("Promotion Name"), "key": "promotion_name", "width": "200px" },
			{ "title": _("Type"), "key": "type", "width": "100px" },
			{ "title": _("Usage Count"), "key": "usage_count", "width": "100px", "align": "end" },
			{ "title": _("Total Discount"), "key": "total_discount", "width": "120px", "align": "end" }
		]

		return {
			"data": promotion_data,
			"summary": summary,
			"headers": headers
		}

	except Exception as e:
		frappe.log_error(f"Error getting promotion report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def export_shift_report(company=None, pos_profile=None, from_date=None, to_date=None):
	"""Export shift report to Excel"""
	try:
		report_data = get_shift_report(company, pos_profile, from_date, to_date)

		if "error" in report_data:
			return {"error": report_data["error"]}

		# Generate Excel content
		content = "BÁO CÁO TOÀN CA - TỔNG HỢP DOANH SỐ\n"
		content += f"Công ty: {company}\n"
		content += f"Hồ sơ POS: {pos_profile or 'Tất cả'}\n"
		content += f"Khoảng thời gian: {from_date} - {to_date}\n"
		content += f"Xuất báo cáo: {get_datetime().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

		# Summary
		summary = report_data["summary"]
		content += "TỔNG QUAN\n"
		content += f"Tổng hóa đơn bán: {summary['total_sale_invoices']}\n"
		content += f"Tổng hóa đơn hoàn: {summary['total_return_invoices']}\n"
		content += f"Tổng doanh số: {summary['total_sale_amount']}\n"
		content += f"Tổng hoàn tiền: {summary['total_return_amount']}\n"
		content += f"Doanh thu ròng: {summary['total_net_amount']}\n"
		content += f"Tiền mặt: {summary['total_cash_amount']}\n"
		content += f"Ngân hàng: {summary['total_bank_amount']}\n"
		content += f"QR Pay: {summary['total_qrpay_amount']}\n"
		content += f"Thẻ tín dụng: {summary['total_card_amount']}\n"
		content += f"Khác: {summary['total_other_amount']}\n"
		content += f"Nộp cuối ca: {summary['total_cash_submitted']}\n"
		content += f"Chênh lệch: {summary['total_difference']}\n\n"

		# Data
		content += "CHI TIẾT THEO NGÀY\n"
		content += "Ngày\tHóa đơn bán\tHóa đơn hoàn\tTổng doanh số\tSố tiền hoàn\tSố tiền NET\tCASH\tBANK\tQRPAY\tCARD\tOTHER\tNộp cuối ca\tChênh lệch\tTiền tệ\n"

		for row in report_data["data"]:
			content += f"{row.get('date', '')}\t"
			content += f"{row.get('sale_invoice_count', 0)}\t"
			content += f"{row.get('return_invoice_count', 0)}\t"
			content += f"{row.get('sale_amount', 0)}\t"
			content += f"{row.get('return_amount', 0)}\t"
			content += f"{row.get('net_amount', 0)}\t"
			content += f"{row.get('cash_amount', 0)}\t"
			content += f"{row.get('bank_amount', 0)}\t"
			content += f"{row.get('qrpay_amount', 0)}\t"
			content += f"{row.get('card_amount', 0)}\t"
			content += f"{row.get('other_amount', 0)}\t"
			content += f"{row.get('cash_submitted', 0)}\t"
			content += f"{row.get('difference', 0)}\t"
			content += f"{row.get('currency', 'VND')}\n"

		# Create file
		file_name = f"bao_cao_toan_ca_{from_date}_{to_date}.xlsx"
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": file_name,
			"content": content,
			"is_private": 1
		})
		file_doc.save()

		return {"file_url": file_doc.file_url}

	except Exception as e:
		frappe.log_error(f"Error exporting shift report: {str(e)}")
		return {"error": str(e)}

# Similar export functions for other reports would follow the same pattern
@frappe.whitelist()
def export_item_report(date=None, pos_profile=None):
	"""Export item report to Excel"""
	try:
		report_data = get_item_report(date, pos_profile)

		if "error" in report_data:
			return {"error": report_data["error"]}

		# Generate Excel content (similar pattern)
		content = "ITEM SALES REPORT\n"
		content += f"Date: {date}\n"
		content += f"Generated: {get_datetime().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

		# Summary
		summary = report_data["summary"]
		content += "SUMMARY\n"
		content += f"Total Items: {summary['total_items']}\n"
		content += f"Total Quantity: {summary['total_quantity']}\n"
		content += f"Total Amount: {summary['total_amount']}\n\n"

		# Data
		content += "ITEM DETAILS\n"
		content += "Item Code\tItem Name\tCategory\tQuantity Sold\tTotal Amount\n"

		for item in report_data["data"]:
			content += f"{item.get('item_code', '')}\t"
			content += f"{item.get('item_name', '')}\t"
			content += f"{item.get('item_group', '')}\t"
			content += f"{item.get('quantity', 0)}\t"
			content += f"{item.get('total_amount', 0)}\n"

		# Create file
		file_name = f"item_report_{date}.xlsx"
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": file_name,
			"content": content,
			"is_private": 1
		})
		file_doc.save()

		return {"file_url": file_doc.file_url}

	except Exception as e:
		frappe.log_error(f"Error exporting item report: {str(e)}")
		return {"error": str(e)}

@frappe.whitelist()
def get_shift_list_report(company=None, pos_profile=None, from_date=None, to_date=None, cashier=None, user=None):
	try:
		# Log input parameters
		log.info(f"[SHIFT_LIST_REPORT] Input: company={company}, pos_profile={pos_profile}, from_date={from_date}, to_date={to_date}, cashier={cashier}, user={user}, session_user={frappe.session.user}")

		if not company:
			log.warning("[SHIFT_LIST_REPORT] Missing required parameter: company")
			return {"error": "Company is required"}
		if not from_date or not to_date:
			log.warning("[SHIFT_LIST_REPORT] Missing required parameter: date range")
			return {"error": "Date range is required"}

		session_user = frappe.session.user
		roles = set(frappe.get_roles(session_user))
		log.info(f"[SHIFT_LIST_REPORT] User roles: {list(roles)}")

		# --- 1) Build shift filters
		shift_filters = {
			"company": company,
			"docstatus": 1,
			"period_end_date": ["between", [from_date, to_date]],  # kết sổ trong khoảng
		}
		if pos_profile:
			shift_filters["pos_profile"] = pos_profile

		# Quyền xem: nếu không phải Sales Manager thì chỉ thấy ca của chính mình
		if "Sales Manager" not in roles:
			shift_filters["user"] = session_user
		elif user:
			shift_filters["user"] = user
		elif cashier:
			shift_filters["user"] = cashier

		shifts = frappe.get_all(
			"POS Closing Shift",
			filters=shift_filters,
			fields=[
				"name", "user", "pos_profile", "company", "currency",
				"period_start_date", "period_start_time",
				"period_end_date", "period_end_time",
				"cash_to_deposit", "cash_counted",
				"workflow_state"
			],
			order_by="period_end_date asc, period_end_time asc"
		)

		log.info(f"[SHIFT_LIST_REPORT] Found {len(shifts)} shifts matching filters")

		if not shifts:
			log.info("[SHIFT_LIST_REPORT] No shifts found, returning empty result")
			return {"success": True, "data": [], "summary": {k:0 for k in [
				"total_shifts","total_sale_invoices","total_return_invoices","total_sale_amount",
				"total_return_amount","total_net_amount","total_cash_amount","total_bank_amount",
				"total_qrpay_amount","total_card_amount","total_other_amount",
				"total_cash_submitted","total_difference"
			]}}

		# --- 2) Build time windows per shift
		shift_windows = {}
		for s in shifts:
			start_dt = frappe.utils.to_datetime(f"{s.period_start_date} {s.period_start_time or '00:00:00'}")
			end_dt   = frappe.utils.to_datetime(f"{s.period_end_date} {s.period_end_time or '23:59:59'}")
			shift_windows[s.name] = (start_dt, end_dt)

		# --- 3) Fetch all invoices in the overall range once
		inv_filters = {
			"company": company,
			"docstatus": 1,
			"posting_date": ["between", [from_date, to_date]],
			"is_pos": 1,
		}
		if pos_profile:
			inv_filters["pos_profile"] = pos_profile

		invoices = frappe.get_all(
			"Sales Invoice",
			filters=inv_filters,
			fields=["name","posting_date","posting_time","pos_profile","is_return",
					"base_grand_total","grand_total","currency","owner","pos_closing_shift"]
		)

		log.info(f"[SHIFT_LIST_REPORT] Found {len(invoices)} invoices in date range")

		# --- 4) Partition invoices to shifts
		# Prefer explicit link; otherwise match by datetime within shift window & same pos_profile
		def within(dt, start, end): return start <= dt <= end

		shift_inv_map = {s.name: [] for s in shifts}
		fallback_bucket = []  # invoices that don't match any shift (for logging)

		for inv in invoices:
			if inv.get("pos_closing_shift") and inv.pos_closing_shift in shift_inv_map:
				shift_inv_map[inv.pos_closing_shift].append(inv)
				continue

			inv_dt = frappe.utils.to_datetime(f"{inv.posting_date} {inv.posting_time or '00:00:00'}")
			matched = False
			for s in shifts:
				if pos_profile and inv.pos_profile != s.pos_profile:
					continue
				st, en = shift_windows[s.name]
				if within(inv_dt, st, en):
					shift_inv_map[s.name].append(inv)
					matched = True
					break
			if not matched:
				fallback_bucket.append(inv.name)

		if fallback_bucket:
			log.warning(f"[SHIFT_LIST_REPORT] {len(fallback_bucket)} invoices not matched to any shift: {fallback_bucket}")

		# --- 5) Fetch all payments for those invoices in one query
		all_inv_names = [inv.name for inv in invoices]
		pay_map = {}
		if all_inv_names:
			placeholders = ",".join(["%s"] * len(all_inv_names))
			rows = frappe.db.sql(f"""
				SELECT sip.parent AS inv, sip.mode_of_payment,
					   SUM(COALESCE(sip.base_amount, sip.amount)) AS amt
				FROM `tabSales Invoice Payment` sip
				WHERE sip.parent IN ({placeholders})
				GROUP BY sip.parent, sip.mode_of_payment
			""", all_inv_names, as_dict=True)

			for r in rows:
				pay_map.setdefault(r.inv, []).append(r)

		log.info(f"[SHIFT_LIST_REPORT] Found {len(rows)} payment records for {len(pay_map)} invoices")

		# --- 6) Helper: normalize mode of payment
		def normalize_mop(m):
			ml = (m or "").strip().lower()
			if any(k in ml for k in ["cash","tiền mặt"]): return "cash"
			if any(k in ml for k in ["qr","qrcode","promptpay","linepay","momo","m-pesa"]): return "qrpay"
			if any(k in ml for k in ["visa","master","card","credit","debit","amex","jcb"]): return "card"
			if any(k in ml for k in ["bank","wire","transfer","eft","atm"]): return "bank"
			return "other"

		# --- 7) Build per-shift rows
		data = []
		summary = {k:0 for k in [
			"total_shifts","total_sale_invoices","total_return_invoices","total_sale_amount",
			"total_return_amount","total_net_amount","total_cash_amount","total_bank_amount",
			"total_qrpay_amount","total_card_amount","total_other_amount",
			"total_cash_submitted","total_difference"
		]}

		# Preload full names in one go
		unique_users = list({s.user for s in shifts})
		names_map = {u: u for u in unique_users}
		if unique_users:
			for u, fn in frappe.get_all("User",
										filters={"name":["in", unique_users]},
										fields=["name","full_name"],
										as_list=True):
				names_map[u] = fn or u

		for s in shifts:
			row = {
				"name": s.name,
				"shift_id": s.name,
				"user": s.user,
				"user_fullname": names_map.get(s.user, s.user),
				"date": s.period_end_date,  # hiển thị theo ngày kết sổ
				"status": s.workflow_state or "Closed",
				"currency": s.currency,
				"sale_invoice_count": 0, "return_invoice_count": 0,
				"sale_amount": 0.0, "return_amount": 0.0, "net_amount": 0.0,
				"cash_amount": 0.0, "bank_amount": 0.0, "qrpay_amount": 0.0, "card_amount": 0.0, "other_amount": 0.0,
				"cash_submitted": float(s.cash_to_deposit or s.cash_counted or 0.0),
				"difference": 0.0,
			}

			invs = shift_inv_map.get(s.name, [])
			inv_names = [i.name for i in invs]

			# Aggregate SALE/RETURN
			for i in invs:
				if i.is_return:
					row["return_invoice_count"] += 1
					row["return_amount"] += abs(float(i.base_grand_total))
				else:
					row["sale_invoice_count"] += 1
					row["sale_amount"] += float(i.base_grand_total)

			# Aggregate payments (net including returns)
			for inv_name in inv_names:
				for p in pay_map.get(inv_name, []):
					cat = normalize_mop(p.mode_of_payment)
					row[f"{cat}_amount"] += float(p.amt or 0)

			row["net_amount"] = row["sale_amount"] - row["return_amount"]
			row["difference"] = row["cash_submitted"] - row["cash_amount"]
			data.append(row)

			# Grand totals
			summary["total_shifts"] += 1
			summary["total_sale_invoices"] += row["sale_invoice_count"]
			summary["total_return_invoices"] += row["return_invoice_count"]
			summary["total_sale_amount"] += row["sale_amount"]
			summary["total_return_amount"] += row["return_amount"]
			summary["total_net_amount"] += row["net_amount"]
			summary["total_cash_amount"] += row["cash_amount"]
			summary["total_bank_amount"] += row["bank_amount"]
			summary["total_qrpay_amount"] += row["qrpay_amount"]
			summary["total_card_amount"] += row["card_amount"]
			summary["total_other_amount"] += row["other_amount"]
			summary["total_cash_submitted"] += row["cash_submitted"]
			summary["total_difference"] += row["difference"]

		result = {"success": True, "data": data, "summary": summary}
		log.info(f"[SHIFT_LIST_REPORT] Output: success=True, shifts_count={len(data)}, summary={summary}")
		return result

	except Exception as e:
		log.error(f"[SHIFT_LIST_REPORT] Error: {str(e)}")
		frappe.log_error(f"[SHIFT_REPORT] {frappe.get_traceback()}")
		result = {"error": str(e)}
		log.info(f"[SHIFT_LIST_REPORT] Output: error={str(e)}")
		return result

@frappe.whitelist()
def export_shift_list_report(company=None, pos_profile=None, from_date=None, to_date=None, cashier=None, user=None):
	"""Export shift list report to Excel"""
	try:
		report_data = get_shift_list_report(company, pos_profile, from_date, to_date, cashier, user)

		if "error" in report_data:
			return {"error": report_data["error"]}

		# Generate Excel content
		content = "BÁO CÁO DANH SÁCH CA LÀM VIỆC\n"
		content += f"Công ty: {company}\n"
		content += f"Hồ sơ POS: {pos_profile or 'Tất cả'}\n"
		content += f"Nhân viên: {cashier or 'Tất cả'}\n"
		content += f"Khoảng thời gian: {from_date} - {to_date}\n"
		content += f"Xuất báo cáo: {get_datetime().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

		# Summary
		summary = report_data["summary"]
		content += "TỔNG QUAN\n"
		content += f"Tổng ca: {summary['total_shifts']}\n"
		content += f"Tổng hóa đơn bán: {summary['total_sale_invoices']}\n"
		content += f"Tổng hóa đơn hoàn: {summary['total_return_invoices']}\n"
		content += f"Tổng doanh số: {summary['total_sale_amount']}\n"
		content += f"Tổng hoàn tiền: {summary['total_return_amount']}\n"
		content += f"Doanh thu ròng: {summary['total_net_amount']}\n"
		content += f"Tiền mặt: {summary['total_cash_amount']}\n"
		content += f"Ngân hàng: {summary['total_bank_amount']}\n"
		content += f"QR Pay: {summary['total_qrpay_amount']}\n"
		content += f"Thẻ tín dụng: {summary['total_card_amount']}\n"
		content += f"Khác: {summary['total_other_amount']}\n"
		content += f"Nộp cuối ca: {summary['total_cash_submitted']}\n"
		content += f"Chênh lệch: {summary['total_difference']}\n\n"

		# Data
		content += "CHI TIẾT CA LÀM VIỆC\n"
		content += "Mã SHIFT\tNhân viên\tNgày\tTrạng thái\tHóa đơn bán\tHóa đơn hoàn\tTổng doanh số\tSố tiền hoàn\tSố tiền NET\tCASH\tBANK\tQRPAY\tCARD\tOTHER\tNộp cuối ca\tChênh lệch\tTiền tệ\n"

		for row in report_data["data"]:
			content += f"{row.get('shift_id', '')}\t"
			content += f"{row.get('user_fullname', '')}\t"
			content += f"{row.get('date', '')}\t"
			content += f"{row.get('status', '')}\t"
			content += f"{row.get('sale_invoice_count', 0)}\t"
			content += f"{row.get('return_invoice_count', 0)}\t"
			content += f"{row.get('sale_amount', 0)}\t"
			content += f"{row.get('return_amount', 0)}\t"
			content += f"{row.get('net_amount', 0)}\t"
			content += f"{row.get('cash_amount', 0)}\t"
			content += f"{row.get('bank_amount', 0)}\t"
			content += f"{row.get('qrpay_amount', 0)}\t"
			content += f"{row.get('card_amount', 0)}\t"
			content += f"{row.get('other_amount', 0)}\t"
			content += f"{row.get('cash_submitted', 0)}\t"
			content += f"{row.get('difference', 0)}\t"
			content += f"{row.get('currency', 'VND')}\n"

		# Create file
		file_name = f"bao_cao_danh_sach_ca_{from_date}_{to_date}.xlsx"
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": file_name,
			"content": content,
			"is_private": 1
		})
		file_doc.save()

		return {"file_url": file_doc.file_url}

	except Exception as e:
		frappe.log_error(f"Error exporting shift list report: {str(e)}")
		return {"error": str(e)}

# Add similar export functions for other report types...