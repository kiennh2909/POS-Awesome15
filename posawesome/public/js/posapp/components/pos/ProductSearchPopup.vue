<template>
	<v-dialog 
		v-model="isVisible" 
		max-width="900px" 
		persistent
		@keydown.esc="closePopup"
	>
		<v-card class="product-search-popup">
			<!-- Header -->
			<v-card-title class="d-flex align-center pa-4 bg-grey-lighten-5">
				<v-icon class="mr-2" color="primary">mdi-magnify</v-icon>
				<span class="text-h6">Tìm Kiếm Sản Phẩm</span>
				<v-spacer></v-spacer>
				<v-btn 
					icon="mdi-close" 
					variant="text" 
					@click="closePopup"
					size="small"
				></v-btn>
			</v-card-title>

			<!-- Search Input -->
			<v-card-text class="pa-4">
				<v-row class="mb-4">
					<v-col cols="9">
						<v-text-field
							ref="searchInput"
							v-model="searchTerm"
							placeholder="Nhập mã sản phẩm, tên sản phẩm hoặc barcode..."
							variant="outlined"
							density="comfortable"
							hide-details
							autofocus
							@keydown.enter="performSearch"
							@input="onSearchInput"
						>
							<template v-slot:prepend-inner>
								<v-icon color="grey">mdi-magnify</v-icon>
							</template>
						</v-text-field>
					</v-col>
					<v-col cols="3">
						<v-btn 
							color="primary" 
							variant="flat"
							size="large"
							block
							@click="performSearch"
							:loading="isSearching"
						>
							Tìm kiếm
						</v-btn>
					</v-col>
				</v-row>

				<!-- Error Message -->
				<v-alert 
					v-if="errorMessage"
					type="error"
					variant="tonal"
					class="mb-4"
					closable
					@click:close="errorMessage = ''"
				>
					{{ errorMessage }}
				</v-alert>

				<!-- Search Results -->
				<div v-if="searchResults.length > 0">
					<!-- Results Header -->
					<div class="results-header mb-3">
						<v-row class="text-caption font-weight-bold text-grey-darken-1 px-3">
							<v-col cols="1" class="text-center">CHỌN</v-col>
							<v-col cols="4">TÊN SẢN PHẨM</v-col>
							<v-col cols="1" class="text-center">SL</v-col>
							<v-col cols="1" class="text-center">ĐVT</v-col>
							<v-col cols="2" class="text-center">ĐƠN GIÁ</v-col>
							<v-col cols="2" class="text-center">CHIẾT KHẤU</v-col>
							<v-col cols="1" class="text-center">THÀNH TIỀN</v-col>
						</v-row>
					</div>

					<!-- Results List -->
					<div class="results-list" style="max-height: 400px; overflow-y: auto;">
						<v-card 
							v-for="(item, index) in searchResults" 
							:key="item.item_code"
							class="mb-2 product-item-card"
							variant="outlined"
							:class="{ 'selected-item': selectedIndex === index }"
							@click="selectItem(index)"
							@keydown.enter="selectItem(index)"
							tabindex="0"
						>
							<v-card-text class="pa-3">
								<v-row align="center">
									<!-- Select Button -->
									<v-col cols="1" class="text-center">
										<v-btn
											color="primary"
											variant="outlined"
											size="small"
											@click.stop="addToCart(item)"
										>
											CHỌN
										</v-btn>
									</v-col>

									<!-- Product Info -->
									<v-col cols="4">
										<div class="product-info">
											<div class="product-name font-weight-medium">
												{{ item.item_name }}
											</div>
											<div class="product-code text-caption text-grey-darken-1">
												{{ item.item_code }}
												<span v-if="item.item_barcode && item.item_barcode.length > 0" class="ml-2">
													• {{ getFirstBarcode(item) }}
												</span>
											</div>
										</div>
									</v-col>

									<!-- Quantity -->
									<v-col cols="1" class="text-center">
										<div class="quantity-display font-weight-medium">
											{{ formatNumber(item.actual_qty || 0) }}
										</div>
									</v-col>

									<!-- UOM -->
									<v-col cols="1" class="text-center">
										<div class="uom-display">
											{{ item.uom || item.stock_uom }}
										</div>
									</v-col>

									<!-- Price -->
									<v-col cols="2" class="text-center">
										<div class="price-display font-weight-medium">
											{{ formatCurrency(item.rate || 0) }}
										</div>
									</v-col>

									<!-- Discount -->
									<v-col cols="2" class="text-center">
										<div class="discount-display">
											{{ formatPercent(item.discount_percentage || 0) }}
										</div>
									</v-col>

									<!-- Total -->
									<v-col cols="1" class="text-center">
										<div class="total-display font-weight-bold text-primary">
											{{ formatCurrency(calculateItemTotal(item)) }}
										</div>
									</v-col>
								</v-row>
							</v-card-text>
						</v-card>
					</div>

					<!-- Results Footer -->
					<div class="results-footer mt-3 d-flex justify-space-between align-center">
						<div class="text-caption text-grey-darken-1">
							Hiển thị {{ searchResults.length }} kết quả
						</div>
						<v-btn 
							variant="outlined" 
							@click="closePopup"
							prepend-icon="mdi-keyboard-esc"
						>
							Đóng (Esc)
						</v-btn>
					</div>
				</div>

				<!-- No Results -->
				<div v-else-if="hasSearched && !isSearching" class="text-center py-8">
					<v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-package-variant-closed</v-icon>
					<div class="text-h6 text-grey-darken-1 mb-2">Sản phẩm không có tồn kho</div>
					<div class="text-body-2 text-grey-darken-1">
						Không tìm thấy sản phẩm nào với từ khóa "{{ searchTerm }}"
					</div>
				</div>

				<!-- Initial State -->
				<div v-else-if="!hasSearched" class="text-center py-8">
					<v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-magnify</v-icon>
					<div class="text-h6 text-grey-darken-1 mb-2">Nhập từ khóa để tìm kiếm</div>
					<div class="text-body-2 text-grey-darken-1">
						Tìm kiếm theo mã sản phẩm, tên sản phẩm hoặc barcode
					</div>
				</div>
			</v-card-text>
		</v-card>
	</v-dialog>
</template>

<script>
import _ from 'lodash';

export default {
	name: 'ProductSearchPopup',
	props: {
		visible: {
			type: Boolean,
			default: false
		},
		posProfile: {
			type: Object,
			required: true
		},
		priceList: {
			type: String,
			required: true
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
			selectedIndex: -1,
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
		// Focus management
		focusSearchInput() {
			if (this.$refs.searchInput) {
				this.$refs.searchInput.focus();
			}
		},

		// Reset popup state
		resetPopup() {
			this.searchTerm = '';
			this.searchResults = [];
			this.selectedIndex = -1;
			this.isSearching = false;
			this.hasSearched = false;
			this.errorMessage = '';
		},

		// Close popup
		closePopup() {
			this.$emit('close');
		},

		// Search input handler with debounce
		onSearchInput: _.debounce(function() {
			if (this.searchTerm.trim().length >= 2) {
				this.performSearch();
			}
		}, 500),

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
				const results = await this.searchProducts(this.searchTerm.trim());
				this.searchResults = results;
				this.selectedIndex = results.length > 0 ? 0 : -1;
			} catch (error) {
				console.error('Search error:', error);
				this.errorMessage = 'Lỗi khi tìm kiếm sản phẩm. Vui lòng thử lại.';
				this.searchResults = [];
			} finally {
				this.isSearching = false;
			}
		},

		// Search products via API
		async searchProducts(searchTerm) {
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.items.search_items_for_popup",
					args: {
						search_term: searchTerm,
						pos_profile: JSON.stringify(this.posProfile),
						price_list: this.priceList,
						customer: this.customer,
						limit: 50
					}
				});

				return response.message || [];
			} catch (error) {
				console.error('API search error:', error);
				throw error;
			}
		},

		// Select item
		selectItem(index) {
			this.selectedIndex = index;
		},

		// Add item to cart
		addToCart(item) {
			this.$emit('add-item', item);
			this.closePopup();
		},

		// Utility methods
		getFirstBarcode(item) {
			if (item.item_barcode && item.item_barcode.length > 0) {
				return item.item_barcode[0].barcode;
			}
			return '';
		},

		formatNumber(value) {
			return parseFloat(value || 0).toFixed(2);
		},

		formatCurrency(value) {
			const amount = parseFloat(value || 0);
			return new Intl.NumberFormat('vi-VN').format(amount);
		},

		formatPercent(value) {
			const percent = parseFloat(value || 0);
			return `${percent.toFixed(2)}%`;
		},

		calculateItemTotal(item) {
			const rate = parseFloat(item.rate || 0);
			const qty = parseFloat(item.actual_qty || 1);
			const discount = parseFloat(item.discount_percentage || 0);
			
			const subtotal = rate * qty;
			const discountAmount = subtotal * (discount / 100);
			return subtotal - discountAmount;
		}
	}
};
</script>

<style scoped>
.product-search-popup {
	border-radius: 12px;
}

.product-item-card {
	transition: all 0.2s ease;
	cursor: pointer;
}

.product-item-card:hover {
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	transform: translateY(-1px);
}

.selected-item {
	border-color: #1976d2 !important;
	background-color: rgba(25, 118, 210, 0.05);
}

.product-info {
	text-align: left;
}

.product-name {
	font-size: 0.95rem;
	line-height: 1.3;
	margin-bottom: 4px;
}

.product-code {
	font-size: 0.8rem;
}

.results-header {
	border-bottom: 2px solid #e0e0e0;
	padding-bottom: 8px;
}

.results-list {
	border: 1px solid #e0e0e0;
	border-radius: 8px;
	padding: 8px;
}

.quantity-display,
.uom-display,
.price-display,
.discount-display,
.total-display {
	font-size: 0.9rem;
}

.results-footer {
	padding-top: 16px;
	border-top: 1px solid #e0e0e0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
	.product-search-popup {
		margin: 16px;
	}
	
	.results-list {
		max-height: 300px;
	}
}
</style>