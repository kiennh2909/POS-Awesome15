<template>
	<!-- Debug: Check if ClosingDialog component is rendering -->
	{{ console.log('[CLOSING_DIALOG] Template rendering, closingDialog:', closingDialog, 'dialog_data:', dialog_data) }}
	<v-row justify="center">
		<v-dialog v-model="closingDialog" max-width="900px" persistent>
			<v-card elevation="8" class="closing-dialog-card">
				<!-- Enhanced White Header -->
				<v-card-title class="closing-header pa-6">
					<div class="header-content">
						<div class="header-icon-wrapper">
							<v-icon class="header-icon" size="40">mdi-store-clock-outline</v-icon>
						</div>
						<div class="header-text">
							<h3 class="header-title">{{ __("Closing POS Shift") }}</h3>
							<p class="header-subtitle">
								{{ __("Reconcile payment methods and close shift") }}
							</p>
						</div>
					</div>
				</v-card-title>

				<v-divider class="header-divider"></v-divider>

				<v-card-text class="white-background">
					<v-container class="pa-6">
						<!-- Shift Information Section -->
						<v-row class="mb-6">
							<v-col cols="12">
								<!-- Debug: Log when shift info section renders -->
								{{ console.log('[CLOSING_DIALOG] Rendering shift info section with data:', dialog_data) }}
								<v-card variant="outlined" class="shift-info-card pa-4">
									<h5 class="text-h6 text-primary mb-4 d-flex align-center">
										<v-icon class="me-2">mdi-information-outline</v-icon>
										{{ __("Shift Information") }}
									</h5>
									<div class="shift-info-grid">
										<div class="shift-info-item">
											<span class="shift-info-label">{{ __("Shift ID:") }}</span>
											<span class="shift-info-value">{{ dialog_data.pos_opening_shift || 'N/A' }}</span>
										</div>
										<div class="shift-info-item">
											<span class="shift-info-label">{{ __("Report ID:") }}</span>
											<span class="shift-info-value shift-report-id" :class="getShiftReportStatusClass">{{ getShiftReportId || 'N/A' }}</span>
										</div>
										<div class="shift-info-item">
											<span class="shift-info-label">{{ __("Status:") }}</span>
											<span class="shift-info-value verification-status-text" :class="getVerificationStatusClass">{{ getVerificationStatusText(dialog_data.verification_status) }}</span>
										</div>
										<div class="shift-info-item">
											<span class="shift-info-label">{{ __("Open Time:") }}</span>
											<span class="shift-info-value">{{ formatDateTime(dialog_data.period_start_date, dialog_data.period_start_time) }}</span>
										</div>
									</div>
								</v-card>
							</v-col>
						</v-row>

						<v-row>
							<v-col cols="12" class="pa-1">
								<div class="table-header mb-4">
									<h4 class="text-h6 text-grey-darken-2 mb-1">
										{{ __("Payment Reconciliation") }}
									</h4>
									<p class="text-body-2 text-grey">
										{{ __("Enter closing amounts for each payment method") }}
									</p>
									<v-alert v-if="!isVerifiedOrConfirmed && (dialog_data.shift_report || dialog_data.shift_report_id)" type="error" class="mt-3">
										{{ __("Shift Report must be verified before closing shift") }}
									</v-alert>
									<v-alert v-if="allFieldsEmpty" type="warning" class="mt-3">
										{{ __("Please enter closing amounts for all payment methods") }}
									</v-alert>
								</div>

								<v-data-table
									:headers="headers"
									:items="dialog_data.payment_reconciliation"
									item-key="mode_of_payment"
									class="elevation-0 rounded-lg white-table"
									:items-per-page="itemsPerPage"
									hide-default-footer
									density="compact"
								>
									<template v-slot:item.closing_amount="props">
										<v-text-field
											v-model="props.item.closing_amount"
											:rules="[
												isNumber,
												max25chars
											]"
											:label="frappe._('Edit')"
											single-line
											counter
											type="number"
											density="compact"
											variant="outlined"
											color="primary"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field"
											hide-details
											:prefix="currencySymbol(pos_profile.currency)"
										></v-text-field>
									</template>
									<template v-slot:item.difference="{ item }">
										{{ currencySymbol(pos_profile.currency) }}
										{{
											item.difference = formatCurrency(
												item.expected_amount - item.closing_amount,
											)
										}}</template
									>
									<template v-slot:item.opening_amount="{ item }">
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(item.opening_amount) }}</template
									>
									<template v-slot:item.expected_amount="{ item }">
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(item.expected_amount) }}</template
									>
								</v-data-table>
							</v-col>
						</v-row>
					</v-container>
				</v-card-text>

				<v-divider></v-divider>
				<v-card-actions class="dialog-actions-container">
				<v-btn
					theme="dark"
					@click="close_dialog"
					class="pos-action-btn cancel-action-btn"
					size="large"
					elevation="2"
				>
					<v-icon start>mdi-close-circle-outline</v-icon>
					<span>{{ __("Close") }}</span>
				</v-btn>
				<v-spacer></v-spacer>

				<v-tooltip
					v-if="!isVerifiedOrConfirmed && (dialog_data.shift_report || dialog_data.shift_report_id)"
					text="Shift report must be verified before closing shift"
					location="top"
				>
					<template v-slot:activator="{ props }">
						<v-btn
							v-bind="props"
							theme="dark"
							@click="submit_dialog"
							class="pos-action-btn submit-action-btn"
							size="large"
							elevation="2"
							:disabled="!isVerifiedOrConfirmed"
						>
							<v-icon start>mdi-check-circle-outline</v-icon>
							<span>{{ __("Submit") }}</span>
						</v-btn>
					</template>
				</v-tooltip>
				<v-btn
					v-else
					theme="dark"
					@click="submit_dialog"
					class="pos-action-btn submit-action-btn"
					size="large"
					elevation="2"
				>
					<v-icon start>mdi-check-circle-outline</v-icon>
					<span>{{ __("Submit") }}</span>
				</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";
export default {
	mixins: [format],
	data: () => ({
		closingDialog: false,
		itemsPerPage: 20,
		dialog_data: {},
		pos_profile: "",
		headers: [
			{
				title: __("Mode of Payment"),
				value: "mode_of_payment",
				align: "start",
				sortable: true,
			},
			{
				title: __("Opening Amount"),
				align: "end",
				sortable: true,
				value: "opening_amount",
			},
			{
				title: __("Closing Amount"),
				value: "closing_amount",
				align: "end",
				sortable: true,
			},
		],
		max25chars: (v) => v.length <= 20 || "Input too long!",
		required: (v) => !!v || "This field is required",
		isNumber: (v) => !isNaN(v) || "Must be a number",
		pagination: {},
	}),
	watch: {},

	methods: {
		close_dialog() {
			this.closingDialog = false;
		},
		submit_dialog() {
			console.log("[CLOSING_DIALOG] Submitting closing shift with data:", this.dialog_data);
			console.log("[CLOSING_DIALOG] Shift Report ID being used:", this.getShiftReportId);
			console.log("[CLOSING_DIALOG] Verification status:", this.dialog_data.verification_status);

			this.eventBus.emit("submit_closing_pos", this.dialog_data);
			this.closingDialog = false;
		},
		initializeClosingAmounts() {
			// Default closing amounts to expected amounts
			if (this.dialog_data.payment_reconciliation) {
				this.dialog_data.payment_reconciliation.forEach(payment => {
					if (payment.expected_amount !== undefined && payment.expected_amount !== null) {
						// Set closing amount to expected amount as default
						payment.closing_amount = payment.expected_amount;
					}
				});
			}
		},


		formatDateTime(date, time) {
			if (!date) return 'N/A';

			try {
				let dateTimeStr = date;
				if (time) {
					dateTimeStr += ' ' + time;
				}

				// Use frappe's datetime formatting if available
				if (window.frappe && frappe.datetime) {
					const dateObj = frappe.datetime.str_to_obj(dateTimeStr);
					return frappe.datetime.prettyDate(dateObj) + ' ' + frappe.datetime.get_time(dateObj);
				}

				// Fallback to basic formatting
				const dateObj = new Date(dateTimeStr);
				return dateObj.toLocaleString();
			} catch (e) {
				console.warn('Error formatting datetime:', e);
				return date + (time ? ' ' + time : '');
			}
		},
	},

	computed: {
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
		allFieldsEmpty() {
			return this.dialog_data.payment_reconciliation?.every(item =>
				!item.closing_amount || item.closing_amount === ''
			) || false;
		},
		isVerified() {
			return this.dialog_data.verification_status === 'Verified';
		},
		isVerifiedOrConfirmed() {
			// Allow closing if shift report exists and is verified, OR if no shift report exists (optional)
			const hasShiftReport = this.dialog_data.shift_report || this.dialog_data.shift_report_id;
			if (!hasShiftReport) {
				return true; // Allow closing without shift report
			}
			return this.dialog_data.verification_status === 'Verified' ||
				   this.dialog_data.verification_status === 'Confirmed';
		},
		getShiftReportStatusClass() {
			const status = this.dialog_data.verification_status;
			if (status === 'Verified' || status === 'Confirmed') {
				return 'verified';
			} else {
				return 'unverified';
			}
		},
		getShiftReportId() {
			return this.dialog_data.shift_report || this.dialog_data.shift_report_id;
		},

		getVerificationStatusText(status) {
			const statusTexts = {
				'Pending': __('Pending'),
				'Verified': __('Verified'),
				'Confirmed': __('Confirmed')
			};
			return statusTexts[status] || __('Unknown');
		},

		getVerificationStatusClass() {
			const status = this.dialog_data.verification_status;
			if (status === 'Verified' || status === 'Confirmed') {
				return 'status-verified';
			} else if (status === 'Pending') {
				return 'status-pending';
			} else {
				return 'status-unknown';
			}
		},
	},

	created: function () {
		console.log("[CLOSING_DIALOG] Component created, waiting for open_ClosingDialog event");
		this.eventBus.on("open_ClosingDialog", (data) => {
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - Received data:", data);
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - Data keys:", Object.keys(data || {}));
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - Data is empty?", !data || Object.keys(data).length === 0);
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - pos_opening_shift:", data?.pos_opening_shift);
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - shift_report:", data?.shift_report);
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - verification_status:", data?.verification_status);
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - period_start_date:", data?.period_start_date);
			console.log("[SHIFT_CLOSE_WORKFLOW] CLOSING_DIALOG_OPEN - period_start_time:", data?.period_start_time);

			this.closingDialog = true;
			this.dialog_data = data;
			console.log("[CLOSING_DIALOG] Dialog data set:", this.dialog_data);
			console.log("[CLOSING_DIALOG] Dialog data keys after set:", Object.keys(this.dialog_data || {}));
			this.initializeClosingAmounts();
		});
		this.eventBus.on("register_pos_profile", (data) => {
			this.pos_profile = data.pos_profile;
			if (!this.pos_profile.hide_expected_amount) {
				this.headers.push({
					title: __("Expected Amount"),
					value: "expected_amount",
					align: "end",
					sortable: false,
				});
				this.headers.push({
					title: __("Difference"),
					value: "difference",
					align: "end",
					sortable: false,
				});
			}
		});
	},
	beforeUnmount() {
		this.eventBus.off("open_ClosingDialog");
		this.eventBus.off("register_pos_profile");
	},
};
</script>

<style scoped>
/* Enhanced Header Styles */
.closing-header {
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
	border-bottom: 1px solid #e0e0e0;
	padding: 24px !important;
}

.header-content {
	display: flex;
	align-items: center;
	gap: 20px;
	width: 100%;
}

.header-icon-wrapper {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 64px;
	height: 64px;
	background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
	border-radius: 16px;
	box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

.header-icon {
	color: white !important;
}

.header-text {
	flex: 1;
}

.header-title {
	font-size: 1.5rem;
	font-weight: 600;
	color: #1a1a1a;
	margin: 0 0 4px 0;
	line-height: 1.2;
}

.header-subtitle {
	font-size: 0.95rem;
	color: #666;
	margin: 0;
	font-weight: 400;
}

.header-divider {
	border-color: #e0e0e0;
}

.white-background {
	background-color: #ffffff;
}

.table-header {
	padding: 0 4px;
}

.white-table {
	background-color: white;
	border: 1px solid #e0e0e0;
}

/* Action Buttons */
.dialog-actions-container {
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
	border-top: 1px solid #e0e0e0;
	padding: 16px 24px;
	gap: 12px;
}

.pos-action-btn {
	border-radius: 12px;
	text-transform: none;
	font-weight: 600;
	padding: 12px 32px;
	min-width: 120px;
	transition: all 0.3s ease;
	color: white !important;
	/* Add this line */
}

/* Add these new rules: */
.pos-action-btn .v-icon {
	color: white !important;
}

.pos-action-btn span {
	color: white !important;
}

.pos-action-btn:disabled .v-icon,
.pos-action-btn:disabled span {
	color: white !important;
}

.cancel-action-btn {
	background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%) !important;
}

.submit-action-btn {
	background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%) !important;
}


.submit-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 6px 20px rgba(46, 125, 50, 0.4);
}

.cancel-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 6px 20px rgba(211, 47, 47, 0.4);
}

.submit-action-btn:disabled {
	opacity: 0.6;
	transform: none;
}

/* Dark theme overrides */
:deep(.dark-theme) .closing-dialog-card,
:deep(.v-theme--dark) .closing-dialog-card,
::v-deep(.dark-theme) .closing-dialog-card,
::v-deep(.v-theme--dark) .closing-dialog-card {
	background: #1e1e1e !important;
}

:deep(.dark-theme) .closing-header,
:deep(.v-theme--dark) .closing-header,
::v-deep(.dark-theme) .closing-header,
::v-deep(.v-theme--dark) .closing-header {
	background: #1e1e1e !important;
	color: #fff !important;
	border-bottom: 1px solid #373737;
}

:deep(.dark-theme) .white-background,
:deep(.v-theme--dark) .white-background,
::v-deep(.dark-theme) .white-background,
::v-deep(.v-theme--dark) .white-background {
	background-color: #1e1e1e !important;
}

:deep(.dark-theme) .white-table,
:deep(.v-theme--dark) .white-table,
::v-deep(.dark-theme) .white-table,
::v-deep(.v-theme--dark) .white-table {
	background-color: #1e1e1e !important;
}

:deep(.dark-theme) .dialog-actions-container,
:deep(.v-theme--dark) .dialog-actions-container,
::v-deep(.dark-theme) .dialog-actions-container,
::v-deep(.v-theme--dark) .dialog-actions-container {
	background: #1e1e1e !important;
	border-top: 1px solid #373737;
}


/* Header Content Layout */
.header-content {
	display: flex;
	align-items: center;
	gap: 20px;
	width: 100%;
	justify-content: space-between;
}

/* Shift Information Card */
.shift-info-card {
	background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
	border: 2px solid #e9ecef !important;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.shift-info-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: 16px;
}

.shift-info-item {
	display: flex;
	flex-direction: column;
	gap: 4px;
	padding: 12px;
	background: white;
	border-radius: 8px;
	border: 1px solid #dee2e6;
	transition: all 0.3s ease;
}

.shift-info-item:hover {
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	transform: translateY(-1px);
}

.shift-info-label {
	font-size: 0.8rem;
	font-weight: 600;
	color: #6c757d;
	text-transform: uppercase;
	letter-spacing: 0.5px;
}

.shift-info-value {
	font-size: 0.95rem;
	font-weight: 600;
	color: #495057;
	font-family: 'Courier New', monospace;
	word-break: break-all;
}

.shift-report-id.unverified {
	color: #d32f2f !important;
	font-weight: 600;
}

.shift-report-id.verified {
	color: #2e7d32 !important;
	font-weight: 600;
}

.verification-status-text {
	font-weight: 600;
	font-size: 0.85rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
}

.verification-status-text.status-verified {
	color: #2e7d32 !important;
}

.verification-status-text.status-pending {
	color: #f57c00 !important;
}

.verification-status-text.status-unknown {
	color: #666 !important;
}

/* Responsive Design */
@media (max-width: 768px) {
	.dialog-actions-container {
		flex-direction: column;
		gap: 12px;
	}

	.pos-action-btn {
		width: 100%;
	}

	.header-content {
		flex-direction: column;
		align-items: flex-start;
		gap: 12px;
	}

	/* Shift Information Card Mobile */
	.shift-info-grid {
		grid-template-columns: 1fr;
		gap: 12px;
	}

	.shift-info-item {
		padding: 10px;
	}

	.shift-info-label {
		font-size: 0.75rem;
	}

	.shift-info-value {
		font-size: 0.9rem;
	}
}
</style>
