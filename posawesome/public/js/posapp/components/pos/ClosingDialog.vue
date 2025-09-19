<template>
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
						<!-- Verification Status Display -->
						<div class="verification-status-wrapper" v-if="dialog_data.verification_status">
							<v-chip
								:color="getVerificationColor(dialog_data.verification_status)"
								variant="outlined"
								size="small"
								class="verification-status-chip"
							>
								<v-icon size="16" class="me-1">
									{{ getVerificationIcon(dialog_data.verification_status) }}
								</v-icon>
								{{ dialog_data.verification_status }}
							</v-chip>
						</div>
					</div>
				</v-card-title>

				<v-divider class="header-divider"></v-divider>

				<v-card-text class="pa-0 white-background">
					<v-container class="pa-6">
						<v-row>
							<v-col cols="12" class="pa-1">
								<div class="table-header mb-4">
									<h4 class="text-h6 text-grey-darken-2 mb-1">
										{{ __("Payment Reconciliation") }}
									</h4>
									<p class="text-body-2 text-grey">
										{{ __("Verify closing amounts for each payment method") }}
									</p>
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
												required,
												isNumber,
												max25chars,
												(v) => notZeroIfExpected(v, props.item)
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

				<!-- Verify Button (Always visible, ReadOnly when verified) -->
				<v-btn
					theme="dark"
					@click="verifyShiftReport"
					class="pos-action-btn verify-action-btn"
					size="large"
					elevation="2"
					:disabled="isVerifiedOrConfirmed"
					:loading="verifying"
				>
					<v-icon start>mdi-check-circle-outline</v-icon>
					<span>{{ __("Verify") }}</span>
				</v-btn>

				<v-tooltip
					v-if="!isVerified"
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
							:disabled="!isVerified"
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
		verifying: false,
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
		notZeroIfExpected: (v, item) => {
			if (item && item.expected_amount > 0) {
				return parseFloat(v) > 0 || "Closing amount cannot be 0 when expected amount > 0";
			}
			return true;
		},
		pagination: {},
	}),
	watch: {},

	methods: {
		close_dialog() {
			this.closingDialog = false;
		},
		submit_dialog() {
			this.eventBus.emit("submit_closing_pos", this.dialog_data);
			this.closingDialog = false;
		},
		initializeClosingAmounts() {
			if (this.dialog_data.payment_reconciliation) {
				this.dialog_data.payment_reconciliation.forEach(item => {
					// Only set default if closing_amount is not set (undefined, null, empty string, or 0) and expected_amount > 0
					const currentAmount = item.closing_amount;
					if ((currentAmount === undefined || currentAmount === null || currentAmount === '' || currentAmount === 0) && item.expected_amount > 0) {
						item.closing_amount = item.expected_amount;
						console.log(`Set default closing_amount for ${item.mode_of_payment}: ${item.expected_amount}`);
					}
				});
			}
		},

		// Verification Methods
		getVerificationColor(status) {
			const colors = {
				'Pending': 'warning',
				'Verified': 'success',
				'Confirmed': 'info'
			};
			return colors[status] || 'grey';
		},

		getVerificationIcon(status) {
			const icons = {
				'Pending': 'mdi-clock-outline',
				'Verified': 'mdi-check-circle',
				'Confirmed': 'mdi-check-circle-outline'
			};
			return icons[status] || 'mdi-help-circle';
		},

		async verifyShiftReport() {
			if (this.isVerifiedOrConfirmed) {
				return; // Already verified
			}

			this.verifying = true;
			try {
				console.log("Verifying shift report:", this.dialog_data.shift_report_id);

				const response = await frappe.call({
					method: "posawesome.posawesome.api.shift_verification.verify_shift_report",
					args: {
						shift_report_id: this.dialog_data.shift_report_id
					}
				});

				console.log("Verify response:", response);

				if (response.message && response.message.success) {
					// Success feedback
					this.showSuccess(__("Shift report verified successfully"));

					// Update local verification status
					this.dialog_data.verification_status = "Verified";

					// Emit event to notify other components
					if (this.eventBus) {
						this.eventBus.emit("shift_report_verified", {
							shift_report_id: this.dialog_data.shift_report_id,
							verification_status: "Verified",
							disable_transaction_buttons: true
						});

						// Emit event to update UI components
						this.eventBus.emit("shift_verification_changed", "Verified");
					}

				} else {
					// Error handling
					const errorMessage = response.message?.message || __("Failed to verify shift report");
					this.showError(errorMessage);
				}
			} catch (error) {
				console.error("Verify error:", error);
				this.showError(__("Error verifying shift report"));
			} finally {
				this.verifying = false;
			}
		},

		showError(message) {
			console.error("ClosingDialog Error:", message);

			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({
					message: message,
					indicator: 'red'
				});
			} else if (window.frappe && frappe.msgprint) {
				frappe.msgprint({
					title: __('Error'),
					message: message,
					indicator: 'red'
				});
			} else {
				alert(`Error: ${message}`);
			}
		},

		showSuccess(message) {
			console.log("ClosingDialog Success:", message);

			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({
					message: message,
					indicator: 'green'
				});
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
			return this.dialog_data.verification_status === 'Verified' ||
				   this.dialog_data.verification_status === 'Confirmed';
		},
	},

	created: function () {
		this.eventBus.on("open_ClosingDialog", (data) => {
			this.closingDialog = true;
			this.dialog_data = data;
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

.verify-action-btn {
	background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
}

.verify-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4);
}

.verify-action-btn:disabled {
	opacity: 0.6;
	transform: none;
	background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%) !important;
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

/* Verification Status Styles */
.verification-status-wrapper {
	display: flex;
	align-items: center;
	margin-left: auto;
}

.verification-status-chip {
	font-weight: 600;
	font-size: 0.8rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	transition: all 0.3s ease;
}

.verification-status-chip:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

/* Header Content Layout */
.header-content {
	display: flex;
	align-items: center;
	gap: 20px;
	width: 100%;
	justify-content: space-between;
}

/* And the responsive section: */
@media (max-width: 768px) {
	.dialog-actions-container {
		flex-direction: column;
		gap: 12px;
	}

	.pos-action-btn {
		width: 100%;
	}

	.verification-status-wrapper {
		margin-left: 0;
		margin-top: 12px;
		justify-content: center;
	}

	.header-content {
		flex-direction: column;
		align-items: flex-start;
		gap: 12px;
	}
}
</style>
