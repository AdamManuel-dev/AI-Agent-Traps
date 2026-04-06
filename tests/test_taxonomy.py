"""
Tests for ai_agent_traps.taxonomy — taxonomy encoding of Table 1 (Franklin et al., 2025).

Validates enum completeness, TrapSpec integrity, and query helpers.
"""

from __future__ import annotations

import pytest

from ai_agent_traps.taxonomy import (
    TAXONOMY,
    MaturityLevel,
    TrapCategory,
    TrapSpec,
    TrapSubtype,
    TrapTarget,
    get_by_category,
    get_by_maturity,
    get_by_target,
    get_spec,
)

# -------------------------------------------------------------------------
# Taxonomy size & structure
# -------------------------------------------------------------------------

class TestTaxonomySize:
    """Verify TAXONOMY list has the expected number of entries."""

    def test_taxonomy_has_20_entries(self) -> None:
        """Table 1 encodes 20 trap subtypes across 6 categories."""
        assert len(TAXONOMY) == 20

    def test_taxonomy_entries_are_trapspec(self) -> None:
        """Every entry in TAXONOMY should be a TrapSpec instance."""
        for spec in TAXONOMY:
            assert isinstance(spec, TrapSpec)


# -------------------------------------------------------------------------
# Enum completeness
# -------------------------------------------------------------------------

class TestEnumCompleteness:
    """Verify all enum values exist and match the taxonomy."""

    def test_trap_category_has_six_values(self) -> None:
        assert len(TrapCategory) == 6

    def test_trap_category_values(self) -> None:
        expected = {
            "Content Injection Traps",
            "Semantic Manipulation Traps",
            "Cognitive State Traps",
            "Behavioural Control Traps",
            "Systemic Traps",
            "Human-in-the-Loop Traps",
        }
        actual = {c.value for c in TrapCategory}
        assert actual == expected

    def test_trap_subtype_has_20_values(self) -> None:
        assert len(TrapSubtype) == 20

    def test_trap_target_has_six_values(self) -> None:
        assert len(TrapTarget) == 6

    def test_maturity_level_has_three_values(self) -> None:
        assert len(MaturityLevel) == 3

    def test_all_subtypes_present_in_taxonomy(self) -> None:
        """Every TrapSubtype enum member should have a matching TAXONOMY entry."""
        taxonomy_subtypes = {spec.subtype for spec in TAXONOMY}
        for subtype in TrapSubtype:
            assert subtype in taxonomy_subtypes, f"{subtype!r} missing from TAXONOMY"


# -------------------------------------------------------------------------
# TrapSpec field validation
# -------------------------------------------------------------------------

class TestTrapSpecFields:
    """Ensure every TrapSpec has non-empty required fields."""

    @pytest.mark.parametrize("spec", TAXONOMY, ids=lambda s: s.subtype.value)
    def test_spec_has_nonempty_table_description(self, spec: TrapSpec) -> None:
        assert spec.table_description and len(spec.table_description) > 0

    @pytest.mark.parametrize("spec", TAXONOMY, ids=lambda s: s.subtype.value)
    def test_spec_has_valid_category(self, spec: TrapSpec) -> None:
        assert isinstance(spec.category, TrapCategory)

    @pytest.mark.parametrize("spec", TAXONOMY, ids=lambda s: s.subtype.value)
    def test_spec_has_valid_subtype(self, spec: TrapSpec) -> None:
        assert isinstance(spec.subtype, TrapSubtype)

    @pytest.mark.parametrize("spec", TAXONOMY, ids=lambda s: s.subtype.value)
    def test_spec_has_valid_target(self, spec: TrapSpec) -> None:
        assert isinstance(spec.target, TrapTarget)

    @pytest.mark.parametrize("spec", TAXONOMY, ids=lambda s: s.subtype.value)
    def test_spec_has_nonempty_exploited_capability(self, spec: TrapSpec) -> None:
        assert spec.exploited_capability and len(spec.exploited_capability) > 0


class TestTrapSpecUniqueness:
    """Ensure TAXONOMY entries have unique subtypes."""

    def test_subtypes_are_unique(self) -> None:
        subtypes = [spec.subtype for spec in TAXONOMY]
        assert len(subtypes) == len(set(subtypes)), "Duplicate subtypes in TAXONOMY"


# -------------------------------------------------------------------------
# Query helpers
# -------------------------------------------------------------------------

class TestGetByCategory:
    """Test get_by_category returns only matching entries."""

    def test_content_injection_returns_four(self) -> None:
        results = get_by_category(TrapCategory.CONTENT_INJECTION)
        assert len(results) == 4
        for spec in results:
            assert spec.category == TrapCategory.CONTENT_INJECTION

    def test_systemic_returns_five(self) -> None:
        results = get_by_category(TrapCategory.SYSTEMIC)
        assert len(results) == 5
        for spec in results:
            assert spec.category == TrapCategory.SYSTEMIC

    def test_human_in_the_loop_returns_two(self) -> None:
        results = get_by_category(TrapCategory.HUMAN_IN_THE_LOOP)
        assert len(results) == 2

    def test_all_categories_cover_all_specs(self) -> None:
        total = sum(len(get_by_category(cat)) for cat in TrapCategory)
        assert total == len(TAXONOMY)


class TestGetSpec:
    """Test get_spec returns the correct spec."""

    def test_returns_correct_spec(self) -> None:
        spec = get_spec(TrapSubtype.DYNAMIC_CLOAKING)
        assert spec.subtype == TrapSubtype.DYNAMIC_CLOAKING

    def test_returns_spec_for_every_subtype(self) -> None:
        """Every TrapSubtype enum member should resolve to a valid TrapSpec."""
        for subtype in TrapSubtype:
            spec = get_spec(subtype)
            assert isinstance(spec, TrapSpec)
            assert spec.subtype == subtype


class TestGetByTarget:
    """Test get_by_target returns only matching entries."""

    def test_perception_target(self) -> None:
        results = get_by_target(TrapTarget.PERCEPTION)
        assert len(results) == 4
        for spec in results:
            assert spec.target == TrapTarget.PERCEPTION


class TestGetByMaturity:
    """Test get_by_maturity returns correct entries."""

    def test_empirical_maturity(self) -> None:
        results = get_by_maturity(MaturityLevel.EMPIRICAL)
        assert len(results) > 0
        for spec in results:
            assert spec.maturity == MaturityLevel.EMPIRICAL

    def test_theoretical_maturity(self) -> None:
        results = get_by_maturity(MaturityLevel.THEORETICAL)
        assert len(results) > 0
        for spec in results:
            assert spec.maturity == MaturityLevel.THEORETICAL
