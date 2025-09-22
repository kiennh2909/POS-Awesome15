<template>
	<v-dialog v-model="show" max-width="1400px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-view-list</v-icon>
				<div class="header-content">
					<div class="header-main">
						<h3 class="header-title">{{ __("List Shifts Report") }}</h3>
						<div class="shift-info" v-if="fromDate && toDate">
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Period:") }}</span>
								<span class="shift-info-value">{{ formatDate(fromDate) }} - {{ formatDate(toDate) }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("POS Profile:") }}</span>
								<span class="shift-info-value">{{ posProfile?.name || 'N/A' }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Cashier:") }}</span>
								<span class="shift-info-value">{{ selectedCashier || 'All' }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Generated:") }}</span>
								<span class="shift-info-value">{{ formatDateTime(new Date()) }}</span>
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
						<v-col cols="12" md="3">
							<v-text-field
								v-model="fromDate"
								:label="__('From Date')"
								type="date"
								variant="outlined"
								density="compact"
								:max="new Date().toISOString().split('T')[0]"
								class="date-filter"
							/>
						</v-col>
						<v-col cols="12" md="3">
							<v-text-field
								v-model="toDate"
								:label="__('To Date')"
								type="date"
								variant="outlined"
								density="compact"
								:max="new Date().toISOString().split('T')[0]"
								:min="fromDate"
								class="date-filter"
							/>
						</v-col>
						<v-col cols="12" md="3">
							<v-select
								v-model="selectedCashier"
								:label="__('Cashier')"
								:items="cashierOptions"
								variant="outlined"
								density="compact"
								clearable
								class="cashier-filter"
							/>
						</v-col>
						<v-col cols="12" md="3">
							<v-btn
								color="primary"
								variant="outlined"
								prepend-icon="mdi-chart-line"
								@click="loadShifts"
								:loading="loading"
								:disabled="!fromDate || !toDate"
								class="action-btn"
							>
								{{ __("Generate") }}
							</v-btn>

							<v-btn
								color="success"
								variant="outlined"
								prepend-icon="mdi-download"
								@click="exportReport"
								:loading="exporting"
								:disabled="!shifts.length"
								class="action-btn"
							>
								{{ __("Export") }}
							</v-btn>

							<v-btn
								color="info"
								variant="outlined"
								prepend-icon="mdi-printer"
								@click="printReport"
								:disabled="!shifts.length"
								class="action-btn"
							>
								{{ __("Print") }}
							</v-btn>

							<v-btn variant="text" @click="close" class="action-btn">
								{{ __("Close") }}
							</v-btn>
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
							<div class="text-caption text-medium-emphasis">{{ __("Sale Invoices") }}</div>
							<div class="text-h6 font-weight-bold text-success">{{ summary.total_sale_invoices || 0 }}</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Return Invoices") }}</div>
							<div class="text-h6 font-weight-bold text-error">{{ summary.total_return_invoices || 0 }}</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Sales") }}</div>
							<div class="text-h6 font-weight-bold text-success">
								{{ formatCurrency(summary.total_sale_amount || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Total Returns") }}</div>
							<div class="text-h6 font-weight-bold text-error">
								{{ formatCurrency(summary.total_return_amount || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="2">
						<v-card variant="outlined" class="pa-3">
							<div class="text-caption text-medium-emphasis">{{ __("Net Amount") }}</div>
							<div class="text-h6 font-weight-bold text-primary">
								{{ formatCurrency(summary.total_net_amount || 0) }}
							</div>
						</v-card>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Data Table -->
				<v-data-table
					:headers="headers"
					:items="shiftsWithTotal"
					:loading="loading"
					class="elevation-0"
					density="compact"
					:show-select="false"
					:items-per-page="-1"
					hide-default-footer
				>
					<template #item="{ item }">
						<tr :class="item.isTotalRow ? 'total-row' : ''">
							<td v-for="(header, hIndex) in headers" :key="hIndex" :class="header.align ? `text-${header.align}` : ''">
								<!-- Shift ID -->
								<v-chip
									v-if="header.key === 'shift_id'"
									variant="outlined"
									size="small"
									color="primary"
								>
									{{ item.shift_id || item.name }}
								</v-chip>

								<!-- Employee -->
								<div v-else-if="header.key === 'user'" class="text-truncate" style="max-width: 120px;">
									{{ item.user_fullname || item.user || '-' }}
								</div>

								<!-- Date -->
								<div v-else-if="header.key === 'date'" class="text-caption">
									{{ formatDate(item.date) }}
								</div>

								<!-- Status -->
								<v-chip
									v-else-if="header.key === 'status'"
									variant="flat"
									size="small"
									:color="getStatusColor(item.status)"
								>
									{{ getStatusText(item.status) }}
								</v-chip>

								<!-- Invoice counts -->
								<span v-else-if="header.key === 'sale_invoice_count' || header.key === 'return_invoice_count'"
									:class="item.isTotalRow ? 'font-weight-bold text-primary' : ''">
									{{ item[header.key] || 0 }}
								</span>

								<!-- Currency amounts -->
								<span v-else-if="header.key.includes('amount') || header.key.includes('sale') || header.key.includes('return') || header.key.includes('net') || header.key.includes('cash') || header.key.includes('bank') || header.key.includes('qrpay') || header.key.includes('card') || header.key.includes('other') || header.key.includes('submitted') || header.key.includes('difference')"
									:class="item.isTotalRow ? 'font-weight-bold text-primary' : getAmountClass(header.key)">
									{{ formatCurrency(item[header.key] || 0) }}
								</span>

								<!-- Currency -->
								<span v-else-if="header.key === 'currency'" :class="item.isTotalRow ? 'font-weight-bold text-primary' : ''">
									{{ item.currency || 'VND' }}
								</span>

								<!-- Actions -->
								<v-btn
									v-else-if="header.key === 'actions' && !item.isTotalRow"
									icon="mdi-eye"
									size="small"
									variant="text"
									@click="viewShiftDetails(item)"
									:title="__('View Shift Details')"
								></v-btn>

								<!-- Default -->
								<span v-else :class="item.isTotalRow ? 'font-weight-bold text-primary' : ''">
									{{ item[header.key] || '-' }}
								</span>
							</td>
						</tr>
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
			exporting: false,
			fromDate: new Date().toISOString().split('T')[0],
			toDate: new Date().toISOString().split('T')[0],
			selectedCashier: null,
			shifts: [],
			totalShifts: 0,
			userRole: null, // 'Sales Person' or 'Sales Manager'
			cashierOptions: [],
			summary: {
				total_shifts: 0,
				total_sale_invoices: 0,
				total_return_invoices: 0,
				total_sale_amount: 0,
				total_return_amount: 0,
				total_net_amount: 0,
				total_cash_amount: 0,
				total_bank_amount: 0,
				total_qrpay_amount: 0,
				total_card_amount: 0,
				total_other_amount: 0,
				total_cash_submitted: 0,
				total_difference: 0
			},
			headers: [
				{ title: this.__("Mã SHIFT"), key: "shift_id", width: "120px" },
				{ title: this.__("Nhân viên"), key: "user", width: "120px" },
				{ title: this.__("Ngày"), key: "date", width: "100px" },
				{ title: this.__("Trạng thái"), key: "status", width: "100px" },
				{ title: this.__("Hóa đơn bán hàng"), key: "sale_invoice_count", width: "120px", align: "end" },
				{ title: this.__("Hóa đơn hoàn"), key: "return_invoice_count", width: "100px", align: "end" },
				{ title: this.__("Tổng doanh số (SALE)"), key: "sale_amount", width: "140px", align: "end" },
				{ title: this.__("Số tiền hoàn (RETURN)"), key: "return_amount", width: "140px", align: "end" },
				{ title: this.__("Số tiền NET"), key: "net_amount", width: "120px", align: "end" },
				{ title: this.__("CASH"), key: "cash_amount", width: "100px", align: "end" },
				{ title: this.__("BANK"), key: "bank_amount", width: "100px", align: "end" },
				{ title: this.__("QRPAY"), key: "qrpay_amount", width: "100px", align: "end" },
				{ title: this.__("CARD"), key: "card_amount", width: "100px", align: "end" },
				{ title: this.__("OTHER"), key: "other_amount", width: "100px", align: "end" },
				{ title: this.__("Nộp cuối ca"), key: "cash_submitted", width: "120px", align: "end" },
				{ title: this.__("Chênh lệch"), key: "difference", width: "100px", align: "end" },
				{ title: this.__("Tiền tệ"), key: "currency", width: "80px" },
				{ title: this.__("Actions"), key: "actions", width: "80px", sortable: false }
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
		shiftsWithTotal() {
			const shifts = [...this.shifts];

			// Add grand total row
			const grandTotal = {
				shift_id: 'TOTAL',
				user: '',
				date: '',
				status: '',
				sale_invoice_count: this.summary.total_sale_invoices || 0,
				return_invoice_count: this.summary.total_return_invoices || 0,
				sale_amount: this.summary.total_sale_amount || 0,
				return_amount: this.summary.total_return_amount || 0,
				net_amount: this.summary.total_net_amount || 0,
				cash_amount: this.summary.total_cash_amount || 0,
				bank_amount: this.summary.total_bank_amount || 0,
				qrpay_amount: this.summary.total_qrpay_amount || 0,
				card_amount: this.summary.total_card_amount || 0,
				other_amount: this.summary.total_other_amount || 0,
				cash_submitted: this.summary.total_cash_submitted || 0,
				difference: this.summary.total_difference || 0,
				currency: this.shifts.length > 0 ? this.shifts[0].currency : 'VND',
				isTotalRow: true
			};

			shifts.push(grandTotal);
			return shifts;
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal) {
				this.initializeDialog();
			}
		}
	},
	mounted() {
		this.debouncedSearch = this.debounce(this.applyFilters, 300);
		this.checkUserRole();
	},
	methods: {
		async initializeDialog() {
			await this.checkUserRole();
			await this.loadCashiers();
			// Don't auto-load shifts, wait for user to click Generate
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

		async loadCashiers() {
			try {
				// Load available cashiers for the POS profile
				const response = await frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "User",
						filters: {
							enabled: 1,
							user_type: "System User"
						},
						fields: ["name", "full_name"],
						limit: 100
					}
				});

				this.cashierOptions = response.message?.map(user => ({
					title: user.full_name || user.name,
					value: user.name
				})) || [];
			} catch (error) {
				console.error("[LIST_SHIFTS] Error loading cashiers:", error);
				this.cashierOptions = [];
			}
		},

		async loadShifts() {
			if (!this.fromDate || !this.toDate) {
				this.showError("Please select both From Date and To Date");
				return;
			}

			this.loading = true;
			try {
				console.log("[LIST_SHIFTS] Loading shifts for period:", this.fromDate, "to", this.toDate, "POS:", this.posProfile.name, "Role:", this.userRole);

				const args = {
					company: this.posProfile?.company || frappe.defaults.get_default("company"),
					pos_profile: this.posProfile.name,
					from_date: this.fromDate,
					to_date: this.toDate
				};

				// Add cashier filter if selected
				if (this.selectedCashier) {
					args.cashier = this.selectedCashier;
				}

				// Add user filter for Sales Person role
				if (this.userRole === 'Sales Person') {
					args.user = frappe.session.user;
				}

				const response = await frappe.call({
					method: "posawesome.posawesome.api.reports.get_shift_list_report",
					args: args
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
					this.resetSummary();
				}
			} catch (error) {
				console.error("[LIST_SHIFTS] Error loading shifts:", error);
				this.showError("Failed to load shifts data");
				this.shifts = [];
				this.totalShifts = 0;
				this.resetSummary();
			} finally {
				this.loading = false;
			}
		},

		calculateSummary() {
			this.summary = this.shifts.reduce((acc, shift) => {
				acc.total_shifts += 1;
				acc.total_sale_invoices += parseInt(shift.sale_invoice_count || 0);
				acc.total_return_invoices += parseInt(shift.return_invoice_count || 0);
				acc.total_sale_amount += parseFloat(shift.sale_amount || 0);
				acc.total_return_amount += parseFloat(shift.return_amount || 0);
				acc.total_net_amount += parseFloat(shift.net_amount || 0);
				acc.total_cash_amount += parseFloat(shift.cash_amount || 0);
				acc.total_bank_amount += parseFloat(shift.bank_amount || 0);
				acc.total_qrpay_amount += parseFloat(shift.qrpay_amount || 0);
				acc.total_card_amount += parseFloat(shift.card_amount || 0);
				acc.total_other_amount += parseFloat(shift.other_amount || 0);
				acc.total_cash_submitted += parseFloat(shift.cash_submitted || 0);
				acc.total_difference += parseFloat(shift.difference || 0);
				return acc;
			}, {
				total_shifts: 0,
				total_sale_invoices: 0,
				total_return_invoices: 0,
				total_sale_amount: 0,
				total_return_amount: 0,
				total_net_amount: 0,
				total_cash_amount: 0,
				total_bank_amount: 0,
				total_qrpay_amount: 0,
				total_card_amount: 0,
				total_other_amount: 0,
				total_cash_submitted: 0,
				total_difference: 0
			});

			console.log("[LIST_SHIFTS] Summary calculated:", this.summary);
		},

		resetSummary() {
			this.summary = {
				total_shifts: 0,
				total_sale_invoices: 0,
				total_return_invoices: 0,
				total_sale_amount: 0,
				total_return_amount: 0,
				total_net_amount: 0,
				total_cash_amount: 0,
				total_bank_amount: 0,
				total_qrpay_amount: 0,
				total_card_amount: 0,
				total_other_amount: 0,
				total_cash_submitted: 0,
				total_difference: 0
			};
		},

		getAmountClass(key) {
			if (key.includes('sale') || key.includes('net') || key.includes('cash') || key.includes('bank') || key.includes('qrpay') || key.includes('card')) {
				return 'text-success';
			} else if (key.includes('return') || key.includes('other')) {
				return 'text-error';
			} else if (key.includes('submitted')) {
				return 'text-info';
			} else if (key.includes('difference')) {
				return 'text-warning';
			}
			return '';
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

		async exportReport() {
			this.exporting = true;
			try {
				const args = {
					company: this.posProfile?.company || frappe.defaults.get_default("company"),
					pos_profile: this.posProfile.name,
					from_date: this.fromDate,
					to_date: this.toDate
				};

				if (this.selectedCashier) {
					args.cashier = this.selectedCashier;
				}

				if (this.userRole === 'Sales Person') {
					args.user = frappe.session.user;
				}

				const response = await frappe.call({
					method: "posawesome.posawesome.api.reports.export_shift_list_report",
					args: args
				});

				if (response.message?.file_url) {
					window.open(response.message.file_url);
				} else {
					this.showSuccess(`Đã xuất báo cáo danh sách ca`);
				}
			} catch (error) {
				console.error(`Error exporting shift list report:`, error);
				this.showError(`Không thể xuất báo cáo danh sách ca`);
			} finally {
				this.exporting = false;
			}
		},

		async printReport() {
			try {
				const printContent = this.generatePrintContent();
				const printWindow = window.open('', '_blank', 'width=800,height=600');
				if (!printWindow) {
					this.showError("Không thể mở cửa sổ in. Vui lòng kiểm tra chặn popup.");
					return;
				}

				printWindow.document.write(printContent);
				printWindow.document.close();

				printWindow.onload = function() {
					printWindow.print();
					printWindow.close();
				};

				this.showSuccess("Đã gửi lệnh in thành công");
			} catch (error) {
				console.error(`Error printing shift list report:`, error);
				this.showError(`Không thể in báo cáo danh sách ca`);
			}
		},

		generatePrintContent() {
			const now = new Date();
			const printDate = now.toLocaleDateString('vi-VN');
			const printTime = now.toLocaleTimeString('vi-VN');

			let content = `
				<!DOCTYPE html>
				<html lang="vi">
				<head>
					<title>BÁO CÁO DANH SÁCH CA LÀM VIỆC</title>
					<meta charset="UTF-8">
					<style>
						@page { size: A4 landscape; margin: 1cm; }
						body { font-family: 'Arial', sans-serif; font-size: 10px; line-height: 1.3; color: #000; }
						.header { text-align: center; border-bottom: 2px solid #1976d2; padding-bottom: 10px; margin-bottom: 15px; }
						.header h1 { color: #000; margin: 0; font-size: 16px; font-weight: bold; }
						.section { margin-bottom: 15px; }
						table { width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 9px; }
						th, td { border: 1px solid #000; padding: 4px 2px; text-align: left; }
						th { background-color: #f5f5f5; font-weight: bold; font-size: 8px; }
						.amount { text-align: right; font-family: 'Courier New', monospace; }
						.total-row { background-color: #fff3cd !important; font-weight: bold; }
						.total-cell { color: #856404 !important; }
						@media print { body { -webkit-print-color-adjust: exact; color-adjust: exact; } }
					</style>
				</head>
				<body>
					<div class="header">
						<h1>BÁO CÁO DANH SÁCH CA LÀM VIỆC</h1>
						<p>Hồ sơ POS: ${this.posProfile?.name || 'N/A'}</p>
						<p>Nhân viên: ${this.selectedCashier || 'Tất cả'}</p>
						<p>Khoảng thời gian: ${this.formatDate(this.fromDate)} - ${this.formatDate(this.toDate)}</p>
						<p>Ngày in: ${printDate} ${printTime}</p>
					</div>

					<div class="section">
						<h2>TỔNG QUAN</h2>
						<table>
							<tr>
								<td><strong>Tổng ca:</strong></td><td>${this.summary.total_shifts}</td>
								<td><strong>Hóa đơn bán:</strong></td><td>${this.summary.total_sale_invoices}</td>
								<td><strong>Hóa đơn hoàn:</strong></td><td>${this.summary.total_return_invoices}</td>
								<td><strong>Tổng SALE:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_sale_amount)}</td>
							</tr>
							<tr>
								<td><strong>Tổng RETURN:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_return_amount)}</td>
								<td><strong>NET Amount:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_net_amount)}</td>
								<td><strong>CASH:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_cash_amount)}</td>
								<td><strong>BANK:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_bank_amount)}</td>
							</tr>
							<tr>
								<td><strong>QRPAY:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_qrpay_amount)}</td>
								<td><strong>CARD:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_card_amount)}</td>
								<td><strong>OTHER:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_other_amount)}</td>
								<td><strong>Nộp cuối ca:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_cash_submitted)}</td>
							</tr>
							<tr>
								<td><strong>Chênh lệch:</strong></td><td class="amount">${this.formatCurrency(this.summary.total_difference)}</td>
								<td colspan="6"></td>
							</tr>
						</table>
					</div>

					<div class="section">
						<h2>CHI TIẾT CA LÀM VIỆC</h2>
						<table>
							<thead>
								<tr>`;

			this.headers.forEach(header => {
				if (header.key !== 'actions') {
					content += `<th>${header.title}</th>`;
				}
			});
			content += `
								</tr>
							</thead>
							<tbody>`;

			this.shiftsWithTotal.forEach(item => {
				const isTotalRow = item.isTotalRow;
				const rowClass = isTotalRow ? 'total-row' : '';
				content += `<tr class="${rowClass}">`;

				this.headers.forEach(header => {
					if (header.key !== 'actions') {
						let value = item[header.key] || '';
						let cellClass = '';

						if (header.key.includes('amount') || header.key.includes('sale') || header.key.includes('return') ||
							header.key.includes('net') || header.key.includes('cash') || header.key.includes('bank') ||
							header.key.includes('qrpay') || header.key.includes('card') || header.key.includes('other') ||
							header.key.includes('submitted') || header.key.includes('difference')) {
							value = this.formatCurrency(value);
							cellClass = 'amount';
						} else if (header.key === 'date') {
							value = this.formatDate(value);
						}

						if (isTotalRow) {
							cellClass += ' total-cell';
						}

						content += `<td class="${cellClass}">${value}</td>`;
					}
				});
				content += `</tr>`;
			});

			content += `
							</tbody>
						</table>
					</div>

					<div style="text-align: center; font-size: 8px; margin-top: 15px; border-top: 1px solid #000; padding-top: 10px;">
						<p>Báo cáo được tạo tự động bởi hệ thống POS Awesome</p>
						<p>© 2025 - Hệ thống POS Awesome</p>
					</div>
				</body>
				</html>`;

			return content;
		},

		showSuccess(message) {
			if (window.frappe?.show_alert) {
				frappe.show_alert({ message, indicator: 'green' });
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
			this.selectedCashier = null;
			this.resetSummary();
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

/* Total Row Styling */
.total-row {
	background-color: #fff3cd !important;
	border-top: 2px solid #ffc107;
	font-weight: bold;
}

.total-row td {
	color: #856404 !important;
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