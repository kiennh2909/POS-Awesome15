<template>
	<div>
		<v-card
			:class="['selection mx-auto mt-3', isDarkTheme ? '' : 'bg-grey-lighten-5']"
			:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
			style="max-height: 80vh; height: 80vh"
		>
			<v-card-title>
				<span class="text-h6 text-primary">{{ __("Offers") }}</span>
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
					@click:row="openOfferDialog"
				>
					<template v-slot:item.offer_applied="{ item }">
						<v-checkbox-btn
							@click.stop="toggleOfferApplied(item)"
							v-model="item.offer_applied"
							:disabled="
								(item.offer == 'Give Product' &&
									!item.give_item &&
									(!item.replace_cheapest_item || !item.replace_item)) ||
								(item.offer == 'Grand Total' &&
									discount_percentage_offer_name &&
									discount_percentage_offer_name != item.name)
							"
						></v-checkbox-btn>
					</template>
				</v-data-table>

				<!-- Dialog hiển thị chi tiết offer -->
				<v-dialog v-model="offerDialog" max-width="600px" persistent>
					<v-card v-if="selectedOffer">
						<v-card-title class="text-h6 pa-4 d-flex align-center">
							<span class="text-primary">{{ selectedOffer.title || selectedOffer.name }}</span>
							<v-spacer></v-spacer>
							<v-btn
								icon="mdi-close"
								variant="text"
								density="compact"
								@click="closeOfferDialog"
							></v-btn>
						</v-card-title>
						<v-divider></v-divider>
						<v-card-text class="pa-4">
							<!-- Hiển thị loading nếu chưa có dữ liệu -->
							<div v-if="!formattedOfferContent" class="text-center py-8">
								<v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
								<div class="mt-2 text-caption">Đang tải thông tin...</div>
							</div>

							<!-- Hiển thị nội dung chi tiết -->
							<div v-else class="offer-dialog-content" v-html="formattedOfferContent"></div>

							<!-- Phần cấu hình cho Give Product -->
							<div v-if="selectedOffer.offer == 'Give Product'" class="offer-config-section mt-4">
								<v-divider class="my-3"></v-divider>
								<div class="config-title mb-3">⚙️ Cấu hình sản phẩm tặng:</div>
								<v-autocomplete
									v-model="selectedOffer.give_item"
									:items="get_give_items(selectedOffer)"
									item-title="item_code"
									variant="outlined"
									density="compact"
									color="primary"
									:label="frappe._('Chọn sản phẩm tặng')"
									:disabled="
										selectedOffer.apply_type != 'Item Group' ||
										selectedOffer.replace_item ||
										selectedOffer.replace_cheapest_item
									"
									class="mb-3"
								></v-autocomplete>
							</div>
						</v-card-text>
						<v-card-actions class="pa-4 pt-0">
							<v-btn
								color="info"
								variant="text"
								size="small"
								@click="showDebugInfo = !showDebugInfo"
							>
								{{ showDebugInfo ? 'Ẩn Debug' : 'Hiện Debug' }}
							</v-btn>
							<v-spacer></v-spacer>
							<v-btn color="primary" variant="tonal" @click="closeOfferDialog">
								{{ __("Đóng") }}
							</v-btn>
						</v-card-actions>

						<!-- Debug Information -->
						<v-expand-transition>
							<v-card-text v-if="showDebugInfo" class="pa-4 pt-0">
								<v-divider class="mb-3"></v-divider>
								<div class="debug-info">
									<h4 class="text-h6 mb-2">🔍 Debug Information</h4>
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
				<v-col cols="12">
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
		allItems: [],
		discount_percentage_offer_name: null,
		itemsPerPage: 1000,
		offerDialog: false,
		selectedOffer: null,
		showDebugInfo: false,
		items_headers: [
			{ title: __("Name"), value: "name", align: "start" },
			{ title: __("Apply On"), value: "apply_on", align: "start" },
			{ title: __("Offer"), value: "offer", align: "start" },
			{ title: __("Applied"), value: "offer_applied", align: "start" },
		],
	}),

	computed: {
		offersCount() {
			return this.pos_offers.length;
		},
		appliedOffersCount() {
			return this.pos_offers.filter((el) => !!el.offer_applied).length;
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
		updatePosOffers(offers) {
			const toRemove = [];
			this.pos_offers.forEach((pos_offer) => {
				const offer = offers.find((offer) => offer.name === pos_offer.name);
				if (!offer) {
					toRemove.push(pos_offer.row_id);
				}
			});
			this.removeOffers(toRemove);
			offers.forEach((offer) => {
				const pos_offer = this.pos_offers.find((pos_offer) => offer.name === pos_offer.name);
				if (pos_offer) {
					pos_offer.items = offer.items;
					if (pos_offer.offer === "Grand Total" && !this.discount_percentage_offer_name) {
						pos_offer.offer_applied = !!pos_offer.auto;
					}
					if (
						offer.apply_on == "Item Group" &&
						offer.apply_type == "Item Group" &&
						offer.replace_cheapest_item
					) {
						pos_offer.give_item = offer.give_item;
						pos_offer.apply_item_code = offer.apply_item_code;
					}
				} else {
					const newOffer = { ...offer };
					if (!offer.row_id) {
						newOffer.row_id = this.makeid(20);
					}
					if (offer.apply_type == "Item Code") {
						newOffer.give_item = offer.apply_item_code || "Nothing";
					}
					if (offer.offer_applied) {
						newOffer.offer_applied == !!offer.offer_applied;
					} else {
						if (
							offer.apply_type == "Item Group" &&
							offer.offer == "Give Product" &&
							!offer.replace_cheapest_item &&
							!offer.replace_item
						) {
							newOffer.offer_applied = false;
						} else if (offer.offer === "Grand Total" && this.discount_percentage_offer_name) {
							newOffer.offer_applied = false;
						} else {
							newOffer.offer_applied = !!offer.auto;
						}
					}
					if (newOffer.offer == "Give Product" && !newOffer.give_item) {
						newOffer.give_item = this.get_give_items(newOffer)[0].item_code;
					}
					this.pos_offers.push(newOffer);
					// Tạo nội dung thông báo chi tiết với format đẹp
					const offerDetails = this.formatOfferDetails(newOffer);
					this.eventBus.emit("show_message", {
						title: __("🎉 New Offer Available!"),
						message: offerDetails,
						color: "warning",
						offer: newOffer,
						timeout: 3000
					});
				}
			});
		},
		removeOffers(offers_id_list) {
			this.pos_offers = this.pos_offers.filter((offer) => !offers_id_list.includes(offer.row_id));
		},
		handelOffers() {
			const applyedOffers = this.pos_offers.filter((offer) => offer.offer_applied);
			this.eventBus.emit("update_invoice_offers", applyedOffers);
		},
		handleNewLine(str) {
			if (str) {
				return str.replace(/(?:\r\n|\r|\n)/g, "<br />");
			} else {
				return "";
			}
		},
		get_give_items(offer) {
			if (offer.apply_type == "Item Code") {
				return [offer.apply_item_code];
			} else if (offer.apply_type == "Item Group") {
				const items = this.allItems;
				let filterd_items = [];
				const filterd_items_1 = items.filter((item) => item.item_group == offer.apply_item_group);
				if (offer.less_then > 0) {
					filterd_items = filterd_items_1.filter((item) => item.rate < offer.less_then);
				} else {
					filterd_items = filterd_items_1;
				}
				return filterd_items;
			} else {
				return [];
			}
		},
		updateCounters() {
			this.eventBus.emit("update_offers_counters", {
				offersCount: this.offersCount,
				appliedOffersCount: this.appliedOffersCount,
			});
		},
		updatePosCoupuns() {
			const applyedOffers = this.pos_offers.filter(
				(offer) => offer.offer_applied && offer.coupon_based,
			);
			this.eventBus.emit("update_pos_coupons", applyedOffers);
		},

		toggleOfferApplied(item) {
			// Toggle trạng thái áp dụng offer
			item.offer_applied = !item.offer_applied;
			this.handelOffers();
			this.forceUpdateItem();
		},

		openOfferDialog(item) {
			// Mở dialog hiển thị chi tiết offer
			console.log('Opening offer dialog for item:', item);
			this.selectedOffer = { ...item };
			console.log('Selected offer:', this.selectedOffer);

			// Test formatOfferDetails
			const formattedDetails = this.formatOfferDetails(this.selectedOffer);
			console.log('Formatted details:', formattedDetails);

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
						this.handelOffers(); // Tính toán lại offers
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

	watch: {
		pos_offers: {
			deep: true,
			handler(pos_offers) {
				this.handelOffers();
				this.updateCounters();
				this.updatePosCoupuns();
			},
		},
	},

	created: function () {
		this.$nextTick(function () {
			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
			});
		});
		this.eventBus.on("update_customer", (customer) => {
			if (this.customer != customer) {
				this.offers = [];
			}
		});
		this.eventBus.on("update_pos_offers", (data) => {
			this.updatePosOffers(data);
		});
		this.eventBus.on("update_discount_percentage_offer_name", (data) => {
			this.discount_percentage_offer_name = data.value;
		});
		this.eventBus.on("set_all_items", (data) => {
			this.allItems = data;
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
.offer-dialog-content {
	line-height: 1.7;
	font-size: 14px;
}

.offer-dialog-content div {
	margin-bottom: 12px;
	padding: 10px 14px;
	border-radius: 8px;
	background: rgba(33, 150, 243, 0.05);
	border-left: 4px solid #2196f3;
	transition: all 0.2s ease;
}

.offer-dialog-content div:hover {
	background: rgba(33, 150, 243, 0.08);
	transform: translateX(2px);
}

.offer-config-section {
	padding: 16px;
	background: rgba(33, 150, 243, 0.05);
	border-radius: 8px;
	border: 1px solid rgba(33, 150, 243, 0.1);
}

.config-title {
	font-size: 15px;
	font-weight: 600;
	color: #1976d2;
	margin-bottom: 12px;
	display: flex;
	align-items: center;
}

.config-title:before {
	content: "⚙️";
	margin-right: 8px;
}

/* Dialog animation */
:deep(.v-dialog__content) {
	animation: dialogFadeIn 0.3s ease-out;
}

@keyframes dialogFadeIn {
	from {
		opacity: 0;
		transform: scale(0.95) translateY(-20px);
	}
	to {
		opacity: 1;
		transform: scale(1) translateY(0);
	}
}

/* Dark theme support */
:deep(.v-theme--dark) .offer-dialog-content div {
	background: rgba(25, 118, 210, 0.1);
	border-left-color: #90caf9;
}

:deep(.v-theme--dark) .offer-config-section {
	background: rgba(25, 118, 210, 0.1);
	border-color: rgba(144, 202, 249, 0.2);
}

:deep(.v-theme--dark) .config-title {
	color: #90caf9;
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
