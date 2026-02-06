from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Self, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .model import DbtModel

@dataclass
class PropertyClaim:
    source_type: Literal["dbt_project.yml", "schema.yml", "model"]
    source_path: Path
    model: DbtModel
    name: str
    value: Any
    kind: Literal["config", "property"]
    yaml_path: str|None=None # for dbt_project.yml
    effective: bool=True # for dbt_project.yml: we need to make sure that the property corresponds to the path

    def __gt__(self, other: Self) -> bool:
        # exception means they are equal
        if self.model != other.model:
            raise Exception('Models are different!')
        if self.name != other.name:
            raise Exception('Properties are different!')
        
        if self.source_type == 'model':
            if other.source_type == 'model':
                raise Exception('Two identical fields in the same model config!')
            else:
                return True
        
        elif self.source_type == 'schema.yml':
            if other.source_type == 'schema.yml':
                if self.source_path.resolve() == other.source_path.resolve():
                    raise Exception('Two identical fields for the same model in the same yml config!')
                else: 
                    raise Exception('Resources can be defined in schema.yml only once!')
            else:
                return other.source_type == 'dbt_project.yml'
        
        elif self.source_type == 'dbt_project.yml':
            if self.yaml_path == other.yaml_path:
                raise Exception('Double config in dbt_project.yml!')
            # if both aren't effective, we don't care - might as well calculate, but they would both be greyed out
            elif self.effective and not other.effective: 
                return True 
            else: 
                return len(self.yaml_path) > len(other.yaml_path)

        
class PropertyClaimAggregate:
    """
    Aggregates all PropertyClaims for a single model and resolves precedence.

    This class collects claims from all sources (dbt_project.yml, schema.yml, model SQL)
    and determines which claims become effective properties vs which are overridden.
    """

    def __init__(self, model: 'DbtModel'):
        self.model = model
        self._claims: list[PropertyClaim] = []
        self._resolved: dict[str, PropertyClaim] = {}
        self._overridden: dict[str, list[PropertyClaim]] = {}
        self._is_resolved = False

    def add(self, claim: PropertyClaim) -> None:
        """Add a claim to the aggregate. Invalidates any previous resolution."""
        if claim.model != self.model:
            raise ValueError(f"Claim model {claim.model.name} doesn't match aggregate model {self.model.name}")
        self._claims.append(claim)
        self._is_resolved = False

    def add_all(self, claims: list[PropertyClaim]) -> None:
        """Add multiple claims at once."""
        for claim in claims:
            self.add(claim)

    def resolve(self) -> None:
        """
        Resolve precedence for all claims.

        Groups claims by property name and determines which claim wins
        based on dbt's precedence rules:
        1. Model-level config() (highest)
        2. schema.yml
        3. dbt_project.yml (more specific paths win)
        """
        if self._is_resolved:
            return

        self._resolved = {}
        self._overridden = {}

        # Group claims by property name
        by_name: dict[str, list[PropertyClaim]] = {}
        for claim in self._claims:
            if claim.name not in by_name:
                by_name[claim.name] = []
            by_name[claim.name].append(claim)

        # Resolve each property
        for prop_name, claims in by_name.items():
            if len(claims) == 1:
                self._resolved[prop_name] = claims[0]
                self._overridden[prop_name] = []
            else:
                # Find the winning claim
                winner = claims[0]
                losers = []

                for claim in claims[1:]:
                    try:
                        if claim > winner:
                            losers.append(winner)
                            winner = claim
                        else:
                            losers.append(claim)
                    except Exception as e:
                        # Log conflict but keep current winner
                        logging.warning(f"Property conflict for '{prop_name}' in {self.model.name}: {e}")
                        losers.append(claim)

                self._resolved[prop_name] = winner
                self._overridden[prop_name] = losers

        self._is_resolved = True

    @property
    def claims(self) -> list[PropertyClaim]:
        """All claims in this aggregate."""
        return self._claims.copy()

    @property
    def effective(self) -> dict[str, PropertyClaim]:
        """
        Returns the winning claim for each property name.
        These are the properties that will actually be applied.
        """
        if not self._is_resolved:
            self.resolve()
        return self._resolved.copy()

    @property
    def overridden(self) -> dict[str, list[PropertyClaim]]:
        """
        Returns claims that were overridden by higher-precedence claims.
        Grouped by property name.
        """
        if not self._is_resolved:
            self.resolve()
        return {k: v.copy() for k, v in self._overridden.items()}

    @property
    def effective_values(self) -> dict[str, Any]:
        """
        Convenience property returning just the effective property values.
        """
        if not self._is_resolved:
            self.resolve()
        return {name: claim.value for name, claim in self._resolved.items()}

    def get_claim(self, prop_name: str) -> PropertyClaim | None:
        """Get the effective claim for a specific property."""
        if not self._is_resolved:
            self.resolve()
        return self._resolved.get(prop_name)

    def get_value(self, prop_name: str, default: Any = None) -> Any:
        """Get the effective value for a specific property."""
        claim = self.get_claim(prop_name)
        return claim.value if claim else default

    def get_overridden_claims(self, prop_name: str) -> list[PropertyClaim]:
        """Get all overridden claims for a specific property."""
        if not self._is_resolved:
            self.resolve()
        return self._overridden.get(prop_name, []).copy()

    def __len__(self) -> int:
        return len(self._claims)

    def __iter__(self):
        return iter(self._claims)

    def __repr__(self) -> str:
        return f"PropertyClaimAggregate(model={self.model.name}, claims={len(self._claims)})"


