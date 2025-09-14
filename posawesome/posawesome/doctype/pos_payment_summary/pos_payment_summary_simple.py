# -*- coding: utf-8 -*-
"""
Simplified version for testing import
"""

import frappe
from frappe import _
from frappe.model.document import Document

class POSPaymentSummary(Document):
    def validate(self):
        pass

@frappe.whitelist()
def create_payment_summaries_for_shift(shift_report_name):
    """Simple test function"""
    return {
        "success": True,
        "message": "Test function works",
        "data": {"shift_report": shift_report_name}
    }

@frappe.whitelist()
def get_payment_summaries_for_shift(shift_report_name):
    """Simple test function"""
    return {
        "success": True,
        "data": []
    }

def get_payment_method_type(payment_method):
    """Simple test function"""
    return "Cash"

@frappe.whitelist()
def initialize_payment_summaries_for_shift(shift_report_name):
    """Simple test function"""
    return {
        "success": True,
        "message": "Initialized successfully"
    }