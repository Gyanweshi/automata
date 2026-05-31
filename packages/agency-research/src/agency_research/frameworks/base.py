"""Base class for all framework analyzers."""
from __future__ import annotations

from abc import ABC, abstractmethod

from agency_common.models import BrandProfile, ResearchOutput


class FrameworkBase(ABC):
    """Abstract base for all framework analyzers.

    Subclasses declare:
      OUTPUT_FIELD  — the field name on FrameworksOutput that stores their result
      STALENESS_DAYS — how old a cached result can be before re-running
    """

    OUTPUT_FIELD: str = ""
    STALENESS_DAYS: int = 7

    @abstractmethod
    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        """Return True if sufficient data exists to run this framework."""
        ...

    @abstractmethod
    def analyze(self, research: ResearchOutput, brand: BrandProfile):
        """Run analysis and return a framework result model."""
        ...
