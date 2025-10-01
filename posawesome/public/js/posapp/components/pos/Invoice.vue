<template>
	<!-- Main Invoice Wrapper -->
	<div class="pa-0">
		<!-- Cancel Sale Confirmation Dialog -->
		<CancelSaleDialog v-model="cancel_dialog" @confirm="cancel_invoice" />

		<!-- Main Invoice Card (contains all invoice content) -->
		 
		<v-card
			ref="invoiceCard"
			:style="{
				height: '55vh' || 'var(--container-height)',
				maxHeight: invoiceHeight || 'var(--container-height)',
				backgroundColor: isDarkTheme ? '#121212' : '',
				resize: 'vertical',
				overflow: 'auto',
			}"
			:class="[
				'cards my-0 py-0 mt-3 resizable',
				isDarkTheme ? '' : 'bg-grey-lighten-5',
				{ 'return-mode': isReturnInvoice },
			]"
			@mouseup="saveInvoiceHeight"
			@touchend="saveInvoiceHeight"
		>
			<!-- Dynamic padding wrapper -->
			<div class="dynamic-padding">
				<!-- Top Row: Customer Selection, Invoice Type, and Columns Button -->
				<v-row align="center" class="items px-3 py-2">
					<v-col :cols="pos_profile.posa_allow_sales_order ? 7 : 9" class="pb-0 pr-0">
						<!-- Customer selection component with Quick View props -->
						<Customer
							:pos_profile="pos_profile"
							:posting_date_display="posting_date_display"
							:customer_balance="customer_balance"
							:selected_price_list="selected_price_list"
							:price_lists="price_lists"
							:formatCurrency="formatCurrency"
							@update:posting_date_display="onPostingDateUpdate"
							@update:priceList="onPriceListUpdate"
						/>
					</v-col>
					<!-- Invoice Type Selection (Only shown if sales orders are allowed) -->
					<v-col v-if="pos_profile.posa_allow_sales_order" cols="2" class="pb-4">
						<v-select
							density="compact"
							hide-details
							variant="solo"
							color="primary"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field compact-select"
							:items="invoiceTypes"
							:label="frappe._('Type')"
							v-model="invoiceType"
							:disabled="invoiceType == 'Return'"
						></v-select>
					</v-col>
					<!-- Columns Button -->
					<v-col :cols="pos_profile.posa_allow_sales_order ? 3 : 3" class="pb-4 d-flex justify-end">
						<v-btn
							density="compact"
							variant="text"
							color="primary"
							prepend-icon="mdi-cog-outline"
							@click="toggleColumnSelection"
							class="column-selector-btn compact-btn"
						>
							{{ __("Columns") }}
						</v-btn>

						<v-dialog v-model="show_column_selector" max-width="500px">
							<v-card>
								<v-card-title class="text-h6 pa-4 d-flex align-center">
									<span>{{ __("Select Columns to Display") }}</span>
									<v-spacer></v-spacer>
									<v-btn
										icon="mdi-close"
										variant="text"
										density="compact"
										@click="show_column_selector = false"
									></v-btn>
								</v-card-title>
								<v-divider></v-divider>
								<v-card-text class="pa-4">
									<v-row dense>
										<v-col
											cols="12"
											v-for="column in available_columns.filter((col) => !col.required)"
											:key="column.key"
										>
											<v-switch
												v-model="temp_selected_columns"
												:label="column.title"
												:value="column.key"
												hide-details
												density="compact"
												color="primary"
												class="column-switch mb-1"
												:disabled="column.required"
											></v-switch>
										</v-col>
									</v-row>
									<div class="text-caption mt-2">
										{{ __("Required columns cannot be hidden") }}
									</div>
								</v-card-text>
								<v-card-actions class="pa-4 pt-0">
									<v-btn color="error" variant="text" @click="cancelColumnSelection">{{
										__("Cancel")
									}}</v-btn>
									<v-spacer></v-spacer>
									<v-btn color="primary" variant="tonal" @click="updateSelectedColumns">{{
										__("Apply")
									}}</v-btn>
								</v-card-actions>
							</v-card>
						</v-dialog>
					</v-col>
				</v-row>

				<!-- REMOVED: CustomerInfo and PostingDateRow - now in Quick View within Customer component -->

				<!-- Delivery Charges Section (Only if enabled in POS profile) -->
				<!-- <DeliveryCharges
					:pos_profile="pos_profile"
					:delivery_charges="delivery_charges"
					:selected_delivery_charge="selected_delivery_charge"
					:delivery_charges_rate="delivery_charges_rate"
					:deliveryChargesFilter="deliveryChargesFilter"
					:formatCurrency="formatCurrency"
					:currencySymbol="currencySymbol"
					:readonly="readonly"
					@update:selected_delivery_charge="
						(val) => {
							selected_delivery_charge = val;
							update_delivery_charges();
						}
					"
				/> -->

				<!-- Multi-Currency Section (Only if enabled in POS profile) -->
				<MultiCurrencyRow
					:pos_profile="pos_profile"
					:selected_currency="selected_currency"
					:plc_conversion_rate="exchange_rate"
					:conversion_rate="conversion_rate"
					:available_currencies="available_currencies"
					:isNumber="isNumber"
					:price_list_currency="price_list_currency"
					@update:selected_currency="
						(val) => {
							selected_currency = val;
							update_currency(val);
						}
					"
					@update:plc_conversion_rate="
						(val) => {
							exchange_rate = val;
							update_exchange_rate();
						}
					"
					@update:conversion_rate="
						(val) => {
							conversion_rate = val;
							update_conversion_rate();
						}
					"
				/>

				<!-- Items Table Section (Main items list for invoice) -->
				<div class="items-table-wrapper">
					<!-- ItemsTable component with reorder event handler -->
					<ItemsTable
						ref="itemsTable"
						:headers="items_headers"
						:items="items"
						:expanded="expanded"
						:itemsPerPage="itemsPerPage"
						:itemSearch="itemSearch"
						:pos_profile="pos_profile"
						:invoice_doc="invoice_doc"
						:invoiceType="invoiceType"
						:displayCurrency="displayCurrency"
						:formatFloat="formatFloat"
						:formatCurrency="formatCurrency"
						:currencySymbol="currencySymbol"
						:isNumber="isNumber"
						:setFormatedQty="setFormatedQty"
						:calcStockQty="calc_stock_qty"
						:setFormatedCurrency="setFormatedCurrency"
						:calcPrices="calc_prices"
						:calcUom="calc_uom"
						:setSerialNo="set_serial_no"
						:setBatchQty="set_batch_qty"
						:validateDueDate="validate_due_date"
						:removeItem="remove_item"
						:subtractOne="subtract_one"
						:addOne="add_one"
						:toggleOffer="toggleOffer"
						@update:expanded="expanded = $event"
						@reorder-items="handleItemReorder"
						@add-item-from-drag="handleItemDrop"
						@show-drop-feedback="showDropFeedback"
						@item-dropped="showDropFeedback(false)"
					/>
				</div>
			</div>
		</v-card>
		<!-- Payment Section -->
		<InvoiceSummary
			:pos_profile="pos_profile"
			:total_qty="total_qty"
			:additional_discount="additional_discount"
			:additional_discount_percentage="additional_discount_percentage"
			:total_items_discount_amount="total_items_discount_amount"
			:subtotal="subtotal"
			:displayCurrency="displayCurrency"
			:formatFloat="formatFloat"
			:formatCurrency="formatCurrency"
			:currencySymbol="currencySymbol"
			:discount_percentage_offer_name="discount_percentage_offer_name"
			:isNumber="isNumber"
			:shiftVerificationStatus="shiftVerificationStatus"
			@update:additional_discount="(val) => (additional_discount = val)"
			@update:additional_discount_percentage="(val) => (additional_discount_percentage = val)"
			@update_discount_umount="update_discount_umount"
			@save-and-clear="save_and_clear_invoice"
			@load-drafts="get_draft_invoices"
			@select-order="get_draft_orders"
			@cancel-sale="cancel_dialog = true"
			@open-returns="open_returns"
			@print-draft="print_draft_invoice"
			@show-payment="show_payment"
			@list-invoices="handleListInvoices"
			@list-shifts="handleListShifts"
		>
			<!-- Add Print and Tax Print Buttons here -->
			<template #actions>
				<v-btn
					color="success"
					@click="submit_invoice"
					:disabled="!can_print"
				>
					<v-icon left>mdi-printer</v-icon>
					{{ __("Submit") }}
				</v-btn>

				<!-- Tax Print Button -->
				<v-btn
					v-if="show_tax_print_button"
					color="primary"
					@click="print_tax_invoice"
					:disabled="!can_print || tax_print_loading"
					:loading="tax_print_loading"
					class="ml-2"
				>
					<v-icon left>mdi-receipt</v-icon>
					{{ __("In Thuế") }}
				</v-btn>
			</template>
		</InvoiceSummary>
	</div>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";
import Customer from "./Customer.vue";
import DeliveryCharges from "./DeliveryCharges.vue";
import MultiCurrencyRow from "./MultiCurrencyRow.vue";
import CancelSaleDialog from "./CancelSaleDialog.vue";
import InvoiceSummary from "./InvoiceSummary.vue";
import ItemsTable from "./ItemsTable.vue";
import invoiceComputed from "./invoiceComputed";
import invoiceWatchers from "./invoiceWatchers";
import itemAddition from "./invoice-item/itemAddition";
import batchSerial from "./invoice-item/batchSerial";
import discountMethods from "./invoice-item/discounts";
import stockUtils from "./invoice-item/stockUtils";
import offerMethods from "./invoiceOfferMethods";
import shortcutMethods from "./invoiceShortcuts";
import invoiceItemMethods from "./invoiceItemMethods";
import { isOffline, saveCustomerBalance, getCachedCustomerBalance } from "../../../offline";
import { updateHeaderTaxDisplay } from "./taxPrintHandler";

export default {
	name: "POSInvoice",
	mixins: [format],
	data() {
		return {
			// POS profile settings
			pos_profile: "",
			pos_opening_shift: "",
			stock_settings: "",
			invoice_doc: "",
			return_doc: "",
			customer: "",
			customer_info: "",
			customer_balance: 0,
			discount_amount: 0,
			additional_discount: 0,
			additional_discount_percentage: 0,
			total_tax: 0,
			items: [], // List of invoice items
			posOffers: [], // All available offers
			posa_offers: [], // Offers applied to this invoice
			posa_coupons: [], // Coupons applied
			allItems: [], // All items for offer logic
			discount_percentage_offer_name: null, // Track which offer is applied
			isApplyingDiscount: false, // Flag to prevent discount calculation loops
			invoiceTypes: ["Invoice", "Order"], // Types of invoices
			invoiceType: "Invoice", // Current invoice type
			itemsPerPage: 1000, // Items per page in table
			expanded: [], // Array of expanded row IDs
			singleExpand: true, // Only one row expanded at a time
			cancel_dialog: false, // Cancel dialog visibility
			float_precision: 6, // Float precision for calculations
			currency_precision: 6, // Currency precision for display
			new_line: false, // Add new line for item
			delivery_charges: [], // List of delivery charges
			delivery_charges_rate: 0, // Selected delivery charge rate
			selected_delivery_charge: "", // Selected delivery charge object
			invoice_posting_date: false, // Posting date dialog
			posting_date: frappe.datetime.nowdate(), // Invoice posting date
			posting_date_display: "", // Display value for date picker
			items_headers: [],
			selected_currency: "", // Currently selected currency
			exchange_rate: 1, // Current exchange rate
			conversion_rate: 1, // Currency to company rate
			exchange_rate_date: "", // Date of fetched exchange rate
			company: null, // Company doc with default currency
			available_currencies: [], // List of available currencies
			price_lists: [], // Available selling price lists
			selected_price_list: "", // Currently selected price list
			price_list_currency: "", // Currency of the selected price list
			selected_columns: [], // Selected columns for items table
			temp_selected_columns: [], // Temporary array for column selection
			available_columns: [], // All available columns
			show_column_selector: false, // Column selector dialog visibility
			invoiceHeight: null,
			tax_print_loading: false, // Loading state for tax print button
			shiftVerificationStatus: null, // Verification status of current shift report
			isApplyingOffer: false, // Flag to prevent recursive offer application
		};
	},

	components: {
		Customer,
		DeliveryCharges,
		MultiCurrencyRow,
		InvoiceSummary,
		CancelSaleDialog,
		ItemsTable,
	},
	computed: {
		...invoiceComputed,
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
		// Show tax print button if POS profile allows and invoice is not a return
		show_tax_print_button() {
			return (
				this.pos_profile &&
				this.pos_profile.posa_enable_tax_print &&
				!this.isReturnInvoice
			);
		},
		// Check if the invoice can be printed (e.g., has items, is not a return unless specifically allowed)
		can_print() {
			return (
				this.items &&
				this.items.length > 0 &&
				(this.invoiceType !== "Return" || this.pos_profile.posa_allow_return_printing)
			);
		},
	},

	methods: {
		// Debounce function - simple implementation
		debounce(func, delay) {
			let timeout;
			return function (...args) {
				const context = this;
				clearTimeout(timeout);
				timeout = setTimeout(() => func.apply(context, args), delay);
				console.log(`⏱️ [DEBOUNCE] Function debounced for ${delay}ms`);
			};
		},

		async calculateDiscountsAPI() {
			console.log("💰 [DISCOUNT_CALC] Starting discount calculation", {
				items_count: this.items.length,
				customer: this.customer,
				coupons_count: this.posa_coupons?.length || 0,
				pos_profile: this.pos_profile?.name
			});

			if (!this.items.length) {
				// Clear offers if cart is empty
				this.posa_offers = [];
				console.log("💰 [DISCOUNT_CALC] Cart is empty, cleared offers");
				return;
			}

			// Prevent recursive discount calculations
			if (this.isApplyingDiscount) {
				console.log("💰 [DISCOUNT_CALC] Skipping recursive discount calculation");
				return;
			}

			// Set flag to prevent recursive watcher calls
			this.isApplyingDiscount = true;
			this.isApplyingOffer = true;
			console.log("💰 [DISCOUNT_CALC] isApplyingDiscount and isApplyingOffer flags set to true");

			this.eventBus.emit("show_loading", true);
			console.log("💰 [DISCOUNT_CALC] Loading indicator shown");

			try {
				const invoice_data = {
					items: this.items,
					customer: this.customer,
					pos_profile: this.pos_profile.name,
					coupons: this.posa_coupons,
				};
				console.log("💰 [DISCOUNT_CALC] Prepared invoice data for API", {
					items_count: invoice_data.items.length,
					customer: invoice_data.customer,
					pos_profile: invoice_data.pos_profile,
					coupons_count: invoice_data.coupons?.length || 0
				});

				const response = await frappe.call({
					method: "posawesome.posawesome.api.discount_calculator.calculate_discounts",
					args: {
						invoice_data: JSON.stringify(invoice_data),
					},
				});
				console.log("💰 [DISCOUNT_CALC] API response received", {
					status: response.message?.status,
					has_updated_items: !!response.message?.updated_items,
					applied_offers_count: response.message?.applied_offers?.length || 0
				});

				if (response.message && response.message.status === "success") {
					// Directly replace items with the processed list from backend
					console.log("💰 [DISCOUNT_CALC] API success, updating items and offers");
					this.items = response.message.updated_items;
					this.posa_offers = response.message.applied_offers;
					console.log("💰 [DISCOUNT_CALC] Items and offers updated successfully", {
						items_count: this.items.length,
						offers_count: this.posa_offers.length
					});
				} else {
					console.log("💰 [DISCOUNT_CALC] API returned error status, falling back to client-side");
					this.eventBus.emit("show_message", {
						title: __("Error Calculating Discounts"),
						color: "error",
						message: response.message.message || "Unknown error",
					});
					// Fallback to client-side calculation if API fails
					this.handelOffers();
				}
			} catch (error) {
				console.error("💰 [DISCOUNT_CALC] API call failed:", error);
				this.eventBus.emit("show_message", {
					title: __("API Call Failed"),
					color: "error",
					message: "Could not connect to the server for discount calculation.",
				});
				// Fallback to client-side calculation if API fails
				console.log("💰 [DISCOUNT_CALC] Falling back to client-side calculation");
				this.handelOffers();
			} finally {
				this.eventBus.emit("show_loading", false);
				// Reset flags after operation completes
				this.isApplyingDiscount = false;
				this.isApplyingOffer = false;
				console.log("💰 [DISCOUNT_CALC] Loading indicator hidden, flags reset to false");
			}
		},
		...shortcutMethods,
		...itemAddition,
		...batchSerial,
		...discountMethods,
		...stockUtils,
		...offerMethods,
		...invoiceItemMethods,
		initializeItemsHeaders() {
			// Define all available columns
			this.available_columns = [
				{ title: __("Name"), align: "start", sortable: true, key: "item_name", required: true },
				{ title: __("QTY"), key: "qty", align: "start", required: true },
				{ title: __("UOM"), key: "uom", align: "start", required: false },
				{ title: __("Rate"), key: "rate", align: "start", required: true },
				{ title: __("Discount %"), key: "discount_value", align: "start", required: false },
				{ title: __("Discount Amount"), key: "discount_amount", align: "start", required: false },
				{ title: __("Amount"), key: "amount", align: "start", required: true },
				{ title: __("Offer?"), key: "posa_is_offer", align: "center", required: false },
			];

			// Initialize selected columns if empty
			if (!this.selected_columns || this.selected_columns.length === 0) {
				// By default, select all required columns and those enabled in POS profile
				this.selected_columns = this.available_columns
					.filter((col) => {
						if (col.required) return true;
						if (col.key === "discount_value" && this.pos_profile.posa_display_discount_percentage)
							return true;
						if (col.key === "discount_amount" && this.pos_profile.posa_display_discount_amount)
							return true;
						return false;
					})
					.map((col) => col.key);
			}

			// Generate headers based on selected columns
			this.updateHeadersFromSelection();
		},
		// Handle item dropped from ItemsSelector to ItemsTable
		handleItemDrop(item) {
			console.log("Item dropped:", item);

			// Use the existing add_item method to add the dropped item
			this.add_item(item);

			// Show success feedback
			this.eventBus.emit("show_message", {
				title: __(`Item {0} added to invoice`, [item.item_name]),
				color: "success",
			});
		},

		// Show visual feedback when item is being dragged over drop zone
		showDropFeedback(isDragging) {
			// Add visual feedback class to the items table
			const itemsTable = this.$el.querySelector(".modern-items-table");
			if (itemsTable) {
				if (isDragging) {
					itemsTable.classList.add("drag-over");
				} else {
					itemsTable.classList.remove("drag-over");
				}
			}
		},
		toggleColumnSelection() {
			// Create a copy of selected columns for temporary editing
			this.temp_selected_columns = [...this.selected_columns];
			this.show_column_selector = true;
		},

		cancelColumnSelection() {
			// Discard changes
			this.show_column_selector = false;
		},

		updateHeadersFromSelection() {
			// Generate headers based on selected columns (without closing dialog)
			this.items_headers = this.available_columns.filter(
				(col) => this.selected_columns.includes(col.key) || col.required,
			);
		},

		updateSelectedColumns() {
			// Apply the temporary selection
			this.selected_columns = [...this.temp_selected_columns];

			// Add required columns if they're not already included
			const requiredKeys = this.available_columns.filter((col) => col.required).map((col) => col.key);

			requiredKeys.forEach((key) => {
				if (!this.selected_columns.includes(key)) {
					this.selected_columns.push(key);
				}
			});

			// Update headers
			this.updateHeadersFromSelection();

			// Save preferences
			this.saveColumnPreferences();

			// Close dialog
			this.show_column_selector = false;
		},

		saveColumnPreferences() {
			try {
				localStorage.setItem("posawesome_selected_columns", JSON.stringify(this.selected_columns));
			} catch (e) {
				console.error("Failed to save column preferences:", e);
			}
		},

		loadColumnPreferences() {
			try {
				const saved = localStorage.getItem("posawesome_selected_columns");
				if (saved) {
					this.selected_columns = JSON.parse(saved);
				}
			} catch (e) {
				console.error("Failed to load column preferences:", e);
			}
		},

		saveInvoiceHeight() {
			if (this.$refs.invoiceCard) {
				this.invoiceHeight = this.$refs.invoiceCard.clientHeight + "px";
				try {
					localStorage.setItem("posawesome_invoice_height", this.invoiceHeight);
				} catch (e) {
					console.error("Failed to save invoice height:", e);
				}
			}
		},

		loadInvoiceHeight() {
			try {
				const saved = localStorage.getItem("posawesome_invoice_height");
				if (saved) {
					this.invoiceHeight = saved;
				} else {
					this.invoiceHeight =
						getComputedStyle(document.documentElement).getPropertyValue("--container-height") ||
						"68vh";
				}
			} catch (e) {
				console.error("Failed to load invoice height:", e);
				this.invoiceHeight =
					getComputedStyle(document.documentElement).getPropertyValue("--container-height") ||
					"68vh";
			}
		},
		makeid(length) {
			let result = "";
			const characters = "abcdefghijklmnopqrstuvwxyz0123456789";
			const charactersLength = characters.length;
			for (var i = 0; i < length; i++) {
				result += characters.charAt(Math.floor(Math.random() * charactersLength));
			}
			return result;
		},

		print_draft_invoice() {
			if (!this.pos_profile.posa_allow_print_draft_invoices) {
				this.eventBus.emit("show_message", {
					title: __(`You are not allowed to print draft invoices`),
					color: "error",
				});
				return;
			}
			let invoice_name = this.invoice_doc.name;
			frappe.run_serially([
				() => {
					const invoice_doc = this.save_and_clear_invoice();
					invoice_name = invoice_doc.name ? invoice_doc.name : invoice_name;
				},
				() => {
					this.load_print_page(invoice_name);
				},
			]);
		},
		async set_delivery_charges() {
			var vm = this;
			if (!this.pos_profile || !this.customer || !this.pos_profile.posa_use_delivery_charges) {
				this.delivery_charges = [];
				this.delivery_charges_rate = 0;
				this.selected_delivery_charge = "";
				return;
			}
			this.delivery_charges_rate = 0;
			this.selected_delivery_charge = "";
			try {
				const r = await frappe.call({
					method: "posawesome.posawesome.api.offers.get_applicable_delivery_charges",
					args: {
						company: this.pos_profile.company,
						pos_profile: this.pos_profile.name,
						customer: this.customer,
					},
				});
				if (r.message && r.message.length) {
					console.log(r.message);
					vm.delivery_charges = r.message;
				}
			} catch (error) {
				console.error("Failed to fetch delivery charges", error);
			}
		},
		deliveryChargesFilter(itemText, queryText, itemRow) {
			const item = itemRow.raw;
			console.log("dl charges", item);
			const textOne = item.name.toLowerCase();
			const searchText = queryText.toLowerCase();
			return textOne.indexOf(searchText) > -1;
		},
		update_delivery_charges() {
			if (this.selected_delivery_charge) {
				this.delivery_charges_rate = this.selected_delivery_charge.rate;
			} else {
				this.delivery_charges_rate = 0;
			}
		},
		updatePostingDate(date) {
			if (!date) return;
			this.posting_date = date;
			this.$forceUpdate();
		},

		// Handle posting date update from Quick View
		onPostingDateUpdate(val) {
			this.posting_date_display = val;
			this.updatePostingDate(val);
		},

		// Handle price list update from Quick View
		onPriceListUpdate(val) {
			this.selected_price_list = val;
			this.update_price_list();
		},
		// Override setFormatedFloat for qty field to handle return mode
		setFormatedQty(item, field_name, precision, no_negative, value) {
			// Use the regular formatter method from the mixin
			let parsedValue = this.setFormatedFloat(item, field_name, precision, no_negative, value);

			// Ensure negative value for return invoices
			if (this.isReturnInvoice && parsedValue > 0) {
				parsedValue = -Math.abs(parsedValue);
				item[field_name] = parsedValue;
			}

			return parsedValue;
		},
		async fetch_available_currencies() {
			try {
				console.log("Fetching available currencies...");
				const r = await frappe.call({
					method: "posawesome.posawesome.api.invoices.get_available_currencies",
				});

				if (r.message) {
					console.log("Received currencies:", r.message);

					// Get base currency for reference
					const baseCurrency = this.pos_profile.currency;

					// Create simple currency list with just names
					this.available_currencies = r.message.map((currency) => {
						return {
							value: currency.name,
							title: currency.name,
						};
					});

					// Sort currencies - base currency first, then others alphabetically
					this.available_currencies.sort((a, b) => {
						if (a.value === baseCurrency) return -1;
						if (b.value === baseCurrency) return 1;
						return a.value.localeCompare(b.value);
					});

					// Set default currency if not already set
					if (!this.selected_currency) {
						this.selected_currency = baseCurrency;
					}

					return this.available_currencies;
				}

				return [];
			} catch (error) {
				console.error("Error fetching currencies:", error);
				// Set default currency as fallback
				const defaultCurrency = this.pos_profile.currency;
				this.available_currencies = [
					{
						value: defaultCurrency,
						title: defaultCurrency,
					},
				];
				this.selected_currency = defaultCurrency;
				return this.available_currencies;
			}
		},

		async fetch_price_lists() {
			if (this.pos_profile.posa_enable_price_list_dropdown) {
				try {
					const r = await frappe.call({
						method: "posawesome.posawesome.api.posapp.get_selling_price_lists",
					});
					if (r && r.message) {
						this.price_lists = r.message.map((pl) => pl.name);
					}
				} catch (error) {
					console.error("Failed fetching price lists", error);
					this.price_lists = [this.pos_profile.selling_price_list];
				}
			} else {
				// Fallback to the price list defined in the POS Profile
				this.price_lists = [this.pos_profile.selling_price_list];
			}

			if (!this.selected_price_list) {
				this.selected_price_list = this.pos_profile.selling_price_list;
			}

			// Fetch and store currency for the applied price list
			try {
				const r = await frappe.call({
					method: "posawesome.posawesome.api.invoices.get_price_list_currency",
					args: { price_list: this.selected_price_list },
				});
				if (r && r.message) {
					this.price_list_currency = r.message;
				}
			} catch (error) {
				console.error("Failed fetching price list currency", error);
			}

			return this.price_lists;
		},

		async update_currency(currency) {
			if (!currency) return;
			this.selected_currency = currency;
			await this.update_currency_and_rate();
		},

		update_exchange_rate() {
			if (!this.exchange_rate || this.exchange_rate <= 0) {
				this.exchange_rate = 1;
			}

			// Emit currency update
			this.eventBus.emit("update_currency", {
				currency: this.selected_currency || this.pos_profile.currency,
				exchange_rate: this.exchange_rate,
			});

			this.update_item_rates();
		},

		update_conversion_rate() {
			if (!this.conversion_rate || this.conversion_rate <= 0) {
				this.conversion_rate = 1;
			}

			this.sync_exchange_rate();
		},

		update_item_rates() {
			console.log("Updating item rates with exchange rate:", this.exchange_rate);

			this.items.forEach((item) => {
				// Set skip flag to avoid double calculations
				item._skip_calc = true;

				// First ensure base rates exist for all items
				if (!item.base_rate) {
					console.log(`Setting base rates for ${item.item_code} for the first time`);
					const baseCurrency = this.price_list_currency || this.pos_profile.currency;
					if (this.selected_currency === baseCurrency) {
						// When in base currency, base rates = displayed rates
						item.base_rate = item.rate;
						item.base_price_list_rate = item.price_list_rate;
						item.base_discount_amount = item.discount_amount || 0;
					} else {
						// When in another currency, calculate base rates
						item.base_rate = item.rate / this.exchange_rate;
						item.base_price_list_rate = item.price_list_rate / this.exchange_rate;
						item.base_discount_amount = (item.discount_amount || 0) / this.exchange_rate;
					}
				}

				// Currency conversion logic
				const baseCurrency = this.price_list_currency || this.pos_profile.currency;
				if (this.selected_currency === baseCurrency) {
					// When switching back to default currency, restore from base rates
					console.log(`Restoring rates for ${item.item_code} from base rates`);
					item.price_list_rate = item.base_price_list_rate;
					item.rate = item.base_rate;
					item.discount_amount = item.base_discount_amount;
				} else if (item.original_currency === this.selected_currency) {
					// When selected currency matches the price list currency,
					// no conversion should be applied
					console.log(`Using original currency rates for ${item.item_code}`);
					item.price_list_rate = item.base_price_list_rate;
					item.rate = item.base_rate;
					item.discount_amount = item.base_discount_amount;
				} else {
					// When switching to another currency, convert from base rates
					console.log(`Converting rates for ${item.item_code} to ${this.selected_currency}`);

					// Convert base currency values to the selected currency
					const converted_price = this.flt(
						item.base_price_list_rate * this.exchange_rate,
						this.currency_precision,
					);
					const converted_rate = this.flt(
						item.base_rate * this.exchange_rate,
						this.currency_precision,
					);
					const converted_discount = this.flt(
						item.base_discount_amount * this.exchange_rate,
						this.currency_precision,
					);

					// Ensure we don't set values to 0 if they're just very small
					item.price_list_rate = converted_price < 0.000001 ? 0 : converted_price;
					item.rate = converted_rate < 0.000001 ? 0 : converted_rate;
					item.discount_amount = converted_discount < 0.000001 ? 0 : converted_discount;
				}

				// Always recalculate final amounts
				item.amount = this.flt(item.qty * item.rate, this.currency_precision);
				item.base_amount = this.flt(item.qty * item.base_rate, this.currency_precision);

				console.log(`Updated rates for ${item.item_code}:`, {
					price_list_rate: item.price_list_rate,
					base_price_list_rate: item.base_price_list_rate,
					rate: item.rate,
					base_rate: item.base_rate,
					discount: item.discount_amount,
					base_discount: item.base_discount_amount,
					amount: item.amount,
					base_amount: item.base_amount,
				});

				// Apply any other pricing rules if needed
				this.calc_item_price(item);
			});

			// Force UI update after all calculations
			this.$forceUpdate();
		},

		formatCurrency(value, precision = null) {
			const prec = precision != null ? precision : this.currency_precision;
			return this.$options.mixins[0].methods.formatCurrency.call(this, value, prec);
		},

		flt(value, precision = null) {
			// Enhanced float handling for small numbers
			if (precision === null) {
				precision = this.float_precision;
			}

			const _value = Number(value);
			if (isNaN(_value)) {
				return 0;
			}

			// Handle very small numbers to prevent them from becoming 0
			if (Math.abs(_value) < 0.000001) {
				return _value;
			}

			return Number((_value || 0).toFixed(precision));
		},

		// Update currency and exchange rate when currency is changed
		async update_currency_and_rate() {
			if (!this.selected_currency) return;

			const companyCurrency =
				(this.company && this.company.default_currency) || this.pos_profile.currency;
			const priceListCurrency = this.price_list_currency || companyCurrency;

			try {
				// Price list currency to selected currency rate
				if (this.selected_currency === priceListCurrency) {
					this.exchange_rate = 1;
				} else {
					const r = await frappe.call({
						method: "posawesome.posawesome.api.invoices.fetch_exchange_rate_pair",
						args: {
							from_currency: priceListCurrency,
							to_currency: this.selected_currency,
						},
					});
					if (r && r.message) {
						this.exchange_rate = r.message.exchange_rate;
					}
				}

				// Selected currency to company currency rate
				if (this.selected_currency === companyCurrency) {
					this.conversion_rate = 1;
					this.exchange_rate_date = this.formatDateForBackend(this.posting_date_display);
				} else {
					const r2 = await frappe.call({
						method: "posawesome.posawesome.api.invoices.fetch_exchange_rate_pair",
						args: {
							from_currency: this.selected_currency,
							to_currency: companyCurrency,
						},
					});
					if (r2 && r2.message) {
						this.conversion_rate = r2.message.exchange_rate;
						this.exchange_rate_date = r2.message.date;
						const posting_backend = this.formatDateForBackend(this.posting_date_display);
						if (this.exchange_rate_date && posting_backend !== this.exchange_rate_date) {
							this.eventBus.emit("show_message", {
								title: __(
									"Exchange rate date " +
										this.exchange_rate_date +
										" differs from posting date " +
										posting_backend,
								),
								color: "warning",
							});
						}
					}
				}
			} catch (error) {
				console.error("Error updating currency:", error);
				this.eventBus.emit("show_message", {
					title: "Error updating currency",
					color: "error",
				});
			}

			this.sync_exchange_rate();

			// If items already exist, update the invoice on the server so that
			// the document currency and rates remain consistent
			if (this.items.length) {
				const doc = this.get_invoice_doc();
				doc.currency = this.selected_currency;
				doc.price_list_currency = priceListCurrency || this.pos_profile.currency;
				doc.conversion_rate = this.conversion_rate;
				doc.plc_conversion_rate = this.exchange_rate;
				try {
					await this.update_invoice(doc);
				} catch (error) {
					console.error("Error updating invoice currency:", error);
					this.eventBus.emit("show_message", {
						title: "Error updating currency",
						color: "error",
					});
				}
			}
		},

		async update_exchange_rate_on_server() {
			if (this.conversion_rate) {
				if (!this.items.length) {
					this.sync_exchange_rate();
					return;
				}

				const doc = this.get_invoice_doc();
				doc.conversion_rate = this.conversion_rate;
				doc.plc_conversion_rate = this.exchange_rate;
				try {
					const resp = await this.update_invoice(doc);
					if (resp && resp.exchange_rate_date) {
						this.exchange_rate_date = resp.exchange_rate_date;
						const posting_backend = this.formatDateForBackend(this.posting_date_display);
						if (posting_backend !== this.exchange_rate_date) {
							this.eventBus.emit("show_message", {
								title: __(
									"Exchange rate date " +
										this.exchange_rate_date +
										" differs from posting date " +
										posting_backend,
								),
								color: "warning",
							});
						}
					}
					this.sync_exchange_rate();
				} catch (error) {
					console.error("Error updating exchange rate:", error);
					this.eventBus.emit("show_message", {
						title: "Error updating exchange rate",
						color: "error",
					});
				}
			}
		},

		sync_exchange_rate() {
			if (!this.exchange_rate || this.exchange_rate <= 0) {
				this.exchange_rate = 1;
			}
			if (!this.conversion_rate || this.conversion_rate <= 0) {
				this.conversion_rate = 1;
			}

			// Emit currency update
			this.eventBus.emit("update_currency", {
				currency: this.selected_currency || this.pos_profile.currency,
				exchange_rate: this.exchange_rate,
				conversion_rate: this.conversion_rate,
			});

			this.update_item_rates();
		},

		// Add new rounding function
		roundAmount(amount) {
			// Respect POS Profile setting to disable rounding
			if (this.pos_profile.disable_rounded_total) {
				// Use configured precision without applying rounding
				return this.flt(amount, this.currency_precision);
			}
			// If multi-currency is enabled and selected currency is different from base currency
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.pos_profile.posa_allow_multi_currency && this.selected_currency !== baseCurrency) {
				// For multi-currency, just keep 2 decimal places without rounding to nearest integer
				return this.flt(amount, 2);
			}
			// For base currency or when multi-currency is disabled, round to nearest integer
			return Math.round(amount);
		},

		// Increase quantity of an item (handles return logic)
		add_one(item) {
			// Increase quantity, return items remain negative
			item.qty++;
			if (item.qty == 0) {
				this.remove_item(item);
			}
			this.calc_stock_qty(item, item.qty);
			this.$forceUpdate();
		},

		// Decrease quantity of an item (handles return logic)
		subtract_one(item) {
			// Decrease quantity, return items remain negative
			item.qty--;
			if (item.qty == 0) {
				this.remove_item(item);
			} else {
				this.calc_stock_qty(item, item.qty);
				this.$forceUpdate();

				// Trigger discount calculation after qty change (if not already applying)
				if (!this.isApplyingDiscount) {
					this.$nextTick(() => {
						setTimeout(() => {
							this.calculateDiscountsDebounced();
						}, 10);
					});
				}
			}
		},

		// Handle item reordering from drag and drop
		handleItemReorder(reorderData) {
			const { fromIndex, toIndex } = reorderData;

			if (fromIndex === toIndex) return;

			// Create a copy of the items array
			const newItems = [...this.items];

			// Remove the item from its original position
			const [movedItem] = newItems.splice(fromIndex, 1);

			// Insert the item at its new position
			newItems.splice(toIndex, 0, movedItem);

			// Update the items array
			this.items = newItems;

			// Show success feedback
			this.eventBus.emit("show_message", {
				title: __("Item order updated"),
				color: "success",
			});

			// Optionally, you can also update the idx field for each item
			this.items.forEach((item, index) => {
				item.idx = index + 1;
			});
		},

		async print_tax_invoice() {
			if (!this.invoice_doc || !this.pos_profile) {
				this.eventBus.emit("show_message", {
					title: __("Missing invoice data or POS profile."),
					color: "error",
				});
				return;
			}

			if (!this.pos_profile.posa_enable_tax_print) {
				this.eventBus.emit("show_message", {
					title: __("Tax printing is not enabled in POS Profile."),
					color: "warning",
				});
				return;
			}

			this.tax_print_loading = true;

			try {
				await handleTaxPrint(
					this.invoice_doc,
					this.pos_profile,
					// onSuccess callback
					(result) => {
						// Update header display with the next invoice number
						updateHeaderTaxDisplay(result.nextDisplay);

						// Update local POS profile state with the new counter
						this.$store.commit('updatePosProfile', {
							tax_current_counter: result.newCounter
						});

						this.eventBus.emit("show_message", {
							title: __("Tax invoice printed successfully."),
							color: "success",
						});
						this.tax_print_loading = false;
					},
					// onError callback
					(error) => {
						console.error("Error printing tax invoice:", error);
						this.eventBus.emit("show_message", {
							title: error.message || __("Failed to print tax invoice."),
							color: "error",
						});
						this.tax_print_loading = false;
					}
				);
			} catch (e) {
				console.error("Unexpected error in print_tax_invoice:", e);
				this.eventBus.emit("show_message", {
					title: __("An unexpected error occurred."),
					color: "error",
				});
				this.tax_print_loading = false;
			}
		},

		handleListInvoices() {
			// Emit event to open list invoices dialog
			this.eventBus.emit("open_list_invoices");
		},

		handleListShifts() {
			// Emit event to open list shifts dialog
			this.eventBus.emit("open_list_shifts");
		},

		// Update shift verification status
		updateShiftVerificationStatus() {
			if (this.pos_shift_report) {
				// Get verification status from shift report data
				if (this.shift_report_data && this.shift_report_data.verification_status) {
					this.shiftVerificationStatus = this.shift_report_data.verification_status;
				} else {
					// Fallback: try to get from server
					this.fetchShiftVerificationStatus();
				}
			} else {
				this.shiftVerificationStatus = null;
			}
		},

		// Fetch verification status from server
		async fetchShiftVerificationStatus() {
			if (!this.pos_shift_report) return;

			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.shift_reports.get_shift_report",
					args: {
						shift_report_id: this.pos_shift_report
					}
				});

				if (response.message && response.message.success) {
					const shiftData = response.message.data;
					this.shiftVerificationStatus = shiftData.verification_status || null;
				}
			} catch (error) {
				console.error("Failed to fetch shift verification status:", error);
				this.shiftVerificationStatus = null;
			}
		},
	},

	mounted() {
		// Setup discount calculation debounced function
		this.calculateDiscountsDebounced = this.debounce(this.calculateDiscountsAPI, 300);
		console.log("⏱️ [DEBOUNCE_SETUP] calculateDiscountsDebounced created with 300ms delay");

		// Load saved column preferences
		this.loadColumnPreferences();
		// Restore saved invoice height
		this.loadInvoiceHeight();
		this.eventBus.on("item-drag-start", (item) => {
			this.showDropFeedback(true);
		});
		this.eventBus.on("item-drag-end", () => {
			this.showDropFeedback(false);
		});

		// Listen for scanned item highlight event
		this.eventBus.on("highlight_scanned_item", (itemCode) => {
			console.log("Invoice received highlight event for:", itemCode);
			if (this.$refs.itemsTable) {
				const result = this.$refs.itemsTable.highlightItem(itemCode);
				if (!result) {
					console.warn("Failed to highlight item:", itemCode);
				}
			} else {
				console.warn("ItemsTable ref not found");
			}
		});

		// Listen for remove item by code event
		this.eventBus.on("remove_item_by_code", (itemCode) => {
			console.log("Received remove_item_by_code event for:", itemCode);
			console.log("Current items in invoice:", this.items.map(i => i.item_code));
			
			const itemToRemove = this.items.find(item => item.item_code === itemCode);
			if (itemToRemove) {
				console.log("Found item to remove:", itemToRemove.item_name);
				this.remove_item(itemToRemove);
				console.log("Successfully removed item:", itemCode);
				frappe.show_alert({
					message: `Removed: ${itemToRemove.item_name}`,
					indicator: "success",
				}, 3);
			} else {
				console.log("Item not found in invoice:", itemCode);
				frappe.show_alert({
					message: `Item ${itemCode} not found in invoice`,
					indicator: "warning",
				}, 3);
			}
		});

		// Register event listeners for POS profile, items, customer, offers, etc.
		this.eventBus.on("register_pos_profile", (data) => {
			this.pos_profile = data.pos_profile;
			this.company = data.company || null;
			this.customer = data.pos_profile.customer;
			this.pos_opening_shift = data.pos_opening_shift;
			this.stock_settings = data.stock_settings;
			
			// Set default customer when POS profile is registered
			this.$nextTick(() => {
				this.setDefaultCustomerAfterClear();
			});
			const prec = parseInt(data.pos_profile.posa_decimal_precision);
			if (!isNaN(prec)) {
				this.float_precision = prec;
				this.currency_precision = prec;
			}
			this.invoiceType = this.pos_profile.posa_default_sales_order ? "Order" : "Invoice";
			this.initializeItemsHeaders();

			// Add this block to handle currency initialization
			if (this.pos_profile.posa_allow_multi_currency) {
				this.fetch_available_currencies()
					.then(async () => {
						// Set default currency after currencies are loaded
						this.selected_currency = this.pos_profile.currency;
						// Fetch proper exchange rate from server
						await this.update_currency_and_rate();
					})
					.catch((error) => {
						console.error("Error initializing currencies:", error);
						this.eventBus.emit("show_message", {
							title: __("Error loading currencies"),
							color: "error",
						});
					});
			}

			this.fetch_price_lists();
			this.update_price_list();
		});
		this.eventBus.on("add_item", this.add_item);
		this.eventBus.on("update_customer", (customer) => {
			this.customer = customer;
		});
		this.eventBus.on("fetch_customer_details", () => {
			this.fetch_customer_details();
		});
		this.eventBus.on("clear_invoice", () => {
			this.clear_invoice();
			// Ensure default customer is set after clearing
			this.$nextTick(() => {
				this.setDefaultCustomerAfterClear();
			});
		});
		this.eventBus.on("load_invoice", (data) => {
			this.load_invoice(data);
		});
		this.eventBus.on("load_order", (data) => {
			this.new_order(data);
			// this.eventBus.emit("set_pos_coupons", data.posa_coupons);
		});
		this.eventBus.on("set_offers", (data) => {
			this.posOffers = data;
		});
		this.eventBus.on("update_invoice_offers", (data) => {
			this.updateInvoiceOffers(data);
		});
		this.eventBus.on("update_invoice_coupons", (data) => {
			console.log("🎫 [EVENT_RECEIVED] update_invoice_coupons received", data);
			this.posa_coupons = data;
			console.log("🎫 [COUPON_UPDATE] posa_coupons updated:", this.posa_coupons);

			// Trigger discount calculation
			this.handelOffers();
			console.log("🎫 [DISCOUNT_TRIGGER] handelOffers() called from coupon update");
		});
		this.eventBus.on("set_all_items", (data) => {
			this.allItems = data;
			this.items.forEach((item) => {
				this.update_item_detail(item);
			});
		});
		this.eventBus.on("load_return_invoice", (data) => {
			// Handle loading of return invoice and set all related fields
			console.log("Invoice component received load_return_invoice event with data:", data);
			this.load_invoice(data.invoice_doc);
			// Explicitly mark as return invoice
			this.invoiceType = "Return";
			this.invoiceTypes = ["Return"];
			this.invoice_doc.is_return = 1;
			// Ensure negative values for returns
			if (this.items && this.items.length) {
				this.items.forEach((item) => {
					// Ensure item quantities are negative
					if (item.qty > 0) item.qty = -Math.abs(item.qty);
					if (item.stock_qty > 0) item.stock_qty = -Math.abs(item.stock_qty);
				});
			}
			if (data.return_doc) {
				console.log("Return against existing invoice:", data.return_doc.name);
				// Ensure negative discount amounts
				this.discount_amount =
					data.return_doc.discount_amount > 0
						? -Math.abs(data.return_doc.discount_amount)
						: data.return_doc.discount_amount;
				this.additional_discount_percentage =
					data.return_doc.additional_discount_percentage > 0
						? -Math.abs(data.return_doc.additional_discount_percentage)
						: data.return_doc.additional_discount_percentage;
				this.return_doc = data.return_doc;
				// Set return_against reference
				this.invoice_doc.return_against = data.return_doc.name;
			} else {
				console.log("Return without invoice reference");
		this.calculateDiscountsDebounced = this.debounce(this.calculateDiscountsAPI, 300);
				// For return without invoice, reset discount values
				this.discount_amount = 0;
				this.additional_discount_percentage = 0;
			}

			// FIX: Force update computed properties after setting return invoice state
			this.$nextTick(() => {
				this.$forceUpdate();
				console.log("Invoice state after loading return:", {
					invoiceType: this.invoiceType,
					is_return: this.invoice_doc.is_return,
					items: this.items.length,
					customer: this.customer,
					subtotal: this.subtotal,
					isReturnInvoice: this.isReturnInvoice,
				});
			});
		});
		this.eventBus.on("set_new_line", (data) => {
			this.new_line = data;
		});
		if (this.pos_profile.posa_allow_multi_currency) {
			this.fetch_available_currencies();
		}
		// Listen for reset_posting_date to reset posting date after invoice submission
		this.eventBus.on("reset_posting_date", () => {
			this.posting_date = frappe.datetime.nowdate();
		});
        this.eventBus.on("calc_uom", this.calc_uom);
        this.eventBus.on("item-drag-start", (item) => {
        	this.showDropFeedback(true);
        });
        this.eventBus.on("item-drag-end", () => {
        	this.showDropFeedback(false);
        });
      
        // Listen for shift verification status changes
        this.eventBus.on("shift_verification_changed", (status) => {
        	this.shiftVerificationStatus = status;
        });
	},
	// Cleanup event listeners before component is destroyed
	beforeUnmount() {
		// Existing cleanup
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("add_item");
		this.eventBus.off("update_customer");
		this.eventBus.off("fetch_customer_details");
		this.eventBus.off("clear_invoice");
		// Cleanup reset_posting_date listener
		this.eventBus.off("reset_posting_date");
		// Cleanup highlight event listener
		this.eventBus.off("highlight_scanned_item");
		// Cleanup remove item event listener
		this.eventBus.off("remove_item_by_code");
		// Cleanup shift verification event listener
		this.eventBus.off("shift_verification_changed");
	},
	// Register global keyboard shortcuts when component is created
	created() {
		document.addEventListener("keydown", this.shortOpenPayment.bind(this));
		document.addEventListener("keydown", this.shortDeleteFirstItem.bind(this));
		document.addEventListener("keydown", this.shortOpenFirstItem.bind(this));
		document.addEventListener("keydown", this.shortSelectDiscount.bind(this));
	},
	// Remove global keyboard shortcuts when component is unmounted
	unmounted() {
		document.removeEventListener("keydown", this.shortOpenPayment);
		document.removeEventListener("keydown", this.shortDeleteFirstItem);
		document.removeEventListener("keydown", this.shortOpenFirstItem);
		document.removeEventListener("keydown", this.shortSelectDiscount);
	},
	watch: invoiceWatchers,
};
</script>

<style scoped>
/* Page content adjustments */
.page-content[data-v-528f966a] {
    flex: 1;
    overflow-y: auto;
    padding-top: 1px;
}

/* Card background adjustments */
.cards {
	background-color: var(--surface-secondary) !important;
}

/* Style for selected checkbox button */
.v-checkbox-btn.v-selected {
	background-color: var(--submit-start) !important;
	color: white;
}

/* Bottom border for elements */
.border_line_bottom {
	border-bottom: 1px solid var(--field-border);
}

/* Disable pointer events for elements */
.disable-events {
	pointer-events: none;
}

/* Style for customer balance field */
:deep(.balance-field) {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	flex-wrap: nowrap;
}

/* Style for balance value text */
:deep(.balance-value) {
	font-size: 1.5rem;
	font-weight: bold;
	color: var(--primary-start);
	margin-left: var(--dynamic-xs);
}

/* Red border and label for return mode card */

/* Red border and label for return mode card */

.return-mode {
	border: 2px solid rgb(var(--v-theme-error)) !important;
	position: relative;
}

/* Label for return mode card */
.return-mode::before {
	content: "RETURN";
	position: absolute;
	top: 0;
	right: 0;
	background-color: rgb(var(--v-theme-error));
	color: white;
	padding: 4px 12px;
	font-weight: bold;
	border-bottom-left-radius: 8px;
	z-index: 1;
}

/* Dynamic padding for responsive layout */
.dynamic-padding {
	/* Uniform spacing for better alignment */
	padding: var(--dynamic-sm);
}

/* Responsive breakpoints */
@media (max-width: 768px) {
	.dynamic-padding {
		/* Smaller uniform padding on tablets */
		padding: var(--dynamic-xs);
	}

	.dynamic-padding .v-row {
		margin: 0 -2px;
	}

	.dynamic-padding .v-col {
		padding: 2px 4px;
	}

	/* Compact buttons for tablets */
	.compact-btn {
		font-size: 0.65rem !important;
		padding: 2px 6px !important;
		min-height: 28px !important;
	}

	.compact-btn .v-icon {
		font-size: 12px !important;
		margin-right: 2px !important;
	}

	.compact-select {
		font-size: 0.75rem !important;
	}

	.compact-select .v-field__input {
		font-size: 0.75rem !important;
		min-height: 36px !important;
	}
}

@media (max-width: 480px) {
	.dynamic-padding {
		padding: var(--dynamic-xs);
	}

	.dynamic-padding .v-row {
		margin: 0 -1px;
	}

	.dynamic-padding .v-col {
		padding: 1px 2px;
	}

	/* Extra compact for mobile */
	.compact-btn {
		font-size: 0.6rem !important;
		padding: 2px 4px !important;
		min-height: 24px !important;
	}

	.compact-btn .v-icon {
		font-size: 10px !important;
		margin-right: 2px !important;
	}

	.compact-select {
		font-size: 0.7rem !important;
	}

	.compact-select .v-field__input {
		font-size: 0.7rem !important;
		min-height: 32px !important;
	}
}

/* Compact button styles for 14-inch POS screens (80% of original size) */
.compact-btn {
	font-size: 0.7rem !important; /* 80% of 0.875rem */
	padding: 4px 8px !important; /* Reduced padding */
	min-height: 32px !important; /* Smaller minimum height */
}

.compact-btn .v-icon {
	font-size: 14px !important; /* Smaller icon */
	margin-right: 4px !important; /* Reduced margin */
}

.compact-select {
	font-size: 0.8rem !important; /* Slightly smaller for select */
}

.compact-select .v-field__input {
	font-size: 0.8rem !important;
	min-height: 40px !important; /* Reduced height */
}

.items-table-wrapper {
	position: relative;
	margin-top: 0; /* Remove margin since button is no longer above */
}

/* New styles for improved column switches */
:deep(.column-switch) {
	margin: 0;
	padding: 0;
}

:deep(.column-switch .v-switch__track) {
	opacity: 0.7;
}

:deep(.column-switch .v-switch__thumb) {
	transform: scale(0.8);
}

:deep(.column-switch .v-label) {
	opacity: 0.9;
	font-size: 0.95rem;
}
</style>