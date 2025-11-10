<template>
	<div class="pos-main-container dynamic-container" :style="responsiveStyles">
		<ClosingShiftNew
			v-model="showClosingShiftDialog"
			:shift-report-id="pos_shift_report || pos_opening_shift"
			:pos-profile="pos_profile"
		></ClosingShiftNew>
		<Drafts></Drafts>
		<SalesOrders></SalesOrders>
		<Returns></Returns>
		<NewAddress></NewAddress>
		<MpesaPayments></MpesaPayments>
		<Variants></Variants>
		<TaxRollDialog></TaxRollDialog>
		<ListInvoicesDialog
			v-model="showListInvoicesDialog"
			:shift-report-id="pos_shift_report || pos_opening_shift"
			:pos-profile="pos_profile"
		></ListInvoicesDialog>
		<ListShiftsDialog v-model="showListShiftsDialog" :pos-profile="pos_profile"></ListShiftsDialog>
		<OpeningDialog v-if="dialog" :dialog="dialog"></OpeningDialog>
		<v-row v-show="!dialog" dense class="ma-0 dynamic-main-row">
			<v-col
				v-show="!payment && !offers && !coupons"
				xl="5"
				lg="5"
				md="5"
				sm="5"
				cols="12"
				class="pos dynamic-col"
			>
				<ItemsSelector></ItemsSelector>
			</v-col>
			<v-col v-show="offers" xl="5" lg="5" md="5" sm="5" cols="12" class="pos dynamic-col">
				<PosOffers></PosOffers>
			</v-col>
			<v-col v-show="coupons" xl="5" lg="5" md="5" sm="5" cols="12" class="pos dynamic-col">
				<PosCoupons></PosCoupons>
			</v-col>
			<v-col v-show="payment" xl="5" lg="5" md="5" sm="5" cols="12" class="pos dynamic-col">
				<Payments></Payments>
			</v-col>

			<v-col xl="7" lg="7" md="7" sm="7" cols="12" class="pos dynamic-col">
				<Invoice :shiftVerificationStatus="shift_report_data.verification_status"></Invoice>
			</v-col>
		</v-row>
	</div>
</template>

<script>
import ItemsSelector from "./ItemsSelector.vue";
import Invoice from "./Invoice.vue";
import OpeningDialog from "./OpeningDialog.vue";
import Payments from "./Payments.vue";
import PosOffers from "./PosOffers.vue";
import PosCoupons from "./PosCoupons.vue";
import Drafts from "./Drafts.vue";
import SalesOrders from "./SalesOrders.vue";
import ClosingShiftNew from "./ClosingShiftNew.vue";
import NewAddress from "./NewAddress.vue";
import Variants from "./Variants.vue";
import Returns from "./Returns.vue";
import MpesaPayments from "./Mpesa-Payments.vue";
import TaxRollDialog from "./TaxRollDialog.vue";
import ListInvoicesDialog from "./ListInvoicesDialog.vue";
import ListShiftsDialog from "./ListShiftsDialog.vue";
import {
	getCachedOffers,
	saveOffers,
	getOpeningStorage,
	setOpeningStorage,
	clearOpeningStorage,
	initPromise,
	checkDbHealth,
	setTaxTemplate,
} from "../../../offline/index.js";
// Import the cache cleanup function
import { clearExpiredCustomerBalances } from "../../../offline/index.js";
import { responsiveMixin } from "../../mixins/responsive.js";

export default {
	mixins: [responsiveMixin],
	data: function () {
		return {
			dialog: false,
			pos_profile: "",
			pos_opening_shift: "",
			pos_shift_report: "",
			shift_report_data: {},
			payment: false,
			offers: false,
			coupons: false,
			showListInvoicesDialog: false,
			showListShiftsDialog: false,
			showClosingShiftDialog: false,
			// Loading states
			loading: false,
			submitting_closing: false,
			// Error handling
			last_error: null,
		};
	},

	components: {
		ItemsSelector,
		Invoice,
		OpeningDialog,
		Payments,
		Drafts,
		ClosingShiftNew,

		Returns,
		PosOffers,
		PosCoupons,
		NewAddress,
		Variants,
		MpesaPayments,
		SalesOrders,
		TaxRollDialog,
		ListInvoicesDialog,
		ListShiftsDialog,
	},

	methods: {
		async check_opening_entry() {
			await initPromise;
			await checkDbHealth();
			return frappe.call({
				method: "posawesome.posawesome.api.shifts.check_opening_shift",
				args: {
					user: frappe.session.user,
				},
				callback: (r) => {
					if (r.message) {
						this.pos_profile = r.message.pos_profile;
						this.pos_opening_shift = r.message.pos_opening_shift;
						this.get_offers(this.pos_profile.name);

						// Load Shift Report data nếu có
						if (r.message.pos_opening_shift && r.message.pos_opening_shift.shift_report) {
							console.info(
								"Found shift report in opening shift:",
								r.message.pos_opening_shift.shift_report,
							);
							this.pos_shift_report = r.message.pos_opening_shift.shift_report;
							this.load_shift_report_data();
						} else {
							console.warn("No shift report found in opening shift data");
						}
						if (this.pos_profile.taxes_and_charges) {
							frappe.call({
								method: "frappe.client.get",
								args: {
									doctype: "Sales Taxes and Charges Template",
									name: this.pos_profile.taxes_and_charges,
								},
								callback: (res) => {
									if (res.message) {
										setTaxTemplate(this.pos_profile.taxes_and_charges, res.message);
									}
								},
							});
						}
						this.eventBus.emit("register_pos_profile", r.message);
						this.eventBus.emit("set_company", r.message.company);
						try {
							frappe.realtime.emit("pos_profile_registered");
						} catch (e) {
							console.warn("Realtime emit failed", e);
						}
						console.info("LoadPosProfile");
						try {
							setOpeningStorage(r.message);
						} catch (e) {
							console.error("Failed to cache opening data", e);
						}
					} else {
						const data = getOpeningStorage();
						if (data) {
							this.pos_profile = data.pos_profile;
							this.pos_opening_shift = data.pos_opening_shift;
							this.get_offers(this.pos_profile.name);
							this.eventBus.emit("register_pos_profile", data);
							this.eventBus.emit("set_company", data.company);
							try {
								frappe.realtime.emit("pos_profile_registered");
							} catch (e) {
								console.warn("Realtime emit failed", e);
							}
							console.info("LoadPosProfile (cached)");
							return;
						}
						this.create_opening_voucher();
					}
				},
				error: (error) => {
					console.error("Failed to check opening entry:", error);

					// Hiển thị cảnh báo nếu có lỗi nghiêm trọng
					if (error && error.message && error.message.includes("Critical Error")) {
						if (window.frappe && frappe.show_alert) {
							frappe.show_alert({
								message: error.message,
								indicator: "red",
							});
						} else {
							alert(error.message);
						}
					}

					const data = getOpeningStorage();
					if (data) {
						this.pos_profile = data.pos_profile;
						this.pos_opening_shift = data.pos_opening_shift;
						this.get_offers(this.pos_profile.name);
						this.eventBus.emit("register_pos_profile", data);
						this.eventBus.emit("set_company", data.company);
						try {
							frappe.realtime.emit("pos_profile_registered");
						} catch (e) {
							console.warn("Realtime emit failed", e);
						}
						console.info("LoadPosProfile (cached)");
						return;
					}
					this.create_opening_voucher();
				},
			});
		},
		create_opening_voucher() {
			this.dialog = true;
		},

		clearBrowserCache() {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Clear Browser Cache Start
			console.log(
				`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE_START - Clearing browser cache and storage`,
			);

			try {
				// Clear localStorage
				localStorage.clear();
				console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Cleared localStorage`);

				// Clear sessionStorage
				sessionStorage.clear();
				console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Cleared sessionStorage`);

				// Clear IndexedDB databases (if any POS-related)
				if (window.indexedDB) {
					// Clear specific POS databases
					const dbNames = ["pos_offline_db", "pos_cache", "posawesome_offline"];
					dbNames.forEach((dbName) => {
						try {
							const deleteRequest = window.indexedDB.deleteDatabase(dbName);
							deleteRequest.onsuccess = () => {
								console.log(
									`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Cleared IndexedDB: ${dbName}`,
								);
							};
							deleteRequest.onerror = () => {
								console.warn(
									`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Failed to clear IndexedDB: ${dbName}`,
								);
							};
						} catch (e) {
							console.warn(
								`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Error clearing IndexedDB ${dbName}:`,
								e,
							);
						}
					});
				}

				// Clear cache storage (if supported)
				if ("caches" in window) {
					caches
						.keys()
						.then((names) => {
							names.forEach((name) => {
								caches.delete(name);
								console.log(
									`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Cleared cache: ${name}`,
								);
							});
						})
						.catch((e) => {
							console.warn(
								`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Error clearing caches:`,
								e,
							);
						});
				}

				console.log(
					`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE_COMPLETED - Browser cache cleared successfully`,
				);
			} catch (error) {
				console.error(
					`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE_ERROR - Error clearing browser cache:`,
					error,
				);
			}
		},

		performLogout() {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Perform Logout Start
			console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_START - Performing user logout`);

			try {
				// Use Frappe's logout mechanism if available
				if (window.frappe && frappe.app) {
					console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT - Using frappe.app.logout()`);
					frappe.app.logout();
				} else if (window.frappe && frappe.call) {
					// Fallback: Call logout API
					console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT - Using frappe.call logout API`);
					frappe.call({
						method: "logout",
						callback: () => {
							console.log(
								`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT - Logout API called successfully`,
							);
						},
					});
				} else {
					// Last resort: Redirect to login page
					console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT - Redirecting to login page`);
					window.location.href = "/login";
				}

				console.log(
					`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_COMPLETED - Logout initiated successfully`,
				);
			} catch (error) {
				console.error(
					`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_ERROR - Error performing logout:`,
					error,
				);

				// Fallback: Force redirect to login
				console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_FALLBACK - Force redirect to login`);
				window.location.href = "/login";
			}
		},
		get_offers(pos_profile) {
			// Load cached offers if available
			if (this.pos_profile && this.pos_profile.posa_local_storage) {
				const cached = getCachedOffers();
				if (cached.length) {
					this.eventBus.emit("set_offers", cached);
				}
			}

			return frappe.call({
				method: "posawesome.posawesome.api.offers.get_offers",
				args: {
					profile: pos_profile,
				},
				callback: (r) => {
					if (r.message) {
						console.info("LoadOffers");
						saveOffers(r.message);
						this.eventBus.emit("set_offers", r.message);
					}
				},
				error: (err) => {
					console.error("Failed to fetch offers:", err);
					const cached = getCachedOffers();
					if (cached.length) {
						this.eventBus.emit("set_offers", cached);
					}
				},
			});
		},
		get_pos_setting() {
			frappe.db.get_doc("POS Settings", undefined).then((doc) => {
				this.eventBus.emit("set_pos_settings", doc);
			});
		},

		load_shift_report_data() {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Load Shift Report Data Start
			console.log(
				`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_START - Shift report: ${this.pos_shift_report}, User: ${frappe.session.user}`,
			);

			if (!this.pos_shift_report) {
				console.warn(
					`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_WARNING - No shift report ID to load`,
				);
				return;
			}

			const startTime = Date.now();

			frappe.call({
				method: "posawesome.posawesome.api.shift_reports.get_shift_report",
				args: {
					shift_report_id: this.pos_shift_report,
				},
				callback: (r) => {
					const processingTime = Date.now() - startTime;

					if (r.message && r.message.success) {
						this.shift_report_data = r.message.data;
						this.eventBus.emit("register_shift_report", this.shift_report_data);
						console.log(
							`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_SUCCESS - Shift Report data loaded successfully - Processing time: ${processingTime}ms`,
						);
					} else {
						console.error(
							`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_ERROR - API returned unsuccessful response - Processing time: ${processingTime}ms - Response:`,
							r.message,
						);
					}
				},
				error: (err) => {
					const processingTime = Date.now() - startTime;

					console.error(
						`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_ERROR - Failed to load shift report data - Processing time: ${processingTime}ms - Error:`,
						err,
					);

					// Hiển thị cảnh báo nếu load shift report thất bại
					if (window.frappe && frappe.show_alert) {
						frappe.show_alert({
							message: __(
								"Warning: Failed to load Shift Report data. Some features may not work properly.",
							),
							indicator: "orange",
						});
					}
				},
			});
		},
	},

	mounted: function () {
		this.$nextTick(function () {
			this.check_opening_entry();
			this.get_pos_setting();
			this.eventBus.on("close_opening_dialog", () => {
				this.dialog = false;
			});
			this.eventBus.on("register_pos_data", (data) => {
				this.pos_profile = data.pos_profile;
				this.get_offers(this.pos_profile.name);
				this.pos_opening_shift = data.pos_opening_shift;
				this.eventBus.emit("register_pos_profile", data);
				console.info("LoadPosProfile");
			});

			this.eventBus.on("register_shift_report", (shift_report_data) => {
				this.pos_shift_report = shift_report_data.name;
				this.shift_report_data = shift_report_data;
				console.info("Shift Report registered:", shift_report_data);
			});
			this.eventBus.on("show_payment", (data) => {
				this.payment = true ? data === "true" : false;
				this.offers = false ? data === "true" : false;
				this.coupons = false ? data === "true" : false;
			});
			this.eventBus.on("show_offers", (data) => {
				console.log("🎯 [POS_MAIN] Received 'show_offers' event with data:", data);
				console.log(
					"🎯 [POS_MAIN] Previous state - offers:",
					this.offers,
					"payment:",
					this.payment,
					"coupons:",
					this.coupons,
				);

				this.offers = true ? data === "true" : false;
				this.payment = false ? data === "true" : false;
				this.coupons = false ? data === "true" : false;

				console.log(
					"🎯 [POS_MAIN] New state - offers:",
					this.offers,
					"payment:",
					this.payment,
					"coupons:",
					this.coupons,
				);
				console.log("🎯 [POS_MAIN] PosOffers component should now be visible:", this.offers);
			});
			this.eventBus.on("show_coupons", (data) => {
				this.coupons = true ? data === "true" : false;
				this.offers = false ? data === "true" : false;
				this.payment = false ? data === "true" : false;
			});
			this.eventBus.on("open_closing_dialog", () => {
				this.showClosingShiftDialog = true;
			});
			this.eventBus.on("open_list_invoices", () => {
				this.showListInvoicesDialog = true;
			});
			this.eventBus.on("open_list_shifts", () => {
				this.showListShiftsDialog = true;
			});
			this.eventBus.on("shift_closed_success", () => {
				// Clear the cached opening shift data
				this.pos_opening_shift = null;
				this.pos_profile = null;
				this.pos_shift_report = null;
				this.shift_report_data = {};

				// Clear from local storage
				clearOpeningStorage();

				this.eventBus.emit("show_message", {
					title: __("POS Shift Closed Successfully"),
					color: "success",
				});
			});
		});
	},
	beforeUnmount() {
		this.eventBus.off("close_opening_dialog");
		this.eventBus.off("register_pos_data");
		this.eventBus.off("register_shift_report");
		this.eventBus.off("LoadPosProfile");
		this.eventBus.off("show_offers");
		this.eventBus.off("show_coupons");
		this.eventBus.off("open_closing_dialog");
		this.eventBus.off("open_list_invoices");
		this.eventBus.off("open_list_shifts");
		this.eventBus.off("shift_closed_success");
	},
	// In the created() or mounted() lifecycle hook
	created() {
		// Clean up expired customer balance cache on POS load
		clearExpiredCustomerBalances();
	},
};
</script>

<style scoped>
.dynamic-container {
	/* add space for the navbar with better spacing */
	padding-top: calc(2px + var(--dynamic-lg));
	/* Navbar height (25px) + larger spacing */
	transition: all 0.3s ease;
}

.dynamic-main-row {
	padding: 0;
	margin: 0;
}

.dynamic-col {
	padding: var(--dynamic-sm);
	transition: padding 0.3s ease;
	margin-top: var(--dynamic-sm);
	/* Add top margin for better separation */
}

@media (max-width: 768px) {
	.dynamic-container {
		padding-top: calc(26px + var(--dynamic-md));
		/* Consistent navbar height + medium spacing */
	}

	.dynamic-col {
		padding: var(--dynamic-xs);
		margin-top: var(--dynamic-xs);
	}
}
</style>
