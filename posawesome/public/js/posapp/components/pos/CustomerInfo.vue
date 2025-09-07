<template>
	<div class="customer-info-section">
		<!-- Customer Info Header -->
		<div class="customer-info-header">
			<div class="header-icon">
				<v-icon size="20" color="primary">mdi-account-details</v-icon>
			</div>
			<div class="header-text">
				<h4 class="header-title">{{ __("Customer Information") }}</h4>
			</div>
		</div>

		<!-- Customer Basic Info Row -->
		<div class="customer-basic-row" v-if="customerData">
			<div class="customer-id-chip">
				<v-chip
					color="primary"
					variant="tonal"
					size="small"
					class="id-chip"
				>
					<v-icon start size="14">mdi-identifier</v-icon>
					{{ customerData.customer_id || __("No ID") }}
				</v-chip>
			</div>
			<div class="customer-tier-chip">
				<v-chip
					:color="getTierColor(customerData.membership_tier)"
					variant="tonal"
					size="small"
					class="tier-chip"
				>
					<v-icon start size="14">mdi-crown</v-icon>
					{{ customerData.membership_tier || __("Standard") }}
				</v-chip>
			</div>
			<div class="customer-card-chip">
				<v-chip
					color="info"
					variant="tonal"
					size="small"
					class="card-chip"
				>
					<v-icon start size="14">mdi-credit-card</v-icon>
					{{ customerData.card_number || __("No Card") }}
				</v-chip>
			</div>
		</div>

		<!-- VIP Status Section -->
		<div class="vip-status-section" v-if="customerData && customerData.vip_info">
			<div class="vip-status-grid">
				<!-- VIP Badge -->
				<div class="vip-badge-item">
					<v-chip
						color="purple"
						variant="flat"
						size="small"
						class="vip-chip"
					>
						<v-icon start size="14">mdi-star</v-icon>
						{{ customerData.vip_info.is_vip ? __("VIP") : __("Standard") }}
					</v-chip>
				</div>

				<!-- Credit Limit -->
				<div class="credit-item">
					<div class="credit-label">{{ __("Credit Limit") }}</div>
					<div class="credit-value">{{ formatCurrency(customerData.vip_info.credit_limit) }}</div>
				</div>

				<!-- Credit Balance -->
				<div class="credit-item">
					<div class="credit-label">{{ __("Credit Balance") }}</div>
					<div class="credit-value">{{ formatCurrency(customerData.vip_info.credit_balance) }}</div>
				</div>

				<!-- Loyalty Points -->
				<div class="loyalty-item">
					<div class="loyalty-label">{{ __("Loyalty Points") }}</div>
					<div class="loyalty-value">{{ formatNumber(customerData.vip_info.loyalty_points) }}</div>
				</div>

				<!-- Available Points -->
				<div class="loyalty-item">
					<div class="loyalty-label">{{ __("Available Points") }}</div>
					<div class="loyalty-value">{{ formatNumber(customerData.vip_info.available_points) }}</div>
				</div>

				<!-- Total Debt -->
				<div class="debt-item">
					<div class="debt-label">{{ __("Total Debt") }}</div>
					<div class="debt-value">{{ formatCurrency(customerData.vip_info.total_debt) }}</div>
				</div>
			</div>
		</div>

		<!-- Empty State -->
		<div v-else class="empty-customer-state">
			<v-icon size="48" color="grey-lighten-1">mdi-account-question</v-icon>
			<p class="empty-text">{{ __("No customer selected") }}</p>
		</div>
	</div>
</template>

<script>
import format from "../../format";

export default {
	name: "CustomerInfo",
	mixins: [format],
	props: {
		customerId: {
			type: String,
			default: ""
		}
	},
	data() {
		return {
			customerData: null,
			loading: false
		};
	},
	watch: {
		customerId: {
			handler(newVal) {
				if (newVal) {
					this.loadCustomerInfo(newVal);
				} else {
					this.customerData = null;
				}
			},
			immediate: true
		}
	},
	methods: {
		async loadCustomerInfo(customerId) {
			if (!customerId) return;

			this.loading = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_detailed_info",
					args: {
						customer: customerId,
					},
				});

				if (response.message) {
					this.customerData = this.formatCustomerData(response.message);
				}
			} catch (error) {
				console.error("Error loading customer info:", error);
				this.customerData = null;
			} finally {
				this.loading = false;
			}
		},

		formatCustomerData(data) {
			return {
				customer_id: data.basic_info?.customer_id || data.basic_info?.name,
				membership_tier: data.classification_info?.customer_group || "Standard",
				card_number: data.basic_info?.tax_id || "N/A",
				vip_info: {
					is_vip: data.classification_info?.customer_type === "VIP",
					credit_limit: data.credit_info?.credit_limit || 0,
					credit_balance: data.credit_info?.credit_balance || 0,
					loyalty_points: data.loyalty_info?.loyalty_points || 0,
					available_points: data.loyalty_info?.loyalty_points_balance || 0,
					total_debt: data.debt_info?.remaining_debt || 0
				}
			};
		},

		getTierColor(tier) {
			const colors = {
				'GOLD': 'warning',
				'PLATINUM': 'info',
				'DIAMOND': 'success',
				'VIP': 'purple'
			};
			return colors[tier?.toUpperCase()] || 'grey';
		},

		formatCurrency(value) {
			if (!value) return '$0.00';
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: 'USD'
			}).format(value);
		},

		formatNumber(value) {
			return new Intl.NumberFormat().format(value || 0);
		}
	}
};
</script>

<style scoped>
/* Custom styling for specific component instance */
.customer-info-section {
    padding: 10px;
    background: #f0e6e6;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin-bottom: 10px;
}

.customer-info-header {
	display: flex;
	align-items: center;
	gap: 12px;
	margin-bottom: 10px;
	padding-bottom: 8px;
	border-bottom: 1px solid #f0f0f0;
}

.header-icon {
	background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
	border-radius: 8px;
	padding: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.header-title {
	margin: 0;
	font-size: 1.1rem;
	font-weight: 600;
	color: #424242;
}

.customer-basic-row {
	display: flex;
	gap: 8px;
	margin-bottom: 16px;
	flex-wrap: wrap;
}

.id-chip, .tier-chip, .card-chip {
	font-weight: 600;
}

.vip-status-section {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-radius: 8px;
	padding: 16px;
	border: 1px solid #dee2e6;
}

.vip-status-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
	gap: 12px;
}

.vip-badge-item {
	display: flex;
	align-items: center;
	justify-content: center;
}

.vip-chip {
	font-weight: 700;
	font-size: 0.9rem;
	width: 100%;
	justify-content: center;
}

.credit-item, .loyalty-item, .debt-item {
	background: white;
	border-radius: 6px;
	padding: 8px 12px;
	border: 1px solid #e0e0e0;
	text-align: center;
}

.credit-label, .loyalty-label, .debt-label {
	font-size: 0.8rem;
	color: #666;
	margin-bottom: 4px;
	font-weight: 500;
}

.credit-value, .loyalty-value, .debt-value {
	font-size: 1rem;
	font-weight: 700;
	color: #424242;
}

.credit-value {
	color: #2e7d32;
}

.loyalty-value {
	color: #f57c00;
}

.debt-value {
	color: #d32f2f;
}

.empty-customer-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 32px 16px;
	text-align: center;
}

.empty-text {
	margin: 16px 0 0 0;
	color: #9e9e9e;
	font-size: 0.9rem;
}

/* Dark theme support */
:deep(.dark-theme) .customer-info-section,
:deep(.v-theme--dark) .customer-info-section {
	background-color: #1e1e1e;
	border-color: #333;
}

:deep(.dark-theme) .header-title,
:deep(.v-theme--dark) .header-title {
	color: #fff;
}

:deep(.dark-theme) .vip-status-section,
:deep(.v-theme--dark) .vip-status-section {
	background: linear-gradient(135deg, #2a2a2a 0%, #333 100%);
	border-color: #444;
}

:deep(.dark-theme) .credit-item,
:deep(.dark-theme) .loyalty-item,
:deep(.dark-theme) .debt-item,
:deep(.v-theme--dark) .credit-item,
:deep(.v-theme--dark) .loyalty-item,
:deep(.v-theme--dark) .debt-item {
	background-color: #2a2a2a;
	border-color: #444;
}

:deep(.dark-theme) .credit-label,
:deep(.dark-theme) .loyalty-label,
:deep(.dark-theme) .debt-label,
:deep(.v-theme--dark) .credit-label,
:deep(.v-theme--dark) .loyalty-label,
:deep(.v-theme--dark) .debt-label {
	color: #ccc;
}

:deep(.dark-theme) .credit-value,
:deep(.dark-theme) .loyalty-value,
:deep(.dark-theme) .debt-value,
:deep(.v-theme--dark) .credit-value,
:deep(.v-theme--dark) .loyalty-value,
:deep(.v-theme--dark) .debt-value {
	color: #fff;
}

/* Responsive design */
@media (max-width: 768px) {
	.customer-basic-row {
		flex-direction: column;
		gap: 6px;
	}

	.vip-status-grid {
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 8px;
	}

	.customer-info-section {
		padding: 12px;
	}
}

@media (max-width: 480px) {
	.vip-status-grid {
		grid-template-columns: 1fr;
	}

	.customer-info-header {
		flex-direction: column;
		text-align: center;
		gap: 8px;
	}
}
</style>