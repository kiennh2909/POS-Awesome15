<template>
	<div class="footer-status-bar">
		<div class="status-bar-content">
			<!-- Current Date -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-calendar</v-icon>
				<span class="status-text">{{ currentDate }}</span>
			</div>

			<!-- System Time -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-clock-outline</v-icon>
				<span class="status-text">{{ currentTime }}</span>
			</div>

			<!-- Cashier Name -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-account-circle</v-icon>
				<span class="status-text">{{ cashierName || __("No Cashier") }}</span>
			</div>

			<!-- POS Shift Report ID -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-clipboard-text</v-icon>
				<span class="status-text">{{ shiftReportId || __("No Shift") }}</span>
			</div>

			<!-- Cash Balance -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-cash</v-icon>
				<span class="status-text">Cash: {{ formatCurrency(cashBalance || 0) }}</span>
			</div>

			<!-- Last Invoice -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-receipt</v-icon>
				<span class="status-text">{{ lastInvoice || __("No invoices") }}</span>
			</div>

			<!-- Today's Sales -->
			<div class="status-item">
				<v-icon size="16" color="white">mdi-chart-line</v-icon>
				<span class="status-text">Today: {{ formatCurrency(todaySales || 0) }}</span>
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
			cashierName: "",
			shiftReportId: "",
			cashBalance: 0,
			lastInvoice: "",
			todaySales: 0,
			currency: "VND",  // Add currency property
			timeInterval: null,
			shiftReportData: null
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

		// Load initial data
		this.loadInitialData();

		// Listen for events
		if (this.eventBus) {
			this.eventBus.on("register_pos_profile", this.handlePosProfileUpdate);
			this.eventBus.on("register_shift_report", this.updateShiftReport);
			this.eventBus.on("set_last_invoice", this.updateLastInvoice);
			this.eventBus.on("update_sales_data", this.handleSalesDataUpdate);
		}
	},
	beforeUnmount() {
		if (this.timeInterval) {
			clearInterval(this.timeInterval);
		}
		if (this.eventBus) {
			this.eventBus.off("register_pos_profile", this.handlePosProfileUpdate);
			this.eventBus.off("register_shift_report", this.updateShiftReport);
			this.eventBus.off("set_last_invoice", this.updateLastInvoice);
			this.eventBus.off("update_sales_data", this.handleSalesDataUpdate);
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

		async loadInitialData() {
			try {
				// Load current user
				this.cashierName = frappe.session.user_fullname || frappe.session.user || "Unknown";

				// Load shift report data
				await this.loadShiftReportData();

			} catch (error) {
				console.error("Error loading initial data:", error);
			}
		},

		async loadShiftReportData() {
			try {
				// Get footer status data from new API
				const result = await frappe.call("posawesome.posawesome.api.shift_reports.get_footer_status_data");

				if (result.message && result.message.success) {
					const data = result.message.data;
					this.updateFooterData(data);
				} else {
					console.warn("No footer status data found");
				}
			} catch (error) {
				console.error("Error loading footer status data:", error);
			}
		},

		handlePosProfileUpdate(posProfileData) {
			if (posProfileData && posProfileData.pos_opening_shift) {
				// Load footer data when POS profile is registered
				this.loadShiftReportData();
			}
		},

		updateShiftReport(shiftReportData) {
			if (shiftReportData) {
				this.updateShiftReportData(shiftReportData);
			}
		},

		updateFooterData(data) {
			if (data) {
				this.cashierName = data.cashier_name || "";
				this.currentDate = data.current_date || "";
				this.currentTime = data.current_time || "";
				this.shiftReportId = data.shift_report_id || "";
				this.cashBalance = data.cash_balance || 0;
				this.lastInvoice = data.last_invoice || "";
				this.todaySales = data.today_sales || 0;
				this.currency = data.currency || "VND";  // Add currency from API
			}
		},

		updateShiftReportData(data) {
			this.shiftReportData = data;
			this.todaySales = data.total_sales || 0;

			// Update last invoice from shift report data
			if (data.invoices && data.invoices.length > 0) {
				const lastInvoiceData = data.invoices[data.invoices.length - 1];
				this.lastInvoice = lastInvoiceData.invoice_no || "";
			}
		},

		updateLastInvoice(invoiceId) {
			this.lastInvoice = invoiceId || "";
		},

		handleSalesDataUpdate(salesData) {
			// Reload footer data when sales data changes
			if (salesData) {
				this.loadShiftReportData();
			}
		},

		formatCurrency(value) {
			if (value === null || value === undefined) return `${this.currency}0`;

			// Use different formatting based on currency
			if (this.currency === 'USD' || this.currency === '$') {
				return new Intl.NumberFormat('en-US', {
					style: 'currency',
					currency: 'USD',
					minimumFractionDigits: 2
				}).format(value);
			} else if (this.currency === 'VND' || this.currency === '₫') {
				return new Intl.NumberFormat('vi-VN', {
					style: 'currency',
					currency: 'VND',
					minimumFractionDigits: 0
				}).format(value);
			} else {
				// Generic formatting for other currencies
				return `${this.currency}${value.toLocaleString()}`;
			}
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
	height: 45px;
	background: #000000;
	color: white;
	border-top: 2px solid #ffffff;
	z-index: 1000;
	box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3);
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
		height: 55px;
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
		height: 65px;
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
	background: #000000;
	border-top-color: #ffffff;
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