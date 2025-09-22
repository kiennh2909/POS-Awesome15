<template>
	<v-dialog v-model="show" max-width="1200px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-store-clock-outline</v-icon>
				<div class="header-content">
					<div class="header-main">
						<h3 class="header-title">{{ __("Close POS Shift") }}</h3>
						<div class="shift-info" v-if="shiftReportData">
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Shift ID:") }}</span>
								<span class="shift-info-value">{{ displayShiftReportId }}</span>
							</div>
						</div>
					</div>
				</div>
				<v-spacer></v-spacer>
				<v-btn icon variant="text" @click="close">
					<v-icon>mdi-close</v-icon>
				</v-btn>
			</v-card-title>

			<v-divider></v-divider>

			<v-card-text class="pa-0">
				<div class="pa-4 action-buttons-section">
					<div class="d-flex justify-space-between align-center">
						<div class="d-flex align-center gap-4">
							<h6 class="text-subtitle-1 mb-0">{{ __("Shift Closing Actions") }}</h6>
						</div>
						<div class="d-flex action-buttons-group">
							<v-btn
								color="primary"
								variant="flat"
								prepend-icon="mdi-store-clock"
								:loading="closingShift"
								@click="closeShift"
								class="action-btn"
							>
								{{ __("Close Shift") }}
							</v-btn>
							<v-btn variant="text" @click="close" class="action-btn">
								{{ __("Cancel") }}
							</v-btn>
						</div>
					</div>
				</div>

				<v-divider></v-divider>

				<div class="pa-4">
					<h6 class="text-subtitle-1 mb-3">{{ __("Payment Reconciliation") }}</h6>
					<v-data-table
						:headers="paymentSummaryHeaders"
						:items="paymentSummaryDataWithTotal"
						:loading="loadingSummary"
						density="compact"
						:items-per-page="-1"
						hide-default-footer
						class="elevation-0 payment-summary-table"
					>
						<template #item.actual_closing_amount="{ item }">
							<v-text-field
								v-if="!item.isTotalRow"
								v-model="item.actual_closing_amount"
								:rules="[isNumber]"
								:label="__('Actual Closing')"
								single-line
								density="compact"
								variant="outlined"
								color="primary"
								hide-details
								:prefix="currencySymbol(posProfile.currency)"
								class="actual-closing-input"
								@input="calculateDifference(item)"
							></v-text-field>
							<span v-else class="font-weight-bold currency-amount">
								{{ formatCurrency(item.actual_closing_amount || 0) }}
							</span>
						</template>
					</v-data-table>
				</div>
			</v-card-text>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: "ClosingShiftNew",
	props: {
		modelValue: { type: Boolean, default: false },
		shiftReportId: { type: String, default: "" },
		posProfile: { type: Object, default: () => ({}) }
	},
	emits: ["update:modelValue"],
	data() {
		return {
			loading: false,
			loadingSummary: false,
			closingShift: false,
			shiftReportData: null,
			paymentSummaryData: [],
			paymentSummaryHeaders: [
				{ title: this.__("Payment Method"), key: "payment_method", width: "140px" },
				{ title: this.__("Opening Amount"), key: "opening_amount", width: "100px", align: "end" },
				{ title: this.__("Sales Amount"), key: "sales_amount", width: "100px", align: "end" },
				{ title: this.__("Returns Amount"), key: "returns_amount", width: "100px", align: "end" },
				{ title: this.__("Transactions"), key: "transaction_amount", width: "100px", align: "end" },
				{ title: this.__("Expected Closing"), key: "expected_closing_amount", width: "100px", align: "end" },
				{ title: this.__("Actual Closing"), key: "actual_closing_amount", width: "120px", align: "end" },
				{ title: this.__("Difference"), key: "difference", width: "100px", align: "end" }
			],
			isNumber: (v) => !isNaN(v) || "Must be a number"
		};
	},
	computed: {
		show: {
			get() { return this.modelValue; },
			set(value) { this.$emit("update:modelValue", value); }
		},
		displayShiftReportId() {
			return this.shiftReportData?.shift_report_id || this.shiftReportData?.name || 'Loading...';
		},
		paymentSummaryDataWithTotal() {
			const dataWithTotal = [...this.paymentSummaryData];
			const totalActual = this.paymentSummaryData.reduce((sum, item) => sum + (parseFloat(item.actual_closing_amount) || 0), 0);
			const totalDifference = this.paymentSummaryData.reduce((sum, item) => sum + (parseFloat(item.difference) || 0), 0);

			dataWithTotal.push({
				payment_method: 'TOTAL',
				actual_closing_amount: totalActual,
				difference: totalDifference,
				isTotalRow: true
			});

			return dataWithTotal;
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal && this.shiftReportId) {
				this.loadShiftData();
			}
		}
	},
	methods: {
		async loadShiftData() {
			this.loading = true;
			try {
				let actualShiftReportId = this.shiftReportId;

				if (typeof this.shiftReportId === 'object' && this.shiftReportId?.doctype === "POS Opening Shift") {
					const shiftReports = await frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "POS Shift Report",
							filters: { pos_opening_shift: this.shiftReportId.name },
							fields: ["name"],
							limit: 1
						}
					});

					if (shiftReports.message?.length > 0) {
						actualShiftReportId = shiftReports.message[0].name;
					}
				}

				const response = await frappe.call({
					method: "posawesome.posawesome.api.shift_reports.get_shift_report_readonly",
					args: { shift_report_id: actualShiftReportId }
				});

				if (response.message?.data) {
					const shiftReportData = response.message.data;

					if (response.message.data.payment_summaries?.length > 0) {
						this.paymentSummaryData = response.message.data.payment_summaries.map(item => ({
							payment_method: item.payment_method,
							opening_amount: item.opening_amount || 0,
							sales_amount: item.sales_amount || 0,
							returns_amount: item.returns_amount || 0,
							transaction_amount: item.transaction_amount || 0,
							expected_closing_amount: item.expected_closing_amount || 0,
							actual_closing_amount: item.expected_closing_amount || 0,
							difference: 0
						}));
					}

					this.shiftReportData = shiftReportData;
				}
			} catch (error) {
				console.error("Error loading shift data:", error);
				this.showError("Failed to load shift data");
			} finally {
				this.loading = false;
			}
		},

		calculateDifference(item) {
			const expected = parseFloat(item.expected_closing_amount) || 0;
			const actual = parseFloat(item.actual_closing_amount) || 0;
			item.difference = actual - expected;
		},

		async closeShift() {
			// Validate that all actual closing amounts are valid numbers
			const invalidAmounts = this.paymentSummaryData.filter(item => {
				const value = item.actual_closing_amount;
				if (value === undefined || value === null || value === '') {
					return false; // Empty is allowed, will default to 0
				}
				const numValue = parseFloat(value);
				return isNaN(numValue);
			});

			if (invalidAmounts.length > 0) {
				this.showError("Please enter valid numbers for actual closing amounts");
				return;
			}

			this.closingShift = true;
			try {
				// Single API call to create and submit closing shift
				const closingShiftData = {
					pos_opening_shift: typeof this.shiftReportId === 'object' ? this.shiftReportId.name : this.shiftReportId,
					pos_profile: this.posProfile.name,
					user: frappe.session.user,
					company: this.posProfile.company,
					period_start_date: this.shiftReportData?.opening_date,
					period_start_time: this.shiftReportData?.opening_time,
					balance_details: this.paymentSummaryData.map(item => ({
						mode_of_payment: item.payment_method,
						amount: item.opening_amount || 0
					})),
					payment_reconciliation: this.paymentSummaryData.map(item => {
						const actualClosing = item.actual_closing_amount;
						let closingAmount = 0;

						if (actualClosing !== '' && actualClosing !== null && actualClosing !== undefined) {
							const parsed = parseFloat(actualClosing);
							if (!isNaN(parsed)) {
								closingAmount = parsed;
							}
						}

						return {
							mode_of_payment: item.payment_method,
							opening_amount: parseFloat(item.opening_amount) || 0,
							expected_amount: parseFloat(item.expected_closing_amount) || 0,
							closing_amount: closingAmount,
							difference: parseFloat(item.difference) || 0
						};
					})
				};

				const response = await frappe.call({
					method: "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.submit_closing_shift_v2",
					args: {
						closing_shift: JSON.stringify(closingShiftData)
					}
				});

				if (response.message?.success) {
					this.showSuccess(__("Shift closed successfully"));
					this.close();
					if (this.eventBus) {
						this.eventBus.emit("shift_closed_success");
					}
				} else {
					this.showError(response.message?.message || __("Failed to close shift"));
				}
			} catch (error) {
				console.error("Error closing shift:", error);
				this.showError(__("Error closing shift"));
			} finally {
				this.closingShift = false;
			}
		},

		close() {
			this.show = false;
		},

		showError(message) {
			if (window.frappe?.show_alert) {
				frappe.show_alert({ message, indicator: 'red' });
			} else {
				alert(`Error: ${message}`);
			}
		},

		showSuccess(message) {
			if (window.frappe?.show_alert) {
				frappe.show_alert({ message, indicator: 'green' });
			}
		},

		formatCurrency(amount) {
			try {
				let currency = 'USD';
				if (this.posProfile?.currency) {
					currency = this.posProfile.currency;
				}
				return new Intl.NumberFormat('en-US', {
					style: 'currency',
					currency: currency,
					minimumFractionDigits: 2,
					maximumFractionDigits: 2
				}).format(amount || 0);
			} catch (error) {
				return `$${amount || 0}`;
			}
		},

		currencySymbol(currency) {
			const symbols = { 'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'KES': 'KSh' };
			return symbols[currency] || currency || '$';
		}
	}
};
</script>

<style scoped>
.v-dialog { max-height: 90vh; }
@media (max-width: 1366px) { .v-dialog { max-width: 95vw; max-height: 85vh; } }

.payment-summary-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-primary));
	color: rgb(var(--v-theme-on-primary));
	font-weight: 600;
	font-size: 0.8rem;
	padding: 8px 12px;
}

.actual-closing-input { min-width: 120px; }
.actual-closing-input :deep(.v-field__input) { text-align: right; font-family: 'Courier New', monospace; }

.action-buttons-section {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-bottom: 1px solid #dee2e6;
	position: sticky;
	top: 0;
	z-index: 10;
}

.currency-amount { font-family: 'Roboto Mono', monospace; font-weight: 500; letter-spacing: 0.5px; }

:deep(.payment-summary-table .v-data-table__tbody tr:last-child) {
	background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-variant)) 100%);
	color: rgb(var(--v-theme-on-primary));
	border-top: 2px solid rgb(var(--v-theme-primary-variant));
}

:deep(.payment-summary-table .v-data-table__tbody tr:last-child td) {
	padding: 12px 16px !important;
	border-bottom: none !important;
	font-size: 0.9rem !important;
	font-weight: 600 !important;
	text-align: center;
}

.action-btn {
	min-height: 44px !important;
	padding: 0 16px !important;
	font-size: 0.9rem !important;
	font-weight: 500 !important;
}

.header-content { display: flex; flex-direction: column; gap: 8px; }
.header-title { margin: 0; font-size: 1.25rem; font-weight: 600; color: rgb(var(--v-theme-on-surface)); }

.shift-info { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 4px; }
.shift-info-item { display: flex; align-items: center; gap: 6px; }
.shift-info-label { font-size: 0.8rem; font-weight: 600; color: rgb(var(--v-theme-on-surface-variant)); min-width: 55px; }
.shift-info-value {
	font-size: 0.8rem; font-weight: 500; color: rgb(var(--v-theme-on-surface));
	font-family: 'Courier New', monospace;
	background: rgba(var(--v-theme-primary), 0.1);
	padding: 2px 6px; border-radius: 4px;
	border: 1px solid rgba(var(--v-theme-primary), 0.2);
}
</style>