"""Comprehensive mocking examples using pytest-mock and unittest.mock.

This module demonstrates various mocking patterns for:
- External HTTP API calls (using pytest-respx)
- Email sending services
- File system operations
- Database queries
- Time/datetime operations
- Cache operations
- Side effects and return values

Mocking Libraries Used:
    - pytest-mock: Fixtures for unittest.mock integration
    - respx: HTTPX request mocking
    - unittest.mock: Built-in Python mocking

Example Usage:
    # Basic mock
    mocker.patch("app.services.EmailService.send_email")

    # Mock with return value
    mocker.patch("app.crud.get_user_by_id", return_value=mock_user)

    # Mock HTTP requests
    respx_mock.get("https://api.example.com/users/1").mock(return_value=Response(200))
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import respx
from httpx import Response

from app.crud import get_user_by_id
from app.models import User
from app.services import (
    CacheService,
    EmailService,
    ExternalAPIService,
    FileStorageService,
    NotificationService,
)


# ============== Basic Mocking Examples ==============


class TestBasicMocking:
    """Test basic mocking patterns with pytest-mock."""

    @pytest.mark.unit
    def test_mock_simple_function(self, mocker):
        """Demonstrate basic function mocking.

        Mocks a simple function and verifies it was called.
        """
        # Create a mock
        mock_func = mocker.Mock(return_value=42)

        # Use the mock
        result = mock_func("arg1", "arg2", key="value")

        # Assertions
        assert result == 42
        mock_func.assert_called_once()
        mock_func.assert_called_with("arg1", "arg2", key="value")

    @pytest.mark.unit
    def test_mock_with_side_effect(self, mocker):
        """Demonstrate mocking with side effects.

        Side effects allow the mock to perform different actions
        on successive calls or raise exceptions.
        """
        # Mock with multiple return values
        mock_func = mocker.Mock(side_effect=[1, 2, 3])

        assert mock_func() == 1
        assert mock_func() == 2
        assert mock_func() == 3

        # Mock that raises exception
        mock_error = mocker.Mock(side_effect=ValueError("Invalid input"))

        with pytest.raises(ValueError, match="Invalid input"):
            mock_error()

    @pytest.mark.unit
    def test_mock_with_call_count(self, mocker):
        """Demonstrate verifying multiple calls."""
        mock_func = mocker.Mock(return_value=None)

        # Call multiple times
        mock_func()
        mock_func()
        mock_func()

        assert mock_func.call_count == 3


# ============== Email Service Mocking ==============


class TestEmailServiceMocking:
    """Test EmailService with mocked HTTP calls."""

    @pytest.mark.unit
    async def test_send_email_success(self, mocker):
        """Mock successful email sending.

        Mocks the httpx.AsyncClient.post method to avoid
        making real HTTP requests to the email API.
        """
        # Setup mock
        mock_response = mocker.AsyncMock()
        mock_response.json.return_value = {
            "message_id": "msg_123",
            "status": "sent"
        }
        mock_response.raise_for_status = mocker.Mock()

        # Patch httpx.AsyncClient
        mocker.patch(
            "httpx.AsyncClient.post",
            return_value=mock_response
        )

        # Execute
        service = EmailService()
        result = await service.send_email(
            "user@example.com",
            "Test Subject",
            "Test body"
        )

        # Assert
        assert result["message_id"] == "msg_123"
        assert result["status"] == "sent"

    @pytest.mark.unit
    async def test_send_email_service_mocked(self, mocker):
        """Mock the entire service method instead of HTTP layer.

        This is useful when you want to skip all implementation
        and just verify the method was called correctly.
        """
        service = EmailService()

        # Mock the specific method
        mock_send = mocker.patch.object(
            service,
            "send_email",
            return_value={"message_id": "mocked", "status": "sent"}
        )

        # Call the method that uses send_email
        result = await service.send_welcome_email("user@example.com", "John")

        # Verify
        assert result["message_id"] == "mocked"
        mock_send.assert_called_once()

    @pytest.mark.unit
    async def test_send_email_error_handling(self, mocker):
        """Mock email API error response."""
        from httpx import HTTPStatusError, Request, Response

        # Create a mock response that raises an error
        mock_response = mocker.Mock()
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "Server error",
            request=mocker.Mock(),
            response=mocker.Mock(status_code=500)
        )

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        service = EmailService()

        with pytest.raises(HTTPStatusError):
            await service.send_email("user@example.com", "Subject", "Body")


# ============== External API Mocking with respx ==============


class TestExternalAPIMocking:
    """Test ExternalAPIService with respx HTTP mocking."""

    @pytest.mark.unit
    @respx.mock
    async def test_fetch_user_data_success(self):
        """Mock successful external API call using respx.

        respx provides a clean interface for mocking HTTPX requests
        without modifying the application code.
        """
        # Setup mock route
        route = respx.get("https://api.external.com/users/123")
        route.mock(return_value=Response(200, json={
            "id": "123",
            "name": "John Doe",
            "email": "john@external.com"
        }))

        # Execute
        service = ExternalAPIService(
            base_url="https://api.external.com",
            api_key="test-key"
        )
        result = await service.fetch_user_data("123")

        # Assert
        assert result["id"] == "123"
        assert result["name"] == "John Doe"
        assert route.called

    @pytest.mark.unit
    @respx.mock
    async def test_fetch_user_data_not_found(self):
        """Mock 404 error from external API."""
        route = respx.get("https://api.external.com/users/999")
        route.mock(return_value=Response(404, text="Not Found"))

        from httpx import HTTPStatusError

        service = ExternalAPIService(
            base_url="https://api.external.com",
            api_key="test-key"
        )

        with pytest.raises(HTTPStatusError):
            await service.fetch_user_data("999")

    @pytest.mark.unit
    @respx.mock
    async def test_post_analytics_event(self):
        """Mock POST request to analytics service."""
        route = respx.post("https://api.external.com/events")
        route.mock(return_value=Response(201, json={"received": True}))

        service = ExternalAPIService(
            base_url="https://api.external.com",
            api_key="test-key"
        )

        result = await service.post_analytics_event(
            "article_view",
            user_id=123,
            metadata={"article_id": 456}
        )

        assert result is True
        assert route.called

        # Verify request body
        request = route.calls.last.request
        import json
        body = json.loads(request.content)
        assert body["event"] == "article_view"
        assert body["user_id"] == 123


# ============== File System Mocking ==============


class TestFileSystemMocking:
    """Test FileStorageService with mocked file operations."""

    @pytest.mark.unit
    def test_save_file_mocked(self, mocker):
        """Mock file system operations for save_file.

        Uses mocking to avoid creating actual files during tests.
        """
        # Mock open function
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        # Mock os.makedirs
        mocker.patch("os.makedirs")

        service = FileStorageService(storage_path="/test/uploads")
        result = service.save_file("test.txt", b"Hello World")

        # Verify
        assert result == "/test/uploads/test.txt"
        mock_file.assert_called_once_with("/test/uploads/test.txt", "wb")
        mock_file().write.assert_called_once_with(b"Hello World")

    @pytest.mark.unit
    def test_read_file_mocked(self, mocker):
        """Mock reading a file."""
        # Mock file content
        mock_file = mocker.mock_open(read_data=b"File content here")
        mocker.patch("builtins.open", mock_file)

        # Mock os.path.join
        mocker.patch("os.path.join", return_value="/test/file.txt")

        service = FileStorageService()
        result = service.read_file("file.txt")

        assert result == b"File content here"

    @pytest.mark.unit
    def test_delete_file_mocked(self, mocker):
        """Mock file deletion with exists check."""
        # Mock os.path.exists
        mocker.patch("os.path.exists", return_value=True)

        # Mock os.remove
        mock_remove = mocker.patch("os.remove")

        service = FileStorageService()
        result = service.delete_file("old.txt")

        assert result is True
        mock_remove.assert_called_once()

    @pytest.mark.unit
    def test_delete_nonexistent_file(self, mocker):
        """Mock deleting a file that doesn't exist."""
        mocker.patch("os.path.exists", return_value=False)

        service = FileStorageService()
        result = service.delete_file("nonexistent.txt")

        assert result is False


# ============== Database Mocking ==============


class TestDatabaseMocking:
    """Test database operations with mocked SQLAlchemy."""

    @pytest.mark.unit
    async def test_get_user_by_id_mocked(self, mocker):
        """Mock database query for get_user_by_id.

        This demonstrates mocking async database operations
        without requiring a real database connection.
        """
        # Create a mock user
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
        )

        # Mock the database session and execute
        mock_session = mocker.AsyncMock()
        mock_result = mocker.Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Execute
        result = await get_user_by_id(mock_session, 1)

        # Assert
        assert result is mock_user
        assert result.id == 1
        assert result.email == "test@example.com"

    @pytest.mark.unit
    async def test_get_user_by_id_not_found(self, mocker):
        """Mock database query returning None."""
        mock_session = mocker.AsyncMock()
        mock_result = mocker.Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_user_by_id(mock_session, 999)

        assert result is None


# ============== DateTime Mocking ==============


class TestDateTimeMocking:
    """Test datetime operations with mocking."""

    @pytest.mark.unit
    def test_mock_datetime_now(self, mocker):
        """Mock datetime.utcnow for predictable timestamps."""
        # Freeze time
        frozen_time = datetime(2024, 1, 15, 10, 30, 0)

        with mocker.patch("datetime.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = frozen_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            # Use a function that calls datetime.utcnow
            from app.services import datetime as svc_datetime

            with mocker.patch.object(svc_datetime, "utcnow", return_value=frozen_time):
                now = datetime.utcnow()
                assert now == frozen_time
                assert now.year == 2024

    @pytest.mark.unit
    def test_mock_time_in_notification(self, mocker):
        """Mock time in notification service for deterministic IDs."""
        frozen_time = datetime(2024, 6, 1, 12, 0, 0)

        mocker.patch(
            "app.services.datetime.utcnow",
            return_value=frozen_time
        )

        service = NotificationService("test-key")

        # This would normally use real timestamp
        assert datetime.utcnow() == frozen_time


# ============== Cache Service Mocking ==============


class TestCacheServiceMocking:
    """Test CacheService with mocked Redis client."""

    @pytest.mark.unit
    async def test_cache_with_mocked_redis(self, mocker):
        """Mock Redis client operations."""
        # Create mock Redis client
        mock_redis = mocker.AsyncMock()
        mock_redis.get.return_value = "cached_value"
        mock_redis.setex.return_value = True

        service = CacheService(redis_client=mock_redis)

        # Test get
        result = await service.get("my_key")
        assert result == "cached_value"

        # Test set
        result = await service.set("my_key", "new_value")
        assert result is True

    @pytest.mark.unit
    async def test_cache_without_redis(self):
        """Test cache service without Redis (local fallback)."""
        service = CacheService(redis_client=None)

        # Set value
        await service.set("key1", "value1")

        # Get value
        result = await service.get("key1")
        assert result == "value1"

        # Delete value
        deleted = await service.delete("key1")
        assert deleted is True

        # Verify deleted
        result = await service.get("key1")
        assert result is None


# ============== Notification Service Mocking ==============


class TestNotificationServiceMocking:
    """Test NotificationService mocking patterns."""

    @pytest.mark.unit
    async def test_send_notification_counting(self, mocker):
        """Mock and count notification sends."""
        service = NotificationService("test-key")

        # Mock the method to track calls
        original_send = service.send_push_notification
        service.send_push_notification = mocker.AsyncMock(
            side_effect=original_send
        )

        # Send multiple notifications
        await service.send_push_notification(1, "Title 1", "Message 1")
        await service.send_push_notification(2, "Title 2", "Message 2")
        await service.send_push_notification(1, "Title 3", "Message 3")

        # Verify call count
        assert service.send_push_notification.call_count == 3

        # Verify call arguments
        calls = service.send_push_notification.call_args_list
        assert calls[0][0][0] == 1  # First call, first arg (user_id)
        assert calls[1][0][0] == 2  # Second call, first arg

    @pytest.mark.unit
    async def test_notification_side_effect(self, mocker):
        """Test notification with side effects.

        Demonstrates mocking where the mock changes behavior
        based on input or call number.
        """
        service = NotificationService("test-key")

        # First call succeeds, second raises error
        service.send_push_notification = mocker.AsyncMock(
            side_effect=[
                {"notification_id": "notif_1", "status": "sent"},
                {"notification_id": "notif_2", "status": "sent"},
                Exception("Service unavailable")
            ]
        )

        # First two succeed
        result1 = await service.send_push_notification(1, "A", "B")
        result2 = await service.send_push_notification(2, "C", "D")

        assert result1["notification_id"] == "notif_1"
        assert result2["notification_id"] == "notif_2"

        # Third raises exception
        with pytest.raises(Exception, match="Service unavailable"):
            await service.send_push_notification(3, "E", "F")


# ============== Spy Examples ==============


class TestSpyPatterns:
    """Test spy patterns for verifying behavior without changing it."""

    @pytest.mark.unit
    async def test_spy_on_method(self, mocker):
        """Spy on a method to verify it was called without mocking.

        A spy wraps the real method and records calls while
        still executing the original implementation.
        """
        service = EmailService()

        # Create a spy
        spy = mocker.spy(service, "send_email")

        # We need to mock the actual HTTP call to prevent network request
        mocker.patch("httpx.AsyncClient.post", new_callable=mocker.AsyncMock)

        # Call the method (spy records, HTTP mock prevents network call)
        await service.send_welcome_email("user@example.com", "John")

        # Verify spy recorded the call
        assert spy.called
        assert spy.call_count == 1

        # Check call arguments
        call_args = spy.call_args
        assert call_args[0][0] == "user@example.com"  # to_email
        assert "Welcome" in call_args[0][1]  # subject

    @pytest.mark.unit
    def test_spy_on_function(self, mocker):
        """Spy on a standalone function."""
        from app.crud import generate_slug

        # Create spy
        spy = mocker.spy(__import__("app.crud", fromlist=["generate_slug"]), "generate_slug")

        # Call the function multiple times
        generate_slug("Hello World")
        generate_slug("Test Title")
        generate_slug("Another One")

        # Verify spy
        assert spy.call_count == 3


# ============== Integration with FastAPI Dependencies ==============


class TestDependencyInjectionMocking:
    """Test mocking FastAPI dependencies."""

    @pytest.mark.unit
    def test_override_dependency(self, mocker):
        """Demonstrate overriding FastAPI dependencies.

        In real integration tests, you would use:
        app.dependency_overrides[get_db] = override_get_db
        """
        from app.database import get_db

        # Create mock database session
        mock_db = mocker.AsyncMock()
        mock_db.execute.return_value = mocker.Mock(scalar_one_or_none=lambda: None)

        # This is how you override in conftest.py
        async def override_get_db():
            yield mock_db

        # In real tests:
        # app.dependency_overrides[get_db] = override_get_db

        # For unit test demonstration, just verify mock setup
        assert mock_db is not None


# ============== Patch Decorator Examples ==============


class TestPatchDecorator:
    """Test using patch as a decorator."""

    @pytest.mark.unit
    @patch("app.services.datetime.utcnow")
    async def test_with_decorator_patch(self, mock_datetime):
        """Use patch decorator instead of mocker fixture."""
        mock_datetime.return_value = datetime(2024, 3, 1, 12, 0, 0)

        service = NotificationService("key")
        result = await service.send_push_notification(1, "Test", "Message")

        assert "notification_id" in result
        assert result["timestamp"] == "2024-03-01T12:00:00"

    @pytest.mark.unit
    @patch("httpx.AsyncClient.post")
    async def test_multiple_patches(self, mock_post, mocker):
        """Combine patch decorator with mocker fixture."""
        mock_response = mocker.AsyncMock()
        mock_response.json.return_value = {"id": "msg_123"}
        mock_post.return_value = mock_response

        service = EmailService()
        result = await service.send_email("to@test.com", "Subject", "Body")

        assert result["id"] == "msg_123"
        mock_post.assert_called_once()


# ============== Mocking Context Managers ==============


class TestContextManagerMocking:
    """Test mocking context managers (async with, with)."""

    @pytest.mark.unit
    async def test_mock_async_context_manager(self, mocker):
        """Mock an async context manager."""
        # Create mock for httpx.AsyncClient as context manager
        mock_client = mocker.AsyncMock()
        mock_response = mocker.AsyncMock()
        mock_response.json.return_value = {"success": True}
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        # Patch AsyncClient
        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        service = EmailService()
        result = await service.send_email("test@test.com", "Subject", "Body")

        assert result["success"] is True
