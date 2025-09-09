import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_days, get_datetime
from datetime import datetime, timedelta
import json

@frappe.whitelist()
def get_shift_analytics(filters=None):
	"""
	Get comprehensive shift analytics

	Args:
		filters (dict): Filter criteria

	Returns:
		dict: Analytics data
	"""
	try:
		default_filters = {
			"docstatus": 1,
			"status": "Closed"
		}

		if filters:
			default_filters.update(filters)

		# Get shift reports
		shift_reports = frappe.get_all(
			"POS Shift Report",
			filters=default_filters,
			fields=[
				"name", "shift_report_id", "opening_date", "opening_time",
				"total_opening_amount", "total_expected_closing", "total_actual_closing",
				"difference", "invoice_count", "total_sales", "total_returns",
				"opened_by", "verification_status"
			],
			order_by="opening_date desc, opening_time desc"
		)

		analytics = {
			"summary": calculate_analytics_summary(shift_reports),
			"trends": calculate_trends(shift_reports),
			"performance": calculate_performance_metrics(shift_reports),
			"variances": calculate_variance_analysis(shift_reports),
			"top_performers": get_top_performers(shift_reports)
		}

		return {
			"success": True,
			"data": analytics
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Analytics Error")
		return {
			"success": False,
			"message": str(e)
		}

def calculate_analytics_summary(shift_reports):
	"""Calculate summary statistics"""
	if not shift_reports:
		return {}

	total_shifts = len(shift_reports)
	total_sales = sum(frt.report.get("total_sales", 0) for report in shift_reports)
	total_returns = sum(frt.report.get("total_returns", 0) for report in shift_reports)
	total_opening = sum(frt.report.get("total_opening_amount", 0) for report in shift_reports)
	total_difference = sum(frt.report.get("difference", 0) for report in shift_reports)

	avg_sales_per_shift = total_sales / total_shifts if total_shifts > 0 else 0
	avg_invoices_per_shift = sum(frt.report.get("invoice_count", 0) for report in shift_reports) / total_shifts if total_shifts > 0 else 0

	return {
		"total_shifts": total_shifts,
		"total_sales": total_sales,
		"total_returns": total_returns,
		"net_sales": total_sales - total_returns,
		"total_opening_amount": total_opening,
		"total_variance": total_difference,
		"average_sales_per_shift": avg_sales_per_shift,
		"average_invoices_per_shift": avg_invoices_per_shift,
		"variance_percentage": (total_difference / total_opening * 100) if total_opening > 0 else 0
	}

def calculate_trends(shift_reports):
	"""Calculate sales trends over time"""
	trends = {}
	daily_sales = {}
	daily_invoices = {}

	for report in shift_reports:
		date = report.get("opening_date")
		if date:
			if date not in daily_sales:
				daily_sales[date] = 0
				daily_invoices[date] = 0

			daily_sales[date] += report.get("total_sales", 0)
			daily_invoices[date] += report.get("invoice_count", 0)

	# Sort by date
	sorted_dates = sorted(daily_sales.keys())

	trends["daily_sales"] = [{"date": date, "amount": daily_sales[date]} for date in sorted_dates]
	trends["daily_invoices"] = [{"date": date, "count": daily_invoices[date]} for date in sorted_dates]

	return trends

def calculate_performance_metrics(shift_reports):
	"""Calculate performance metrics"""
	performance = {
		"best_shift": None,
		"worst_shift": None,
		"most_efficient": None,
		"highest_variance": None
	}

	if not shift_reports:
		return performance

	best_sales = 0
	worst_sales = float('inf')
	highest_variance = 0
	most_efficient = 0

	for report in shift_reports:
		sales = report.get("total_sales", 0)
		variance = abs(report.get("difference", 0))
		invoices = report.get("invoice_count", 0)

		# Best performing shift by sales
		if sales > best_sales:
			best_sales = sales
			performance["best_shift"] = report

		# Worst performing shift
		if sales < worst_sales and sales > 0:
			worst_sales = sales
			performance["worst_shift"] = report

		# Highest variance
		if variance > highest_variance:
			highest_variance = variance
			performance["highest_variance"] = report

		# Most efficient (sales per invoice)
		if invoices > 0:
			efficiency = sales / invoices
			if efficiency > most_efficient:
				most_efficient = efficiency
				performance["most_efficient"] = report

	return performance

def calculate_variance_analysis(shift_reports):
	"""Analyze variances in shift reports"""
	variances = {
		"within_tolerance": 0,
		"over_tolerance": 0,
		"under_tolerance": 0,
		"variance_ranges": {
			"0-10": 0,
			"10-50": 0,
			"50-100": 0,
			"100+": 0
		}
	}

	tolerance = 10  # Default tolerance

	for report in shift_reports:
		difference = report.get("difference", 0)
		variance_abs = abs(difference)

		# Categorize by tolerance
		if variance_abs <= tolerance:
			variances["within_tolerance"] += 1
		elif difference > 0:
			variances["over_tolerance"] += 1
		else:
			variances["under_tolerance"] += 1

		# Categorize by variance range
		if variance_abs <= 10:
			variances["variance_ranges"]["0-10"] += 1
		elif variance_abs <= 50:
			variances["variance_ranges"]["10-50"] += 1
		elif variance_abs <= 100:
			variances["variance_ranges"]["50-100"] += 1
		else:
			variances["variance_ranges"]["100+"] += 1

	return variances

def get_top_performers(shift_reports):
	"""Get top performing users and shifts"""
	performers = {
		"top_sales_users": [],
		"top_invoice_users": [],
		"top_efficient_users": []
	}

	user_stats = {}

	# Aggregate by user
	for report in shift_reports:
		user = report.get("opened_by")
		if not user:
			continue

		if user not in user_stats:
			user_stats[user] = {
				"total_sales": 0,
				"total_invoices": 0,
				"shift_count": 0
			}

		user_stats[user]["total_sales"] += report.get("total_sales", 0)
		user_stats[user]["total_invoices"] += report.get("invoice_count", 0)
		user_stats[user]["shift_count"] += 1

	# Calculate averages and find top performers
	for user, stats in user_stats.items():
		avg_sales = stats["total_sales"] / stats["shift_count"] if stats["shift_count"] > 0 else 0
		avg_invoices = stats["total_invoices"] / stats["shift_count"] if stats["shift_count"] > 0 else 0
		efficiency = avg_sales / avg_invoices if avg_invoices > 0 else 0

		performers["top_sales_users"].append({
			"user": user,
			"avg_sales": avg_sales,
			"total_sales": stats["total_sales"],
			"shift_count": stats["shift_count"]
		})

		performers["top_invoice_users"].append({
			"user": user,
			"avg_invoices": avg_invoices,
			"total_invoices": stats["total_invoices"],
			"shift_count": stats["shift_count"]
		})

		performers["top_efficient_users"].append({
			"user": user,
			"efficiency": efficiency,
			"avg_sales": avg_sales,
			"avg_invoices": avg_invoices
		})

	# Sort and get top 5
	for key in performers:
		if key == "top_sales_users":
			performers[key].sort(key=lambda x: x["avg_sales"], reverse=True)
		elif key == "top_invoice_users":
			performers[key].sort(key=lambda x: x["avg_invoices"], reverse=True)
		else:  # top_efficient_users
			performers[key].sort(key=lambda x: x["efficiency"], reverse=True)

		performers[key] = performers[key][:5]

	return performers

@frappe.whitelist()
def get_shift_comparison_report(date_from, date_to, group_by="day"):
	"""
	Get shift comparison report for a date range

	Args:
		date_from (str): Start date
		date_to (str): End date
		group_by (str): Group by day/week/month

	Returns:
		dict: Comparison report
	"""
	try:
		# Get shift reports in date range
		shift_reports = frappe.get_all(
			"POS Shift Report",
			filters={
				"opening_date": ["between", [date_from, date_to]],
				"docstatus": 1,
				"status": "Closed"
			},
			fields=[
				"name", "opening_date", "opening_time", "total_sales",
				"total_returns", "invoice_count", "difference"
			],
			order_by="opening_date, opening_time"
		)

		comparison = {}

		for report in shift_reports:
			date = report.get("opening_date")
			if not date:
				continue

			# Group by specified period
			if group_by == "week":
				# Get week start date
				date_obj = getdate(date)
				week_start = date_obj - timedelta(days=date_obj.weekday())
				group_key = week_start.strftime("%Y-%m-%d")
			elif group_by == "month":
				group_key = date[:7]  # YYYY-MM
			else:  # day
				group_key = date

			if group_key not in comparison:
				comparison[group_key] = {
					"period": group_key,
					"total_sales": 0,
					"total_returns": 0,
					"net_sales": 0,
					"invoice_count": 0,
					"total_variance": 0,
					"shift_count": 0
				}

			comparison[group_key]["total_sales"] += report.get("total_sales", 0)
			comparison[group_key]["total_returns"] += report.get("total_returns", 0)
			comparison[group_key]["invoice_count"] += report.get("invoice_count", 0)
			comparison[group_key]["total_variance"] += report.get("difference", 0)
			comparison[group_key]["shift_count"] += 1

		# Calculate net sales
		for period in comparison.values():
			period["net_sales"] = period["total_sales"] - period["total_returns"]

		# Convert to list and sort
		result = list(comparison.values())
		result.sort(key=lambda x: x["period"])

		return {
			"success": True,
			"data": result,
			"summary": {
				"total_periods": len(result),
				"total_sales": sum(p["total_sales"] for p in result),
				"total_returns": sum(p["total_returns"] for p in result),
				"net_sales": sum(p["net_sales"] for p in result),
				"avg_sales_per_period": sum(p["total_sales"] for p in result) / len(result) if result else 0
			}
		}

	except Exception as e:
		frappe.log_error(str(e), "Get Shift Comparison Report Error")
		return {
			"success": False,
			"message": str(e)
		}

@frappe.whitelist()
def export_shift_analytics(filters=None, format="json"):
	"""
	Export shift analytics data

	Args:
		filters (dict): Filter criteria
		format (str): Export format (json/csv)

	Returns:
		dict: Export result
	"""
	try:
		analytics = get_shift_analytics(filters)

		if not analytics["success"]:
			return analytics

		data = analytics["data"]

		if format == "csv":
			# Convert to CSV format
			csv_data = convert_analytics_to_csv(data)
			return {
				"success": True,
				"data": csv_data,
				"format": "csv"
			}
		else:
			return analytics

	except Exception as e:
		frappe.log_error(str(e), "Export Shift Analytics Error")
		return {
			"success": False,
			"message": str(e)
		}

def convert_analytics_to_csv(analytics_data):
	"""Convert analytics data to CSV format"""
	# This would implement CSV conversion logic
	# For now, return placeholder
	return "CSV conversion not implemented yet"