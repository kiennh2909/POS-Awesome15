# Tạo branch backup trước khi thay đổi
git checkout -b backup-before-shift-report-integration
git add .
git commit -m "BACKUP: Pre-Shift Report Integration - $(date)"

# Tạo tag cho version hiện tại
git tag "v1.0.0-stable-$(date +%Y%m%d)" -m "Stable version before major Shift Report integration"

# Push backup lên remote
git push origin backup-before-shift-report-integration
git push origin --tags

bash


