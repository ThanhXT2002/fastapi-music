# 🔐 Admin Panel Setup Guide

## Quick Setup

### 1. **Setup Environment**
```bash
# Copy environment template
cp .env.example .env

# Install dependencies
uv pip install -r requirements.txt
```

### 2. **Generate Admin Password**
```bash
# Run the password generator
python generate_admin_password.py

# Follow prompts to create secure password
# Script will automatically update .env file
```

### 3. **Start Server**
```bash
# Run with uv
uv run python main.py

# Or activate venv first
python main.py
```

### 4. **Access Admin Panel**
- **URL**: http://localhost:8000/admin
- **Username**: Set in ADMIN_USERNAME (default: musicadmin)
- **Password**: What you created in step 2

---

## 🚀 Production Deployment

### Environment Variables Required:
```bash
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD_HASH=generated_bcrypt_hash
ADMIN_SECRET_KEY=secure_random_string
```

### Generate Password on Production:
```bash
# Method 1: Use the script (Recommended)
python generate_admin_password.py

# Method 2: Manual bcrypt (if script not available)
python -c "
import bcrypt
password = 'your_secure_password'
hash_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print('ADMIN_PASSWORD_HASH=' + hash_bytes.decode('utf-8'))
"
```

### Docker Environment:
```dockerfile
# In your Dockerfile or docker-compose.yml
ENV ADMIN_USERNAME=musicadmin
ENV ADMIN_PASSWORD_HASH=your_generated_hash
ENV ADMIN_SECRET_KEY=your_secret_key
```

---

## 🔒 Security Best Practices

### ✅ Current Security Features:
- **bcrypt password hashing** with salt
- **Environment variable configuration**
- **Separate secret key** for admin sessions
- **No hardcoded credentials** in code

### 🎯 Additional Recommendations:
- Use **HTTPS** in production
- Implement **rate limiting** for login attempts
- Enable **2FA** for admin accounts
- Use **database-based user management** for multiple admins
- Set up **audit logging** for admin actions

---

## 🛠️ Admin Panel Features

### 📊 **Available Models:**
- **Users**: Manage user accounts and authentication
- **Songs**: Music library management
- **YouTube Cache**: Downloaded video cache management

### 🔍 **Features:**
- **Search & Filter**: Find records quickly
- **CRUD Operations**: Create, Read, Update, Delete
- **Pagination**: Handle large datasets
- **Export Data**: Download records as needed

---

## 🚨 Troubleshooting

### Common Issues:

#### "No module named 'sqladmin'"
```bash
uv pip install sqladmin
```

#### "No module named 'bcrypt'"  
```bash
uv pip install bcrypt
```

#### "Admin panel setup failed"
Check your environment variables:
```bash
echo $ADMIN_USERNAME
echo $ADMIN_PASSWORD_HASH
echo $ADMIN_SECRET_KEY
```

#### "Authentication failed"
Regenerate password hash:
```bash
python generate_admin_password.py
```

---

## 📝 File Structure

```
fastapi-music/
├── app/config/admin.py          # Admin panel configuration
├── generate_admin_password.py   # Password generation utility
├── .env                        # Environment variables (DO NOT COMMIT)
├── .env.example               # Environment template
└── ADMIN_SETUP.md            # This guide
```

**Important**: Never commit `.env` to version control!
