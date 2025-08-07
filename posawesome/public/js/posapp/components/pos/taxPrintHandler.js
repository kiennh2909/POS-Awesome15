
export async function handleTaxPrint(invoice, pos_profile, onSuccess, onError) {
  try {
    // === BƯỚC 0: KIỂM TRA DỮ LIỆU CẦN THIẾT ===
    const apiUrl = pos_profile.custom_print_api_url || "http://0.0.0.0:5000/api/print";
    const protectKey = pos_profile.custom_protect_key || "f47ac10b-58cc-4372-a567-0e02b2c3d479";

    // Validation chi tiết hơn
    const validationErrors = [];

    if (!protectKey) validationErrors.push("ProtectKey chưa được cấu hình");
    if (!pos_profile.tax_roll_code) validationErrors.push("Tax Roll Code chưa được thiết lập");
    if (!pos_profile.tax_current_counter && pos_profile.tax_current_counter !== 0) validationErrors.push("Tax Current Counter chưa được thiết lập");
    if (!pos_profile.tax_start_number && pos_profile.tax_start_number !== 0) validationErrors.push("Tax Start Number chưa được thiết lập");

    if (validationErrors.length > 0) {
      const errorMessage = `Lỗi cấu hình POS Profile:\n${validationErrors.map(e => `• ${e}`).join('\n')}\n\nVui lòng thiết lập đầy đủ trong TaxRollDialog.`;
      throw new Error(errorMessage);
    }

    console.log(`POS Profile Validation Passed:`, {
      tax_roll_code: pos_profile.tax_roll_code,
      tax_current_counter: pos_profile.tax_current_counter,
      tax_start_number: pos_profile.tax_start_number,
      has_protect_key: !!protectKey,
      api_url: apiUrl
    });

    // === BƯỚC 4a & 4b: KIỂM TRA VÀ XÁC ĐỊNH FLAG ===
    const nextTaxCodeNumber = pos_profile.tax_current_counter;
    const taxCode = `${pos_profile.tax_roll_code}${nextTaxCodeNumber}`;

    // Bước 2.2 & 3.2: Xác định Flag dựa trên so sánh counter
    let flag = "CONTINUE"; // Mặc định cho hóa đơn thứ 2, 3, 4...

    if (pos_profile.tax_current_counter === pos_profile.tax_start_number) {
      // Bước 2.2: Đây là hóa đơn đầu tiên của cuộn mới
      flag = "REPLACE";
      console.log(`Giai Đoạn 2: Hóa đơn đầu tiên của cuộn mới - Flag = REPLACE`);
      frappe.show_alert({
        message: `Bắt đầu in hóa đơn đầu tiên: ${taxCode} (Flag: REPLACE)`,
        indicator: "blue"
      });
    } else {
      // Bước 3.2: Đây là hóa đơn thứ hai trở đi
      flag = "CONTINUE";
      console.log(`Giai Đoạn 3: Hóa đơn tiếp theo - Flag = CONTINUE`);
    }

    console.log(`Tax Print Analysis:
    - Current Counter: ${pos_profile.tax_current_counter}
    - Start Number: ${pos_profile.tax_start_number}
    - Tax Code: ${taxCode}
    - Flag: ${flag}
    - Logic: ${pos_profile.tax_current_counter} === ${pos_profile.tax_start_number} ? ${pos_profile.tax_current_counter === pos_profile.tax_start_number}`);

    // === BƯỚC 2.2 & 3.2: CHUẨN BỊ PAYLOAD GỬI ĐẾN API PROXY ===
    const body = {
      taxCode: taxCode,
      internalCode: invoice.name,
      flag: flag,

      // Thông tin hóa đơn
      docNo: invoice.name,
      customerName: invoice.customer,
      requestTime: new Date().toISOString(),
      cashier: invoice.owner,
      products: invoice.items.map(item => ({
        name: item.item_name,
        qty: String(item.qty || "0"),
        price: String(item.rate || "0")
      })),
      total: String(invoice.total || "0"),
      discount: String(invoice.discount_amount || "0"),
      grandTotal: String(invoice.grand_total || "0")
    };

    // === BƯỚC 2.3 & 3.3: GỌI API PROXY ===
    console.log(`Sending to API Proxy:`, {
      url: apiUrl,
      taxCode: body.taxCode,
      flag: body.flag,
      docNo: body.docNo
    });

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Protect-Print-Key": protectKey
      },
      body: JSON.stringify(body)
    });

    const responseText = await response.text();

    console.log(`API Proxy Response:`, {
      status: response.status,
      ok: response.ok,
      body: responseText.substring(0, 200) + (responseText.length > 200 ? '...' : '')
    });

    if (!response.ok) {
      // Xử lý lỗi chi tiết hơn cho từng trường hợp
      let errorMessage = `Lỗi từ máy chủ in (${response.status})`;

      if (response.status === 401 || response.status === 403) {
        errorMessage = "Không có quyền truy cập máy chủ in. Vui lòng kiểm tra ProtectKey.";
      } else if (response.status === 400) {
        errorMessage = `Dữ liệu không hợp lệ: ${responseText}`;
      } else if (response.status >= 500) {
        errorMessage = `Lỗi máy chủ in: ${responseText}`;
      } else {
        errorMessage += `: ${responseText}`;
      }

      throw new Error(errorMessage);
    }

    // === BƯỚC 2.4 & 3.4: XỬ LÝ KẾT QUẢ THÀNH CÔNG ===
    console.log(`${flag === "REPLACE" ? "Giai Đoạn 2.4" : "Giai Đoạn 3.4"}: Print API Response:`, responseText);

    // a. Cập nhật Tax Code của POS Invoice và tăng counter thông qua API
    console.log(`Updating invoice ${invoice.name} with tax_code: ${taxCode}`);
    const updateResponse = await frappe.call({
      method: "posawesome.posawesome.api.tax_roll.increment_tax_counter",
      args: {
        pos_profile: pos_profile.name,
        invoice_name: invoice.name,
        tax_code: taxCode
      }
    });

    if (updateResponse.message.success) {
      const newCounter = updateResponse.message.new_counter;
      const nextDisplay = updateResponse.message.next_display;

      console.log(`${flag === "REPLACE" ? "Bước 2.4" : "Bước 3.4"} - Backend Updates:`, {
        old_counter: pos_profile.tax_current_counter,
        new_counter: newCounter,
        next_display: nextDisplay,
        invoice_updated: invoice.name
      });

      // b. Cập nhật POS Profile local (Bước 2.4 & 3.4)
      pos_profile.tax_current_counter = newCounter;

      // c. Cập nhật header display real-time (Bước 2.4 & 3.4)
      updateHeaderTaxDisplay(nextDisplay);

      // d. Gọi callback thành công
      if (onSuccess) {
        onSuccess({
          taxCode: taxCode,
          nextDisplay: nextDisplay,
          newCounter: newCounter,
          flag: flag,
          phase: flag === "REPLACE" ? "Giai Đoạn 2" : "Giai Đoạn 3"
        });
      }

      // e. Thông báo thành công cho người dùng (Bước 2.4 & 3.4)
      const successMessage = flag === "REPLACE"
        ? `✅ Giai Đoạn 2 hoàn thành: In thành công hóa đơn đầu tiên ${taxCode}`
        : `✅ Giai Đoạn 3 hoàn thành: In thành công hóa đơn tiếp theo ${taxCode}`;

      frappe.show_alert({
        message: successMessage,
        indicator: "green"
      });

      console.log(`🎉 Tax Print Complete:
      - Printed: ${taxCode} 
      - Next: ${nextDisplay}
      - Counter: ${pos_profile.tax_current_counter - 1} → ${pos_profile.tax_current_counter}
      - Phase: ${flag === "REPLACE" ? "Giai Đoạn 2 (REPLACE)" : "Giai Đoạn 3 (CONTINUE)"}`);
    }

  } catch (error) {
    console.error("Tax Print Error:", error);

    if (onError) {
      onError(error);
    }

    frappe.msgprint({
      title: "Lỗi In Hóa Đơn Thuế",
      message: `Không thể in hóa đơn thuế: ${error.message}`,
      indicator: "red"
    });
  }
}

// Hàm helper để cập nhật hiển thị trên header
export function updateHeaderTaxDisplay(newDisplay) {
  // Emit event để navbar cập nhật
  const navbar = document.querySelector('nav');
  if (navbar && navbar.__vue__) {
    if (navbar.__vue__.update_tax_display) {
      navbar.__vue__.update_tax_display(newDisplay);
    }
  }

  // Hoặc sử dụng event bus
  if (window.posEventBus) {
    window.posEventBus.$emit('tax-display-updated', newDisplay);
  }
}
