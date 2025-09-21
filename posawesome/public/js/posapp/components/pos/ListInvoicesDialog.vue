<template>
	<v-dialog v-model="show" max-width="1200px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-receipt-text-multiple</v-icon>
				<div class="header-content">
					<div class="header-main">
						<h3 class="header-title">{{ __("Shift Report Invoices") }}</h3>
						<!-- Shift Information -->
						<div class="shift-info" v-if="shiftReportData">
							<div class="shift-info-item">
								<span class="shift-info-label">{{ __("Shift ID:") }}</span>
								<span class="shift-info-value">{{ shiftReportData.shift_report_id || 'N/A' }}</span>
							</div>
							<div class="shift-info-item" v-if="shiftReportData.created">
								<span class="shift-info-label">{{ __("Started:") }}</span>
								<span class="shift-info-value">{{ formatDateTime(shiftReportData.created) }}</span>
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
				<!-- Action Buttons Section (MOVED TO TOP) -->
				<div class="pa-4 action-buttons-section">
					<div class="d-flex justify-space-between align-center">
						<div class="d-flex align-center gap-4">
							<h6 class="text-subtitle-1 mb-0">{{ __("Shift Report Actions") }}</h6>

							<!-- Verification Status Display -->
							<v-chip
								v-if="shiftReportData"
								:color="getVerificationColor(shiftReportData.verification_status)"
								variant="outlined"
								size="small"
								class="verification-status-chip"
							>
								<v-icon size="16" class="me-1">
									{{ getVerificationIcon(shiftReportData.verification_status) }}
								</v-icon>
								{{ shiftReportData.verification_status || 'Pending' }}
							</v-chip>
						</div>

						<div class="d-flex action-buttons-group">
							<!-- Verify Button -->
							<v-tooltip
								v-if="isVerifiedOrConfirmed"
								text="Shift report has already been verified"
							>
								<template v-slot:activator="{ props }">
									<v-btn
										v-bind="props"
										color="success"
										variant="outlined"
										prepend-icon="mdi-check-circle-outline"
										:disabled="isVerifiedOrConfirmed"
										@click="verifyShiftReport"
										class="action-btn"
									>
										{{ __("Verify") }}
									</v-btn>
								</template>
							</v-tooltip>
							<v-btn
								v-else
								color="success"
								variant="outlined"
								prepend-icon="mdi-check-circle-outline"
								:loading="verifying"
								@click="verifyShiftReport"
								class="action-btn"
							>
								{{ __("Verify") }}
							</v-btn>

							<v-btn
								color="info"
								variant="outlined"
								prepend-icon="mdi-printer"
								@click="printReport"
								class="action-btn"
							>
								{{ __("Print") }}
							</v-btn>
							<v-btn
								color="primary"
								variant="flat"
								prepend-icon="mdi-download"
								@click="exportData"
								class="action-btn"
							>
								{{ __("Export") }}
							</v-btn>
							<v-btn
								variant="text"
								@click="close"
								class="action-btn"
							>
								{{ __("Close") }}
							</v-btn>
						</div>
					</div>
				</div>

				<v-divider></v-divider>

				<!-- Payment Summary Section -->
				<div class="pa-4">
					<h6 class="text-subtitle-1 mb-3">{{ __("Payment Summary") }}</h6>
					<v-data-table
						:headers="paymentSummaryHeaders"
						:items="paymentSummaryData"
						:loading="loadingSummary"
						density="compact"
						:items-per-page="-1"
						hide-default-footer
						class="elevation-0 payment-summary-table"
					>
						<template #item.opening_amount="{ item }">
							<span class="font-weight-bold currency-amount">{{ formatCurrency(item.opening_amount || 0) }}</span>
						</template>

						<template #item.transaction_amount="{ item }">
							<span class="currency-amount" :class="item.transaction_amount >= 0 ? 'text-success' : 'text-error'">
								{{ formatCurrency(item.transaction_amount || 0) }}
							</span>
						</template>

						<template #item.closing_amount="{ item }">
							<span class="font-weight-bold text-primary currency-amount">{{ formatCurrency(item.closing_amount || 0) }}</span>
						</template>
					</v-data-table>

					<!-- Total Row -->
					<v-divider class="my-3"></v-divider>
					<div class="total-row d-flex justify-space-between align-center">
						<span class="font-weight-bold">{{ __("TOTAL") }}</span>
						<div class="d-flex gap-8 align-center">
							<span class="font-weight-bold currency-amount">{{ formatCurrency(totalOpeningAmount) }}</span>
							<span class="font-weight-bold text-success currency-amount">{{ formatCurrency(totalTransactionAmount) }}</span>
							<span class="font-weight-bold text-primary currency-amount">{{ formatCurrency(totalClosingAmount) }}</span>
						</div>
					</div>
				</div>

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
								{{ formatCurrency((summary.total_sales || 0) + (summary.total_returns || 0)) }}
							</div>
						</v-card>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Info Banner -->
				<div class="pa-3 bg-blue-lighten-5 rounded mb-2">
					<v-icon size="16" color="info" class="me-2">mdi-information</v-icon>
					<span class="text-caption text-info">
						{{ __("Showing latest 5 invoices per page, sorted by newest first") }}
					</span>
				</div>

				<!-- Data Table with Pagination -->
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
					:items-per-page-options="[5, 10, 15, 25]"
				>
					<!-- Custom pagination slot -->
					<template #bottom>
						<div class="d-flex align-center justify-space-between pa-3">
							<div class="text-caption text-medium-emphasis">
								{{ __("Showing latest 5 invoices per page") }}
							</div>
							<v-pagination
								v-model="currentPage"
								:length="Math.ceil(filteredInvoices.length / itemsPerPage)"
								:total-visible="5"
								size="small"
								variant="outlined"
							></v-pagination>
						</div>
					</template>
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
			searchQuery: "",
			statusFilter: "",
			paymentFilter: "",
			itemsPerPage: 5,
			currentPage: 1,
			totalInvoices: 0,
			invoices: [],
			summary: {
				total_invoices: 0,
				total_sales: 0,
				total_returns: 0
			},
			// Payment Summary Data
			loadingSummary: false,
			paymentSummaryData: [],
			openingAmounts: {},
			// Verification Data
			verifying: false,
			shiftReportData: null,
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
			],
			paymentSummaryHeaders: [
				{ title: this.__("Payment Method"), key: "payment_method", width: "150px" },
				{ title: this.__("Opening Amount"), key: "opening_amount", width: "150px", align: "end" },
				{ title: this.__("Transactions"), key: "transaction_amount", width: "150px", align: "end" },
				{ title: this.__("Closing Amount"), key: "closing_amount", width: "150px", align: "end" }
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
		},
		// Payment Summary Totals
		totalOpeningAmount() {
			return this.paymentSummaryData.reduce((sum, item) => sum + (item.opening_amount || 0), 0);
		},
		totalTransactionAmount() {
			return this.paymentSummaryData.reduce((sum, item) => sum + (item.transaction_amount || 0), 0);
		},
		totalClosingAmount() {
			return this.paymentSummaryData.reduce((sum, item) => sum + (item.closing_amount || 0), 0);
		},
		// Verification Computed Properties
		isVerifiedOrConfirmed() {
			return this.shiftReportData?.verification_status === 'Verified' ||
				   this.shiftReportData?.verification_status === 'Confirmed';
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal && this.shiftReportId) {
				console.log("Dialog opened with shiftReportId:", this.shiftReportId);
				this.loadInvoices();
			} else if (newVal && !this.shiftReportId) {
				console.warn("Dialog opened but no shiftReportId provided");
				this.showError("No shift report ID provided");
			}
		},
		shiftReportId(newVal, oldVal) {
			if (newVal && newVal !== oldVal && this.modelValue) {
				console.log("shiftReportId changed from", oldVal, "to", newVal);
				this.loadInvoices();
			}
		}
	},
	mounted() {
		this.debouncedSearch = this.debounce(this.applyFilters, 300);
		console.log("ListInvoicesDialog mounted, shiftReportId:", this.shiftReportId);
	},
	methods: {
	async loadInvoices() {
		if (!this.shiftReportId) {
			console.log("No shiftReportId provided, skipping load");
			return;
		}

		this.loading = true;
		try {
			console.log("Loading invoices for shift:", this.shiftReportId);

			// ✅ REAL API CALL - Sử dụng API mới với payment summary
			const response = await frappe.call({
				method: "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
				args: {
					shift_report_id: this.shiftReportId
				}
			});

			console.log("API Response:", response);

			if (response.message && response.message.invoices) {
				// ✅ HANDLE SHIFT REPORT DATA - API trả về object với invoices array
				const shiftReportData = response.message;

				console.log("Shift Report Data:", shiftReportData);

				// ✅ SET INVOICES DIRECTLY FROM SHIFT REPORT
				this.invoices = shiftReportData.invoices || [];

				// ✅ SORT BY NEWEST FIRST (descending order)
				this.invoices = this.invoices.sort((a, b) => {
					// First sort by invoice_date (newest first)
					const dateA = new Date(a.invoice_date + ' ' + (a.invoice_time || '00:00:00'));
					const dateB = new Date(b.invoice_date + ' ' + (b.invoice_time || '00:00:00'));

					// If dates are the same, sort by invoice_no
					if (dateA.getTime() === dateB.getTime()) {
						return b.invoice_no.localeCompare(a.invoice_no);
					}

					return dateB.getTime() - dateA.getTime();
				});

				// ✅ SET SUMMARY DATA FROM SHIFT REPORT
				this.summary = {
					total_invoices: shiftReportData.invoice_count || 0,
					total_sales: shiftReportData.total_sales || 0,
					total_returns: shiftReportData.total_returns || 0
				};

				this.totalInvoices = this.invoices.length;

				console.log(`Loaded ${this.invoices.length} invoices for shift ${this.shiftReportId}`);
				console.log("Summary:", this.summary);

				// ✅ LOAD PAYMENT SUMMARY FROM NEW API RESPONSE
				if (shiftReportData.payment_summaries) {
					this.paymentSummaryData = shiftReportData.payment_summaries;
					console.log("Payment summary loaded from API:", this.paymentSummaryData);
				} else {
					// Fallback to old method if payment_summaries not available
					this.loadPaymentSummaryFromShiftReport(shiftReportData);
				}

				// Store shift report data for verification status
				this.shiftReportData = shiftReportData;

				// Load shift report data for footer status bar
				await this.loadShiftReportData();

			} else {
				console.warn("No shift report data found or invalid response format");
				console.log("Response structure:", response);
				this.invoices = [];
				this.totalInvoices = 0;
				this.summary = {
					total_invoices: 0,
					total_sales: 0,
					total_returns: 0
				};
			}

		} catch (error) {
			console.error("Error loading invoices:", error);
			this.showError("Failed to load invoices from database");
			// Fallback to empty state
			this.invoices = [];
			this.totalInvoices = 0;
		} finally {
			this.loading = false;
		}
	},

	// ✅ LOAD SHIFT REPORT DATA FOR FOOTER STATUS BAR
	async loadShiftReportData() {
		if (!this.shiftReportId) {
			console.warn("[SHIFT_REPORT] No shiftReportId provided");
			return;
		}

		try {
			console.log("[SHIFT_REPORT] Loading shift report data for footer:", this.shiftReportId);
			console.log("[SHIFT_REPORT] shiftReportId type:", typeof this.shiftReportId);

			// ✅ DETECT IF shiftReportId IS AN OBJECT INSTEAD OF STRING
			let actualShiftReportId = this.shiftReportId;

			if (typeof this.shiftReportId === 'object' && this.shiftReportId !== null) {
				console.log("[SHIFT_REPORT] 📋 shiftReportId is an object, extracting ID...");
				console.log("[SHIFT_REPORT] Object keys:", Object.keys(this.shiftReportId));
				console.log("[SHIFT_REPORT] Object doctype:", this.shiftReportId.doctype);

				// ✅ CHECK IF THIS IS POS OPENING SHIFT (wrong object type)
				if (this.shiftReportId.doctype === "POS Opening Shift") {
					console.log("[SHIFT_REPORT] ⚠️  Received POS Opening Shift object, need to get associated shift report");

					// Try to get shift report from opening shift
					if (this.shiftReportId.shift_report) {
						console.log("[SHIFT_REPORT] ✅ Opening shift has shift_report:", this.shiftReportId.shift_report);
						actualShiftReportId = this.shiftReportId.shift_report;
					} else {
						console.error("[SHIFT_REPORT] ❌ Opening shift has no associated shift report");
						console.error("[SHIFT_REPORT] Opening shift details:", {
							name: this.shiftReportId.name,
							status: this.shiftReportId.status,
							user: this.shiftReportId.user
						});
						this.showError("No shift report found for this opening shift. Please create a shift report first.");
						return;
					}
				}
				// ✅ THIS IS ALREADY A POS SHIFT REPORT OBJECT
				else if (this.shiftReportId.doctype === "POS Shift Report") {
					console.log("[SHIFT_REPORT] ✅ Received POS Shift Report object directly");

					// Use the name field as the ID
					if (this.shiftReportId.name) {
						actualShiftReportId = this.shiftReportId.name;
						console.log("[SHIFT_REPORT] ✅ Using shift report name:", actualShiftReportId);
					} else {
						console.error("[SHIFT_REPORT] ❌ POS Shift Report object missing name field");
						this.showError("Invalid shift report object - missing name field");
						return;
					}
				}
				// ✅ UNKNOWN OBJECT TYPE - Try to extract any valid ID
				else {
					console.log("[SHIFT_REPORT] ⚠️  Unknown object type, trying to extract ID...");

					// Priority: name > shift_report_id > any string field
					if (this.shiftReportId.name) {
						actualShiftReportId = this.shiftReportId.name;
						console.log("[SHIFT_REPORT] ✅ Using name field:", actualShiftReportId);
					} else if (this.shiftReportId.shift_report_id) {
						actualShiftReportId = this.shiftReportId.shift_report_id;
						console.log("[SHIFT_REPORT] ✅ Using shift_report_id field:", actualShiftReportId);
					} else {
						// Try any string field
						let foundId = null;
						for (const [key, value] of Object.entries(this.shiftReportId)) {
							if (typeof value === 'string' && value && value.trim().length > 0 && value.length < 50) {
								console.log(`[SHIFT_REPORT] ⚠️  Found potential ID in '${key}': ${value}`);
								foundId = value.trim();
								break;
							}
						}

						if (foundId) {
							actualShiftReportId = foundId;
							console.log("[SHIFT_REPORT] ✅ Using found field as ID:", actualShiftReportId);
						} else {
							console.error("[SHIFT_REPORT] ❌ Cannot extract valid ID from unknown object");
							console.error("[SHIFT_REPORT] Object details:", JSON.stringify(this.shiftReportId, null, 2));
							this.showError("Cannot identify shift report from the provided data");
							return;
						}
					}
				}
			}

			// ✅ VALIDATE FINAL ID
			if (!actualShiftReportId || actualShiftReportId.trim() === '') {
				console.error("[SHIFT_REPORT] ❌ Final shiftReportId is empty or invalid:", actualShiftReportId);
				return;
			}

			console.log("[SHIFT_REPORT] ✅ Final shiftReportId to use:", actualShiftReportId);
			console.log("[SHIFT_REPORT] 📊 Original object had shift_report:", this.shiftReportId.shift_report);
			console.log("[SHIFT_REPORT] 📊 Original object had shift_report_id:", this.shiftReportId.shift_report_id);

			console.log("[SHIFT_REPORT] Using custom API with ID:", actualShiftReportId);
			const shiftReportResponse = await frappe.call({
				method: "posawesome.posawesome.api.shift_reports.get_shift_report_with_payment_summary",
				args: {
					shift_report_id: actualShiftReportId
				}
			});

			console.log("[SHIFT_REPORT] Generic API Response:", shiftReportResponse);

			console.log("[SHIFT_REPORT] API Response:", shiftReportResponse);
			console.log("[SHIFT_REPORT] Response type:", typeof shiftReportResponse);
			console.log("[SHIFT_REPORT] Has message:", shiftReportResponse && 'message' in shiftReportResponse);

			if (shiftReportResponse && shiftReportResponse.message) {
				// ✅ HANDLE UPDATED API RESPONSE FORMAT (direct data)
				const shiftReportData = shiftReportResponse.message;

				// Emit event to update footer status bar
				if (this.eventBus) {
					this.eventBus.emit("register_shift_report", {
						shift_report_id: shiftReportData.shift_report_id,
						total_sales: shiftReportData.total_sales || 0,
						total_returns: shiftReportData.total_returns || 0,
						total_invoices: shiftReportData.invoice_count || 0,
						total_revenue: (shiftReportData.total_sales || 0) + (shiftReportData.total_returns || 0),
						last_invoice: shiftReportData.invoices && shiftReportData.invoices.length > 0 ?
							shiftReportData.invoices[shiftReportData.invoices.length - 1].invoice_no : "",
						invoices: shiftReportData.invoices || []
					});
				}

				console.log("[SHIFT_REPORT] Shift report data loaded for footer:", shiftReportData.shift_report_id);
			} else {
				console.error("[SHIFT_REPORT] API call failed - no data returned");
			}
		} catch (error) {
			console.error("[SHIFT_REPORT] Error loading shift report data for footer:", error);

			// ✅ FALLBACK: Try to emit with default values
			if (this.eventBus) {
				this.eventBus.emit("register_shift_report", {
					shift_report_id: this.shiftReportId,
					total_sales: 0,
					total_returns: 0,
					total_invoices: 0,
					total_revenue: 0,
					last_invoice: "",
					invoices: []
				});
			}
		}
	},

	// ✅ LOAD PAYMENT SUMMARY FROM SHIFT REPORT DATA
	loadPaymentSummaryFromShiftReport(shiftReportData) {
		try {
			console.log("Loading payment summary from shift report data");

			if (!shiftReportData || !shiftReportData.payment_breakdown) {
				console.warn("No payment breakdown data in shift report");
				this.paymentSummaryData = [];
				return;
			}

			// Convert payment_breakdown object to array format for UI
			const paymentMethods = [];
			const breakdown = shiftReportData.payment_breakdown;

			// Get opening amounts from shift report (if available)
			const openingAmounts = shiftReportData.opening_amounts || {};
			const expectedClosing = shiftReportData.expected_closing_amounts || {};

			Object.keys(breakdown).forEach(method => {
				const transactionAmount = breakdown[method] || 0;
				const openingAmount = openingAmounts[method] || 0;
				const expectedAmount = expectedClosing[method] || openingAmount;

				paymentMethods.push({
					payment_method: method,
					opening_amount: openingAmount,
					transaction_amount: transactionAmount,
					closing_amount: openingAmount + transactionAmount
				});
			});

			// Sort by payment method name
			this.paymentSummaryData = paymentMethods.sort((a, b) =>
				a.payment_method.localeCompare(b.payment_method)
			);

			console.log("Payment summary loaded from shift report:", this.paymentSummaryData);

		} catch (error) {
			console.error("Error loading payment summary from shift report:", error);
			this.paymentSummaryData = [];
		}
	},

	// Fallback method to calculate payment summary from invoices only
	calculatePaymentSummaryFromInvoices() {
		console.log("Using fallback payment summary calculation");

		const paymentMethods = {};
		this.invoices.forEach(invoice => {
			const method = invoice.payment_method || "Cash";
			const amount = parseFloat(invoice.total_amount) || 0;

			if (!paymentMethods[method]) {
				paymentMethods[method] = {
					payment_method: method,
					opening_amount: 0, // Unknown without opening shift data
					transaction_amount: 0,
					closing_amount: 0
				};
			}

			paymentMethods[method].transaction_amount += invoice.is_return ? -amount : amount;
			paymentMethods[method].closing_amount = paymentMethods[method].opening_amount + paymentMethods[method].transaction_amount;
		});

		this.paymentSummaryData = Object.values(paymentMethods).sort((a, b) =>
			a.payment_method.localeCompare(b.payment_method)
		);
	},

		calculateSummary() {
			try {
				console.log("Calculating summary for", this.invoices.length, "invoices");

				// ✅ ENHANCED SUMMARY CALCULATION với validation
				const salesInvoices = this.invoices.filter(inv => !inv.is_return && inv.status === 'Submitted');
				const returnInvoices = this.invoices.filter(inv => inv.is_return && inv.status === 'Submitted');

				const totalSales = salesInvoices.reduce((sum, inv) => {
					const amount = parseFloat(inv.total_amount) || 0;
					return sum + amount;
				}, 0);

				const totalReturns = Math.abs(returnInvoices.reduce((sum, inv) => {
					const amount = parseFloat(inv.total_amount) || 0;
					return sum + amount;
				}, 0));

				this.summary = {
					total_invoices: this.invoices.length,
					total_sales: totalSales,
					total_returns: totalReturns
				};

				console.log("Summary calculated:", this.summary);

			} catch (error) {
				console.error("Error calculating summary:", error);
				// Fallback to safe values
				this.summary = {
					total_invoices: this.invoices.length || 0,
					total_sales: 0,
					total_returns: 0
				};
			}
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

		// ✅ HELPER METHOD: Get payment method from invoice
		getPaymentMethod(invoice) {
			try {
				if (invoice.payments && Array.isArray(invoice.payments) && invoice.payments.length > 0) {
					return invoice.payments[0].mode_of_payment || "Cash";
				}
				// Fallback to default payment method
				return "Cash";
			} catch (error) {
				console.warn("Error getting payment method:", error);
				return "Cash";
			}
		},

		// ✅ HELPER METHOD: Format time from API response
		formatTime(postingTime) {
			try {
				if (!postingTime) return "00:00:00";

				// If posting_time is already in HH:MM:SS format, return as is
				if (typeof postingTime === 'string' && postingTime.match(/^\d{2}:\d{2}:\d{2}$/)) {
					return postingTime;
				}

				// If it's a Date object or timestamp, format it
				const date = new Date(postingTime);
				if (!isNaN(date.getTime())) {
					return date.toTimeString().split(' ')[0];
				}

				return "00:00:00";
			} catch (error) {
				console.warn("Error formatting time:", error);
				return "00:00:00";
			}
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
			try {
				// Get currency from POS Profile or default to USD
				let currency = 'USD';
				if (this.posProfile && this.posProfile.currency) {
					currency = this.posProfile.currency;
				}

				return new Intl.NumberFormat('en-US', {
					style: 'currency',
					currency: currency,
					minimumFractionDigits: 2,
					maximumFractionDigits: 2
				}).format(amount || 0);
			} catch (error) {
				console.warn("Error formatting currency:", error);
				return `$${amount || 0}`;
			}
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
				console.log("Exporting data for shift:", this.shiftReportId);

				// ✅ ENHANCED EXPORT: Include invoices and payment summary
				const invoiceData = this.invoices.map(item => ({
					"Loại": "Hóa đơn",
					"Số hóa đơn": item.invoice_no,
					"Ngày": item.invoice_date,
					"Giờ": item.invoice_time,
					"Khách hàng": item.customer || "N/A",
					"Tổng tiền": item.total_amount || 0,
					"Thuế": item.tax_amount || 0,
					"Phương thức thanh toán": item.payment_method || "Tiền mặt",
					"Trạng thái": item.status || "Không xác định",
					"Trả hàng": item.is_return ? "Có" : "Không"
				}));

				// Add payment summary data
				const paymentSummaryData = this.paymentSummaryData.map(item => ({
					"Loại": "Tóm tắt thanh toán",
					"Số hóa đơn": item.payment_method,
					"Ngày": "",
					"Giờ": "",
					"Khách hàng": "",
					"Tổng tiền": "",
					"Thuế": "",
					"Phương thức thanh toán": item.payment_method,
					"Trạng thái": "",
					"Trả hàng": "",
					"Số tiền đầu ca": item.opening_amount || 0,
					"Phát sinh trong ca": item.transaction_amount || 0,
					"Số tiền cuối ca": item.closing_amount || 0
				}));

				// Add summary cards data
				const summaryData = [{
					"Loại": "Tóm tắt tổng hợp",
					"Số hóa đơn": `Tổng số hóa đơn: ${this.summary.total_invoices || 0}`,
					"Ngày": "",
					"Giờ": "",
					"Khách hàng": "",
					"Tổng tiền": "",
					"Thuế": "",
					"Phương thức thanh toán": "",
					"Trạng thái": "",
					"Trả hàng": "",
					"Số tiền đầu ca": "",
					"Phát sinh trong ca": "",
					"Số tiền cuối ca": ""
				}, {
					"Loại": "Tóm tắt tổng hợp",
					"Số hóa đơn": `Tổng bán: ${this.formatCurrency(this.summary.total_sales || 0)}`,
					"Ngày": "",
					"Giờ": "",
					"Khách hàng": "",
					"Tổng tiền": "",
					"Thuế": "",
					"Phương thức thanh toán": "",
					"Trạng thái": "",
					"Trả hàng": "",
					"Số tiền đầu ca": "",
					"Phát sinh trong ca": "",
					"Số tiền cuối ca": ""
				}, {
					"Loại": "Tóm tắt tổng hợp",
					"Số hóa đơn": `Tổng trả: ${this.formatCurrency(this.summary.total_returns || 0)}`,
					"Ngày": "",
					"Giờ": "",
					"Khách hàng": "",
					"Tổng tiền": "",
					"Thuế": "",
					"Phương thức thanh toán": "",
					"Trạng thái": "",
					"Trả hàng": "",
					"Số tiền đầu ca": "",
					"Phát sinh trong ca": "",
					"Số tiền cuối ca": ""
				}, {
					"Loại": "Tóm tắt tổng hợp",
					"Số hóa đơn": `Tổng thuần: ${this.formatCurrency((this.summary.total_sales || 0) + (this.summary.total_returns || 0))}`,
					"Ngày": "",
					"Giờ": "",
					"Khách hàng": "",
					"Tổng tiền": "",
					"Thuế": "",
					"Phương thức thanh toán": "",
					"Trạng thái": "",
					"Trả hàng": "",
					"Số tiền đầu ca": "",
					"Phát sinh trong ca": "",
					"Số tiền cuối ca": ""
				}];

				// Add totals row
				const totalsData = [{
					"Loại": "TỔNG CỘNG",
					"Số hóa đơn": "",
					"Ngày": "",
					"Giờ": "",
					"Khách hàng": "",
					"Tổng tiền": "",
					"Thuế": "",
					"Phương thức thanh toán": "",
					"Trạng thái": "",
					"Trả hàng": "",
					"Số tiền đầu ca": this.totalOpeningAmount,
					"Phát sinh trong ca": this.totalTransactionAmount,
					"Số tiền cuối ca": this.totalClosingAmount
				}];

				const data = [...invoiceData, {}, ...summaryData, {}, ...paymentSummaryData, {}, ...totalsData];

				if (data.length === 0) {
					this.showError("No data to export");
					return;
				}

				// ✅ GENERATE FILE NAME: Thời gian + ngày_tháng_năm_POS Profile name_CashierName
				const now = new Date();
				const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, ''); // HHMMSS
				const dateStr = now.toISOString().split('T')[0].replace(/-/g, '_'); // YYYY_MM_DD
				const posProfileName = (this.posProfile && this.posProfile.name) ? this.posProfile.name.replace(/\s+/g, '_') : 'Unknown_POS';
				const cashierName = frappe.session.user || 'Unknown_User';

				const fileName = `${timeStr}_${dateStr}_${posProfileName}_${cashierName}_Shift_Report.xlsx`;

				// Create Excel content with Unicode support
				const headers = Object.keys(data[0]);
				const excelContent = [
					headers.join('\t'), // Tab-separated for Excel
					...data.map(row =>
						headers.map(header => {
							const value = row[header];
							// Handle numbers and strings properly for Excel
							if (typeof value === 'number') {
								return value.toString();
							}
							if (typeof value === 'string') {
								// Escape quotes and wrap in quotes for Excel
								return `"${value.replace(/"/g, '""')}"`;
							}
							return value || '';
						}).join('\t')
					)
				].join('\n');

				// Download as Excel file (.xlsx extension but tab-separated content)
				const blob = new Blob(['\ufeff', excelContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = fileName;
				a.click();
				window.URL.revokeObjectURL(url);

				this.showSuccess(`Exported ${data.length} invoices successfully`);

			} catch (error) {
				console.error("Error exporting data:", error);
				this.showError("Failed to export data");
			}
		},

		async refreshData() {
			await this.loadInvoices();
		},

		// ✅ PRINT REPORT: Only first page with summary
		async printReport() {
			try {
				console.log("Printing shift report...");

				// Create print content
				const printContent = this.generatePrintContent();

				// Open print window
				const printWindow = window.open('', '_blank', 'width=800,height=600');
				if (!printWindow) {
					this.showError("Unable to open print window. Please check popup blocker.");
					return;
				}

				printWindow.document.write(printContent);
				printWindow.document.close();

				// Wait for content to load then print
				printWindow.onload = function() {
					printWindow.print();
					printWindow.close();
				};

				this.showSuccess("Print job sent successfully");

			} catch (error) {
				console.error("Error printing report:", error);
				this.showError("Failed to print report");
			}
		},

		// Generate HTML content for printing
		generatePrintContent() {
			const now = new Date();
			const printDate = now.toLocaleDateString('vi-VN');
			const printTime = now.toLocaleTimeString('vi-VN');

			let content = `
				<!DOCTYPE html>
				<html>
				<head>
					<title>Báo cáo ca làm việc</title>
					<meta charset="UTF-8">
					<style>
						@page {
							size: A4;
							margin: 1cm;
						}
						body {
							font-family: 'Arial', sans-serif;
							font-size: 12px;
							line-height: 1.4;
							color: #333;
							max-width: 100%;
						}
						.header {
							text-align: center;
							border-bottom: 2px solid #1976d2;
							padding-bottom: 10px;
							margin-bottom: 20px;
						}
						.header h1 {
							color: #1976d2;
							margin: 0;
							font-size: 18px;
						}
						.header p {
							margin: 5px 0;
							color: #666;
						}
						.section {
							margin-bottom: 20px;
						}
						.section h2 {
							color: #1976d2;
							font-size: 14px;
							border-bottom: 1px solid #ddd;
							padding-bottom: 5px;
							margin-bottom: 10px;
						}
						table {
							width: 100%;
							border-collapse: collapse;
							margin-bottom: 15px;
						}
						th, td {
							border: 1px solid #ddd;
							padding: 8px;
							text-align: left;
						}
						th {
							background-color: #f5f5f5;
							font-weight: bold;
							color: #333;
						}
						.total-row {
							background-color: #e3f2fd !important;
							font-weight: bold;
						}
						.amount {
							text-align: right;
							font-family: 'Courier New', monospace;
						}
						.positive {
							color: #2e7d32;
						}
						.negative {
							color: #d32f2f;
						}
						.summary-cards {
							display: flex;
							gap: 15px;
							margin-bottom: 20px;
						}
						.card {
							flex: 1;
							border: 1px solid #ddd;
							padding: 10px;
							border-radius: 4px;
							text-align: center;
						}
						.card-title {
							font-size: 10px;
							color: #666;
							margin-bottom: 5px;
						}
						.card-value {
							font-size: 16px;
							font-weight: bold;
							color: #1976d2;
						}
						.print-info {
							text-align: center;
							font-size: 10px;
							color: #999;
							margin-top: 20px;
							border-top: 1px solid #eee;
							padding-top: 10px;
						}
						@media print {
							body { print-color-adjust: exact; }
						}
					</style>
				</head>
				<body>
					<div class="header">
						<h1>BÁO CÁO CA LÀM VIỆC</h1>
						<p>POS Profile: ${this.posProfile?.name || 'N/A'}</p>
						<p>Nhân viên: ${frappe.session?.user_fullname || frappe.session?.user || 'N/A'}</p>
						<p>Ngày in: ${printDate} ${printTime}</p>
					</div>

					<div class="section">
						<h2>TÓM TẮT TỔNG QUAN</h2>
						<div class="summary-cards">
							<div class="card">
								<div class="card-title">Tổng số hóa đơn</div>
								<div class="card-value">${this.summary.total_invoices || 0}</div>
							</div>
							<div class="card">
								<div class="card-title">Tổng bán</div>
								<div class="card-value positive">${this.formatCurrency(this.summary.total_sales || 0)}</div>
							</div>
							<div class="card">
								<div class="card-title">Tổng trả</div>
								<div class="card-value negative">${this.formatCurrency(this.summary.total_returns || 0)}</div>
							</div>
							<div class="card">
								<div class="card-title">Tổng thuần</div>
								<div class="card-value">${this.formatCurrency((this.summary.total_sales || 0) + (this.summary.total_returns || 0))}</div>
							</div>
						</div>
					</div>

					<div class="section">
						<h2>TÓM TẮT THANH TOÁN THEO PHƯƠNG THỨC</h2>
						<table>
							<thead>
								<tr>
									<th>Phương thức thanh toán</th>
									<th class="amount">Số tiền đầu ca</th>
									<th class="amount">Phát sinh trong ca</th>
									<th class="amount">Số tiền cuối ca</th>
								</tr>
							</thead>
							<tbody>
			`;

			// Add payment summary rows
			this.paymentSummaryData.forEach(item => {
				const transactionClass = item.transaction_amount >= 0 ? 'positive' : 'negative';
				content += `
					<tr>
						<td>${item.payment_method}</td>
						<td class="amount">${this.formatCurrency(item.opening_amount || 0)}</td>
						<td class="amount ${transactionClass}">${this.formatCurrency(item.transaction_amount || 0)}</td>
						<td class="amount">${this.formatCurrency(item.closing_amount || 0)}</td>
					</tr>
				`;
			});

			// Add total row
			content += `
					<tr class="total-row">
						<td><strong>TỔNG CỘNG</strong></td>
						<td class="amount"><strong>${this.formatCurrency(this.totalOpeningAmount)}</strong></td>
						<td class="amount"><strong class="positive">${this.formatCurrency(this.totalTransactionAmount)}</strong></td>
						<td class="amount"><strong>${this.formatCurrency(this.totalClosingAmount)}</strong></td>
					</tr>
				</tbody>
			</table>
		</div>

		<div class="print-info">
			<p>Báo cáo được tạo tự động bởi hệ thống POS</p>
			<p>Chỉ in trang đầu tiên chứa thông tin tổng hợp</p>
		</div>
	</body>
</html>`;

			return content;
		},

		showError(message) {
			console.error("ListInvoicesDialog Error:", message);

			// ✅ ENHANCED ERROR HANDLING
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({
					message: message,
					indicator: 'red'
				});
			} else if (window.frappe && frappe.msgprint) {
				frappe.msgprint({
					title: __('Error'),
					message: message,
					indicator: 'red'
				});
			} else {
				alert(`Error: ${message}`);
			}
		},

		showSuccess(message) {
			console.log("ListInvoicesDialog Success:", message);

			// ✅ SUCCESS NOTIFICATION
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({
					message: message,
					indicator: 'green'
				});
			}
		},

		formatDateTime(dateTimeStr) {
			if (!dateTimeStr) return '';

			try {
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
				return dateTimeStr;
			}
		},

		// ✅ VERIFICATION METHODS
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

		async verifyShiftReport() {
			if (this.isVerifiedOrConfirmed) {
				return; // Already verified
			}

			this.verifying = true;
			try {
				console.log("Verifying shift report:", this.shiftReportId);

				const response = await frappe.call({
					method: "posawesome.posawesome.api.shift_verification.verify_shift_report",
					args: {
						shift_report_id: this.shiftReportId
					}
				});

				console.log("Verify response:", response);

				if (response.message && response.message.success) {
					// Success feedback
					this.showSuccess(__("Shift report verified successfully"));

					// Refresh data to get updated verification status
					await this.loadInvoices();

					// Emit event to disable Pay/Return buttons on main interface
					if (this.eventBus) {
						this.eventBus.emit("shift_report_verified", {
							shift_report_id: this.shiftReportId,
							verification_status: "Verified",
							disable_transaction_buttons: true
						});

						// Emit event to update UI components
						this.eventBus.emit("shift_verification_changed", "Verified");
					}

				} else {
					// Error handling
					const errorMessage = response.message?.message || __("Failed to verify shift report");
					this.showError(errorMessage);
				}
			} catch (error) {
				console.error("Verify error:", error);
				this.showError(__("Error verifying shift report"));
			} finally {
				this.verifying = false;
			}
		},

		close() {
			console.log("Closing ListInvoicesDialog");
			this.resetData();
			this.show = false;
		},

		resetFilters() {
			this.searchQuery = "";
			this.statusFilter = "";
			this.paymentFilter = "";
		},

		resetData() {
			console.log("Resetting ListInvoicesDialog data");
			this.invoices = [];
			this.totalInvoices = 0;
			this.summary = {
				total_invoices: 0,
				total_sales: 0,
				total_returns: 0
			};
			this.resetFilters();
		}
	}
};
</script>

<style scoped>
/* Main Dialog Styles */
.v-dialog {
	max-height: 90vh;
}

/* Responsive Dialog for 13-inch screens */
@media (max-width: 1366px) {
	.v-dialog {
		max-width: 95vw;
		max-height: 85vh;
	}
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

/* Payment Summary Table Styles */
.payment-summary-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-primary));
	color: rgb(var(--v-theme-on-primary));
	font-weight: 600;
	font-size: 0.8rem;
	padding: 8px 12px;
}

.payment-summary-table :deep(.v-data-table__td) {
	padding: 8px 12px;
	font-size: 0.85rem;
}

/* Total Row Styles */
.total-row {
	background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-variant)) 100%);
	color: rgb(var(--v-theme-on-primary));
	font-weight: 600;
	border-radius: 8px;
	margin: 8px 0;
	padding: 12px 16px;
}

/* Responsive Design for 13-inch screens */
@media (max-width: 1366px) {
	/* Compact filters */
	.v-row.dense .v-col {
		padding: 4px 8px;
	}

	/* Smaller table cells */
	.v-data-table :deep(.v-data-table__td),
	.v-data-table :deep(.v-data-table__th) {
		padding: 6px 8px;
		font-size: 0.8rem;
	}

	/* Compact summary cards */
	.v-card.pa-3 {
		padding: 12px !important;
	}

	/* Smaller dialog content */
	.v-card-text .pa-4 {
		padding: 16px !important;
	}

	/* Compact payment summary */
	.payment-summary-table :deep(.v-data-table__td),
	.payment-summary-table :deep(.v-data-table__th) {
		padding: 6px 8px;
		font-size: 0.75rem;
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

	/* Hide some columns on mobile */
	.v-data-table :deep(.v-data-table__th:nth-child(6)),
	.v-data-table :deep(.v-data-table__td:nth-child(6)) {
		display: none;
	}

	/* Compact summary cards grid */
	.v-row.pa-4.dense .v-col {
		min-width: 120px;
		flex: 1;
	}
}

/* Scrollable content for small screens */
.dialog-content {
	max-height: calc(90vh - 120px);
	overflow-y: auto;
}

/* Action Buttons Section */
.action-buttons-section {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-bottom: 1px solid #dee2e6;
	position: sticky;
	top: 0;
	z-index: 10;
}

/* Enhanced currency display */
.currency-amount {
	font-family: 'Roboto Mono', monospace;
	font-weight: 500;
	letter-spacing: 0.5px;
}

/* Loading states */
.loading-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(255, 255, 255, 0.8);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 10;
}

/* Gap utilities */
.gap-8 {
	gap: 8px;
}

/* Verification Status Chip */
.verification-status-chip {
	font-weight: 600;
	font-size: 0.8rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	transition: all 0.3s ease;
}

.verification-status-chip:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

/* Dark theme adjustments */
:deep(.dark-theme) .total-row,
:deep(.v-theme--dark) .total-row {
	background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-variant)) 100%);
}

:deep(.dark-theme) .v-data-table :deep(.v-data-table__th),
:deep(.v-theme--dark) .v-data-table :deep(.v-data-table__th) {
	background-color: rgb(var(--v-theme-surface-variant));
	color: rgb(var(--v-theme-on-surface-variant));
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
	min-width: 55px;
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

/* Action Buttons Styling */
.action-buttons-group {
	gap: 5px;
}

.action-btn {
	min-height: 44px !important;
	padding: 0 16px !important;
	font-size: 0.9rem !important;
	font-weight: 500 !important;
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
</style>