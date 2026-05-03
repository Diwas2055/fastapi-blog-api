"""External service integrations with mockable interfaces.

This module contains external service calls that should be mocked in tests:
- Email sending
- External API calls
- File storage operations
- Payment processing
- Notification services

Example:
    # In production
    email_service = EmailService()
    await email_service.send_welcome_email(user)

    # In tests (mocked)
    mocker.patch("app.services.EmailService.send_email")
"""
from datetime import datetime
from typing import Optional

import httpx


class EmailService:
    """Service for sending emails via external provider.

    This class wraps email API calls to make them easily mockable in tests.

    Attributes:
        api_key: The email service API key.
        base_url: The email service API endpoint.
        sender: The default sender email address.
    """

    def __init__(
        self,
        api_key: str = "test-api-key",
        base_url: str = "https://api.emailservice.com/v1",
        sender: str = "noreply@example.com",
    ):
        """Initialize email service.

        Args:
            api_key: API key for authentication.
            base_url: Base URL for the email API.
            sender: Default sender email address.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.sender = sender

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> dict:
        """Send an email via the external API.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            body: Plain text email body.
            html_body: Optional HTML email body.

        Returns:
            API response containing message_id and status.

        Raises:
            httpx.HTTPError: If the API request fails.

        Example:
            >>> service = EmailService()
            >>> result = await service.send_email(
            ...     "user@example.com",
            ...     "Welcome!",
            ...     "Thanks for joining!"
            ... )
            >>> print(result["message_id"])
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/send",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.sender,
                    "to": to_email,
                    "subject": subject,
                    "text": body,
                    "html": html_body,
                },
            )
            response.raise_for_status()
            return response.json()

    async def send_welcome_email(self, user_email: str, username: str) -> dict:
        """Send a welcome email to a new user.

        Args:
            user_email: The new user's email address.
            username: The new user's username.

        Returns:
            API response from send_email.
        """
        return await self.send_email(
            to_email=user_email,
            subject="Welcome to FastAPI Blog!",
            body=f"Hi {username}, welcome to our platform!",
            html_body=f"<h1>Welcome {username}!</h1><p>We're glad you're here.</p>",
        )

    async def send_password_reset(
        self, user_email: str, reset_token: str
    ) -> dict:
        """Send a password reset email.

        Args:
            user_email: The user's email address.
            reset_token: The password reset token.

        Returns:
            API response from send_email.
        """
        reset_url = f"https://example.com/reset?token={reset_token}"
        return await self.send_email(
            to_email=user_email,
            subject="Password Reset Request",
            body=f"Click here to reset your password: {reset_url}",
            html_body=f'<a href="{reset_url}">Reset Password</a>',
        )


class ExternalAPIService:
    """Service for calling external REST APIs.

    Demonstrates mocking HTTP requests with pytest-respx or responses.

    Attributes:
        base_url: The external API base URL.
        api_key: API key for authentication.
    """

    def __init__(self, base_url: str, api_key: str):
        """Initialize the external API service.

        Args:
            base_url: Base URL for all API calls.
            api_key: Authentication key for the API.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def fetch_user_data(self, external_user_id: str) -> dict:
        """Fetch user data from external API.

        Args:
            external_user_id: The user's ID in the external system.

        Returns:
            User data dictionary from the external API.

        Raises:
            httpx.HTTPError: If the request fails or user not found.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{external_user_id}",
                headers={"X-API-Key": self.api_key},
            )
            response.raise_for_status()
            return response.json()

    async def post_analytics_event(
        self, event_name: str, user_id: int, metadata: Optional[dict] = None
    ) -> bool:
        """Post an analytics event to external service.

        Args:
            event_name: Name of the event to track.
            user_id: The user who triggered the event.
            metadata: Optional event metadata.

        Returns:
            True if event was successfully recorded.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/events",
                headers={"X-API-Key": self.api_key},
                json={
                    "event": event_name,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": metadata or {},
                },
            )
            return response.status_code == 201


class FileStorageService:
    """Service for file storage operations.

    Demonstrates mocking file system operations.

    Attributes:
        storage_path: Base path for file storage.
        max_file_size: Maximum allowed file size in bytes.
    """

    def __init__(self, storage_path: str = "/tmp/uploads", max_file_size: int = 10_000_000):
        """Initialize file storage service.

        Args:
            storage_path: Directory path for storing files.
            max_file_size: Maximum file size in bytes (default 10MB).
        """
        self.storage_path = storage_path
        self.max_file_size = max_file_size

    def save_file(self, filename: str, content: bytes) -> str:
        """Save a file to storage.

        Args:
            filename: Name to save the file as.
            content: Binary file content.

        Returns:
            Full path to the saved file.

        Raises:
            ValueError: If file exceeds max_file_size.
        """
        if len(content) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum of {self.max_file_size} bytes")

        import os

        os.makedirs(self.storage_path, exist_ok=True)
        file_path = os.path.join(self.storage_path, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    def read_file(self, filename: str) -> bytes:
        """Read a file from storage.

        Args:
            filename: Name of the file to read.

        Returns:
            Binary file content.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        import os

        file_path = os.path.join(self.storage_path, filename)

        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage.

        Args:
            filename: Name of the file to delete.

        Returns:
            True if file was deleted, False if it didn't exist.
        """
        import os

        file_path = os.path.join(self.storage_path, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


class NotificationService:
    """Service for sending push notifications.

    Demonstrates mocking with side effects and return value manipulation.

    Attributes:
        push_api_key: API key for push notification service.
    """

    def __init__(self, push_api_key: str):
        """Initialize notification service.

        Args:
            push_api_key: API key for push service.
        """
        self.push_api_key = push_api_key
        self._sent_notifications = []

    async def send_push_notification(
        self, user_id: int, title: str, message: str
    ) -> dict:
        """Send a push notification to a user.

        Args:
            user_id: The user ID to send notification to.
            title: Notification title.
            message: Notification body message.

        Returns:
            Response with notification_id and delivery_status.
        """
        # In production, this would call a push service API
        notification = {
            "notification_id": f"notif_{user_id}_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "title": title,
            "message": message,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._sent_notifications.append(notification)
        return notification

    def get_sent_notifications(self) -> list:
        """Get all sent notifications (for testing/auditing).

        Returns:
            List of all notifications sent by this service instance.
        """
        return self._sent_notifications.copy()


class CacheService:
    """Simple cache service wrapper.

    Demonstrates mocking with dependency injection.

    Attributes:
        redis_client: Redis client instance (can be mocked).
        default_ttl: Default time-to-live in seconds.
    """

    def __init__(self, redis_client=None, default_ttl: int = 300):
        """Initialize cache service.

        Args:
            redis_client: Redis client instance. Can be mocked for testing.
            default_ttl: Default expiration time in seconds.
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self._local_cache = {}  # Fallback for testing

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache.

        Args:
            key: Cache key to retrieve.

        Returns:
            Cached value or None if not found.
        """
        if self.redis:
            return await self.redis.get(key)
        return self._local_cache.get(key)

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to store.
            ttl: Time-to-live in seconds (uses default if not specified).

        Returns:
            True if value was stored successfully.
        """
        expiration = ttl or self.default_ttl

        if self.redis:
            return await self.redis.setex(key, expiration, value)

        self._local_cache[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if key existed and was deleted.
        """
        if self.redis:
            return await self.redis.delete(key) > 0

        if key in self._local_cache:
            del self._local_cache[key]
            return True
        return False
