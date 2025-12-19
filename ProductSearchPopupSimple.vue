<template>
	<v-dialog 
		v-model="isVisible" 
		max-width="600px" 
		persistent
	>
		<v-card>
			<!-- Header -->
			<v-card-title class="d-flex align-center pa-4">
				<v-icon class="mr-2">mdi-magnify</v-icon>
				<span>Tìm Kiếm Sản Phẩm (Simple)</span>
				<v-spacer></v-spacer>
				<v-btn 
					icon="mdi-close" 
					variant="text" 
					@click="closePopup"
					size="small"
				></v-btn>
			</v-card-title>

			<!-- Content -->
			<v-card-text class="pa-4">
				<!-- Search Input -->
				<v-text-field
					ref="searchInput"
					v-model="searchTerm"
					placeholder="Nhập từ khóa tìm kiếm..."
					variant="outlined"
					hide-details
					class="mb-4"
					@keydown.enter="performSearch"
				>
					<template v-slot:append-inner>
						<v-btn 
							color="primary" 
							variant="flat"
							@click="performSearch"
							:loading="isSearching"
							size="small"
						>
							Tìm
						</v-btn>
					</template>
				</v-text-field>

				<!-- Debug Info -->
				<v-alert 
					type="info" 
					variant="tonal" 
					class="mb-4"
				>
					<div><strong>Debug Info:</strong></div>
					<div>Search Term: "{{ searchTerm }}"</div>
					<div>Is Searching: {{ isSearching }}</div>
					<div>Has Searched: {{ hasSearched }}</div>
					<div>Results Count: {{ searchResults.length }}</div>
					<div>Error: {{ errorMessage || 'None' }}</div>
				</v-alert>

				<!-- Loading -->
				<div v-if="isSearching" class="text-center py-4">
					<v-progress-circular indeterminate color="primary"></v-progress-circular>
					<div class="mt-2">Đang tìm kiếm...</div>
				</div>

				<!-- Error -->
				<v-alert 
					v-if="errorMessage"
					type="error"
					variant="tonal"
					class="mb-4"
				>
					{{ errorMessage }}
				</v-alert>

				<!-- Results -->
				<div v-if="searchResults.length > 0">
					<div class="mb-2"><strong>Kết quả ({{ searchResults.length }}):</strong></div>
					<v-list>
						<v-list-item
							v-for="(item, index) in searchResults"
							:key="item.item_code"
							@click="addToCart(item)"
							class="border mb-1"
						>
							<v-list-item-title>{{ item.item_name }}</v-list-item-title>
							<v-list-item-subtitle>
								{{ item.item_code }} • {{ formatCurrency(item.rate) }}
							</v-list-item-subtitle>
							<template v-slot:append>
								<v-btn color="primary" size="small">CHỌN</v-btn>
							</template>
						</v-list-item>
					</v-list>
				</div>

				<!-- No Results -->
				<div v-else-if="hasSearched && !isSearching" class="text-center py-4">
					<v-icon size="48" color="grey">mdi-package-variant-closed</v-icon>
					<div class="mt-2">Không tìm thấy sản phẩm</div>
				</div>

				<!-- Initial State -->
				<div v-else-if="!hasSearched" class="text-center py-4">
					<v-icon size="48" color="grey">mdi-magnify</v-icon>
					<div class="mt-2">Nhập từ khóa để tìm kiếm</div>
				</div>
			</v-card-text>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: 'ProductSearchPopupSimple',
	props: {
		visible: {
			type: Boolean,
			default: false
		},
		posProfile: {
			type: Object,
			default: () => ({})
		},
		priceList: {
			type: String,
			default: 'Standard Selling'
		},
		customer: {
			type: String,
			default: null
		}
	},
	data() {
		return {
			searchTerm: '',
			searchResults: [],
			isSearching: false,
			hasSearched: false,
			errorMessage: ''
		};
	},
	computed: {
		isVisible: {
			get() {
				return this.visible;
			},
			set(value) {
				if (!value) {
					this.closePopup();
				}
			}
		}
	},
	watch: {
		visible(newVal) {
			if (newVal) {
				this.resetPopup();
				this.$nextTick(() => {
					this.focusSearchInput();
				});
			}
		}
	},
	methods: {
		// Focus search input
		focusSearchInput() {
			if (this.$refs.searchInput) {
				this.$refs.searchInput.focus();
			}
		},

		// Reset popup state
		resetPopup() {
			this.searchTerm = '';
			this.searchResults = [];
			this.isSearching = false;
			this.hasSearched = false;
			this.errorMessage = '';
		},

		// Close popup
		closePopup() {
			this.$emit('close');
		},

		// Perform search
		async performSearch() {
			console.log('[SimplePopup] performSearch called with:', this.searchTerm);
			
			if (!this.searchTerm.trim()) {
				this.errorMessage = 'Vui lòng nhập từ khóa tìm kiếm';
				return;
			}

			this.isSearching = true;
			this.errorMessage = '';
			this.hasSearched = true;

			try {
				console.log('[SimplePopup] Calling API...');
				
				// Check if frappe is available
				if (typeof frappe === 'undefined') {
					throw new Error('frappe object not available');
				}

				const response = await frappe.call({
					method: "posawesome.posawesome.api.items.search_items_for_popup",
					args: {
						search_term: this.searchTerm.trim(),
						pos_profile: JSON.stringify(this.posProfile),
						price_list: this.priceList,
						customer: this.customer,
						limit: 10
					}
				});

				console.log('[SimplePopup] API response:', response);

				if (response && response.message) {
					this.searchResults = response.message;
					console.log('[SimplePopup] Search results:', this.searchResults.length, 'items');
				} else {
					this.searchResults = [];
					console.warn('[SimplePopup] No results returned');
				}

			} catch (error) {
				console.error('[SimplePopup] Search error:', error);
				this.errorMessage = `Lỗi: ${error.message}`;
				this.searchResults = [];
			} finally {
				this.isSearching = false;
			}
		},

		// Add item to cart
		addToCart(item) {
			console.log('[SimplePopup] Adding item to cart:', item.item_name);
			this.$emit('add-item', item);
			this.closePopup();
		},

		// Format currency
		formatCurrency(value) {
			const amount = parseFloat(value || 0);
			return new Intl.NumberFormat('vi-VN').format(amount);
		}
	}
};
</script>

<style scoped>
.border {
	border: 1px solid #e0e0e0;
	border-radius: 4px;
}
</style>