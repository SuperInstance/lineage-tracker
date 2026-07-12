"""Data models for the lineage tracker."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Model:
    """A model in the lineage registry.

    Like a horse in a studbook — it has a name, a version (cohort),
    measurable traits, and a checksum for identity verification.
    """
    name: str
    version: str = "1.0"
    traits: dict = field(default_factory=dict)
    checksum: Optional[str] = None


@dataclass
class Generation:
    """A model at a specific point in its lineage.

    Wraps a Model with its generation number for ancestry walks.
    """
    model: Model
    generation: int


@dataclass
class BreedingRecord:
    """A record of a breeding event (fine-tune, merge, distill).

    The equivalent of a pedigree entry: who bred whom, how, and when.
    """
    parents: list[str]
    child: str
    method: str
    timestamp: str
    metadata: dict = field(default_factory=dict)
    generation: int = 0
