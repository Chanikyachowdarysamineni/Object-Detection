# 🔒 Security Implementation Guide

**Current Security Level:** 🟢 **Enterprise-Grade**

This document provides a quick reference for the security features implemented in this application.

---

## 🚀 Quick Start - Security Setup

### 1. Install Security Dependencies

```bash
pip install -r requirements.txt
# Includes: passlib, cryptography, slowapi, etc.
```

### 2. Generate Production Secrets

```bash
# Run security setup script
bash setup-security.sh

# Or manually generate:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Configure Environment Variables

```bash
# Copy template
cp .env.example .env.production

# Edit with secure values
ENVIRONMENT=production
SECRET_KEY=<generated-key>
ALLOWED_ORIGINS=https://your-domain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### 4. Verify Security Headers

```bash
# Start the application
python -m uvicorn app.main:app --reload

# In another terminal, run security check
pip install requests colorama
python test_security_headers.py
```

---

## 🔐 Security Features

### Authentication & Authorization

#### JWT Tokens
- **Access Token:** 30 minutes expiration
- **Refresh Token:** 7 days expiration
- **Payload:** Contains user ID, expiration, token type, scopes

```python
from app.core.security import create_access_token, decode_token

# Create token
token = create_access_token({"sub": "user123"}, scopes=["read", "write"])

# Verify token
payload = decode_token(token)
```

#### Password Security
- **Algorithm:** BCrypt (secure, slow on purpose)
- **Requirements:**
  - Minimum 12 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character

```python
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength
)

# Hash password
hashed = get_password_hash("SecurePassword123!")

# Verify password
if verify_password("SecurePassword123!", hashed):
    print("✅ Password matches")

# Validate strength
is_strong, message = validate_password_strength("password123")
```

#### API Key Management
```python
from app.core.security import generate_api_key, hash_api_key, validate_api_key

# Generate key
api_key = generate_api_key()  # Store this for user

# Hash for database
api_key_hash = hash_api_key(api_key)  # Store this

# Verify later
if validate_api_key(provided_key, stored_hash):
    # Valid API key
    pass
```

### Rate Limiting

**Configuration:** 100 requests per 60 seconds per IP

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/detect/image")
@limiter.limit("10/minute")
async def detect_image(file: UploadFile):
    # Endpoint with rate limiting
    pass
```

### Data Protection

#### Input Validation & Sanitization
```python
from app.core.security import (
    sanitize_input,
    validate_email,
    validate_username
)

# Sanitize user input
clean_input = sanitize_input(user_input, max_length=255)

# Validate email
if validate_email(email):
    # Valid email
    pass

# Validate username
is_valid, message = validate_username(username)
```

#### SQL Injection Prevention
- Uses SQLAlchemy ORM (parameterized queries)
- All user inputs validated before database queries
- No string concatenation in SQL

```python
# ✅ GOOD: Using ORM
user = db.query(User).filter(User.name == user_input).first()

# ❌ BAD: String concatenation (NEVER!)
query = f"SELECT * FROM users WHERE name = '{user_input}'"
```

#### CORS Configuration
- **Allowed Methods:** GET, POST, PUT, DELETE, OPTIONS
- **Allowed Headers:** Content-Type, Authorization, Accept, Origin
- **Allowed Origins:** Configured via environment variable

```env
ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
```

### Infrastructure Security

#### Docker Security
- **Non-root user:** Application runs as `appuser:1000`
- **Read-only filesystem:** Root filesystem is read-only
- **Resource limits:** 2 CPUs / 4GB RAM (max), 1 CPU / 2GB RAM (reserved)
- **Health checks:** Enabled for orchestration

#### Database Security
- **Connection pooling:** 10 connections with automatic recycling
- **Pre-ping:** Detects stale connections
- **Credentials:** From environment variables only
- **Timeout:** Automatic connection reset after 1 hour

### Security Headers

All responses include security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Referrer-Policy` | `strict-origin` | Control referrer |
| `Permissions-Policy` | `geolocation=()` | Disable APIs |
| `Content-Security-Policy` | Restrictive | Control resource loading |
| `Strict-Transport-Security` | 1 year (prod only) | Force HTTPS |

### Error Handling

- **Development:** Detailed error messages and stack traces
- **Production:** Generic error messages, detailed logging server-side
- **No data leakage:** Internal system details never exposed to clients

```python
# In production, error responses look like:
{
  "detail": "Internal server error"
}

# In development, full details are provided for debugging
```

---

## 🧪 Testing Security

### Run Security Header Tests

```bash
python test_security_headers.py
```

This checks:
- All expected security headers present
- Correct header values
- CORS configuration
- Endpoint security
- Documentation disabled in production

### Manual Testing

**Check security headers:**
```bash
curl -i http://localhost:8000/api/health | grep -E "X-|Strict|CSP|Referrer|Permissions"
```

**Test rate limiting:**
```bash
for i in {1..101}; do curl http://localhost:8000/api/health; done
# Last request should get 429 Too Many Requests
```

**Test CORS:**
```bash
curl -i -H "Origin: https://example.com" http://localhost:8000/api/health
```

---

## 📋 Deployment Checklist

### Pre-Production

- [ ] ✅ Generate `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] ✅ Set `ENVIRONMENT=production`
- [ ] ✅ Set `DEBUG=false`
- [ ] ✅ Configure `ALLOWED_ORIGINS` with production domain
- [ ] ✅ Update `DATABASE_URL` with production database
- [ ] ✅ Generate database password
- [ ] ✅ Configure SSL/TLS certificates
- [ ] ✅ Set up reverse proxy (Nginx)
- [ ] ✅ Configure rate limiting rules
- [ ] ✅ Enable request logging
- [ ] ✅ Set up monitoring/alerting
- [ ] ✅ Run security tests

### Production

- [ ] ✅ Use .env.production (never in git!)
- [ ] ✅ HTTPS only (port 443)
- [ ] ✅ Security headers validated
- [ ] ✅ Rate limiting active
- [ ] ✅ Monitoring configured
- [ ] ✅ Alerts configured
- [ ] ✅ Backups automated
- [ ] ✅ Access logs enabled

---

## 🔄 Updates & Maintenance

### Check for Vulnerabilities

```bash
# Install safety checker
pip install safety

# Check requirements
safety check -r requirements.txt

# Fix vulnerabilities
pip install --upgrade -r requirements.txt
```

### Security Audit Log

Check application logs for security events:

```bash
# Failed login attempts
grep "Invalid" logs/*.log

# Rate limit violations
grep "Rate limit" logs/*.log

# Token verification failures
grep "Invalid token" logs/*.log
```

---

## 🚨 Security Issues

### Report Security Vulnerability

**DO NOT** report security issues publicly!

1. Email: security@yourdomain.com
2. Include: Description, steps to reproduce, impact
3. Wait: 48 hours for response before public disclosure

---

## 📚 Resources

- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **JWT Best Practices:** https://tools.ietf.org/html/rfc8725
- **Passlib Documentation:** https://passlib.readthedocs.io/

---

## ✅ Security Status

**Last Updated:** May 16, 2026  
**Next Audit:** June 16, 2026  
**Status:** 🟢 **Production Ready**

All security measures implemented and tested.

