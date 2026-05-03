"""End-to-end tests for complete user workflows."""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestUserRegistrationAndAuthentication:
    """E2E test for user registration and authentication flow."""

    async def test_complete_registration_login_flow(self, client: AsyncClient):
        """Test complete user registration and login flow."""
        # Step 1: Register a new user
        register_data = {
            "email": "e2euser@example.com",
            "username": "e2euser",
            "password": "SecurePass123!",
            "full_name": "E2E Test User",
            "bio": "This is an E2E test user",
        }
        
        register_response = await client.post(
            "/api/users/register", json=register_data
        )
        assert register_response.status_code == 201
        
        register_result = register_response.json()
        assert "token" in register_result
        assert register_result["user"]["email"] == register_data["email"]
        
        token = register_result["token"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Get current user info
        me_response = await client.get("/api/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        
        me_data = me_response.json()
        assert me_data["email"] == register_data["email"]
        assert me_data["username"] == register_data["username"]
        
        # Step 3: Login with credentials
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"],
        }
        
        login_response = await client.post("/api/users/login", json=login_data)
        assert login_response.status_code == 200
        
        login_result = login_response.json()
        assert "token" in login_result
        
        # Step 4: Update user profile
        update_data = {
            "full_name": "Updated E2E User",
            "bio": "Updated bio from E2E test",
        }
        
        update_response = await client.put(
            "/api/users/me", headers=auth_headers, json=update_data
        )
        assert update_response.status_code == 200
        
        updated_data = update_response.json()
        assert updated_data["full_name"] == update_data["full_name"]
        
        # Step 5: Get public user profile
        user_id = me_data["id"]
        public_response = await client.get(f"/api/users/{user_id}")
        assert public_response.status_code == 200
        
        public_data = public_response.json()
        assert public_data["username"] == register_data["username"]
        assert "email" in public_data  # Should be visible in public profile


@pytest.mark.e2e
class TestArticleLifecycle:
    """E2E test for complete article lifecycle."""

    async def test_article_crud_workflow(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test complete article create, read, update, delete workflow."""
        
        # Step 1: Create a new article
        article_data = {
            "title": "My E2E Test Article",
            "description": "This article was created during E2E testing",
            "body": "This is the full content of the E2E test article. " * 10,
            "tag_list": ["e2e", "testing", "fastapi"],
            "published": False,
        }
        
        create_response = await client.post(
            "/api/articles", headers=auth_headers, json=article_data
        )
        assert create_response.status_code == 201
        
        article = create_response.json()
        article_slug = article["slug"]
        assert article["title"] == article_data["title"]
        assert len(article["tags"]) == 3
        
        # Step 2: Get the article by slug
        get_response = await client.get(f"/api/articles/{article_slug}")
        assert get_response.status_code == 200
        
        fetched_article = get_response.json()
        assert fetched_article["title"] == article_data["title"]
        assert fetched_article["views_count"] > 0  # Should be incremented
        
        # Step 3: List articles and verify ours is there
        list_response = await client.get("/api/articles?published_only=false")
        assert list_response.status_code == 200
        
        list_data = list_response.json()
        assert any(a["slug"] == article_slug for a in list_data["articles"])
        
        # Step 4: Update the article
        update_data = {
            "title": "Updated E2E Article Title",
            "published": True,
        }
        
        update_response = await client.put(
            f"/api/articles/{article_slug}", headers=auth_headers, json=update_data
        )
        assert update_response.status_code == 200
        
        updated_article = update_response.json()
        assert updated_article["title"] == update_data["title"]
        assert updated_article["published"] is True
        
        # Step 5: Verify published article appears in public list
        public_list_response = await client.get("/api/articles")
        assert public_list_response.status_code == 200
        
        public_data = public_list_response.json()
        assert any(a["slug"] == updated_article["slug"] for a in public_data["articles"])
        
        # Step 6: Delete the article
        delete_response = await client.delete(
            f"/api/articles/{updated_article['slug']}", headers=auth_headers
        )
        assert delete_response.status_code == 204
        
        # Step 7: Verify article is deleted
        get_deleted_response = await client.get(
            f"/api/articles/{updated_article['slug']}"
        )
        assert get_deleted_response.status_code == 404


@pytest.mark.e2e
class TestCommentWorkflow:
    """E2E test for comment workflow."""

    async def test_comment_lifecycle(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user,  # This is actually a User model from fixture
    ):
        """Test complete comment lifecycle on an article."""
        # Note: We need to create article via API to ensure proper setup
        article_data = {
            "title": "Article for Comments",
            "description": "Testing comments",
            "body": "Article body content here.",
            "published": True,
        }
        
        create_article_response = await client.post(
            "/api/articles", headers=auth_headers, json=article_data
        )
        assert create_article_response.status_code == 201
        
        article = create_article_response.json()
        article_slug = article["slug"]
        
        # Step 1: Add a comment
        comment_data = {"body": "This is a great article! Thanks for sharing."}
        
        comment_response = await client.post(
            f"/api/articles/{article_slug}/comments",
            headers=auth_headers,
            json=comment_data,
        )
        assert comment_response.status_code == 201
        
        comment = comment_response.json()
        comment_id = comment["id"]
        assert comment["body"] == comment_data["body"]
        assert "author" in comment
        
        # Step 2: List comments
        list_response = await client.get(f"/api/articles/{article_slug}/comments")
        assert list_response.status_code == 200
        
        comments = list_response.json()
        assert len(comments) > 0
        assert any(c["id"] == comment_id for c in comments)
        
        # Step 3: Update the comment
        update_data = {"body": "Updated: This article is even better than I thought!"}
        
        update_response = await client.put(
            f"/api/articles/{article_slug}/comments/{comment_id}",
            headers=auth_headers,
            json=update_data,
        )
        assert update_response.status_code == 200
        
        updated_comment = update_response.json()
        assert updated_comment["body"] == update_data["body"]
        
        # Step 4: Delete the comment
        delete_response = await client.delete(
            f"/api/articles/{article_slug}/comments/{comment_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204
        
        # Step 5: Verify comment is deleted
        list_after_delete = await client.get(
            f"/api/articles/{article_slug}/comments"
        )
        comments_after = list_after_delete.json()
        assert not any(c["id"] == comment_id for c in comments_after)


@pytest.mark.e2e
class TestTagManagement:
    """E2E test for tag management workflow."""

    async def test_tag_workflow(
        self, client: AsyncClient, superuser_auth_headers: dict, auth_headers: dict
    ):
        """Test complete tag management workflow."""
        
        # Step 1: List all tags
        list_response = await client.get("/api/tags")
        assert list_response.status_code == 200
        
        # Verify tags endpoint works
        assert isinstance(list_response.json(), list)
        
        # Step 2: Create a new tag (as superuser)
        tag_data = {"name": "e2e-test-tag"}
        
        create_response = await client.post(
            "/api/tags", headers=superuser_auth_headers, json=tag_data
        )
        assert create_response.status_code == 201
        
        created_tag = create_response.json()
        assert created_tag["name"] == tag_data["name"]
        
        # Step 3: Verify regular user cannot create tags
        unauthorized_response = await client.post(
            "/api/tags", headers=auth_headers, json={"name": "unauthorized-tag"}
        )
        assert unauthorized_response.status_code == 403
        
        # Step 4: Get popular tags
        popular_response = await client.get("/api/tags/popular")
        assert popular_response.status_code == 200
        
        # Step 5: Delete the tag (as superuser)
        delete_response = await client.delete(
            f"/api/tags/{tag_data['name']}", headers=superuser_auth_headers
        )
        assert delete_response.status_code == 204


@pytest.mark.e2e
class TestFeedAndDiscovery:
    """E2E test for feed and content discovery."""

    async def test_user_feed_and_article_discovery(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test user feed and article discovery features."""
        
        # Step 1: Create multiple articles
        articles = []
        for i in range(3):
            article_data = {
                "title": f"Feed Article {i}",
                "description": f"Description for article {i}",
                "body": f"Content for article {i}",
                "tag_list": ["python", "fastapi"],
                "published": True,
            }
            
            response = await client.post(
                "/api/articles", headers=auth_headers, json=article_data
            )
            assert response.status_code == 201
            articles.append(response.json())
        
        # Step 2: Get user feed
        feed_response = await client.get("/api/articles/feed", headers=auth_headers)
        assert feed_response.status_code == 200
        
        feed_data = feed_response.json()
        assert len(feed_data["articles"]) > 0
        
        # Step 3: Filter by tag
        tag_filter_response = await client.get("/api/articles?tag=python")
        assert tag_filter_response.status_code == 200
        
        # Articles should have the python tag
        tagged_articles_data = tag_filter_response.json()
        assert "articles" in tagged_articles_data
        
        # Step 4: Pagination test
        paginated_response = await client.get("/api/articles?skip=0&limit=2")
        assert paginated_response.status_code == 200
        
        paginated_data = paginated_response.json()
        assert len(paginated_data["articles"]) <= 2
        
        # Step 5: View an article multiple times
        article_slug = articles[0]["slug"]
        
        # View 1
        await client.get(f"/api/articles/{article_slug}")
        # View 2
        await client.get(f"/api/articles/{article_slug}")
        # View 3
        final_view = await client.get(f"/api/articles/{article_slug}")
        
        final_article = final_view.json()
        assert final_article["views_count"] >= 3


@pytest.mark.e2e
class TestErrorHandling:
    """E2E test for error handling scenarios."""

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        
        # Try to create article without auth
        response = await client.post("/api/articles", json={"title": "Test"})
        assert response.status_code == 401
        
        # Try to access protected user endpoint
        response = await client.get("/api/users/me")
        assert response.status_code == 401
        
        # Try to access feed without auth (should work if public, but feed is protected)
        response = await client.get("/api/articles/feed")
        assert response.status_code == 401

    async def test_not_found_errors(self, client: AsyncClient):
        """Test handling of not found errors."""
        
        # Get non-existent article
        response = await client.get("/api/articles/non-existent-article-slug")
        assert response.status_code == 404
        
        # Get non-existent user
        response = await client.get("/api/users/999999")
        assert response.status_code == 404

    async def test_validation_errors(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test validation error handling."""
        
        # Create article with invalid data
        invalid_data = {
            "title": "",  # Empty title
            "description": "Desc",
            "body": "Body",
        }
        
        response = await client.post(
            "/api/articles", headers=auth_headers, json=invalid_data
        )
        assert response.status_code == 422  # Validation error

    async def test_forbidden_access(
        self,
        client: AsyncClient,
        db_session,
    ):
        """Test forbidden access scenarios."""
        from app.crud import create_user, create_article
        from app.schemas import UserCreate, ArticleCreate
        from app.auth import create_access_token
        
        # Create two users
        user1 = await create_user(
            db_session,
            UserCreate(email="user1@example.com", username="user1", password="pass123"),
        )
        user2 = await create_user(
            db_session,
            UserCreate(email="user2@example.com", username="user2", password="pass123"),
        )
        
        # Create article as user1
        article = await create_article(
            db_session,
            ArticleCreate(title="User1 Article", description="Desc", body="Body"),
            user1.id,
        )
        
        # Try to update as user2
        user2_token = create_access_token(user2.id)
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        response = await client.put(
            f"/api/articles/{article.slug}",
            headers=user2_headers,
            json={"title": "Hacked!"},
        )
        assert response.status_code == 403
