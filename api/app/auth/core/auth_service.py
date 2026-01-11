import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.users.infra.user_model import User
from app.users.infra.user_repository import UserRepository
from app.auth.infra.token_repository import TokenRepository
from app.auth.infra.token_model import Token

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-minimum-32-characters")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthService:
    """Business logic for authentication. No direct database access."""

    def __init__(self, user_repository: UserRepository = None, token_repository: TokenRepository = None):
        self.user_repository = user_repository
        self.token_repository = token_repository

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify if password matches hash using bcrypt."""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        if not self.user_repository:
            raise ValueError("UserRepository is required for authentication")

        user = self.user_repository.find_by_email(email)
        if not user or not user.hashed_password:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        if not self.user_repository:
            raise ValueError("UserRepository is required")
        return self.user_repository.find_by_email(email)

    def get_user_by_uuid(self, user_uuid: str) -> Optional[User]:
        """Get user by UUID."""
        if not self.user_repository:
            raise ValueError("UserRepository is required")
        from uuid import UUID as UUIDType
        return self.user_repository.find_by_uuid(UUIDType(user_uuid))

    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        if not self.user_repository:
            raise ValueError("UserRepository is required")
        return self.user_repository.find_by_google_id(google_id)

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Generate hash of token for secure storage."""
        return bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_token_hash(token: str, token_hash: str) -> bool:
        """Verify if token matches hash."""
        try:
            return bcrypt.checkpw(token.encode('utf-8'), token_hash.encode('utf-8'))
        except Exception:
            return False

    def get_token_by_hash(self, plain_token: str) -> Optional[Token]:
        """Find token by plain token (used for validation)."""
        if not self.token_repository:
            raise ValueError("TokenRepository is required")

        tokens = self.token_repository.find_active_tokens()
        for token in tokens:
            if self.verify_token_hash(plain_token, token.token_hash):
                self.token_repository.update_last_used(token)
                return token
        return None
