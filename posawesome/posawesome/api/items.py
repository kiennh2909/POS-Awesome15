# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.utils import nowdate, flt, cstr
from erpnext.stock.get_item_details import get_item_details
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from frappe.utils.background_jobs import enqueue
from erpnext.stock.doctype.batch.batch import (
    get_batch_no,
    get_batch_qty,
)
from frappe.utils.caching import redis_cache
from typing import List, Dict
from posawesome.posawesome.utils.logging import get_logger

def get_seearch_items_conditions(item_code, serial_no, batch_no, barcode):
    """Build item search conditions safely."""
    # Gracefully handle missing item_code values to avoid TypeErrors
    item_code = item_code or ""

    if serial_no or batch_no or barcode:
        return " and name = {0}".format(frappe.db.escape(item_code))

    return """ and (name like {item_code} or item_name like {item_code})""".format(
        item_code=frappe.db.escape("%" + item_code + "%")
    )


def get_item_group_condition(pos_profile):
    cond = " and 1=1"
    item_groups = get_item_groups(pos_profile)
    if item_groups:
        cond = " and item_group in (%s)" % (", ".join(["%s"] * len(item_groups)))

    return cond % tuple(item_groups)


def search_serial_or_batch_or_barcode_number(search_value, search_serial_no):
    """Search for items by serial number, batch number, or barcode."""
    # Search by barcode
    barcode_data = frappe.db.get_value(
        "Item Barcode", {"barcode": search_value}, ["parent as item_code", "barcode"], as_dict=True
    )
    if barcode_data:
        return {"item_code": barcode_data.item_code, "barcode": barcode_data.barcode}
    
    # Search by batch number
    batch_data = frappe.db.get_value(
        "Batch", {"name": search_value}, ["item as item_code", "name as batch_no"], as_dict=True
    )
    if batch_data:
        return {"item_code": batch_data.item_code, "batch_no": batch_data.batch_no}
    
    # Search by serial number if enabled
    if search_serial_no:
        serial_data = frappe.db.get_value(
            "Serial No", {"name": search_value}, ["item_code", "name as serial_no"], as_dict=True
        )
        if serial_data:
            return {"item_code": serial_data.item_code, "serial_no": serial_data.serial_no}
    
    return {}


def get_stock_availability(item_code, warehouse):
    """Lấy stock từ Bin - Optimized for performance"""
    actual_qty = frappe.db.get_value(
        "Bin",
        filters={
            "item_code": item_code,
            "warehouse": warehouse
        },
        fieldname="actual_qty"
    ) or 0.0
    return actual_qty


@redis_cache(ttl=30)  # Cache 30 giây
def get_stock_from_bin(item_code, warehouse):
    """Lấy stock từ Bin với performance tối ưu + cache"""
    return frappe.db.get_value(
        "Bin",
        filters={
            "item_code": item_code,
            "warehouse": warehouse
        },
        fieldname="actual_qty"
    ) or 0.0


@redis_cache(ttl=30)
def get_available_stock_from_bin(item_code, warehouse):
    """Lấy stock available (actual - reserved) từ Bin với cache"""
    bin_data = frappe.db.get_value(
        "Bin",
        filters={
            "item_code": item_code,
            "warehouse": warehouse
        },
        fieldname=["actual_qty", "reserved_qty"],
        as_dict=True
    )

    if bin_data:
        available_qty = bin_data.actual_qty - (bin_data.reserved_qty or 0)
        return available_qty

    return 0.0


def get_stock_from_bin_bulk(item_codes, warehouse):
    """Lấy stock cho nhiều items cùng lúc từ Bin - Performance optimized"""
    if not item_codes:
        return {}

    bin_data = frappe.get_all(
        "Bin",
        filters={
            "item_code": ["in", item_codes],
            "warehouse": warehouse
        },
        fields=["item_code", "actual_qty", "reserved_qty"]
    )

    # Convert to dict for fast lookup
    stock_map = {}
    for bin_item in bin_data:
        stock_map[bin_item.item_code] = {
            "actual_qty": bin_item.actual_qty or 0,
            "available_qty": (bin_item.actual_qty or 0) - (bin_item.reserved_qty or 0)
        }

    return stock_map


def clear_stock_cache():
    """Clear Redis cache cho các hàm stock"""
    try:
        # Clear cache cho các hàm stock
        frappe.cache().delete_key("get_stock_from_bin")
        frappe.cache().delete_key("get_available_stock_from_bin")
        frappe.cache().delete_key("get_stock_availability")
        print("Stock cache cleared successfully")
    except Exception as e:
        print(f"Error clearing stock cache: {e}")


@frappe.whitelist()
def get_stock_unified(item_code, warehouse, source="bin"):
    """
    Hàm unified để lấy stock với tùy chọn nguồn
    - source="bin": Sử dụng Bin (nhanh)
    - source="stock_ledger": Sử dụng Stock Ledger Entry (chính xác)
    - source="auto": Tự động chọn
    """
    if source == "bin":
        return get_stock_from_bin(item_code, warehouse)
    elif source == "stock_ledger":
        return get_stock_availability_from_ledger(item_code, warehouse)
    else:  # auto
        # Thử Bin trước, nếu không có thì dùng Stock Ledger
        bin_qty = get_stock_from_bin(item_code, warehouse)
        if bin_qty > 0:
            return bin_qty
        else:
            return get_stock_availability_from_ledger(item_code, warehouse)


def get_stock_availability_from_ledger(item_code, warehouse):
    """Lấy stock từ Stock Ledger Entry (for fallback)"""
    actual_qty = (
        frappe.db.get_value(
            "Stock Ledger Entry",
            filters={
                "item_code": item_code,
                "warehouse": warehouse,
                "is_cancelled": 0,
            },
            fieldname="qty_after_transaction",
            order_by="posting_date desc, posting_time desc, creation desc",
        )
        or 0.0
    )
    return actual_qty

def get_item_group_condition(pos_profile_name: str) -> str:
    """Tạo điều kiện lọc theo nhóm hàng từ POS Profile."""
    item_groups = get_item_groups(pos_profile_name)
    if not item_groups:
        return ""
    
    # Sử dụng frappe.db.escape để đảm bảo an toàn
    placeholders = ", ".join(["%s"] * len(item_groups))
    return f"AND item_group IN ({placeholders}) " % tuple(item_groups)

def search_serial_or_batch_or_barcode_number(search_value: str, search_serial_no: int) -> Dict:
    """
    Tìm kiếm Item Code dựa trên Barcode, Batch No, hoặc Serial No.
    Thứ tự ưu tiên: Barcode > Batch > Serial No.
    """
    # Tìm theo Barcode
    barcode_data = frappe.db.get_value(
        "Item Barcode", {"barcode": search_value}, ["parent as item_code", "barcode"], as_dict=True
    )
    if barcode_data:
        return {"item_code": barcode_data.item_code, "barcode": barcode_data.barcode}

    # Tìm theo Batch No
    batch_data = frappe.db.get_value(
        "Batch", {"name": search_value}, ["item as item_code", "name as batch_no"], as_dict=True
    )
    if batch_data:
        return {"item_code": batch_data.item_code, "batch_no": batch_data.batch_no}

    # Tìm theo Serial No (nếu được bật)
    if search_serial_no:
        serial_data = frappe.db.get_value(
            "Serial No", {"name": search_value}, ["item_code", "name as serial_no"], as_dict=True
        )
        if serial_data:
            return {"item_code": serial_data.item_code, "serial_no": serial_data.serial_no}

    return {}

def _to_positive_int(value) -> int | None:
    """Chuyển đổi giá trị sang số nguyên không âm."""
    try:
        ivalue = int(value)
        return ivalue if ivalue >= 0 else None
    except (TypeError, ValueError):
        return None

# --- CÁC HÀM CHÍNH (ĐÃ VIẾT LẠI HOÀN TOÀN) ---

@frappe.whitelist()
def get_items(
    pos_profile: str,
    price_list: str = None,
    item_group: str = "",
    search_value: str = "",
    customer: str = None,
    limit: int = None,
    offset: int = None,
):
    """
    Hàm Wrapper bên ngoài, xử lý cache.
    Gọi đến hàm _get_items_optimized để thực hiện logic chính.
    """
    _pos_profile = json.loads(pos_profile)
    use_server_cache = _pos_profile.get("posa_use_server_cache")

    @redis_cache(ttl=60)
    def __get_items_cached(*args, **kwargs):
        return _get_items_optimized(*args, **kwargs)

    # Nếu cache được bật, sử dụng hàm có cache
    if use_server_cache:
        return __get_items_cached(pos_profile, price_list, item_group, search_value, customer, limit, offset)
    
    # Ngược lại, gọi trực tiếp
    return _get_items_optimized(pos_profile, price_list, item_group, search_value, customer, limit, offset)


def _get_items_optimized(
    pos_profile_json: str,
    price_list: str = None,
    item_group_filter: str = "",
    search_value: str = "",
    customer: str = None,
    limit: int = None,
    offset: int = None,
):
    """
    Phiên bản tối ưu của get_items.
    1. Lấy danh sách sản phẩm có tồn kho từ `Bin` trước (nếu cần).
    2. Lấy thông tin chính của Item.
    3. Lấy thông tin phụ (giá, barcode, UOM) bằng các truy vấn hàng loạt.
    4. Tổng hợp dữ liệu và trả về.
    """
    pos_profile = json.loads(pos_profile_json)
    warehouse = pos_profile.get("warehouse")
    company = pos_profile.get("company")

    # --- BƯỚC 1: XÂY DỰNG BỘ LỌC CHÍNH (FILTERS) ---
    item_filters = {"disabled": 0, "is_sales_item": 1, "is_fixed_asset": 0}
    
    # Lọc theo nhóm hàng từ POS Profile
    profile_item_groups = get_item_groups(pos_profile.get("name"))
    if profile_item_groups:
        item_filters["item_group"] = ["in", profile_item_groups]
    
    # Lọc theo nhóm hàng người dùng chọn trên UI
    if item_group_filter:
        item_filters["item_group"] = ["like", f"%{item_group_filter}%"]

    if not pos_profile.get("posa_show_template_items"):
        item_filters["has_variants"] = 0

    # --- BƯỚC 2: TỐI ƯU - LẤY TỒN KHO TỪ `Bin` TRƯỚC ---
    stock_map = {}
    if pos_profile.get("posa_display_items_in_stock"):
        # Sử dụng bulk query để lấy stock cho tất cả items
        bin_items = frappe.get_all(
            "Bin",
            filters={"warehouse": warehouse, "actual_qty": [">", 0]},
            fields=["item_code", "actual_qty", "reserved_qty"]
        )
        if not bin_items:
            return []  # Tối ưu: Nếu không có gì trong kho, trả về rỗng ngay lập tức

        in_stock_item_codes = [b.item_code for b in bin_items]
        # Tạo stock_map với cả actual_qty và available_qty
        stock_map = {}
        for b in bin_items:
            stock_map[b.item_code] = {
                "actual_qty": b.actual_qty or 0,
                "available_qty": (b.actual_qty or 0) - (b.reserved_qty or 0)
            }
        item_filters["name"] = ["in", in_stock_item_codes]

    # --- BƯỚC 3: XỬ LÝ TÌM KIẾM ---
    or_filters = []
    if search_value:
        search_data = search_serial_or_batch_or_barcode_number(search_value, pos_profile.get("posa_search_serial_no"))
        item_code_from_search = search_data.get("item_code", search_value)

        if search_data.get("item_code"):  # Tìm thấy chính xác
            item_filters["name"] = item_code_from_search
        else:  # Tìm kiếm tương đối
            or_filters = [
                ["name", "like", f"%{item_code_from_search}%"],
                ["item_name", "like", f"%{item_code_from_search}%"]
            ]

    # --- BƯỚC 4: TRUY VẤN LẤY DANH SÁCH ITEM CHÍNH ---
    limit_page_length = _to_positive_int(limit)
    limit_start = _to_positive_int(offset)
    if limit_page_length is None and pos_profile.get("pose_use_limit_search"):
        limit_page_length = pos_profile.get("posa_search_limit", 200)
        if pos_profile.get("posa_force_reload_items") and search_value:
            limit_page_length = None

    items_data = frappe.get_all(
        "Item",
        filters=item_filters,
        or_filters=or_filters or None,
        fields=[
            "name as item_code", "item_name", "description", "stock_uom", "image",
            "is_stock_item", "has_variants", "variant_of", "item_group",
            "has_batch_no", "has_serial_no", "max_discount", "brand"
        ],
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by="item_name ASC"
    )

    if not items_data:
        return []

    item_codes = [d.item_code for d in items_data]
    result = []
    
    # --- BƯỚC 5: TRUY VẤN HÀNG LOẠT (BULK FETCH) CHO DỮ LIỆU PHỤ ---
    today = nowdate()
    selling_price_list = price_list or pos_profile.get("selling_price_list")
    
    # Lấy giá hàng loạt
    price_data = frappe.get_all(
        "Item Price",
        fields=["item_code", "price_list_rate", "currency", "uom"],
        filters={
            "price_list": selling_price_list, "item_code": ["in", item_codes],
            "selling": 1, "valid_from": ["<=", today],
            "customer": ["in", ["", None, customer]]
        },
        or_filters=[["valid_upto", ">=", today], ["valid_upto", "is", "not set"]],
    )
    prices_map = {}
    for p in price_data:
        prices_map.setdefault(p.item_code, {})[p.get("uom") or "None"] = p

    # Lấy barcode hàng loạt
    barcode_data = frappe.get_all("Item Barcode", fields=["parent", "barcode", "posa_uom"], filters={"parent": ["in", item_codes]})
    barcodes_map = {}
    for b in barcode_data:
        barcodes_map.setdefault(b.parent, []).append({"barcode": b.barcode, "posa_uom": b.posa_uom})

    # Lấy UOM hàng loạt
    uom_data = frappe.get_all("UOM Conversion Detail", fields=["parent", "uom", "conversion_factor"], filters={"parent": ["in", item_codes]})
    uoms_map = {}
    for u in uom_data:
        uoms_map.setdefault(u.parent, []).append({"uom": u.uom, "conversion_factor": u.conversion_factor})

    # --- BƯỚC 6: TỔNG HỢP DỮ LIỆU (KHÔNG TRUY VẤN DB TRONG VÒNG LẶP) ---
    for item in items_data:
        item_code = item.item_code
        
        # Lấy giá từ map
        item_prices = prices_map.get(item_code, {})
        item_price = item_prices.get(item.stock_uom) or item_prices.get("None") or {}
        
        # Lấy UOMs từ map và thêm stock_uom nếu chưa có
        item_uoms = uoms_map.get(item_code, [])
        if item.stock_uom and not any(u['uom'] == item.stock_uom for u in item_uoms):
            item_uoms.append({"uom": item.stock_uom, "conversion_factor": 1.0})

        # Lấy tồn kho từ stock_map đã có (tối ưu từ Bin)
        stock_info = stock_map.get(item_code, {"actual_qty": 0, "available_qty": 0})
        actual_qty = stock_info["actual_qty"]

        row = {
            **item,
            "rate": item_price.get("price_list_rate", 0),
            "currency": item_price.get("currency") or pos_profile.get("currency"),
            "item_barcode": barcodes_map.get(item_code, []),
            "actual_qty": actual_qty,  # ← Từ Bin (đã có sẵn)
            "item_uoms": item_uoms,
            # Giữ các trường này để tương thích với frontend
            "serial_no_data": [],
            "batch_no_data": [],
            "attributes": "",
            "item_attributes": "",
        }
        result.append(row)
        
    return result

# @frappe.whitelist()


# @frappe.whitelist()
# def get_items(
#     pos_profile,
#     price_list=None,
#     item_group="",
#     search_value="",
#     customer=None,
#     limit=None,
#     offset=None,
# ):
#     _pos_profile = json.loads(pos_profile)
#     use_price_list = _pos_profile.get("posa_use_server_cache")

#     @redis_cache(ttl=60)
#     def __get_items(
#         pos_profile,
#         price_list,
#         item_group,
#         search_value,
#         customer=None,
#         limit=None,
#         offset=None,
#     ):
#         return _get_items(
#             pos_profile,
#             price_list,
#             item_group,
#             search_value,
#             customer,
#             limit,
#             offset,
#         )

#     def _get_items(
#         pos_profile,
#         price_list,
#         item_group,
#         search_value,
#         customer=None,
#         limit=None,
#         offset=None,
#     ):
#         pos_profile = json.loads(pos_profile)
#         condition = ""
        
#         # Clear quantity cache to ensure fresh values on each search
#         try:
#             if hasattr(frappe.local.cache, "delete_key"):
#                 frappe.local.cache.delete_key('bin_qty_cache')
#             elif frappe.cache().get_value('bin_qty_cache'):
#                 frappe.cache().delete_value('bin_qty_cache')
#         except Exception as e:
#             frappe.log_error(f"Error clearing bin_qty_cache: {str(e)}", "POS Awesome")
        
#         today = nowdate()
#         warehouse = pos_profile.get("warehouse")
#         use_limit_search = pos_profile.get("pose_use_limit_search")
#         search_serial_no = pos_profile.get("posa_search_serial_no")
#         search_batch_no = pos_profile.get("posa_search_batch_no")
#         posa_show_template_items = pos_profile.get("posa_show_template_items")
#         posa_display_items_in_stock = pos_profile.get("posa_display_items_in_stock")
#         search_limit = 0

#         if not price_list:
#             price_list = pos_profile.get("selling_price_list")

#         limit_clause = ""

#         def _to_positive_int(value):
#             """Convert the input to a non-negative integer if possible."""
#             try:
#                 ivalue = int(value)
#                 return ivalue if ivalue >= 0 else None
#             except (TypeError, ValueError):
#                 return None

#         limit = _to_positive_int(limit)
#         offset = _to_positive_int(offset)

#         if limit is not None:
#             limit_clause = f" LIMIT {limit}"
#             if offset:
#                 limit_clause += f" OFFSET {offset}"

#         condition += get_item_group_condition(pos_profile.get("name"))

#         if use_limit_search and limit is None:
#             search_limit = pos_profile.get("posa_search_limit") or 500
#             data = {}
#             if search_value:
#                 data = search_serial_or_batch_or_barcode_number(
#                     search_value, search_serial_no
#                 )

#             item_code = data.get("item_code") if data.get("item_code") else search_value
#             serial_no = data.get("serial_no") if data.get("serial_no") else ""
#             batch_no = data.get("batch_no") if data.get("batch_no") else ""
#             barcode = data.get("barcode") if data.get("barcode") else ""

#             condition += get_seearch_items_conditions(
#                 item_code, serial_no, batch_no, barcode
#             )
#             if item_group:
#                 # Escape item_group to avoid SQL errors with special characters
#                 safe_item_group = frappe.db.escape("%" + item_group + "%")
#                 condition += " AND item_group like {item_group}".format(
#                     item_group=safe_item_group
#                 )

#             # Always apply a search limit when limit search is enabled
#             limit_clause = " LIMIT {search_limit}".format(search_limit=search_limit)

#             # If force reload is enabled and the user is explicitly searching,
#             # remove the limit to return all matching items
#             if pos_profile.get("posa_force_reload_items") and search_value:
#                 limit_clause = ""

#         if not posa_show_template_items:
#             condition += " AND has_variants = 0"

#         result = []

#         # Build ORM filters
#         filters = {
#             "disabled": 0,
#             "is_sales_item": 1,
#             "is_fixed_asset": 0
#         }
        
#         # Add item group filter
#         item_groups = get_item_groups(pos_profile.get("name"))
#         if item_groups:
#             filters["item_group"] = ["in", item_groups]
        
#         # Add search conditions
#         or_filters = []
#         if use_limit_search and search_value:
#             data = search_serial_or_batch_or_barcode_number(
#                 search_value, search_serial_no
#             )
#             item_code = data.get("item_code") if data.get("item_code") else search_value
            
#             or_filters = [
#                 ["name", "like", f"%{item_code}%"],
#                 ["item_name", "like", f"%{item_code}%"]
#             ]
            
#             # Check for exact barcode match
#             if data.get("item_code"):
#                 filters["name"] = data.get("item_code")
#                 or_filters = []
        
#         if item_group:
#             filters["item_group"] = ["like", f"%{item_group}%"]
        
#         if not posa_show_template_items:
#             filters["has_variants"] = 0
        
#         # Determine limit
#         limit_page_length = None
#         limit_start = None
        
#         if limit is not None:
#             limit_page_length = limit
#             if offset:
#                 limit_start = offset
#         elif use_limit_search:
#             limit_page_length = search_limit
#             if pos_profile.get("posa_force_reload_items") and search_value:
#                 limit_page_length = None
        
#         items_data = frappe.get_all(
#             "Item",
#             filters=filters,
#             or_filters=or_filters if or_filters else None,
#             fields=[
#                 "name as item_code",
#                 "item_name",
#                 "description", 
#                 "stock_uom",
#                 "image",
#                 "is_stock_item",
#                 "has_variants",
#                 "variant_of",
#                 "item_group",
#                 "idx",
#                 "has_batch_no",
#                 "has_serial_no",
#                 "max_discount",
#                 "brand"
#             ],
#             limit_start=limit_start,
#             limit_page_length=limit_page_length,
#             order_by="item_name asc"
#         )

#         if items_data:
#             items = [d.item_code for d in items_data]
#             price_list_currency = frappe.db.get_value("Price List", price_list, "currency")
#             item_prices_data = frappe.get_all(
#                 "Item Price",
#                 fields=["item_code", "price_list_rate", "currency", "uom"],
#                 filters={
#                     "price_list": price_list,
#                     "item_code": ["in", items],
#                     "currency": price_list_currency or pos_profile.get("currency"),
#                     "selling": 1,
#                     "valid_from": ["<=", today],
#                     "customer": ["in", ["", None, customer]],
#                 },
#                 or_filters=[
#                     ["valid_upto", ">=", today],
#                     ["valid_upto", "in", ["", None]],
#                 ],
#                 order_by="valid_from ASC, valid_upto DESC",
#             )

#             item_prices = {}
#             for d in item_prices_data:
#                 item_prices.setdefault(d.item_code, {})
#                 item_prices[d.item_code][d.get("uom") or "None"] = d

#             for item in items_data:
#                 item_code = item.item_code
#                 item_price = {}
#                 if item_prices.get(item_code):
#                     item_price = (
#                         item_prices.get(item_code).get(item.stock_uom)
#                         or item_prices.get(item_code).get("None")
#                         or {}
#                     )
#                 item_barcode = frappe.get_all(
#                     "Item Barcode",
#                     filters={"parent": item_code},
#                     fields=["barcode", "posa_uom"],
#                 )
#                 batch_no_data = []
#                 if search_batch_no or item.has_batch_no:
#                     batch_list = get_batch_qty(warehouse=warehouse, item_code=item_code)
#                     if batch_list:
#                         for batch in batch_list:
#                             if batch.qty > 0 and batch.batch_no:
#                                 batch_doc = frappe.get_cached_doc(
#                                     "Batch", batch.batch_no
#                                 )
#                                 if (
#                                     str(batch_doc.expiry_date) > str(today)
#                                     or batch_doc.expiry_date in ["", None]
#                                 ) and batch_doc.disabled == 0:
#                                     batch_no_data.append(
#                                         {
#                                             "batch_no": batch.batch_no,
#                                             "batch_qty": batch.qty,
#                                             "expiry_date": batch_doc.expiry_date,
#                                             "batch_price": batch_doc.posa_batch_price,
#                                             "manufacturing_date": batch_doc.manufacturing_date,
#                                         }
#                                     )
#                 serial_no_data = []
#                 if search_serial_no or item.has_serial_no:
#                     serial_no_data = frappe.get_all(
#                         "Serial No",
#                         filters={
#                             "item_code": item_code,
#                             "status": "Active",
#                             "warehouse": warehouse,
#                         },
#                         fields=["name as serial_no"],
#                     )
#                 # Fetch UOM conversion details for the item
#                 uoms = frappe.get_all(
#                     "UOM Conversion Detail",
#                     filters={"parent": item_code},
#                     fields=["uom", "conversion_factor"],
#                 )
#                 stock_uom = item.stock_uom
#                 if stock_uom and not any(u.get("uom") == stock_uom for u in uoms):
#                     uoms.append({"uom": stock_uom, "conversion_factor": 1.0})
#                 item_stock_qty = 0
#                 if pos_profile.get("posa_display_items_in_stock") or use_limit_search:
#                     item_stock_qty = get_stock_availability(
#                         item_code, pos_profile.get("warehouse")
#                     )
#                 attributes = ""
#                 if pos_profile.get("posa_show_template_items") and item.has_variants:
#                     attributes = get_item_attributes(item.item_code)
#                 item_attributes = ""
#                 if pos_profile.get("posa_show_template_items") and item.variant_of:
#                     item_attributes = frappe.get_all(
#                         "Item Variant Attribute",
#                         fields=["attribute", "attribute_value"],
#                         filters={"parent": item.item_code, "parentfield": "attributes"},
#                     )
#                 if posa_display_items_in_stock and (
#                     not item_stock_qty or item_stock_qty < 0
#                 ):
#                     pass
#                 else:
#                     row = {}
#                     row.update(item)
#                     row.update(
#                         {
#                             "rate": item_price.get("price_list_rate") or 0,
#                             "currency": item_price.get("currency")
#                             or price_list_currency
#                             or pos_profile.get("currency"),
#                             "item_barcode": item_barcode or [],
#                             "actual_qty": item_stock_qty or 0,
#                             "serial_no_data": serial_no_data or [],
#                             "batch_no_data": batch_no_data or [],
#                             "attributes": attributes or "",
#                             "item_attributes": item_attributes or "",
#                             "item_uoms": uoms or [],
#                         }
#                     )
#                     result.append(row)
#         return result

#     if use_price_list:
#         return __get_items(
#             pos_profile,
#             price_list,
#             item_group,
#             search_value,
#             customer,
#             limit,
#             offset,
#         )
#     else:
#         return _get_items(
#             pos_profile,
#             price_list,
#             item_group,
#             search_value,
#             customer,
#             limit,
#             offset,
#         )


@frappe.whitelist()
def get_items_groups():
    return frappe.db.sql(
        """select name from `tabItem Group`
        where is_group = 0 order by name limit 500""", as_dict=1
    )


@frappe.whitelist()
def get_items_details(pos_profile, items_data, price_list=None):
    pos_profile = json.loads(pos_profile)
    items_data = json.loads(items_data)
    warehouse = pos_profile.get("warehouse")
    company = pos_profile.get("company")
    result = []
    
    if items_data:
        for item in items_data:
            item_code = item.get("item_code")
            if item_code:
                item_detail = get_item_detail(
                    json.dumps(item),
                    warehouse=warehouse, 
                    price_list=price_list or pos_profile.get("selling_price_list"),
                    company=company
                )
                if item_detail:
                    result.append(item_detail)
    
    return result


def get_item_optional_attributes(item_code):
	"""Get optional attributes for an item."""
	return frappe.get_all(
		"Item Variant Attribute",
		fields=["attribute", "attribute_value"],
		filters={"parent": item_code, "parentfield": "attributes"},
	)

def get_item_variants(pos_profile, parent_item_code, price_list=None, customer=None):
	pos_profile = json.loads(pos_profile)
	price_list = price_list or pos_profile.get("selling_price_list")

	fields = [
		"name as item_code",
		"item_name",
		"description",
		"stock_uom",
		"image",
		"is_stock_item",
		"has_variants",
		"variant_of",
		"item_group",
		"idx",
		"has_batch_no",
		"has_serial_no",
		"max_discount",
		"brand",
	]

	items_data = frappe.get_all(
		"Item",
		filters={"variant_of": parent_item_code, "disabled": 0},
		fields=fields,
		order_by="item_name asc",
	)

	if not items_data:
		return []

	details = get_items_details(
		json.dumps(pos_profile),
		json.dumps(items_data),
		price_list=price_list,
	)

	detail_map = {d["item_code"]: d for d in details}
	result = []
	for item in items_data:
		item_barcode = frappe.get_all(
			"Item Barcode",
			filters={"parent": item["item_code"]},
			fields=["barcode", "posa_uom"],
		)
		item["item_barcode"] = item_barcode or []
		if detail_map.get(item["item_code"]):
			item.update(detail_map[item["item_code"]])
		result.append(item)

	return result

@frappe.whitelist()
def get_item_tax_info(item_code, price_list=None, pos_profile=None):
    """Lấy thông tin thuế cho MISA API từ Item + Item Price với ưu tiên theo thứ tự"""

    # Lấy từ Item (thuộc tính cố định)
    item_doc = frappe.get_doc("Item", item_code)

    # Lấy POS Profile để lấy Sales Taxes and Charges Template
    pos_profile_doc = None
    if pos_profile:
        try:
            pos_profile_data = json.loads(pos_profile) if isinstance(pos_profile, str) else pos_profile
            pos_profile_name = pos_profile_data.get("name") if isinstance(pos_profile_data, dict) else pos_profile
            pos_profile_doc = frappe.get_doc("POS Profile", pos_profile_name)
        except:
            pass

    # === ƯU TIÊN 1: Item Tax Template Detail ===
    vat_rate = None
    # Lấy Item Tax Template từ bảng Item Tax (child table của Item)
    item_tax_data = frappe.get_all(
        "Item Tax",
        filters={"parent": item_code},
        fields=["item_tax_template"],
        limit=1
    )
    item_tax_template = item_tax_data[0].get("item_tax_template") if item_tax_data else None

    if item_tax_template:
        tax_template_details = frappe.get_all(
            "Item Tax Template Detail",
            filters={"parent": item_tax_template},
            fields=["tax_rate"],
            limit=1
        )
        if tax_template_details and tax_template_details[0].get("tax_rate"):
            vat_rate = str(tax_template_details[0]["tax_rate"])
            get_logger("items").info(f"[VAT_DEBUG] 📊 Priority 1 - Using VAT rate from Item Tax Template: {vat_rate}%")

    # === ƯU TIÊN 2: Sales Taxes and Charges Template từ POS Profile ===
    if not vat_rate and pos_profile_doc and pos_profile_doc.sales_taxes_and_charges_template:
        sales_tax_template = pos_profile_doc.sales_taxes_and_charges_template
        tax_template_details = frappe.get_all(
            "Sales Taxes and Charges",
            filters={"parent": sales_tax_template},
            fields=["rate"],
            limit=1
        )
        if tax_template_details and tax_template_details[0].get("rate"):
            vat_rate = str(tax_template_details[0]["rate"])
            get_logger("items").info(f"[VAT_DEBUG] 📊 Priority 2 - Using VAT rate from POS Profile Sales Tax Template: {vat_rate}%")

    # === ƯU TIÊN 3: Sales Taxes and Charges Template từ Company ===
    if not vat_rate and pos_profile_doc:
        company = pos_profile_doc.company
        company_doc = frappe.get_doc("Company", company)
        if company_doc.default_sales_taxes_and_charges_template:
            sales_tax_template = company_doc.default_sales_taxes_and_charges_template
            tax_template_details = frappe.get_all(
                "Sales Taxes and Charges",
                filters={"parent": sales_tax_template},
                fields=["rate"],
                limit=1
            )
            if tax_template_details and tax_template_details[0].get("rate"):
                vat_rate = str(tax_template_details[0]["rate"])
                get_logger("items").info(f"[VAT_DEBUG] 📊 Priority 3 - Using VAT rate from Company Sales Tax Template: {vat_rate}%")

    # === FALLBACK: Custom VAT Rate hoặc mặc định 0% ===
    if not vat_rate:
        vat_rate = item_doc.custom_vat_rate or "0"  # Mặc định VAT 0%
        if item_doc.custom_vat_rate:
            get_logger("items").info(f"[VAT_DEBUG] 📊 Fallback - Using custom VAT rate: {vat_rate}%")
        else:
            get_logger("items").info(f"[VAT_DEBUG] 📊 Fallback - Using default VAT rate: {vat_rate}%")

    # Lấy từ Item Price (thuộc tính theo giá)
    price_filters = {"item_code": item_code}
    if price_list:
        price_filters["price_list"] = price_list

    item_price_data = frappe.get_all(
        "Item Price",
        filters=price_filters,
        fields=["custom_service_fee_rate", "custom_discount_rate"],
        limit=1
    )

    # Tính VAT rate cuối cùng
    # Logic: Nếu custom_vat_applicable = False thì VAT = -1 (không áp dụng)
    # Nếu custom_vat_applicable = True hoặc undefined thì VAT = vat_rate đã tính
    vat_applicable = item_doc.custom_vat_applicable if item_doc.custom_vat_applicable is not None else True
    final_vat_rate = vat_rate if vat_applicable else "-1"

    # === LOG DEBUG CHI TIẾT VAT ===
    get_logger("items").info(f"[VAT_DEBUG] 🎯 GET_ITEM_TAX_INFO - Item: {item_code}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Item Master - custom_vat_applicable: {item_doc.custom_vat_applicable} (type: {type(item_doc.custom_vat_applicable)}), custom_vat_rate: {item_doc.custom_vat_rate}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Item Tax Template: {item_tax_template}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 POS Profile Tax Template: {pos_profile_doc.sales_taxes_and_charges_template if pos_profile_doc else 'N/A'}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Company Tax Template: {frappe.get_value('Company', pos_profile_doc.company if pos_profile_doc else None, 'default_sales_taxes_and_charges_template') if pos_profile_doc else 'N/A'}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Logic Check - vat_applicable is None: {item_doc.custom_vat_applicable is None}, so vat_applicable = {vat_applicable}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Calculated - vat_applicable: {vat_applicable}, vat_rate: {vat_rate}, final_vat_rate: {final_vat_rate}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Item Price - service_fee_rate: {item_price_data[0].custom_service_fee_rate if item_price_data else 'N/A'}, discount_rate: {item_price_data[0].custom_discount_rate if item_price_data else 'N/A'}")

    return {
        "custom_inventory_type": item_doc.custom_inventory_type or "0",
        "custom_vat_applicable": vat_applicable,
        "custom_vat_rate": vat_rate,
        "custom_excise_rate": item_doc.custom_excise_rate or "0",
        "custom_service_fee_rate": item_price_data[0].custom_service_fee_rate if item_price_data else "0",
        "custom_discount_rate": item_price_data[0].custom_discount_rate if item_price_data else "0",
        "item_group": item_doc.item_group or "",
        "vat_rate": final_vat_rate,
        "final_vat_rate": final_vat_rate  # Thêm field này để client dễ sử dụng
    }


@frappe.whitelist()
def get_item_detail(item, doc=None, warehouse=None, price_list=None, company=None):
    item = json.loads(item)
    today = nowdate()
    item_code = item.get("item_code")
    batch_no_data = []
    serial_no_data = []
    if warehouse and item.get("has_batch_no"):
        batch_list = get_batch_qty(warehouse=warehouse, item_code=item_code)
        if batch_list:
            for batch in batch_list:
                if batch.qty > 0 and batch.batch_no:
                    batch_doc = frappe.get_cached_doc("Batch", batch.batch_no)
                    if (
                        str(batch_doc.expiry_date) > str(today)
                        or batch_doc.expiry_date in ["", None]
                    ) and batch_doc.disabled == 0:
                        batch_no_data.append(
                            {
                                "batch_no": batch.batch_no,
                                "batch_qty": batch.qty,
                                "expiry_date": batch_doc.expiry_date,
                                "batch_price": batch_doc.posa_batch_price,
                                "manufacturing_date": batch_doc.manufacturing_date,
                            }
                        )
    if warehouse and item.get("has_serial_no"):
        serial_no_data = frappe.get_all(
            "Serial No",
            filters={
                "item_code": item_code,
                "status": "Active",
                "warehouse": warehouse,
            },
            fields=["name as serial_no"],
        )

    item["selling_price_list"] = price_list

    # Determine if multi-currency is enabled on the POS Profile
    allow_multi_currency = False
    if item.get("pos_profile"):
        allow_multi_currency = (
            frappe.db.get_value("POS Profile", item.get("pos_profile"), "posa_allow_multi_currency")
            or 0
        )

    # Ensure conversion rate exists when price list currency differs from
    # company currency to avoid ValidationError from ERPNext. Also provide
    # sensible defaults when price list or currency is missing.
    if company and price_list:
        company_currency = frappe.db.get_value("Company", company, "default_currency")
        price_list_currency = (
            frappe.db.get_value("Price List", price_list, "currency") or company_currency
        )

        exchange_rate = 1
        if price_list_currency != company_currency and allow_multi_currency:
            from erpnext.setup.utils import get_exchange_rate

            try:
                exchange_rate = get_exchange_rate(price_list_currency, company_currency, today)
            except Exception:
                frappe.log_error(
                    f"Missing exchange rate from {price_list_currency} to {company_currency}",
                    "POS",
                )

        item["price_list_currency"] = price_list_currency
        item["plc_conversion_rate"] = exchange_rate
        item["conversion_rate"] = exchange_rate

        if doc:
            doc.price_list_currency = price_list_currency
            doc.plc_conversion_rate = exchange_rate
            doc.conversion_rate = exchange_rate

    # Add company and doctype to the item args for ERPNext validation
    if company:
        item["company"] = company

    # Set doctype for ERPNext validation
    item["doctype"] = "Sales Invoice"

    # Create a proper doc structure with company for ERPNext validation
    if not doc and company:
        doc = frappe._dict({
            "doctype": "Sales Invoice",
            "company": company
        })

    max_discount = frappe.get_value("Item", item_code, "max_discount")
    res = get_item_details(
        item,
        doc,
        overwrite_warehouse=False,
    )
    if item.get("is_stock_item") and warehouse:
        # Sử dụng Bin cho performance tối ưu
        res["actual_qty"] = get_stock_from_bin(item_code, warehouse)
    res["max_discount"] = max_discount
    res["batch_no_data"] = batch_no_data
    res["serial_no_data"] = serial_no_data

    # Add UOMs data directly from item document
    uoms = frappe.get_all(
        "UOM Conversion Detail",
        filters={"parent": item_code},
        fields=["uom", "conversion_factor"],
    )

    # Add stock UOM if not already in uoms list
    stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
    if stock_uom:
        stock_uom_exists = False
        for uom_data in uoms:
            if uom_data.get("uom") == stock_uom:
                stock_uom_exists = True
                break

        if not stock_uom_exists:
            uoms.append({"uom": stock_uom, "conversion_factor": 1.0})

    res["item_uoms"] = uoms

    # === THÊM THÔNG TIN THUẾ CHO MISA ===
    tax_info = get_item_tax_info(item_code, price_list)
    res.update(tax_info)

    # === LOG DEBUG CHI TIẾT VAT KHI LOAD ITEM ===
    get_logger("items").info(f"[VAT_DEBUG] 🎯 GET_ITEM_DETAIL - Item: {item_code}, Price List: {price_list}")
    get_logger("items").info(f"[VAT_DEBUG] 📊 Item Detail Response - custom_vat_applicable: {res.get('custom_vat_applicable')} (type: {type(res.get('custom_vat_applicable'))}), custom_vat_rate: {res.get('custom_vat_rate')}, final_vat_rate: {res.get('final_vat_rate')}")
    get_logger("items").info(f"[VAT_DEBUG] 💰 Price Info - rate: {res.get('rate')}, base_rate: {res.get('base_rate')}, base_amount: {res.get('base_amount')}, base_net_amount: {res.get('base_net_amount')}")

    return res


@frappe.whitelist()
def mark_invoice_as_submitted_vntax(invoice_name, meinvoice_ref_id=None):
    """Đánh dấu hóa đơn đã gửi MISA thành công"""
    update_data = {"custom_misa_status": "Submitted"}

    if meinvoice_ref_id:
        update_data["custom_misa_ref_id"] = meinvoice_ref_id

    frappe.db.set_value("Sales Invoice", invoice_name, update_data)
    frappe.db.commit()

    return {"success": True, "ref_id": meinvoice_ref_id}


@frappe.whitelist()
def get_items_from_barcode(selling_price_list, currency, barcode):
    search_item = frappe.db.get_value(
        "Item Barcode", {"barcode": barcode}, ["parent as item_code", "posa_uom"], as_dict=1
    )
    if search_item:
        item_doc = frappe.get_cached_doc("Item", search_item.item_code)
        item_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": search_item.item_code,
                "price_list": selling_price_list,
                "currency": currency,
            },
            "price_list_rate",
        )
        
        return {
            "item_code": item_doc.name,
            "item_name": item_doc.item_name,
            "barcode": barcode,
            "rate": item_price or 0,
            "uom": search_item.posa_uom or item_doc.stock_uom,
            "currency": currency
        }
    return None


def build_item_cache(item_code):
    """Build item cache for faster access."""
    # Implementation for building item cache
    pass


def get_item_optional_attributes(item_code):
    """Get optional attributes for an item."""
    return frappe.get_all(
        "Item Variant Attribute",
        fields=["attribute", "attribute_value"],
        filters={"parent": item_code, "parentfield": "attributes"},
    )


@frappe.whitelist()
def get_item_attributes(item_code):
    """Get item attributes."""
    return frappe.get_all(
        "Item Attribute",
        fields=["name", "attribute_name"],
        filters={"name": ["in", [
            attr.attribute for attr in frappe.get_all(
                "Item Variant Attribute",
                fields=["attribute"],
                filters={"parent": item_code}
            )
        ]]}
    )


@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value, search_serial_no):
    """Search for items by serial number, batch number, or barcode."""
    # Search by barcode
    barcode_data = frappe.db.get_value(
        "Item Barcode", {"barcode": search_value}, ["parent as item_code", "barcode"], as_dict=True
    )
    if barcode_data:
        return {"item_code": barcode_data.item_code, "barcode": barcode_data.barcode}
    
    # Search by batch number
    batch_data = frappe.db.get_value(
        "Batch", {"name": search_value}, ["item as item_code", "name as batch_no"], as_dict=True
    )
    if batch_data:
        return {"item_code": batch_data.item_code, "batch_no": batch_data.batch_no}
    
    # Search by serial number if enabled
    if search_serial_no:
        serial_data = frappe.db.get_value(
            "Serial No", {"name": search_value}, ["item_code", "name as serial_no"], as_dict=True
        )
        if serial_data:
            return {"item_code": serial_data.item_code, "serial_no": serial_data.serial_no}
    
    return {}


@frappe.whitelist()
def update_price_list_rate(item_code, price_list, rate, uom=None):
    """Create or update Item Price for the given item and price list."""
    # log = get_logger("items")
    # log.info(f"[UPDATE_PRICE_LIST_RATE] 🎯 START - Item: {item_code}, Price List: {price_list}, Rate: {rate}, UOM: {uom}")

    # if not item_code or not price_list:
    #     log.error(f"[UPDATE_PRICE_LIST_RATE] ❌ Missing required fields - Item: {item_code}, Price List: {price_list}")
    #     frappe.throw(_("Item Code and Price List are required"))

    # rate = flt(rate)
    # filters = {"item_code": item_code, "price_list": price_list}
    # if uom:
    #     filters["uom"] = uom
    # else:
    #     filters["uom"] = ["", None]

    # log.info(f"[UPDATE_PRICE_LIST_RATE] 🔍 Checking existing Item Price with filters: {filters}")
    # name = frappe.db.exists("Item Price", filters)
    # if name:
    #     log.info(f"[UPDATE_PRICE_LIST_RATE] 📝 Updating existing Item Price: {name}")
    #     doc = frappe.get_doc("Item Price", name)
    #     doc.price_list_rate = rate
    #     doc.save(ignore_permissions=True)
    #     log.info(f"[UPDATE_PRICE_LIST_RATE] ✅ Updated Item Price: {name} with rate: {rate}")
    # else:
    #     log.info(f"[UPDATE_PRICE_LIST_RATE] 🆕 Creating new Item Price")
    #     doc = frappe.get_doc({
    #         "doctype": "Item Price",
    #         "item_code": item_code,
    #         "price_list": price_list,
    #         "uom": uom,
    #         "price_list_rate": rate,
    #         "selling": 1,
    #     })
    #     doc.insert(ignore_permissions=True)
    #     log.info(f"[UPDATE_PRICE_LIST_RATE] ✅ Created new Item Price: {doc.name} with rate: {rate}")

    # frappe.db.commit()
    log.info(f"[UPDATE_PRICE_LIST_RATE] 🎉 COMPLETED - Item Price called for {item_code}")
    return _("Item Price has been called or updated")


# @frappe.whitelist()
# def update_price_list_rate(item_code, price_list, rate, uom=None):
#     """Create or update Item Price for the given item and price list."""
#     log = get_logger("items")
#     log.info(f"[UPDATE_PRICE_LIST_RATE] 🎯 START - Item: {item_code}, Price List: {price_list}, Rate: {rate}, UOM: {uom}")

#     if not item_code or not price_list:
#         log.error(f"[UPDATE_PRICE_LIST_RATE] ❌ Missing required fields - Item: {item_code}, Price List: {price_list}")
#         frappe.throw(_("Item Code and Price List are required"))

#     rate = flt(rate)
#     filters = {"item_code": item_code, "price_list": price_list}
#     if uom:
#         filters["uom"] = uom
#     else:
#         filters["uom"] = ["", None]

#     log.info(f"[UPDATE_PRICE_LIST_RATE] 🔍 Checking existing Item Price with filters: {filters}")
#     name = frappe.db.exists("Item Price", filters)
#     if name:
#         log.info(f"[UPDATE_PRICE_LIST_RATE] 📝 Updating existing Item Price: {name}")
#         doc = frappe.get_doc("Item Price", name)
#         doc.price_list_rate = rate
#         doc.save(ignore_permissions=True)
#         log.info(f"[UPDATE_PRICE_LIST_RATE] ✅ Updated Item Price: {name} with rate: {rate}")
#     else:
#         log.info(f"[UPDATE_PRICE_LIST_RATE] 🆕 Creating new Item Price")
#         doc = frappe.get_doc({
#             "doctype": "Item Price",
#             "item_code": item_code,
#             "price_list": price_list,
#             "uom": uom,
#             "price_list_rate": rate,
#             "selling": 1,
#         })
#         doc.insert(ignore_permissions=True)
#         log.info(f"[UPDATE_PRICE_LIST_RATE] ✅ Created new Item Price: {doc.name} with rate: {rate}")

#     frappe.db.commit()
#     log.info(f"[UPDATE_PRICE_LIST_RATE] 🎉 COMPLETED - Item Price updated for {item_code}")
#     return _("Item Price has been added or updated")


@frappe.whitelist()
def get_price_for_uom(item_code, price_list, uom):
    """Return Item Price for the given item, price list and UOM if it exists."""
    if not (item_code and price_list and uom):
        return None

    price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": price_list,
            "uom": uom,
            "selling": 1,
        },
        "price_list_rate",
    )
    return price


@frappe.whitelist()
def get_item_by_barcode_exact(barcode, pos_profile=None, price_list=None, customer=None):
    """
    API exact barcode match - trả về đúng 1 item nếu tìm thấy barcode chính xác.
    Ưu tiên tuyệt đối cho exact match trước khi fallback fuzzy.
    ĐẢM BẢO: UOM và Price phải đi cùng nhau, không có fallback không kiểm soát.
    """
    if not barcode:
        return None

    # Tìm exact barcode match
    barcode_data = frappe.db.get_value(
        "Item Barcode",
        {"barcode": barcode},  # Exact match với barcode
        ["parent as item_code", "barcode", "posa_uom"],
        as_dict=True
    )

    if not barcode_data:
        return None

    item_code = barcode_data.item_code

    # Validate user context (POS Profile, company, warehouse)
    pos_profile_data = None
    if pos_profile:
        try:
            pos_profile_data = json.loads(pos_profile)
        except:
            pos_profile_data = frappe.get_cached_doc("POS Profile", pos_profile)

    warehouse = pos_profile_data.get("warehouse") if pos_profile_data else None
    company = pos_profile_data.get("company") if pos_profile_data else None

    # Lấy item data cơ bản
    item_doc = frappe.get_cached_doc("Item", item_code)
    if item_doc.disabled or not item_doc.is_sales_item or item_doc.is_fixed_asset:
        return None

    # Validate item group từ POS Profile
    if pos_profile_data:
        item_groups = get_item_groups(pos_profile_data.get("name"))
        if item_groups and item_doc.item_group not in item_groups:
            return None

    # Validate stock (nếu POS Profile yêu cầu chỉ hiển thị item có stock)
    if pos_profile_data and pos_profile_data.get("posa_display_items_in_stock"):
        actual_qty = get_stock_from_bin(item_code, warehouse)
        if actual_qty <= 0:
            return None

    # ✅ ĐẢM BẢO UOM CHÍNH XÁC: Set UOM từ barcode, fallback to stock_uom
    barcode_uom = barcode_data.posa_uom or item_doc.stock_uom

    # ✅ VALIDATE UOM: Đảm bảo UOM tồn tại trong item_uoms
    item_uoms = frappe.get_all(
        "UOM Conversion Detail",
        filters={"parent": item_code},
        fields=["uom", "conversion_factor"]
    )

    # Thêm stock UOM nếu chưa có
    stock_uom = item_doc.stock_uom
    if stock_uom and not any(u.get("uom") == stock_uom for u in item_uoms):
        item_uoms.append({"uom": stock_uom, "conversion_factor": 1.0})

    # Validate barcode UOM exists, fallback to stock_uom if not
    if barcode_uom not in [u['uom'] for u in item_uoms]:
        frappe.log_error(
            f"Barcode UOM '{barcode_uom}' not found in item '{item_code}' UOMs. Using stock UOM.",
            "POS Barcode UOM Validation"
        )
        barcode_uom = item_doc.stock_uom

    # ✅ ĐẢM BẢO PRICE ĐÚNG CHO UOM: Lấy giá cho UOM cụ thể
    selling_price_list = price_list or (pos_profile_data.get("selling_price_list") if pos_profile_data else None)
    today = nowdate()

    # Ưu tiên: Tìm giá cho UOM cụ thể từ barcode
    item_price_data = frappe.get_all(
        "Item Price",
        fields=["price_list_rate", "currency", "uom"],
        filters={
            "item_code": item_code,
            "price_list": selling_price_list,
            "selling": 1,
            "valid_from": ["<=", today],
            "customer": ["in", ["", None, customer]],
            "uom": barcode_uom  # ← ĐẢM BẢO GIÁ CHO UOM CỤ THỂ
        },
        or_filters=[["valid_upto", ">=", today], ["valid_upto", "is", "not set"]],
        order_by="valid_from DESC",
        limit=1
    )

    # Nếu không có giá cho UOM cụ thể, fallback nhưng log warning
    if not item_price_data:
        frappe.log_error(
            f"No price found for item '{item_code}' with UOM '{barcode_uom}' in price list '{selling_price_list}'. Using general price.",
            "POS Barcode Price Validation"
        )
        # Fallback to any available price for this item
        item_price_data = frappe.get_all(
            "Item Price",
            fields=["price_list_rate", "currency", "uom"],
            filters={
                "item_code": item_code,
                "price_list": selling_price_list,
                "selling": 1,
                "valid_from": ["<=", today],
                "customer": ["in", ["", None, customer]]
            },
            or_filters=[["valid_upto", ">=", today], ["valid_upto", "is", "not set"]],
            order_by="valid_from DESC",
            limit=1
        )

    item_price = item_price_data[0] if item_price_data else {}

    # Lấy tất cả barcodes của item (bao gồm cái đang tìm)
    item_barcodes = frappe.get_all(
        "Item Barcode",
        filters={"parent": item_code},
        fields=["barcode", "posa_uom"]
    )

    # Lấy stock quantity
    actual_qty = get_stock_from_bin(item_code, warehouse) if warehouse else 0

    # ✅ ĐẢM BẢO RESULT CÓ UOM CHÍNH XÁC
    result = {
        "item_code": item_doc.name,
        "item_name": item_doc.item_name,
        "description": item_doc.description,
        "stock_uom": item_doc.stock_uom,
        "uom": barcode_uom,  # ← UOM CHÍNH XÁC từ barcode
        "image": item_doc.image,
        "is_stock_item": item_doc.is_stock_item,
        "has_variants": item_doc.has_variants,
        "variant_of": item_doc.variant_of,
        "item_group": item_doc.item_group,
        "has_batch_no": item_doc.has_batch_no,
        "has_serial_no": item_doc.has_serial_no,
        "max_discount": item_doc.max_discount,
        "brand": item_doc.brand,
        "rate": item_price.get("price_list_rate", 0),  # ← Giá tương ứng với UOM
        "currency": item_price.get("currency") or (pos_profile_data.get("currency") if pos_profile_data else "VND"),
        "item_barcode": item_barcodes,
        "actual_qty": actual_qty,
        "item_uoms": item_uoms,
        "serial_no_data": [],  # Để tương thích, sẽ load khi cần
        "batch_no_data": [],   # Để tương thích, sẽ load khi cần
        "attributes": "",
        "item_attributes": "",
    }

    return result
