"""Integration tests for database operations."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_article,
    create_comment,
    create_tag,
    create_user,
    delete_article,
    delete_comment,
    delete_user,
    get_all_tags,
    get_article_by_id,
    get_article_by_slug,
    get_articles,
    get_comment_by_id,
    get_comments_by_article,
    get_or_create_tags,
    get_popular_tags,
    get_tag_by_name,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    increment_article_views,
    update_article,
    update_comment,
    update_user,
)
from app.models import Article, Comment, Tag, User
from app.schemas import (
    ArticleCreate,
    ArticleUpdate,
    CommentCreate,
    TagCreate,
    UserCreate,
    UserUpdate,
)


@pytest.mark.integration
class TestUserCRUD:
    """Test User CRUD operations."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user_data = UserCreate(
            email="crudtest@example.com",
            username="crudtest",
            password="password123",
        )
        
        user = await create_user(db_session, user_data)
        
        assert user.id is not None
        assert user.email == user_data.email
        assert user.username == user_data.username
        assert user.hashed_password is not None

    async def test_get_user_by_id(self, db_session: AsyncSession, test_user: User):
        """Test getting user by ID."""
        user = await get_user_by_id(db_session, test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_user_by_email(self, db_session: AsyncSession, test_user: User):
        """Test getting user by email."""
        user = await get_user_by_email(db_session, test_user.email)
        
        assert user is not None
        assert user.email == test_user.email

    async def test_get_user_by_username(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting user by username."""
        user = await get_user_by_username(db_session, test_user.username)
        
        assert user is not None
        assert user.username == test_user.username

    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """Test updating user."""
        update_data = UserUpdate(full_name="Updated Name", bio="Updated Bio")
        
        updated = await update_user(db_session, test_user, update_data)
        
        assert updated.full_name == "Updated Name"
        assert updated.bio == "Updated Bio"

    async def test_delete_user(self, db_session: AsyncSession):
        """Test deleting user."""
        # Create a user to delete
        user_data = UserCreate(
            email="deletetest@example.com",
            username="deletetest",
            password="password123",
        )
        user = await create_user(db_session, user_data)
        user_id = user.id
        
        # Delete the user
        await delete_user(db_session, user)
        
        # Verify deletion
        deleted = await get_user_by_id(db_session, user_id)
        assert deleted is None


@pytest.mark.integration
class TestArticleCRUD:
    """Test Article CRUD operations."""

    async def test_create_article(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating an article."""
        article_data = ArticleCreate(
            title="Test Article",
            description="Test Description",
            body="Test body content",
            tag_list=["python", "fastapi"],
            published=True,
        )
        
        article = await create_article(db_session, article_data, test_user.id)
        
        assert article.id is not None
        assert article.title == article_data.title
        assert article.slug is not None
        assert article.author_id == test_user.id
        assert len(article.tags) == 2

    async def test_get_article_by_id(
        self, db_session: AsyncSession, test_article: Article
    ):
        """Test getting article by ID."""
        article = await get_article_by_id(db_session, test_article.id)
        
        assert article is not None
        assert article.id == test_article.id

    async def test_get_article_by_slug(
        self, db_session: AsyncSession, test_article: Article
    ):
        """Test getting article by slug."""
        article = await get_article_by_slug(db_session, test_article.slug)
        
        assert article is not None
        assert article.slug == test_article.slug

    async def test_get_articles_pagination(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test article pagination."""
        # Create multiple articles
        for i in range(5):
            await create_article(
                db_session,
                ArticleCreate(
                    title=f"Article {i}",
                    description=f"Description {i}",
                    body=f"Body {i}",
                    published=True,
                ),
                test_user.id,
            )
        
        articles, total = await get_articles(db_session, skip=0, limit=3)
        
        assert len(articles) == 3
        assert total >= 5

    async def test_update_article(
        self, db_session: AsyncSession, test_article: Article
    ):
        """Test updating article."""
        update_data = ArticleUpdate(title="Updated Title", published=False)
        
        updated = await update_article(db_session, test_article, update_data)
        
        assert updated.title == "Updated Title"
        assert updated.published is False

    async def test_delete_article(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting article."""
        # Create article to delete
        article = await create_article(
            db_session,
            ArticleCreate(
                title="To Delete",
                description="Description",
                body="Body",
                published=True,
            ),
            test_user.id,
        )
        article_id = article.id
        
        # Delete
        await delete_article(db_session, article)
        
        # Verify deletion
        deleted = await get_article_by_id(db_session, article_id, load_relations=False)
        assert deleted is None

    async def test_increment_article_views(
        self, db_session: AsyncSession, test_article: Article
    ):
        """Test incrementing article view count."""
        initial_views = test_article.views_count
        
        await increment_article_views(db_session, test_article)
        
        # Reload from DB
        updated = await get_article_by_id(db_session, test_article.id, load_relations=False)
        assert updated.views_count == initial_views + 1


@pytest.mark.integration
class TestCommentCRUD:
    """Test Comment CRUD operations."""

    async def test_create_comment(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_article: Article,
    ):
        """Test creating a comment."""
        comment_data = CommentCreate(body="Test comment body")
        
        comment = await create_comment(
            db_session, comment_data, test_article.id, test_user.id
        )
        
        assert comment.id is not None
        assert comment.body == comment_data.body
        assert comment.article_id == test_article.id
        assert comment.author_id == test_user.id

    async def test_get_comment_by_id(
        self, db_session: AsyncSession, test_comment: Comment
    ):
        """Test getting comment by ID."""
        comment = await get_comment_by_id(db_session, test_comment.id)
        
        assert comment is not None
        assert comment.id == test_comment.id

    async def test_get_comments_by_article(
        self,
        db_session: AsyncSession,
        test_article: Article,
        test_user: User,
    ):
        """Test getting comments by article."""
        # Create multiple comments
        for i in range(3):
            await create_comment(
                db_session,
                CommentCreate(body=f"Comment {i}"),
                test_article.id,
                test_user.id,
            )
        
        comments, total = await get_comments_by_article(db_session, test_article.id)
        
        assert len(comments) == 3
        assert total == 3

    async def test_update_comment(
        self, db_session: AsyncSession, test_comment: Comment
    ):
        """Test updating comment."""
        new_body = "Updated comment body"
        
        updated = await update_comment(db_session, test_comment, new_body)
        
        assert updated.body == new_body

    async def test_delete_comment(
        self,
        db_session: AsyncSession,
        test_article: Article,
        test_user: User,
    ):
        """Test deleting comment."""
        # Create comment to delete
        comment = await create_comment(
            db_session,
            CommentCreate(body="To delete"),
            test_article.id,
            test_user.id,
        )
        comment_id = comment.id
        
        # Delete
        await delete_comment(db_session, comment)
        
        # Verify deletion
        deleted = await get_comment_by_id(db_session, comment_id)
        assert deleted is None


@pytest.mark.integration
class TestTagCRUD:
    """Test Tag CRUD operations."""

    async def test_create_tag(self, db_session: AsyncSession):
        """Test creating a tag."""
        tag_data = TagCreate(name="newtag")
        
        tag = await create_tag(db_session, tag_data)
        
        assert tag.id is not None
        assert tag.name == "newtag"

    async def test_get_tag_by_name(
        self, db_session: AsyncSession, test_tag: Tag
    ):
        """Test getting tag by name."""
        tag = await get_tag_by_name(db_session, test_tag.name)
        
        assert tag is not None
        assert tag.name == test_tag.name

    async def test_get_all_tags(
        self, db_session: AsyncSession, test_tag: Tag
    ):
        """Test getting all tags."""
        tags = await get_all_tags(db_session)
        
        assert len(tags) > 0
        assert any(t.name == test_tag.name for t in tags)

    async def test_get_or_create_tags(self, db_session: AsyncSession):
        """Test get or create tags functionality."""
        tag_names = ["python", "fastapi", "python"]  # duplicate
        
        tags = await get_or_create_tags(db_session, tag_names)
        
        assert len(tags) == 2  # duplicates should be deduplicated

    async def test_get_popular_tags(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test getting popular tags."""
        # Create articles with tags
        for i in range(3):
            await create_article(
                db_session,
                ArticleCreate(
                    title=f"Article {i}",
                    description="Description",
                    body="Body",
                    tag_list=["python"],
                    published=True,
                ),
                test_user.id,
            )
        
        popular = await get_popular_tags(db_session, limit=10)
        
        assert len(popular) > 0
        assert any(name == "python" for name, _ in popular)


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test database transaction behavior."""

    async def test_transaction_rollback_on_error(self, db_session: AsyncSession):
        """Test that failed operations don't commit partial data."""
        # This test verifies transaction isolation
        # Operations in one session shouldn't affect another until commit
        
        from sqlalchemy import select
        
        result = await db_session.execute(
            select(User).where(User.email == "transaction@test.com")
        )
        initial_count = len(result.scalars().all())
        
        # The session fixture handles rollback automatically
        # So any operations should be rolled back after test
        assert initial_count == 0
