# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip
from frappe.utils import getdate, today
from posawesome.posawesome.utils.logging import get_logger

log = get_logger("coupon")


class POSCoupon(Document):
	def autoname(self):
		self.coupon_name = strip(self.coupon_name)
		self.name = self.coupon_name

		if not self.coupon_code:
			if self.coupon_type == "Promotional":
				self.coupon_code = "".join(i for i in self.coupon_name if not i.isdigit())[0:8].upper()
			elif self.coupon_type == "Gift Card":
				self.coupon_code = frappe.generate_hash()[:10].upper()

	def validate(self):
	    log.info("🎫 [COUPON_VALIDATE] Starting validation for coupon", {
	        "coupon_name": self.coupon_name,
	        "coupon_code": self.coupon_code,
	        "coupon_type": self.coupon_type
	    })

	    # Enhanced validation methods
	    self.validate_coupon_uniqueness()
	    self.validate_date_constraints()
	    self.validate_usage_constraints()
	    self.validate_customer_constraints()
	    self.validate_relationships()

	    # Legacy validation
	    if self.coupon_type == "Gift Card":
	        self.maximum_use = 1
	        if not self.customer:
	            frappe.throw(_("Please select the customer."))

	    pos_offer = frappe.get_doc("POS Offer", self.pos_offer)
	    if self.company != pos_offer.company:
	        frappe.throw(_("Please select the correct POS Offer with the same company."))
	    if not pos_offer.coupon_based:
	        frappe.throw(_("Please select Coupon Code Based POS Offer."))
	    if pos_offer.disable:
	        frappe.throw(_("POS Offer is disable."))
	    if pos_offer.valid_from and pos_offer.valid_from > getdate(self.valid_from):
	        self.valid_from = pos_offer.valid_from
	    if pos_offer.valid_upto and pos_offer.valid_upto < getdate(self.valid_upto):
	        self.valid_upto = pos_offer.valid_upto

	    log.info("🎫 [COUPON_VALIDATE] Validation completed successfully")

	def create_coupon_from_referral(self):
		if not self.customer:
			frappe.throw(_("Customer is required"))
		if not self.referral_code:
			frappe.throw(_("Referral Code is required"))
		ref_doc = None
		ref_code_exist = frappe.db.exists("Referral Code", self.referral_code)
		if not ref_code_exist:
			ref_doc = frappe.get_doc("Referral Code", {"referral_code": self.referral_code})
		else:
			ref_doc = frappe.get_doc("Referral Code", self.referral_code)
		if not ref_doc:
			frappe.throw(_("Referral Code {0} is not exists").format(self.referral_code))
		if ref_doc.disabled:
			frappe.throw(_("Referral Code {0} is disabled").format(self.referral_code))

		self.coupon_name = frappe.generate_hash()[:10].upper()
		self.coupon_type = "Gift Card"
		self.company = ref_doc.company
		self.pos_offer = ref_doc.customer_offer
		self.campaign = ref_doc.campaign
		self.referral_code = ref_doc.name
		self.save(ignore_permissions=True)

		if ref_doc.primary_offer:
			doc = frappe.new_doc("POS Coupon")
			doc.coupon_name = frappe.generate_hash()[:10].upper()
			doc.coupon_type = "Gift Card"
			doc.company = ref_doc.company
			doc.customer = ref_doc.customer
			doc.pos_offer = ref_doc.primary_offer
			doc.campaign = ref_doc.campaign
			doc.referral_code = ref_doc.name
			doc.save(ignore_permissions=True)

	def validate_coupon_uniqueness(self):
		"""Validate uniqueness based on unique indexes in schema"""
		# Check coupon_name uniqueness (đã có trong autoname)
		if self.coupon_name:
			existing = frappe.db.exists("POS Coupon", {
				"coupon_name": self.coupon_name,
				"name": ["!=", self.name]
			})
			if existing:
				frappe.throw(_("Coupon Name '{0}' already exists").format(self.coupon_name))

		# Check coupon_code uniqueness
		if self.coupon_code:
			existing = frappe.db.exists("POS Coupon", {
				"coupon_code": self.coupon_code.upper(),
				"name": ["!=", self.name]
			})
			if existing:
				frappe.throw(_("Coupon Code '{0}' already exists").format(self.coupon_code))

	def validate_date_constraints(self):
		"""Validate date fields based on schema"""
		if self.valid_from and self.valid_upto:
			if self.valid_from >= self.valid_upto:
				frappe.throw(_("Valid From date must be before Valid Upto date"))

		# Validate against POS Offer dates
		if self.pos_offer:
			pos_offer = frappe.get_doc("POS Offer", self.pos_offer)
			if pos_offer.valid_from and self.valid_from and self.valid_from < pos_offer.valid_from:
				frappe.throw(_("Coupon valid from date cannot be earlier than offer valid from date"))

			if pos_offer.valid_upto and self.valid_upto and self.valid_upto > pos_offer.valid_upto:
				frappe.throw(_("Coupon valid upto date cannot be later than offer valid upto date"))

	def validate_usage_constraints(self):
		"""Validate usage fields based on schema"""
		if self.maximum_use < 0:
			frappe.throw(_("Maximum use cannot be negative"))

		if self.used < 0:
			frappe.throw(_("Used count cannot be negative"))

		if self.maximum_use > 0 and self.used > self.maximum_use:
			frappe.throw(_("Used count ({0}) cannot exceed Maximum Use ({1})").format(
				self.used, self.maximum_use))

	def validate_customer_constraints(self):
		"""Validate customer-related fields based on schema"""
		if self.coupon_type == "Gift Card":
			if not self.customer:
				frappe.throw(_("Customer is required for Gift Card coupons"))

			# Validate customer exists
			if not frappe.db.exists("Customer", self.customer):
				frappe.throw(_("Selected customer does not exist"))

		elif self.coupon_type == "Promotional":
			if self.customer:
				frappe.throw(_("Promotional coupons cannot be assigned to specific customers"))

	def validate_relationships(self):
		"""Validate foreign key relationships based on schema"""
		# Validate POS Offer exists and is valid
		if not frappe.db.exists("POS Offer", self.pos_offer):
			frappe.throw(_("Selected POS Offer does not exist"))

		# Validate Company exists
		if self.company and not frappe.db.exists("Company", self.company):
			frappe.throw(_("Selected Company does not exist"))

		# Validate Customer exists (if specified)
		if self.customer and not frappe.db.exists("Customer", self.customer):
			frappe.throw(_("Selected Customer does not exist"))

		# Validate Campaign exists (if specified)
		if self.campaign and not frappe.db.exists("Campaign", self.campaign):
			frappe.throw(_("Selected Campaign does not exist"))


def check_coupon_code(coupon_code, customer=None, company=None):
	res = {"coupon": None}
	if not frappe.db.exists("POS Coupon", {"coupon_code": coupon_code.upper()}):
		res["msg"] = _("Sorry, this coupon code not exists")
		return res

	coupon = frappe.get_doc("POS Coupon", {"coupon_code": coupon_code.upper()})
	pos_offer = frappe.get_doc("POS Offer", coupon.pos_offer)

	if coupon.valid_from:
		if coupon.valid_from > getdate(today()):
			res["msg"] = _("Sorry, this coupon code's validity has not started")
			return res
	if coupon.valid_upto:
		if coupon.valid_upto < getdate(today()):
			res["msg"] = _("Sorry, this coupon code's validity has expired")
			return res
	if coupon.used and coupon.maximum_use and coupon.used >= coupon.maximum_use:
		res["msg"] = _("Sorry, this coupon code is no longer valid")
		return res

	if pos_offer.disable:
		res["msg"] = _("Sorry, this coupon code is no longer valid")
		return res
	if pos_offer.valid_from:
		if pos_offer.valid_from > getdate(today()):
			res["msg"] = _("Sorry, this coupon code's validity has not started")
			return res
	if pos_offer.valid_upto:
		if pos_offer.valid_upto < getdate(today()):
			res["msg"] = _("Sorry, this coupon code's validity has expired")
			return res

	if customer and coupon.coupon_type == "Gift Card":
		if customer != coupon.customer:
			res["msg"] = _("Sorry, this coupon code cannot be used by this customer")
			return res

	if company and coupon.company != company:
		res["msg"] = _("Sorry, this coupon code cannot be used by this company")
		return res

	if customer and coupon.one_use:
		count = frappe.db.count(
			"POS Coupon Detail",
			filters={
				"parentfield": "posa_coupons",
				"parenttype": "Sales Invoice",
				"docstatus": 1,
				"customer": customer,
			},
		)
		if count > 0:
			res["msg"] = _("Sorry, {0} have used this coupon before").format(customer)
			return res

	res["coupon"] = coupon
	res["msg"] = "Apply"
	return res


def validate_coupon_code(coupon_code, customer=None, company=None):
	res = check_coupon_code(coupon_code, customer, company)
	if not res.get("coupon"):
		frappe.throw(res.get("msg"))
	else:
		return res


def update_coupon_code_count(coupon_name, transaction_type):
	coupon = frappe.get_doc("POS Coupon", coupon_name)
	if coupon:
		if transaction_type == "used":
			if coupon.maximum_use and coupon.used >= coupon.maximum_use:
				frappe.throw(
					_("{0} Coupon used are {1}. Allowed quantity is exhausted").format(
						coupon.coupon_code, coupon.used
					)
				)
			else:
				coupon.used = coupon.used + 1
				coupon.save(ignore_permissions=True)

		elif transaction_type == "cancelled":
			if coupon.used > 0:
				coupon.used = coupon.used - 1
				coupon.save(ignore_permissions=True)


@frappe.whitelist()
def get_coupon_analytics(filters=None):
	"""Enhanced analytics dựa trên schema fields"""
	log.info("🎫 [COUPON_ANALYTICS] Getting coupon analytics", filters)

	if not filters:
		filters = {}

	# Build query dựa trên schema indexes
	query_filters = {}

	if filters.get("coupon_type"):
		query_filters["coupon_type"] = filters["coupon_type"]

	if filters.get("company"):
		query_filters["company"] = filters["company"]

	if filters.get("customer"):
		query_filters["customer"] = filters["customer"]

	if filters.get("campaign"):
		query_filters["campaign"] = filters["campaign"]

	# Date range filters
	if filters.get("from_date"):
		query_filters["creation"] = [">=", filters["from_date"]]

	if filters.get("to_date"):
		if "creation" in query_filters:
			query_filters["creation"].append("<=")
			query_filters["creation"].append(filters["to_date"])
		else:
			query_filters["creation"] = ["<=", filters["to_date"]]

	coupons = frappe.get_all("POS Coupon",
		filters=query_filters,
		fields=[
			"name", "coupon_code", "coupon_name", "coupon_type",
			"customer", "company", "campaign", "pos_offer",
			"valid_from", "valid_upto", "maximum_use", "used", "one_use",
			"creation", "modified"
		],
		order_by="creation desc"
	)

	analytics = []
	for coupon in coupons:
		# Get usage details từ POS Coupon Detail
		usage_details = frappe.get_all("POS Coupon Detail",
			filters={
				"parent": coupon.name,
				"parenttype": "Sales Invoice",
				"docstatus": 1  # Only successful transactions
			},
			fields=[
				"customer", "creation", "parent as invoice_name",
				"modified as used_date"
			],
			order_by="creation desc"
		)

		# Calculate metrics dựa trên schema fields
		usage_count = len(usage_details)
		usage_rate = (usage_count / coupon.maximum_use * 100) if coupon.maximum_use else 0

		# Calculate validity status
		validity_status = "active"
		today = getdate(today())

		if coupon.valid_upto and coupon.valid_upto < today:
			validity_status = "expired"
		elif coupon.valid_from and coupon.valid_from > today:
			validity_status = "not_started"
		elif coupon.maximum_use and coupon.used >= coupon.maximum_use:
			validity_status = "exhausted"

		analytics.append({
			"coupon_code": coupon.coupon_code,
			"coupon_name": coupon.coupon_name,
			"coupon_type": coupon.coupon_type,
			"customer": coupon.customer,
			"company": coupon.company,
			"campaign": coupon.campaign,
			"pos_offer": coupon.pos_offer,
			"valid_from": coupon.valid_from,
			"valid_upto": coupon.valid_upto,
			"maximum_use": coupon.maximum_use,
			"used_count": coupon.used,
			"usage_rate": usage_rate,
			"validity_status": validity_status,
			"created_on": coupon.creation,
			"last_used": usage_details[0]["used_date"] if usage_details else None,
			"usage_history": usage_details[:10],  # Last 10 usages
			"unique_customers": len(set(u["customer"] for u in usage_details if u["customer"]))
		})

	result = {
		"analytics": analytics,
		"summary": {
			"total_coupons": len(analytics),
			"active_coupons": len([c for c in analytics if c["validity_status"] == "active"]),
			"expired_coupons": len([c for c in analytics if c["validity_status"] == "expired"]),
			"exhausted_coupons": len([c for c in analytics if c["validity_status"] == "exhausted"]),
			"total_usage": sum(c["used_count"] for c in analytics),
			"average_usage_rate": sum(c["usage_rate"] for c in analytics) / len(analytics) if analytics else 0
		}
	}

	log.info("🎫 [COUPON_ANALYTICS] Analytics generated", {
		"total_coupons": result["summary"]["total_coupons"],
		"active_coupons": result["summary"]["active_coupons"]
	})

	return result
