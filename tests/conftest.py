"""Pytest configuration and shared test fixtures.

This module provides shared fixtures for all test types:
- Database fixtures (async SQLAlchemy sessions)
- HTTP client fixtures (AsyncClient for API testing)
- Test data fixtures (sample users, articles, comments)
- Authentication fixtures (JWT tokens, auth headers)

Fixtures are organized by scope:
- session: Database setup, event loop
- function: Clean database state per test

Example:
    Use fixtures in tests:
    async def test_create_article(client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/articles", headers=auth_headers)
        assert response.status_code == 201
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.auth import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models import Article, Comment, Tag, User

fake = Faker()

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_test_db():
    """Initialize test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_test_db():
    """Drop test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Setup test database once per session."""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client for API testing."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Generate test user data."""
    return {
        "email": fake.email(),
        "username": fake.user_name(),
        "password": "SecurePass123!",
        "full_name": fake.name(),
        "bio": fake.text(max_nb_chars=200),
    }


@pytest.fixture
def test_article_data():
    """Generate test article data."""
    return {
        "title": fake.sentence(),
        "description": fake.text(max_nb_chars=200),
        "body": fake.text(max_nb_chars=2000),
        "tag_list": [fake.word() for _ in range(3)],
        "published": True,
    }


@pytest.fixture
def test_comment_data():
    """Generate test comment data."""
    return {
        "body": fake.text(max_nb_chars=500),
    }


# ============== Async Fixtures for Models ==============

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in database."""
    user = User(
        email=fake.email(),
        username=fake.user_name(),
        hashed_password=get_password_hash("testpass123"),
        full_name=fake.name(),
        bio=fake.text(max_nb_chars=200),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a test superuser in database."""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_article(db_session: AsyncSession, test_user: User) -> Article:
    """Create a test article in database."""
    from slugify import slugify
    
    article = Article(
        slug=slugify(fake.sentence(), max_length=255),
        title=fake.sentence(),
        description=fake.text(max_nb_chars=200),
        body=fake.text(max_nb_chars=2000),
        author_id=test_user.id,
        published=True,
        views_count=0,
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    return article


@pytest_asyncio.fixture
async def test_comment(
    db_session: AsyncSession, test_user: User, test_article: Article
) -> Comment:
    """Create a test comment in database."""
    comment = Comment(
        body=fake.text(max_nb_chars=500),
        article_id=test_article.id,
        author_id=test_user.id,
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    return comment


@pytest_asyncio.fixture
async def test_tag(db_session: AsyncSession) -> Tag:
    """Create a test tag in database."""
    tag = Tag(name=fake.word().lower())
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Generate authentication headers for test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def superuser_auth_headers(test_superuser: User) -> dict:
    """Generate authentication headers for test superuser."""
    token = create_access_token(test_superuser.id)
    return {"Authorization": f"Bearer {token}"}
