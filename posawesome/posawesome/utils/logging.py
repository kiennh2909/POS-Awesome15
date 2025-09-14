# -*- coding: utf-8 -*-
"""
POS Awesome Logging Utilities

This module provides standardized logging helpers for the POS Awesome application.
"""

import frappe
import logging


def get_logger(name):
    """
    Get a standardized logger for POS Awesome modules.

    Args:
        name (str): Logger name (will be used as log file name)

    Returns:
        logging.Logger: Configured logger instance

    Usage:
        from posawesome.posawesome.utils.logging import get_logger
        log = get_logger("invoice")
        log.info("Processing invoice...")
    """
    # Get frappe logger with specified name
    logger = frappe.logger(name)

    # Set appropriate log level based on developer mode
    if frappe.conf.developer_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


# Pre-configured loggers for common modules
invoice_log = get_logger("invoice")
shift_report_log = get_logger("shift_report")
payment_log = get_logger("payment")
customer_log = get_logger("customer")