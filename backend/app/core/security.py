"""
Comprehensive security utilities for authentication, authorization, and cryptographic operations.

Features:
- Password hashing with bcrypt
- JWT token generation and verification
- API key management
- Input sanitization
- Security token generation
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from .config import settings
import logging
import secrets
import hashlib
import re

logger = logging.getLogger(__name__)

# Password hashing context - bcrypt with automatic migration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# PASSWORD SECURITY
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed version.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: BCrypt hash to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        if not is_valid:
            logger.warning("⚠️  Invalid password attempt")
        return is_valid
    except Exception as e:
        logger.error(f"❌ Error verifying password: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    Generate bcrypt hash for a password.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hash of password
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength requirements.
    
    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


# ============================================================================
# JWT TOKEN SECURITY
# ============================================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    scopes: list = None
) -> str:
    """
    Create JWT access token with security claims.
    
    Args:
        data: Token payload (should contain 'sub' for user identifier)
        expires_delta: Custom expiration time
        scopes: List of permission scopes
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    scopes = scopes or []
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "scopes": scopes
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        logger.debug(f"✅ Access token created for: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"❌ Error creating access token: {str(e)}")
        raise


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token with extended expiration.
    
    Args:
        data: Token payload
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        logger.debug(f"✅ Refresh token created for: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"❌ Error creating refresh token: {str(e)}")
        raise


def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Decode and verify JWT token with type validation.
    
    Args:
        token: JWT token to decode
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        # Validate token type
        if payload.get("type") != token_type:
            logger.warning(f"⚠️  Invalid token type: expected {token_type}")
            return None
        
        logger.debug(f"✅ Token verified for: {payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("⚠️  Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"⚠️  Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Error decoding token: {str(e)}")
        return None


def validate_jwt_claims(payload: dict) -> bool:
    """
    Validate JWT token claims and expiration.
    
    Args:
        payload: Decoded JWT payload
        
    Returns:
        True if all claims are valid
    """
    required_claims = {"sub", "exp", "iat"}
    
    if not all(claim in payload for claim in required_claims):
        logger.warning("⚠️  Missing required JWT claims")
        return False
    
    # Check expiration
    try:
        if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            logger.warning("⚠️  Token has expired")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating token expiration: {str(e)}")
        return False
    
    return True


# ============================================================================
# API KEY SECURITY
# ============================================================================

def generate_api_key(length: int = 32) -> str:
    """
    Generate cryptographically secure API key.
    
    Args:
        length: Length of key to generate
        
    Returns:
        Random secure API key
    """
    return secrets.token_urlsafe(length)


def hash_api_key(api_key: str) -> str:
    """
    Hash API key using SHA-256.
    
    Args:
        api_key: API key to hash
        
    Returns:
        SHA-256 hash of API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key(api_key: str, stored_hash: str) -> bool:
    """
    Validate API key against stored hash.
    
    Args:
        api_key: API key to validate
        stored_hash: Stored SHA-256 hash
        
    Returns:
        True if API key matches hash
    """
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key_hash == stored_hash


# ============================================================================
# INPUT SECURITY
# ============================================================================

def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return ""
    
    # Truncate to max length
    sanitized = input_string[:max_length]
    
    # Remove null bytes (SQL injection prevention)
    sanitized = sanitized.replace("\x00", "")
    
    # Remove control characters except newlines, tabs
    sanitized = "".join(
        char for char in sanitized
        if ord(char) >= 32 or char in "\n\r\t"
    )
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format and length.
    
    Requirements:
    - 3-32 characters
    - Alphanumeric and underscore only
    - Must start with letter
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not 3 <= len(username) <= 32:
        return False, "Username must be 3-32 characters"
    
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", username):
        return False, "Username must start with letter, use only alphanumeric and underscore"
    
    return True, "Username is valid"


# ============================================================================
# SECURITY TOKEN GENERATION
# ============================================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    
    Args:
        length: Token length
        
    Returns:
        Secure random token
    """
    return secrets.token_urlsafe(length)


def generate_confirmation_token() -> str:
    """Generate token for email confirmation or password reset."""
    return secrets.token_urlsafe(32)


def generate_mfa_code() -> str:
    """Generate 6-digit code for multi-factor authentication."""
    return str(secrets.randbelow(1000000)).zfill(6)
