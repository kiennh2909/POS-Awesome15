<template>
	<div fluid>
		<v-row v-show="!dialog">
			<!-- Left Panel - Invoices and Payments -->
			<v-col md="8" cols="12" class="pb-2 pr-0">
				<v-card
					:class="[
						'main mx-auto mt-3 p-3 pb-16 overflow-y-auto',
						isDarkTheme ? '' : 'bg-grey-lighten-5',
					]"
					:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
					style="max-height: 94vh; height: 94vh"
				>
					<Customer></Customer>
					<v-divider></v-divider>

					<!-- Outstanding Invoices Header -->
					<div class="section-header mb-4">
						<v-row dense class="align-center">
							<v-col cols="12">
								<div class="d-flex align-center justify-space-between">
									<div class="d-flex align-center">
										<v-icon size="24" color="primary" class="mr-3">mdi-file-document-multiple</v-icon>
										<div>
											<h3 class="text-h6 font-weight-bold text-primary mb-1">
												{{ __("Outstanding Invoices") }}
											</h3>
											<p class="text-body-2 text-grey-darken-1 mb-0">
												{{ __("Select invoices to process payment") }}
											</p>
										</div>
									</div>
									<div class="text-right">
										<div v-if="total_outstanding_amount" class="text-h6 font-weight-bold text-success mb-1">
											{{ currencySymbol(pos_profile.currency) }}
											{{ formatCurrency(total_outstanding_amount) }}
										</div>
										<div class="text-caption text-grey">{{ __("Total Outstanding") }}</div>
									</div>
								</div>
							</v-col>
						</v-row>
						<v-row v-if="total_selected_invoices" dense class="mt-2">
							<v-col cols="12">
								<v-alert
									type="info"
									variant="tonal"
									density="compact"
									class="mb-0"
								>
									<div class="d-flex align-center justify-space-between">
										<span class="font-weight-medium">
											{{ __("Selected for Payment:") }}
											{{ selected_invoices.length }} {{ __("invoice(s)") }}
										</span>
										<span class="font-weight-bold text-primary">
											{{ currencySymbol(pos_profile.currency) }}
											{{ formatCurrency(total_selected_invoices) }}
										</span>
									</div>
								</v-alert>
							</v-col>
						</v-row>
					</div>

					<!-- Search and Action Buttons -->
					<v-row align="center" no-gutters class="mb-3">
						<v-col md="4" cols="12">
							<v-select
								density="compact"
								variant="outlined"
								hide-details
								clearable
								class="dark-field"
								:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
								v-model="pos_profile_search"
								:items="pos_profiles_list"
								label="Select POS Profile"
							></v-select>
						</v-col>
						<v-col></v-col>
						<v-col md="3" cols="12" class="pr-1">
							<v-btn
								block
								color="warning"
								theme="dark"
								size="default"
								prepend-icon="mdi-magnify"
								class="standard-btn"
								@click="get_outstanding_invoices"
							>
								{{ __("Search") }}
							</v-btn>
						</v-col>
						<v-col md="3" cols="12" class="pl-1">
							<v-btn
								v-if="selected_invoices.length"
								block
								color="error"
								theme="dark"
								size="default"
								prepend-icon="mdi-close-circle"
								class="standard-btn"
								@click="selected_invoices = []; $forceUpdate();"
							>
								{{ __("Clear") }}
							</v-btn>
						</v-col>
					</v-row>

					<!-- Outstanding Invoices Table -->
					<v-data-table
						:headers="invoices_headers"
						:items="outstanding_invoices"
						item-key="voucher_no"
						class="elevation-1 mt-0"
						:loading="invoices_loading"
						@click:row="selectSingleInvoice"
						:item-class="isSelected"
					>
						<template v-slot:item.actions="{ item }">
							<v-checkbox
								:model-value="isInvoiceSelected(item)"
								color="primary"
								@click.stop="toggleInvoiceSelection(item)"
							>
							</v-checkbox>
						</template>
						<template v-slot:item.invoice_amount="{ item }">
							{{ currencySymbol(item.currency) }}
							{{ formatCurrency(item.invoice_amount) }}
						</template>
						<template v-slot:item.outstanding_amount="{ item }">
							<span class="text-primary">
								{{ currencySymbol(item?.currency || pos_profile.currency) }}
								{{ formatCurrency(item?.outstanding_amount || 0) }}
							</span>
						</template>
					</v-data-table>
					<v-divider></v-divider>

					<!-- Unallocated Payments Section -->
					<div v-if="pos_profile.posa_allow_reconcile_payments && unallocated_payments.length">
						<v-row>
							<v-col md="7" cols="12">
								<p>
									<strong>{{ __("Payments") }}</strong>
									<span v-if="total_unallocated_amount" class="text-primary">
										{{ __("- Total Unallocated") }} :
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(total_unallocated_amount) }}
									</span>
								</p>
							</v-col>
							<v-col md="5" cols="12">
								<p v-if="total_selected_payments" class="golden--text text-end">
									<span>{{ __("Total Selected :") }}</span>
									<span>
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(total_selected_payments) }}
									</span>
								</p>
							</v-col>
						</v-row>
						<v-data-table
							:headers="unallocated_payments_headers"
							:items="unallocated_payments"
							item-key="name"
							class="elevation-1 mt-0"
							:loading="unallocated_payments_loading"
						>
							<template v-slot:item.select="{ item }">
								<v-checkbox
									v-model="selected_payments"
									:value="item"
									color="primary"
									hide-details
									@click.stop
								></v-checkbox>
							</template>
							<template v-slot:item.paid_amount="{ item }">
								{{ currencySymbol(item.currency) }}
								{{ formatCurrency(item.paid_amount) }}
							</template>
							<template v-slot:item.unallocated_amount="{ item }">
								<span class="text-primary"
									>{{ currencySymbol(item.currency) }}
									{{ formatCurrency(item.unallocated_amount) }}</span
								>
							</template>
						</v-data-table>
						<v-divider></v-divider>
					</div>

					<!-- Mpesa Payments Section -->
					<div v-if="pos_profile.posa_allow_mpesa_reconcile_payments">
						<v-row>
							<v-col md="8" cols="12">
								<p>
									<span
										><strong>{{ __("Search Mpesa Payments") }}</strong></span
									>
								</p>
							</v-col>
							<v-col md="4" cols="12" v-if="total_selected_mpesa_payments">
								<p class="golden--text text-end">
									<span>{{ __("Total Selected :") }}</span>
									<span>
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(total_selected_mpesa_payments) }}
									</span>
								</p>
							</v-col>
						</v-row>
						<v-row align="center" no-gutters class="mb-1">
							<v-col md="4" cols="12" class="mr-1">
								<v-text-field
									density="compact"
									variant="outlined"
									color="primary"
									:label="frappe._('Search by Name')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="mpesa_search_name"
									clearable
								></v-text-field>
							</v-col>
							<v-col md="4" cols="12" class="mr-1">
								<v-text-field
									density="compact"
									variant="outlined"
									color="primary"
									:label="frappe._('Search by Mobile')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="mpesa_search_mobile"
									clearable
								></v-text-field>
							</v-col>
							<v-col> </v-col>
							<v-col md="3" cols="12">
								<v-btn
									block
									color="warning"
									theme="dark"
									@click="get_draft_mpesa_payments_register"
									>{{ __("Search") }}</v-btn
								>
							</v-col>
						</v-row>
						<v-data-table
							:headers="mpesa_payment_headers"
							:items="mpesa_payments"
							item-key="name"
							class="elevation-1 mt-0"
							:single-select="singleSelect"
							show-select
							v-model="selected_mpesa_payments"
							:loading="mpesa_payments_loading"
							checkbox-color="primary"
						>
							<template v-slot:item.amount="{ item }">
								<span class="text-primary">
									{{ currencySymbol(item.currency) }}
									{{ formatCurrency(item.amount) }}
								</span>
							</template>
						</v-data-table>
					</div>
				</v-card>
			</v-col>

			<!-- Right Panel - Totals and Actions -->
			<v-col md="4" cols="12" class="pb-3">
				<v-card
					:class="['invoices mx-auto mt-3 p-3', isDarkTheme ? '' : 'bg-grey-lighten-5']"
					:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
					style="max-height: 94vh; height: 94vh"
				>
					<strong>
						<h4 class="text-primary">Totals</h4>
						<v-row>
							<v-col md="7" class="mt-1">
								<span>{{ __("Total Invoices:") }}</span>
							</v-col>
							<v-col md="5">
								<v-text-field
									class="p-0 m-0 dark-field"
									density="compact"
									color="primary"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									:model-value="formatCurrency(total_selected_invoices)"
									readonly
									flat
									:prefix="currencySymbol(pos_profile.currency)"
								></v-text-field>
								<small v-if="selected_invoices.length" class="text-primary"
									>{{ selected_invoices.length }} invoice(s) selected</small
								>
							</v-col>
						</v-row>

						<v-row v-if="total_selected_payments">
							<v-col md="7" class="mt-1"
								><span>{{ __("Total Payments:") }}</span></v-col
							>
							<v-col md="5">
								<v-text-field
									class="p-0 m-0 dark-field"
									density="compact"
									color="primary"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									:model-value="formatCurrency(total_selected_payments)"
									readonly
									flat
									:prefix="currencySymbol(pos_profile.currency)"
								></v-text-field>
							</v-col>
						</v-row>

						<v-row v-if="total_selected_mpesa_payments">
							<v-col md="7" class="mt-1"
								><span>{{ __("Total Mpesa:") }}</span></v-col
							>
							<v-col md="5">
								<v-text-field
									class="p-0 m-0 dark-field"
									density="compact"
									color="primary"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									:model-value="formatCurrency(total_selected_mpesa_payments)"
									readonly
									flat
									:prefix="currencySymbol(pos_profile.currency)"
								></v-text-field>
							</v-col>
						</v-row>

						<v-divider v-if="payment_methods.length"></v-divider>
						<div v-if="pos_profile.posa_allow_make_new_payments">
							<h4 class="text-primary">Make New Payment</h4>
							<v-row
								v-if="payment_methods.length"
								v-for="method in payment_methods"
								:key="method.row_id"
							>
								<v-col md="7"
									><span class="mt-1">{{ __(method.mode_of_payment) }}:</span>
								</v-col>
								<v-col md="5">
									<div class="d-flex align-center">
										<div class="mr-1 text-primary">
											{{ currencySymbol(pos_profile.currency) }}
										</div>
										<v-text-field
											class="p-0 m-0 dark-field"
											density="compact"
											color="primary"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											hide-details
											v-model="method.amount"
											type="number"
											flat
											@input="$forceUpdate()"
										></v-text-field>
									</div>
								</v-col>
							</v-row>
						</div>

						<v-divider></v-divider>
						<v-row>
							<v-col md="7">
								<h4 class="text-primary mt-1">{{ __("Difference:") }}</h4>
							</v-col>
							<v-col md="5">
								<v-text-field
									class="p-0 m-0 dark-field"
									density="compact"
									color="primary"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									:model-value="formatCurrency(total_of_diff)"
									readonly
									flat
									:prefix="currencySymbol(pos_profile.currency)"
								></v-text-field>
							</v-col>
						</v-row>
					</strong>
					<div class="pb-6 pr-6" style="position: absolute; bottom: 0; width: 100%">
						<v-row>
							<v-col cols="6" class="pr-1">
								<v-btn
									block
									size="large"
									color="primary"
									theme="dark"
									@click="submit"
									:disabled="vaildatPayment || isSubmitting"
									:loading="isSubmitting"
								>
									{{ __("Submit") }}
								</v-btn>
							</v-col>
							<v-col cols="6" class="pl-1">
								<v-btn
									block
									size="large"
									color="success"
									theme="dark"
									@click="submit_and_print()"
									:disabled="vaildatPayment || isSubmitting"
									:loading="isSubmitting"
								>
									{{ __("Submit & Print") }}
								</v-btn>
							</v-col>
						</v-row>
					</div>
				</v-card>
			</v-col>
		</v-row>
	</div>
</template>

<script>
import format from "../../format";
import Customer from "../pos/Customer.vue";
import {
	getOpeningStorage,
	setOpeningStorage,
	initPromise,
	checkDbHealth,
	saveOfflinePayment,
	syncOfflinePayments,
	getPendingOfflinePaymentCount,
	isOffline,
	getCustomerStorage,
	getOfflineCustomers,
} from "../../../offline/index.js";
import { silentPrint } from "../../plugins/print.js";

export default {
	mixins: [format],
	data: function () {
		return {
			dialog: false,
			pos_profile: "",
			pos_opening_shift: "",
			customer_name: "",
			customer_info: "",
			company: "",
			singleSelect: true,
			invoices_loading: false,
			unallocated_payments_loading: false,
			mpesa_payments_loading: false,
			payment_methods: [],
			outstanding_invoices: [],
			unallocated_payments: [],
			mpesa_payments: [],
			selected_invoices: [],
			selected_payments: [],
			selected_mpesa_payments: [],
			pos_profiles_list: [],
			pos_profile_search: "",
			payment_methods_list: [],
			mpesa_search_name: "",
			mpesa_search_mobile: "",
			invoices_headers: [
				{ title: "", align: "start", sortable: false, key: "actions", width: "50px" },
				{ title: __("Invoice"), align: "start", sortable: true, key: "voucher_no" },
				{ title: __("Customer"), align: "start", sortable: true, key: "customer_name" },
				{ title: __("Date"), align: "start", sortable: true, key: "posting_date" },
				{ title: __("Due Date"), align: "start", sortable: true, key: "due_date" },
				{ title: __("Total"), align: "end", sortable: true, key: "invoice_amount" },
				{ title: __("Outstanding"), align: "end", sortable: true, key: "outstanding_amount" },
			],
			unallocated_payments_headers: [
				{ title: "", align: "center", sortable: false, key: "select", width: "50px" },
				{ title: __("Payment ID"), align: "start", sortable: true, key: "name" },
				{ title: __("Customer"), align: "start", sortable: true, key: "customer_name" },
				{ title: __("Date"), align: "start", sortable: true, key: "posting_date" },
				{ title: __("Mode"), align: "start", sortable: true, key: "mode_of_payment" },
				{ title: __("Paid"), align: "end", sortable: true, key: "paid_amount" },
				{ title: __("Unallocated"), align: "end", sortable: true, key: "unallocated_amount" },
			],
			mpesa_payment_headers: [
				{ title: __("Payment ID"), align: "start", sortable: true, key: "transid" },
				{ title: __("Full Name"), align: "start", sortable: true, key: "full_name" },
				{ title: __("Mobile Number"), align: "start", sortable: true, key: "mobile_no" },
				{ title: __("Date"), align: "start", sortable: true, key: "posting_date" },
				{ title: __("Amount"), align: "end", sortable: true, key: "amount" },
			],
			isSubmitting: false,
		};
	},

	components: { Customer },

	methods: {
		async check_opening_entry() {
			const vm = this;
			await initPromise;
			await checkDbHealth();
			return frappe
				.call("posawesome.posawesome.api.shifts.check_opening_shift", { user: frappe.session.user })
				.then((r) => {
					if (r.message) {
						this.pos_profile = r.message.pos_profile;
						this.pos_opening_shift = r.message.pos_opening_shift;
						this.company = r.message.company.name;
						vm.eventBus.emit("payments_register_pos_profile", r.message);
						vm.eventBus.emit("set_company", r.message.company);
						this.set_payment_methods();
						try { setOpeningStorage(r.message); } catch (e) { console.error("Failed to cache opening data", e); }

						// init search profile: keep empty by default
						this.pos_profile_search = "";
						this.pos_profiles_list = [];
						if (r.message.pos_profile && r.message.pos_profile.name) {
							this.pos_profiles_list.push(r.message.pos_profile.name);
						}

						this.payment_methods_list = [];
						this.pos_profile.payments.forEach((el) => this.payment_methods_list.push(el.mode_of_payment));
						this.get_available_pos_profiles();
						this.get_outstanding_invoices();
						this.get_draft_mpesa_payments_register();
					} else {
						const data = getOpeningStorage();
						if (data) {
							this.pos_profile = data.pos_profile;
							this.pos_opening_shift = data.pos_opening_shift;
							this.company = data.company.name;
							vm.eventBus.emit("payments_register_pos_profile", data);
							vm.eventBus.emit("set_company", data.company);
							this.set_payment_methods();
							this.payment_methods_list = [];
							this.pos_profile.payments.forEach((el) => this.payment_methods_list.push(el.mode_of_payment));
							this.get_available_pos_profiles();
							this.get_outstanding_invoices();
							this.get_draft_mpesa_payments_register();
							return;
						}
						this.create_opening_voucher();
					}
				})
				.catch(() => {
					const data = getOpeningStorage();
					if (data) {
						this.pos_profile = data.pos_profile;
						this.pos_opening_shift = data.pos_opening_shift;
						this.company = data.company.name;
						vm.eventBus.emit("payments_register_pos_profile", data);
						vm.eventBus.emit("set_company", data.company);
						this.set_payment_methods();
						this.payment_methods_list = [];
						this.pos_profile.payments.forEach((el) => this.payment_methods_list.push(el.mode_of_payment));
						this.get_available_pos_profiles();
						this.get_outstanding_invoices();
						this.get_draft_mpesa_payments_register();
						return;
					}
					this.create_opening_voucher();
				});
		},
		get_available_pos_profiles() {
			if (!this.pos_profile.posa_allow_mpesa_reconcile_payments) return;
			return frappe
				.call("posawesome.posawesome.api.payment_entry.get_available_pos_profiles", {
					company: this.company,
					currency: this.pos_profile.currency,
				})
				.then((r) => {
					if (r.message) {
						this.pos_profiles_list = r.message;
					}
				});
		},
		create_opening_voucher() { this.dialog = true; },

		async fetch_customer_details() {
			const vm = this;
			if (!vm.customer_name) return;

			// --- helper: gắn tax_id vào invoice_doc ngay khi có ---
			const attachTaxIdToInvoice = (taxIdRaw) => {
				const taxId = (taxIdRaw || "").toString().trim();
				// đảm bảo luôn có object để gắn reactivity
				vm.invoice_doc = vm.invoice_doc || {};
				// gắn vào các field có thể dùng
				vm.invoice_doc.tax_id = taxId;
				vm.invoice_doc.customer_tax_id = taxId;
				console.log("[TRACE] attachTaxIdToInvoice ->", taxId);

				// (tuỳ chọn) nếu cả 2 field không tồn tại trong DocType và bạn muốn vẫn in được:
				// if (!("tax_id" in vm.invoice_doc) && !("customer_tax_id" in vm.invoice_doc) && taxId) {
				//   const line = `Tax ID: ${taxId}`;
				//   const remarks = (vm.invoice_doc.remarks || "").split("\n").filter(Boolean);
				//   if (!remarks.some(r => r.includes(line))) {
				//     remarks.push(line);
				//     vm.invoice_doc.remarks = remarks.join("\n");
				//   }
				// }
			};

			// --- OFFLINE FIRST: thử lấy từ cache ---
			if (isOffline()) {
				try {
				const cached =
					(getCustomerStorage() || []).find(
					(c) => c.name === vm.customer_name || c.customer_name === vm.customer_name
					) || null;

				if (cached) {
					vm.customer_info = { ...cached };
					console.log("[TRACE] customer_info from cache =", vm.customer_info);
					attachTaxIdToInvoice(vm.customer_info.tax_id);
					vm.set_mpesa_search_params();
					vm.eventBus.emit("set_customer_info_to_edit", vm.customer_info);
					return;
				}

				const queued = (getOfflineCustomers() || [])
					.map((e) => e.args)
					.find((c) => c.customer_name === vm.customer_name);

				if (queued) {
					vm.customer_info = { ...queued, name: queued.customer_name };
					console.log("[TRACE] customer_info from offline queue =", vm.customer_info);
					attachTaxIdToInvoice(vm.customer_info.tax_id);
					vm.set_mpesa_search_params();
					vm.eventBus.emit("set_customer_info_to_edit", vm.customer_info);
				}
				} catch (error) {
				console.error("Failed to fetch cached customer", error);
				}
				return;
			}

			// --- ONLINE: gọi API ---
			try {
				const r = await frappe.call({
				method: "posawesome.posawesome.api.posapp.get_customer_info",
				args: { customer: vm.customer_name },
				});

				if (!r.exc && r.message) {
				vm.customer_info = { ...r.message };
				console.log("[TRACE] customer_info from server =", vm.customer_info);

				// GẮN TAX_ID NGAY TẠI ĐÂY
				attachTaxIdToInvoice(vm.customer_info.tax_id);

				// phục vụ các UI khác
				vm.set_mpesa_search_params();
				vm.eventBus.emit("set_customer_info_to_edit", vm.customer_info);
				} else {
				console.warn("[TRACE] get_customer_info trả về rỗng hoặc có exc", r);
				}
			} catch (error) {
				console.error("Failed to fetch customer details", error);
			}
		},
		selectSingleInvoice(item) {
			if (item && item.voucher_no) {
				this.eventBus.emit("set_invoice", item);
				this.$nextTick(() => this.$forceUpdate());
			}
		},
		// Remove duplicate method
		// async fetch_customer_details() {
		// 	const vm = this;
		// 	if (!this.customer_name) return;

		// 	// Offline first: try cache
		// 	if (isOffline()) {
		// 		try {
		// 			const cached = (getCustomerStorage() || []).find(
		// 				(c) => c.name === vm.customer_name || c.customer_name === vm.customer_name,
		// 			);
		// 			if (cached) {
		// 				vm.customer_info = { ...cached };
		// 				vm.set_mpesa_search_params();
		// 				vm.eventBus.emit("set_customer_info_to_edit", vm.customer_info);
		// 				return;
		// 			}
		// 			const queued = (getOfflineCustomers() || [])
		// 				.map((e) => e.args)
		// 				.find((c) => c.customer_name === vm.customer_name);
		// 			if (queued) {
		// 				vm.customer_info = { ...queued, name: queued.customer_name };
		// 				vm.set_mpesa_search_params();
		// 				vm.eventBus.emit("set_customer_info_to_edit", vm.customer_info);
		// 			}
		// 		} catch (error) {
		// 			console.error("Failed to fetch cached customer", error);
		// 		}
		// 		return;
		// 	}

		// 	try {
		// 		const r = await frappe.call({
		// 			method: "posawesome.posawesome.api.posapp.get_customer_info",
		// 			args: { customer: vm.customer_name },
		// 		});
		// 		if (!r.exc && r.message) {
		// 			vm.customer_info = { ...r.message }; // tax_id nằm trong đây nếu cần sử dụng
		// 			vm.set_mpesa_search_params();
		// 			vm.eventBus.emit("set_customer_info_to_edit", vm.customer_info);
		// 		}
		// 	} catch (error) {
		// 		console.error("Failed to fetch customer details", error);
		// 	}
		// },

		onInvoiceSelected(event) {
			if (event && event.item && event.item.customer) {
				this.eventBus.emit("set_customer", event.item.customer);
				this.$nextTick(() => this.$forceUpdate());
			}
		},
		get_outstanding_invoices() {
			this.invoices_loading = true;
			this.selected_invoices = [];

			if (isOffline()) {
				this.outstanding_invoices = [];
				this.invoices_loading = false;
				return;
			}

			return frappe
				.call("posawesome.posawesome.api.payment_entry.get_outstanding_invoices", {
					customer: this.customer_name,
					company: this.company,
					currency: this.pos_profile.currency,
					pos_profile: this.pos_profile_search || null,
				})
				.then((r) => {
					if (r.message) {
						this.outstanding_invoices = r.message;
					}
				})
				.finally(() => {
					this.invoices_loading = false;
					this.$nextTick(() => this.$forceUpdate());
				});
		},
		get_unallocated_payments() {
			if (!this.pos_profile.posa_allow_reconcile_payments) return;
			this.unallocated_payments_loading = true;
			if (!this.customer_name) {
				this.unallocated_payments = [];
				this.unallocated_payments_loading = false;
				return;
			}

			if (isOffline()) {
				this.unallocated_payments = [];
				this.unallocated_payments_loading = false;
				return;
			}
			return frappe
				.call("posawesome.posawesome.api.payment_entry.get_unallocated_payments", {
					customer: this.customer_name,
					company: this.company,
					currency: this.pos_profile.currency,
				})
				.then((r) => {
					if (r.message) {
						this.unallocated_payments = r.message;
					}
				})
				.finally(() => {
					this.unallocated_payments_loading = false;
				});
		},
		set_mpesa_search_params() {
			if (!this.pos_profile.posa_allow_mpesa_reconcile_payments) return;
			if (!this.customer_name) return;
			this.mpesa_search_name = (this.customer_info.customer_name || "").split(" ")[0] || "";
			if (this.customer_info.mobile_no) {
				this.mpesa_search_mobile =
					this.customer_info.mobile_no.substring(0, 4) +
					" ***** " +
					this.customer_info.mobile_no.substring(9);
			}
		},
		get_draft_mpesa_payments_register() {
			if (!this.pos_profile.posa_allow_mpesa_reconcile_payments) return;
			const vm = this;
			this.mpesa_payments_loading = true;

			if (isOffline()) {
				this.mpesa_payments = [];
				this.mpesa_payments_loading = false;
				return;
			}
			return frappe
				.call("posawesome.posawesome.api.m_pesa.get_mpesa_draft_payments", {
					company: vm.company,
					mode_of_payment: null,
					full_name: vm.mpesa_search_name || null,
					mobile_no: vm.mpesa_search_mobile || null,
					payment_methods_list: vm.payment_methods_list,
				})
				.then((r) => {
					vm.mpesa_payments = r.message || [];
				})
				.finally(() => {
					vm.mpesa_payments_loading = false;
				});
		},
		set_payment_methods() {
			if (!this.pos_profile.posa_allow_make_new_payments) return;
			this.payment_methods = [];
			this.pos_profile.payments.forEach((method) => {
				this.payment_methods.push({ mode_of_payment: method.mode_of_payment, amount: 0, row_id: method.name });
			});
		},
		clear_all(with_customer_info = true) {
			this.customer_name = "";
			if (with_customer_info) this.customer_info = "";
			this.mpesa_search_mobile = "";
			this.mpesa_search_name = "";
			this.mpesa_payments = [];
			this.selected_mpesa_payments = [];
			this.outstanding_invoices = [];
			this.unallocated_payments = [];
			this.selected_invoices = [];
			this.selected_payments = [];
			this.selected_mpesa_payments = [];
			this.set_payment_methods();
		},
		submit() {
			if (this.isSubmitting) return;
			this.isSubmitting = true;
			const customer = this.customer_name;
			const vm = this;

			if (!customer) {
				this.isSubmitting = false;
				frappe.throw(__("Please select a customer"));
				return;
			}
			if (this.selected_invoices.length === 0) {
				this.isSubmitting = false;
				frappe.throw(__("Please select an invoice"));
				return;
			}

			let total_payments = this.total_selected_payments + this.total_selected_mpesa_payments + this.total_payment_methods;
			if (total_payments <= 0) {
				this.isSubmitting = false;
				frappe.throw(__("Please make a payment or select an payment"));
				return;
			}

			this.payment_methods.forEach((payment) => { payment.amount = this.flt(payment.amount); });

			const payload = {
				customer,
				company: this.company,
				currency: this.pos_profile.currency,
				pos_opening_shift_name: this.pos_opening_shift.name,
				pos_profile_name: this.pos_profile.name,
				pos_profile: this.pos_profile,
				payment_methods: this.payment_methods,
				selected_invoices: this.selected_invoices,
				selected_payments: this.selected_payments,
				total_selected_invoices: this.flt(this.total_selected_invoices),
				selected_mpesa_payments: this.selected_mpesa_payments,
				total_selected_payments: this.flt(this.total_selected_payments),
				total_payment_methods: this.flt(this.total_payment_methods),
				total_selected_mpesa_payments: this.flt(this.total_selected_mpesa_payments),
			};

			if (isOffline()) {
				try {
					saveOfflinePayment({ args: { payload } });
					vm.eventBus.emit("show_message", { title: __("Payment saved offline"), color: "warning" });
					vm.clear_all(false);
					vm.customer_name = customer;
					vm.get_outstanding_invoices();
					vm.get_unallocated_payments();
					vm.set_mpesa_search_params();
					vm.get_draft_mpesa_payments_register();
				} catch (error) {
					frappe.msgprint(__("Cannot Save Offline Payment: ") + (error.message || __("Unknown error")));
				}
				vm.isSubmitting = false;
				return;
			}

			frappe.call({
				method: "posawesome.posawesome.api.payment_entry.process_pos_payment",
				args: { payload },
				freeze: true,
				freeze_message: __("Processing Payment"),
				callback: function (r) {
					vm.isSubmitting = false;
					if (r.message) {
						frappe.utils.play_sound("submit");
						vm.clear_all(false);
						vm.customer_name = customer;
						vm.get_outstanding_invoices();
						vm.get_unallocated_payments();
						vm.set_mpesa_search_params();
						vm.get_draft_mpesa_payments_register();
					}
				},
				error: function () { vm.isSubmitting = false; },
			});
		},
		submit_and_print() {
			if (this.isSubmitting) return;
			this.isSubmitting = true;
			const customer = this.customer_name;
			const vm = this;
			if (!customer) {
				this.isSubmitting = false;
				frappe.throw(__("Please select a customer"));
				return;
			}
			if (this.selected_invoices.length === 0) {
				this.isSubmitting = false;
				frappe.throw(__("Please select an invoice"));
				return;
			}

			let total_payments = this.total_selected_payments + this.total_selected_mpesa_payments + this.total_payment_methods;
			if (total_payments <= 0) {
				this.isSubmitting = false;
				frappe.throw(__("Please make a payment or select an payment"));
				return;
			}

			this.payment_methods.forEach((payment) => { payment.amount = this.flt(payment.amount); });

			const payload = {
				customer,
				company: this.company,
				currency: this.pos_profile.currency,
				pos_opening_shift_name: this.pos_opening_shift.name,
				pos_profile_name: this.pos_profile.name,
				pos_profile: this.pos_profile,
				payment_methods: this.payment_methods,
				selected_invoices: this.selected_invoices,
				selected_payments: this.selected_payments,
				total_selected_invoices: this.flt(this.total_selected_invoices),
				selected_mpesa_payments: this.selected_mpesa_payments,
				total_selected_payments: this.flt(this.total_selected_payments),
				total_payment_methods: this.flt(this.total_payment_methods),
				total_selected_mpesa_payments: this.flt(this.total_selected_mpesa_payments),
			};

			if (isOffline()) {
				try {
					saveOfflinePayment({ args: { payload } });
					vm.eventBus.emit("show_message", { title: __("Payment saved offline"), color: "warning" });
					vm.clear_all(false);
					vm.customer_name = customer;
					vm.get_outstanding_invoices();
					vm.get_unallocated_payments();
					vm.set_mpesa_search_params();
					vm.get_draft_mpesa_payments_register();
				} catch (error) {
					frappe.msgprint(__("Cannot Save Offline Payment: ") + (error.message || __("Unknown error")));
				}
				vm.isSubmitting = false;
				return;
			}

			frappe.call({
				method: "posawesome.posawesome.api.payment_entry.process_pos_payment",
				args: { payload },
				freeze: true,
				freeze_message: __("Processing Payment"),
				callback: function (r) {
					vm.isSubmitting = false;
					if (r.message) {
						console.log("Server response:", JSON.stringify(r.message));
						frappe.utils.play_sound("submit");
						const payment_name =
							r.message.new_payments_entry && r.message.new_payments_entry.length > 0
								? r.message.new_payments_entry[0].name
								: null;
						if (payment_name) {
							vm.load_print_page(payment_name);
						} else {
							frappe.msgprint(
								__("Payment submitted but print function could not be executed. Payment name not found."),
							);
						}
						vm.clear_all(false);
						vm.customer_name = customer;
						vm.get_outstanding_invoices();
						vm.get_unallocated_payments();
						vm.set_mpesa_search_params();
						vm.get_draft_mpesa_payments_register();
					}
				},
				error: function () { vm.isSubmitting = false; },
			});
		},
		selectSingleInvoice(item) {
			if (item && item.voucher_no) {
				this.eventBus.emit("set_invoice", item);
				this.$nextTick(() => this.$forceUpdate());
			}
		},
		isInvoiceSelected(item) {
			return this.selected_invoices.some((i) => i.voucher_no === item.voucher_no);
		},
		toggleInvoiceSelection(item) {
			if (this.isInvoiceSelected(item)) {
				this.selected_invoices = this.selected_invoices.filter((i) => i.voucher_no !== item.voucher_no);
			} else {
				this.selected_invoices.push(item);
				if (item.customer && !this.customer_name) {
					this.eventBus.emit("set_customer", item.customer);
				}
			}
			this.$nextTick(() => {
				this.$forceUpdate();
			});
		},
		isSelected(item) {
			return this.isInvoiceSelected(item) ? "selected-row bg-primary bg-lighten-4" : "";
		},
		load_print_page(payment_name) {
			if (!payment_name) {
				frappe.msgprint(__("Payment name not found. Cannot open print view."));
				return;
			}
			const url =
				frappe.urllib.get_base_url() +
				"/printview?doctype=Payment%20Entry" +
				"&name=" +
				payment_name +
				"&trigger_print=1";
			if (this.pos_profile?.posa_silent_print) {
				silentPrint(url);
			} else {
				window.open(url, "_blank");
			}
		},
		async syncPendingPayments() {
			const pending = getPendingOfflinePaymentCount();
			if (pending) {
				this.eventBus.emit("show_message", {
					title: `${pending} payment${pending > 1 ? "s" : ""} pending for sync`,
					color: "warning",
				});
			}
			if (isOffline()) return;
			const result = await syncOfflinePayments();
			if (result && result.synced) {
				this.eventBus.emit("show_message", {
					title: `${result.synced} offline payment${result.synced > 1 ? "s" : ""} synced`,
					color: "success",
				});
			}
		},
	},

	computed: {
		total_outstanding_amount() {
			if (!this.outstanding_invoices || !this.outstanding_invoices.length) return 0;
			return this.outstanding_invoices.reduce((acc, cur) => acc + this.flt(cur?.outstanding_amount || 0), 0);
		},
		total_unallocated_amount() {
			if (!this.unallocated_payments || !this.unallocated_payments.length) return 0;
			return this.unallocated_payments.reduce((acc, cur) => acc + this.flt(cur?.unallocated_amount || 0), 0);
		},
		total_selected_invoices() {
			if (!this.selected_invoices || !this.selected_invoices.length) return 0;
			return this.selected_invoices.reduce((acc, cur) => acc + this.flt(cur?.outstanding_amount || 0), 0);
		},
		total_selected_payments() {
			if (!this.selected_payments || !this.selected_payments.length) return 0;
			return this.selected_payments.reduce((acc, cur) => acc + this.flt(cur?.unallocated_amount || 0), 0);
		},
		total_selected_mpesa_payments() {
			if (!this.selected_mpesa_payments || !this.selected_mpesa_payments.length) return 0;
			return this.selected_mpesa_payments.reduce((acc, cur) => acc + this.flt(cur?.amount || 0), 0);
		},
		total_payment_methods() {
			if (!this.payment_methods || !this.payment_methods.length) return 0;
			const total = this.payment_methods.reduce((acc, cur) => {
				const amount = parseFloat(cur?.amount || 0);
				return acc + (isNaN(amount) ? 0 : amount);
			}, 0);
			return total;
		},
		total_of_diff() {
			const invoiceTotal = this.total_selected_invoices || 0;
			const paymentTotal = (this.total_selected_payments || 0) + (this.total_selected_mpesa_payments || 0) + (this.total_payment_methods || 0);
			return this.flt(invoiceTotal - paymentTotal);
		},
		isDarkTheme() { return this.$theme.current === "dark"; },
	},

	created() {
		this.syncPendingPayments();
		this.eventBus.on("network-online", this.syncPendingPayments);
		this.eventBus.on("server-online", this.syncPendingPayments);
	},

	mounted: function () {
		this.$nextTick(function () {
			this.check_opening_entry();
			this.eventBus.on("update_customer", (customer_name) => {
				this.clear_all(true);
				this.customer_name = customer_name;
				this.fetch_customer_details();
				this.get_outstanding_invoices();
				this.get_unallocated_payments();
				this.get_draft_mpesa_payments_register();
			});
			this.eventBus.on("fetch_customer_details", () => { this.fetch_customer_details(); });
		});
	},
	beforeUnmount() {
		this.eventBus.off("update_customer");
		this.eventBus.off("fetch_customer_details");
		this.eventBus.off("network-online", this.syncPendingPayments);
		this.eventBus.off("server-online", this.syncPendingPayments);
	},
};
</script>

<style>
/* Dark mode input styling */
:deep(.dark-theme) .dark-field,
:deep(.v-theme--dark) .dark-field,
::v-deep(.dark-theme) .dark-field,
::v-deep(.v-theme--dark) .dark-field {
	background-color: #1e1e1e !important;
}

:deep(.dark-theme) .dark-field :deep(.v-field__input),
:deep(.v-theme--dark) .dark-field :deep(.v-field__input),
:deep(.dark-theme) .dark-field :deep(input),
:deep(.v-theme--dark) .dark-field :deep(input),
:deep(.dark-theme) .dark-field :deep(.v-label),
:deep(.v-theme--dark) .dark-field :deep(.v-label),
::v-deep(.dark-theme) .dark-field .v-field__input,
::v-deep(.v-theme--dark) .dark-field .v-field__input,
::v-deep(.dark-theme) .dark-field input,
::v-deep(.v-theme--dark) .dark-field input,
::v-deep(.dark-theme) .dark-field .v-label,
::v-deep(.v-theme--dark) .dark-field .v-label {
	color: #fff !important;
}

:deep(.dark-theme) .dark-field :deep(.v-field__overlay),
:deep(.v-theme--dark) .dark-field :deep(.v-field__overlay),
::v-deep(.dark-theme) .dark-field .v-field__overlay,
::v-deep(.v-theme--dark) .dark-field .v-field__overlay {
	background-color: #1e1e1e !important;
}

input[total_of_diff] { text-align: right; }
input[payments_methods] { text-align: right; }
input[total_selected_payments] { text-align: right; }
input[total_selected_invoices] { text-align: right; }
input[total_selected_mpesa_payments] { text-align: right; }

.selected-row { background-color: #e3f2fd !important; }

/* Standard Button Styling - matching InvoiceSummary.vue */
.standard-btn {
    min-height: 60px !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    text-transform: none;
    margin: 1px;
    border-radius: 6px;
    padding: 6px 8px !important;
    white-space: nowrap !important;
}

/* Section Header Styling */
.section-header {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    border: 1px solid #e0e0e0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Dark theme for section header */
:deep(.dark-theme) .section-header,
:deep(.v-theme--dark) .section-header {
    background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
    border-color: #333;
    color: #fff;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .standard-btn {
        min-height: 50px !important;
        font-size: 1.1rem !important;
        padding: 4px 6px !important;
    }

    .section-header {
        padding: 12px;
        margin-bottom: 12px;
    }
}

@media (max-width: 480px) {
    .standard-btn {
        min-height: 48px !important;
        font-size: 1.0rem !important;
        padding: 4px 6px !important;
    }

    .section-header {
        padding: 8px;
        margin-bottom: 8px;
    }
}
</style>
