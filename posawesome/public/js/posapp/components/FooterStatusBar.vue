<template>
	<div class="footer-status-bar">
		<div class="status-bar-content">
			<!-- Date and Time -->
			<div class="status-item">
				<v-icon size="16" color="primary">mdi-calendar</v-icon>
				<span class="status-text">{{ currentDate }}</span>
			</div>

			<div class="status-item">
				<v-icon size="16" color="primary">mdi-clock</v-icon>
				<span class="status-text">{{ currentTime }}</span>
			</div>

			<!-- User Account -->
			<div class="status-item">
				<v-icon size="16" :color="userStatusColor">mdi-account-circle</v-icon>
				<span class="status-text">{{ currentUser }}</span>
			</div>

			<!-- Cash Balance -->
			<div class="status-item">
				<v-icon size="16" color="success">mdi-cash</v-icon>
				<span class="status-text">{{ formatCurrency(cashBalance) }}</span>
			</div>

			<!-- Last Invoice -->
			<div class="status-item">
				<v-icon size="16" color="info">mdi-receipt</v-icon>
				<span class="status-text">{{ lastInvoice || __("No invoices") }}</span>
			</div>

			<!-- Today's Sales -->
			<div class="status-item">
				<v-icon size="16" color="warning">mdi-chart-line</v-icon>
				<span class="status-text">{{ formatCurrency(todaySales) }}</span>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: "FooterStatusBar",
	data() {
		return {
			currentDate: "",
			currentTime: "",
			currentUser: "admin", // Default user
			cashBalance: 1250.00,
			lastInvoice: "INV-001",
			todaySales: 2450.00,
			timeInterval: null
		};
	},
	computed: {
		userStatusColor() {
			// You can make this dynamic based on user status
			return "success";
		}
	},
	mounted() {
		this.updateDateTime();
		// Update time every second
		this.timeInterval = setInterval(this.updateDateTime, 1000);

		// Listen for user and sales data updates
		if (this.eventBus) {
			this.eventBus.on("update_user_info", this.updateUserInfo);
			this.eventBus.on("update_sales_data", this.updateSalesData);
			this.eventBus.on("update_cash_balance", this.updateCashBalance);
		}
	},
	beforeUnmount() {
		if (this.timeInterval) {
			clearInterval(this.timeInterval);
		}
		if (this.eventBus) {
			this.eventBus.off("update_user_info", this.updateUserInfo);
			this.eventBus.off("update_sales_data", this.updateSalesData);
			this.eventBus.off("update_cash_balance", this.updateCashBalance);
		}
	},
	methods: {
		updateDateTime() {
			const now = new Date();
			this.currentDate = now.toLocaleDateString('en-US', {
				year: 'numeric',
				month: '2-digit',
				day: '2-digit'
			});
			this.currentTime = now.toLocaleTimeString('en-US', {
				hour12: false,
				hour: '2-digit',
				minute: '2-digit',
				second: '2-digit'
			});
		},

		updateUserInfo(userData) {
			if (userData.name) {
				this.currentUser = userData.name;
			}
		},

		updateSalesData(salesData) {
			if (salesData.todaySales !== undefined) {
				this.todaySales = salesData.todaySales;
			}
			if (salesData.lastInvoice) {
				this.lastInvoice = salesData.lastInvoice;
			}
		},

		updateCashBalance(balance) {
			if (typeof balance === 'number') {
				this.cashBalance = balance;
			}
		},

		formatCurrency(value) {
			if (value === null || value === undefined) return '$0.00';
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: 'USD',
				minimumFractionDigits: 2
			}).format(value);
		}
	}
};
</script>

<style scoped>
.footer-status-bar {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 40px;
	background: linear-gradient(135deg, #343a40 0%, #495057 100%);
	color: white;
	border-top: 2px solid #17a2b8;
	z-index: 1000;
	box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.status-bar-content {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 100%;
	padding: 0 16px;
	gap: 16px;
}

.status-item {
	display: flex;
	align-items: center;
	gap: 6px;
	min-width: 0;
	flex-shrink: 0;
}

.status-item .v-icon {
	flex-shrink: 0;
}

.status-text {
	font-size: 13px;
	font-weight: 500;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	color: #ffffff;
}

/* Responsive design */
@media (max-width: 1024px) {
	.status-bar-content {
		padding: 0 12px;
		gap: 12px;
	}

	.status-text {
		font-size: 12px;
	}
}

@media (max-width: 768px) {
	.footer-status-bar {
		height: 50px;
	}

	.status-bar-content {
		flex-wrap: wrap;
		padding: 4px 12px;
		gap: 8px;
		align-items: center;
		justify-content: center;
	}

	.status-item {
		flex: 1;
		min-width: 80px;
		justify-content: center;
	}

	.status-text {
		font-size: 11px;
	}
}

@media (max-width: 480px) {
	.footer-status-bar {
		height: 60px;
	}

	.status-bar-content {
		flex-direction: column;
		gap: 2px;
		padding: 6px 8px;
	}

	.status-item {
		min-width: 0;
		flex: none;
		justify-content: flex-start;
	}

	.status-text {
		font-size: 10px;
	}
}

/* Dark theme support */
:deep(.dark-theme) .footer-status-bar,
:deep(.v-theme--dark) .footer-status-bar {
	background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
	border-top-color: #17a2b8;
}

:deep(.dark-theme) .status-text,
:deep(.v-theme--dark) .status-text {
	color: #ffffff;
}

/* Hover effects */
.status-item:hover {
	opacity: 0.9;
}

/* Animation for time updates */
.status-text {
	transition: opacity 0.3s ease;
}

.status-text.updating {
	opacity: 0.7;
}
</style>