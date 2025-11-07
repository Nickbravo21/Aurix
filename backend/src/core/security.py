"""
Security utilities: JWT validation, OAuth token encryption, password hashing.
"""
import base64
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# OAuth token encryption
class TokenEncryption:
    """Encrypt and decrypt OAuth tokens using Fernet symmetric encryption."""
    
    def __init__(self, key: str | None = None) -> None:
        """Initialize with encryption key from settings."""
        key_bytes = (key or settings.encryption_key).encode()
        # Ensure key is properly formatted for Fernet
        if len(key_bytes) != 44 or not key_bytes.endswith(b"="):
            # Generate from settings if not a valid Fernet key
            key_bytes = base64.urlsafe_b64encode(key_bytes[:32].ljust(32, b"0"))
        self.cipher = Fernet(key_bytes)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self.cipher.decrypt(ciphertext.encode()).decode()


token_encryption = TokenEncryption()


# JWT handling
def create_access_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (usually user ID)
        expires_delta: Optional expiration time delta
        additional_claims: Additional claims to include
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.supabase_service_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_public_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_supabase_jwt(token: str) -> dict[str, Any]:
    """
    Verify a Supabase JWT token.
    
    Args:
        token: JWT token from Supabase auth
        
    Returns:
        Decoded payload with user info
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_public_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},  # Supabase doesn't use aud claim
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid Supabase token: {e}") from e
