
<template>
  <v-dialog v-model="dialog" persistent max-width="800px">
    <v-card>
      <v-card-title class="headline">
        <v-icon left>mdi-receipt</v-icon>
        Cập Nhật Thay Thế Cuộn Giấy In
      </v-card-title>
      
      <v-card-text>
        <!-- Action Selection -->
        <v-row class="mb-4">
          <v-col cols="12">
            <v-select
              v-model="selectedAction"
              :items="actionOptions"
              label="Hành động"
              outlined
              dense
            ></v-select>
          </v-col>
        </v-row>

        <!-- Current Roll Information -->
        <v-card outlined class="mb-4" v-if="currentRollInfo">
          <v-card-subtitle>Session Cuộn Hiện Tại</v-card-subtitle>
          <v-card-text>
            <v-row>
              <v-col cols="3">
                <div class="text-subtitle2">Prefix</div>
                <div class="text-h6">{{ currentRollInfo.tax_roll_code || 'N/A' }}</div>
              </v-col>
              <v-col cols="3">
                <div class="text-subtitle2">Start</div>
                <div class="text-h6">{{ currentRollInfo.tax_start_number || 'N/A' }}</div>
              </v-col>
              <v-col cols="3">
                <div class="text-subtitle2">Số hiện tại</div>
                <div class="text-h6">{{ currentRollInfo.tax_current_counter || 'N/A' }}</div>
              </v-col>
              <v-col cols="3">
                <div class="text-subtitle2">Tình trạng</div>
                <v-chip
                  :color="getStatusColor(currentRollInfo.tax_roll_status)"
                  small
                >
                  {{ getStatusText(currentRollInfo.tax_roll_status) }}
                </v-chip>
              </v-col>
            </v-row>
            <v-row class="mt-2">
              <v-col cols="12">
                <div class="text-caption">
                  Thời gian cập nhật: {{ formatDateTime(currentRollInfo.tax_update_time) }}
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- New Roll Configuration -->
        <v-card outlined v-if="selectedAction">
          <v-card-subtitle>Session Thay Thế</v-card-subtitle>
          <v-card-text>
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="newRollConfig.prefix"
                  label="Prefix"
                  outlined
                  dense
                  :rules="[rules.required, rules.prefixFormat]"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="newRollConfig.startNumber"
                  label="Start"
                  type="number"
                  outlined
                  dense
                  :rules="[rules.required, rules.positiveNumber]"
                ></v-text-field>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="newRollConfig.currentNumber"
                  label="Số hiện tại"
                  type="number"
                  outlined
                  dense
                  readonly
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="newRollConfig.status"
                  :items="statusOptions"
                  label="Tình trạng"
                  outlined
                  dense
                ></v-select>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <div class="text-caption">
                  Thời gian cập nhật: {{ formatDateTime(new Date()) }}
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Preview -->
        <v-alert
          v-if="previewText"
          type="info"
          outlined
          class="mt-4"
        >
          <strong>Preview:</strong> {{ previewText }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="closeDialog">
          CLOSE
        </v-btn>
        <v-btn text color="warning" @click="cancelChanges">
          HỦY BỎ
        </v-btn>
        <v-btn 
          color="primary" 
          @click="saveChanges"
          :loading="saving"
          :disabled="!isFormValid"
        >
          SAVE
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "TaxRollDialog",
  data() {
    return {
      dialog: false,
      saving: false,
      selectedAction: "",
      currentRollInfo: null,
      newRollConfig: {
        prefix: "",
        startNumber: 1,
        currentNumber: 1,
        status: "Active"
      },
      actionOptions: [
        { text: "Cập nhật cuộn hiện tại", value: "update_current" },
        { text: "Thay thế bằng cuộn mới", value: "new_roll" },
        { text: "Kết thúc cuộn hiện tại", value: "finish_current" }
      ],
      statusOptions: [
        { text: "Đang hoạt động", value: "Active" },
        { text: "Đã kết thúc", value: "Finished" },
        { text: "Không hoạt động", value: "Inactive" }
      ],
      rules: {
        required: value => !!value || "Trường này là bắt buộc",
        prefixFormat: value => /^[A-Z]{1,4}$/.test(value) || "Prefix phải là 1-4 ký tự in hoa",
        positiveNumber: value => value > 0 || "Số phải lớn hơn 0"
      }
    };
  },
  computed: {
    isFormValid() {
      if (!this.selectedAction) return false;
      if (this.selectedAction === "update_current") return true;
      
      return this.newRollConfig.prefix && 
             this.newRollConfig.startNumber > 0 &&
             /^[A-Z]{1,4}$/.test(this.newRollConfig.prefix);
    },
    previewText() {
      if (!this.selectedAction || !this.newRollConfig.prefix || !this.newRollConfig.startNumber) {
        return "";
      }
      return `${this.newRollConfig.prefix} ${this.newRollConfig.startNumber}`;
    }
  },
  watch: {
    selectedAction(newVal) {
      if (newVal === "update_current" && this.currentRollInfo) {
        // Keep current roll settings
        this.newRollConfig.prefix = this.currentRollInfo.tax_roll_code || "";
        this.newRollConfig.startNumber = this.currentRollInfo.tax_start_number || 1;
        this.newRollConfig.currentNumber = this.currentRollInfo.tax_current_counter || 1;
      } else if (newVal === "new_roll") {
        // Reset for new roll
        this.newRollConfig.prefix = "";
        this.newRollConfig.startNumber = 1;
        this.newRollConfig.currentNumber = 1;
        this.newRollConfig.status = "Active";
      } else if (newVal === "finish_current" && this.currentRollInfo) {
        // Set current roll as finished
        this.newRollConfig.prefix = this.currentRollInfo.tax_roll_code || "";
        this.newRollConfig.startNumber = this.currentRollInfo.tax_start_number || 1;
        this.newRollConfig.currentNumber = this.currentRollInfo.tax_current_counter || 1;
        this.newRollConfig.status = "Finished";
      }
    },
    "newRollConfig.startNumber"(newVal) {
      if (this.selectedAction === "new_roll") {
        this.newRollConfig.currentNumber = newVal;
      }
    }
  },
  methods: {
    openDialog(posProfile) {
      this.currentRollInfo = posProfile;
      this.dialog = true;
      this.resetForm();
    },
    closeDialog() {
      this.dialog = false;
      this.resetForm();
    },
    resetForm() {
      this.selectedAction = "";
      this.newRollConfig = {
        prefix: "",
        startNumber: 1,
        currentNumber: 1,
        status: "Active"
      };
      this.saving = false;
    },
    cancelChanges() {
      this.resetForm();
    },
    async saveChanges() {
      if (!this.isFormValid) return;
      
      this.saving = true;
      
      try {
        let response;
        
        if (this.selectedAction === "update_current") {
          response = await frappe.call({
            method: "posawesome.posawesome.api.tax_roll.update_current_tax_roll",
            args: {
              pos_profile: this.currentRollInfo.name,
              action: "update_current"
            }
          });
        } else {
          response = await frappe.call({
            method: "posawesome.posawesome.api.tax_roll.update_tax_roll",
            args: {
              pos_profile: this.currentRollInfo.name,
              new_prefix: this.newRollConfig.prefix,
              new_start_number: this.newRollConfig.startNumber,
              action: this.selectedAction
            }
          });
        }

        if (response.message && response.message.success) {
          // Update the current profile data
          Object.assign(this.currentRollInfo, {
            tax_roll_code: response.message.tax_roll_code,
            tax_start_number: response.message.tax_start_number,
            tax_current_counter: response.message.tax_current_counter,
            tax_roll_status: response.message.tax_roll_status
          });

          // Emit success event
          this.eventBus.emit("tax_roll_updated", response.message);
          
          this.eventBus.emit("show_message", {
            title: "Thành công",
            message: response.message.message,
            color: "success"
          });
          
          this.closeDialog();
        } else {
          throw new Error(response.message || "Có lỗi xảy ra khi cập nhật cuộn in");
        }
      } catch (error) {
        console.error("Error updating tax roll:", error);
        this.eventBus.emit("show_message", {
          title: "Lỗi",
          message: error.message || "Không thể cập nhật cuộn in",
          color: "error"
        });
      } finally {
        this.saving = false;
      }
    },
    getStatusColor(status) {
      const statusColors = {
        Active: "success",
        Finished: "warning",
        Inactive: "error"
      };
      return statusColors[status] || "grey";
    },
    getStatusText(status) {
      const statusTexts = {
        Active: "Đang hoạt động",
        Finished: "Đã kết thúc",
        Inactive: "Không hoạt động"
      };
      return statusTexts[status] || status;
    },
    formatDateTime(dateTime) {
      if (!dateTime) return "N/A";
      const date = new Date(dateTime);
      return date.toLocaleString("vi-VN");
    }
  },
  mounted() {
    this.eventBus.on("open_tax_roll_dialog", (posProfile) => {
      this.openDialog(posProfile);
    });
  },
  beforeUnmount() {
    this.eventBus.off("open_tax_roll_dialog");
  }
};
</script>

<style scoped>
.text-subtitle2 {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
}
</style>
