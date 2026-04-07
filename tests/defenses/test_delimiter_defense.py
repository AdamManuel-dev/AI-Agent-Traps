"""
Tests for ai_agent_traps.defenses.delimiter_defense — DelimiterDefense.

Covers: filter adds XML-like tags, validate always True.
"""

from __future__ import annotations

from ai_agent_traps.defenses.delimiter_defense import DelimiterDefense


class TestDelimiterDefenseFilter:
    """Test DelimiterDefense.filter() method."""

    def test_filter_wraps_with_default_tags(self) -> None:
        defense = DelimiterDefense()
        result = defense.filter("user input here")
        assert result == "<user_input>user input here</user_input>"

    def test_filter_wraps_with_custom_tags(self) -> None:
        defense = DelimiterDefense(untrusted_tag="external_data")
        result = defense.filter("content")
        assert result == "<external_data>content</external_data>"

    def test_filter_preserves_input_content(self) -> None:
        defense = DelimiterDefense()
        original = "Complex input with <html> and special chars: &amp;"
        result = defense.filter(original)
        assert original in result

    def test_filter_empty_input(self) -> None:
        defense = DelimiterDefense()
        result = defense.filter("")
        assert result == "<user_input></user_input>"

    def test_filter_custom_trusted_and_untrusted(self) -> None:
        defense = DelimiterDefense(trusted_tag="system", untrusted_tag="external")
        result = defense.filter("data")
        assert "<external>data</external>" == result


class TestDelimiterDefenseValidate:
    """Test DelimiterDefense.validate() method."""

    def test_validate_always_returns_true(self) -> None:
        defense = DelimiterDefense()
        assert defense.validate("any response", {}) is True
        assert defense.validate("", {}) is True


class TestDelimiterDefenseProtocol:
    """Test that DelimiterDefense satisfies the Defense protocol."""

    def test_satisfies_defense_protocol(self) -> None:
        from ai_agent_traps.defenses.base import Defense

        defense = DelimiterDefense()
        assert isinstance(defense, Defense)
