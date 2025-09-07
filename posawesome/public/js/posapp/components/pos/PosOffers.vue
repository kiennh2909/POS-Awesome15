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
					:single-expand="singleExpand"
					v-model:expanded="expanded"
					show-expand
					item-key="row_id"
					class="elevation-1"
					:items-per-page="itemsPerPage"
					hide-default-footer
					@click:row="toggleExpanded"
				>
					<template v-slot:item.offer_applied="{ item }">
						<v-checkbox-btn
							@click="toggleOfferApplied(item)"
							v-model="item.offer_applied"
							:disabled="
								(item.offer == 'Give Product' &&
									!item.give_item &&
									(!offer.replace_cheapest_item || !offer.replace_item)) ||
								(item.offer == 'Grand Total' &&
									discount_percentage_offer_name &&
									discount_percentage_offer_name != item.name)
							"
						></v-checkbox-btn>
					</template>
					<template v-slot:expanded-item="{ headers, item }">
						<td :colspan="headers.length">
							<div class="offer-expanded-content">
								<!-- Thông tin chi tiết của offer -->
								<div class="offer-details-section" v-html="formatOfferDetails(item)"></div>

								<!-- Phần cấu hình cho Give Product -->
								<div v-if="item.offer == 'Give Product'" class="offer-config-section">
									<v-divider class="my-3"></v-divider>
									<div class="config-title">Cấu hình sản phẩm tặng:</div>
									<v-autocomplete
										v-model="item.give_item"
										:items="get_give_items(item)"
										item-title="item_code"
										variant="outlined"
										density="compact"
										color="primary"
										:label="frappe._('Chọn sản phẩm tặng')"
										:disabled="
											item.apply_type != 'Item Group' ||
											item.replace_item ||
											item.replace_cheapest_item
										"
										class="mt-2"
									></v-autocomplete>
								</div>
							</div>
						</td>
					</template>
				</v-data-table>
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
		expanded: [],
		singleExpand: true,
		items_headers: [
			{ title: __("Name"), value: "name", align: "start" },
			{ title: __("Apply On"), value: "apply_on", align: "start" },
			{ title: __("Offer"), value: "offer", align: "start" },
			{ title: __("Applied"), value: "offer_applied", align: "start" },
			{ title: "", value: "data-table-expand", align: "end" },
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

		toggleExpanded(item) {
			// Toggle expanded state
			const index = this.expanded.indexOf(item.row_id);
			if (index > -1) {
				this.expanded.splice(index, 1);
			} else {
				if (this.singleExpand) {
					this.expanded = [item.row_id];
				} else {
					this.expanded.push(item.row_id);
				}
			}
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

/* Expand icon styling */
:deep(.v-data-table__td .v-btn--icon) {
	margin: 0;
	padding: 0;
	min-width: 24px;
	width: 24px;
	height: 24px;
}

:deep(.v-data-table__td .v-icon) {
	font-size: 18px;
}

/* Expanded content styling */
.offer-expanded-content {
	padding: 20px;
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
	border-radius: 12px;
	margin: 12px 0;
	border: 2px solid rgba(33, 150, 243, 0.1);
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
	animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
	from {
		opacity: 0;
		transform: translateY(-10px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.offer-details-section {
	margin-bottom: 20px;
	line-height: 1.7;
}

.offer-details-section div {
	margin-bottom: 10px;
	padding: 8px 12px;
	border-radius: 6px;
	background: rgba(255, 255, 255, 0.8);
	border-left: 3px solid #2196f3;
	transition: all 0.2s ease;
}

.offer-details-section div:hover {
	background: rgba(33, 150, 243, 0.05);
	transform: translateX(2px);
}

.offer-config-section {
	margin-top: 20px;
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

.offer-expanded-content .v-divider {
	margin: 20px 0;
	border-color: rgba(33, 150, 243, 0.2);
	border-width: 1px;
}

/* Dark theme support */
:deep(.v-theme--dark) .offer-expanded-content {
	background: linear-gradient(135deg, rgba(33, 33, 33, 0.98) 0%, rgba(45, 45, 45, 0.98) 100%);
	border-color: rgba(144, 202, 249, 0.2);
}

:deep(.v-theme--dark) .offer-details-section div {
	background: rgba(66, 66, 66, 0.8);
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
	.offer-expanded-content {
		padding: 16px;
		margin: 8px 0;
		border-radius: 8px;
	}

	.offer-details-section {
		margin-bottom: 16px;
	}

	.offer-details-section div {
		padding: 6px 8px;
		margin-bottom: 8px;
		font-size: 14px;
	}

	.config-title {
		font-size: 14px;
		margin-bottom: 10px;
	}

	.offer-config-section {
		padding: 12px;
		margin-top: 16px;
	}
}

/* Row hover effect */
:deep(.v-data-table__tr:hover) {
	background-color: rgba(33, 150, 243, 0.04) !important;
	transition: background-color 0.2s ease;
}

:deep(.v-theme--dark .v-data-table__tr:hover) {
	background-color: rgba(144, 202, 249, 0.08) !important;
}

/* Expand transition */
:deep(.v-data-table__expanded-content) {
	transition: all 0.3s ease;
}
</style>
