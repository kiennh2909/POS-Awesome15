<template>
	<v-dialog 
		v-model="isVisible" 
		max-width="1000px"
		max-height="650px"
		persistent
		@keydown="handleGlobalKeydown"
	>
		<v-card class="numpad-exact-design">
			<!-- Header with Teal Background -->
			<v-card-title class="numpad-header-exact">
				<v-icon class="mr-3" size="large">mdi-package-variant</v-icon>
				<div class="header-content">
					<div class="header-title">Chỉnh Sửa Sản Phẩm</div>
				</div>
				<v-btn 
					icon="mdi-close" 
					variant="text" 
					color="white"
					@click="closeNumPad"
					size="large"
					class="close-btn"
				></v-btn>
			</v-card-title>

			<!-- Main Content - 3 Column Layout -->
			<v-card-text class="pa-0">
				<div class="three-column-layout">
					<!-- Left Column: Item Info -->
					<div class="left-column">
						<!-- Item Information -->
						<div class="info-section-exact">
							<h3 class="section-title-exact">Thông Tin Sản Phẩm</h3>
							<div class="info-item-exact">
								<span class="info-label-exact">Mã:</span> 
								<span class="info-value-exact">{{ selectedItem?.item_code || 'VT181801' }}</span>
							</div>
							<div class="info-item-exact">
								<span class="info-label-exact">Tên:</span> 
								<span class="info-value-exact">{{ selectedItem?.item_name || '1EGQPIE 蛋塔' }}</span>
							</div>
							<div class="info-item-exact">
								<span class="info-label-exact">ĐVT:</span> 
								<span class="info-value-exact">{{ selectedUom || selectedItem?.uom || '份' }}</span>
							</div>
						</div>

						<!-- Field Selection -->
						<div class="field-section-exact">
							<h3 class="section-title-exact">Chọn Trường Chỉnh Sửa</h3>
							<div class="field-buttons-exact">
								<v-btn
									variant="flat"
									color="teal"
									class="field-btn-exact active-field-exact"
									disabled
								>
									<v-icon class="mr-2">mdi-counter</v-icon>
									SỐ LƯỢNG
								</v-btn>
								<v-btn
									variant="outlined"
									color="grey"
									class="field-btn-exact disabled-field-exact"
									disabled
								>
									<v-icon class="mr-2">mdi-currency-usd</v-icon>
									ĐƠN GIÁ
								</v-btn>
							</div>
						</div>

						<!-- Current Price Display -->
						<div class="price-section-exact">
							<h3 class="section-title-exact">Giá Trị Hiện Tại</h3>
							<div class="price-display-exact">
								<div class="price-label-exact">Đơn Giá</div>
								<div class="price-value-exact">$ {{ formatPrice(selectedItem?.rate || 35) }}</div>
							</div>
						</div>
					</div>

					<!-- Middle Column: UOM Selection -->
					<div class="middle-column">
						<div class="uom-selection-exact">
							<v-btn
								v-for="uom in availableUoms"
								:key="uom.uom"
								:variant="selectedUom === uom.uom ? 'flat' : 'outlined'"
								:color="selectedUom === uom.uom ? 'light-blue' : 'grey'"
								class="uom-btn-exact"
								:class="{ 'uom-active': selectedUom === uom.uom }"
								@click="selectUom(uom.uom)"
							>
								<div class="uom-btn-content">
									<div class="uom-main-text">{{ getUomMainText(uom) }}</div>
									<div class="uom-sub-text" v-if="getUomSubText(uom)">{{ getUomSubText(uom) }}</div>
								</div>
							</v-btn>
						</div>
					</div>

					<!-- Right Column: NumPad -->
					<div class="right-column">
						<!-- Quantity Input Display -->
						<div class="qty-input-exact">
							<div class="input-label-exact">Nhập Số Lượng</div>
							<div class="qty-display-exact">
								<span class="qty-value-exact">{{ displayValue || '19' }}</span>
							</div>
						</div>

						<!-- NumPad Grid -->
						<div class="numpad-grid-exact">
							<!-- Row 1: Action Buttons -->
							<div class="numpad-row-exact">
								<v-btn class="numpad-btn-exact delete-btn-exact" @click="deleteItem">
									DELETE
								</v-btn>
								<v-btn class="numpad-btn-exact minus-btn-exact" @click="decreaseValue">
									- -
								</v-btn>
								<v-btn class="numpad-btn-exact plus-btn-exact" @click="increaseValue">
									+ +
								</v-btn>
								<v-btn class="numpad-btn-exact backspace-btn-exact" @click="backspace">
									<v-icon>mdi-close</v-icon>
								</v-btn>
							</div>

							<!-- Row 2: 7, 8, 9 -->
							<div class="numpad-row-exact">
								<v-btn 
									v-for="num in [7, 8, 9]" 
									:key="num"
									class="numpad-btn-exact number-btn-exact" 
									@click="inputNumber(num)"
								>
									{{ num }}
								</v-btn>
							</div>

							<!-- Row 3: 4, 5, 6 -->
							<div class="numpad-row-exact">
								<v-btn 
									v-for="num in [4, 5, 6]" 
									:key="num"
									class="numpad-btn-exact number-btn-exact" 
									@click="inputNumber(num)"
								>
									{{ num }}
								</v-btn>
							</div>

							<!-- Row 4: 1, 2, 3 -->
							<div class="numpad-row-exact">
								<v-btn 
									v-for="num in [1, 2, 3]" 
									:key="num"
									class="numpad-btn-exact number-btn-exact" 
									@click="inputNumber(num)"
								>
									{{ num }}
								</v-btn>
							</div>

							<!-- Row 5: 0, ., 000, CLEAR -->
							<div class="numpad-row-exact">
								<v-btn class="numpad-btn-exact number-btn-exact" @click="inputNumber(0)">
									0
								</v-btn>
								<v-btn class="numpad-btn-exact number-btn-exact" @click="inputDecimal">
									.
								</v-btn>
								<v-btn class="numpad-btn-exact number-btn-exact" @click="inputTripleZero">
									000
								</v-btn>
								<v-btn class="numpad-btn-exact clear-btn-exact" @click="clear">
									CLEAR
								</v-btn>
							</div>

							<!-- Row 6: ENTER -->
							<div class="numpad-row-exact">
								<v-btn 
									class="numpad-btn-exact enter-btn-exact" 
									@click="confirmValue"
									:disabled="hasError"
									block
								>
									<v-icon class="mr-2">mdi-check</v-icon>
									ENTER - XÁC NHẬN
								</v-btn>
							</div>
						</div>
					</div>
				</div>
			</v-card-text>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	name: 'ItemEditNumPad',
	props: {
		visible: {
			type: Boolean,
			default: false
		},
		selectedItem: {
			type: Object,
			default: null
		},
		initialField: {
			type: String,
			default: 'qty'
		}
	},
	data() {
		return {
			selectedField: 'qty', // Only qty allowed, no rate/discount editing
			displayValue: '',
			originalValue: '',
			hasError: false,
			errorMessage: '',
			selectedUom: null
		};
	},
	computed: {
		isVisible: {
			get() {
				return this.visible;
			},
			set(value) {
				if (!value) {
					this.closeNumPad();
				}
			}
		},
		
		// Get available UOMs for this item - with sample data matching the design
		availableUoms() {
			if (!this.selectedItem || !this.selectedItem.item_uoms) {
				// Sample UOMs matching the design
				return [
					{ uom: 'CÁI' },
					{ uom: 'BOX LỐC 6' },
					{ uom: 'CARTON THÙNG 24' },
					{ uom: 'CARTON THÙNG 48' }
				];
			}
			return this.selectedItem.item_uoms || [];
		}
	},
	watch: {
		visible(newVal) {
			if (newVal) {
				this.initializeNumPad();
			}
		},
		
		displayValue() {
			this.validateInput();
		}
	},
	methods: {
		initializeNumPad() {
			this.selectedField = 'qty'; // Always qty only
			this.selectedUom = this.selectedItem?.uom || 'Túi';
			this.initializeFieldValue();
			this.hasError = false;
			this.errorMessage = '';
		},
		
		initializeFieldValue() {
			if (!this.selectedItem) return;
			
			const value = this.selectedItem.qty || 0;
			this.originalValue = String(value);
			this.displayValue = this.originalValue;
		},
		
		// UOM Selection
		selectUom(uom) {
			this.selectedUom = uom;
			console.log('[NumPad] UOM selected:', uom);
			
			// Emit UOM change event
			this.$emit('update-field', {
				field: 'uom',
				value: uom,
				item: this.selectedItem
			});
		},
		
		// NumPad Input Methods
		inputNumber(num) {
			if (this.displayValue === '0' || this.displayValue === this.originalValue) {
				this.displayValue = String(num);
			} else {
				this.displayValue += String(num);
			}
		},
		
		inputDecimal() {
			if (this.displayValue.includes('.')) return;
			
			if (!this.displayValue || this.displayValue === this.originalValue) {
				this.displayValue = '0.';
			} else {
				this.displayValue += '.';
			}
		},
		
		inputTripleZero() {
			if (this.displayValue === '0' || this.displayValue === this.originalValue) {
				this.displayValue = '0';
			} else {
				this.displayValue += '000';
			}
		},
		
		backspace() {
			if (this.displayValue.length > 0) {
				this.displayValue = this.displayValue.slice(0, -1);
			}
			if (!this.displayValue) {
				this.displayValue = '0';
			}
		},
		
		clear() {
			this.displayValue = '0';
		},
		
		increaseValue() {
			const currentValue = parseFloat(this.displayValue) || 0;
			this.displayValue = String(currentValue + 1);
		},
		
		decreaseValue() {
			const currentValue = parseFloat(this.displayValue) || 0;
			const newValue = Math.max(0, currentValue - 1);
			this.displayValue = String(newValue);
		},
		
		// Validation - Only for quantity
		validateInput() {
			this.hasError = false;
			this.errorMessage = '';
			
			const value = parseFloat(this.displayValue);
			
			if (isNaN(value)) {
				this.hasError = true;
				this.errorMessage = 'Giá trị không hợp lệ';
				return;
			}
			
			if (value <= 0) {
				this.hasError = true;
				this.errorMessage = 'Số lượng phải lớn hơn 0';
				return;
			}
		},
		
		// Actions
		confirmValue() {
			if (this.hasError) return;
			
			const value = parseFloat(this.displayValue);
			
			// Emit quantity update
			this.$emit('update-field', {
				field: 'qty',
				value: value,
				item: this.selectedItem
			});
			
			// Emit UOM update if changed
			if (this.selectedUom !== this.selectedItem?.uom) {
				this.$emit('update-field', {
					field: 'uom',
					value: this.selectedUom,
					item: this.selectedItem
				});
			}
			
			// Emit special event for F2 focus after confirmation
			this.$emit('confirmed-and-close');
		},
		
		deleteItem() {
			this.$emit('delete-item', this.selectedItem);
			this.closeNumPad();
		},
		
		closeNumPad() {
			this.$emit('close');
		},
		
		// Keyboard Handling
		handleGlobalKeydown(event) {
			event.stopPropagation();
			
			const key = event.key;
			
			// Numbers
			if (/^[0-9]$/.test(key)) {
				event.preventDefault();
				this.inputNumber(parseInt(key));
				return;
			}
			
			// Special keys
			switch (key) {
				case '.':
					event.preventDefault();
					this.inputDecimal();
					break;
				case 'Backspace':
					event.preventDefault();
					this.backspace();
					break;
				case 'Delete':
					event.preventDefault();
					this.clear();
					break;
				case 'Enter':
					event.preventDefault();
					this.confirmValue();
					break;
				case 'Escape':
					event.preventDefault();
					this.closeNumPad();
					break;
				case '+':
					event.preventDefault();
					this.increaseValue();
					break;
				case '-':
					event.preventDefault();
					this.decreaseValue();
					break;
			}
		},
		
		// UOM Text Parsing
		getUomMainText(uom) {
			// Parse UOM to get main text (first part)
			const uomStr = uom.uom || uom;
			const parts = uomStr.split(' ');
			return parts[0] || uomStr;
		},
		
		getUomSubText(uom) {
			// Parse UOM to get sub text (second part)
			const uomStr = uom.uom || uom;
			const parts = uomStr.split(' ');
			return parts.slice(1).join(' ') || '';
		},
		
		// Utility Methods
		formatPrice(value) {
			return Math.round(value || 0);
		}
	}
};
</script>

<style scoped>
/* Main Container - Exact Design Match */
.numpad-exact-design {
	border-radius: 0;
	overflow: hidden;
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
	max-height: 650px;
	background: white;
}

/* Header - Exact Teal Match */
.numpad-header-exact {
	background: linear-gradient(135deg, #26a69a, #00695c) !important;
	color: white !important;
	padding: 16px 24px;
	min-height: 70px;
	border-radius: 0;
}

.header-content {
	flex-grow: 1;
}

.header-title {
	font-size: 1.4rem;
	font-weight: 600;
	margin-bottom: 0;
}

.close-btn {
	background: rgba(255, 255, 255, 0.1) !important;
}

.close-btn:hover {
	background: rgba(255, 255, 255, 0.2) !important;
}

/* 3-Column Layout */
.three-column-layout {
	display: flex;
	height: 550px;
	background: white;
}

/* Left Column - Item Info */
.left-column {
	width: 300px;
	background: #f8f9fa;
	padding: 20px;
	border-right: 1px solid #e0e0e0;
}

/* Middle Column - UOM Selection */
.middle-column {
	width: 200px;
	background: #f0f0f0;
	padding: 20px 10px;
	border-right: 1px solid #e0e0e0;
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
}

/* Right Column - NumPad */
.right-column {
	flex: 1;
	background: white;
	padding: 20px;
}

/* Left Column Sections */
.info-section-exact {
	margin-bottom: 24px;
}

.section-title-exact {
	font-size: 1rem;
	font-weight: 600;
	color: #333;
	margin-bottom: 12px;
	border-bottom: 2px solid #26a69a;
	padding-bottom: 4px;
}

/* Item Info Section */
.info-section {
	margin-bottom: 16px;
}

.info-item {
	margin-bottom: 6px;
	font-size: 0.9rem;
}

.info-label {
	font-weight: 600;
	color: #555;
	min-width: 35px;
	display: inline-block;
}

.info-value {
	color: #333;
	font-weight: 500;
}

/* Field Selection */
.field-section {
	margin-bottom: 16px;
}

.field-buttons {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.field-btn {
	width: 100% !important;
	height: 40px !important;
	font-weight: 600 !important;
	text-transform: none !important;
	justify-content: flex-start !important;
	font-size: 0.85rem !important;
}

.active-field {
	background: #26a69a !important;
	color: white !important;
}

.disabled-field {
	opacity: 0.5 !important;
}

/* Price Display */
.price-section {
	margin-bottom: 16px;
}

.price-display {
	background: white;
	border: 2px solid #e0e0e0;
	border-radius: 8px;
	padding: 12px;
	text-align: center;
}

.price-label {
	font-size: 0.8rem;
	color: #666;
	margin-bottom: 2px;
}

.price-value {
	font-size: 1.4rem;
	font-weight: 700;
	color: #26a69a;
}

/* UOM Buttons */
.uom-section {
	margin-bottom: 16px;
}

.uom-buttons {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
}

.uom-btn {
	min-width: 60px !important;
	height: 36px !important;
	font-size: 0.85rem !important;
	font-weight: 600 !important;
}

/* Right Panel */
.right-panel {
	padding: 16px;
}

/* Quantity Input Display */
.qty-input-section {
	margin-bottom: 16px;
}

.input-label {
	font-size: 0.9rem;
	font-weight: 600;
	color: #555;
	margin-bottom: 6px;
	text-align: center;
}

.qty-display {
	background: white;
	border: 3px solid #26a69a;
	border-radius: 12px;
	padding: 12px;
	text-align: center;
	min-height: 50px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.qty-value {
	font-size: 1.8rem;
	font-weight: 700;
	color: #333;
}

/* NumPad Grid - Removed duplicate, see Compact Layout section */

.numpad-btn {
	flex: 1;
	height: 50px !important;
	font-size: 1.1rem !important;
	font-weight: 700 !important;
	border-radius: 8px !important;
	text-transform: none !important;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
	transition: all 0.2s ease !important;
}

.numpad-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

/* Button Colors */
.number-btn {
	background: #26a69a !important;
	color: white !important;
}

.number-btn:hover {
	background: #00695c !important;
}

.delete-btn {
	background: #f44336 !important;
	color: white !important;
}

.delete-btn:hover {
	background: #d32f2f !important;
}

.minus-btn {
	background: #ff9800 !important;
	color: white !important;
}

.minus-btn:hover {
	background: #f57c00 !important;
}

.plus-btn {
	background: #4caf50 !important;
	color: white !important;
}

.plus-btn:hover {
	background: #388e3c !important;
}

.backspace-btn {
	background: #9e9e9e !important;
	color: white !important;
}

.backspace-btn:hover {
	background: #757575 !important;
}

.clear-btn {
	background: #ff9800 !important;
	color: white !important;
	font-size: 0.9rem !important;
}

.clear-btn:hover {
	background: #f57c00 !important;
}

.enter-btn {
	background: #4caf50 !important;
	color: white !important;
	height: 48px !important;
	font-size: 1rem !important;
}

.enter-btn:hover {
	background: #388e3c !important;
}

.enter-btn:disabled {
	background: #e0e0e0 !important;
	color: #9e9e9e !important;
}

/* Dark Theme Support */
:deep(.v-theme--dark) .left-panel {
	background: #2a2a2a;
}

:deep(.v-theme--dark) .section-title {
	color: #fff;
}

:deep(.v-theme--dark) .info-label {
	color: #bbb;
}

:deep(.v-theme--dark) .info-value {
	color: #fff;
}

:deep(.v-theme--dark) .price-display {
	background: #333;
	border-color: #555;
}

:deep(.v-theme--dark) .qty-display {
	background: #333;
}

:deep(.v-theme--dark) .qty-value {
	color: #fff;
}

/* Dialog Size Control */
.v-dialog {
	align-items: center !important;
}

.v-dialog > .v-overlay__content {
	max-height: 90vh !important;
	overflow: hidden !important;
}

/* Compact Layout */
.numpad-grid-redesign {
	display: flex;
	flex-direction: column;
	gap: 6px;
	max-height: 350px;
}

.numpad-row {
	display: flex;
	gap: 6px;
}

/* Responsive Design */
@media (max-width: 768px) {
	.item-edit-numpad-redesign {
		margin: 8px;
		max-width: calc(100vw - 16px) !important;
		max-height: calc(100vh - 16px) !important;
	}
	
	.left-panel {
		margin-right: 8px;
		padding: 12px;
		max-height: 400px;
	}
	
	.right-panel {
		padding: 12px;
	}
	
	.numpad-btn {
		height: 45px !important;
		font-size: 1rem !important;
	}
	
	.qty-value {
		font-size: 1.6rem;
	}
	
	.price-value {
		font-size: 1.3rem;
	}
	
	.numpad-grid-redesign {
		max-height: 300px;
	}
}
</style>

/* Item Info */
.info-item-exact {
	margin-bottom: 8px;
	font-size: 0.9rem;
}

.info-label-exact {
	font-weight: 600;
	color: #555;
	min-width: 40px;
	display: inline-block;
}

.info-value-exact {
	color: #333;
	font-weight: 500;
}

/* Field Selection */
.field-section-exact {
	margin-bottom: 24px;
}

.field-buttons-exact {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.field-btn-exact {
	width: 100% !important;
	height: 44px !important;
	font-weight: 600 !important;
	text-transform: none !important;
	justify-content: flex-start !important;
	font-size: 0.9rem !important;
}

.active-field-exact {
	background: #26a69a !important;
	color: white !important;
}

.disabled-field-exact {
	opacity: 0.5 !important;
	background: #f5f5f5 !important;
}

/* Price Display */
.price-section-exact {
	margin-bottom: 16px;
}

.price-display-exact {
	background: white;
	border: 2px solid #e0e0e0;
	border-radius: 8px;
	padding: 16px;
	text-align: center;
}

.price-label-exact {
	font-size: 0.9rem;
	color: #666;
	margin-bottom: 4px;
}

.price-value-exact {
	font-size: 1.6rem;
	font-weight: 700;
	color: #26a69a;
}

/* UOM Selection - Middle Column */
.uom-selection-exact {
	display: flex;
	flex-direction: column;
	gap: 12px;
	height: 100%;
}

.uom-btn-exact {
	width: 100% !important;
	height: 80px !important;
	padding: 8px !important;
	border-radius: 8px !important;
	text-transform: none !important;
	background: white !important;
	border: 2px solid #e0e0e0 !important;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
	transition: all 0.2s ease !important;
}

.uom-btn-exact:hover {
	border-color: #26a69a !important;
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

.uom-btn-exact.uom-active {
	background: #e3f2fd !important;
	border-color: #2196f3 !important;
	color: #1976d2 !important;
}

.uom-btn-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	height: 100%;
}

.uom-main-text {
	font-size: 1.1rem;
	font-weight: 700;
	color: #333;
	margin-bottom: 2px;
}

.uom-active .uom-main-text {
	color: #1976d2;
}

.uom-sub-text {
	font-size: 0.8rem;
	font-weight: 500;
	color: #666;
	text-align: center;
	line-height: 1.2;
}

.uom-active .uom-sub-text {
	color: #1976d2;
}

/* Right Column - Quantity Input */
.qty-input-exact {
	margin-bottom: 20px;
}

.input-label-exact {
	font-size: 1rem;
	font-weight: 600;
	color: #555;
	margin-bottom: 8px;
	text-align: center;
}

.qty-display-exact {
	background: white;
	border: 3px solid #26a69a;
	border-radius: 12px;
	padding: 16px;
	text-align: center;
	min-height: 70px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.qty-value-exact {
	font-size: 2.5rem;
	font-weight: 700;
	color: #333;
}

/* NumPad Grid - Exact Design */
.numpad-grid-exact {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.numpad-row-exact {
	display: flex;
	gap: 8px;
}

.numpad-btn-exact {
	flex: 1;
	height: 55px !important;
	font-size: 1.2rem !important;
	font-weight: 700 !important;
	border-radius: 8px !important;
	text-transform: none !important;
	box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
	transition: all 0.2s ease !important;
}

.numpad-btn-exact:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
}

/* Button Colors - Exact Match */
.number-btn-exact {
	background: #26a69a !important;
	color: white !important;
}

.number-btn-exact:hover {
	background: #00695c !important;
}

.delete-btn-exact {
	background: #f44336 !important;
	color: white !important;
	font-size: 0.9rem !important;
}

.delete-btn-exact:hover {
	background: #d32f2f !important;
}

.minus-btn-exact {
	background: #ff9800 !important;
	color: white !important;
}

.minus-btn-exact:hover {
	background: #f57c00 !important;
}

.plus-btn-exact {
	background: #4caf50 !important;
	color: white !important;
}

.plus-btn-exact:hover {
	background: #388e3c !important;
}

.backspace-btn-exact {
	background: #9e9e9e !important;
	color: white !important;
}

.backspace-btn-exact:hover {
	background: #757575 !important;
}

.clear-btn-exact {
	background: #ff9800 !important;
	color: white !important;
	font-size: 0.9rem !important;
}

.clear-btn-exact:hover {
	background: #f57c00 !important;
}

.enter-btn-exact {
	background: #4caf50 !important;
	color: white !important;
	height: 50px !important;
	font-size: 1rem !important;
}

.enter-btn-exact:hover {
	background: #388e3c !important;
}

.enter-btn-exact:disabled {
	background: #e0e0e0 !important;
	color: #9e9e9e !important;
}

/* Dark Theme Support */
:deep(.v-theme--dark) .three-column-layout {
	background: #1e1e1e;
}

:deep(.v-theme--dark) .left-column {
	background: #2a2a2a;
	border-right-color: #444;
}

:deep(.v-theme--dark) .middle-column {
	background: #333;
	border-right-color: #444;
}

:deep(.v-theme--dark) .right-column {
	background: #1e1e1e;
}

:deep(.v-theme--dark) .section-title-exact {
	color: #fff;
}

:deep(.v-theme--dark) .info-label-exact {
	color: #bbb;
}

:deep(.v-theme--dark) .info-value-exact {
	color: #fff;
}

:deep(.v-theme--dark) .price-display-exact {
	background: #333;
	border-color: #555;
}

:deep(.v-theme--dark) .qty-display-exact {
	background: #333;
}

:deep(.v-theme--dark) .qty-value-exact {
	color: #fff;
}

:deep(.v-theme--dark) .uom-btn-exact {
	background: #333 !important;
	border-color: #555 !important;
}

:deep(.v-theme--dark) .uom-main-text {
	color: #fff;
}

:deep(.v-theme--dark) .uom-sub-text {
	color: #bbb;
}

/* Responsive Design */
@media (max-width: 1024px) {
	.three-column-layout {
		height: auto;
		min-height: 500px;
	}
	
	.left-column {
		width: 280px;
	}
	
	.middle-column {
		width: 180px;
	}
}

@media (max-width: 768px) {
	.three-column-layout {
		flex-direction: column;
		height: auto;
	}
	
	.left-column,
	.middle-column,
	.right-column {
		width: 100%;
		border-right: none;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.middle-column {
		padding: 15px;
	}
	
	.uom-selection-exact {
		flex-direction: row;
		flex-wrap: wrap;
		gap: 8px;
	}
	
	.uom-btn-exact {
		width: calc(50% - 4px) !important;
		height: 60px !important;
	}
	
	.numpad-btn-exact {
		height: 50px !important;
		font-size: 1.1rem !important;
	}
	
	.qty-value-exact {
		font-size: 2rem;
	}
}
</style>