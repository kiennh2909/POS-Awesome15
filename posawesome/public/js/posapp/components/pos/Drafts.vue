<template>
	<v-row justify="center">
		<v-dialog v-model="draftsDialog" max-width="950px" persistent>
			<v-card class="drafts-dialog-card">
				<!-- Enhanced Header -->
				<v-card-title class="drafts-header pa-6">
					<div class="header-content">
						<div class="header-icon-wrapper">
							<v-icon class="header-icon" size="28">mdi-file-document-multiple</v-icon>
						</div>
						<div class="header-text">
							<h3 class="header-title">{{ __("Load Sales Invoice") }}</h3>
							<p class="header-subtitle">{{ __("Load previously saved invoices") }}</p>
							<div class="header-stats" v-if="dialog_data && dialog_data.length > 0">
								<v-chip
									color="primary"
									variant="tonal"
									size="small"
									class="status-chip"
								>
									<v-icon start size="14">mdi-file-document-outline</v-icon>
									{{ dialog_data.length }} {{ __("Drafts") }}
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

				<!-- Content -->
				<v-card-text class="pa-0 white-background">
					<div class="content-container">
						<!-- Empty State -->
						<div v-if="!dialog_data || dialog_data.length === 0" class="empty-state text-center py-12">
							<div class="empty-icon-wrapper mb-4">
								<v-icon size="80" color="grey" class="empty-icon">mdi-file-document-outline</v-icon>
							</div>
							<h3 class="text-h5 mb-3 text-grey-darken-2 font-weight-medium">
								{{ __("No Draft Invoices") }}
							</h3>
							<p class="text-body-1 text-grey-darken-1 mb-0">
								{{ __("No previously saved invoices found") }}
							</p>
						</div>

						<!-- Drafts Table -->
						<div v-else class="table-container">
							<div class="table-header mb-4">
								<h4 class="text-h6 text-grey-darken-2 mb-1">{{ __("Available Drafts") }}</h4>
								<p class="text-body-2 text-grey">
									{{ __("Select an invoice to load and continue editing") }}
								</p>
							</div>

							<v-data-table
								:headers="headers"
								:items="dialog_data"
								item-value="name"
								class="drafts-table"
								show-select
								v-model="selected"
								select-strategy="single"
								return-object
								:items-per-page="10"
								:items-per-page-options="[5, 10, 15, 25]"
							>
								<template v-slot:item.customer_name="{ item }">
									<div class="customer-cell">
										<v-avatar size="32" color="primary" class="mr-3">
											<v-icon size="18" color="white">mdi-account</v-icon>
										</v-avatar>
										<div>
											<div class="font-weight-medium text-grey-darken-2">
												{{ item.customer_name || __("Walk-in Customer") }}
											</div>
											<div class="text-caption text-grey">{{ __("Customer") }}</div>
										</div>
									</div>
								</template>

								<template v-slot:item.posting_date="{ item }">
									<v-chip size="small" color="info" variant="tonal" class="date-chip">
										<v-icon start size="14">mdi-calendar</v-icon>
										{{ item.posting_date }}
									</v-chip>
								</template>

								<template v-slot:item.posting_time="{ item }">
									<div class="time-cell">
										<v-icon size="16" color="grey" class="mr-1">mdi-clock-outline</v-icon>
										<span class="text-body-2">{{ item.posting_time.split(".")[0] }}</span>
									</div>
								</template>

								<template v-slot:item.grand_total="{ item }">
									<div class="amount-cell text-right">
										<div class="text-h6 font-weight-bold text-success">
											{{ currencySymbol(item.currency) }}
											{{ formatCurrency(item.grand_total) }}
										</div>
										<div class="text-caption text-grey">{{ __("Total Amount") }}</div>
									</div>
								</template>
							</v-data-table>
						</div>
					</div>
				</v-card-text>

				<!-- Enhanced Footer -->
				<v-divider></v-divider>
				<v-card-actions class="dialog-actions-container">
					<div class="footer-info">
						<span class="footer-text">
							<v-icon start size="16" color="primary">mdi-information-outline</v-icon>
							{{ __("Select one invoice to load") }}
						</span>
					</div>
					<v-spacer></v-spacer>
					<v-btn
						theme="dark"
						variant="outlined"
						@click="close_dialog"
						class="standard-btn cancel-btn"
						size="default"
					>
						<v-icon start>mdi-close</v-icon>
						{{ __("Cancel") }}
					</v-btn>
					<v-btn
						theme="dark"
						variant="elevated"
						color="primary"
						@click="submit_dialog"
						:disabled="!selected || selected.length === 0"
						class="standard-btn load-btn"
						size="default"
					>
						<v-icon start>mdi-file-upload</v-icon>
						{{ __("Load Invoice") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";
export default {
	name: "DraftsDialog",
	mixins: [format],
	data: () => ({
		draftsDialog: false,
		singleSelect: true,
		selected: [],
		dialog_data: [],
		headers: [
			{
				title: __("Customer"),
				value: "customer_name",
				align: "start",
				sortable: true,
				width: "30%",
			},
			{
				title: __("Date"),
				align: "center",
				sortable: true,
				value: "posting_date",
				width: "15%",
			},
			{
				title: __("Time"),
				align: "center",
				sortable: true,
				value: "posting_time",
				width: "15%",
			},
			{
				title: __("Invoice"),
				value: "name",
				align: "start",
				sortable: true,
				width: "20%",
			},
			{
				title: __("Amount"),
				value: "grand_total",
				align: "end",
				sortable: false,
				width: "20%",
			},
		],
	}),
	watch: {},
	methods: {
		close_dialog() {
			this.draftsDialog = false;
			this.selected = [];
		},

		submit_dialog() {
			if (this.selected && this.selected.length > 0) {
				this.eventBus.emit("load_invoice", this.selected[0]);
				this.draftsDialog = false;
				this.selected = [];
			} else {
				this.eventBus.emit("show_message", {
					title: __("Please select an invoice to load"),
					color: "error",
				});
			}
		},
	},
	created: function () {
		this.eventBus.on("open_drafts", (data) => {
			this.draftsDialog = true;
			this.dialog_data = Array.isArray(data) ? data : [];
			this.selected = [];
		});
	},
	beforeUnmount() {
		this.eventBus.off("open_drafts");
	},
};
</script>

<style scoped>
/* Drafts Dialog Card */
.drafts-dialog-card {
	border-radius: 20px !important;
	overflow: hidden;
	background: white;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
	max-height: 90vh;
}

/* Enhanced Header */
.drafts-header {
	background: var(--surface-primary, white);
	color: var(--text-primary, #1a1a1a);
	border-bottom: 1px solid var(--field-border, #f0f0f0);
	position: relative;
	min-height: auto !important;
}

.drafts-header::before {
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

/* Content */
.white-background {
	background: white;
}

.content-container {
	padding: 24px;
	max-height: 60vh;
	overflow-y: auto;
}

/* Empty State */
.empty-state {
	padding: 64px 24px;
	background: white;
}

.empty-icon-wrapper {
	display: inline-block;
	padding: 20px;
	background: rgba(144, 164, 174, 0.1);
	border-radius: 50%;
}

.empty-icon {
	filter: drop-shadow(0 2px 8px rgba(144, 164, 174, 0.3));
}

/* Table Container */
.table-container {
	background: white;
}

.table-header {
	padding: 0 4px;
}

/* Enhanced Table */
.drafts-table {
	background: white;
	border: 1px solid #f0f0f0;
	border-radius: 16px;
	overflow: hidden;
}

.drafts-table :deep(th) {
	font-weight: 600;
	color: #424242;
	font-size: 0.875rem;
	padding: 16px;
	background: #fafafa;
	border-bottom: 2px solid #f0f0f0;
}

.drafts-table :deep(tr) {
	border-bottom: 1px solid #f5f5f5;
}

.drafts-table :deep(tr:hover) {
	background-color: rgba(25, 118, 210, 0.02);
}

.drafts-table :deep(td) {
	padding: 16px;
	border-bottom: 1px solid #f5f5f5;
}

/* Enhanced Cells */
.customer-cell {
	display: flex;
	align-items: center;
}

.amount-cell {
	font-family: "Roboto Mono", monospace;
}

.date-chip {
	border-radius: 8px;
	font-weight: 500;
}

.time-cell {
	display: flex;
	align-items: center;
	font-size: 0.875rem;
	color: #666;
}

/* Footer */
.dialog-actions-container {
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
	border-top: 1px solid #e0e0e0 !important;
	padding: 16px 24px !important;
	gap: 12px !important;
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

/* Standard Buttons */
.standard-btn {
	border-radius: 12px !important;
	text-transform: none !important;
	font-weight: 600 !important;
	height: 44px !important;
	padding: 0 24px !important;
	transition: all 0.3s ease !important;
	min-width: 120px !important;
}

.cancel-btn {
	background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%) !important;
	color: white !important;
}

.cancel-btn:hover {
	transform: translateY(-2px) !important;
	box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4) !important;
}

.load-btn {
	background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
	color: white !important;
}

.load-btn:hover {
	transform: translateY(-2px) !important;
	box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4) !important;
}

.load-btn:disabled {
	opacity: 0.6 !important;
	transform: none !important;
	box-shadow: none !important;
}

/* Responsive Design */
@media (max-width: 768px) {
	.drafts-dialog-card {
		margin: 16px;
		max-height: 85vh;
	}

	.drafts-header {
		padding: 16px !important;
	}

	.header-content {
		flex-direction: column;
		align-items: flex-start;
		gap: 16px;
		padding-right: 50px;
	}

	.content-container {
		padding: 16px;
		max-height: 50vh;
	}

	.table-container {
		overflow-x: auto;
	}

	.standard-btn {
		min-width: 100px !important;
		padding: 0 16px !important;
		font-size: 0.875rem !important;
	}
}

@media (max-width: 480px) {
	.header-title {
		font-size: 1.25rem !important;
	}

	.standard-btn {
		height: 40px !important;
		padding: 0 12px !important;
		font-size: 0.8rem !important;
		min-width: 90px !important;
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
