<template>
	<v-dialog v-model="show" max-width="1400px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-view-list</v-icon>
				<div class="header-content">
					<div class="header-main">
						<h3 class="header-title">{{ __("List Shifts") }}</h3>
						<div class="shift-info" v-if="selectedDate">
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Date:") }}</span>
								<span class="shift-info-value">{{ formatDate(selectedDate) }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("POS Profile:") }}</span>
								<span class="shift-info-value">{{ posProfile?.name || 'N/A' }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("User Role:") }}</span>
								<span class="shift-info-value">{{ userRole === 'Sales Manager' ? 'Manager' : 'Sales Person' }}</span>
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
				<!-- Filters Section -->
				<div class="pa-4 filters-section">
					<v-row dense>
						<v-col cols="12" md="4">
							<v-text-field
								v-model="selectedDate"
								:label="__('Select Date')"
								type="date"
								variant="outlined"
								density="compact"
								:max="new Date().toISOString().split('T')[0]"
								@change="loadShifts"
								class="date-filter"
							/>
						</v-col>
						<v-col cols="12" md="4">
							<v-text-field
								v-model="searchQuery"
								:label="__('Search by Shift ID or Cashier')"
								prepend-inner-icon="mdi-magnify"
								variant="outlined"
								density="compact"
								clearable
								@input="debouncedSearch"
								class="search-filter"
							/>
						</v-col>
						<v-col cols="12" md="4">
							<v-select
								v-model="statusFilter"
								:label="__('Filter by Status')"
								:items="statusOptions"
								variant="outlined"
								density="compact"
								clearable
								class="status-filter"
							/>
						</v-col>
					</v-row>
				</div>

				<v-divider></v-divider>

				<!-- Summary Cards -->
				<v-row class="pa-4" dense>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Shifts") }}</div>
							<div class="text-h6 font-weight-bold">{{ summary.total_shifts || 0 }}</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Sales") }}</div>
							<div class="text-h6 font-weight-bold text-success">
								{{ formatCurrency(summary.total_sales || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Returns") }}</div>
							<div class="text-h6 font-weight-bold text-error">
								{{ formatCurrency(summary.total_returns || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Opening Amount") }}</div>
							<div class="text-h6 font-weight-bold text-primary">
								{{ formatCurrency(summary.total_opening || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Expected Closing") }}</div>
							<div class="text-h6 font-weight-bold text-info">
								{{ formatCurrency(summary.total_expected_closing || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Actual Closing") }}</div>
							<div class="text-h6 font-weight-bold text-warning">
								{{ formatCurrency(summary.total_actual_closing || 0) }}
							</div>
						</v-card>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Data Table -->
				<v-data-table
					:headers="headers"
					:items="filteredShifts"
					:loading="loading"
					:items-length="totalShifts"
					item-key="name"
					class="elevation-0"
					density="compact"
					:show-select="false"
					:items-per-page-options="[10, 25, 50]"
					:items-per-page="itemsPerPage"
				>
					<template #item.shift_id="{ item }">
						<v-chip
							variant="outlined"
							size="small"
							color="primary"
						>
							{{ item.shift_id || item.name }}
						</v-chip>
					</template>

					<template #item.opening_time="{ item }">
						<div class="text-caption">
							{{ formatDateTime(item.opening_date, item.opening_time) }}
						</div>
					</template>

					<template #item.user="{ item }">
						<div class="text-truncate" style="max-width: 120px;">
							{{ item.user_fullname || item.user || '-' }}
						</div>
					</template>

					<template #item.total_invoices="{ item }">
						<span class="text-center">{{ item.invoice_count || 0 }}</span>
					</template>

					<template #item.total_sales="{ item }">
						<span class="text-success font-weight-medium">
							{{ formatCurrency(item.total_sales || 0) }}
						</span>
					</template>

					<template #item.total_opening="{ item }">
						<span class="text-primary">
							{{ formatCurrency(item.total_opening || 0) }}
						</span>
					</template>

					<template #item.total_returns="{ item }">
						<span class="text-error">
							{{ formatCurrency(item.total_returns || 0) }}
						</span>
					</template>

					<template #item.expected_closing_amount="{ item }">
						<span class="text-info">
							{{ formatCurrency(item.expected_closing_amount || 0) }}
						</span>
					</template>

					<template #item.actual_closing_amount="{ item }">
						<span class="text-warning">
							{{ formatCurrency(item.actual_closing_amount || 0) }}
						</span>
					</template>

					<template #item.closing_date="{ item }">
						<div class="text-caption">
							{{ item.closing_date ? formatDateTime(item.closing_date, item.closing_time) : '-' }}
						</div>
					</template>

					<template #item.status="{ item }">
						<v-chip
							variant="flat"
							size="small"
							:color="getStatusColor(item.status)"
						>
							{{ getStatusText(item.status) }}
						</v-chip>
					</template>

					<template #item.actions="{ item }">
						<v-btn
							icon="mdi-eye"
							size="small"
							variant="text"
							@click="viewShiftDetails(item)"
							:title="__('View Shift Details')"
						></v-btn>
					</template>
				</v-data-table>
			</v-card-text>

			<v-divider></v-divider>

			<!-- ListInvoicesDialog Integration -->
			<ListInvoicesDialog
				v-model="showListInvoicesDialog"
				:shift-report-id="selectedShift"
				:pos-profile="posProfile"
			/>
		</v-card>
	</v-dialog>
</template>

<script>
import ListInvoicesDialog from './ListInvoicesDialog.vue';

export default {
	name: "ListShiftsDialog",
	components: {
		ListInvoicesDialog
	},
	props: {
		modelValue: {
			type: Boolean,
			default: false
		},
		posProfile: {
			type: Object,
			default: () => ({})
		}
	},
	emits: ["update:modelValue"],
	data() {
		return {
			loading: false,
			selectedDate: new Date().toISOString().split('T')[0], // Today by default
			searchQuery: "",
			statusFilter: "",
			shifts: [],
			totalShifts: 0,
			itemsPerPage: 10,
			userRole: null, // 'Sales Person' or 'Sales Manager'
			summary: {
				total_shifts: 0,
				total_sales: 0,
				total_returns: 0,
				total_opening: 0,
				total_expected_closing: 0,
				total_actual_closing: 0
			},
			headers: [
				{ title: this.__("Shift ID"), key: "shift_id", width: "120px" },
				{ title: this.__("Started"), key: "opening_time", width: "140px" },
				{ title: this.__("Cashier"), key: "user", width: "120px" },
				{ title: this.__("Total Invoices"), key: "total_invoices", width: "100px", align: "center" },
				{ title: this.__("Total Sales"), key: "total_sales", width: "120px", align: "end" },
				{ title: this.__("Opening"), key: "total_opening", width: "120px", align: "end" },
				{ title: this.__("Returns"), key: "total_returns", width: "120px", align: "end" },
				{ title: this.__("Expected Closing"), key: "expected_closing_amount", width: "130px", align: "end" },
				{ title: this.__("Actual Closing"), key: "actual_closing_amount", width: "130px", align: "end" },
				{ title: this.__("Closed"), key: "closing_date", width: "140px" },
				{ title: this.__("Status"), key: "status", width: "100px" },
				{ title: this.__("Actions"), key: "actions", width: "80px", sortable: false }
			],
			statusOptions: [
				{ title: this.__("Open"), value: "Open" },
				{ title: this.__("Closed"), value: "Closed" },
				{ title: this.__("Verified"), value: "Verified" }
			],
			// ListInvoicesDialog integration
			showListInvoicesDialog: false,
			selectedShift: null
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
		filteredShifts() {
			let filtered = [...this.shifts];

			// Search filter
			if (this.searchQuery) {
				const query = this.searchQuery.toLowerCase();
				filtered = filtered.filter(item =>
					(item.shift_id || item.name)?.toLowerCase().includes(query) ||
					(item.user_fullname || item.user)?.toLowerCase().includes(query)
				);
			}

			// Status filter
			if (this.statusFilter) {
				filtered = filtered.filter(item => item.status === this.statusFilter);
			}

			return filtered;
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal) {
				this.initializeDialog();
			}
		},
		statusFilter() {
			// Auto-filter when status changes
		}
	},
	mounted() {
		this.debouncedSearch = this.debounce(this.applyFilters, 300);
		this.checkUserRole();
	},
	methods: {
		async initializeDialog() {
			await this.checkUserRole();
			await this.loadShifts();
		},

		async checkUserRole() {
			try {
				// Check if user has Sales Manager role
				const roles = frappe.user_roles || [];
				this.userRole = roles.includes('Sales Manager') ? 'Sales Manager' : 'Sales Person';
				console.log("[LIST_SHIFTS] User role determined:", this.userRole);
			} catch (error) {
				console.error("[LIST_SHIFTS] Error checking user role:", error);
				this.userRole = 'Sales Person'; // Default fallback
			}
		},

		async loadShifts() {
			if (!this.selectedDate || !this.posProfile?.name) {
				console.warn("[LIST_SHIFTS] Missing required data:", { selectedDate: this.selectedDate, posProfile: this.posProfile });
				return;
			}

			this.loading = true;
			try {
				console.log("[LIST_SHIFTS] Loading shifts for date:", this.selectedDate, "POS:", this.posProfile.name, "Role:", this.userRole);

				const response = await frappe.call({
					method: "posawesome.posawesome.api.shift_reports.get_shift_list",
					args: {
						date: this.selectedDate,
						pos_profile: this.posProfile.name,
						user_role: this.userRole,
						user: this.userRole === 'Sales Person' ? frappe.session.user : null
					}
				});

				console.log("[LIST_SHIFTS] API Response:", response);

				if (response.message?.success && response.message?.data) {
					this.shifts = response.message.data || [];
					this.totalShifts = this.shifts.length;

					// Calculate summary
					this.calculateSummary();

					console.log(`[LIST_SHIFTS] Loaded ${this.shifts.length} shifts`);
				} else {
					console.warn("[LIST_SHIFTS] No shifts data found");
					this.shifts = [];
					this.totalShifts = 0;
					this.summary = {
						total_shifts: 0,
						total_sales: 0,
						total_returns: 0,
						total_opening: 0,
						total_expected_closing: 0,
						total_actual_closing: 0
					};
				}
			} catch (error) {
				console.error("[LIST_SHIFTS] Error loading shifts:", error);
				this.showError("Failed to load shifts data");
				this.shifts = [];
				this.totalShifts = 0;
			} finally {
				this.loading = false;
			}
		},

		calculateSummary() {
			this.summary = this.shifts.reduce((acc, shift) => {
				acc.total_shifts += 1;
				acc.total_sales += parseFloat(shift.total_sales || 0);
				acc.total_returns += parseFloat(shift.total_returns || 0);
				acc.total_opening += parseFloat(shift.total_opening || 0);
				acc.total_expected_closing += parseFloat(shift.expected_closing_amount || 0);
				acc.total_actual_closing += parseFloat(shift.actual_closing_amount || 0);
				return acc;
			}, {
				total_shifts: 0,
				total_sales: 0,
				total_returns: 0,
				total_opening: 0,
				total_expected_closing: 0,
				total_actual_closing: 0
			});

			console.log("[LIST_SHIFTS] Summary calculated:", this.summary);
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

		viewShiftDetails(shift) {
			console.log("[LIST_SHIFTS] Viewing shift details:", shift);
			this.selectedShift = shift.name || shift.shift_report_id;
			this.showListInvoicesDialog = true;
		},

		getStatusColor(status) {
			const colors = {
				'Open': 'warning',
				'Closed': 'success',
				'Verified': 'info',
				'Pending': 'grey'
			};
			return colors[status] || 'grey';
		},

		getStatusText(status) {
			const texts = {
				'Open': 'Open',
				'Closed': 'Closed',
				'Verified': 'Verified',
				'Pending': 'Pending'
			};
			return texts[status] || status || 'Unknown';
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

		formatDate(dateStr) {
			if (!dateStr) return '';
			try {
				return new Date(dateStr).toLocaleDateString('vi-VN');
			} catch (e) {
				return dateStr;
			}
		},

		formatDateTime(date, time) {
			if (!date) return '-';

			try {
				let dateTimeStr = date;
				if (time) {
					dateTimeStr += ' ' + time;
				}

				if (window.frappe && frappe.datetime) {
					const dateObj = frappe.datetime.str_to_obj(dateTimeStr);
					return frappe.datetime.prettyDate(dateObj) + ' ' + frappe.datetime.get_time(dateObj);
				}

				const dateObj = new Date(dateTimeStr);
				return dateObj.toLocaleString();
			} catch (e) {
				console.warn('Error formatting datetime:', e);
				return date + (time ? ' ' + time : '');
			}
		},

		showError(message) {
			if (window.frappe?.show_alert) {
				frappe.show_alert({ message, indicator: 'red' });
			} else {
				alert(`Error: ${message}`);
			}
		},

		close() {
			this.resetData();
			this.show = false;
		},

		resetData() {
			this.shifts = [];
			this.totalShifts = 0;
			this.searchQuery = "";
			this.statusFilter = "";
			this.summary = {
				total_shifts: 0,
				total_sales: 0,
				total_returns: 0,
				total_opening: 0,
				total_expected_closing: 0,
				total_actual_closing: 0
			};
		}
	}
};
</script>

<style scoped>
/* Main Dialog Styles */
.v-dialog {
	max-height: 90vh;
}

/* Responsive Dialog */
@media (max-width: 1366px) {
	.v-dialog {
		max-width: 95vw;
		max-height: 85vh;
	}
}

/* Filters Section */
.filters-section {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-bottom: 1px solid #dee2e6;
}

/* Data Table Styles */
.v-data-table {
	border: none;
}

.v-data-table :deep(.v-data-table__td) {
	border-bottom: 1px solid rgb(var(--v-theme-surface-variant));
	padding: 8px 12px;
}

.v-data-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-surface));
	font-weight: 600;
	border-bottom: 2px solid rgb(var(--v-theme-primary));
	padding: 12px;
	font-size: 0.875rem;
}

/* Filter inputs */
.date-filter, .search-filter, .status-filter {
	margin-bottom: 8px;
}

/* Header Content Layout */
.header-content {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.header-main {
	display: flex;
	flex-direction: column;
	gap: 4px;
}

.header-title {
	margin: 0;
	font-size: 1.25rem;
	font-weight: 600;
	color: rgb(var(--v-theme-on-surface));
}

/* Shift Information Styles */
.shift-info {
	display: flex;
	flex-wrap: wrap;
	gap: 16px;
	margin-top: 4px;
}

.shift-info-item {
	display: flex;
	align-items: center;
	gap: 6px;
}

.shift-info-label {
	font-size: 0.8rem;
	font-weight: 600;
	color: rgb(var(--v-theme-on-surface-variant));
	min-width: 80px;
}

.shift-info-value {
	font-size: 0.8rem;
	font-weight: 500;
	color: rgb(var(--v-theme-on-surface));
	font-family: 'Courier New', monospace;
	background: rgba(var(--v-theme-primary), 0.1);
	padding: 2px 6px;
	border-radius: 4px;
	border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

/* Responsive adjustments */
@media (max-width: 768px) {
	.shift-info {
		flex-direction: column;
		gap: 8px;
		align-items: flex-start;
	}

	.shift-info-item {
		width: 100%;
	}

	.shift-info-label {
		min-width: auto;
	}
}

/* Mobile responsive */
@media (max-width: 768px) {
	.v-dialog {
		max-width: 98vw;
		max-height: 95vh;
		margin: 8px;
	}

	/* Stack filters vertically on mobile */
	.v-row.dense {
		flex-direction: column;
	}

	.v-row.dense .v-col {
		width: 100%;
		padding: 8px 0;
	}
}
</style>