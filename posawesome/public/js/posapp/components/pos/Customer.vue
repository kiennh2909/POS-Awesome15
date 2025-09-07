<template>
	<!-- Customer Input Section -->
	<div class="customer-input-wrapper">
		<div class="customer-input-row">
			<v-autocomplete
				ref="customerDropdown"
				class="customer-autocomplete sleek-field"
				density="compact"
				clearable
				variant="solo"
				color="primary"
				:label="frappe._('Customer')"
				v-model="internalCustomer"
				:items="filteredCustomers"
				item-title="customer_name"
				item-value="name"
				:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
				:no-data-text="__('Customers not found')"
				hide-details
				:customFilter="() => true"
				:disabled="readonly || loadingCustomers"
				:menu-props="{ closeOnContentClick: false }"
				@update:menu="onCustomerMenuToggle"
				@update:modelValue="onCustomerChange"
				@update:search="onCustomerSearch"
				@keydown.enter="handleEnter"
				:virtual-scroll="true"
				:virtual-scroll-item-height="48"
			>
				<!-- Edit icon (left) -->
				<template #prepend-inner>
					<v-tooltip text="Edit customer">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="edit_customer"
							>
								mdi-account-edit
							</v-icon>
						</template>
					</v-tooltip>
				</template>

				<!-- Add icon (right) -->
				<template #append-inner>
					<v-tooltip text="Add new customer">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="new_customer"
							>
								mdi-plus
							</v-icon>
						</template>
					</v-tooltip>
				</template>

				<!-- Dropdown display -->
				<template #item="{ props, item }">
					<v-list-item v-bind="props">
						<v-list-item-subtitle v-if="item.raw.customer_name !== item.raw.name">
							<div v-html="`ID: ${item.raw.name}`"></div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.tax_id">
							<div v-html="`TAX ID: ${item.raw.tax_id}`"></div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.email_id">
							<div v-html="`Email: ${item.raw.email_id}`"></div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.mobile_no">
							<div v-html="`Mobile No: ${item.raw.mobile_no}`"></div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.primary_address">
							<div v-html="`Primary Address: ${item.raw.primary_address}`"></div>
						</v-list-item-subtitle>
					</v-list-item>
				</template>
			</v-autocomplete>

			<!-- View Details Button (moved outside dropdown) -->
			<v-btn
				v-if="customer"
				icon
				size="default"
				variant="outlined"
				color="primary"
				@click="viewCustomerDetails(customer)"
				class="view-details-btn"
				:disabled="readonly || loadingCustomers"
			>
				<v-icon size="20">mdi-eye</v-icon>
				<v-tooltip activator="parent" location="top">
					{{ __("View Customer Details") }}
				</v-tooltip>
			</v-btn>
		</div>

		<!-- Update customer modal -->
		<div class="mt-4">
			<UpdateCustomer />
		</div>

		<!-- Customer Detail modal -->
		<div class="mt-4">
			<CustomerDetail
				:key="customerDetailKey"
				v-model="showCustomerDetail"
				:customer-id="customer"
				@update:modelValue="onCustomerDetailDialogUpdate"
			/>
		</div>
	</div>
</template>

<style scoped>
.customer-input-wrapper {
	width: 100%;
	max-width: 100%;
	padding-right: 1.5rem;
	/* Elegant space at the right edge */
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
}

.customer-input-row {
	display: flex;
	align-items: center;
	gap: 12px;
	width: 100%;
}

.customer-autocomplete {
	width: 100%;
	box-sizing: border-box;
	border-radius: 12px;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
	transition: box-shadow 0.3s ease;
	background-color: #fff;
}

.customer-autocomplete:hover {
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Dark mode styling */
:deep(.dark-theme) .customer-autocomplete,
:deep(.v-theme--dark) .customer-autocomplete,
::v-deep(.dark-theme) .customer-autocomplete,
::v-deep(.v-theme--dark) .customer-autocomplete {
	/* Use surface color for dark mode */
	background-color: #1e1e1e !important;
}

:deep(.dark-theme) .customer-autocomplete :deep(.v-field__input),
:deep(.v-theme--dark) .customer-autocomplete :deep(.v-field__input),
:deep(.dark-theme) .customer-autocomplete :deep(input),
:deep(.v-theme--dark) .customer-autocomplete :deep(input),
:deep(.dark-theme) .customer-autocomplete :deep(.v-label),
:deep(.v-theme--dark) .customer-autocomplete :deep(.v-label),
::v-deep(.dark-theme) .customer-autocomplete .v-field__input,
::v-deep(.v-theme--dark) .customer-autocomplete .v-field__input,
::v-deep(.dark-theme) .customer-autocomplete input,
::v-deep(.v-theme--dark) .customer-autocomplete input,
::v-deep(.dark-theme) .customer-autocomplete .v-label,
::v-deep(.v-theme--dark) .customer-autocomplete .v-label {
	color: #fff !important;
}

:deep(.dark-theme) .customer-autocomplete :deep(.v-field__overlay),
:deep(.v-theme--dark) .customer-autocomplete :deep(.v-field__overlay),
::v-deep(.dark-theme) .customer-autocomplete .v-field__overlay,
::v-deep(.v-theme--dark) .customer-autocomplete .v-field__overlay {
	background-color: #1e1e1e !important;
}

.icon-button {
	cursor: pointer;
	font-size: 20px;
	opacity: 0.7;
	transition: all 0.2s ease;
}

.icon-button:hover {
	opacity: 1;
	color: var(--v-theme-primary);
}

.view-details-btn {
	min-width: 48px !important;
	height: 48px !important;
	border-radius: 12px !important;
	transition: all 0.2s ease;
	flex-shrink: 0;
}

.view-details-btn:hover {
	transform: scale(1.05);
	box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

/* Responsive Design */
@media (max-width: 768px) {
	.customer-input-wrapper {
		padding-right: 1rem;
	}

	.customer-input-row {
		flex-direction: column;
		align-items: stretch;
		gap: 8px;
	}

	.customer-autocomplete {
		flex: 1;
	}

	.view-details-btn {
		align-self: flex-end;
		min-width: 44px !important;
		height: 44px !important;
	}
}
</style>

<script>
import UpdateCustomer from "./UpdateCustomer.vue";
import CustomerDetail from "./CustomerDetail.vue";
import { getCustomerStorage, setCustomerStorage } from "../../../offline/index.js";

export default {
	props: {
		pos_profile: Object,
	},

	data: () => ({
		pos_profile: "",
		customers: [],
		customer: "", // Selected customer
		internalCustomer: null, // Model bound to the dropdown
		tempSelectedCustomer: null, // Temporarily holds customer selected from dropdown
		isMenuOpen: false, // Tracks whether dropdown menu is open
		readonly: false,
		customer_info: {}, // Used for edit modal
		loadingCustomers: false, // ? New state to track loading status
		customerSearch: "", // Search text
		showCustomerDetail: false, // Show customer detail dialog
		customerDetailKey: 0, // Key to force re-render CustomerDetail component
	}),

	components: {
		UpdateCustomer,
		CustomerDetail,
	},

	computed: {
		isDarkTheme() {
			return this.$theme.current === "dark";
		},

		filteredCustomers() {
			const search = this.customerSearch.toLowerCase();
			let results = this.customers;
			if (search) {
				results = results.filter((cust) => {
					return (
						(cust.customer_name && cust.customer_name.toLowerCase().includes(search)) ||
						(cust.tax_id && cust.tax_id.toLowerCase().includes(search)) ||
						(cust.email_id && cust.email_id.toLowerCase().includes(search)) ||
						(cust.mobile_no && cust.mobile_no.toLowerCase().includes(search)) ||
						(cust.name && cust.name.toLowerCase().includes(search))
					);
				});
			}
			return results;
		},
	},

	methods: {
		// Called when dropdown opens or closes
		onCustomerMenuToggle(isOpen) {
			this.isMenuOpen = isOpen;

			if (isOpen) {
				this.internalCustomer = null;

				this.$nextTick(() => {
					setTimeout(() => {
						const dropdown = this.$refs.customerDropdown?.$el?.querySelector(
							".v-overlay__content .v-select-list",
						);
						if (dropdown) dropdown.scrollTop = 0;
					}, 50);
				});
			} else {
				// Restore selection if user didn't pick anything
				if (this.tempSelectedCustomer) {
					this.internalCustomer = this.tempSelectedCustomer;
					this.customer = this.tempSelectedCustomer;
					this.eventBus.emit("update_customer", this.customer);
				} else if (this.customer) {
					this.internalCustomer = this.customer;
				}

				this.tempSelectedCustomer = null;
			}
		},

		// Called when a customer is selected
		onCustomerChange(val) {
			this.tempSelectedCustomer = val;

			if (!this.isMenuOpen && val) {
				this.customer = val;
				this.eventBus.emit("update_customer", val);
			}
		},

		onCustomerSearch(val) {
			this.customerSearch = val || "";
		},

		// Pressing Enter in input
		handleEnter(event) {
			const inputText = event.target.value?.toLowerCase() || "";

			const matched = this.customers.find((cust) => {
				return (
					cust.customer_name?.toLowerCase().includes(inputText) ||
					cust.name?.toLowerCase().includes(inputText)
				);
			});

			if (matched) {
				this.tempSelectedCustomer = matched.name;
				this.internalCustomer = matched.name;
				this.customer = matched.name;
				this.eventBus.emit("update_customer", matched.name);
				this.isMenuOpen = false;

				event.target.blur();
			}
		},

		// Load default customer info from server
		loadDefaultCustomerFromServer() {
			// Handle both direct pos_profile object and nested structure
			let actualProfile = this.pos_profile;
			if (this.pos_profile && this.pos_profile.pos_profile) {
				actualProfile = this.pos_profile.pos_profile;
			}
			
			if (!actualProfile || !actualProfile.name) {
				console.log("❌ No POS Profile name available for server call");
				return;
			}

			frappe.call({
				method: "posawesome.posawesome.api.utilities.get_default_customer",
				args: {
					pos_profile: actualProfile.name,
				},
				callback: (r) => {
					if (r.message) {
						console.log("Default customer info from server:", r.message);
						// Add to customers list if not already present
						const existingCustomer = this.customers.find(c => c.name === r.message.name);
						if (!existingCustomer) {
							this.customers.unshift(r.message);
							console.log("Added default customer to list:", r.message);
						}
						// Set as selected customer
						this.customer = r.message.name;
						this.internalCustomer = r.message.name;
						this.eventBus.emit("update_customer", r.message.name);
					}
				},
				error: (err) => {
					console.error("Failed to load default customer from server:", err);
				}
			});
		},

		// Fetch customers list
		get_customer_names() {
			console.log("=== DEBUG: get_customer_names() called ===");
			var vm = this;
			console.log("Current customers.length:", this.customers.length);
			console.log("POS Profile:", this.pos_profile);
			
			if (this.customers.length > 0) {
				// If customers already loaded, just check for default customer
				console.log("✅ Customers already loaded, checking for default customer");
				vm.setDefaultCustomerIfConfigured();
				return;
			}

			// Load from cache first if available
			if (vm.pos_profile.posa_local_storage && getCustomerStorage().length) {
				try {
					vm.customers = getCustomerStorage();
					console.log("✅ Loaded customers from cache:", vm.customers.length);
					// Check for default customer after loading from cache
					vm.setDefaultCustomerIfConfigured();
				} catch (e) {
					console.error("❌ Failed to parse customer cache:", e);
					vm.customers = [];
				}
			}

			console.log("📡 Fetching customers from server...");
			this.loadingCustomers = true;
			frappe.call({
				method: "posawesome.posawesome.api.customers.get_customer_names",
				args: {
					pos_profile: this.pos_profile.pos_profile,
				},
				callback: function (r) {
					console.log("📡 Server response:", r);
					if (r.message && r.message.length > 0) {
						vm.customers = r.message;
						console.log("✅ Loaded customers from server:", vm.customers.length);
						console.log("First few customers:", vm.customers.slice(0, 3));

						if (vm.pos_profile.posa_local_storage) {
							setCustomerStorage(r.message);
							console.log("💾 Saved customers to local storage");
						}

						// Set default customer after loading customers from server
						console.log("🔄 Setting default customer after server load...");
						vm.$nextTick(() => {
							vm.setDefaultCustomerIfConfigured();
							// If default customer setting failed, try loading from server
							let actualProfile = vm.pos_profile;
							if (vm.pos_profile && vm.pos_profile.pos_profile) {
								actualProfile = vm.pos_profile.pos_profile;
							}
							if (!vm.customer && actualProfile && actualProfile.default_customer) {
								console.log("🔄 Default customer not set, trying loadDefaultCustomerFromServer...");
								vm.loadDefaultCustomerFromServer();
							}
						});
					} else {
						console.log("❌ No customers received from server");
					}
					vm.loadingCustomers = false;
				},
				error: function (err) {
					console.error("❌ Failed to fetch customers:", err);
					vm.loadingCustomers = false;
				},
			});
			console.log("=== END DEBUG: get_customer_names() ===");
		},

		// Method to set default customer if configured
		setDefaultCustomerIfConfigured() {
			console.log("=== DEBUG: setDefaultCustomerIfConfigured() called ===");
			console.log("POS Profile (full object):", JSON.stringify(this.pos_profile, null, 2));
			
			// Handle both direct pos_profile object and nested structure
			let actualProfile = this.pos_profile;
			if (this.pos_profile && this.pos_profile.pos_profile) {
				// Nested structure: {pos_profile: {...}, company: {...}, ...}
				actualProfile = this.pos_profile.pos_profile;
				console.log("Using nested pos_profile structure");
			}
			
			console.log("Actual Profile default_customer:", actualProfile?.default_customer);
			console.log("Actual Profile keys:", actualProfile ? Object.keys(actualProfile) : 'null');
			console.log("Current customer:", this.customer);
			console.log("Customers loaded:", this.customers.length);

			if (!actualProfile) {
				console.log("❌ POS Profile is null/undefined");
				return;
			}

			if (!actualProfile.default_customer) {
				console.log("❌ No default customer configured in POS Profile");
				console.log("Available actualProfile fields:", Object.keys(actualProfile));
				return;
			}

			if (this.customers.length === 0) {
				console.log("❌ No customers loaded yet, skipping default customer setting");
				return;
			}

			// Skip if customer already selected (but allow empty string to be overridden)
			if (this.customer && this.customer !== "" && this.customer !== null) {
				console.log("❌ Customer already selected:", this.customer);
				return;
			}

			const defaultCustomerId = actualProfile.default_customer;
			console.log("🔍 Looking for default customer:", defaultCustomerId);
			console.log("Available customers:", this.customers.map(c => ({ name: c.name, customer_name: c.customer_name })));
			
			const defaultCustomer = this.customers.find(c => c.name === defaultCustomerId);
			if (defaultCustomer) {
				console.log("✅ Found default customer:", defaultCustomer);
				console.log("Setting customer properties...");
				
				// Set all customer-related properties
				this.customer = defaultCustomer.name;
				this.internalCustomer = defaultCustomer.name;
				this.tempSelectedCustomer = defaultCustomer.name;
				
				console.log("Customer properties set:");
				console.log("- this.customer:", this.customer);
				console.log("- this.internalCustomer:", this.internalCustomer);
				console.log("- this.tempSelectedCustomer:", this.tempSelectedCustomer);
				
				// Emit update event
				this.eventBus.emit("update_customer", defaultCustomer.name);
				console.log("✅ Default customer applied successfully:", defaultCustomer.customer_name);
				console.log("Event 'update_customer' emitted with:", defaultCustomer.name);
			} else {
				console.log("❌ Default customer not found in customer list:", defaultCustomerId);
				console.log("All available customer names:", this.customers.map(c => c.name));
			}
			console.log("=== END DEBUG: setDefaultCustomerIfConfigured() ===");
		},

		new_customer() {
			this.eventBus.emit("open_update_customer", null);
		},

		edit_customer() {
			this.eventBus.emit("open_update_customer", this.customer_info);
		},

		viewCustomerDetails(customerId) {
			console.log('[Customer] viewCustomerDetails called with:', customerId);
			console.log('[Customer] Current showCustomerDetail:', this.showCustomerDetail);

			this.customer = customerId;
			this.showCustomerDetail = true;
			this.customerDetailKey += 1; // Force re-render by changing key

			console.log('[Customer] After setting - customer:', this.customer, 'showCustomerDetail:', this.showCustomerDetail, 'key:', this.customerDetailKey);

			// Force update to ensure reactivity
			this.$nextTick(() => {
				this.$forceUpdate();
				console.log('[Customer] Force updated component');
			});
		},

		onCustomerDetailDialogUpdate(value) {
			console.log('[Customer] onCustomerDetailDialogUpdate called with:', value);
			console.log('[Customer] Current showCustomerDetail before update:', this.showCustomerDetail);

			this.showCustomerDetail = value;

			console.log('[Customer] showCustomerDetail updated to:', this.showCustomerDetail);

			// Force update to ensure reactivity
			this.$nextTick(() => {
				this.$forceUpdate();
				console.log('[Customer] Force updated after dialog update');
			});
		},
	},

	created() {
		// Load cached customers immediately for offline use
		if (getCustomerStorage().length) {
			try {
				this.customers = getCustomerStorage();
				console.log("Loaded customers from cache on component create:", this.customers.length);
			} catch (e) {
				console.error("Failed to parse customer cache:", e);
				this.customers = [];
			}
		}

		this.$nextTick(() => {
			this.eventBus.on("register_pos_profile", (pos_profile) => {
				console.log("=== EVENT: register_pos_profile ===");
				console.log("POS Profile registered in Customer component (full):", JSON.stringify(pos_profile, null, 2));
				console.log("default_customer in profile:", pos_profile?.default_customer);
				console.log("pos_profile keys:", pos_profile ? Object.keys(pos_profile) : 'null');
				this.pos_profile = pos_profile;
				this.get_customer_names();
			});

			this.eventBus.on("payments_register_pos_profile", (pos_profile) => {
				console.log("=== EVENT: payments_register_pos_profile ===");
				console.log("POS Profile registered from payments (full):", JSON.stringify(pos_profile, null, 2));
				console.log("default_customer in profile:", pos_profile?.default_customer);
				console.log("pos_profile keys:", pos_profile ? Object.keys(pos_profile) : 'null');
				this.pos_profile = pos_profile;
				this.get_customer_names();
			});

			this.eventBus.on("set_customer", (customer) => {
				this.customer = customer;
				this.internalCustomer = customer;
			});

			this.eventBus.on("add_customer_to_list", (customer) => {
				const index = this.customers.findIndex((c) => c.name === customer.name);
				if (index !== -1) {
					// Replace existing entry to avoid duplicates after update
					this.customers.splice(index, 1, customer);
				} else {
					this.customers.push(customer);
				}
				if (this.pos_profile.posa_local_storage) {
					setCustomerStorage(this.customers);
				}
				this.customer = customer.name;
				this.internalCustomer = customer.name;
				this.eventBus.emit("update_customer", customer.name);
			});

			this.eventBus.on("set_customer_readonly", (value) => {
				this.readonly = value;
			});

			this.eventBus.on("set_customer_info_to_edit", (data) => {
				this.customer_info = data;
			});

			this.eventBus.on("fetch_customer_details", () => {
				this.get_customer_names();
			});

			// Listen for POS profile updates to set default customer
			this.eventBus.on("pos_profile_updated", () => {
				console.log("=== EVENT: pos_profile_updated ===");
				console.log("POS Profile updated, checking for default customer");
				console.log("Current pos_profile:", this.pos_profile);
				console.log("Current customers count:", this.customers.length);
				this.$nextTick(() => {
					this.setDefaultCustomerIfConfigured();
				});
			});
		});
	},
};
</script>
