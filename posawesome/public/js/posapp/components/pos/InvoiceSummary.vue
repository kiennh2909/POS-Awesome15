<template>
	<v-card
		:class="[
			'cards mb-0 mt-2 py-3 px-3 rounded-lg resizable sticky-invoice-summary fixed-spacing',
			isDarkTheme ? '' : 'bg-grey-lighten-4',
		]"
		:style="(isDarkTheme ? 'background-color:#1E1E1E;' : '') + 'resize: vertical; overflow: auto;'"
	>
		<!-- Row 1: All numeric fields - Total Qty, Additional Discount, Items Discount, Total -->
		<v-row dense class="mb-0">
			<v-col cols="12">
				<v-row dense>
					<!-- Total Qty -->
					<v-col cols="2">
						<v-text-field
							:model-value="formatFloat(total_qty, hide_qty_decimals ? 0 : undefined)"
							:label="frappe._('Total Qty')"
							prepend-inner-icon="mdi-format-list-numbered"
							variant="solo"
							density="compact"
							readonly
							color="accent"
							class="standard-text-field"
						/>
					</v-col>
					<!-- Additional Discount -->
					<v-col cols="2" v-if="!pos_profile.posa_use_percentage_discount">
						<v-text-field
							:model-value="additional_discount"
							@update:model-value="$emit('update:additional_discount', $event)"
							:label="frappe._('Additional Discount')"
							prepend-inner-icon="mdi-cash-minus"
							variant="solo"
							density="compact"
							color="warning"
							:prefix="currencySymbol(pos_profile.currency)"
							:disabled="
								!pos_profile.posa_allow_user_to_edit_additional_discount ||
								!!discount_percentage_offer_name
							"
							class="standard-text-field"
						/>
					</v-col>
					<v-col cols="2" v-else>
						<v-text-field
							:model-value="additional_discount_percentage"
							@update:model-value="$emit('update:additional_discount_percentage', $event)"
							@change="$emit('update_discount_umount')"
							:rules="[isNumber]"
							:label="frappe._('Additional Discount %')"
							suffix="%"
							prepend-inner-icon="mdi-percent"
							variant="solo"
							density="compact"
							color="warning"
							:disabled="
								!pos_profile.posa_allow_user_to_edit_additional_discount ||
								!!discount_percentage_offer_name
							"
							class="standard-text-field"
						/>
					</v-col>
					<!-- Items Discount -->
					<v-col cols="2">
						<v-text-field
							:model-value="formatCurrency(total_items_discount_amount)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Items Discounts')"
							prepend-inner-icon="mdi-tag-minus"
							variant="solo"
							density="compact"
							color="warning"
							readonly
							class="standard-text-field"
						/>
					</v-col>
					<!-- Total (with larger font) -->
					<v-col cols="2">
						<v-text-field
							:model-value="formatCurrency(subtotal)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Total')"
							prepend-inner-icon="mdi-cash"
							variant="solo"
							density="compact"
							readonly
							color="success"
							class="total-field-large standard-text-field"
						/>
					</v-col>
					<!-- VAT Amount -->
					<v-col cols="2">
						<v-text-field
							:model-value="formatCurrency(vatAmount)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('VAT Amount')"
							prepend-inner-icon="mdi-percent"
							variant="solo"
							density="compact"
							readonly
							color="info"
							class="standard-text-field"
						/>
					</v-col>
					<!-- Total INC VAT -->
					<v-col cols="2">
						<v-text-field
							:model-value="formatCurrency(totalIncVat)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Total INC VAT')"
							prepend-inner-icon="mdi-cash-plus"
							variant="solo"
							density="compact"
							readonly
							color="primary"
							class="total-field-large standard-text-field"
						/>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Row 2: SAVE & CLEAR, LOAD DRAFTS, CANCEL SALE Bản 11h đêm-->
		<v-row dense class="mb-0">
			<v-col cols="12">
				<v-row dense>
					<v-col cols="3" class="button-col pa-1">
						<v-tooltip
							v-if="isShiftVerified"
							text="Cannot save - Shift report has been verified"
							location="top"
						>
							<template v-slot:activator="{ props }">
								<v-btn
									v-bind="props"
									block
									color="accent"
									theme="dark"
									size="small"
									prepend-icon="mdi-content-save"
									@click="$emit('save-and-clear')"
									class="summary-btn"
									title="Ctrl+<u>S</u> - Save and Clear"
									:disabled="isShiftVerified"
								>
									{{ __("SAVE") }}
								</v-btn>
							</template>
						</v-tooltip>
						<v-btn
							v-else
							block
							color="accent"
							theme="dark"
							size="small"
							prepend-icon="mdi-content-save"
							@click="$emit('save-and-clear')"
							class="summary-btn"
							title="Ctrl+<u>S</u> - Save and Clear"
						>
							{{ __("SAVE") }}
						</v-btn>
					</v-col>
					<v-col cols="3" class="button-col pa-1">
						<v-tooltip
							v-if="isShiftVerified"
							text="Cannot load drafts - Shift report has been verified"
							location="top"
						>
							<template v-slot:activator="{ props }">
								<v-btn
									v-bind="props"
									block
									color="warning"
									theme="dark"
									size="small"
									prepend-icon="mdi-file-document"
									@click="$emit('load-drafts')"
									class="white-text-btn summary-btn"
									title="Ctrl+<u>L</u> - Load Drafts"
									:disabled="isShiftVerified"
								>
									{{ __("LOAD") }}
								</v-btn>
							</template>
						</v-tooltip>
						<v-btn
							v-else
							block
							color="warning"
							theme="dark"
							size="small"
							prepend-icon="mdi-file-document"
							@click="$emit('load-drafts')"
							class="white-text-btn summary-btn"
							title="Ctrl+<u>L</u> - Load Drafts"
						>
							{{ __("LOAD") }}
						</v-btn>
					</v-col>
					<v-col cols="3" class="button-col pa-1">
						<v-tooltip
							v-if="isShiftVerified"
							text="Cannot cancel sale - Shift report has been verified"
							location="top"
						>
							<template v-slot:activator="{ props }">
								<v-btn
									v-bind="props"
									block
									color="error"
									theme="dark"
									size="small"
									prepend-icon="mdi-close-circle"
									@click="$emit('cancel-sale')"
									class="summary-btn"
									title="Ctrl+<u>C</u> - Cancel Sale"
									:disabled="isShiftVerified"
								>
									{{ __("CANCEL") }}
								</v-btn>
							</template>
						</v-tooltip>
						<v-btn
							v-else
							block
							color="error"
							theme="dark"
							size="small"
							prepend-icon="mdi-close-circle"
							@click="$emit('cancel-sale')"
							class="summary-btn"
							title="Ctrl+<u>C</u> - Cancel Sale"
						>
							{{ __("CANCEL") }}
						</v-btn>
					</v-col>
					<v-col cols="3" class="button-col pa-1">
						<v-btn
							block
							color="info"
							theme="dark"
							size="small"
							prepend-icon="mdi-view-list"
							@click="$emit('list-shifts')"
							class="summary-btn list-shifts-btn"
							title="Ctrl+<u>S</u> - List Shifts"
						>
							{{ __("LIST SHIFTS") }}
						</v-btn>
					</v-col>
					<v-col cols="3" class="button-col pa-1" v-if="false">
						<v-btn
							block
							color="info"
							theme="dark"
							size="small"
							prepend-icon="mdi-account-plus"
							@click="$emit('add-customer')"
							class="summary-btn add-customer-btn"
							title="Ctrl+<u>A</u> - Add Customer"
						>
							{{ __("ADD CUSTOMER") }}
						</v-btn>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Row 3: PRINT DRAFT, PAY, TRẢ HÀNG BÁN -->
		<v-row dense>
			<v-col cols="12">
				<v-row dense>
					<v-col
						cols="3"
						v-if="pos_profile.posa_allow_print_draft_invoices"
						class="button-col pa-1"
					>
						<v-tooltip
							v-if="isShiftVerified"
							text="Cannot print draft - Shift report has been verified"
							location="top"
						>
							<template v-slot:activator="{ props }">
								<v-btn
									v-bind="props"
									block
									color="primary"
									theme="dark"
									size="small"
									prepend-icon="mdi-file-document-outline"
									@click="$emit('print-draft')"
									class="summary-btn"
									title="Ctrl+<u>D</u> - Draft Invoice"
									:disabled="isShiftVerified"
								>
									{{ __("DRAFT") }}
								</v-btn>
							</template>
						</v-tooltip>
						<v-btn
							v-else
							block
							color="primary"
							theme="dark"
							size="small"
							prepend-icon="mdi-file-document-outline"
							@click="$emit('print-draft')"
							class="summary-btn"
							title="Ctrl+<u>D</u> - Draft Invoice"
						>
							{{ __("DRAFT") }}
						</v-btn>
					</v-col>
					<v-col
						:cols="pos_profile.posa_allow_print_draft_invoices ? 3 : 4"
						class="button-col pa-1"
					>
						<v-tooltip
							v-if="isShiftVerified"
							text="Cannot process payment - Shift report has been verified"
							location="top"
						>
							<template v-slot:activator="{ props }">
								<v-btn
									v-bind="props"
									block
									color="success"
									theme="dark"
									size="small"
									prepend-icon="mdi-credit-card"
									@click="$emit('show-payment')"
									class="summary-btn pay-btn"
									title="Ctrl+<u>P</u> - Payment"
									:disabled="isShiftVerified"
								>
									{{ __("PAY") }}
								</v-btn>
							</template>
						</v-tooltip>
						<v-btn
							v-else
							block
							color="success"
							theme="dark"
							size="small"
							prepend-icon="mdi-credit-card"
							@click="$emit('show-payment')"
							class="summary-btn pay-btn"
							title="Ctrl+<u>P</u> - Payment"
						>
							{{ __("PAY") }}
						</v-btn>
					</v-col>
					<v-col
						:cols="pos_profile.posa_allow_print_draft_invoices ? 3 : 4"
						v-if="pos_profile.posa_allow_return == 1"
						class="button-col pa-1"
					>
						<v-tooltip
							v-if="isShiftVerified"
							text="Cannot process returns - Shift report has been verified"
							location="top"
						>
							<template v-slot:activator="{ props }">
								<v-btn
									v-bind="props"
									block
									color="teal"
									theme="dark"
									size="small"
									prepend-icon="mdi-backup-restore"
									@click="$emit('open-returns')"
									class="summary-btn"
									title="Ctrl+<u>R</u> - Return"
									:disabled="isShiftVerified"
								>
									{{ __("RETURN") }}
								</v-btn>
							</template>
						</v-tooltip>
						<v-btn
							v-else
							block
							color="teal"
							theme="dark"
							size="small"
							prepend-icon="mdi-backup-restore"
							@click="$emit('open-returns')"
							class="summary-btn"
							title="Ctrl+<u>R</u> - Return"
						>
							{{ __("RETURN") }}
						</v-btn>
					</v-col>
					<v-col
						:cols="
							pos_profile.posa_allow_print_draft_invoices
								? pos_profile.posa_allow_return == 1
									? 3
									: 6
								: pos_profile.posa_allow_return == 1
									? 4
									: 8
						"
						class="button-col pa-1"
					>
						<v-btn
							block
							color="secondary"
							theme="dark"
							size="small"
							prepend-icon="mdi-format-list-bulleted"
							@click="$emit('list-invoices')"
							class="summary-btn list-invoices-btn"
							title="Ctrl+<u>I</u> - List Invoices"
						>
							{{ __("LIST INVOICES") }}
						</v-btn>
					</v-col>
				</v-row>
			</v-col>
		</v-row>
	</v-card>
</template>

<script>
export default {
	props: {
		pos_profile: Object,
		total_qty: [Number, String],
		additional_discount: Number,
		additional_discount_percentage: Number,
		total_items_discount_amount: Number,
		subtotal: Number,
		vatAmount: Number,
		totalIncVat: Number,
		displayCurrency: String,
		formatFloat: Function,
		formatCurrency: Function,
		currencySymbol: Function,
		discount_percentage_offer_name: [String, Number],
		isNumber: Function,
		shiftVerificationStatus: {
			type: String,
			default: null,
		},
	},
	emits: [
		"update:additional_discount",
		"update:additional_discount_percentage",
		"update_discount_umount",
		"save-and-clear",
		"load-drafts",
		"select-order",
		"cancel-sale",
		"open-returns",
		"print-draft",
		"show-payment",
		"add-customer",
		"list-invoices",
		"list-shifts",
	],
	computed: {
		isDarkTheme() {
			return this.$theme?.current === "dark";
		},
		hide_qty_decimals() {
			try {
				const saved = localStorage.getItem("posawesome_item_selector_settings");
				if (saved) {
					const opts = JSON.parse(saved);
					return !!opts.hide_qty_decimals;
				}
			} catch (e) {
				console.error("Failed to load item selector settings:", e);
			}
			return false;
		},
		isShiftVerified() {
			return this.shiftVerificationStatus === "Verified";
		},
	},

	methods: {
		setupKeyboardShortcuts() {
			// Keyboard shortcuts for invoice actions
			document.addEventListener("keydown", this.handleKeyboardShortcuts);
		},

		handleKeyboardShortcuts(event) {
			// Only handle shortcuts when not typing in input fields
			if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA") {
				return;
			}

			// Prevent default browser behavior for our shortcuts
			const key = event.key.toLowerCase();

			switch (key) {
				case "s":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						this.$emit("save-and-clear");
						console.log("Shortcut: Ctrl+S - Save and Clear");

						// Focus back to search input after save
						this.$nextTick(() => {
							// Try multiple selectors to find the search input
							let searchInput =
								document.querySelector('input[placeholder*="Search"]') ||
								document.querySelector(".v-text-field input") ||
								document.querySelector("input[autofocus]");

							if (searchInput) {
								searchInput.focus();
								searchInput.select(); // Select all text for easy replacement
								console.log("Focused back to search input after save");
							} else {
								console.warn("Could not find search input to focus");
							}
						});
					}
					break;
				case "p":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						this.$emit("show-payment");
						console.log("Shortcut: Ctrl+P - Payment");
					}
					break;
				case "l":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						this.$emit("load-drafts");
						console.log("Shortcut: Ctrl+L - Load Drafts");
					}
					break;
				case "c":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						this.$emit("cancel-sale");
						console.log("Shortcut: Ctrl+C - Cancel Sale");
					}
					break;
				case "r":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						if (this.pos_profile.posa_allow_return == 1) {
							this.$emit("open-returns");
							console.log("Shortcut: Ctrl+R - Return");
						}
					}
					break;
				case "d":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						if (this.pos_profile.posa_allow_print_draft_invoices) {
							this.$emit("print-draft");
							console.log("Shortcut: Ctrl+D - Draft Invoice");
						}
					}
					break;
				case "a":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						this.$emit("add-customer");
						console.log("Shortcut: Ctrl+A - Add Customer");
					}
					break;
				case "i":
					if (event.ctrlKey || event.metaKey) {
						event.preventDefault();
						this.$emit("list-invoices");
						console.log("Shortcut: Ctrl+I - List Invoices");
					}
					break;
			}
		},
	},

	mounted() {
		// Setup keyboard shortcuts when component is mounted
		this.setupKeyboardShortcuts();
	},

	beforeUnmount() {
		// Clean up keyboard event listener
		document.removeEventListener("keydown", this.handleKeyboardShortcuts);
	},
};
</script>

<style scoped>
.cards {
	background-color: #f5f5f5 !important;
}

:deep(.dark-theme) .cards,
:deep(.dark-theme) .cards .v-card__underlay,
:deep(.v-theme--dark) .cards,
:deep(.v-theme--dark) .cards .v-card__underlay,
:deep(.cards.v-theme--dark),
:deep(.cards.v-theme--dark) .v-card__underlay,
::v-deep(.dark-theme) .cards,
::v-deep(.dark-theme) .cards .v-card__underlay,
::v-deep(.v-theme--dark) .cards,
::v-deep(.v-theme--dark) .cards .v-card__underlay,
::v-deep(.cards.v-theme--dark),
::v-deep(.cards.v-theme--dark) .v-card__underlay {
	background-color: #1e1e1e !important;
}

.white-text-btn {
	color: white !important;
}

.white-text-btn :deep(.v-btn__content) {
	color: white !important;
}

/* ensure long button labels stay within the button */
.summary-btn :deep(.v-btn__content) {
	white-space: normal !important;
}

/* Custom spacing for action buttons */
.action-buttons-row {
	gap: 3px;
}

/* Row spacing */
.v-row.dense.mb-0 {
	margin-bottom: 5px !important;
}

/* Spacing giữa Row 2 và Row 3 */
.v-row.dense.mb-0 + .v-row.dense {
	margin-top: 1px !important;
}

/* Spacing giữa Row 3 và các elements khác */
.v-row.dense:last-child {
	margin-bottom: 2px !important;
}

/* Dense row styling */
.v-row--dense > .v-col,
.v-row--dense > [class*="v-col-"] {
	padding: 1px;
}

.v-row--dense {
	margin: -2px;
}

/* Button spacing */
.button-col {
	margin-bottom: 0px;
	padding: 0px;
	margin-right: 3px;
	flex-shrink: 0; /* Prevent shrinking */
}

.button-col:last-child {
	margin-right: 0px;
}

/* Ensure buttons don't wrap */
.v-row.dense .v-col .v-row.dense {
	flex-wrap: nowrap !important;
	align-items: stretch;
	display: flex !important;
}

.v-row.dense .v-col .v-row.dense .button-col {
	flex: 1;
	min-width: 0; /* Allow flex shrinking */
	flex-shrink: 0;
}

/* Force single line layout */
.v-row.dense .v-col .v-row.dense .v-col {
	flex-shrink: 0 !important;
	min-width: fit-content !important;
}

.button-col {
	margin-bottom: 0px;
	padding: 0px;
}

.button-col-large {
	margin-bottom: 0px;
	padding: 0px;
}

.button-col-pay {
	margin-bottom: 0px;
	padding: 0px;
}

/* Custom column width for 6-column layout */
.v-col-2 {
	flex: 0 0 16.6666666667% !important;
	max-width: 16.6666666667% !important;
}

.v-col-3 {
	flex: 0 0 24% !important;
	max-width: 24% !important;
}

.v-col-4 {
	flex: 0 0 32.3333333333% !important;
	max-width: 33.3333333333% !important;
}

/* Standard button styling - compact size */
.summary-btn {
	min-height: 60px !important;
	font-size: 1.3rem !important;
	font-weight: 600 !important;
	text-transform: none;
	margin: 1px;
	border-radius: 6px;
	padding: 6px 8px !important;
	white-space: nowrap !important;
}

/* Large button styling for PRINT DRAFT */
.large-btn {
	min-height: 60px !important;
	font-size: 0.9rem !important;
	font-weight: 600 !important;
	margin: 1px;
	padding: 6px 10px !important;
}

/* Extra large PAY button */
.pay-btn {
	min-height: 60px !important;
	font-size: 1rem !important;
	font-weight: 700 !important;
	text-transform: uppercase;
	letter-spacing: 1px;
	margin: 1px;
	border-radius: 8px;
	padding: 8px 12px !important;
}

/* ADD CUSTOMER button */
.add-customer-btn {
	min-height: 60px !important;
	font-size: 1.1rem !important;
	font-weight: 600 !important;
	margin: 1px;
	border-radius: 6px;
	padding: 6px 8px !important;
}

/* LIST INVOICES button */
.list-invoices-btn {
	min-height: 60px !important;
	font-size: 1.1rem !important;
	font-weight: 600 !important;
	margin: 1px;
	border-radius: 6px;
	padding: 6px 8px !important;
}

/* LIST SHIFTS button */
.list-shifts-btn {
	min-height: 60px !important;
	font-size: 1.1rem !important;
	font-weight: 600 !important;
	margin: 1px;
	border-radius: 6px;
	padding: 6px 8px !important;
}

.pay-btn :deep(.v-btn__content) {
	font-size: 1.3rem !important;
	font-weight: 700 !important;
}

.pay-btn :deep(.mdi-credit-card) {
	font-size: 1.5rem !important;
}

/* Standard text field styling - match ItemsSelector */
.standard-text-field :deep(.v-field__input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

.standard-text-field :deep(.v-field__input input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

/* Large font for Total field */
.total-field-large :deep(.v-field__input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

.total-field-large :deep(.v-field__input input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

/* Ensure all buttons in row 2 and 3 have same height */
.v-row.dense .button-col .v-btn {
	min-height: 60px !important;
}

/* Vuetify input field height to match buttons */
.v-input--density-compact .v-field--variant-filled,
.v-input--density-compact .v-field--variant-solo,
.v-input--density-compact .v-field--variant-solo-filled,
.v-input--density-compact .v-field--variant-solo-inverted {
	--v-input-control-height: 50px;
	--v-field-padding-bottom: 0px;
}

/* Prevent button text wrapping */
.summary-btn :deep(.v-btn__content) {
	white-space: nowrap !important;
	overflow: hidden !important;
	text-overflow: ellipsis !important;
}

/* Force container to not wrap */
.invoice-summary-row {
	display: flex !important;
	flex-wrap: nowrap !important;
	width: 100% !important;
}

/* Fixed spacing between ItemsTable and InvoiceSummary */
.fixed-spacing {
	margin-top: 5px !important;
}

/* Sticky InvoiceSummary at right side only */
.sticky-invoice-summary {
	position: fixed !important;
	bottom: 0 !important;
	right: 0 !important;
	width: 58% !important;
	z-index: 1000 !important;
	box-shadow: 0 -4px 12px #00000026 !important;
	border-top: 2px solid #2ac446 !important;
	border-left: 3px solid #17d86f !important;
	height: 280px !important;
	overflow-y: auto !important;
	background: blueviolet !important;
}

.sticky-invoice-summary[data-v-ab85018a] {
	position: fixed !important;
	bottom: 0 !important;
	right: 0 !important;
	width: 58% !important;
	z-index: 1000 !important;
	box-shadow: 0 -4px 12px #00000026 !important;
	border-top: 5px solid #d9dfe6 !important;
	border-left: 5px solid #d9dfe6 !important;
	height: 280px !important;
	overflow-y: auto !important;
	/* background: blueviolet !important; */
}

/* Mobile responsive adjustments for sticky */
@media (max-width: 768px) {
	.sticky-invoice-summary {
		width: 100% !important; /* Full width on mobile */
		max-height: 220px !important;
		padding: 8px !important;
	}

	.standard-text-field :deep(.v-field__input) {
		font-size: 1.1rem !important;
		min-height: 45px !important;
	}

	.standard-text-field :deep(.v-field__input input) {
		font-size: 1.1rem !important;
		min-height: 45px !important;
	}

	/* Custom column width for mobile 6-column layout */
	.v-col-2 {
		flex: 0 0 50% !important;
		max-width: 50% !important;
	}

	.add-customer-btn,
	.list-invoices-btn {
		font-size: 0.9rem !important;
		min-height: 50px !important;
	}

	.total-field-large :deep(.v-field__input) {
		font-size: 1.2rem !important;
		min-height: 50px !important;
	}

	.total-field-large :deep(.v-field__input input) {
		font-size: 1.2rem !important;
		min-height: 50px !important;
	}
}

@media (max-width: 480px) {
	.sticky-invoice-summary {
		max-height: 200px !important;
		padding: 6px !important;
	}

	.standard-text-field :deep(.v-field__input) {
		font-size: 1rem !important;
		min-height: 42px !important;
	}

	.standard-text-field :deep(.v-field__input input) {
		font-size: 1rem !important;
		min-height: 42px !important;
	}

	/* Custom column width for mobile 6-column layout */
	.v-col-2 {
		flex: 0 0 100% !important;
		max-width: 100% !important;
	}

	.add-customer-btn,
	.list-invoices-btn {
		font-size: 0.8rem !important;
		min-height: 48px !important;
	}

	.total-field-large :deep(.v-field__input) {
		font-size: 1.1rem !important;
		min-height: 48px !important;
	}

	.total-field-large :deep(.v-field__input input) {
		font-size: 1.1rem !important;
		min-height: 48px !important;
	}
}
</style>
