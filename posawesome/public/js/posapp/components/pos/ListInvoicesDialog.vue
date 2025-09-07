<template>
	<v-row justify="center">
		<v-dialog v-model="listInvoicesDialog" max-width="1400px" persistent>
			<v-card class="list-invoices-dialog-card">
				<!-- Enhanced Header -->
				<v-card-title class="list-invoices-header pa-6">
					<div class="header-content">
						<div class="header-icon-wrapper">
							<v-icon class="header-icon" size="28">mdi-file-chart</v-icon>
						</div>
						<div class="header-text">
							<h3 class="header-title">{{ __("List Invoices - Shift Summary") }}</h3>
							<p class="header-subtitle">{{ __("View all invoices from opening to closing shift") }}</p>
							<div class="header-stats">
								<v-chip
									color="primary"
									variant="tonal"
									size="small"
									class="status-chip"
								>
									<v-icon start size="14">mdi-receipt</v-icon>
									{{ shiftStatistics.total_invoices }} {{ __("Invoices") }}
								</v-chip>
								<v-chip
									color="success"
									variant="tonal"
									size="small"
									class="status-chip"
								>
									<v-icon start size="14">mdi-cash</v-icon>
									{{ formatCurrency(shiftStatistics.total_revenue) }}
								</v-chip>
							</div>
						</div>
					</div>
					<v-btn
						icon="mdi-close"
						variant="text"
						size="default"
						@click="close_dialog"
						class="close-btn"
					></v-btn>
				</v-card-title>

				<v-divider class="header-divider"></v-divider>

				<!-- Shift Summary Header -->
				<v-card-text class="shift-summary-header pa-4">
					<v-row dense>
						<v-col cols="12" md="6">
							<div class="summary-item">
								<v-icon color="primary" class="mr-2">mdi-calendar</v-icon>
								<span class="summary-label">{{ __("Date:") }}</span>
								<span class="summary-value">{{ shiftStatistics.date }}</span>
							</div>
							<div class="summary-item">
								<v-icon color="primary" class="mr-2">mdi-clock</v-icon>
								<span class="summary-label">{{ __("Time:") }}</span>
								<span class="summary-value">{{ shiftStatistics.time }}</span>
							</div>
							<div class="summary-item">
								<v-icon color="success" class="mr-2">mdi-account</v-icon>
								<span class="summary-label">{{ __("User:") }}</span>
								<span class="summary-value">{{ shiftStatistics.user }}</span>
							</div>
						</v-col>
						<v-col cols="12" md="6">
							<div class="summary-item">
								<v-icon color="success" class="mr-2">mdi-cash-plus</v-icon>
								<span class="summary-label">{{ __("Opening:") }}</span>
								<span class="summary-value">{{ formatCurrency(shiftStatistics.opening_amount) }}</span>
							</div>
							<div class="summary-item">
								<v-icon color="info" class="mr-2">mdi-chart-line</v-icon>
								<span class="summary-label">{{ __("Today:") }}</span>
								<span class="summary-value">{{ formatCurrency(shiftStatistics.today_revenue) }}</span>
							</div>
							<div class="summary-item">
								<v-icon color="warning" class="mr-2">mdi-sync</v-icon>
								<span class="summary-label">{{ __("Last Sync:") }}</span>
								<span class="summary-value">{{ shiftStatistics.last_sync }}</span>
							</div>
						</v-col>
					</v-row>
				</v-card-text>

				<v-divider></v-divider>

				<!-- Content -->
				<v-card-text class="pa-0 white-background">
					<div class="content-container">
						<!-- Advanced Filters -->
						<div class="filters-section pa-4">
							<h4 class="text-h6 mb-4">{{ __("🔍 Advanced Filters") }}</h4>
							<v-row dense>
								<v-col cols="12" md="2">
									<v-select
										v-model="filters.pos_profile"
										:items="posProfiles"
										label="POS Profile"
										variant="outlined"
										density="compact"
										clearable
										hide-details
									></v-select>
								</v-col>
								<v-col cols="12" md="2">
									<v-text-field
										v-model="filters.user_id"
										label="User ID"
										variant="outlined"
										density="compact"
										clearable
										hide-details
									></v-text-field>
								</v-col>
								<v-col cols="12" md="2">
									<v-text-field
										v-model="filters.customer_name"
										label="Customer Name"
										variant="outlined"
										density="compact"
										clearable
										hide-details
									></v-text-field>
								</v-col>
								<v-col cols="12" md="2">
									<v-text-field
										v-model="filters.customer_tax_id"
										label="Tax ID"
										variant="outlined"
										density="compact"
										clearable
										hide-details
									></v-text-field>
								</v-col>
								<v-col cols="12" md="2">
									<v-text-field
										v-model="filters.invoice_no"
										label="Invoice No"
										variant="outlined"
										density="compact"
										clearable
										hide-details
									></v-text-field>
								</v-col>
								<v-col cols="12" md="2">
									<v-select
										v-model="filters.payment_method"
										:items="paymentMethods"
										label="Payment Method"
										variant="outlined"
										density="compact"
										clearable
										hide-details
									></v-select>
								</v-col>
							</v-row>
							<v-row dense class="mt-2">
								<v-col cols="12" md="2">
									<v-text-field
										v-model="filters.amount_min"
										label="Min Amount"
										variant="outlined"
										density="compact"
										type="number"
										:prefix="currencySymbol('USD')"
										hide-details
									></v-text-field>
								</v-col>
								<v-col cols="12" md="2">
									<v-text-field
										v-model="filters.amount_max"
										label="Max Amount"
										variant="outlined"
										density="compact"
										type="number"
										:prefix="currencySymbol('USD')"
										hide-details
									></v-text-field>
								</v-col>
								<v-col cols="12" md="8">
									<v-btn
										color="primary"
										variant="outlined"
										@click="applyFilters"
										class="mr-2"
									>
										<v-icon start>mdi-magnify</v-icon>
										{{ __("Apply Filters") }}
									</v-btn>
									<v-btn
										color="grey"
										variant="outlined"
										@click="clearFilters"
										class="mr-2"
									>
										<v-icon start>mdi-refresh</v-icon>
										{{ __("Clear Filters") }}
									</v-btn>
									<v-btn
										color="success"
										variant="outlined"
										@click="exportData"
									>
										<v-icon start>mdi-download</v-icon>
										{{ __("Export") }}
									</v-btn>
								</v-col>
							</v-row>
						</div>

						<v-divider></v-divider>

						<!-- Invoices Table -->
						<div class="table-section">
							<div class="table-header pa-4">
								<h4 class="text-h6">{{ __("📋 Invoices Table") }}</h4>
								<p class="text-body-2 text-grey">{{ __("Showing all invoices from current shift") }}</p>
							</div>

							<v-data-table
								:headers="tableHeaders"
								:items="filteredInvoices"
								:items-per-page="15"
								:items-per-page-options="[10, 15, 25, 50]"
								class="invoices-table"
								fixed-header
								height="500"
							>
								<template v-slot:item.index="{ item }">
									<span class="font-weight-bold">{{ item.index }}</span>
								</template>

								<template v-slot:item.pos_profile="{ item }">
									<v-chip size="small" color="primary" variant="tonal">
										{{ item.pos_profile }}
									</v-chip>
								</template>

								<template v-slot:item.user_id="{ item }">
									<span class="text-body-2">{{ item.user_id }}</span>
								</template>

								<template v-slot:item.date="{ item }">
									<v-chip size="small" color="info" variant="tonal">
										{{ item.date }}
									</v-chip>
								</template>

								<template v-slot:item.time="{ item }">
									<div class="time-cell">
										<v-icon size="14" color="grey" class="mr-1">mdi-clock</v-icon>
										{{ item.time }}
									</div>
								</template>

								<template v-slot:item.customer_name="{ item }">
									<div class="customer-cell">
										<v-avatar size="24" color="primary" class="mr-2">
											<v-icon size="14" color="white">mdi-account</v-icon>
										</v-avatar>
										<div>
											<div class="font-weight-medium">{{ item.customer_name }}</div>
											<div class="text-caption text-grey" v-if="item.customer_tax_id">
												{{ item.customer_tax_id }}
											</div>
										</div>
									</div>
								</template>

								<template v-slot:item.invoice_no="{ item }">
									<span class="font-mono">{{ item.invoice_no }}</span>
								</template>

								<template v-slot:item.total_amount="{ item }">
									<span class="font-weight-bold text-success">
										{{ formatCurrency(item.total_amount) }}
									</span>
								</template>

								<template v-slot:item.paid_amount="{ item }">
									<span class="text-success">
										{{ formatCurrency(item.paid_amount) }}
									</span>
								</template>

								<template v-slot:item.outstanding="{ item }">
									<span :class="item.outstanding > 0 ? 'text-error font-weight-bold' : 'text-success'">
										{{ formatCurrency(item.outstanding) }}
									</span>
								</template>

								<template v-slot:item.payment_method="{ item }">
									<v-chip
										size="small"
										:color="getPaymentColor(item.payment_method)"
										variant="flat"
									>
										{{ getPaymentIcon(item.payment_method) }} {{ item.payment_method }}
									</v-chip>
								</template>

								<template v-slot:item.tax_invoice_no="{ item }">
									<span class="font-mono text-body-2">{{ item.tax_invoice_no }}</span>
								</template>

								<template v-slot:item.invoice_status="{ item }">
									<v-chip
										size="small"
										:color="getStatusColor(item.invoice_status)"
										variant="tonal"
									>
										{{ getStatusIcon(item.invoice_status) }} {{ item.invoice_status }}
									</v-chip>
								</template>
							</v-data-table>
						</div>

						<v-divider></v-divider>

						<!-- Shift Statistics -->
						<div class="statistics-section pa-4">
							<h4 class="text-h6 mb-4">{{ __("📊 Shift Statistics") }}</h4>

							<!-- Opening Section -->
							<div class="stats-group mb-4">
								<h5 class="text-subtitle-1 mb-3">{{ __("🏦 MỞ CA") }}</h5>
								<v-row dense>
									<v-col cols="3">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.opening.cash)"
											label="💰 Tiền mặt"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.opening.bank)"
											label="🏦 Bank"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.opening.total)"
											label="📊 Tổng mở ca"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.opening.user"
											label="👤 User mở ca"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
								</v-row>
								<v-row dense class="mt-2">
									<v-col cols="4">
										<v-text-field
											:model-value="shiftStatistics.opening.date"
											label="📅 Ngày mở ca"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="4">
										<v-text-field
											:model-value="shiftStatistics.opening.time"
											label="🕐 Giờ mở ca"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
								</v-row>
							</div>

							<!-- Transactions Section -->
							<div class="stats-group mb-4">
								<h5 class="text-subtitle-1 mb-3">{{ __("📈 PHÁT SINH TRONG CA") }}</h5>
								<v-row dense>
									<v-col cols="2">
										<v-text-field
											:model-value="shiftStatistics.transactions.total_invoices"
											label="Total Inv."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="2">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.transactions.total_revenue)"
											label="Total Rev."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="2">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.transactions.cash_revenue)"
											label="Cash Rev."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="2">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.transactions.card_revenue)"
											label="Card Rev."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="2">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.transactions.bank_revenue)"
											label="Bank Rev."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="2">
										<v-text-field
											:model-value="formatCurrency(shiftStatistics.transactions.outstanding)"
											label="Outstanding"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
								</v-row>
								<v-row dense class="mt-2">
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.transactions.tax_invoices"
											label="Tax Inv."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.transactions.exported"
											label="Exported"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.transactions.failed"
											label="Failed"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.transactions.pending"
											label="Pending"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
								</v-row>
							</div>

							<!-- Closing Section -->
							<div class="stats-group mb-4">
								<h5 class="text-subtitle-1 mb-3">{{ __("🔐 ĐÓNG CA") }}</h5>
								<div class="closing-cash mb-3">
									<h6 class="text-body-1 mb-2">{{ __("💰 TIỀN MẶT") }}</h6>
									<v-row dense>
										<v-col cols="4">
											<v-text-field
												:model-value="formatCurrency(shiftStatistics.closing.cash.opening)"
												label="Opening"
												readonly
												variant="outlined"
												density="compact"
												hide-details
											></v-text-field>
										</v-col>
										<v-col cols="4">
											<v-text-field
												:model-value="formatCurrency(shiftStatistics.closing.cash.current)"
												label="Current"
												readonly
												variant="outlined"
												density="compact"
												hide-details
											></v-text-field>
										</v-col>
										<v-col cols="4">
											<v-text-field
												:model-value="formatCurrency(shiftStatistics.closing.cash.expected)"
												label="Expected Closing"
												readonly
												variant="outlined"
												density="compact"
												hide-details
											></v-text-field>
										</v-col>
									</v-row>
									<div class="difference-display mt-2">
										<v-chip
											:color="shiftStatistics.closing.cash.difference >= 0 ? 'success' : 'error'"
											variant="tonal"
											size="small"
										>
											{{ __("Difference:") }} {{ formatCurrency(shiftStatistics.closing.cash.difference) }}
										</v-chip>
									</div>
								</div>

								<div class="closing-bank">
									<h6 class="text-body-1 mb-2">{{ __("🏦 BANK") }}</h6>
									<v-row dense>
										<v-col cols="4">
											<v-text-field
												:model-value="formatCurrency(shiftStatistics.closing.bank.opening)"
												label="Opening"
												readonly
												variant="outlined"
												density="compact"
												hide-details
											></v-text-field>
										</v-col>
										<v-col cols="4">
											<v-text-field
												:model-value="formatCurrency(shiftStatistics.closing.bank.current)"
												label="Current"
												readonly
												variant="outlined"
												density="compact"
												hide-details
											></v-text-field>
										</v-col>
										<v-col cols="4">
											<v-text-field
												:model-value="formatCurrency(shiftStatistics.closing.bank.expected)"
												label="Expected Closing"
												readonly
												variant="outlined"
												density="compact"
												hide-details
											></v-text-field>
										</v-col>
									</v-row>
									<div class="difference-display mt-2">
										<v-chip
											:color="shiftStatistics.closing.bank.difference >= 0 ? 'success' : 'error'"
											variant="tonal"
											size="small"
										>
											{{ __("Difference:") }} {{ formatCurrency(shiftStatistics.closing.bank.difference) }}
										</v-chip>
									</div>
								</div>
							</div>

							<!-- Invoice Range Section -->
							<div class="stats-group mb-4">
								<h5 class="text-subtitle-1 mb-3">{{ __("📄 SỐ HÓA ĐƠN") }}</h5>
								<v-row dense>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.invoice_range.first_invoice"
											label="First Invoice"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.invoice_range.last_invoice"
											label="Last Invoice"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.invoice_range.total_invoices"
											label="Total Invoices"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.invoice_range.time_range"
											label="Time Range"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
								</v-row>
							</div>

							<!-- Tax Invoice Range Section -->
							<div class="stats-group">
								<h5 class="text-subtitle-1 mb-3">{{ __("🧾 SỐ HÓA ĐƠN THUẾ") }}</h5>
								<v-row dense>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.tax_invoice_range.first_tax_invoice"
											label="First Tax Inv."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.tax_invoice_range.last_tax_invoice"
											label="Last Tax Inv."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.tax_invoice_range.total_tax_invoices"
											label="Total Tax Inv."
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="3">
										<v-text-field
											:model-value="shiftStatistics.tax_invoice_range.success_rate + '%'"
											label="Success Rate"
											readonly
											variant="outlined"
											density="compact"
											hide-details
										></v-text-field>
									</v-col>
								</v-row>
							</div>
						</div>
					</div>
				</v-card-text>

				<!-- Enhanced Footer -->
				<v-divider></v-divider>
				<v-card-actions class="dialog-actions-container">
					<div class="footer-info">
						<span class="footer-text">
							<v-icon start size="16" color="primary">mdi-information-outline</v-icon>
							{{ __("Click on any invoice to view details") }}
						</span>
					</div>
					<v-spacer></v-spacer>
					<v-btn
						color="primary"
						variant="outlined"
						@click="printAllInvoices"
						class="mr-2"
					>
						<v-icon start>mdi-printer</v-icon>
						{{ __("Print All") }}
					</v-btn>
					<v-btn
						color="info"
						variant="outlined"
						@click="emailReport"
						class="mr-2"
					>
						<v-icon start>mdi-email</v-icon>
						{{ __("Email Report") }}
					</v-btn>
					<v-btn
						color="success"
						variant="outlined"
						@click="exportData"
						class="mr-2"
					>
						<v-icon start>mdi-download</v-icon>
						{{ __("Export Data") }}
					</v-btn>
					<v-btn
						color="warning"
						variant="outlined"
						@click="closeShift"
						class="mr-2"
					>
						<v-icon start>mdi-lock</v-icon>
						{{ __("Đóng Ca") }}
					</v-btn>
					<v-btn
						color="error"
						variant="outlined"
						@click="close_dialog"
					>
						<v-icon start>mdi-close</v-icon>
						{{ __("Close") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";

export default {
	name: "ListInvoicesDialog",
	mixins: [format],
	data() {
		return {
			listInvoicesDialog: false,
			filters: {
				pos_profile: '',
				user_id: '',
				customer_name: '',
				customer_tax_id: '',
				invoice_no: '',
				amount_min: '',
				amount_max: '',
				payment_method: ''
			},
			posProfiles: ['Main POS', 'Secondary POS', 'Express POS'],
			paymentMethods: ['Cash', 'Card', 'Bank', 'M-Pesa'],
			tableHeaders: [
				{ title: '#', key: 'index', width: '60px', sortable: false },
				{ title: 'POS Profile', key: 'pos_profile', width: '100px' },
				{ title: 'User ID', key: 'user_id', width: '80px' },
				{ title: 'Date', key: 'date', width: '90px', sortable: true },
				{ title: 'Time', key: 'time', width: '70px', sortable: true },
				{ title: 'Customer', key: 'customer_name', width: '150px' },
				{ title: 'Tax ID', key: 'customer_tax_id', width: '100px' },
				{ title: 'Invoice No', key: 'invoice_no', width: '120px' },
				{ title: 'Total Amount', key: 'total_amount', width: '110px', align: 'right' },
				{ title: 'Paid Amount', key: 'paid_amount', width: '110px', align: 'right' },
				{ title: 'Outstanding', key: 'outstanding', width: '110px', align: 'right' },
				{ title: 'Pay Method', key: 'payment_method', width: '100px' },
				{ title: 'Tax Invoice', key: 'tax_invoice_no', width: '120px' },
				{ title: 'Invoice Status', key: 'invoice_status', width: '120px' }
			],
			invoices: [
				{
					index: 1,
					pos_profile: 'Main POS',
					user_id: 'admin',
					date: '01/15',
					time: '14:25',
					customer_name: 'John Doe',
					customer_tax_id: 'TX123456',
					invoice_no: 'INV-001',
					total_amount: 125.00,
					paid_amount: 125.00,
					outstanding: 0.00,
					payment_method: 'Visa',
					tax_invoice_no: 'TX-INV-001',
					invoice_status: 'Exported'
				},
				{
					index: 2,
					pos_profile: 'Main POS',
					user_id: 'admin',
					date: '01/15',
					time: '14:18',
					customer_name: 'Jane Smith',
					customer_tax_id: 'TX789012',
					invoice_no: 'INV-002',
					total_amount: 89.50,
					paid_amount: 89.50,
					outstanding: 0.00,
					payment_method: 'Cash',
					tax_invoice_no: 'TX-INV-002',
					invoice_status: 'Exported'
				},
				{
					index: 3,
					pos_profile: 'Main POS',
					user_id: 'cashier',
					date: '01/15',
					time: '14:12',
					customer_name: 'Walk-in Customer',
					customer_tax_id: '',
					invoice_no: 'INV-003',
					total_amount: 67.25,
					paid_amount: 50.00,
					outstanding: 17.25,
					payment_method: 'Bank',
					tax_invoice_no: 'TX-INV-003',
					invoice_status: 'Pending'
				},
				{
					index: 4,
					pos_profile: 'Main POS',
					user_id: 'admin',
					date: '01/15',
					time: '14:08',
					customer_name: 'Mike Johnson',
					customer_tax_id: 'TX345678',
					invoice_no: 'INV-004',
					total_amount: 203.75,
					paid_amount: 203.75,
					outstanding: 0.00,
					payment_method: 'Master',
					tax_invoice_no: 'TX-INV-004',
					invoice_status: 'Failed'
				},
				{
					index: 5,
					pos_profile: 'Main POS',
					user_id: 'cashier',
					date: '01/15',
					time: '14:02',
					customer_name: 'Sarah Wilson',
					customer_tax_id: 'TX901234',
					invoice_no: 'INV-005',
					total_amount: 156.80,
					paid_amount: 100.00,
					outstanding: 56.80,
					payment_method: 'Cash',
					tax_invoice_no: 'TX-INV-005',
					invoice_status: 'Exported'
				}
			],
			shiftStatistics: {
				date: '2024-01-15',
				time: '14:30:25',
				user: 'admin',
				opening_amount: 500.00,
				today_revenue: 12450.00,
				last_sync: '14:28:15',
				total_invoices: 95,
				total_revenue: 12450.00,
				opening: {
					cash: 500.00,
					bank: 0.00,
					total: 500.00,
					user: 'admin',
					date: '2024-01-15',
					time: '09:00:00'
				},
				transactions: {
					total_invoices: 95,
					total_revenue: 12450.00,
					cash_revenue: 6250.00,
					card_revenue: 4500.00,
					bank_revenue: 1700.00,
					outstanding: 1250.00,
					tax_invoices: 87,
					exported: 82,
					failed: 5,
					pending: 8
				},
				closing: {
					cash: {
						opening: 500.00,
						current: 6750.00,
						expected: 7250.00,
						difference: 500.00
					},
					bank: {
						opening: 0.00,
						current: 5700.00,
						expected: 1700.00,
						difference: -4000.00
					}
				},
				invoice_range: {
					first_invoice: 'INV-011',
					last_invoice: 'INV-095',
					total_invoices: 95,
					time_range: '09:00-14:30'
				},
				tax_invoice_range: {
					first_tax_invoice: 'TX-INV-001',
					last_tax_invoice: 'TX-INV-093',
					total_tax_invoices: 87,
					success_rate: 94.3
				}
			}
		};
	},
	computed: {
		filteredInvoices() {
			let filtered = this.invoices;

			if (this.filters.pos_profile) {
				filtered = filtered.filter(inv => inv.pos_profile === this.filters.pos_profile);
			}
			if (this.filters.user_id) {
				filtered = filtered.filter(inv => inv.user_id.toLowerCase().includes(this.filters.user_id.toLowerCase()));
			}
			if (this.filters.customer_name) {
				filtered = filtered.filter(inv => inv.customer_name.toLowerCase().includes(this.filters.customer_name.toLowerCase()));
			}
			if (this.filters.customer_tax_id) {
				filtered = filtered.filter(inv => inv.customer_tax_id.includes(this.filters.customer_tax_id));
			}
			if (this.filters.invoice_no) {
				filtered = filtered.filter(inv => inv.invoice_no.includes(this.filters.invoice_no));
			}
			if (this.filters.payment_method) {
				filtered = filtered.filter(inv => inv.payment_method === this.filters.payment_method);
			}
			if (this.filters.amount_min) {
				filtered = filtered.filter(inv => inv.total_amount >= parseFloat(this.filters.amount_min));
			}
			if (this.filters.amount_max) {
				filtered = filtered.filter(inv => inv.total_amount <= parseFloat(this.filters.amount_max));
			}

			return filtered;
		}
	},
	methods: {
		close_dialog() {
			this.listInvoicesDialog = false;
		},

		applyFilters() {
			// Filters are applied automatically via computed property
			this.$forceUpdate();
		},

		clearFilters() {
			this.filters = {
				pos_profile: '',
				user_id: '',
				customer_name: '',
				customer_tax_id: '',
				invoice_no: '',
				amount_min: '',
				amount_max: '',
				payment_method: ''
			};
		},

		getPaymentColor(method) {
			const colors = {
				'Cash': 'success',
				'Visa': 'primary',
				'Master': 'info',
				'Bank': 'warning',
				'M-Pesa': 'purple'
			};
			return colors[method] || 'grey';
		},

		getPaymentIcon(method) {
			const icons = {
				'Cash': '💰',
				'Visa': '💳',
				'Master': '💳',
				'Bank': '🏦',
				'M-Pesa': '📱'
			};
			return icons[method] || '❓';
		},

		getStatusColor(status) {
			const colors = {
				'Exported': 'success',
				'Pending': 'warning',
				'Failed': 'error'
			};
			return colors[status] || 'grey';
		},

		getStatusIcon(status) {
			const icons = {
				'Exported': '✅',
				'Pending': '⏳',
				'Failed': '❌'
			};
			return icons[status] || '❓';
		},

		printAllInvoices() {
			// TODO: Implement print functionality
			this.$emit('show_message', {
				title: 'Print All Invoices',
				message: 'Printing all invoices from current shift...',
				color: 'info'
			});
		},

		emailReport() {
			// TODO: Implement email functionality
			this.$emit('show_message', {
				title: 'Email Report',
				message: 'Sending shift report to admin...',
				color: 'info'
			});
		},

		exportData() {
			// TODO: Implement export functionality
			this.$emit('show_message', {
				title: 'Export Data',
				message: 'Exporting invoice data...',
				color: 'success'
			});
		},

		closeShift() {
			// TODO: Implement close shift functionality
			this.$emit('show_message', {
				title: 'Close Shift',
				message: 'Closing current shift...',
				color: 'warning'
			});
		}
	},
	created() {
		this.eventBus.on("open_list_invoices", () => {
			this.listInvoicesDialog = true;
		});
	},
	beforeUnmount() {
		this.eventBus.off("open_list_invoices");
	}
};
</script>

<style scoped>
/* List Invoices Dialog Card */
.list-invoices-dialog-card {
	border-radius: 20px !important;
	overflow: hidden;
	background: white;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
	max-height: 95vh;
}

/* Enhanced Header */
.list-invoices-header {
	background: var(--surface-primary, white);
	color: var(--text-primary, #1a1a1a);
	border-bottom: 1px solid var(--field-border, #f0f0f0);
	position: relative;
	min-height: auto !important;
}

.list-invoices-header::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 4px;
	background: linear-gradient(90deg, var(--primary-start, #1976d2) 0%, var(--primary-end, #42a5f5) 100%);
}

.header-content {
	display: flex;
	align-items: center;
	gap: 20px;
	padding-right: 60px;
}

.header-icon-wrapper {
	background: linear-gradient(135deg, var(--primary-start, #1976d2) 0%, var(--primary-end, #42a5f5) 100%);
	border-radius: 16px;
	padding: 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
}

.header-icon {
	color: white;
}

.header-text {
	flex: 1;
}

.header-title {
	margin: 0 0 4px 0;
	font-weight: 700;
	color: var(--text-primary, #1a1a1a);
	font-size: 1.5rem;
	line-height: 1.2;
}

.header-subtitle {
	margin: 0 0 12px 0;
	font-size: 14px;
	color: var(--text-secondary, #666);
	font-weight: 400;
	line-height: 1.2;
}

.header-stats {
	display: flex;
	gap: 8px;
}

.status-chip {
	font-weight: 600;
	border-radius: 12px;
}

.close-btn {
	position: absolute;
	top: 16px;
	right: 16px;
	color: var(--text-secondary, #666) !important;
}

.header-divider {
	border-color: var(--field-border, #f0f0f0);
}

/* Shift Summary Header */
.shift-summary-header {
	background: #f8f9fa;
	border-bottom: 1px solid #e0e0e0;
}

.summary-item {
	display: flex;
	align-items: center;
	margin-bottom: 8px;
}

.summary-label {
	font-weight: 600;
	color: #666;
	min-width: 80px;
	margin-right: 8px;
}

.summary-value {
	font-weight: 600;
	color: #333;
}

/* Content */
.white-background {
	background: white;
}

.content-container {
	padding: 0;
	max-height: 75vh;
	overflow-y: auto;
}

/* Filters Section */
.filters-section {
	background: #fafafa;
	border-bottom: 1px solid #e0e0e0;
}

/* Table Section */
.table-section {
	background: white;
}

.table-header {
	padding: 16px 24px 8px 24px;
}

/* Enhanced Table */
.invoices-table {
	background: white;
	border: 1px solid #f0f0f0;
	border-radius: 16px;
	overflow: hidden;
	margin: 0 24px;
}

.invoices-table :deep(th) {
	font-weight: 600;
	color: #424242;
	font-size: 0.875rem;
	padding: 16px;
	background: #fafafa;
	border-bottom: 2px solid #f0f0f0;
}

.invoices-table :deep(tr) {
	border-bottom: 1px solid #f5f5f5;
}

.invoices-table :deep(tr:hover) {
	background-color: rgba(25, 118, 210, 0.02);
}

.invoices-table :deep(td) {
	padding: 12px 16px;
	border-bottom: 1px solid #f5f5f5;
}

/* Enhanced Cells */
.customer-cell {
	display: flex;
	align-items: center;
}

.time-cell {
	display: flex;
	align-items: center;
	font-size: 0.875rem;
	color: #666;
}

.font-mono {
	font-family: 'Roboto Mono', monospace;
	font-size: 0.875rem;
}

/* Statistics Section */
.statistics-section {
	background: #f8f9fa;
	border-top: 1px solid #e0e0e0;
}

.stats-group {
	background: white;
	border-radius: 12px;
	padding: 16px;
	margin-bottom: 16px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stats-group h5 {
	color: #1976d2;
	font-weight: 600;
	margin-bottom: 16px;
}

.closing-cash, .closing-bank {
	background: #f9f9f9;
	border-radius: 8px;
	padding: 12px;
	margin-top: 8px;
}

.difference-display {
	text-align: center;
}

/* Footer */
.dialog-actions-container {
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
	border-top: 1px solid #e0e0e0 !important;
	padding: 16px 24px !important;
	gap: 8px !important;
}

.footer-info {
	display: flex;
	align-items: center;
}

.footer-text {
	font-size: 13px;
	color: #666;
	display: flex;
	align-items: center;
	gap: 6px;
}

/* Responsive Design */
@media (max-width: 1200px) {
	.list-invoices-dialog-card {
		margin: 8px;
		max-height: 90vh;
	}

	.invoices-table {
		margin: 0 16px;
	}

	.content-container {
		padding: 0;
		max-height: 70vh;
	}
}

@media (max-width: 768px) {
	.header-content {
		flex-direction: column;
		align-items: flex-start;
		gap: 16px;
		padding-right: 50px;
	}

	.shift-summary-header .v-row {
		flex-direction: column;
	}

	.summary-item {
		justify-content: flex-start;
		margin-bottom: 4px;
	}

	.filters-section .v-row {
		flex-direction: column;
	}

	.filters-section .v-col {
		margin-bottom: 8px;
	}

	.table-section {
		overflow-x: auto;
	}

	.invoices-table {
		min-width: 800px;
		margin: 0 8px;
	}

	.statistics-section .v-row {
		flex-direction: column;
	}

	.stats-group .v-col {
		margin-bottom: 8px;
	}

	.dialog-actions-container {
		flex-direction: column;
		gap: 8px !important;
	}

	.dialog-actions-container .v-btn {
		width: 100%;
	}
}

@media (max-width: 480px) {
	.header-title {
		font-size: 1.25rem !important;
	}

	.invoices-table {
		min-width: 600px;
	}

	.stats-group {
		padding: 12px;
	}
}

/* Scrollbar Styling */
.content-container::-webkit-scrollbar {
	width: 6px;
}

.content-container::-webkit-scrollbar-track {
	background: #f1f1f1;
	border-radius: 3px;
}

.content-container::-webkit-scrollbar-thumb {
	background: #c1c1c1;
	border-radius: 3px;
}

.content-container::-webkit-scrollbar-thumb:hover {
	background: #a8a8a8;
}
</style>