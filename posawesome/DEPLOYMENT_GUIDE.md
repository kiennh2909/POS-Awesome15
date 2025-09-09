# 🚀 **POS SHIFT REPORT SYSTEM - DEPLOYMENT GUIDE**

## 📋 **Tổng quan**

Hướng dẫn triển khai đầy đủ hệ thống POS Shift Report cho ERPNext/Frappe Framework.

---

## 🎯 **PREREQUISITES**

### **System Requirements**
- ✅ ERPNext v14+ hoặc v15+
- ✅ Frappe Framework v14+
- ✅ Python 3.8+
- ✅ Node.js 16+
- ✅ MariaDB/MySQL 10.3+
- ✅ Bench CLI

### **Required Apps**
- ✅ `frappe`
- ✅ `erpnext`
- ✅ `posawesome` (custom app)

### **User Permissions**
- ✅ System Manager access
- ✅ File system access
- ✅ Database access

---

## 📁 **STEP 1: PREPARE ENVIRONMENT**

### **1.1 Backup Current System**
```bash
# Navigate to frappe-bench directory
cd /home/frappe/frappe-bench

# Create backup
bench backup --with-files
```

### **1.2 Verify POS Awesome App**
```bash
# Check if posawesome app is installed
bench list-apps

# If not installed, install it
bench get-app posawesome https://github.com/your-repo/posawesome.git
bench install-app posawesome
```

### **1.3 Create Site Backup**
```bash
# Backup specific site
bench backup --site your-site-name
```

---

## 🗄️ **STEP 2: DATABASE MIGRATION**

### **2.1 Copy Migration Files**
```bash
# Copy migration script to patches directory
cp posawesome/patches/add_pos_shift_report_tables.py \
   /home/frappe/frappe-bench/apps/posawesome/posawesome/patches/
```

### **2.2 Run Migration**
```bash
# Navigate to bench directory
cd /home/frappe/frappe-bench

# Run migration for specific site
bench migrate --site your-site-name
```

### **2.3 Verify Migration**
```bash
# Check if DocTypes were created
bench mariadb --site your-site-name

# In MariaDB console:
SHOW TABLES LIKE 'tabPOS Shift Report';
SHOW TABLES LIKE 'tabPOS Shift Report Invoice';
DESCRIBE `tabPOS Shift Report`;
DESCRIBE `tabPOS Shift Report Invoice`;
```

### **2.4 Verify Custom Fields**
```bash
# Check custom fields in existing tables
SELECT * FROM `tabCustom Field`
WHERE dt IN ('POS Opening Shift', 'POS Closing Shift', 'Sales Invoice')
AND fieldname LIKE '%shift_report%';
```

---

## 🔧 **STEP 3: BACKEND SETUP**

### **3.1 Copy API Files**
```bash
# Copy all API files
cp -r posawesome/posawesome/api/* \
      /home/frappe/frappe-bench/apps/posawesome/posawesome/api/

# Copy DocType files
cp -r posawesome/posawesome/doctype/* \
      /home/frappe/frappe-bench/apps/posawesome/posawesome/doctype/
```

### **3.2 Set File Permissions**
```bash
# Set proper permissions
chmod -R 755 /home/frappe/frappe-bench/apps/posawesome/
chown -R frappe:frappe /home/frappe/frappe-bench/apps/posawesome/
```

### **3.3 Clear Cache**
```bash
# Clear Frappe cache
bench clear-cache --site your-site-name

# Restart services
sudo supervisorctl restart all
```

### **3.4 Test API Endpoints**
```bash
# Test basic API connectivity
curl -X GET "https://your-site.com/api/method/posawesome.posawesome.api.shift_reports.get_shift_reports" \
     -H "Authorization: token your-api-key:your-api-secret"
```

---

## 🎨 **STEP 4: FRONTEND SETUP**

### **4.1 Copy Frontend Files**
```bash
# Copy Vue components
cp -r posawesome/public/js/posapp/components/pos/* \
      /home/frappe/frappe-bench/apps/posawesome/posawesome/public/js/posapp/components/pos/

# Copy service files
cp posawesome/public/js/posapp/services/shiftReportService.js \
   /home/frappe/frappe-bench/apps/posawesome/posawesome/public/js/posapp/services/
```

### **4.2 Build Frontend Assets**
```bash
# Navigate to posawesome app directory
cd /home/frappe/frappe-bench/apps/posawesome

# Install dependencies
npm install

# Build assets
npm run build
```

### **4.3 Clear Browser Cache**
```bash
# Clear browser cache or use incognito mode for testing
# Hard refresh: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
```

---

## 🔐 **STEP 5: PERMISSION SETUP**

### **5.1 Assign User Roles**
```bash
# Access ERPNext as Administrator
# Navigate to: User > User List

# For Sales Managers:
# - Assign role: "Sales Manager"
# - Assign role: "POS User"

# For Sales Users:
# - Assign role: "Sales User"
# - Assign role: "POS User"
```

### **5.2 Verify Role Permissions**
```bash
# In ERPNext, go to:
# Setup > Role Permissions Manager

# Verify permissions for:
# - POS Shift Report (DocType)
# - POS Shift Report Invoice (DocType)
```

### **5.3 Set DocType Permissions**
```sql
-- Verify permissions in database
SELECT * FROM `tabDocPerm`
WHERE parent IN ('POS Shift Report', 'POS Shift Report Invoice')
ORDER BY role, permlevel;
```

---

## 🧪 **STEP 6: TESTING & VALIDATION**

### **6.1 Test Database Tables**
```bash
# Test DocType creation
bench console --site your-site-name

# In Python console:
from frappe import get_doc
doc = get_doc("POS Shift Report")
print("POS Shift Report DocType created successfully")

doc = get_doc("POS Shift Report Invoice")
print("POS Shift Report Invoice DocType created successfully")
```

### **6.2 Test API Endpoints**
```python
# Test API functionality
import frappe

# Test shift report creation
result = frappe.call(
    "posawesome.posawesome.api.shift_reports.create_shift_report",
    data={
        "pos_opening_shift": "POS-OPEN-001",
        "opening_amounts": '{"Cash": 1000}'
    }
)
print("API Test Result:", result)
```

### **6.3 Test Frontend Components**
```javascript
// In browser console (after login to ERPNext)

// Test service import
import shiftReportService from '/assets/posawesome/js/posapp/services/shiftReportService.js';

// Test API call
shiftReportService.getShiftReports().then(result => {
    console.log('Frontend API Test:', result);
});
```

### **6.4 Run Integration Tests**
```bash
# Copy test file
cp posawesome/test_shift_report_integration.js \
   /home/frappe/frappe-bench/apps/posawesome/

# Run tests (in browser console)
ShiftReportIntegrationTest.run();
```

---

## 📊 **STEP 7: CONFIGURATION**

### **7.1 POS Profile Setup**
```bash
# In ERPNext, navigate to:
# POS > POS Profile

# Configure:
# - Enable shift management
# - Set closing amount tolerance
# - Configure payment methods
# - Set tax inclusive settings
```

### **7.2 System Settings**
```bash
# Navigate to:
# Setup > System Settings

# Configure:
# - Default currency
# - Date format
# - Time zone
# - Number format
```

### **7.3 Email Notifications (Optional)**
```bash
# Setup email alerts for shift reports
# Navigate to:
# Setup > Email Alert

# Create alerts for:
# - Shift report verification pending
# - Shift report confirmed
# - Variance threshold exceeded
```

---

## 🚀 **STEP 8: PRODUCTION DEPLOYMENT**

### **8.1 Final Migration**
```bash
# Run final migration
bench migrate --site your-site-name

# Clear all caches
bench clear-cache --site your-site-name
bench clear-website-cache --site your-site-name
```

### **8.2 Restart Services**
```bash
# Restart all services
sudo supervisorctl restart frappe-bench-web:
sudo supervisorctl restart frappe-bench-worker:
sudo supervisorctl restart frappe-bench-schedule:
```

### **8.3 Verify Deployment**
```bash
# Check service status
sudo supervisorctl status

# Test application access
curl -I https://your-site.com

# Test POS access
curl -I https://your-site.com/app/pos
```

### **8.4 User Training**
```bash
# Create user documentation
# Schedule training sessions
# Setup support channels
```

---

## 🔍 **STEP 9: MONITORING & MAINTENANCE**

### **9.1 Setup Monitoring**
```bash
# Monitor logs
tail -f /home/frappe/frappe-bench/logs/web.log
tail -f /home/frappe/frappe-bench/logs/worker.log

# Monitor database
bench mariadb --site your-site-name
SHOW PROCESSLIST;
```

### **9.2 Performance Monitoring**
```bash
# Check slow queries
bench mariadb --site your-site-name
SELECT * FROM information_schema.PROCESSLIST
WHERE TIME > 10 ORDER BY TIME DESC;

# Monitor cache usage
bench console --site your-site-name
from frappe.utils import get_cache_stats
print(get_cache_stats())
```

### **9.3 Backup Strategy**
```bash
# Setup automated backups
crontab -e

# Add to crontab:
# 0 2 * * * cd /home/frappe/frappe-bench && bench backup --with-files --site your-site-name
```

---

## 🆘 **TROUBLESHOOTING**

### **Common Issues & Solutions**

#### **Issue 1: Migration Fails**
```bash
# Check migration logs
tail -f /home/frappe/frappe-bench/logs/web.log

# Manual migration
bench migrate --site your-site-name --force
```

#### **Issue 2: API Not Working**
```bash
# Check API logs
tail -f /home/frappe/frappe-bench/logs/web.log

# Test API manually
curl -X POST "https://your-site.com/api/method/posawesome.posawesome.api.shift_reports.get_shift_reports" \
     -H "Content-Type: application/json" \
     -d '{}'
```

#### **Issue 3: Frontend Not Loading**
```bash
# Clear frontend cache
bench clear-website-cache --site your-site-name

# Rebuild assets
cd /home/frappe/frappe-bench/apps/posawesome
npm run build
```

#### **Issue 4: Permission Errors**
```bash
# Check user roles
bench console --site your-site-name

# In Python console:
user = frappe.get_doc("User", "user@example.com")
print("User roles:", user.get("roles"))
```

#### **Issue 5: Database Connection Issues**
```bash
# Check database connectivity
bench mariadb --site your-site-name
SELECT 1;

# Restart database service
sudo systemctl restart mariadb
```

---

## 📞 **SUPPORT & DOCUMENTATION**

### **Support Resources**
- 📖 **Documentation**: `/apps/posawesome/docs/`
- 🐛 **Issue Tracker**: GitHub Issues
- 💬 **Community Forum**: ERPNext Forum
- 📧 **Email Support**: support@yourcompany.com

### **Key Contacts**
- **Technical Lead**: [Name] - [Email]
- **Project Manager**: [Name] - [Email]
- **Business Analyst**: [Name] - [Email]

### **Emergency Contacts**
- **24/7 Support**: [Phone Number]
- **System Administrator**: [Phone Number]

---

## ✅ **POST-DEPLOYMENT CHECKLIST**

### **Functional Testing**
- [ ] Create test shift report
- [ ] Verify calculation logic
- [ ] Test verification workflow
- [ ] Test confirmation process
- [ ] Validate reporting features

### **Performance Testing**
- [ ] Response time < 2 seconds
- [ ] Concurrent users support
- [ ] Memory usage monitoring
- [ ] Database query optimization

### **Security Testing**
- [ ] Role-based access control
- [ ] Data validation
- [ ] Input sanitization
- [ ] Audit trail verification

### **User Acceptance Testing**
- [ ] User training completed
- [ ] User feedback collected
- [ ] Issues resolved
- [ ] Go-live approval received

---

## 🎉 **DEPLOYMENT COMPLETE**

**Congratulations! POS Shift Report System has been successfully deployed.**

### **Next Steps**
1. ✅ Monitor system performance
2. ✅ Collect user feedback
3. ✅ Plan feature enhancements
4. ✅ Schedule regular maintenance
5. ✅ Prepare for future updates

### **System Health Check**
```bash
# Run health check script
curl https://your-site.com/api/method/posawesome.posawesome.api.shift_reports.get_shift_reports
```

**Status: 🟢 SYSTEM READY FOR PRODUCTION USE**

---

*This deployment guide ensures a smooth and successful implementation of the POS Shift Report System. Follow each step carefully and contact support if you encounter any issues.*