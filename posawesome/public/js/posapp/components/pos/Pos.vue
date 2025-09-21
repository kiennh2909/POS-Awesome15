<template>
	<div class="pos-main-container dynamic-container" :style="responsiveStyles">
		<ClosingDialog></ClosingDialog>
		<Drafts></Drafts>
		<SalesOrders></SalesOrders>
		<Returns></Returns>
		<NewAddress></NewAddress>
		<MpesaPayments></MpesaPayments>
		<Variants></Variants>
		<TaxRollDialog></TaxRollDialog>
		<ListInvoicesDialog
			v-model="showListInvoicesDialog"
			:shift-report-id="pos_opening_shift"
			:pos-profile="pos_profile"
		></ListInvoicesDialog>
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
import ClosingDialog from "./ClosingDialog.vue";
import NewAddress from "./NewAddress.vue";
import Variants from "./Variants.vue";
import Returns from "./Returns.vue";
import MpesaPayments from "./Mpesa-Payments.vue";
import TaxRollDialog from "./TaxRollDialog.vue";
import ListInvoicesDialog from "./ListInvoicesDialog.vue";
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
		ClosingDialog,

		Returns,
		PosOffers,
		PosCoupons,
		NewAddress,
		Variants,
		MpesaPayments,
		SalesOrders,
		TaxRollDialog,
		ListInvoicesDialog,
	},

	methods: {
		async check_opening_entry() {
			await initPromise;
			await checkDbHealth();
			return frappe
				.call("posawesome.posawesome.api.shifts.check_opening_shift", {
					user: frappe.session.user,
				})
				.then((r) => {
					if (r.message) {
						this.pos_profile = r.message.pos_profile;
						this.pos_opening_shift = r.message.pos_opening_shift;
						this.get_offers(this.pos_profile.name);

						// Load Shift Report data nếu có
						if (r.message.pos_opening_shift && r.message.pos_opening_shift.shift_report) {
							console.info("Found shift report in opening shift:", r.message.pos_opening_shift.shift_report);
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
				})
				.catch((error) => {
					console.error("Failed to check opening entry:", error);

					// Hiển thị cảnh báo nếu có lỗi nghiêm trọng
					if (error && error.message && error.message.includes("Critical Error")) {
						if (window.frappe && frappe.show_alert) {
							frappe.show_alert({
								message: error.message,
								indicator: 'red'
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
				});
		},
		create_opening_voucher() {
			this.dialog = true;
		},
		get_closing_data() {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Get Closing Data Start
			console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_GET_CLOSING_DATA_START - Opening shift: ${this.pos_opening_shift}, User: ${frappe.session.user}`);

			// Validate opening shift exists
			if (!this.pos_opening_shift) {
				console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_GET_CLOSING_DATA_ERROR - No active opening shift found`);
				this.eventBus.emit("show_message", {
					title: __("No active opening shift found"),
					color: "error",
				});
				return;
			}

			// Set loading state
			this.loading = true;

			// Show loading message
			this.eventBus.emit("show_message", {
				title: __("Loading closing shift data..."),
				color: "blue",
			});

			const startTime = Date.now();

			return frappe
				.call(
					"posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.make_closing_shift_from_opening",
					{
						opening_shift: this.pos_opening_shift,
					},
				)
				.then((r) => {
					const processingTime = Date.now() - startTime;

					if (r.message) {
						console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_GET_CLOSING_DATA_SUCCESS - Closing shift data loaded successfully - Processing time: ${processingTime}ms`);
						this.eventBus.emit("open_ClosingDialog", r.message);
						this.eventBus.emit("show_message", {
							title: __("Closing shift data loaded"),
							color: "success",
						});
					} else {
						console.warn(`[SHIFT_CLOSE_WORKFLOW] VUE_GET_CLOSING_DATA_WARNING - No closing shift data received - Processing time: ${processingTime}ms`);
						this.eventBus.emit("show_message", {
							title: __("No closing shift data received"),
							color: "warning",
						});
					}
				})
				.catch((error) => {
					const processingTime = Date.now() - startTime;
					const error_message = error.message || __("Failed to load closing shift data");

					console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_GET_CLOSING_DATA_ERROR - Failed to load closing shift data - Processing time: ${processingTime}ms - Error:`, error);

					this.eventBus.emit("show_message", {
						title: error_message,
						color: "error",
					});
				})
				.finally(() => {
					this.loading = false;
				});
		},
		submit_closing_pos(data) {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Submit Closing POS Start
			console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_CLOSING_POS_START - Opening shift: ${data?.pos_opening_shift}, User: ${frappe.session.user}`);

			// Validate input data
			if (!data || !data.pos_opening_shift) {
				console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_CLOSING_POS_ERROR - Invalid closing shift data`);
				this.eventBus.emit("show_message", {
					title: __("Invalid closing shift data"),
					color: "error",
				});
				return;
			}

			// Set loading state
			this.submitting_closing = true;
			this.last_error = null;

			// Show loading message
			this.eventBus.emit("show_message", {
				title: __("Submitting closing shift..."),
				color: "blue",
			});

			const startTime = Date.now();

			frappe
				.call(
					"posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.submit_closing_shift",
					{
						closing_shift: JSON.stringify(data),
					},
				)
				.then((r) => {
					const processingTime = Date.now() - startTime;

					if (r.message && r.message.success) {
						console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_CLOSING_POS_SUCCESS - POS Shift closed successfully - Processing time: ${processingTime}ms - Request ID: ${r.message.request_id}`);

						// Success handling
						this.last_error = null;

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

						// Emit success event for UI refresh and cache clearing
						this.eventBus.emit("shift_closed_success");

						// Handle post-submit cleanup from backend response
						console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP_START - Processing backend response data:`, r.message.data);

						if (r.message.data) {
							const responseData = r.message.data;
							console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP_DATA - Response data keys:`, Object.keys(responseData));

							// Check if backend requires logout
							if (responseData.requires_logout) {
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - ✅ Backend requires logout: ${responseData.requires_logout}`);
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - 🔄 Starting browser cache clearing...`);

								// Clear browser cache/storage
								this.clearBrowserCache();

								// Logout user after a short delay
								setTimeout(() => {
									console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - 🚪 Performing logout after 1.5s delay`);
									this.performLogout();
								}, 1500);
							} else {
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - ❌ Backend does NOT require logout: ${responseData.requires_logout}`);
							}

							// Check if backend requires UI refresh
							if (responseData.requires_ui_refresh) {
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - ✅ Backend requires UI refresh: ${responseData.requires_ui_refresh}`);

								// Refresh page after logout delay
								setTimeout(() => {
									console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - 🔄 Refreshing page after 2s delay`);
									window.location.reload();
								}, 2000);
							} else {
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP - ❌ Backend does NOT require UI refresh: ${responseData.requires_ui_refresh}`);
							}

							console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP_COMPLETED - Post-submit cleanup flags processed`);

						} else {
							console.warn(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP_NO_DATA - No response data received, using fallback`);
							// Fallback: Reload opening entry after a short delay
							setTimeout(() => {
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_POST_SUBMIT_CLEANUP_FALLBACK - Reloading opening entry after 1s delay`);
								this.check_opening_entry();
							}, 1000);
						}

					} else {
						// Handle API error response
						const error_message = r.message?.message || __("Failed to close POS shift");
						this.last_error = error_message;

						console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_CLOSING_POS_ERROR - API returned unsuccessful response - Processing time: ${processingTime}ms - Error:`, r.message);

						this.eventBus.emit("show_message", {
							title: error_message,
							color: "error",
						});
					}
				})
				.catch((error) => {
					const processingTime = Date.now() - startTime;

					// Handle network/other errors
					const error_message = error.message || __("Network error while closing shift");
					this.last_error = error_message;

					console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_SUBMIT_CLOSING_POS_ERROR - Network error while closing shift - Processing time: ${processingTime}ms - Error:`, error);

					this.eventBus.emit("show_message", {
						title: error_message,
						color: "error",
					});
				})
				.finally(() => {
					// Always clear loading state
					this.submitting_closing = false;
				});
		},

		clearBrowserCache() {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Clear Browser Cache Start
			console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE_START - Clearing browser cache and storage`);

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
					const dbNames = ['pos_offline_db', 'pos_cache', 'posawesome_offline'];
					dbNames.forEach(dbName => {
						try {
							const deleteRequest = window.indexedDB.deleteDatabase(dbName);
							deleteRequest.onsuccess = () => {
								console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Cleared IndexedDB: ${dbName}`);
							};
							deleteRequest.onerror = () => {
								console.warn(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Failed to clear IndexedDB: ${dbName}`);
							};
						} catch (e) {
							console.warn(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Error clearing IndexedDB ${dbName}:`, e);
						}
					});
				}

				// Clear cache storage (if supported)
				if ('caches' in window) {
					caches.keys().then(names => {
						names.forEach(name => {
							caches.delete(name);
							console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Cleared cache: ${name}`);
						});
					}).catch(e => {
						console.warn(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE - Error clearing caches:`, e);
					});
				}

				console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE_COMPLETED - Browser cache cleared successfully`);

			} catch (error) {
				console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_CLEAR_BROWSER_CACHE_ERROR - Error clearing browser cache:`, error);
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
							console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT - Logout API called successfully`);
						}
					});
				} else {
					// Last resort: Redirect to login page
					console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT - Redirecting to login page`);
					window.location.href = '/login';
				}

				console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_COMPLETED - Logout initiated successfully`);

			} catch (error) {
				console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_ERROR - Error performing logout:`, error);

				// Fallback: Force redirect to login
				console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_PERFORM_LOGOUT_FALLBACK - Force redirect to login`);
				window.location.href = '/login';
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

			return frappe
				.call("posawesome.posawesome.api.offers.get_offers", {
					profile: pos_profile,
				})
				.then((r) => {
					if (r.message) {
						console.info("LoadOffers");
						saveOffers(r.message);
						this.eventBus.emit("set_offers", r.message);
					}
				})
				.catch((err) => {
					console.error("Failed to fetch offers:", err);
					const cached = getCachedOffers();
					if (cached.length) {
						this.eventBus.emit("set_offers", cached);
					}
				});
		},
		get_pos_setting() {
			frappe.db.get_doc("POS Settings", undefined).then((doc) => {
				this.eventBus.emit("set_pos_settings", doc);
			});
		},

		load_shift_report_data() {
			// [SHIFT_CLOSE_WORKFLOW] Vue Component - Load Shift Report Data Start
			console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_START - Shift report: ${this.pos_shift_report}, User: ${frappe.session.user}`);

			if (!this.pos_shift_report) {
				console.warn(`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_WARNING - No shift report ID to load`);
				return;
			}

			const startTime = Date.now();

			frappe.call("posawesome.posawesome.api.shift_reports.get_shift_report", {
				shift_report_id: this.pos_shift_report
			}).then((r) => {
				const processingTime = Date.now() - startTime;

				if (r.message && r.message.success) {
					this.shift_report_data = r.message.data;
					this.eventBus.emit("register_shift_report", this.shift_report_data);
					console.log(`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_SUCCESS - Shift Report data loaded successfully - Processing time: ${processingTime}ms`);
				} else {
					console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_ERROR - API returned unsuccessful response - Processing time: ${processingTime}ms - Response:`, r.message);
				}
			}).catch((err) => {
				const processingTime = Date.now() - startTime;

				console.error(`[SHIFT_CLOSE_WORKFLOW] VUE_LOAD_SHIFT_REPORT_ERROR - Failed to load shift report data - Processing time: ${processingTime}ms - Error:`, err);

				// Hiển thị cảnh báo nếu load shift report thất bại
				if (window.frappe && frappe.show_alert) {
					frappe.show_alert({
						message: __("Warning: Failed to load Shift Report data. Some features may not work properly."),
						indicator: 'orange'
					});
				}
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
				this.offers = true ? data === "true" : false;
				this.payment = false ? data === "true" : false;
				this.coupons = false ? data === "true" : false;
			});
			this.eventBus.on("show_coupons", (data) => {
				this.coupons = true ? data === "true" : false;
				this.offers = false ? data === "true" : false;
				this.payment = false ? data === "true" : false;
			});
			this.eventBus.on("open_closing_dialog", () => {
				this.get_closing_data();
			});
			this.eventBus.on("submit_closing_pos", (data) => {
				this.submit_closing_pos(data);
			});
			this.eventBus.on("open_list_invoices", () => {
				this.showListInvoicesDialog = true;
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
		this.eventBus.off("submit_closing_pos");
		this.eventBus.off("open_list_invoices");
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
