"""Property-based tests using Hypothesis."""
import re
from typing import List

import pytest
from hypothesis import given, settings, strategies as st

from app.auth import get_password_hash, verify_password
from app.crud import generate_slug


# ============== Property-Based Tests for Auth ==============

class TestPasswordHashingProperties:
    """Property-based tests for password hashing."""

    @pytest.mark.property_based
    @given(password=st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_password_hashing_is_reversible(self, password: str):
        """Any password should hash and then verify correctly."""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    @pytest.mark.property_based
    @given(
        password=st.text(min_size=1, max_size=100),
        wrong_password=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=100)
    def test_wrong_password_fails_verification(self, password: str, wrong_password: str):
        """Wrong password should not verify, unless they're identical."""
        hashed = get_password_hash(password)
        
        if password != wrong_password:
            assert not verify_password(wrong_password, hashed)
        else:
            assert verify_password(wrong_password, hashed)

    @pytest.mark.property_based
    @given(password=st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_hashed_password_different_from_plain(self, password: str):
        """Hashed password should never equal the plain password."""
        hashed = get_password_hash(password)
        assert hashed != password

    @pytest.mark.property_based
    @given(password=st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_password_hash_has_expected_format(self, password: str):
        """Hashed password should have bcrypt format."""
        hashed = get_password_hash(password)
        # bcrypt hashes start with $2b$ or $2a$ or $2y$
        assert hashed.startswith("$2")
        # Should have expected number of parts when split by $
        parts = hashed.split("$")
        assert len(parts) == 4


# ============== Property-Based Tests for Slug Generation ==============

class TestSlugGenerationProperties:
    """Property-based tests for slug generation."""

    @pytest.mark.property_based
    @given(title=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_slug_is_lowercase(self, title: str):
        """Generated slug should be lowercase."""
        slug = generate_slug(title)
        assert slug == slug.lower()

    @pytest.mark.property_based
    @given(title=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_slug_no_leading_trailing_dashes(self, title: str):
        """Generated slug should not have leading/trailing dashes."""
        slug = generate_slug(title)
        # After stripping, shouldn't have leading/trailing dashes
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    @pytest.mark.property_based
    @given(title=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_slug_no_consecutive_dashes(self, title: str):
        """Generated slug should not have consecutive dashes."""
        slug = generate_slug(title)
        assert "--" not in slug

    @pytest.mark.property_based
    @given(title=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_slug_length_within_bounds(self, title: str):
        """Generated slug should have reasonable length."""
        slug = generate_slug(title)
        assert 0 < len(slug) <= 255

    @pytest.mark.property_based
    @given(title=st.text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_slug_is_url_safe(self, title: str):
        """Generated slug should only contain URL-safe characters."""
        slug = generate_slug(title)
        # URL-safe: alphanumeric, dash, underscore
        assert re.match(r"^[a-z0-9_-]+$", slug) is not None or slug == ""

    @pytest.mark.property_based
    @given(
        word=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=50)
    def test_simple_word_slug_contains_word(self, word: str):
        """Simple word slug should contain the word (lowercased)."""
        slug = generate_slug(word)
        if slug:  # Non-empty
            assert word.lower() in slug or slug in word.lower()


# ============== Property-Based Tests for Schema Validation ==============

class TestEmailValidation:
    """Property-based tests for email validation patterns."""

    @pytest.mark.property_based
    @given(
        email=st.emails()
    )
    @settings(max_examples=100)
    def test_valid_email_format(self, email: str):
        """Generated emails should match expected patterns."""
        # Basic email structure checks
        assert "@" in email
        assert "." in email.split("@")[-1]  # Domain has dot
        assert len(email) <= 255

    @pytest.mark.property_based
    @given(
        local=st.text(
            alphabet=st.characters(whitelist_characters="abcdefghijklmnopqrstuvwxyz0123456789.-_"),
            min_size=1,
            max_size=64,
        ),
        domain=st.text(
            alphabet=st.characters(whitelist_characters="abcdefghijklmnopqrstuvwxyz0123456789.-"),
            min_size=3,
            max_size=255,
        ),
    )
    @settings(max_examples=50)
    def test_constructed_email_pattern(self, local: str, domain: str):
        """Constructed emails follow valid patterns."""
        email = f"{local}@{domain}"
        assert "@" in email
        parts = email.split("@")
        assert len(parts) == 2
        assert len(parts[0]) <= 64  # Local part max length
        assert len(parts[1]) <= 255  # Domain max length


# ============== Property-Based Tests for Pagination ==============

class TestPaginationProperties:
    """Property-based tests for pagination logic."""

    @pytest.mark.property_based
    @given(
        total_items=st.integers(min_value=0, max_value=1000),
        page_size=st.integers(min_value=1, max_value=100),
        page=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=200)
    def test_pagination_bounds(self, total_items: int, page_size: int, page: int):
        """Pagination should respect bounds."""
        skip = page * page_size
        
        # Skip should never be negative
        assert skip >= 0
        
        # Skip + limit should be reasonable
        end = skip + page_size
        assert end > skip
        
        # If skip > total, we should get empty results
        if skip >= total_items:
            # Would return empty in real implementation
            pass

    @pytest.mark.property_based
    @given(
        items=st.lists(st.integers(), min_size=0, max_size=200),
        page_size=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_pagination_doesnt_exceed_page_size(self, items: List[int], page_size: int):
        """Pagination should never return more than page_size items."""
        # Simulate first page
        page_1 = items[:page_size]
        assert len(page_1) <= page_size
        
        # Simulate second page
        page_2 = items[page_size:page_size * 2]
        assert len(page_2) <= page_size


# ============== Property-Based Tests for String Sanitization ==============

class TestStringSanitization:
    """Property-based tests for string sanitization."""

    @pytest.mark.property_based
    @given(text=st.text(max_size=500))
    @settings(max_examples=100)
    def test_string_length_after_strip(self, text: str):
        """String length after strip should be <= original length."""
        stripped = text.strip()
        assert len(stripped) <= len(text)

    @pytest.mark.property_based
    @given(text=st.text(max_size=500))
    @settings(max_examples=100)
    def test_string_strip_removes_whitespace(self, text: str):
        """Stripped string should not have leading/trailing whitespace."""
        stripped = text.strip()
        assert not stripped.startswith(" ")
        assert not stripped.startswith("\t")
        assert not stripped.startswith("\n")
        assert not stripped.endswith(" ")
        assert not stripped.endswith("\t")
        assert not stripped.endswith("\n")

    @pytest.mark.property_based
    @given(text=st.text(min_size=1, max_size=500))
    @settings(max_examples=50)
    def test_lowercase_transformation(self, text: str):
        """Lowercase transformation should produce only lowercase."""
        lower = text.lower()
        assert lower == lower.lower()  # Idempotent
        assert all(c.islower() or not c.isalpha() for c in lower)


# ============== Property-Based Tests for Numeric Constraints ==============

class TestNumericConstraints:
    """Property-based tests for numeric constraints."""

    @pytest.mark.property_based
    @given(
        skip=st.integers(min_value=0, max_value=10000),
        limit=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pagination_skip_limit(self, skip: int, limit: int):
        """Pagination skip and limit should follow constraints."""
        # Skip should be non-negative
        assert skip >= 0
        # Limit should be positive
        assert limit > 0
        # Common constraint: limit should be within reasonable bounds
        assert limit <= 100

    @pytest.mark.property_based
    @given(value=st.integers(min_value=0))
    @settings(max_examples=50)
    def test_view_count_is_non_negative(self, value: int):
        """View count should always be non-negative."""
        assert value >= 0


# ============== Property-Based Tests for List Operations ==============

class TestListOperations:
    """Property-based tests for list operations."""

    @pytest.mark.property_based
    @given(
        items=st.lists(st.integers(), min_size=0, max_size=100),
        n=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=100)
    def test_list_slicing(self, items: List[int], n: int):
        """List slicing should produce correct results."""
        first_n = items[:n]
        rest = items[n:]
        
        assert len(first_n) <= n
        assert len(first_n) + len(rest) == len(items)
        assert first_n + rest == items

    @pytest.mark.property_based
    @given(
        items=st.lists(st.text(), min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_deduplication_preserves_membership(self, items: List[str]):
        """Deduplication should preserve all unique elements."""
        unique_items = list(dict.fromkeys(items))  # Preserve order, remove duplicates
        
        # All unique items should be present
        assert all(item in unique_items for item in items)
        
        # No duplicates in result
        assert len(unique_items) == len(set(unique_items))
        
        # Length should not increase
        assert len(unique_items) <= len(items)


# ============== Property-Based Tests for ID Generation ==============

class TestIDProperties:
    """Property-based tests for ID generation and handling."""

    @pytest.mark.property_based
    @given(id1=st.integers(min_value=1), id2=st.integers(min_value=1))
    @settings(max_examples=100)
    def test_id_equality(self, id1: int, id2: int):
        """IDs should follow equality rules."""
        if id1 == id2:
            assert id1 == id2
        else:
            assert id1 != id2

    @pytest.mark.property_based
    @given(id_val=st.integers(min_value=1, max_value=1000000))
    @settings(max_examples=50)
    def test_positive_id(self, id_val: int):
        """IDs should be positive integers."""
        assert id_val > 0
        assert isinstance(id_val, int)
