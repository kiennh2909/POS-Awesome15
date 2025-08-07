<template>
  <v-dialog v-model="show_dialog" max-width="700px" persistent>
    <v-card>
      <v-card-title class="headline">
        <v-icon left>mdi-receipt</v-icon>
        Cập Nhật Thay Thế Cuộn Giấy In
      </v-card-title>

      <v-card-text>
        <v-container>
          <!-- Dropdown Hành động -->
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="selected_action"
                :items="action_options"
                label="Hành động"
                outlined
                dense
                @change="onActionChange"
              ></v-select>
            </v-col>
          </v-row>

          <v-divider class="my-4"></v-divider>

          <!-- Session Cuộn hiện tại -->
          <v-row>
            <v-col cols="12">
              <h3 class="mb-3">Session Cuộn Hiện Tại</h3>
              <v-card outlined class="pa-3 mb-4">
                <v-row dense>
                  <v-col cols="6" md="3">
                    <div class="text-caption grey--text">Prefix</div>
                    <div class="text-h6">{{ current_tax_info.tax_roll_code || 'N/A' }}</div>
                  </v-col>
                  <v-col cols="6" md="3">
                    <div class="text-caption grey--text">Start</div>
                    <div class="text-h6">{{ current_tax_info.tax_start_number || 'N/A' }}</div>
                  </v-col>
                  <v-col cols="6" md="3">
                    <div class="text-caption grey--text">Số hiện tại</div>
                    <div class="text-h6">{{ current_tax_info.tax_current_counter || 'N/A' }}</div>
                  </v-col>
                  <v-col cols="6" md="3">
                    <div class="text-caption grey--text">Tình trạng</div>
                    <v-chip 
                      :color="getStatusColor(current_tax_info.tax_roll_status)"
                      small
                      text-color="white"
                    >
                      {{ getStatusText(current_tax_info.tax_roll_status) }}
                    </v-chip>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption grey--text">Thời gian cập nhật</div>
                    <div class="text-body-2">{{ formatDateTime(current_tax_info.tax_update_time) || 'Chưa cập nhật' }}</div>
                  </v-col>
                </v-row>
              </v-card>
            </v-col>
          </v-row>

          <!-- Session Thay thế -->
          <v-row>
            <v-col cols="12">
              <h3 class="mb-3">Session Thay Thế</h3>
              <v-card outlined class="pa-3">
                <v-row dense>
                  <v-col cols="6">
                    <v-text-field
                      v-model="new_prefix"
                      label="Prefix"
                      placeholder="VD: PW, BZ, CZ"
                      :rules="[rules.required, rules.prefix]"
                      outlined
                      dense
                      :disabled="selected_action !== 'new_roll'"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="new_start_number"
                      label="Start"
                      type="number"
                      :rules="[rules.required, rules.number]"
                      outlined
                      dense
                      :disabled="selected_action !== 'new_roll'"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <div class="text-caption grey--text">Số hiện tại</div>
                    <div class="text-h6">{{ new_start_number || 'N/A' }}</div>
                  </v-col>
                  <v-col cols="6">
                    <div class="text-caption grey--text">Tình trạng</div>
                    <v-chip color="green" small text-color="white">
                      Đang hoạt động
                    </v-chip>
                  </v-col>
                  <v-col cols="12">
                    <div class="text-caption grey--text">Thời gian cập nhật</div>
                    <div class="text-body-2">{{ getCurrentTime() }}</div>
                  </v-col>
                </v-row>
              </v-card>
            </v-col>
          </v-row>

          <!-- Preview -->
          <v-row v-if="new_prefix && new_start_number && selected_action === 'new_roll'">
            <v-col cols="12">
              <v-alert type="info" outlined class="mt-3">
                <strong>Mã thuế tiếp theo sẽ là:</strong> {{ new_prefix }} {{ new_start_number }}
              </v-alert>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <v-btn color="grey" text @click="close_dialog">
          Close
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn color="grey" text @click="close_dialog">
          Hủy bỏ
        </v-btn>
        <v-btn 
          color="primary" 
          @click="save_changes"
          :loading="loading"
          :disabled="!canSave"
        >
          Save
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "TaxRollDialog",
  props: {
    show: {
      type: Boolean,
      default: false
    },
    pos_profile: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      show_dialog: false,
      loading: false,
      current_tax_info: {},
      new_prefix: "",
      new_start_number: "",
      selected_action: "update_current",
      action_options: [
        { text: "Cập nhật cuộn hiện tại", value: "update_current" },
        { text: "Thay cuộn mới", value: "new_roll" }
      ],
      rules: {
        required: v => !!v || 'Trường này bắt buộc',
        prefix: v => /^[A-Z]{2,5}$/.test(v) || 'Prefix phải là 2-5 ký tự viết hoa',
        number: v => /^\d+$/.test(v) && parseInt(v) > 0 || 'Phải là số nguyên dương'
      }
    }
  },
  computed: {
    canSave() {
      if (this.selected_action === "update_current") {
        return true; // Có thể cập nhật cuộn hiện tại
      } else if (this.selected_action === "new_roll") {
        return this.new_prefix && this.new_start_number;
      }
      return false;
    }
  },
  watch: {
    show(val) {
      this.show_dialog = val;
      if (val) {
        this.load_current_tax_info();
      }
    },
    show_dialog(val) {
      if (!val) {
        this.$emit('close');
      }
    }
  },
  methods: {
    async load_current_tax_info() {
      try {
        const response = await frappe.call({
          method: "posawesome.posawesome.api.tax_roll.get_current_tax_info",
          args: {
            pos_profile: this.pos_profile
          }
        });
        this.current_tax_info = response.message || {};

        // Điền sẵn thông tin cho session thay thế
        if (this.current_tax_info.tax_roll_code) {
          this.new_prefix = this.current_tax_info.tax_roll_code;
        }
      } catch (error) {
        console.error("Error loading tax info:", error);
        this.$toast.error("Không thể tải thông tin cuộn thuế");
      }
    },

    onActionChange() {
      if (this.selected_action === "update_current") {
        // Reset form khi chọn cập nhật cuộn hiện tại
        this.new_prefix = this.current_tax_info.tax_roll_code || "";
        this.new_start_number = "";
      } else if (this.selected_action === "new_roll") {
        // Để trống để người dùng nhập mới
        this.new_prefix = "";
        this.new_start_number = "";
      }
    },

    async save_changes() {
      this.loading = true;
      try {
        let response;

        if (this.selected_action === "update_current") {
          // Logic cập nhật cuộn hiện tại
          response = await frappe.call({
            method: "posawesome.posawesome.api.tax_roll.update_current_tax_roll",
            args: {
              pos_profile: this.pos_profile,
              action: "update_current"
            }
          });
        } else if (this.selected_action === "new_roll") {
          // Logic thay cuộn mới - Bước 1.2
          response = await frappe.call({
            method: "posawesome.posawesome.api.tax_roll.update_tax_roll",
            args: {
              pos_profile: this.pos_profile,
              new_prefix: this.new_prefix.toUpperCase(),
              new_start_number: parseInt(this.new_start_number),
              action: "new_roll"
            }
          });
        }

        if (response.message.success) {
          // Bước 1.4: Cập nhật giao diện
          this.$toast.success(response.message.message);
          
          // Emit event với thông tin đầy đủ để cập nhật header bar
          this.$emit('updated', {
            ...response.message,
            pos_profile: this.pos_profile,
            action: this.selected_action,
            new_prefix: this.new_prefix,
            new_start_number: this.new_start_number
          });
          
          // Reload current tax info để đồng bộ
          await this.load_current_tax_info();
          
          this.close_dialog();
          
          // Log kết quả thành công
          console.log(`Tax Roll Setup Complete: ${response.message.tax_code_display || this.new_prefix + ' ' + this.new_start_number}`);
        }
      } catch (error) {
        console.error("Error saving changes:", error);
        this.$toast.error("Không thể lưu thay đổi: " + error.message);
      } finally {
        this.loading = false;
      }
    },

    close_dialog() {
      this.show_dialog = false;
      this.new_prefix = "";
      this.new_start_number = "";
      this.selected_action = "update_current";
    },

    formatDateTime(datetime) {
      if (!datetime) return "";
      const date = new Date(datetime);
      const time = date.toLocaleTimeString('vi-VN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
      const dateStr = date.toLocaleDateString('vi-VN');
      return `${time} - ${dateStr}`;
    },

    getCurrentTime() {
      const now = new Date();
      const time = now.toLocaleTimeString('vi-VN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
      const dateStr = now.toLocaleDateString('vi-VN');
      return `${time} - ${dateStr}`;
    },

    getStatusColor(status) {
      switch(status) {
        case 'Active': return 'green';
        case 'Finished': return 'orange';
        case 'Inactive': return 'grey';
        default: return 'grey';
      }
    },

    getStatusText(status) {
      switch(status) {
        case 'Active': return 'Đang hoạt động';
        case 'Finished': return 'Đã kết thúc';
        case 'Inactive': return 'Không hoạt động';
        default: return 'N/A';
      }
    }
  }
}
</script>

<style scoped>
.text-caption {
  font-size: 0.75rem !important;
  line-height: 1rem !important;
}
</style>