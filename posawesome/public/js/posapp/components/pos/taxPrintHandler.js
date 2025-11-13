/**
 * Chế độ gỡ lỗi. Đặt thành true khi phát triển để xem log chi tiết.
 */
const DEBUG_MODE = true;

/**
 * Ghi log chi tiết nếu DEBUG_MODE được bật.
 * @param {string} message - Tin nhắn chính.
 * @param {object} [details] - Đối tượng chứa thông tin chi tiết.
 */
function debugLog(message, details) {
	if (DEBUG_MODE) {
		if (details !== undefined) {
			console.log(`[TaxPrintHandler DEBUG] ${message}`, details);
		} else {
			console.log(`[TaxPrintHandler DEBUG] ${message}`);
		}
	}
}

/**
 * Xử lý toàn bộ quy trình in hóa đơn thuế: xác thực, chuẩn bị dữ liệu,
 * gọi API Proxy, và cập nhật trạng thái trở lại ERPNext.
 * @param {object} invoice - Đối tượng POS Invoice đầy đủ từ Frappe.
 * @param {object} pos_profile - Đối tượng POS Profile đang hoạt động.
 * @param {function} onSuccess - Callback được gọi khi in thành công.
 * @param {function} onError - Callback được gọi khi có lỗi xảy ra.
 */
export async function handleTaxPrint(invoice, pos_profile, onSuccess, onError) {
	debugLog("Hàm handleTaxPrint được gọi với các tham số sau:", {
		invoice: invoice,
		pos_profile: pos_profile,
	});

	try {
		// === BƯỚC 0: KIỂM TRA CẤU HÌNH VÀ DỮ LIỆU CẦN THIẾT ===
		debugLog("Bước 0: Bắt đầu xác thực cấu hình.");
		const apiUrl = pos_profile.custom_print_api_url || "http://localhost:5000/api/print";
		const protectKey = pos_profile.custom_protect_key;

		const validationErrors = [];
		if (!protectKey) validationErrors.push("ProtectKey chưa được cấu hình");
		if (!pos_profile.tax_roll_code) validationErrors.push("Tax Roll Code (tiền tố) chưa được thiết lập");
		if (pos_profile.tax_current_counter == null)
			validationErrors.push("Tax Current Counter (số hiện tại) chưa được thiết lập");
		if (pos_profile.tax_start_number == null)
			validationErrors.push("Tax Start Number (số bắt đầu) chưa được thiết lập");
		if (!invoice || !invoice.name) validationErrors.push("Dữ liệu hóa đơn không hợp lệ");

		if (validationErrors.length > 0) {
			const errorMessage = `Lỗi cấu hình POS Profile:\n${validationErrors.map((e) => `• ${e}`).join("\n")}`;
			throw new Error(errorMessage);
		}
		debugLog("Xác thực cấu hình thành công.");

		// === BƯỚC 1: XÁC ĐỊNH TAXCODE VÀ FLAG ===
		const nextTaxCodeNumber = pos_profile.tax_current_counter;
		const taxCode = `${pos_profile.tax_roll_code}${nextTaxCodeNumber}`;
		const flag =
			pos_profile.tax_current_counter === pos_profile.tax_start_number ? "REPLACE" : "CONTINUE";
		debugLog("Bước 1: Xác định TaxCode và Flag.", { taxCode, flag });

		// === BƯỚC 2: TẠO BODY HOÀN CHỈNH CHO REQUEST, KHỚP VỚI MẪU ===
		const resolvedTaxId = String(invoice.tax_id || invoice.customer_tax_id || "").trim();
		console.log("[TRACE] handler resolvedTaxId =", resolvedTaxId);

		const body = {
			Flag: flag,
			DocNo: invoice.name,
			TaxCode: taxCode,
			InternalCode: invoice.name,

			CustomerName: String(invoice.customer || invoice.customer_name || invoice.title),
			CustomerInfo: resolvedTaxId || String(invoice.title || "N/A"),
			Cashier: String(invoice.owner || invoice.modified_by),
			CashierName: String(invoice.owner || invoice.modified_by),

			Products: [
				{
					Name: "商品總數 (SP)",
					Qty: String(invoice.total_qty || "0"),
					Price: String(invoice.total || "0"),
				},
			],

			OriginalContent: "Summary Only",
			Total: String(invoice.total || "0"),
			TotalAmount: String(invoice.total || "0"),
			ServiceFee: String(invoice.total_commission || "0"),
			Discount: String(invoice.discount_amount || "0"),
			TotalDiscount: String(invoice.discount_amount || "0"),
			GrandTotal: String(invoice.grand_total || "0"),
			Cash: String(invoice.paid_amount || "0"),
			Statistics: String(invoice.grand_total || "0"),
			ErrorMessage: " ",
			StatusReason: "Valid",
			TaxStatus: "valid",
			Currency: String(invoice.currency || "TWD"),
			PrinterName: String(pos_profile.name || "PRINTER_NAME"),
			PosTerminal: String(pos_profile.name || pos_profile.warehouse || "POS Terminal"),

			RequestTime: new Date().toISOString(),
		};
		debugLog("[TRACE] print body preview =", {
			CustomerName: body.CustomerName,
			CustomerInfo: body.CustomerInfo,
			TaxCode: body.TaxCode,
		});

		debugLog("Bước 2: Tạo body request thành công, khớp với mẫu yêu cầu.", { body });

		// === BƯỚC 3: GỌI API PROXY ===
		debugLog("Bước 3: Gửi yêu cầu đến API Proxy...", { url: apiUrl });
		const response = await fetch(apiUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Protect-Print-Key": protectKey,
			},
			body: JSON.stringify(body),
		});

		const responseText = await response.text();
		debugLog("Nhận được phản hồi từ API Proxy.", {
			status: response.status,
			ok: response.ok,
			body: responseText.substring(0, 500),
		});

		if (!response.ok) {
			throw new Error(`Lỗi từ máy chủ in (${response.status}): ${responseText}`);
		}

		// === BƯỚC 4: XỬ LÝ KHI IN THÀNH CÔNG (CẬP NHẬT TRẠNG THÁI LÊN ERPNext) ===
		debugLog("Bước 4: In thành công, đang cập nhật trạng thái lên ERPNext...");
		const updateResponse = await frappe.call({
			method: "posawesome.posawesome.api.tax_roll.increment_tax_counter",
			args: {
				pos_profile: pos_profile.name,
				invoice_name: invoice.name,
				tax_code: taxCode,
			},
		});

		if (!updateResponse.message || !updateResponse.message.success) {
			throw new Error("Không thể cập nhật Tax Counter trên server sau khi in.");
		}

		debugLog("Cập nhật trạng thái lên ERPNext thành công.", updateResponse.message);

		// === BƯỚC 5: XỬ LÝ PHÍA CLIENT SAU KHI MỌI THỨ THÀNH CÔNG ===
		const { new_counter, next_display } = updateResponse.message;

		// Cập nhật pos_profile object
		pos_profile.tax_current_counter = new_counter;

		// Cập nhật header display
		updateHeaderTaxDisplay(next_display);

		if (onSuccess) {
			onSuccess({
				taxCode: taxCode,
				newCounter: new_counter,
				nextDisplay: next_display,
				flag: flag,
			});
		}

		frappe.show_alert({
			message: `Đã in thành công hóa đơn thuế: ${taxCode}`,
			indicator: "green",
		});

		debugLog("🎉 Hoàn tất quy trình in thuế thành công!");
	} catch (error) {
		console.error("Tax Print Error:", error);
		if (onError) {
			onError(error);
		}
		frappe.msgprint({
			title: "Lỗi In Hóa Đơn Thuế",
			message: `Không thể hoàn tất quá trình in: ${error.message}`,
			indicator: "red",
		});
	}
}

/**
 * Xử lý quy trình in hóa đơn GTGT Việt Nam (VNTAX).
 * Gửi danh sách sản phẩm chi tiết để PrintController tự tính toán.
 * @param {object} invoice - Đối tượng POS Invoice đầy đủ từ Frappe.
 * @param {object} pos_profile - Đối tượng POS Profile đang hoạt động.
 * @param {function} onSuccess - Callback được gọi khi in thành công.
 * @param {function} onError - Callback được gọi khi có lỗi xảy ra.
 */
export async function handleVietnamTaxPrint(invoice, pos_profile, onSuccess, onError) {
	debugLog(`[VNTAX_START] 🚀 Bắt đầu gửi hóa đơn Việt Nam: ${invoice.name}, ${invoice.items.length} items`);

	try {
		// === BƯỚC 0: KIỂM TRA CẤU HÌNH ===
		const apiUrl = pos_profile.custom_print_api_url || "http://localhost:5000/api/print";
		const protectKey = pos_profile.custom_protect_key;

		if (!protectKey) {
			throw new Error("ProtectKey chưa được cấu hình trong POS Profile.");
		}
		if (!invoice || !invoice.name || !invoice.items || invoice.items.length === 0) {
			throw new Error("Dữ liệu hóa đơn không hợp lệ hoặc không có sản phẩm.");
		}

		// === BƯỚC 1: CHUẨN BỊ DỮ LIỆU SẢN PHẨM ===
		debugLog(`[VNTAX_PROCESS] 📦 Chuẩn bị ${invoice.items.length} sản phẩm với VAT rate...`);

		// Populate VAT rate cho từng item (đơn giản hóa)
		for (const item of invoice.items) {
			try {
				const vatRateResponse = await frappe.call({
					method: "posawesome.posawesome.api.invoices.get_item_vat_rate",
					args: { item_code: item.item_code }
				});
				item.calculated_vat_rate = vatRateResponse?.message ? parseFloat(vatRateResponse.message) : 0;
			} catch (error) {
				console.warn(`Failed to get VAT rate for ${item.item_code}:`, error);
				item.calculated_vat_rate = 0;
			}
		}

		// Tạo products array với VAT rate
		const products = invoice.items.map((item) => {
			const isCommercialDiscount =
				item.custom_inventory_type === "4" ||
				item.item_name?.toLowerCase().includes("chiết khấu") ||
				item.item_name?.toLowerCase().includes("chiếu khấu");

			const vatRate = isCommercialDiscount ? "0" : String(Math.round(item.calculated_vat_rate || 0));

			return {
				Name: item.item_name || item.description,
				Qty: String(item.qty),
				Price: String(item.rate),
				UnitName: item.uom || "Cái",
				InventoryItemType: isCommercialDiscount ? "4" : "0",
				VATRate: vatRate,
				DiscountRate: "0",
				ServiceFeeRate: "0",
				ExciseTaxRate: "0",
				Category: isCommercialDiscount ? "CK" : item.item_group || "N/A",
				WarehouseCode: isCommercialDiscount ? "CK" : item.warehouse || "N/A",
			};
		});

		debugLog(`[VNTAX_PROCESS] ✅ Đã chuẩn bị ${products.length} sản phẩm`);

		// === BƯỚC 2: TẠO REQUEST BODY ===
		const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
		const internalCode = `VN-IC-${randomSuffix}`;

		const body = {
			Flag: "VNTAX",
			Country: "VN",
			DocNo: invoice.name,
			InternalCode: internalCode,
			TaxCode: "VN-0111200981",
			Cashier: String(invoice.owner || invoice.modified_by),
			CustomerName: String(invoice.customer || invoice.customer_name || invoice.title || "Khách lẻ"),
			CustomerInfo: String(invoice.tax_id || invoice.customer_tax_id || "").trim(),
			PrinterName: "DONG_ANH_Printer",
			PosTerminal: String(pos_profile.name || pos_profile.warehouse || "POS Terminal"),
			RequestTime: new Date().toISOString(),
			Currency: String(invoice.currency || "VND"),
			Products: products,
		};

		// === BƯỚC 3: GỌI API MISA ===
		debugLog(`[VNTAX_API] 📤 Gửi request đến MISA API: ${apiUrl}`);
		debugLog(`[VNTAX_API] 📊 Invoice: ${invoice.name}, Products: ${products.length}, Total: ${invoice.grand_total}`);

		const response = await fetch(apiUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Protect-Print-Key": protectKey,
			},
			body: JSON.stringify(body),
		});

		const responseText = await response.text();

		debugLog(`[VNTAX_API] 📥 MISA Response - Status: ${response.status}, Success: ${response.ok}`);

		if (response.status >= 400 && response.status < 600) {
			throw new Error(`Lỗi từ MISA API (${response.status}): ${responseText}`);
		}

		// === BƯỚC 4: CẬP NHẬT TRẠNG THÁI ERPNext ===
		debugLog(`[VNTAX_UPDATE] 🔄 Cập nhật trạng thái invoice: ${invoice.name}`);

		const updateResponse = await frappe.call({
			method: "posawesome.posawesome.api.invoice.mark_invoice_as_submitted_vntax",
			args: {
				invoice_name: invoice.name,
				response_data: responseText,
			},
		});

		if (!updateResponse.message || updateResponse.message.success === false) {
			throw new Error(`Không thể cập nhật trạng thái: ${updateResponse.message?.message || 'Unknown error'}`);
		}

		debugLog(`[VNTAX_UPDATE] ✅ Cập nhật thành công`);

		// === BƯỚC 5: XỬ LÝ THÀNH CÔNG ===
		const responseMessage = updateResponse.message || {};
		const { req_id } = responseMessage;

		if (onSuccess) {
			onSuccess({
				reqId: req_id,
				newCounter: responseMessage.new_counter,
				nextDisplay: responseMessage.next_display,
			});
		}

		frappe.show_alert({
			message: `Đã gửi hóa đơn VNTAX thành công. ReqID: ${req_id || responseText}`,
			indicator: "green",
		});

		debugLog(`[VNTAX_SUCCESS] 🎉 Hoàn tất gửi MISA thành công: ${invoice.name}`);

	} catch (error) {
		console.error("[VNTAX_ERROR] Lỗi VNTAX:", error);
		debugLog(`[VNTAX_ERROR] ❌ Thất bại: ${error.message}`);

		if (onError) {
			onError(error);
		}
		frappe.msgprint({
			title: "Lỗi Gửi Hóa Đơn MISA",
			message: `Không thể hoàn tất: ${error.message}`,
			indicator: "red",
		});
	}
}

/**
 * Hàm helper để cập nhật hiển thị số hóa đơn trên header.
 * Cách tốt nhất là thông qua một Event Bus toàn cục.
 * @param {string} newDisplay - Chuỗi mới để hiển thị (ví dụ: "PW 689").
 */
export function updateHeaderTaxDisplay(newDisplay) {
	debugLog("Updating header tax display:", { newDisplay });

	// Method 1: Event Bus
	if (window.posEventBus && typeof window.posEventBus.emit === "function") {
		debugLog("Phát sự kiện 'tax-display-updated' qua Event Bus.", { newDisplay });
		window.posEventBus.emit("tax-display-updated", newDisplay);
	}

	// Method 2: Frappe realtime event
	if (frappe && frappe.realtime && typeof frappe.realtime.emit === "function") {
		debugLog("Phát sự kiện qua frappe.realtime.", { newDisplay });
		frappe.realtime.emit("tax_display_updated", { display: newDisplay });
	}

	// Method 3: Custom event
	try {
		const event = new CustomEvent("taxDisplayUpdated", {
			detail: { display: newDisplay },
		});
		document.dispatchEvent(event);
		debugLog("Dispatched custom event 'taxDisplayUpdated'");
	} catch (e) {
		console.warn("Could not dispatch custom event:", e);
	}
}
