"""User authentication and management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
)
from app.crud import create_user, get_user_by_email, get_user_by_id, update_user
from app.database import get_db
from app.models import User
from app.schemas import (
    AuthResponse,
    Token,
    UserCreate,
    UserInDB,
    UserLogin,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user account.

    Creates a new user with the provided email, username, and password.
    Automatically hashes the password and returns the user data with an
    authentication token.

    Args:
        user_in: User registration data including email, username, and password.
        db: Database session dependency.

    Returns:
        AuthResponse containing the new user data and JWT access token.

    Raises:
        HTTPException: 400 error if email or username is already taken.

    Example:
        POST /api/users/register
        {
            "email": "user@example.com",
            "username": "john_doe",
            "password": "securepass123"
        }
    """
    # Check if email already exists
    if await get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username already exists
    if await get_user_by_id(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Create user
    user = await create_user(db, user_in)
    
    # Generate token
    access_token = create_access_token(user.id)
    
    return AuthResponse(
        user=UserInDB.model_validate(user),
        token=Token(access_token=access_token),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Authenticate a user and return access token.

    Validates user credentials (email and password) and returns a JWT
    access token for authenticated requests.

    Args:
        credentials: User login credentials containing email and password.
        db: Database session dependency.

    Returns:
        AuthResponse containing the user data and JWT access token.

    Raises:
        HTTPException: 401 error if credentials are invalid.
    """
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user.id)
    
    return AuthResponse(
        user=UserInDB.model_validate(user),
        token=Token(access_token=access_token),
    )


@router.get("/me", response_model=UserInDB)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserInDB:
    """Get the current authenticated user's full profile.

    Requires a valid JWT token in the Authorization header.

    Args:
        current_user: The authenticated user from JWT token.

    Returns:
        UserInDB containing the complete user profile information.

    Raises:
        HTTPException: 401 error if token is missing or invalid.
    """
    return UserInDB.model_validate(current_user)


@router.put("/me", response_model=UserInDB)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserInDB:
    """Update the current authenticated user's profile.

    Allows users to update their email, full name, and bio.
    Requires a valid JWT token.

    Args:
        user_in: User update data with fields to modify.
        current_user: The authenticated user from JWT token.
        db: Database session dependency.

    Returns:
        UserInDB containing the updated user profile.

    Raises:
        HTTPException: 400 error if new email is already taken.
    """
    # Check if new email is already taken
    if user_in.email and user_in.email != current_user.email:
        if await get_user_by_email(db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    updated_user = await update_user(db, current_user, user_in)
    return UserInDB.model_validate(updated_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get a user's public profile by ID.

    Returns publicly visible user information. Does not require authentication.

    Args:
        user_id: The unique identifier of the user to retrieve.
        db: Database session dependency.

    Returns:
        UserResponse containing public user information.

    Raises:
        HTTPException: 404 error if user is not found or inactive.
    """
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)
