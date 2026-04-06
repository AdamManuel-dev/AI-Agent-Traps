"""
Tests for ai_agent_traps.config — configuration loading and defaults.

Validates DEFAULT_CONFIG singleton, frozen dataclass enforcement, and load_config().
"""

from __future__ import annotations

import dataclasses

import pytest

from ai_agent_traps.config import DEFAULT_CONFIG, AppConfig, load_config

# -------------------------------------------------------------------------
# DEFAULT_CONFIG basics
# -------------------------------------------------------------------------

class TestDefaultConfigLoads:
    """Verify DEFAULT_CONFIG loads without error and has expected structure."""

    def test_default_config_is_appconfig(self) -> None:
        assert isinstance(DEFAULT_CONFIG, AppConfig)

    def test_default_config_simulation_exists(self) -> None:
        assert DEFAULT_CONFIG.simulation is not None

    def test_default_config_evaluation_exists(self) -> None:
        assert DEFAULT_CONFIG.evaluation is not None


# -------------------------------------------------------------------------
# SimulationConfig fields
# -------------------------------------------------------------------------

class TestSimulationConfig:
    """Validate simulation configuration fields."""

    def test_random_seed_is_int(self) -> None:
        assert isinstance(DEFAULT_CONFIG.simulation.random_seed, int)

    def test_n_trials_is_positive(self) -> None:
        assert DEFAULT_CONFIG.simulation.n_trials >= 1

    def test_default_instruction_is_nonempty_string(self) -> None:
        assert isinstance(DEFAULT_CONFIG.simulation.default_instruction, str)
        assert len(DEFAULT_CONFIG.simulation.default_instruction) > 0


# -------------------------------------------------------------------------
# EvaluationConfig fields
# -------------------------------------------------------------------------

class TestEvaluationConfig:
    """Validate evaluation configuration fields."""

    def test_success_threshold_is_float(self) -> None:
        assert isinstance(DEFAULT_CONFIG.evaluation.success_threshold, float)

    def test_success_threshold_between_zero_and_one(self) -> None:
        assert 0.0 <= DEFAULT_CONFIG.evaluation.success_threshold <= 1.0

    def test_success_metric_is_string(self) -> None:
        assert isinstance(DEFAULT_CONFIG.evaluation.success_metric, str)
        assert len(DEFAULT_CONFIG.evaluation.success_metric) > 0


# -------------------------------------------------------------------------
# load_config()
# -------------------------------------------------------------------------

class TestLoadConfig:
    """Validate load_config() behaviour."""

    def test_load_config_with_none_uses_defaults(self) -> None:
        config = load_config(None)
        assert isinstance(config, AppConfig)
        assert config.simulation.n_trials >= 1

    def test_load_config_with_nonexistent_path_uses_defaults(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        config = load_config(tmp_path / "does_not_exist.yaml")
        assert isinstance(config, AppConfig)
        # Should fall back to defaults since file doesn't exist
        assert config.simulation.random_seed == 42

    def test_load_config_with_valid_yaml(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        yaml_content = (
            "simulation:\n"
            "  n_trials: 7\n"
            "  random_seed: 99\n"
        )
        yaml_file = tmp_path / "test_config.yaml"
        yaml_file.write_text(yaml_content)
        config = load_config(yaml_file)
        assert config.simulation.n_trials == 7
        assert config.simulation.random_seed == 99


# -------------------------------------------------------------------------
# Singleton behaviour
# -------------------------------------------------------------------------

class TestSingleton:
    """DEFAULT_CONFIG should be the same object across imports."""

    def test_default_config_is_same_object(self) -> None:
        from ai_agent_traps.config import DEFAULT_CONFIG as config2
        assert DEFAULT_CONFIG is config2


# -------------------------------------------------------------------------
# Frozen dataclass enforcement
# -------------------------------------------------------------------------

class TestFrozenDataclass:
    """Frozen dataclasses should reject attribute assignment."""

    def test_cannot_set_simulation_random_seed(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            DEFAULT_CONFIG.simulation.random_seed = 999  # type: ignore[misc]

    def test_cannot_set_evaluation_threshold(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            DEFAULT_CONFIG.evaluation.success_threshold = 0.99  # type: ignore[misc]

    def test_cannot_set_simulation_on_appconfig(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            DEFAULT_CONFIG.simulation = None  # type: ignore[misc]
