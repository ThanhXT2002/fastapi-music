# 📦 Hướng dẫn cập nhật Dependencies

## 🔄 Cách cập nhật requirements.txt

### Phương pháp 1: Sử dụng UV (Khuyến nghị)

```bash
# Cập nhật tất cả dependencies lên phiên bản mới nhất
uv sync --upgrade

# Tạo requirements.txt mới từ môi trường hiện tại
uv pip freeze > requirements.txt
```

### Phương pháp 2: Sử dụng pip truyền thống

```bash
# Cập nhật một package cụ thể
pip install --upgrade package_name

# Cập nhật tất cả packages
pip list --outdated
pip install --upgrade package1 package2 ...

# Tạo requirements.txt mới
pip freeze > requirements.txt
```

### Phương pháp 3: Cập nhật thủ công

1. Kiểm tra phiên bản hiện tại:
```bash
uv pip freeze | grep package_name
```

2. Cập nhật package:
```bash
uv add package_name@latest
```

3. Cập nhật requirements.txt:
```bash
uv pip freeze > requirements.txt
```

## 🎯 Các packages đã được cập nhật

### ✅ Packages mới được thêm (cho Firebase):
- `firebase-admin==6.8.0`
- `google-api-core==2.24.2`
- `google-api-python-client==2.170.0`
- `google-auth-httplib2==0.2.0`
- `google-cloud-core==2.4.3`
- `google-cloud-firestore==2.21.1`
- `google-cloud-storage==2.20.0`
- `grpcio==1.71.2`
- `protobuf==5.29.4`

### ⬆️ Packages đã được cập nhật:
- `yt-dlp`: `2024.5.27` → `2025.5.22`
- `email_validator` → `email-validator`
- `pydantic_core` → `pydantic-core`
- `SQLAlchemy` → `sqlalchemy`

## 🧪 Kiểm tra sau khi cập nhật

```bash
# Test ứng dụng hoạt động
python firebase_auth_test_suite.py

# Khởi động server
python main.py
```

## 📋 Checklist cập nhật dependencies

- [ ] Backup requirements.txt cũ
- [ ] Chạy `uv sync --upgrade` hoặc `pip install --upgrade`
- [ ] Tạo requirements.txt mới với `uv pip freeze > requirements.txt`
- [ ] Test toàn bộ ứng dụng
- [ ] Commit thay đổi vào git

## ⚠️ Lưu ý

1. **Backup trước khi cập nhật**: Luôn backup `requirements.txt` cũ
2. **Test sau khi cập nhật**: Chạy test suite để đảm bảo không có breaking changes
3. **Cập nhật từng loại**: Có thể cập nhật từng nhóm packages (core, testing, dev)
4. **Kiểm tra compatibility**: Đảm bảo các packages tương thích với nhau

## 🚀 Automation

Có thể tạo script tự động:

```bash
# update_deps.ps1
$backup = "requirements_backup_$(Get-Date -Format 'yyyyMMdd').txt"
Copy-Item requirements.txt $backup
uv sync --upgrade
uv pip freeze > requirements.txt
python firebase_auth_test_suite.py
```

---

**Lần cập nhật cuối**: 31/05/2025  
**Status**: ✅ All tests passed
