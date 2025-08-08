
<template>
  <div>
    <!-- Dialog -->
    <v-dialog v-model="dialog" max-width="600px" persistent>
      <v-card>
        <v-card-title class="headline">
          <v-icon left>mdi-receipt</v-icon>
          Quản Lý Cuộn Hóa Đơn Thuế
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text>
          <!-- POS Profile Validation Warning -->
          <v-alert 
            v-if="!isPosProfileValid" 
            type="error"
            outlined
            class="mb-4"
          >
            <div class="d-flex align-center">
              <v-icon left>mdi-alert-circle</v-icon>
              <strong>Lỗi:</strong> POS Profile không hợp lệ hoặc chưa được chọn
            </div>
          </v-alert>

          <!-- Current Status Display -->
          <v-alert 
            v-if="currentTaxStatus" 
            :type="currentTaxStatus.status === 'Active' ? 'info' : 'warning'"
            outlined
            class="mb-4"
          >
            <div class="d-flex justify-space-between align-center">
              <div>
                <strong>Trạng thái hiện tại:</strong>
                {{ currentTaxStatus.display }}
              </div>
              <v-chip 
                :color="currentTaxStatus.status === 'Active' ? 'green' : 'orange'"
                text-color="white"
                small
              >
                {{ currentTaxStatus.status }}
              </v-chip>
            </div>
          </v-alert>

          <!-- Action Selection -->
          <v-radio-group 
            v-model="selectedAction" 
            class="mb-4"
            @change="resetForm"
          >
            <v-radio
              label="Thiết lập cuộn hóa đơn mới"
              value="new_roll"
              color="primary"
            ></v-radio>
            <v-radio
              label="Cập nhật thông tin cuộn hiện tại"
              value="update"
              color="primary"
            ></v-radio>
          </v-radio-group>

          <v-divider class="mb-4"></v-divider>

          <!-- Form inputs -->
          <v-form ref="taxRollForm" v-model="formValid">
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="newRollConfig.prefix"
                  label="Prefix (2 ký tự)"
                  placeholder="VD: PW, BZ, CZ"
                  outlined
                  dense
                  maxlength="2"
                  :rules="[rules.required, rules.prefixFormat]"
                  @input="newRollConfig.prefix = newRollConfig.prefix.toUpperCase()"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="newRollConfig.startNumber"
                  label="Số bắt đầu"
                  placeholder="VD: 688"
                  outlined
                  dense
                  type="number"
                  min="1"
                  :rules="[rules.required, rules.positiveNumber]"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>

          <!-- Preview -->
          <v-card v-if="isFormValid" outlined class="mt-4">
            <v-card-subtitle class="pb-2">
              <v-icon small left>mdi-eye</v-icon>
              Xem trước
            </v-card-subtitle>
            <v-card-text class="pt-0">
              <div class="d-flex align-center">
                <v-chip color="primary" text-color="white" class="mr-2">
                  {{ previewText }}
                </v-chip>
                <span class="text-caption text--secondary">
                  ({{ selectedAction === 'new_roll' ? 'Cuộn mới' : 'Cập nhật' }})
                </span>
              </div>
            </v-card-text>
          </v-card>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn 
            text 
            @click="closeDialog"
            :disabled="loading"
          >
            Hủy
          </v-btn>
          <v-btn 
            color="primary" 
            @click="submitTaxRoll"
            :disabled="!isFormValid"
            :loading="loading"
          >
            {{ selectedAction === 'new_roll' ? 'Bắt Đầu Cuộn Mới' : 'Cập Nhật' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: 'TaxRollDialog',
  
  props: {
    show: {
      type: Boolean,
      default: false
    },
    posProfile: {
      type: Object,
      default: () => ({})
    }
  },

  data() {
    return {
      dialog: false,
      loading: false,
      formValid: false,
      selectedAction: 'new_roll',
      newRollConfig: {
        prefix: '',
        startNumber: 1
      },
      rules: {
        required: value => !!value || "Trường này là bắt buộc",
        prefixFormat: value => /^[A-Z]{2}$/.test(value) || "Prefix phải là đúng 2 ký tự in hoa (VD: PW, BZ, CZ)",
        positiveNumber: value => value > 0 || "Số phải lớn hơn 0"
      }
    };
  },

  computed: {
    isPosProfileValid() {
      return this.posProfile && 
             typeof this.posProfile === 'object' && 
             this.posProfile.name && 
             this.posProfile.name.trim() !== '';
    },

    currentTaxStatus() {
      if (!this.isPosProfileValid || !this.posProfile.tax_roll_code) {
        return null;
      }
      
      return {
        display: `${this.posProfile.tax_roll_code} ${this.posProfile.tax_current_counter || 1}`,
        status: this.posProfile.tax_roll_status || 'Inactive'
      };
    },

    isFormValid() {
      return this.isPosProfileValid &&
             this.newRollConfig.prefix && 
             this.newRollConfig.startNumber > 0 &&
             /^[A-Z]{2}$/.test(this.newRollConfig.prefix);
    },

    previewText() {
      if (!this.selectedAction || !this.newRollConfig.prefix || !this.newRollConfig.startNumber) {
        return '';
      }
      return `${this.newRollConfig.prefix} ${this.newRollConfig.startNumber}`;
    }
  },

  watch: {
    show(newVal) {
      this.dialog = newVal;
      if (newVal) {
        this.initializeForm();
      }
    },

    dialog(newVal) {
      if (!newVal) {
        this.$emit('close');
      }
    }
  },

  methods: {
    initializeForm() {
      // Khởi tạo form với dữ liệu hiện tại nếu có
      if (this.posProfile.tax_roll_code) {
        this.newRollConfig.prefix = this.posProfile.tax_roll_code;
        this.newRollConfig.startNumber = this.posProfile.tax_current_counter || 1;
      } else {
        this.resetForm();
      }
    },

    resetForm() {
      this.newRollConfig = {
        prefix: '',
        startNumber: 1
      };
      if (this.$refs.taxRollForm) {
        this.$refs.taxRollForm.resetValidation();
      }
    },

    async submitTaxRoll() {
      if (!this.isFormValid) {
        this.$refs.taxRollForm.validate();
        return;
      }

      this.loading = true;

      try {
        // Enhanced POS Profile validation
        if (!this.posProfile || typeof this.posProfile !== 'object') {
          throw new Error("POS Profile data không hợp lệ");
        }
        
        if (!this.posProfile.name || this.posProfile.name.trim() === '') {
          throw new Error("Tên POS Profile không được để trống");
        }
        
        if (!this.newRollConfig.prefix || !this.newRollConfig.startNumber) {
          throw new Error("Prefix và số bắt đầu là bắt buộc");
        }

        // Log for debugging
        console.log("POS Profile data:", {
          name: this.posProfile.name,
          prefix: this.newRollConfig.prefix,
          startNumber: this.newRollConfig.startNumber,
          action: this.selectedAction
        });

        const response = await frappe.call({
          method: "posawesome.posawesome.api.tax_roll.update_tax_roll",
          args: {
            pos_profile: this.posProfile.name.trim(),
            new_prefix: this.newRollConfig.prefix.toUpperCase().trim(),
            new_start_number: parseInt(this.newRollConfig.startNumber),
            action: this.selectedAction
          }
        });

        if (response.message && response.message.success) {
          // Emit success event with updated data
          this.$emit('tax-roll-updated', {
            taxRollCode: response.message.tax_roll_code,
            taxCurrentCounter: response.message.tax_current_counter,
            taxStartNumber: response.message.tax_start_number,
            taxRollStatus: response.message.tax_roll_status,
            display: response.message.tax_code_display
          });

          // Show success message
          frappe.show_alert({
            message: response.message.message,
            indicator: "green"
          });

          this.closeDialog();
        } else {
          throw new Error(response.message || "Có lỗi xảy ra khi cập nhật cuộn hóa đơn");
        }

      } catch (error) {
        console.error("Tax Roll Update Error:", error);
        frappe.msgprint({
          title: "Lỗi",
          message: error.message || "Không thể cập nhật cuộn hóa đơn thuế",
          indicator: "red"
        });
      } finally {
        this.loading = false;
      }
    },

    closeDialog() {
      this.dialog = false;
      this.resetForm();
      this.loading = false;
    }
  }
};
</script>

<style scoped>
.headline {
  background: linear-gradient(45deg, #1976d2, #42a5f5);
  color: white !important;
}

.v-chip {
  font-weight: 500;
}

.text-caption {
  font-style: italic;
}
</style>
