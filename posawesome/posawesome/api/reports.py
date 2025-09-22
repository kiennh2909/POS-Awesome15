import frappe
from frappe import _
from frappe.utils import getdate, nowdate, get_datetime
import json

@frappe.whitelist()
def get_shift_report(date=None, pos_profile=None):
	"""Get shift report data for a specific date"""
	try:
		if not date:
			date = nowdate()

		user = frappe.session.user
		user_roles = frappe.get_roles(user)

		# Build filters based on user role
		filters = {
			"posting_date": date,
			"docstatus": 1  # Only submitted shifts
		}

		# If not Sales Manager, only show user's shifts
		if "Sales Manager" not in user_roles:
			filters["owner"] = user

		# If POS profile specified, filter by it
		if pos_profile:
			filters["pos_profile"] = pos_profile

		shifts = frappe.get_all(
			"POS Shift Report",
			filters=filters,
			fields=[
				"name", "shift_report_id", "posting_date", "posting_time",
				"total_sales", "total_returns", "net_sales", "owner",
				"pos_profile", "status", "verification_status"
			],
			order_by="posting_time desc"
		)

		# Calculate summary
		summary = {
			"total_shifts": len(shifts),
			"total_sales": sum(float(s.get("total_sales", 0)) for s in shifts),
			"total_returns": sum(float(s.get("total_returns", 0)) for s in shifts),
			"net_sales": sum(float(s.get("net_sales", 0)) for s in shifts)
		}

		headers = [
			{ "title": _("Shift ID"), "key": "shift_report_id", "width": "120px" },
			{ "title": _("Employee"), "key": "owner", "width": "150px" },
			{ "title": _("Start Time"), "key": "posting_time", "width": "120px" },
			{ "title": _("Total Sales"), "key": "total_sales", "width": "120px", "align": "end" },
			{ "title": _("Total Returns"), "key": "total_returns", "width": "120px", "align": "end" },
			{ "title": _("Net Sales"), "key": "net_sales", "width": "120px", "align": "end" },
			{ "title": _("Status"), "key": "status", "width": "100px" }
		]

		return {
			"data": shifts,
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
def export_shift_report(date=None, pos_profile=None):
	"""Export shift report to Excel"""
	try:
		report_data = get_shift_report(date, pos_profile)

		if "error" in report_data:
			return {"error": report_data["error"]}

		# Generate Excel content
		content = "SHIFT REPORT\n"
		content += f"Date: {date}\n"
		content += f"Generated: {get_datetime().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

		# Summary
		summary = report_data["summary"]
		content += "SUMMARY\n"
		content += f"Total Shifts: {summary['total_shifts']}\n"
		content += f"Total Sales: {summary['total_sales']}\n"
		content += f"Total Returns: {summary['total_returns']}\n"
		content += f"Net Sales: {summary['net_sales']}\n\n"

		# Data
		content += "SHIFT DETAILS\n"
		content += "Shift ID\tEmployee\tStart Time\tTotal Sales\tTotal Returns\tNet Sales\tStatus\n"

		for shift in report_data["data"]:
			content += f"{shift.get('shift_report_id', '')}\t"
			content += f"{shift.get('owner', '')}\t"
			content += f"{shift.get('posting_time', '')}\t"
			content += f"{shift.get('total_sales', 0)}\t"
			content += f"{shift.get('total_returns', 0)}\t"
			content += f"{shift.get('net_sales', 0)}\t"
			content += f"{shift.get('status', '')}\n"

		# Create file
		file_name = f"shift_report_{date}.xlsx"
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

# Add similar export functions for other report types...