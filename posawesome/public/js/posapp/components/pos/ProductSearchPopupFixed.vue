<template>
	<v-dialog 
		:model-value="visible" 
		max-width="800px" 
		persistent
		@update:model-value="handleDialogUpdate"
	>
		<v-card>
			<!-- Header -->
			<v-card-title class="d-flex align-center pa-4 bg-primary text-white">
				<v-icon class="mr-2">mdi-magnify</v-icon>
				<span>Tìm Kiếm Sản Phẩm</span>
				<v-spacer></v-spacer>
				<v-btn 
					icon="mdi-close" 
					variant="text" 
					color="white"
					@click="closePopup"
					size="small"
				></v-btn>
			</v-card-title>

			<!-- Content -->
			<v-card-text class="pa-4">
				<!-- Search Input -->
				<v-row class="mb-4">
					<v-col cols="8">
						<v-text-field
							ref="searchInput"
							v-model="searchTerm"
							placeholder="Nhập từ khóa tìm kiếm..."
							variant="outlined"
							hide-details
							@keydown.enter="performSearch"
						>
							<template v-slot:prepend-inner>
								<v-icon>mdi-magnify</v-icon>
							</template>
						</v-text-field>
					</v-col>
					<v-col cols="4">
						<v-btn 
							color="primary" 
							variant="flat"
							block
							@click="performSearch"
							:loading="isSearching"
						>
							Tìm kiếm
						</v-btn>
					</v-col>
				</v-row>

				<!-- Loading -->
				<div v-if="isSearching" class="text-center py-4">
					<v-progress-circular indeterminate color="primary"></v-progress-circular>
					<div class="mt-2">Đang tìm kiếm...</div>
				</div>

				<!-- Error -->
				<v-alert 
					v-else-if="errorMessage"
					type="error"
					class="mb-4"
				>
					{{ errorMessage }}
				</v-alert>

				<!-- Results -->
				<div v-else-if="searchResults.length > 0">
					<div class="mb-3">
						<strong>Tìm thấy {{ searchResults.length }} sản phẩm:</strong>
					</div>
					
					<!-- Simple Results List -->
					<v-list class="border rounded">
						<v-list-item
							v-for="(item, index) in searchResults"
							:key="item.item_code"
							class="border-b"
						>
							<template v-slot:prepend>
								<v-avatar color="grey-lighten-3">
									<v-icon>mdi-package-variant</v-icon>
								</v-avatar>
							</template>

							<v-list-item-title>{{ item.item_name }}</v-list-item-title>
							<v-list-item-subtitle>
								{{ item.item_code }} • {{ formatCurrency(item.rate) }} • SL: {{ item.actual_qty || 0 }}
							</v-list-item-subtitle>

							<template v-slot:append>
								<v-btn 
									color="primary" 
									size="small"
									@click="addToCart(item)"
								>
									CHỌN
								</v-btn>
							</template>
						</v-list-item>
					</v-list>
				</div>

				<!-- No Results -->
				<div v-else-if="hasSearched && !isSearching" class="text-center py-8">
					<v-icon size="64" color="grey">mdi-package-variant-closed</v-icon>
					<div class="mt-2">Không tìm thấy sản phẩm</div>
				</div>

				<!-- Initial State -->
				<div v-else class="text-center py-8">
					<v-icon size="64" color="grey">mdi-magnify</v-icon>
					<div class="mt-2">Nhập từ khóa để tìm kiếm</div>
				</div>
			</v-card-text>

			<!-- Footer -->
			<v-card-actions class="pa-4">
				<v-spacer></v-spacer>
				<v-btn 
					variant="outlined" 
					@click="closePopup"
				>
					Đóng
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: 'ProductSearchPopupFixed',
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
		// Handle dialog update (prevent infinite loop)
		handleDialogUpdate(value) {
			if (!value) {
				this.closePopup();
			}
		},

		// Focus search input
		focusSearchInput() {
			try {
				if (this.$refs.searchInput) {
					this.$refs.searchInput.focus();
				}
			} catch (error) {
				console.warn('[ProductSearchPopup] Focus error:', error);
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
			if (!this.searchTerm.trim()) {
				this.errorMessage = 'Vui lòng nhập từ khóa tìm kiếm';
				return;
			}

			this.isSearching = true;
			this.errorMessage = '';
			this.hasSearched = true;

			try {
				// Simple API call without complex validation
				const response = await frappe.call({
					method: "posawesome.posawesome.api.items.search_items_for_popup",
					args: {
						search_term: this.searchTerm.trim(),
						pos_profile: JSON.stringify(this.posProfile || {}),
						price_list: this.priceList || 'Standard Selling',
						customer: this.customer,
						limit: 20
					}
				});

				if (response && response.message) {
					this.searchResults = response.message;
				} else {
					this.searchResults = [];
				}

			} catch (error) {
				console.error('[ProductSearchPopup] Search error:', error);
				this.errorMessage = 'Lỗi khi tìm kiếm sản phẩm';
				this.searchResults = [];
			} finally {
				this.isSearching = false;
			}
		},

		// Add item to cart
		addToCart(item) {
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
}

.border-b {
	border-bottom: 1px solid #f0f0f0;
}
</style>