<template>
	<v-card
		:class="['cards mb-0 mt-2 py-3 px-3 rounded-lg resizable', isDarkTheme ? '' : 'bg-grey-lighten-4']"
		:style="(isDarkTheme ? 'background-color:#1E1E1E;' : '') + 'resize: vertical; overflow: auto;'"
	>
		<!-- Row 1: All numeric fields - Total Qty, Additional Discount, Items Discount, Total -->
		<v-row dense class="mb-0">
			<v-col cols="12">
				<v-row dense>
					<!-- Total Qty -->
					<v-col cols="3">
						<v-text-field
							:model-value="formatFloat(total_qty, hide_qty_decimals ? 0 : undefined)"
							:label="frappe._('Total Qty')"
							prepend-inner-icon="mdi-format-list-numbered"
							variant="solo"
							density="compact"
							readonly
							color="accent"
						/>
					</v-col>
					<!-- Additional Discount -->
					<v-col cols="3" v-if="!pos_profile.posa_use_percentage_discount">
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
						/>
					</v-col>
					<v-col cols="3" v-else>
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
						/>
					</v-col>
					<!-- Items Discount -->
					<v-col cols="3">
						<v-text-field
							:model-value="formatCurrency(total_items_discount_amount)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Items Discounts')"
							prepend-inner-icon="mdi-tag-minus"
							variant="solo"
							density="compact"
							color="warning"
							readonly
						/>
					</v-col>
					<!-- Total (with larger font) -->
					<v-col cols="3">
						<v-text-field
							:model-value="formatCurrency(subtotal)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Total')"
							prepend-inner-icon="mdi-cash"
							variant="solo"
							density="compact"
							readonly
							color="success"
							class="total-field-large"
						/>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Row 2: SAVE & CLEAR, LOAD DRAFTS, CANCEL SALE -->
		<v-row dense class="mb-0">
			<v-col cols="12">
				<v-row dense>
					<v-col cols="4" class="button-col pa-1">
						<v-btn
							block
							color="accent"
							theme="dark"
							size="default"
							prepend-icon="mdi-content-save"
							@click="$emit('save-and-clear')"
							class="summary-btn"
						>
							{{ __("SAVE & CLEAR") }}
						</v-btn>
					</v-col>
					<v-col cols="4" class="button-col pa-1">
						<v-btn
							block
							color="warning"
							theme="dark"
							size="default"
							prepend-icon="mdi-file-document"
							@click="$emit('load-drafts')"
							class="white-text-btn summary-btn"
						>
							{{ __("LOAD DRAFTS") }}
						</v-btn>
					</v-col>
					<v-col cols="4" class="button-col pa-1">
						<v-btn
							block
							color="error"
							theme="dark"
							size="default"
							prepend-icon="mdi-close-circle"
							@click="$emit('cancel-sale')"
							class="summary-btn"
						>
							{{ __("CANCEL SALE") }}
						</v-btn>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Row 3: PRINT DRAFT, PAY, TRẢ HÀNG BÁN -->
		<v-row dense>
			<v-col cols="12">
				<v-row dense>
					<v-col cols="4" v-if="pos_profile.posa_allow_print_draft_invoices" class="button-col pa-1">
						<v-btn
							block
							color="primary"
							theme="dark"
							size="default"
							prepend-icon="mdi-printer"
							@click="$emit('print-draft')"
							class="summary-btn"
						>
							{{ __("PRINT DRAFT") }}
						</v-btn>
					</v-col>
					<v-col :cols="pos_profile.posa_allow_print_draft_invoices ? 4 : 6" class="button-col pa-1">
						<v-btn
							block
							color="success"
							theme="dark"
							size="x-large"
							prepend-icon="mdi-credit-card"
							@click="$emit('show-payment')"
							class="summary-btn pay-btn"
						>
							{{ __("PAY") }}
						</v-btn>
					</v-col>
					<v-col :cols="pos_profile.posa_allow_print_draft_invoices ? 4 : 6" v-if="pos_profile.posa_allow_return == 1" class="button-col pa-1">
						<v-btn
							block
							color="teal"
							theme="dark"
							size="default"
							prepend-icon="mdi-backup-restore"
							@click="$emit('open-returns')"
							class="summary-btn"
						>
							{{ __("TRẢ HÀNG BÁN") }}
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
		displayCurrency: String,
		formatFloat: Function,
		formatCurrency: Function,
		currencySymbol: Function,
		discount_percentage_offer_name: [String, Number],
		isNumber: Function,
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
	flex-wrap: nowrap;
	align-items: stretch;
}

.v-row.dense .v-col .v-row.dense .button-col {
	flex: 1;
	min-width: 0; /* Allow flex shrinking */
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

/* Standard button styling - compact size */
.summary-btn {
	min-height: 44px !important;
	font-size: 0.95rem !important;
	font-weight: 600 !important;
	text-transform: none;
	margin: 1px;
	border-radius: 6px;
	padding: 8px 12px !important;
}

/* Large button styling for PRINT DRAFT */
.large-btn {
	min-height: 48px !important;
	font-size: 1.1rem !important;
	font-weight: 600 !important;
	margin: 1px;
	padding: 10px 14px !important;
}

/* Extra large PAY button */
.pay-btn {
	min-height: 56px !important;
	font-size: 1.2rem !important;
	font-weight: 700 !important;
	text-transform: uppercase;
	letter-spacing: 1px;
	margin: 1px;
	border-radius: 8px;
	padding: 12px 16px !important;
}

.pay-btn :deep(.v-btn__content) {
	font-size: 1.3rem !important;
	font-weight: 700 !important;
}

.pay-btn :deep(.mdi-credit-card) {
	font-size: 1.5rem !important;
}

/* Large font for Total field */
.total-field-large :deep(.v-field__input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
}

.total-field-large :deep(.v-field__input input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
}

/* Ensure all buttons in row 2 and 3 have same height */
.v-row.dense .button-col .v-btn {
	min-height: 44px !important;
}
</style>
