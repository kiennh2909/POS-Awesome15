<template>
	<div>
		<v-card
			:class="['selection mx-auto mt-3', isDarkTheme ? '' : 'bg-grey-lighten-5']"
			:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
			style="max-height: 80vh; height: 80vh"
		>
			<v-card-title>
				<span class="text-h6 text-primary">{{ __("Coupons") }}</span>
				<v-spacer></v-spacer>
				<v-btn
					variant="text"
					color="warning"
					@click="back_to_invoice"
				>
					<v-icon size="small" class="mr-1">mdi-arrow-left</v-icon>
					{{ __("Back") }}
				</v-btn>
			</v-card-title>

			<!-- Input and Button Row - Same Level -->
			<v-row class="px-4 pb-2" no-gutters>
				<v-col cols="8" class="pr-2">
					<v-text-field
						density="compact"
						variant="outlined"
						color="primary"
						:label="frappe._('Coupon')"
						bg-color="white"
						hide-details
						v-model="new_coupon"
						class="coupon-input"
						@keydown.enter="add_coupon(new_coupon)"
					>
					</v-text-field>
				</v-col>
				<v-col cols="4">
					<v-btn
						class="add-coupon-btn"
						color="success"
						theme="dark"
						block
						@click="add_coupon(new_coupon)"
					>
						<v-icon size="small" class="mr-1">mdi-plus</v-icon>
						{{ __("Add") }}
					</v-btn>
				</v-col>
			</v-row>

			<div
				class="my-0 py-0 overflow-y-auto"
				style="max-height: 75vh"
				@mouseover="style = 'cursor: pointer'"
			>
				<v-data-table
					:headers="items_headers"
					:items="posa_coupons"
					:single-expand="singleExpand"
					v-model:expanded="expanded"
					item-key="coupon"
					class="elevation-1"
					:items-per-page="itemsPerPage"
					hide-default-footer
				>
					<template v-slot:item.applied="{ item }">
						<v-checkbox-btn v-model="item.applied" disabled></v-checkbox-btn>
					</template>
				</v-data-table>
			</div>
		</v-card>
	</div>
</template>

<script>
export default {
	data: () => ({
		loading: false,
		pos_profile: "",
		customer: "",
		posa_coupons: [],
		new_coupon: null,
		itemsPerPage: 1000,
		singleExpand: true,
		couponInputTimeout: null, // For debouncing
		items_headers: [
			{ title: __("Coupon"), value: "coupon_code", align: "start" },
			{ title: __("Type"), value: "type", align: "start" },
			{ title: __("Offer"), value: "pos_offer", align: "start" },
			{ title: __("Applied"), value: "applied", align: "start" },
		],
	}),

	computed: {
		couponsCount() {
			return this.posa_coupons.length;
		},
		appliedCouponsCount() {
			return this.posa_coupons.filter((el) => !!el.applied).length;
		},
		isDarkTheme() {
			return this.$theme?.current === "dark";
		},
	},

	methods: {
		// Debounce function for coupon input
		debounceCouponInput(func, delay) {
			return function(...args) {
				const context = this;
				clearTimeout(this.couponInputTimeout);
				this.couponInputTimeout = setTimeout(() => func.apply(context, args), delay);
				console.log(`⏱️ [COUPON_DEBOUNCE] Function debounced for ${delay}ms`);
			};
		},

		// Validate coupon input based on schema constraints
		validateCouponInput(couponCode) {
			if (!couponCode || couponCode.trim().length === 0) {
				return { valid: false, message: __("Coupon code is required") };
			}

			// Check format based on schema constraints
			const code = couponCode.trim().toUpperCase();
			if (code.length < 3 || code.length > 20) {
				return { valid: false, message: __("Coupon code must be 3-20 characters") };
			}

			// Check for invalid characters
			if (!/^[A-Z0-9\-_]+$/.test(code)) {
				return { valid: false, message: __("Only letters, numbers, hyphens, underscores allowed") };
			}

			return { valid: true, code: code };
		},

		back_to_invoice() {
			this.eventBus.emit("show_coupons", "false");
		},
		add_coupon(new_coupon) {
			// Enhanced validation with schema-based checks
			if (!this.customer) {
				this.eventBus.emit("show_message", {
					title: __("Select a customer to use coupon"),
					color: "error",
				});
				return;
			}

			const validation = this.validateCouponInput(new_coupon);
			if (!validation.valid) {
				this.eventBus.emit("show_message", {
					title: __("Invalid Coupon Code"),
					message: validation.message,
					color: "warning"
				});
				return;
			}

			// Check for duplicates in current session
			const exist = this.posa_coupons.find((el) => el.coupon_code == validation.code);
			if (exist) {
				this.eventBus.emit("show_message", {
					title: __("This coupon already used !"),
					color: "error",
				});
				return;
			}

			// Debounce the actual API call
			this.debouncedAddCoupon(validation.code);
		},

		// Debounced API call method
		_addCouponAPI(couponCode) {
			console.log("🎫 [COUPON_ADD] Adding validated coupon:", couponCode);
			const vm = this;

			frappe.call({
				method: "posawesome.posawesome.api.offers.get_pos_coupon",
				args: {
					coupon: couponCode,
					customer: vm.customer,
					company: vm.pos_profile.company,
				},
				callback: function (r) {
					console.log("🎫 [COUPON_API] API response received", {
						has_coupon: !!r.message?.coupon,
						message: r.message?.msg
					});

					if (r.message) {
						const res = r.message;
						if (res.msg != "Apply" || !res.coupon) {
							console.warn("🎫 [COUPON_ERROR] Coupon validation failed:", res.msg);
							vm.eventBus.emit("show_message", {
								title: __("Coupon Validation Failed"),
								message: res.msg,
								color: "error",
							});
						} else {
							console.log("🎫 [COUPON_SUCCESS] Coupon added successfully", {
								coupon_code: couponCode,
								coupon_type: res.coupon.coupon_type
							});

							vm.new_coupon = null;
							const coupon = res.coupon;
							vm.posa_coupons.push({
								coupon: coupon.name,
								coupon_code: coupon.coupon_code,
								type: coupon.coupon_type,
								applied: 0,
								pos_offer: coupon.pos_offer,
								customer: coupon.customer || vm.customer,
								valid_from: coupon.valid_from,
								valid_upto: coupon.valid_upto,
								maximum_use: coupon.maximum_use,
								used: coupon.used
							});

							vm.eventBus.emit("show_message", {
								title: __("Coupon Added"),
								message: __("Coupon {0} has been added successfully", [couponCode]),
								color: "success",
								timeout: 2000
							});
						}
					}
				},
			});
		},
		setActiveGiftCoupons() {
			if (!this.customer) return;
			const vm = this;
			frappe.call({
				method: "posawesome.posawesome.api.offers.get_active_gift_coupons",
				args: {
					customer: vm.customer,
					company: vm.pos_profile.company,
				},
				callback: function (r) {
					if (r.message) {
						const coupons = r.message;
						coupons.forEach((coupon_code) => {
							vm.add_coupon(coupon_code);
						});
					}
				},
			});
		},

		updatePosCoupons(offers) {
			this.posa_coupons.forEach((coupon) => {
				const offer = offers.find((el) => el.offer_applied && el.coupon == coupon.coupon);
				if (offer) {
					coupon.applied = 1;
				} else {
					coupon.applied = 0;
				}
			});
		},

		removeCoupon(reomove_list) {
			this.posa_coupons = this.posa_coupons.filter((coupon) => !reomove_list.includes(coupon.coupon));
		},
		updateInvoice() {
			this.eventBus.emit("update_invoice_coupons", this.posa_coupons);
		},
		updateCounters() {
			this.eventBus.emit("update_coupons_counters", {
				couponsCount: this.couponsCount,
				appliedCouponsCount: this.appliedCouponsCount,
			});
		},

		// Keyboard shortcuts handler
		handleKeyboardShortcuts(event) {
			// Only handle when dialog is active and focused
			if (!this.$el || !this.$el.contains(document.activeElement)) return;

			// Ctrl/Cmd + Enter: Add coupon
			if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
				event.preventDefault();
				if (this.new_coupon && this.new_coupon.trim()) {
					this.add_coupon(this.new_coupon.trim());
				}
			}

			// Delete key: Remove selected coupon
			if (event.key === "Delete" && !event.target.matches('input, textarea')) {
				event.preventDefault();
				if (this.expanded.length > 0) {
					const selectedCoupon = this.posa_coupons.find(c =>
						c.coupon === this.expanded[0]
					);
					if (selectedCoupon) {
						this.remove_coupon(selectedCoupon);
					}
				}
			}

			// Escape: Back to invoice
			if (event.key === "Escape") {
				event.preventDefault();
				this.back_to_invoice();
			}
		},
	},

	beforeUnmount() {
		// Cleanup keyboard event listener
		document.removeEventListener("keydown", this.handleKeyboardShortcuts);
	},

	watch: {
		posa_coupons: {
			deep: true,
			handler() {
				this.updateInvoice();
				this.updateCounters();
			},
		},
	},

	created: function () {
		this.$nextTick(function () {
			// Initialize debounced coupon addition
			this.debouncedAddCoupon = this.debounceCouponInput(this._addCouponAPI, 300);

			// Add keyboard shortcuts
			document.addEventListener("keydown", this.handleKeyboardShortcuts.bind(this));

			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
			});
		});
		this.eventBus.on("update_customer", (customer) => {
			if (this.customer != customer) {
				const to_remove = [];
				this.posa_coupons.forEach((el) => {
					if (el.type == "Promotional") {
						el.customer = customer;
					} else {
						to_remove.push(el.coupon);
					}
				});
				this.customer = customer;
				if (to_remove.length) {
					this.removeCoupon(to_remove);
				}
			}
			this.setActiveGiftCoupons();
		});
		this.eventBus.on("update_pos_coupons", (data) => {
			this.updatePosCoupons(data);
		});
		this.eventBus.on("set_pos_coupons", (data) => {
			this.posa_coupons = data;
		});
	},
};
</script>

<style scoped>
.coupon-input {
	height: 40px;
}

.add-coupon-btn {
	height: 40px;
	font-weight: 600 !important;
	transition: all 0.3s ease !important;
}

.add-coupon-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}
</style>
