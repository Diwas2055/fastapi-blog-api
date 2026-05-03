# FastAPI Blog API - Complete Demo with Full Testing

A production-ready FastAPI blog API demonstrating real-world patterns with comprehensive testing including unit tests, integration tests, E2E tests, and property-based testing with Hypothesis.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access control
- **CRUD Operations**: Full CRUD for Users, Articles, Comments, and Tags
- **Database**: Async SQLAlchemy with SQLite (dev) or PostgreSQL (production)
- **Validation**: Pydantic schemas with strict validation
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Real-world Patterns**: Slug generation, pagination, filtering, view counting

## Project Structure

```
fastapi-blog-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── database.py          # Database setup and session management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── auth.py              # Authentication utilities (JWT, password hashing)
│   ├── crud.py              # Database CRUD operations
│   ├── dependencies.py      # FastAPI dependencies
│   └── routers/
│       ├── __init__.py
│       ├── users.py         # User endpoints (auth, profile)
│       ├── articles.py      # Article endpoints
│       ├── comments.py      # Comment endpoints
│       └── tags.py          # Tag endpoints
├── tests/
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── unit/                # Unit tests (isolated, fast)
│   │   ├── test_auth.py
│   │   ├── test_schemas.py
│   │   ├── test_models.py
│   │   └── test_crud.py
│   ├── integration/         # Integration tests (DB, API)
│   │   ├── test_api.py
│   │   └── test_database.py
│   ├── e2e/                 # End-to-end tests (full workflows)
│   │   └── test_end_to_end.py
│   └── property_based/      # Property-based tests (Hypothesis)
│       └── test_properties.py
├── pyproject.toml          # Project configuration (uv)
├── pytest.ini              # Pytest configuration
├── .env.example            # Environment variables template
├── .python-version         # Python version for uv
└── README.md               # This file
```

## Installation (using uv)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone/navigate to project
cd fastapi_complete_demo

# Create virtual environment and sync dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Copy environment variables
cp .env.example .env
```

### uv Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Add a new dependency
uv add fastapi

# Add a dev dependency
uv add --dev pytest

# Run a command in the environment
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Update lockfile
uv lock
```

## Running the Application

```bash
# Development server
uv run uvicorn app.main:app --reload

# Production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or activate environment first, then run
source .venv/bin/activate
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login and get token
- `GET /api/users/me` - Get current user
- `PUT /api/users/me` - Update current user
- `GET /api/users/{id}` - Get public user profile

### Articles
- `GET /api/articles` - List articles (with pagination, filters)
- `POST /api/articles` - Create article (auth required)
- `GET /api/articles/feed` - Get user feed (auth required)
- `GET /api/articles/{slug}` - Get single article
- `PUT /api/articles/{slug}` - Update article (owner only)
- `DELETE /api/articles/{slug}` - Delete article (owner only)

### Comments
- `GET /api/articles/{slug}/comments` - List comments
- `POST /api/articles/{slug}/comments` - Add comment (auth required)
- `PUT /api/articles/{slug}/comments/{id}` - Update comment (owner only)
- `DELETE /api/articles/{slug}/comments/{id}` - Delete comment (owner/article owner)

### Tags
- `GET /api/tags` - List all tags
- `GET /api/tags/popular` - Get popular tags
- `POST /api/tags` - Create tag (superuser only)
- `DELETE /api/tags/{name}` - Delete tag (superuser only)

## Testing

### Test Categories

1. **Unit Tests**: Fast, isolated tests for individual functions
2. **Integration Tests**: Tests with database and API interactions
3. **E2E Tests**: Complete user workflow tests
4. **Property-Based Tests**: Hypothesis tests for invariant properties
5. **Mocking Tests**: Examples of mocking external services, HTTP requests, and file operations

### Mocking Examples

The project includes comprehensive mocking examples in `tests/unit/test_mocking.py`:

```python
# Basic mocking with pytest-mock
@pytest.mark.unit
async def test_send_email_mocked(self, mocker):
    """Mock email service to avoid sending real emails."""
    # Mock the HTTP request
    mock_response = mocker.AsyncMock()
    mock_response.json.return_value = {"message_id": "msg_123"}
    mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

    service = EmailService()
    result = await service.send_email("user@test.com", "Subject", "Body")
    assert result["message_id"] == "msg_123"

# HTTP mocking with respx
@pytest.mark.unit
@respx.mock
async def test_external_api_call(self):
    """Mock external API with respx."""
    route = respx.get("https://api.external.com/users/123")
    route.mock(return_value=Response(200, json={"id": "123", "name": "John"}))

    service = ExternalAPIService("https://api.external.com", "api-key")
    result = await service.fetch_user_data("123")
    assert result["name"] == "John"

# File system mocking
@pytest.mark.unit
def test_file_operations_mocked(self, mocker):
    """Mock file system operations."""
    mock_file = mocker.mock_open(read_data=b"File content")
    mocker.patch("builtins.open", mock_file)

    service = FileStorageService()
    result = service.read_file("test.txt")
    assert result == b"File content"
```

**Mocking Libraries Used:**
- `pytest-mock` - pytest fixture for unittest.mock
- `respx` - HTTPX request mocking
- `unittest.mock` - Built-in Python mocking

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test categories
uv run pytest -m unit              # Unit tests only
uv run pytest -m integration       # Integration tests only
uv run pytest -m e2e               # E2E tests only
uv run pytest -m property_based    # Property-based tests only

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_auth.py -v

# Run with markers
uv run pytest -v --tb=short
```

### Test Configuration

Tests are configured in `pytest.ini`:
- `tests/unit/` - Unit tests (marked with `@pytest.mark.unit`)
- `tests/integration/` - Integration tests (marked with `@pytest.mark.integration`)
- `tests/e2e/` - E2E tests (marked with `@pytest.mark.e2e`)
- `tests/property_based/` - Property-based tests (marked with `@pytest.mark.property_based`)

## Test-Driven Development (TDD)

This project follows TDD principles:

1. **Red**: Write a failing test first
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Improve code while keeping tests green

### Example TDD Workflow

```python
# 1. Write the test first
def test_password_hashing():
    password = "testpass123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)

# 2. Implement the feature
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# 3. Run tests to verify
pytest tests/unit/test_auth.py -v
```

## Property-Based Testing with Hypothesis

Property-based tests verify invariants that should always hold:

```python
@given(password=st.text(min_size=1, max_size=100))
def test_password_hashing_is_reversible(password: str):
    """Any password should hash and verify correctly."""
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
```

This generates 100+ random passwords to verify the property holds.

## Environment Variables

```bash
# Application
APP_NAME="FastAPI Blog API"
DEBUG=false
SECRET_KEY=your-secret-key-change-in-production # python -c "import secrets; print(secrets.token_urlsafe(32))"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite+aiosqlite:///./blog.db
# For PostgreSQL: postgresql+asyncpg://user:password@localhost/blogdb

# Security
PASSWORD_MIN_LENGTH=8
```

## Key Libraries

- **FastAPI**: Modern web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation
- **Pytest**: Testing framework
- **Hypothesis**: Property-based testing
- **python-jose**: JWT handling
- **passlib**: Password hashing
- **python-slugify**: URL-friendly slugs
- **uv**: Fast Python package manager and resolver

## Why uv?

This project uses [uv](https://github.com/astral-sh/uv) instead of pip because:
- **10-100x faster** dependency resolution and installation
- **Universal lockfile** (`uv.lock`) for reproducible builds
- **Built-in virtual environment** management
- **Single `pyproject.toml`** for all configuration
- **Compatible** with pip when needed

## License

MIT License
