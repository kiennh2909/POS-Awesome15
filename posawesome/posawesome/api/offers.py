# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.utils import nowdate
from posawesome.posawesome.doctype.pos_coupon.pos_coupon import check_coupon_code
from posawesome.posawesome.doctype.delivery_charges.delivery_charges import (
	get_applicable_delivery_charges as _get_applicable_delivery_charges,
)
from posawesome.posawesome.utils.logging import get_logger

log = get_logger("offers")


@frappe.whitelist()
def get_pos_coupon(coupon, customer, company):
	res = check_coupon_code(coupon, customer, company)
	return res


@frappe.whitelist()
def get_active_gift_coupons(customer, company):
	coupons = []
	coupons_data = frappe.get_all(
		"POS Coupon",
		filters={
			"company": company,
			"coupon_type": "Gift Card",
			"customer": customer,
			"used": 0,
		},
		fields=["coupon_code"],
	)
	if len(coupons_data):
		coupons = [i.coupon_code for i in coupons_data]
	return coupons


@frappe.whitelist()
def get_offers(profile, item_code=None, offer_title=None):
	log.info(f"[OFFERS] 📋 get_offers called for POS Profile: {profile}, item_code: {item_code}, offer_title: {offer_title}")

	date = nowdate()

	values = {
		"pos_profile": profile,
		"valid_from": date,
		"valid_upto": date,
	}

	# Build WHERE conditions
	where_conditions = """
        disable = 0 AND
        is_template = 0 AND
        (pos_profile is NULL OR pos_profile  = '' OR  pos_profile = %(pos_profile)s) AND
        (valid_from is NULL OR valid_from  = '' OR  valid_from <= %(valid_from)s) AND
        (valid_upto is NULL OR valid_from  = '' OR  valid_upto >= %(valid_upto)s)
    """

	# Add search conditions
	if item_code:
		where_conditions += " AND item = %(item_code)s"
		values["item_code"] = item_code
		log.info(f"[OFFERS] 📋 Adding exact item_code filter: {item_code}")

	if offer_title:
		where_conditions += " AND title LIKE %(offer_title)s"
		values["offer_title"] = f"%{offer_title}%"
		log.info(f"[OFFERS] 📋 Adding title LIKE filter: {offer_title}")

	log.info(f"[OFFERS] 📋 Query parameters: {values}")

	data = frappe.db.sql(
		f"""
        SELECT *
        FROM `tabPOS Offer`
        WHERE {where_conditions}
    """,
		values=values,
		as_dict=1,
	)

	log.info(f"[OFFERS] 📋 Found {len(data)} offers for POS Profile '{profile}' with filters")
	if data:
		offer_names = [f"{o.get('title', o.get('name'))} ({o.get('offer')})" for o in data[:5]]  # Log first 5 offers
		log.info(f"[OFFERS] 📋 Sample offers: {offer_names}")
		if len(data) > 5:
			log.info(f"[OFFERS] 📋 ... and {len(data) - 5} more offers")

	return data


@frappe.whitelist()
def get_applicable_delivery_charges(company, pos_profile, customer, shipping_address_name=None):
	return _get_applicable_delivery_charges(company, pos_profile, customer, shipping_address_name)
