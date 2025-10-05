<template>
	<div>
		<v-card
			:class="['selection mx-auto mt-3', isDarkTheme ? '' : 'bg-grey-lighten-5']"
			:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
			style="max-height: 80vh; height: 80vh"
		>
			<v-card-title>
				<span class="text-h6 text-primary">{{ __("Danh sách chương trình khuyến mại") }}</span>
			</v-card-title>
			<div
				class="my-0 py-0 overflow-y-auto"
				style="max-height: 75vh"
				@mouseover="style = 'cursor: pointer'"
			>
				<v-data-table
					:headers="items_headers"
					:items="pos_offers"
					item-key="row_id"
					class="elevation-1"
					:items-per-page="itemsPerPage"
					hide-default-footer
				>
					<template v-slot:item.name="{ item }">
						<div class="d-flex align-center">
							<span
								class="offer-name-link mr-2"
								@click.stop="openOfferDialog(item)"
								title="Click để xem chi tiết"
							>
								{{ item.name }}
							</span>
							<v-btn
								icon="mdi-information-outline"
								size="small"
								variant="text"
								color="info"
								@click.stop="openOfferDialog(item)"
								title="Xem chi tiết"
							></v-btn>
						</div>
					</template>
					<template v-slot:item.actions="{ item }">
						<v-btn
							icon="mdi-eye"
							size="small"
							variant="text"
							color="primary"
							@click.stop="openOfferDialog(item)"
							title="Xem chi tiết offer"
						>
							<v-icon size="small">mdi-eye</v-icon>
						</v-btn>
					</template>
				</v-data-table>

				<!-- Dialog hiển thị chi tiết offer -->
				<v-dialog v-model="offerDialog" max-width="650px" persistent>
					<v-card v-if="selectedOffer" class="offer-detail-dialog">
						<v-card-title class="offer-dialog-header pa-4 d-flex align-center">
							<div class="d-flex align-center">
								<v-icon color="primary" class="mr-2">mdi-gift</v-icon>
								<span class="offer-dialog-title">{{ selectedOffer.title || selectedOffer.name }}</span>
							</div>
							<v-spacer></v-spacer>
							<v-btn
								icon="mdi-close"
								variant="text"
								density="compact"
								color="grey"
								@click="closeOfferDialog"
								title="Đóng"
							></v-btn>
						</v-card-title>
						<v-divider></v-divider>
						<v-card-text class="pa-0">
							<div class="offer-dialog-body">
								<!-- Hiển thị loading nếu chưa có dữ liệu -->
								<div v-if="!formattedOfferContent" class="text-center py-8">
									<v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
									<div class="mt-2 text-caption text-grey-600">Đang tải thông tin...</div>
								</div>

								<!-- Hiển thị nội dung chi tiết -->
								<div v-else class="offer-dialog-content" v-html="formattedOfferContent"></div>

							</div>
						</v-card-text>
						<v-card-actions class="offer-dialog-footer pa-4">
							<v-btn
								color="info"
								variant="text"
								size="small"
								@click="showDebugInfo = !showDebugInfo"
								class="debug-toggle-btn"
							>
								<v-icon size="small" class="mr-1">mdi-bug</v-icon>
								{{ showDebugInfo ? 'Ẩn Debug' : 'Hiện Debug' }}
							</v-btn>
							<v-spacer></v-spacer>
							<v-btn
								color="primary"
								variant="tonal"
								@click="closeOfferDialog"
								class="close-btn"
							>
								<v-icon size="small" class="mr-1">mdi-check</v-icon>
								{{ __("Đóng") }}
							</v-btn>
						</v-card-actions>

						<!-- Debug Information -->
						<v-expand-transition>
							<v-card-text v-if="showDebugInfo" class="pa-4 pt-0">
								<v-divider class="mb-3"></v-divider>
								<div class="debug-info">
									<h4 class="text-h6 mb-2 d-flex align-center">
										<v-icon color="orange" size="small" class="mr-2">mdi-bug</v-icon>
										Debug Information
									</h4>
									<pre class="debug-json">{{ JSON.stringify(selectedOffer, null, 2) }}</pre>
								</div>
							</v-card-text>
						</v-expand-transition>
					</v-card>
				</v-dialog>
			</div>
		</v-card>

		<v-card flat style="max-height: 11vh; height: 11vh" class="cards mb-0 mt-3 py-0">
			<v-row align="start" no-gutters>
				<v-col cols="6">
					<v-btn
						block
						class="pa-1"
						size="large"
						color="success"
						theme="dark"
						@click="check_offers"
						>{{ __("Kiểm tra Offer") }}</v-btn
					>
				</v-col>
				<v-col cols="6">
					<v-btn
						block
						class="pa-1"
						size="large"
						color="warning"
						theme="dark"
						@click="back_to_invoice"
						>{{ __("Back") }}</v-btn
					>
				</v-col>
			</v-row>
		</v-card>
	</div>
</template>

<script>
import format from "../../format";
export default {
	mixins: [format],
	data: () => ({
		loading: false,
		pos_profile: "",
		pos_offers: [],
		itemsPerPage: 1000,
		offerDialog: false,
		selectedOffer: null,
		showDebugInfo: false,
		items_headers: [
			{ title: __("Name"), value: "name", align: "start" },
			{ title: __("Apply On"), value: "apply_on", align: "start" },
			{ title: __("Offer"), value: "offer", align: "start" },
			{ title: __("Actions"), value: "actions", align: "center", sortable: false },
		],
	}),

	computed: {
		offersCount() {
			return this.pos_offers.length;
		},
		appliedOffersCount() {
			// Không còn sử dụng offer_applied state trong dialog này
			return 0;
		},
		isDarkTheme() {
			return this.$theme?.current === "dark";
		},
		formattedOfferContent() {
			if (!this.selectedOffer) return '';

			try {
				const content = this.formatOfferDetails(this.selectedOffer);
				console.log('Computed formatted content:', content);
				return content || this.getFallbackContent();
			} catch (error) {
				console.error('Error formatting offer details:', error);
				return this.getFallbackContent();
			}
		},
	},

	methods: {
		back_to_invoice() {
			this.eventBus.emit("show_offers", "false");
		},

		async check_offers() {
			console.log("🔍 [POS_OFFERS] Check offers button clicked - calculating applicable offers");

			try {
				// Emit event để Invoice component tính toán offers với giỏ hàng hiện tại
				this.eventBus.emit("check_applicable_offers");

				this.eventBus.emit("show_message", {
					title: __("Đang kiểm tra offers..."),
					message: __("Đang tính toán các chương trình khuyến mại phù hợp với giỏ hàng hiện tại."),
					color: "info",
					timeout: 2000
				});

				console.log("🔍 [POS_OFFERS] Check offers request sent");
			} catch (error) {
				console.error("🔍 [POS_OFFERS] Error checking offers:", error);
				this.eventBus.emit("show_message", {
					title: __("Lỗi kiểm tra offers"),
					message: error.message || __("Không thể kiểm tra chương trình khuyến mại."),
					color: "error"
				});
			}
		},

		async loadOffers() {
			console.log("📋 [POS_OFFERS] Loading all offers for POS Profile:", this.pos_profile?.name);

			if (!this.pos_profile?.name) {
				console.warn("📋 [POS_OFFERS] No POS Profile available");
				return;
			}

			try {
				this.loading = true;

				const response = await frappe.call({
					method: "posawesome.posawesome.api.offers.get_offers",
					args: {
						profile: this.pos_profile.name
					}
				});

				if (response.message) {
					// Reset tất cả offers về không áp dụng
					this.pos_offers = response.message.map(offer => ({
						...offer,
						offer_applied: false
					}));

					console.log("📋 [POS_OFFERS] Loaded", this.pos_offers.length, "offers");
					this.updateCounters();
				}

			} catch (error) {
				console.error("📋 [POS_OFFERS] Error loading offers:", error);
				this.eventBus.emit("show_message", {
					title: __("Lỗi tải offers"),
					message: __("Không thể tải danh sách chương trình khuyến mại."),
					color: "error"
				});
			} finally {
				this.loading = false;
			}
		},
		forceUpdateItem() {
			let list_offers = [];
			list_offers = [...this.pos_offers];
			this.pos_offers = list_offers;
		},
		makeid(length) {
			let result = "";
			const characters = "abcdefghijklmnopqrstuvwxyz0123456789";
			const charactersLength = characters.length;
			for (var i = 0; i < length; i++) {
				result += characters.charAt(Math.floor(Math.random() * charactersLength));
			}
			return result;
		},
		handleNewLine(str) {
			if (str) {
				return str.replace(/(?:\r\n|\r|\n)/g, "<br />");
			} else {
				return "";
			}
		},
		updateCounters() {
			this.eventBus.emit("update_offers_counters", {
				offersCount: this.offersCount,
				appliedOffersCount: this.appliedOffersCount,
			});
			// Không còn gọi updatePosCoupuns() vì không áp dụng offers trong dialog
		},


		openOfferDialog(item) {
			// Mở dialog hiển thị chi tiết offer
			console.log('Opening offer dialog for item:', item);
			console.log('Item keys:', Object.keys(item));
			console.log('Item values:', Object.values(item));

			// Kiểm tra xem item có phải là offer thực tế không
			if (!item || typeof item !== 'object') {
				console.error('Invalid item passed to openOfferDialog:', item);
				return;
			}

			// Copy object an toàn hơn
			try {
				this.selectedOffer = JSON.parse(JSON.stringify(item));
				console.log('Selected offer after copy:', this.selectedOffer);
				console.log('Selected offer type:', typeof this.selectedOffer);
				console.log('Selected offer keys:', Object.keys(this.selectedOffer));
			} catch (error) {
				console.error('Error copying offer object:', error);
				this.selectedOffer = item; // Fallback
			}

			// Test formatOfferDetails
			try {
				const formattedDetails = this.formatOfferDetails(this.selectedOffer);
				console.log('Formatted details:', formattedDetails);
			} catch (error) {
				console.error('Error formatting offer details:', error);
			}

			this.offerDialog = true;
		},

		closeOfferDialog() {
			// Cập nhật lại offer trong danh sách chính nếu có thay đổi
			if (this.selectedOffer) {
				const originalOffer = this.pos_offers.find(offer => offer.row_id === this.selectedOffer.row_id);
				if (originalOffer) {
					// Cập nhật give_item nếu có thay đổi
					if (originalOffer.give_item !== this.selectedOffer.give_item) {
						originalOffer.give_item = this.selectedOffer.give_item;
						// Không còn tự động áp dụng offers trong dialog
						console.log("📝 [POS_OFFERS] Updated give_item for offer:", originalOffer.name);
					}
				}
			}

			// Đóng dialog
			this.offerDialog = false;
			this.selectedOffer = null;
		},
		formatOfferDetails(offer) {
			let details = `<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;">`;

			// Tên chương trình - màu đen, font to
			details += `<div style="font-size: 18px; font-weight: bold; color: #000000; margin-bottom: 8px;">`;
			details += `📋 ${offer.title || offer.name}`;
			details += `</div>`;

			// Thời gian khuyến mại - màu đen
			if (offer.valid_from || offer.valid_upto) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📅 Thời gian: `;
				if (offer.valid_from) {
					details += `${this.formatDate(offer.valid_from)}`;
				}
				if (offer.valid_upto) {
					details += ` - ${this.formatDate(offer.valid_upto)}`;
				}
				details += `</div>`;
			}

			// Hiển thị thông tin chi tiết theo từng loại offer
			details += this.getOfferSpecificDetails(offer);

			details += `</div>`;
			return details;
		},

		getOfferSpecificDetails(offer) {
			let details = '';

			switch (offer.offer) {
				case 'Give Product':
					details += this.formatGiveProductDetails(offer);
					break;
				case 'Item Price':
					details += this.formatItemPriceDetails(offer);
					break;
				case 'Grand Total':
					details += this.formatGrandTotalDetails(offer);
					break;
				case 'Loyalty Point':
					details += this.formatLoyaltyPointDetails(offer);
					break;
				default:
					details += this.formatDefaultOfferDetails(offer);
			}

			return details;
		},

		formatGiveProductDetails(offer) {
			let details = '';

			// Loại khuyến mại
			details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
			details += `🏷️ Loại: Tặng sản phẩm`;
			details += `</div>`;

			// Thông tin sản phẩm được tặng
			if (offer.apply_item_code) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `🎁 Sản phẩm tặng: <strong>${offer.apply_item_code}</strong>`;
				details += `</div>`;
			} else if (offer.apply_item_group) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `🎁 Nhóm sản phẩm tặng: <strong>${offer.apply_item_group}</strong>`;
				details += `</div>`;
			}

			// Số lượng tặng
			if (offer.given_qty) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📦 Số lượng: <strong>${offer.given_qty}</strong>`;
				details += `</div>`;
			}

			// Điều kiện áp dụng
			if (offer.min_qty || offer.min_amt) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `⚡ Điều kiện: `;
				if (offer.min_qty) {
					details += `Mua tối thiểu <strong>${offer.min_qty}</strong> sản phẩm`;
				}
				if (offer.min_amt) {
					if (offer.min_qty) details += ` hoặc `;
					details += `Tổng tiền tối thiểu <strong>${this.formatCurrency(offer.min_amt)}</strong>`;
				}
				details += `</div>`;
			}

			// Mô tả
			if (offer.description) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📝 ${offer.description}`;
				details += `</div>`;
			}

			return details;
		},

		formatItemPriceDetails(offer) {
			let details = '';

			// Loại khuyến mại
			details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
			details += `🏷️ Loại: Giảm giá sản phẩm`;
			details += `</div>`;

			// Sản phẩm được giảm giá
			if (offer.item) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `🛒 Sản phẩm: <strong>${offer.item}</strong>`;
				details += `</div>`;
			} else if (offer.item_group) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `🛒 Nhóm sản phẩm: <strong>${offer.item_group}</strong>`;
				details += `</div>`;
			}

			// Chi tiết giảm giá
			const discountDetails = this.getDiscountDetails(offer);
			if (discountDetails) {
				details += `<div style="font-size: 14px; color: #ff6f00; font-weight: bold; margin-bottom: 6px;">`;
				details += `💰 ${discountDetails}`;
				details += `</div>`;
			}

			// Điều kiện áp dụng
			if (offer.min_qty || offer.min_amt) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `⚡ Điều kiện: `;
				if (offer.min_qty) {
					details += `Mua tối thiểu <strong>${offer.min_qty}</strong> sản phẩm`;
				}
				if (offer.min_amt) {
					if (offer.min_qty) details += ` hoặc `;
					details += `Tổng tiền tối thiểu <strong>${this.formatCurrency(offer.min_amt)}</strong>`;
				}
				details += `</div>`;
			}

			// Mô tả
			if (offer.description) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📝 ${offer.description}`;
				details += `</div>`;
			}

			return details;
		},

		formatGrandTotalDetails(offer) {
			let details = '';

			// Loại khuyến mại
			details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
			details += `🏷️ Loại: Giảm giá hóa đơn`;
			details += `</div>`;

			// Chi tiết giảm giá
			const discountDetails = this.getDiscountDetails(offer);
			if (discountDetails) {
				details += `<div style="font-size: 14px; color: #ff6f00; font-weight: bold; margin-bottom: 6px;">`;
				details += `💰 ${discountDetails}`;
				details += `</div>`;
			}

			// Điều kiện áp dụng
			if (offer.min_qty || offer.min_amt) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `⚡ Điều kiện: `;
				if (offer.min_qty) {
					details += `Tổng số lượng tối thiểu <strong>${offer.min_qty}</strong> sản phẩm`;
				}
				if (offer.min_amt) {
					if (offer.min_qty) details += ` hoặc `;
					details += `Tổng tiền tối thiểu <strong>${this.formatCurrency(offer.min_amt)}</strong>`;
				}
				details += `</div>`;
			}

			// Mô tả
			if (offer.description) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📝 ${offer.description}`;
				details += `</div>`;
			}

			return details;
		},

		formatLoyaltyPointDetails(offer) {
			let details = '';

			// Loại khuyến mại
			details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
			details += `🏷️ Loại: Tích điểm thưởng`;
			details += `</div>`;

			// Số điểm thưởng
			if (offer.loyalty_points) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `⭐ Số điểm: <strong>${offer.loyalty_points}</strong>`;
				details += `</div>`;
			}

			// Điều kiện áp dụng
			if (offer.min_qty || offer.min_amt) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `⚡ Điều kiện: `;
				if (offer.min_qty) {
					details += `Mua tối thiểu <strong>${offer.min_qty}</strong> sản phẩm`;
				}
				if (offer.min_amt) {
					if (offer.min_qty) details += ` hoặc `;
					details += `Tổng tiền tối thiểu <strong>${this.formatCurrency(offer.min_amt)}</strong>`;
				}
				details += `</div>`;
			}

			// Mô tả
			if (offer.description) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📝 ${offer.description}`;
				details += `</div>`;
			}

			return details;
		},

		formatDefaultOfferDetails(offer) {
			let details = '';

			// Loại khuyến mại
			details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
			details += `🏷️ Loại: ${this.getOfferTypeText(offer.offer)}`;
			details += `</div>`;

			// Mô tả
			if (offer.description) {
				details += `<div style="font-size: 14px; color: #000000; margin-bottom: 6px;">`;
				details += `📝 ${offer.description}`;
				details += `</div>`;
			}

			return details;
		},
		formatDate(dateStr) {
			if (!dateStr) return '';
			try {
				const date = new Date(dateStr);
				return date.toLocaleDateString('vi-VN', {
					day: '2-digit',
					month: '2-digit',
					year: 'numeric'
				});
			} catch (e) {
				return dateStr;
			}
		},
		getOfferTypeText(offerType) {
			const types = {
				'Item Price': 'Giảm giá sản phẩm',
				'Give Product': 'Tặng sản phẩm',
				'Grand Total': 'Giảm giá hóa đơn',
				'Loyalty Point': 'Tích điểm thưởng'
			};
			return types[offerType] || offerType;
		},
		getDiscountDetails(offer) {
			if (!offer.discount_type) return null;

			switch (offer.discount_type) {
				case 'Rate':
					return `Giá: ${this.formatCurrency(offer.rate)}`;
				case 'Discount Percentage':
					return `Giảm: ${offer.discount_percentage}%`;
				case 'Discount Amount':
					return `Giảm: ${this.formatCurrency(offer.discount_amount)}`;
				default:
					return null;
			}
		},

		getFallbackContent() {
			if (!this.selectedOffer) return '';

			let content = `<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;">`;

			// Tên offer
			content += `<div style="font-size: 18px; font-weight: bold; color: #000000; margin-bottom: 12px;">`;
			content += `📋 ${this.selectedOffer.title || this.selectedOffer.name || 'Chương trình khuyến mại'}`;
			content += `</div>`;

			// Thông tin cơ bản
			content += `<div style="font-size: 14px; color: #000000; margin-bottom: 8px;">`;
			content += `🏷️ Loại: ${this.getOfferTypeText(this.selectedOffer.offer)}`;
			content += `</div>`;

			// Mô tả nếu có
			if (this.selectedOffer.description) {
				content += `<div style="font-size: 14px; color: #000000; margin-bottom: 8px;">`;
				content += `📝 ${this.selectedOffer.description}`;
				content += `</div>`;
			}

			// Thông tin debug
			content += `<div style="font-size: 12px; color: #666; margin-top: 16px; padding: 8px; background: #f5f5f5; border-radius: 4px;">`;
			content += `<strong>Debug Info:</strong><br>`;
			content += `Offer Type: ${this.selectedOffer.offer}<br>`;
			content += `Name: ${this.selectedOffer.name}<br>`;
			content += `Title: ${this.selectedOffer.title}<br>`;
			content += `</div>`;

			content += `</div>`;
			return content;
		},
	},

	// Removed watch for pos_offers - no longer auto-applying offers in dialog

	created: function () {
		this.$nextTick(function () {
			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
				// Tự động load offers khi POS Profile được đăng ký
				this.loadOffers();
			});
		});
	},
};
</script>

<style scoped>
/* Data table styling */
.elevation-1 {
	border-radius: 8px;
	overflow: hidden;
}

/* Row hover effect - pointer cursor để chỉ ra có thể click */
:deep(.v-data-table__tr) {
	cursor: pointer;
	transition: all 0.2s ease;
}

:deep(.v-data-table__tr:hover) {
	background-color: rgba(33, 150, 243, 0.08) !important;
	transform: translateY(-1px);
	box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
}

:deep(.v-theme--dark .v-data-table__tr:hover) {
	background-color: rgba(144, 202, 249, 0.12) !important;
	box-shadow: 0 2px 8px rgba(144, 202, 249, 0.2);
}

/* Dialog styling */
.offer-detail-dialog {
	border-radius: 16px;
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15) !important;
	overflow: hidden;
}

.offer-dialog-header {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.offer-dialog-title {
	font-size: 20px;
	font-weight: 600;
	color: #2c3e50;
	line-height: 1.3;
}

.offer-dialog-body {
	padding: 24px;
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
	min-height: 300px;
}

.offer-dialog-content {
	line-height: 1.8;
	font-size: 15px;
	font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.offer-dialog-content div {
	margin-bottom: 16px;
	padding: 14px 18px;
	border-radius: 12px;
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.9) 100%);
	border: 1px solid rgba(33, 150, 243, 0.1);
	border-left: 5px solid #2196f3;
	transition: all 0.3s ease;
	box-shadow: 0 2px 8px rgba(33, 150, 243, 0.08);
	position: relative;
}

.offer-dialog-content div:hover {
	background: linear-gradient(135deg, rgba(33, 150, 243, 0.08) 0%, rgba(25, 118, 210, 0.08) 100%);
	transform: translateX(4px) translateY(-2px);
	box-shadow: 0 6px 20px rgba(33, 150, 243, 0.15);
}

.offer-dialog-content div:before {
	content: '';
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
	border-radius: 12px;
	pointer-events: none;
}

.offer-config-section {
	margin-top: 24px;
}

.config-section-wrapper {
	padding: 20px;
	background: linear-gradient(135deg, rgba(33, 150, 243, 0.05) 0%, rgba(25, 118, 210, 0.05) 100%);
	border-radius: 12px;
	border: 2px solid rgba(33, 150, 243, 0.1);
	box-shadow: 0 4px 16px rgba(33, 150, 243, 0.08);
}

.config-title {
	font-size: 16px;
	font-weight: 600;
	color: #1976d2;
	margin-bottom: 16px;
	display: flex;
	align-items: center;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.config-autocomplete {
	background: rgba(255, 255, 255, 0.8);
	border-radius: 8px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.offer-dialog-footer {
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.debug-toggle-btn {
	border-radius: 20px;
	font-weight: 500;
	text-transform: none;
}

.close-btn {
	border-radius: 20px;
	font-weight: 500;
	text-transform: none;
	box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
}

/* Dialog animation */
:deep(.v-dialog__content) {
	animation: dialogFadeIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes dialogFadeIn {
	from {
		opacity: 0;
		transform: scale(0.9) translateY(-30px) rotate(-2deg);
	}
	to {
		opacity: 1;
		transform: scale(1) translateY(0) rotate(0deg);
	}
}

/* Enhanced hover effects */
:deep(.v-btn:hover) {
	transform: translateY(-1px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	transition: all 0.2s ease;
}

/* Dark theme support */
:deep(.v-theme--dark) .offer-detail-dialog {
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3) !important;
}

:deep(.v-theme--dark) .offer-dialog-header {
	background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
	border-bottom-color: rgba(255, 255, 255, 0.1);
}

:deep(.v-theme--dark) .offer-dialog-title {
	color: #ffffff;
}

:deep(.v-theme--dark) .offer-dialog-body {
	background: linear-gradient(135deg, rgba(33, 33, 33, 0.98) 0%, rgba(45, 45, 45, 0.98) 100%);
}

:deep(.v-theme--dark) .offer-dialog-content div {
	background: linear-gradient(135deg, rgba(66, 66, 66, 0.9) 0%, rgba(55, 55, 55, 0.9) 100%);
	border-color: rgba(144, 202, 249, 0.2);
	border-left-color: #90caf9;
	box-shadow: 0 2px 8px rgba(144, 202, 249, 0.1);
}

:deep(.v-theme--dark) .offer-dialog-content div:hover {
	background: linear-gradient(135deg, rgba(144, 202, 249, 0.1) 0%, rgba(25, 118, 210, 0.1) 100%);
	box-shadow: 0 6px 20px rgba(144, 202, 249, 0.2);
}

:deep(.v-theme--dark) .config-section-wrapper {
	background: linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(33, 150, 243, 0.1) 100%);
	border-color: rgba(144, 202, 249, 0.2);
	box-shadow: 0 4px 16px rgba(144, 202, 249, 0.1);
}

:deep(.v-theme--dark) .config-title {
	color: #90caf9;
}

:deep(.v-theme--dark) .config-autocomplete {
	background: rgba(66, 66, 66, 0.8);
}

:deep(.v-theme--dark) .offer-dialog-footer {
	background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
	border-top-color: rgba(255, 255, 255, 0.1);
}

:deep(.v-theme--dark) .debug-toggle-btn {
	background: rgba(255, 152, 0, 0.1);
	color: #ffb74d;
}

:deep(.v-theme--dark) .close-btn {
	background: rgba(33, 150, 243, 0.1);
	color: #90caf9;
	box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
}

/* Responsive cho mobile */
@media (max-width: 600px) {
	:deep(.v-dialog) {
		margin: 8px;
		max-width: calc(100vw - 16px) !important;
	}

	.offer-dialog-content {
		font-size: 13px;
	}

	.offer-dialog-content div {
		padding: 8px 10px;
		margin-bottom: 10px;
		font-size: 13px;
	}

	.config-title {
		font-size: 14px;
		margin-bottom: 10px;
	}

	.offer-config-section {
		padding: 12px;
	}
}

/* Prevent checkbox click from triggering row click */
:deep(.v-checkbox-btn) {
	pointer-events: auto;
}

/* Offer name link styling */
.offer-name-link {
	cursor: pointer;
	color: #1976d2;
	text-decoration: none;
	transition: all 0.2s ease;
	font-weight: 500;
}

.offer-name-link:hover {
	color: #0d47a1;
	text-decoration: underline;
	background-color: rgba(25, 118, 210, 0.1);
	padding: 2px 4px;
	border-radius: 4px;
}

:deep(.v-theme--dark) .offer-name-link {
	color: #90caf9;
}

:deep(.v-theme--dark) .offer-name-link:hover {
	color: #42a5f5;
	background-color: rgba(144, 202, 249, 0.1);
}

/* Debug information styling */
.debug-info {
	background: rgba(255, 235, 59, 0.1);
	border: 1px solid rgba(255, 235, 59, 0.3);
	border-radius: 8px;
	padding: 12px;
	margin-top: 8px;
}

.debug-info h4 {
	color: #f57c00;
	margin-bottom: 8px;
}

.debug-json {
	background: #f5f5f5;
	border: 1px solid #ddd;
	border-radius: 4px;
	padding: 8px;
	font-size: 11px;
	line-height: 1.4;
	max-height: 200px;
	overflow-y: auto;
	white-space: pre-wrap;
	word-break: break-all;
}

:deep(.v-theme--dark) .debug-json {
	background: #2a2a2a;
	border-color: #555;
	color: #e0e0e0;
}
</style>
