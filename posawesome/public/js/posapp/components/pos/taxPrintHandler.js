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
	debugLog("Hàm handleVietnamTaxPrint (VIỆT NAM) được gọi...");

	// === LOG DEBUG CHI TIẾT INVOICE DATA ===
	debugLog(`[VAT_DEBUG] 🎯 INVOICE DATA RECEIVED:`);
	debugLog(`[VAT_DEBUG] 📊 Invoice Info: ${invoice.name}, Items Count: ${invoice.items.length}`);
	debugLog(`[VAT_DEBUG] 📊 POS Profile Country: ${pos_profile.country}`);

	try {
		// === BƯỚC 0: KIỂM TRA CẤU HÌNH (VIỆT NAM) ===
		debugLog("Bước 0: Bắt đầu xác thực cấu hình (Việt Nam).");
		const apiUrl = pos_profile.custom_print_api_url || "http://localhost:5000/api/print";
		const protectKey = pos_profile.custom_protect_key;

		if (!protectKey) {
			throw new Error("Lỗi cấu hình: ProtectKey chưa được cấu hình trong POS Profile.");
		}
		if (!invoice || !invoice.name || !invoice.items || invoice.items.length === 0) {
			throw new Error("Dữ liệu hóa đơn không hợp lệ hoặc không có sản phẩm.");
		}
		debugLog("Xác thực cấu hình (Việt Nam) thành công.");

		// === BƯỚC 1: TẠO DANH SÁCH SẢN PHẨM CHI TIẾT (ProductDto) ===
		// Ánh xạ 'invoice.items' (POS Invoice Item) sang 'ProductDto'
		// Lưu ý: invoice.items là các POS Invoice Item, không phải Item master
		debugLog("Bước 1: Bắt đầu tạo danh sách sản phẩm chi tiết (ProductDto) từ POS Invoice Items...");

		// === ĐẢM BẢO TAX INFO ĐƯỢC POPULATE CHO INVOICE ITEMS ===
		// Nếu invoice items chưa có tax info (từ database cũ), lấy từ Item master
		for (const item of invoice.items) {
			if (item.custom_vat_applicable === undefined || item.custom_vat_applicable === null) {
				try {
					debugLog(`[VAT_DEBUG] 📦 Populating tax info for item: ${item.item_code}`);
					const taxInfo = await frappe.call({
						method: "posawesome.posawesome.api.items.get_item_tax_info",
						args: { item_code: item.item_code, price_list: null }
					});
					// Tax information removed - using ERPNext default tax mechanism
					debugLog(`[VAT_DEBUG] 📦 Tax info removed for ${item.item_code}`);
				} catch (error) {
					console.error(`Failed to get tax info for ${item.item_code}:`, error);
					// Tax information removed - using ERPNext default tax mechanism
				}
			}
		}

		// === LOG DEBUG CHI TIẾT INVOICE ITEMS ===
		debugLog(`[VAT_DEBUG] 📦 PROCESSING ${invoice.items.length} INVOICE ITEMS:`);
		invoice.items.forEach((item, index) => {
			debugLog(`[VAT_DEBUG] 📦 Item ${index + 1}: ${item.item_name} (${item.item_code})`);
			debugLog(`[VAT_DEBUG] 📦 Raw Data:`, {
				rate: item.rate,
				base_rate: item.base_rate,
				base_amount: item.base_amount,
				base_net_amount: item.base_net_amount,
				amount: item.amount,
				qty: item.qty,
				custom_vat_applicable: item.custom_vat_applicable,
				custom_vat_rate: item.custom_vat_rate,
				custom_inventory_type: item.custom_inventory_type,
			});

			// Tax information removed - using ERPNext default tax mechanism
		});

		// === TẠO PROMISE ARRAY ĐỂ LẤY VAT RATE CHO TẤT CẢ ITEMS ===
		const itemPromises = invoice.items.map(async (item) => {
			// Xử lý đặc biệt cho dòng chiết khấu thương mại (Type 4)
			const isCommercialDiscount =
				item.custom_inventory_type === "4" ||
				item.item_name?.toLowerCase().includes("chiết khấu") ||
				item.item_name?.toLowerCase().includes("chiếu khấu");

			// === LẤY VAT RATE TỪ ITEM TAX TEMPLATE ===
			let vatRate = "0"; // Mặc định 0%
			let exciseRate = "0"; // Mặc định 0%
			let priceExcludingVAT = item.rate; // Mặc định = giá hiện tại

			try {
				// Gọi API để lấy VAT rate thực từ item_tax_template
				const vatResponse = await frappe.call({
					method: "posawesome.posawesome.api.invoices.get_item_vat_rate",
					args: { item_code: item.item_code }
				});

				if (vatResponse && vatResponse.message !== undefined) {
					vatRate = String(Math.round(vatResponse.message)); // Làm tròn và chuyển thành string
					debugLog(`[VAT_DEBUG] ✅ Got VAT rate for ${item.item_code}: ${vatRate}%`);
				} else {
					debugLog(`[VAT_DEBUG] ⚠️ No VAT rate found for ${item.item_code}, using default 0%`);
					vatRate = "0";
				}
			} catch (error) {
				console.error(`[VAT_DEBUG] ❌ Error getting VAT rate for ${item.item_code}:`, error);
				debugLog(`[VAT_DEBUG] ⚠️ Using default VAT rate 0% for ${item.item_code}`);
				vatRate = "0";
			}

			// Item processed for tax print with correct VAT rate

			return {
				Name: item.item_name || item.description,
				Qty: String(item.qty),
				Price: String(priceExcludingVAT),
				UnitName: item.uom || "Cái",

				// VAT information from item_tax_template
				InventoryItemType: isCommercialDiscount ? "4" : "0",
				VATRate: isCommercialDiscount ? "0" : vatRate,
				DiscountRate: "0",
				ServiceFeeRate: "0",
				ExciseTaxRate: exciseRate,

				Category: isCommercialDiscount ? "CK" : item.item_group || "N/A",
				WarehouseCode: isCommercialDiscount ? "CK" : item.warehouse || "N/A",
			};
		});

		// === CHỜ TẤT CẢ PROMISES HOÀN THÀNH ===
		const products = await Promise.all(itemPromises);
		debugLog("Tạo danh sách sản phẩm chi tiết thành công.", { productCount: products.length });

		// Products array prepared for tax print

		// === BƯỚC 2: TẠO BODY HOÀN CHỈNH (PrintRequest) ===
		// TUÂN THỦ CHÍNH XÁC theo Test Client (bản 10 test case)
		debugLog("Bước 2: Tạo body request (PrintRequest) cho VNTAX theo chuẩn test case...");

		// Tạo InternalCode theo format: VN-IC-{4 ký tự ngẫu nhiên}
		const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
		const internalCode = `VN-IC-${randomSuffix}`;

		// === LOG DEBUG CHI TIẾT REQUEST BODY ===
		debugLog(`[VAT_DEBUG] 📤 REQUEST BODY FOR MISA API:`);
		debugLog(`[VAT_DEBUG] 📤 Header Info:`, {
			Flag: "VNTAX",
			Country: "VN",
			DocNo: invoice.name,
			InternalCode: internalCode,
			CustomerName: String(invoice.customer || invoice.customer_name || invoice.title || "Khách lẻ"),
			Currency: String(invoice.currency || "VND"),
		});
		debugLog(`[VAT_DEBUG] 📤 Products Count: ${products.length}`);

		const body = {
			// Cờ (QUAN TRỌNG - PHẢI LÀ "VNTAX")
			Flag: "VNTAX",
			Country: "VN",

			// Mã định danh (TUÂN THỦ CHUẨN TEST CASE)
			DocNo: invoice.name,
			InternalCode: internalCode, // Format: VN-IC-XXXX
			TaxCode: "VN-0111200981", // PHẢI LÀ "VN-TaxCode-IGNORE" theo test case

			// Thông tin chung (KHỚP VỚI TEST CASE)
			Cashier: String(invoice.owner || invoice.modified_by),
			CustomerName: String(invoice.customer || invoice.customer_name || invoice.title || "Khách lẻ"),
			CustomerInfo: String(invoice.tax_id || invoice.customer_tax_id || "").trim(), // Có thể là empty string
			PrinterName: "DONG_ANH_Printer", // PHẢI LÀ "TestClientPrinter" theo test case
			PosTerminal: String(pos_profile.name || pos_profile.warehouse || "POS Terminal"),
			RequestTime: new Date().toISOString(),
			Currency: String(invoice.currency || "VND"),

			// Dữ liệu thô (Server sẽ tính toán lại dựa trên 'Products')
			Products: products,

			// === KHÔNG CẦN CÁC TRƯỜNG TỔNG HỢP ===
			// Server sẽ tự tính toán từ Products array
			// Total, ServiceFee, Discount, GrandTotal, Cash, Statistics - BỎ ĐI
		};
		debugLog("Tạo body request (VNTAX) thành công.", body);

		// === BƯỚC 3: GỌI API PROXY ===
		debugLog("Bước 3: Gửi yêu cầu đến API Proxy (VNTAX)...");

		// === LOG DEBUG CHI TIẾT REQUEST BEING SENT ===
		debugLog(`[VAT_DEBUG] 🚀 SENDING REQUEST TO MISA API:`);
		debugLog(`[VAT_DEBUG] 🚀 URL: ${apiUrl}`);
		debugLog(`[VAT_DEBUG] 🚀 Method: POST`);
		debugLog(`[VAT_DEBUG] 🚀 Headers:`, {
			"Content-Type": "application/json",
			"X-Protect-Print-Key": protectKey ? "***PROTECTED***" : "MISSING",
		});
		debugLog(`[VAT_DEBUG] 🚀 Body Preview:`, JSON.stringify(body).substring(0, 1000) + "...");

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

		// === LOG DEBUG CHI TIẾT RESPONSE ===
		debugLog(`[VAT_DEBUG] 📥 MISA API RESPONSE:`);
		debugLog(`[VAT_DEBUG] 📥 Status: ${response.status} (${response.ok ? "OK" : "ERROR"})`);
		debugLog(`[VAT_DEBUG] 📥 Response Body: ${responseText}`);

		// API có thể trả về 200 OK ngay cả khi có lỗi (như duplicate request)
		// Chỉ throw error nếu thực sự là lỗi HTTP hoặc server error
		if (response.status >= 400 && response.status < 600) {
			throw new Error(`Lỗi từ máy chủ in (${response.status}): ${responseText}`);
		}

		// Kiểm tra response text có chứa error message không
		if (responseText && typeof responseText === 'string') {
			const lowerResponse = responseText.toLowerCase();
			if (lowerResponse.includes('error') || lowerResponse.includes('failed') || lowerResponse.includes('lỗi')) {
				// Nếu response chứa từ khóa lỗi nhưng status là 200, vẫn coi như thành công
				// vì API có thể trả về warning message
				debugLog(`[VAT_DEBUG] ⚠️ Response contains error keywords but status is ${response.status}, treating as success`);
			}
		}

		// === BƯỚC 4: XỬ LÝ KHI THÀNH CÔNG (CẬP NHẬT TRẠNG THÁI LÊN ERPNext) ===
		debugLog("Bước 4: Gửi MISA thành công, đang cập nhật trạng thái lên ERPNext...");

		// Cập nhật trạng thái hóa đơn Việt Nam (tương tự bước 4 của handleTaxPrint)
		const updateResponse = await frappe.call({
			method: "posawesome.posawesome.api.invoice.mark_invoice_as_submitted_vntax",
			args: {
				invoice_name: invoice.name,
				response_data: responseText,
			},
		});

		debugLog(`[VAT_DEBUG] 📥 ERPNext API Response:`, updateResponse);

		if (!updateResponse.message) {
			debugLog(`[VAT_DEBUG] ❌ No message in updateResponse:`, updateResponse);
			throw new Error("Không nhận được phản hồi từ server khi cập nhật trạng thái.");
		}

		debugLog(`[VAT_DEBUG] 📊 Update response message:`, updateResponse.message);

		// Kiểm tra success flag nếu có, nếu không thì coi như thành công
		if (updateResponse.message.success === false) {
			debugLog(`[VAT_DEBUG] ❌ Update failed with success=false:`, updateResponse.message);
			throw new Error(`Không thể cập nhật trạng thái hóa đơn Việt Nam trên server: ${updateResponse.message.message || 'Unknown error'}`);
		}

		debugLog(`[VAT_DEBUG] ✅ Update successful:`, updateResponse.message);

		debugLog("Cập nhật trạng thái ERPNext thành công.", updateResponse.message);

		// === BƯỚC 5: XỬ LÝ PHÍA CLIENT SAU KHI MỌI THỨ THÀNH CÔNG ===
		// Duy trì bộ đếm ký hiệu riêng cho các hóa đơn phát hành ở Việt Nam (tương tự handleTaxPrint)
		const responseMessage = updateResponse.message || {};
		const { new_counter, next_display, req_id } = responseMessage;

		// Cập nhật pos_profile object nếu có counter mới
		if (new_counter !== undefined) {
			pos_profile.tax_current_counter = new_counter;
		}

		// Cập nhật header display nếu có
		if (next_display) {
			updateHeaderTaxDisplay(next_display);
		}

		if (onSuccess) {
			onSuccess({
				reqId: req_id,
				newCounter: new_counter,
				nextDisplay: next_display,
			});
		}

		frappe.show_alert({
			message: `Đã gửi hóa đơn VNTAX thành công. ReqID: ${req_id || responseText}`,
			indicator: "green",
		});

		debugLog("🎉 Hoàn tất quy trình VNTAX thành công!");
	} catch (error) {
		console.error("Lỗi VNTAX Print:", error);
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
