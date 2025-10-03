import {
	isOffline,
	saveCustomerBalance,
	getCachedCustomerBalance,
	getCachedPriceListItems,
	getItemUOMs,
	getCustomerStorage,
	getOfflineCustomers,
	getTaxTemplate,
	getTaxInclusiveSetting,
} from "../../../offline/index.js";

// Import format utilities
import { formatCurrency } from "../../format.js";

export default {
	remove_item(item) {
		const index = this.items.findIndex((el) => el.posa_row_id == item.posa_row_id);
		if (index >= 0) {
			this.items.splice(index, 1);
		}
		// Remove from expanded if present
		this.expanded = this.expanded.filter((id) => id !== item.posa_row_id);

		// Trigger discount calculation after item removal (if not already applying)
		if (!this.isApplyingDiscount) {
			this.$nextTick(() => {
				setTimeout(() => {
					this.calculateDiscountsDebounced();
				}, 10);
			});
		}
	},

       add_item(item) {
               console.log("Invoice.add_item received", {
                       code: item.item_code,
                       rate: item.rate,
               });
               if (!item.uom) {
                       item.uom = item.stock_uom;
               }

               // Check if pack optimization should be applied
               if (this.shouldOptimizePacks(item)) {
                       console.log('[PACK_OPTIMIZER] Applying pack optimization for:', item.item_code);
                       return this.add_item_with_pack_optimization(item);
               }
		let index = -1;
		if (!this.new_line) {
			// Simplified logic: just check item_code, uom, and basic flags
			// Ignore complex batch logic that can cause mismatches
			index = this.items.findIndex(
				(el) =>
					el.item_code === item.item_code &&
					el.uom === item.uom &&
					!el.posa_is_offer &&
					!el.posa_is_replace,
			);

			// Debug: Log item matching logic
			console.log("add_item: checking for existing item", {
				new_item: {
					item_code: item.item_code,
					uom: item.uom,
					has_batch_no: item.has_batch_no,
					batch_no: item.batch_no,
					posa_is_offer: item.posa_is_offer,
					posa_is_replace: item.posa_is_replace
				},
				posa_auto_set_batch: this.pos_profile.posa_auto_set_batch,
				items_count: this.items.length,
				found_index: index
			});

			// Log existing items for comparison
			if (this.items.length > 0) {
				console.log("add_item: existing items in cart:");
				this.items.forEach((existing, idx) => {
					console.log(`  [${idx}]:`, {
						item_code: existing.item_code,
						uom: existing.uom,
						has_batch_no: existing.has_batch_no,
						batch_no: existing.batch_no,
						posa_is_offer: existing.posa_is_offer,
						posa_is_replace: existing.posa_is_replace,
						posa_row_id: existing.posa_row_id
					});
				});
			}
		}

		let new_item;
		if (index === -1 || this.new_line) {
			new_item = this.get_new_item(item);
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
			// Make quantity negative for returns
			if (this.isReturnInvoice) {
				new_item.qty = -Math.abs(new_item.qty || 1);
			}

                       this.items.unshift(new_item);
                       // Replace the newly inserted item at index 0 to ensure
                       // Vue reactivity and avoid overwriting existing rows
                       this.items[0] = { ...new_item };
                       console.log("Item inserted at", 0, {
                               code: new_item.item_code,
                               rate: new_item.rate,
                       });
                       // Force update of item rates when item is first added
                       console.log("Before update_item_detail - Initial item state", {
                               Item_code: new_item.item_code,
                               Price: new_item.rate,
                               Uom: new_item.uom,
                               base_rate: new_item.base_rate,
                               stock_uom: new_item.stock_uom,
                               conversion_factor: new_item.conversion_factor
                       });
                       this.update_item_detail(new_item, true);
                       console.log("After update_item_detail - Item state after server call", {
                               Item_code: new_item.item_code,
                               Price: new_item.rate,
                               Uom: new_item.uom,
                               base_rate: new_item.base_rate,
                               base_price_list_rate: new_item.base_price_list_rate,
                               stock_uom: new_item.stock_uom,
                               conversion_factor: new_item.conversion_factor
                       });
                       // Apply UOM conversion immediately
                       if (new_item.uom && new_item.uom !== new_item.stock_uom) {
                        console.log("Calling calc_uom for barcode scan", {
                         Item_code: new_item.item_code,
                         current_uom: new_item.uom,
                         stock_uom: new_item.stock_uom,
                         base_rate_before: new_item.base_rate,
                         rate_before: new_item.rate
                        });
                   
                        // CRITICAL: Apply immediate UOM conversion to ensure rate is correct before ItemsTable renders
                        // First, ensure we have the correct conversion_factor by finding the UOM
                        const uomData = this.find_uom(new_item, new_item.uom);
                        if (uomData) {
                        	// Direct assignment since this is not a Vue component context
                        	new_item.conversion_factor = uomData.conversion_factor;
                        	console.log("UOM data found for immediate conversion", {
                        		Item_code: new_item.item_code,
                        		uom: new_item.uom,
                        		conversion_factor: new_item.conversion_factor
                        	});
                   
                        	// Ensure base_rate is set before conversion
                        	if (!new_item.base_rate || new_item.base_rate === 0) {
                        		new_item.base_rate = new_item.rate || 0;
                        		console.log("Setting base_rate for immediate conversion", {
                        			Item_code: new_item.item_code,
                        			base_rate: new_item.base_rate,
                        			original_rate: new_item.rate
                        		});
                        	}
                   
                        	// Apply immediate conversion if needed
                        	if (new_item.base_rate && new_item.conversion_factor !== 1) {
                        		const convertedRate = new_item.base_rate * new_item.conversion_factor;
                        		new_item.rate = convertedRate;
                        		new_item.price_list_rate = (new_item.base_price_list_rate || new_item.base_rate) * new_item.conversion_factor;
                        		console.log("Immediate UOM conversion applied in add_item", {
                        			Item_code: new_item.item_code,
                        			base_rate: new_item.base_rate,
                        			conversion_factor: new_item.conversion_factor,
                        			converted_rate: convertedRate
                        		});
                        	}
                        } else {
                        	console.log("No UOM data found for immediate conversion", {
                        		Item_code: new_item.item_code,
                        		uom: new_item.uom,
                        		stock_uom: new_item.stock_uom
                        	});
                        }
                   
                        this.calc_uom(new_item, new_item.uom);
                        console.log("After calc_uom for barcode scan", {
                         Item_code: new_item.item_code,
                         final_uom: new_item.uom,
                         base_rate_after: new_item.base_rate,
                         rate_after: new_item.rate,
                         conversion_factor: new_item.conversion_factor
                        });

                        // CRITICAL: Force update ItemsTable after calc_uom completes
                        setTimeout(() => {
                         	this.$forceUpdate();
                         	console.log("Force update after calc_uom completion", {
                         		Item_code: new_item.item_code,
                         		rate_after_force_update: new_item.rate,
                         		conversion_factor: new_item.conversion_factor
                         	});
                         }, 50);

                         // CRITICAL: Force update after calc_uom to ensure ItemsTable gets the updated rate
                         setTimeout(() => {
                         	this.$forceUpdate();
                         	// Emit event to force ItemsTable update
                         	this.eventBus.emit("force_items_table_update");
                         	console.log("Force update after calc_uom completion", {
                         		Item_code: new_item.item_code,
                         		rate_after_force_update: new_item.rate,
                         		conversion_factor: new_item.conversion_factor
                         	});
                         }, 100);
                       } else {
                        console.log("No UOM conversion needed for barcode scan", {
                         Item_code: new_item.item_code,
                         uom: new_item.uom,
                         stock_uom: new_item.stock_uom,
                         rate: new_item.rate
                        });
                       }

   // Ensure stock_qty is calculated correctly after UOM conversion
   this.calc_stock_qty(new_item, new_item.qty);

   // Force Vue reactivity update for ItemsTable - critical for price display
   this.$forceUpdate();

   // Additional force update after a short delay to ensure all async operations complete
   setTimeout(() => {
   	this.$forceUpdate();
   	console.log("Additional force update after barcode scan", {
   		Item_code: new_item.item_code,
   		final_rate: new_item.rate,
   		final_uom: new_item.uom
   	});
   }, 200);

   console.log("Barcode scan - Final quantities after UOM conversion", {
   	Item_code: new_item.item_code,
   	Price: new_item.rate,
   	Uom: new_item.uom,
   	display_qty: new_item.qty,
   	stock_qty: new_item.stock_qty,
   	conversion_factor: new_item.conversion_factor,
   	stock_uom: new_item.stock_uom,
   	base_rate: new_item.base_rate,
   	expected_display_rate: new_item.base_rate * new_item.conversion_factor
   });

			// Expand new item if it has batch or serial number
			if ((!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) || new_item.has_serial_no) {
				this.$nextTick(() => {
					this.expanded = [new_item.posa_row_id];
				});
			}
		} else {
			const cur_item = this.items[index];
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

			// For returns, subtract from quantity to make it more negative
			if (this.isReturnInvoice) {
				cur_item.qty -= item.qty || 1;
			} else {
				cur_item.qty += item.qty || 1;
			}
			this.calc_stock_qty(cur_item, cur_item.qty);

			// Update batch quantity if needed
			if (cur_item.has_batch_no && cur_item.batch_no) {
				this.set_batch_qty(cur_item, cur_item.batch_no, false);
			}

			this.set_serial_no(cur_item);
			if (cur_item.uom && cur_item.uom !== cur_item.stock_uom) {
				this.calc_uom(cur_item, cur_item.uom);
			}

			// Ensure Vue watcher is triggered after all updates complete (if not already applying)
			if (!this.isApplyingDiscount) {
				this.$nextTick(() => {
					setTimeout(() => {
						this.calculateDiscountsDebounced();
					}, 10);
				});
			}
		}
		this.$forceUpdate();

		// Only try to expand if new_item exists and should be expanded
		if (
			new_item &&
			((!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) || new_item.has_serial_no)
		) {
			this.expanded = [new_item.posa_row_id];
		}
	},

	// Create a new item object with default and calculated fields
	get_new_item(item) {
		const new_item = { ...item };
		if (!new_item.warehouse) {
			new_item.warehouse = this.pos_profile.warehouse;
		}
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
			new_item.base_price_list_rate = item.base_price_list_rate || item.rate / this.exchange_rate;
			new_item.base_rate = item.base_rate || item.rate / this.exchange_rate;
			new_item.base_discount_amount = 0;
		} else {
			// In base currency, base rates = displayed rates
			new_item.base_price_list_rate = item.base_price_list_rate || item.rate;
			new_item.base_rate = item.base_rate || item.rate;
			new_item.base_discount_amount = 0;
		}

		// CRITICAL: Ensure base_rate is set correctly for UOM conversion
		// Base rates MUST always be in stock UOM, not display UOM
		if (!new_item.base_rate || new_item.base_rate === 0) {
			new_item.base_rate = item.rate || 0;
			console.log("Setting base_rate in get_new_item", {
				Item_code: new_item.item_code,
				base_rate: new_item.base_rate,
				original_rate: item.rate
			});
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
		new_item.posa_offers = "[]";
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

		// Call the new method to set the default customer
		this.setDefaultCustomerAfterClear();
	},

	// Method to set the default customer
	setDefaultCustomerAfterClear() {
		console.log("=== setDefaultCustomerAfterClear() called ===");
		console.log("POS Profile:", this.pos_profile);
		
		// Priority 1: Check for default_customer field
		if (this.pos_profile && this.pos_profile.default_customer) {
			console.log("✅ Using default_customer:", this.pos_profile.default_customer);
			this.customer = this.pos_profile.default_customer;
		}
		// Priority 2: Fallback to customer field 
		else if (this.pos_profile && this.pos_profile.customer) {
			console.log("✅ Using fallback customer:", this.pos_profile.customer);
			this.customer = this.pos_profile.customer;
		}
		// Priority 3: Clear customer if no default
		else {
			console.log("❌ No default customer found, clearing");
			this.customer = "";
		}
		
		this.eventBus.emit("set_customer_readonly", false);
		
		// Only fetch details if customer is set
		if (this.customer) {
			this.fetch_customer_details();
			this.fetch_customer_balance();
		}
		
		console.log("=== Final customer set to:", this.customer, "===");
	},

	// Fetch customer balance from backend or cache
	async fetch_customer_balance() {
		try {
			if (!this.customer) {
				this.customer_balance = 0;
				return;
			}

			// Check if offline and use cached balance
			if (isOffline()) {
				const cachedBalance = getCachedCustomerBalance(this.customer);
				if (cachedBalance !== null) {
					this.customer_balance = cachedBalance;
					return;
				} else {
					// No cached balance available in offline mode
					this.customer_balance = 0;
					this.eventBus.emit("show_message", {
						title: __("Customer balance unavailable offline"),
						text: __("Balance will be updated when connection is restored"),
						color: "warning",
					});
					return;
				}
			}

			// Online mode: fetch from server and cache the result
			const r = await frappe.call({
				method: "posawesome.posawesome.api.customer.get_customer_balance",
				args: { customer: this.customer },
			});

			const balance = r?.message?.balance || 0;
			this.customer_balance = balance;

			// Cache the balance for offline use
			saveCustomerBalance(this.customer, balance);
		} catch (error) {
			console.error("Error fetching balance:", error);

			// Try to use cached balance as fallback
			const cachedBalance = getCachedCustomerBalance(this.customer);
			if (cachedBalance !== null) {
				this.customer_balance = cachedBalance;
				this.eventBus.emit("show_message", {
					title: __("Using cached customer balance"),
					text: __("Could not fetch latest balance from server"),
					color: "warning",
				});
			} else {
				this.eventBus.emit("show_message", {
					title: __("Error fetching customer balance"),
					color: "error",
				});
				this.customer_balance = 0;
			}
		}
	},

	// Cancel the current invoice, optionally delete from backend
	async cancel_invoice() {
		const doc = this.get_invoice_doc();
		this.invoiceType = this.pos_profile.posa_default_sales_order ? "Order" : "Invoice";
		this.invoiceTypes = ["Invoice", "Order"];
		this.posting_date = frappe.datetime.nowdate();
		var vm = this;
		if (doc.name && this.pos_profile.posa_allow_delete) {
			await frappe.call({
				method: "posawesome.posawesome.api.invoices.delete_invoice",
				args: { invoice: doc.name },
				async: true,
				callback: function (r) {
					if (r.message) {
						vm.eventBus.emit("show_message", {
							text: r.message,
							color: "warning",
						});
					}
				},
			});
		}
		this.clear_invoice(); // This already calls setDefaultCustomerAfterClear()
		this.cancel_dialog = false;
		
		// Ensure default customer is set after cancel
		this.$nextTick(() => {
			this.setDefaultCustomerAfterClear();
		});
	},

	// Load an invoice (or return invoice) from data, set all fields accordingly
	async load_invoice(data = {}) {
		console.log("load_invoice called with data:", {
			is_return: data.is_return,
			return_against: data.return_against,
			customer: data.customer,
			items_count: data.items ? data.items.length : 0,
		});

		this.clear_invoice();
		if (data.is_return) {
			console.log("Processing return invoice");
			// For return without invoice case, check if there's a return_against
			// Only set customer readonly if this is a return with reference to an invoice
			if (data.return_against) {
				console.log("Return has reference to invoice:", data.return_against);
				this.eventBus.emit("set_customer_readonly", true);
			} else {
				console.log("Return without invoice reference, customer can be selected");
				// Allow customer selection for returns without invoice
				this.eventBus.emit("set_customer_readonly", false);
			}
			this.invoiceType = "Return";
			this.invoiceTypes = ["Return"];
		}

		this.invoice_doc = data;
		this.items = data.items || [];
		console.log("Items set:", this.items.length, "items");

		if (this.items.length > 0) {
			this.update_items_details(this.items);
			this.posa_offers = data.posa_offers || [];
			this.items.forEach((item) => {
				if (!item.posa_row_id) {
					item.posa_row_id = this.makeid(20);
				}
				if (item.batch_no) {
					this.set_batch_qty(item, item.batch_no);
				}
			});
		} else {
			console.log("Warning: No items in return invoice");
		}

		this.customer = data.customer;
		this.posting_date = this.formatDateForBackend(data.posting_date || frappe.datetime.nowdate());
		this.discount_amount = data.discount_amount;
		this.additional_discount_percentage = data.additional_discount_percentage;

		if (this.items.length > 0) {
			this.items.forEach((item) => {
				if (item.serial_no) {
					item.serial_no_selected = [];
					const serial_list = item.serial_no.split("\n");
					serial_list.forEach((element) => {
						if (element.length) {
							item.serial_no_selected.push(element);
						}
					});
					item.serial_no_selected_count = item.serial_no_selected.length;
				}
			});
		}

		if (data.is_return) {
			console.log("Setting return values for discounts");
			this.discount_amount = -data.discount_amount;
			this.additional_discount_percentage = -data.additional_discount_percentage;
			this.return_doc = data;
		} else {
			this.eventBus.emit("set_pos_coupons", data.posa_coupons);
		}

		console.log("load_invoice completed, invoice state:", {
			invoiceType: this.invoiceType,
			is_return: this.invoice_doc.is_return,
			items: this.items.length,
			customer: this.customer,
		});
	},

	// Save and clear the current invoice (draft logic)
	save_and_clear_invoice() {
		const doc = this.get_invoice_doc();
		if (doc.name) {
			old_invoice = this.update_invoice(doc);
		} else {
			if (doc.items.length) {
				old_invoice = this.update_invoice(doc);
			} else {
				this.eventBus.emit("show_message", {
					title: `Nothing to save`,
					color: "error",
				});
			}
		}
		if (!old_invoice) {
			this.eventBus.emit("show_message", {
				title: `Error saving the current invoice`,
				color: "error",
			});
		} else {
			this.clear_invoice(); // This already calls setDefaultCustomerAfterClear()

			// Ensure default customer is set after save and clear
			this.$nextTick(() => {
				this.setDefaultCustomerAfterClear();
			});

			return old_invoice;
		}
	},

	// Start a new order (or return order) with provided data
	async new_order(data = {}) {
		let old_invoice = null;
		this.eventBus.emit("set_customer_readonly", false);
		this.expanded = [];
		this.posa_offers = [];
		this.eventBus.emit("set_pos_coupons", []);
		this.posa_coupons = [];
		this.return_doc = "";
		if (!data.name && !data.is_return) {
			this.items = [];
			this.customer = this.pos_profile.customer;
			this.invoice_doc = "";
			this.discount_amount = 0;
			this.additional_discount_percentage = 0;
			this.invoiceType = "Invoice";
			this.invoiceTypes = ["Invoice", "Order"];
			
			// Set default customer after clearing
			this.setDefaultCustomerAfterClear();
		} else {
			if (data.is_return) {
				// For return without invoice case, check if there's a return_against
				// Only set customer readonly if this is a return with reference to an invoice
				if (data.return_against) {
					this.eventBus.emit("set_customer_readonly", true);
				} else {
					// Allow customer selection for returns without invoice
					this.eventBus.emit("set_customer_readonly", false);
				}
				this.invoiceType = "Return";
				this.invoiceTypes = ["Return"];
			}
			this.invoice_doc = data;
			this.items = data.items;
			this.update_items_details(this.items);
			this.posa_offers = data.posa_offers || [];
			this.items.forEach((item) => {
				if (!item.posa_row_id) {
					item.posa_row_id = this.makeid(20);
				}
				if (item.batch_no) {
					this.set_batch_qty(item, item.batch_no);
				}
			});
			this.customer = data.customer;
			this.posting_date = this.formatDateForBackend(data.posting_date || frappe.datetime.nowdate());
			this.discount_amount = data.discount_amount;
			this.additional_discount_percentage = data.additional_discount_percentage;
			this.items.forEach((item) => {
				if (item.serial_no) {
					item.serial_no_selected = [];
					const serial_list = item.serial_no.split("\n");
					serial_list.forEach((element) => {
						if (element.length) {
							item.serial_no_selected.push(element);
						}
					});
					item.serial_no_selected_count = item.serial_no_selected.length;
				}
			});
		}
		return old_invoice;
	},

	// Build the invoice document object for backend submission
	get_invoice_doc() {
		let doc = {};
		if (this.invoice_doc.name) {
			doc = { ...this.invoice_doc };
		}

		// Always set these fields first
		if (this.invoiceType === "Order" && this.pos_profile.posa_create_only_sales_order) {
			doc.doctype = "Sales Order";
		} else {
			doc.doctype = "Sales Invoice";
		}
		doc.is_pos = 1;
		doc.ignore_pricing_rule = 1;
		doc.company = doc.company || this.pos_profile.company;
		doc.pos_profile = doc.pos_profile || this.pos_profile.name;

		// Currency related fields
		doc.currency = this.selected_currency || this.pos_profile.currency;
		doc.conversion_rate =
			(this.invoice_doc && this.invoice_doc.conversion_rate) || this.conversion_rate || 1;

		// Use actual price list currency if available
		doc.price_list_currency = this.price_list_currency || doc.currency;

		doc.plc_conversion_rate =
			(this.invoice_doc && this.invoice_doc.plc_conversion_rate) ||
			(doc.price_list_currency === doc.currency ? 1 : this.exchange_rate);

		// Other fields
		doc.campaign = doc.campaign || this.pos_profile.campaign;
		doc.selling_price_list = this.pos_profile.selling_price_list;
		doc.naming_series = doc.naming_series || this.pos_profile.naming_series;
		doc.customer = this.customer;

		// Determine if this is a return invoice
		const isReturn = this.isReturnInvoice;
		doc.is_return = isReturn ? 1 : 0;

		// Calculate amounts in selected currency
		const items = this.get_invoice_items();
		doc.items = items;

		// Calculate totals in selected currency ensuring negative values for returns
		let total = this.Total;
		if (isReturn && total > 0) total = -Math.abs(total);

		doc.total = total;
		doc.net_total = total; // Will adjust later if taxes are inclusive
		doc.base_total = total * (this.exchange_rate || 1);
		doc.base_net_total = total * (this.exchange_rate || 1);

		// Apply discounts with correct sign for returns - only use one discount type
		let discountAmount = flt(this.additional_discount);
		let discountPercentage = flt(this.additional_discount_percentage);

		// Choose one discount mechanism: if user entered percentage, use percentage; if amount, use amount
		if (discountPercentage !== 0) {
			// User entered percentage, set amount to 0
			discountAmount = 0;
			if (isReturn && discountPercentage > 0) discountPercentage = -Math.abs(discountPercentage);
			doc.additional_discount_percentage = discountPercentage;
			doc.discount_amount = 0;
			doc.base_discount_amount = 0;
		} else if (discountAmount !== 0) {
			// User entered amount, set percentage to 0
			discountPercentage = 0;
			if (isReturn && discountAmount > 0) discountAmount = -Math.abs(discountAmount);
			doc.discount_amount = discountAmount;
			doc.base_discount_amount = discountAmount * (this.exchange_rate || 1);
			doc.additional_discount_percentage = 0;
		} else {
			// No discount
			doc.discount_amount = 0;
			doc.base_discount_amount = 0;
			doc.additional_discount_percentage = 0;
		}

		// Calculate grand total with correct sign for returns
		let grandTotal = this.subtotal;

		// Prepare taxes array
		doc.taxes = [];
		if (this.invoice_doc && this.invoice_doc.taxes) {
			let totalTax = 0;
			this.invoice_doc.taxes.forEach((tax) => {
				if (tax.tax_amount) {
					grandTotal += flt(tax.tax_amount);
					totalTax += flt(tax.tax_amount);
				}
				doc.taxes.push({
					account_head: tax.account_head,
					charge_type: tax.charge_type || "On Net Total",
					description: tax.description,
					rate: tax.rate,
					included_in_print_rate: tax.included_in_print_rate || 0,
					tax_amount: tax.tax_amount,
					total: tax.total,
					base_tax_amount: tax.tax_amount * (this.exchange_rate || 1),
					base_total: tax.total * (this.exchange_rate || 1),
				});
			});
			doc.total_taxes_and_charges = totalTax;
		} else if (isOffline()) {
			const tmpl = getTaxTemplate(this.pos_profile.taxes_and_charges);
			if (tmpl && Array.isArray(tmpl.taxes)) {
				const inclusive = getTaxInclusiveSetting();
				let runningTotal = grandTotal;
				let totalTax = 0;
				tmpl.taxes.forEach((row) => {
					let tax_amount = 0;
					if (row.charge_type === "Actual") {
						tax_amount = flt(row.tax_amount || 0);
					} else if (inclusive) {
						tax_amount = flt((doc.total * flt(row.rate)) / 100);
					} else {
						tax_amount = flt((doc.net_total * flt(row.rate)) / 100);
					}
					if (!inclusive) {
						runningTotal += tax_amount;
					}
					totalTax += tax_amount;
					doc.taxes.push({
						account_head: row.account_head,
						charge_type: row.charge_type || "On Net Total",
						description: row.description,
						rate: row.rate,
						included_in_print_rate: inclusive ? 1 : 0,
						tax_amount: tax_amount,
						total: runningTotal,
						base_tax_amount: tax_amount * (this.exchange_rate || 1),
						base_total: runningTotal * (this.exchange_rate || 1),
					});
				});
				if (inclusive) {
					doc.net_total = doc.total - totalTax;
					doc.base_net_total = doc.net_total * (this.exchange_rate || 1);
					grandTotal = doc.total;
				} else {
					grandTotal = runningTotal;
				}
				doc.total_taxes_and_charges = totalTax;
			}
		}

		if (isReturn && grandTotal > 0) grandTotal = -Math.abs(grandTotal);

		doc.grand_total = grandTotal;
		doc.base_grand_total = grandTotal * (this.exchange_rate || 1);

		// Apply rounding to get rounded total unless disabled in POS Profile
		if (this.pos_profile.disable_rounded_total) {
			doc.rounded_total = flt(grandTotal, this.currency_precision);
			doc.base_rounded_total = flt(doc.base_grand_total, this.currency_precision);
		} else {
			doc.rounded_total = this.roundAmount(grandTotal);
			doc.base_rounded_total = this.roundAmount(doc.base_grand_total);
		}

		// Add POS specific fields
		doc.posa_pos_opening_shift = this.pos_opening_shift.name;
		doc.payments = this.get_payments();

		// Handle return specific fields
		if (isReturn) {
			if (this.invoice_doc.return_against) {
				doc.return_against = this.invoice_doc.return_against;
			}
			doc.update_stock = 1;

			// Double-check all values are negative
			if (doc.grand_total > 0) doc.grand_total = -Math.abs(doc.grand_total);
			if (doc.base_grand_total > 0) doc.base_grand_total = -Math.abs(doc.base_grand_total);
			if (doc.rounded_total > 0) doc.rounded_total = -Math.abs(doc.rounded_total);
			if (doc.base_rounded_total > 0) doc.base_rounded_total = -Math.abs(doc.base_rounded_total);
			if (doc.total > 0) doc.total = -Math.abs(doc.total);
			if (doc.base_total > 0) doc.base_total = -Math.abs(doc.base_total);
			if (doc.net_total > 0) doc.net_total = -Math.abs(doc.net_total);
			if (doc.base_net_total > 0) doc.base_net_total = -Math.abs(doc.base_net_total);

			// Ensure payments have negative amounts
			if (doc.payments && doc.payments.length) {
				doc.payments.forEach((payment) => {
					if (payment.amount > 0) payment.amount = -Math.abs(payment.amount);
					if (payment.base_amount > 0) payment.base_amount = -Math.abs(payment.base_amount);
				});
			}
		}

		// Add offer details - keep as arrays for document compatibility
		doc.posa_offers = this.posa_offers || [];
		doc.posa_coupons = this.posa_coupons || [];
		doc.posa_delivery_charges = this.selected_delivery_charge?.name || null;
		doc.posa_delivery_charges_rate = this.delivery_charges_rate || 0;
		doc.posting_date = this.formatDateForBackend(this.posting_date_display);

		// Add flags to ensure proper rate handling
		doc.ignore_pricing_rule = 1;

		// Preserve the real price list currency
		doc.price_list_currency = this.price_list_currency || doc.currency;
		doc.plc_conversion_rate = this.exchange_rate || doc.conversion_rate;
		doc.ignore_default_fields = 1; // Add this to prevent default field updates

		// Add custom fields to track offer rates
		doc.posa_is_offer_applied = this.posa_offers.length > 0 ? 1 : 0;

		// Calculate base amounts using the exchange rate
		const baseCurrency = this.price_list_currency || this.pos_profile.currency;
		if (this.selected_currency !== baseCurrency) {
			// For returns, we need to ensure negative values
			const multiplier = isReturn ? -1 : 1;

			// Convert amounts back to the base currency
			doc.base_total = (total / this.exchange_rate) * multiplier;
			doc.base_net_total = (total / this.exchange_rate) * multiplier;
			doc.base_discount_amount = (discountAmount / this.exchange_rate) * multiplier;
			doc.base_grand_total = (grandTotal / this.exchange_rate) * multiplier;
			doc.base_rounded_total = (grandTotal / this.exchange_rate) * multiplier;
		} else {
			// Same currency, just ensure negative values for returns
			const multiplier = isReturn ? -1 : 1;
			// When in base currency, the base amounts are the same as the regular amounts
			doc.base_total = total * multiplier;
			doc.base_net_total = total * multiplier;
			doc.base_discount_amount = discountAmount * multiplier;
			doc.base_grand_total = grandTotal * multiplier;
			doc.base_rounded_total = grandTotal * multiplier;
		}

		// Ensure payments have correct base amounts
		if (doc.payments && doc.payments.length) {
			doc.payments.forEach((payment) => {
				if (this.selected_currency !== baseCurrency) {
					// Convert payment amount to base currency
					payment.base_amount = payment.amount / this.exchange_rate;
				} else {
					payment.base_amount = payment.amount;
				}

				// For returns, ensure negative values
				if (isReturn) {
					payment.amount = -Math.abs(payment.amount);
					payment.base_amount = -Math.abs(payment.base_amount);
				}
			});
		}

		return doc;
	},

	// Get invoice doc from order doc (for sales order to invoice conversion)
	async get_invoice_from_order_doc() {
		let doc = {};
		if (this.invoice_doc.doctype == "Sales Order") {
			await frappe.call({
				method: "posawesome.posawesome.api.invoices.create_sales_invoice_from_order",
				args: {
					sales_order: this.invoice_doc.name,
				},
				// async: false,
				callback: function (r) {
					if (r.message) {
						doc = r.message;
					}
				},
			});
		} else {
			doc = this.invoice_doc;
		}
		const Items = [];
		const updatedItemsData = this.get_invoice_items();
		doc.items.forEach((item) => {
			const updatedData = updatedItemsData.find(
				(updatedItem) => updatedItem.item_code === item.item_code,
			);
			if (updatedData) {
				item.item_code = updatedData.item_code;
				item.posa_row_id = updatedData.posa_row_id;
				item.posa_offers = typeof updatedData.posa_offers === 'string' ? updatedData.posa_offers : JSON.stringify(updatedData.posa_offers || []);
				item.posa_offer_applied = updatedData.posa_offer_applied;
				item.posa_is_offer = updatedData.posa_is_offer;
				item.posa_is_replace = updatedData.posa_is_replace;
				item.is_free_item = updatedData.is_free_item;
				item.qty = flt(updatedData.qty);
				item.rate = flt(updatedData.rate);
				item.uom = updatedData.uom;
				item.amount = flt(updatedData.qty) * flt(updatedData.rate);
				item.conversion_factor = updatedData.conversion_factor;
				item.serial_no = updatedData.serial_no;
				item.discount_percentage = flt(updatedData.discount_percentage);
				item.discount_amount = flt(updatedData.discount_amount);
				item.batch_no = updatedData.batch_no;
				item.posa_notes = updatedData.posa_notes;
				item.posa_delivery_date = this.formatDateForDisplay(updatedData.posa_delivery_date);
				item.price_list_rate = updatedData.price_list_rate;
				Items.push(item);
			}
		});

		doc.items = Items;
		const newItems = [...doc.items];
		const existingItemCodes = new Set(newItems.map((item) => item.item_code));
		updatedItemsData.forEach((updatedItem) => {
			if (!existingItemCodes.has(updatedItem.item_code)) {
				newItems.push(updatedItem);
			}
		});
		doc.items = newItems;
		doc.update_stock = 1;
		doc.is_pos = 1;
		doc.payments = this.get_payments();
		return doc;
	},

	// Prepare items array for invoice doc
	get_invoice_items() {
		const items_list = [];
		const isReturn = this.isReturnInvoice;

		this.items.forEach((item) => {
			const new_item = {
				item_code: item.item_code,
				// Retain the item name for offline invoices
				// Fallback to item_code if item_name is not available
				item_name: item.item_name || item.item_code,
				posa_row_id: item.posa_row_id,
				posa_offers: item.posa_offers || JSON.stringify([]),
				posa_offer_applied: item.posa_offer_applied,
				posa_is_offer: item.posa_is_offer,
				posa_is_replace: item.posa_is_replace,
				is_free_item: item.is_free_item,
				qty: flt(item.qty),
				uom: item.uom,
				conversion_factor: item.conversion_factor,
				serial_no: item.serial_no,
				// Link to original Sales Invoice Item when doing returns
				// Needed for backend validation that the item exists in
				// the referenced Sales Invoice
				...(item.sales_invoice_item && { sales_invoice_item: item.sales_invoice_item }),
				discount_percentage: flt(item.discount_percentage),
				batch_no: item.batch_no,
				posa_notes: item.posa_notes,
				posa_delivery_date: this.formatDateForBackend(item.posa_delivery_date),
			};
			if (isReturn && !new_item.sales_invoice_item && item.name) {
				new_item.sales_invoice_item = item.name;
			}

			// Handle currency conversion for rates and amounts
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.selected_currency !== baseCurrency) {
				// If exchange rate is 300 PKR = 1 USD
				// item.rate is in USD (e.g. 10 USD)
				// base_rate should be in PKR (e.g. 3000 PKR)
				// So multiply by exchange rate to get base_rate
				new_item.rate = flt(item.rate); // Keep rate in USD

				// Use pre-stored base_rate if available, otherwise calculate
				new_item.base_rate = item.base_rate || flt(item.rate / this.exchange_rate);

				new_item.price_list_rate = flt(item.price_list_rate); // Keep price list rate in USD
				new_item.base_price_list_rate =
					item.base_price_list_rate || flt(item.price_list_rate / this.exchange_rate);

				// Calculate amounts
				new_item.amount = flt(item.qty) * new_item.rate; // Amount in USD
				new_item.base_amount = new_item.amount / this.exchange_rate; // Convert to base currency

				// Handle discount amount
				new_item.discount_amount = flt(item.discount_amount); // Keep discount in USD
				new_item.base_discount_amount =
					item.base_discount_amount || flt(item.discount_amount / this.exchange_rate);
			} else {
				// Same currency, make sure we use base rates if available
				new_item.rate = flt(item.rate);
				new_item.base_rate = item.base_rate || flt(item.rate);
				new_item.price_list_rate = flt(item.price_list_rate);
				new_item.base_price_list_rate = item.base_price_list_rate || flt(item.price_list_rate);
				new_item.amount = flt(item.qty) * new_item.rate;
				new_item.base_amount = new_item.amount;
				new_item.discount_amount = flt(item.discount_amount);
				new_item.base_discount_amount = item.base_discount_amount || flt(item.discount_amount);
			}

			// For returns, ensure all amounts are negative
			if (isReturn) {
				new_item.qty = -Math.abs(new_item.qty);
				new_item.amount = -Math.abs(new_item.amount);
				new_item.base_amount = -Math.abs(new_item.base_amount);
				new_item.discount_amount = -Math.abs(new_item.discount_amount);
				new_item.base_discount_amount = -Math.abs(new_item.base_discount_amount);
			}

			items_list.push(new_item);
		});

		return items_list;
	},

	// Prepare items array for order doc
	get_order_items() {
		const items_list = [];
		this.items.forEach((item) => {
			const new_item = {
				item_code: item.item_code,
				// Retain item name to show on offline order documents
				// Use item_code if item_name is missing
				item_name: item.item_name || item.item_code,
				posa_row_id: item.posa_row_id,
				posa_offers: item.posa_offers,
				posa_offer_applied: item.posa_offer_applied,
				posa_is_offer: item.posa_is_offer,
				posa_is_replace: item.posa_is_replace,
				is_free_item: item.is_free_item,
				qty: flt(item.qty),
				rate: flt(item.rate),
				uom: item.uom,
				amount: flt(item.qty) * flt(item.rate),
				conversion_factor: item.conversion_factor,
				serial_no: item.serial_no,
				discount_percentage: flt(item.discount_percentage),
				discount_amount: flt(item.discount_amount),
				batch_no: item.batch_no,
				posa_notes: item.posa_notes,
				posa_delivery_date: item.posa_delivery_date,
				price_list_rate: item.price_list_rate,
			};
			items_list.push(new_item);
		});

		return items_list;
	},

	// Prepare payments array for invoice doc
	get_payments() {
		const payments = [];
		// Use this.subtotal which is already in selected currency and includes all calculations
		const total_amount = this.subtotal;
		let remaining_amount = total_amount;

		this.pos_profile.payments.forEach((payment, index) => {
			// For the first payment method, assign the full remaining amount
			const payment_amount = index === 0 ? remaining_amount : payment.amount || 0;

			// For return invoices, ensure payment amounts are negative
			const adjusted_amount = this.isReturnInvoice ? -Math.abs(payment_amount) : payment_amount;

			// Handle currency conversion
			// If selected_currency is USD and base is PKR:
			// amount is in USD (e.g. 10 USD)
			// base_amount should be in PKR (e.g. 3000 PKR)
			// So multiply by exchange rate to get base_amount
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			const base_amount =
				this.selected_currency !== baseCurrency
					? this.flt(adjusted_amount / (this.exchange_rate || 1), this.currency_precision)
					: adjusted_amount;

			payments.push({
				amount: adjusted_amount, // Keep in selected currency (e.g. USD)
				base_amount: base_amount, // Convert to base currency (e.g. PKR)
				mode_of_payment: payment.mode_of_payment,
				default: payment.default,
				account: payment.account || "",
				type: payment.type || "Cash",
				currency: this.selected_currency || this.pos_profile.currency,
				conversion_rate: this.conversion_rate || 1,
			});

			remaining_amount -= payment_amount;
		});

		console.log("Generated payments:", {
			currency: this.selected_currency,
			exchange_rate: this.exchange_rate,
			payments: payments.map((p) => ({
				mode: p.mode_of_payment,
				amount: p.amount,
				base_amount: p.base_amount,
			})),
		});

		return payments;
	},

	// Convert amount to selected currency
	convert_amount(amount) {
		const baseCurrency = this.price_list_currency || this.pos_profile.currency;
		if (this.selected_currency === baseCurrency) {
			return amount;
		}
		return this.flt(amount * this.exchange_rate, this.currency_precision);
	},

	// Update invoice in backend
	update_invoice(doc) {
		var vm = this;
		if (isOffline()) {
			// When offline, simply merge the passed doc with the current invoice_doc
			// to allow offline invoice creation without server calls
			vm.invoice_doc = Object.assign({}, vm.invoice_doc || {}, doc);
			return vm.invoice_doc;
		}
		frappe.call({
			method:
				doc.doctype === "Sales Order" && this.pos_profile.posa_create_only_sales_order
					? "posawesome.posawesome.api.sales_orders.update_sales_order"
					: "posawesome.posawesome.api.invoices.update_invoice",
			args: {
				data: doc,
			},
			async: false,
			callback: function (r) {
				if (r.message) {
					vm.invoice_doc = r.message;
					if (r.message.exchange_rate_date) {
						vm.exchange_rate_date = r.message.exchange_rate_date;
						const posting_backend = vm.formatDateForBackend(vm.posting_date_display);
						if (posting_backend !== vm.exchange_rate_date) {
							vm.eventBus.emit("show_message", {
								title: __(
									"Exchange rate date " +
										vm.exchange_rate_date +
										" differs from posting date " +
										posting_backend,
								),
								color: "warning",
							});
						}
					}
				}
			},
		});
		return this.invoice_doc;
	},

	// Update invoice from order in backend
	update_invoice_from_order(doc) {
		var vm = this;
		if (isOffline()) {
			// Offline mode - merge doc locally without server update
			vm.invoice_doc = Object.assign({}, vm.invoice_doc || {}, doc);
			return vm.invoice_doc;
		}
		frappe.call({
			method: "posawesome.posawesome.api.invoices.update_invoice_from_order",
			args: {
				data: doc,
			},
			async: false,
			callback: function (r) {
				if (r.message) {
					vm.invoice_doc = r.message;
					if (r.message.exchange_rate_date) {
						vm.exchange_rate_date = r.message.exchange_rate_date;
						const posting_backend = vm.formatDateForBackend(vm.posting_date_display);
						if (posting_backend !== vm.exchange_rate_date) {
							vm.eventBus.emit("show_message", {
								title: __(
									"Exchange rate date " +
										vm.exchange_rate_date +
										" differs from posting date " +
										posting_backend,
								),
								color: "warning",
							});
						}
					}
				}
			},
		});
		return this.invoice_doc;
	},

	// Process and save invoice (handles update or create)
	process_invoice() {
		const doc = this.get_invoice_doc();
		try {
			const updated_doc = this.update_invoice(doc);
			if (updated_doc && updated_doc.posting_date) {
				this.posting_date = this.formatDateForBackend(updated_doc.posting_date);
			}
			return updated_doc;
		} catch (error) {
			console.error("Error in process_invoice:", error);
			this.eventBus.emit("show_message", {
				title: __(error.message || "Error processing invoice"),
				color: "error",
			});
			return false;
		}
	},

	// Process and save invoice from order
	async process_invoice_from_order() {
		const doc = await this.get_invoice_from_order_doc();
		var up_invoice;
		if (doc.name) {
			up_invoice = await this.update_invoice_from_order(doc);
			return up_invoice;
		} else {
			return this.update_invoice_from_order(doc);
		}
	},

	// Show payment dialog after validation and processing
	async show_payment() {
		try {
			console.log("Starting show_payment process");
			console.log("Invoice state before payment:", {
				invoiceType: this.invoiceType,
				is_return: this.invoice_doc ? this.invoice_doc.is_return : false,
				items_count: this.items.length,
				customer: this.customer,
			});

			if (!this.customer) {
				console.log("Customer validation failed");
				this.eventBus.emit("show_message", {
					title: __(`Select a customer`),
					color: "error",
				});
				return;
			}

			if (!this.items.length) {
				console.log("Items validation failed - no items");
				this.eventBus.emit("show_message", {
					title: __(`Select items to sell`),
					color: "error",
				});
				return;
			}

			console.log("Basic validations passed, proceeding to main validation");
			const isValid = this.validate();
			console.log("Main validation result:", isValid);

			if (!isValid) {
				console.log("Main validation failed");
				return;
			}

			let invoice_doc;
			if (
				this.invoiceType === "Order" &&
				this.pos_profile.posa_create_only_sales_order &&
				!this.new_delivery_date &&
				!this.invoice_doc.posa_delivery_date
			) {
				console.log("Building local Sales Order doc for payment");
				invoice_doc = this.get_invoice_doc();
			} else if (this.invoice_doc.doctype == "Sales Order" && this.invoiceType === "Invoice") {
				console.log("Processing Sales Order payment");
				invoice_doc = await this.process_invoice_from_order();
			} else {
				console.log("Processing regular invoice");
				invoice_doc = this.process_invoice();
			}

			if (!invoice_doc) {
				console.log("Failed to process invoice");
				return;
			}

			// Update invoice_doc with current currency info
			invoice_doc.currency = this.selected_currency || this.pos_profile.currency;
			invoice_doc.conversion_rate = this.conversion_rate || 1;
			invoice_doc.plc_conversion_rate = this.exchange_rate || 1;

			// Preserve totals calculated on the server to ensure taxes are included
			// The process_invoice method already updates the invoice with taxes and
			// totals via the backend. Overriding those values here caused the
			// payment dialog to display amounts without taxes applied. Simply use
			// the values returned from the server instead of recalculating them on
			// the client side.

			// Update totals on the client has been disabled. The original code is
			// kept below for reference and is intentionally commented out to avoid
			// overriding the server calculated values.
			// invoice_doc.total = this.Total;
			// invoice_doc.grand_total = this.subtotal;

			// if (this.pos_profile.disable_rounded_total) {
			//   invoice_doc.rounded_total = flt(this.subtotal, this.currency_precision);
			// } else {
			//   invoice_doc.rounded_total = this.roundAmount(this.subtotal);
			// }
			// invoice_doc.base_total = this.Total * (1 / this.exchange_rate || 1);
			// invoice_doc.base_grand_total = this.subtotal * (1 / this.exchange_rate || 1);
			// if (this.pos_profile.disable_rounded_total) {
			//   invoice_doc.base_rounded_total = flt(invoice_doc.base_grand_total, this.currency_precision);
			// } else {
			//   invoice_doc.base_rounded_total = this.roundAmount(invoice_doc.base_grand_total);
			// }

			// Check if this is a return invoice
			if (this.isReturnInvoice || invoice_doc.is_return) {
				console.log("Preparing RETURN invoice for payment with:", {
					is_return: invoice_doc.is_return,
					invoiceType: this.invoiceType,
					return_against: invoice_doc.return_against,
					items: invoice_doc.items.length,
					grand_total: invoice_doc.grand_total,
				});

				// For return invoices, explicitly ensure all amounts are negative
				invoice_doc.is_return = 1;
				if (invoice_doc.grand_total > 0) invoice_doc.grand_total = -Math.abs(invoice_doc.grand_total);
				if (invoice_doc.rounded_total > 0)
					invoice_doc.rounded_total = -Math.abs(invoice_doc.rounded_total);
				if (invoice_doc.total > 0) invoice_doc.total = -Math.abs(invoice_doc.total);
				if (invoice_doc.base_grand_total > 0)
					invoice_doc.base_grand_total = -Math.abs(invoice_doc.base_grand_total);
				if (invoice_doc.base_rounded_total > 0)
					invoice_doc.base_rounded_total = -Math.abs(invoice_doc.base_rounded_total);
				if (invoice_doc.base_total > 0) doc.base_total = -Math.abs(doc.base_total);

				// Ensure all items have negative quantity and amount
				if (invoice_doc.items && invoice_doc.items.length) {
					invoice_doc.items.forEach((item) => {
						if (item.qty > 0) item.qty = -Math.abs(item.qty);
						if (item.stock_qty > 0) item.stock_qty = -Math.abs(item.stock_qty);
						if (item.amount > 0) item.amount = -Math.abs(item.amount);
					});
				}
			}

			// Get payments with correct sign (positive/negative)
			invoice_doc.payments = this.get_payments();
			console.log("Final payment data:", invoice_doc.payments);

			// Double-check return invoice payments are negative
			if ((this.isReturnInvoice || invoice_doc.is_return) && invoice_doc.payments.length) {
				invoice_doc.payments.forEach((payment) => {
					if (payment.amount > 0) payment.amount = -Math.abs(payment.amount);
					if (payment.base_amount > 0) payment.base_amount = -Math.abs(payment.base_amount);
				});
				console.log("Ensured negative payment amounts for return:", invoice_doc.payments);
			}

			console.log("Showing payment dialog with currency:", invoice_doc.currency);
			this.eventBus.emit("show_payment", "true");
			this.eventBus.emit("send_invoice_doc_payment", invoice_doc);
		} catch (error) {
			console.error("Error in show_payment:", error);
			this.eventBus.emit("show_message", {
				title: __("Error processing payment"),
				color: "error",
				message: error.message,
			});
		}
	},

	// Validate invoice before payment/submit (return logic, quantity, rates, etc)
	async validate() {
		console.log("Starting return validation");

		// For all returns, check if amounts are negative
		if (this.isReturnInvoice) {
			console.log("Validating return invoice values");

			// Check if quantities are negative
			const positiveItems = this.items.filter((item) => item.qty >= 0 || item.stock_qty >= 0);
			if (positiveItems.length > 0) {
				console.log(
					"Found positive quantities in return items:",
					positiveItems.map((i) => i.item_code),
				);
				this.eventBus.emit("show_message", {
					title: __(`Return items must have negative quantities`),
					color: "error",
				});

				// Fix the quantities to be negative
				positiveItems.forEach((item) => {
					item.qty = -Math.abs(item.qty);
					item.stock_qty = -Math.abs(item.stock_qty);
				});

				// Force update to reflect changes
				this.$forceUpdate();
			}

			// Ensure total amount is negative
			if (this.subtotal > 0) {
				console.log("Return has positive subtotal:", this.subtotal);
				this.eventBus.emit("show_message", {
					title: __(`Return total must be negative`),
					color: "warning",
				});
			}
		}

		// For return with reference to existing invoice
		if (this.invoice_doc.is_return && this.invoice_doc.return_against) {
			console.log("Return doc:", this.invoice_doc);
			console.log("Current items:", this.items);

			try {
				// Get original invoice items for comparison
				const original_items = await new Promise((resolve, reject) => {
					frappe.call({
						method: "frappe.client.get",
						args: {
							doctype: "Sales Invoice",
							name: this.invoice_doc.return_against,
						},
						callback: (r) => {
							if (r.message) {
								console.log("Original invoice data:", r.message);
								resolve(r.message.items || []);
							} else {
								reject(new Error("Original invoice not found"));
							}
						},
					});
				});

				console.log("Original invoice items:", original_items);
				console.log(
					"Original item codes:",
					original_items.map((item) => ({
						item_code: item.item_code,
						qty: item.qty,
						rate: item.rate,
					})),
				);

				// Validate each return item
				for (const item of this.items) {
					console.log("Validating return item:", {
						item_code: item.item_code,
						rate: item.rate,
						qty: item.qty,
					});

					// Normalize item codes by trimming and converting to uppercase
					const normalized_return_item_code = item.item_code.trim().toUpperCase();

					// Find matching item in original invoice
					const original_item = original_items.find(
						(orig) => orig.item_code.trim().toUpperCase() === normalized_return_item_code,
					);

					if (!original_item) {
						console.log("Item not found in original invoice:", {
							return_item_code: normalized_return_item_code,
							original_items: original_items.map((i) => i.item_code.trim().toUpperCase()),
						});

						this.eventBus.emit("show_message", {
							title: __(`Item ${item.item_code} not found in original invoice`),
							color: "error",
						});
						return false;
					}

					// Compare rates with precision
					const rate_diff = Math.abs(original_item.rate - item.rate);
					console.log("Rate comparison:", {
						return_rate: item.rate,
						orig_rate: original_item.rate,
						difference: rate_diff,
					});

					if (rate_diff > 0.01) {
						this.eventBus.emit("show_message", {
							title: __(`Rate mismatch for item ${item.item_code}`),
							color: "error",
						});
						return false;
					}

					// Compare quantities
					const return_qty = Math.abs(item.qty);
					const orig_qty = original_item.qty;
					console.log("Quantity comparison:", {
						return_qty: return_qty,
						orig_qty: orig_qty,
					});

					if (return_qty > orig_qty) {
						this.eventBus.emit("show_message", {
							title: __(
								`Return quantity cannot be greater than original quantity for item ${item.item_code}`,
							),
							color: "error",
						});
						return false;
					}
				}
			} catch (error) {
				console.error("Error in validation:", error);
				this.eventBus.emit("show_message", {
					title: __(`Error validating return: ${error.message}`),
					color: "error",
				});
				return false;
			}
		}
		return true;
	},

	// Get draft invoices from backend
	get_draft_invoices() {
		var vm = this;
		frappe.call({
			method: "posawesome.posawesome.api.invoices.get_draft_invoices",
			args: {
				pos_opening_shift: this.pos_opening_shift.name,
			},
			async: false,
			callback: function (r) {
				if (r.message) {
					vm.eventBus.emit("open_drafts", r.message);
				}
			},
		});
	},

	// Get draft orders from backend
	get_draft_orders() {
		var vm = this;
		frappe.call({
			method: "posawesome.posawesome.api.sales_orders.search_orders",
			args: {
				company: this.pos_profile.company,
				currency: this.pos_profile.currency,
			},
			async: false,
			callback: function (r) {
				if (r.message) {
					vm.eventBus.emit("open_orders", r.message);
				}
			},
		});
	},

	// Open returns dialog
	open_returns() {
		this.eventBus.emit("open_returns", this.pos_profile.company);
	},

	// Close payment dialog
	close_payments() {
		this.eventBus.emit("show_payment", "false");
	},

	// Update details for all items (fetch from backend)
	async update_items_details(items) {
		if (!items?.length) return;
		if (!this.pos_profile) return;

		try {
			const response = await frappe.call({
				method: "posawesome.posawesome.api.items.get_items_details",
				args: {
					pos_profile: JSON.stringify(this.pos_profile),
					items_data: JSON.stringify(items),
				},
			});

			if (response?.message) {
				items.forEach((item) => {
					const updated_item = response.message.find(
						(element) => element.posa_row_id == item.posa_row_id,
					);
					if (updated_item) {
						item.actual_qty = updated_item.actual_qty;
						item.serial_no_data = updated_item.serial_no_data;
						item.batch_no_data = updated_item.batch_no_data;
						item.item_uoms = updated_item.item_uoms;
						item.has_batch_no = updated_item.has_batch_no;
						item.has_serial_no = updated_item.has_serial_no;
					}
				});
			}
		} catch (error) {
			console.error("Error updating items:", error);
			this.eventBus.emit("show_message", {
				title: __("Error updating item details"),
				color: "error",
			});
		}
	},

	// Update details for a single item (fetch from backend)
       update_item_detail(item, force_update = false) {
               console.log("update_item_detail request", {
                       Item_code: item.item_code,
                       Price: item.rate,
                       Uom: item.uom,
                       force_update,
               });
               if (!item.item_code) {
                       return;
               }
		var vm = this;

		// Remove this block which was causing the issue - rates should persist regardless of currency
		// if (item.price_list_rate && !item.posa_offer_applied) {
		//   item.rate = item.price_list_rate;
		//   this.$forceUpdate();
		// }

		frappe.call({
			method: "posawesome.posawesome.api.items.get_item_detail",
			args: {
				warehouse: this.pos_profile.warehouse,
				doc: this.get_invoice_doc(),
				price_list: this.selected_price_list || this.pos_profile.selling_price_list,
				item: {
					item_code: item.item_code,
					customer: this.customer,
					doctype: "Sales Invoice",
					name: "New Sales Invoice 1",
					company: this.pos_profile.company,
					conversion_rate: 1,
					currency: this.pos_profile.currency,
					qty: item.qty,
					price_list_rate: item.base_price_list_rate || item.price_list_rate,
					child_docname: "New Sales Invoice Item 1",
					cost_center: this.pos_profile.cost_center,
					pos_profile: this.pos_profile.name,
					uom: item.uom,
					tax_category: "",
					transaction_type: "selling",
					update_stock: this.pos_profile.update_stock,
					price_list: this.get_price_list(),
					has_batch_no: item.has_batch_no,
					serial_no: item.serial_no,
					batch_no: item.batch_no,
					is_stock_item: item.is_stock_item,
				},
			},
			callback: function (r) {
				if (r.message) {
					const data = r.message;
					// Ensure price list currency is synced from server response
					if (data.price_list_currency) {
						vm.price_list_currency = data.price_list_currency;
					}

					if (!item.original_currency) {
						item.original_currency =
							data.price_list_currency || vm.price_list_currency || vm.selected_currency;
					}
					if (!item.original_rate) {
						item.original_rate = data.price_list_rate;
					}
					if (data.batch_no_data) {
						item.batch_no_data = data.batch_no_data;
					}
					if (
						item.has_batch_no &&
						vm.pos_profile.posa_auto_set_batch &&
						!item.batch_no &&
						data.batch_no_data &&
						data.batch_no_data.length > 0
					) {
						item.batch_no_data = data.batch_no_data;
						// Pass null instead of undefined to avoid console warning
						vm.set_batch_qty(item, null, false);
					}

					// First save base rates if not exists or when force update is requested
					// BASE RATES MUST ALWAYS BE IN STOCK UOM - NOT UOM SPECIFIC!
					// Server may return UOM-specific price, but base rates should always be stock UOM
					if (force_update || !item.base_rate) {
						console.log("update_item_detail: setting base rates", {
							Item_code: item.item_code,
							server_price_list_rate: data.price_list_rate,
							item_uom: item.uom,
							stock_uom: item.stock_uom,
							conversion_factor: item.conversion_factor,
							has_uom_conversion: item.uom !== item.stock_uom
						});

						// If server returns UOM-specific price but item has different UOM, convert back to stock UOM
						let stockUOMPrice = data.price_list_rate;
						if (item.uom && item.uom !== item.stock_uom && item.conversion_factor && item.conversion_factor !== 1) {
							// Convert UOM price back to stock UOM price
							stockUOMPrice = data.price_list_rate / item.conversion_factor;
							console.log("update_item_detail: converted UOM price back to stock UOM", {
								Item_code: item.item_code,
								uom_price: data.price_list_rate,
								conversion_factor: item.conversion_factor,
								stock_uom_price: stockUOMPrice
							});
						}

						// Always store base rates in stock UOM
						if (stockUOMPrice !== 0 || !item.base_price_list_rate) {
							item.base_price_list_rate = stockUOMPrice;
							if (!item.posa_offer_applied) {
								item.base_rate = stockUOMPrice;
							}
							console.log("update_item_detail: base rates set to stock UOM", {
								Item_code: item.item_code,
								base_rate: item.base_rate,
								base_price_list_rate: item.base_price_list_rate
							});
						}
					}

					// Only update rates if no offer is applied
					if (!item.posa_offer_applied) {
						const companyCurrency = vm.pos_profile.currency;
						const baseCurrency = companyCurrency;

						// Check if rate has been modified by UOM conversion (different from base_rate)
						const rateModifiedByUOM = item.rate && item.rate !== item.base_rate && item.uom !== item.stock_uom;

						console.log("Rate modification check:", {
							Item_code: item.item_code,
							current_rate: item.rate,
							base_rate: item.base_rate,
							uom: item.uom,
							stock_uom: item.stock_uom,
							rateModifiedByUOM: rateModifiedByUOM
						});

						if (
							vm.selected_currency === vm.price_list_currency &&
							vm.selected_currency !== companyCurrency
						) {
							const conv = vm.conversion_rate || 1;
							item.price_list_rate = vm.flt(
								item.base_price_list_rate / conv,
								vm.currency_precision,
							);

							if (!item._manual_rate_set && !rateModifiedByUOM) {
								item.rate = vm.flt(item.base_rate / conv, vm.currency_precision);
							}
						} else if (vm.selected_currency !== baseCurrency) {
							const exchange_rate = vm.exchange_rate || 1;
							item.price_list_rate = vm.flt(
								item.base_price_list_rate * exchange_rate,
								vm.currency_precision,
							);

							if (!rateModifiedByUOM) {
								item.rate = vm.flt(item.base_rate * exchange_rate, vm.currency_precision);
							}
						} else {
							item.price_list_rate = item.base_price_list_rate;

							if (!item._manual_rate_set && !rateModifiedByUOM) {
								item.rate = item.base_rate;
							}
						}
					} else {
						// For items with offers, only update price_list_rate
						const companyCurrency = vm.pos_profile.currency;
						const baseCurrency = companyCurrency;

						if (
							vm.selected_currency === vm.price_list_currency &&
							vm.selected_currency !== companyCurrency
						) {
							const conv = vm.conversion_rate || 1;
							item.price_list_rate = vm.flt(
								item.base_price_list_rate / conv,
								vm.currency_precision,
							);
						} else if (vm.selected_currency !== baseCurrency) {
							const exchange_rate = vm.exchange_rate || 1;
							item.price_list_rate = vm.flt(
								item.base_price_list_rate * exchange_rate,
								vm.currency_precision,
							);
						} else {
							item.price_list_rate = item.base_price_list_rate;
						}
					}

					// Handle customer discount only if no offer is applied
					if (
						!item.posa_offer_applied &&
						vm.pos_profile.posa_apply_customer_discount &&
						vm.customer_info.posa_discount > 0 &&
						vm.customer_info.posa_discount <= 100 &&
						item.posa_is_offer == 0 &&
						!item.posa_is_replace
					) {
						const discount_percent =
							item.max_discount > 0
								? Math.min(item.max_discount, vm.customer_info.posa_discount)
								: vm.customer_info.posa_discount;

						item.discount_percentage = discount_percent;

						// Calculate discount in selected currency
						const discount_amount = vm.flt(
							(item.price_list_rate * discount_percent) / 100,
							vm.currency_precision,
						);
						item.discount_amount = discount_amount;

						// Also store base discount amount
						item.base_discount_amount = vm.flt(
							(item.base_price_list_rate * discount_percent) / 100,
							vm.currency_precision,
						);

						// Update rates with discount
						item.rate = vm.flt(item.price_list_rate - discount_amount, vm.currency_precision);
						item.base_rate = vm.flt(
							item.base_price_list_rate - item.base_discount_amount,
							vm.currency_precision,
						);
					}

					// Update other item details
					item.last_purchase_rate = data.last_purchase_rate;
					item.projected_qty = data.projected_qty;
					item.reserved_qty = data.reserved_qty;
					item.conversion_factor = data.conversion_factor;
					item.stock_qty = data.stock_qty;
					item.actual_qty = data.actual_qty;
					item.stock_uom = data.stock_uom;
					item.has_serial_no = data.has_serial_no;
					item.has_batch_no = data.has_batch_no;

					// Calculate final amount
					item.amount = vm.flt(item.qty * item.rate, vm.currency_precision);
					item.base_amount = vm.flt(item.qty * item.base_rate, vm.currency_precision);

					// Log updated rates for debugging
					console.log(`Updated rates for ${item.item_code} on expand:`, {
						Item_code: item.item_code,
						Price: item.rate,
						Uom: item.uom,
						base_rate: item.base_rate,
						rate: item.rate,
						base_price_list_rate: item.base_price_list_rate,
						price_list_rate: item.price_list_rate,
						exchange_rate: vm.exchange_rate,
						selected_currency: vm.selected_currency,
						default_currency: vm.pos_profile.currency,
						stock_uom: item.stock_uom,
						conversion_factor: item.conversion_factor,
						needs_uom_conversion: item.uom !== item.stock_uom
					});

					// CRITICAL: Do NOT override rate if it was already set by UOM conversion
					// Only update if rate is still the old value
					const shouldUpdateRate = !item.rate || item.rate === item.base_rate;
					console.log("Rate update decision:", {
						Item_code: item.item_code,
						current_rate: item.rate,
						base_rate: item.base_rate,
						shouldUpdateRate: shouldUpdateRate
					});

					// If item has different UOM than stock UOM, ensure UOM conversion is applied
					if (item.uom && item.uom !== item.stock_uom) {
						console.log("Applying UOM conversion after update_item_detail", {
							Item_code: item.item_code,
							uom: item.uom,
							stock_uom: item.stock_uom,
							base_rate: item.base_rate,
							rate_before_conversion: item.rate,
							force_update: force_update
						});
						// Always apply UOM conversion after base rates are set
						setTimeout(() => {
							vm.calc_uom(item, item.uom);
							// Force update after UOM conversion to ensure ItemsTable gets updated
							setTimeout(() => {
								vm.$forceUpdate();
								console.log("Force update after UOM conversion", {
									Item_code: item.item_code,
									final_rate: item.rate,
									final_uom: item.uom
								});
							}, 50);
						}, 100);
					}

					// Force update UI immediately
					vm.$forceUpdate();

					// Trigger discount calculation after item detail update (if not already applying)
					if (!vm.isApplyingDiscount) {
						vm.$nextTick(() => {
							setTimeout(() => {
								vm.calculateDiscountsDebounced();
							}, 10);
						});
					}
				}
			},
		});
	},

	// Fetch customer details (info, price list, etc)
	async fetch_customer_details() {
		var vm = this;
		if (!this.customer) return;

		if (isOffline()) {
			try {
				const cached = (getCustomerStorage() || []).find(
					(c) => c.name === vm.customer || c.customer_name === vm.customer,
				);
				if (cached) {
					vm.customer_info = { ...cached };
					if (vm.pos_profile.posa_force_reload_items && cached.customer_price_list) {
						vm.selected_price_list = cached.customer_price_list;
						vm.eventBus.emit("update_customer_price_list", cached.customer_price_list);
						vm.apply_cached_price_list(cached.customer_price_list);
					}
					return;
				}
				const queued = (getOfflineCustomers() || [])
					.map((e) => e.args)
					.find((c) => c.customer_name === vm.customer);
				if (queued) {
					vm.customer_info = { ...queued, name: queued.customer_name };
					if (vm.pos_profile.posa_force_reload_items && queued.customer_price_list) {
						vm.selected_price_list = queued.customer_price_list;
						vm.eventBus.emit("update_customer_price_list", queued.customer_price_list);
						vm.apply_cached_price_list(queued.customer_price_list);
					}
					return;
				}
			} catch (error) {
				console.error("Failed to fetch cached customer", error);
			}
		}

		try {
			const r = await frappe.call({
				method: "posawesome.posawesome.api.customers.get_customer_info",
				args: {
					customer: vm.customer,
				},
			});
			const message = r.message;
			if (!r.exc) {
				vm.customer_info = {
					...message,
				};
			}
			// When force reload is enabled, automatically switch to the
			// customer's default price list so that item rates are fetched
			// correctly from the server.
			if (vm.pos_profile.posa_force_reload_items && message.customer_price_list) {
				vm.selected_price_list = message.customer_price_list;
				vm.eventBus.emit("update_customer_price_list", message.customer_price_list);
				vm.apply_cached_price_list(message.customer_price_list);
			}
		} catch (error) {
			console.error("Failed to fetch customer details", error);
		}
	},

	// Get price list for current customer
	get_price_list() {
		// Use the currently selected price list if available,
		// otherwise fall back to the POS Profile selling price list
		return this.selected_price_list || this.pos_profile.selling_price_list;
	},

	// Update price list for customer
	update_price_list() {
		// Only set the POS Profile price list if it has changed
		const price_list = this.pos_profile.selling_price_list;
		if (this.selected_price_list !== price_list) {
			this.selected_price_list = price_list;
			// Clear any customer specific price list to avoid reloading items
			this.eventBus.emit("update_customer_price_list", null);
		}
	},

	// Apply cached price list rates to existing invoice items
	apply_cached_price_list(price_list) {
		const cached = getCachedPriceListItems(price_list);
		if (!cached) {
			return;
		}

		const map = {};
		cached.forEach((ci) => {
			map[ci.item_code] = ci;
		});

		this.items.forEach((item) => {
			const ci = map[item.item_code];
			if (!ci) return;

			const newRate = ci.rate || ci.price_list_rate;
			const priceCurrency = ci.currency || this.selected_currency;

			if (!item.original_currency) {
				item.original_currency = priceCurrency;
			}
			if (!item.original_rate) {
				item.original_rate = newRate;
			}

			if (priceCurrency === this.selected_currency) {
				const companyCurrency = this.pos_profile.currency;
				if (priceCurrency !== companyCurrency) {
					const conv = this.conversion_rate || 1;
					item.base_price_list_rate = newRate * conv;
					if (!item._manual_rate_set) {
						item.base_rate = newRate * conv;
					}
				} else {
					item.base_price_list_rate = newRate;
					if (!item._manual_rate_set) {
						item.base_rate = newRate;
					}
				}
				item.price_list_rate = newRate;
				if (!item._manual_rate_set) {
					item.rate = newRate;
				}
			} else {
				// Rate in base currency
				if (newRate !== 0 || !item.base_price_list_rate) {
					item.base_price_list_rate = newRate;
					if (!item._manual_rate_set) {
						item.base_rate = newRate;
					}
				}

				const baseCurrency = this.pos_profile.currency;
				if (this.selected_currency !== baseCurrency) {
					const conv = this.exchange_rate || 1;
					const convRate = this.flt(newRate * conv, this.currency_precision);
					if (newRate !== 0 || !item.price_list_rate) {
						item.price_list_rate = convRate;
					}
					if (!item._manual_rate_set && (newRate !== 0 || !item.rate)) {
						item.rate = convRate;
					}
				} else {
					if (newRate !== 0 || !item.price_list_rate) {
						item.price_list_rate = newRate;
					}
					if (!item._manual_rate_set && (newRate !== 0 || !item.rate)) {
						item.rate = newRate;
					}
				}
			}

			// Recalculate final amounts
			item.amount = this.flt(item.qty * item.rate, this.currency_precision);
			item.base_amount = this.flt(item.qty * item.base_rate, this.currency_precision);
		});

		this.$forceUpdate();
	},

	// Update additional discount amount based on percentage
	update_discount_umount() {
		const value = flt(this.additional_discount_percentage);
		// If value is too large, reset to 0
		if (value < -100 || value > 100) {
			this.additional_discount_percentage = 0;
			this.additional_discount = 0;
			return;
		}

		// Calculate discount amount based on percentage
		if (this.Total && this.Total !== 0) {
			this.additional_discount = (this.Total * value) / 100;
		} else {
			this.additional_discount = 0;
		}
	},

	// Calculate prices and discounts for an item based on field change
	async calc_prices(item, value, $event) {
		if (!$event?.target?.id || !item) return;

		const fieldId = $event.target.id;
		let newValue = flt(value, this.currency_precision);

		try {
			// Flag to track manual rate changes
			if (fieldId === "rate") {
				item._manual_rate_set = true;
			}

			// Handle negative values
			if (newValue < 0) {
				newValue = 0;
				this.eventBus.emit("show_message", {
					title: __("Negative values not allowed"),
					color: "error",
				});
			}

			// price_list_rate is always in selected currency, base_price_list_rate is always in base currency
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			const converted_price_list_rate = item.price_list_rate; // Already in selected currency

			// Field-wise calculations
			switch (fieldId) {
				case "rate":
					// Store base rate and convert to selected currency
					item.base_rate = this.flt(newValue * this.exchange_rate, this.currency_precision);
					item.rate = newValue;

					// Calculate discount amount in selected currency
					item.discount_amount = this.flt(
						converted_price_list_rate - item.rate,
						this.currency_precision,
					);
					item.base_discount_amount = this.flt(
						item.base_price_list_rate - item.base_rate,
						this.currency_precision,
					);

					// Calculate percentage based on converted values
					if (converted_price_list_rate) {
						item.discount_percentage = this.flt(
							(item.discount_amount / converted_price_list_rate) * 100,
							this.float_precision,
						);
					}
					break;

				case "price_list_rate":
					item._manual_rate_set = true;
					item.base_price_list_rate = this.flt(
						newValue * this.exchange_rate,
						this.currency_precision,
					);
					item.price_list_rate = newValue;
					item.base_rate = item.base_price_list_rate;
					item.rate = newValue;
					item.discount_amount = 0;
					item.base_discount_amount = 0;
					item.discount_percentage = 0;
					break;

				case "discount_amount":
					console.log("[calc_prices] Event Target ID:", fieldId);
					console.log("[calc_prices] RAW value received by function:", value); // <-- ADDED THIS
					console.log("[calc_prices] Original item.price_list_rate:", item.price_list_rate);
					console.log(
						"[calc_prices] Converted price_list_rate for calc:",
						converted_price_list_rate,
					);
					console.log("[calc_prices] Input value (newValue before Math.min):", newValue);

					// Ensure discount amount doesn't exceed price list rate
					newValue = Math.min(newValue, converted_price_list_rate);
					console.log("[calc_prices] Input value (newValue after Math.min):", newValue);

					// selected currency
					item.discount_amount = newValue;
					item.rate = this.flt(item.price_list_rate - newValue, this.currency_precision);

					// base currency
					item.base_discount_amount = this.flt(newValue * this.exchange_rate, this.currency_precision);
					item.base_rate = this.flt(item.base_price_list_rate - item.base_discount_amount, this.currency_precision);

					console.log("[calc_prices] Updated item.discount_amount:", item.discount_amount);
					console.log(
						"[calc_prices] Updated item.base_discount_amount:",
						item.base_discount_amount,
					);
					console.log("[calc_prices] Calculated item.rate:", item.rate);
					console.log("[calc_prices] Calculated item.base_rate:", item.base_rate);

					// Calculate percentage
					if (converted_price_list_rate) {
						item.discount_percentage = this.flt(
							(item.discount_amount / converted_price_list_rate) * 100,
							this.float_precision,
						);
					} else {
						item.discount_percentage = 0; // Avoid division by zero
					}
					console.log(
						"[calc_prices] Calculated item.discount_percentage:",
						item.discount_percentage,
					);
					break;

				case "discount_percentage":
					// Ensure percentage doesn't exceed 100%
					newValue = Math.min(newValue, 100);
					item.discount_percentage = this.flt(newValue, this.float_precision);

					// Calculate discount amount in selected currency
					item.discount_amount = this.flt(
						(converted_price_list_rate * item.discount_percentage) / 100,
						this.currency_precision,
					);
					item.base_discount_amount = this.flt(
						(item.base_price_list_rate * item.discount_percentage) / 100,
						this.currency_precision,
					);

					// Update rates
					item.rate = this.flt(
						converted_price_list_rate - item.discount_amount,
						this.currency_precision,
					);
					item.base_rate = this.flt(
						item.base_price_list_rate - item.base_discount_amount,
						this.currency_precision,
					);
					break;
			}

			// Ensure rate doesn't go below zero
			if (item.rate < 0) {
				item.rate = 0;
				item.base_rate = 0;
				item.discount_amount = converted_price_list_rate;
				item.base_discount_amount = item.base_price_list_rate;
				item.discount_percentage = 100;
			}

			// Update stock calculations
			this.calc_stock_qty(item, item.qty);

			// Use async flow to avoid race conditions
			await this.updateItemCalculations(item);

		} catch (error) {
			console.error("Error calculating prices:", error);
			this.eventBus.emit("show_message", {
				title: __("Error calculating prices"),
				color: "error",
			});
		}
	},

	// Async method to handle item calculations and trigger discount calculation
	async updateItemCalculations(item) {
		// Force UI update
		this.$forceUpdate();

		// Trigger discount calculation after price/discount changes (if not already applying)
		if (!this.isApplyingDiscount) {
			// Use nextTick to ensure DOM updates are complete
			await this.$nextTick();
			// Trigger debounced discount calculation
			this.calculateDiscountsDebounced();
		}
	},

	// Unified async method to handle all item updates and prevent race conditions
	async updateItemAfterChanges(item, skipDiscountCalc = false) {
		// Force UI update
		this.$forceUpdate();

		// Trigger discount calculation if not skipped and not already applying
		if (!skipDiscountCalc && !this.isApplyingDiscount) {
			// Use nextTick to ensure DOM updates are complete
			await this.$nextTick();
			// Trigger debounced discount calculation
			this.calculateDiscountsDebounced();
		}
	},

	// Calculate item price and discount fields
	calc_item_price(item) {
		// Skip recalculation if called from update_item_rates to avoid double calculations
		if (item._skip_calc) {
			item._skip_calc = false;
			return;
		}

		const baseCurrency = this.price_list_currency || this.pos_profile.currency;

		if (!item.posa_offer_applied) {
			if (item.price_list_rate) {
				// Always work with base rates first
				if (!item.base_price_list_rate) {
					item.base_price_list_rate = item.price_list_rate;
					item.base_rate = item.rate;
				}

				// Convert to selected currency
				if (this.selected_currency !== baseCurrency) {
					// Convert base currency values to the selected currency
					item.price_list_rate = this.flt(
						item.base_price_list_rate * this.exchange_rate,
						this.currency_precision,
					);
					item.rate = this.flt(item.base_rate * this.exchange_rate, this.currency_precision);
				} else {
					item.price_list_rate = item.base_price_list_rate;
					item.rate = item.base_rate;
				}
			}
		}

		// Handle discounts
		if (item.discount_percentage) {
			// Calculate discount in selected currency
			const price_list_rate = item.price_list_rate;
			const discount_amount = this.flt(
				(price_list_rate * item.discount_percentage) / 100,
				this.currency_precision,
			);

			item.discount_amount = discount_amount;
			item.rate = this.flt(price_list_rate - discount_amount, this.currency_precision);

			// Store base discount amount
			if (this.selected_currency !== baseCurrency) {
				// Convert discount amount back to base currency by multiplying by exchange rate
				item.base_discount_amount = this.flt(
					discount_amount / this.exchange_rate,
					this.currency_precision,
				);
			} else {
				item.base_discount_amount = item.discount_amount;
			}
		}

		// Calculate amounts
		item.amount = this.flt(item.qty * item.rate, this.currency_precision);
		if (this.selected_currency !== baseCurrency) {
			// Convert amount back to base currency by dividing by exchange rate
			item.base_amount = this.flt(item.amount / this.exchange_rate, this.currency_precision);
		} else {
			item.base_amount = item.amount;
		}

		this.$forceUpdate();
	},

	// Helper: Find UOM from various sources
	find_uom(item, value) {
		console.log("calc_uom: initial UOM search", {
			item_code: item.item_code,
			searched_uom: value,
			item_uoms_count: item.item_uoms?.length || 0
		});

		// Try item UOMs first
		let new_uom = item.item_uoms?.find((element) => element.uom == value);

		// Try cached UOMs
		if (!new_uom) {
			const cached = getItemUOMs(item.item_code);
			console.log("calc_uom: checking cached UOMs", {
				item_code: item.item_code,
				cached_uoms_count: cached.length,
				searched_uom: value
			});
			if (cached.length) {
				item.item_uoms = cached;
				new_uom = cached.find((u) => u.uom == value);
				console.log("calc_uom: UOM found in cache", {
					item_code: item.item_code,
					found_uom: new_uom ? "YES" : "NO",
					uom_data: new_uom
				});
			}
		}

		// Fallback to stock UOM
		if (!new_uom && item.stock_uom === value) {
			new_uom = { uom: item.stock_uom, conversion_factor: 1 };
			if (!item.item_uoms) item.item_uoms = [];
			item.item_uoms.push(new_uom);
			console.log("calc_uom: fallback to stock UOM", {
				item_code: item.item_code,
				stock_uom: item.stock_uom,
				conversion_factor: 1
			});
		}

		if (!new_uom) {
			console.log("calc_uom: UOM not found - ERROR", {
				item_code: item.item_code,
				searched_uom: value,
				available_uoms: item.item_uoms?.map(u => u.uom) || []
			});
			this.eventBus.emit("show_message", {
				title: __("UOM not found"),
				color: "error",
			});
			return null;
		}

		return new_uom;
	},

	// Helper: Find UOM-specific price
	async find_uom_price(item, new_uom) {
		const priceList = this.get_price_list();
		let uomRate = null;

		console.log("calc_uom: searching for UOM-specific price", {
			item_code: item.item_code,
			price_list: priceList,
			uom: new_uom.uom,
			conversion_factor: new_uom.conversion_factor
		});

		// Check cache first
		if (priceList) {
			const cached = getCachedPriceListItems(priceList) || [];
			console.log("calc_uom: checking cached price list", {
				price_list: priceList,
				cached_items_count: cached.length,
				searching_for: `${item.item_code} + ${new_uom.uom}`
			});
			const match = cached.find((p) => p.item_code === item.item_code && p.uom === new_uom.uom);
			if (match) {
				uomRate = match.price_list_rate || match.rate;
				console.log("calc_uom: found UOM price in cache", {
					item_code: item.item_code,
					uom: new_uom.uom,
					uom_rate: uomRate,
					source: "cache"
				});
			}
		}

		// Fetch from server if not found in cache and not offline
		if (!uomRate && !isOffline()) {
			console.log("calc_uom: fetching UOM price from server", {
				item_code: item.item_code,
				price_list: priceList,
				uom: new_uom.uom
			});
			try {
				const r = await frappe.call({
					method: "posawesome.posawesome.api.items.get_price_for_uom",
					args: {
						item_code: item.item_code,
						price_list: priceList,
						uom: new_uom.uom,
					},
				});
				if (r.message) {
					uomRate = r.message;
					console.log("calc_uom: received UOM price from server", {
						item_code: item.item_code,
						uom: new_uom.uom,
						uom_rate: uomRate,
						source: "server"
					});
				} else {
					console.log("calc_uom: no UOM price found on server", {
						item_code: item.item_code,
						uom: new_uom.uom
					});
				}
			} catch (e) {
				console.error("calc_uom: failed to fetch UOM price from server", {
					item_code: item.item_code,
					uom: new_uom.uom,
					error: e.message
				});
			}
		}

		return uomRate;
	},

	// Helper: Apply UOM-specific pricing
	apply_uom_pricing(item, uomRate, baseCurrency) {
		console.log("calc_uom: applying UOM-specific pricing", {
			item_code: item.item_code,
			uom: item.uom,
			uom_rate: uomRate,
			has_offer: item.posa_offer_applied,
			selected_currency: this.selected_currency,
			base_currency: baseCurrency
		});

		// Base rates luôn theo stock UOM (chai) - không phụ thuộc UOM hiển thị
		// Lấy giá thực tế theo stock UOM từ item.base_price_list_rate
		const stockUOMBaseRate = item.base_price_list_rate || item.price_list_rate || 0;

		item.base_price_list_rate = stockUOMBaseRate; // Luôn theo stock UOM
		if (!item.posa_offer_applied) {
			item.base_rate = stockUOMBaseRate; // Luôn theo stock UOM
		}

		// Display rates theo UOM-price (để hiển thị cho user)
		if (this.selected_currency !== baseCurrency) {
			item.price_list_rate = this.flt(uomRate * this.exchange_rate, this.currency_precision);
			item.rate = this.flt(uomRate * this.exchange_rate, this.currency_precision);
			console.log("calc_uom: converted to selected currency", {
				item_code: item.item_code,
				display_price_list_rate: item.price_list_rate,
				display_rate: item.rate,
				base_rate: item.base_rate,
				exchange_rate: this.exchange_rate
			});
		} else {
			item.price_list_rate = uomRate; // Hiển thị theo UOM-price
			item.rate = uomRate; // Hiển thị theo UOM-price
			console.log("calc_uom: using base currency rates", {
				item_code: item.item_code,
				display_price_list_rate: item.price_list_rate,
				display_rate: item.rate,
				base_rate: item.base_rate
			});
		}

		this.calc_stock_qty(item, item.qty);
		this.$forceUpdate();
		console.log("calc_uom: completed UOM-specific pricing", {
			item_code: item.item_code,
			display_rate: item.rate,
			base_rate: item.base_rate,
			final_uom: item.uom
		});
	},

	// Helper: Process offer items with UOM conversion
	process_offer_item_uom(item, new_uom, old_conversion_factor, conversion_ratio, baseCurrency) {
		console.log("calc_uom: processing offer item", {
			item_code: item.item_code,
			uom: new_uom.uom,
			conversion_factor: item.conversion_factor,
			posa_offer_applied: item.posa_offer_applied
		});

		const offer = this.posOffers && Array.isArray(this.posOffers)
			? this.posOffers.find((o) => {
					if (!o || !o.items) return false;
					const items = typeof o.items === "string" ? JSON.parse(o.items) : o.items;
					return Array.isArray(items) && items.includes(item.posa_row_id);
				})
			: null;

		console.log("calc_uom: found offer for item", {
			item_code: item.item_code,
			offer_found: offer ? "YES" : "NO",
			offer_type: offer?.discount_type,
			offer_rate: offer?.rate,
			offer_percentage: offer?.discount_percentage
		});

		if (offer && offer.discount_type === "Rate") {
			this.apply_rate_offer_uom(item, offer, baseCurrency);
		} else if (offer && offer.discount_type === "Discount Percentage") {
			this.apply_percentage_offer_uom(item, offer, conversion_ratio, baseCurrency);
		}
	},

	// Helper: Apply rate offer for UOM
	apply_rate_offer_uom(item, offer, baseCurrency) {
		console.log("calc_uom: applying rate offer", {
			item_code: item.item_code,
			original_offer_rate: offer.rate,
			conversion_factor: item.conversion_factor
		});

		// Base rates luôn theo stock UOM
		const stockUOMBaseRate = item.base_price_list_rate || item.price_list_rate || 0;
		item.base_rate = stockUOMBaseRate;
		item.base_price_list_rate = stockUOMBaseRate;

		// Display rates theo offer rate trực tiếp (offer rate đã là giá cuối cùng cho UOM)
		const displayRate = offer.rate; // Không nhân conversion_factor

		if (this.selected_currency !== baseCurrency) {
			item.rate = this.flt(displayRate * this.exchange_rate, this.currency_precision);
			item.price_list_rate = item.rate;
			console.log("calc_uom: rate offer converted to selected currency", {
				item_code: item.item_code,
				display_rate: displayRate,
				final_rate: item.rate,
				base_rate: item.base_rate,
				exchange_rate: this.exchange_rate
			});
		} else {
			item.rate = displayRate;
			item.price_list_rate = displayRate;
			console.log("calc_uom: rate offer in base currency", {
				item_code: item.item_code,
				display_rate: displayRate,
				base_rate: item.base_rate
			});
		}
	},

	// Helper: Apply percentage offer for UOM
	apply_percentage_offer_uom(item, offer, conversion_ratio, baseCurrency) {
		console.log("calc_uom: applying percentage discount offer", {
			item_code: item.item_code,
			offer_percentage: offer.discount_percentage,
			original_base_price: item.original_base_price_list_rate,
			conversion_factor: item.conversion_factor
		});

		// Base rates luôn theo stock UOM
		const stockUOMBaseRate = item.base_price_list_rate || 12;
		const baseDiscount = this.flt(
			(stockUOMBaseRate * offer.discount_percentage) / 100,
			this.currency_precision,
		);

		item.base_price_list_rate = stockUOMBaseRate;
		item.base_discount_amount = baseDiscount;
		item.base_rate = this.flt(stockUOMBaseRate - baseDiscount, this.currency_precision);

		// Display rates = (base_rate_after_discount) × conversion_factor
		const displayRate = item.base_rate * item.conversion_factor;
		const displayPriceListRate = item.base_price_list_rate * item.conversion_factor;
		const displayDiscountAmount = baseDiscount * item.conversion_factor;

		console.log("calc_uom: calculated discount for percentage offer", {
			item_code: item.item_code,
			base_discount: baseDiscount,
			base_rate_after_discount: item.base_rate,
			display_rate: displayRate
		});

		if (this.selected_currency !== baseCurrency) {
			item.price_list_rate = this.flt(displayPriceListRate * this.exchange_rate, this.currency_precision);
			item.discount_amount = this.flt(displayDiscountAmount * this.exchange_rate, this.currency_precision);
			item.rate = this.flt(displayRate * this.exchange_rate, this.currency_precision);
			console.log("calc_uom: percentage offer converted to selected currency", {
				item_code: item.item_code,
				display_price_list_rate: item.price_list_rate,
				display_discount_amount: item.discount_amount,
				display_rate: item.rate
			});
		} else {
			item.price_list_rate = displayPriceListRate;
			item.discount_amount = displayDiscountAmount;
			item.rate = displayRate;
			console.log("calc_uom: percentage offer in base currency", {
				item_code: item.item_code,
				display_price_list_rate: item.price_list_rate,
				display_discount_amount: item.discount_amount,
				display_rate: item.rate
			});
		}
	},

	// Helper: Process regular items with UOM conversion
	process_regular_item_uom(item, old_conversion_factor, baseCurrency) {
		console.log("calc_uom: processing regular item", {
			item_code: item.item_code,
			uom: item.uom,
			conversion_factor: item.conversion_factor,
			has_batch_price: !!item.batch_price,
			has_original_base_rate: !!item.original_base_rate,
			base_price_list_rate_before: item.base_price_list_rate,
			base_rate_before: item.base_rate
		});

		// Base rates luôn theo stock UOM (chai) - không phụ thuộc UOM hiển thị
		const stockUOMBaseRate = item.base_price_list_rate || item.base_rate || 0;

		console.log("calc_uom: stock UOM base rate calculation", {
			item_code: item.item_code,
			base_price_list_rate: item.base_price_list_rate,
			base_rate: item.base_rate,
			stockUOMBaseRate: stockUOMBaseRate,
			conversion_factor: item.conversion_factor
		});

		// Đảm bảo base rates được set đúng theo stock UOM
		if (!item.base_price_list_rate || item.base_price_list_rate === 0) {
			item.base_price_list_rate = stockUOMBaseRate;
		}
		if (!item.base_rate || item.base_rate === 0) {
			item.base_rate = stockUOMBaseRate;
		}

		// Display rates = base_rate × conversion_factor (để hiển thị cho user)
		const displayRate = stockUOMBaseRate * item.conversion_factor;
		const displayPriceListRate = item.base_price_list_rate * item.conversion_factor;

		console.log("calc_uom: calculated display rates", {
			item_code: item.item_code,
			stockUOMBaseRate: stockUOMBaseRate,
			conversion_factor: item.conversion_factor,
			displayRate: displayRate,
			displayPriceListRate: displayPriceListRate
		});

		if (this.selected_currency !== baseCurrency) {
			console.log("calc_uom: converting regular item to selected currency", {
				item_code: item.item_code,
				base_rate: item.base_rate,
				display_rate_before_convert: displayRate,
				exchange_rate: this.exchange_rate
			});
			item.rate = this.flt(displayRate * this.exchange_rate, this.currency_precision);
			item.price_list_rate = this.flt(displayPriceListRate * this.exchange_rate, this.currency_precision);
		} else {
			console.log("calc_uom: using base currency for regular item", {
				item_code: item.item_code,
				display_rate: displayRate,
				base_rate: item.base_rate
			});
			item.rate = displayRate;
			item.price_list_rate = displayPriceListRate;
		}

		console.log("calc_uom: final rates for regular item", {
			Item_code: item.item_code,
			Price: item.rate,
			Uom: item.uom,
			base_rate: item.base_rate,
			display_rate: item.rate,
			conversion_factor: item.conversion_factor
		});
	},

	// Update UOM (unit of measure) for an item and recalculate prices
	async calc_uom(item, value) {
		console.log("calc_uom called", {
			item_code: item.item_code,
			current_uom: item.uom,
			new_uom_value: value,
			stock_uom: item.stock_uom,
			has_offer: item.posa_offer_applied,
			price_list: this.get_price_list()
		});

		const baseCurrency = this.price_list_currency || this.pos_profile.currency;

		// Find the UOM
		const new_uom = this.find_uom(item, value);
		if (!new_uom) return;

		// Store old conversion factor for ratio calculation
		const old_conversion_factor = item.conversion_factor || 1;
		item.conversion_factor = new_uom.conversion_factor;
		const conversion_ratio = item.conversion_factor / old_conversion_factor;

		// Try to find UOM-specific price
		const uomRate = await this.find_uom_price(item, new_uom);

		if (uomRate) {
			// Apply UOM-specific pricing
			this.apply_uom_pricing(item, uomRate, baseCurrency);
			return;
		}

		console.log("calc_uom: no UOM-specific price found, using conversion factor logic", {
			item_code: item.item_code,
			uom: new_uom.uom,
			conversion_factor: new_uom.conversion_factor,
			has_offer: item.posa_offer_applied
		});

		// Reset discount if not offer
		if (!item.posa_offer_applied) {
			item.discount_amount = 0;
			item.discount_percentage = 0;
		}

		// Store original base rates if not already stored
		if (!item.original_base_rate && !item.posa_offer_applied) {
			item.original_base_rate = item.base_rate / old_conversion_factor;
			item.original_base_price_list_rate = item.base_price_list_rate / old_conversion_factor;
		}

		// Process based on item type
		if (item.posa_offer_applied) {
			this.process_offer_item_uom(item, new_uom, old_conversion_factor, conversion_ratio, baseCurrency);
		} else {
			this.process_regular_item_uom(item, old_conversion_factor, baseCurrency);
		}

		// Update item details
		this.calc_stock_qty(item, item.qty);
		this.$forceUpdate();

		// Trigger discount calculation after UOM changes (if not already applying)
		console.log(`[UOM_CHANGE] 🎯 UOM changed for item ${item.item_code}: ${item.uom} - triggering discount calculation`);
		if (!this.isApplyingDiscount) {
			this.$nextTick(() => {
				setTimeout(() => {
					console.log(`[UOM_CHANGE] 📊 Calling calculateDiscountsDebounced() after UOM change for ${item.item_code}`);
					this.calculateDiscountsDebounced();
				}, 10);
			});
		} else {
			console.log(`[UOM_CHANGE] ⚠️ Skipping discount calculation - isApplyingDiscount is true`);
		}

		console.log("calc_uom: completed conversion factor logic", {
			Item_code: item.item_code,
			Price: item.rate,
			Uom: item.uom,
			display_qty: item.qty,
			stock_qty: item.stock_qty,
			conversion_factor: item.conversion_factor,
			stock_uom: item.stock_uom,
			final_rate: item.rate,
			final_price_list_rate: item.price_list_rate
		});
	},

	// Calculate stock quantity for an item
	calc_stock_qty(item, value) {
		item.stock_qty = item.conversion_factor * value;
	},

	// Set serial numbers for an item (and update qty)
	set_serial_no(item) {
		console.log(item);
		if (!item.has_serial_no) return;
		item.serial_no = "";
		item.serial_no_selected.forEach((element) => {
			item.serial_no += element + "\n";
		});
		item.serial_no_selected_count = item.serial_no_selected.length;
		if (item.serial_no_selected_count != item.stock_qty) {
			item.qty = item.serial_no_selected_count;
			this.calc_stock_qty(item, item.qty);
			this.$forceUpdate();
		}
	},

	// Set batch number for an item (and update batch data)
	set_batch_qty(item, value, update = true) {
		console.log("Setting batch quantity:", item, value);
		const baseCurrency = this.price_list_currency || this.pos_profile.currency;
		const existing_items = this.items.filter(
			(element) => element.item_code == item.item_code && element.posa_row_id != item.posa_row_id,
		);
		const used_batches = {};
		item.batch_no_data.forEach((batch) => {
			used_batches[batch.batch_no] = {
				...batch,
				used_qty: 0,
				remaining_qty: batch.batch_qty,
			};
			existing_items.forEach((element) => {
				if (element.batch_no && element.batch_no == batch.batch_no) {
					used_batches[batch.batch_no].used_qty += element.qty;
					used_batches[batch.batch_no].remaining_qty -= element.qty;
					used_batches[batch.batch_no].batch_qty -= element.qty;
				}
			});
		});

		const batch_no_data = Object.values(used_batches)
			.filter((batch) => batch.remaining_qty > 0)
			.sort((a, b) => {
				if (a.expiry_date && b.expiry_date) {
					return new Date(a.expiry_date) - new Date(b.expiry_date);
				} else if (a.expiry_date) {
					return -1;
				} else if (b.expiry_date) {
					return 1;
				} else if (a.manufacturing_date && b.manufacturing_date) {
					return new Date(a.manufacturing_date) - new Date(b.manufacturing_date);
				} else if (a.manufacturing_date) {
					return -1;
				} else if (b.manufacturing_date) {
					return 1;
				} else {
					return b.remaining_qty - a.remaining_qty;
				}
			});

		if (batch_no_data.length > 0) {
			let batch_to_use = null;
			if (value) {
				batch_to_use = batch_no_data.find((batch) => batch.batch_no == value);
			}
			if (!batch_to_use) {
				batch_to_use = batch_no_data[0];
			}

			item.batch_no = batch_to_use.batch_no;
			item.actual_batch_qty = batch_to_use.batch_qty;
			item.batch_no_expiry_date = batch_to_use.expiry_date;

			if (batch_to_use.batch_price) {
				// Store batch price in base currency
				item.base_batch_price = batch_to_use.batch_price;

				// Convert batch price to selected currency if needed
				if (this.selected_currency !== baseCurrency) {
					// Convert base batch price using the current exchange rate
					item.batch_price = this.flt(
						batch_to_use.batch_price * this.exchange_rate,
						this.currency_precision,
					);
				} else {
					item.batch_price = batch_to_use.batch_price;
				}

				// Set rates based on batch price
				item.base_price_list_rate = item.base_batch_price;
				item.base_rate = item.base_batch_price;

				if (this.selected_currency !== baseCurrency) {
					item.price_list_rate = item.batch_price;
					item.rate = item.batch_price;
				} else {
					item.price_list_rate = item.base_batch_price;
					item.rate = item.base_batch_price;
				}

				// Reset discounts since we're using batch price
				item.discount_percentage = 0;
				item.discount_amount = 0;
				item.base_discount_amount = 0;

				// Calculate final amounts
				item.amount = this.flt(item.qty * item.rate, this.currency_precision);
				item.base_amount = this.flt(item.qty * item.base_rate, this.currency_precision);

				console.log("Updated batch prices:", {
					base_batch_price: item.base_batch_price,
					batch_price: item.batch_price,
					rate: item.rate,
					base_rate: item.base_rate,
					price_list_rate: item.price_list_rate,
					exchange_rate: this.exchange_rate,
				});
			} else if (update) {
				item.batch_price = null;
				item.base_batch_price = null;
				this.update_item_detail(item);
			}
		} else {
			item.batch_no = null;
			item.actual_batch_qty = null;
			item.batch_no_expiry_date = null;
			item.batch_price = null;
			item.base_batch_price = null;
		}

		// Update batch_no_data
		item.batch_no_data = batch_no_data;

		// Force UI update
		this.$forceUpdate();

		// Trigger discount calculation after batch changes (if not already applying)
		if (!this.isApplyingDiscount) {
			this.$nextTick(() => {
				setTimeout(() => {
					this.calculateDiscountsDebounced();
				}, 10);
			});
		}
	},

	// change_price_list_rate(item) {
	// 	const vm = this;

	// 	const d = new frappe.ui.Dialog({
	// 		title: __("Change Price"),
	// 		fields: [
	// 			{
	// 				fieldname: "new_rate",
	// 				fieldtype: "Float",
	// 				label: __("New Price List Rate"),
	// 				default: item.price_list_rate || item.rate,
	// 				reqd: 1,
	// 			},
	// 		],
	// 		primary_action_label: __("Update"),
	// 		primary_action(values) {
	// 			const rate = flt(values.new_rate);
	// 			frappe.call({
	// 				method: "posawesome.posawesome.api.items.update_price_list_rate",
	// 				args: {
	// 					item_code: item.item_code,
	// 					price_list: vm.get_price_list(),
	// 					rate: rate,
	// 					uom: item.uom,
	// 				},
	// 				callback(r) {
	// 					if (!r.exc) {
	// 						item.price_list_rate = rate;
	// 						item.base_price_list_rate = rate;
	// 						if (!item._manual_rate_set) {
	// 							item.rate = rate;
	// 							item.base_rate = rate;
	// 						}
	// 						vm.calc_item_price(item);
	// 						vm.eventBus.emit("show_message", {
	// 							title: r.message || __("Item price updated"),
	// 							color: "success",
	// 						});
	// 					}
	// 				},
	// 			});
	// 			d.hide();
	// 		},
	// 	});

	// 	d.get_field("new_rate").$input.on("keydown", function (e) {
	// 		if (e.key === "Enter") {
	// 			d.get_primary_btn().click();
	// 		}
	// 	});

	// 	d.show();
	// ============================================================================
	// PACK OPTIMIZATION FUNCTIONS - Tự động tối ưu combo pack
	// ============================================================================

	// Lấy danh sách pack có sẵn từ POS Offers (động từ Item Price)
	getAvailablePacks(item_code) {
		const packs = [];

		// Lấy thông tin item để biết stock UOM
		const item = this.items.find(i => i.item_code === item_code) ||
					this.allItems?.find(i => i.item_code === item_code);

		if (!item) {
			console.warn('[PACK_OPTIMIZER] Item not found:', item_code);
			return packs;
		}

		const stockUOM = item.stock_uom;
		const basePrice = item.base_price_list_rate || item.price_list_rate || 0;

		// Pack lẻ (không KM) - luôn có với giá từ Item Price
		packs.push({
			size: 1,
			uom: stockUOM,
			price: basePrice,
			is_offer: false
		});

		// Lấy packs từ POS Offers đang active
		if (this.posa_offers && Array.isArray(this.posa_offers)) {
			this.posa_offers.forEach(offer => {
				if (offer.is_used_block && offer.uom_ref && offer.total_items_in_block_qty) {
					// Kiểm tra offer có áp dụng cho item này không
					if (this.isOfferApplicableToItem(offer, item_code)) {
						// Tính giá pack sau KM
						const originalPrice = this.getPackOriginalPrice(offer.total_items_in_block_qty, item_code);
						const discountAmount = offer.total_discount_amount_per_block || 0;
						const packPrice = Math.max(0, originalPrice - discountAmount); // Đảm bảo không âm

						packs.push({
							size: offer.total_items_in_block_qty,
							uom: offer.uom_ref,
							price: packPrice,
							is_offer: true,
							offer: offer
						});
					}
				}
			});
		}

		// Sắp xếp theo size tăng dần để DP hoạt động đúng
		return packs.sort((a, b) => a.size - b.size);
	},

	// Kiểm tra offer có áp dụng cho item không
	isOfferApplicableToItem(offer, item_code) {
		// Kiểm tra theo item code hoặc item group
		if (offer.item && offer.item === item_code) return true;
		if (offer.item_group) {
			// TODO: Kiểm tra item có thuộc item group không
			return true; // Tạm thời return true
		}
		return false;
	},

	// Tính giá gốc của pack (trước KM)
	getPackOriginalPrice(packSize, item_code) {
		// Lấy thông tin item
		const item = this.items.find(i => i.item_code === item_code) ||
					this.allItems?.find(i => i.item_code === item_code);

		if (!item) {
			console.warn('[PACK_OPTIMIZER] Item not found for price calculation:', item_code);
			return 0;
		}

		// Lấy giá từ Item Price cho stock UOM
		const basePrice = item.base_price_list_rate || item.price_list_rate || 0;
		return basePrice * packSize;
	},

	// Thuật toán DP để tìm combo pack tối ưu (min cost)
	findOptimalPackCombination(totalQty, packs) {
		console.log('[PACK_OPTIMIZER] Finding optimal combo for qty:', totalQty, 'with packs:', packs);

		if (!packs || packs.length === 0) {
			// Nếu không có packs, dùng pack lẻ với giá từ pack đầu tiên (nếu có)
			const unitPrice = packs.length > 0 ? packs[0].price / packs[0].size : 0;
			return {1: totalQty, total: totalQty * unitPrice};
		}

		// Khởi tạo DP array
		const dp = new Array(totalQty + 1).fill(Infinity);
		const choices = new Array(totalQty + 1).fill(null);

		dp[0] = 0;

		// Điền DP table
		for (let qty = 1; qty <= totalQty; qty++) {
			for (const pack of packs) {
				if (qty >= pack.size && dp[qty - pack.size] + pack.price < dp[qty]) {
					dp[qty] = dp[qty - pack.size] + pack.price;
					choices[qty] = {pack: pack, prev: qty - pack.size};
				}
			}
		}

		// Reconstruct optimal combination - sử dụng pack sizes động
		const result = {total: dp[totalQty]};
		let current = totalQty;

		while (current > 0 && choices[current]) {
			const choice = choices[current];
			const packSize = choice.pack.size;

			// Tăng số lượng pack tương ứng
			result[packSize] = (result[packSize] || 0) + 1;

			current = choice.prev;
		}

		// Xử lý phần dư (nếu có) - dùng pack nhỏ nhất
		if (current > 0) {
			const smallestPack = Math.min(...packs.map(p => p.size));
			result[smallestPack] = (result[smallestPack] || 0) + Math.ceil(current / smallestPack);
		}

		console.log('[PACK_OPTIMIZER] Optimal combo found:', result);
		return result;
	},

	// Tách item thành multiple lines theo combo tối ưu
	splitItemIntoOptimalPacks(item, optimalCombo, availablePacks) {
		console.log('[PACK_SPLITTER] Splitting item into optimal packs:', item.item_code, optimalCombo);

		const newItems = [];
		const baseItem = {...item};

		// Tạo line cho từng loại pack trong optimalCombo
		Object.keys(optimalCombo).forEach(packSizeStr => {
			const qty = optimalCombo[packSizeStr];
			if (qty > 0 && packSizeStr !== 'total') {
				const packSize = parseInt(packSizeStr);
				const packItem = {...baseItem};
				packItem.posa_row_id = this.makeid(20);
				packItem.qty = qty;

				// Tìm pack tương ứng để lấy UOM và giá
				const packInfo = availablePacks.find(p => p.size === packSize);
				if (packInfo) {
					packItem.uom = packInfo.uom;
					packItem.rate = packInfo.price / packInfo.size; // Giá per unit
					packItem.price_list_rate = packItem.rate;
					packItem.amount = packItem.qty * packItem.rate;

					// Set conversion factor dựa trên pack size
					packItem.conversion_factor = packInfo.size;

					// Tính stock_qty
					this.calc_stock_qty(packItem, packItem.qty);

					newItems.push(packItem);
					console.log('[PACK_SPLITTER] Created pack line:', packSize, 'qty:', qty, 'rate:', packItem.rate, 'uom:', packItem.uom);
				}
			}
		});

		return newItems;
	},


	// Tích hợp pack optimization vào add_item
	add_item_with_pack_optimization(item) {
		console.log('[PACK_OPTIMIZER] add_item_with_pack_optimization called for:', item.item_code, 'qty:', item.qty);

		// Kiểm tra có cần tối ưu pack không
		const shouldOptimize = this.shouldOptimizePacks(item);
		if (!shouldOptimize) {
			// Dùng logic add_item thông thường
			return this.add_item(item);
		}

		// Lấy danh sách packs có sẵn
		const availablePacks = this.getAvailablePacks(item.item_code);
		console.log('[PACK_OPTIMIZER] Available packs:', availablePacks);

		// Tìm combo tối ưu
		const optimalCombo = this.findOptimalPackCombination(item.qty, availablePacks);

		// Tách thành multiple lines
		const packItems = this.splitItemIntoOptimalPacks(item, optimalCombo, availablePacks);

		// Thêm các lines vào invoice
		packItems.forEach(packItem => {
			this.items.unshift(packItem);
			this.update_item_detail(packItem, true);
		});

		// Force update UI
		this.$forceUpdate();

		// Hiển thị thông báo combo tối ưu
		this.showPackOptimizationMessage(optimalCombo, availablePacks);

		console.log('[PACK_OPTIMIZER] Pack optimization completed for:', item.item_code);
	},

	// Kiểm tra có nên tối ưu pack không
	shouldOptimizePacks(item) {
		// Tối ưu cho tất cả items có POS offers với block discounts
		return this.posa_offers && this.posa_offers.some(offer =>
			offer.is_used_block && offer.uom_ref && offer.total_items_in_block_qty
		);
	},

	// Hiển thị thông báo combo tối ưu
	showPackOptimizationMessage(optimalCombo, availablePacks) {
		const savings = this.calculateSavings(optimalCombo, availablePacks);
		if (savings > 0) {
			this.eventBus.emit("show_message", {
				title: __("Combo tối ưu được áp dụng"),
				text: __(`Tiết kiệm ${formatCurrency(savings)} so với mua lẻ`),
				color: "success",
			});
		}
	},

	// Tính số tiền tiết kiệm
	calculateSavings(optimalCombo, availablePacks) {
		// Tìm pack lẻ để tính giá gốc
		const unitPack = availablePacks.find(p => p.size === 1);
		if (!unitPack) return 0;

		// Tính tổng số lượng từ optimalCombo
		let totalQty = 0;
		Object.keys(optimalCombo).forEach(packSize => {
			if (packSize !== 'total') {
				totalQty += parseInt(packSize) * optimalCombo[packSize];
			}
		});

		const regularPrice = totalQty * (unitPack.price / unitPack.size); // Giá mua lẻ per unit
		const optimizedPrice = optimalCombo.total;
		return Math.max(0, regularPrice - optimizedPrice); // Đảm bảo không âm
	},

	// ============================================================================
	// END PACK OPTIMIZATION FUNCTIONS
	// ============================================================================
};
