<template>
	<v-dialog 
		v-model="isVisible" 
		max-width="500px" 
		persistent
		@keydown="handleGlobalKeydown"
	>
		<v-card class="item-edit-numpad">
			<!-- Header -->
			<v-card-title class="d-flex align-center pa-4 bg-primary text-white">
				<v-icon class="mr-2">mdi-calculator-variant</v-icon>
				<div class="flex-grow-1">
					<div class="text-h6">Chỉnh Sửa Sản Phẩm</div>
					<div class="text-caption opacity-80">{{ selectedItem?.item_name || 'N/A' }}</div>
				</div>
				<v-btn 
					icon="mdi-close" 
					variant="text" 
					color="white"
					@click="closeNumPad"
					size="small"
				></v-btn>
			</v-card-title>

			<!-- Content -->
			<v-card-text class="pa-4">
				<v-row>
					<!-- Left: Item Info & Field Selection -->
					<v-col cols="5">
						<!-- Item Info -->
						<div class="item-info mb-4">
							<div class="text-subtitle-2 mb-2">Thông Tin Sản Phẩm</div>
							<div class="item-details">
								<div class="text-body-2"><strong>Mã:</strong> {{ selectedItem?.item_code }}</div>
								<div class="text-body-2"><strong>Tên:</strong> {{ selectedItem?.item_name }}</div>
								<div class="text-body-2"><strong>ĐVT:</strong> {{ selectedItem?.uom }}</div>
							</div>
						</div>

						<!-- Field Selection -->
						<div class="field-selection">
							<div class="text-subtitle-2 mb-2">Chọn Trường Chỉnh Sửa</div>
							<v-btn-toggle
								v-model="selectedField"
								mandatory
								variant="outlined"
								divided
								class="field-toggle"
							>
								<v-btn value="qty" size="small" class="field-btn">
									<v-icon class="mr-1">mdi-counter</v-icon>
									Số Lượng
								</v-btn>
								<v-btn value="rate" size="small" class="field-btn">
									<v-icon class="mr-1">mdi-currency-usd</v-icon>
									Đơn Giá
								</v-btn>
								<v-btn value="discount_percentage" size="small" class="field-btn">
									<v-icon class="mr-1">mdi-percent</v-icon>
									Chiết Khấu
								</v-btn>
							</v-btn-toggle>
						</div>

						<!-- Current Value Display -->
						<div class="current-value mt-4">
							<div class="text-subtitle-2 mb-2">Giá Trị Hiện Tại</div>
							<v-text-field
								:model-value="currentFieldValue"
								:label="fieldLabels[selectedField]"
								:prefix="fieldPrefixes[selectedField]"
								:suffix="fieldSuffixes[selectedField]"
								variant="outlined"
								readonly
								density="compact"
								class="current-value-field"
							></v-text-field>
						</div>
					</v-col>

					<!-- Right: NumPad -->
					<v-col cols="7">
						<div class="numpad-section">
							<!-- Display -->
							<div class="numpad-display mb-3">
								<v-text-field
									v-model="displayValue"
									:label="`Nhập ${fieldLabels[selectedField]}`"
									:prefix="fieldPrefixes[selectedField]"
									:suffix="fieldSuffixes[selectedField]"
									variant="outlined"
									readonly
									class="display-field"
									:class="{ 'error-field': hasError }"
								>
									<template v-slot:append-inner>
										<v-icon v-if="hasError" color="error">mdi-alert</v-icon>
									</template>
								</v-text-field>
								<div v-if="errorMessage" class="text-caption text-error mt-1">
									{{ errorMessage }}
								</div>
							</div>

							<!-- NumPad Grid -->
							<div class="numpad-grid">
								<!-- Row 1: Special buttons -->
								<v-row dense class="mb-2">
									<v-col cols="3">
										<v-btn
											color="error"
											variant="flat"
											size="large"
											block
											@click="deleteItem"
											class="numpad-btn special-btn"
										>
											<v-icon>mdi-delete</v-icon>
											<div class="btn-label">DELETE</div>
										</v-btn>
									</v-col>
									<v-col cols="3">
										<v-btn
											color="orange"
											variant="flat"
											size="large"
											block
											@click="decreaseValue"
											class="numpad-btn special-btn"
										>
											<v-icon>mdi-minus</v-icon>
											<div class="btn-label">-</div>
										</v-btn>
									</v-col>
									<v-col cols="3">
										<v-btn
											color="success"
											variant="flat"
											size="large"
											block
											@click="increaseValue"
											class="numpad-btn special-btn"
										>
											<v-icon>mdi-plus</v-icon>
											<div class="btn-label">+</div>
										</v-btn>
									</v-col>
									<v-col cols="3">
										<v-btn
											color="grey"
											variant="flat"
											size="large"
											block
											@click="backspace"
											class="numpad-btn special-btn"
										>
											<v-icon>mdi-backspace</v-icon>
											<div class="btn-label">⌫</div>
										</v-btn>
									</v-col>
								</v-row>

								<!-- Row 2: 7, 8, 9 -->
								<v-row dense class="mb-2">
									<v-col cols="4" v-for="num in [7, 8, 9]" :key="num">
										<v-btn
											color="primary"
											variant="flat"
											size="x-large"
											block
											@click="inputNumber(num)"
											class="numpad-btn number-btn"
										>
											{{ num }}
										</v-btn>
									</v-col>
								</v-row>

								<!-- Row 3: 4, 5, 6 -->
								<v-row dense class="mb-2">
									<v-col cols="4" v-for="num in [4, 5, 6]" :key="num">
										<v-btn
											color="primary"
											variant="flat"
											size="x-large"
											block
											@click="inputNumber(num)"
											class="numpad-btn number-btn"
										>
											{{ num }}
										</v-btn>
									</v-col>
								</v-row>

								<!-- Row 4: 1, 2, 3 -->
								<v-row dense class="mb-2">
									<v-col cols="4" v-for="num in [1, 2, 3]" :key="num">
										<v-btn
											color="primary"
											variant="flat"
											size="x-large"
											block
											@click="inputNumber(num)"
											class="numpad-btn number-btn"
										>
											{{ num }}
										</v-btn>
									</v-col>
								</v-row>

								<!-- Row 5: 0, ., 000, CLEAR -->
								<v-row dense class="mb-2">
									<v-col cols="3">
										<v-btn
											color="primary"
											variant="flat"
											size="x-large"
											block
											@click="inputNumber(0)"
											class="numpad-btn number-btn"
										>
											0
										</v-btn>
									</v-col>
									<v-col cols="3">
										<v-btn
											color="primary"
											variant="flat"
											size="x-large"
											block
											@click="inputDecimal"
											class="numpad-btn number-btn"
											:disabled="!allowDecimal || displayValue.includes('.')"
										>
											.
										</v-btn>
									</v-col>
									<v-col cols="3">
										<v-btn
											color="primary"
											variant="flat"
											size="x-large"
											block
											@click="inputTripleZero"
											class="numpad-btn number-btn"
										>
											000
										</v-btn>
									</v-col>
									<v-col cols="3">
										<v-btn
											color="warning"
											variant="flat"
											size="large"
											block
											@click="clear"
											class="numpad-btn special-btn"
										>
											<div class="btn-label">CLEAR</div>
										</v-btn>
									</v-col>
								</v-row>

								<!-- Row 6: ENTER -->
								<v-row dense>
									<v-col cols="12">
										<v-btn
											color="success"
											variant="flat"
											size="x-large"
											block
											@click="confirmValue"
											class="numpad-btn enter-btn"
											:disabled="hasError"
										>
											<v-icon class="mr-2">mdi-check</v-icon>
											ENTER - Xác Nhận
										</v-btn>
									</v-col>
								</v-row>
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
			selectedField: 'qty',
			displayValue: '',
			originalValue: '',
			hasError: false,
			errorMessage: '',
			
			fieldLabels: {
				qty: 'Số Lượng',
				rate: 'Đơn Giá',
				discount_percentage: 'Chiết Khấu (%)'
			},
			
			fieldPrefixes: {
				qty: '',
				rate: '$',
				discount_percentage: ''
			},
			
			fieldSuffixes: {
				qty: '',
				rate: '',
				discount_percentage: '%'
			}
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
		
		currentFieldValue() {
			if (!this.selectedItem) return '';
			
			const value = this.selectedItem[this.selectedField];
			if (this.selectedField === 'rate') {
				return this.formatCurrency(value || 0);
			} else if (this.selectedField === 'discount_percentage') {
				return `${value || 0}%`;
			} else {
				return String(value || 0);
			}
		},
		
		allowDecimal() {
			return this.selectedField !== 'discount_percentage'; // Discount can be decimal
		}
	},
	watch: {
		visible(newVal) {
			if (newVal) {
				this.initializeNumPad();
			}
		},
		
		selectedField() {
			this.initializeFieldValue();
			this.validateInput();
		},
		
		displayValue() {
			this.validateInput();
		}
	},
	methods: {
		initializeNumPad() {
			this.selectedField = this.initialField || 'qty';
			this.initializeFieldValue();
			this.hasError = false;
			this.errorMessage = '';
		},
		
		initializeFieldValue() {
			if (!this.selectedItem) return;
			
			const value = this.selectedItem[this.selectedField];
			this.originalValue = String(value || 0);
			this.displayValue = this.originalValue;
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
			if (!this.allowDecimal) return;
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
			const step = this.selectedField === 'qty' ? 1 : (this.selectedField === 'discount_percentage' ? 5 : 1000);
			this.displayValue = String(currentValue + step);
		},
		
		decreaseValue() {
			const currentValue = parseFloat(this.displayValue) || 0;
			const step = this.selectedField === 'qty' ? 1 : (this.selectedField === 'discount_percentage' ? 5 : 1000);
			const newValue = Math.max(0, currentValue - step);
			this.displayValue = String(newValue);
		},
		
		// Validation
		validateInput() {
			this.hasError = false;
			this.errorMessage = '';
			
			const value = parseFloat(this.displayValue);
			
			if (isNaN(value)) {
				this.hasError = true;
				this.errorMessage = 'Giá trị không hợp lệ';
				return;
			}
			
			if (this.selectedField === 'qty' && value <= 0) {
				this.hasError = true;
				this.errorMessage = 'Số lượng phải lớn hơn 0';
				return;
			}
			
			if (this.selectedField === 'rate' && value < 0) {
				this.hasError = true;
				this.errorMessage = 'Đơn giá không được âm';
				return;
			}
			
			if (this.selectedField === 'discount_percentage' && (value < 0 || value > 100)) {
				this.hasError = true;
				this.errorMessage = 'Chiết khấu phải từ 0% đến 100%';
				return;
			}
		},
		
		// Actions
		confirmValue() {
			if (this.hasError) return;
			
			const value = parseFloat(this.displayValue);
			this.$emit('update-field', {
				field: this.selectedField,
				value: value,
				item: this.selectedItem
			});
			
			this.closeNumPad();
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
				case 'Tab':
					event.preventDefault();
					this.switchField();
					break;
			}
		},
		
		switchField() {
			const fields = ['qty', 'rate', 'discount_percentage'];
			const currentIndex = fields.indexOf(this.selectedField);
			const nextIndex = (currentIndex + 1) % fields.length;
			this.selectedField = fields[nextIndex];
		},
		
		// Utility Methods
		formatCurrency(value) {
			return new Intl.NumberFormat('vi-VN').format(value || 0);
		}
	}
};
</script>

<style scoped>
.item-edit-numpad {
	border-radius: 12px;
}

.item-info {
	background: #f5f5f5;
	border-radius: 8px;
	padding: 12px;
}

.item-details {
	font-size: 0.9rem;
	line-height: 1.4;
}

.field-selection .field-toggle {
	width: 100%;
}

.field-btn {
	font-size: 0.75rem !important;
	padding: 8px 4px !important;
}

.current-value-field {
	background: #e3f2fd;
}

.numpad-display {
	position: relative;
}

.display-field {
	font-size: 1.2rem;
	font-weight: bold;
}

.error-field {
	background: #ffebee !important;
}

.numpad-grid {
	max-width: 100%;
}

.numpad-btn {
	height: 60px !important;
	font-size: 1.1rem !important;
	font-weight: bold !important;
	border-radius: 8px !important;
	margin: 2px !important;
}

.number-btn {
	font-size: 1.4rem !important;
}

.special-btn {
	font-size: 0.9rem !important;
}

.btn-label {
	font-size: 0.7rem;
	line-height: 1;
	margin-top: 2px;
}

.enter-btn {
	height: 50px !important;
	font-size: 1.1rem !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
	.item-edit-numpad {
		margin: 8px;
	}
	
	.numpad-btn {
		height: 50px !important;
		font-size: 1rem !important;
	}
}
</style>