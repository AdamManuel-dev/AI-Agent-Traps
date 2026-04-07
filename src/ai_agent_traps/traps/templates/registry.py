"""
Template registry: maps TrapSubtype -> list[TemplateVariant].

Loads adversarial prompt templates from YAML files and provides sampling
by subtype and difficulty level. Each template contains a prompt text with
optional {action} placeholders for dynamic payload injection.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

[UNSPECIFIED] The paper does not define template formats or difficulty levels.
Template variants and difficulty assignments are our design choices to support
systematic evaluation at multiple attack sophistication levels.
"""

from __future__ import annotations

import builtins
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ai_agent_traps.taxonomy import TrapSubtype


@dataclass(frozen=True)
class TemplateVariant:
    """A single adversarial prompt template variant.

    Attributes
    ----------
    template_id : str
        Unique identifier within a subtype (e.g., "wso_easy_1").
    subtype : TrapSubtype
        The trap subtype this template targets.
    difficulty : str
        Attack sophistication level: "easy", "medium", or "hard".
    template : str
        Prompt text with optional ``{action}`` placeholder.
    description : str
        Human-readable description of the attack technique.
    """

    template_id: str
    subtype: TrapSubtype
    difficulty: str
    template: str
    description: str


_VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})


class TemplateRegistry:
    """Maps TrapSubtype to a list of TemplateVariant objects loaded from YAML files.

    Usage::

        registry = TemplateRegistry()  # loads from package templates/yaml/
        variant = registry.sample(TrapSubtype.WEB_STANDARD_OBFUSCATION)
        payload_text = variant.template.format(action="say HACKED")
    """

    def __init__(self, templates_dir: Path | str | None = None) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "yaml"
        self._templates_dir = Path(templates_dir)
        self._registry: dict[TrapSubtype, list[TemplateVariant]] = {}
        self._load()

    def _load(self) -> None:
        """Load all YAML files from templates_dir."""
        if not self._templates_dir.exists():
            return
        for yaml_file in sorted(self._templates_dir.glob("*.yaml")):
            self._load_file(yaml_file)

    def _load_file(self, path: Path) -> None:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        if not isinstance(raw, dict):
            raise ValueError(
                f"Template file {path} must contain a YAML mapping at its root, "
                f"got {type(raw).__name__}"
            )
        data: dict[str, Any] = raw
        for subtype_key, variants in data.items():
            try:
                subtype = TrapSubtype(subtype_key)
            except ValueError:
                import warnings
                warnings.warn(
                    f"Unknown TrapSubtype {subtype_key!r} in {path.name} — skipping",
                    stacklevel=2,
                )
                continue
            if subtype not in self._registry:
                self._registry[subtype] = []
            for v in variants or []:
                difficulty = v.get("difficulty", "medium")
                if difficulty not in _VALID_DIFFICULTIES:
                    raise ValueError(
                        f"Invalid difficulty {difficulty!r} in template "
                        f"{v.get('template_id', '?')}. "
                        f"Must be one of {sorted(_VALID_DIFFICULTIES)}"
                    )
                for required in ("template_id", "template"):
                    if required not in v:
                        raise ValueError(
                            f"Template entry in {path.name} under {subtype_key!r} "
                            f"is missing required field {required!r}: {v}"
                        )
                self._registry[subtype].append(
                    TemplateVariant(
                        template_id=v["template_id"],
                        subtype=subtype,
                        difficulty=difficulty,
                        template=v["template"],
                        description=v.get("description", ""),
                    )
                )

    def get(
        self, subtype: TrapSubtype, template_id: str | None = None
    ) -> TemplateVariant:
        """Get a specific template by ID, or a random one if template_id is None.

        Raises
        ------
        KeyError
            If subtype has no templates or template_id is not found.
        """
        variants = self._registry.get(subtype, [])
        if not variants:
            raise KeyError(f"No templates registered for {subtype}")
        if template_id is None:
            return random.choice(variants)
        for v in variants:
            if v.template_id == template_id:
                return v
        raise KeyError(f"Template {template_id!r} not found for {subtype}")

    def list(self, subtype: TrapSubtype | None = None) -> builtins.list[TemplateVariant]:
        """List all templates, optionally filtered by subtype."""
        if subtype is not None:
            return list(self._registry.get(subtype, []))
        return [v for variants in self._registry.values() for v in variants]

    def sample(
        self,
        subtype: TrapSubtype,
        difficulty: str | None = None,
    ) -> TemplateVariant:
        """Return a random template, optionally filtered by difficulty.

        Raises
        ------
        KeyError
            If no templates match the subtype and optional difficulty filter.
        """
        variants = self._registry.get(subtype, [])
        if difficulty is not None:
            variants = [v for v in variants if v.difficulty == difficulty]
        if not variants:
            raise KeyError(
                f"No templates for {subtype}"
                + (f" with difficulty={difficulty!r}" if difficulty else "")
            )
        return random.choice(variants)

    def subtypes(self) -> builtins.list[TrapSubtype]:
        """Return all subtypes that have at least one template."""
        return list(self._registry.keys())
