<template>
	<v-dialog v-model="show" max-width="1200px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-store-clock-outline</v-icon>
				<div class="header-content">
					<div class="header-main">
						<h3 class="header-title">{{ __("Close POS Shift") }}</h3>
						<div class="shift-info" v-if="shiftReportData">
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Shift ID:") }}</span>
								<span class="shift-info-value">{{ displayShiftReportId }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Opened:") }}</span>
								<span class="shift-info-value">{{ formatDateTime(shiftReportData.opening_date, shiftReportData.opening_time) }}</span>
							</div>
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Status:") }}</span>
								<div class="d-flex flex-column align-start gap-1">
									<v-chip
										:color="getVerificationColor(shiftReportData.verification_status)"
										variant="outlined"
										size="small"
										class="verification-status-chip"
									>
										<v-icon size="14" class="me-1">
											{{ getVerificationIcon(shiftReportData.verification_status) }}
										</v-icon>
										{{ shiftReportData.verification_status || 'Pending' }}
									</v-chip>
									<span v-if="shiftReportData.verification_status === 'Pending'" class="verification-warning-text">
										{{ __("Need to Verify before Close Shift") }}
									</span>
								</div>
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
				<div class="pa-4 action-buttons-section">
					<div class="d-flex justify-space-between align-center">
						<div class="d-flex align-center gap-4">
							<h6 class="text-subtitle-1 mb-0">{{ __("Shift Closing Actions") }}</h6>
						</div>
						<div class="d-flex action-buttons-group">
							<v-btn
								color="success"
								variant="outlined"
								prepend-icon="mdi-download"
								@click="exportShiftSummary"
								class="action-btn"
							>
								{{ __("Export") }}
							</v-btn>
							<v-btn
								color="info"
								variant="outlined"
								prepend-icon="mdi-printer"
								@click="printShiftSummary"
								class="action-btn"
							>
								{{ __("Print") }}
							</v-btn>
							<v-btn
								color="primary"
								variant="flat"
								prepend-icon="mdi-store-clock"
								:loading="closingShift"
								@click="closeShift"
								class="action-btn"
							>
								{{ __("Close Shift") }}
							</v-btn>
							<v-btn variant="text" @click="close" class="action-btn">
								{{ __("Cancel") }}
							</v-btn>
						</div>
					</div>
				</div>

				<v-divider></v-divider>

				<div class="pa-4">
					<h6 class="text-subtitle-1 mb-3">{{ __("Payment Reconciliation") }}</h6>
					<v-data-table
						:headers="paymentSummaryHeaders"
						:items="paymentSummaryDataWithTotal"
						:loading="loadingSummary"
						density="compact"
						:items-per-page="-1"
						hide-default-footer
						class="elevation-0 payment-summary-table"
					>
						<template #item.actual_closing_amount="{ item }">
							<v-text-field
								v-if="!item.isTotalRow"
								v-model="item.actual_closing_amount"
								:rules="[isNumber]"
								:label="__('Actual Closing')"
								single-line
								density="compact"
								variant="outlined"
								color="primary"
								hide-details
								:prefix="currencySymbol(posProfile.currency)"
								class="actual-closing-input"
								@input="calculateDifference(item)"
							></v-text-field>
							<span v-else class="font-weight-bold currency-amount">
								{{ formatCurrency(item.actual_closing_amount || 0) }}
							</span>
						</template>
					</v-data-table>
				</div>
			</v-card-text>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: "ClosingShiftNew",
	props: {
		modelValue: { type: Boolean, default: false },
		shiftReportId: { type: String, default: "" },
		posProfile: { type: Object, default: () => ({}) }
	},
	emits: ["update:modelValue"],
	data() {
		return {
			loading: false,
			loadingSummary: false,
			closingShift: false,
			shiftReportData: null,
			paymentSummaryData: [],
			paymentSummaryHeaders: [
				{ title: this.__("Payment Method"), key: "payment_method", width: "140px" },
				{ title: this.__("Opening Amount"), key: "opening_amount", width: "100px", align: "end" },
				{ title: this.__("Sales Amount"), key: "sales_amount", width: "100px", align: "end" },
				{ title: this.__("Returns Amount"), key: "returns_amount", width: "100px", align: "end" },
				{ title: this.__("Transactions"), key: "transaction_amount", width: "100px", align: "end" },
				{ title: this.__("Expected Closing"), key: "expected_closing_amount", width: "100px", align: "end" },
				{ title: this.__("Actual Closing"), key: "actual_closing_amount", width: "120px", align: "end" },
				{ title: this.__("Difference"), key: "difference", width: "100px", align: "end" }
			],
			isNumber: (v) => !isNaN(v) || "Must be a number"
		};
	},
	computed: {
		show: {
			get() { return this.modelValue; },
			set(value) { this.$emit("update:modelValue", value); }
		},
		displayShiftReportId() {
			return this.shiftReportData?.shift_report_id || this.shiftReportData?.name || 'Loading...';
		},
		paymentSummaryDataWithTotal() {
			const dataWithTotal = [...this.paymentSummaryData];
			const totalActual = this.paymentSummaryData.reduce((sum, item) => sum + (parseFloat(item.actual_closing_amount) || 0), 0);
			const totalDifference = this.paymentSummaryData.reduce((sum, item) => sum + (parseFloat(item.difference) || 0), 0);

			dataWithTotal.push({
				payment_method: 'TOTAL',
				actual_closing_amount: totalActual,
				difference: totalDifference,
				isTotalRow: true
			});

			return dataWithTotal;
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal && this.shiftReportId) {
				this.loadShiftData();
			}
		}
	},
	methods: {
		async loadShiftData() {
			this.loading = true;
			try {
				let actualShiftReportId = this.shiftReportId;

				if (typeof this.shiftReportId === 'object' && this.shiftReportId?.doctype === "POS Opening Shift") {
					const shiftReports = await frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "POS Shift Report",
							filters: { pos_opening_shift: this.shiftReportId.name },
							fields: ["name"],
							limit: 1
						}
					});

					if (shiftReports.message?.length > 0) {
						actualShiftReportId = shiftReports.message[0].name;
					}
				}

				const response = await frappe.call({
					method: "posawesome.posawesome.api.shift_reports.get_shift_report_readonly",
					args: { shift_report_id: actualShiftReportId }
				});

				if (response.message?.data) {
					const shiftReportData = response.message.data;

					if (response.message.data.payment_summaries?.length > 0) {
						this.paymentSummaryData = response.message.data.payment_summaries.map(item => ({
							payment_method: item.payment_method,
							opening_amount: item.opening_amount || 0,
							sales_amount: item.sales_amount || 0,
							returns_amount: item.returns_amount || 0,
							transaction_amount: item.transaction_amount || 0,
							expected_closing_amount: item.expected_closing_amount || 0,
							actual_closing_amount: item.expected_closing_amount || 0,
							difference: 0
						}));
					}

					this.shiftReportData = shiftReportData;
				}
			} catch (error) {
				console.error("Error loading shift data:", error);
				this.showError("Failed to load shift data");
			} finally {
				this.loading = false;
			}
		},

		calculateDifference(item) {
			const expected = parseFloat(item.expected_closing_amount) || 0;
			const actual = parseFloat(item.actual_closing_amount) || 0;
			item.difference = actual - expected;
		},

		async closeShift() {
			// Validate that all actual closing amounts are valid numbers
			const invalidAmounts = this.paymentSummaryData.filter(item => {
				const value = item.actual_closing_amount;
				if (value === undefined || value === null || value === '') {
					return false; // Empty is allowed, will default to 0
				}
				const numValue = parseFloat(value);
				return isNaN(numValue);
			});

			if (invalidAmounts.length > 0) {
				this.showError("Please enter valid numbers for actual closing amounts");
				return;
			}

			this.closingShift = true;
			try {
				// Single API call to create and submit closing shift
				// Use POS Opening Shift from shift report data, or fallback to shiftReportId if it's already an opening shift
				let posOpeningShift = this.shiftReportData?.pos_opening_shift;
				if (!posOpeningShift) {
					posOpeningShift = typeof this.shiftReportId === 'object' ? this.shiftReportId.name : this.shiftReportId;
				}

				const closingShiftData = {
					pos_opening_shift: posOpeningShift,
					pos_profile: this.posProfile.name,
					user: frappe.session.user,
					company: this.posProfile.company,
					period_start_date: this.shiftReportData?.opening_date,
					period_start_time: this.shiftReportData?.opening_time,
					balance_details: this.paymentSummaryData.map(item => ({
						mode_of_payment: item.payment_method,
						amount: item.opening_amount || 0
					})),
					payment_reconciliation: this.paymentSummaryData.map(item => {
						const actualClosing = item.actual_closing_amount;
						let closingAmount = 0;

						if (actualClosing !== '' && actualClosing !== null && actualClosing !== undefined) {
							const parsed = parseFloat(actualClosing);
							if (!isNaN(parsed)) {
								closingAmount = parsed;
							}
						}

						return {
							mode_of_payment: item.payment_method,
							opening_amount: parseFloat(item.opening_amount) || 0,
							expected_amount: parseFloat(item.expected_closing_amount) || 0,
							closing_amount: closingAmount,
							difference: parseFloat(item.difference) || 0
						};
					})
				};

				const response = await frappe.call({
					method: "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.submit_closing_shift_v2",
					args: {
						closing_shift: JSON.stringify(closingShiftData)
					}
				});

				if (response.message?.success) {
					this.showSuccess(__("Shift closed successfully"));
					this.close();

					// Handle post-submit cleanup: logout, clear cache, refresh
					await this.handlePostShiftClose();

					if (this.eventBus) {
						this.eventBus.emit("shift_closed_success");
					}
				} else {
					this.showError(response.message?.message || __("Failed to close shift"));
				}
			} catch (error) {
				console.error("Error closing shift:", error);
				this.showError(__("Error closing shift"));
			} finally {
				this.closingShift = false;
			}
		},

		close() {
			this.show = false;
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

		currencySymbol(currency) {
			const symbols = { 'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'KES': 'KSh' };
			return symbols[currency] || currency || '$';
		},

		formatDateTime(date, time) {
			if (!date) return 'N/A';

			try {
				let dateTimeStr = date;
				if (time) {
					dateTimeStr += ' ' + time;
				}

				// Use frappe's datetime formatting if available
				if (window.frappe && frappe.datetime) {
					const dateObj = frappe.datetime.str_to_obj(dateTimeStr);
					return frappe.datetime.prettyDate(dateObj) + ' ' + frappe.datetime.get_time(dateObj);
				}

				// Fallback to basic formatting
				const dateObj = new Date(dateTimeStr);
				return dateObj.toLocaleString();
			} catch (e) {
				console.warn('Error formatting datetime:', e);
				return date + (time ? ' ' + time : '');
			}
		},

		getVerificationColor(status) {
			const colors = {
				'Pending': 'warning',
				'Verified': 'success',
				'Confirmed': 'info'
			};
			return colors[status] || 'grey';
		},

		getVerificationIcon(status) {
			const icons = {
				'Pending': 'mdi-clock-outline',
				'Verified': 'mdi-check-circle',
				'Confirmed': 'mdi-check-circle-outline'
			};
			return icons[status] || 'mdi-help-circle';
		},

		async exportShiftSummary() {
			try {
				console.log("[EXPORT_SHIFT_SUMMARY] Bắt đầu xuất tổng kết ca ra Excel");

				// Tạo dữ liệu summary
				const summaryData = this.prepareSummaryData();

				// Lấy danh sách invoices
				const invoicesData = this.prepareInvoicesData();

				// Tạo nội dung Excel
				const excelContent = this.generateExcelContent(summaryData, invoicesData);

				// Tạo tên file
				const now = new Date();
				const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '');
				const dateStr = now.toISOString().split('T')[0].replace(/-/g, '_');
				const posProfileName = (this.posProfile?.name || 'Unknown').replace(/\s+/g, '_');
				const cashierName = (frappe.session?.user || 'Unknown').replace(/[^a-zA-Z0-9]/g, '_');
				const fileName = `${timeStr}_${dateStr}_${posProfileName}_${cashierName}_Tong_Ket_Ca.xlsx`;

				// Download file
				const blob = new Blob(['\ufeff', excelContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = fileName;
				a.click();
				window.URL.revokeObjectURL(url);

				this.showSuccess(`Đã xuất thành công báo cáo tổng kết ca`);

			} catch (error) {
				console.error("[EXPORT_SHIFT_SUMMARY] Lỗi khi xuất Excel:", error);
				this.showError("Lỗi khi xuất báo cáo tổng kết ca");
			}
		},

		prepareSummaryData() {
			const now = new Date();
			const printTime = now.toLocaleString('vi-VN');

			return [
				{
					"Loại": "THÔNG TIN CHUNG",
					"Mã ca": this.displayShiftReportId,
					"Hồ sơ POS": this.posProfile?.name || 'N/A',
					"Nhân viên": frappe.session?.user_fullname || frappe.session?.user || 'N/A',
					"Thời gian mở ca": this.formatDateTime(this.shiftReportData?.opening_date, this.shiftReportData?.opening_time),
					"Thời gian xuất báo cáo": printTime,
					"Trạng thái xác minh": this.shiftReportData?.verification_status || 'Chưa xác minh'
				},
				{}, // Empty row
				{
					"Loại": "TỔNG KẾT DOANH THU",
					"Tổng số hóa đơn": this.shiftReportData?.invoice_count || 0,
					"Tổng tiền bán": this.formatCurrency(this.shiftReportData?.total_sales || 0),
					"Tổng tiền trả lại": this.formatCurrency(this.shiftReportData?.total_returns || 0),
					"Tổng thu nhập": this.formatCurrency((this.shiftReportData?.total_sales || 0) + (this.shiftReportData?.total_returns || 0))
				},
				{} // Empty row
			];
		},

		prepareInvoicesData() {
			if (!this.shiftReportData?.invoices || this.shiftReportData.invoices.length === 0) {
				return [{
					"Loại": "DANH SÁCH HÓA ĐƠN",
					"Thông báo": "Không có hóa đơn nào trong ca này"
				}];
			}

			const invoiceRows = this.shiftReportData.invoices.map(invoice => ({
				"Loại": "DANH SÁCH HÓA ĐƠN",
				"Mã hóa đơn": invoice.invoice_no || '',
				"Ngày": invoice.invoice_date || '',
				"Giờ": invoice.invoice_time || '',
				"Khách hàng": invoice.customer || 'Khách lẻ',
				"Tổng tiền": this.formatCurrency(invoice.total_amount || 0),
				"Phương thức thanh toán": invoice.payment_method || 'Tiền mặt',
				"Trạng thái": invoice.status || 'Chưa xác định',
				"Loại hóa đơn": invoice.is_return ? 'Trả lại' : 'Bán hàng'
			}));

			return invoiceRows;
		},

		generateExcelContent(summaryData, invoicesData) {
			// Header information
			let content = [
				"TỔNG KẾT CA LÀM VIỆC - BÁO CÁO CHI TIẾT",
				`Hồ sơ POS: ${this.posProfile?.name || 'N/A'}`,
				`Mã ca: ${this.displayShiftReportId}`,
				`Nhân viên: ${frappe.session?.user_fullname || frappe.session?.user || 'N/A'}`,
				`Thời gian mở ca: ${this.formatDateTime(this.shiftReportData?.opening_date, this.shiftReportData?.opening_time)}`,
				`Thời gian xuất: ${new Date().toLocaleString('vi-VN')}`,
				""
			];

			// Summary section
			content.push("THÔNG TIN TỔNG QUAN");
			content.push("Tổng số hóa đơn\tTổng tiền bán\tTổng tiền trả lại\tTổng thu nhập");
			content.push(`${this.shiftReportData?.invoice_count || 0}\t${this.formatCurrency(this.shiftReportData?.total_sales || 0)}\t${this.formatCurrency(this.shiftReportData?.total_returns || 0)}\t${this.formatCurrency((this.shiftReportData?.total_sales || 0) + (this.shiftReportData?.total_returns || 0))}`);
			content.push("");

			// Payment reconciliation section
			content.push("BẢNG ĐỐI CHIẾU THANH TOÁN");
			content.push("Phương thức thanh toán\tSố dư đầu ca\tDoanh thu bán\tDoanh thu trả lại\tTổng giao dịch\tDự kiến đóng ca\tThực tế đóng ca\tChênh lệch");

			this.paymentSummaryDataWithTotal.forEach(item => {
				content.push(`${item.payment_method}\t${this.formatCurrency(item.opening_amount || 0)}\t${this.formatCurrency(item.sales_amount || 0)}\t${this.formatCurrency(item.returns_amount || 0)}\t${this.formatCurrency(item.transaction_amount || 0)}\t${this.formatCurrency(item.expected_closing_amount || 0)}\t${this.formatCurrency(item.actual_closing_amount || 0)}\t${this.formatCurrency(item.difference || 0)}`);
			});

			content.push("");
			content.push("DANH SÁCH CHI TIẾT HÓA ĐƠN");
			content.push("Mã hóa đơn\tNgày\tGiờ\tKhách hàng\tTổng tiền\tPhương thức thanh toán\tTrạng thái\tLoại hóa đơn");

			if (this.shiftReportData?.invoices && this.shiftReportData.invoices.length > 0) {
				this.shiftReportData.invoices.forEach(invoice => {
					content.push(`${invoice.invoice_no || ''}\t${invoice.invoice_date || ''}\t${invoice.invoice_time || ''}\t${invoice.customer || 'Khách lẻ'}\t${this.formatCurrency(invoice.total_amount || 0)}\t${invoice.payment_method || 'Tiền mặt'}\t${invoice.status || 'Chưa xác định'}\t${invoice.is_return ? 'Trả lại' : 'Bán hàng'}`);
				});
			} else {
				content.push("Không có hóa đơn nào trong ca này");
			}

			content.push("");
			content.push("Báo cáo được tạo tự động bởi hệ thống POS Awesome");
			content.push(`Xuất vào lúc: ${new Date().toLocaleString('vi-VN')}`);

			return content.join('\n');
		},

		async printShiftSummary() {
			try {
				console.log("[PRINT_SHIFT_SUMMARY] Bắt đầu in tổng kết ca");

				// Tạo nội dung in
				const printContent = this.generatePrintContent();

				// Mở cửa sổ in
				const printWindow = window.open('', '_blank', 'width=800,height=600');
				if (!printWindow) {
					this.showError("Không thể mở cửa sổ in. Vui lòng kiểm tra chặn popup.");
					return;
				}

				printWindow.document.write(printContent);
				printWindow.document.close();

				// Đợi nội dung load xong thì in
				printWindow.onload = function() {
					printWindow.print();
					printWindow.close();
				};

				this.showSuccess("Đã gửi lệnh in thành công");

			} catch (error) {
				console.error("[PRINT_SHIFT_SUMMARY] Lỗi khi in tổng kết ca:", error);
				this.showError("Lỗi khi in tổng kết ca");
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
					<title>TỔNG KẾT CA LÀM VIỆC</title>
					<meta charset="UTF-8">
					<style>
						@page {
							size: A4;
							margin: 1cm;
						}
						body {
							font-family: 'Arial', 'Times New Roman', serif;
							font-size: 12px;
							line-height: 1.4;
							color: #000 !important;
							max-width: 100%;
							background: white;
							-webkit-print-color-adjust: exact;
							color-adjust: exact;
						}
						* {
							color: #000 !important;
						}
						.header {
							text-align: center;
							border-bottom: 2px solid #1976d2;
							padding-bottom: 10px;
							margin-bottom: 20px;
						}
						.header h1 {
							color: #000;
							margin: 0;
							font-size: 20px;
							font-weight: bold;
						}
						.header p {
							margin: 5px 0;
							color: #000;
							font-size: 11px;
						}
						.section {
							margin-bottom: 20px;
						}
						.section h2 {
							color: #000;
							font-size: 14px;
							border-bottom: 1px solid #000;
							padding-bottom: 5px;
							margin-bottom: 10px;
							font-weight: bold;
						}
						table {
							width: 100%;
							border-collapse: collapse;
							margin-bottom: 15px;
							font-size: 11px;
						}
						th, td {
							border: 1px solid #000;
							padding: 8px;
							text-align: left;
						}
						th {
							background-color: #f5f5f5 !important;
							font-weight: bold;
							color: #000;
							-webkit-print-color-adjust: exact;
							color-adjust: exact;
						}
						.total-row {
							background-color: #e3f2fd !important;
							font-weight: bold;
							-webkit-print-color-adjust: exact;
							color-adjust: exact;
						}
						.amount {
							text-align: right;
							font-family: 'Courier New', monospace;
							font-weight: bold;
						}
						.positive {
							color: #000;
						}
						.negative {
							color: #000;
						}
						.summary-cards {
							display: flex;
							gap: 15px;
							margin-bottom: 20px;
						}
						.card {
							flex: 1;
							border: 1px solid #000;
							padding: 10px;
							border-radius: 4px;
							text-align: center;
						}
						.card-title {
							font-size: 10px;
							color: #000;
							margin-bottom: 5px;
							font-weight: bold;
						}
						.card-value {
							font-size: 16px;
							font-weight: bold;
							color: #000;
						}
						.print-info {
							text-align: center;
							font-size: 10px;
							color: #000;
							margin-top: 20px;
							border-top: 1px solid #000;
							padding-top: 10px;
						}
						@media print {
							body { -webkit-print-color-adjust: exact; color-adjust: exact; }
							th { background-color: #f5f5f5 !important; }
							.total-row { background-color: #e3f2fd !important; }
						}
					</style>
				</head>
				<body>
					<div class="header">
						<h1>TỔNG KẾT CA LÀM VIỆC</h1>
						<p>Hồ sơ POS: ${this.posProfile?.name || 'N/A'}</p>
						<p>Nhân viên: ${frappe.session?.user_fullname || frappe.session?.user || 'N/A'}</p>
						<p>Ngày in: ${printDate} ${printTime}</p>
					</div>

					<div class="section">
						<h2>THÔNG TIN CA LÀM VIỆC</h2>
						<table>
							<tr><td><strong>Mã ca:</strong></td><td>${this.displayShiftReportId}</td></tr>
							<tr><td><strong>Thời gian mở ca:</strong></td><td>${this.formatDateTime(this.shiftReportData?.opening_date, this.shiftReportData?.opening_time)}</td></tr>
							<tr><td><strong>Trạng thái xác minh:</strong></td><td>${this.shiftReportData?.verification_status || 'Chưa xác minh'}</td></tr>
						</table>
					</div>

					<div class="section">
						<h2>TỔNG KẾT DOANH THU</h2>
						<div class="summary-cards">
							<div class="card">
								<div class="card-title">Tổng số hóa đơn</div>
								<div class="card-value">${this.shiftReportData?.invoice_count || 0}</div>
							</div>
							<div class="card">
								<div class="card-title">Tổng tiền bán</div>
								<div class="card-value positive">${this.formatCurrency(this.shiftReportData?.total_sales || 0)}</div>
							</div>
							<div class="card">
								<div class="card-title">Tổng tiền trả lại</div>
								<div class="card-value negative">${this.formatCurrency(this.shiftReportData?.total_returns || 0)}</div>
							</div>
							<div class="card">
								<div class="card-title">Tổng thu nhập</div>
								<div class="card-value">${this.formatCurrency((this.shiftReportData?.total_sales || 0) + (this.shiftReportData?.total_returns || 0))}</div>
							</div>
						</div>
					</div>

					<div class="section">
						<h2>BẢNG ĐỐI CHIẾU THANH TOÁN</h2>
						<table>
							<thead>
								<tr>
									<th>Phương thức thanh toán</th>
									<th class="amount">Số dư đầu ca</th>
									<th class="amount">Doanh thu bán</th>
									<th class="amount">Doanh thu trả lại</th>
									<th class="amount">Tổng giao dịch</th>
									<th class="amount">Dự kiến đóng ca</th>
									<th class="amount">Thực tế đóng ca</th>
									<th class="amount">Chênh lệch</th>
								</tr>
							</thead>
							<tbody>
			`;

			// Thêm các hàng payment summary
			this.paymentSummaryDataWithTotal.forEach(item => {
				const transactionClass = item.transaction_amount >= 0 ? 'positive' : 'negative';
				const isTotalRow = item.isTotalRow;
				const rowClass = isTotalRow ? 'total-row' : '';

				content += `
					<tr class="${rowClass}">
						<td>${item.payment_method}</td>
						<td class="amount">${this.formatCurrency(item.opening_amount || 0)}</td>
						<td class="amount positive">${this.formatCurrency(item.sales_amount || 0)}</td>
						<td class="amount negative">${this.formatCurrency(item.returns_amount || 0)}</td>
						<td class="amount ${transactionClass}">${this.formatCurrency(item.transaction_amount || 0)}</td>
						<td class="amount">${this.formatCurrency(item.expected_closing_amount || 0)}</td>
						<td class="amount">${this.formatCurrency(item.actual_closing_amount || 0)}</td>
						<td class="amount">${this.formatCurrency(item.difference || 0)}</td>
					</tr>
				`;
			});

			content += `
							</tbody>
						</table>
					</div>

					<div class="print-info">
						<p>Báo cáo tổng kết ca được tạo tự động bởi hệ thống POS Awesome</p>
						<p>Chỉ in trang tổng kết để đối chiếu và xác minh số liệu</p>
					</div>
				</body>
			</html>`;

			return content;
		},

		async handlePostShiftClose() {
			console.log("[SHIFT_CLOSE_SUCCESS] Starting post-shift-close cleanup: logout, clear cache, refresh");

			try {
				// Step 1: Clear browser cache/storage
				await this.clearBrowserCache();

				// Step 2: Logout user after a short delay
				setTimeout(() => {
					console.log("[SHIFT_CLOSE_SUCCESS] Performing user logout");
					this.performLogout();
				}, 1500);

				// Step 3: Refresh page after logout delay
				setTimeout(() => {
					console.log("[SHIFT_CLOSE_SUCCESS] Refreshing page");
					window.location.reload();
				}, 2500);

			} catch (error) {
				console.error("[SHIFT_CLOSE_SUCCESS] Error during post-shift-close cleanup:", error);
				// Fallback: Force refresh after error
				setTimeout(() => {
					window.location.reload();
				}, 1000);
			}
		},

		async clearBrowserCache() {
			console.log("[SHIFT_CLOSE_SUCCESS] Clearing browser cache and storage");

			try {
				// Clear localStorage
				localStorage.clear();
				console.log("[SHIFT_CLOSE_SUCCESS] Cleared localStorage");

				// Clear sessionStorage
				sessionStorage.clear();
				console.log("[SHIFT_CLOSE_SUCCESS] Cleared sessionStorage");

				// Clear IndexedDB databases (if any POS-related)
				if (window.indexedDB) {
					const dbNames = ['pos_offline_db', 'pos_cache', 'posawesome_offline'];
					const clearPromises = dbNames.map(dbName => {
						return new Promise((resolve) => {
							try {
								const deleteRequest = window.indexedDB.deleteDatabase(dbName);
								deleteRequest.onsuccess = () => {
									console.log(`[SHIFT_CLOSE_SUCCESS] Cleared IndexedDB: ${dbName}`);
									resolve();
								};
								deleteRequest.onerror = () => {
									console.warn(`[SHIFT_CLOSE_SUCCESS] Failed to clear IndexedDB: ${dbName}`);
									resolve();
								};
							} catch (e) {
								console.warn(`[SHIFT_CLOSE_SUCCESS] Error clearing IndexedDB ${dbName}:`, e);
								resolve();
							}
						});
					});
					await Promise.all(clearPromises);
				}

				// Clear cache storage (if supported)
				if ('caches' in window) {
					const cacheNames = await caches.keys();
					await Promise.all(cacheNames.map(name => caches.delete(name)));
					console.log("[SHIFT_CLOSE_SUCCESS] Cleared cache storage");
				}

				console.log("[SHIFT_CLOSE_SUCCESS] Browser cache cleared successfully");

			} catch (error) {
				console.error("[SHIFT_CLOSE_SUCCESS] Error clearing browser cache:", error);
			}
		},

		performLogout() {
			console.log("[SHIFT_CLOSE_SUCCESS] Performing user logout");

			try {
				// Use Frappe's logout mechanism if available
				if (window.frappe && frappe.app) {
					console.log("[SHIFT_CLOSE_SUCCESS] Using frappe.app.logout()");
					frappe.app.logout();
				} else if (window.frappe && frappe.call) {
					// Fallback: Call logout API
					console.log("[SHIFT_CLOSE_SUCCESS] Using frappe.call logout API");
					frappe.call({
						method: "logout",
						callback: () => {
							console.log("[SHIFT_CLOSE_SUCCESS] Logout API called successfully");
						}
					});
				} else {
					// Last resort: Redirect to login page
					console.log("[SHIFT_CLOSE_SUCCESS] Redirecting to login page");
					window.location.href = '/login';
				}

				console.log("[SHIFT_CLOSE_SUCCESS] Logout initiated successfully");

			} catch (error) {
				console.error("[SHIFT_CLOSE_SUCCESS] Error performing logout:", error);

				// Fallback: Force redirect to login
				console.log("[SHIFT_CLOSE_SUCCESS] Force redirect to login");
				window.location.href = '/login';
			}
		}
	}
};
</script>

<style scoped>
.v-dialog { max-height: 90vh; }
@media (max-width: 1366px) { .v-dialog { max-width: 95vw; max-height: 85vh; } }

.payment-summary-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-primary));
	color: rgb(var(--v-theme-on-primary));
	font-weight: 600;
	font-size: 0.8rem;
	padding: 8px 12px;
}

.actual-closing-input { min-width: 120px; }
.actual-closing-input :deep(.v-field__input) { text-align: right; font-family: 'Courier New', monospace; }

.action-buttons-section {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-bottom: 1px solid #dee2e6;
	position: sticky;
	top: 0;
	z-index: 10;
}

.currency-amount { font-family: 'Roboto Mono', monospace; font-weight: 500; letter-spacing: 0.5px; }

:deep(.payment-summary-table .v-data-table__tbody tr:last-child) {
	background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-variant)) 100%);
	color: rgb(var(--v-theme-on-primary));
	border-top: 2px solid rgb(var(--v-theme-primary-variant));
}

:deep(.payment-summary-table .v-data-table__tbody tr:last-child td) {
	padding: 12px 16px !important;
	border-bottom: none !important;
	font-size: 0.9rem !important;
	font-weight: 600 !important;
	text-align: center;
}

.action-btn {
	min-height: 44px !important;
	padding: 0 16px !important;
	font-size: 0.9rem !important;
	font-weight: 500 !important;
}

.header-content { display: flex; flex-direction: column; gap: 8px; }
.header-title { margin: 0; font-size: 1.25rem; font-weight: 600; color: rgb(var(--v-theme-on-surface)); }

.shift-info { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 4px; }
.shift-info-item { display: flex; align-items: center; gap: 6px; }
.shift-info-label { font-size: 0.8rem; font-weight: 600; color: rgb(var(--v-theme-on-surface-variant)); min-width: 55px; }
.shift-info-value {
	font-size: 0.8rem; font-weight: 500; color: rgb(var(--v-theme-on-surface));
	font-family: 'Courier New', monospace;
	background: rgba(var(--v-theme-primary), 0.1);
	padding: 2px 6px; border-radius: 4px;
	border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.verification-status-chip {
	font-weight: 600;
	font-size: 0.75rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	transition: all 0.3s ease;
}

.verification-status-chip:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.verification-warning-text {
	font-size: 0.7rem;
	color: rgb(var(--v-theme-warning));
	font-weight: 500;
	font-style: italic;
	line-height: 1.2;
	margin-top: 2px;
}
</style>