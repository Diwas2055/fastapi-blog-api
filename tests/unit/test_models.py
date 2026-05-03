"""Unit tests for SQLAlchemy models."""
import pytest

from app.models import Article, Comment, Tag, User


class TestUserModel:
    """Test User model."""

    @pytest.mark.unit
    def test_user_creation(self):
        """Test creating a User instance."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User",
            bio="A test bio",
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashedpassword"
        assert user.full_name == "Test User"
        assert user.bio == "A test bio"
        assert user.is_active is True
        assert user.is_superuser is False

    @pytest.mark.unit
    def test_user_repr(self):
        """Test User string representation."""
        user = User(id=1, username="testuser")
        
        assert repr(user) == "<User(id=1, username=testuser)>"

    @pytest.mark.unit
    def test_user_default_values(self):
        """Test User default values."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
        )
        
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.full_name is None
        assert user.bio is None

    @pytest.mark.unit
    def test_user_relationships_empty_by_default(self):
        """Test User relationships are empty by default."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
        )
        
        assert user.articles == []
        assert user.comments == []


class TestArticleModel:
    """Test Article model."""

    @pytest.mark.unit
    def test_article_creation(self):
        """Test creating an Article instance."""
        article = Article(
            slug="test-article",
            title="Test Article",
            description="A test description",
            body="This is the article body.",
            author_id=1,
            published=True,
        )
        
        assert article.slug == "test-article"
        assert article.title == "Test Article"
        assert article.description == "A test description"
        assert article.body == "This is the article body."
        assert article.author_id == 1
        assert article.published is True
        assert article.views_count == 0

    @pytest.mark.unit
    def test_article_default_values(self):
        """Test Article default values."""
        article = Article(
            slug="test",
            title="Test",
            description="Description",
            body="Body",
            author_id=1,
        )
        
        assert article.published is False
        assert article.views_count == 0

    @pytest.mark.unit
    def test_article_repr(self):
        """Test Article string representation."""
        article = Article(id=1, title="Test Article")
        
        assert repr(article) == "<Article(id=1, title=Test Article)>"

    @pytest.mark.unit
    def test_article_relationships_empty_by_default(self):
        """Test Article relationships are empty by default."""
        article = Article(
            slug="test",
            title="Test",
            description="Description",
            body="Body",
            author_id=1,
        )
        
        assert article.comments == []
        assert article.tags == []


class TestCommentModel:
    """Test Comment model."""

    @pytest.mark.unit
    def test_comment_creation(self):
        """Test creating a Comment instance."""
        comment = Comment(
            body="This is a test comment.",
            article_id=1,
            author_id=2,
        )
        
        assert comment.body == "This is a test comment."
        assert comment.article_id == 1
        assert comment.author_id == 2

    @pytest.mark.unit
    def test_comment_repr(self):
        """Test Comment string representation."""
        comment = Comment(id=1, article_id=5)
        
        assert repr(comment) == "<Comment(id=1, article_id=5)>"


class TestTagModel:
    """Test Tag model."""

    @pytest.mark.unit
    def test_tag_creation(self):
        """Test creating a Tag instance."""
        tag = Tag(name="python")
        
        assert tag.name == "python"

    @pytest.mark.unit
    def test_tag_repr(self):
        """Test Tag string representation."""
        tag = Tag(id=1, name="python")
        
        assert repr(tag) == "<Tag(id=1, name=python)>"

    @pytest.mark.unit
    def test_tag_relationships_empty_by_default(self):
        """Test Tag relationships are empty by default."""
        tag = Tag(name="python")
        
        assert tag.articles == []


class TestModelRelationships:
    """Test model relationships."""

    @pytest.mark.unit
    def test_user_article_relationship(self):
        """Test User-Article relationship setup."""
        user = User(
            id=1,
            email="author@example.com",
            username="author",
            hashed_password="hashed",
        )
        article = Article(
            id=1,
            slug="test",
            title="Test",
            description="Description",
            body="Body",
            author_id=user.id,
        )
        
        # In real DB, this would be populated via SQLAlchemy
        # Here we just test the structure exists
        assert article.author_id == user.id

    @pytest.mark.unit
    def test_article_comment_relationship(self):
        """Test Article-Comment relationship setup."""
        article = Article(
            id=1,
            slug="test",
            title="Test",
            description="Description",
            body="Body",
            author_id=1,
        )
        comment = Comment(
            id=1,
            body="Test comment",
            article_id=article.id,
            author_id=2,
        )
        
        assert comment.article_id == article.id

    @pytest.mark.unit
    def test_user_comment_relationship(self):
        """Test User-Comment relationship setup."""
        user = User(
            id=2,
            email="commenter@example.com",
            username="commenter",
            hashed_password="hashed",
        )
        comment = Comment(
            id=1,
            body="Test comment",
            article_id=1,
            author_id=user.id,
        )
        
        assert comment.author_id == user.id


class TestModelEdgeCases:
    """Test model edge cases."""

    @pytest.mark.unit
    def test_user_with_max_length_username(self):
        """Test user with maximum length username."""
        long_username = "a" * 50
        user = User(
            email="test@example.com",
            username=long_username,
            hashed_password="hashed",
        )
        
        assert len(user.username) == 50

    @pytest.mark.unit
    def test_article_with_max_length_title(self):
        """Test article with maximum length title."""
        long_title = "a" * 255
        article = Article(
            slug="test",
            title=long_title,
            description="Description",
            body="Body",
            author_id=1,
        )
        
        assert len(article.title) == 255

    @pytest.mark.unit
    def test_tag_with_max_length_name(self):
        """Test tag with maximum length name."""
        long_name = "a" * 50
        tag = Tag(name=long_name)
        
        assert len(tag.name) == 50

    @pytest.mark.unit
    def test_comment_with_max_length_body(self):
        """Test comment with long body."""
        long_body = "a" * 5000
        comment = Comment(
            body=long_body,
            article_id=1,
            author_id=2,
        )
        
        assert len(comment.body) == 5000
