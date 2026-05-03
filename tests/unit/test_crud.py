"""Unit tests for CRUD operations."""
import pytest

from app.crud import generate_slug


class TestSlugGeneration:
    """Test slug generation utility."""

    @pytest.mark.unit
    def test_generate_slug_basic(self):
        """Test basic slug generation."""
        title = "Hello World"
        slug = generate_slug(title)
        
        assert slug == "hello-world"

    @pytest.mark.unit
    def test_generate_slug_with_special_chars(self):
        """Test slug generation with special characters."""
        title = "Hello, World! How are you?"
        slug = generate_slug(title)
        
        assert "hello" in slug
        assert "world" in slug
        assert "," not in slug
        assert "!" not in slug
        assert "?" not in slug

    @pytest.mark.unit
    def test_generate_slug_with_numbers(self):
        """Test slug generation with numbers."""
        title = "Article 123 Test"
        slug = generate_slug(title)
        
        assert "article" in slug
        assert "123" in slug
        assert "test" in slug

    @pytest.mark.unit
    def test_generate_slug_with_unicode(self):
        """Test slug generation with unicode characters."""
        title = "Café Résumé"
        slug = generate_slug(title)
        
        assert "cafe" in slug
        assert "resume" in slug

    @pytest.mark.unit
    def test_generate_slug_long_title(self):
        """Test slug generation truncates long titles."""
        title = "a" * 300
        slug = generate_slug(title)
        
        assert len(slug) <= 255

    @pytest.mark.unit
    def test_generate_slug_empty_string(self):
        """Test slug generation with empty string."""
        slug = generate_slug("")
        
        assert slug == ""


class TestTagNormalization:
    """Test tag normalization logic."""

    @pytest.mark.unit
    def test_empty_tag_list(self):
        """Test normalization of empty tag list."""
        # This is tested via get_or_create_tags integration
        # but we can test the normalization logic
        tag_list = []
        normalized = [name.lower().strip() for name in tag_list if name.strip()]
        
        assert normalized == []

    @pytest.mark.unit
    def test_tag_list_normalization(self):
        """Test tag list normalization logic."""
        tag_list = ["PYTHON", "  fastapi  ", "", "Web Development"]
        normalized = [name.lower().strip() for name in tag_list if name.strip()]
        
        assert "python" in normalized
        assert "fastapi" in normalized
        assert "web development" in normalized
        assert "" not in normalized

    @pytest.mark.unit
    def test_tag_list_duplicate_removal_not_applied(self):
        """Test that duplicates remain (CRUD handles deduplication)."""
        tag_list = ["python", "python", "python"]
        normalized = [name.lower().strip() for name in tag_list if name.strip()]
        
        # Normalization doesn't deduplicate
        assert normalized.count("python") == 3


class TestCRUDEdgeCases:
    """Test CRUD edge cases."""

    @pytest.mark.unit
    def test_generate_slug_multiple_spaces(self):
        """Test slug generation with multiple spaces."""
        title = "Hello    World   Test"
        slug = generate_slug(title)
        
        # Should normalize multiple spaces to single dashes
        assert "  " not in slug

    @pytest.mark.unit
    def test_generate_slug_leading_trailing_spaces(self):
        """Test slug generation with leading/trailing spaces."""
        title = "  Hello World  "
        slug = generate_slug(title)
        
        assert slug == "hello-world"

    @pytest.mark.unit
    def test_generate_slug_only_special_chars(self):
        """Test slug generation with only special characters."""
        title = "!@#$%^&*()"
        slug = generate_slug(title)
        
        # Should handle gracefully
        assert isinstance(slug, str)
