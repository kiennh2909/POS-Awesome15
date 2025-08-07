<template>
	<v-app-bar
		app
		flat
		height="56"
		:color="appBarColor"
		:theme="isDark ? 'dark' : 'light'"
		class="navbar-enhanced elevation-2 px-2 pb-1"
	>
		<v-app-bar-nav-icon ref="navIcon" @click="$emit('nav-click')" class="text-secondary nav-icon" />

		<v-img
			src="/assets/posawesome/js/posapp/components/pos/pos.png"
			alt="POS Awesome"
			max-width="32"
			class="mx-2"
		/>

		<v-toolbar-title
			@click="$emit('go-desk')"
			class="text-h6 font-weight-bold text-primary navbar-title"
			style="cursor: pointer; text-decoration: none"
		>
			<span class="font-weight-light">POS</span><span>Awesome</span>
		</v-toolbar-title>

		<!-- Tax Code Display Section -->
        <div v-if="tax_code_display || can_manage_tax_roll" class="tax-section mx-2 d-flex align-center">
          <!-- Tax Code Display -->
          <v-chip
            v-if="tax_code_display"
            color="success"
            variant="elevated"
            size="small"
            class="tax-chip mr-2"
          >
            <v-icon start size="small">mdi-receipt-text</v-icon>
            <span class="font-weight-bold">{{ tax_code_display }}</span>
          </v-chip>

          <!-- Tax Status Indicator -->
          <v-chip
            v-if="tax_code_display"
            color="green"
            variant="outlined"
            size="x-small"
            class="status-chip mr-2"
          >
            <v-icon start size="x-small">mdi-check-circle</v-icon>
            Hoạt động
          </v-chip>

          <!-- Tax Roll Management Button -->
          <v-btn
            v-if="can_manage_tax_roll"
            icon
            size="small"
            variant="outlined"
            color="primary"
            @click="show_tax_roll_dialog = true"
            class="tax-management-btn"
          >
            <v-icon size="small">mdi-cog</v-icon>
            <v-tooltip activator="parent" location="bottom">
              Quản lý cuộn hóa đơn thuế
            </v-tooltip>
          </v-btn>
        </div>

        <v-spacer></v-spacer>

		<!-- Enhanced connectivity status indicator - Always visible -->
		<slot name="status-indicator"></slot>

		<!-- Cache Usage Meter -->
		<slot name="cache-usage-meter"></slot>

		<div class="profile-section mx-1">
			<v-chip color="primary" variant="outlined" class="profile-chip">
				<v-icon start>mdi-account-circle</v-icon>
				{{ displayName }}
			</v-chip>
		</div>

		<v-btn
			icon
			color="primary"
			class="mx-1 offline-invoices-btn"
			@click="$emit('show-offline-invoices')"
			:class="{ 'has-pending': pendingInvoices > 0 }"
		>
			<v-badge v-if="pendingInvoices > 0" :content="pendingInvoices" color="error" overlap>
				<v-icon>mdi-file-document-multiple-outline</v-icon>
			</v-badge>
			<v-icon v-else>mdi-file-document-multiple-outline</v-icon>
			<v-tooltip activator="parent" location="bottom">
				{{ __("Offline Invoices") }} ({{ pendingInvoices }})
			</v-tooltip>
		</v-btn>

		<!-- Menu component slot -->
		<slot name="menu"></slot>

		<TaxRollDialog
			:show="show_tax_roll_dialog"
			:pos_profile="pos_profile"
			@close="show_tax_roll_dialog = false"
			@updated="handle_tax_roll_updated"
		/>
	</v-app-bar>
</template>

<script>
import { useNavbar } from '../../composables/useNavbar'
import TaxRollDialog from '../pos/TaxRollDialog.vue'

export default {
	name: "NavbarAppBar",
	components: {
		TaxRollDialog
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
		isDark: Boolean,
	},
	data() {
		return {
			show_tax_roll_dialog: false,
			tax_code_display: "",
			tax_refresh_interval: null,
		}
	},
	computed: {
		appBarColor() {
			return this.isDark ? this.$vuetify.theme.themes.dark.colors.surface : "white";
		},

		displayName() {
			// Show POS profile name if available, otherwise show user name
			if (this.posProfile && this.posProfile.name) {
				return this.posProfile.name;
			}

			// Fallback to Frappe user
			if (frappe.session && frappe.session.user_fullname) {
				return frappe.session.user_fullname;
			}

			if (frappe.session && frappe.session.user) {
				return frappe.session.user;
			}

			return "User";
		},
		can_manage_tax_roll() {
			// Chỉ cho phép user có quyền System Manager hoặc POS Manager
			return frappe.user_roles.includes('System Manager') ||
				   frappe.user_roles.includes('POS Manager');
		},
		pos_profile() {
			// Thử nhiều cách để lấy pos_profile
			if (this.$store.state.pos_profile?.name) {
				return this.$store.state.pos_profile.name;
			}
			if (this.posProfile?.name) {
				return this.posProfile.name;
			}
			// Fallback từ props
			return null;
		},
	},
	mounted() {
		this.load_tax_code_display();
		// Set up interval để refresh định kỳ
		this.tax_refresh_interval = setInterval(() => {
			this.load_tax_code_display();
		}, 30000); // Refresh mỗi 30 giây
	},
	beforeUnmount() {
		if (this.tax_refresh_interval) {
			clearInterval(this.tax_refresh_interval);
		}
	},
	watch: {
		pos_profile: {
			handler(newVal) {
				if (newVal) {
					this.load_tax_code_display();
				}
			},
			immediate: true
		},
		'$store.state.pos_profile': {
			handler() {
				this.load_tax_code_display();
			},
			deep: true
		}
	},
	methods: {
		async load_tax_code_display() {
			const profile_name = this.pos_profile;
			console.log("Loading tax display for profile:", profile_name);
			
			if (!profile_name) {
				console.log("No pos_profile found, skipping tax display load");
				return;
			}

			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.tax_roll.get_current_tax_info",
					args: {
						pos_profile: profile_name
					}
				});

				console.log("Tax info response:", response.message);

				if (response.message && response.message.current_display) {
					this.tax_code_display = response.message.current_display;
					console.log("Tax display updated:", this.tax_code_display);
				} else {
					// Nếu không có current_display, thử tạo từ các trường riêng lẻ
					const info = response.message;
					if (info && info.tax_roll_code && info.tax_current_counter) {
						this.tax_code_display = `${info.tax_roll_code} ${info.tax_current_counter}`;
						console.log("Tax display created manually:", this.tax_code_display);
					}
				}
			} catch (error) {
				console.error("Error loading tax code display:", error);
				// Log thêm thông tin để debug
				console.error("Profile name:", profile_name);
				console.error("Store state:", this.$store.state);
			}
		},

		handle_tax_roll_updated(data) {
			if (data && data.tax_code_display) {
				this.tax_code_display = data.tax_code_display;
			}
			this.load_tax_code_display(); // Refresh display
		},

		update_tax_display(new_display) {
			this.tax_code_display = new_display;
		},
	},
	emits: ["nav-click", "go-desk", "show-offline-invoices"],
};
</script>

<style scoped>
/* Enhanced Navbar Styling */
.navbar-enhanced {
	background-image: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
	background-color: #ffffff !important;
	border-bottom: 2px solid #e3f2fd !important;
	backdrop-filter: blur(10px);
	transition: all 0.3s ease;
	padding-bottom: 4px !important;
}

.navbar-enhanced:hover {
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
}

/* Logo and Brand Styling */
.navbar-title {
	text-decoration: none !important;
	border-bottom: none !important;
}

.navbar-title:hover {
	text-decoration: none !important;
}

/* Navigation Icon */
.nav-icon {
	border-radius: 12px;
	padding: 6px;
	transition: all 0.3s ease;
}

.nav-icon:hover {
	background-color: rgba(25, 118, 210, 0.1);
	transform: scale(1.1);
}

/* Profile Section */
.profile-section {
	margin: 0 8px;
}

.profile-chip {
	font-weight: 500;
	padding: 6px 12px;
	border-radius: 20px;
	transition: all 0.3s ease;
}

.profile-chip:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

/* Offline Invoices Button Enhancement */
.offline-invoices-btn {
	position: relative;
	transition: all 0.3s ease;
	padding: 4px;
}

.offline-invoices-btn:hover {
	transform: scale(1.05);
}

.offline-invoices-btn.has-pending {
	animation: pulse 2s infinite;
}

@keyframes pulse {
	0% {
		box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4);
	}
	70% {
		box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
	}
	100% {
		box-shadow: 0 0 0 0 rgba(244, 67, 54, 0);
	}
}

/* Tax Section Styling */
.tax-section {
	background: rgba(76, 175, 80, 0.05);
	border: 1px solid rgba(76, 175, 80, 0.2);
	border-radius: 20px;
	padding: 4px 8px;
	transition: all 0.3s ease;
}

.tax-section:hover {
	background: rgba(76, 175, 80, 0.1);
	transform: translateY(-1px);
}

.tax-chip {
	font-size: 0.75rem !important;
	height: 24px !important;
	box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3) !important;
}

.status-chip {
	font-size: 0.625rem !important;
	height: 20px !important;
	border-color: #4CAF50 !important;
	color: #4CAF50 !important;
}

.tax-management-btn {
	border-color: rgba(25, 118, 210, 0.5) !important;
	transition: all 0.3s ease;
}

.tax-management-btn:hover {
	background-color: rgba(25, 118, 210, 0.1) !important;
	border-color: #1976D2 !important;
	transform: scale(1.05);
}

/* Dark theme adjustments */
:deep(.dark-theme) .navbar-enhanced,
:deep(.v-theme--dark) .navbar-enhanced {
	background-image: linear-gradient(
		135deg,
		var(--surface-primary, #1e1e1e) 0%,
		var(--surface-secondary, #2d2d2d) 100%
	) !important;
	background-color: var(--surface-primary, #1e1e1e) !important;
	border-bottom: 2px solid var(--border-color, rgba(255, 255, 255, 0.12)) !important;
	color: var(--text-primary, #ffffff) !important;
}

:deep(.dark-theme) .tax-section,
:deep(.v-theme--dark) .tax-section {
	background: rgba(76, 175, 80, 0.1) !important;
	border-color: rgba(76, 175, 80, 0.3) !important;
}

:deep(.dark-theme) .navbar-enhanced:hover,
:deep(.v-theme--dark) .navbar-enhanced:hover {
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}

:deep(.dark-theme) .nav-icon,
:deep(.v-theme--dark) .nav-icon {
	color: var(--text-primary, #ffffff) !important;
}

:deep(.dark-theme) .nav-icon:hover,
:deep(.v-theme--dark) .nav-icon:hover {
	background-color: rgba(144, 202, 249, 0.1);
}

:deep(.dark-theme) .navbar-title,
:deep(.v-theme--dark) .navbar-title {
	color: var(--text-primary, #ffffff) !important;
}

:deep(.dark-theme) .profile-chip,
:deep(.v-theme--dark) .profile-chip {
	background-color: var(--surface-secondary, #2d2d2d) !important;
	color: var(--text-primary, #ffffff) !important;
	border-color: var(--primary-light, #90caf9) !important;
}
</style>