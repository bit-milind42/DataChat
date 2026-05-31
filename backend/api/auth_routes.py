"""Authentication routes for user management"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from passlib.context import CryptContext

from databases.models import get_db
from databases.collaboration_models import User
from api.schemas import UserCreate

router = APIRouter(prefix="/api", tags=["auth"])

# Password hashing
# Use pbkdf2_sha256 to avoid bcrypt backend issues in this environment.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return pwd_context.verify(plain_password, hashed_password)


@router.post("/auth/signup")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account"""
    try:
        # Validate password
        if not user.password or len(user.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        if len(user.password) > 72:
            raise HTTPException(status_code=400, detail="Password must be less than 72 characters")
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        new_user = User(
            id=str(uuid.uuid4()),
            email=user.email,
            name=user.name or user.email.split('@')[0],
            hashed_password=hash_password(user.password),
            is_active=True,
            role="user"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "data": {
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "name": new_user.name,
                    "role": new_user.role,
                    "created_at": new_user.created_at.isoformat()
                },
                "token": None  # JWT token can be added here if needed
            },
            "message": "User created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/auth/login")
async def login(user_login: UserCreate, db: Session = Depends(get_db)):
    """Authenticate user and return user info"""
    try:
        # Validate password
        if not user_login.password or len(user_login.password) > 72:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = db.query(User).filter(User.email == user_login.email).first()
        
        if not user or not verify_password(user_login.password, user.hashed_password or ""):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")
        
        return {
            "success": True,
            "data": {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "created_at": user.created_at.isoformat()
                },
                "token": None  # JWT token can be added here if needed
            },
            "message": "Login successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/auth/user/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user details"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "created_at": user.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
