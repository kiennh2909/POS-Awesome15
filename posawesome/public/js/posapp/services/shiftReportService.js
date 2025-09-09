/**
 * Shift Report Service - Frontend API Integration
 * Handles all communication between frontend components and backend APIs
 */

class ShiftReportService {
    constructor() {
        this.baseUrl = '/api/method/posawesome.posawesome.api';
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Generic API call method with error handling
     */
    async apiCall(method, args = {}) {
        try {
            const response = await frappe.call({
                method: `${this.baseUrl}.${method}`,
                args: args
            });

            if (response.message && response.message.success === false) {
                throw new Error(response.message.message || 'API call failed');
            }

            return response.message || response;
        } catch (error) {
            console.error(`API Error [${method}]:`, error);
            throw error;
        }
    }

    /**
     * Create new shift report
     */
    async createShiftReport(data) {
        return this.apiCall('shift_reports.create_shift_report', data);
    }

    /**
     * Get shift report by ID
     */
    async getShiftReport(shiftReportId) {
        const cacheKey = `shift_report_${shiftReportId}`;
        const cached = this.getCached(cacheKey);

        if (cached) {
            return cached;
        }

        const result = await this.apiCall('shift_reports.get_shift_report', {
            shift_report_id: shiftReportId
        });

        this.setCached(cacheKey, result);
        return result;
    }

    /**
     * Update shift report
     */
    async updateShiftReport(shiftReportId, data) {
        const result = await this.apiCall('shift_reports.update_shift_report', {
            shift_report_id: shiftReportId,
            data: JSON.stringify(data)
        });

        // Clear cache
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Get list of shift reports
     */
    async getShiftReports(filters = {}, pageLength = 20, pageStart = 0) {
        const cacheKey = `shift_reports_${JSON.stringify(filters)}_${pageLength}_${pageStart}`;
        const cached = this.getCached(cacheKey);

        if (cached) {
            return cached;
        }

        const result = await this.apiCall('shift_reports.get_shift_reports', {
            filters: JSON.stringify(filters),
            limit_page_length: pageLength,
            limit_start: pageStart
        });

        this.setCached(cacheKey, result);
        return result;
    }

    /**
     * Get current user's shift report
     */
    async getCurrentShiftReport() {
        return this.apiCall('shift_reports.get_current_shift_report');
    }

    /**
     * Submit shift report
     */
    async submitShiftReport(shiftReportId) {
        const result = await this.apiCall('shift_reports.submit_shift_report', {
            shift_report_id: shiftReportId
        });

        // Clear related caches
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Verify shift report
     */
    async verifyShiftReport(shiftReportId, notes = '') {
        const result = await this.apiCall('shift_verification.verify_shift_report', {
            shift_report_id: shiftReportId,
            notes: notes
        });

        // Clear cache
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Confirm shift report
     */
    async confirmShiftReport(shiftReportId, notes = '') {
        const result = await this.apiCall('shift_verification.confirm_shift_report', {
            shift_report_id: shiftReportId,
            notes: notes
        });

        // Clear cache
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Reject shift report
     */
    async rejectShiftReport(shiftReportId, reason) {
        const result = await this.apiCall('shift_verification.reject_shift_report', {
            shift_report_id: shiftReportId,
            reason: reason
        });

        // Clear cache
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Get verification history
     */
    async getVerificationHistory(shiftReportId) {
        return this.apiCall('shift_verification.get_shift_report_verification_history', {
            shift_report_id: shiftReportId
        });
    }

    /**
     * Calculate expected closing amounts
     */
    async calculateExpectedClosing(shiftReportId) {
        const result = await this.apiCall('shift_calculations.calculate_expected_closing_amounts', {
            shift_report_id: shiftReportId
        });

        // Clear cache
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Validate closing amounts
     */
    async validateClosingAmounts(shiftReportId, actualAmounts) {
        return this.apiCall('shift_calculations.validate_closing_amounts', {
            shift_report_id: shiftReportId,
            actual_amounts: JSON.stringify(actualAmounts)
        });
    }

    /**
     * Generate shift report summary
     */
    async generateShiftReportSummary(shiftReportId) {
        const cacheKey = `shift_report_summary_${shiftReportId}`;
        const cached = this.getCached(cacheKey);

        if (cached) {
            return cached;
        }

        const result = await this.apiCall('shift_calculations.generate_shift_report_summary', {
            shift_report_id: shiftReportId
        });

        this.setCached(cacheKey, result);
        return result;
    }

    /**
     * Get performance metrics
     */
    async getPerformanceMetrics(shiftReportId) {
        return this.apiCall('shift_calculations.get_shift_performance_metrics', {
            shift_report_id: shiftReportId
        });
    }

    /**
     * Auto calculate shift report
     */
    async autoCalculateShiftReport(shiftReportId) {
        const result = await this.apiCall('shift_calculations.auto_calculate_shift_report', {
            shift_report_id: shiftReportId
        });

        // Clear cache
        this.clearCache(`shift_report_${shiftReportId}`);
        return result;
    }

    /**
     * Get shift analytics
     */
    async getShiftAnalytics(filters = {}) {
        const cacheKey = `shift_analytics_${JSON.stringify(filters)}`;
        const cached = this.getCached(cacheKey);

        if (cached) {
            return cached;
        }

        const result = await this.apiCall('shift_analytics.get_shift_analytics', {
            filters: JSON.stringify(filters)
        });

        this.setCached(cacheKey, result);
        return result;
    }

    /**
     * Get shift comparison report
     */
    async getShiftComparisonReport(dateFrom, dateTo, groupBy = 'day') {
        const cacheKey = `shift_comparison_${dateFrom}_${dateTo}_${groupBy}`;
        const cached = this.getCached(cacheKey);

        if (cached) {
            return cached;
        }

        const result = await this.apiCall('shift_analytics.get_shift_comparison_report', {
            date_from: dateFrom,
            date_to: dateTo,
            group_by: groupBy
        });

        this.setCached(cacheKey, result);
        return result;
    }

    /**
     * Get pending verifications
     */
    async getPendingVerifications() {
        return this.apiCall('shift_verification.get_pending_verifications');
    }

    /**
     * Get verification summary
     */
    async getVerificationSummary() {
        const cacheKey = 'verification_summary';
        const cached = this.getCached(cacheKey);

        if (cached) {
            return cached;
        }

        const result = await this.apiCall('shift_verification.get_verification_summary');

        this.setCached(cacheKey, result, 2 * 60 * 1000); // 2 minutes cache
        return result;
    }

    /**
     * Bulk verify shift reports
     */
    async bulkVerifyShiftReports(shiftReportIds, notes = '') {
        const result = await this.apiCall('shift_verification.bulk_verify_shift_reports', {
            shift_report_ids: JSON.stringify(shiftReportIds),
            notes: notes
        });

        // Clear caches for all affected reports
        shiftReportIds.forEach(id => {
            this.clearCache(`shift_report_${id}`);
        });

        return result;
    }

    /**
     * Cache management methods
     */
    getCached(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }

    setCached(key, data, timeout = null) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });

        // Auto cleanup after timeout
        if (timeout || this.cacheTimeout) {
            setTimeout(() => {
                this.cache.delete(key);
            }, timeout || this.cacheTimeout);
        }
    }

    clearCache(key) {
        this.cache.delete(key);
    }

    clearAllCache() {
        this.cache.clear();
    }

    /**
     * Utility methods
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatDate(date) {
        if (!date) return '-';
        return new Date(date).toLocaleDateString();
    }

    formatDateTime(dateTime) {
        if (!dateTime) return '-';
        return new Date(dateTime).toLocaleString();
    }

    /**
     * Real-time updates subscription
     */
    subscribeToUpdates(callback) {
        if (window.frappe && frappe.realtime) {
            frappe.realtime.on('shift_report_updated', callback);
            frappe.realtime.on('shift_report_verified', callback);
            frappe.realtime.on('shift_report_confirmed', callback);
        }
    }

    unsubscribeFromUpdates(callback) {
        if (window.frappe && frappe.realtime) {
            frappe.realtime.off('shift_report_updated', callback);
            frappe.realtime.off('shift_report_verified', callback);
            frappe.realtime.off('shift_report_confirmed', callback);
        }
    }
}

// Export singleton instance
const shiftReportService = new ShiftReportService();
export default shiftReportService;