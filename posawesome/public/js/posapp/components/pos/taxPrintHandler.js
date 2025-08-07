
/**
 * Chế độ gỡ lỗi. Đặt thành true khi phát triển để xem log chi tiết,
 * đặt thành false khi triển khai (production).
 */
const DEBUG_MODE = true;

/**
 * Ghi log chi tiết nếu DEBUG_MODE được bật.
 * @param {string} message - Tin nhắn chính.
 * @param {object} [details] - Đối tượng chứa thông tin chi tiết.
 */
function debugLog(message, details) {
  if (DEBUG_MODE) {
    if (details) {
      console.log(`[TaxPrintHandler DEBUG] ${message}`, details);
    } else {
      console.log(`[TaxPrintHandler DEBUG] ${message}`);
    }
  }
}

/**
 * Xử lý toàn bộ quy trình in hóa đơn thuế: xác thực, chuẩn bị dữ liệu,
 * gọi API Proxy, và cập nhật trạng thái trở lại ERPNext.
 * PHIÊN BẢN NÀY CHỈ GỬI DÒNG TÓM TẮT SẢN PHẨM.
 * @param {object} invoice - Đối tượng POS Invoice đầy đủ từ Frappe.
 * @param {object} pos_profile - Đối tượng POS Profile đang hoạt động.
 * @param {function} onSuccess - Callback được gọi khi in thành công.
 * @param {function} onError - Callback được gọi khi có lỗi xảy ra.
 */
export async function handleTaxPrint(invoice, pos_profile, onSuccess, onError) {
  console.log(
    "%c handleTaxPrint đang tiếp nhận truyền đối tượng sau vào handleTaxPrint:",
    "color: green; font-weight: bold;",
    this.invoice
  );
  console.log(
    "%c handleTaxPrint đang tiếp nhận  đối tượng Pos-Profile sau vào handleTaxPrint:",
    "color: green; font-weight: bold;",
    this.pos_profile
  );
  try {
    // === BƯỚC 0: KIỂM TRA CẤU HÌNH VÀ DỮ LIỆU CẦN THIẾT ===
    debugLog("Bước 0: Bắt đầu xác thực cấu hình.");
    const apiUrl = pos_profile.custom_print_api_url || "http://localhost:5000/api/print";
    const protectKey = pos_profile.custom_protect_key;

    const validationErrors = [];
    if (!protectKey) validationErrors.push("ProtectKey chưa được cấu hình");
    if (!pos_profile.tax_roll_code) validationErrors.push("Tax Roll Code (tiền tố) chưa được thiết lập");
    if (pos_profile.tax_current_counter == null) validationErrors.push("Tax Current Counter (số hiện tại) chưa được thiết lập");
    if (pos_profile.tax_start_number == null) validationErrors.push("Tax Start Number (số bắt đầu) chưa được thiết lập");
    if (!invoice || !invoice.name) validationErrors.push("Dữ liệu hóa đơn không hợp lệ");

    if (validationErrors.length > 0) {
      const errorMessage = `Lỗi cấu hình POS Profile:\n${validationErrors.map(e => `• ${e}`).join('\n')}`;
      throw new Error(errorMessage);
    }
    debugLog("Xác thực cấu hình thành công.", { pos_profile, invoice_name: invoice.name });

    // === BƯỚC 1: XÁC ĐỊNH TAXCODE VÀ FLAG ===
    const nextTaxCodeNumber = pos_profile.tax_current_counter;
    const taxCode = `${pos_profile.tax_roll_code}${nextTaxCodeNumber}`;
    const flag = (pos_profile.tax_current_counter === pos_profile.tax_start_number) ? "REPLACE" : "CONTINUE";
    debugLog("Bước 1: Xác định TaxCode và Flag.", { taxCode, flag });

    // === BƯỚC 2: TẠO BODY HOÀN CHỈNH CHO REQUEST ===
    const body = {
      taxCode,
      internalCode: invoice.name,
      flag,
      docNo: invoice.name,
      customerName: invoice.customer,
      requestTime: new Date().toISOString(),
      cashier: invoice.owner,
      products: [{
        name: "TONG SO SAN PHAM",
        qty: String(invoice.total_qty || "0"),
        price: String(invoice.total || "0")
      }],
      total: String(invoice.total || "0"),
      serviceFee: String(invoice.service_fee || "0"),
      discount: String(invoice.discount_amount || "0"),
      grandTotal: String(invoice.grand_total || "0"),
      cash: String(invoice.paid_amount || "0"),
      statistics: String(invoice.grand_total || "0")
    };
    debugLog("Bước 2: Tạo body request thành công.", { body });

    // === BƯỚC 3: GỌI API PROXY ===
    debugLog("Bước 3: Gửi yêu cầu đến API Proxy...", { url: apiUrl });
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Protect-Print-Key": protectKey
      },
      body: JSON.stringify(body)
    });

    const responseText = await response.text();
    debugLog("Nhận được phản hồi từ API Proxy.", { status: response.status, ok: response.ok, body: responseText.substring(0, 200) });

    if (!response.ok) {
      throw new Error(`Lỗi từ máy chủ in (${response.status}): ${responseText}`);
    }

    // === BƯỚC 4: XỬ LÝ KHI IN THÀNH CÔNG (CẬP NHẬT TRẠNG THÁI LÊN ERPNEXT) ===
    debugLog("Bước 4: In thành công, đang cập nhật trạng thái lên ERPNext...");
    const updateResponse = await frappe.call({
      method: "posawesome.posawesome.api.tax_roll.increment_tax_counter",
      args: {
        pos_profile: pos_profile.name,
        invoice_name: invoice.name,
        tax_code: taxCode
      }
    });

    if (!updateResponse.message || !updateResponse.message.success) {
      throw new Error("Không thể cập nhật Tax Counter trên server sau khi in.");
    }

    debugLog("Cập nhật trạng thái lên ERPNext thành công.", updateResponse.message);

    // === BƯỚC 5: XỬ LÝ PHÍA CLIENT SAU KHI MỌI THỨ THÀNH CÔNG ===
    const { new_counter, next_display } = updateResponse.message;

    // Cập nhật trạng thái local
    pos_profile.tax_current_counter = new_counter;

    // Gọi callback onSuccess với tất cả dữ liệu cần thiết
    if (onSuccess) {
      onSuccess({
        taxCode: taxCode,
        newCounter: new_counter,
        nextDisplay: next_display,
        flag: flag
      });
    }

    // Thông báo cho người dùng
    frappe.show_alert({
      message: `Đã in thành công hóa đơn thuế: ${taxCode}`,
      indicator: "green"
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
      indicator: "red"
    });
  }
}

/**
 * Hàm helper để cập nhật hiển thị số hóa đơn trên header.
 * Cách tốt nhất là thông qua một Event Bus toàn cục.
 * @param {string} newDisplay - Chuỗi mới để hiển thị (ví dụ: "PW 689").
 */
export function updateHeaderTaxDisplay(newDisplay) {
  if (window.posEventBus && typeof window.posEventBus.emit === 'function') {
    debugLog("Phát sự kiện 'tax-display-updated' qua Event Bus.", { newDisplay });
    window.posEventBus.emit('tax-display-updated', newDisplay);
  } else {
    // Phương án dự phòng: truy cập trực tiếp component (không khuyến khích)
    console.warn("posEventBus not found. Attempting direct component access (this is not recommended).");
    try {
      const navbar = document.querySelector('nav'); // Hoặc một selector cụ thể hơn
      if (navbar && navbar.__vue_app__ && typeof navbar.__vue_app__.config.globalProperties.eventBus.emit === 'function') {
        navbar.__vue_app__.config.globalProperties.eventBus.emit('tax-display-updated', newDisplay);
      }
    } catch (e) {
      console.error("Could not update header display.", e);
    }
  }
}