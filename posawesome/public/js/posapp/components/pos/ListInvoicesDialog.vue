<template>
	<v-dialog v-model="show" max-width="1200px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-receipt-text-multiple</v-icon>
				{{ __("Shift Report Invoices") }}
				<v-spacer></v-spacer>
				<v-btn icon variant="text" @click="close">
					<v-icon>mdi-close</v-icon>
				</v-btn>
			</v-card-title>

			<v-divider></v-divider>

			<v-card-text class="pa-0">
				<!-- Filters Section -->
				<v-row class="pa-4" dense>
					<v-col cols="12" md="3">
						<v-text-field
							v-model="searchQuery"
							:label="__('Search')"
							prepend-inner-icon="mdi-magnify"
							variant="outlined"
							density="compact"
							clearable
							@input="debouncedSearch"
						></v-text-field>
					</v-col>
					<v-col cols="12" md="3">
						<v-select
							v-model="statusFilter"
							:label="__('Status')"
							:items="statusOptions"
							variant="outlined"
							density="compact"
							clearable
							@update:modelValue="applyFilters"
						></v-select>
					</v-col>
					<v-col cols="12" md="3">
						<v-select
							v-model="paymentFilter"
							:label="__('Payment Method')"
							:items="paymentOptions"
							variant="outlined"
							density="compact"
							clearable
							@update:modelValue="applyFilters"
						></v-select>
					</v-col>
					<v-col cols="12" md="3">
						<v-btn
							color="primary"
							variant="outlined"
							prepend-icon="mdi-refresh"
							@click="refreshData"
							:loading="loading"
						>
							{{ __("Refresh") }}
						</v-btn>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Summary Cards -->
				<v-row class="pa-4" dense>
					<v-col cols="12" md="3">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Invoices") }}</div>
							<div class="text-h6 font-weight-bold">{{ summary.total_invoices || 0 }}</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="3">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Sales") }}</div>
							<div class="text-h6 font-weight-bold text-success">
								{{ formatCurrency(summary.total_sales || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="3">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Returns") }}</div>
							<div class="text-h6 font-weight-bold text-error">
								{{ formatCurrency(summary.total_returns || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="3">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Net Amount") }}</div>
							<div class="text-h6 font-weight-bold text-primary">
								{{ formatCurrency((summary.total_sales || 0) - (summary.total_returns || 0)) }}
							</div>
						</v-card>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Data Table -->
				<v-data-table
					v-model:items-per-page="itemsPerPage"
					:headers="headers"
					:items="filteredInvoices"
					:loading="loading"
					:items-length="totalInvoices"
					item-key="invoice_no"
					class="elevation-0"
					density="compact"
					:show-select="false"
				>
					<template #item.invoice_no="{ item }">
						<v-chip
							variant="outlined"
							size="small"
							:color="item.is_return ? 'error' : 'primary'"
						>
							{{ item.invoice_no }}
						</v-chip>
					</template>

					<template #item.customer="{ item }">
						<div class="text-truncate" style="max-width: 150px;">
							{{ item.customer || '-' }}
						</div>
					</template>

					<template #item.total_amount="{ item }">
						<span :class="item.is_return ? 'text-error' : 'text-success'">
							{{ formatCurrency(item.total_amount || 0) }}
						</span>
					</template>

					<template #item.payment_method="{ item }">
						<v-chip
							variant="flat"
							size="small"
							:color="getPaymentColor(item.payment_method)"
						>
							{{ item.payment_method || 'Cash' }}
						</v-chip>
					</template>

					<template #item.status="{ item }">
						<v-chip
							variant="outlined"
							size="small"
							:color="item.status === 'Submitted' ? 'success' : 'warning'"
						>
							{{ item.status }}
						</v-chip>
					</template>

					<template #item.actions="{ item }">
						<v-btn
							icon="mdi-eye"
							size="small"
							variant="text"
							@click="viewInvoice(item)"
							:title="__('View Invoice')"
						></v-btn>
						<v-btn
							icon="mdi-printer"
							size="small"
							variant="text"
							@click="printInvoice(item)"
							:title="__('Print Invoice')"
						></v-btn>
					</template>
				</v-data-table>
			</v-card-text>

			<v-divider></v-divider>

			<v-card-actions class="pa-4">
				<v-spacer></v-spacer>
				<v-btn variant="text" @click="close">
					{{ __("Close") }}
				</v-btn>
				<v-btn
					color="primary"
					variant="flat"
					prepend-icon="mdi-download"
					@click="exportData"
				>
					{{ __("Export") }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: "ListInvoicesDialog",
	props: {
		modelValue: {
			type: Boolean,
			default: false
		},
		shiftReportId: {
			type: String,
			default: ""
		}
	},
	emits: ["update:modelValue"],
	data() {
		return {
			loading: false,
			searchQuery: "",
			statusFilter: "",
			paymentFilter: "",
			itemsPerPage: 10,
			totalInvoices: 0,
			invoices: [],
			summary: {
				total_invoices: 0,
				total_sales: 0,
				total_returns: 0
			},
			headers: [
				{ title: this.__("Invoice No"), key: "invoice_no", width: "120px" },
				{ title: this.__("Date"), key: "invoice_date", width: "100px" },
				{ title: this.__("Time"), key: "invoice_time", width: "80px" },
				{ title: this.__("Customer"), key: "customer", width: "150px" },
				{ title: this.__("Amount"), key: "total_amount", width: "120px", align: "end" },
				{ title: this.__("Payment"), key: "payment_method", width: "100px" },
				{ title: this.__("Status"), key: "status", width: "100px" },
				{ title: this.__("Actions"), key: "actions", width: "120px", sortable: false }
			],
			statusOptions: [
				{ title: this.__("Submitted"), value: "Submitted" },
				{ title: this.__("Cancelled"), value: "Cancelled" }
			],
			paymentOptions: [
				{ title: this.__("Cash"), value: "Cash" },
				{ title: this.__("Card"), value: "Card" },
				{ title: this.__("M-Pesa"), value: "M-Pesa" }
			]
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
		filteredInvoices() {
			let filtered = [...this.invoices];

			// Search filter
			if (this.searchQuery) {
				const query = this.searchQuery.toLowerCase();
				filtered = filtered.filter(item =>
					item.invoice_no?.toLowerCase().includes(query) ||
					item.customer?.toLowerCase().includes(query)
				);
			}

			// Status filter
			if (this.statusFilter) {
				filtered = filtered.filter(item => item.status === this.statusFilter);
			}

			// Payment filter
			if (this.paymentFilter) {
				filtered = filtered.filter(item => item.payment_method === this.paymentFilter);
			}

			return filtered;
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal && this.shiftReportId) {
				this.loadInvoices();
			}
		}
	},
	mounted() {
		this.debouncedSearch = this.debounce(this.applyFilters, 300);
	},
	methods: {
		async loadInvoices() {
			if (!this.shiftReportId) return;

			this.loading = true;
			try {
				// Mock data for now - will be replaced with real API call
				this.invoices = [
					{
						invoice_no: "INV-001",
						invoice_date: "2025-01-09",
						invoice_time: "14:30:00",
						customer: "John Doe",
						total_amount: 150.00,
						paid_amount: 150.00,
						tax_amount: 15.00,
						payment_method: "Cash",
						is_return: false,
						status: "Submitted"
					},
					{
						invoice_no: "INV-002",
						invoice_date: "2025-01-09",
						invoice_time: "15:45:00",
						customer: "Jane Smith",
						total_amount: 75.50,
						paid_amount: 75.50,
						tax_amount: 7.55,
						payment_method: "Card",
						is_return: false,
						status: "Submitted"
					},
					{
						invoice_no: "RTN-001",
						invoice_date: "2025-01-09",
						invoice_time: "16:20:00",
						customer: "Bob Johnson",
						total_amount: -25.00,
						paid_amount: -25.00,
						tax_amount: -2.50,
						payment_method: "Cash",
						is_return: true,
						status: "Submitted"
					}
				];

				this.calculateSummary();
				this.totalInvoices = this.invoices.length;

			} catch (error) {
				console.error("Error loading invoices:", error);
				this.showError("Failed to load invoices");
			} finally {
				this.loading = false;
			}
		},

		calculateSummary() {
			this.summary = {
				total_invoices: this.invoices.length,
				total_sales: this.invoices
					.filter(inv => !inv.is_return)
					.reduce((sum, inv) => sum + (inv.total_amount || 0), 0),
				total_returns: Math.abs(this.invoices
					.filter(inv => inv.is_return)
					.reduce((sum, inv) => sum + (inv.total_amount || 0), 0))
			};
		},

		applyFilters() {
			// Filters are applied automatically through computed property
		},

		debounce(func, delay) {
			let timeoutId;
			return function (...args) {
				clearTimeout(timeoutId);
				timeoutId = setTimeout(() => func.apply(this, args), delay);
			};
		},

		getPaymentColor(paymentMethod) {
			const colors = {
				"Cash": "success",
				"Card": "primary",
				"M-Pesa": "info"
			};
			return colors[paymentMethod] || "grey";
		},

		formatCurrency(amount) {
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: 'USD'
			}).format(amount);
		},

		viewInvoice(invoice) {
			// Open invoice in new window/tab
			const url = `/app/sales-invoice/${invoice.invoice_no}`;
			window.open(url, '_blank');
		},

		printInvoice(invoice) {
			// Print invoice
			const url = `/app/print/Sales%20Invoice/${invoice.invoice_no}`;
			window.open(url, '_blank');
		},

		async exportData() {
			try {
				// Export filtered data to CSV
				const data = this.filteredInvoices.map(item => ({
					"Invoice No": item.invoice_no,
					"Date": item.invoice_date,
					"Time": item.invoice_time,
					"Customer": item.customer,
					"Amount": item.total_amount,
					"Payment Method": item.payment_method,
					"Status": item.status
				}));

				// Create CSV content
				const headers = Object.keys(data[0] || {});
				const csvContent = [
					headers.join(','),
					...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
				].join('\n');

				// Download CSV
				const blob = new Blob([csvContent], { type: 'text/csv' });
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = `shift_report_invoices_${this.shiftReportId}_${new Date().toISOString().split('T')[0]}.csv`;
				a.click();
				window.URL.revokeObjectURL(url);

			} catch (error) {
				console.error("Error exporting data:", error);
				this.showError("Failed to export data");
			}
		},

		async refreshData() {
			await this.loadInvoices();
		},

		showError(message) {
			// Show error message using Frappe's toast or similar
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({ message, indicator: 'red' });
			} else {
				alert(message);
			}
		},

		close() {
			this.show = false;
			this.resetFilters();
		},

		resetFilters() {
			this.searchQuery = "";
			this.statusFilter = "";
			this.paymentFilter = "";
		}
	}
};
</script>

<style scoped>
.v-data-table {
	border: none;
}

.v-data-table :deep(.v-data-table__td) {
	border-bottom: 1px solid rgb(var(--v-theme-surface-variant));
}

.v-data-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-surface));
	font-weight: 600;
	border-bottom: 2px solid rgb(var(--v-theme-primary));
}
</style>