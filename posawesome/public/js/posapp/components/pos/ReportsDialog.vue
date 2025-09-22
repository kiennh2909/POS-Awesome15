<template>
	<v-dialog v-model="show" max-width="1400px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2" :color="reportConfig.iconColor">{{ reportConfig.icon }}</v-icon>
				<div class="header-content">
					<div class="header-main">
						<h3 class="header-title">{{ reportConfig.title }}</h3>
						<div class="report-info" v-if="reportData">
							<div class="report-info-item">
								<span class="report-info-label">{{ __("Period:") }}</span>
								<span class="report-info-value">{{ formatDate(fromDate) }} - {{ formatDate(toDate) }}</span>
							</div>
							<div class="report-info-item">
								<span class="report-info-label">{{ __("Generated:") }}</span>
								<span class="report-info-value">{{ formatDateTime(new Date()) }}</span>
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
					<div class="d-flex justify-space-between align-center">
						<div class="d-flex align-center gap-4">
							<h6 class="text-subtitle-1 mb-0">{{ __("Report Filters") }}</h6>
						</div>
						<div class="d-flex filter-controls gap-3">
							<!-- Date Range Pickers -->
							<v-text-field
								v-model="fromDate"
								type="date"
								:label="__('From Date')"
								density="compact"
								variant="outlined"
								:max="maxDate"
								class="date-filter"
							></v-text-field>
							<v-text-field
								v-model="toDate"
								type="date"
								:label="__('To Date')"
								density="compact"
								variant="outlined"
								:max="maxDate"
								:min="fromDate"
								class="date-filter"
							></v-text-field>

							<!-- Generate Report Button -->
							<v-btn
								color="primary"
								variant="outlined"
								prepend-icon="mdi-chart-line"
								@click="loadReportData"
								:loading="loading"
								:disabled="!fromDate || !toDate"
								class="action-btn"
							>
								{{ __("Generate") }}
							</v-btn>

							<!-- Export Button -->
							<v-btn
								color="success"
								variant="outlined"
								prepend-icon="mdi-download"
								@click="exportReport"
								:loading="exporting"
								:disabled="!reportData"
								class="action-btn"
							>
								{{ __("Export") }}
							</v-btn>

							<!-- Print Button -->
							<v-btn
								color="info"
								variant="outlined"
								prepend-icon="mdi-printer"
								@click="printReport"
								:disabled="!reportData"
								class="action-btn"
							>
								{{ __("Print") }}
							</v-btn>

							<!-- Close Button -->
							<v-btn variant="text" @click="close" class="action-btn">
								{{ __("Close") }}
							</v-btn>
						</div>
					</div>
				</div>

				<v-divider></v-divider>

				<!-- Summary Cards -->
				<div class="pa-4" v-if="summaryData">
					<v-row dense>
						<v-col
							v-for="(item, index) in summaryData"
							:key="index"
							cols="12"
							:md="summaryData.length === 4 ? 3 : summaryData.length === 3 ? 4 : 6"
						>
							<v-card variant="outlined" class="pa-3 summary-card">
								<div class="text-caption text-medium-emphasis">{{ item.label }}</div>
								<div class="text-h6 font-weight-bold" :class="item.colorClass">
									{{ item.value }}
								</div>
							</v-card>
						</v-col>
					</v-row>
				</div>

				<v-divider v-if="summaryData"></v-divider>

				<!-- Data Table -->
				<div class="pa-4">
					<v-data-table
						:headers="tableHeaders"
						:items="tableData"
						:loading="loading"
						density="compact"
						:items-per-page="-1"
						hide-default-footer
						class="elevation-0 report-table"
						:item-key="reportConfig.itemKey"
					>
						<template #item="{ item }">
							<tr :class="item.isTotalRow ? 'total-row' : ''">
								<td v-for="(header, hIndex) in tableHeaders" :key="hIndex" :class="header.align ? `text-${header.align}` : ''">
									<!-- Custom rendering based on header type -->
									<span v-if="header.key.includes('amount') || header.key.includes('total') || header.key.includes('sale') || header.key.includes('return') || header.key.includes('net') || header.key.includes('cash') || header.key.includes('bank') || header.key.includes('qrpay') || header.key.includes('card') || header.key.includes('other') || header.key.includes('submitted') || header.key.includes('difference')" :class="item.isTotalRow ? 'font-weight-bold text-primary' : 'text-success'">
										{{ formatCurrency(item[header.key]) }}
									</span>
									<span v-else-if="header.key === 'date'" :class="item.isTotalRow ? 'font-weight-bold text-primary' : ''">
										{{ item[header.key] }}
									</span>
									<span v-else-if="header.key === 'status'" :class="item.statusClass">
										<v-chip
											variant="outlined"
											size="small"
											:color="getStatusColor(item[header.key])"
										>
											{{ item[header.key] }}
										</v-chip>
									</span>
									<span v-else-if="header.key.includes('invoice_count')" :class="item.isTotalRow ? 'font-weight-bold text-primary' : ''">
										{{ item[header.key] }}
									</span>
									<span v-else :class="item[header.key + 'Class']">
										{{ item[header.key] }}
									</span>
								</td>
							</tr>
						</template>

						<template #bottom v-if="tableData.length > 10">
							<div class="d-flex align-center justify-center pa-3">
								<v-pagination
									v-model="currentPage"
									:length="Math.ceil(tableData.length / itemsPerPage)"
									:total-visible="5"
									size="small"
									variant="outlined"
								></v-pagination>
							</div>
						</template>
					</v-data-table>
				</div>
			</v-card-text>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: "ReportsDialog",
	props: {
		modelValue: {
			type: Boolean,
			default: false
		},
		reportType: {
			type: String,
			required: true
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
			currentPage: 1,
			itemsPerPage: 10,
			reportData: null,
			tableData: [],
			summaryData: null,
			tableHeaders: []
		};
	},
	computed: {
		show: {
			get() { return this.modelValue; },
			set(value) { this.$emit("update:modelValue", value); }
		},
		maxDate() {
			return new Date().toISOString().split('T')[0];
		},
		reportConfig() {
			const configs = {
				shift: {
					title: "Báo cáo toàn ca",
					icon: "mdi-store-clock",
					iconColor: "primary",
					itemKey: "shift_id"
				},
				item: {
					title: "Báo cáo mặt hàng",
					icon: "mdi-package-variant",
					iconColor: "success",
					itemKey: "item_code"
				},
				tax: {
					title: "Báo cáo thuế",
					icon: "mdi-receipt-text",
					iconColor: "warning",
					itemKey: "invoice_no"
				},
				inventory: {
					title: "Báo cáo hàng hóa",
					icon: "mdi-warehouse",
					iconColor: "purple",
					itemKey: "item_code"
				},
				price: {
					title: "Báo cáo bảng giá",
					icon: "mdi-tag-multiple",
					iconColor: "pink",
					itemKey: "item_code"
				},
				employee: {
					title: "Báo cáo nhân viên",
					icon: "mdi-account-group",
					iconColor: "teal",
					itemKey: "employee_id"
				},
				promotion: {
					title: "Báo cáo hàng khuyến mại",
					icon: "mdi-gift",
					iconColor: "orange",
					itemKey: "promotion_code"
				}
			};
			return configs[this.reportType] || configs.shift;
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal) {
				// Reset data when dialog opens
				this.resetData();
			}
		},
		reportType() {
			if (this.modelValue) {
				this.resetData();
			}
		}
	},
	methods: {
		async loadReportData() {
			if (!this.fromDate || !this.toDate) return;
	
			this.loading = true;
			try {
				const args = {
					company: this.posProfile?.company || frappe.defaults.get_default("company"),
					pos_profile: this.posProfile?.name
				};
	
				// Add date parameters based on report type
				if (this.reportType === 'shift') {
					args.from_date = this.fromDate;
					args.to_date = this.toDate;
				} else {
					args.date = this.fromDate; // For backward compatibility with other reports
				}
	
				const response = await frappe.call({
					method: `posawesome.posawesome.api.reports.get_${this.reportType}_report`,
					args: args
				});
	
				if (response.message) {
					this.reportData = response.message;
					this.tableData = response.message.data || [];
					this.summaryData = this.buildSummaryCards(response.message.summary);
					this.tableHeaders = response.message.headers || this.getDefaultHeaders();
				}
			} catch (error) {
				console.error(`Error loading ${this.reportType} report:`, error);
				this.showError(`Không thể tải báo cáo ${this.reportConfig.title}`);
			} finally {
				this.loading = false;
			}
		},
	
		buildSummaryCards(summary) {
			if (!summary) return null;
	
			const cards = [];
	
			if (this.reportType === 'shift') {
				cards.push(
					{ label: "Tổng hóa đơn bán", value: summary.total_sale_invoices || 0, colorClass: "text-success" },
					{ label: "Tổng hóa đơn hoàn", value: summary.total_return_invoices || 0, colorClass: "text-error" },
					{ label: "Tổng doanh số", value: this.formatCurrency(summary.total_sale_amount || 0), colorClass: "text-success" },
					{ label: "Tổng hoàn tiền", value: this.formatCurrency(summary.total_return_amount || 0), colorClass: "text-error" },
					{ label: "Doanh thu ròng", value: this.formatCurrency(summary.total_net_amount || 0), colorClass: "text-primary" },
					{ label: "Tiền mặt", value: this.formatCurrency(summary.total_cash_amount || 0), colorClass: "text-info" }
				);
			}
	
			return cards;
		},

		getDefaultHeaders() {
			const defaultHeaders = {
				shift: [
					{ title: this.__("Shift ID"), key: "shift_id", width: "120px" },
					{ title: this.__("Employee"), key: "employee", width: "150px" },
					{ title: this.__("Start Time"), key: "start_time", width: "120px" },
					{ title: this.__("End Time"), key: "end_time", width: "120px" },
					{ title: this.__("Total Sales"), key: "total_sales", width: "120px", align: "end" },
					{ title: this.__("Status"), key: "status", width: "100px" }
				],
				item: [
					{ title: this.__("Item Code"), key: "item_code", width: "120px" },
					{ title: this.__("Item Name"), key: "item_name", width: "200px" },
					{ title: this.__("Category"), key: "category", width: "120px" },
					{ title: this.__("Quantity Sold"), key: "quantity", width: "100px", align: "end" },
					{ title: this.__("Total Amount"), key: "total", width: "120px", align: "end" }
				],
				tax: [
					{ title: this.__("Invoice No"), key: "invoice_no", width: "120px" },
					{ title: this.__("Date"), key: "date", width: "100px" },
					{ title: this.__("Customer"), key: "customer", width: "150px" },
					{ title: this.__("Tax Amount"), key: "tax_amount", width: "120px", align: "end" },
					{ title: this.__("Total Amount"), key: "total", width: "120px", align: "end" }
				],
				inventory: [
					{ title: this.__("Item Code"), key: "item_code", width: "120px" },
					{ title: this.__("Item Name"), key: "item_name", width: "200px" },
					{ title: this.__("Stock Qty"), key: "stock_qty", width: "100px", align: "end" },
					{ title: this.__("Reserved Qty"), key: "reserved_qty", width: "100px", align: "end" },
					{ title: this.__("Available Qty"), key: "available_qty", width: "100px", align: "end" }
				],
				price: [
					{ title: this.__("Item Code"), key: "item_code", width: "120px" },
					{ title: this.__("Item Name"), key: "item_name", width: "200px" },
					{ title: this.__("Old Price"), key: "old_price", width: "100px", align: "end" },
					{ title: this.__("New Price"), key: "new_price", width: "100px", align: "end" },
					{ title: this.__("Changed Date"), key: "changed_date", width: "120px" }
				],
				employee: [
					{ title: this.__("Employee ID"), key: "employee_id", width: "120px" },
					{ title: this.__("Employee Name"), key: "employee_name", width: "150px" },
					{ title: this.__("Shifts Count"), key: "shifts_count", width: "100px", align: "end" },
					{ title: this.__("Total Sales"), key: "total_sales", width: "120px", align: "end" },
					{ title: this.__("Performance"), key: "performance", width: "100px" }
				],
				promotion: [
					{ title: this.__("Promotion Code"), key: "promotion_code", width: "120px" },
					{ title: this.__("Promotion Name"), key: "promotion_name", width: "200px" },
					{ title: this.__("Type"), key: "type", width: "100px" },
					{ title: this.__("Usage Count"), key: "usage_count", width: "100px", align: "end" },
					{ title: this.__("Total Discount"), key: "total_discount", width: "120px", align: "end" }
				]
			};
			return defaultHeaders[this.reportType] || defaultHeaders.shift;
		},

		async exportReport() {
			this.exporting = true;
			try {
				const args = {
					company: this.posProfile?.company || frappe.defaults.get_default("company"),
					pos_profile: this.posProfile?.name
				};
	
				// Add date parameters based on report type
				if (this.reportType === 'shift') {
					args.from_date = this.fromDate;
					args.to_date = this.toDate;
				} else {
					args.date = this.fromDate; // For backward compatibility
				}
	
				const response = await frappe.call({
					method: `posawesome.posawesome.api.reports.export_${this.reportType}_report`,
					args: args
				});
	
				if (response.message?.file_url) {
					window.open(response.message.file_url);
				} else {
					this.showSuccess(`Đã xuất báo cáo ${this.reportConfig.title}`);
				}
			} catch (error) {
				console.error(`Error exporting ${this.reportType} report:`, error);
				this.showError(`Không thể xuất báo cáo ${this.reportConfig.title}`);
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
				console.error(`Error printing ${this.reportType} report:`, error);
				this.showError(`Không thể in báo cáo ${this.reportConfig.title}`);
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
					<title>${this.reportConfig.title}</title>
					<meta charset="UTF-8">
					<style>
						@page { size: A4; margin: 1cm; }
						body { font-family: 'Arial', sans-serif; font-size: 12px; line-height: 1.4; color: #000; }
						.header { text-align: center; border-bottom: 2px solid #1976d2; padding-bottom: 10px; margin-bottom: 20px; }
						.header h1 { color: #000; margin: 0; font-size: 18px; font-weight: bold; }
						.section { margin-bottom: 20px; }
						.section h2 { color: #000; font-size: 14px; border-bottom: 1px solid #000; padding-bottom: 5px; margin-bottom: 10px; font-weight: bold; }
						table { width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 11px; }
						th, td { border: 1px solid #000; padding: 8px; text-align: left; }
						th { background-color: #f5f5f5; font-weight: bold; }
						.amount { text-align: right; }
						.total-row { background-color: #fff3cd !important; font-weight: bold; }
						.total-cell { color: #856404 !important; }
						.summary-cards { display: flex; gap: 15px; margin-bottom: 20px; }
						.card { flex: 1; border: 1px solid #000; padding: 10px; border-radius: 4px; text-align: center; }
						.card-title { font-size: 10px; color: #000; margin-bottom: 5px; font-weight: bold; }
						.card-value { font-size: 16px; font-weight: bold; color: #000; }
						@media print { body { -webkit-print-color-adjust: exact; color-adjust: exact; } }
					</style>
				</head>
				<body>
					<div class="header">
						<h1>${this.reportConfig.title}</h1>
						<p>Hồ sơ POS: ${this.posProfile?.name || 'N/A'}</p>
						<p>Ngày báo cáo: ${this.formatDate(this.fromDate)} - ${this.formatDate(this.toDate)}</p>
						<p>Ngày in: ${printDate} ${printTime}</p>
					</div>`;

			if (this.summaryData) {
				content += `
					<div class="section">
						<h2>TỔNG QUAN</h2>
						<div class="summary-cards">`;
				this.summaryData.forEach(item => {
					content += `
							<div class="card">
								<div class="card-title">${item.label}</div>
								<div class="card-value">${item.value}</div>
							</div>`;
				});
				content += `
						</div>
					</div>`;
			}

			content += `
					<div class="section">
						<h2>CHI TIẾT DỮ LIỆU</h2>
						<table>
							<thead>
								<tr>`;
			this.tableHeaders.forEach(header => {
				content += `<th>${header.title}</th>`;
			});
			content += `
								</tr>
							</thead>
							<tbody>`;
			this.tableData.forEach(item => {
				const isTotalRow = item.isTotalRow;
				const rowClass = isTotalRow ? 'total-row' : '';
				content += `<tr class="${rowClass}">`;
				this.tableHeaders.forEach(header => {
					let value = item[header.key] || '';
					let cellClass = '';

					if (header.key.includes('amount') || header.key.includes('total') || header.key.includes('sale') ||
						header.key.includes('return') || header.key.includes('net') || header.key.includes('cash') ||
						header.key.includes('bank') || header.key.includes('qrpay') || header.key.includes('card') ||
						header.key.includes('other') || header.key.includes('submitted') || header.key.includes('difference')) {
						value = this.formatCurrency(value);
						cellClass = 'amount';
					} else if (header.key === 'date') {
						value = this.formatDate(value);
					}

					if (isTotalRow) {
						cellClass += ' total-cell';
					}

					content += `<td class="${cellClass}">${value}</td>`;
				});
				content += `</tr>`;
			});
			content += `
							</tbody>
						</table>
					</div>
				</body>
				</html>`;

			return content;
		},

		close() {
			this.show = false;
			this.resetData();
		},

		resetData() {
			this.reportData = null;
			this.tableData = [];
			this.summaryData = null;
			this.tableHeaders = [];
			this.currentPage = 1;
			// Reset dates to current date
			const today = new Date().toISOString().split('T')[0];
			this.fromDate = today;
			this.toDate = today;
		},

		formatCurrency(amount) {
			if (!amount && amount !== 0) return '0';
			try {
				let currency = 'VND';
				if (this.posProfile?.currency) {
					currency = this.posProfile.currency;
				}
				return new Intl.NumberFormat('vi-VN', {
					style: 'currency',
					currency: currency,
					minimumFractionDigits: 0,
					maximumFractionDigits: 0
				}).format(amount);
			} catch (error) {
				return `${amount}`;
			}
		},

		formatDate(dateStr) {
			if (!dateStr) return '';
			try {
				const date = new Date(dateStr);
				return date.toLocaleDateString('vi-VN', {
					day: '2-digit',
					month: '2-digit',
					year: 'numeric'
				});
			} catch (e) {
				return dateStr;
			}
		},

		formatDateTime(dateTimeStr) {
			if (!dateTimeStr) return '';
			try {
				const date = new Date(dateTimeStr);
				return date.toLocaleString('vi-VN');
			} catch (e) {
				return dateTimeStr;
			}
		},

		getStatusColor(status) {
			const colors = {
				'Active': 'success',
				'Completed': 'success',
				'Pending': 'warning',
				'Cancelled': 'error',
				'In Stock': 'success',
				'Low Stock': 'warning',
				'Out of Stock': 'error'
			};
			return colors[status] || 'grey';
		},

		showError(message) {
			if (window.frappe?.show_alert) {
				frappe.show_alert({ message, indicator: 'red' });
			} else {
				alert(`Error: ${message}`);
			}
		},

		showSuccess(message) {
			if (window.frappe?.show_alert) {
				frappe.show_alert({ message, indicator: 'green' });
			}
		}
	}
};
</script>

<style scoped>
.v-dialog {
	max-height: 90vh;
}

@media (max-width: 1366px) {
	.v-dialog {
		max-width: 95vw;
		max-height: 85vh;
	}
}

.filters-section {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-bottom: 1px solid #dee2e6;
}

.filter-controls {
	gap: 8px;
}

.date-filter {
	min-width: 150px;
}

.action-btn {
	min-height: 36px !important;
	padding: 0 12px !important;
	font-size: 0.85rem !important;
	font-weight: 500 !important;
}

.summary-card {
	transition: all 0.3s ease;
}

.summary-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.report-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-primary));
	color: rgb(var(--v-theme-on-primary));
	font-weight: 600;
	font-size: 0.8rem;
	padding: 8px 12px;
}

.report-table :deep(.v-data-table__td) {
	padding: 8px 12px;
	font-size: 0.85rem;
}

.total-row {
	background-color: #fff3cd !important;
	border-top: 2px solid #ffc107;
	font-weight: bold;
}

.total-row td {
	color: #856404 !important;
}

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

.report-info {
	display: flex;
	flex-wrap: wrap;
	gap: 16px;
	margin-top: 4px;
}

.report-info-item {
	display: flex;
	align-items: center;
	gap: 6px;
}

.report-info-label {
	font-size: 0.8rem;
	font-weight: 600;
	color: rgb(var(--v-theme-on-surface-variant));
	min-width: 80px;
}

.report-info-value {
	font-size: 0.8rem;
	font-weight: 500;
	color: rgb(var(--v-theme-on-surface));
	font-family: 'Courier New', monospace;
	background: rgba(var(--v-theme-primary), 0.1);
	padding: 2px 6px;
	border-radius: 4px;
	border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

@media (max-width: 768px) {
	.filter-controls {
		flex-direction: column;
		align-items: stretch;
		gap: 8px;
	}

	.date-filter {
		min-width: auto;
	}

	.report-info {
		flex-direction: column;
		gap: 8px;
		align-items: flex-start;
	}

	.report-info-item {
		width: 100%;
	}

	.report-info-label {
		min-width: auto;
	}
}
</style>