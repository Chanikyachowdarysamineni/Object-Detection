# 🔒 Security Features - Complete Reference

**Implementation Date:** May 16, 2026  
**Security Level:** 🟢 Enterprise-Grade  
**Status:** ✅ Production Ready

---

## 📋 Overview

This document provides a complete reference of all security features implemented in the Real-Time Object Detection application.

---

## 🔐 Authentication & JWT Tokens

### Token Generation

**Location:** `backend/app/core/security.py`

```python
from app.core.security import create_access_token, create_refresh_token

# Generate access token (30 min expiration)
access_token = create_access_token(
    data={"sub": "user123"},
    scopes=["read", "write"]
)

# Generate refresh token (7 day expiration)
refresh_token = create_refresh_token(data={"sub": "user123"})
```

### Token Verification

```python
from app.core.security import decode_token, validate_jwt_claims

# Verify token
payload = decode_token(token, token_type="access")

if payload:
    user_id = payload["sub"]
    is_valid = validate_jwt_claims(payload)
```

### Token Payload

```json
{
  "sub": "user123",
  "exp": 1715900000,
  "iat": 1715898000,
  "type": "access",
  "scopes": ["read", "write"]
}
```

---

## 🔑 Password Security

### Hashing & Verification

```python
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength
)

# Hash password
hashed = get_password_hash("SecurePassword123!")

# Verify password
is_correct = verify_password("SecurePassword123!", hashed)

# Validate strength
is_strong, msg = validate_password_strength("password123")
# Returns: (False, "Password must be at least 12 characters long")
```

### Password Requirements

- ✅ Minimum 12 characters
- ✅ At least 1 uppercase letter (A-Z)
- ✅ At least 1 lowercase letter (a-z)
- ✅ At least 1 digit (0-9)
- ✅ At least 1 special character (!@#$%^&*)

### Hashing Algorithm

- **Algorithm:** BCrypt
- **Cost Factor:** Auto-configured (secure, slow on purpose)
- **Salting:** Automatic with each hash

---

## 🔑 API Key Management

### Generate API Key

```python
from app.core.security import generate_api_key, hash_api_key

# Generate secure key
api_key = generate_api_key()  # Returns: "...secure-random-string..."

# Hash for storage in database
api_key_hash = hash_api_key(api_key)

# User gets: api_key
# Database stores: api_key_hash
```

### Validate API Key

```python
from app.core.security import validate_api_key

# User provides key
user_key = "...api-key..."

# Check against database hash
if validate_api_key(user_key, db.api_key_hash):
    # Valid API key
    pass
```

---

## 🚦 Rate Limiting

### Configuration

**Default:** 100 requests per 60 seconds per IP address

**Location:** `backend/app/main.py`

### Applying to Endpoints

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/detect/image")
@limiter.limit("10/minute")
async def detect_image(file: UploadFile):
    # Endpoint limited to 10 requests per minute
    pass

@app.post("/api/detect/video")
@limiter.limit("5/minute")
async def detect_video(file: UploadFile):
    # Heavy operation - 5 requests per minute
    pass

@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check():
    # Allow more frequent health checks
    pass
```

### Rate Limit Response

```json
HTTP 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## 🔒 Data Protection

### Input Sanitization

```python
from app.core.security import sanitize_input

# Sanitize user input
user_input = sanitize_input(filename, max_length=255)

# Removes:
# - Null bytes (\x00)
# - Control characters
# - Truncates to max_length
```

### Email Validation

```python
from app.core.security import validate_email

if validate_email("user@example.com"):
    # Valid email
    pass
```

### Username Validation

```python
from app.core.security import validate_username

is_valid, error_msg = validate_username("john_doe")
# Valid if: 3-32 chars, alphanumeric + underscore, starts with letter
```

### SQL Injection Prevention

```python
# ✅ GOOD: Using SQLAlchemy ORM
from sqlalchemy import select

stmt = select(User).where(User.email == user_email)
result = session.execute(stmt).first()

# ❌ BAD: Never concatenate user input
stmt = f"SELECT * FROM users WHERE email = '{user_email}'"
```

---

## 🛡️ Security Headers

### Headers Implemented

All HTTP responses include these security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking attacks |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS protection filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Disable APIs |
| `Content-Security-Policy` | Restrictive policy | Control resource loading |
| `Strict-Transport-Security` | `max-age=31536000` | Force HTTPS (production only) |

### CSP Policy

```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self';
connect-src 'self' https:;
frame-ancestors 'none'
```

### Automatic Application

Headers are automatically added to all responses via middleware.

---

## 🌐 CORS Configuration

### Allowed Methods

- GET
- POST
- PUT
- DELETE
- OPTIONS

### Allowed Headers

- Content-Type
- Authorization
- Accept
- Origin

### Configuration

```env
# .env file
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Environment-Based

```python
# Development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Production
ALLOWED_ORIGINS=https://app.yourdomain.com
```

---

## 🏗️ Infrastructure Security

### Docker Security

**Non-Root User:**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**Read-Only Filesystem:**
```yaml
read_only_rootfs: true
tmpfs:
  - /tmp
  - /run
```

**Resource Limits:**
```yaml
resources:
  limits:
    cpus: '2'
    memory: 4G
  reservations:
    cpus: '1'
    memory: 2G
```

### Database Security

**Connection Pooling:**
- Pool Size: 10
- Max Overflow: 20
- Pool Recycle: 3600 seconds (1 hour)
- Pre-ping: Enabled (detects stale connections)

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

---

## 🔄 Environment Configuration

### Environment Variables

```bash
# Security
SECRET_KEY=generated-secure-key
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### No Hardcoded Secrets

- ✅ All credentials from environment variables
- ✅ No secrets in version control
- ✅ .env files in .gitignore
- ✅ Production uses secure secret management

---

## 🧪 Testing Security

### Automated Tests

```bash
python test_security_headers.py
```

**Checks:**
- ✅ All security headers present
- ✅ Correct header values
- ✅ CORS configuration
- ✅ Endpoint security
- ✅ Documentation disabled in production

### Manual Testing

**Check Headers:**
```bash
curl -i http://localhost:8000/api/health | grep -E "X-|Strict|CSP"
```

**Test Rate Limiting:**
```bash
# Send 101 requests quickly
for i in {1..101}; do curl http://localhost:8000/api/health; done
# Last request should return 429
```

**Test CORS:**
```bash
curl -H "Origin: https://example.com" \
  -i http://localhost:8000/api/health
```

---

## 📋 Security Checklist

### Before Production Deployment

- [ ] Generate strong SECRET_KEY
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=false
- [ ] Configure ALLOWED_ORIGINS
- [ ] Update DATABASE_URL
- [ ] Set up SSL/TLS certificate
- [ ] Configure reverse proxy (Nginx)
- [ ] Enable rate limiting
- [ ] Enable access logging
- [ ] Set up monitoring/alerting
- [ ] Run security tests
- [ ] Review security headers
- [ ] Database backups configured
- [ ] Disaster recovery plan ready

---

## 🚨 Security Incident Response

### If Compromised

1. **Revoke all tokens immediately**
   ```python
   # Invalidate all active tokens
   # (Implementation specific to your token storage)
   ```

2. **Rotate SECRET_KEY**
   ```bash
   # Generate new key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # Deploy with new key
   ```

3. **Rotate database credentials**

4. **Review access logs for suspicious activity**

5. **Audit all API access logs**

---

## 📚 Related Documentation

- [SECURITY_POLICY.md](./SECURITY_POLICY.md) - Comprehensive policy
- [SECURITY_QUICK_START.md](./SECURITY_QUICK_START.md) - Quick reference
- [.env.example](./.env.example) - Configuration template

---

## 🔗 External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)

---

**Security Status:** ✅ **Production Ready**  
**Last Updated:** May 16, 2026

