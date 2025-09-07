<template>
	<nav>
		<!-- Use the modular NavbarAppBar component -->
		<NavbarAppBar
			:pos-profile="posProfile"
			:pending-invoices="pendingInvoices"
			:is-dark="isDark"
			@nav-click="handleNavClick"
			@go-desk="goDesk"
			@show-offline-invoices="showOfflineInvoices = true"
		>
			<!-- Slot for status indicator -->
			<template #status-indicator>
				<StatusIndicator
					:network-online="networkOnline"
					:server-online="serverOnline"
					:server-connecting="serverConnecting"
					:is-ip-host="isIpHost"
					:sync-totals="syncTotals"
				/>
			</template>

			<!-- Slot for cache usage meter -->
			<template #cache-usage-meter>
				<CacheUsageMeter
					:cache-usage="cacheUsage"
					:cache-usage-loading="cacheUsageLoading"
					:cache-usage-details="cacheUsageDetails"
					@refresh="refreshCacheUsage"
				/>
			</template>

			<!-- Slot for menu -->
			<template #menu>
				<NavbarMenu
					:pos-profile="posProfile"
					:last-invoice-id="lastInvoiceId"
					:manual-offline="manualOffline"
					:network-online="networkOnline"
					:server-online="serverOnline"
					:is-dark="isDark"
					:is-fullscreen="isFullscreen"
					@close-shift="openCloseShift"
					@print-last-invoice="printLastInvoice"
					@sync-invoices="syncPendingInvoices"
					@toggle-offline="toggleManualOffline"
					@clear-cache="clearCache"
					@show-about="showAboutDialog = true"
					@toggle-theme="toggleTheme"
					@toggle-fullscreen="toggleFullscreen"
					@logout="logOut"
				/>
			</template>
		</NavbarAppBar>

		<!-- Use the modular NavbarDrawer component -->
		<NavbarDrawer
			v-model:drawer="drawer"
			v-model:item="item"
			:company="company"
			:company-img="companyImg"
			:items="items"
			:is-dark="isDark"
			@change-page="changePage"
		/>

		<!-- Use the modular AboutDialog component -->
		<AboutDialog v-model="showAboutDialog" />

		<!-- Keep existing dialogs -->
		<v-dialog v-model="freeze" persistent max-width="290">
			<v-card>
				<v-card-title class="text-h5">{{ freezeTitle }}</v-card-title>
				<v-card-text>{{ freezeMsg }}</v-card-text>
			</v-card>
		</v-dialog>

		<OfflineInvoicesDialog
			v-model="showOfflineInvoices"
			:pos-profile="posProfile"
			@deleted="updateAfterDelete"
			@sync-all="syncPendingInvoices"
		/>

		<!-- Offer Notification Dialog -->
		<v-dialog v-model="snack" max-width="500" persistent>
			<v-card class="offer-dialog-card">
				<v-card-title class="offer-header pa-5">
					<div class="header-content">
						<div class="header-icon-wrapper">
							<v-icon size="24" class="header-icon">mdi-gift</v-icon>
						</div>
						<div class="header-text">
							<h3 class="header-title">{{ __("Thông báo !") }}</h3>
							<p class="header-subtitle">{{ __("Nội dung chi tiết") }}</p>
						</div>
					</div>
					<v-btn
						icon="mdi-close"
						variant="text"
						size="default"
						@click="snack = false"
						class="close-btn"
					></v-btn>
				</v-card-title>

				<v-card-text class="pa-0">
					<div class="offer-content-container">
						<div
							v-html="snackText"
							class="offer-notification-content"
						></div>
					</div>
				</v-card-text>

				<v-card-actions class="offer-actions pa-4">
					<v-spacer></v-spacer>
					<v-btn
						color="black"
						variant="tonal"
						@click="snack = false"
						class="offer-close-action-btn"
					>
						{{ __("Close") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</nav>
</template>

<script>
import NavbarAppBar from "./navbar/NavbarAppBar.vue";
import NavbarDrawer from "./navbar/NavbarDrawer.vue";
import NavbarMenu from "./navbar/NavbarMenu.vue";
import StatusIndicator from "./navbar/StatusIndicator.vue";
import CacheUsageMeter from "./navbar/CacheUsageMeter.vue";
import AboutDialog from "./navbar/AboutDialog.vue";
import OfflineInvoices from "./OfflineInvoices.vue";
import { forceClearAllCache } from "../../offline/cache.js";
import { clearAllCaches } from "../../utils/clearAllCaches.js";
import { isOffline } from "../../offline/index.js";

export default {
	name: "NavBar",
	components: {
		NavbarAppBar,
		NavbarDrawer,
		NavbarMenu,
		StatusIndicator,
		CacheUsageMeter,
		AboutDialog,
		OfflineInvoicesDialog: OfflineInvoices,
	},
	props: {
		posProfile: {
			type: Object,
			default: () => ({}),
		},
		pendingInvoices: {
			type: Number,
			default: 0,
		},
		lastInvoiceId: String,
		networkOnline: Boolean,
		serverOnline: Boolean,
		serverConnecting: Boolean,
		isIpHost: Boolean,
		syncTotals: {
			type: Object,
			default: () => ({ pending: 0, synced: 0, drafted: 0 }),
		},
		manualOffline: Boolean,
		isDark: Boolean,
		cacheUsage: {
			type: Number,
			default: 0,
		},
		cacheUsageLoading: {
			type: Boolean,
			default: false,
		},
		cacheUsageDetails: {
			type: Object,
			default: () => ({ total: 0, indexedDB: 0, localStorage: 0 }),
		},
	},
	data() {
		return {
			drawer: false,
			mini: true,
			item: 0,
			items: [
				{ text: "POS", icon: "mdi-network-pos" },
				{ text: "Payments", icon: "mdi-credit-card" },
			],
			company: "POS Awesome",
			companyImg: "/assets/posawesome/js/posapp/components/pos/pos.png",
			showAboutDialog: false,
			showOfflineInvoices: false,
			freeze: false,
			freezeTitle: "",
			freezeMsg: "",
			snack: false,
			snackText: "",
			snackColor: "success",
			snackTimeout: 3000,
			isFullscreen: false,
		};
	},
	computed: {
		appBarColor() {
			return this.isDark ? this.$vuetify.theme.themes.dark.colors.surface : "white";
		},
	},
	mounted() {
		this.initializeNavbar();

		// Listen for fullscreen changes
		document.addEventListener('fullscreenchange', () => {
			this.isFullscreen = !!document.fullscreenElement;
		});

		if (this.eventBus) {
			this.eventBus.on("show_message", this.showMessage);
			this.eventBus.on("freeze", this.handleFreeze);
			this.eventBus.on("unfreeze", this.handleUnfreeze);
			this.eventBus.on("set_company", this.handleSetCompany);
		}
	},
	unmounted() {
		// Remove fullscreen event listener
		document.removeEventListener('fullscreenchange', () => {
			this.isFullscreen = !!document.fullscreenElement;
		});

		if (this.eventBus) {
			this.eventBus.off("show_message", this.showMessage);
			this.eventBus.off("freeze", this.handleFreeze);
			this.eventBus.off("unfreeze", this.handleUnfreeze);
			this.eventBus.off("set_company", this.handleSetCompany);
		}
	},
	methods: {
		initializeNavbar() {
			// Initialize company info from Frappe boot data
			if (frappe.boot && frappe.boot.sysdefaults && frappe.boot.sysdefaults.company) {
				this.company = frappe.boot.sysdefaults.company;
			}

			// Try multiple sources for company logo
			if (frappe.boot && frappe.boot.website_settings && frappe.boot.website_settings.app_logo) {
				this.companyImg = frappe.boot.website_settings.app_logo;
			} else if (
				frappe.boot &&
				frappe.boot.website_settings &&
				frappe.boot.website_settings.banner_image
			) {
				this.companyImg = frappe.boot.website_settings.banner_image;
			}

			// Force reactivity update
			this.$forceUpdate();
		},
		handleNavClick() {
			this.drawer = !this.drawer;
			this.$emit("nav-click");
		},
		goDesk() {
			window.location.href = "/app";
		},
		changePage(page) {
			this.$emit("change-page", page);
		},
		openCloseShift() {
			this.$emit("close-shift");
		},
		printLastInvoice() {
			this.$emit("print-last-invoice");
		},
		syncPendingInvoices() {
			this.$emit("sync-invoices");
		},
		toggleManualOffline() {
			this.$emit("toggle-offline");
		},
		async clearCache() {
			if (isOffline()) {
				this.showMessage({
					color: "warning",
					title: this.__("Cannot clear cache while offline"),
				});
				return;
			}
			try {
				await forceClearAllCache();
				await clearAllCaches({ confirmBeforeClear: false }).catch(() => {});
				this.showMessage({
					color: "success",
					title: this.__("Cache cleared successfully"),
				});
			} catch (e) {
				console.error("Failed to clear cache", e);
				this.showMessage({
					color: "error",
					title: this.__("Failed to clear cache"),
				});
			} finally {
				setTimeout(() => location.reload(), 1000);
			}
		},
		toggleTheme() {
			this.$emit("toggle-theme");
		},
		toggleFullscreen() {
			if (!document.fullscreenElement) {
				document.documentElement.requestFullscreen().then(() => {
					this.isFullscreen = true;
				}).catch(err => {
					console.error("Error attempting to enable fullscreen:", err);
				});
			} else {
				document.exitFullscreen().then(() => {
					this.isFullscreen = false;
				}).catch(err => {
					console.error("Error attempting to exit fullscreen:", err);
				});
			}
		},
		logOut() {
			this.$emit("logout");
		},
		refreshCacheUsage() {
			this.$emit("refresh-cache-usage");
		},
		updateAfterDelete() {
			this.$emit("update-after-delete");
		},
		showMessage(data) {
			// Hỗ trợ hiển thị thông báo với HTML content
			if (data.message) {
				// Tạo nội dung với HTML
				this.snackText = data.message;
			} else {
				// Fallback cho thông báo đơn giản
				this.snackText = data.title;
			}

			this.snackColor = data.color || "success";
			// Dialog không tự động đóng như snackbar
			this.snackTimeout = 0; // Không timeout cho dialog
			this.snack = true;
		},
		handleFreeze(data) {
			this.freezeTitle = data?.title || "";
			this.freezeMsg = data?.message || "";
			this.freeze = true;
		},
		handleUnfreeze() {
			this.freeze = false;
			this.freezeTitle = "";
			this.freezeMsg = "";
		},
		handleSetCompany(data) {
			if (typeof data === "string") {
				this.company = data;
			} else if (data && data.name) {
				this.company = data.name;
				if (data.company_image) {
					this.companyImg = data.company_image;
				}
			}
		},
		handleMouseLeave() {
			if (!this.drawer) return;
			clearTimeout(this._closeTimeout);
			this._closeTimeout = setTimeout(() => {
				this.drawer = false;
				this.mini = true;
			}, 250);
		},
	},
	emits: [
		"nav-click",
		"change-page",
		"close-shift",
		"print-last-invoice",
		"sync-invoices",
		"toggle-offline",
		"toggle-theme",
		"logout",
		"refresh-cache-usage",
		"update-after-delete",
	],
};
</script>

<style scoped>
/* Main navigation container styles */
nav {
	position: relative;
	z-index: 1000;
}

/* Snackbar positioning */
:deep(.v-snackbar) {
	z-index: 9999;
}

/* Dark theme adjustments */
:deep(.dark-theme) nav,
:deep(.v-theme--dark) nav {
	background-color: var(--background) !important;
}

/* Offer Dialog - Centered Popup Style */
.offer-dialog-card {
	border-radius: 16px !important;
	overflow: hidden;
	background: #ffb74d !important; /* Màu vàng cam */
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
	max-height: 80vh;
	border: 2px solid #ff9800;
}

/* Header với gradient */
.offer-header {
	background: linear-gradient(135deg, #ffb74d 0%, #ff9800 100%) !important;
	color: #000000 !important;
	border-bottom: 2px solid #ff9800;
	position: relative;
	min-height: auto !important;
	padding: 20px !important;
}

.offer-header::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 4px;
	background: linear-gradient(90deg, #ff6f00 0%, #ff9800 100%);
}

.header-content {
	display: flex;
	align-items: center;
	gap: 16px;
	padding-right: 60px;
}

.header-icon-wrapper {
	background: linear-gradient(135deg, #ff6f00 0%, #ff9800 100%);
	border-radius: 14px;
	padding: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 3px 8px rgba(255, 111, 0, 0.3);
}

.header-icon {
	color: white !important;
}

.header-text {
	flex: 1;
}

.header-title {
	margin: 0 0 6px 0;
	font-weight: 700 !important;
	color: #000000 !important;
	font-size: 1.5rem !important;
	line-height: 1.2;
	text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

.header-subtitle {
	margin: 0;
	font-size: 14px;
	color: #333 !important;
	font-weight: 500;
	line-height: 1.2;
}

.close-btn {
	position: absolute;
	top: 12px;
	right: 12px;
	color: #000000 !important;
	background: rgba(255, 255, 255, 0.2) !important;
	border-radius: 50% !important;
}

/* Content container */
.offer-content-container {
	padding: 24px;
	background: rgba(255, 255, 255, 0.95);
	min-height: 150px;
	max-height: 400px;
	overflow-y: auto;
}

.offer-notification-content {
	font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
	color: #000000 !important;
	line-height: 1.6;
}

.offer-notification-content div {
	margin-bottom: 8px;
	padding: 8px 12px;
	background: rgba(255, 255, 255, 0.8);
	border-radius: 8px;
	border-left: 3px solid #ff9800;
}

.offer-notification-content div:last-child {
	margin-bottom: 0;
}

/* Tiêu đề trong content */
.offer-notification-content div:first-child {
	font-size: 18px !important;
	font-weight: bold !important;
	margin-bottom: 12px !important;
	background: rgba(255, 152, 0, 0.1) !important;
	border-left-color: #ff6f00 !important;
}

/* Các dòng thông tin khác */
.offer-notification-content div:not(:first-child) {
	font-size: 14px !important;
	font-weight: 500 !important;
}

/* Actions */
.offer-actions {
	background: rgba(255, 255, 255, 0.9) !important;
	border-top: 1px solid #ff9800;
	min-height: auto !important;
	padding: 16px 24px !important;
}

.offer-close-action-btn {
	border-radius: 10px !important;
	font-weight: 600 !important;
	text-transform: none !important;
	height: 40px !important;
	padding: 0 24px !important;
	background: #000000 !important;
	color: #ffb74d !important;
	border: 2px solid #ff9800 !important;
}

.offer-close-action-btn:hover {
	background: #333 !important;
	transform: translateY(-1px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Responsive Design */
@media (max-width: 600px) {
	.offer-dialog-card {
		margin: 16px;
		max-height: 85vh;
		max-width: 95vw !important;
	}

	.header-content {
		gap: 12px;
		padding-right: 50px;
	}

	.offer-content-container {
		padding: 16px;
		max-height: 300px;
	}

	.header-title {
		font-size: 1.3rem !important;
	}
}

/* Scrollbar styling */
.offer-content-container::-webkit-scrollbar {
	width: 6px;
}

.offer-content-container::-webkit-scrollbar-track {
	background: rgba(255, 152, 0, 0.1);
	border-radius: 3px;
}

.offer-content-container::-webkit-scrollbar-thumb {
	background: #ff9800;
	border-radius: 3px;
}

.offer-content-container::-webkit-scrollbar-thumb:hover {
	background: #ff6f00;
}
</style>
