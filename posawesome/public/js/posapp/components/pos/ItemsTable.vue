<template>
	<div
		class="my-0 py-0 overflow-y-auto items-table-container"
		:style="{ height: 'calc(100vh - 400px)', maxHeight: 'calc(100vh - 400px)' }"
		@dragover="onDragOverFromSelector($event)"
		@drop="onDropFromSelector($event)"
		@dragenter="onDragEnterFromSelector"
		@dragleave="onDragLeaveFromSelector"
	>
		<v-data-table-virtual
			:headers="headers"
			:items="items"
			:theme="$theme.current"
			:expanded="expanded"
			show-expand
			item-value="posa_row_id"
			class="modern-items-table elevation-2"
			:items-per-page="itemsPerPage"
			expand-on-click
			density="compact"
			hide-default-footer
			:single-expand="true"
			:header-props="headerProps"
			:item-class="getRowClass"
			:item-props="getItemProps"
			@update:expanded="$emit('update:expanded', $event)"

			:search="itemSearch"
		>
			<!-- Name column (Tên + Mã Barcode) -->
			<template v-slot:item.item_name="{ item }">
				<div class="item-name-display">
					<div class="item-name">{{ item.item_name }}</div>
					<div class="item-code text-caption text-grey">{{ item.item_code }}</div>
				</div>
			</template>

			<!-- Quantity column - Clickable QTY Field -->
			<template v-slot:item.qty="{ item }">
				<div 
					class="qty-field-clickable"
					@click.stop="handleQtyClick(item)"
					:class="{ 'qty-selected': selectedItemForEdit?.posa_row_id === item.posa_row_id }"
				>
					<div class="qty-value">
						{{ formatFloat(item.qty, hide_qty_decimals ? 0 : undefined) }}
					</div>
					<v-icon v-if="selectedItemForEdit?.posa_row_id === item.posa_row_id" 
						size="small" 
						class="qty-edit-icon">
						mdi-calculator-variant
					</v-icon>
				</div>
			</template>

			<!-- Rate column -->
			<template v-slot:item.rate="{ item }">
				<div class="currency-display">
					<span
						v-if="item.is_free_item || (item.posa_is_offer && item.rate === 0)"
						class="free-badge"
					>
						<v-chip size="small" color="success" variant="flat" class="free-chip">
							<v-icon size="small" class="mr-1">mdi-gift</v-icon>
							FREE
						</v-chip>
					</span>
					<span v-else>
							<span class="amount-value">{{ formatCurrency(getRateUomBase(item) * (item.conversion_factor || 1), 0) }}</span>
					</span>
				</div>
			</template>

			<!-- RATE_UOM_BASE column -->
			<template v-slot:item.rate_uom_base="{ item }">
				<div class="currency-display">
					<span class="amount-value">{{ formatCurrency(getRateUomBase(item), 0) }}</span>
				</div>
			</template>

			<!-- Amount before discount column (Tổng chưa giảm = Giá × Qty) -->
			<template v-slot:item.amount_before_discount="{ item }">
				<div class="currency-display">
					<span class="amount-value">{{ formatCurrency(item.qty * (getRateUomBase(item) * (item.conversion_factor || 1)), 0) }}</span>
				</div>
			</template>

			<!-- Net Amount before VAT column (Thành tiền = Tổng chưa giảm - Giảm giá) -->
			<template v-slot:item.net_amount_before_vat="{ item }">
				<div class="currency-display">
					<span class="currency-symbol">{{ currencySymbol(displayCurrency) }}</span>
					<span class="amount-value">{{ formatCurrency((item.qty * (getRateUomBase(item) * (item.conversion_factor || 1))) - (item.discount_amount || 0), 0) }}</span>
				</div>
			</template>

			<!-- VAT Amount column (Tiền VAT = VatRate × Thành tiền) -->
			<template v-slot:item.vat_amount="{ item }">
				<div class="currency-display">
					<span class="amount-value">{{ formatCurrency(((item.qty * (getRateUomBase(item) * (item.conversion_factor || 1))) - (item.discount_amount || 0)) * ((item.custom_vat_rate || 0) / 100), 0) }}</span>
					<span v-if="item.custom_vat_rate" class="text-caption text-orange ml-1">
						({{ item.custom_vat_rate }}%)
					</span>
				</div>
			</template>

			<!-- Total with VAT column (Tổng phụ(có VAT) = After Discount + VAT Amount) -->
			<template #item.total_with_vat="{ item }">
				<div class="currency-display net-amount-cell" title="Tổng tiền bao gồm VAT">
					<v-icon size="small" color="success" class="mr-1">mdi-cash</v-icon>
					<span class="amount-value net-amount-value">{{ formatCurrency(calculateTotalWithVat(item), 0) }}</span>
				</div>
			</template>

			<!-- Discount percentage column -->
			<template v-slot:item.discount_value="{ item }">
				<div class="amount-value">
					{{
						formatFloat(
							item.discount_percentage ||
								(item.price_list_rate
									? (item.discount_amount / item.price_list_rate) * 100
									: 0),
						)
					}}%
				</div>
			</template>

			<!-- Discount amount column -->
			<template v-slot:item.discount_amount="{ item }">
				<div class="currency-display">
					<span class="amount-value">{{ formatCurrency(item.discount_amount || 0, 0) }}</span>
				</div>
			</template>

			<!-- Price list rate column -->
			<template v-slot:item.price_list_rate="{ item }">
				<div class="currency-display">
					<span class="amount-value">{{ formatCurrency(item.price_list_rate, 0) }}</span>
				</div>
			</template>

			<!-- Offer checkbox column -->
			<template v-slot:item.posa_is_offer="{ item }">
				<v-checkbox-btn
					v-model="item.posa_is_offer"
					class="center"
					@change="handleOfferToggle(item)"
				></v-checkbox-btn>
			</template>

			<!-- Pack info column -->
			<template v-slot:item.pack_info="{ item }">
				<div class="pack-info-display">
					<v-chip
						v-if="getPackInfo(item)"
						:color="getPackInfo(item).color"
						size="small"
						variant="flat"
						class="pack-chip"
					>
						<v-icon size="small" class="mr-1">{{ getPackInfo(item).icon }}</v-icon>
						{{ getPackInfo(item).text }}
					</v-chip>
				</div>
			</template>

			<!-- Expanded row content using Vuetify's built-in system -->
			<template v-slot:expanded-row="{ item }">
				<td :colspan="headers.length" class="ma-0 pa-0">
					<div class="expanded-content">
						<!-- Action buttons with improved layout and visual feedback -->
						<div class="action-panel">
							<div class="action-button-group">
								<v-btn
									:disabled="!!item.posa_is_replace"
									icon="mdi-trash-can-outline"
									size="large"
									color="error"
									variant="tonal"
									class="item-action-btn delete-btn"
									@click.stop="removeItem(item)"
								>
									<v-icon size="large">mdi-trash-can-outline</v-icon>
									<span class="action-label">{{ __("Remove") }}</span>
								</v-btn>
							</div>

							<div class="action-button-group">
								<v-btn
									:disabled="!!item.posa_is_replace"
									size="large"
									color="warning"
									variant="tonal"
									class="item-action-btn minus-btn"
									@click.stop="subtractOne(item)"
								>
									<v-icon size="large">mdi-minus-circle-outline</v-icon>
									<span class="action-label">{{ __("Decrease") }}</span>
								</v-btn>
								<v-btn
									:disabled="!!item.posa_is_replace"
									size="large"
									color="success"
									variant="tonal"
									class="item-action-btn plus-btn"
									@click.stop="addOne(item)"
								>
									<v-icon size="large">mdi-plus-circle-outline</v-icon>
									<span class="action-label">{{ __("Increase") }}</span>
								</v-btn>
							</div>
						</div>

						<!-- Item details form with all fields -->
						<div class="item-details-form">
							<!-- First row of fields -->
							<div class="form-row">
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Mã SP')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										v-model="item.item_code"
										disabled
										prepend-inner-icon="mdi-barcode"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('SL')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="
											formatFloat(item.qty, hide_qty_decimals ? 0 : undefined)
										"
										@change="onQtyChange(item, $event.target.value)"
										:rules="[isNumber]"
										:disabled="!!item.posa_is_replace"
										prepend-inner-icon="mdi-numeric"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-select
										density="compact"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										:label="frappe._('ĐVT')"
										v-model="item.uom"
										:items="item.item_uoms"
										variant="outlined"
										item-title="uom"
										item-value="uom"
										hide-details
										@update:model-value="onUomChange(item, $event)"
										:disabled="
											!!item.posa_is_replace ||
											(isReturnInvoice && invoice_doc.return_against)
										"
										prepend-inner-icon="mdi-weight"
									></v-select>
								</div>
							</div>

							<!-- Second row of fields -->
							<div class="form-row">
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										id="rate"
										:label="frappe._('Đơn giá')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatCurrency(getRateUomBase(item) * (item.conversion_factor || 1))"
										@change="[
											setFormatedCurrency(item, 'rate', null, false, $event),
											calcPrices(item, $event.target.value, $event),
										]"
										:disabled="!!item.posa_is_replace || !!item.posa_offer_applied"
										prepend-inner-icon="mdi-currency-usd"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('VAT (%)')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="item.custom_vat_rate || ''"
										disabled
										prepend-inner-icon="mdi-percent"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Thành tiền (*incl VAT)')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatCurrency(getRateUomBase(item) * (item.conversion_factor || 1), 0)"
										disabled
										prepend-inner-icon="mdi-currency-usd"
									></v-text-field>
								</div>
							</div>

							<!-- Third row of fields -->
							<div class="form-row">
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										id="discount_percentage"
										:label="frappe._('Giảm giá %')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatFloat(item.discount_percentage || 0)"
										@change="[
											setFormatedCurrency(
												item,
												'discount_percentage',
												null,
												false,
												$event,
											),
											calcPrices(item, $event.target.value, $event),
										]"
										:disabled="!!item.posa_is_replace || !!item.posa_offer_applied"
										prepend-inner-icon="mdi-percent"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										id="discount_amount"
										:label="frappe._('Giảm giá')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatCurrency(item.discount_amount || 0, 0)"
										@change="[
											setFormatedCurrency(item, 'discount_amount', null, false, $event),
											calcPrices(item, $event.target.value, $event),
										]"
										:disabled="!!item.posa_is_replace || !!item.posa_offer_applied"
										prepend-inner-icon="mdi-tag-minus"
									></v-text-field>
								</div>
							</div>

							<!-- Third row of fields -->
							<div class="form-row">
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Đơn giá')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatCurrency(getRateUomBase(item) * (item.conversion_factor || 1), 0)"
										:disabled="!pos_profile.posa_allow_price_list_rate_change"
										:prefix="currencySymbol(pos_profile.currency)"
										@change="changePriceListRate(item)"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('SL có sẵn')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatFloat(item.actual_qty)"
										disabled
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Nhóm')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										v-model="item.item_group"
										disabled
									></v-text-field>
								</div>
							</div>

							<!-- Fourth row of fields -->
							<div class="form-row">
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('SL tồn')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatFloat(item.stock_qty)"
										disabled
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('ĐVT tồn')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										v-model="item.stock_uom"
										disabled
									></v-text-field>
								</div>
								<div class="form-field" v-if="item.posa_offer_applied">
									<v-checkbox
										density="compact"
										:label="frappe._('KM')"
										v-model="item.posa_offer_applied"
										readonly
										hide-details
										class="mt-1"
									></v-checkbox>
								</div>
							</div>

							<!-- Serial Number Section -->
							<div class="form-section" v-if="item.has_serial_no == 1 || item.serial_no">
								<div class="form-row">
									<div class="form-field">
										<v-text-field
											density="compact"
											variant="outlined"
											color="primary"
											:label="frappe._('SL Serial')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field"
											hide-details
											v-model="item.serial_no_selected_count"
											type="number"
											disabled
										></v-text-field>
									</div>
								</div>
								<div class="form-row">
									<div class="form-field full-width">
										<v-autocomplete
											v-model="item.serial_no_selected"
											:items="item.serial_no_data"
											item-title="serial_no"
											item-value="serial_no"
											variant="outlined"
											density="compact"
											chips
											color="primary"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field"
											:label="frappe._('Số Serial')"
											multiple
											@update:model-value="setSerialNo(item)"
										></v-autocomplete>
									</div>
								</div>
							</div>

							<!-- Batch Number Section -->
							<div class="form-section" v-if="item.has_batch_no == 1 || item.batch_no">
								<div class="form-row">
									<div class="form-field">
										<v-text-field
											density="compact"
											variant="outlined"
											color="primary"
											:label="frappe._('SL Batch có sẵn')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field"
											hide-details
											:model-value="formatFloat(item.actual_batch_qty)"
											disabled
										></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field
											density="compact"
											variant="outlined"
											color="primary"
											:label="frappe._('Ngày hết hạn Batch')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field"
											hide-details
											v-model="item.batch_no_expiry_date"
											disabled
										></v-text-field>
									</div>
									<div class="form-field">
										<v-autocomplete
											v-model="item.batch_no"
											:items="item.batch_no_data"
											item-title="batch_no"
											variant="outlined"
											density="compact"
											color="primary"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field"
											:label="frappe._('Số Batch')"
											@update:model-value="setBatchQty(item, $event)"
											hide-details
										>
											<template v-slot:item="{ props, item }">
												<v-list-item v-bind="props">
													<v-list-item-title
														v-html="item.raw.batch_no"
													></v-list-item-title>
													<v-list-item-subtitle
														v-html="
															`Available QTY  '${item.raw.batch_qty}' - Expiry Date ${item.raw.expiry_date}`
														"
													></v-list-item-subtitle>
												</v-list-item>
											</template>
										</v-autocomplete>
									</div>
								</div>
							</div>

							<!-- Delivery Date Section -->
							<div
								class="form-section"
								v-if="pos_profile.posa_allow_sales_order && invoiceType == 'Order'"
							>
								<div class="form-row">
									<div class="form-field">
										<VueDatePicker
											v-model="item.posa_delivery_date"
											model-type="format"
											format="dd-MM-yyyy"
											:min-date="new Date()"
											auto-apply
											:dark="isDarkTheme"
											@update:model-value="validateDueDate(item)"
										/>
									</div>
								</div>
							</div>

							<!-- Fourth row for warehouse and other details -->
							<div class="form-row">
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Kho')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										v-model="item.warehouse"
										disabled
										prepend-inner-icon="mdi-warehouse"
									></v-text-field>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Đơn giá')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatCurrency(getRateUomBase(item) * (item.conversion_factor || 1), 0)"
										:disabled="!pos_profile.posa_allow_price_list_rate_change"
										prepend-inner-icon="mdi-format-list-numbered"
										@change="changePriceListRate(item)"
									></v-text-field>
									<v-btn
										v-if="pos_profile.posa_allow_price_list_rate_change"
										size="x-small"
										class="ml-1"
										@click.stop="changePriceListRate(item)"
										>{{ __("Change") }}</v-btn
									>
								</div>
								<div class="form-field">
									<v-text-field
										density="compact"
										variant="outlined"
										color="primary"
										:label="frappe._('Thanh toán')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field"
										hide-details
										:model-value="formatCurrency(item.qty * (getRateUomBase(item) * (item.conversion_factor || 1)), 0)"
										disabled
										prepend-inner-icon="mdi-calculator"
									></v-text-field>
								</div>
							</div>
						</div>
					</div>
				</td>
			</template>
		</v-data-table-virtual>

		<!-- 🆕 Item Edit NumPad -->
		<ItemEditNumPad
			:visible="numpadVisible"
			:selected-item="selectedItemForEdit"
			:initial-field="initialEditField"
			@update-field="handleUpdateField"
			@delete-item="handleDeleteItem"
			@close="closeNumPad"
			@confirmed-and-close="handleConfirmedAndClose"
		/>
	</div>
</template>

<script>
import ItemEditNumPad from './ItemEditNumPad.vue';

export default {
	name: "ItemsTable",
	components: {
		ItemEditNumPad
	},
	props: {
		headers: Array,
		items: Array,
		expanded: Array,
		itemsPerPage: Number,
		itemSearch: String,
		pos_profile: Object,
		invoice_doc: Object,
		invoiceType: String,
		displayCurrency: String,
		formatFloat: Function,
		formatCurrency: Function,
		currencySymbol: Function,
		isNumber: Function,
		setFormatedQty: Function,
		calcStockQty: Function,
		setFormatedCurrency: Function,
		calcPrices: Function,
		calcUom: Function,
		setSerialNo: Function,
		setBatchQty: Function,
		validateDueDate: Function,
		removeItem: Function,
		subtractOne: Function,
		addOne: Function,
		isReturnInvoice: Boolean,
		toggleOffer: Function,
		changePriceListRate: Function,
	},
	data() {
		return {
			draggedItem: null,
			draggedIndex: null,
			dragOverIndex: null,
			isDragging: false,
			highlightedRowId: null,
			
			// 🆕 Smart Highlight System
			highlightedItems: new Map(), // Map<itemCode, highlightConfig>
			highlightTimers: new Map(), // Map<itemCode, timerId>
			lastHighlightTime: new Map(), // Map<itemCode, timestamp> for debouncing
			
			// 🆕 NumPad State
			numpadVisible: false,
			selectedItemForEdit: null,
			initialEditField: 'qty'
		};
	},
	computed: {
		headerProps() {
			return this.isDarkTheme ? { style: "background-color:#121212;color:#fff" } : {};
		},
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
		hide_qty_decimals() {
			try {
				const saved = localStorage.getItem("posawesome_item_selector_settings");
				if (saved) {
					const opts = JSON.parse(saved);
					return !!opts.hide_qty_decimals;
				}
			} catch (e) {
				console.error("Failed to load item selector settings:", e);
			}
			return false;
		},
	},
	watch: {
		items: {
			handler(newItems) {
				console.log(
					"[ItemsTable] Items updated - checking rates:",
					newItems.map((item) => ({
						Item_code: item.item_code,
						Price: item.custom_price_list_rate_after_vat || item.rate,
						VAT_Rate: item.custom_vat_rate,
						Uom: item.uom,
						qty: item.qty,
						amount: item.qty * (item.custom_price_list_rate_after_vat || item.rate),
						base_rate: item.base_rate,
						conversion_factor: item.conversion_factor,
						expected_price: item.base_rate * (item.conversion_factor || 1),
					})),
				);

				// Check if any item has wrong price (should be base_rate * conversion_factor for UOM items)
				// DISABLED: Auto-fix logic is causing issues with barcode scanning
				// The UOM conversion should be handled properly in invoiceItemMethods.js
				newItems.forEach((item) => {
					// Only log for debugging, don't auto-fix prices
					console.log("[ItemsTable] Price check (no auto-fix):", {
						Item_code: item.item_code,
						uom: item.uom,
						stock_uom: item.stock_uom,
						conversion_factor: item.conversion_factor,
						base_rate: item.base_rate,
						current_rate: item.custom_price_list_rate_after_vat || item.rate,
						vat_rate: item.custom_vat_rate,
						posa_offer_applied: item.posa_offer_applied,
					});
				});
			},
			deep: true,
			immediate: true,
		},
	},
	mounted() {
		console.log("[ItemsTable] ✅ Mounted successfully, setting up listeners");
		console.log("[ItemsTable] 📋 Props received:", {
			hasToggleOffer: typeof this.toggleOffer === "function",
			itemsCount: this.items?.length || 0,
			headersCount: this.headers?.length || 0,
			headers: this.headers?.map(h => h.key) || [],
		});

		// Listen for force update events
		this.eventBus.on("force_items_table_update", () => {
			console.log("[ItemsTable] Force update triggered by event");
			this.$forceUpdate();
		});

		// Listen for highlight events
		this.eventBus.on("highlight_invoice_item", (data) => {
			console.log("[ItemsTable] 📨 Received highlight_invoice_item event:", data);
			this.highlightItem(data.itemRowId);
		});

		this.eventBus.on("highlight_scanned_item", (itemCode) => {
			console.log("[ItemsTable] 📨 Received old highlight_scanned_item event for:", itemCode);
			this.highlightItem(itemCode);
		});
		
		// 🆕 Listen for smart highlight events
		this.eventBus.on("smart_highlight_item", (config) => {
			console.log("[ItemsTable] 📨 Received smart_highlight_item event:", config);
			this.handleSmartHighlight(config);
		});
	},
	beforeUnmount() {
		// Cleanup event listeners
		if (this.eventBus) {
			this.eventBus.off("force_items_table_update");
			this.eventBus.off("highlight_invoice_item");
			this.eventBus.off("highlight_scanned_item");
			this.eventBus.off("smart_highlight_item"); // 🆕 Cleanup smart highlight
		}
		
		// 🆕 Cleanup highlight timers
		this.highlightTimers.forEach(timer => clearTimeout(timer));
		this.highlightTimers.clear();
		this.highlightedItems.clear();
	},
	methods: {
		getRowClass(item) {
			// 🆕 Enhanced row class with smart highlight types
			const highlightConfig = this.highlightedItems.get(item.item_code);
			
			if (highlightConfig) {
				if (highlightConfig.highlightType === 'new_item') {
					return 'row-highlight-new-item';
				} else if (highlightConfig.highlightType === 'quantity_update') {
					return 'row-highlight-quantity-update';
				}
			}
			
			// Fallback to old system
			return this.highlightedRowId === item.posa_row_id ? "row-highlight" : "";
		},
		
		// 🆕 SMART HIGHLIGHT SYSTEM
		handleSmartHighlight(config) {
			const { itemCode, rowId, isNewItem, duration, highlightType, newQuantity } = config;
			
			console.log('[ItemsTable] 🎯 Smart highlight triggered:', {
				itemCode,
				isNewItem,
				highlightType,
				duration
			});
			
			// Debounce rapid scans of same item
			const now = Date.now();
			const lastTime = this.lastHighlightTime.get(itemCode) || 0;
			
			if (now - lastTime < 300 && highlightType === 'quantity_update') {
				console.log('[ItemsTable] ⏭️ Debouncing rapid scan of same item');
				// Extend existing highlight instead of creating new one
				this.extendHighlight(itemCode, duration);
				return;
			}
			
			this.lastHighlightTime.set(itemCode, now);
			
			// Clear existing timer for this item
			const existingTimer = this.highlightTimers.get(itemCode);
			if (existingTimer) {
				clearTimeout(existingTimer);
			}
			
			// Set highlight config
			this.highlightedItems.set(itemCode, {
				isNewItem,
				highlightType,
				newQuantity,
				startTime: now
			});
			
			// Force update to apply CSS classes
			this.$forceUpdate();
			
			// Scroll item into view if needed
			this.$nextTick(() => {
				this.scrollItemIntoView(itemCode, isNewItem);
			});
			
			// Set timer to remove highlight
			const timer = setTimeout(() => {
				this.highlightedItems.delete(itemCode);
				this.highlightTimers.delete(itemCode);
				this.$forceUpdate();
				console.log('[ItemsTable] ✅ Highlight removed for:', itemCode);
			}, duration);
			
			this.highlightTimers.set(itemCode, timer);
		},
		
		extendHighlight(itemCode, additionalDuration) {
			const existingTimer = this.highlightTimers.get(itemCode);
			if (existingTimer) {
				clearTimeout(existingTimer);
			}
			
			const timer = setTimeout(() => {
				this.highlightedItems.delete(itemCode);
				this.highlightTimers.delete(itemCode);
				this.$forceUpdate();
			}, additionalDuration);
			
			this.highlightTimers.set(itemCode, timer);
		},
		
		scrollItemIntoView(itemCode, isNewItem) {
			// Find the row element
			const tableElement = this.$el.querySelector('.modern-items-table');
			if (!tableElement) return;
			
			// Find item in items array
			const itemIndex = this.items.findIndex(item => item.item_code === itemCode);
			if (itemIndex === -1) return;
			
			// For new items at top (index 0), no scroll needed - already visible
			if (isNewItem && itemIndex === 0) {
				console.log('[ItemsTable] 📍 New item at top, no scroll needed');
				return;
			}
			
			// For existing items, check if visible
			const rows = tableElement.querySelectorAll('tbody tr');
			const targetRow = rows[itemIndex];
			
			if (!targetRow) return;
			
			// Check if row is in viewport
			const rect = targetRow.getBoundingClientRect();
			const containerRect = tableElement.getBoundingClientRect();
			
			const isVisible = (
				rect.top >= containerRect.top &&
				rect.bottom <= containerRect.bottom
			);
			
			if (!isVisible) {
				console.log('[ItemsTable] 📜 Scrolling item into view:', itemCode);
				targetRow.scrollIntoView({
					behavior: 'smooth',
					block: 'center'
				});
			} else {
				console.log('[ItemsTable] ✅ Item already visible, no scroll needed');
			}
		},
		getItemProps(item) {
			return {
				"data-row-id": item.posa_row_id,
				"data-item-code": item.item_code,
			};
		},
		onUomChange(item, value) {
			this.calcUom(item, value);
			this.eventBus.emit("uom_changed", item, value);
		},

		onDragOverFromSelector(event) {
			// Check if drag data is from item selector
			const dragData = event.dataTransfer.types.includes("application/json");
			if (dragData) {
				event.preventDefault();
				event.dataTransfer.dropEffect = "copy";
			}
		},

		onDragEnterFromSelector(event) {
			this.$emit("show-drop-feedback", true);
		},

		onDragLeaveFromSelector(event) {
			// Only hide feedback if leaving the entire table area
			if (!event.currentTarget.contains(event.relatedTarget)) {
				this.$emit("show-drop-feedback", false);
			}
		},

		onDropFromSelector(event) {
			event.preventDefault();

			try {
				const dragData = JSON.parse(event.dataTransfer.getData("application/json"));

				if (dragData.type === "item-from-selector") {
					this.$emit("add-item-from-drag", dragData.item);
					this.$emit("item-dropped", false);
				}
			} catch (error) {
				console.error("Error parsing drag data:", error);
			}
		},

		highlightItem(key) {
			const idx = this.items.findIndex((it) => it.posa_row_id === key || it.item_code === key);
			if (idx < 0) return;

			this.highlightedRowId = this.items[idx].posa_row_id;

			this.$nextTick(() => {
				// Tìm chính <tr> theo data-row-id đã gắn từ getItemProps
				const rowEl = this.$el.querySelector(`[data-row-id="${this.highlightedRowId}"]`);
				if (rowEl && rowEl.scrollIntoView) {
					rowEl.scrollIntoView({ block: "center", behavior: "smooth" });
				} else {
					// Fallback: scroll container của virtual table nếu cần
					const scroller =
						this.$el.querySelector(".v-data-table__wrapper") ||
						this.$el.querySelector(".v-table__wrapper") ||
						this.$el.querySelector(".v-virtual-scroll");
					if (scroller)
						scroller.scrollTop = Math.max(0, rowEl?.offsetTop - scroller.clientHeight / 2 || 0);
				}

				setTimeout(() => (this.highlightedRowId = null), 1200);
			});
		},

		// Handle offer toggle with debug logging
		handleOfferToggle(item) {
			console.log("🎯 [ITEMS_TABLE] Offer checkbox clicked for item:", {
				item_code: item.item_code,
				posa_row_id: item.posa_row_id,
				current_posa_is_offer: item.posa_is_offer,
				timestamp: new Date().toISOString(),
			});

			// Call the parent toggleOffer method
			this.toggleOffer(item);
		},

		// Handle quantity change from direct input
		onQtyChange(item, value) {
			console.log(
				"📝 [QTY_CHANGE] Direct qty input for item:",
				item.item_code,
				"from:",
				item.qty,
				"to:",
				value,
			);

			// Update qty using setFormatedQty
			this.setFormatedQty(item, "qty", null, false, value);

			// Calculate stock qty
			this.calcStockQty(item, item.qty);

			// Trigger discount calculation (same as INCREASE/DECREASE buttons)
			if (!this.$parent.isApplyingDiscount) {
				console.log("📝 [QTY_CHANGE] Triggering discount calculation for direct qty input");
				this.$parent.$nextTick(() => {
					setTimeout(() => {
						this.$parent.calculateDiscountsDebounced();
						console.log(
							"✅ [QTY_CHANGE] calculateDiscountsDebounced() called for direct qty input",
						);
					}, 10);
				});
			} else {
				console.log("📝 [QTY_CHANGE] Skipping discount calculation - isApplyingDiscount is true");
			}

			// Force UI update
			this.$forceUpdate();
		},

		// Get pack information for display
		getPackInfo(item) {
			// Check if item is part of a pack based on UOM (dynamic)
			if (item.uom && item.uom.includes("THÙNG")) {
				// Extract pack size from UOM (e.g., 'THÙNG-24' -> 24)
				const packSizeMatch = item.uom.match(/THÙNG-(\d+)/);
				if (packSizeMatch) {
					const packSize = parseInt(packSizeMatch[1]);
					// Dynamic pack display based on size
					let color = "info";
					let icon = "mdi-package-variant";

					// Color coding based on pack size (can be customized)
					if (packSize >= 20) {
						color = "success";
						icon = "mdi-package-variant-closed";
					} else if (packSize >= 10) {
						color = "primary";
						icon = "mdi-package-variant";
					} else if (packSize >= 5) {
						color = "secondary";
						icon = "mdi-package-variant";
					}

					return {
						text: `${packSize} Pack`,
						icon: icon,
						color: color,
					};
				}
			}

			// Check if item has offer applied (combo discount)
			if (item.posa_offer_applied) {
				return {
					text: "Combo",
					icon: "mdi-percent",
					color: "warning",
				};
			}

			// Default for single items
			return null;
		},

		// Get RATE_UOM_BASE: đơn giá cơ bản không VAT của đơn vị tồn kho
		getRateUomBase(item) {
			// Lấy base_rate (giá không VAT của stock UOM)
			return item.base_rate || 0;
		},

		// Calculate Total with VAT: After Discount + VAT Amount
		calculateTotalWithVat(item) {
			const afterDiscount = (item.qty * (this.getRateUomBase(item) * (item.conversion_factor || 1))) - (item.discount_amount || 0);
			const vatAmount = afterDiscount * ((item.custom_vat_rate || 0) / 100);
			return afterDiscount + vatAmount;
		},

		// 🆕 NUMPAD INTEGRATION METHODS

		// Handle QTY field click to open NumPad
		handleQtyClick(item) {
			console.log('[ItemsTable] 🔢 QTY field clicked for NumPad:', item.item_code);
			
			this.selectedItemForEdit = item;
			this.initialEditField = 'qty'; // Always QTY since user clicked QTY field
			this.numpadVisible = true;
			
			console.log('[ItemsTable] ✅ NumPad opened for QTY edit:', {
				item_code: item.item_code,
				item_name: item.item_name,
				current_qty: item.qty,
				focus_field: 'qty'
			});
		},

		// Handle field update from NumPad
		handleUpdateField({ field, value, item }) {
			console.log('[ItemsTable] 📝 Updating field from NumPad:', {
				field,
				value,
				item_code: item.item_code,
				old_value: item[field]
			});

			switch (field) {
				case 'qty':
					this.updateItemQty(item, value);
					break;
				case 'uom':
					this.updateItemUom(item, value);
					break;
				default:
					console.warn('[ItemsTable] ⚠️ Unknown field:', field);
			}

			// Keep NumPad open for further edits
			// User can close with ESC or click close button
			console.log('[ItemsTable] ✅ Field updated, NumPad remains open');
		},

		// Update item quantity
		updateItemQty(item, newQty) {
			console.log('[ItemsTable] 📊 Updating quantity:', {
				item_code: item.item_code,
				old_qty: item.qty,
				new_qty: newQty
			});

			// Use existing setFormatedQty method
			this.setFormatedQty(item, 'qty', null, false, newQty);
			this.calcStockQty(item, newQty);

			// Trigger discount calculation (same as INCREASE/DECREASE buttons)
			if (!this.$parent.isApplyingDiscount) {
				console.log('[ItemsTable] 🔄 Triggering discount calculation for NumPad qty update');
				this.$parent.$nextTick(() => {
					setTimeout(() => {
						this.$parent.calculateDiscountsDebounced();
						console.log('[ItemsTable] ✅ calculateDiscountsDebounced() called for NumPad qty update');
					}, 10);
				});
			} else {
				console.log('[ItemsTable] ⏭️ Skipping discount calculation - isApplyingDiscount is true');
			}

			// Force UI update
			this.$forceUpdate();
		},

		// Update item UOM
		updateItemUom(item, newUom) {
			console.log('[ItemsTable] 📏 Updating UOM:', {
				item_code: item.item_code,
				old_uom: item.uom,
				new_uom: newUom
			});

			// Use existing onUomChange method
			this.onUomChange(item, newUom);

			// Force UI update
			this.$forceUpdate();
		},

		// Handle delete item from NumPad
		handleDeleteItem(item) {
			console.log('[ItemsTable] 🗑️ Deleting item from NumPad:', item.item_code);
			this.removeItem(item);
			this.closeNumPad();
		},

		// Close NumPad
		closeNumPad() {
			console.log('[ItemsTable] ❌ Closing NumPad');
			this.numpadVisible = false;
			this.selectedItemForEdit = null;
		},

		// Handle confirmed and close - Focus back to F2 barcode
		handleConfirmedAndClose() {
			console.log('[ItemsTable] ✅ NumPad confirmed, closing and focusing F2 barcode');
			
			// Close NumPad first
			this.closeNumPad();
			
			// Focus back to F2 barcode input after a short delay
			this.$nextTick(() => {
				setTimeout(() => {
					this.focusF2BarcodeInput();
				}, 100);
			});
		},

		// Focus F2 barcode input field
		focusF2BarcodeInput() {
			try {
				// Try multiple selectors to find the barcode input
				const barcodeSelectors = [
					'input[placeholder*="barcode"]',
					'input[placeholder*="Barcode"]', 
					'input[placeholder*="mã vạch"]',
					'input[placeholder*="Mã vạch"]',
					'.barcode-input input',
					'.search-input input',
					'#barcode-input',
					'input[type="text"]:first-of-type'
				];
				
				let barcodeInput = null;
				
				for (const selector of barcodeSelectors) {
					barcodeInput = document.querySelector(selector);
					if (barcodeInput) {
						console.log('[ItemsTable] 🎯 Found barcode input with selector:', selector);
						break;
					}
				}
				
				if (barcodeInput) {
					barcodeInput.focus();
					barcodeInput.select(); // Select all text if any
					console.log('[ItemsTable] ✅ F2 Barcode input focused successfully');
					
					// Emit event to parent components
					this.$emit('barcode-focused');
				} else {
					console.warn('[ItemsTable] ⚠️ Could not find barcode input field');
					
					// Try to emit event to parent to handle F2 focus
					this.$emit('request-barcode-focus');
				}
			} catch (error) {
				console.error('[ItemsTable] ❌ Error focusing barcode input:', error);
			}
		},
	},
};
</script>

<style scoped>
/* Modern table styling with enhanced visual hierarchy */
.modern-items-table {
	border-radius: var(--border-radius-lg);
	overflow: hidden;
	box-shadow: var(--shadow-md);
	border: 1px solid rgba(0, 0, 0, 0.09);
	height: 100%;
	display: flex;
	flex-direction: column;
	transition: all 0.3s ease;
}

/* Ensure items table can scroll when many rows exist */
.items-table-container {
	overflow-y: auto;
	scrollbar-width: thin;
	scroll-behavior: smooth;
}

/* Force table wrapper to scroll properly */
.items-table-container :deep(.v-data-table__wrapper) {
	max-height: 100%;
	overflow-y: auto;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
	.items-table-container {
		height: calc(100vh - 350px) !important;
		max-height: calc(100vh - 350px) !important;
	}
}

@media (max-width: 480px) {
	.items-table-container {
		height: calc(100vh - 320px) !important;
		max-height: calc(100vh - 320px) !important;
	}
}

/* Table wrapper styling */
.modern-items-table :deep(.v-data-table__wrapper),
.modern-items-table :deep(.v-table__wrapper) {
	border-radius: var(--border-radius-sm);
	height: 100%;
	overflow-y: auto;
	scrollbar-width: thin;
}

/* Table header styling */
.modern-items-table :deep(th) {
	font-weight: 600;
	font-size: 0.9rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	padding: 12px 16px;
	transition: background-color var(--transition-normal);
	border-bottom: 2px solid var(--table-header-border);
	background-color: var(--table-header-bg);
	color: var(--table-header-text);
	position: sticky;
	top: 0;
	z-index: 1;
}

/* Table row styling */
.modern-items-table :deep(tr) {
	transition: all 0.2s ease;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.modern-items-table :deep(tr:hover) {
	background-color: var(--table-row-hover);
	transform: translateY(-1px);
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

/* Table cell styling */
.modern-items-table :deep(td) {
	padding: 12px 16px;
	vertical-align: middle;
}

/* Expanded content styling */
.expanded-content {
	padding: var(--dynamic-md);
	background-color: var(--surface-secondary);
	border-radius: 0 0 var(--border-radius-md) var(--border-radius-md);
	box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.05);
	animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(-10px);
	}

	to {
		opacity: 1;
		transform: translateY(0);
	}
}

/* Action panel styling */
.action-panel {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 12px;
	margin-bottom: 16px;
	background-color: rgba(0, 0, 0, 0.02);
	border-radius: var(--border-radius-md);
	border: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.dark-theme) .action-panel,
:deep(.v-theme--dark) .action-panel {
	background-color: rgba(255, 255, 255, 0.05);
	border: 1px solid rgba(255, 255, 255, 0.1);
}

.action-button-group {
	display: flex;
	gap: 8px;
}

/* Item action buttons styling */
.item-action-btn {
	min-width: 44px !important;
	height: 44px !important;
	border-radius: 12px !important;
	transition: all 0.3s ease;
	box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1) !important;
	position: relative;
	overflow: hidden;
	display: flex;
	align-items: center;
	padding: 0 16px !important;
}

.item-action-btn .action-label {
	margin-left: 8px;
	font-weight: 500;
	display: none;
}

@media (min-width: 600px) {
	.item-action-btn .action-label {
		display: inline-block;
	}

	.item-action-btn {
		min-width: 120px !important;
	}
}

.item-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 5px 12px rgba(0, 0, 0, 0.15) !important;
}

.item-action-btn .v-icon {
	font-size: 22px !important;
	position: relative;
	z-index: 2;
}

/* Light theme button styles with enhanced gradients */
.item-action-btn.delete-btn {
	background: linear-gradient(145deg, #ffebee, #ffcdd2) !important;
}

.item-action-btn.delete-btn:hover {
	background: linear-gradient(145deg, #ffcdd2, #ef9a9a) !important;
}

.item-action-btn.minus-btn {
	background: linear-gradient(145deg, #fff8e1, #ffecb3) !important;
}

.item-action-btn.minus-btn:hover {
	background: linear-gradient(145deg, #ffecb3, #ffe082) !important;
}

.item-action-btn.plus-btn {
	background: linear-gradient(145deg, #e8f5e9, #c8e6c9) !important;
}

.item-action-btn.plus-btn:hover {
	background: linear-gradient(145deg, #c8e6c9, #a5d6a7) !important;
}

/* Dark theme button styles */
:deep(.dark-theme) .item-action-btn.delete-btn,
:deep(.v-theme--dark) .item-action-btn.delete-btn {
	background: linear-gradient(145deg, #4a1515, #3a1010) !important;
	color: #ff8a80 !important;
}

:deep(.dark-theme) .item-action-btn.delete-btn:hover,
:deep(.v-theme--dark) .item-action-btn.delete-btn:hover {
	background: linear-gradient(145deg, #5a1a1a, #4a1515) !important;
}

:deep(.dark-theme) .item-action-btn.minus-btn,
:deep(.v-theme--dark) .item-action-btn.minus-btn {
	background: linear-gradient(145deg, #4a3c10, #3a2e0c) !important;
	color: #ffe082 !important;
}

:deep(.dark-theme) .item-action-btn.minus-btn:hover,
:deep(.v-theme--dark) .item-action-btn.minus-btn:hover {
	background: linear-gradient(145deg, #5a4a14, #4a3c10) !important;
}

:deep(.dark-theme) .item-action-btn.plus-btn,
:deep(.v-theme--dark) .item-action-btn.plus-btn {
	background: linear-gradient(145deg, #1b4620, #133419) !important;
	color: #a5d6a7 !important;
}

:deep(.dark-theme) .item-action-btn.plus-btn:hover,
:deep(.v-theme--dark) .item-action-btn.plus-btn:hover {
	background: linear-gradient(145deg, #235828, #1b4620) !important;
}

:deep(.dark-theme) .item-action-btn .v-icon,
:deep(.v-theme--dark) .item-action-btn .v-icon {
	opacity: 0.9;
}

/* Form layout styling */
.item-details-form {
	margin-top: 16px;
}

.form-row {
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
	margin-bottom: 12px;
}

.form-field {
	flex: 1;
	min-width: 200px;
}

.form-field.full-width {
	flex-basis: 100%;
}

.form-section {
	margin-top: 16px;
	padding-top: 16px;
	border-top: 1px dashed rgba(0, 0, 0, 0.1);
}

:deep(.dark-theme) .form-section,
:deep(.v-theme--dark) .form-section {
	border-top: 1px dashed rgba(255, 255, 255, 0.1);
}

/* Currency and amount display */
.currency-display {
	display: flex;
	align-items: center;
	justify-content: flex-start;
}

.currency-symbol {
	opacity: 0.7;
	margin-right: 2px;
	font-size: 0.85em;
}

.amount-value {
	font-weight: 500;
	text-align: left;
	transition: font-size 0.3s ease;
}

/* Drag and drop styles */
.draggable-row {
	transition: all 0.2s ease;
	cursor: move;
}

.draggable-row:hover {
	background-color: rgba(0, 0, 0, 0.02);
}

:deep(.dark-theme) .draggable-row:hover,
:deep(.v-theme--dark) .draggable-row:hover {
	background-color: rgba(255, 255, 255, 0.05);
}

.drag-handle-cell {
	width: 40px;
	text-align: center;
	padding: 8px 4px;
}

.drag-handle {
	cursor: grab;
	opacity: 0.6;
	transition: opacity 0.2s ease;
}

.drag-handle:hover {
	opacity: 1;
}

.drag-handle:active {
	cursor: grabbing;
}

.drag-source {
	opacity: 0.5;
	background-color: rgba(25, 118, 210, 0.1) !important;
}

.drag-over {
	background-color: rgba(25, 118, 210, 0.2) !important;
	border-top: 2px solid #1976d2;
	transform: translateY(-1px);
}

.drag-active .draggable-row:not(.drag-source):not(.drag-over) {
	opacity: 0.7;
}

/* Dark theme drag styles */
:deep(.dark-theme) .drag-source,
:deep(.v-theme--dark) .drag-source {
	background-color: rgba(144, 202, 249, 0.1) !important;
}

:deep(.dark-theme) .drag-over,
:deep(.v-theme--dark) .drag-over {
	background-color: rgba(144, 202, 249, 0.2) !important;
	border-top: 2px solid #90caf9;
}

/* Expanded row styling */
.expanded-row {
	background-color: var(--surface-secondary);
}

/* 🆕 SMART HIGHLIGHT SYSTEM - Multi-Cue Feedback */

/* NEW ITEM Highlight - Blue theme for new additions */
:deep(.row-highlight-new-item) {
	animation: flashNewItem 1.2s ease;
	border-left: 4px solid #2196f3 !important; /* Blue for new items */
	background: linear-gradient(90deg, rgba(33, 150, 243, 0.1) 0%, transparent 100%) !important;
}

@keyframes flashNewItem {
	0% {
		background-color: rgba(33, 150, 243, 0.3);
		transform: scale(1.02);
	}
	50% {
		background-color: rgba(33, 150, 243, 0.15);
	}
	100% {
		background-color: transparent;
		transform: scale(1);
	}
}

/* QUANTITY UPDATE Highlight - Green theme for updates */
:deep(.row-highlight-quantity-update) {
	animation: flashQuantityUpdate 0.8s ease;
	border-left: 4px solid #4caf50 !important; /* Green for quantity updates */
}

@keyframes flashQuantityUpdate {
	0% {
		background-color: rgba(76, 175, 80, 0.2);
	}
	50% {
		background-color: rgba(76, 175, 80, 0.1);
	}
	100% {
		background-color: transparent;
	}
}

/* Quantity column pulse effect for updates */
:deep(.row-highlight-quantity-update) .amount-value {
	animation: pulseQuantity 0.6s ease;
	font-weight: 700 !important;
	color: #2e7d32 !important;
}

@keyframes pulseQuantity {
	0% {
		transform: scale(1);
	}
	50% {
		transform: scale(1.1);
		color: #1b5e20 !important;
	}
	100% {
		transform: scale(1);
	}
}

/* Enhanced new item styling */
:deep(.row-highlight-new-item) .item-name {
	font-weight: 600 !important;
	color: #1976d2 !important;
}

:deep(.row-highlight-new-item) .amount-value {
	font-weight: 700 !important;
	color: #1976d2 !important;
}

/* Legacy highlight styling (fallback) */
:deep(.row-highlight) {
	animation: flashRow 1.2s ease;
	border-left: 4px solid #4caf50 !important;
}

@keyframes flashRow {
	from {
		background-color: #c8e6c9;
	}
	to {
		background-color: transparent;
	}
}

:deep(.row-highlight) .amount-value {
	font-weight: 700 !important;
	color: #2e7d32 !important;
}

/* Pack info display styling */
.pack-info-display {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 32px;
}

.pack-chip {
	font-size: 0.75rem !important;
	font-weight: 500;
	text-transform: uppercase;
	letter-spacing: 0.5px;
}

.pack-chip .v-icon {
	margin-right: 4px !important;
}

/* Item name display styling */
.item-name-display {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	min-height: 32px;
}

.item-name {
	font-weight: 500;
	line-height: 1.2;
	margin-bottom: 2px;
}

.item-code {
	font-size: 0.75rem;
	color: #666;
	line-height: 1.1;
}

/* Net amount cell styling - make it more prominent */
.net-amount-cell {
	background-color: rgba(76, 175, 80, 0.08) !important;
	border-radius: 4px;
	padding: 4px 8px;
	border: 1px solid rgba(76, 175, 80, 0.2);
	display: flex;
	align-items: center;
	justify-content: flex-start;
}

.net-amount-cell .v-icon {
	margin-right: 4px;
	flex-shrink: 0;
}

.net-amount-value {
	font-weight: 600 !important;
	color: #2e7d32 !important;
	font-size: 0.95rem;
}

/* Dark theme support for net amount */
:deep(.dark-theme) .net-amount-cell,
:deep(.v-theme--dark) .net-amount-cell {
	background-color: rgba(129, 199, 132, 0.15) !important;
	border: 1px solid rgba(129, 199, 132, 0.3);
}

:deep(.dark-theme) .net-amount-value,
:deep(.v-theme--dark) .net-amount-value {
	color: #81c784 !important;
}

/* Free item badge styling */
.free-badge {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 32px;
}

.free-chip {
	font-size: 0.75rem !important;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	animation: pulse 2s infinite;
}

@keyframes pulse {
	0% {
		transform: scale(1);
	}
	50% {
		transform: scale(1.05);
	}
	100% {
		transform: scale(1);
	}
}

/* 🆕 NUMPAD INTEGRATION STYLES */

/* Clickable QTY Field Styling */
.qty-field-clickable {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	min-width: 60px;
	height: 32px;
	padding: 4px 8px;
	border: 2px solid #e0e0e0;
	border-radius: 6px;
	background: #ffffff;
	cursor: pointer;
	transition: all 0.2s ease;
	position: relative;
	font-weight: 500;
}

.qty-field-clickable:hover {
	border-color: #1976d2;
	background: #f3f8ff;
	transform: translateY(-1px);
	box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
}

.qty-field-clickable.qty-selected {
	border-color: #1976d2;
	background: #e3f2fd;
	box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.qty-value {
	font-size: 1rem;
	font-weight: 600;
	color: #333;
	min-width: 30px;
	text-align: center;
}

.qty-edit-icon {
	margin-left: 4px;
	color: #1976d2;
	animation: pulse 1.5s infinite;
}

@keyframes pulse {
	0%, 100% { opacity: 1; }
	50% { opacity: 0.6; }
}

/* Dark theme support for QTY field */
:deep(.dark-theme) .qty-field-clickable,
:deep(.v-theme--dark) .qty-field-clickable {
	background: #2a2a2a;
	border-color: #555;
	color: #fff;
}

:deep(.dark-theme) .qty-field-clickable:hover,
:deep(.v-theme--dark) .qty-field-clickable:hover {
	border-color: #90caf9;
	background: #1a237e;
}

:deep(.dark-theme) .qty-field-clickable.qty-selected,
:deep(.v-theme--dark) .qty-field-clickable.qty-selected {
	border-color: #90caf9;
	background: #1565c0;
}

:deep(.dark-theme) .qty-value,
:deep(.v-theme--dark) .qty-value {
	color: #fff;
}

/* Remove row hover effect since we're using QTY click */
.modern-items-table :deep(tr:hover) {
	background-color: var(--table-row-hover);
	/* Remove cursor pointer and transform since row is not clickable anymore */
}

/* Selected row for NumPad editing */
.modern-items-table :deep(.v-data-table__tr--selected) {
	background-color: rgba(25, 118, 210, 0.08) !important;
	border-left: 4px solid #1976d2 !important;
	position: relative;
}

.modern-items-table :deep(.v-data-table__tr--selected):before {
	content: '🔢';
	position: absolute;
	left: -2px;
	top: 50%;
	transform: translateY(-50%);
	background: #1976d2;
	color: white;
	width: 20px;
	height: 20px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 10px;
	z-index: 2;
}

/* Dark theme support for selected row */
:deep(.dark-theme) .modern-items-table :deep(.v-data-table__tr--selected),
:deep(.v-theme--dark) .modern-items-table :deep(.v-data-table__tr--selected) {
	background-color: rgba(144, 202, 249, 0.12) !important;
	border-left: 4px solid #90caf9 !important;
}

:deep(.dark-theme) .modern-items-table :deep(.v-data-table__tr--selected):before,
:deep(.v-theme--dark) .modern-items-table :deep(.v-data-table__tr--selected):before {
	background: #90caf9;
	color: #1a1a1a;
}

/* NumPad active indicator */
.numpad-active-indicator {
	position: fixed;
	top: 20px;
	right: 20px;
	background: #1976d2;
	color: white;
	padding: 8px 16px;
	border-radius: 20px;
	font-size: 0.9rem;
	font-weight: 500;
	z-index: 9999;
	animation: slideInRight 0.3s ease;
	box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

@keyframes slideInRight {
	from {
		transform: translateX(100%);
		opacity: 0;
	}
	to {
		transform: translateX(0);
		opacity: 1;
	}
}
</style>

