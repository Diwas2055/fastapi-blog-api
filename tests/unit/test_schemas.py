"""Unit tests for Pydantic data validation schemas.

This module tests all Pydantic models used for request/response validation:
- User schemas (create, update, response, login)
- Article schemas (create, update, response)
- Comment schemas (create, update)
- Tag schemas (create, response)
- Authentication schemas

Tests cover valid data scenarios, validation errors, and edge cases.
"""
import pytest
from pydantic import ValidationError

from app.schemas import (
    ArticleCreate,
    ArticleUpdate,
    CommentCreate,
    TagCreate,
    UserCreate,
    UserLogin,
    UserUpdate,
)


class TestUserCreateSchema:
    """Test suite for UserCreate schema validation.

    Tests user registration data validation including:
    - Valid user data acceptance
    - Optional fields handling
    - Email format validation
    - Password length requirements
    - Username length constraints
    """

    @pytest.mark.unit
    def test_valid_user_create(self):
        """Test creating user with valid data."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        }
        user = UserCreate(**data)
        
        assert user.email == data["email"]
        assert user.username == data["username"]
        assert user.password == data["password"]

    @pytest.mark.unit
    def test_user_create_with_optional_fields(self):
        """Test creating user with all optional fields."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
            "full_name": "Test User",
            "bio": "A test bio",
        }
        user = UserCreate(**data)
        
        assert user.full_name == data["full_name"]
        assert user.bio == data["bio"]

    @pytest.mark.unit
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="securepass123",
            )
        
        assert "email" in str(exc_info.value)

    @pytest.mark.unit
    def test_user_create_short_password(self):
        """Test user creation with short password fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",
            )
        
        assert "password" in str(exc_info.value)

    @pytest.mark.unit
    def test_user_create_short_username(self):
        """Test user creation with short username fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="ab",
                password="securepass123",
            )
        
        assert "username" in str(exc_info.value)


class TestUserUpdateSchema:
    """Test UserUpdate schema validation."""

    @pytest.mark.unit
    def test_valid_user_update(self):
        """Test updating user with valid data."""
        data = {
            "email": "new@example.com",
            "full_name": "New Name",
            "bio": "New bio",
        }
        update = UserUpdate(**data)
        
        assert update.email == data["email"]
        assert update.full_name == data["full_name"]
        assert update.bio == data["bio"]

    @pytest.mark.unit
    def test_user_update_partial(self):
        """Test partial user update."""
        data = {"bio": "Updated bio"}
        update = UserUpdate(**data)
        
        assert update.bio == data["bio"]
        assert update.email is None
        assert update.full_name is None

    @pytest.mark.unit
    def test_user_update_empty(self):
        """Test empty user update."""
        update = UserUpdate()
        
        assert update.email is None
        assert update.full_name is None
        assert update.bio is None


class TestArticleCreateSchema:
    """Test ArticleCreate schema validation."""

    @pytest.mark.unit
    def test_valid_article_create(self):
        """Test creating article with valid data."""
        data = {
            "title": "Test Article",
            "description": "A test description",
            "body": "This is the article body with enough content.",
            "tag_list": ["python", "fastapi"],
            "published": True,
        }
        article = ArticleCreate(**data)
        
        assert article.title == data["title"]
        assert article.description == data["description"]
        assert article.body == data["body"]
        assert article.tag_list == ["python", "fastapi"]  # normalized
        assert article.published is True

    @pytest.mark.unit
    def test_article_create_tag_normalization(self):
        """Test tag normalization in article creation."""
        data = {
            "title": "Test",
            "description": "Test description",
            "body": "Test body",
            "tag_list": ["PYTHON", "  fastapi  ", "", "web"],
        }
        article = ArticleCreate(**data)
        
        assert "python" in article.tag_list
        assert "fastapi" in article.tag_list
        assert "web" in article.tag_list
        assert "" not in article.tag_list

    @pytest.mark.unit
    def test_article_create_empty_title_fails(self):
        """Test article creation with empty title fails."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleCreate(
                title="",
                description="Description",
                body="Body content",
            )
        
        assert "title" in str(exc_info.value)

    @pytest.mark.unit
    def test_article_create_long_description_fails(self):
        """Test article creation with too long description fails."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleCreate(
                title="Test",
                description="a" * 501,
                body="Body content",
            )
        
        assert "description" in str(exc_info.value)


class TestArticleUpdateSchema:
    """Test ArticleUpdate schema validation."""

    @pytest.mark.unit
    def test_valid_article_update(self):
        """Test updating article with valid data."""
        data = {
            "title": "Updated Title",
            "published": True,
        }
        update = ArticleUpdate(**data)
        
        assert update.title == data["title"]
        assert update.published is True
        assert update.description is None

    @pytest.mark.unit
    def test_article_update_empty(self):
        """Test empty article update."""
        update = ArticleUpdate()
        
        assert update.title is None
        assert update.published is None


class TestCommentCreateSchema:
    """Test CommentCreate schema validation."""

    @pytest.mark.unit
    def test_valid_comment_create(self):
        """Test creating comment with valid data."""
        data = {"body": "This is a test comment."}
        comment = CommentCreate(**data)
        
        assert comment.body == data["body"]

    @pytest.mark.unit
    def test_comment_create_empty_body_fails(self):
        """Test comment creation with empty body fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommentCreate(body="")
        
        assert "body" in str(exc_info.value)

    @pytest.mark.unit
    def test_comment_create_long_body_fails(self):
        """Test comment creation with too long body fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommentCreate(body="a" * 5001)
        
        assert "body" in str(exc_info.value)


class TestTagCreateSchema:
    """Test TagCreate schema validation."""

    @pytest.mark.unit
    def test_valid_tag_create(self):
        """Test creating tag with valid data."""
        data = {"name": "python"}
        tag = TagCreate(**data)
        
        assert tag.name == data["name"]

    @pytest.mark.unit
    def test_tag_create_empty_name_fails(self):
        """Test tag creation with empty name fails."""
        with pytest.raises(ValidationError) as exc_info:
            TagCreate(name="")
        
        assert "name" in str(exc_info.value)


class TestUserLoginSchema:
    """Test UserLogin schema validation."""

    @pytest.mark.unit
    def test_valid_user_login(self):
        """Test valid user login data."""
        data = {
            "email": "test@example.com",
            "password": "password123",
        }
        login = UserLogin(**data)
        
        assert login.email == data["email"]
        assert login.password == data["password"]

    @pytest.mark.unit
    def test_user_login_invalid_email(self):
        """Test user login with invalid email fails."""
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(
                email="invalid-email",
                password="password123",
            )
        
        assert "email" in str(exc_info.value)
