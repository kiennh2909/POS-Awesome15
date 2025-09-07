<template>
	<v-row justify="center">
		<v-dialog v-model="dialog" max-width="1200px" persistent>
			<v-card>
				<v-card-title class="primary white--text">
					<span class="text-h5">{{ __("Customer Details") }}</span>
					<v-spacer></v-spacer>
					<v-btn icon color="white" @click="dialog = false">
						<v-icon>mdi-close</v-icon>
					</v-btn>
				</v-card-title>

				<v-card-text class="pa-0">
					<v-container fluid v-if="customerData">
						<v-row>
							<!-- 1. Thông tin cơ bản -->
							<v-col cols="12" md="6">
								<v-card class="mb-4">
									<v-card-title class="secondary white--text">
										<v-icon left>mdi-account</v-icon>
										{{ __("Basic Information") }}
									</v-card-title>
									<v-card-text>
										<v-row dense>
											<v-col cols="6">
												<strong>{{ __("Customer ID") }}:</strong>
												<div>{{ customerData.basic_info.customer_id }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Customer Name") }}:</strong>
												<div>{{ customerData.basic_info.customer_name }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Mobile No") }}:</strong>
												<div>{{ customerData.basic_info.mobile_no || __("Not provided") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Email") }}:</strong>
												<div>{{ customerData.basic_info.email_id || __("Not provided") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Tax ID") }}:</strong>
												<div>{{ customerData.basic_info.tax_id || __("Not provided") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("City") }}:</strong>
												<div>{{ customerData.basic_info.city || __("Not provided") }}</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- 2. Thông tin phân loại -->
							<v-col cols="12" md="6">
								<v-card class="mb-4">
									<v-card-title class="info white--text">
										<v-icon left>mdi-tag</v-icon>
										{{ __("Classification") }}
									</v-card-title>
									<v-card-text>
										<v-row dense>
											<v-col cols="6">
												<strong>{{ __("Customer Type") }}:</strong>
												<div>{{ customerData.classification_info.customer_type || __("Not specified") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Customer Group") }}:</strong>
												<div>{{ customerData.classification_info.customer_group || __("Not specified") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Territory") }}:</strong>
												<div>{{ customerData.classification_info.territory || __("Not specified") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Gender") }}:</strong>
												<div>{{ customerData.classification_info.gender || __("Not specified") }}</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- 3. Thông tin Credit -->
							<v-col cols="12" md="6">
								<v-card class="mb-4">
									<v-card-title class="success white--text">
										<v-icon left>mdi-credit-card</v-icon>
										{{ __("Credit Information") }}
									</v-card-title>
									<v-card-text>
										<v-row dense>
											<v-col cols="6">
												<strong>{{ __("Credit Limit") }}:</strong>
												<div class="text-success">{{ formatCurrency(customerData.credit_info.credit_limit) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Outstanding Amount") }}:</strong>
												<div class="text-warning">{{ formatCurrency(customerData.credit_info.outstanding_amount) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Credit Balance") }}:</strong>
												<div :class="customerData.credit_info.credit_balance >= 0 ? 'text-success' : 'text-error'">
													{{ formatCurrency(customerData.credit_info.credit_balance) }}
												</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Payment Terms") }}:</strong>
												<div>{{ customerData.credit_info.payment_terms || __("Not specified") }}</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- 4. Thông tin Loyalty -->
							<v-col cols="12" md="6">
								<v-card class="mb-4">
									<v-card-title class="purple white--text">
										<v-icon left>mdi-star</v-icon>
										{{ __("Loyalty Points") }}
									</v-card-title>
									<v-card-text>
										<v-row dense>
											<v-col cols="6">
												<strong>{{ __("Loyalty Program") }}:</strong>
												<div>{{ customerData.loyalty_info.loyalty_program || __("Not enrolled") }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Total Points") }}:</strong>
												<div class="text-primary">{{ formatNumber(customerData.loyalty_info.loyalty_points) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Points Used") }}:</strong>
												<div class="text-orange">{{ formatNumber(customerData.loyalty_info.loyalty_points_used) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Points Balance") }}:</strong>
												<div class="text-success">{{ formatNumber(customerData.loyalty_info.loyalty_points_balance) }}</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- 5. Công nợ -->
							<v-col cols="12" md="6">
								<v-card class="mb-4">
									<v-card-title class="orange white--text">
										<v-icon left>mdi-cash-multiple</v-icon>
										{{ __("Debt Information") }}
									</v-card-title>
									<v-card-text>
										<v-row dense>
											<v-col cols="6">
												<strong>{{ __("Total Debt Generated") }}:</strong>
												<div class="text-error">{{ formatCurrency(customerData.debt_info.total_debt_generated) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Total Paid") }}:</strong>
												<div class="text-success">{{ formatCurrency(customerData.debt_info.total_paid) }}</div>
											</v-col>
											<v-col cols="12">
												<strong>{{ __("Remaining Debt") }}:</strong>
												<div :class="customerData.debt_info.remaining_debt > 0 ? 'text-error' : 'text-success'">
													{{ formatCurrency(customerData.debt_info.remaining_debt) }}
												</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- 6. Thống kê -->
							<v-col cols="12" md="6">
								<v-card class="mb-4">
									<v-card-title class="teal white--text">
										<v-icon left>mdi-chart-bar</v-icon>
										{{ __("Customer Statistics") }}
									</v-card-title>
									<v-card-text>
										<v-row dense>
											<v-col cols="6">
												<strong>{{ __("Total Orders") }}:</strong>
												<div class="text-primary">{{ formatNumber(customerData.statistics_info.total_orders) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Total GMV") }}:</strong>
												<div class="text-success">{{ formatCurrency(customerData.statistics_info.total_gmv) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Paid Orders") }}:</strong>
												<div class="text-success">{{ formatNumber(customerData.statistics_info.total_paid_orders) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Return Orders") }}:</strong>
												<div class="text-error">{{ formatNumber(customerData.statistics_info.total_return_orders) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Avg Order Value") }}:</strong>
												<div>{{ formatCurrency(customerData.statistics_info.avg_order_value) }}</div>
											</v-col>
											<v-col cols="6">
												<strong>{{ __("Last Order Date") }}:</strong>
												<div>{{ customerData.statistics_info.last_order_date || __("No orders yet") }}</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>
						</v-row>
					</v-container>

					<!-- Loading state -->
					<v-container v-else class="text-center py-12">
						<v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
						<p class="mt-4">{{ __("Loading customer details...") }}</p>
					</v-container>
				</v-card-text>

				<v-card-actions class="justify-end">
					<v-btn color="primary" @click="dialog = false">
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
	data() {
		return {
			dialog: this.modelValue,
			customerData: null,
			loading: false,
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
.v-card-title {
	font-weight: 600;
}

.v-card-text strong {
	display: block;
	margin-bottom: 4px;
	font-size: 0.875rem;
	color: rgba(0, 0, 0, 0.6);
}

.v-card-text div {
	font-size: 0.9rem;
	margin-bottom: 8px;
}
</style>