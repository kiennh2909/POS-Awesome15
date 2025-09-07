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

		<!-- Snackbar for notifications -->
		<v-snackbar
			v-model="snack"
			:timeout="snackTimeout"
			:color="snackColor"
			class="offer-notification-snackbar"
			:style="{
				'--snackbar-bg': snackColor === 'warning' ? '#ffb74d' : (snackColor === 'primary' ? '#1976d2' : '#4caf50'),
				'--snackbar-text': snackColor === 'warning' ? '#000000' : '#ffffff',
				'--snackbar-shadow': '0 4px 12px rgba(0,0,0,0.15)'
			}"
		>
			<div
				v-html="snackText"
				class="offer-notification-content"
				:style="{
					fontSize: '14px',
					lineHeight: '1.5',
					fontWeight: '500'
				}"
			></div>
			<template v-slot:actions>
				<v-btn
					:color="snackColor === 'warning' ? 'black' : 'white'"
					variant="text"
					@click="snack = false"
					class="offer-close-btn"
					size="small"
				>
					{{ __("Close") }}
				</v-btn>
			</template>
		</v-snackbar>
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
			this.snackTimeout = data.timeout || 3000;
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

/* Custom styling for offer notification snackbar */
.offer-notification-snackbar {
	border-radius: 8px !important;
	box-shadow: var(--snackbar-shadow) !important;
	max-width: 450px !important;
	min-width: 350px !important;
	position: fixed !important;
	top: 80px !important;
	right: 20px !important;
	z-index: 10000 !important;
	transform: none !important;
}

.offer-notification-snackbar :deep(.v-snackbar__wrapper) {
	border-radius: 8px !important;
	background: var(--snackbar-bg) !important;
	color: var(--snackbar-text) !important;
	position: static !important;
	transform: none !important;
}

.offer-notification-content {
	padding: 4px 0;
	font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
	color: var(--snackbar-text) !important;
}

.offer-notification-content div {
	margin-bottom: 6px;
}

.offer-notification-content div:last-child {
	margin-bottom: 0;
}

/* Tiêu đề to hơn */
.offer-notification-content div:first-child {
	font-size: 18px !important;
	font-weight: bold !important;
	margin-bottom: 8px !important;
}

/* Các dòng thông tin khác */
.offer-notification-content div:not(:first-child) {
	font-size: 14px !important;
	font-weight: 500 !important;
}

.offer-close-btn {
	font-weight: 600 !important;
	text-transform: none !important;
	min-width: auto !important;
	padding: 4px 8px !important;
}

/* Nút Close màu đen khi background vàng */
.offer-notification-snackbar :deep(.v-btn--variant-text) {
	color: var(--snackbar-text) !important;
}

/* Ensure good contrast for readability */
.offer-notification-snackbar :deep(.v-snackbar__content) {
	padding: 16px 20px !important;
}

/* Responsive adjustments */
@media (max-width: 600px) {
	.offer-notification-snackbar {
		max-width: 90vw !important;
		min-width: 300px !important;
		top: 70px !important;
		right: 10px !important;
	}

	.offer-notification-content {
		font-size: 13px !important;
	}
}

/* Desktop adjustments */
@media (min-width: 601px) {
	.offer-notification-snackbar {
		right: 20px !important;
		top: 80px !important;
	}
}
</style>
