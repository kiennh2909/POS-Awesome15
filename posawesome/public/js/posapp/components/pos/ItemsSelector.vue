<template>
	<div :style="responsiveStyles">
		<v-card
			:class="[
				'selection mx-auto my-0 py-0 mt-3 dynamic-card resizable',
				isDarkTheme ? '' : 'bg-grey-lighten-5',
			]"
			:style="{
				height: responsiveStyles['--container-height'],
				maxHeight: responsiveStyles['--container-height'],
				backgroundColor: isDarkTheme ? '#121212' : '',
				resize: 'vertical',
				overflow: 'hidden', // Changed from 'auto' to 'hidden'
			}"
		>
			<v-progress-linear
				:active="loading"
				:indeterminate="loading"
				absolute
				location="top"
				color="info"
			></v-progress-linear>
			<v-overlay :model-value="loading" class="align-center justify-center" absolute>
				<v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
			</v-overlay>

			<!-- Sticky Search Header -->
			<div class="sticky-search-header">
				<div class="dynamic-padding">
					<v-row class="items">
						<v-col class="pb-0">
							<v-text-field
								ref="searchInput"
								v-model="debounce_search"
								:placeholder="dynamicPlaceholder"
								:hint="dynamicHint"
								density="compact"
								clearable
								autofocus
								variant="solo"
								color="primary"
								hide-details="auto"
								@keydown="handleKeyDown"
								@focus="handleSearchFocus"
								@blur="handleSearchBlur"
								@click:clear="clearSearch"
								class="barcode-input"
								:class="`search-mode-${search_mode}`"
							>
								<!-- Mode indicator icon -->
								<template v-slot:prepend-inner>
									<v-icon :color="modeColor" size="small">
										{{ modeIcon }}
									</v-icon>
								</template>
								
								<!-- Keyboard hint -->
								<template v-slot:append-inner>
									<span class="keyboard-hint text-caption">
										{{ search_mode === 'barcode' ? 'F3: Text' : 'F3: Barcode' }}
									</span>
									<!-- Product Search Popup Button -->
									<v-btn
										icon="mdi-magnify-plus-outline"
										size="small"
										color="orange"
										variant="text"
										@click="openProductSearchPopup"
										:title="__('Advanced Search')"
										class="ml-1"
									>
									</v-btn>
									<!-- Add camera scan button if enabled -->
									<v-btn
										v-if="pos_profile.posa_enable_camera_scanning"
										icon="mdi-camera"
										size="small"
										color="primary"
										variant="text"
										@click="startCameraScanning"
										:title="__('Scan with Camera')"
									>
									</v-btn>
								</template>
							</v-text-field>
							<!-- Mode indicator badge -->
							<div class="mode-indicator-badge mt-1">
								<v-chip 
									:color="search_mode === 'barcode' ? 'primary' : 'orange'"
									size="x-small"
									variant="flat"
									class="mode-chip"
								>
									<v-icon size="x-small" class="mr-1">
										{{ modeIcon }}
									</v-icon>
									{{ search_mode === 'barcode' ? 'BARCODE' : 'TEXT SEARCH' }}
								</v-chip>
							</div>
						</v-col>
						<v-col cols="4" class="pb-0" v-if="pos_profile.posa_input_qty">
							<v-text-field
								ref="qtyInput"
								density="compact"
								variant="solo"
								color="primary"
								:label="frappe._('QTY')"
								hide-details
								v-model="debounce_qty"
								type="text"
								readonly
								@click="showNumPad"
								@focus="showNumPad"
								class="standard-text-field qty-input-field"
								style="cursor: pointer;"
							>
								<template v-slot:append-inner>
									<v-icon size="small" color="primary">mdi-calculator</v-icon>
								</template>
							</v-text-field>
						</v-col>
						
						<!-- 🆕 Search Results List (thay thế popup) -->
						<v-col cols="12" v-if="search_results_visible && search_results.length > 0" class="pt-0">
							<v-expand-transition>
								<v-card 
									class="search-results-card"
									:class="{ 'view-only-mode': search_results_view_only }"
									elevation="4"
								>
									<v-card-title class="py-2">
										<span class="text-subtitle-1">
											Tìm thấy {{ search_results.length }} sản phẩm
										</span>
										<v-spacer></v-spacer>
										<span class="text-caption keyboard-hint">
											Click để chọn • Esc: Đóng
										</span>
									</v-card-title>
									
									<v-list class="search-results-list" max-height="300" style="overflow-y: auto;">
										<v-list-item
											v-for="(item, index) in search_results"
											:key="item.item_code"
											:class="{ 'selected-result': index === selected_result_index }"
											@click="selectSearchResult(index)"
											class="search-result-item"
										>
											<template v-slot:prepend>
												<v-img
													:src="item.image || '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'"
													width="40"
													height="40"
													class="rounded"
												></v-img>
											</template>
											
											<v-list-item-title>{{ item.item_name }}</v-list-item-title>
											<v-list-item-subtitle>
												{{ item.item_code }} • 
												{{ format_currency(item.rate, pos_profile.currency) }}
											</v-list-item-subtitle>
											
											<template v-slot:append>
												<span class="text-caption">
													{{ item.actual_qty || 0 }} {{ item.stock_uom }}
												</span>
											</template>
										</v-list-item>
									</v-list>
								</v-card>
							</v-expand-transition>
						</v-col>
						
						<v-col cols="12" class="dynamic-margin-xs">
							<div class="settings-container">
								<v-btn
									density="compact"
									variant="text"
									color="primary"
									prepend-icon="mdi-cog-outline"
									@click="toggleItemSettings"
									class="settings-btn"
								>
									{{ __("Settings") }}
								</v-btn>
								<v-spacer></v-spacer>
								<v-btn
									density="compact"
									variant="text"
									color="primary"
									prepend-icon="mdi-refresh"
									@click="forceReloadItems"
									class="settings-btn"
								>
									{{ __("Reload Items") }}
								</v-btn>

								<v-dialog v-model="show_item_settings" max-width="400px">
									<v-card>
										<v-card-title class="text-h6 pa-4 d-flex align-center">
											<span>{{ __("Item Selector Settings") }}</span>
											<v-spacer></v-spacer>
											<v-btn
												icon="mdi-close"
												variant="text"
												density="compact"
												@click="show_item_settings = false"
											></v-btn>
										</v-card-title>
										<v-divider></v-divider>
										<v-card-text class="pa-4">
											<v-switch
												v-model="temp_hide_qty_decimals"
												:label="__('Hide quantity decimals')"
												hide-details
												density="compact"
												color="primary"
												class="mb-2"
											></v-switch>
											<v-switch
												v-model="temp_hide_zero_rate_items"
												:label="__('Hide zero rated items')"
												hide-details
												density="compact"
												color="primary"
											></v-switch>
										</v-card-text>
										<v-card-actions class="pa-4 pt-0">
											<v-btn color="error" variant="text" @click="cancelItemSettings">{{
												__("Cancel")
											}}</v-btn>
											<v-spacer></v-spacer>
											<v-btn
												color="primary"
												variant="tonal"
												@click="applyItemSettings"
												>{{ __("Apply") }}</v-btn
											>
										</v-card-actions>
									</v-card>
								</v-dialog>
							</div>
						</v-col>
					</v-row>
				</div>
			</div>

			<!-- Scrollable Items Container -->
			<div class="scrollable-items-container">
				<div class="dynamic-padding">
					<v-row class="items">
						<v-col cols="12" class="pt-0 mt-0">
							<div
								fluid
								class="items-grid dynamic-scroll"
								ref="itemsContainer"
								v-if="items_view == 'card'"
								:style="{ maxHeight: 'calc(100vh - 200px)' }"
							>
								<v-card
									v-for="item in filtered_items"
									:key="item.item_code"
									hover
									class="dynamic-item-card"
									:draggable="true"
									@dragstart="onDragStart($event, item)"
									@dragend="onDragEnd"
									@click="add_item(item)"
								>
									<v-img
										:src="
											item.image ||
											'/assets/posawesome/js/posapp/components/pos/placeholder-image.png'
										"
										class="text-white align-end"
										gradient="to bottom, rgba(0,0,0,0), rgba(0,0,0,0.4)"
										height="100px"
									>
										<v-card-text class="text-caption px-1 pb-0 truncate">{{
											item.item_name
										}}</v-card-text>
									</v-img>
									<v-card-text class="text--primary pa-1">
										<div class="text-caption text-primary truncate">
											{{
												currencySymbol(
													item.original_currency || pos_profile.currency,
												) || ""
											}}
											{{
												format_currency(
													item.custom_price_list_rate_after_vat || item.base_price_list_rate,
													item.original_currency || pos_profile.currency,
													ratePrecision(item.custom_price_list_rate_after_vat || item.base_price_list_rate),
												)
											}}
											<span v-if="item.custom_vat_rate" class="text-caption text-orange ml-1">
												(VAT {{ item.custom_vat_rate }}%)
											</span>
										</div>
										<div
											v-if="
												pos_profile.posa_allow_multi_currency &&
												selected_currency !== pos_profile.currency
											"
											class="text-caption text-success truncate"
										>
											{{ currencySymbol(selected_currency) || "" }}
											{{
												format_currency(
													item.rate,
													selected_currency,
													ratePrecision(item.rate),
												)
											}}
										</div>
										<div class="text-caption golden--text truncate">
											{{
												format_number(item.actual_qty, hide_qty_decimals ? 0 : 4) || 0
											}}
											{{ item.stock_uom || "" }}
										</div>
									</v-card-text>
								</v-card>
							</div>
							<div v-else>
								<v-data-table-virtual
									:headers="headers"
									:items="filtered_items"
									class="sleek-data-table overflow-y-auto"
									:style="{ maxHeight: 'calc(100vh - 200px)' }"
									item-key="item_code"
									@click:row="click_item_row"
								>
									<template v-slot:item.rate="{ item }">
										<div>
											<div class="text-primary">
												{{
													currencySymbol(
														item.original_currency || pos_profile.currency,
													)
												}}
												{{
													format_currency(
														item.custom_price_list_rate_after_vat || item.base_price_list_rate ,
														item.original_currency || pos_profile.currency,
														ratePrecision(item.custom_price_list_rate_after_vat || item.base_price_list_rate),
													)
												}}
												<span v-if="item.custom_vat_rate" class="text-caption text-orange ml-1">
													(VAT {{ item.custom_vat_rate }}%)
												</span>
											</div>
											<div
												v-if="
													pos_profile.posa_allow_multi_currency &&
													selected_currency !== pos_profile.currency
												"
												class="text-success"
											>
												{{ currencySymbol(selected_currency) }}
												{{
													format_currency(
														item.rate,
														selected_currency,
														ratePrecision(item.rate),
													)
												}}
											</div>
										</div>
									</template>
									<template v-slot:item.actual_qty="{ item }">
										<span class="golden--text">{{
											format_number(item.actual_qty, hide_qty_decimals ? 0 : 4)
										}}</span>
									</template>
								</v-data-table-virtual>
							</div>
						</v-col>
					</v-row>
				</div>
			</div>
		</v-card>
		<v-card class="cards mb-0 mt-3 dynamic-padding resizable" style="resize: vertical; overflow: auto">
			<v-row no-gutters align="center" justify="space-between" class="dynamic-spacing-sm">
				<v-col cols="3" class="dynamic-margin-xs">
					<v-btn-toggle
						v-model="items_view"
						color="primary"
						group
						density="compact"
						rounded
						class="summary-btn"
					>
						<v-btn size="small" value="list" min-height="60">{{ __("List") }}</v-btn>
						<v-btn size="small" value="card" min-height="60">{{ __("Card") }}</v-btn>
					</v-btn-toggle>
				</v-col>
				<v-col cols="12" class="mb-2" v-if="pos_profile.posa_enable_price_list_dropdown">
					<v-text-field
						density="compact"
						variant="solo"
						color="primary"
						:label="frappe._('Price List')"
						hide-details
						:model-value="active_price_list"
						readonly
						class="standard-text-field"
					></v-text-field>
				</v-col>
				<v-col cols="auto" class="d-flex justify-end align-center" style="gap: 5px">
					<v-btn
						color="warning"
						variant="text"
						size="default"
						@click="show_offers"
						class="icon-link-btn"
						min-height="60"
					>
						<v-icon size="default">mdi-gift</v-icon>
					</v-btn>
					<v-btn
						color="primary"
						variant="text"
						size="default"
						@click="show_coupons"
						class="icon-link-btn"
						min-height="60"
					>
						<v-icon size="default">mdi-ticket-percent</v-icon>
					</v-btn>
				</v-col>
			</v-row>
		</v-card>

		<!-- Mode Selection Section - Hidden as per requirements -->
		<!-- NLine, Add Mode, and Remove Mode buttons are now hidden -->
		<!-- Always default to Add Mode -->

		<!-- Camera Scanner Component -->
		<CameraScanner
			v-if="pos_profile.posa_enable_camera_scanning"
			ref="cameraScanner"
			:scan-type="pos_profile.posa_camera_scan_type || 'Both'"
			@barcode-scanned="onBarcodeScanned"
		/>
		
		<!-- 🆕 Product Search Popup -->
		<ProductSearchPopup
			:visible="product_search_popup_visible"
			:pos-profile="pos_profile"
			:price-list="active_price_list"
			:customer="customer"
			@close="closeProductSearchPopup"
			@add-item="onPopupAddItem"
		/>
		
		<!-- 🆕 NumPad Popup for Quantity Input -->
		<v-dialog 
			v-model="numpad_visible" 
			max-width="400px"
			persistent
			:fullscreen="$vuetify.display.mobile"
		>
			<v-card class="numpad-card">
				<v-card-title class="text-center py-3">
					<span class="text-h6">Nhập Số Lượng</span>
					<v-spacer></v-spacer>
					<v-btn 
						icon="mdi-close" 
						variant="text" 
						size="small"
						@click="hideNumPad"
					></v-btn>
				</v-card-title>
				
				<v-card-text class="pa-4">
					<!-- Display current value -->
					<v-text-field
						v-model="numpad_display"
						variant="outlined"
						readonly
						class="numpad-display text-center"
						:style="{ fontSize: '2rem', fontWeight: 'bold' }"
					></v-text-field>
					
					<!-- NumPad Grid -->
					<div class="numpad-grid mt-4">
						<!-- Row 1: 7, 8, 9 -->
						<v-btn 
							v-for="num in [7, 8, 9]" 
							:key="num"
							@click="numpadInput(num)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							{{ num }}
						</v-btn>
						
						<!-- Row 2: 4, 5, 6 -->
						<v-btn 
							v-for="num in [4, 5, 6]" 
							:key="num"
							@click="numpadInput(num)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							{{ num }}
						</v-btn>
						
						<!-- Row 3: 1, 2, 3 -->
						<v-btn 
							v-for="num in [1, 2, 3]" 
							:key="num"
							@click="numpadInput(num)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							{{ num }}
						</v-btn>
						
						<!-- Row 4: ., 0, Backspace -->
						<v-btn 
							@click="numpadInput('.')"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							•
						</v-btn>
						
						<v-btn 
							@click="numpadInput(0)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							0
						</v-btn>
						
						<v-btn 
							@click="numpadBackspace"
							class="numpad-btn"
							size="large"
							variant="outlined"
							color="warning"
						>
							<v-icon>mdi-backspace</v-icon>
						</v-btn>
						
						<!-- Row 5: Clear, Enter -->
						<v-btn 
							@click="numpadClear"
							class="numpad-btn numpad-btn-wide numpad-clear-btn"
							size="large"
							variant="outlined"
							color="error"
						>
							CLEAR
						</v-btn>
						
						<v-btn 
							@click="numpadEnter"
							class="numpad-btn numpad-btn-wide"
							size="large"
							variant="tonal"
							color="success"
						>
							ENTER
						</v-btn>
					</div>
				</v-card-text>
			</v-card>
		</v-dialog>

		<!-- 🆕 Product Confirmation Popup -->
		<v-dialog 
			v-model="product_confirmation_visible" 
			max-width="500px"
			persistent
			:fullscreen="$vuetify.display.mobile"
		>
			<v-card class="product-confirmation-card">
				<v-card-title class="text-center py-3 bg-primary text-white">
					<span class="text-h6">Xác Nhận Sản Phẩm</span>
					<v-spacer></v-spacer>
					<v-btn 
						icon="mdi-close" 
						variant="text" 
						size="small"
						color="white"
						@click="hideProductConfirmation"
					></v-btn>
				</v-card-title>
				
				<v-card-text class="pa-4" v-if="selected_product">
					<!-- Product Image and Info -->
					<div class="d-flex align-center mb-4">
						<v-img
							:src="selected_product.image || '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'"
							width="80"
							height="80"
							class="rounded mr-4"
						></v-img>
						
						<div class="flex-grow-1">
							<h3 class="text-h6 mb-1">{{ selected_product.item_name }}</h3>
							<p class="text-body-2 text-grey-darken-1 mb-1">{{ selected_product.item_code }}</p>
							<p class="text-h6 text-primary mb-0">
								{{ format_currency(selected_product.rate, pos_profile.currency) }}
								<span v-if="selected_product.custom_vat_rate" class="text-caption text-orange ml-1">
									(VAT {{ selected_product.custom_vat_rate }}%)
								</span>
							</p>
							<p class="text-caption text-grey-darken-1">
								Tồn kho: {{ selected_product.actual_qty || 0 }} {{ selected_product.stock_uom }}
							</p>
						</div>
					</div>
					
					<!-- Quantity Input -->
					<v-divider class="mb-4"></v-divider>
					<div class="quantity-section">
						<h4 class="text-subtitle-1 mb-3">Số Lượng</h4>
						
						<div class="d-flex align-center gap-3">
							<!-- Decrease Button -->
							<v-btn
								icon="mdi-minus"
								size="large"
								variant="outlined"
								color="error"
								@click="decreaseProductQuantity"
								:disabled="product_quantity <= 0.1"
							></v-btn>
							
							<!-- Quantity Display/Input -->
							<v-text-field
								v-model="product_quantity_display"
								variant="outlined"
								class="quantity-input text-center"
								readonly
								@click="showProductNumPad"
								style="cursor: pointer; max-width: 120px;"
							>
								<template v-slot:append-inner>
									<v-icon size="small" color="primary">mdi-calculator</v-icon>
								</template>
							</v-text-field>
							
							<!-- Increase Button -->
							<v-btn
								icon="mdi-plus"
								size="large"
								variant="outlined"
								color="success"
								@click="increaseProductQuantity"
							></v-btn>
						</div>
						
						<!-- Quick Quantity Buttons -->
						<div class="d-flex gap-2 mt-3 justify-center">
							<v-btn
								v-for="qty in [1, 2, 5, 10]"
								:key="qty"
								@click="setProductQuantity(qty)"
								size="small"
								variant="outlined"
								:color="product_quantity === qty ? 'primary' : 'default'"
							>
								{{ qty }}
							</v-btn>
						</div>
					</div>
					
					<!-- Total Price -->
					<v-divider class="my-4"></v-divider>
					<div class="total-section text-center">
						<h4 class="text-subtitle-1 mb-2">Tổng Tiền</h4>
						<p class="text-h5 text-primary font-weight-bold">
							{{ format_currency(selected_product.rate * product_quantity, pos_profile.currency) }}
						</p>
					</div>
				</v-card-text>
				
				<v-card-actions class="pa-4 pt-0">
					<v-btn 
						color="error" 
						variant="outlined" 
						@click="hideProductConfirmation"
						class="flex-grow-1"
					>
						Hủy
					</v-btn>
					<v-btn 
						color="success" 
						variant="tonal" 
						@click="confirmAddProduct"
						class="flex-grow-1 ml-2"
						:disabled="!product_quantity || product_quantity <= 0"
					>
						Thêm Vào Giỏ Hàng
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- 🆕 Product NumPad Popup -->
		<v-dialog 
			v-model="product_numpad_visible" 
			max-width="400px"
			persistent
			:fullscreen="$vuetify.display.mobile"
		>
			<v-card class="numpad-card">
				<v-card-title class="text-center py-3">
					<span class="text-h6">Nhập Số Lượng Sản Phẩm</span>
					<v-spacer></v-spacer>
					<v-btn 
						icon="mdi-close" 
						variant="text" 
						size="small"
						@click="hideProductNumPad"
					></v-btn>
				</v-card-title>
				
				<v-card-text class="pa-4">
					<!-- Display current value -->
					<v-text-field
						v-model="product_numpad_display"
						variant="outlined"
						readonly
						class="numpad-display text-center"
						:style="{ fontSize: '2rem', fontWeight: 'bold' }"
					></v-text-field>
					
					<!-- NumPad Grid -->
					<div class="numpad-grid mt-4">
						<!-- Row 1: 7, 8, 9 -->
						<v-btn 
							v-for="num in [7, 8, 9]" 
							:key="num"
							@click="productNumpadInput(num)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							{{ num }}
						</v-btn>
						
						<!-- Row 2: 4, 5, 6 -->
						<v-btn 
							v-for="num in [4, 5, 6]" 
							:key="num"
							@click="productNumpadInput(num)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							{{ num }}
						</v-btn>
						
						<!-- Row 3: 1, 2, 3 -->
						<v-btn 
							v-for="num in [1, 2, 3]" 
							:key="num"
							@click="productNumpadInput(num)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							{{ num }}
						</v-btn>
						
						<!-- Row 4: ., 0, Backspace -->
						<v-btn 
							@click="productNumpadInput('.')"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							•
						</v-btn>
						
						<v-btn 
							@click="productNumpadInput(0)"
							class="numpad-btn"
							size="large"
							variant="outlined"
						>
							0
						</v-btn>
						
						<v-btn 
							@click="productNumpadBackspace"
							class="numpad-btn"
							size="large"
							variant="outlined"
							color="warning"
						>
							<v-icon>mdi-backspace</v-icon>
						</v-btn>
						
						<!-- Row 5: Clear, Enter -->
						<v-btn 
							@click="productNumpadClear"
							class="numpad-btn numpad-btn-wide numpad-clear-btn"
							size="large"
							variant="outlined"
							color="error"
						>
							CLEAR
						</v-btn>
						
						<v-btn 
							@click="productNumpadEnter"
							class="numpad-btn numpad-btn-wide"
							size="large"
							variant="tonal"
							color="success"
						>
							ENTER
						</v-btn>
					</div>
				</v-card-text>
			</v-card>
		</v-dialog>
	</div>
</template>

<script type="module">
import format from "../../format";
import _ from "lodash";
import CameraScanner from "./CameraScanner.vue";
import ProductSearchPopup from "./ProductSearchPopup.vue";
import { ensurePosProfile } from "../../../utils/pos_profile.js";
import {
	saveItemUOMs,
	getItemUOMs,
	getLocalStock,
	isOffline,
	initializeStockCache,
	getItemsStorage,
	setItemsStorage,
	getLocalStockCache,
	setLocalStockCache,
	initPromise,
	checkDbHealth,
	getCachedPriceListItems,
	savePriceListItems,
	updateLocalStockCache,
	isStockCacheReady,
	getCachedItemDetails,
	saveItemDetailsCache,
} from "../../../offline/index.js";
import { responsiveMixin } from "../../mixins/responsive.js";

export default {
	mixins: [format, responsiveMixin],
	components: {
		CameraScanner,
		ProductSearchPopup,
	},
	data: () => ({
		pos_profile: "",
		flags: {},
		items_view: "list",
		loading: false,
		items: [],
		search: "",
		first_search: "",
		search_backup: "",
		// Limit the displayed items to avoid overly large lists
		itemsPerPage: 50,
		offersCount: 0,
		appliedOffersCount: 0,
		couponsCount: 0,
		appliedCouponsCount: 0,
		customer_price_list: null,
		customer: null,
		new_line: false,
		qty: 1,
		refresh_interval: null,
		currentRequest: null,
		abortController: null,
		itemDetailsRetryCount: 0,
		itemDetailsRetryTimeout: null,
		items_loaded: false,
		selected_currency: "",
		exchange_rate: 1,
		prePopulateInProgress: false,
		itemWorker: null,
		items_request_token: 0,
		show_item_settings: false,
		hide_qty_decimals: false,
		temp_hide_qty_decimals: false,
		hide_zero_rate_items: false,
		temp_hide_zero_rate_items: false,
		isDragging: false,
		// Track if the current search was triggered by a scanner
		search_from_scanner: false,
		// Track the current scan mode: true for Add, false for Remove
		scan_add_mode: true,
		// Prevent multiple simultaneous scan processing
		processing_scan: false,
		// Prevent duplicate scans within short time period
		_lastScanCode: null,
		_lastScanAt: 0,
		// Prevent multiple simultaneous search processing
		processing_search: false,
		// Queue for sequential search processing
		search_queue: [],
		// Current search operation ID
		current_search_id: 0,
		// Abort controller for current search
		current_search_controller: null,
		// Debounce for barcode scanning to prevent duplicate scans
		lastScanTime: 0,
		scanDebounceMs: 160,
		
		// 🆕 Search Mode Management
		search_mode: 'barcode', // 'barcode' | 'text'
		
		// 🆕 Keyboard State
		f2_enabled: true,
		f3_enabled: true,
		
		// 🆕 Search Results State (thay thế popup)
		search_results: [],
		search_results_visible: false,
		selected_result_index: 0,
		search_results_view_only: false, // Track if results are view-only
		
		// 🆕 Product Search Popup State
		product_search_popup_visible: false,
		
		// 🆕 UI State
		current_focus_element: null,
		is_processing_barcode: false,
		
		// 🆕 NumPad State
		numpad_visible: false,
		numpad_display: '',
		numpad_original_qty: null,
		
		// 🆕 Product Confirmation State
		product_confirmation_visible: false,
		selected_product: null,
		product_quantity: 1,
		product_quantity_display: '1',
		
		// 🆕 Product NumPad State
		product_numpad_visible: false,
		product_numpad_display: '',
	}),

	watch: {
		customer: _.debounce(function () {
			if (this.pos_profile.posa_force_reload_items) {
				if (this.pos_profile.posa_smart_reload_mode) {
					// When limit search is enabled there may be no items yet.
					// Fallback to full reload if nothing is loaded
					if (!this.items_loaded || !this.filtered_items.length) {
						this.items_loaded = false;
						this.get_items(true);
					} else {
						// Only refresh prices for visible items when smart reload is enabled
						this.$nextTick(() => this.refreshPricesForVisibleItems());
					}
				} else {
					// Fall back to full reload
					this.items_loaded = false;
					this.get_items(true);
				}
				return;
			}
			// When the customer changes, avoid reloading all items.
			// Simply refresh prices for visible items only
			if (this.items_loaded && this.filtered_items && this.filtered_items.length > 0) {
				this.$nextTick(() => this.refreshPricesForVisibleItems());
			} else {
				this.get_items();
			}
		}, 300),
		customer_price_list: _.debounce(function () {
			if (this.pos_profile.posa_force_reload_items) {
				if (this.pos_profile.posa_smart_reload_mode) {
					// When limit search is enabled there may be no items yet.
					// Fallback to full reload if nothing is loaded
					if (!this.items_loaded || !this.items.length) {
						this.items_loaded = false;
						this.get_items(true);
					} else {
						// Only refresh prices for visible items when smart reload is enabled
						this.$nextTick(() => this.refreshPricesForVisibleItems());
					}
				} else {
					// Fall back to full reload
					this.items_loaded = false;
					this.get_items(true);
				}
				return;
			}
			// Apply cached rates if available for immediate update
			if (this.items_loaded && this.items && this.items.length > 0) {
				const cached = getCachedPriceListItems(this.customer_price_list);
				if (cached && cached.length) {
					const map = {};
					cached.forEach((ci) => {
						map[ci.item_code] = ci;
					});
					this.items.forEach((it) => {
						const ci = map[it.item_code];
						if (ci) {
							it.rate = ci.rate;
							it.price_list_rate = ci.price_list_rate || ci.rate;
						}
					});
					this.eventBus.emit("set_all_items", this.items);
					this.update_items_details(this.items);
					return;
				}
			}
			// No cache found - force a reload so prices are updated
			this.items_loaded = false;
			this.get_items(true);
		}, 300),
		new_line() {
			this.eventBus.emit("set_new_line", this.new_line);
		},
		filtered_items(new_value, old_value) {
			// Update item details if items changed
			if (!this.pos_profile.pose_use_limit_search && new_value.length !== old_value.length) {
				this.update_items_details(new_value);
			}
		},
		// Automatically search and add item whenever the query changes
		first_search: _.debounce(function (val) {
			// Only auto-search in barcode mode or when from scanner
			// In text mode, user must press Enter to search
			console.log(`[WATCHER] first_search changed: "${val}", mode: ${this.search_mode}, from_scanner: ${this.search_from_scanner}`);
			if (this.search_mode === 'barcode' || this.search_from_scanner) {
				console.log('[WATCHER] Triggering auto-search');
				this.queueSearch(val, this.search_from_scanner);
			} else {
				console.log('[WATCHER] Text mode - no auto-search, waiting for Enter');
			}
		}, 300), // Increased debounce time to match search debounce

		// Refresh item prices whenever the user changes currency
		selected_currency() {
			this.applyCurrencyConversionToItems();
		},

		// Also react when exchange rate is adjusted manually
		exchange_rate() {
			this.applyCurrencyConversionToItems();
		},
		windowWidth(val) {
			this.adjustItemsPerPage(val, this.windowHeight);
		},
		windowHeight(val) {
			this.adjustItemsPerPage(this.windowWidth, val);
		},
	},

	computed: {
		headers() {
			return this.getItemsHeaders();
		},
		
		// 🆕 Dynamic UI Properties
		dynamicPlaceholder() {
			return this.search_mode === 'barcode' 
				? 'Quét / nhập Barcode'
				: 'Nhập tên / SKU sản phẩm';
		},
		
		dynamicHint() {
			return this.search_mode === 'barcode'
				? 'F3 – Chuyển sang tìm theo Tên / SKU'
				: 'F3 – Quay về quét Barcode';
		},
		
		modeIcon() {
			return this.search_mode === 'barcode' ? 'mdi-barcode-scan' : 'mdi-magnify';
		},
		
		modeColor() {
			return this.search_mode === 'barcode' ? 'primary' : 'orange';
		},
		
		filtered_items() {
			// In text mode, don't auto-filter while typing - only show all items
			// User will search by pressing Enter which triggers handleTextSearchEnter()
			if (this.search_mode === 'text') {
				console.log('[TEXT_MODE] filtered_items: showing all items, no auto-filter');
				// Show all items without filtering in text mode
				let filtered = [];
				if (
					this.pos_profile.posa_show_template_items &&
					this.pos_profile.posa_hide_variants_items
				) {
					filtered = this.items
						.filter((item) => !item.variant_of)
						.slice(0, this.itemsPerPage);
				} else {
					filtered = this.items.slice(0, this.itemsPerPage);
				}

				if (this.hide_zero_rate_items) {
					filtered = filtered.filter((item) => parseFloat(item.rate) !== 0);
				}

				// Ensure quantities are defined
				filtered.forEach((item) => {
					if (item.actual_qty === undefined) {
						item.actual_qty = 0;
					}
				});

				return filtered;
			}

			// Barcode mode: continue with original logic
			this.search = this.get_search(this.first_search).trim();
			
			if (!this.pos_profile.pose_use_limit_search) {
				let filtred_list = [];
				let filtred_group_list = this.items;
				if (!this.search || this.search.length < 3) {
					let filtered = [];
					if (
						this.pos_profile.posa_show_template_items &&
						this.pos_profile.posa_hide_variants_items
					) {
						filtered = filtred_group_list
							.filter((item) => !item.variant_of)
							.slice(0, this.itemsPerPage);
					} else {
						filtered = filtred_group_list.slice(0, this.itemsPerPage);
					}

					if (this.hide_zero_rate_items) {
						filtered = filtered.filter((item) => parseFloat(item.rate) !== 0);
					}

					// Ensure quantities are defined
					filtered.forEach((item) => {
						if (item.actual_qty === undefined) {
							item.actual_qty = 0;
						}
					});

					return filtered;
				} else if (this.search) {
					const term = this.search.toLowerCase();
					// Match barcode directly
					filtred_list = filtred_group_list.filter((item) =>
						item.item_barcode.some((b) => b.barcode === this.search),
					);

					if (filtred_list.length === 0) {
						// Match by code or name containing the term
						filtred_list = filtred_group_list.filter(
							(item) =>
								item.item_code.toLowerCase().includes(term) ||
								item.item_name.toLowerCase().includes(term),
						);
					}

					if (filtred_list.length === 0) {
						// Fallback to partial fuzzy match on name
						const search_combinations = this.generateWordCombinations(this.search);
						filtred_list = filtred_group_list.filter((item) => {
							const nameLower = item.item_name.toLowerCase();
							return search_combinations.some((element) => {
								element = element.toLowerCase().trim();
								const element_regex = new RegExp(`.*${element.split("").join(".*")}.*`);
								return element_regex.test(nameLower);
							});
						});
					}

					if (filtred_list.length === 0 && this.pos_profile.posa_search_serial_no) {
						filtred_list = filtred_group_list.filter((item) => {
							for (let element of item.serial_no_data) {
								if (element.serial_no === this.search) {
									this.flags.serial_no = this.search;
									return true;
								}
							}
							return false;
						});
					}

					if (filtred_list.length === 0 && this.pos_profile.posa_search_batch_no) {
						filtred_list = filtred_group_list.filter((item) => {
							for (let element of item.batch_no_data) {
								if (element.batch_no === this.search) {
									this.flags.batch_no = this.search;
									return true;
								}
							}
							return false;
						});
					}
				}

				let final_filtered_list = [];
				if (this.pos_profile.posa_show_template_items && this.pos_profile.posa_hide_variants_items) {
					final_filtered_list = filtred_list
						.filter((item) => !item.variant_of)
						.slice(0, this.itemsPerPage);
				} else {
					final_filtered_list = filtred_list.slice(0, this.itemsPerPage);
				}

				if (this.hide_zero_rate_items) {
					final_filtered_list = final_filtered_list.filter((item) => parseFloat(item.rate) !== 0);
				}

				// Ensure quantities are defined for each item
				final_filtered_list.forEach((item) => {
					if (item.actual_qty === undefined) {
						item.actual_qty = 0;
					}
				});

				// Item details will be refreshed via watchers when the filtered
				// list length changes. Removing the automatic call here prevents
				// redundant requests each time this computed property re-evaluates.

				return final_filtered_list;
			} else {
				const items_list = this.items.slice(0, this.itemsPerPage);

				// Ensure quantities are defined
				items_list.forEach((item) => {
					if (item.actual_qty === undefined) {
						item.actual_qty = 0;
					}
				});

				if (this.hide_zero_rate_items) {
					return items_list.filter((item) => parseFloat(item.rate) !== 0);
				}

				return items_list;
			}
		},
		debounce_search: {
			get() {
				return this.first_search;
			},
			set: _.debounce(function (newValue) {
				// Only trim in barcode mode
				if (this.search_mode === 'barcode') {
					this.first_search = (newValue || "").trim();
				} else {
					this.first_search = newValue || "";
				}
			}, 300), // Increased debounce time to prevent rapid consecutive inputs
		},
		// Computed property cho hộp nhập số lượng (QTY) - fix bug xóa dấu thập phân khi nhập
		// - Khi hide_qty_decimals = true: Làm tròn xuống số nguyên bằng Math.trunc() (loại bỏ phần thập phân, không làm tròn lên)
		// - Khi hide_qty_decimals = false: Giữ nguyên giá trị thập phân
		debounce_qty: {
			get() {
				// Display the raw quantity while typing to avoid forced decimal format
				if (this.qty === null || this.qty === "") return "";
				// Tạm thời comment cơ chế làm tròn: return this.hide_qty_decimals ? Math.trunc(this.qty) : this.qty;
				return this.qty; // Không làm tròn, giữ nguyên giá trị
			},
			set: _.debounce(function (value) {
				let cleanValue = String(value).replace(/,/g, "");

				// Fix bug: Nếu user đang nhập decimal (kết thúc bằng "."), giữ nguyên để tránh mất dấu chấm
				if (cleanValue.match(/^\d+\.$/)) {
					this.qty = cleanValue; // Giữ "1.", "2.", etc. như string
					return;
				}

				let parsed = parseFloat(cleanValue);
				if (isNaN(parsed)) {
					parsed = null;
				}
				// Tạm thời comment cơ chế làm tròn:
				// if (this.hide_qty_decimals && parsed != null) {
				//     parsed = Math.trunc(parsed); // Làm tròn xuống số nguyên
				// }
				this.qty = parsed;
			}, 300), // Increased debounce time to match search debounce
		},
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
		active_price_list() {
			return this.customer_price_list || (this.pos_profile && this.pos_profile.selling_price_list);
		},
	},

	methods: {
		// Helper nhận diện barcode (≥6–8 ký tự, tinh chỉnh theo chuẩn UPC/EAN)
		looksLikeBarcode(code) {
			if (!code || typeof code !== "string") return false;
			const cleanCode = code.trim();
			// Barcode thường ≥6 ký tự, chứa số, có thể có ký tự đặc biệt
			return cleanCode.length >= 6 && /^\d{6,}$/.test(cleanCode.replace(/[-\s]/g, ""));
		},

		// Enhanced barcode validation to prevent malformed barcodes
		isValidBarcode(code) {
			if (!this.looksLikeBarcode(code)) return false;

			// Additional validation: check for scale barcode format
			if (
				this.pos_profile.posa_scale_barcode_start &&
				code.startsWith(this.pos_profile.posa_scale_barcode_start)
			) {
				// Scale barcode must have at least prefix + 5 digits for weight
				return code.length >= this.pos_profile.posa_scale_barcode_start.length + 5;
			}

			// Standard barcode validation
			const cleanCode = code.replace(/[-\s]/g, "");
			// Must be numeric and reasonable length (6-18 digits for standard barcodes)
			return /^\d{6,18}$/.test(cleanCode);
		},

		// 🎹 KEYBOARD EVENT HANDLERS
		handleKeyDown(event) {
			// Log F2/F3 key press for debugging
			if (event.key === 'F2' || event.key === 'F3') {
				console.info(`[handleKeyDown] ${event.key} pressed`);
			}
			
			// Prevent default and stop propagation for special keys
			if (['F2', 'F3', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
				event.preventDefault();
				event.stopPropagation();
				event.stopImmediatePropagation();
			}
			
			switch(event.key) {
				case 'F2':
					console.info('[handleKeyDown] Calling handleF2Reset');
					this.handleF2Reset();
					break;
				case 'F3':
					console.info('[handleKeyDown] Calling handleF3SearchToggle');
					this.handleF3SearchToggle();
					break;
				case 'Enter':
					event.preventDefault();
					this.handleEnterKey();
					break;
				case 'Escape':
					event.preventDefault();
					this.handleEscapeKey();
					break;
				case 'ArrowUp':
					if (this.search_results_visible) {
						this.navigateResults(-1);
					}
					break;
				case 'ArrowDown':
					if (this.search_results_visible) {
						this.navigateResults(1);
					}
					break;
			}
		},
		
		// Global keyboard listener
		globalKeyHandler(event) {
			// Log F2/F3 key press for debugging
			if (event.key === 'F2' || event.key === 'F3') {
				console.info(`[Global] ${event.key} pressed, numpad_visible:`, this.numpad_visible, 
					'product_numpad_visible:', this.product_numpad_visible,
					'product_confirmation_visible:', this.product_confirmation_visible);
			}
			
			// Handle NumPad keyboard input (both regular and product)
			if (this.numpad_visible || this.product_numpad_visible) {
				this.handleNumPadKeyboard(event);
				return;
			}
			
			// Handle Product Confirmation popup keyboard input
			if (this.product_confirmation_visible) {
				event.preventDefault();
				event.stopPropagation();
				
				if (event.key === 'Escape') {
					this.hideProductConfirmation();
				} else if (event.key === 'Enter') {
					this.confirmAddProduct();
				} else if (event.key === '+' || event.key === '=') {
					this.increaseProductQuantity();
				} else if (event.key === '-') {
					this.decreaseProductQuantity();
				} else if (/^[1-9]$/.test(event.key)) {
					// Quick quantity selection with number keys
					const qty = parseInt(event.key);
					if ([1, 2, 3, 4, 5, 6, 7, 8, 9].includes(qty)) {
						this.setProductQuantity(qty);
					}
				}
				return;
			}
			
			// Handle F2/F3 globally, even when input not focused
			if (event.key === 'F2' || event.key === 'F3') {
				console.info(`[Global] Handling ${event.key} globally - preventing default and stopping propagation`);
				event.preventDefault();
				event.stopPropagation();
				event.stopImmediatePropagation();
				this.handleKeyDown(event);
			}
		},
		
		// Handle keyboard input when NumPad is visible
		handleNumPadKeyboard(event) {
			event.preventDefault();
			
			const key = event.key;
			
			// Check if Product NumPad is visible
			if (this.product_numpad_visible) {
				// Handle Product NumPad keyboard input
				if (/^[0-9]$/.test(key)) {
					this.productNumpadInput(parseInt(key));
				} else if (key === '.' || key === ',') {
					this.productNumpadInput('.');
				} else if (key === 'Backspace') {
					this.productNumpadBackspace();
				} else if (key === 'Delete') {
					this.productNumpadClear();
				} else if (key === 'Enter') {
					this.productNumpadEnter();
				} else if (key === 'Escape') {
					this.hideProductNumPad();
				} else if (key.toLowerCase() === 'c') {
					this.productNumpadClear();
				}
				return;
			}
			
			// Handle regular NumPad keyboard input
			if (/^[0-9]$/.test(key)) {
				this.numpadInput(parseInt(key));
			}
			// Decimal point
			else if (key === '.' || key === ',') {
				this.numpadInput('.');
			}
			// Backspace
			else if (key === 'Backspace') {
				this.numpadBackspace();
			}
			// Clear (Delete key)
			else if (key === 'Delete') {
				this.numpadClear();
			}
			// Enter
			else if (key === 'Enter') {
				this.numpadEnter();
			}
			// Escape - close NumPad
			else if (key === 'Escape') {
				this.hideNumPad();
			}
			// C key for clear
			else if (key.toLowerCase() === 'c') {
				this.numpadClear();
			}
		},
		
		// 🔹 F2 - RESET TO BARCODE MODE AND FOCUS
		handleF2Reset: _.debounce(function() {
			if (!this.f2_enabled) {
				console.warn('[F2] F2 is disabled, ignoring');
				return;
			}
			
			console.info('[F2] ALWAYS reset to Barcode mode and focus, current mode:', this.search_mode);
			
			// 1️⃣ Hide search results and popups
			this.hideSearchResults();
			this.hideProductConfirmation();
			
			// 🆕 Close NumPad if open
			if (this.numpad_visible) {
				this.hideNumPad();
				return; // NumPad will handle focus return
			}
			
			// 2️⃣ Clear all focus states
			this.clearAllFocus();
			
			// 3️⃣ ALWAYS reset to barcode mode
			this.search_mode = 'barcode';
			
			// 4️⃣ Clear search input
			this.clearSearch();
			
			// 5️⃣ Focus back to search input
			this.focusSearchInput();
			
			// 6️⃣ Reset processing states
			this.resetProcessingStates();
			
			// Show feedback - removed for speed
			console.info('[F2] Mode set to Barcode + Focus');
			
			console.info('[F2] Mode set to:', this.search_mode);
		}, 200), // Debounce 200ms to prevent multiple calls
		
		// 🔹 F3 - SWITCH TO TEXT SEARCH MODE (SEARCH ONLY)
		handleF3SearchToggle: _.debounce(function() {
			console.info('[F3] handleF3SearchToggle called, f3_enabled:', this.f3_enabled);
			if (!this.f3_enabled) {
				console.warn('[F3] F3 is disabled, ignoring');
				return;
			}
			
			console.info('[F3] ALWAYS switching to Text Search mode (view-only), current mode:', this.search_mode);
			
			// Hide any popups and results
			this.hideSearchResults();
			this.hideProductConfirmation();
			
			// ALWAYS switch to text mode (F3 = Text Search ONLY, no toggle)
			this.search_mode = 'text';
			
			// Clear current search
			this.clearSearch();
			
			// Keep focus on input
			this.$nextTick(() => {
				this.focusSearchInput();
			});
			
			// Show mode change feedback - removed for speed
			console.info('[F3] Mode set to Text Search');
			
			console.info('[F3] Mode set to:', this.search_mode);
		}, 200), // Debounce 200ms to prevent multiple calls
		
		// 🎯 ENTER KEY ROUTER
		handleEnterKey() {
			if (this.search_results_visible) {
				// Có kết quả tìm kiếm đang hiển thị
				this.selectCurrentResult();
			} else if (this.search_mode === 'barcode') {
				this.handleBarcodeEnter();
			} else {
				this.handleTextSearchEnter();
			}
		},
		
		handleEscapeKey() {
			if (this.search_results_visible) {
				this.hideSearchResults();
				this.focusSearchInput();
			} else {
				this.clearSearch();
				this.focusSearchInput();
			}
		},
		
		// 📱 BARCODE MODE ENTER
		async handleBarcodeEnter() {
			const barcode = this.debounce_search.trim();
			
			if (!barcode) return;
			
			// Prevent double processing
			if (this.is_processing_barcode) return;
			this.is_processing_barcode = true;
			
			try {
				console.info('[Manual Barcode Entry] Processing:', barcode);
				
				// Validate barcode format
				if (!this.isValidBarcode(barcode)) {
					this.showError('Mã vạch không hợp lệ', 'red');
					this.selectAllSearchText();
					return;
				}
				
				// Find item by barcode
				const item = await this.findItemByBarcode(barcode);
				
				if (item) {
					// ✅ Found - add to cart
					await this.addItemToCart(item);
					this.showSuccess(`✅ Đã thêm vào giỏ hàng: ${item.item_name}`);
					this.clearSearchAndRefocus();
				} else {
					// ❌ Not found
					this.showError('❌ Không tìm thấy sản phẩm với mã vạch này', 'red');
					this.selectAllSearchText();
				}
				
			} catch (error) {
				console.error('[Manual Barcode Entry] Error:', error);
				this.showError('❌ Lỗi xử lý mã vạch', 'red');
			} finally {
				this.is_processing_barcode = false;
			}
		},
		
		// 🔍 TEXT SEARCH MODE ENTER (WITH PRODUCT CONFIRMATION)
		async handleTextSearchEnter() {
			const searchTerm = this.debounce_search.trim();
			
			if (!searchTerm || searchTerm.length < 2) {
				this.showError('Nhập ít nhất 2 ký tự', 'orange');
				return;
			}
			
			try {
				console.info('[Text Mode] Searching with confirmation popup:', searchTerm);
				
				const results = await this.searchItemsByText(searchTerm);
				
				if (results.length === 0) {
					this.showError('Không tìm thấy sản phẩm', 'orange');
					this.selectAllSearchText();
				} else if (results.length === 1) {
					// ✅ Single result - show confirmation popup directly
					console.info('[Text Mode] Single result - showing confirmation popup');
					this.showProductConfirmation(results[0]);
				} else {
					// 📋 Multiple results - show list for selection
					console.info('[Text Mode] Multiple results - showing selection list');
					this.showSearchResults(results, false); // false = allow selection
					// Alert removed for speed
					console.info(`[Text Search] Found ${results.length} products`);
				}
				
			} catch (error) {
				console.error('[Text Mode] Error:', error);
				this.showError('Lỗi tìm kiếm', 'orange');
			}
		},
		
		// Helper method để tiếp tục với normal search logic (không phải barcode)
		continueWithNormalSearch(fromScanner) {
			if (this.pos_profile.pose_use_limit_search) {
				// Only trigger search when query length meets minimum threshold
				if (this.search && this.search.length >= 3) {
					this.get_items();
				}
			} else {
				// Save the current filtered items before search to maintain quantity data
				const current_items = [...this.filtered_items];
				if (this.search && this.search.length >= 3) {
					this.enter_event();
				}

				// After search, update quantities for newly filtered items
				if (this.filtered_items && this.filtered_items.length > 0) {
					setTimeout(() => {
						this.update_items_details(this.filtered_items);
					}, 300);
				}
			}

			// Clear the input only when triggered via scanner
			if (fromScanner) {
				this.clearSearch();
				this.$refs.debounce_search && this.$refs.debounce_search.focus();
				this.search_from_scanner = false;
			}
		},

		// Helper method để tiếp tục với local search logic
		// 🚫 DEPRECATED: continueWithLocalSearch - Không còn sử dụng
		/*
		async continueWithLocalSearch(searchKey) {
			// Method này đã được thay thế bằng luồng thống nhất handleBarcodeEnter()
		},
		*/

		// 🆕 Method chỉ lấy item data từ API, không add (tránh double add)
		async getItemByBarcodeExact(rawCode) {
			try {
				console.info("[ItemsSelector] 🔍 Getting exact barcode match for:", rawCode);

				const response = await frappe.call({
					method: "posawesome.posawesome.api.items.get_item_by_barcode_exact",
					args: {
						barcode: rawCode,
						pos_profile: JSON.stringify(this.pos_profile),
						price_list: this.active_price_list,
						customer: this.customer,
					},
					// Support for abort controller if available
					signal: this.current_search_controller
						? this.current_search_controller.signal
						: undefined,
				});

				// Check if search was cancelled after API call
				if (this.current_search_controller && this.current_search_controller.signal.aborted) {
					throw new Error("Search cancelled");
				}

				if (response.message) {
					const item = response.message;
					console.info("[ItemsSelector] ✅ Exact barcode match found:", item.item_code);

					// ✅ ĐẢM BẢO UOM từ backend (đã validate và chính xác)
					if (!item.uom) {
						console.error(
							"[ItemsSelector] ❌ Backend returned item without UOM:",
							item.item_code,
						);
						console.error(`[Barcode] Item ${item.item_name} missing UOM`);
						return null;
					}

					// ✅ VALIDATE: Đảm bảo UOM tồn tại trong item_uoms
					if (item.item_uoms && item.item_uoms.length > 0) {
						const uomExists = item.item_uoms.some((uom) => uom.uom === item.uom);
						if (!uomExists) {
							console.error(
								"[ItemsSelector] ❌ UOM validation failed:",
								item.uom,
								"not in item_uoms",
							);
							console.error(`[Barcode] Invalid UOM for item ${item.item_name}`);
							return null;
						}
					}

					// Check cancellation before returning item
					if (this.current_search_controller && this.current_search_controller.signal.aborted) {
						throw new Error("Search cancelled");
					}

					return item; // Return item data only, don't add
				} else {
					console.info("[ItemsSelector] ❌ No exact barcode match for:", rawCode);
					return null; // No match found
				}
			} catch (error) {
				if (error.name === "AbortError" || error.message === "Search cancelled") {
					throw error; // Re-throw cancellation errors
				}
				console.error("[ItemsSelector] Error getting exact barcode:", error);
				return null;
			}
		},

		// 🚫 DEPRECATED: fetchExactBarcodeAndAdd - Gây double add, đã thay thế bằng getItemByBarcodeExact
		// Method này gọi add_item() bên trong, gây ra double add khi được gọi từ handleBarcodeEnter
		// Đã thay thế bằng getItemByBarcodeExact() chỉ trả về item data
		/*
		async fetchExactBarcodeAndAdd(rawCode) {
			// DEPRECATED - causes double add
			// Use getItemByBarcodeExact() instead
		}
		*/
		adjustItemsPerPage(width, height = this.windowHeight) {
			const cardWidth = 200; // approximate width of each item card
			const cardHeight = 160; // approximate height including margins
			const containerHeight = height * 0.68; // card container is ~68% of viewport
			const columns = Math.max(1, Math.floor(width / cardWidth));
			const rows = Math.max(1, Math.floor(containerHeight / cardHeight));
			this.itemsPerPage = columns * rows;
		},
		refreshPricesForVisibleItems() {
			const vm = this;
			if (!vm.filtered_items || vm.filtered_items.length === 0) return;

			vm.loading = true;

			// Cancel previous request if any
			if (vm.currentRequest) {
				vm.abortController.abort();
				vm.currentRequest = null;
			}

			const itemCodes = vm.filtered_items.map((it) => it.item_code);
			const cacheResult = getCachedItemDetails(vm.pos_profile.name, vm.active_price_list, itemCodes);
			const updates = [];

			cacheResult.cached.forEach((det) => {
				const item = vm.filtered_items.find((it) => it.item_code === det.item_code);
				if (item) {
					const upd = {
						actual_qty: det.actual_qty,
						serial_no_data: det.serial_no_data,
						batch_no_data: det.batch_no_data,
					};
					if (det.item_uoms && det.item_uoms.length > 0) {
						upd.item_uoms = det.item_uoms;
						saveItemUOMs(item.item_code, det.item_uoms);
					}
					if (det.rate !== undefined) {
						if (det.rate !== 0 || !item.rate) {
							upd.rate = det.rate;
							upd.price_list_rate = det.price_list_rate || det.rate;
						}
					}
					updates.push({ item, upd });
				}
			});

			if (cacheResult.missing.length === 0) {
				vm.$nextTick(() => {
					updates.forEach(({ item, upd }) => Object.assign(item, upd));
					updateLocalStockCache(cacheResult.cached);
					vm.loading = false;
				});
				return;
			}

			vm.abortController = new AbortController();
			const itemsToFetch = vm.filtered_items.filter((it) => cacheResult.missing.includes(it.item_code));

			frappe.call({
				method: "posawesome.posawesome.api.items.get_items_details",
				args: {
					pos_profile: JSON.stringify(vm.pos_profile),
					items_data: JSON.stringify(itemsToFetch),
					price_list: vm.active_price_list,
				},
				freeze: false,
				signal: vm.abortController.signal,
				callback: function (r) {
					if (r.message) {
						r.message.forEach((updItem) => {
							const item = vm.filtered_items.find((it) => it.item_code === updItem.item_code);
							if (item) {
								const upd = {
									actual_qty: updItem.actual_qty,
									serial_no_data: updItem.serial_no_data,
									batch_no_data: updItem.batch_no_data,
								};
								if (updItem.item_uoms && updItem.item_uoms.length > 0) {
									upd.item_uoms = updItem.item_uoms;
									saveItemUOMs(item.item_code, updItem.item_uoms);
								}
								if (updItem.rate !== undefined) {
									if (updItem.rate !== 0 || !item.rate) {
										upd.rate = updItem.rate;
										upd.price_list_rate = updItem.price_list_rate || updItem.rate;
									}
								}
								updates.push({ item, upd });
							}
						});

						vm.$nextTick(() => {
							updates.forEach(({ item, upd }) => Object.assign(item, upd));
							updateLocalStockCache(r.message);
							saveItemDetailsCache(vm.pos_profile.name, vm.active_price_list, r.message);
							vm.loading = false;
						});
					}
				},
				error: function (err) {
					if (err.name !== "AbortError") {
						console.error("Error fetching item details:", err);
						vm.loading = false;
					}
				},
			});
		},

		show_offers() {
			console.log("🎁 [ITEMS_SELECTOR] Button Offer clicked - opening offers dialog");
			console.log("🎁 [ITEMS_SELECTOR] Emitting 'show_offers' event with value: 'true'");
			console.log("🎁 [ITEMS_SELECTOR] Current POS Profile:", this.pos_profile?.name);
			console.log("🎁 [ITEMS_SELECTOR] Current customer:", this.customer);
			console.log("🎁 [ITEMS_SELECTOR] Customer info:", this.customer_info);

			// Emit event để PosOffers component load danh sách offers
			this.eventBus.emit("show_offers", "true");

			console.log("🎁 [ITEMS_SELECTOR] Event emitted successfully");
		},
		show_coupons() {
			this.eventBus.emit("show_coupons", "true");
		},
		forceReloadItems() {
			// Always recreate the worker when forcing a reload so
			// subsequent reloads fetch fresh data from the server.
			if (!this.itemWorker && typeof Worker !== "undefined") {
				try {
					const workerUrl = "/assets/posawesome/js/posapp/workers/itemWorker.js";
					this.itemWorker = new Worker(workerUrl, { type: "classic" });
				} catch (e) {
					console.error("Failed to start item worker", e);
					this.itemWorker = null;
				}
			}
			this.items_loaded = false;
			this.get_items(true);
		},
		async get_items(force_server = false) {
			await initPromise;
			await checkDbHealth();
			const request_token = ++this.items_request_token;
			if (!this.pos_profile) {
				console.error("No POS Profile");
				return;
			}

			if (force_server && this.pos_profile.posa_local_storage) {
				localStorage.setItem("items_storage", "");
			}

			const vm = this;
			this.loading = true;

			// Removed noisy debug log
			let search = this.get_search(this.first_search);
			let sr = search || "";

			// Skip reload if items already loaded, not forcing, not searching and limit search disabled
			if (
				this.items_loaded &&
				!force_server &&
				!this.first_search &&
				!this.pos_profile.pose_use_limit_search
			) {
				console.info("Items already loaded, skipping reload");
				if (this.filtered_items && this.filtered_items.length > 0) {
					this.update_items_details(this.filtered_items);
				}
				this.loading = false;
				return;
			}
			// Removed noisy debug log

			// Attempt to load cached items for the current price list
			if (!force_server && !this.pos_profile.pose_use_limit_search) {
				const cached = getCachedPriceListItems(vm.customer_price_list);
				if (cached && cached.length) {
					vm.items = cached;
					vm.items.forEach((it) => {
						if (!it.item_uoms || it.item_uoms.length === 0) {
							const cachedUoms = getItemUOMs(it.item_code);
							if (cachedUoms.length > 0) {
								it.item_uoms = cachedUoms;
							} else if (it.stock_uom) {
								it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
							}
						}
					});
					this.eventBus.emit("set_all_items", vm.items);
					vm.loading = false;
					vm.items_loaded = true;

					if (vm.items && vm.items.length > 0) {
						vm.prePopulateStockCache(vm.items);
						vm.update_items_details(vm.items);
					}
					return;
				}
			}

			// Load from localStorage when available and not forcing
			if (
				vm.pos_profile.posa_local_storage &&
				getItemsStorage().length &&
				!vm.pos_profile.pose_use_limit_search &&
				!force_server
			) {
				vm.items = getItemsStorage();
				// Fallback to cached UOMs when loading from storage
				vm.items.forEach((it) => {
					if (!it.item_uoms || it.item_uoms.length === 0) {
						const cached = getItemUOMs(it.item_code);
						if (cached.length > 0) {
							it.item_uoms = cached;
						} else if (it.stock_uom) {
							it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
						}
					}
				});
				this.eventBus.emit("set_all_items", vm.items);
				vm.loading = false;
				vm.items_loaded = true;

				if (vm.items && vm.items.length > 0) {
					await vm.prePopulateStockCache(vm.items);
					vm.update_items_details(vm.items);
				}
				return;
			}
			// Removed noisy debug log

			if (this.itemWorker) {
				try {
					const res = await fetch("/api/method/posawesome.posawesome.api.items.get_items", {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
							"X-Frappe-CSRF-Token": frappe.csrf_token,
						},
						credentials: "same-origin",
						body: JSON.stringify({
							pos_profile: JSON.stringify(vm.pos_profile),
							price_list: vm.customer_price_list,
							search_value: sr,
							customer: vm.customer,
						}),
					});

					const text = await res.text();
					// console.info(text)
					this.itemWorker.onmessage = async (ev) => {
						if (this.items_request_token !== request_token) return;
						if (ev.data.type === "parsed") {
							const parsed = ev.data.items;
							vm.items = parsed.message || parsed;
							savePriceListItems(vm.customer_price_list, vm.items);
							// Ensure UOMs are available for each item
							vm.items.forEach((it) => {
								if (it.item_uoms && it.item_uoms.length > 0) {
									saveItemUOMs(it.item_code, it.item_uoms);
								} else {
									const cached = getItemUOMs(it.item_code);
									if (cached.length > 0) {
										it.item_uoms = cached;
									} else if (it.stock_uom) {
										it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
									}
								}
							});
							vm.eventBus.emit("set_all_items", vm.items);
							vm.loading = false;
							vm.items_loaded = true;
							console.info("Items Loaded");

							// Pre-populate stock cache when items are freshly loaded
							vm.prePopulateStockCache(vm.items);

							vm.$nextTick(() => {
								if (vm.search && !vm.pos_profile.pose_use_limit_search) {
									vm.search_onchange();
								}
							});

							// Always refresh quantities after items are loaded
							if (vm.items && vm.items.length > 0) {
								vm.update_items_details(vm.items);
							}

							if (vm.pos_profile.posa_local_storage && !vm.pos_profile.pose_use_limit_search) {
								try {
									setItemsStorage(vm.items);
									vm.items.forEach((it) => {
										if (it.item_uoms && it.item_uoms.length > 0) {
											saveItemUOMs(it.item_code, it.item_uoms);
										}
									});
								} catch (e) {
									console.error(e);
								}
							}

							if (vm.pos_profile.pose_use_limit_search) {
								vm.enter_event();
							}

							// Terminate the worker after items are parsed to
							// release memory held by the worker thread.
							if (vm.itemWorker) {
								vm.itemWorker.terminate();
								vm.itemWorker = null;
							}
						} else if (ev.data.type === "error") {
							console.error("Item worker parse error:", ev.data.error);
							vm.loading = false;
						}
					};
					this.itemWorker.postMessage({
						type: "parse_and_cache",
						json: text,
						priceList: vm.customer_price_list,
					});
				} catch (err) {
					console.error("Failed to fetch items", err);
					vm.loading = false;
				}
			} else {
				frappe.call({
					method: "posawesome.posawesome.api.items.get_items",
					args: {
						pos_profile: JSON.stringify(vm.pos_profile),
						price_list: vm.customer_price_list,
						search_value: sr,
						customer: vm.customer,
					},
					callback: async function (r) {
						if (vm.items_request_token !== request_token) return;
						if (r.message) {
							vm.items = r.message;
							// Ensure UOMs are available for each item
							vm.items.forEach((it) => {
								if (it.item_uoms && it.item_uoms.length > 0) {
									saveItemUOMs(it.item_code, it.item_uoms);
								} else {
									const cached = getItemUOMs(it.item_code);
									if (cached.length > 0) {
										it.item_uoms = cached;
									} else if (it.stock_uom) {
										it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
									}
								}
							});
							vm.eventBus.emit("set_all_items", vm.items);
							vm.loading = false;
							vm.items_loaded = true;
							savePriceListItems(vm.customer_price_list, vm.items);
							console.info("Items Loaded");

							// Pre-populate stock cache when items are freshly loaded
							vm.prePopulateStockCache(vm.items);

							vm.$nextTick(() => {
								if (vm.search && !vm.pos_profile.pose_use_limit_search) {
									vm.search_onchange();
								}
							});

							// Always refresh quantities after items are loaded
							if (vm.items && vm.items.length > 0) {
								vm.update_items_details(vm.items);
							}

							if (vm.pos_profile.posa_local_storage && !vm.pos_profile.pose_use_limit_search) {
								try {
									setItemsStorage(r.message);
									r.message.forEach((it) => {
										if (it.item_uoms && it.item_uoms.length > 0) {
											saveItemUOMs(it.item_code, it.item_uoms);
										}
									});
								} catch (e) {
									console.error(e);
								}
							}
							if (vm.pos_profile.pose_use_limit_search) {
								vm.enter_event();
							}
						}
					},
				});
			}
		},
		getItemsHeaders() {
			const items_headers = [
				{
					title: __("Name"),
					align: "start",
					sortable: true,
					key: "item_name",
				},
				{
					title: __("Code"),
					align: "start",
					sortable: true,
					key: "item_code",
				},
				{ title: __("Rate"), key: "rate", align: "start" },
				{ title: __("Available QTY"), key: "actual_qty", align: "start" },
				{ title: __("UOM"), key: "stock_uom", align: "start" },
			];
			if (!this.pos_profile.posa_display_item_code) {
				items_headers.splice(1, 1);
			}

			return items_headers;
		},
		async click_item_row(event, { item }) {
			await this.add_item(item);
		},
		async add_item(item) {
			item = { ...item };
			if (item.has_variants) {
				let variants = this.items.filter((it) => it.variant_of == item.item_code);
				if (!variants.length) {
					try {
						const res = await frappe.call({
							method: "posawesome.posawesome.api.items.get_item_variants",
							args: {
								pos_profile: JSON.stringify(this.pos_profile),
								parent_item_code: item.item_code,
								price_list: this.active_price_list,
								customer: this.customer,
							},
						});
						if (res.message) {
							variants = res.message;
							this.items.push(...variants);
						}
					} catch (e) {
						console.error("Failed to fetch variants", e);
					}
				}
				this.eventBus.emit("show_message", {
					title: __("This is an item template. Please choose a variant."),
					color: "warning",
				});
				console.info("sending profile", this.pos_profile);
				this.eventBus.emit("open_variants_model", item, variants, this.pos_profile);
			} else {
				if (item.actual_qty === 0 && this.pos_profile.posa_display_items_in_stock) {
					this.eventBus.emit("show_message", {
						title: `No stock available for ${item.item_name}`,
						color: "warning",
					});
					await this.update_items_details([item]);
					return;
				}

				// Ensure UOMs are initialized before adding the item
				if (!item.item_uoms || item.item_uoms.length === 0) {
					// If UOMs are not available, fetch them first
					await this.update_items_details([item]);

					// Add stock UOM as fallback
					if (!item.item_uoms || item.item_uoms.length === 0) {
						item.item_uoms = [{ uom: item.stock_uom, conversion_factor: 1.0 }];
					}
				}

				// Ensure correct rate based on selected currency
				if (this.pos_profile.posa_allow_multi_currency) {
					this.applyCurrencyConversionToItem(item);

					// Compute base rates from original values
					const base_rate =
						item.original_currency === this.pos_profile.currency
							? item.original_rate
							: item.original_rate * (item.plc_conversion_rate || this.exchange_rate);
					item.base_rate = base_rate;
					item.base_price_list_rate = base_rate;
				}

				if (!item.qty || item.qty === 1) {
					let qtyVal = this.qty != null ? this.qty : 1;
					qtyVal = Math.abs(qtyVal);
					if (this.hide_qty_decimals) {
						qtyVal = Math.trunc(qtyVal);
					}
					item.qty = qtyVal;
				}
				this.eventBus.emit("add_item", item, this.scan_add_mode);
				this.qty = 1;

				// 🆕 RESTORE Smart Highlight System
				setTimeout(() => {
					console.log("[ItemsSelector] 🎯 Smart highlighting item:", item.item_code);
					
					// Emit enhanced highlight event with UX-optimized parameters
					this.eventBus.emit("smart_highlight_item", {
						itemCode: item.item_code,
						scanMode: this.scan_add_mode,
						isNewItem: true, // This is always a new add from ItemsSelector
						duration: 1200, // Slightly longer for better visibility
						highlightType: "new_item" // Distinguish from quantity updates
					});

					console.log("[ItemsSelector] ✅ Smart highlight event emitted");
				}, 150); // Reduced delay for faster feedback
			}
		},
		async enter_event() {
			let match = false;
			if (!this.filtered_items.length || !this.first_search) {
				return;
			}

			// If multiple items match, keep the list visible for user selection
			if (this.filtered_items.length > 1) {
				console.info("[ItemsSelector] Multiple items found, keeping list visible for user selection");
				// Don't auto-add, let user click on the desired item from the visible list
				return;
			}

			// Single item match - proceed with adding
			const qty = this.get_item_qty(this.first_search);
			const new_item = { ...this.filtered_items[0] };
			new_item.qty = flt(qty); // This should always be 1 now

			// Handle barcode, serial, batch matching
			new_item.item_barcode.forEach((element) => {
				if (this.search == element.barcode) {
					new_item.uom = element.posa_uom;
					match = true;
				}
			});

			if (
				!new_item.to_set_serial_no &&
				new_item.has_serial_no &&
				this.pos_profile.posa_search_serial_no
			) {
				new_item.serial_no_data.forEach((element) => {
					if (this.search && element.serial_no == this.search) {
						new_item.to_set_serial_no = this.first_search;
						match = true;
					}
				});
			}

			if (this.flags.serial_no) {
				new_item.to_set_serial_no = this.flags.serial_no;
			}

			if (!new_item.to_set_batch_no && new_item.has_batch_no && this.pos_profile.posa_search_batch_no) {
				new_item.batch_no_data.forEach((element) => {
					if (this.search && element.batch_no == this.search) {
						new_item.to_set_batch_no = this.first_search;
						new_item.batch_no = this.first_search;
						match = true;
					}
				});
			}

			if (this.flags.batch_no) {
				new_item.to_set_batch_no = this.flags.batch_no;
			}

			// Add the single matched item
			await this.add_item(new_item);

			// Clear all flags and reset state
			this.flags.serial_no = null;
			this.flags.batch_no = null;
			this.qty = 1; // Ensure qty is reset

			// Bỏ highlight hoàn toàn để tăng tốc độ
			// // Highlight item in invoice table for Enter/search flow
			// setTimeout(() => {
			// 	console.log("[ItemsSelector] 🎯 Highlighting item from Enter/search:", new_item.item_code);

			// 	// Emit to both event names for compatibility
			// 	this.eventBus.emit("highlight_invoice_item", {
			// 		itemRowId: new_item.item_code,
			// 		scanMode: this.scan_add_mode,
			// 		duration: 1000, // 1 second highlight
			// 		enlargeFont: true,
			// 	});

			// 	// Also emit the old event name for backward compatibility
			// 	this.eventBus.emit("highlight_scanned_item", new_item.item_code);

			// 	console.log("[ItemsSelector] ✅ Highlight event emitted for Enter/search successfully");
			// }, 1000);

			// Clear search field after successfully adding an item
			this.clearSearch();
			this.$refs.debounce_search.focus();
		},
		search_onchange: _.debounce(async function (newSearchTerm) {
			const vm = this;

			// Use queue system to eliminate race conditions completely
			const query = typeof newSearchTerm === "string" ? newSearchTerm : vm.first_search;
			const fromScanner = vm.search_from_scanner;
			vm.queueSearch(query, fromScanner);
		}, 300),

		get_item_qty(first_search) {
			// Simplified: Always return 1 for regular items, no scale weight parsing
			// This prevents decimal quantities from appearing when scanning invalid barcodes
			let qty = 1;

			if (this.hide_qty_decimals) {
				qty = Math.trunc(qty);
			}
			return qty;
		},
		get_search(first_search) {
			// Simplified: Always return the search term as-is, no scale barcode parsing
			return first_search || "";
		},
		esc_event() {
			this.search = null;
			this.first_search = null;
			this.search_backup = null;
			this.qty = 1;
			this.$refs.debounce_search.focus();
		},
		async update_items_details(items) {
			const vm = this;
			if (!items || !items.length) return;

			// reset any pending retry timer
			if (vm.itemDetailsRetryTimeout) {
				clearTimeout(vm.itemDetailsRetryTimeout);
				vm.itemDetailsRetryTimeout = null;
			}

			const itemCodes = items.map((it) => it.item_code);
			const cacheResult = getCachedItemDetails(vm.pos_profile.name, vm.active_price_list, itemCodes);
			cacheResult.cached.forEach((det) => {
				const item = items.find((it) => it.item_code === det.item_code);
				if (item) {
					Object.assign(item, {
						actual_qty: det.actual_qty,
						serial_no_data: det.serial_no_data,
						batch_no_data: det.batch_no_data,
						has_batch_no: det.has_batch_no,
						has_serial_no: det.has_serial_no,
					});
					if (det.item_uoms && det.item_uoms.length > 0) {
						item.item_uoms = det.item_uoms;
						saveItemUOMs(item.item_code, det.item_uoms);
					}
					if (det.rate !== undefined) {
						if (det.rate !== 0 || !item.rate) {
							item.rate = det.rate;
							item.price_list_rate = det.price_list_rate || det.rate;
						}
					}

					if (!item.original_rate) {
						item.original_rate = item.rate;
						item.original_currency = item.currency || vm.pos_profile.currency;
					}

					vm.applyCurrencyConversionToItem(item);
				}
			});

			let allCached = cacheResult.missing.length === 0;
			items.forEach((item) => {
				const localQty = getLocalStock(item.item_code);
				if (localQty !== null) {
					item.actual_qty = localQty;
				} else {
					allCached = false;
				}

				if (!item.item_uoms || item.item_uoms.length === 0) {
					const cachedUoms = getItemUOMs(item.item_code);
					if (cachedUoms.length > 0) {
						item.item_uoms = cachedUoms;
					} else if (isOffline()) {
						item.item_uoms = [{ uom: item.stock_uom, conversion_factor: 1.0 }];
					} else {
						allCached = false;
					}
				}
			});

			// When offline or everything is cached, skip server call
			if (isOffline() || allCached) {
				vm.itemDetailsRetryCount = 0;
				return;
			}

			// Cancel previous request
			if (vm.currentRequest) {
				vm.abortController.abort();
				vm.currentRequest = null;
			}

			vm.abortController = new AbortController();

			const itemsToFetch = items.filter(
				(it) => cacheResult.missing.includes(it.item_code) && !it.has_variants,
			);

			if (itemsToFetch.length === 0) {
				vm.itemDetailsRetryCount = 0;
				return;
			}

			try {
				vm.currentRequest = await frappe.call({
					method: "posawesome.posawesome.api.items.get_items_details",
					args: {
						pos_profile: JSON.stringify(vm.pos_profile),
						items_data: JSON.stringify(itemsToFetch),
						price_list: vm.active_price_list,
					},
					freeze: false,
					signal: vm.abortController.signal,
				});

				const r = vm.currentRequest;
				if (r && r.message) {
					vm.itemDetailsRetryCount = 0;
					let qtyChanged = false;
					let updatedItems = [];

					items.forEach((item) => {
						const updated_item = r.message.find((element) => element.item_code == item.item_code);
						if (updated_item) {
							const prev_qty = item.actual_qty;

							updatedItems.push({
								item: item,
								updates: {
									actual_qty: updated_item.actual_qty,
									serial_no_data: updated_item.serial_no_data,
									batch_no_data: updated_item.batch_no_data,
									has_batch_no: updated_item.has_batch_no,
									has_serial_no: updated_item.has_serial_no,
									item_uoms:
										updated_item.item_uoms && updated_item.item_uoms.length > 0
											? updated_item.item_uoms
											: item.item_uoms,
								},
							});

							if (prev_qty > 0 && updated_item.actual_qty === 0) {
								qtyChanged = true;
							}

							if (updated_item.item_uoms && updated_item.item_uoms.length > 0) {
								saveItemUOMs(item.item_code, updated_item.item_uoms);
							}
						}
					});

					updatedItems.forEach(({ item, updates }) => {
						Object.assign(item, updates);
						vm.applyCurrencyConversionToItem(item);
					});

					updateLocalStockCache(r.message);
					saveItemDetailsCache(vm.pos_profile.name, vm.active_price_list, r.message);

					if (qtyChanged) {
						vm.$forceUpdate();
					}
				}
			} catch (err) {
				if (err.name !== "AbortError") {
					console.error("Error fetching item details:", err);
					items.forEach((item) => {
						const localQty = getLocalStock(item.item_code);
						if (localQty !== null) {
							item.actual_qty = localQty;
						}
						if (!item.item_uoms || item.item_uoms.length === 0) {
							const cached = getItemUOMs(item.item_code);
							if (cached.length > 0) {
								item.item_uoms = cached;
							}
						}
					});

					if (!isOffline()) {
						vm.itemDetailsRetryCount += 1;
						const delay = Math.min(32000, 1000 * Math.pow(2, vm.itemDetailsRetryCount - 1));
						vm.itemDetailsRetryTimeout = setTimeout(() => {
							vm.update_items_details(items);
						}, delay);
					}
				}
			}

			// Cleanup on component destroy
			this.cleanupBeforeDestroy = () => {
				if (vm.abortController) {
					vm.abortController.abort();
				}
			};
		},
		update_cur_items_details() {
			if (this.filtered_items && this.filtered_items.length > 0) {
				this.update_items_details(this.filtered_items);
			}
		},
		async prePopulateStockCache(items) {
			if (this.prePopulateInProgress) {
				return;
			}
			this.prePopulateInProgress = true;
			try {
				// Use the new isStockCacheReady function
				if (isStockCacheReady()) {
					console.debug("Stock cache already initialized");
					return;
				}

				console.info("Pre-populating stock cache for", items.length, "items");
				await initializeStockCache(items, this.pos_profile);
			} catch (error) {
				console.error("Failed to pre-populate stock cache:", error);
			} finally {
				this.prePopulateInProgress = false;
			}
		},

		applyCurrencyConversionToItems() {
			if (!this.items || !this.items.length) return;
			this.items.forEach((it) => this.applyCurrencyConversionToItem(it));
		},

		applyCurrencyConversionToItem(item) {
			if (!item) return;
			const base = this.pos_profile.currency;

			if (!item.original_rate) {
				item.original_rate = item.rate;
				item.original_currency = item.currency || base;
			}

			// original_rate is in price list currency
			const price_list_rate = item.original_rate;

			// Determine base rate using available conversion info
			const base_rate = price_list_rate * (item.plc_conversion_rate || 1);

			item.base_rate = base_rate;
			item.base_price_list_rate = price_list_rate;

			// If the price list currency matches the selected currency,
			// don't apply any conversion
			const converted_rate =
				item.original_currency === this.selected_currency
					? price_list_rate
					: price_list_rate * (this.exchange_rate || 1);

			item.rate = this.flt(converted_rate, this.currency_precision);
			item.currency = this.selected_currency;
			item.price_list_rate = item.rate;
		},
		scan_barcoud() {
			const vm = this;
			try {
				// Check if scanner is already attached to document
				if (document._scannerAttached) {
					return;
				}

				onScan.attachTo(document, {
					suffixKeyCodes: [13], // Enter
					reactToPaste: false,
					minLength: 6, // tuỳ chuẩn UPC/EAN
					timeBeforeScanTest: 20, // giảm độ trễ phát hiện
					avgTimeByChar: 15,
					keyCodeMapper: function (oEvent) {
						oEvent.stopImmediatePropagation();
						oEvent.preventDefault();
						return onScan.decodeKeyEvent(oEvent);
					},
					onScan: (sCode) => {
						vm.trigger_onscan(sCode);
					}, // bỏ delay 300ms
				});

				// Mark document as having scanner attached
				document._scannerAttached = true;
			} catch (error) {
				console.warn("Scanner initialization error:", error.message);
			}
		},
		trigger_onscan(sCode) {
			// Debounce to prevent duplicate scans within short time period
			const now = Date.now();
			if (now - this.lastScanTime < this.scanDebounceMs) {
				console.log("Ignoring duplicate hardware scan within debounce period");
				return;
			}
			this.lastScanTime = now;

			console.info('[Hardware Scanner] Scanned barcode:', sCode);

			// 🚀 AUTO-ENTER: Đưa barcode vào search input và tự động thực hiện Enter
			this.search_mode = 'barcode';
			this.hideSearchResults();
			
			// Đưa barcode vào search input
			this.debounce_search = sCode.trim();
			this.first_search = sCode.trim();
			
			// Focus vào search input và tự động thực hiện Enter
			this.$nextTick(() => {
				this.focusSearchInput();
				// 🚀 TỰ ĐỘNG THỰC HIỆN ENTER
				setTimeout(() => {
					this.handleBarcodeEnter();
				}, 50); // Small delay to ensure input is updated
			});
			
			console.info(`[Hardware Scanner] Auto-processing: ${sCode}`);
		},
		generateWordCombinations(inputString) {
			const words = inputString.split(" ");
			const wordCount = words.length;
			const combinations = [];

			// Helper function to generate all permutations
			function permute(arr, m = []) {
				if (arr.length === 0) {
					combinations.push(m.join(" "));
				} else {
					for (let i = 0; i < arr.length; i++) {
						const current = arr.slice();
						const next = current.splice(i, 1);
						permute(current.slice(), m.concat(next));
					}
				}
			}

			permute(words);

			return combinations;
		},
		clearSearch() {
			this.search_backup = this.first_search;
			this.first_search = "";
			this.search = "";
			// No need to call get_items() again
		},

		// Enhanced search state clearing after successful processing
		clearSearchState() {
			this.clearSearch();
			this.search_from_scanner = false;
			this.processing_search = false;
			this.qty = 1; // Always reset quantity to 1

			// Clear all flags that might affect qty calculation
			this.flags.serial_no = null;
			this.flags.batch_no = null;

			// Clear any pending operations
			if (this.current_search_controller) {
				this.current_search_controller.abort();
				this.current_search_controller = null;
			}

			// Refocus input after clearing
			setTimeout(() => {
				if (this.$refs.debounce_search) {
					this.$refs.debounce_search.focus();
				}
			}, 150);
		},

		// Queue-based search processing to eliminate race conditions
		queueSearch(searchTerm, fromScanner = false) {
			const searchId = ++this.current_search_id;

			// Cancel any ongoing search
			this.cancelCurrentSearch();

			// Add to queue (but since we cancel previous, queue will only have latest)
			this.search_queue = [{ searchTerm, fromScanner, searchId }];

			// Process immediately if not currently processing
			if (!this.processing_search) {
				this.processSearchQueue();
			}
		},

		// Process search queue sequentially
		async processSearchQueue() {
			if (this.search_queue.length === 0 || this.processing_search) {
				return;
			}

			const { searchTerm, fromScanner, searchId } = this.search_queue.shift();
			this.processing_search = true;

			try {
				// Create new abort controller for this search
				this.current_search_controller = new AbortController();
				this.current_search_id = searchId;

				await this.executeSearch(searchTerm, fromScanner, searchId);
			} catch (error) {
				if (error.name !== "AbortError") {
					console.error("[ItemsSelector] Search error:", error);
				}
			} finally {
				this.processing_search = false;
				this.current_search_controller = null;

				// Process next item in queue if any
				if (this.search_queue.length > 0) {
					setTimeout(() => this.processSearchQueue(), 50);
				}
			}
		},

		// Cancel current search operation
		cancelCurrentSearch() {
			if (this.current_search_controller) {
				this.current_search_controller.abort();
				this.current_search_controller = null;
			}
			this.processing_search = false;
		},

		// Execute the actual search logic
		async executeSearch(searchTerm, fromScanner, searchId) {
			// Check if this search was cancelled
			if (this.current_search_id !== searchId) {
				throw new Error("Search cancelled");
			}

			// Only trim in barcode mode or when from scanner
			// In text mode, preserve user input exactly as typed for auto-search
			let query;
			if (this.search_mode === 'barcode' || fromScanner) {
				query = (searchTerm || "").trim();
			} else {
				query = searchTerm || "";
			}

			if (!query) {
				this.search_from_scanner = false;
				return;
			}

			this.search = query;

			// Check cancellation again
			if (this.current_search_id !== searchId) {
				throw new Error("Search cancelled");
			}

			// Priority: If search term is valid barcode (check with trimmed version), try exact match first
			const trimmedQuery = query.trim();
			if (this.isValidBarcode(trimmedQuery)) {
				console.info(`[ItemsSelector] 🔍 Processing barcode search: ${trimmedQuery} (ID: ${searchId})`);

				// Try local exact match first
				const exactItem = this.items.find(
					(item) => item.item_barcode && item.item_barcode.some((bc) => bc.barcode === trimmedQuery),
				);

				if (exactItem) {
					console.info(`[ItemsSelector] ✅ Found exact barcode match: ${exactItem.item_code}`);

					// Set UOM from barcode data
					const barcodeData = exactItem.item_barcode.find((bc) => bc.barcode === trimmedQuery);
					if (barcodeData && barcodeData.posa_uom) {
						exactItem.uom = barcodeData.posa_uom;
					}

					// Check cancellation before adding item
					if (this.current_search_id !== searchId) {
						throw new Error("Search cancelled");
					}

					await this.add_item(exactItem);
					this.clearSearchState();
					return;
				}

				// Try API exact match (get item data only, then add via normal flow)
				try {
					const exactItem = await this.getItemByBarcodeExact(trimmedQuery);
					if (exactItem) {
						console.info(`[ItemsSelector] ✅ Exact barcode API match found`);
						await this.add_item(exactItem);
						return;
					}
				} catch (apiError) {
					if (apiError.name === "AbortError") {
						throw apiError; // Re-throw abort errors
					}
					console.warn(`[ItemsSelector] API search failed:`, apiError);
				}

				// Fallback to normal search if no exact match
				console.info(`[ItemsSelector] ❌ No exact match, falling back to normal search`);
			}

			// Normal search logic - simplified to prevent decimal qty issues
			if (this.pos_profile.pose_use_limit_search) {
				if (query.length >= 3) {
					this.get_items();
				}
			} else {
				// Ensure qty is reset before enter_event to prevent decimal issues
				this.qty = 1;
				// 🆕 THỐNG NHẤT: Tất cả scanner đều đưa vào search input, không auto-add
				if (!fromScanner && query.length >= 3) {
					this.enter_event();
				}

				// Update item details after search
				if (this.filtered_items && this.filtered_items.length > 0) {
					setTimeout(() => {
						if (this.current_search_id === searchId) {
							// Check if still valid
							this.update_items_details(this.filtered_items);
						}
					}, 300);
				}
			}

			// Clear search state for scanner inputs
			if (fromScanner) {
				this.clearSearchState();
			}
		},

		// 📋 SEARCH RESULTS NAVIGATION
		showSearchResults(results, viewOnlyMode = false) {
			this.search_results = results.slice(0, 10); // Limit to 10 results
			this.search_results_visible = true;
			this.selected_result_index = 0;
			this.search_results_view_only = viewOnlyMode; // Track if this is view-only mode
			
			// Navigation hint removed for speed
			console.info(`[Search Results] ${results.length} results displayed`);
		},

		navigateResults(direction) {
			if (!this.search_results_visible || this.search_results.length === 0) return;
			
			const newIndex = this.selected_result_index + direction;
			
			if (newIndex >= 0 && newIndex < this.search_results.length) {
				this.selected_result_index = newIndex;
				
				// Scroll selected item into view
				this.$nextTick(() => {
					const selectedElement = document.querySelector('.selected-result');
					if (selectedElement) {
						selectedElement.scrollIntoView({ 
							behavior: 'smooth', 
							block: 'nearest' 
						});
					}
				});
			}
		},

		selectSearchResult(index) {
			this.selected_result_index = index;
			this.selectCurrentResult();
		},

		async selectCurrentResult() {
			if (!this.search_results_visible || this.search_results.length === 0) return;
			
			const selectedItem = this.search_results[this.selected_result_index];
			if (!selectedItem) return;
			
			// 🆕 Always show product confirmation popup when selecting from search results
			console.info('[Text Search] Showing product confirmation for:', selectedItem.item_name);
			this.showProductConfirmation(selectedItem);
		},

		hideSearchResults() {
			this.search_results_visible = false;
			this.search_results = [];
			this.selected_result_index = 0;
			this.search_results_view_only = false; // Reset view-only flag
		},
		
		// 🔍 SEARCH LOGIC
		async findItemByBarcode(barcode) {
			// Try API exact match first
			try {
				const apiResult = await this.getItemByBarcodeExact(barcode);
				if (apiResult) return apiResult;
			} catch (error) {
				console.warn('API barcode search failed:', error);
			}
			
			// Fallback to local search
			return this.items.find(item => 
				item.item_barcode?.some(bc => bc.barcode === barcode)
			);
		},

		async searchItemsByText(searchTerm) {
			const term = searchTerm.toLowerCase();
			
			// Search in item code and name
			const results = this.items.filter(item => {
				const codeMatch = item.item_code.toLowerCase().includes(term);
				const nameMatch = item.item_name.toLowerCase().includes(term);
				return codeMatch || nameMatch;
			});
			
			// Sort by relevance (exact matches first)
			return results.sort((a, b) => {
				const aCodeExact = a.item_code.toLowerCase() === term;
				const bCodeExact = b.item_code.toLowerCase() === term;
				const aNameExact = a.item_name.toLowerCase() === term;
				const bNameExact = b.item_name.toLowerCase() === term;
				
				if (aCodeExact && !bCodeExact) return -1;
				if (bCodeExact && !aCodeExact) return 1;
				if (aNameExact && !bNameExact) return -1;
				if (bNameExact && !aNameExact) return 1;
				
				return a.item_name.localeCompare(b.item_name);
			}).slice(0, 20); // Limit results
		},
		
		restoreSearch() {
			if (this.first_search === "") {
				this.first_search = this.search_backup;
				this.search = this.search_backup;
				// No need to reload items when focus is lost
			}
		},
		
		// 🎯 FOCUS MANAGEMENT
		handleSearchFocus() {
			this.current_focus_element = 'search_input';
		},

		handleSearchBlur() {
			// Don't clear focus immediately - may be navigating to results
			setTimeout(() => {
				if (this.current_focus_element === 'search_input') {
					this.current_focus_element = null;
				}
			}, 100);
		},

		clearQty() {
			// This method is now handled by NumPad
			// Keep for backward compatibility
			this.qty = null;
		},
		
		// 🧹 HELPER METHODS
		clearAllFocus() {
			// Clear any focused elements
			if (document.activeElement && document.activeElement.blur) {
				document.activeElement.blur();
			}
			this.current_focus_element = null;
		},

		resetProcessingStates() {
			this.is_processing_barcode = false;
			this.processing_scan = false;
			this.search_from_scanner = false;
		},

		focusSearchInput() {
			this.$nextTick(() => {
				if (this.$refs.searchInput) {
					this.$refs.searchInput.focus();
				}
			});
		},

		clearSearchAndRefocus() {
			this.clearSearch();
			setTimeout(() => {
				this.focusSearchInput();
			}, 100);
		},

		selectAllSearchText() {
			this.$nextTick(() => {
				if (this.$refs.searchInput && this.$refs.searchInput.$el) {
					const input = this.$refs.searchInput.$el.querySelector('input');
					if (input) {
						input.select();
					}
				}
			});
		},
		
		// 🎨 FEEDBACK METHODS
		showSuccess(message) {
			// Alert removed for speed
			console.info(`[Success] ${message}`);
		},

		showError(message, color = 'red') {
			// Alert removed for speed
			console.error(`[Error] ${message}`);
		},

		async addItemToCart(item) {
			// Use existing add_item method
			await this.add_item(item);
		},
		
		// 🆕 PRODUCT CONFIRMATION METHODS
		showProductConfirmation(item) {
			this.selected_product = { ...item };
			this.product_quantity = 1;
			this.product_quantity_display = '1';
			this.product_confirmation_visible = true;
			
			// Hide search results
			this.hideSearchResults();
			
			console.info('[Product Confirmation] Showing popup for:', item.item_name);
		},
		
		hideProductConfirmation() {
			this.product_confirmation_visible = false;
			this.selected_product = null;
			this.product_quantity = 1;
			this.product_quantity_display = '1';
			
			// Return focus to search input
			this.clearSearchAndRefocus();
			
			console.info('[Product Confirmation] Popup closed');
		},
		
		async confirmAddProduct() {
			if (!this.selected_product || !this.product_quantity || this.product_quantity <= 0) {
				this.showError('Số lượng không hợp lệ', 'red');
				return;
			}
			
			try {
				// Set the quantity for the item
				const itemToAdd = { ...this.selected_product };
				itemToAdd.qty = this.product_quantity;
				
				// Add to cart using existing method
				await this.add_item(itemToAdd);
				
				// Show success message
				this.showSuccess(`Đã thêm: ${itemToAdd.item_name} (SL: ${this.product_quantity})`);
				
				// Hide popup and return to search
				this.hideProductConfirmation();
				
			} catch (error) {
				console.error('Error adding product:', error);
				this.showError('Lỗi thêm sản phẩm', 'red');
			}
		},
		
		// Quantity control methods
		increaseProductQuantity() {
			this.product_quantity = parseFloat(this.product_quantity) + 1;
			this.product_quantity_display = String(this.product_quantity);
		},
		
		decreaseProductQuantity() {
			const newQty = parseFloat(this.product_quantity) - 1;
			if (newQty >= 0.1) {
				this.product_quantity = newQty;
				this.product_quantity_display = String(this.product_quantity);
			}
		},
		
		setProductQuantity(qty) {
			this.product_quantity = qty;
			this.product_quantity_display = String(qty);
		},
		
		// 🧮 NUMPAD METHODS
		showNumPad() {
			// Store original quantity
			this.numpad_original_qty = this.qty;
			
			// Set display value
			this.numpad_display = this.qty ? String(this.qty) : '';
			
			// Show NumPad
			this.numpad_visible = true;
			
			// Disable F2/F3 while NumPad is open
			console.info('[NumPad] Disabling F2/F3, before - f3_enabled:', this.f3_enabled);
			this.f2_enabled = false;
			this.f3_enabled = false;
			console.info('[NumPad] After disable - f3_enabled:', this.f3_enabled);
			
			console.info('[NumPad] Opened with value:', this.numpad_display);
			console.info('[NumPad] Current search mode:', this.search_mode, '(will return to Barcode mode on close)');
		},
		
		hideNumPad() {
			this.numpad_visible = false;
			
			// Re-enable F2/F3
			console.info('[NumPad] Re-enabling F2/F3, before - f3_enabled:', this.f3_enabled);
			this.f2_enabled = true;
			this.f3_enabled = true;
			console.info('[NumPad] After enable - f3_enabled:', this.f3_enabled);
			
			// 🆕 ALWAYS return to Barcode mode when closing NumPad
			this.search_mode = 'barcode';
			
			// Clear any search results that might be showing
			this.hideSearchResults();
			
			// Focus back to barcode input
			this.$nextTick(() => {
				this.focusSearchInput();
			});
			
			console.info('[NumPad] Closed, returned to BARCODE mode with focus on search input');
		},
		
		numpadInput(value) {
			// Handle decimal point
			if (value === '.') {
				if (this.numpad_display.includes('.')) {
					return; // Already has decimal point
				}
				if (!this.numpad_display) {
					this.numpad_display = '0.';
					return;
				}
			}
			
			// Handle numbers
			if (this.numpad_display === '0' && value !== '.') {
				this.numpad_display = String(value);
			} else {
				this.numpad_display += String(value);
			}
			
			console.info('[NumPad] Input:', value, 'Display:', this.numpad_display);
		},
		
		numpadBackspace() {
			if (this.numpad_display.length > 0) {
				this.numpad_display = this.numpad_display.slice(0, -1);
			}
			console.info('[NumPad] Backspace, Display:', this.numpad_display);
		},
		
		numpadClear() {
			this.numpad_display = '';
			console.info('[NumPad] Cleared');
		},
		
		numpadEnter() {
			// Validate input
			let value = parseFloat(this.numpad_display);
			
			if (isNaN(value) || value <= 0) {
				// Invalid input - error removed for speed
				console.error('[NumPad] Invalid quantity input');
				return;
			}
			
			// Apply quantity
			this.qty = value;
			
			// Success feedback removed for speed
			console.info(`[NumPad] Quantity set to: ${value} - Barcode mode`);
			
			// Close NumPad and return focus to barcode input (will auto-switch to barcode mode)
			this.hideNumPad();
			
			console.info('[NumPad] Enter pressed, qty set to:', value, '- Switched to Barcode mode');
		},
		
		// 🆕 PRODUCT NUMPAD METHODS
		showProductNumPad() {
			// Store current quantity
			this.product_numpad_display = this.product_quantity_display;
			
			// Show Product NumPad
			this.product_numpad_visible = true;
			
			console.info('[Product NumPad] Opened with value:', this.product_numpad_display);
		},
		
		hideProductNumPad() {
			this.product_numpad_visible = false;
			
			console.info('[Product NumPad] Closed');
		},
		
		productNumpadInput(value) {
			// Handle decimal point
			if (value === '.') {
				if (this.product_numpad_display.includes('.')) {
					return; // Already has decimal point
				}
				if (!this.product_numpad_display) {
					this.product_numpad_display = '0.';
					return;
				}
			}
			
			// Handle numbers
			if (this.product_numpad_display === '0' && value !== '.') {
				this.product_numpad_display = String(value);
			} else {
				this.product_numpad_display += String(value);
			}
			
			console.info('[Product NumPad] Input:', value, 'Display:', this.product_numpad_display);
		},
		
		productNumpadBackspace() {
			if (this.product_numpad_display.length > 0) {
				this.product_numpad_display = this.product_numpad_display.slice(0, -1);
			}
			console.info('[Product NumPad] Backspace, Display:', this.product_numpad_display);
		},
		
		productNumpadClear() {
			this.product_numpad_display = '';
			console.info('[Product NumPad] Cleared');
		},
		
		productNumpadEnter() {
			// Validate input
			let value = parseFloat(this.product_numpad_display);
			
			if (isNaN(value) || value <= 0) {
				// Invalid input - error removed for speed
				console.error('[Product NumPad] Invalid quantity input');
				return;
			}
			
			// Apply quantity to product
			this.product_quantity = value;
			this.product_quantity_display = String(value);
			
			// Success feedback removed for speed
			console.info(`[Product NumPad] Quantity set to: ${value}`);
			
			// Close Product NumPad
			this.hideProductNumPad();
			
			console.info('[Product NumPad] Enter pressed, product qty set to:', value);
		},

		startCameraScanning() {
			if (this.$refs.cameraScanner) {
				this.$refs.cameraScanner.startScanning();
			}
		},

		// 🆕 Product Search Popup Methods
		openProductSearchPopup() {
			console.info('[Popup] Opening product search popup');
			this.product_search_popup_visible = true;
		},

		closeProductSearchPopup() {
			console.info('[Popup] Closing product search popup');
			this.product_search_popup_visible = false;
			// Return focus to main search input
			this.$nextTick(() => {
				this.focusSearchInput();
			});
		},

		async onPopupAddItem(item) {
			console.info('[Popup] Adding item from popup:', item.item_name);
			try {
				await this.add_item(item);
				// Success alert removed for speed
				console.info(`[Popup] Successfully added: ${item.item_name}`);
			} catch (error) {
				console.error('[Popup] Error adding item:', error);
				// Error alert removed for speed
				console.error(`[Popup] Failed to add product: ${error.message}`);
			}
		},
		onBarcodeScanned(scannedCode) {
			console.info("Camera Scanner: Barcode scanned:", scannedCode);

			// Debounce to prevent duplicate scans within short time period
			const now = Date.now();
			if (now - this.lastScanTime < this.scanDebounceMs) {
				console.log("Ignoring duplicate camera scan within debounce period");
				return;
			}
			this.lastScanTime = now;

			// 🚀 AUTO-ENTER: Đưa barcode vào search input và tự động thực hiện Enter
			this.search_mode = 'barcode';
			this.hideSearchResults();
			
			// Đưa barcode vào search input
			this.debounce_search = scannedCode.trim();
			this.first_search = scannedCode.trim();
			
			// Focus vào search input và tự động thực hiện Enter
			this.$nextTick(() => {
				this.focusSearchInput();
				// 🚀 TỰ ĐỘNG THỰC HIỆN ENTER
				setTimeout(() => {
					this.handleBarcodeEnter();
				}, 50); // Small delay to ensure input is updated
			});
			
			console.info(`[Camera Scanner] Auto-processing: ${scannedCode}`);
		},
		// 🚫 DEPRECATED: processScannedItem - Không còn sử dụng do thống nhất luồng Enter
		// Tất cả scanner (hardware, camera, manual) đều đưa barcode vào search input
		// và yêu cầu nhấn Enter để xử lý thông qua handleBarcodeEnter()
		/*
		async processScannedItem(scannedCode) {
			// Method này đã được thay thế bằng luồng thống nhất:
			// Scanner → Search Input → Enter → handleBarcodeEnter()
		},
		*/
		// 🚫 DEPRECATED: searchItemsByCode - Không còn sử dụng
		/*
		searchItemsByCode(code) {
			// Method này đã được thay thế bằng luồng thống nhất handleBarcodeEnter()
		},
		*/
		// 🚫 DEPRECATED: addScannedItemToInvoice - Không còn sử dụng
		/*
		async addScannedItemToInvoice(item, scannedCode) {
			// Method này đã được thay thế bằng luồng thống nhất handleBarcodeEnter() → addItemToCart()
		},
		*/
		showMultipleItemsDialog(items, scannedCode) {
			// Create a dialog to let user choose from multiple matches
			const mode = this.scan_add_mode ? "Add" : "Remove";
			const dialog = new frappe.ui.Dialog({
				title: __(`Multiple Items Found - ${mode} Mode`),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "items_html",
						options: this.generateItemSelectionHTML(items, scannedCode),
					},
				],
				primary_action_label: __("Cancel"),
				primary_action: () => dialog.hide(),
			});

			dialog.show();

			// Add click handlers for item selection
			setTimeout(() => {
				items.forEach((item, index) => {
					const button = dialog.$wrapper.find(`[data-item-index="${index}"]`);
					button.on("click", () => {
						this.addScannedItemToInvoice(item, scannedCode);
						dialog.hide();
					});
				});
			}, 100);
		},
		generateItemSelectionHTML(items, scannedCode) {
			let html = `<div class="mb-3"><strong>Scanned Code:</strong> ${scannedCode}</div>`;
			html += '<div class="item-selection-list">';

			items.forEach((item, index) => {
				html += `
          <div class="item-option p-3 mb-2 border rounded cursor-pointer" data-item-index="${index}" style="border: 1px solid #ddd; cursor: pointer;">
            <div class="d-flex align-items-center">
              <img src="${item.image || "/assets/posawesome/js/posapp/components/pos/placeholder-image.png"}" 
                   style="width: 50px; height: 50px; object-fit: cover; margin-right: 15px;" />
              <div>
                <div class="font-weight-bold">${item.item_name}</div>
                <div class="text-muted small">${item.item_code}</div>
                <div class="text-primary">${this.format_currency(item.rate, this.pos_profile.currency, this.ratePrecision(item.rate))}</div>
              </div>
            </div>
          </div>
        `;
			});

			html += "</div>";
			return html;
		},
		handleItemNotFound(scannedCode) {
			console.warn("Item not found for scanned code:", scannedCode);

			// Error message removed for speed
			console.error(`[Item Search] Item not found: ${scannedCode}`);

			// Keep the search term for manual search but don't trigger_onscan to avoid loops
			this.first_search = scannedCode;
			this.search = scannedCode;

			// Refocus input without triggering search
			setTimeout(() => {
				if (this.$refs.debounce_search) {
					this.$refs.debounce_search.focus();
				}
			}, 100);
		},

		onScanModeChange() {
			const mode = this.scan_add_mode ? "Add Mode" : "Remove Mode";
			// Alert removed for speed
			console.info(`[Scan Mode] Switched to ${mode}`);
		},

		setScanMode(isAddMode) {
			console.info(`[ItemsSelector] User clicked ${isAddMode ? "Add Mode" : "Remove Mode"} button`);
			console.info(`[ItemsSelector] Previous mode: ${this.scan_add_mode ? "Add Mode" : "Remove Mode"}`);
			console.info(`[ItemsSelector] New mode: ${isAddMode ? "Add Mode" : "Remove Mode"}`);

			this.scan_add_mode = isAddMode;

			const mode = this.scan_add_mode ? "Add Mode" : "Remove Mode";
			console.info(`[ItemsSelector] Mode switched to: ${mode}`);

			// Alert removed for speed
			console.info(`[Scan Mode] Switched to ${mode}`);

			console.info(`[ItemsSelector] Scan mode change completed`);
		},

		currencySymbol(currency) {
			return get_currency_symbol(currency);
		},
		format_currency(value, currency, precision) {
			const prec = typeof precision === "number" ? precision : this.currency_precision;
			return this.formatCurrency(value, prec);
		},
		ratePrecision(value) {
			const numericValue = typeof value === "string" ? parseFloat(value) : value;
			return Number.isInteger(numericValue) ? 0 : this.currency_precision;
		},
		format_number(value, precision) {
			const prec = typeof precision === "number" ? precision : this.float_precision;
			return this.formatFloat(value, prec);
		},
		hasDecimalPrecision(value) {
			// Check if the value has any decimal precision when converted by exchange rate
			if (this.exchange_rate && this.exchange_rate !== 1) {
				let convertedValue = value * this.exchange_rate;
				return !Number.isInteger(convertedValue);
			}
			return !Number.isInteger(value);
		},

		toggleItemSettings() {
			this.temp_hide_qty_decimals = this.hide_qty_decimals;
			this.temp_hide_zero_rate_items = this.hide_zero_rate_items;
			this.show_item_settings = true;
		},
		cancelItemSettings() {
			this.show_item_settings = false;
		},
		applyItemSettings() {
			this.hide_qty_decimals = this.temp_hide_qty_decimals;
			this.hide_zero_rate_items = this.temp_hide_zero_rate_items;
			this.saveItemSettings();
			this.show_item_settings = false;
		},
		onDragStart(event, item) {
			this.isDragging = true;

			// Set drag data
			event.dataTransfer.setData(
				"application/json",
				JSON.stringify({
					type: "item-from-selector",
					item: item,
				}),
			);

			// Set drag effect
			event.dataTransfer.effectAllowed = "copy";

			// Emit event to show drop feedback in ItemsTable
			this.eventBus.emit("item-drag-start", item);
		},
		onDragEnd(event) {
			this.isDragging = false;

			// Emit event to hide drop feedback
			this.eventBus.emit("item-drag-end");
		},
		saveItemSettings() {
			try {
				const settings = {
					hide_qty_decimals: this.hide_qty_decimals,
					hide_zero_rate_items: this.hide_zero_rate_items,
				};
				localStorage.setItem("posawesome_item_selector_settings", JSON.stringify(settings));
			} catch (e) {
				console.error("Failed to save item selector settings:", e);
			}
		},
		loadItemSettings() {
			try {
				const saved = localStorage.getItem("posawesome_item_selector_settings");
				if (saved) {
					const opts = JSON.parse(saved);
					if (typeof opts.hide_qty_decimals === "boolean") {
						this.hide_qty_decimals = opts.hide_qty_decimals;
					}
					if (typeof opts.hide_zero_rate_items === "boolean") {
						this.hide_zero_rate_items = opts.hide_zero_rate_items;
					}
				}
			} catch (e) {
				console.error("Failed to load item selector settings:", e);
			}
		},
	},

	created: function () {
		this.loadItemSettings();
		if (typeof Worker !== "undefined") {
			try {
				// Use the plain URL so the service worker can match the cached file
				// even when offline. Using a query string causes cache lookups to fail
				// which results in "Failed to fetch a worker script" errors.
				const workerUrl = "/assets/posawesome/js/posapp/workers/itemWorker.js";
				this.itemWorker = new Worker(workerUrl, { type: "classic" });

				this.itemWorker.onerror = function (event) {
					console.error("Worker error:", event);
					console.error("Message:", event.message);
					console.error("Filename:", event.filename);
					console.error("Line number:", event.lineno);
				};
				console.info("Created worker nowwwwww");
			} catch (e) {
				console.error("Failed to start item worker", e);
				this.itemWorker = null;
			}
		}
		this.$nextTick(function () {});
		this.eventBus.on("register_pos_profile", async (data) => {
			await initPromise;
			await checkDbHealth();
			this.pos_profile = data.pos_profile;
			if (this.pos_profile.posa_force_reload_items && !this.pos_profile.posa_smart_reload_mode) {
				await this.get_items(true);
			} else {
				await this.get_items();
			}
			this.items_view = this.pos_profile.posa_default_card_view ? "card" : "list";
		});
		this.eventBus.on("update_cur_items_details", () => {
			this.update_cur_items_details();
		});
		this.eventBus.on("update_offers_counters", (data) => {
			this.offersCount = data.offersCount;
			this.appliedOffersCount = data.appliedOffersCount;
		});
		this.eventBus.on("update_coupons_counters", (data) => {
			this.couponsCount = data.couponsCount;
			this.appliedCouponsCount = data.appliedCouponsCount;
		});
		this.eventBus.on("update_customer_price_list", (data) => {
			this.customer_price_list = data;
		});
		this.eventBus.on("update_customer", (data) => {
			console.log("🎯 [ITEMS_SELECTOR] Customer updated via event bus:", data);
			this.customer = data;
		});

		// Manually trigger a full item reload when requested
		this.eventBus.on("force_reload_items", async () => {
			this.items_loaded = false;
			await this.get_items(true);
		});

		// Refresh item quantities when connection to server is restored
		this.eventBus.on("server-online", async () => {
			if (this.items && this.items.length > 0) {
				await this.update_items_details(this.items);
			}
		});

		// Setup auto-refresh for item quantities
		// Trigger an immediate refresh once items are available
		this.update_cur_items_details();
		this.refresh_interval = setInterval(() => {
			if (this.filtered_items && this.filtered_items.length > 0) {
				this.update_cur_items_details();
			}
		}, 30000); // Refresh every 30 seconds after the initial fetch

		// Add new event listener for currency changes
		this.eventBus.on("update_currency", (data) => {
			this.selected_currency = data.currency;
			this.exchange_rate = data.exchange_rate;

			// Refresh visible item prices when currency changes
			this.applyCurrencyConversionToItems();
			this.update_cur_items_details();
		});
	},

	async mounted() {
		const profile = await ensurePosProfile();
		if (!this.pos_profile) {
			this.pos_profile = profile;
		}
		this.scan_barcoud();
		// grid layout adjusts automatically with CSS, set items per page based on device size
		this.adjustItemsPerPage(this.windowWidth, this.windowHeight);
		
		// 🆕 Add global keyboard listener
		document.addEventListener('keydown', this.globalKeyHandler);
		
		// Auto-focus search input
		this.focusSearchInput();
		
		// Set initial mode
		this.search_mode = 'barcode';
	},

	beforeUnmount() {
		// Cancel any ongoing search operations
		this.cancelCurrentSearch();

		// Clear search queue
		this.search_queue = [];

		// Clear interval when component is destroyed
		if (this.refresh_interval) {
			clearInterval(this.refresh_interval);
		}

		if (this.itemDetailsRetryTimeout) {
			clearTimeout(this.itemDetailsRetryTimeout);
		}
		this.itemDetailsRetryCount = 0;

		// Call cleanup function for abort controller
		if (this.cleanupBeforeDestroy) {
			this.cleanupBeforeDestroy();
		}

		// Detach scanner if it was attached
		if (document._scannerAttached) {
			try {
				onScan.detachFrom(document);
				document._scannerAttached = false;
			} catch (error) {
				console.warn("Scanner detach error:", error.message);
			}
		}

		if (this.itemWorker) {
			this.itemWorker.terminate();
		}

		// 🆕 Remove global keyboard listener
		document.removeEventListener('keydown', this.globalKeyHandler);

		this.eventBus.off("update_currency");
		this.eventBus.off("server-online");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("update_cur_items_details");
		this.eventBus.off("update_offers_counters");
		this.eventBus.off("update_coupons_counters");
		this.eventBus.off("update_customer_price_list");
		this.eventBus.off("update_customer");
		this.eventBus.off("force_reload_items");
	},
};
</script>

<style scoped>
.dynamic-card {
	composes: pos-card;
}

.dynamic-padding {
	/* Equal spacing on all sides for consistent alignment */
	padding: var(--dynamic-sm);
}

.dynamic-scroll {
	transition: max-height var(--transition-normal);
	padding-bottom: var(--dynamic-xs);
	overflow-y: auto;
	scrollbar-gutter: stable;
}

/* Sticky Search Header */
.sticky-search-header {
	position: sticky;
	top: 0;
	z-index: 10;
	background-color: var(--surface-secondary);
	border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.dark-theme) .sticky-search-header,
:deep(.v-theme--dark) .sticky-search-header {
	background-color: #121212;
	border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Scrollable Items Container */
.scrollable-items-container {
	height: calc(100% - 120px); /* Adjust based on header height */
	overflow-y: auto;
	scrollbar-gutter: stable;
}

.items-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	gap: var(--dynamic-sm);
	align-items: start;
	align-content: start;
}

.dynamic-item-card {
	margin: var(--dynamic-xs);
	transition: var(--transition-normal);
	background-color: var(--surface-secondary);
	display: flex;
	flex-direction: column;
	height: auto;
	box-sizing: border-box;
}

.dynamic-item-card .v-img {
	object-fit: contain;
}

.dynamic-item-card:hover {
	transform: scale(calc(1 + 0.02 * var(--font-scale)));
}

.text-success {
	color: #4caf50 !important;
}

.sleek-data-table {
	composes: pos-table;
	margin: var(--dynamic-xs);
}

.sleek-data-table:hover {
	box-shadow: var(--shadow-md) !important;
}

.settings-container {
	display: flex;
	align-items: center;
}

.truncate {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

/* Light mode card backgrounds */
.selection,
.cards {
	background-color: var(--surface-secondary) !important;
}

/* Consistent spacing with navbar and system */
.dynamic-spacing-sm {
	padding: var(--dynamic-sm) !important;
}

.action-btn-consistent {
	margin-top: var(--dynamic-xs) !important;
	padding: var(--dynamic-xs) var(--dynamic-sm) !important;
	transition: var(--transition-normal) !important;
}

.action-btn-consistent:hover {
	background-color: rgba(25, 118, 210, 0.1) !important;
	transform: translateY(-1px) !important;
}

/* Large action buttons styling */
.action-btn-large {
	font-size: 1rem !important;
	font-weight: 600 !important;
	text-transform: uppercase !important;
	letter-spacing: 0.5px !important;
	border-radius: 10px !important;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
	transition: all 0.3s ease !important;
}

.action-btn-large:hover {
	transform: translateY(-2px) !important;
	box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25) !important;
}

.action-btn-large .v-icon {
	font-size: 20px !important;
	margin-right: 8px !important;
}

.action-btn-large .mode-btn-text {
	font-size: 0.95rem !important;
	font-weight: 600 !important;
}

/* Ensure consistent spacing with navbar pattern */
.cards {
	margin-top: var(--dynamic-sm) !important;
	padding: var(--dynamic-sm) !important;
}

/* Responsive breakpoints */
@media (max-width: 768px) {
	.dynamic-padding {
		/* Reduce spacing uniformly on smaller screens */
		padding: var(--dynamic-xs);
	}

	.dynamic-spacing-sm {
		padding: var(--dynamic-xs) !important;
	}

	.action-btn-consistent {
		padding: var(--dynamic-xs) !important;
		font-size: 0.875rem !important;
	}

	.action-btn-large {
		font-size: 0.9rem !important;
		height: 50px !important;
	}

	.action-btn-large .v-icon {
		font-size: 18px !important;
		margin-right: 6px !important;
	}

	.action-btn-large .mode-btn-text {
		font-size: 0.85rem !important;
	}

	/* Mode buttons responsive */
	.mode-btn-large {
		min-width: 140px !important;
		font-size: 0.9rem !important;
		height: 50px !important;
	}

	.mode-btn-large .v-icon {
		margin-right: 6px !important;
		font-size: 20px !important;
	}

	.mode-btn-text {
		font-size: 0.9rem !important;
	}

	/* Sticky search header responsive */
	.sticky-search-header {
		position: relative; /* Remove sticky on mobile for better UX */
		box-shadow: none;
		border-bottom: none;
	}

	.scrollable-items-container {
		height: calc(100% - 100px); /* Adjust for mobile */
	}
}

@media (max-width: 480px) {
	.dynamic-padding {
		padding: var(--dynamic-xs);
	}

	.cards {
		padding: var(--dynamic-xs) !important;
	}

	/* Stack mode buttons vertically on very small screens */
	.gap-4 {
		gap: 8px !important;
	}

	.mode-btn-large {
		min-width: 100% !important;
		height: 50px !important;
		font-size: 0.85rem !important;
		margin-bottom: 4px !important;
	}

	.mode-btn-large .v-icon {
		font-size: 18px !important;
	}

	/* Adjust mode selection card for mobile */
	.mode-selection-card {
		margin-top: var(--dynamic-sm) !important;
	}

	.mode-selection-row {
		padding: var(--dynamic-sm) !important;
	}

	/* Button toggle responsive */
	.v-btn-toggle.summary-btn .v-btn {
		min-height: 50px !important;
		font-size: 1.1rem !important;
	}

	/* Ensure mode buttons stay in one line on mobile */
	@media (max-width: 768px) {
		.mode-selection-row .d-flex {
			flex-wrap: nowrap !important;
			overflow-x: auto !important;
			scrollbar-width: none !important;
			-ms-overflow-style: none !important;
		}

		.mode-selection-row .d-flex::-webkit-scrollbar {
			display: none !important;
		}
	}
}

/* Mode Selection Card Styling */
.mode-selection-card {
	background-color: var(--surface-secondary) !important;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.mode-selection-row {
	padding: var(--dynamic-md) !important;
	background: #13110b !important;
}

/* Large Mode Selection Buttons Styling */
.mode-btn-large {
	transition: all 0.3s ease !important;
	min-width: 180px !important;
	border-radius: 12px !important;
	font-weight: 600 !important;
	font-size: 1.1rem !important;
	text-transform: uppercase !important;
	letter-spacing: 0.5px !important;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

.mode-btn-large:hover {
	transform: translateY(-2px) !important;
	box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25) !important;
}

.mode-btn-large .v-icon {
	margin-right: 8px !important;
	font-size: 24px !important;
}

.mode-btn-text {
	font-weight: 600 !important;
}

/* Controls container for horizontal layout */
.controls-container {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 5px;
	flex-wrap: wrap;
}

.control-item {
	display: flex;
	align-items: center;
}

/* Gap utility class */
.gap-2 {
	gap: 8px;
}

/* Compact mode buttons styling */
.mode-btn-compact {
	transition: all 0.3s ease !important;
	min-width: 120px !important;
	border-radius: 8px !important;
	font-weight: 500 !important;
	font-size: 0.9rem !important;
	text-transform: uppercase !important;
	letter-spacing: 0.3px !important;
	box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
	height: 48px !important;
}

.mode-btn-compact:hover {
	transform: translateY(-1px) !important;
	box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
}

.mode-btn-compact .v-icon {
	margin-right: 6px !important;
	font-size: 18px !important;
}

.mode-btn-compact .mode-btn-text {
	font-weight: 500 !important;
	font-size: 0.85rem !important;
}

/* Standard button styling - compact size */
.summary-btn {
	min-height: 60px !important;
	font-size: 1.3rem !important;
	font-weight: 600 !important;
	text-transform: none;
	margin: 1px;
	border-radius: 6px;
	padding: 6px 8px !important;
	white-space: nowrap !important;
}

/* Icon link button styling */
.icon-link-btn {
	min-width: 60px !important;
	min-height: 60px !important;
	border-radius: 50% !important;
	transition: all 0.3s ease !important;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.icon-link-btn:hover {
	transform: scale(1.1) !important;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

.icon-link-btn .v-icon {
	font-size: 28px !important;
}

/* 🆕 Barcode input styling */
.barcode-input :deep(.v-field__input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

.barcode-input :deep(.v-field__input input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

/* Mode-specific border colors and background */
.search-mode-barcode :deep(.v-field__outline) {
	border-left: 4px solid rgb(var(--v-theme-primary)) !important;
	border-color: rgb(var(--v-theme-primary)) !important;
}

.search-mode-barcode :deep(.v-field) {
	background-color: rgba(var(--v-theme-primary), 0.05) !important;
}

.search-mode-text :deep(.v-field__outline) {
	border-left: 4px solid rgb(var(--v-theme-orange)) !important;
	border-color: rgb(var(--v-theme-orange)) !important;
}

.search-mode-text :deep(.v-field) {
	background-color: rgba(255, 152, 0, 0.05) !important;
}

/* Enhanced visual feedback when focused */
.search-mode-barcode :deep(.v-field--focused .v-field__outline) {
	border-width: 2px !important;
	border-color: rgb(var(--v-theme-primary)) !important;
	box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.15) !important;
}

.search-mode-text :deep(.v-field--focused .v-field__outline) {
	border-width: 2px !important;
	border-color: rgb(var(--v-theme-orange)) !important;
	box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.15) !important;
}

/* Mode indicator badge */
.mode-indicator-badge {
	display: flex;
	justify-content: flex-start;
	margin-top: 4px;
}

.mode-chip {
	font-size: 0.7rem !important;
	font-weight: 600 !important;
	letter-spacing: 0.5px !important;
	transition: all 0.2s ease !important;
}

.mode-chip:hover {
	transform: scale(1.05) !important;
}

/* Keyboard hint styling */
.keyboard-hint {
	font-size: 0.75rem !important;
	color: rgba(var(--v-theme-on-surface), 0.6) !important;
	font-style: italic;
}

/* Search results styling */
.search-results-card {
	border: 2px solid rgb(var(--v-theme-primary));
	border-radius: 8px !important;
}

.search-results-list {
	max-height: 300px;
	overflow-y: auto;
}

.search-result-item {
	transition: background-color 0.2s ease;
	cursor: pointer;
}

.search-result-item:hover,
.search-result-item.selected-result {
	background-color: rgba(var(--v-theme-primary), 0.1) !important;
}

.selected-result {
	border-left: 4px solid rgb(var(--v-theme-primary)) !important;
}

/* 🆕 NumPad Styling */
.numpad-card {
	border-radius: 16px !important;
}

.numpad-display :deep(.v-field__input) {
	text-align: center !important;
	font-size: 2rem !important;
	font-weight: bold !important;
	color: rgb(var(--v-theme-primary)) !important;
}

.numpad-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 12px;
	max-width: 300px;
	margin: 0 auto;
}

.numpad-btn {
	aspect-ratio: 1;
	font-size: 1.5rem !important;
	font-weight: bold !important;
	min-height: 60px !important;
	border-radius: 12px !important;
	transition: all 0.2s ease !important;
}

.numpad-btn:hover {
	transform: scale(1.05) !important;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

.numpad-btn-wide {
	grid-column: span 2;
	aspect-ratio: 2/1;
}

.numpad-clear-btn {
	font-size: 1.2rem !important; /* Smaller font for CLEAR button */
	white-space: nowrap !important; /* Prevent text wrapping */
	overflow: hidden !important; /* Hide overflow text */
	text-overflow: ellipsis !important; /* Show ... if text is too long */
}

/* 🆕 Product Confirmation Popup Styling */
.product-confirmation-card {
	border-radius: 16px !important;
	overflow: hidden;
}

.quantity-section {
	background-color: rgba(var(--v-theme-surface), 0.5);
	border-radius: 12px;
	padding: 16px;
}

.quantity-input :deep(.v-field__input) {
	text-align: center !important;
	font-size: 1.5rem !important;
	font-weight: bold !important;
	color: rgb(var(--v-theme-primary)) !important;
}

.total-section {
	background-color: rgba(var(--v-theme-primary), 0.05);
	border-radius: 12px;
	padding: 16px;
}

/* Product confirmation responsive */
@media (max-width: 768px) {
	.product-confirmation-card {
		margin: 8px;
	}
	
	.quantity-input :deep(.v-field__input) {
		font-size: 1.3rem !important;
	}
}

/* QTY Input Field Styling */
.qty-input-field {
	cursor: pointer !important;
}

.qty-input-field :deep(.v-field__input) {
	cursor: pointer !important;
}

/* Standard text field styling - match InvoiceSummary */
.standard-text-field :deep(.v-field__input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

.standard-text-field :deep(.v-field__input input) {
	font-size: 1.4rem !important;
	font-weight: 700 !important;
	min-height: 60px !important;
}

/* ensure long button labels stay within the button */
.summary-btn :deep(.v-btn__content) {
	white-space: normal !important;
}

/* Responsive adjustments for compact buttons */
@media (max-width: 768px) {
	.mode-btn-compact {
		min-width: 100px !important;
		font-size: 0.8rem !important;
		height: 44px !important;
	}

	.mode-btn-compact .v-icon {
		font-size: 16px !important;
		margin-right: 4px !important;
	}

	.mode-btn-compact .mode-btn-text {
		font-size: 0.8rem !important;
	}

	.summary-btn {
		min-height: 50px !important;
		font-size: 1.1rem !important;
	}

	.icon-link-btn {
		min-width: 50px !important;
		min-height: 50px !important;
	}

	.icon-link-btn .v-icon {
		font-size: 24px !important;
	}

	.barcode-input :deep(.v-field__input) {
		font-size: 1.2rem !important;
		min-height: 50px !important;
	}
	
	.barcode-input :deep(.v-field__input input) {
		font-size: 1.2rem !important;
		min-height: 50px !important;
	}
	
	.keyboard-hint {
		display: none; /* Hide on mobile */
	}
	
	.mode-indicator-badge {
		margin-top: 2px;
	}
	
	.mode-chip {
		font-size: 0.6rem !important;
	}
	
	/* NumPad responsive */
	.numpad-btn {
		min-height: 50px !important;
		font-size: 1.3rem !important;
	}
	
	.numpad-clear-btn {
		font-size: 1.0rem !important; /* Even smaller on mobile */
	}
	
	.numpad-display :deep(.v-field__input) {
		font-size: 1.8rem !important;
	}

	.standard-text-field :deep(.v-field__input) {
		font-size: 1.2rem !important;
		min-height: 50px !important;
	}

	.standard-text-field :deep(.v-field__input input) {
		font-size: 1.2rem !important;
		min-height: 50px !important;
	}
}

@media (max-width: 480px) {
	.controls-container,
	.controls-container-right {
		flex-direction: column;
		gap: 8px;
	}

	.control-item {
		width: 100%;
		justify-content: center;
	}

	.mode-btn-compact {
		width: 100% !important;
		min-width: unset !important;
		max-width: 200px !important;
	}

	/* Button toggle mobile responsive */
	.v-btn-toggle.summary-btn {
		width: 100% !important;
	}

	.v-btn-toggle.summary-btn .v-btn {
		flex: 1 !important;
		min-height: 48px !important;
		font-size: 1rem !important;
	}

	.summary-btn {
		min-height: 48px !important;
		font-size: 1rem !important;
		padding: 4px 6px !important;
	}

	.standard-text-field :deep(.v-field__input) {
		font-size: 1.1rem !important;
		min-height: 48px !important;
	}

	.standard-text-field :deep(.v-field__input input) {
		font-size: 1.1rem !important;
		min-height: 48px !important;
	}

	.icon-link-btn {
		min-width: 48px !important;
		min-height: 48px !important;
	}

	.icon-link-btn .v-icon {
		font-size: 20px !important;
	}
}
</style>
