<template>
	<v-dialog 
		v-model="isVisible" 
		width="800px"
		height="500px"
		persistent
		@keydown="handleGlobalKeydown"
	>
		<v-card class="item-edit-numpad-redesign">
			<!-- Header with Teal Background -->
			<v-card-title class="numpad-header">
				<v-icon class="mr-3" size="large">mdi-package-variant</v-icon>
				<div class="header-content">
					<div class="header-title">Chỉnh Sửa Sản Phẩm</div>
					<div class="header-subtitle">{{ selectedItem?.item_name || 'MANG LA TUOI HA THANH' }}</div>
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

			<!-- Content -->
			<v-card-text class="pa-4">
				<v-row no-gutters>
					<!-- Left Panel: Item Info -->
					<v-col cols="4" class="left-panel">
						<!-- Item Information -->
						<div class="info-section">
							<h3 class="section-title">Thông Tin Sản Phẩm</h3>
							<div class="info-item">
								<span class="info-label">Mã:</span> 
								<span class="info-value">{{ selectedItem?.item_code || '893850105318' }}</span>
							</div>
							<div class="info-item">
								<span class="info-label">Tên:</span> 
								<span class="info-value">{{ selectedItem?.item_name || 'MANG LA TUOI HA THANH' }}</span>
							</div>
							<div class="info-item">
								<span class="info-label">ĐVT:</span> 
								<span class="info-value">{{ selectedUom || selectedItem?.uom || 'Túi' }}</span>
							</div>
						</div>

						<!-- Field Selection - Only QTY -->
						<div class="field-section">
							<h3 class="section-title">Chọn Trường Chỉnh Sửa</h3>
							<div class="field-buttons">
								<v-btn
									variant="flat"
									color="teal"
									class="field-btn active-field"
									disabled
								>
									<v-icon class="mr-2">mdi-counter</v-icon>
									SỐ LƯỢNG
								</v-btn>
								<v-btn
									variant="outlined"
									color="grey"
									class="field-btn disabled-field"
									disabled
								>
									<v-icon class="mr-2">mdi-currency-usd</v-icon>
									ĐƠN GIÁ
								</v-btn>
							</div>
						</div>

						<!-- Current Price Display (Read-only) -->
						<div class="price-section">
							<h3 class="section-title">Giá Trị Hiện Tại</h3>
							<div class="price-display">
								<div class="price-label">Đơn Giá</div>
								<div class="price-value">$ {{ formatPrice(selectedItem?.rate || 65) }}</div>
							</div>
						</div>

						<!-- UOM Selection Buttons - Always Show -->
						<div class="uom-section">
							<h3 class="section-title">Đơn Vị Tính</h3>
							<div class="uom-buttons">
								<v-btn
									v-for="(uom, index) in availableUoms"
									:key="index"
									:variant="selectedUom === (uom.uom || uom) ? 'flat' : 'outlined'"
									:color="selectedUom === (uom.uom || uom) ? 'teal' : 'grey'"
									class="uom-btn"
									@click="selectUom(uom.uom || uom)"
									size="small"
								>
									{{ uom.uom || uom }}
								</v-btn>
							</div>
							<!-- Debug Info (remove after testing) -->
							<div class="debug-info text-caption mt-2">
								<div>UOMs: {{ availableUoms.length }}</div>
								<div>Current: {{ selectedUom }}</div>
							</div>
						</div>
					</v-col>

					<!-- Right Panel: NumPad -->
					<v-col cols="8" class="right-panel">
						<!-- Quantity Input Display -->
						<div class="qty-input-section">
							<div class="input-label">Nhập Số Lượng</div>
							<div class="qty-display">
								<span class="qty-value">{{ displayValue || '0' }}</span>
							</div>
						</div>

						<!-- NumPad Grid -->
						<div class="numpad-grid-redesign">
							<!-- Row 1: Action Buttons -->
							<div class="numpad-row">
								<v-btn class="numpad-btn delete-btn" @click="deleteItem">
									DELETE
								</v-btn>
								<v-btn class="numpad-btn minus-btn" @click="decreaseValue">
									- -
								</v-btn>
								<v-btn class="numpad-btn plus-btn" @click="increaseValue">
									+ +
								</v-btn>
								<v-btn class="numpad-btn backspace-btn" @click="backspace">
									<v-icon>mdi-close</v-icon>
								</v-btn>
							</div>

							<!-- Row 2: 7, 8, 9 -->
							<div class="numpad-row">
								<v-btn 
									v-for="num in [7, 8, 9]" 
									:key="num"
									class="numpad-btn number-btn" 
									@click="inputNumber(num)"
								>
									{{ num }}
								</v-btn>
							</div>

							<!-- Row 3: 4, 5, 6 -->
							<div class="numpad-row">
								<v-btn 
									v-for="num in [4, 5, 6]" 
									:key="num"
									class="numpad-btn number-btn" 
									@click="inputNumber(num)"
								>
									{{ num }}
								</v-btn>
							</div>

							<!-- Row 4: 1, 2, 3 -->
							<div class="numpad-row">
								<v-btn 
									v-for="num in [1, 2, 3]" 
									:key="num"
									class="numpad-btn number-btn" 
									@click="inputNumber(num)"
								>
									{{ num }}
								</v-btn>
							</div>

							<!-- Row 5: 0, ., 000, CLEAR -->
							<div class="numpad-row">
								<v-btn class="numpad-btn number-btn" @click="inputNumber(0)">
									0
								</v-btn>
								<v-btn class="numpad-btn number-btn" @click="inputDecimal">
									.
								</v-btn>
								<v-btn class="numpad-btn number-btn" @click="inputTripleZero">
									000
								</v-btn>
								<v-btn class="numpad-btn clear-btn" @click="clear">
									CLEAR
								</v-btn>
							</div>

							<!-- Row 6: ENTER -->
							<div class="numpad-row">
								<v-btn 
									class="numpad-btn enter-btn" 
									@click="confirmValue"
									:disabled="hasError"
									block
								>
									<v-icon class="mr-2">mdi-check</v-icon>
									ENTER - XÁC NHẬN
								</v-btn>
							</div>
						</div>
					</v-col>
				</v-row>
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
		
		// Get available UOMs for this item
		availableUoms() {
			console.log('[NumPad] Computing availableUoms for item:', this.selectedItem);
			
			// If item has item_uoms array, use it
			if (this.selectedItem?.item_uoms && Array.isArray(this.selectedItem.item_uoms) && this.selectedItem.item_uoms.length > 0) {
				console.log('[NumPad] Using item_uoms:', this.selectedItem.item_uoms);
				return this.selectedItem.item_uoms;
			}
			
			// Fallback: create array with current UOM and some common UOMs
			const currentUom = this.selectedItem?.uom || 'Cái';
			const commonUoms = ['Cái', 'Túi', 'Kg', 'Thùng', 'Hộp', 'Lít'];
			
			// Always include current UOM first
			const uomList = [currentUom];
			
			// Add other common UOMs if they're different
			commonUoms.forEach(uom => {
				if (uom !== currentUom) {
					uomList.push(uom);
				}
			});
			
			console.log('[NumPad] Using fallback UOMs:', uomList);
			return uomList.map(uom => ({ uom }));
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
		
		// Utility Methods
		formatPrice(value) {
			return Math.round(value || 0);
		}
	}
};
</script>

<style scoped>
/* Main Container */
.item-edit-numpad-redesign {
	border-radius: 16px;
	overflow: hidden;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
	height: 500px !important;
	max-height: 500px !important;
	display: flex;
	flex-direction: column;
}

/* Header Styling - Teal Background */
.numpad-header {
	background: linear-gradient(135deg, #26a69a, #00695c) !important;
	color: white !important;
	padding: 12px 16px;
	min-height: 50px;
	flex-shrink: 0;
}

.header-content {
	flex-grow: 1;
}

.header-title {
	font-size: 1.5rem;
	font-weight: 600;
	margin-bottom: 4px;
}

.header-subtitle {
	font-size: 0.9rem;
	opacity: 0.9;
	font-weight: 400;
}

.close-btn {
	background: rgba(255, 255, 255, 0.1) !important;
}

.close-btn:hover {
	background: rgba(255, 255, 255, 0.2) !important;
}

/* Left Panel */
.left-panel {
	background: #f8f9fa;
	border-radius: 12px;
	padding: 12px;
	margin-right: 8px;
	height: 400px;
	max-height: 400px;
	overflow-y: auto;
}

.section-title {
	font-size: 1rem;
	font-weight: 600;
	color: #333;
	margin-bottom: 8px;
	border-bottom: 2px solid #26a69a;
	padding-bottom: 2px;
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
	margin-bottom: 12px;
}

.uom-buttons {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
}

.uom-btn {
	min-width: 50px !important;
	height: 32px !important;
	font-size: 0.8rem !important;
	font-weight: 600 !important;
}

/* Debug Info */
.debug-info {
	background: #fff3cd;
	border: 1px solid #ffeaa7;
	border-radius: 4px;
	padding: 4px 8px;
	font-size: 0.7rem;
	color: #856404;
}

/* Right Panel */
.right-panel {
	padding: 12px;
	height: 400px;
	display: flex;
	flex-direction: column;
}

/* Quantity Input Display */
.qty-input-section {
	margin-bottom: 12px;
	flex-shrink: 0;
}

.input-label {
	font-size: 0.85rem;
	font-weight: 600;
	color: #555;
	margin-bottom: 4px;
	text-align: center;
}

.qty-display {
	background: white;
	border: 3px solid #26a69a;
	border-radius: 10px;
	padding: 10px;
	text-align: center;
	height: 45px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.qty-value {
	font-size: 1.6rem;
	font-weight: 700;
	color: #333;
}

/* NumPad Grid - Removed duplicate, see Compact Layout section */

.numpad-btn {
	flex: 1;
	height: 45px !important;
	font-size: 1rem !important;
	font-weight: 700 !important;
	border-radius: 6px !important;
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
	height: 500px !important;
	max-height: 500px !important;
	overflow: hidden !important;
}

/* Force card content to fit */
.item-edit-numpad-redesign .v-card-text {
	flex: 1;
	overflow: hidden;
	padding: 12px !important;
}

/* Compact Layout */
.numpad-grid-redesign {
	display: flex;
	flex-direction: column;
	gap: 4px;
	flex: 1;
	max-height: 300px;
}

.numpad-row {
	display: flex;
	gap: 4px;
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