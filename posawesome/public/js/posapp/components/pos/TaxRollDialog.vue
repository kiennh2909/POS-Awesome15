
<template>
  <v-dialog v-model="show_dialog" max-width="600px" persistent>
    <v-card>
      <v-card-title class="headline">
        <v-icon left>mdi-receipt</v-icon>
        Quản Lý Cuộn Hóa Đơn Thuế
      </v-card-title>
      
      <v-card-text>
        <v-container>
          <!-- Thông tin cuộn hiện tại -->
          <v-row>
            <v-col cols="12">
              <h3>Cuộn Hiện Tại</h3>
              <v-simple-table dense>
                <tbody>
                  <tr>
                    <td><strong>Prefix:</strong></td>
                    <td>{{ current_tax_info.tax_roll_code || 'Chưa thiết lập' }}</td>
                  </tr>
                  <tr>
                    <td><strong>Số bắt đầu:</strong></td>
                    <td>{{ current_tax_info.tax_start_number || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <td><strong>Số hiện tại:</strong></td>
                    <td>{{ current_tax_info.tax_current_counter || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <td><strong>Trạng thái:</strong></td>
                    <td>
                      <v-chip 
                        :color="current_tax_info.tax_roll_status === 'Active' ? 'green' : 'grey'"
                        small
                        text-color="white"
                      >
                        {{ current_tax_info.tax_roll_status || 'N/A' }}
                      </v-chip>
                    </td>
                  </tr>
                  <tr v-if="current_tax_info.tax_update_time">
                    <td><strong>Cập nhật lần cuối:</strong></td>
                    <td>{{ formatDateTime(current_tax_info.tax_update_time) }}</td>
                  </tr>
                </tbody>
              </v-simple-table>
            </v-col>
          </v-row>

          <v-divider class="my-4"></v-divider>

          <!-- Form cập nhật -->
          <v-row>
            <v-col cols="12">
              <h3>Cập Nhật Cuộn Mới</h3>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="new_prefix"
                label="Prefix Mới"
                placeholder="VD: PW, BZ, CZ"
                :rules="[rules.required, rules.prefix]"
                outlined
                dense
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="new_start_number"
                label="Số Bắt Đầu"
                type="number"
                :rules="[rules.required, rules.number]"
                outlined
                dense
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Preview -->
          <v-row v-if="new_prefix && new_start_number">
            <v-col cols="12">
              <v-alert type="info" outlined>
                <strong>Mã thuế tiếp theo sẽ là:</strong> {{ new_prefix }} {{ new_start_number }}
              </v-alert>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="grey" text @click="close_dialog">
          Hủy
        </v-btn>
        <v-btn 
          color="primary" 
          @click="update_tax_roll"
          :loading="loading"
          :disabled="!new_prefix || !new_start_number"
        >
          Bắt Đầu Cuộn Mới
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
      rules: {
        required: v => !!v || 'Trường này bắt buộc',
        prefix: v => /^[A-Z]{2,5}$/.test(v) || 'Prefix phải là 2-5 ký tự viết hoa',
        number: v => /^\d+$/.test(v) && parseInt(v) > 0 || 'Phải là số nguyên dương'
      }
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
      } catch (error) {
        console.error("Error loading tax info:", error);
        this.$toast.error("Không thể tải thông tin cuộn thuế");
      }
    },

    async update_tax_roll() {
      this.loading = true;
      try {
        const response = await frappe.call({
          method: "posawesome.posawesome.api.tax_roll.update_tax_roll",
          args: {
            pos_profile: this.pos_profile,
            new_prefix: this.new_prefix.toUpperCase(),
            new_start_number: parseInt(this.new_start_number),
            action: "new_roll"
          }
        });

        if (response.message.success) {
          this.$toast.success(response.message.message);
          this.$emit('updated', response.message);
          this.close_dialog();
        }
      } catch (error) {
        console.error("Error updating tax roll:", error);
        this.$toast.error("Không thể cập nhật cuộn thuế: " + error.message);
      } finally {
        this.loading = false;
      }
    },

    close_dialog() {
      this.show_dialog = false;
      this.new_prefix = "";
      this.new_start_number = "";
    },

    formatDateTime(datetime) {
      if (!datetime) return "";
      return new Date(datetime).toLocaleString('vi-VN');
    }
  }
}
</script>
