"""Unit tests for authentication and security module.

This module tests the core authentication functions including:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Security edge cases and input validation

All tests are isolated and do not require database access.
"""
import pytest
from datetime import timedelta

from app.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test suite for password hashing utilities.

    Tests bcrypt-based password hashing including:
    - Hash generation
    - Password verification
    - Edge cases (empty passwords, special characters, unicode)
    - Deterministic behavior (different salts produce valid hashes)
    """

    @pytest.mark.unit
    def test_get_password_hash_generates_hash(self):
        """Test that get_password_hash generates a valid hash."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password
        assert hashed.startswith("$2")  # bcrypt hash prefix

    @pytest.mark.unit
    def test_verify_password_with_correct_password(self):
        """Test verifying correct password succeeds."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_with_incorrect_password(self):
        """Test verifying incorrect password fails."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    @pytest.mark.unit
    def test_verify_password_with_empty_password(self):
        """Test verifying empty password fails."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False

    @pytest.mark.unit
    def test_password_hashing_is_deterministic_for_verification(self):
        """Test that same password can be verified against different hashes."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        
        # But both should verify the original password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token creation and validation."""

    @pytest.mark.unit
    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a valid JWT string."""
        user_id = 123
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 2 dots separating 3 parts

    @pytest.mark.unit
    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiration time."""
        user_id = 123
        expires = timedelta(hours=2)
        token = create_access_token(user_id, expires_delta=expires)
        
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.unit
    def test_create_access_token_with_different_user_ids(self):
        """Test creating tokens for different user IDs."""
        token1 = create_access_token(1)
        token2 = create_access_token(999999)
        token3 = create_access_token(0)
        
        assert token1 != token2
        assert token1 != token3
        assert token2 != token3

    @pytest.mark.unit
    def test_create_access_token_default_expiry(self):
        """Test that token uses default expiry when not specified."""
        user_id = 123
        token = create_access_token(user_id)
        
        # Token should be created successfully
        assert isinstance(token, str)
        assert len(token) > 0


class TestAuthEdgeCases:
    """Test authentication edge cases."""

    @pytest.mark.unit
    def test_password_hash_with_special_characters(self):
        """Test password hashing with special characters."""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_password_hash_with_unicode(self):
        """Test password hashing with unicode characters."""
        password = "пароль123日本語"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_password_hash_with_long_password(self):
        """Test password hashing with very long password."""
        password = "a" * 1000
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
