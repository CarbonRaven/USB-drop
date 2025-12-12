"""Authentication service."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import logging

from app.config import get_settings
from app.database import SessionLocal
from app.models.user import User, APIKey

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key. Returns (key, hash)."""
    key = f"usbdrop_{secrets.token_urlsafe(32)}"
    key_hash = get_password_hash(key)
    return key, key_hash


def verify_api_key(db: Session, api_key: str) -> Optional[User]:
    """Verify an API key and return the associated user."""
    # Get all active API keys and check each
    api_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    for key_record in api_keys:
        if verify_password(api_key, key_record.key_hash):
            # Update last used
            key_record.last_used = datetime.utcnow()
            db.commit()
            return key_record.user
    return None


def create_initial_admin():
    """Create initial admin user if not exists."""
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == settings.admin_username).first()
        if admin:
            logger.info(f"Admin user '{settings.admin_username}' already exists")
            return

        # Create admin user
        admin = User(
            username=settings.admin_username,
            email=settings.admin_email,
            password_hash=get_password_hash(settings.admin_password),
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        logger.info(f"Created initial admin user: {settings.admin_username}")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()
