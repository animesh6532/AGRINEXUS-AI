"""
Authentication API Endpoints for AgriNexus-AI.
Handles registration, authentication, session validation, and current user retrieval.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...core.logging import logger
from ...core.security import create_access_token, decode_access_token, hash_password, verify_password
from ...database.models import FarmActivityEvent, FarmerProfile, User
from ...schemas.auth import AuthTokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that resolves the authenticated User model from JWT Bearer Token,
    or falls back cleanly to X-User-ID header / legacy identity for backwards compatibility.
    """
    user: Optional[User] = None

    # 1. Attempt resolution via Bearer JWT token
    if auth_credentials and auth_credentials.credentials:
        payload = decode_access_token(auth_credentials.credentials)
        if payload and payload.get("sub"):
            user_id = payload["sub"]
            user = db.query(User).filter(User.id == user_id).first()

    # 2. Fallback resolution via X-User-ID header (email or string ID)
    if not user and x_user_id and x_user_id.strip():
        raw_id = x_user_id.strip()
        # Check if user exists by ID or Email
        user = db.query(User).filter((User.id == raw_id) | (User.email == raw_id.lower())).first()
        if not user:
            # Auto-provision stable User entity for legacy frontend header if needed
            email = raw_id if "@" in raw_id else f"{raw_id}@agrinexus.ai"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    id=raw_id if len(raw_id) <= 36 else str(uuid.uuid4()),
                    email=email.lower(),
                    password_hash=hash_password("defaultpassword123"),
                    full_name=raw_id.replace("_", " ").title() if "_" in raw_id else "Farmer User",
                )
                db.add(user)
                db.commit()
                db.refresh(user)

    # 3. Final default fallback for unauthenticated development queries
    if not user:
        user = db.query(User).filter(User.email == "farmer@agrinexus.ai").first()
        if not user:
            user = User(
                id="default_user_id",
                email="farmer@agrinexus.ai",
                password_hash=hash_password("password123"),
                full_name="Default Farmer",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # Ensure associated FarmerProfile exists for resolved User
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user.id).first()
    if not profile:
        profile = FarmerProfile(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            preferred_language="en",
        )
        db.add(profile)
        db.commit()

    return user


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user, create permanent User & FarmerProfile records,
    and issue an authenticated JWT access token.
    """
    email_lower = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email_lower).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead.",
        )

    # Create permanent User identity
    user = User(
        id=str(uuid.uuid4()),
        email=email_lower,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.flush()

    # Create associated FarmerProfile
    profile = FarmerProfile(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=payload.phone,
        preferred_language=payload.preferred_language,
    )
    db.add(profile)

    # Create activity event
    event = FarmActivityEvent(
        user_id=user.id,
        event_type="USER_REGISTERED",
        title="Account Created",
        description=f"Account registered for {user.full_name} ({user.email}).",
    )
    db.add(event)

    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(),
        "farmer_profile": profile.to_dict(),
    }


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user credentials against permanent database records,
    issue a JWT token, and return profile metadata.
    """
    email_lower = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_lower).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
        )

    # Ensure profile exists
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user.id).first()
    if not profile:
        profile = FarmerProfile(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            preferred_language="en",
        )
        db.add(profile)
        db.commit()

    # Log login activity event
    login_event = FarmActivityEvent(
        user_id=user.id,
        event_type="USER_LOGGED_IN",
        title="User Login",
        description=f"User {user.full_name} authenticated successfully.",
    )
    db.add(login_event)
    db.commit()

    access_token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(),
        "farmer_profile": profile.to_dict(),
    }


@router.get("/me")
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve authenticated user and farmer profile from backend database.
    """
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user.id).first()
    return {
        "user": user.to_dict(),
        "farmer_profile": profile.to_dict() if profile else None,
    }
