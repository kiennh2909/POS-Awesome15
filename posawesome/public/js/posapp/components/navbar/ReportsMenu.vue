<template>
	<v-menu :min-width="280" :close-on-content-click="true" location="bottom end" :offset="[0, 4]">
		<template #activator="{ props }">
			<v-btn v-bind="props" color="info" variant="elevated" class="reports-menu-btn">
				<v-icon start size="16">mdi-chart-bar</v-icon>
				{{ __("Báo cáo") }}
				<v-icon end size="16" class="ml-1">mdi-menu-down</v-icon>
			</v-btn>
		</template>
		<v-card class="reports-menu-card" elevation="12">
			<div class="reports-menu-header">
				<v-icon color="info" size="20">mdi-chart-bar</v-icon>
				<span class="reports-menu-header-text">{{ __("Báo cáo & Thống kê") }}</span>
			</div>
			<v-divider></v-divider>
			<v-list density="compact" class="reports-menu-list">
				<!-- Báo cáo toàn ca -->
				<v-list-item @click="$emit('show-shift-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper shift-reports-icon">
							<v-icon color="white" size="16">mdi-store-clock</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo toàn ca") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Danh sách các báo cáo toàn ca làm việc") }}</v-list-item-subtitle>
					</div>
				</v-list-item>

				<!-- Báo cáo mặt hàng -->
				<v-list-item @click="$emit('show-item-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper item-reports-icon">
							<v-icon color="white" size="16">mdi-package-variant</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo mặt hàng") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Báo cáo mặt hàng theo danh mục") }}</v-list-item-subtitle>
					</div>
				</v-list-item>

				<!-- Báo cáo thuế -->
				<v-list-item @click="$emit('show-tax-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper tax-reports-icon">
							<v-icon color="white" size="16">mdi-receipt-text</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo thuế") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Báo cáo thuế") }}</v-list-item-subtitle>
					</div>
				</v-list-item>

				<!-- Báo cáo hàng hóa -->
				<v-list-item @click="$emit('show-inventory-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper inventory-reports-icon">
							<v-icon color="white" size="16">mdi-warehouse</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo hàng hóa") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Danh mục hàng hóa") }}</v-list-item-subtitle>
					</div>
				</v-list-item>

				<!-- Báo cáo bảng giá -->
				<v-list-item @click="$emit('show-price-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper price-reports-icon">
							<v-icon color="white" size="16">mdi-tag-multiple</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo bảng giá") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Danh mục sản phẩm có giá thay đổi trong ngày") }}</v-list-item-subtitle>
					</div>
				</v-list-item>

				<!-- Báo cáo nhân viên -->
				<v-list-item @click="$emit('show-employee-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper employee-reports-icon">
							<v-icon color="white" size="16">mdi-account-group</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo nhân viên") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Hiệu suất nhân viên trong 1 tháng") }}</v-list-item-subtitle>
					</div>
				</v-list-item>

				<!-- Báo cáo hàng khuyến mại -->
				<v-list-item @click="$emit('show-promotion-reports')" class="reports-menu-item">
					<template v-slot:prepend>
						<div class="reports-icon-wrapper promotion-reports-icon">
							<v-icon color="white" size="16">mdi-gift</v-icon>
						</div>
					</template>
					<div class="reports-content">
						<v-list-item-title class="reports-item-title">{{ __("Báo cáo hàng khuyến mại") }}</v-list-item-title>
						<v-list-item-subtitle class="reports-item-subtitle">{{ __("Danh mục hàng khuyến mại") }}</v-list-item-subtitle>
					</div>
				</v-list-item>
			</v-list>
		</v-card>
	</v-menu>
</template>

<script>
export default {
	name: "ReportsMenu",
	emits: [
		"show-shift-reports",
		"show-item-reports",
		"show-tax-reports",
		"show-inventory-reports",
		"show-price-reports",
		"show-employee-reports",
		"show-promotion-reports",
	],
};
</script>

<style scoped>
/* Reports Menu Button */
.reports-menu-btn {
	margin-left: 8px;
	margin-right: 8px;
	padding: 6px 16px;
	border-radius: 20px;
	font-weight: 600;
	text-transform: none;
	font-size: 13px;
	letter-spacing: 0.3px;
	box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	background: linear-gradient(135deg, #0288d1 0%, #4fc3f7 100%);
	min-width: 100px;
	height: 36px;
}

.reports-menu-btn:hover {
	transform: translateY(-1px) scale(1.02);
	box-shadow: 0 4px 12px rgba(2, 136, 209, 0.3);
	background: linear-gradient(135deg, #0277bd 0%, #0288d1 100%);
}

/* Reports Menu Card */
.reports-menu-card {
	border-radius: 16px;
	overflow: hidden;
	background: #ffffff;
	border: none;
	box-shadow:
		0 8px 24px rgba(0, 0, 0, 0.12),
		0 2px 6px rgba(0, 0, 0, 0.08);
	backdrop-filter: blur(8px);
	min-width: 300px;
	max-width: 320px;
	margin-top: 2px;
}

/* Reports Menu Header */
.reports-menu-header {
	padding: 12px 16px 10px;
	background: linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%);
	display: flex;
	align-items: center;
	gap: 10px;
	border-bottom: 1px solid rgba(2, 136, 209, 0.06);
}

.reports-menu-header-text {
	font-size: 14px;
	font-weight: 600;
	color: #0288d1;
	letter-spacing: 0.3px;
}

/* Reports Menu List */
.reports-menu-list {
	padding: 8px 6px 12px;
	background: #ffffff;
}

/* Reports Menu Items */
.reports-menu-item {
	border-radius: 12px;
	margin: 3px 0;
	padding: 12px 16px;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	cursor: pointer;
	position: relative;
	overflow: hidden;
	min-height: 56px;
	display: flex;
	align-items: center;
	gap: 12px;
}

.reports-menu-item::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: transparent;
	transition: all 0.3s ease;
	z-index: 0;
	border-radius: 12px;
}

.reports-menu-item:hover::before {
	background: linear-gradient(135deg, rgba(2, 136, 209, 0.05) 0%, rgba(79, 195, 247, 0.08) 100%);
}

.reports-menu-item:hover {
	transform: translateX(3px) scale(1.01);
	box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
}

/* Reports Icon Wrapper */
.reports-icon-wrapper {
	width: 32px;
	height: 32px;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s ease;
	position: relative;
	z-index: 1;
	flex-shrink: 0;
}

/* Reports Content Wrapper */
.reports-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 2px;
	position: relative;
	z-index: 1;
}

/* Reports Icon Colors */
.shift-reports-icon {
	background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
	box-shadow: 0 2px 6px rgba(25, 118, 210, 0.2);
}

.item-reports-icon {
	background: linear-gradient(135deg, #388e3c 0%, #4caf50 100%);
	box-shadow: 0 2px 6px rgba(56, 142, 60, 0.2);
}

.tax-reports-icon {
	background: linear-gradient(135deg, #f57c00 0%, #ff9800 100%);
	box-shadow: 0 2px 6px rgba(245, 124, 0, 0.2);
}

.inventory-reports-icon {
	background: linear-gradient(135deg, #7b1fa2 0%, #ba68c8 100%);
	box-shadow: 0 2px 6px rgba(123, 31, 162, 0.2);
}

.price-reports-icon {
	background: linear-gradient(135deg, #c2185b 0%, #e91e63 100%);
	box-shadow: 0 2px 6px rgba(194, 24, 91, 0.2);
}

.employee-reports-icon {
	background: linear-gradient(135deg, #00796b 0%, #009688 100%);
	box-shadow: 0 2px 6px rgba(0, 121, 107, 0.2);
}

.promotion-reports-icon {
	background: linear-gradient(135deg, #e64a19 0%, #ff5722 100%);
	box-shadow: 0 2px 6px rgba(230, 74, 25, 0.2);
}

/* Reports Text Styling */
.reports-item-title {
	font-weight: 600;
	font-size: 14px;
	color: #212121;
	line-height: 1.2;
	margin-bottom: 1px;
}

.reports-item-subtitle {
	font-size: 11px;
	color: #666666;
	line-height: 1.3;
	font-weight: 400;
}

/* Reports Hover Effects */
.reports-menu-item:hover .shift-reports-icon {
	transform: scale(1.1) rotate(5deg);
	box-shadow: 0 3px 8px rgba(25, 118, 210, 0.25);
}

.reports-menu-item:hover .item-reports-icon {
	transform: scale(1.1) rotate(-5deg);
	box-shadow: 0 3px 8px rgba(56, 142, 60, 0.25);
}

.reports-menu-item:hover .tax-reports-icon {
	transform: scale(1.1) rotate(360deg);
	box-shadow: 0 3px 8px rgba(245, 124, 0, 0.25);
}

.reports-menu-item:hover .inventory-reports-icon {
	transform: scale(1.1) rotate(5deg);
	box-shadow: 0 3px 8px rgba(123, 31, 162, 0.25);
}

.reports-menu-item:hover .price-reports-icon {
	transform: scale(1.1) rotate(-5deg);
	box-shadow: 0 3px 8px rgba(194, 24, 91, 0.25);
}

.reports-menu-item:hover .employee-reports-icon {
	transform: scale(1.1) rotate(360deg);
	box-shadow: 0 3px 8px rgba(0, 121, 107, 0.25);
}

.reports-menu-item:hover .promotion-reports-icon {
	transform: scale(1.1) rotate(5deg);
	box-shadow: 0 3px 8px rgba(230, 74, 25, 0.25);
}

/* Responsive Design */
@media (max-width: 768px) {
	.reports-menu-card {
		min-width: 280px;
		max-width: 300px;
		border-radius: 14px;
	}

	.reports-menu-item {
		padding: 10px 14px;
		min-height: 52px;
		gap: 10px;
	}

	.reports-icon-wrapper {
		width: 30px;
		height: 30px;
	}

	.reports-menu-header {
		padding: 10px 14px 8px;
	}

	.reports-menu-btn {
		margin-left: 6px;
		padding: 5px 14px;
		min-width: 95px;
		height: 34px;
		font-size: 12px;
	}
}

@media (max-width: 480px) {
	.reports-menu-card {
		min-width: 260px;
		max-width: 280px;
	}

	.reports-menu-item {
		padding: 9px 12px;
		min-height: 48px;
		gap: 9px;
	}

	.reports-menu-header {
		padding: 9px 12px 7px;
	}

	.reports-menu-btn {
		min-width: 90px;
		height: 32px;
	}
}

/* Animation for Menu Appearance */
.v-overlay__content {
	animation: reportsMenuSlideIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes reportsMenuSlideIn {
	from {
		opacity: 0;
		transform: translateY(-8px) scale(0.95);
	}

	to {
		opacity: 1;
		transform: translateY(0) scale(1);
	}
}

/* Focus States */
.reports-menu-item:focus-visible {
	outline: 1px solid #0288d1;
	outline-offset: 1px;
}

.reports-menu-btn:focus-visible {
	outline: 1px solid #0288d1;
	outline-offset: 2px;
}

/* Dark Theme Adjustments */
:deep(.dark-theme) .reports-menu-btn,
:deep(.v-theme--dark) .reports-menu-btn {
	background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
	color: #0d47a1 !important;
}

:deep(.dark-theme) .reports-menu-btn:hover,
:deep(.v-theme--dark) .reports-menu-btn:hover {
	background: linear-gradient(135deg, #29b6f6 0%, #0288d1 100%);
	box-shadow: 0 4px 12px rgba(79, 195, 247, 0.3);
}

:deep(.dark-theme) .reports-menu-card,
:deep(.v-theme--dark) .reports-menu-card {
	background: var(--surface-primary, #1e1e1e) !important;
	border: 1px solid rgba(255, 255, 255, 0.12);
	box-shadow:
		0 8px 24px rgba(0, 0, 0, 0.4),
		0 2px 6px rgba(0, 0, 0, 0.2);
}

:deep(.dark-theme) .reports-menu-header,
:deep(.v-theme--dark) .reports-menu-header {
	background: linear-gradient(135deg, #2d2d2d 0%, #1e1e1e 100%) !important;
	border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

:deep(.dark-theme) .reports-menu-header-text,
:deep(.v-theme--dark) .reports-menu-header-text {
	color: var(--primary-light, #4fc3f7) !important;
}

:deep(.dark-theme) .reports-menu-list,
:deep(.v-theme--dark) .reports-menu-list {
	background: var(--surface-primary, #1e1e1e) !important;
}

:deep(.dark-theme) .reports-item-title,
:deep(.v-theme--dark) .reports-item-title {
	color: var(--text-primary, #ffffff) !important;
}

:deep(.dark-theme) .reports-item-subtitle,
:deep(.v-theme--dark) .reports-item-subtitle {
	color: var(--text-secondary, #b0b0b0) !important;
}

:deep(.dark-theme) .reports-menu-item:hover::before,
:deep(.v-theme--dark) .reports-menu-item:hover::before {
	background: linear-gradient(
		135deg,
		rgba(79, 195, 247, 0.05) 0%,
		rgba(79, 195, 247, 0.08) 100%
	) !important;
}

/* Dark mode icon adjustments */
:deep(.dark-theme) .shift-reports-icon,
:deep(.v-theme--dark) .shift-reports-icon {
	background: linear-gradient(135deg, #90caf9 0%, #42a5f5 100%);
	box-shadow: 0 2px 6px rgba(144, 202, 249, 0.3);
}

:deep(.dark-theme) .item-reports-icon,
:deep(.v-theme--dark) .item-reports-icon {
	background: linear-gradient(135deg, #81c784 0%, #4caf50 100%);
	box-shadow: 0 2px 6px rgba(129, 199, 132, 0.3);
}

:deep(.dark-theme) .tax-reports-icon,
:deep(.v-theme--dark) .tax-reports-icon {
	background: linear-gradient(135deg, #ffb74d 0%, #ff9800 100%);
	box-shadow: 0 2px 6px rgba(255, 183, 77, 0.3);
}

:deep(.dark-theme) .inventory-reports-icon,
:deep(.v-theme--dark) .inventory-reports-icon {
	background: linear-gradient(135deg, #ce93d8 0%, #ba68c8 100%);
	box-shadow: 0 2px 6px rgba(206, 147, 216, 0.3);
}

:deep(.dark-theme) .price-reports-icon,
:deep(.v-theme--dark) .price-reports-icon {
	background: linear-gradient(135deg, #f48fb1 0%, #e91e63 100%);
	box-shadow: 0 2px 6px rgba(244, 143, 177, 0.3);
}

:deep(.dark-theme) .employee-reports-icon,
:deep(.v-theme--dark) .employee-reports-icon {
	background: linear-gradient(135deg, #80cbc4 0%, #009688 100%);
	box-shadow: 0 2px 6px rgba(128, 203, 196, 0.3);
}

:deep(.dark-theme) .promotion-reports-icon,
:deep(.v-theme--dark) .promotion-reports-icon {
	background: linear-gradient(135deg, #ff8a65 0%, #ff5722 100%);
	box-shadow: 0 2px 6px rgba(255, 138, 101, 0.3);
}
</style>