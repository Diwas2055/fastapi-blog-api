"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============== User Schemas ==============

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None


class UserInDB(UserBase):
    """Schema for user as stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserResponse(UserBase):
    """Schema for user response (public view)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


# ============== Tag Schemas ==============

class TagBase(BaseModel):
    """Base tag schema."""
    name: str = Field(..., min_length=1, max_length=50)


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


class TagInDB(TagBase):
    """Schema for tag as stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


# ============== Comment Schemas ==============

class CommentBase(BaseModel):
    """Base comment schema."""
    body: str = Field(..., min_length=1, max_length=5000)


class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    pass


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    body: str = Field(..., min_length=1, max_length=5000)


class CommentInDB(CommentBase):
    """Schema for comment as stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    article_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    author: UserResponse


# ============== Article Schemas ==============

class ArticleBase(BaseModel):
    """Base article schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)


class ArticleCreate(ArticleBase):
    """Schema for creating a new article."""
    tag_list: List[str] = Field(default_factory=list)
    published: bool = False
    
    @field_validator("tag_list")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        return [tag.lower().strip() for tag in v if tag.strip()]


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = Field(None, min_length=1)
    tag_list: Optional[List[str]] = None
    published: Optional[bool] = None


class ArticleInDB(ArticleBase):
    """Schema for article as stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    published: bool
    views_count: int
    author: UserResponse
    tags: List[TagInDB]
    comments_count: int = 0
    
    @field_validator("comments_count", mode="before")
    @classmethod
    def count_comments(cls, v, info) -> int:
        """Count comments from the article object."""
        if hasattr(info.data.get("comments", []), "__len__"):
            return len(info.data.get("comments", []))
        return 0


class ArticleResponse(ArticleInDB):
    """Schema for article response with full details."""
    comments: List[CommentInDB] = []


class ArticleListResponse(BaseModel):
    """Schema for paginated article list response."""
    articles: List[ArticleInDB]
    total: int
    skip: int
    limit: int


# ============== Authentication Schemas ==============

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: Optional[int] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserRegister(UserCreate):
    """Schema for user registration."""
    pass


class AuthResponse(BaseModel):
    """Schema for authentication response with user and token."""
    user: UserInDB
    token: Token
