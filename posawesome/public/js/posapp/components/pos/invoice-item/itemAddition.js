export default {
	remove_item(item) {
		const index = this.items.findIndex((el) => el.posa_row_id == item.posa_row_id);
		if (index >= 0) {
			this.items.splice(index, 1);
		}
		// Remove from expanded if present
		this.expanded = this.expanded.filter((id) => id !== item.posa_row_id);
	},

	add_item(item, scanMode = null) {
		// Get scan mode from ItemsSelector via eventBus if not provided
		if (scanMode === null) {
			// Listen for scan mode from ItemsSelector
			this.eventBus.emit("get_scan_mode");
			// For now, default to add mode if not specified
			scanMode = true;
		}

		console.log(`[Invoice.add_item] Processing item ${item.item_code} in ${scanMode ? 'Add' : 'Remove'} mode`);

		if (!item.uom) {
			item.uom = item.stock_uom;
		}
		let index = -1;
		if (!this.new_line) {
			// For auto_set_batch enabled, we should check if the item code and UOM match only
			// For items with batch but auto_set_batch disabled, check if batch numbers match
			// This will allow quantity to increment for batch items with auto_set_batch enabled
			if (this.pos_profile.posa_auto_set_batch && item.has_batch_no) {
				index = this.items.findIndex(
					(el) =>
						el.item_code === item.item_code &&
						el.uom === item.uom &&
						!el.posa_is_offer &&
						!el.posa_is_replace,
				);
			} else {
				index = this.items.findIndex(
					(el) =>
						el.item_code === item.item_code &&
						el.uom === item.uom &&
						!el.posa_is_offer &&
						!el.posa_is_replace &&
						((el.batch_no && item.batch_no && el.batch_no === item.batch_no) ||
							(!el.batch_no && !item.batch_no)),
				);
			}
		}

		let new_item;
		let target_item;
		let is_new_item = false;

		if (index === -1 || this.new_line) {
			// Create new item
			new_item = this.get_new_item(item);
			target_item = new_item;
			is_new_item = true;

			// Handle serial number logic
			if (item.has_serial_no && item.to_set_serial_no) {
				new_item.serial_no_selected = [];
				new_item.serial_no_selected.push(item.to_set_serial_no);
				item.to_set_serial_no = null;
			}
			// Handle batch number logic
			if (item.has_batch_no && item.to_set_batch_no) {
				new_item.batch_no = item.to_set_batch_no;
				item.to_set_batch_no = null;
				item.batch_no = null;
				this.set_batch_qty(new_item, new_item.batch_no, false);
			}

			// Apply scan mode logic for new items
			if (!scanMode) {
				// Remove mode: set negative quantity for new items
				new_item.qty = -Math.abs(new_item.qty || 1);
			} else {
				// Add mode: keep positive quantity (default behavior)
				if (this.isReturnInvoice) {
					new_item.qty = -Math.abs(new_item.qty || 1);
				}
			}

			this.items.unshift(new_item);
			// Force update of item rates when item is first added
			this.update_item_detail(new_item, true);

			// Expand new item if it has batch or serial number
			if ((!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) || new_item.has_serial_no) {
				this.$nextTick(() => {
					this.expanded = [new_item.posa_row_id];
				});
			}
		} else {
			// Update existing item
			const cur_item = this.items[index];
			target_item = cur_item;
			is_new_item = false;

			this.update_items_details([cur_item]);
			// Serial number logic for existing item
			if (item.has_serial_no && item.to_set_serial_no) {
				if (cur_item.serial_no_selected.includes(item.to_set_serial_no)) {
					this.eventBus.emit("show_message", {
						title: __(`This Serial Number {0} has already been added!`, [item.to_set_serial_no]),
						color: "warning",
					});
					item.to_set_serial_no = null;
					return;
				}
				cur_item.serial_no_selected.push(item.to_set_serial_no);
				item.to_set_serial_no = null;
			}

			// Apply scan mode logic for existing items
			const qty_change = item.qty || 1;
			if (!scanMode) {
				// Remove mode: decrease quantity
				if (this.isReturnInvoice) {
					cur_item.qty -= qty_change; // Make more negative for returns
				} else {
					cur_item.qty -= qty_change; // Decrease for normal invoices
				}
			} else {
				// Add mode: increase quantity (original behavior)
				if (this.isReturnInvoice) {
					cur_item.qty -= qty_change; // Make more negative for returns
				} else {
					cur_item.qty += qty_change; // Increase for normal invoices
				}
			}

			this.calc_stock_qty(cur_item, cur_item.qty);

			// Update batch quantity if needed
			if (cur_item.has_batch_no && cur_item.batch_no) {
				this.set_batch_qty(cur_item, cur_item.batch_no, false);
			}

			this.set_serial_no(cur_item);
		}

		this.$forceUpdate();

		// Only try to expand if new_item exists and should be expanded
		if (
			new_item &&
			((!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) || new_item.has_serial_no)
		) {
			this.expanded = [new_item.posa_row_id];
		}

		// Apply highlight effect for the affected item
		if (target_item) {
			this.applyItemHighlight(target_item.posa_row_id, scanMode);
		}

		// Sync to dual screen if enabled
		if (this.dualScreenEnabled) {
			this.syncInvoiceToDualScreen();
		}
	},

	// Apply highlight effect with green background and enlarged font for quantity and amount
	applyItemHighlight(itemRowId, scanMode) {
		console.log(`[Invoice.applyItemHighlight] Highlighting item ${itemRowId} in ${scanMode ? 'Add' : 'Remove'} mode`);

		// Emit event to ItemsTable to apply highlight with enlarged font
		this.eventBus.emit("highlight_invoice_item", {
			itemRowId: itemRowId,
			scanMode: scanMode,
			duration: 2000, // 2 seconds highlight duration
			enlargeFont: true // Enable font enlargement for quantity and amount
		});

		// Also emit to show visual feedback
		this.eventBus.emit("show_message", {
			title: scanMode ? __("Item Added") : __("Item Removed"),
			color: scanMode ? "success" : "warning",
		});
	},

	// Create a new item object with default and calculated fields
	get_new_item(item) {
		const new_item = { ...item };
		if (!item.qty) {
			item.qty = 1;
		}
		if (!item.posa_is_offer) {
			item.posa_is_offer = 0;
		}
		if (!item.posa_is_replace) {
			item.posa_is_replace = "";
		}

		// Initialize flag for tracking manual rate changes
		new_item._manual_rate_set = false;

		// Set negative quantity for return invoices
		if (this.isReturnInvoice && item.qty > 0) {
			item.qty = -Math.abs(item.qty);
		}

		new_item.stock_qty = item.qty;
		new_item.discount_amount = 0;
		new_item.discount_percentage = 0;
		new_item.discount_amount_per_item = 0;
		new_item.price_list_rate = item.rate;

		// Setup base rates properly for multi-currency
		const baseCurrency = this.price_list_currency || this.pos_profile.currency;
		if (this.selected_currency !== baseCurrency) {
			// Store original base currency values
			new_item.base_price_list_rate = item.rate / this.exchange_rate;
			new_item.base_rate = item.rate / this.exchange_rate;
			new_item.base_discount_amount = 0;
		} else {
			// In base currency, base rates = displayed rates
			new_item.base_price_list_rate = item.rate;
			new_item.base_rate = item.rate;
			new_item.base_discount_amount = 0;
		}

		new_item.qty = item.qty;
		new_item.uom = item.uom ? item.uom : item.stock_uom;
		// Ensure item_uoms is initialized
		new_item.item_uoms = item.item_uoms || [];
		if (new_item.item_uoms.length === 0 && new_item.stock_uom) {
			new_item.item_uoms.push({ uom: new_item.stock_uom, conversion_factor: 1 });
		}
		new_item.actual_batch_qty = "";
		new_item.batch_no_expiry_date = item.batch_no_expiry_date || null;
		new_item.conversion_factor = 1;
		new_item.posa_offers = JSON.stringify([]);
		new_item.posa_offer_applied = 0;
		new_item.posa_is_offer = item.posa_is_offer;
		new_item.posa_is_replace = item.posa_is_replace || null;
		new_item.is_free_item = 0;
		new_item.posa_notes = "";
		new_item.posa_delivery_date = "";
		new_item.posa_row_id = this.makeid(20);
		if (new_item.has_serial_no && !new_item.serial_no_selected) {
			new_item.serial_no_selected = [];
			new_item.serial_no_selected_count = 0;
		}
		// Expand row if batch/serial required
		if ((!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) || new_item.has_serial_no) {
			this.expanded.push(new_item);
		}
		return new_item;
	},

	// Reset all invoice fields to default/empty values
	clear_invoice() {
		this.items = [];
		this.posa_offers = [];
		this.expanded = [];
		this.eventBus.emit("set_pos_coupons", []);
		this.posa_coupons = [];
		this.invoice_doc = "";
		this.return_doc = "";
		this.discount_amount = 0;
		this.additional_discount = 0; // Added for additional discount
		this.additional_discount_percentage = 0;
		this.delivery_charges_rate = 0;
		this.selected_delivery_charge = "";
		// Reset posting date to today
		this.posting_date = frappe.datetime.nowdate();

		// Reset price list to default
		this.update_price_list();

		// Always reset to default customer after invoice
		this.customer = this.pos_profile.customer;

		this.eventBus.emit("set_customer_readonly", false);
		this.invoiceType = this.pos_profile.posa_default_sales_order ? "Order" : "Invoice";
		this.invoiceTypes = ["Invoice", "Order"];
	},
};
