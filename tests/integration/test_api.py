"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_article,
    create_user,
)
from app.models import Article, User
from app.schemas import ArticleCreate, UserCreate


@pytest.mark.integration
class TestUserEndpoints:
    """Test user API endpoints."""

    async def test_register_user_success(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test successful user registration."""
        response = await client.post("/api/users/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["username"] == test_user_data["username"]
        assert "password" not in data["user"]

    async def test_register_user_duplicate_email(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": test_user.email,
            "username": "different_username",
            "password": "password123",
        }
        
        response = await client.post("/api/users/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_login_user_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful user login."""
        # First create a user
        user_data = {
            "email": "logintest@example.com",
            "username": "logintest",
            "password": "testpass123",
        }
        await create_user(db_session, UserCreate(**user_data))
        
        # Then login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"],
        }
        response = await client.post("/api/users/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data

    async def test_login_user_invalid_credentials(
        self, client: AsyncClient
    ):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        }
        response = await client.post("/api/users/login", json=login_data)
        
        assert response.status_code == 401

    async def test_get_current_user(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test getting current user with valid token."""
        response = await client.get("/api/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username

    async def test_get_current_user_no_token(
        self, client: AsyncClient
    ):
        """Test getting current user without token fails."""
        response = await client.get("/api/users/me")
        
        assert response.status_code == 401

    async def test_update_current_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test updating current user information."""
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
        }
        
        response = await client.put(
            "/api/users/me",
            headers=auth_headers,
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["bio"] == update_data["bio"]


@pytest.mark.integration
class TestArticleEndpoints:
    """Test article API endpoints."""

    async def test_list_articles_empty(
        self, client: AsyncClient
    ):
        """Test listing articles when none exist."""
        response = await client.get("/api/articles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["articles"] == []
        assert data["total"] == 0

    async def test_list_articles_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_article: Article,
    ):
        """Test listing articles with data."""
        response = await client.get("/api/articles")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) > 0
        assert data["total"] > 0

    async def test_create_article_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_article_data: dict,
    ):
        """Test successful article creation."""
        response = await client.post(
            "/api/articles",
            headers=auth_headers,
            json=test_article_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_article_data["title"]
        assert data["slug"] is not None
        assert "id" in data

    async def test_create_article_unauthorized(
        self, client: AsyncClient, test_article_data: dict
    ):
        """Test creating article without authentication fails."""
        response = await client.post("/api/articles", json=test_article_data)
        
        assert response.status_code == 401

    async def test_get_article_by_slug(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting article by slug."""
        # Create article first
        article_data = ArticleCreate(
            title="Test Article for Get",
            description="Description",
            body="Body content",
            published=True,
        )
        article = await create_article(db_session, article_data, test_user.id)
        
        response = await client.get(f"/api/articles/{article.slug}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == article.title
        assert data["slug"] == article.slug

    async def test_get_article_not_found(
        self, client: AsyncClient
    ):
        """Test getting non-existent article."""
        response = await client.get("/api/articles/non-existent-slug")
        
        assert response.status_code == 404

    async def test_update_article_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user: User,
    ):
        """Test successful article update."""
        # Create article first
        article_data = ArticleCreate(
            title="Original Title",
            description="Description",
            body="Body content",
            published=True,
        )
        article = await create_article(db_session, article_data, test_user.id)
        
        update_data = {"title": "Updated Title"}
        response = await client.put(
            f"/api/articles/{article.slug}",
            headers=auth_headers,
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    async def test_delete_article_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_user: User,
    ):
        """Test successful article deletion."""
        # Create article first
        article_data = ArticleCreate(
            title="Article to Delete",
            description="Description",
            body="Body content",
            published=True,
        )
        article = await create_article(db_session, article_data, test_user.id)
        
        response = await client.delete(
            f"/api/articles/{article.slug}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(f"/api/articles/{article.slug}")
        assert get_response.status_code == 404

    async def test_update_article_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_article: Article,
    ):
        """Test updating article by non-owner fails."""
        # Create another user
        other_user = await create_user(
            db_session,
            UserCreate(
                email="other@example.com",
                username="otheruser",
                password="password123",
            ),
        )
        
        # Get token for other user
        from app.auth import create_access_token
        other_headers = {"Authorization": f"Bearer {create_access_token(other_user.id)}"}
        
        update_data = {"title": "Unauthorized Update"}
        response = await client.put(
            f"/api/articles/{test_article.slug}",
            headers=other_headers,
            json=update_data,
        )
        
        assert response.status_code == 403


@pytest.mark.integration
class TestCommentEndpoints:
    """Test comment API endpoints."""

    async def test_list_comments(
        self,
        client: AsyncClient,
        test_article: Article,
    ):
        """Test listing comments for an article."""
        response = await client.get(f"/api/articles/{test_article.slug}/comments")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_comment_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_article: Article,
        test_comment_data: dict,
    ):
        """Test successful comment creation."""
        response = await client.post(
            f"/api/articles/{test_article.slug}/comments",
            headers=auth_headers,
            json=test_comment_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["body"] == test_comment_data["body"]
        assert "author" in data

    async def test_create_comment_article_not_found(
        self, client: AsyncClient, auth_headers: dict, test_comment_data: dict
    ):
        """Test creating comment for non-existent article fails."""
        response = await client.post(
            "/api/articles/non-existent/comments",
            headers=auth_headers,
            json=test_comment_data,
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestTagEndpoints:
    """Test tag API endpoints."""

    async def test_list_tags(
        self, client: AsyncClient, test_tag
    ):
        """Test listing all tags."""
        response = await client.get("/api/tags")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_tag_superuser(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
    ):
        """Test creating tag as superuser."""
        tag_data = {"name": "newtag"}
        
        response = await client.post(
            "/api/tags",
            headers=superuser_auth_headers,
            json=tag_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tag_data["name"]

    async def test_create_tag_regular_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating tag as regular user fails."""
        tag_data = {"name": "newtag"}
        
        response = await client.post(
            "/api/tags",
            headers=auth_headers,
            json=tag_data,
        )
        
        assert response.status_code == 403
