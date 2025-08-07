
export async function handleTaxPrint(invoice, pos_profile, onSuccess, onError) {
  try {
    // === BƯỚC 0: KIỂM TRA DỮ LIỆU CẦN THIẾT ===
    const apiUrl = pos_profile.custom_print_api_url || "http://0.0.0.0:5000/api/print";
    const protectKey = pos_profile.custom_protect_key;

    if (!protectKey || !pos_profile.tax_roll_code || !pos_profile.tax_current_counter) {
      throw new Error("Lỗi cấu hình: Vui lòng thiết lập đầy đủ thông tin cuộn hóa đơn và ProtectKey trong POS Profile.");
    }

    // === BƯỚC 4a & 4b: KIỂM TRA VÀ XÁC ĐỊNH FLAG ===
    const nextTaxCodeNumber = pos_profile.tax_current_counter;
    const taxCode = `${pos_profile.tax_roll_code}${nextTaxCodeNumber}`;
    
    let flag = "CONTINUE"; // Mặc định
    if (pos_profile.tax_current_counter === pos_profile.tax_start_number) {
      flag = "REPLACE";
      frappe.show_alert({
        message: "Bắt đầu in trên cuộn hóa đơn mới",
        indicator: "blue"
      });
    }
    
    // === BƯỚC 4c: CHUẨN BỊ PAYLOAD GỬI ĐẾN API PROXY ===
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

    // === BƯỚC 4c (tiếp): GỌI API PROXY ===
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Protect-Print-Key": protectKey
      },
      body: JSON.stringify(body)
    });

    const responseText = await response.text();
    if (!response.ok) {
      throw new Error(`Lỗi từ máy chủ in (${response.status}): ${responseText}`);
    }
    
    // === BƯỚC 5: XỬ LÝ KHI IN THÀNH CÔNG ===
    console.log("Print API Response:", responseText);

    // a. Cập nhật Tax Code và tăng counter thông qua API
    const updateResponse = await frappe.call({
      method: "posawesome.posawesome.api.tax_roll.increment_tax_counter",
      args: {
        pos_profile: pos_profile.name,
        invoice_name: invoice.name,
        tax_code: taxCode
      }
    });

    if (updateResponse.message.success) {
      // b. Cập nhật POS Profile local
      pos_profile.tax_current_counter = updateResponse.message.new_counter;
      
      // c. Gọi callback thành công
      if (onSuccess) {
        onSuccess({
          taxCode: taxCode,
          nextDisplay: updateResponse.message.next_display,
          newCounter: updateResponse.message.new_counter
        });
      }

      // d. Thông báo cho người dùng
      frappe.show_alert({
        message: `Đã in thành công hóa đơn thuế: ${taxCode}`,
        indicator: "green"
      });
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
