<template>
	<v-row justify="center">
		<v-dialog v-model="dialog" max-width="1000px" persistent>
			<v-card class="customer-detail-dialog-card">
				<!-- Enhanced Header -->
				<v-card-title class="customer-detail-header pa-6">
					<div class="header-content">
						<div class="header-icon-wrapper">
							<v-icon class="header-icon" size="28">mdi-account-details</v-icon>
						</div>
						<div class="header-text">
							<h3 class="header-title">{{ __("Customer Details") }}</h3>
							<p class="header-subtitle">{{ __("Complete customer information and analytics") }}</p>
							<div class="header-stats" v-if="customerData">
								<v-chip
									color="primary"
									variant="tonal"
									size="small"
									class="status-chip"
								>
									<v-icon start size="14">mdi-account</v-icon>
									{{ customerData.basic_info.customer_name }}
								</v-chip>
							</div>
						</div>
					</div>
					<v-btn
						icon="mdi-close"
						variant="text"
						size="default"
						@click="dialog = false"
						class="close-btn"
					></v-btn>
				</v-card-title>

				<v-divider class="header-divider"></v-divider>

				<!-- Content -->
				<v-card-text class="pa-0 white-background">
					<div class="content-container" v-if="customerData">
						<!-- Customer Information Table -->
						<div class="table-container">
							<div class="table-header mb-4">
								<h4 class="text-h6 text-grey-darken-2 mb-1">{{ __("Customer Information") }}</h4>
								<p class="text-body-2 text-grey">
									{{ __("Detailed customer profile and transaction history") }}
								</p>
							</div>

							<v-data-table
								:headers="headers"
								:items="customerInfoItems"
								class="customer-detail-table"
								:items-per-page="-1"
								hide-default-footer
							>
								<template v-slot:item.section="{ item }">
									<div class="section-header">
										<v-icon :color="item.iconColor" size="20" class="mr-2">{{ item.icon }}</v-icon>
										<span class="font-weight-medium">{{ item.section }}</span>
									</div>
								</template>

								<template v-slot:item.value="{ item }">
									<div class="value-cell" :class="item.valueClass">
										{{ item.value }}
									</div>
								</template>
							</v-data-table>
						</div>
					</div>

					<!-- Loading state -->
					<div v-else class="empty-state text-center py-12">
						<div class="empty-icon-wrapper mb-4">
							<v-icon size="80" color="primary" class="empty-icon">mdi-account-details</v-icon>
						</div>
						<h3 class="text-h5 mb-3 text-grey-darken-2 font-weight-medium">
							{{ __("Loading Customer Details") }}
						</h3>
						<p class="text-body-1 text-grey-darken-1 mb-0">
							{{ __("Please wait while we fetch customer information...") }}
						</p>
						<v-progress-circular indeterminate color="primary" size="48" class="mt-4"></v-progress-circular>
					</div>
				</v-card-text>

				<!-- Enhanced Footer -->
				<v-divider></v-divider>
				<v-card-actions class="dialog-actions-container">
					<div class="footer-info">
						<span class="footer-text">
							<v-icon start size="16" color="primary">mdi-information-outline</v-icon>
							{{ __("Customer details loaded successfully") }}
						</span>
					</div>
					<v-spacer></v-spacer>
					<v-btn
						theme="dark"
						variant="outlined"
						@click="dialog = false"
						class="standard-btn cancel-btn"
						size="default"
					>
						<v-icon start>mdi-close</v-icon>
						{{ __("Close") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";

export default {
	name: "CustomerDetail",
	mixins: [format],
	props: {
		modelValue: Boolean,
		customerId: String,
	},
	emits: ["update:modelValue"],
	computed: {
		customerInfoItems() {
			if (!this.customerData) return [];

			const items = [];

			// Basic Information Section
			items.push({
				section: __("Basic Information"),
				field: __("Customer ID"),
				value: this.customerData.basic_info.customer_id,
				icon: "mdi-account",
				iconColor: "primary",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Customer Name"),
				value: this.customerData.basic_info.customer_name,
				icon: "",
				iconColor: "",
				valueClass: "font-weight-medium",
			});
			items.push({
				section: "",
				field: __("Mobile No"),
				value: this.customerData.basic_info.mobile_no || __("Not provided"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Email"),
				value: this.customerData.basic_info.email_id || __("Not provided"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Tax ID"),
				value: this.customerData.basic_info.tax_id || __("Not provided"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("City"),
				value: this.customerData.basic_info.city || __("Not provided"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});

			// Classification Section
			items.push({
				section: __("Classification"),
				field: __("Customer Type"),
				value: this.customerData.classification_info.customer_type || __("Not specified"),
				icon: "mdi-tag",
				iconColor: "info",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Customer Group"),
				value: this.customerData.classification_info.customer_group || __("Not specified"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Territory"),
				value: this.customerData.classification_info.territory || __("Not specified"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Gender"),
				value: this.customerData.classification_info.gender || __("Not specified"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});

			// Credit Information Section
			items.push({
				section: __("Credit Information"),
				field: __("Credit Limit"),
				value: this.formatCurrency(this.customerData.credit_info.credit_limit),
				icon: "mdi-credit-card",
				iconColor: "success",
				valueClass: "text-success font-weight-medium",
			});
			items.push({
				section: "",
				field: __("Outstanding Amount"),
				value: this.formatCurrency(this.customerData.credit_info.outstanding_amount),
				icon: "",
				iconColor: "",
				valueClass: "text-warning",
			});
			items.push({
				section: "",
				field: __("Credit Balance"),
				value: this.formatCurrency(this.customerData.credit_info.credit_balance),
				icon: "",
				iconColor: "",
				valueClass: this.customerData.credit_info.credit_balance >= 0 ? "text-success" : "text-error",
			});
			items.push({
				section: "",
				field: __("Payment Terms"),
				value: this.customerData.credit_info.payment_terms || __("Not specified"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});

			// Loyalty Points Section
			items.push({
				section: __("Loyalty Points"),
				field: __("Loyalty Program"),
				value: this.customerData.loyalty_info.loyalty_program || __("Not enrolled"),
				icon: "mdi-star",
				iconColor: "purple",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Total Points"),
				value: this.formatNumber(this.customerData.loyalty_info.loyalty_points),
				icon: "",
				iconColor: "",
				valueClass: "text-primary font-weight-medium",
			});
			items.push({
				section: "",
				field: __("Points Used"),
				value: this.formatNumber(this.customerData.loyalty_info.loyalty_points_used),
				icon: "",
				iconColor: "",
				valueClass: "text-orange",
			});
			items.push({
				section: "",
				field: __("Points Balance"),
				value: this.formatNumber(this.customerData.loyalty_info.loyalty_points_balance),
				icon: "",
				iconColor: "",
				valueClass: "text-success font-weight-medium",
			});

			// Debt Information Section
			items.push({
				section: __("Debt Information"),
				field: __("Total Debt Generated"),
				value: this.formatCurrency(this.customerData.debt_info.total_debt_generated),
				icon: "mdi-cash-multiple",
				iconColor: "orange",
				valueClass: "text-error",
			});
			items.push({
				section: "",
				field: __("Total Paid"),
				value: this.formatCurrency(this.customerData.debt_info.total_paid),
				icon: "",
				iconColor: "",
				valueClass: "text-success",
			});
			items.push({
				section: "",
				field: __("Remaining Debt"),
				value: this.formatCurrency(this.customerData.debt_info.remaining_debt),
				icon: "",
				iconColor: "",
				valueClass: this.customerData.debt_info.remaining_debt > 0 ? "text-error font-weight-medium" : "text-success",
			});

			// Statistics Section
			items.push({
				section: __("Customer Statistics"),
				field: __("Total Orders"),
				value: this.formatNumber(this.customerData.statistics_info.total_orders),
				icon: "mdi-chart-bar",
				iconColor: "teal",
				valueClass: "text-primary font-weight-medium",
			});
			items.push({
				section: "",
				field: __("Total GMV"),
				value: this.formatCurrency(this.customerData.statistics_info.total_gmv),
				icon: "",
				iconColor: "",
				valueClass: "text-success font-weight-medium",
			});
			items.push({
				section: "",
				field: __("Paid Orders"),
				value: this.formatNumber(this.customerData.statistics_info.total_paid_orders),
				icon: "",
				iconColor: "",
				valueClass: "text-success",
			});
			items.push({
				section: "",
				field: __("Return Orders"),
				value: this.formatNumber(this.customerData.statistics_info.total_return_orders),
				icon: "",
				iconColor: "",
				valueClass: "text-error",
			});
			items.push({
				section: "",
				field: __("Avg Order Value"),
				value: this.formatCurrency(this.customerData.statistics_info.avg_order_value),
				icon: "",
				iconColor: "",
				valueClass: "",
			});
			items.push({
				section: "",
				field: __("Last Order Date"),
				value: this.customerData.statistics_info.last_order_date || __("No orders yet"),
				icon: "",
				iconColor: "",
				valueClass: "",
			});

			return items;
		},
	},
	data() {
		return {
			dialog: this.modelValue,
			customerData: null,
			loading: false,
			headers: [
				{
					title: __("Section"),
					value: "section",
					align: "start",
					sortable: false,
					width: "30%",
				},
				{
					title: __("Field"),
					value: "field",
					align: "start",
					sortable: false,
					width: "35%",
				},
				{
					title: __("Value"),
					value: "value",
					align: "start",
					sortable: false,
					width: "35%",
				},
			],
		};
	},
	watch: {
		modelValue(val) {
			this.dialog = val;
			if (val && this.customerId) {
				this.loadCustomerDetails();
			}
		},
		customerId(val) {
			if (val && this.dialog) {
				this.loadCustomerDetails();
			}
		},
	},
	methods: {
		async loadCustomerDetails() {
			if (!this.customerId) return;

			this.loading = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_detailed_info",
					args: {
						customer: this.customerId,
					},
				});

				if (response.message) {
					this.customerData = response.message;
				}
			} catch (error) {
				console.error("Error loading customer details:", error);
				frappe.msgprint(__("Failed to load customer details"));
			} finally {
				this.loading = false;
			}
		},

		formatNumber(value) {
			return new Intl.NumberFormat().format(value || 0);
		},
	},
};
</script>

<style scoped>
/* Customer Detail Dialog Card */
.customer-detail-dialog-card {
	border-radius: 20px !important;
	overflow: hidden;
	background: white;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
	max-height: 90vh;
}

/* Enhanced Header */
.customer-detail-header {
	background: var(--surface-primary, white);
	color: var(--text-primary, #1a1a1a);
	border-bottom: 1px solid var(--field-border, #f0f0f0);
	position: relative;
	min-height: auto !important;
}

.customer-detail-header::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 4px;
	background: linear-gradient(90deg, var(--primary-start, #1976d2) 0%, var(--primary-end, #42a5f5) 100%);
}

.header-content {
	display: flex;
	align-items: center;
	gap: 20px;
	padding-right: 60px;
}

.header-icon-wrapper {
	background: linear-gradient(135deg, var(--primary-start, #1976d2) 0%, var(--primary-end, #42a5f5) 100%);
	border-radius: 16px;
	padding: 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
}

.header-icon {
	color: white;
}

.header-text {
	flex: 1;
}

.header-title {
	margin: 0 0 4px 0;
	font-weight: 700;
	color: var(--text-primary, #1a1a1a);
	font-size: 1.5rem;
	line-height: 1.2;
}

.header-subtitle {
	margin: 0 0 12px 0;
	font-size: 14px;
	color: var(--text-secondary, #666);
	font-weight: 400;
	line-height: 1.2;
}

.header-stats {
	display: flex;
	gap: 8px;
}

.status-chip {
	font-weight: 600;
	border-radius: 12px;
}

.close-btn {
	position: absolute;
	top: 16px;
	right: 16px;
	color: var(--text-secondary, #666) !important;
}

.header-divider {
	border-color: var(--field-border, #f0f0f0);
}

/* Content */
.white-background {
	background: white;
}

.content-container {
	padding: 24px;
	max-height: 60vh;
	overflow-y: auto;
}

/* Empty State */
.empty-state {
	padding: 64px 24px;
	background: white;
}

.empty-icon-wrapper {
	display: inline-block;
	padding: 20px;
	background: rgba(25, 118, 210, 0.1);
	border-radius: 50%;
}

.empty-icon {
	filter: drop-shadow(0 2px 8px rgba(25, 118, 210, 0.3));
}

/* Table Container */
.table-container {
	background: white;
}

.table-header {
	padding: 0 4px;
}

/* Enhanced Table */
.customer-detail-table {
	background: white;
	border: 1px solid #f0f0f0;
	border-radius: 16px;
	overflow: hidden;
}

.customer-detail-table :deep(th) {
	font-weight: 600;
	color: #424242;
	font-size: 0.875rem;
	padding: 16px;
	background: #fafafa;
	border-bottom: 2px solid #f0f0f0;
}

.customer-detail-table :deep(tr) {
	border-bottom: 1px solid #f5f5f5;
}

.customer-detail-table :deep(tr:hover) {
	background-color: rgba(25, 118, 210, 0.02);
}

.customer-detail-table :deep(td) {
	padding: 12px 16px;
	border-bottom: 1px solid #f5f5f5;
}

/* Enhanced Cells */
.section-header {
	display: flex;
	align-items: center;
	font-weight: 600;
	color: #424242;
}

.section-header .v-icon {
	margin-right: 8px;
}

.value-cell {
	font-size: 0.9rem;
	line-height: 1.4;
}

.value-cell.font-weight-medium {
	font-weight: 600;
}

/* Footer */
.dialog-actions-container {
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
	border-top: 1px solid #e0e0e0 !important;
	padding: 16px 24px !important;
	gap: 12px !important;
}

.footer-info {
	display: flex;
	align-items: center;
}

.footer-text {
	font-size: 13px;
	color: #666;
	display: flex;
	align-items: center;
	gap: 6px;
}

/* Standard Buttons */
.standard-btn {
	border-radius: 12px !important;
	text-transform: none !important;
	font-weight: 600 !important;
	height: 44px !important;
	padding: 0 24px !important;
	transition: all 0.3s ease !important;
	min-width: 120px !important;
}

.cancel-btn {
	background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%) !important;
	color: white !important;
}

.cancel-btn:hover {
	transform: translateY(-2px) !important;
	box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4) !important;
}

/* Dark Theme Support */
:deep(.dark-theme) .customer-detail-dialog-card,
:deep(.v-theme--dark) .customer-detail-dialog-card {
	background-color: #1e1e1e !important;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

:deep(.dark-theme) .customer-detail-header,
:deep(.v-theme--dark) .customer-detail-header {
	background-color: #1e1e1e !important;
	color: #fff !important;
	border-bottom-color: #333 !important;
}

:deep(.dark-theme) .header-title,
:deep(.v-theme--dark) .header-title {
	color: #fff !important;
}

:deep(.dark-theme) .header-subtitle,
:deep(.v-theme--dark) .header-subtitle {
	color: #ccc !important;
}

:deep(.dark-theme) .white-background,
:deep(.v-theme--dark) .white-background {
	background-color: #121212 !important;
}

:deep(.dark-theme) .customer-detail-table,
:deep(.v-theme--dark) .customer-detail-table {
	background-color: #121212 !important;
}

:deep(.dark-theme) .customer-detail-table :deep(th),
:deep(.v-theme--dark) .customer-detail-table :deep(th) {
	background-color: #1e1e1e !important;
	color: #fff !important;
	border-bottom-color: #333 !important;
}

:deep(.dark-theme) .customer-detail-table :deep(td),
:deep(.v-theme--dark) .customer-detail-table :deep(td) {
	background-color: #1e1e1e !important;
	color: #fff !important;
	border-bottom-color: #333 !important;
}

:deep(.dark-theme) .section-header,
:deep(.v-theme--dark) .section-header {
	color: #fff !important;
}

:deep(.dark-theme) .dialog-actions-container,
:deep(.v-theme--dark) .dialog-actions-container {
	background: #1e1e1e !important;
	border-top-color: #333 !important;
}

/* Responsive Design */
@media (max-width: 768px) {
	.customer-detail-dialog-card {
		margin: 16px;
		max-height: 85vh;
	}

	.customer-detail-header {
		padding: 16px !important;
	}

	.header-content {
		flex-direction: column;
		align-items: flex-start;
		gap: 16px;
		padding-right: 50px;
	}

	.content-container {
		padding: 16px;
		max-height: 50vh;
	}

	.table-container {
		overflow-x: auto;
	}

	.standard-btn {
		min-width: 100px !important;
		padding: 0 16px !important;
		font-size: 0.875rem !important;
	}
}

@media (max-width: 480px) {
	.header-title {
		font-size: 1.25rem !important;
	}

	.standard-btn {
		height: 40px !important;
		padding: 0 12px !important;
		font-size: 0.8rem !important;
		min-width: 90px !important;
	}
}

/* Scrollbar Styling */
.content-container::-webkit-scrollbar {
	width: 6px;
}

.content-container::-webkit-scrollbar-track {
	background: #f1f1f1;
	border-radius: 3px;
}

.content-container::-webkit-scrollbar-thumb {
	background: #c1c1c1;
	border-radius: 3px;
}

.content-container::-webkit-scrollbar-thumb:hover {
	background: #a8a8a8;
}
</style>