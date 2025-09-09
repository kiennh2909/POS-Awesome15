<template>
	<v-dialog v-model="show" max-width="800px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2" :color="actionColor">{{ actionIcon }}</v-icon>
				{{ dialogTitle }}
				<v-spacer></v-spacer>
				<v-btn icon variant="text" @click="close">
					<v-icon>mdi-close</v-icon>
				</v-btn>
			</v-card-title>

			<v-divider></v-divider>

			<v-card-text class="pa-4">
				<!-- Shift Report Summary -->
				<v-alert
					variant="tonal"
					:color="actionColor"
					class="mb-4"
				>
					<div class="d-flex align-center">
						<v-icon class="me-2">{{ actionIcon }}</v-icon>
						<div>
							<div class="font-weight-bold">{{ shiftReportData.shift_report_id }}</div>
							<div class="text-body-2">{{ formatDate(shiftReportData.opening_date) }} - {{ shiftReportData.opened_by }}</div>
						</div>
					</div>
				</v-alert>

				<!-- Financial Comparison -->
				<div class="mb-4">
					<h6 class="text-subtitle-1 mb-3">{{ __("Financial Summary") }}</h6>
					<v-row dense>
						<v-col cols="12" md="4">
							<v-card variant="outlined" class="pa-3 text-center">
								<div class="text-caption text-medium-emphasis">{{ __("Opening Amount") }}</div>
								<div class="text-h6 font-weight-bold text-primary">
									{{ formatCurrency(shiftReportData.total_opening_amount || 0) }}
								</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="4">
							<v-card variant="outlined" class="pa-3 text-center">
								<div class="text-caption text-medium-emphasis">{{ __("Expected Closing") }}</div>
								<div class="text-h6 font-weight-bold text-info">
									{{ formatCurrency(shiftReportData.total_expected_closing || 0) }}
								</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="4">
							<v-card variant="outlined" class="pa-3 text-center">
								<div class="text-caption text-medium-emphasis">{{ __("Actual Closing") }}</div>
								<div class="text-h6 font-weight-bold text-success">
									{{ formatCurrency(shiftReportData.total_actual_closing || 0) }}
								</div>
							</v-card>
						</v-col>
					</v-row>
				</div>

				<!-- Difference Highlight -->
				<v-alert
					variant="tonal"
					:color="differenceColor"
					class="mb-4"
				>
					<div class="d-flex align-center justify-space-between">
						<div class="d-flex align-center">
							<v-icon class="me-2">{{ differenceIcon }}</v-icon>
							<div>
								<div class="font-weight-bold">{{ __("Difference") }}</div>
								<div class="text-body-2">{{ differenceMessage }}</div>
							</div>
						</div>
						<div class="text-h5 font-weight-bold" :class="differenceTextColor">
							{{ formatCurrency(shiftReportData.difference || 0) }}
						</div>
					</div>
				</v-alert>

				<!-- Invoice Summary -->
				<div class="mb-4">
					<h6 class="text-subtitle-1 mb-3">{{ __("Invoice Summary") }}</h6>
					<v-row dense>
						<v-col cols="12" md="4">
							<v-card variant="outlined" class="pa-3">
								<div class="d-flex align-center">
									<v-icon color="primary" class="me-2">mdi-receipt-text</v-icon>
									<div>
										<div class="text-caption text-medium-emphasis">{{ __("Total Invoices") }}</div>
										<div class="text-h6 font-weight-bold">{{ shiftReportData.invoice_count || 0 }}</div>
									</div>
								</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="4">
							<v-card variant="outlined" class="pa-3">
								<div class="d-flex align-center">
									<v-icon color="success" class="me-2">mdi-cash-plus</v-icon>
									<div>
										<div class="text-caption text-medium-emphasis">{{ __("Total Sales") }}</div>
										<div class="text-h6 font-weight-bold text-success">
											{{ formatCurrency(shiftReportData.total_sales || 0) }}
										</div>
									</div>
								</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="4">
							<v-card variant="outlined" class="pa-3">
								<div class="d-flex align-center">
									<v-icon color="error" class="me-2">mdi-cash-minus</v-icon>
									<div>
										<div class="text-caption text-medium-emphasis">{{ __("Total Returns") }}</div>
										<div class="text-h6 font-weight-bold text-error">
											{{ formatCurrency(shiftReportData.total_returns || 0) }}
										</div>
									</div>
								</div>
							</v-card>
						</v-col>
					</v-row>
				</div>

				<!-- Notes Section -->
				<div class="mb-4">
					<v-textarea
						v-model="notes"
						:label="__('Notes')"
						:placeholder="__('Add verification notes...')"
						variant="outlined"
						rows="3"
						counter
						maxlength="500"
					></v-textarea>
				</div>

				<!-- Action Warning -->
				<v-alert
					variant="tonal"
					color="warning"
					v-if="action === 'reject'"
					class="mb-4"
				>
					<div class="d-flex align-center">
						<v-icon class="me-2">mdi-alert</v-icon>
						<div>
							<div class="font-weight-bold">{{ __("Rejection Notice") }}</div>
							<div class="text-body-2">{{ __("This action will reset the verification status and require re-verification.") }}</div>
						</div>
					</div>
				</v-alert>
			</v-card-text>

			<v-divider></v-divider>

			<v-card-actions class="pa-4">
				<v-spacer></v-spacer>
				<v-btn variant="text" @click="close">
					{{ __("Cancel") }}
				</v-btn>
				<v-btn
					v-if="action === 'reject'"
					color="error"
					variant="flat"
					prepend-icon="mdi-close-circle"
					@click="confirmAction"
					:loading="processing"
				>
					{{ __("Reject Report") }}
				</v-btn>
				<v-btn
					v-else
					:color="actionColor"
					variant="flat"
					:prepend-icon="actionIcon"
					@click="confirmAction"
					:loading="processing"
				>
					{{ actionButtonText }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: "ShiftVerificationDialog",
	props: {
		modelValue: {
			type: Boolean,
			default: false
		},
		action: {
			type: String,
			default: "verify", // "verify", "confirm", "reject"
			validator: (value) => ["verify", "confirm", "reject"].includes(value)
		},
		shiftReportData: {
			type: Object,
			default: () => ({})
		}
	},
	emits: ["update:modelValue", "confirmed"],
	data() {
		return {
			processing: false,
			notes: ""
		};
	},
	computed: {
		show: {
			get() {
				return this.modelValue;
			},
			set(value) {
				this.$emit("update:modelValue", value);
			}
		},
		dialogTitle() {
			const titles = {
				"verify": this.__("Verify Shift Report"),
				"confirm": this.__("Confirm Shift Report"),
				"reject": this.__("Reject Shift Report")
			};
			return titles[this.action] || this.__("Shift Report Action");
		},
		actionIcon() {
			const icons = {
				"verify": "mdi-check-circle-outline",
				"confirm": "mdi-check-all",
				"reject": "mdi-close-circle-outline"
			};
			return icons[this.action] || "mdi-information";
		},
		actionColor() {
			const colors = {
				"verify": "info",
				"confirm": "success",
				"reject": "error"
			};
			return colors[this.action] || "primary";
		},
		actionButtonText() {
			const texts = {
				"verify": this.__("Verify Report"),
				"confirm": this.__("Confirm Report"),
				"reject": this.__("Reject Report")
			};
			return texts[this.action] || this.__("Confirm Action");
		},
		differenceColor() {
			const difference = this.shiftReportData.difference || 0;
			if (difference === 0) return "success";
			return difference > 0 ? "warning" : "error";
		},
		differenceIcon() {
			const difference = this.shiftReportData.difference || 0;
			if (difference === 0) return "mdi-check-circle";
			return difference > 0 ? "mdi-plus-circle" : "mdi-minus-circle";
		},
		differenceTextColor() {
			const difference = this.shiftReportData.difference || 0;
			if (difference === 0) return "text-success";
			return difference > 0 ? "text-warning" : "text-error";
		},
		differenceMessage() {
			const difference = this.shiftReportData.difference || 0;
			if (difference === 0) {
				return this.__("Amounts match perfectly");
			} else if (difference > 0) {
				return this.__("Actual amount is higher than expected");
			} else {
				return this.__("Actual amount is lower than expected");
			}
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal) {
				this.resetForm();
			}
		}
	},
	methods: {
		resetForm() {
			this.notes = "";
			this.processing = false;
		},

		async confirmAction() {
			if (this.action === "reject" && !this.notes.trim()) {
				this.showError(this.__("Please provide a reason for rejection"));
				return;
			}

			this.processing = true;

			try {
				// Mock API call - will be replaced with real implementation
				await new Promise(resolve => setTimeout(resolve, 1500));

				const result = {
					action: this.action,
					shift_report_id: this.shiftReportData.shift_report_id,
					notes: this.notes,
					timestamp: new Date().toISOString()
				};

				this.showSuccess(this.getSuccessMessage());
				this.$emit("confirmed", result);
				this.close();

			} catch (error) {
				console.error("Error processing shift report action:", error);
				this.showError(this.getErrorMessage());
			} finally {
				this.processing = false;
			}
		},

		getSuccessMessage() {
			const messages = {
				"verify": this.__("Shift report verified successfully"),
				"confirm": this.__("Shift report confirmed successfully"),
				"reject": this.__("Shift report rejected successfully")
			};
			return messages[this.action] || this.__("Action completed successfully");
		},

		getErrorMessage() {
			const messages = {
				"verify": this.__("Failed to verify shift report"),
				"confirm": this.__("Failed to confirm shift report"),
				"reject": this.__("Failed to reject shift report")
			};
			return messages[this.action] || this.__("Action failed");
		},

		formatDate(date) {
			if (!date) return "-";
			return new Date(date).toLocaleDateString();
		},

		formatCurrency(amount) {
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: 'USD'
			}).format(amount);
		},

		showSuccess(message) {
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({ message, indicator: 'green' });
			} else {
				alert(message);
			}
		},

		showError(message) {
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({ message, indicator: 'red' });
			} else {
				alert(message);
			}
		},

		close() {
			this.show = false;
		}
	}
};
</script>

<style scoped>
.v-card {
	border-radius: 12px;
}

.v-alert {
	border-radius: 8px;
}

.v-card-actions {
	border-top: 1px solid rgb(var(--v-theme-surface-variant));
}
</style>