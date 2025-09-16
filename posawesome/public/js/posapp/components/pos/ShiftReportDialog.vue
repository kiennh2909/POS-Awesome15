<template>
	<v-dialog v-model="show" max-width="1000px" persistent>
		<v-card>
			<v-card-title class="d-flex align-center">
				<v-icon class="me-2">mdi-chart-line</v-icon>
				{{ __("Shift Report") }}: {{ shiftReportData.shift_report_id || 'N/A' }}
				<v-spacer></v-spacer>
				<v-chip
					v-if="shiftReportData.verification_status"
					:color="getStatusColor(shiftReportData.verification_status)"
					variant="flat"
					size="small"
					class="me-2"
				>
					{{ shiftReportData.verification_status }}
				</v-chip>
				<v-btn icon variant="text" @click="close">
					<v-icon>mdi-close</v-icon>
				</v-btn>
			</v-card-title>

			<v-divider></v-divider>

			<v-card-text class="pa-0">
				<!-- Shift Information -->
				<v-row class="pa-4" dense>
					<v-col cols="12" md="6">
						<v-card variant="outlined" class="pa-3">
							<h6 class="text-subtitle-1 mb-2">{{ __("Opening Information") }}</h6>
							<div class="text-body-2 mb-1">
								<strong>{{ __("Date") }}:</strong> {{ formatDate(shiftReportData.opening_date) }}
							</div>
							<div class="text-body-2 mb-1">
								<strong>{{ __("Time") }}:</strong> {{ shiftReportData.opening_time }}
							</div>
							<div class="text-body-2 mb-1">
								<strong>{{ __("Opened By") }}:</strong> {{ shiftReportData.opened_by }}
							</div>
							<div class="text-body-2">
								<strong>{{ __("Opening Amount") }}:</strong>
								<span class="text-success font-weight-bold">
									{{ formatCurrency(shiftReportData.total_opening_amount || 0) }}
								</span>
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="6">
						<v-card variant="outlined" class="pa-3">
							<h6 class="text-subtitle-1 mb-2">{{ __("Current Status") }}</h6>
							<div class="text-body-2 mb-1">
								<strong>{{ __("Status") }}:</strong>
								<v-chip
									:color="shiftReportData.status === 'Open' ? 'success' : 'primary'"
									variant="outlined"
									size="small"
									class="ml-1"
								>
									{{ shiftReportData.status }}
								</v-chip>
							</div>
							<div class="text-body-2 mb-1">
								<strong>{{ __("Invoice Count") }}:</strong> {{ shiftReportData.invoice_count || 0 }}
							</div>
							<div class="text-body-2 mb-1">
								<strong>{{ __("Total Sales") }}:</strong>
								<span class="text-success">{{ formatCurrency(shiftReportData.total_sales || 0) }}</span>
							</div>
							<div class="text-body-2">
								<strong>{{ __("Total Returns") }}:</strong>
								<span class="text-error">{{ formatCurrency(shiftReportData.total_returns || 0) }}</span>
							</div>
						</v-card>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Financial Summary -->
				<v-row class="pa-4" dense>
					<v-col cols="12" md="4">
						<v-card variant="outlined" class="pa-3 text-center">
							<v-icon color="success" size="32" class="mb-2">mdi-cash-plus</v-icon>
							<div class="text-caption text-medium-emphasis">{{ __("Expected Closing") }}</div>
							<div class="text-h6 font-weight-bold text-success">
								{{ formatCurrency(shiftReportData.total_expected_closing || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="4">
						<v-card variant="outlined" class="pa-3 text-center">
							<v-icon color="primary" size="32" class="mb-2">mdi-cash-minus</v-icon>
							<div class="text-caption text-medium-emphasis">{{ __("Actual Closing") }}</div>
							<div class="text-h6 font-weight-bold text-primary">
								{{ formatCurrency(shiftReportData.total_actual_closing || 0) }}
							</div>
						</v-card>
					</v-col>
					<v-col cols="12" md="4">
						<v-card variant="outlined" class="pa-3 text-center">
							<v-icon
								:color="getDifferenceColor(shiftReportData.difference)"
								size="32"
								class="mb-2"
							>
								mdi-cash
							</v-icon>
							<div class="text-caption text-medium-emphasis">{{ __("Difference") }}</div>
							<div
								class="text-h6 font-weight-bold"
								:class="getDifferenceColor(shiftReportData.difference)"
							>
								{{ formatCurrency(shiftReportData.difference || 0) }}
							</div>
						</v-card>
					</v-col>
				</v-row>

				<v-divider></v-divider>

				<!-- Payment Breakdown -->
				<div class="pa-4">
					<h6 class="text-subtitle-1 mb-3">{{ __("Payment Breakdown") }}</h6>
					<v-row dense>
						<v-col
							v-for="(amount, method) in shiftReportData.payment_breakdown"
							:key="method"
							cols="12"
							sm="6"
							md="3"
						>
							<v-card variant="outlined" class="pa-3">
								<div class="d-flex align-center">
									<v-icon :color="getPaymentIconColor(method)" class="me-2">mdi-credit-card</v-icon>
									<div>
										<div class="text-caption text-medium-emphasis">{{ method }}</div>
										<div class="text-body-1 font-weight-bold">
											{{ formatCurrency(amount || 0) }}
										</div>
									</div>
								</div>
							</v-card>
						</v-col>
					</v-row>
				</div>

				<v-divider></v-divider>

				<!-- Recent Invoices -->
				<div class="pa-4">
					<div class="d-flex align-center justify-space-between mb-3">
						<h6 class="text-subtitle-1">{{ __("Recent Invoices") }}</h6>
						<v-btn
							color="primary"
							variant="outlined"
							size="small"
							prepend-icon="mdi-receipt-text-multiple"
							@click="showInvoicesList"
						>
							{{ __("View All") }}
						</v-btn>
					</div>

					<v-data-table
						:headers="invoiceHeaders"
						:items="recentInvoices"
						:loading="loadingInvoices"
						density="compact"
						:items-per-page="itemsPerPage"
						:items-per-page-options="itemsPerPageOptions"
						:page="currentPage"
						@update:page="handlePageChange"
						@update:items-per-page="handleItemsPerPageChange"
						hide-default-footer
						class="elevation-0"
						:key="`table-${currentPage}-${itemsPerPage}`"
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

						<template #item.total_amount="{ item }">
							<span :class="item.is_return ? 'text-error' : 'text-success'">
								{{ formatCurrency(item.total_amount || 0) }}
							</span>
						</template>

						<template #item.actions="{ item }">
							<v-btn
								icon="mdi-eye"
								size="small"
								variant="text"
								@click="viewInvoice(item)"
							></v-btn>
						</template>

						<!-- Custom footer with pagination -->
						<template #bottom>
							<div class="d-flex align-center justify-space-between pa-3">
								<div class="text-caption text-medium-emphasis">
									{{ __("Showing {0} to {1} of {2} invoices", [
										(currentPage - 1) * itemsPerPage + 1,
										Math.min(currentPage * itemsPerPage, totalItems),
										totalItems
									]) }}
								</div>
								<div class="d-flex align-center" v-if="totalPages > 1">
									<v-select
										v-model="itemsPerPage"
										:items="itemsPerPageOptions"
										density="compact"
										variant="outlined"
										hide-details
										style="width: 80px;"
										class="me-2"
										@change="handleItemsPerPageChange"
									/>
									<v-pagination
										v-model="currentPage"
										:length="totalPages"
										:total-visible="5"
										size="small"
										:input-value="currentPage"
										@input="handlePageChange"
									/>
								</div>
								<div v-else class="text-caption text-medium-emphasis">
									{{ totalItems }} {{ totalItems === 1 ? __("invoice") : __("invoices") }}
								</div>
							</div>
						</template>
					</v-data-table>
				</div>

				<!-- Notes Section -->
				<v-divider></v-divider>
				<div class="pa-4">
					<h6 class="text-subtitle-1 mb-2">{{ __("Notes") }}</h6>
					<v-textarea
						v-model="shiftReportData.notes"
						:placeholder="__('Add notes...')"
						variant="outlined"
						density="compact"
						rows="3"
						readonly
					></v-textarea>
				</div>

				<!-- Debug Panel (Hidden by default, enable with v-if="true") -->
				<v-divider v-if="false"></v-divider>
				<div class="pa-4" v-if="true">
					<div class="d-flex align-center justify-space-between mb-3">
						<h6 class="text-subtitle-1 text-warning">{{ __("Debug Panel") }}</h6>
						<div class="d-flex gap-2">
							<v-chip size="small" variant="outlined" color="info">
								Session: {{ sessionId?.substring(0, 12) }}
							</v-chip>
							<v-chip size="small" variant="outlined" color="primary">
								Logs: {{ paginationLogs.length }}
							</v-chip>
						</div>
					</div>

					<!-- Pagination State -->
					<v-row dense class="mb-3">
						<v-col cols="12" md="3">
							<v-card variant="outlined" class="pa-2">
								<div class="text-caption text-medium-emphasis">{{ __("Current Page") }}</div>
								<div class="text-h6">{{ currentPage }}</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="3">
							<v-card variant="outlined" class="pa-2">
								<div class="text-caption text-medium-emphasis">{{ __("Items/Page") }}</div>
								<div class="text-h6">{{ itemsPerPage }}</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="3">
							<v-card variant="outlined" class="pa-2">
								<div class="text-caption text-medium-emphasis">{{ __("Total Items") }}</div>
								<div class="text-h6">{{ totalItems }}</div>
							</v-card>
						</v-col>
						<v-col cols="12" md="3">
							<v-card variant="outlined" class="pa-2">
								<div class="text-caption text-medium-emphasis">{{ __("Total Pages") }}</div>
								<div class="text-h6">{{ totalPages }}</div>
							</v-card>
						</v-col>
					</v-row>

					<!-- Recent Logs -->
					<div class="mb-3">
						<h6 class="text-subtitle-2 mb-2">{{ __("Recent Logs") }}</h6>
						<v-card variant="outlined" class="pa-2" style="max-height: 200px; overflow-y: auto;">
							<div
								v-for="(log, index) in paginationLogs.slice(-10)"
								:key="index"
								class="text-caption mb-1"
								:class="getLogColor(log.action)"
							>
								<strong>{{ log.action }}</strong>
								<span class="text-medium-emphasis">
									{{ new Date(log.timestamp).toLocaleTimeString() }}
								</span>
								<span v-if="log.requestId" class="text-info">
									[{{ log.requestId?.substring(0, 8) }}]
								</span>
								<div class="text-caption text-medium-emphasis ml-2">
									{{ JSON.stringify(log.data, null, 0) }}
								</div>
							</div>
							<div v-if="paginationLogs.length === 0" class="text-caption text-medium-emphasis">
								{{ __("No logs yet") }}
							</div>
						</v-card>
					</div>

					<!-- Debug Actions -->
					<div class="d-flex gap-2">
						<v-btn
							size="small"
							color="primary"
							variant="outlined"
							@click="testAPI"
						>
							{{ __("Test API") }}
						</v-btn>
						<v-btn
							size="small"
							color="success"
							variant="outlined"
							@click="exportTrackingLogs"
						>
							{{ __("Export Logs") }}
						</v-btn>
						<v-btn
							size="small"
							color="warning"
							variant="outlined"
							@click="clearTrackingLogs"
						>
							{{ __("Clear Logs") }}
						</v-btn>
					</div>
				</div>
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
					prepend-icon="mdi-printer"
					@click="printReport"
				>
					{{ __("Print Report") }}
				</v-btn>
				<v-btn
					v-if="false"
					color="info"
					variant="outlined"
					prepend-icon="mdi-bug"
					@click="testAPI"
				>
					{{ __("Test API") }}
				</v-btn>
				<v-btn
					v-if="false"
					color="warning"
					variant="outlined"
					prepend-icon="mdi-file-export"
					@click="exportTrackingLogs"
				>
					{{ __("Export Logs") }}
				</v-btn>
				<v-btn
					v-if="false"
					color="error"
					variant="outlined"
					prepend-icon="mdi-delete"
					@click="clearTrackingLogs"
				>
					{{ __("Clear Logs") }}
				</v-btn>
				<v-btn
					v-if="canVerify"
					color="success"
					variant="flat"
					prepend-icon="mdi-check-circle"
					@click="verifyReport"
					:loading="verifying"
				>
					{{ __("Verify") }}
				</v-btn>
				<v-btn
					v-if="canConfirm"
					color="primary"
					variant="flat"
					prepend-icon="mdi-check-all"
					@click="confirmReport"
					:loading="confirming"
				>
					{{ __("Confirm") }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: "ShiftReportDialog",
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
	emits: ["update:modelValue", "show-invoices-list"],
	data() {
		return {
			loadingInvoices: false,
			verifying: false,
			confirming: false,
			shiftReportData: {},
			recentInvoices: [],
			// Pagination properties
			currentPage: 1,
			itemsPerPage: 5,
			totalItems: 0,
			totalPages: 0,
			itemsPerPageOptions: [5, 10, 15, 25],
			// Tracking logs for debugging
			paginationLogs: [],
			sessionId: null,
			invoiceHeaders: [
				{ title: this.__("Invoice No"), key: "invoice_no", width: "120px" },
				{ title: this.__("Date"), key: "invoice_date", width: "100px" },
				{ title: this.__("Customer"), key: "customer", width: "150px" },
				{ title: this.__("Amount"), key: "total_amount", width: "120px", align: "end" },
				{ title: this.__("Actions"), key: "actions", width: "80px", sortable: false }
			]
		};
	},
	created() {
		// Initialize session for tracking
		this.sessionId = this.generateSessionId();
		this.addTrackingLog({
			timestamp: new Date().toISOString(),
			action: 'COMPONENT_CREATED',
			sessionId: this.sessionId,
			data: {
				shiftReportId: this.shiftReportId,
				userAgent: navigator.userAgent,
				url: window.location.href
			}
		});
	},
	beforeDestroy() {
		// Log component destruction
		this.addTrackingLog({
			timestamp: new Date().toISOString(),
			action: 'COMPONENT_DESTROYED',
			sessionId: this.sessionId,
			data: {
				totalLogs: this.paginationLogs.length,
				finalState: {
					currentPage: this.currentPage,
					itemsPerPage: this.itemsPerPage,
					totalItems: this.totalItems
				}
			}
		});
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
		canVerify() {
			return this.shiftReportData.verification_status === "Pending" &&
				   this.shiftReportData.status === "Open";
		},
		canConfirm() {
			return this.shiftReportData.verification_status === "Verified" &&
				   this.shiftReportData.status === "Open";
		}
	},
	watch: {
		modelValue(newVal) {
			if (newVal && this.shiftReportId) {
				this.loadShiftReport();
			}
		}
	},
	methods: {
		async loadShiftReport() {
			if (!this.shiftReportId) return;

			try {
				// Mock data for now - will be replaced with real API call
				this.shiftReportData = {
					shift_report_id: "SHIFT-001",
					pos_opening_shift: "POS-OPEN-001",
					opening_date: "2025-01-09",
					opening_time: "09:00:00",
					opened_by: "admin",
					total_opening_amount: 1000.00,
					total_expected_closing: 1500.00,
					total_actual_closing: 1450.00,
					difference: -50.00,
					verification_status: "Pending",
					status: "Open",
					invoice_count: 15,
					total_sales: 1450.00,
					total_returns: 0.00,
					payment_breakdown: {
						"Cash": 1200.00,
						"Card": 250.00
					},
					notes: "Shift report for morning session"
				};

				await this.loadRecentInvoices();

			} catch (error) {
				console.error("Error loading shift report:", error);
				this.showError("Failed to load shift report");
			}
		},

		async loadRecentInvoices() {
			const requestId = this.generateRequestId();
			const startTime = performance.now();

			this.addTrackingLog({
				timestamp: new Date().toISOString(),
				action: 'API_REQUEST_START',
				sessionId: this.sessionId,
				requestId,
				data: {
					shiftReportId: this.shiftReportId,
					page: this.currentPage,
					pageSize: this.itemsPerPage,
					totalItems: this.totalItems,
					totalPages: this.totalPages
				}
			});

			this.loadingInvoices = true;

			try {
				console.log("🔄 [PAGINATION_TRACKING] Loading invoices:", {
					requestId,
					page: this.currentPage,
					pageSize: this.itemsPerPage,
					shiftReportId: this.shiftReportId
				});

				// Call real API to get paginated invoices
				const apiStartTime = performance.now();
				const response = await frappe.call({
					method: "posawesome.posawesome.api.shifts.get_shift_report_invoices",
					args: {
						shift_report_id: this.shiftReportId,
						page: this.currentPage,
						page_size: this.itemsPerPage
					}
				});
				const apiEndTime = performance.now();

				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'API_RESPONSE_RECEIVED',
					sessionId: this.sessionId,
					requestId,
					data: {
						responseTime: apiEndTime - apiStartTime,
						hasMessage: !!response.message,
						success: response.message?.success,
						invoiceCount: response.message?.invoices?.length,
						totalCount: response.message?.total_count
					}
				});

				console.log("📡 [PAGINATION_TRACKING] API Response:", {
					requestId,
					responseTime: `${(apiEndTime - apiStartTime).toFixed(2)}ms`,
					success: response.message?.success,
					invoiceCount: response.message?.invoices?.length,
					totalCount: response.message?.total_count
				});

				if (response.message && response.message.success) {
					console.log("✅ [PAGINATION_TRACKING] API Success:", {
						requestId,
						invoices: response.message.invoices?.length,
						total: response.message.total_count,
						pages: response.message.total_pages
					});

					// Use Vue.set for reactive updates
					this.$set(this, 'recentInvoices', response.message.invoices || []);
					this.$set(this, 'totalItems', response.message.total_count || 0);
					this.$set(this, 'totalPages', response.message.total_pages || 0);

					this.addTrackingLog({
						timestamp: new Date().toISOString(),
						action: 'DATA_UPDATE_SUCCESS',
						sessionId: this.sessionId,
						requestId,
						data: {
							invoiceCount: response.message.invoices?.length,
							totalItems: response.message.total_count,
							totalPages: response.message.total_pages
						}
					});

					// Force update to ensure UI re-renders
					this.$nextTick(() => {
						this.$forceUpdate();
						const endTime = performance.now();
						this.addTrackingLog({
							timestamp: new Date().toISOString(),
							action: 'UI_UPDATE_COMPLETE',
							sessionId: this.sessionId,
							requestId,
							data: {
								totalTime: endTime - startTime,
								invoiceCount: this.recentInvoices.length
							}
						});
					});
				} else {
					console.warn("❌ [PAGINATION_TRACKING] API call failed:", {
						requestId,
						error: response.message
					});

					this.addTrackingLog({
						timestamp: new Date().toISOString(),
						action: 'API_ERROR',
						sessionId: this.sessionId,
						requestId,
						data: {
							error: response.message,
							fallback: 'mock_data'
						}
					});

					this.useMockData();
				}
			} catch (error) {
				const endTime = performance.now();
				console.error("💥 [PAGINATION_TRACKING] Error loading invoices:", {
					requestId,
					error: error.message,
					totalTime: endTime - startTime
				});

				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'API_EXCEPTION',
					sessionId: this.sessionId,
					requestId,
					data: {
						error: error.message,
						stack: error.stack,
						totalTime: endTime - startTime,
						fallback: 'mock_data'
					}
				});

				this.showError("Failed to load invoices");
				this.useMockData();
			} finally {
				this.loadingInvoices = false;
				const endTime = performance.now();
				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'REQUEST_COMPLETE',
					sessionId: this.sessionId,
					requestId,
					data: {
						totalTime: endTime - startTime,
						finalInvoiceCount: this.recentInvoices.length
					}
				});
			}
		},

		// Generate mock data for testing pagination
		useMockData() {
			console.log("🎭 Using mock data for pagination testing");

			// Generate more mock data to test pagination
			const mockInvoices = [];
			const totalMockItems = 47; // Enough for multiple pages

			for (let i = 1; i <= totalMockItems; i++) {
				const isReturn = Math.random() < 0.2; // 20% return invoices
				mockInvoices.push({
					invoice_no: isReturn ? `RTN-${String(i).padStart(3, '0')}` : `INV-${String(i).padStart(3, '0')}`,
					invoice_date: "2025-01-09",
					customer: `Customer ${i}`,
					total_amount: isReturn ? -(Math.random() * 200 + 10) : (Math.random() * 300 + 20),
					is_return: isReturn
				});
			}

			// Apply pagination to mock data with proper validation
			const startIndex = Math.max(0, (this.currentPage - 1) * this.itemsPerPage);
			const endIndex = Math.min(startIndex + this.itemsPerPage, totalMockItems);

			// Use Vue.set for reactive updates
			this.$set(this, 'recentInvoices', mockInvoices.slice(startIndex, endIndex));
			this.$set(this, 'totalItems', totalMockItems);
			this.$set(this, 'totalPages', Math.ceil(totalMockItems / this.itemsPerPage));

			console.log(`📄 Mock pagination: Page ${this.currentPage}/${this.totalPages}, Items ${startIndex + 1}-${endIndex} of ${totalMockItems}`);

			// Force update to ensure UI re-renders
			this.$nextTick(() => {
				this.$forceUpdate();
			});
		},

		getStatusColor(status) {
			const colors = {
				"Pending": "warning",
				"Verified": "info",
				"Confirmed": "success"
			};
			return colors[status] || "grey";
		},

		getDifferenceColor(difference) {
			if (!difference) return "text-primary";
			return difference >= 0 ? "text-success" : "text-error";
		},

		getPaymentIconColor(method) {
			const colors = {
				"Cash": "success",
				"Card": "primary",
				"M-Pesa": "info"
			};
			return colors[method] || "grey";
		},

		getLogColor(action) {
			const colors = {
				'COMPONENT_CREATED': 'text-success',
				'COMPONENT_DESTROYED': 'text-error',
				'API_REQUEST_START': 'text-info',
				'API_RESPONSE_RECEIVED': 'text-success',
				'API_ERROR': 'text-error',
				'API_EXCEPTION': 'text-error',
				'DATA_UPDATE_SUCCESS': 'text-success',
				'UI_UPDATE_COMPLETE': 'text-primary',
				'PAGE_CHANGE': 'text-primary',
				'PAGE_CHANGE_VALID': 'text-success',
				'PAGE_CHANGE_INVALID': 'text-warning',
				'ITEMS_PER_PAGE_CHANGE': 'text-primary',
				'ITEMS_PER_PAGE_VALID': 'text-success',
				'ITEMS_PER_PAGE_INVALID': 'text-warning',
				'REQUEST_COMPLETE': 'text-info'
			};
			return colors[action] || 'text-medium-emphasis';
		},

		formatDate(date) {
			if (!date) return "-";
			return new Date(date).toLocaleDateString();
		},

		formatCurrency(amount) {
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: 'USD'
			}).format(amount);
		},

		showInvoicesList() {
			this.$emit("show-invoices-list", this.shiftReportId);
		},

		viewInvoice(invoice) {
			const url = `/app/sales-invoice/${invoice.invoice_no}`;
			window.open(url, '_blank');
		},

		async verifyReport() {
			this.verifying = true;
			try {
				// Mock verification - will be replaced with real API call
				await new Promise(resolve => setTimeout(resolve, 1000));

				this.shiftReportData.verification_status = "Verified";
				this.shiftReportData.verification_date = new Date().toISOString().split('T')[0];

				this.showSuccess("Shift report verified successfully");

			} catch (error) {
				console.error("Error verifying report:", error);
				this.showError("Failed to verify shift report");
			} finally {
				this.verifying = false;
			}
		},

		async confirmReport() {
			this.confirming = true;
			try {
				// Mock confirmation - will be replaced with real API call
				await new Promise(resolve => setTimeout(resolve, 1000));

				this.shiftReportData.verification_status = "Confirmed";
				this.shiftReportData.confirmation_date = new Date().toISOString().split('T')[0];

				this.showSuccess("Shift report confirmed successfully");

			} catch (error) {
				console.error("Error confirming report:", error);
				this.showError("Failed to confirm shift report");
			} finally {
				this.confirming = false;
			}
		},

		printReport() {
			// Print shift report
			const url = `/app/print/POS%20Shift%20Report/${this.shiftReportId}`;
			window.open(url, '_blank');
		},

		showSuccess(message) {
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({ message, indicator: 'green' });
			} else {
				alert(message);
			}
		},

		showError(message) {
			if (window.frappe && frappe.show_alert) {
				frappe.show_alert({ message, indicator: 'red' });
			} else {
				alert(message);
			}
		},

		close() {
			this.show = false;
		},

		// Handle page change in pagination
		handlePageChange(newPage) {
			const timestamp = new Date().toISOString();
			const logEntry = {
				timestamp,
				action: 'PAGE_CHANGE',
				sessionId: this.sessionId,
				data: {
					requestedPage: newPage,
					currentPage: this.currentPage,
					totalPages: this.totalPages,
					itemsPerPage: this.itemsPerPage
				}
			};

			console.log("📄 [PAGINATION_TRACKING]", logEntry);
			this.addTrackingLog(logEntry);

			const pageNum = parseInt(newPage);
			if (pageNum && pageNum !== this.currentPage && pageNum >= 1 && pageNum <= this.totalPages) {
				this.currentPage = pageNum;
				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'PAGE_CHANGE_VALID',
					sessionId: this.sessionId,
					data: { newPage: pageNum }
				});
				this.loadRecentInvoices();
			} else {
				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'PAGE_CHANGE_INVALID',
					sessionId: this.sessionId,
					data: { reason: 'Invalid page number or out of range' }
				});
			}
		},

		// Handle items per page change
		handleItemsPerPageChange(newItemsPerPage) {
			const timestamp = new Date().toISOString();
			const logEntry = {
				timestamp,
				action: 'ITEMS_PER_PAGE_CHANGE',
				sessionId: this.sessionId,
				data: {
					requestedSize: newItemsPerPage,
					currentSize: this.itemsPerPage,
					availableOptions: this.itemsPerPageOptions
				}
			};

			console.log("🔢 [PAGINATION_TRACKING]", logEntry);
			this.addTrackingLog(logEntry);

			const sizeNum = parseInt(newItemsPerPage);
			if (sizeNum && sizeNum !== this.itemsPerPage && this.itemsPerPageOptions.includes(sizeNum)) {
				this.itemsPerPage = sizeNum;
				this.currentPage = 1; // Reset to first page when changing items per page
				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'ITEMS_PER_PAGE_VALID',
					sessionId: this.sessionId,
					data: { newSize: sizeNum, resetPage: true }
				});
				this.loadRecentInvoices();
			} else {
				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'ITEMS_PER_PAGE_INVALID',
					sessionId: this.sessionId,
					data: { reason: 'Invalid size or not in allowed options' }
				});
			}
		},

		// Tracking and logging utilities
		addTrackingLog(logEntry) {
			// Add to internal logs array
			this.paginationLogs.push(logEntry);

			// Keep only last 100 logs to prevent memory issues
			if (this.paginationLogs.length > 100) {
				this.paginationLogs = this.paginationLogs.slice(-100);
			}

			// Also log to browser console with structured format
			console.log(`🔍 [${logEntry.action}]`, {
				timestamp: logEntry.timestamp,
				sessionId: logEntry.sessionId,
				requestId: logEntry.requestId,
				data: logEntry.data
			});
		},

		generateRequestId() {
			return `REQ_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
		},

		generateSessionId() {
			return `SESSION_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
		},

		// Get tracking logs for debugging
		getTrackingLogs() {
			return this.paginationLogs;
		},

		// Clear tracking logs
		clearTrackingLogs() {
			this.paginationLogs = [];
			console.log("🧹 Tracking logs cleared");
		},

		// Export tracking logs for analysis
		exportTrackingLogs() {
			const dataStr = JSON.stringify(this.paginationLogs, null, 2);
			const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

			const exportFileDefaultName = `pagination_tracking_${this.sessionId}_${new Date().toISOString().split('T')[0]}.json`;

			const linkElement = document.createElement('a');
			linkElement.setAttribute('href', dataUri);
			linkElement.setAttribute('download', exportFileDefaultName);
			linkElement.click();
		},

		// Debug method to test API
		async testAPI() {
			const testRequestId = this.generateRequestId();

			this.addTrackingLog({
				timestamp: new Date().toISOString(),
				action: 'API_TEST_START',
				sessionId: this.sessionId,
				requestId: testRequestId,
				data: { endpoint: 'get_shift_report_invoices' }
			});

			try {
				console.log("🧪 Testing API endpoint...");
				const response = await frappe.call({
					method: "posawesome.posawesome.api.shifts.get_shift_report_invoices",
					args: {
						shift_report_id: "SHIFT-001",
						page: 1,
						page_size: 5
					}
				});

				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'API_TEST_SUCCESS',
					sessionId: this.sessionId,
					requestId: testRequestId,
					data: {
						success: response.message?.success,
						invoiceCount: response.message?.invoices?.length,
						totalCount: response.message?.total_count
					}
				});

				console.log("🧪 API Test Result:", response);
			} catch (error) {
				this.addTrackingLog({
					timestamp: new Date().toISOString(),
					action: 'API_TEST_ERROR',
					sessionId: this.sessionId,
					requestId: testRequestId,
					data: { error: error.message }
				});

				console.error("🧪 API Test Failed:", error);
			}
		}
	}
};
</script>

<style scoped>
.v-card {
	border-radius: 12px;
}

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