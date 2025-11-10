<!-- eslint-disable vue/multi-word-component-names -->
<template>
	<div class="pa-0">
		<v-card
			:class="['selection mx-auto pa-1 my-0 mt-3', isDarkTheme ? '' : 'bg-grey-lighten-5']"
			:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
			style="max-height: 68vh; height: 68vh"
		>
			<v-progress-linear
				:active="loading"
				:indeterminate="loading"
				absolute
				location="top"
				color="info"
			></v-progress-linear>
			<div class="overflow-y-auto pa-2" style="max-height: 67vh">
				<!-- Payment Summary (Paid, To Be Paid, Change) -->
				<v-row v-if="invoice_doc" class="pa-1" dense>
					<v-col cols="7">
						<v-text-field
							variant="solo"
							color="primary"
							:label="frappe._('Paid Amount')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field large-text"
							hide-details
							v-model="total_payments_display"
							readonly
							:prefix="currencySymbol(invoice_doc.currency)"
							density="compact"
							@click="showPaidAmount"
						></v-text-field>
					</v-col>
					<v-col cols="5">
						<v-text-field
							variant="solo"
							color="primary"
							label="To Be Paid"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							v-model="diff_payment_display"
							:prefix="currencySymbol(invoice_doc.currency)"
							density="compact"
							@focus="showDiffPayment"
							persistent-placeholder
						></v-text-field>
					</v-col>

					<!-- Paid Change (if applicable) -->
					<v-col cols="7" v-if="credit_change > 0 && !invoice_doc.is_return">
						<v-text-field
							variant="solo"
							color="primary"
							:label="frappe._('Paid Change')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							:model-value="formatCurrency(paid_change)"
							:prefix="currencySymbol(invoice_doc.currency)"
							:rules="paid_change_rules"
							density="compact"
							readonly
							type="text"
							@click="showPaidChange"
						></v-text-field>
					</v-col>

					<!-- Credit Change (if applicable) -->
					<v-col cols="5" v-if="credit_change > 0 && !invoice_doc.is_return">
						<v-text-field
							variant="solo"
							color="primary"
							:label="frappe._('Credit Change')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							:model-value="formatCurrency(credit_change)"
							:prefix="currencySymbol(invoice_doc.currency)"
							density="compact"
							type="text"
							@change="
								setFormatedCurrency(this, 'credit_change', null, false, $event);
								updateCreditChange(this.credit_change);
							"
						></v-text-field>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Payment Inputs (All Payment Methods) -->
				<div v-if="is_cashback">
					<v-row class="payments pa-1" v-for="payment in invoice_doc.payments" :key="payment.name">
						<v-col cols="6" v-if="!is_mpesa_c2b_payment(payment)">
							<v-text-field
								density="compact"
								variant="solo"
								color="primary"
								:label="frappe._(payment.mode_of_payment)"
								:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
								class="dark-field sleek-field large-text"
								hide-details
								:model-value="formatCurrency(payment.amount)"
								@change="setFormatedCurrency(payment, 'amount', null, false, $event)"
								:rules="[
									isNumber,
									(v) =>
										!payment.mode_of_payment.toLowerCase().includes('cash') ||
										this.is_credit_sale ||
										v >=
											(this.invoice_doc.rounded_total ||
												this.invoice_doc.grand_total) ||
										'Cash payment cannot be less than invoice total when credit sale is off',
								]"
								:prefix="currencySymbol(invoice_doc.currency)"
								@focus="set_rest_amount(payment.idx)"
								:readonly="invoice_doc.is_return"
							></v-text-field>
						</v-col>
						<v-col cols="6" v-if="!is_mpesa_c2b_payment(payment)">
							<v-btn
								block
								color="primary"
								theme="dark"
								size="large"
								@click="set_full_amount(payment.idx)"
							>
								{{ payment.mode_of_payment }}
							</v-btn>
						</v-col>

						<!-- M-Pesa Payment Button (if payment is M-Pesa) -->
						<!-- <v-col cols="12" v-if="is_mpesa_c2b_payment(payment)" class="pl-3">
							<v-btn block color="success" theme="dark" @click="mpesa_c2b_dialog(payment)">
								{{ __("Get Payments") }} {{ payment.mode_of_payment }}
							</v-btn>
						</v-col> -->

						<!-- Request Payment for Phone Type -->
						<!-- <v-col
							cols="3"
							v-if="payment.type === 'Phone' && payment.amount > 0 && request_payment_field"
							class="pl-1"
						>
							<v-btn
								block
								color="success"
								theme="dark"
								:disabled="payment.amount === 0"
								@click="request_payment(payment)"
							>
								{{ __("Request") }}
							</v-btn>
						</v-col> -->
					</v-row>
				</div>

				<!-- Loyalty Points Redemption -->
				<v-row
					class="payments pa-1"
					v-if="invoice_doc && available_points_amount > 0 && !invoice_doc.is_return"
				>
					<v-col cols="7">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Redeem Loyalty Points')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(loyalty_amount)"
							type="text"
							@change="setFormatedCurrency(this, 'loyalty_amount', null, false, $event)"
							:prefix="currencySymbol(invoice_doc.currency)"
						></v-text-field>
					</v-col>
					<v-col cols="5">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('You can redeem up to')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatFloat(available_points_amount)"
							:prefix="currencySymbol(invoice_doc.currency)"
							readonly
						></v-text-field>
					</v-col>
				</v-row>

				<!-- Customer Credit Redemption -->
				<v-row
					class="payments pa-1"
					v-if="
						invoice_doc &&
						available_customer_credit > 0 &&
						!invoice_doc.is_return &&
						redeem_customer_credit
					"
				>
					<v-col cols="7">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Redeemed Customer Credit')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(redeemed_customer_credit)"
							type="text"
							@change="
								setFormatedCurrency(this, 'redeemed_customer_credit', null, false, $event)
							"
							:prefix="currencySymbol(invoice_doc.currency)"
							readonly
						></v-text-field>
					</v-col>
					<v-col cols="5">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('You can redeem credit up to')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(available_customer_credit)"
							:prefix="currencySymbol(invoice_doc.currency)"
							readonly
						></v-text-field>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Invoice Totals (Net, Tax, Total, Discount, Grand, Rounded) -->
				<v-row class="pa-1">
					<v-col cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Net Total')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							:model-value="formatCurrency(invoice_doc.net_total, displayCurrency)"
							readonly
							:prefix="currencySymbol()"
							persistent-placeholder
						></v-text-field>
					</v-col>
					<v-col cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Tax and Charges')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="
								formatCurrency(invoice_doc.total_taxes_and_charges, displayCurrency)
							"
							readonly
							:prefix="currencySymbol()"
							persistent-placeholder
						></v-text-field>
					</v-col>
					<v-col cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Total Amount')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(invoice_doc.total, displayCurrency)"
							readonly
							:prefix="currencySymbol()"
							persistent-placeholder
						></v-text-field>
					</v-col>
					<v-col cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="diff_label"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(diff_payment, displayCurrency)"
							readonly
							:prefix="currencySymbol()"
							persistent-placeholder
						></v-text-field>
					</v-col>
					<v-col cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Discount Amount')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(invoice_doc.discount_amount)"
							readonly
							:prefix="currencySymbol(invoice_doc.currency)"
							persistent-placeholder
						></v-text-field>
					</v-col>
					<v-col cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Grand Total')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(invoice_doc.grand_total)"
							readonly
							:prefix="currencySymbol(invoice_doc.currency)"
							persistent-placeholder
						></v-text-field>
					</v-col>
					<v-col v-if="invoice_doc.rounded_total" cols="6">
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Rounded Total')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							:model-value="formatCurrency(invoice_doc.rounded_total)"
							readonly
							:prefix="currencySymbol(invoice_doc.currency)"
							persistent-placeholder
						></v-text-field>
					</v-col>

					<!-- Delivery Date and Address (if applicable) -->
					<v-col cols="6" v-if="pos_profile.posa_allow_sales_order && invoiceType === 'Order'">
						<VueDatePicker
							v-model="new_delivery_date"
							model-type="format"
							format="dd-MM-yyyy"
							:min-date="new Date()"
							auto-apply
							:dark="isDarkTheme"
							class="dark-field sleek-field"
							@update:model-value="update_delivery_date()"
						/>
					</v-col>
					<!-- Shipping Address Selection (if delivery date is set) -->
					<v-col cols="12" v-if="invoice_doc.posa_delivery_date">
						<v-autocomplete
							density="compact"
							clearable
							auto-select-first
							variant="solo"
							color="primary"
							:label="frappe._('Address')"
							v-model="invoice_doc.shipping_address_name"
							:items="addresses"
							item-title="address_title"
							item-value="name"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							no-data-text="Address not found"
							hide-details
							:customFilter="addressFilter"
							append-icon="mdi-plus"
							@click:append="new_address"
						>
							<template v-slot:item="{ item }">
								<v-list-item>
									<v-list-item-title class="text-primary text-subtitle-1">
										<div v-html="item.address_title"></div>
									</v-list-item-title>
									<v-list-item-subtitle>
										<div v-html="item.address_line1"></div>
									</v-list-item-subtitle>
									<v-list-item-subtitle v-if="item.address_line2">
										<div v-html="item.address_line2"></div>
									</v-list-item-subtitle>
									<v-list-item-subtitle v-if="item.city">
										<div v-html="item.city"></div>
									</v-list-item-subtitle>
									<v-list-item-subtitle v-if="item.state">
										<div v-html="item.state"></div>
									</v-list-item-subtitle>
									<v-list-item-subtitle v-if="item.country">
										<div v-html="item.country"></div>
									</v-list-item-subtitle>
									<v-list-item-subtitle v-if="item.mobile_no">
										<div v-html="item.mobile_no"></div>
									</v-list-item-subtitle>
									<v-list-item-subtitle v-if="item.address_type">
										<div v-html="item.address_type"></div>
									</v-list-item-subtitle>
								</v-list-item>
							</template>
						</v-autocomplete>
					</v-col>

					<!-- Additional Notes (if enabled in POS profile) -->
					<v-col cols="12" v-if="pos_profile.posa_display_additional_notes">
						<v-textarea
							class="pa-0 dark-field sleek-field"
							variant="solo"
							density="compact"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							clearable
							color="primary"
							auto-grow
							rows="2"
							:label="frappe._('Additional Notes')"
							v-model="invoice_doc.posa_notes"
						></v-textarea>
					</v-col>
				</v-row>

				<!-- Customer Purchase Order (if enabled in POS profile) -->
				<div v-if="pos_profile.posa_allow_customer_purchase_order">
					<v-divider></v-divider>
					<v-row class="pa-1" justify="center" align="start">
						<v-col cols="6">
							<v-text-field
								v-model="invoice_doc.po_no"
								:label="frappe._('Purchase Order')"
								variant="solo"
								density="compact"
								:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
								class="dark-field sleek-field"
								clearable
								color="primary"
								hide-details
							></v-text-field>
						</v-col>
						<v-col cols="6">
							<VueDatePicker
								v-model="new_po_date"
								model-type="format"
								format="dd-MM-yyyy"
								:min-date="new Date()"
								auto-apply
								:dark="isDarkTheme"
								class="dark-field sleek-field"
								@update:model-value="update_po_date()"
							/>
							<v-text-field
								v-model="invoice_doc.po_date"
								:label="frappe._('Purchase Order Date')"
								readonly
								variant="solo"
								density="compact"
								hide-details
								color="primary"
							></v-text-field>
						</v-col>
					</v-row>
				</div>

				<v-divider></v-divider>

				<!-- Switches for Write Off and Credit Sale -->
				<v-row class="pa-1" align="start" no-gutters>
					<v-col
						cols="6"
						v-if="
							pos_profile.posa_allow_write_off_change &&
							credit_change > 0 &&
							!invoice_doc.is_return
						"
					>
						<v-switch
							v-model="is_write_off_change"
							flat
							:label="frappe._('Write Off Difference Amount')"
							class="my-0 pa-1"
						></v-switch>
					</v-col>
					<v-col cols="6" v-if="pos_profile.posa_allow_credit_sale && !invoice_doc.is_return">
						<v-switch v-model="is_credit_sale" :label="frappe._('Credit Sale?')"></v-switch>
					</v-col>
					<v-col cols="6" v-if="invoice_doc.is_return && pos_profile.use_cashback">
						<v-switch
							v-model="is_cashback"
							flat
							:label="frappe._('Cashback?')"
							class="my-0 pa-1"
						></v-switch>
					</v-col>
					<v-col cols="6" v-if="invoice_doc.is_return">
						<v-switch
							v-model="is_credit_return"
							flat
							:label="frappe._('Credit Return?')"
							class="my-0 pa-1"
						></v-switch>
					</v-col>
					<v-col cols="6" v-if="is_credit_sale">
						<VueDatePicker
							v-model="new_credit_due_date"
							model-type="format"
							format="dd-MM-yyyy"
							:min-date="new Date()"
							auto-apply
							:dark="isDarkTheme"
							class="dark-field sleek-field"
							@update:model-value="update_credit_due_date()"
						/>
						<v-text-field
							class="mt-2 dark-field sleek-field"
							density="compact"
							variant="solo"
							type="number"
							min="0"
							max="365"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							v-model.number="credit_due_days"
							:label="frappe._('Days until due')"
							hide-details
							@change="applyDuePreset(credit_due_days)"
						></v-text-field>
						<div class="mt-1">
							<v-chip
								v-for="d in credit_due_presets"
								:key="d"
								size="small"
								class="ma-1"
								variant="solo"
								color="primary"
								@click="applyDuePreset(d)"
							>
								{{ d }} {{ frappe._("days") }}
							</v-chip>
						</div>
					</v-col>
					<v-col cols="6" v-if="!invoice_doc.is_return && pos_profile.use_customer_credit">
						<v-switch
							v-model="redeem_customer_credit"
							flat
							:label="frappe._('Use Customer Credit')"
							class="my-0 pa-1"
							@update:model-value="get_available_credit(redeem_customer_credit)"
						></v-switch>
					</v-col>
				</v-row>

				<!-- Customer Credit Details -->
				<div
					v-if="
						invoice_doc &&
						available_customer_credit > 0 &&
						!invoice_doc.is_return &&
						redeem_customer_credit
					"
				>
					<v-row v-for="(row, idx) in customer_credit_dict" :key="idx">
						<v-col cols="4">
							<div class="pa-2 py-3">{{ row.credit_origin }}</div>
						</v-col>
						<v-col cols="4">
							<v-text-field
								density="compact"
								variant="solo"
								color="primary"
								:label="frappe._('Available Credit')"
								:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
								class="dark-field sleek-field"
								hide-details
								:model-value="formatCurrency(row.total_credit)"
								readonly
								:prefix="currencySymbol(invoice_doc.currency)"
							></v-text-field>
						</v-col>
						<v-col cols="4">
							<v-text-field
								density="compact"
								variant="solo"
								color="primary"
								:label="frappe._('Redeem Credit')"
								:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
								class="dark-field sleek-field"
								hide-details
								type="text"
								:model-value="formatCurrency(row.credit_to_redeem)"
								@change="setFormatedCurrency(row, 'credit_to_redeem', null, false, $event)"
								:prefix="currencySymbol(invoice_doc.currency)"
							></v-text-field>
						</v-col>
					</v-row>
				</div>

				<v-divider></v-divider>

				<!-- Sales Person Selection - ẩn tạm thời, có thể sử dụng sau -->
				<v-row class="pb-0 mb-2" align="start" v-if="false">
					<v-col cols="12">
						<p v-if="sales_persons && sales_persons.length > 0" class="mt-1 mb-1 text-subtitle-2">
							{{ sales_persons.length }} sales persons found
						</p>
						<p v-else class="mt-1 mb-1 text-subtitle-2 text-red">No sales persons found</p>
						<v-select
							density="compact"
							clearable
							variant="solo"
							color="primary"
							:label="frappe._('Sales Person')"
							v-model="sales_person"
							:items="sales_persons"
							item-title="title"
							item-value="value"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							:no-data-text="__('Sales Person not found')"
							hide-details
							:disabled="readonly"
						></v-select>
					</v-col>
				</v-row>
			</div>
		</v-card>

		<!-- Action Buttons -->
		<v-card flat class="cards mb-0 mt-3 pa-0">
			<v-row align="start" no-gutters>
				<!-- IN HOA ĐƠN 1 (hidden for Vietnam) -->
				<v-col cols="6" v-if="!isVietnamCountry">
					<v-btn
						block
						size="large"
						color="primary"
						theme="dark"
						@click="submit(undefined, false, true, false)"
						:loading="loading"
						:disabled="loading || vaildatPayment"
					>
						{{ __("IN HOA ĐƠN 1") }}
					</v-btn>
				</v-col>
				<!-- IN HOA ĐƠN 2 (hidden for Vietnam) -->
				<v-col cols="6" class="pl-1" v-if="!isVietnamCountry">
					<v-btn
						block
						size="large"
						color="success"
						theme="dark"
						@click="submit(undefined, false, true, true)"
						:loading="loading"
						:disabled="loading || vaildatPayment"
					>
						{{ __("IN HOA ĐƠN 2") }}
					</v-btn>
				</v-col>
				<!-- THANH TOÁN VN (shown for Vietnam) -->
				<v-col cols="6" v-if="isVietnamCountry">
					<v-btn
						block
						size="large"
						color="success"
						theme="dark"
						@click="submit(undefined, false, false, true)"
						:loading="loading"
						:disabled="loading || vaildatPayment"
					>
						{{ __("THANH TOÁN VN 1") }}
					</v-btn>
				</v-col>
				<!-- THANH TOÁN VN (shown for Vietnam) -->
				<v-col cols="6" class="pl-1" v-if="isVietnamCountry">
					<v-btn
						block
						size="large"
						color="primary"
						theme="dark"
						@click="submit(undefined, false, false, false)"
						:loading="loading"
						:disabled="loading || vaildatPayment"
					>
						{{ __("THANH TOÁN VN 2") }}
					</v-btn>
				</v-col>
				<v-col cols="12">
					<v-btn
						block
						class="mt-2 pa-1"
						size="large"
						color="error"
						theme="dark"
						@click="back_to_invoice"
					>
						{{ __("Cancel Payment") }}
					</v-btn>
				</v-col>
			</v-row>
		</v-card>
		<!-- Custom Days Dialog -->
		<v-dialog v-model="custom_days_dialog" max-width="300px">
			<v-card>
				<v-card-title class="text-h6">
					{{ __("Custom Due Days") }}
				</v-card-title>
				<v-card-text class="pa-0">
					<v-container>
						<v-text-field
							density="compact"
							variant="solo"
							type="number"
							min="0"
							max="365"
							class="dark-field sleek-field"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							v-model.number="custom_days_value"
							:label="frappe._('Days')"
							hide-details
						></v-text-field>
					</v-container>
				</v-card-text>
				<v-card-actions>
					<v-spacer></v-spacer>
					<v-btn color="error" theme="dark" @click="custom_days_dialog = false">
						{{ __("Close") }}
					</v-btn>
					<v-btn color="primary" theme="dark" @click="applyCustomDays">
						{{ __("Apply") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Phone Payment Dialog -->
		<v-dialog v-model="phone_dialog" max-width="400px">
			<v-card>
				<v-card-title>
					<span class="text-h5 text-primary">{{ __("Confirm Mobile Number") }}</span>
				</v-card-title>
				<v-card-text class="pa-0">
					<v-container>
						<v-text-field
							density="compact"
							variant="solo"
							color="primary"
							:label="frappe._('Mobile Number')"
							:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
							class="dark-field sleek-field"
							hide-details
							v-model="invoice_doc.contact_mobile"
							type="number"
						></v-text-field>
					</v-container>
				</v-card-text>
				<v-card-actions>
					<v-spacer></v-spacer>
					<v-btn color="error" theme="dark" @click="phone_dialog = false">
						{{ __("Close") }}
					</v-btn>
					<v-btn color="primary" theme="dark" @click="request_payment">
						{{ __("Request") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</div>
</template>

<script>
/* eslint-disable vue/no-dupe-keys */
// Importing format mixin for currency and utility functions
import format from "../../format";
import {
	saveOfflineInvoice,
	syncOfflineInvoices,
	getPendingOfflineInvoiceCount,
	isOffline,
	getSalesPersonsStorage,
	setSalesPersonsStorage,
	updateLocalStock,
} from "../../../offline/index.js";

import generateOfflineInvoiceHTML from "../../../offline_print_template";
import { silentPrint } from "../../plugins/print.js";

export default {
	// Using format mixin for shared formatting methods
	mixins: [format],
	data() {
		return {
			loading: false, // UI loading state
			pos_profile: "", // POS profile settings
			pos_settings: "", // POS settings
			invoice_doc: "", // Current invoice document
			invoiceType: "Invoice", // Type of invoice
			is_return: false, // Is this a return invoice?
			loyalty_amount: 0, // Loyalty points to redeem
			redeemed_customer_credit: 0, // Customer credit to redeem
			credit_change: 0, // Change to be given as credit
			paid_change: 0, // Change to be given as paid
			is_credit_sale: false, // Is this a credit sale?
			is_write_off_change: false, // Write-off for change enabled
			is_cashback: true, // Cashback enabled
			is_credit_return: false, // Is this a credit return?
			redeem_customer_credit: false, // Redeem customer credit?
			customer_credit_dict: [], // List of available customer credits
			paid_change_rules: [], // Validation rules for paid change
			phone_dialog: false, // Show phone payment dialog
			custom_days_dialog: false, // Show custom days dialog
			custom_days_value: null, // Custom days entry
			new_delivery_date: null, // New delivery date value
			new_po_date: null, // New PO date value
			new_credit_due_date: null, // New credit due date value
			credit_due_days: null, // Number of days until due
			credit_due_presets: [7, 14, 30], // Preset options for due days
			customer_info: "", // Customer info
			mpesa_modes: [], // List of available M-Pesa modes
			sales_persons: [], // List of sales persons
			sales_person: "", // Selected sales person
			addresses: [], // List of customer addresses
			is_user_editing_paid_change: false, // User interaction flag
		};
	},
	computed: {
		// Check if POS profile country is Vietnam
		isVietnamCountry() {
			return (
				this.pos_profile &&
				(this.pos_profile.country === "VN" || this.pos_profile.country === "Vietnam")
			);
		},
		// Get currency symbol for given or current currency
		currencySymbol() {
			return (currency) => {
				return get_currency_symbol(currency || this.invoice_doc.currency);
			};
		},
		// Display currency for invoice
		displayCurrency() {
			return this.invoice_doc ? this.invoice_doc.currency : "";
		},
		// Calculate total payments (all methods, loyalty, credit)
		total_payments() {
			let total = 0;
			if (this.invoice_doc && this.invoice_doc.payments) {
				this.invoice_doc.payments.forEach((payment) => {
					// Payment amount is already in selected currency
					total += parseFloat(payment.amount) || 0;
				});
			}

			// Add loyalty amount (convert if needed)
			if (this.loyalty_amount) {
				// Loyalty points are stored in base currency (PKR)
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					// Convert to selected currency (e.g. USD) by dividing
					total += this.flt(
						this.loyalty_amount / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				} else {
					total += parseFloat(this.loyalty_amount) || 0;
				}
			}

			// Add redeemed customer credit (convert if needed)
			if (this.redeemed_customer_credit) {
				// Customer credit is stored in base currency (PKR)
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					// Convert to selected currency (e.g. USD) by dividing
					total += this.flt(
						this.redeemed_customer_credit / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				} else {
					total += parseFloat(this.redeemed_customer_credit) || 0;
				}
			}

			return this.flt(total, this.currency_precision);
		},

		// Calculate difference between invoice total and payments
		diff_payment() {
			if (!this.invoice_doc) return 0;

			// For multi-currency, use grand_total instead of rounded_total
			let invoice_total;
			if (
				this.pos_profile.posa_allow_multi_currency &&
				this.invoice_doc.currency !== this.pos_profile.currency
			) {
				invoice_total = this.flt(this.invoice_doc.grand_total, this.currency_precision);
			} else {
				invoice_total = this.flt(
					this.invoice_doc.rounded_total || this.invoice_doc.grand_total,
					this.currency_precision,
				);
			}

			// Calculate difference (all amounts are in selected currency)
			let diff = this.flt(invoice_total - this.total_payments, this.currency_precision);

			// For returns, ensure difference is not negative
			if (this.invoice_doc.is_return) {
				return diff >= 0 ? diff : 0;
			}

			return diff >= 0 ? diff : 0;
		},

		// Calculate change to be given back to customer
		credit_change() {
			// For multi-currency, use grand_total instead of rounded_total
			let invoice_total;
			if (
				this.pos_profile.posa_allow_multi_currency &&
				this.invoice_doc.currency !== this.pos_profile.currency
			) {
				invoice_total = this.flt(this.invoice_doc.grand_total, this.currency_precision);
			} else {
				invoice_total = this.flt(
					this.invoice_doc.rounded_total || this.invoice_doc.grand_total,
					this.currency_precision,
				);
			}

			// Calculate change (all amounts are in selected currency)
			let change = this.flt(this.total_payments - invoice_total, this.currency_precision);

			// Ensure change is not negative
			return change > 0 ? change : 0;
		},

		// Label for the difference field (To Be Paid/Change)
		diff_label() {
			return this.diff_payment > 0
				? `To Be Paid (${this.displayCurrency})`
				: `Change (${this.displayCurrency})`;
		},
		// Display formatted total payments
		total_payments_display() {
			return this.formatCurrency(this.total_payments, this.displayCurrency);
		},
		// Display formatted difference payment
		diff_payment_display() {
			return this.formatCurrency(this.diff_payment, this.displayCurrency);
		},
		// Calculate available loyalty points amount in selected currency
		available_points_amount() {
			let amount = 0;
			if (this.customer_info.loyalty_points) {
				// Convert loyalty points to amount in base currency (PKR)
				amount = this.customer_info.loyalty_points * this.customer_info.conversion_factor;

				// Convert to selected currency if needed
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					// Convert PKR to USD by dividing
					amount = this.flt(
						amount / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				}
			}
			return amount;
		},
		// Calculate total available customer credit
		available_customer_credit() {
			return this.customer_credit_dict.reduce((total, row) => total + this.flt(row.total_credit), 0);
		},
		// Validate if payment can be submitted
		vaildatPayment() {
			if (this.pos_profile.posa_allow_sales_order) {
				if (this.invoiceType === "Order" && !this.invoice_doc.posa_delivery_date) {
					return true;
				}
			}
			return false;
		},
		// Should request payment field be shown?
		request_payment_field() {
			return (
				this.pos_settings?.invoice_fields?.some(
					(el) => el.fieldtype === "Button" && el.fieldname === "request_for_payment",
				) || false
			);
		},
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
	},
	watch: {
		// Watch diff_payment to update paid_change
		diff_payment(newVal) {
			if (!this.is_user_editing_paid_change) {
				this.paid_change = -newVal;
			}
		},
		// Watch paid_change to validate and update credit_change
		paid_change(newVal) {
			const changeLimit = -this.diff_payment;
			if (newVal > changeLimit) {
				this.paid_change = changeLimit;
				this.credit_change = 0;
				this.paid_change_rules = ["Paid change can not be greater than total change!"];
			} else {
				this.paid_change_rules = [];
				this.credit_change = this.flt(newVal - changeLimit, this.currency_precision);
			}
		},
		// Watch loyalty_amount to handle loyalty points redemption
		loyalty_amount(value) {
			if (value > this.available_points_amount) {
				this.invoice_doc.loyalty_amount = 0;
				this.invoice_doc.redeem_loyalty_points = 0;
				this.invoice_doc.loyalty_points = 0;
				this.loyalty_amount = 0;
				this.eventBus.emit("show_message", {
					title: `Loyalty Amount can not be more than ${this.available_points_amount}`,
					color: "error",
				});
			} else {
				this.invoice_doc.loyalty_amount = this.flt(this.loyalty_amount);
				this.invoice_doc.redeem_loyalty_points = 1;
				this.invoice_doc.loyalty_points =
					this.flt(this.loyalty_amount) / this.customer_info.conversion_factor;
			}
		},
		// Watch redeemed_customer_credit to validate
		redeemed_customer_credit(newVal) {
			if (newVal > this.available_customer_credit) {
				this.redeemed_customer_credit = this.available_customer_credit;
				this.eventBus.emit("show_message", {
					title: `You can redeem customer credit up to ${this.available_customer_credit}`,
					color: "error",
				});
			}
		},
		// Recalculate total redeemed credit whenever credit entries change
		customer_credit_dict: {
			handler(newVal) {
				const total = newVal.reduce((sum, row) => sum + this.flt(row.credit_to_redeem || 0), 0);
				this.redeemed_customer_credit = this.flt(total, this.currency_precision);
			},
			deep: true,
		},
		// Watch sales_person to update sales_team
		sales_person(newVal) {
			if (newVal) {
				this.invoice_doc.sales_team = [
					{
						sales_person: newVal,
						allocated_percentage: 100,
					},
				];
				console.log("Updated sales_team with sales_person:", newVal);
			} else {
				this.invoice_doc.sales_team = [];
				console.log("Cleared sales_team");
			}
		},
		// Watch is_credit_sale to reset cash payments
		is_credit_sale(newVal) {
			if (newVal) {
				// If credit sale is enabled, set cash payment to 0
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.mode_of_payment.toLowerCase() === "cash") {
						payment.amount = 0;
					}
				});
			} else {
				// If credit sale is disabled, set cash payment to invoice total
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.mode_of_payment.toLowerCase() === "cash") {
						payment.amount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
					}
				});
			}
		},
		// Watch is_credit_return to toggle cashback payments
		is_credit_return(newVal) {
			if (newVal) {
				this.is_cashback = false;
				// Clear any payment amounts
				this.invoice_doc.payments.forEach((payment) => {
					payment.amount = 0;
					if (payment.base_amount !== undefined) {
						payment.base_amount = 0;
					}
				});
			} else {
				this.is_cashback = true;
				// Ensure default negative payment for returns
				this.ensureReturnPaymentsAreNegative();
			}
		},
		// Watch payment amounts for changes (for debugging payment switching)
		"invoice_doc.payments": {
			handler(newPayments, oldPayments) {
				if (newPayments && oldPayments) {
					console.log("🔄 [PAYMENT WATCH] Payments array changed:");
					newPayments.forEach((payment, index) => {
						const oldPayment = oldPayments[index];
						if (oldPayment && payment.amount !== oldPayment.amount) {
							console.log(
								`   Payment ${index} (${payment.mode_of_payment}): ${oldPayment.amount} → ${payment.amount}`,
							);
						}
					});
				}
			},
			deep: true,
			immediate: false,
		},
	},
	methods: {
		// Go back to invoice view and reset customer readonly
		back_to_invoice() {
			this.eventBus.emit("show_payment", "false");
			this.eventBus.emit("set_customer_readonly", false);
		},
		// Reset all cash payments to zero
		reset_cash_payments() {
			this.invoice_doc.payments.forEach((payment) => {
				if (payment.mode_of_payment.toLowerCase() === "cash") {
					payment.amount = 0;
				}
			});
		},
		// Ensure all payments are negative for return invoices
		ensureReturnPaymentsAreNegative() {
			if (!this.invoice_doc || !this.invoice_doc.is_return || !this.is_cashback) {
				return;
			}
			// Check if any payment amount is set
			let hasPaymentSet = false;
			this.invoice_doc.payments.forEach((payment) => {
				if (Math.abs(payment.amount) > 0) {
					hasPaymentSet = true;
				}
			});
			// If no payment set, set the default one
			if (!hasPaymentSet) {
				const default_payment = this.invoice_doc.payments.find((payment) => payment.default === 1);
				if (default_payment) {
					const amount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
					default_payment.amount = -Math.abs(amount);
					if (default_payment.base_amount !== undefined) {
						default_payment.base_amount = -Math.abs(amount);
					}
				}
			}
			// Ensure all set payments are negative
			this.invoice_doc.payments.forEach((payment) => {
				if (payment.amount > 0) {
					payment.amount = -Math.abs(payment.amount);
				}
				if (payment.base_amount !== undefined && payment.base_amount > 0) {
					payment.base_amount = -Math.abs(payment.base_amount);
				}
			});
		},
		submit(event, payment_received = false, print = false, tax = false) {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Submit Payment Start
			console.log(
				`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_PAYMENT_START - Invoice: ${this.invoice_doc?.name}, User: ${frappe.session.user}, Print: ${print}, Tax: ${tax}`,
			);

			// CHẶN DOUBLE-SUBMIT
			if (this.loading) {
				console.warn(
					`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_PAYMENT_WARNING - Double submit prevented for invoice: ${this.invoice_doc?.name}`,
				);
				return;
			}

			// For return invoices, ensure payment amounts are negative
			if (this.invoice_doc.is_return) {
				this.ensureReturnPaymentsAreNegative();
			}
			// Validate total payments only if not credit sale and invoice total is not zero
			if (
				!this.is_credit_sale &&
				!this.invoice_doc.is_return &&
				this.total_payments <= 0 &&
				(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
			) {
				this.eventBus.emit("show_message", {
					title: `Please enter payment amount`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate cash payments when credit sale is off
			if (!this.is_credit_sale && !this.invoice_doc.is_return) {
				let has_cash_payment = false;
				let cash_amount = 0;
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.mode_of_payment.toLowerCase().includes("cash")) {
						has_cash_payment = true;
						cash_amount = this.flt(payment.amount);
					}
				});
				if (has_cash_payment && cash_amount > 0) {
					if (
						!this.pos_profile.posa_allow_partial_payment &&
						cash_amount < (this.invoice_doc.rounded_total || this.invoice_doc.grand_total) &&
						(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
					) {
						this.eventBus.emit("show_message", {
							title: `Cash payment cannot be less than invoice total when partial payment is not allowed`,
							color: "error",
						});
						frappe.utils.play_sound("error");
						return;
					}
				}
			}
			// Validate partial payments only if not credit sale and invoice total is not zero
			if (
				!this.is_credit_sale &&
				!this.pos_profile.posa_allow_partial_payment &&
				this.total_payments < (this.invoice_doc.rounded_total || this.invoice_doc.grand_total) &&
				(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
			) {
				this.eventBus.emit("show_message", {
					title: `The amount paid is not complete`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate phone payment
			let phone_payment_is_valid = true;
			if (!payment_received) {
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.type === "Phone" && ![0, "0", "", null, undefined].includes(payment.amount)) {
						phone_payment_is_valid = false;
					}
				});
				if (!phone_payment_is_valid) {
					this.eventBus.emit("show_message", {
						title: __("Please request phone payment or use another payment method"),
						color: "error",
					});
					frappe.utils.play_sound("error");
					return;
				}
			}
			// Validate paid_change
			if (this.paid_change > -this.diff_payment) {
				this.eventBus.emit("show_message", {
					title: `Paid change cannot be greater than total change!`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate cashback
			let total_change = this.flt(this.flt(this.paid_change) + this.flt(-this.credit_change));
			if (this.is_cashback && total_change !== -this.diff_payment) {
				this.eventBus.emit("show_message", {
					title: `Error in change calculations!`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate customer credit redemption
			let credit_calc_check = this.customer_credit_dict.filter((row) => {
				return this.flt(row.credit_to_redeem) > this.flt(row.total_credit);
			});
			if (credit_calc_check.length > 0) {
				this.eventBus.emit("show_message", {
					title: `Redeemed credit cannot be greater than its total.`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			if (
				!this.invoice_doc.is_return &&
				this.redeemed_customer_credit >
					(this.invoice_doc.rounded_total || this.invoice_doc.grand_total)
			) {
				this.eventBus.emit("show_message", {
					title: `Cannot redeem customer credit more than invoice total`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}

			// ✅ Tới đây mới bật loading & gọi submit_invoice
			this.loading = true;
			this.submit_invoice(print, tax);
		},
		submit_invoice(print, tax) {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Submit Invoice Start
			console.log(
				`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_INVOICE_START - Invoice: ${this.invoice_doc?.name}, User: ${frappe.session.user}, Print: ${print}, Tax: ${tax}`,
			);

			// === BƯỚC 1: CHUẨN BỊ DỮ LIỆU ===
			if (this.invoice_doc.is_return) {
				this.ensureReturnPaymentsAreNegative();
			}

			const data = {
				total_change: !this.invoice_doc.is_return ? -this.diff_payment : 0,
				paid_change: !this.invoice_doc.is_return ? this.paid_change : 0,
				credit_change: -this.credit_change,
				redeemed_customer_credit: this.redeemed_customer_credit,
				customer_credit_dict: this.customer_credit_dict,
				is_cashback: this.is_cashback,
			};

			if (print) this.invoice_doc.posa_is_printed = true;
			if (tax) this.invoice_doc.tax_report = true;

			const vm = this;
			const original_invoice_doc = { ...this.invoice_doc };

			// Detailed client-side logging before sending to server
			console.log(`[CLIENT_DEBUG] 📤 CLIENT SENDING INVOICE TO SERVER - DETAILED LOG:`);
			console.log(`[CLIENT_DEBUG] 📊 REQUEST METADATA:`);
			console.log(`[CLIENT_DEBUG] 📊   - Timestamp: ${new Date().toISOString()}`);
			console.log(`[CLIENT_DEBUG] 📊   - User: ${frappe.session.user}`);
			console.log(
				`[CLIENT_DEBUG] 📊   - Action: submit_invoice (${print ? "print" : "no_print"}, ${tax ? "tax" : "no_tax"})`,
			);

			console.log(`[CLIENT_DEBUG] 📋 BASIC INVOICE INFO:`);
			console.log(`[CLIENT_DEBUG] 📋   - Name: ${this.invoice_doc?.name || "New Invoice"}`);
			console.log(`[CLIENT_DEBUG] 📋   - Customer: ${this.invoice_doc?.customer}`);
			console.log(`[CLIENT_DEBUG] 📋   - Company: ${this.invoice_doc?.company}`);
			console.log(`[CLIENT_DEBUG] 📋   - POS Profile: ${this.invoice_doc?.pos_profile}`);
			console.log(`[CLIENT_DEBUG] 📋   - Currency: ${this.invoice_doc?.currency}`);
			console.log(`[CLIENT_DEBUG] 📋   - Grand Total: ${this.invoice_doc?.grand_total}`);
			console.log(`[CLIENT_DEBUG] 📋   - Is Return: ${this.invoice_doc?.is_return}`);
			console.log(`[CLIENT_DEBUG] 📋   - Posting Date: ${this.invoice_doc?.posting_date}`);

			console.log(`[CLIENT_DEBUG] 📦 ITEMS DETAILS:`);
			if (this.invoice_doc?.items?.length > 0) {
				console.log(`[CLIENT_DEBUG] 📦   - Items Count: ${this.invoice_doc.items.length}`);
				this.invoice_doc.items.slice(0, 3).forEach((item, i) => {
					console.log(`[CLIENT_DEBUG] 📦   - Item ${i + 1}:`);
					console.log(`[CLIENT_DEBUG] 📦     * item_code: ${item.item_code}`);
					console.log(`[CLIENT_DEBUG] 📦     * item_name: ${item.item_name}`);
					console.log(`[CLIENT_DEBUG] 📦     * qty: ${item.qty}`);
					console.log(`[CLIENT_DEBUG] 📦     * rate: ${item.rate}`);
					console.log(`[CLIENT_DEBUG] 📦     * amount: ${item.amount}`);
					console.log(`[CLIENT_DEBUG] 📦     * uom: ${item.uom}`);
					console.log(`[CLIENT_DEBUG] 📦     * posa_row_id: ${item.posa_row_id}`);
					console.log(
						`[CLIENT_DEBUG] 📦     * posa_offers: ${item.posa_offers} (type: ${typeof item.posa_offers})`,
					);
					console.log(`[CLIENT_DEBUG] 📦     * posa_offer_applied: ${item.posa_offer_applied}`);
					console.log(`[CLIENT_DEBUG] 📦     * discount_amount: ${item.discount_amount}`);
					console.log(`[CLIENT_DEBUG] 📦     * discount_percentage: ${item.discount_percentage}`);
				});
				if (this.invoice_doc.items.length > 3) {
					console.log(
						`[CLIENT_DEBUG] 📦   - ... and ${this.invoice_doc.items.length - 3} more items`,
					);
				}
			} else {
				console.log(`[CLIENT_DEBUG] 📦   - No items in invoice`);
			}

			console.log(`[CLIENT_DEBUG] 💳 PAYMENTS DETAILS:`);
			if (this.invoice_doc?.payments?.length > 0) {
				console.log(`[CLIENT_DEBUG] 💳   - Payments Count: ${this.invoice_doc.payments.length}`);
				this.invoice_doc.payments.forEach((payment, i) => {
					console.log(`[CLIENT_DEBUG] 💳   - Payment ${i + 1}:`);
					console.log(`[CLIENT_DEBUG] 💳     * mode_of_payment: ${payment.mode_of_payment}`);
					console.log(`[CLIENT_DEBUG] 💳     * amount: ${payment.amount}`);
					console.log(`[CLIENT_DEBUG] 💳     * base_amount: ${payment.base_amount}`);
					console.log(`[CLIENT_DEBUG] 💳     * type: ${payment.type}`);
				});
			} else {
				console.log(`[CLIENT_DEBUG] 💳   - No payments in invoice`);
			}

			console.log(`[CLIENT_DEBUG] 🎫 POS OFFERS DETAILS:`);
			if (this.invoice_doc?.posa_offers?.length > 0) {
				console.log(`[CLIENT_DEBUG] 🎫   - Offers Count: ${this.invoice_doc.posa_offers.length}`);
				this.invoice_doc.posa_offers.slice(0, 2).forEach((offer, i) => {
					console.log(`[CLIENT_DEBUG] 🎫   - Offer ${i + 1}:`);
					console.log(`[CLIENT_DEBUG] 🎫     * name: ${offer.name}`);
					console.log(`[CLIENT_DEBUG] 🎫     * title: ${offer.title}`);
					console.log(`[CLIENT_DEBUG] 🎫     * discount_type: ${offer.discount_type}`);
					console.log(`[CLIENT_DEBUG] 🎫     * rate: ${offer.rate}`);
					console.log(`[CLIENT_DEBUG] 🎫     * discount_percentage: ${offer.discount_percentage}`);
					console.log(`[CLIENT_DEBUG] 🎫     * items: ${offer.items}`);
				});
				if (this.invoice_doc.posa_offers.length > 2) {
					console.log(
						`[CLIENT_DEBUG] 🎫   - ... and ${this.invoice_doc.posa_offers.length - 2} more offers`,
					);
				}
			} else {
				console.log(`[CLIENT_DEBUG] 🎫   - No POS offers in invoice`);
			}

			console.log(`[CLIENT_DEBUG] 📋 PAYMENT SUBMIT DATA:`, data);
			console.log(`[CLIENT_DEBUG] 📋 INVOICE DOC KEYS:`, Object.keys(this.invoice_doc || {}));
			console.log(`[CLIENT_DEBUG] ✅ CLIENT LOGGING COMPLETED - Sending to server`);

			console.log(
				`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_INVOICE_PROCESS - Prepared data for invoice: ${this.invoice_doc?.name}`,
			);

			// === BƯỚC 2: GỌI SERVER ===
			const req = frappe.call({
				method:
					this.invoiceType === "Order" && this.pos_profile.posa_create_only_sales_order
						? "posawesome.posawesome.api.sales_orders.submit_sales_order"
						: "posawesome.posawesome.api.invoices.submit_invoice",
				args: {
					data: data,
					invoice: original_invoice_doc,
					order: original_invoice_doc,
				},
				callback: async function (r) {
					// Đưa việc tắt loading vào finally/.always để “an toàn tuyệt đối”

					// Xử lý lỗi phản hồi
					if (r.exc || !r.message || !r.message.name) {
						console.error("Error submitting invoice:", r.exc || "Invalid response from server");
						vm.eventBus.emit("show_message", {
							title: __("Error submitting invoice: ") + (r.exc || "Invalid response"),
							color: "error",
						});
						return;
					}

					// === BƯỚC 3: BUILD ĐỐI TƯỢNG HÓA ĐƠN HOÀN CHỈNH ===
					const invoice_to_print = {
						...original_invoice_doc,
						name: r.message.name,
					};

					console.log(
						`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_INVOICE_SUCCESS - Invoice submitted successfully: ${invoice_to_print.name}`,
					);

					// Thông báo & cập nhật
					vm.eventBus.emit("show_message", {
						title: __("Invoice {0} is Submitted", [invoice_to_print.name]),
						color: "success",
					});
					frappe.utils.play_sound("submit");
					vm.eventBus.emit("set_last_invoice", invoice_to_print.name);
					vm.eventBus.emit("update_sales_data"); // Trigger footer refresh
					updateLocalStock(invoice_to_print.items || []);

					// === BƯỚC 4: IN (NẾU CẦN) ===
					try {
						if (print && tax) {
							vm.load_print_page(invoice_to_print);
							await vm.load_print_page_tax(invoice_to_print);
						} else if (print) {
							vm.load_print_page(invoice_to_print);
						}
						// ✅ CẬP NHẬT FOOTER STATUS BAR SAU KHI IN THÀNH CÔNG
						vm.eventBus.emit("update_sales_data");
					} catch (printError) {
						console.error("Printing process failed after submission:", printError);
						vm.eventBus.emit("show_message", {
							title:
								__("Invoice submitted, but printing failed: ") +
								(printError?.message || printError),
							color: "error",
						});
					}

					// === BƯỚC 5: DỌN DẸP ===
					vm.customer_credit_dict = [];
					vm.redeem_customer_credit = false;
					vm.is_cashback = true;
					vm.is_credit_return = false;
					vm.sales_person = "";
					vm.addresses = [];
					vm.eventBus.emit("clear_invoice");
					vm.back_to_invoice();
				},
			});

			// === BẢO HIỂM: LUÔN TẮT LOADING DÙ CÓ GÌ XẢY RA ===
			if (req && typeof req.always === "function") {
				// Trường hợp frappe.call trả về jqXHR (có .always/.fail)
				req.always(() => {
					vm.loading = false;
				});
			} else {
				// Trường hợp frappe.call trả về Promise
				Promise.resolve(req)
					.catch(() => {}) // để .finally vẫn chạy
					.finally(() => {
						vm.loading = false;
					});
			}
		},
		// Load print page for invoice

		// Submit invoice and handle printing
		// Submit payment after validation
		// submit(event, payment_received = false, print = false, tax = false ) {
		// 	// For return invoices, ensure payment amounts are negative
		// 	if (this.invoice_doc.is_return) {
		// 		this.ensureReturnPaymentsAreNegative();
		// 	}
		// 	// Validate total payments only if not credit sale and invoice total is not zero
		// 	if (
		// 		!this.is_credit_sale &&
		// 		!this.invoice_doc.is_return &&
		// 		this.total_payments <= 0 &&
		// 		(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
		// 	) {
		// 		this.eventBus.emit("show_message", {
		// 			title: `Please enter payment amount`,
		// 			color: "error",
		// 		});
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}
		// 	// Validate cash payments when credit sale is off
		// 	if (!this.is_credit_sale && !this.invoice_doc.is_return) {
		// 		let has_cash_payment = false;
		// 		let cash_amount = 0;
		// 		this.invoice_doc.payments.forEach((payment) => {
		// 			if (payment.mode_of_payment.toLowerCase().includes("cash")) {
		// 				has_cash_payment = true;
		// 				cash_amount = this.flt(payment.amount);
		// 			}
		// 		});
		// 		if (has_cash_payment && cash_amount > 0) {
		// 			if (
		// 				!this.pos_profile.posa_allow_partial_payment &&
		// 				cash_amount < (this.invoice_doc.rounded_total || this.invoice_doc.grand_total) &&
		// 				(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
		// 			) {
		// 				this.eventBus.emit("show_message", {
		// 					title: `Cash payment cannot be less than invoice total when partial payment is not allowed`,
		// 					color: "error",
		// 				});
		// 				frappe.utils.play_sound("error");
		// 				return;
		// 			}
		// 		}
		// 	}
		// 	// Validate partial payments only if not credit sale and invoice total is not zero
		// 	if (
		// 		!this.is_credit_sale &&
		// 		!this.pos_profile.posa_allow_partial_payment &&
		// 		this.total_payments < (this.invoice_doc.rounded_total || this.invoice_doc.grand_total) &&
		// 		(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
		// 	) {
		// 		this.eventBus.emit("show_message", {
		// 			title: `The amount paid is not complete`,
		// 			color: "error",
		// 		});
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}
		// 	// Validate phone payment
		// 	let phone_payment_is_valid = true;
		// 	if (!payment_received) {
		// 		this.invoice_doc.payments.forEach((payment) => {
		// 			if (payment.type === "Phone" && ![0, "0", "", null, undefined].includes(payment.amount)) {
		// 				phone_payment_is_valid = false;
		// 			}
		// 		});
		// 		if (!phone_payment_is_valid) {
		// 			this.eventBus.emit("show_message", {
		// 				title: __("Please request phone payment or use another payment method"),
		// 				color: "error",
		// 			});
		// 			frappe.utils.play_sound("error");
		// 			return;
		// 		}
		// 	}
		// 	// Validate paid_change
		// 	if (this.paid_change > -this.diff_payment) {
		// 		this.eventBus.emit("show_message", {
		// 			title: `Paid change cannot be greater than total change!`,
		// 			color: "error",
		// 		});
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}
		// 	// Validate cashback
		// 	let total_change = this.flt(this.flt(this.paid_change) + this.flt(-this.credit_change));
		// 	if (this.is_cashback && total_change !== -this.diff_payment) {
		// 		this.eventBus.emit("show_message", {
		// 			title: `Error in change calculations!`,
		// 			color: "error",
		// 		});
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}
		// 	// Validate customer credit redemption
		// 	let credit_calc_check = this.customer_credit_dict.filter((row) => {
		// 		return this.flt(row.credit_to_redeem) > this.flt(row.total_credit);
		// 	});
		// 	if (credit_calc_check.length > 0) {
		// 		this.eventBus.emit("show_message", {
		// 			title: `Redeemed credit cannot be greater than its total.`,
		// 			color: "error",
		// 		});
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}
		// 	if (
		// 		!this.invoice_doc.is_return &&
		// 		this.redeemed_customer_credit >
		// 			(this.invoice_doc.rounded_total || this.invoice_doc.grand_total)
		// 	) {
		// 		this.eventBus.emit("show_message", {
		// 			title: `Cannot redeem customer credit more than invoice total`,
		// 			color: "error",
		// 		});
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}
		// 	// Proceed to submit the invoice
		// 	this.loading = true;
		// 	this.submit_invoice(print , tax);
		// },
		// Submit invoice to backend after all validations
		// submit_invoice(print , tax) {
		// 	// For return invoices, ensure payments are negative one last time
		// 	if (this.invoice_doc.is_return) {
		// 		this.ensureReturnPaymentsAreNegative();
		// 	}
		// 	let totalPayedAmount = 0;
		// 	this.invoice_doc.payments.forEach((payment) => {
		// 		payment.amount = this.flt(payment.amount);
		// 		totalPayedAmount += payment.amount;
		// 	});
		// 	if (this.invoice_doc.is_return && totalPayedAmount === 0) {
		// 		this.invoice_doc.is_pos = 0;
		// 	}
		// 	if (this.customer_credit_dict.length) {
		// 		this.customer_credit_dict.forEach((row) => {
		// 			row.credit_to_redeem = this.flt(row.credit_to_redeem);
		// 		});
		// 	}
		// 	let data = {
		// 		total_change: !this.invoice_doc.is_return ? -this.diff_payment : 0,
		// 		paid_change: !this.invoice_doc.is_return ? this.paid_change : 0,
		// 		credit_change: -this.credit_change,
		// 		redeemed_customer_credit: this.redeemed_customer_credit,
		// 		customer_credit_dict: this.customer_credit_dict,
		// 		is_cashback: this.is_cashback,
		// 	};
		// 	if (print) {
		// 		this.invoice_doc.posa_is_printed = true;
		// 	}
		// 	if (tax) {
		// 		this.invoice_doc.tax_report = true;
		// 	} else if (print) {
		// 		this.invoice_doc.tax_report = false;
		// 	}

		// 	const vm = this;
		// 	if (isOffline()) {
		// 		try {
		// 			saveOfflineInvoice({ data: data, invoice: this.invoice_doc });
		// 			this.eventBus.emit("pending_invoices_changed", getPendingOfflineInvoiceCount());
		// 			vm.eventBus.emit("show_message", {
		// 				title: __("Invoice saved offline"),
		// 				color: "warning",
		// 			});
		// 			if (print) {
		// 				this.print_offline_invoice(this.invoice_doc);
		// 			}
		// 			vm.eventBus.emit("clear_invoice");
		// 			vm.eventBus.emit("reset_posting_date");
		// 			vm.back_to_invoice();
		// 			vm.loading = false;
		// 			return;
		// 		} catch (error) {
		// 			vm.eventBus.emit("show_message", {
		// 				title: __("Cannot Save Offline Invoice: ") + (error.message || __("Unknown error")),
		// 				color: "error",
		// 			});
		// 			vm.loading = false;
		// 			return;
		// 		}
		// 	}
		// 	frappe.call({
		// 		method:
		// 			this.invoiceType === "Order" && this.pos_profile.posa_create_only_sales_order
		// 				? "posawesome.posawesome.api.sales_orders.submit_sales_order"
		// 				: "posawesome.posawesome.api.invoices.submit_invoice",
		// 		args: {
		// 			data: data,
		// 			invoice: this.invoice_doc,
		// 			order: this.invoice_doc,
		// 		},
		// 		callback: function (r) {
		// 			if (r.exc) {
		// 				console.error("Error submitting invoice:", r.exc);
		// 				// Show detailed error message to help debugging
		// 				let errorMsg = r.exc.toString();
		// 				if (errorMsg.includes("Amount must be negative")) {
		// 					vm.eventBus.emit("show_message", {
		// 						title: __("Fixing payment amounts for return invoice..."),
		// 						color: "warning",
		// 					});
		// 					// Force fix the amounts
		// 					vm.invoice_doc.payments.forEach((payment) => {
		// 						if (payment.amount > 0) {
		// 							payment.amount = -Math.abs(payment.amount);
		// 						}
		// 						if (payment.base_amount > 0) {
		// 							payment.base_amount = -Math.abs(payment.base_amount);
		// 						}
		// 					});
		// 					// Retry submission once
		// 					console.log("Retrying submission with fixed payment amounts");
		// 					setTimeout(() => {
		// 						vm.submit_invoice(print);
		// 					}, 500);
		// 				} else {
		// 					vm.eventBus.emit("show_message", {
		// 						title: __("Error submitting invoice: ") + errorMsg,
		// 						color: "error",
		// 					});
		// 				}
		// 				vm.loading = false;
		// 				return;
		// 			}
		// 			if (!r.message) {
		// 				vm.eventBus.emit("show_message", {
		// 					title: __("Error submitting invoice: No response from server"),
		// 					color: "error",
		// 				});
		// 				vm.loading = false;
		// 				return;
		// 			}

		// 			if (print && tax) {
		// 				    console.log(
		// 					"%c CHUẨN BỊ GỌI load_print_page_tax. Dữ liệu this.invoice_doc là:",
		// 					"color: blue; font-weight: bold;", // Style để log nổi bật
		// 					this.invoice_doc
		// 				);
		// 				vm.load_print_page_tax();
		// 			} else if (print) {
		// 				vm.load_print_page();
		// 			}
		// 			vm.customer_credit_dict = [];
		// 			vm.redeem_customer_credit = false;
		// 			vm.is_cashback = true;
		// 			vm.is_credit_return = false;
		// 			vm.sales_person = "";
		// 			vm.eventBus.emit("set_last_invoice", vm.invoice_doc.name);
		// 			vm.eventBus.emit("show_message", {
		// 				title:
		// 					vm.invoiceType === "Order" && vm.pos_profile.posa_create_only_sales_order
		// 						? __("Sales Order {0} is Submitted", [r.message.name])
		// 						: __("Invoice {0} is Submitted", [r.message.name]),
		// 				color: "success",
		// 			});
		// 			frappe.utils.play_sound("submit");
		// 			// Update local stock quantities immediately after successful
		// 			// invoice submission so item availability reflects changes
		// 			updateLocalStock(vm.invoice_doc.items || []);
		// 			vm.addresses = [];
		// 			vm.eventBus.emit("clear_invoice");
		// 			vm.eventBus.emit("reset_posting_date");
		// 			vm.back_to_invoice();
		// 			vm.loading = false;
		// 		},
		// 	});
		// },
		// Set full amount for a payment method (or negative for returns)

		// // Thay thế hàm submit_invoice cũ của bạn bằng hàm này
		// submit_invoice(print, tax) {
		// 	// Bước 1: Chuẩn bị dữ liệu và xử lý các trường hợp đặc biệt (trả hàng, offline)
		// 	if (this.invoice_doc.is_return) {
		// 		this.ensureReturnPaymentsAreNegative();
		// 	}

		// 	// Chuẩn bị dữ liệu bổ sung để gửi lên server
		// 	let data = {
		// 		total_change: !this.invoice_doc.is_return ? -this.diff_payment : 0,
		// 		paid_change: !this.invoice_doc.is_return ? this.paid_change : 0,
		// 		credit_change: -this.credit_change,
		// 		redeemed_customer_credit: this.redeemed_customer_credit,
		// 		customer_credit_dict: this.customer_credit_dict,
		// 		is_cashback: this.is_cashback,
		// 	};

		// 	if (print) this.invoice_doc.posa_is_printed = true;

		// 	// Đánh dấu hóa đơn này là hóa đơn thuế để xử lý backend nếu cần
		// 	if (tax) {
		// 		this.invoice_doc.tax_report = true;
		// 	}

		// 	const vm = this; // Giữ lại 'this' để dùng trong callback

		// 	// // Xử lý trường hợp OFFLINE - disable đi
		// 	// if (isOffline()) {
		// 	// 	try {
		// 	// 		saveOfflineInvoice({ data: data, invoice: this.invoice_doc });
		// 	// 		this.eventBus.emit("pending_invoices_changed", getPendingOfflineInvoiceCount());
		// 	// 		vm.eventBus.emit("show_message", {
		// 	// 			title: __("Invoice saved offline"),
		// 	// 			color: "warning",
		// 	// 		});
		// 	// 		if (print) {
		// 	// 			this.print_offline_invoice(this.invoice_doc);
		// 	// 		}
		// 	// 		// Dọn dẹp sau khi lưu offline
		// 	// 		vm.eventBus.emit("clear_invoice");
		// 	// 		vm.back_to_invoice();
		// 	// 		vm.loading = false;
		// 	// 		return;
		// 	// 	} catch (error) {
		// 	// 		vm.eventBus.emit("show_message", {
		// 	// 			title: __("Cannot Save Offline Invoice: ") + (error.message || __("Unknown error")),
		// 	// 			color: "error",
		// 	// 		});
		// 	// 		vm.loading = false;
		// 	// 		return;
		// 	// 	}
		// 	// }

		// 	// Bước 2: Gửi hóa đơn chính lên server ERPNext
		// 	frappe.call({
		// 		method:
		// 			this.invoiceType === "Order" && this.pos_profile.posa_create_only_sales_order
		// 				? "posawesome.posawesome.api.sales_orders.submit_sales_order"
		// 				: "posawesome.posawesome.api.invoices.submit_invoice",
		// 		args: {
		// 			data: data,
		// 			invoice: this.invoice_doc,
		// 			order: this.invoice_doc,
		// 		},
		// 		callback: async function (r) {
		// 			vm.loading = false; // Luôn tắt loading ở đầu callback

		// 			// Xử lý lỗi từ server
		// 			if (r.exc || !r.message || !r.message.name) {
		// 				console.error("Error submitting invoice:", r.exc || "Invalid response from server");
		// 				vm.eventBus.emit("show_message", {
		// 					title: __("Error submitting invoice: ") + (r.exc || "Invalid response"),
		// 					color: "error",
		// 				});
		// 				return;
		// 			}

		// 			// Bước 3: Lấy đối tượng hóa đơn hoàn chỉnh từ phản hồi của server
		// 			const completed_invoice = r.message;

		// 			// Thông báo thành công cho hóa đơn chính
		// 			vm.eventBus.emit("show_message", {
		// 				title: __("Invoice {0} is Submitted", [completed_invoice.name]),
		// 				color: "success",
		// 			});
		// 			frappe.utils.play_sound("submit");

		// 			// Cập nhật các trạng thái cần thiết
		// 			vm.eventBus.emit("set_last_invoice", completed_invoice.name);
		// 			updateLocalStock(completed_invoice.items || []);

		// 			// Bước 4: Thực hiện in (nếu có) VỚI DỮ LIỆU ĐÃ HOÀN CHỈNH
		// 			try {
		// 				if (print && tax) {
		// 					await vm.load_print_page_tax(completed_invoice);
		// 				} else if (print) {
		// 					vm.load_print_page(completed_invoice);
		// 				}
		// 			} catch (printError) {
		// 				// Nếu quá trình in lỗi, thông báo cho người dùng nhưng không dừng luồng
		// 				console.error("Printing process failed after submission:", printError);
		// 				vm.eventBus.emit("show_message", {
		// 					title: __("Invoice submitted, but printing failed: ") + printError.message,
		// 					color: "error",
		// 				});
		// 			}

		// 			// Bước 5: Dọn dẹp form để chuẩn bị cho giao dịch tiếp theo
		// 			// Luôn thực hiện bước này sau khi tất cả các hành động khác đã hoàn tất.
		// 			vm.customer_credit_dict = [];
		// 			vm.redeem_customer_credit = false;
		// 			vm.is_cashback = true;
		// 			vm.is_credit_return = false;
		// 			vm.sales_person = "";
		// 			vm.addresses = [];
		// 			vm.eventBus.emit("clear_invoice");
		// 			vm.back_to_invoice();
		// 		},
		// 	});
		// },

		// submit_invoice(print, tax) {
		// 	// === BƯỚC 1: CHUẨN BỊ DỮ LIỆU ===
		// 	// Xử lý trường hợp trả hàng
		// 	if (this.invoice_doc.is_return) {
		// 		this.ensureReturnPaymentsAreNegative();
		// 	}

		// 	// Chuẩn bị dữ liệu thanh toán bổ sung để gửi lên server
		// 	const data = {
		// 		total_change: !this.invoice_doc.is_return ? -this.diff_payment : 0,
		// 		paid_change: !this.invoice_doc.is_return ? this.paid_change : 0,
		// 		credit_change: -this.credit_change,
		// 		redeemed_customer_credit: this.redeemed_customer_credit,
		// 		customer_credit_dict: this.customer_credit_dict,
		// 		is_cashback: this.is_cashback,
		// 	};

		// 	// Đánh dấu các cờ in ấn
		// 	if (print) this.invoice_doc.posa_is_printed = true;
		// 	if (tax) this.invoice_doc.tax_report = true;

		// 	const vm = this;

		// 	// Tạo một bản sao đầy đủ của hóa đơn trước khi gửi đi.
		// 	// Điều này rất quan trọng để giữ lại chi tiết hóa đơn cho việc in ấn sau này.
		// 	const original_invoice_doc = { ...this.invoice_doc };

		// 	// === BƯỚC 2: GỬI HÓA ĐƠN CHÍNH LÊN SERVER ERNEXT (LUỒNG ONLINE) ===
		// 	frappe.call({
		// 		method:
		// 			this.invoiceType === "Order" && this.pos_profile.posa_create_only_sales_order
		// 				? "posawesome.posawesome.api.sales_orders.submit_sales_order"
		// 				: "posawesome.posawesome.api.invoices.submit_invoice",
		// 		args: {
		// 			data: data,
		// 			invoice: original_invoice_doc,
		// 			order: original_invoice_doc,
		// 		},
		// 		callback: async function (r) {
		// 			vm.loading = false; // Luôn tắt loading ở đầu callback

		// 			// Xử lý lỗi từ server
		// 			if (r.exc || !r.message || !r.message.name) {
		// 				console.error("Error submitting invoice:", r.exc || "Invalid response from server");
		// 				vm.eventBus.emit("show_message", {
		// 					title: __("Error submitting invoice: ") + (r.exc || "Invalid response"),
		// 					color: "error",
		// 				});
		// 				return;
		// 			}

		// 			// === BƯỚC 3: KẾT HỢP DỮ LIỆU ĐỂ TẠO ĐỐI TƯỢNG HÓA ĐƠN HOÀN CHỈNH ===
		// 			// Lấy TÊN HÓA ĐƠN từ phản hồi của server và kết hợp với dữ liệu gốc
		// 			const invoice_to_print = {
		// 				...original_invoice_doc,
		// 				name: r.message.name
		// 			};

		// 			// Thông báo thành công và cập nhật các trạng thái
		// 			vm.eventBus.emit("show_message", {
		// 				title: __("Invoice {0} is Submitted", [invoice_to_print.name]),
		// 				color: "success",
		// 			});
		// 			frappe.utils.play_sound("submit");
		// 			vm.eventBus.emit("set_last_invoice", invoice_to_print.name);
		// 			updateLocalStock(invoice_to_print.items || []);

		// 			// === BƯỚC 4: THỰC HIỆN IN (NẾU CÓ) VỚI DỮ LIỆU ĐÃ HOÀN CHỈNH ===
		// 			try {
		// 				if (print && tax) {
		// 					vm.load_print_page(invoice_to_print);
		// 					await vm.load_print_page_tax(invoice_to_print);
		// 				} else if (print) {
		// 					vm.load_print_page(invoice_to_print);
		// 				}
		// 			} catch (printError) {
		// 				console.error("Printing process failed after submission:", printError);
		// 				vm.eventBus.emit("show_message", {
		// 					title: __("Invoice submitted, but printing failed: ") + printError.message,
		// 					color: "error",
		// 				});
		// 			}

		// 			// === BƯỚC 5: DỌN DẸP FORM ĐỂ CHUẨN BỊ CHO GIAO DỊCH MỚI ===
		// 			vm.customer_credit_dict = [];
		// 			vm.redeem_customer_credit = false;
		// 			vm.is_cashback = true;
		// 			vm.is_credit_return = false;
		// 			vm.sales_person = "";
		// 			vm.addresses = [];
		// 			vm.eventBus.emit("clear_invoice");
		// 			vm.back_to_invoice();
		// 		},
		// 	});
		// },

		// // Thay thế hàm load_print_page_tax cũ của bạn bằng hàm này
		// async load_print_page_tax(invoice_to_print) { // <-- Sửa để nhận tham số
		// 	// Tải động handler
		// 	const { handleTaxPrint } = await import('./taxPrintHandler.js');
		// 	// === DÒNG DEBUG 2: KIỂM TRA DỮ LIỆU ĐƯỢC TRUYỀN VÀO ===
		// 	console.log(
		// 		"%c load_print_page_tax đang truyền đối tượng sau vào handleTaxPrint:",
		// 		"color: green; font-weight: bold;",
		// 		invoice_to_print
		// 	);

		// 	try {
		// 		await handleTaxPrint(
		// 			invoice_to_print, // <-- Sử dụng đối tượng hóa đơn hoàn chỉnh được truyền vào
		// 			this.pos_profile,
		// 			// onSuccess callback
		// 			(result) => {
		// 				// Bạn có thể cập nhật UI ở đây nếu cần, ví dụ:
		// 				// this.updateHeaderTaxDisplay(result.nextDisplay);
		// 				console.log("Tax print process successful:", result);
		// 			},
		// 			// onError callback
		// 			(error) => {
		// 				// Lỗi từ handleTaxPrint đã được log chi tiết bên trong,
		// 				// ở đây ta chỉ cần hiển thị thông báo cho người dùng.
		// 				console.error("Tax print handler reported an error:", error);
		// 				frappe.msgprint({
		// 					title: "Lỗi In Hóa Đơn Thuế",
		// 					message: `Không thể in hóa đơn thuế: ${error.message}`,
		// 					indicator: "red"
		// 				});
		// 			}
		// 		);
		// 	} catch (error) {
		// 		// Bắt các lỗi không mong muốn (vd: không tải được file handler)
		// 		console.error("An unexpected error occurred in load_print_page_tax:", error);
		// 		frappe.msgprint({
		// 			title: "Lỗi Hệ Thống In",
		// 			message: `Có lỗi không mong đợi xảy ra: ${error.message}`,
		// 			indicator: "red"
		// 		});
		// 		// Ném lỗi ra ngoài để khối try-catch trong submit_invoice có thể bắt được
		// 		throw error;
		// 	}
		// },

		// === REPLACE your old load_print_page_tax with this version ===
		async load_print_page_tax(invoice_or_name) {
			try {
				// 1) Lấy invoice "fresh" từ server để chắc chắn có tax_id do server đã patch
				let invoice_to_print = null;

				// Cho phép truyền vào: object hoặc chỉ name (string)
				const passedName =
					(typeof invoice_or_name === "string" && invoice_or_name) ||
					(invoice_or_name && invoice_or_name.name);

				if (!passedName) {
					console.error(
						"[TaxPrint] load_print_page_tax: thiếu 'name' của invoice!",
						invoice_or_name,
					);
					frappe.msgprint("Không thể in: Thiếu tên hóa đơn (invoice name).");
					return;
				}

				invoice_to_print = await frappe.db.get_doc("Sales Invoice", passedName);

				// 2) TRACE: log các trường quan trọng để debug tax_id
				console.log("%c[TRACE] Fresh invoice từ server:", "color:#0aa; font-weight:bold;", {
					name: invoice_to_print?.name,
					customer: invoice_to_print?.customer,
					tax_id: invoice_to_print?.tax_id,
					customer_tax_id: invoice_to_print?.customer_tax_id,
					remarks: invoice_to_print?.remarks?.slice?.(0, 200) || "",
				});

				// 3) Fallback: nếu vì lý do nào đó vẫn chưa có tax_id, dùng từ customer_info (nếu đang có)
				if (
					!invoice_to_print.tax_id &&
					!invoice_to_print.customer_tax_id &&
					this?.customer_info?.tax_id
				) {
					const fallbackTax = String(this.customer_info.tax_id).trim();
					if (fallbackTax) {
						invoice_to_print.tax_id = fallbackTax;
						invoice_to_print.customer_tax_id = fallbackTax;
						console.warn("[TaxPrint] Fallback gắn tax_id từ customer_info:", fallbackTax);
					}
				}

				// 4) Double-check lần nữa trước khi in
				const resolvedTaxId = String(
					invoice_to_print.tax_id || invoice_to_print.customer_tax_id || "",
				).trim();

				console.log("%c[TRACE] TaxID để in =", "color:#970; font-weight:bold;", resolvedTaxId);

				if (!resolvedTaxId) {
					// Không chặn in, nhưng cảnh báo mạnh để biết lý do
					console.warn(
						"[TaxPrint] CẢNH BÁO: invoice không có tax_id. Nếu yêu cầu in hóa đơn thuế bắt buộc có Tax ID, hãy kiểm tra lại luồng gán tax_id phía server hoặc dữ liệu khách hàng.",
					);
				}

				// 5) Import handler và gọi in - LUỒNG RIÊNG RẼ THEO QUỐC GIA
				const { handleTaxPrint, handleVietnamTaxPrint } = await import("./taxPrintHandler.js");

				if (this.isVietnamCountry) {
					// === LUỒNG VIỆT NAM: Gửi lên MISA API ===
					console.log(
						"%c load_print_page_tax -> handleVietnamTaxPrint (VIỆT NAM):",
						"color: blue; font-weight: bold;",
						{
							name: invoice_to_print?.name,
							customer: invoice_to_print?.customer,
							tax_id: invoice_to_print?.tax_id,
							customer_tax_id: invoice_to_print?.customer_tax_id,
							grand_total: invoice_to_print?.grand_total,
							country: this.pos_profile?.country,
						},
					);

					await handleVietnamTaxPrint(
						invoice_to_print,
						this.pos_profile,
						// onSuccess
						(result) => {
							console.log("[TaxPrint] Vietnam Success:", result);
						},
						// onError
						(error) => {
							console.error("[TaxPrint] Vietnam Handler error:", error);
							frappe.msgprint({
								title: "Lỗi Gửi Hóa Đơn MISA",
								message: `Không thể gửi hóa đơn lên MISA: ${error.message}`,
								indicator: "red",
							});
						},
					);
				} else {
					// === LUỒNG ĐÀI LOAN: In tại chỗ ===
					console.log(
						"%c load_print_page_tax -> handleTaxPrint (ĐÀI LOAN):",
						"color: green; font-weight: bold;",
						{
							name: invoice_to_print?.name,
							customer: invoice_to_print?.customer,
							tax_id: invoice_to_print?.tax_id,
							customer_tax_id: invoice_to_print?.customer_tax_id,
							grand_total: invoice_to_print?.grand_total,
							country: this.pos_profile?.country,
						},
					);

					await handleTaxPrint(
						invoice_to_print,
						this.pos_profile,
						// onSuccess
						(result) => {
							console.log("[TaxPrint] Taiwan Success:", result);
							// Nếu cần cập nhật header: đã có updateHeaderTaxDisplay trong handler
						},
						// onError
						(error) => {
							console.error("[TaxPrint] Taiwan Handler error:", error);
							frappe.msgprint({
								title: "Lỗi In Hóa Đơn Thuế",
								message: `Không thể in hóa đơn thuế: ${error.message}`,
								indicator: "red",
							});
						},
					);
				}

			} catch (error) {
				console.error("[TaxPrint] Unexpected error in load_print_page_tax:", error);
				frappe.msgprint({
					title: "Lỗi Hệ Thống In",
					message: `Có lỗi không mong đợi xảy ra: ${error.message}`,
					indicator: "red",
				});
				// Cho caller biết để xử lý tiếp (nếu cần)
				throw error;
			}
		},

		/**
		 * Mở trang in tiêu chuẩn của Frappe cho một hóa đơn đã hoàn chỉnh.
		 * @param {object} invoice_to_print - Đối tượng hóa đơn hoàn chỉnh (có .name) cần in.
		 */
		load_print_page(invoice_to_print) {
			console.log(
				"%c load_print_page_tax đang truyền đối tượng sau vào handleTaxPrint:",
				"color: green; font-weight: bold;",
				invoice_to_print,
			);
			// === SỬA LỖI: Thêm bước kiểm tra dữ liệu đầu vào ===
			if (!invoice_to_print || !invoice_to_print.name) {
				console.error("load_print_page was called with an invalid invoice object.", invoice_to_print);
				frappe.msgprint("Không thể in: Dữ liệu hóa đơn không hợp lệ.");
				return;
			}

			const print_format = this.pos_profile.print_format_for_online || this.pos_profile.print_format;
			const letter_head = this.pos_profile.letter_head || 0;

			// === SỬA LỖI: Sử dụng 'invoice_to_print.name' thay vì 'this.invoice_doc.name' ===
			const url =
				frappe.urllib.get_base_url() +
				"/printview?doctype=Sales%20Invoice&name=" +
				invoice_to_print.name + // <-- SỬA LỖI Ở ĐÂY
				"&trigger_print=1" +
				"&format=" +
				print_format +
				"&no_letterhead=" +
				letter_head;

			if (this.pos_profile.posa_silent_print) {
				silentPrint(url);
			} else {
				const printWindow = window.open(url, "Print");
				// Thêm kiểm tra để tránh lỗi nếu popup bị chặn
				if (printWindow) {
					printWindow.addEventListener(
						"load",
						function () {
							printWindow.print();
						},
						{ once: true },
					);
				} else {
					frappe.msgprint("Trình duyệt đã chặn cửa sổ in. Vui lòng cho phép pop-up.");
				}
			}
		},
		// Set full amount for a payment method when clicked

		// set_full_amount(idx, ev) {
		// 	// [SHIFT_CLOSE_WORKFLOW] Vue Component - Set Full Amount Start
		// 	console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_SET_FULL_AMOUNT_START - Invoice: ${this.invoice_doc?.name}, Payment idx: ${idx}, User: ${frappe.session.user}`);

		// 	console.log("🔄 [PAYMENT] set_full_amount called with idx:", idx);
		// 	console.log("📋 [PAYMENT] Event object:", ev);
		// 	console.log("📄 [PAYMENT] Current invoice_doc:", {
		// 		name: this.invoice_doc?.name,
		// 		is_return: this.invoice_doc?.is_return,
		// 		invoiceType: this.invoiceType,
		// 		rounded_total: this.invoice_doc?.rounded_total,
		// 		grand_total: this.invoice_doc?.grand_total,
		// 		currency: this.invoice_doc?.currency
		// 	});

		// 	const isReturn = this.invoice_doc.is_return || this.invoiceType === "Return";
		// 	const totalAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;

		// 	console.log("💰 [PAYMENT] Calculated values:", {
		// 		isReturn,
		// 		totalAmount,
		// 		currency: this.invoice_doc?.currency
		// 	});

		// 	// Reset all payment amounts trước
		// 	console.log("🔄 [PAYMENT] Resetting all payment amounts...");
		// 	let resetCount = 0;
		// 	this.invoice_doc.payments.forEach((payment, index) => {
		// 		const oldAmount = payment.amount;
		// 		const oldBaseAmount = payment.base_amount;

		// 		console.log(`💸 [PAYMENT] Resetting payment ${index}:`, {
		// 			idx: payment.idx,
		// 			mode_of_payment: payment.mode_of_payment,
		// 			old_amount: oldAmount,
		// 			old_base_amount: oldBaseAmount,
		// 			has_base_amount: payment.hasOwnProperty('base_amount')
		// 		});

		// 		// Ensure we're setting to exactly 0
		// 		payment.amount = 0;
		// 		if (payment.hasOwnProperty('base_amount')) {
		// 			payment.base_amount = 0;
		// 		}

		// 		// Track changes
		// 		if (oldAmount !== 0 || (oldBaseAmount !== undefined && oldBaseAmount !== 0)) {
		// 			resetCount++;
		// 		}
		// 	});
		// 	console.log(`✅ [PAYMENT] Reset ${resetCount} payments with non-zero amounts`);

		// 	// Tìm payment theo idx (ổn định hơn text nút)
		// 	console.log("🔍 [PAYMENT] Finding payment with idx:", idx);
		// 	const clickedPayment = this.invoice_doc.payments.find((p) => p.idx === idx);

		// 	if (clickedPayment) {
		// 		console.log("✅ [PAYMENT] Found clicked payment:", {
		// 			idx: clickedPayment.idx,
		// 			mode_of_payment: clickedPayment.mode_of_payment,
		// 			type: clickedPayment.type,
		// 			default: clickedPayment.default
		// 		});

		// 		let amount = isReturn ? -Math.abs(totalAmount) : totalAmount;
		// 		console.log("💵 [PAYMENT] Setting amount:", {
		// 			original_total: totalAmount,
		// 			isReturn,
		// 			calculated_amount: amount,
		// 			will_be_negative: isReturn
		// 		});

		// 		clickedPayment.amount = amount;
		// 		if (clickedPayment.hasOwnProperty('base_amount')) {
		// 			clickedPayment.base_amount = isReturn ? -Math.abs(amount) : amount;
		// 			console.log("🔄 [PAYMENT] Set base_amount:", clickedPayment.base_amount);
		// 		}

		// 		console.log("✅ [PAYMENT] Final payment state:", {
		// 			idx: clickedPayment.idx,
		// 			mode_of_payment: clickedPayment.mode_of_payment,
		// 			amount: clickedPayment.amount,
		// 			base_amount: clickedPayment.base_amount
		// 		});

		// 		// Trigger reactive update
		// 		this.$nextTick(() => {
		// 			console.log("🔄 [PAYMENT] Triggering reactive update...");

		// 			// Force update computed properties
		// 			this.$forceUpdate();

		// 			// Emit event để update totals
		// 			this.eventBus.emit("payment_amount_changed");
		// 			console.log("📢 [PAYMENT] Emitted payment_amount_changed event");

		// 			// Additional reactive triggers
		// 			this.$emit('payment-updated', {
		// 				payment_idx: idx,
		// 				amount: clickedPayment.amount,
		// 				mode_of_payment: clickedPayment.mode_of_payment
		// 			});

		// 			console.log("📊 [PAYMENT] Current totals after update:", {
		// 				total_payments: this.total_payments,
		// 				diff_payment: this.diff_payment,
		// 				credit_change: this.credit_change
		// 			});
		// 		});

		// 	} else {
		// 		console.error("❌ [PAYMENT] No payment found for idx:", idx);
		// 		console.log("📋 [PAYMENT] Available payments:", this.invoice_doc.payments.map(p => ({
		// 			idx: p.idx,
		// 			mode_of_payment: p.mode_of_payment
		// 		})));

		// 		this.eventBus.emit("show_message", {
		// 			title: __("Payment method not found"),
		// 			color: "error"
		// 		});
		// 	}

		// 	// Log final state of all payments
		// 	console.log("📊 [PAYMENT] Final state of all payments:");
		// 	this.invoice_doc.payments.forEach((payment, index) => {
		// 		console.log(`   ${index}: ${payment.mode_of_payment} (idx: ${payment.idx}) = ${payment.amount}`);
		// 	});

		// 	// Force Vue update khi cần
		// 	this.$forceUpdate();
		// 	console.log("🔄 [PAYMENT] Forced Vue update completed");
		// },

		set_full_amount(idx) {
			const isReturn = this.invoice_doc.is_return || this.invoiceType === "Return";
			let totalAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;

			console.log("Setting full amount for payment method idx:", idx);
			console.log("Current payments:", JSON.stringify(this.invoice_doc.payments));

			// Reset all payment amounts first
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = 0;
				if (payment.base_amount !== undefined) {
					payment.base_amount = 0;
				}
			});

			// Get the clicked payment method's name from the button text
			const clickedButton = event?.target?.textContent?.trim();
			console.log("Clicked button text:", clickedButton);

			// Set amount only for clicked payment method
			const clickedPayment = this.invoice_doc.payments.find(
				(payment) => payment.mode_of_payment === clickedButton,
			);

			if (clickedPayment) {
				console.log("Found clicked payment:", clickedPayment.mode_of_payment);
				let amount = isReturn ? -Math.abs(totalAmount) : totalAmount;
				clickedPayment.amount = amount;
				if (clickedPayment.base_amount !== undefined) {
					clickedPayment.base_amount = isReturn ? -Math.abs(amount) : amount;
				}
				console.log("Set amount for payment:", clickedPayment.mode_of_payment, "amount:", amount);
			} else {
				console.log("No payment found for button text:", clickedButton);
			}

			// Force Vue to update the view
			this.$forceUpdate();
		},

		// Set remaining amount for a payment method when focused
		set_rest_amount(idx) {
			const isReturn = this.invoice_doc.is_return || this.invoiceType === "Return";
			this.invoice_doc.payments.forEach((payment) => {
				if (payment.idx === idx && payment.amount === 0 && this.diff_payment > 0) {
					let amount = this.diff_payment;
					if (isReturn) {
						amount = -Math.abs(amount);
					}
					payment.amount = amount;
					if (payment.base_amount !== undefined) {
						payment.base_amount = isReturn ? -Math.abs(amount) : amount;
					}
				}
			});
		},
		// Clear all payment amounts
		clear_all_amounts() {
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = 0;
			});
		},
		// Debug method to log current payment state
		// Usage in browser console:
		// 1. Find Payments component: document.querySelector('[data-component="payments"]')
		// 2. Get Vue instance: vm = $0.__vue__
		// 3. Call debug: vm.debugPayments()
		debugPayments() {
			console.log("🐛 [DEBUG] Current Payment State:");
			console.log("📄 Invoice:", {
				name: this.invoice_doc?.name,
				total: this.invoice_doc?.grand_total,
				is_return: this.invoice_doc?.is_return,
				currency: this.invoice_doc?.currency,
			});

			console.log("💰 Payments Array:");
			this.invoice_doc.payments.forEach((payment, index) => {
				console.log(`   ${index}: ${payment.mode_of_payment}`, {
					idx: payment.idx,
					amount: payment.amount,
					base_amount: payment.base_amount,
					type: payment.type,
					default: payment.default,
				});
			});

			console.log("📊 Calculated Values:", {
				total_payments: this.total_payments,
				diff_payment: this.diff_payment,
				credit_change: this.credit_change,
				isReturn: this.invoice_doc?.is_return || this.invoiceType === "Return",
			});

			return {
				invoice: this.invoice_doc,
				payments: this.invoice_doc.payments,
				totals: {
					total_payments: this.total_payments,
					diff_payment: this.diff_payment,
					credit_change: this.credit_change,
				},
			};
		},
		// Open print page for invoice
		// load_print_page() {
		// 	const print_format = this.pos_profile.print_format_for_online || this.pos_profile.print_format;
		// 	const letter_head = this.pos_profile.letter_head || 0;
		// 	const url =
		// 		frappe.urllib.get_base_url() +
		// 		"/printview?doctype=Sales%20Invoice&name=" +
		// 		this.invoice_doc.name +
		// 		"&trigger_print=1" +
		// 		"&format=" +
		// 		print_format +
		// 		"&no_letterhead=" +
		// 		letter_head;
		// 	if (this.pos_profile.posa_silent_print) {
		// 		silentPrint(url);
		// 	} else {
		// 		const printWindow = window.open(url, "Print");
		// 		printWindow.addEventListener(
		// 			"load",
		// 			function () {
		// 				printWindow.print();
		// 			},
		// 			{ once: true },
		// 		);
		// 	}
		// },

		// async load_print_page_tax() {
		// 	// Import tax print handler
		// 	const { handleTaxPrint } = await import('./taxPrintHandler.js');

		// 	try {
		// 		await handleTaxPrint(
		// 			this.invoice_doc,
		// 			this.pos_profile,
		// 			// onSuccess callback
		// 			(result) => {
		// 				// Thông báo thành công
		// 				frappe.show_alert({
		// 					message: `Đã in thành công hóa đơn thuế: ${result.taxCode}`,
		// 					indicator: "green"
		// 				});
		// 			},
		// 			// onError callback
		// 			(error) => {
		// 				console.error("Lỗi in hóa đơn thuế:", error);
		// 				frappe.msgprint({
		// 					title: "Lỗi In Hóa Đơn Thuế",
		// 					message: `Không thể in hóa đơn thuế: ${error.message}`,
		// 					indicator: "red"
		// 				});
		// 			}
		// 		);
		// 	} catch (error) {
		// 		console.error("Lỗi không mong đợi:", error);
		// 		frappe.msgprint({
		// 			title: "Lỗi In Hóa Đơn Thuế",
		// 			message: `Có lỗi không mong đợi xảy ra: ${error.message}`,
		// 			indicator: "red"
		// 		});
		// 	}
		// },

		// async load_print_page_tax() {
		// 	// Import tax print handler
		// 	const { handleTaxPrint } = await import('./taxPrintHandler.js');

		// 	// === CẢI TIẾN: Thêm trạng thái chờ ===
		// 	this.loading = true; // Giả sử component có một biến data 'loading'
		// 	// Vô hiệu hóa các nút khác nếu cần
		// 	        // === DÒNG DEBUG 2: KIỂM TRA DỮ LIỆU ĐƯỢC TRUYỀN VÀO ===
		// 	console.log(
		// 		"%c load_print_page_tax đang truyền đối tượng sau vào handleTaxPrint:",
		// 		"color: green; font-weight: bold;",
		// 		this.invoice_doc
		// 	);
		// 	console.log(
		// 		"%c load_print_page_tax đang truyền đối tượng Pos-Profile sau vào handleTaxPrint:",
		// 		"color: green; font-weight: bold;",
		// 		this.pos_profile
		// 	);

		// 	try {
		// 		await handleTaxPrint(
		// 			this.invoice_doc,
		// 			this.pos_profile,
		// 			// onSuccess callback
		// 			(result) => {
		// 				frappe.show_alert({
		// 					message: `Đã in thành công hóa đơn thuế: ${result.taxCode}`,
		// 					indicator: "green"
		// 				});
		// 			},
		// 			// onError callback
		// 			(error) => {
		// 				console.error("Lỗi in hóa đơn thuế:", error);
		// 				frappe.msgprint({
		// 					title: "Lỗi In Hóa Đơn Thuế",
		// 					message: `Không thể in hóa đơn thuế: ${error.message}`,
		// 					indicator: "red"
		// 				});
		// 			}
		// 		);
		// 	} catch (error) {
		// 		console.error("Lỗi không mong đợi:", error);
		// 		frappe.msgprint({
		// 			title: "Lỗi In Hóa Đơn Thuế",
		// 			message: `Có lỗi không mong đợi xảy ra: ${error.message}`,
		// 			indicator: "red"
		// 		});
		// 	} finally {
		// 		// === CẢI TIẾN: Luôn tắt trạng thái chờ sau khi hoàn tất ===
		// 		this.loading = false;
		// 		// Bật lại các nút khác
		// 	}
		// },

		// Print invoice using a more detailed offline template
		print_offline_invoice(invoice) {
			if (!invoice) return;
			const html = generateOfflineInvoiceHTML(invoice);
			const win = window.open("", "_blank");
			win.document.write(html);
			win.document.close();
			win.focus();
			win.print();
		},
		// Validate due date (should not be in the past)
		validate_due_date() {
			const today = frappe.datetime.now_date();
			const new_date = Date.parse(this.invoice_doc.due_date);
			const parse_today = Date.parse(today);
			if (new_date < parse_today) {
				this.invoice_doc.due_date = today;
			}
		},
		// Keyboard shortcut for payment submit (Ctrl+X)
		shortPay(e) {
			if (e.key.toLowerCase() === "x" && (e.ctrlKey || e.metaKey)) {
				e.preventDefault();
				e.stopPropagation();
				if (this.invoice_doc && this.invoice_doc.payments) {
					this.submit_invoice();
				}
			}
		},
		// Get available customer credit and auto-allocate
		get_available_credit(use_credit) {
			this.clear_all_amounts();
			if (use_credit) {
				frappe
					.call("posawesome.posawesome.api.payments.get_available_credit", {
						customer: this.invoice_doc.customer,
						company: this.pos_profile.company,
					})
					.then((r) => {
						const data = r.message;
						if (data.length) {
							const amount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
							let remainAmount = amount;
							data.forEach((row) => {
								if (remainAmount > 0) {
									if (remainAmount >= row.total_credit) {
										row.credit_to_redeem = row.total_credit;
										remainAmount -= row.total_credit;
									} else {
										row.credit_to_redeem = remainAmount;
										remainAmount = 0;
									}
								} else {
									row.credit_to_redeem = 0;
								}
							});
							this.customer_credit_dict = data;
						} else {
							this.customer_credit_dict = [];
						}
					});
			} else {
				this.customer_credit_dict = [];
			}
		},
		// Get customer addresses for shipping
		get_addresses() {
			const vm = this;
			if (!vm.invoice_doc || !vm.invoice_doc.customer) {
				vm.addresses = [];
				return;
			}
			frappe.call({
				method: "posawesome.posawesome.api.customers.get_customer_addresses",
				args: { customer: vm.invoice_doc.customer },
				async: true,
				callback: function (r) {
					if (!r.exc) {
						vm.addresses = r.message;
					} else {
						vm.addresses = [];
					}
				},
			});
		},
		// Filter addresses for autocomplete
		addressFilter(item, queryText, itemText) {
			const searchText = queryText.toLowerCase();
			return (
				(item.address_title && item.address_title.toLowerCase().includes(searchText)) ||
				(item.address_line1 && item.address_line1.toLowerCase().includes(searchText)) ||
				(item.address_line2 && item.address_line2.toLowerCase().includes(searchText)) ||
				(item.city && item.city.toLowerCase().includes(searchText)) ||
				(item.name && item.name.toLowerCase().includes(searchText))
			);
		},
		// Open dialog to add new address
		new_address() {
			if (!this.invoice_doc || !this.invoice_doc.customer) {
				this.eventBus.emit("show_message", {
					title: __("Please select a customer first"),
					color: "error",
				});
				return;
			}
			this.eventBus.emit("open_new_address", this.invoice_doc.customer);
		},
		// Get sales person names from API/localStorage
		get_sales_person_names() {
			const vm = this;
			if (vm.pos_profile.posa_local_storage && getSalesPersonsStorage().length) {
				try {
					vm.sales_persons = getSalesPersonsStorage();
				} catch (e) {}
			}
			frappe.call({
				method: "posawesome.posawesome.api.utilities.get_sales_person_names",
				callback: function (r) {
					if (r.message && r.message.length > 0) {
						vm.sales_persons = r.message.map((sp) => ({
							value: sp.name,
							title: sp.sales_person_name,
							sales_person_name: sp.sales_person_name,
							name: sp.name,
						}));
						if (vm.pos_profile.posa_local_storage) {
							setSalesPersonsStorage(vm.sales_persons);
						}
					} else {
						vm.sales_persons = [];
					}
				},
			});
		},
		// Request payment for phone type
		request_payment(payment) {
			this.phone_dialog = false;
			const vm = this;
			if (!this.invoice_doc.contact_mobile) {
				this.eventBus.emit("show_message", {
					title: __("Please set the customer's mobile number"),
					color: "error",
				});
				this.eventBus.emit("open_edit_customer");
				this.back_to_invoice();
				return;
			}
			this.eventBus.emit("freeze", { title: __("Waiting for payment...") });
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = this.flt(payment.amount);
			});
			let formData = { ...this.invoice_doc };
			formData["total_change"] = !this.invoice_doc.is_return ? -this.diff_payment : 0;
			formData["paid_change"] = !this.invoice_doc.is_return ? this.paid_change : 0;
			formData["credit_change"] = -this.credit_change;
			formData["redeemed_customer_credit"] = this.redeemed_customer_credit;
			formData["customer_credit_dict"] = this.customer_credit_dict;
			formData["is_cashback"] = this.is_cashback;
			frappe
				.call({
					method: "posawesome.posawesome.api.invoices.update_invoice",
					args: { data: formData },
					async: false,
					callback: function (r) {
						if (r.message) {
							vm.invoice_doc = r.message;
						}
					},
				})
				.then(() => {
					frappe
						.call({
							method: "posawesome.posawesome.api.payments.create_payment_request",
							args: { doc: vm.invoice_doc },
						})
						.fail(() => {
							vm.eventBus.emit("unfreeze");
							vm.eventBus.emit("show_message", {
								title: __("Payment request failed"),
								color: "error",
							});
						})
						.then(({ message }) => {
							const payment_request_name = message.name;
							setTimeout(() => {
								frappe.db
									.get_value("Payment Request", payment_request_name, [
										"status",
										"grand_total",
									])
									.then(({ message }) => {
										if (message.status !== "Paid") {
											vm.eventBus.emit("unfreeze");
											vm.eventBus.emit("show_message", {
												title: __(
													"Payment Request took too long to respond. Please try requesting for payment again",
												),
												color: "error",
											});
										} else {
											vm.eventBus.emit("unfreeze");
											vm.eventBus.emit("show_message", {
												title: __("Payment of {0} received successfully.", [
													vm.formatCurrency(
														message.grand_total,
														vm.invoice_doc.currency,
														0,
													),
												]),
												color: "success",
											});
											frappe.db
												.get_doc("Sales Invoice", vm.invoice_doc.name)
												.then((doc) => {
													vm.invoice_doc = doc;
													vm.submit(null, true);
												});
										}
									});
							}, 30000);
						});
				});
		},
		// Get M-Pesa payment modes from backend
		get_mpesa_modes() {
			const vm = this;
			frappe.call({
				method: "posawesome.posawesome.api.m_pesa.get_mpesa_mode_of_payment",
				args: { company: vm.pos_profile.company },
				async: true,
				callback: function (r) {
					if (!r.exc) {
						vm.mpesa_modes = r.message;
					} else {
						vm.mpesa_modes = [];
					}
				},
			});
		},
		// Check if payment is M-Pesa C2B
		is_mpesa_c2b_payment(payment) {
			if (this.mpesa_modes.includes(payment.mode_of_payment) && payment.type === "Bank") {
				payment.amount = 0;
				return true;
			} else {
				return false;
			}
		},
		// Open M-Pesa payment dialog
		mpesa_c2b_dialog(payment) {
			const data = {
				company: this.pos_profile.company,
				mode_of_payment: payment.mode_of_payment,
				customer: this.invoice_doc.customer,
			};
			this.eventBus.emit("open_mpesa_payments", data);
		},
		// Set M-Pesa payment as customer credit
		set_mpesa_payment(payment) {
			this.pos_profile.use_customer_credit = true;
			this.redeem_customer_credit = true;
			const invoiceAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
			let amount =
				payment.unallocated_amount > invoiceAmount ? invoiceAmount : payment.unallocated_amount;
			amount = amount > 0 ? amount : 0;
			const advance = {
				type: "Advance",
				credit_origin: payment.name,
				total_credit: this.flt(payment.unallocated_amount),
				credit_to_redeem: this.flt(amount),
			};
			this.clear_all_amounts();
			this.customer_credit_dict.push(advance);
		},
		// Update delivery date after selection
		update_delivery_date() {
			this.invoice_doc.posa_delivery_date = this.formatDate(this.new_delivery_date);
			// After setting delivery date, fetch addresses if not already loaded
			if (this.invoice_doc.customer && (!this.addresses || this.addresses.length === 0)) {
				this.get_addresses();
			}
		},
		// Update purchase order date after selection
		update_po_date() {
			this.invoice_doc.po_date = this.formatDate(this.new_po_date);
		},
		// Update credit due date after selection
		update_credit_due_date() {
			this.invoice_doc.due_date = this.formatDate(this.new_credit_due_date);
		},
		// Apply preset or typed number of days to set due date
		applyDuePreset(days) {
			if (days === null || days === "" || isNaN(days)) {
				return;
			}
			const d = new Date();
			d.setDate(d.getDate() + parseInt(days, 10));
			this.new_credit_due_date = this.formatDateDisplay(d);
			this.credit_due_days = parseInt(days, 10);
			this.update_credit_due_date();
		},
		// Apply days entered in dialog
		applyCustomDays() {
			this.applyDuePreset(this.custom_days_value);
			this.custom_days_dialog = false;
		},
		// Format date to YYYY-MM-DD
		formatDate(date) {
			if (!date) return null;
			if (typeof date === "string") {
				if (/^\d{4}-\d{2}-\d{2}$/.test(date)) {
					return date;
				}
				if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(date)) {
					const [d, m, y] = date.split("-");
					return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
				}
			}
			const d = new Date(date);
			if (!isNaN(d.getTime())) {
				const year = d.getFullYear();
				const month = `0${d.getMonth() + 1}`.slice(-2);
				const day = `0${d.getDate()}`.slice(-2);
				return `${year}-${month}-${day}`;
			}
			return date;
		},

		formatDateDisplay(date) {
			if (!date) return "";
			if (typeof date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
				const [y, m, d] = date.split("-");
				return `${d}-${m}-${y}`;
			}
			const d = new Date(date);
			if (!isNaN(d.getTime())) {
				const year = d.getFullYear();
				const month = `0${d.getMonth() + 1}`.slice(-2);
				const day = `0${d.getDate()}`.slice(-2);
				return `${day}-${month}-${year}`;
			}
			return date;
		},
		// Show paid amount info message
		showPaidAmount() {
			this.eventBus.emit("show_message", {
				title: `Total Paid Amount: ${this.formatCurrency(this.total_payments)}`,
				color: "info",
			});
		},
		// Show diff payment info message
		showDiffPayment() {
			if (!this.invoice_doc) return;
			this.eventBus.emit("show_message", {
				title: `To Be Paid: ${this.formatCurrency(this.diff_payment)}`,
				color: "info",
			});
		},
		// Show paid change info message
		showPaidChange() {
			this.eventBus.emit("show_message", {
				title: `Paid Change: ${this.formatCurrency(this.paid_change)}`,
				color: "info",
			});
		},
		// Show credit change info message
		showCreditChange(value) {
			if (value > 0) {
				this.credit_change = value;
				this.paid_change = -this.diff_payment;
			} else {
				this.credit_change = 0;
			}
		},
		// Format currency value
		formatCurrency(value) {
			return this.$options.mixins[0].methods.formatCurrency.call(this, value, this.currency_precision);
		},
		// Get change amount for display
		get_change_amount() {
			return Math.max(0, this.total_payments - this.invoice_doc.grand_total);
		},
		// Sync any invoices stored offline and show pending/synced counts
		async syncPendingInvoices() {
			const pending = getPendingOfflineInvoiceCount();
			if (pending) {
				this.eventBus.emit("show_message", {
					title: `${pending} invoice${pending > 1 ? "s" : ""} pending for sync`,
					color: "warning",
				});
				this.eventBus.emit("pending_invoices_changed", pending);
			}
			if (isOffline()) {
				// Don't attempt to sync while offline; just update the counter
				return;
			}
			const result = await syncOfflineInvoices();
			if (result && (result.synced || result.drafted)) {
				if (result.synced) {
					this.eventBus.emit("show_message", {
						title: `${result.synced} offline invoice${result.synced > 1 ? "s" : ""} synced`,
						color: "success",
					});
				}
				if (result.drafted) {
					this.eventBus.emit("show_message", {
						title: `${result.drafted} offline invoice${result.drafted > 1 ? "s" : ""} saved as draft`,
						color: "warning",
					});
				}
			}
			this.eventBus.emit("pending_invoices_changed", getPendingOfflineInvoiceCount());
		},
	},
	// Lifecycle hook: created
	created() {
		// Register keyboard shortcut for payment
		document.addEventListener("keydown", this.shortPay.bind(this));
		this.syncPendingInvoices();
		this.eventBus.on("network-online", this.syncPendingInvoices);
		// Also sync when the server connection is re-established
		this.eventBus.on("server-online", this.syncPendingInvoices);
	},
	// Lifecycle hook: mounted
	mounted() {
		this.$nextTick(() => {
			// Listen to various event bus events for POS actions
			this.eventBus.on("send_invoice_doc_payment", (invoice_doc) => {
				this.invoice_doc = invoice_doc;
				const default_payment = this.invoice_doc.payments.find((payment) => payment.default === 1);
				this.is_credit_sale = false;
				this.is_write_off_change = false;
				if (invoice_doc.is_return) {
					this.is_return = true;
					this.is_credit_return = false;
					// Reset all payment amounts to zero for returns
					invoice_doc.payments.forEach((payment) => {
						payment.amount = 0;
						payment.base_amount = 0;
					});
					// Set default payment to negative amount for returns
					if (default_payment) {
						const amount = invoice_doc.rounded_total || invoice_doc.grand_total;
						default_payment.amount = -Math.abs(amount);
						if (default_payment.base_amount !== undefined) {
							default_payment.base_amount = -Math.abs(amount);
						}
					}
				} else if (default_payment) {
					// For regular invoices, set positive amount
					default_payment.amount = this.flt(
						invoice_doc.rounded_total || invoice_doc.grand_total,
						this.currency_precision,
					);
					this.is_credit_return = false;
				}
				this.loyalty_amount = 0;
				this.redeemed_customer_credit = 0;
				// Only get addresses if customer exists
				if (invoice_doc.customer) {
					this.get_addresses();
				}
				this.get_sales_person_names();
			});
			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
				this.get_mpesa_modes();
			});
			this.eventBus.on("add_the_new_address", (data) => {
				this.addresses.push(data);
				this.$forceUpdate();
			});
			this.eventBus.on("update_invoice_type", (data) => {
				this.invoiceType = data;
				if (this.invoice_doc && data !== "Order") {
					this.invoice_doc.posa_delivery_date = null;
					this.invoice_doc.posa_notes = null;
					this.invoice_doc.shipping_address_name = null;
				} else if (this.invoice_doc && data === "Order") {
					// Initialize delivery date to today when switching to Order type
					this.new_delivery_date = this.formatDateDisplay(frappe.datetime.now_date());
					this.update_delivery_date();
				}
				// Handle return invoices properly
				if (this.invoice_doc && data === "Return") {
					this.invoice_doc.is_return = 1;
					// Ensure payments are negative for returns
					this.ensureReturnPaymentsAreNegative();
					this.is_credit_return = false;
				}
			});
			this.eventBus.on("update_customer", (customer) => {
				if (this.customer !== customer) {
					this.customer_credit_dict = [];
					this.redeem_customer_credit = false;
					this.is_cashback = true;
					this.is_credit_return = false;
				}
			});
			this.eventBus.on("set_pos_settings", (data) => {
				this.pos_settings = data;
			});
			this.eventBus.on("set_customer_info_to_edit", (data) => {
				this.customer_info = data;
			});
			this.eventBus.on("set_mpesa_payment", (data) => {
				this.set_mpesa_payment(data);
			});
			// Clear any stored invoice when parent emits clear_invoice
			this.eventBus.on("clear_invoice", () => {
				this.invoice_doc = "";
				this.is_return = false;
				this.is_credit_return = false;
			});
		});
	},
	// Lifecycle hook: beforeUnmount
	beforeUnmount() {
		// Remove all event listeners
		this.eventBus.off("send_invoice_doc_payment");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("add_the_new_address");
		this.eventBus.off("update_invoice_type");
		this.eventBus.off("update_customer");
		this.eventBus.off("set_pos_settings");
		this.eventBus.off("set_customer_info_to_edit");
		this.eventBus.off("set_mpesa_payment");
		this.eventBus.off("clear_invoice");
		this.eventBus.off("network-online", this.syncPendingInvoices);
		this.eventBus.off("server-online", this.syncPendingInvoices);
	},
	// Lifecycle hook: unmounted
	unmounted() {
		// Remove keyboard shortcut listener
		document.removeEventListener("keydown", this.shortPay);
	},
};
</script>

<style scoped>
.v-text-field {
	composes: pos-form-field;
}

/* Remove readonly styling */
.v-text-field--readonly {
	cursor: text;
}

.v-text-field--readonly:hover {
	background-color: transparent;
}

.cards {
	background-color: var(--surface-secondary) !important;
}

/* Large text for better visibility */
.large-text {
	font-size: 24px !important;
}

/* Dark mode styling for input fields */
:deep(.dark-theme) .dark-field,
:deep(.v-theme--dark) .dark-field,
::v-deep(.dark-theme) .dark-field,
::v-deep(.v-theme--dark) .dark-field {
	background-color: #1e1e1e !important;
}

:deep(.dark-theme) .dark-field :deep(.v-field__input),
:deep(.v-theme--dark) .dark-field :deep(.v-field__input),
:deep(.dark-theme) .dark-field :deep(input),
:deep(.v-theme--dark) .dark-field :deep(input),
:deep(.dark-theme) .dark-field :deep(.v-label),
:deep(.v-theme--dark) .dark-field :deep(.v-label),
::v-deep(.dark-theme) .dark-field .v-field__input,
::v-deep(.v-theme--dark) .dark-field .v-field__input,
::v-deep(.dark-theme) .dark-field input,
::v-deep(.v-theme--dark) .dark-field input,
::v-deep(.dark-theme) .dark-field .v-label,
::v-deep(.v-theme--dark) .dark-field .v-label {
	color: #fff !important;
}

:deep(.dark-theme) .dark-field :deep(.v-field__overlay),
:deep(.v-theme--dark) .dark-field :deep(.v-field__overlay),
::v-deep(.dark-theme) .dark-field .v-field__overlay,
::v-deep(.v-theme--dark) .dark-field .v-field__overlay {
	background-color: #1e1e1e !important;
}
</style>
