import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
from google.auth.transport import requests
from google.oauth2 import id_token

from ..models import User, UserRole, SubscriptionTier
from ...monitoring.logger import logger


class AuthManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256", use_firebase: bool = False):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()
        self.firebase_app = None
        self.use_firebase = use_firebase
        
        if self.use_firebase:
            self._init_firebase()

    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                # Try to initialize with service account key if available
                service_key_path = "serviceAccountKey.json"
                if os.path.exists(service_key_path):
                    cred = credentials.Certificate(service_key_path)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with service account key")
                else:
                    # Initialize without credentials for development
                    logger.warning("Firebase service account key not found, initializing without credentials")
                    self.firebase_app = None
            else:
                self.firebase_app = firebase_admin.get_app()
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.firebase_app = None

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_access_token(self, user: User, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "subscription_tier": user.subscription_tier.value,
            "exp": expire
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def verify_google_token(self, token: str) -> Dict[str, Any]:
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request())
            return idinfo
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )

    def verify_firebase_token(self, token: str) -> Dict[str, Any]:
        try:
            if self.firebase_app is None:
                logger.warning("Firebase not initialized, skipping token verification")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Firebase authentication not available"
                )
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )

    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        token = credentials.credentials
        return self.verify_token(token)

    def check_permission(self, user: Dict[str, Any], required_role: UserRole) -> bool:
        user_role = UserRole(user.get("role"))
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.ANALYST: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

    def require_role(self, required_role: UserRole):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not self.check_permission(current_user, required_role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def check_subscription_tier(self, user: Dict[str, Any], required_tier: SubscriptionTier) -> bool:
        user_tier = SubscriptionTier(user.get("subscription_tier"))
        tier_hierarchy = {
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.ADVANCED: 2,
            SubscriptionTier.ENTERPRISE: 3
        }
        return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)

    def require_subscription(self, required_tier: SubscriptionTier):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not self.check_subscription_tier(current_user, required_tier):
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail="Upgrade subscription required"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator