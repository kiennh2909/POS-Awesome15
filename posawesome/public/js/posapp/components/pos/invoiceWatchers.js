import { clearPriceListCache } from "../../../offline/index.js";

export default {
	// Watch for customer change and update related data
	customer() {
		console.log("👀 [WATCHER] customer changed", {
			old: this.customer,
			new: this.customer,
			trigger: "customer field modified",
		});

		this.close_payments();
		this.eventBus.emit("set_customer", this.customer);
		this.fetch_customer_details();
		this.fetch_customer_balance();
		this.set_delivery_charges();

		// Trigger discount calculation only if cart has items
		if (this.items.length > 0) {
			this.calculateDiscountsDebounced();
			console.log("👀 [DISCOUNT_TRIGGER] calculateDiscountsDebounced() called from customer watcher");
		} else {
			console.log("👀 [DISCOUNT_TRIGGER] Skipped discount calculation - cart is empty");
		}
	},
	// Watch for customer_info change and emit to edit form
	customer_info() {
		this.eventBus.emit("set_customer_info_to_edit", this.customer_info);
	},
	// Watch for expanded row change and update item detail
	expanded(data_value) {
		if (data_value.length > 0) {
			this.update_item_detail(data_value[0]);
		}
	},
	// Watch for discount offer name change and emit
	discount_percentage_offer_name() {
		this.eventBus.emit("update_discount_percentage_offer_name", {
			value: this.discount_percentage_offer_name,
		});
	},
	// Watch for items array changes (deep) and re-handle offers
	items: {
		deep: true,
		handler(items, oldItems) {
			// Prevent recursive calls when applying offers
			if (this.isApplyingOffer) {
				console.log("items watcher: skipping due to isApplyingOffer = true");
				return;
			}

			// Check if items array structure changed or qty changed
			const structureChanged = items.length !== (oldItems?.length || 0);
			let qtyChanged = false;

			// Check if quantity changed for same items
			if (!structureChanged && oldItems && items.length === oldItems.length) {
				for (let i = 0; i < items.length; i++) {
					const newItem = items[i];
					const oldItem = oldItems[i];

					console.log("items watcher: comparing items", {
						index: i,
						newItem_row_id: newItem.posa_row_id,
						oldItem_row_id: oldItem?.posa_row_id,
						new_qty: newItem.qty,
						old_qty: oldItem?.qty,
						row_ids_match: newItem.posa_row_id === oldItem?.posa_row_id,
						qty_match: newItem.qty === oldItem?.qty,
					});

					// Compare by posa_row_id to ensure same item
					if (newItem.posa_row_id === oldItem?.posa_row_id) {
						if (newItem.qty !== oldItem.qty) {
							qtyChanged = true;
							console.log("items watcher: qty changed detected", {
								item_code: newItem.item_code,
								old_qty: oldItem.qty,
								new_qty: newItem.qty,
							});
							break;
						}
					}
				}
			}

			// Special case: First item added to empty cart
			const isFirstItemAdded = items.length === 1 && (!oldItems || oldItems.length === 0);

			console.log("items watcher: checking for discount trigger", {
				structureChanged,
				qtyChanged,
				isFirstItemAdded,
				itemsCount: items.length,
				oldItemsCount: oldItems?.length || 0,
				willTriggerDiscount: structureChanged || qtyChanged || isFirstItemAdded,
			});

			if (structureChanged || qtyChanged || isFirstItemAdded) {
				// Debounce the call to the new API only if cart has items
				if (this.calculateDiscountsDebounced && this.items.length > 0) {
					console.log("items watcher: triggering calculateDiscountsDebounced");
					this.calculateDiscountsDebounced();
				} else if (this.items.length === 0) {
					console.log("items watcher: skipped calculateDiscountsDebounced - cart is empty");
				} else {
					console.log("items watcher: calculateDiscountsDebounced not available");
				}
			}
			this.$forceUpdate();
		},
	},
	// Watch for invoice type change and emit
	invoiceType() {
		this.eventBus.emit("update_invoice_type", this.invoiceType);
	},
	// Watch for additional discount and update percentage accordingly
	additional_discount() {
		if (!this.additional_discount || this.additional_discount == 0) {
			this.additional_discount_percentage = 0;
		} else if (this.pos_profile.posa_use_percentage_discount) {
			// Prevent division by zero which causes NaN
			if (this.Total && this.Total !== 0) {
				this.additional_discount_percentage = (this.additional_discount / this.Total) * 100;
			} else {
				this.additional_discount_percentage = 0;
			}
		} else {
			this.additional_discount_percentage = 0;
		}
	},
	// Keep display date in sync with posting_date
	posting_date: {
		handler(newVal) {
			this.posting_date_display = this.formatDateForDisplay(newVal);
		},
		immediate: true,
	},
	// Update posting_date when user changes the display value
	posting_date_display(newVal) {
		this.posting_date = this.formatDateForBackend(newVal);
	},

	selected_price_list(newVal) {
		// Clear cached price list items to avoid mixing rates
		clearPriceListCache();

		const price_list = newVal === this.pos_profile.selling_price_list ? null : newVal;
		this.eventBus.emit("update_customer_price_list", price_list);
		const applied = newVal || this.pos_profile.selling_price_list;
		this.apply_cached_price_list(applied);

		// If multi-currency is enabled, sync currency with the price list currency
		if (this.pos_profile.posa_allow_multi_currency && applied) {
			frappe.call({
				method: "posawesome.posawesome.api.invoices.get_price_list_currency",
				args: { price_list: applied },
				callback: (r) => {
					if (r.message) {
						// Store price list currency for later use
						this.price_list_currency = r.message;
						// Sync invoice currency with price list currency
						this.update_currency(r.message);
					}
				},
			});
		}
	},

	// Reactively update item prices when currency changes
	selected_currency() {
		clearPriceListCache();
		if (this.items && this.items.length) {
			this.update_item_rates();
		}
	},

	// Reactively update item prices when exchange rate changes
	exchange_rate() {
		if (this.items && this.items.length) {
			this.update_item_rates();
		}
	},
};
