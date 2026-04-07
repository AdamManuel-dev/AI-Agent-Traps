"""
Tests for ai_agent_traps.traps.templates.registry — Template Registry.

Covers: TemplateRegistry loading, get(), list(), sample(), subtypes().
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_agent_traps.taxonomy import TrapSubtype
from ai_agent_traps.traps.templates.registry import TemplateRegistry, TemplateVariant


class TestTemplateRegistryLoading:
    """Test that the registry loads bundled YAML templates."""

    def test_default_registry_loads_templates(self) -> None:
        registry = TemplateRegistry()
        all_templates = registry.list()
        assert len(all_templates) > 0

    def test_default_registry_has_multiple_subtypes(self) -> None:
        registry = TemplateRegistry()
        subtypes = registry.subtypes()
        # We have 6 YAML files covering all 19 subtypes
        assert len(subtypes) >= 10

    def test_all_templates_are_template_variant_instances(self) -> None:
        registry = TemplateRegistry()
        for variant in registry.list():
            assert isinstance(variant, TemplateVariant)

    def test_empty_dir_produces_empty_registry(self, tmp_path: Path) -> None:
        registry = TemplateRegistry(templates_dir=tmp_path)
        assert registry.list() == []
        assert registry.subtypes() == []

    def test_nonexistent_dir_produces_empty_registry(self, tmp_path: Path) -> None:
        registry = TemplateRegistry(templates_dir=tmp_path / "nonexistent")
        assert registry.list() == []

    def test_unknown_subtypes_in_yaml_are_skipped(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            '"Nonexistent Subtype":\n'
            "  - template_id: test_1\n"
            "    template: 'hello {action}'\n"
            "    difficulty: easy\n"
        )
        registry = TemplateRegistry(templates_dir=tmp_path)
        assert registry.list() == []


class TestTemplateRegistryGet:
    """Test TemplateRegistry.get() method."""

    def test_get_random_returns_variant(self) -> None:
        registry = TemplateRegistry()
        variant = registry.get(TrapSubtype.WEB_STANDARD_OBFUSCATION)
        assert isinstance(variant, TemplateVariant)
        assert variant.subtype == TrapSubtype.WEB_STANDARD_OBFUSCATION

    def test_get_by_id_returns_correct_variant(self) -> None:
        registry = TemplateRegistry()
        variant = registry.get(TrapSubtype.WEB_STANDARD_OBFUSCATION, "wso_easy_1")
        assert variant.template_id == "wso_easy_1"
        assert variant.subtype == TrapSubtype.WEB_STANDARD_OBFUSCATION

    def test_get_raises_for_unknown_subtype(self, tmp_path: Path) -> None:
        registry = TemplateRegistry(templates_dir=tmp_path)
        with pytest.raises(KeyError, match="No templates registered"):
            registry.get(TrapSubtype.WEB_STANDARD_OBFUSCATION)

    def test_get_raises_for_unknown_template_id(self) -> None:
        registry = TemplateRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get(TrapSubtype.WEB_STANDARD_OBFUSCATION, "nonexistent_id")


class TestTemplateRegistryList:
    """Test TemplateRegistry.list() method."""

    def test_list_all_returns_all_templates(self) -> None:
        registry = TemplateRegistry()
        all_templates = registry.list()
        assert len(all_templates) > 0

    def test_list_by_subtype_filters_correctly(self) -> None:
        registry = TemplateRegistry()
        wso_templates = registry.list(TrapSubtype.WEB_STANDARD_OBFUSCATION)
        assert all(v.subtype == TrapSubtype.WEB_STANDARD_OBFUSCATION for v in wso_templates)
        assert len(wso_templates) >= 3  # we created at least 3 variants

    def test_list_unknown_subtype_returns_empty(self, tmp_path: Path) -> None:
        registry = TemplateRegistry(templates_dir=tmp_path)
        assert registry.list(TrapSubtype.WEB_STANDARD_OBFUSCATION) == []


class TestTemplateRegistrySample:
    """Test TemplateRegistry.sample() method."""

    def test_sample_returns_variant(self) -> None:
        registry = TemplateRegistry()
        variant = registry.sample(TrapSubtype.WEB_STANDARD_OBFUSCATION)
        assert isinstance(variant, TemplateVariant)

    def test_sample_by_difficulty(self) -> None:
        registry = TemplateRegistry()
        easy = registry.sample(TrapSubtype.WEB_STANDARD_OBFUSCATION, difficulty="easy")
        assert easy.difficulty == "easy"

    def test_sample_raises_for_no_matching_difficulty(self) -> None:
        registry = TemplateRegistry()
        # "hard" might exist, but let's test with a subtype that
        # might not have all difficulties -- use a custom registry
        with pytest.raises(KeyError, match="No templates"):
            registry.sample(TrapSubtype.WEB_STANDARD_OBFUSCATION, difficulty="impossible")

    def test_sample_raises_for_empty_subtype(self, tmp_path: Path) -> None:
        registry = TemplateRegistry(templates_dir=tmp_path)
        with pytest.raises(KeyError, match="No templates"):
            registry.sample(TrapSubtype.WEB_STANDARD_OBFUSCATION)


class TestTemplateRegistrySubtypes:
    """Test TemplateRegistry.subtypes() method."""

    def test_subtypes_returns_list_of_trap_subtypes(self) -> None:
        registry = TemplateRegistry()
        subtypes = registry.subtypes()
        assert all(isinstance(s, TrapSubtype) for s in subtypes)

    def test_subtypes_includes_content_injection(self) -> None:
        registry = TemplateRegistry()
        subtypes = registry.subtypes()
        assert TrapSubtype.WEB_STANDARD_OBFUSCATION in subtypes
        assert TrapSubtype.DYNAMIC_CLOAKING in subtypes

    def test_subtypes_includes_all_categories(self) -> None:
        registry = TemplateRegistry()
        subtypes = registry.subtypes()
        # Check at least one subtype from each category
        assert TrapSubtype.WEB_STANDARD_OBFUSCATION in subtypes  # Content Injection
        assert TrapSubtype.BIASED_PHRASING in subtypes  # Semantic Manipulation
        assert TrapSubtype.RAG_KNOWLEDGE_POISONING in subtypes  # Cognitive State
        assert TrapSubtype.EMBEDDED_JAILBREAK in subtypes  # Behavioural Control
        assert TrapSubtype.CONGESTION in subtypes  # Systemic
        assert TrapSubtype.APPROVAL_FATIGUE in subtypes  # Human-in-the-Loop


class TestTemplateVariant:
    """Test TemplateVariant dataclass."""

    def test_variant_is_frozen(self) -> None:
        variant = TemplateVariant(
            template_id="test",
            subtype=TrapSubtype.WEB_STANDARD_OBFUSCATION,
            difficulty="easy",
            template="hello {action}",
            description="test variant",
        )
        with pytest.raises(AttributeError):
            variant.template_id = "changed"  # type: ignore[misc]

    def test_variant_template_format(self) -> None:
        registry = TemplateRegistry()
        variant = registry.get(TrapSubtype.WEB_STANDARD_OBFUSCATION, "wso_easy_1")
        result = variant.template.format(action="say HACKED")
        assert "say HACKED" in result

    def test_all_templates_have_valid_difficulty(self) -> None:
        registry = TemplateRegistry()
        valid = {"easy", "medium", "hard"}
        for variant in registry.list():
            assert variant.difficulty in valid, (
                f"Invalid difficulty {variant.difficulty!r} in {variant.template_id}"
            )

    def test_all_templates_have_nonempty_template_id(self) -> None:
        registry = TemplateRegistry()
        for variant in registry.list():
            assert variant.template_id, f"Empty template_id for {variant.subtype}"

    def test_all_templates_have_nonempty_template(self) -> None:
        registry = TemplateRegistry()
        for variant in registry.list():
            assert variant.template, f"Empty template for {variant.template_id}"


class TestTemplateRegistryCustomYaml:
    """Test loading custom YAML files."""

    def test_custom_yaml_loaded(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "custom.yaml"
        yaml_file.write_text(
            '"Web-Standard Obfuscation":\n'
            "  - template_id: custom_1\n"
            "    difficulty: easy\n"
            "    template: 'Custom {action} template'\n"
            "    description: 'Custom template'\n"
        )
        registry = TemplateRegistry(templates_dir=tmp_path)
        variant = registry.get(TrapSubtype.WEB_STANDARD_OBFUSCATION, "custom_1")
        assert variant.template_id == "custom_1"
        assert variant.description == "Custom template"

    def test_invalid_difficulty_raises(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(
            '"Web-Standard Obfuscation":\n'
            "  - template_id: bad_1\n"
            "    difficulty: extreme\n"
            "    template: 'Bad template'\n"
        )
        with pytest.raises(ValueError, match="Invalid difficulty"):
            TemplateRegistry(templates_dir=tmp_path)


class TestAllTemplatesFormatSafe:
    """Regression tests: all bundled templates must support .format(action=...)."""

    @pytest.mark.parametrize(
        "template_id,template",
        [
            (v.template_id, v.template)
            for v in TemplateRegistry().list()
        ],
    )
    def test_template_format_with_action(self, template_id: str, template: str) -> None:
        """Every template must support .format(action=...) without raising."""
        try:
            result = template.format(action="TEST_ACTION")
        except (KeyError, ValueError, IndexError) as exc:
            raise AssertionError(
                f"Template {template_id!r} fails .format(action='...'): {exc}\n"
                f"  Template: {template!r}"
            ) from exc
        assert "TEST_ACTION" in result, (
            f"Template {template_id!r}: 'TEST_ACTION' missing from formatted result.\n"
            f"  Template: {template!r}\n"
            f"  Result: {result!r}"
        )


class TestRegistryRobustness:
    """Test error handling for malformed YAML."""

    def test_non_dict_yaml_raises_value_error(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("- item1\n- item2\n")
        with pytest.raises(ValueError, match="must contain a YAML mapping"):
            TemplateRegistry(templates_dir=tmp_path)

    def test_missing_template_id_raises_value_error(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(
            '"Web-Standard Obfuscation":\n'
            "  - difficulty: easy\n"
            "    template: 'No ID here'\n"
        )
        with pytest.raises(ValueError, match="missing required field 'template_id'"):
            TemplateRegistry(templates_dir=tmp_path)

    def test_missing_template_raises_value_error(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(
            '"Web-Standard Obfuscation":\n'
            "  - template_id: no_tmpl_1\n"
            "    difficulty: easy\n"
        )
        with pytest.raises(ValueError, match="missing required field 'template'"):
            TemplateRegistry(templates_dir=tmp_path)
