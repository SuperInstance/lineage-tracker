"""LineageTracker — fine-tune provenance as bloodline records."""

from .model import Model, Generation, BreedingRecord
from .store import LineageStore
from datetime import datetime, timezone
from typing import Optional
import hashlib


class LineageTracker:
    """Track fine-tune provenance as structured breeding records.

    Think of it as a pedigree registry for models: every fine-tune,
    merge, or distillation is recorded as a breeding event with full
    ancestry tracking.
    """

    def __init__(self, path: str = "lineage.json"):
        """Initialize the tracker with a JSON store path.

        Args:
            path: Path to the JSON file used for persistence.
        """
        self.store = LineageStore(path)

    def record_breeding(
        self,
        parents: list[str],
        child_name: str,
        method: str = "full",
        metadata: Optional[dict] = None,
        child_version: str = "1.0",
        child_traits: Optional[dict] = None,
    ) -> Model:
        """Record a breeding (fine-tune) event.

        Creates a child Model linked to one or more parent models via
        a BreedingRecord.

        Args:
            parents: List of parent model names.
            child_name: Name for the new child model.
            method: Breeding method — 'lora', 'full', 'merge', 'distill', etc.
            metadata: Arbitrary metadata (hyperparams, dataset, etc.).
            child_version: Version string for the child model.
            child_traits: Trait dict for the child (e.g. benchmark scores).

        Returns:
            The newly created child Model.
        """
        if not parents:
            raise ValueError("At least one parent is required")

        # Validate model names don't contain '@' (used as separator in references)
        if "@" in child_name:
            raise ValueError("Model names cannot contain '@' character")
        for pname in parents:
            if "@" in pname:
                raise ValueError("Model names cannot contain '@' character")

        # Resolve parent models
        parent_models = []
        for pname in parents:
            pmodel = self.store.get_model(pname)
            if pmodel is None:
                # Auto-register unknown parents as root models
                pmodel = Model(name=pname, version="unknown")
                self.store.save_model(pmodel)
            parent_models.append(pmodel)

        # Determine child generation
        max_gen = max(
            (self.store.get_generation(pm.name, pm.version) or 0
             for pm in parent_models),
            default=0,
        )
        child_gen = max_gen + 1

        # Create child model
        # Include parent versions in checksum for true provenance uniqueness
        parent_refs = [f"{pm.name}@{pm.version}" for pm in parent_models]
        checksum_input = f"{child_name}:{child_version}:{':'.join(parent_refs)}"
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:16]
        child = Model(
            name=child_name,
            version=child_version,
            traits=child_traits or {},
            checksum=checksum,
        )

        # Create breeding record
        record = BreedingRecord(
            parents=[f"{pm.name}@{pm.version}" for pm in parent_models],
            child=f"{child.name}@{child.version}",
            method=method,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            metadata=metadata or {},
            generation=child_gen,
        )

        self.store.save_model(child)
        self.store.save_breeding_record(record)
        self.store.set_generation(child.name, child.version, child_gen)

        return child

    def get_lineage(self, model_name: str) -> list[Generation]:
        """Trace the full lineage of a model back to its roots.

        Returns a list of Generation objects, ordered from the model
        itself (generation 0 relative) back through ancestors.
        """
        result: list[Generation] = []
        visited: set[str] = set()
        self._trace_lineage(model_name, result, visited, depth=0)
        return result

    def _trace_lineage(
        self,
        model_name: str,
        result: list[Generation],
        visited: set[str],
        depth: int,
    ) -> None:
        if model_name in visited:
            return
        visited.add(model_name)

        model = self.store.get_model(model_name)
        if model is None:
            result.append(Generation(
                model=Model(name=model_name, version="unknown"),
                generation=depth,
            ))
            return

        # Get stored generation, or 0 for auto-registered root models,
        # or depth for completely unknown models
        gen = self.store.get_generation(model.name, model.version)
        if gen is None:
            gen = 0 if model.version == "unknown" else depth
        result.append(Generation(model=model, generation=gen))

        # Find direct parents
        for record in self.store.get_all_breeding_records():
            if record.child.split("@")[0] == model_name or record.child == model_name:
                for parent_ref in record.parents:
                    parent_name = parent_ref.split("@")[0]
                    self._trace_lineage(parent_name, result, visited, depth + 1)

    def compare_generations(
        self, model_a: str, model_b: str
    ) -> dict:
        """Compare two models across generations.

        Returns a dict with trait diffs, shared ancestry, and generation gap.
        """
        lineage_a = self.get_lineage(model_a)
        lineage_b = self.get_lineage(model_b)

        names_a = {g.model.name for g in lineage_a}
        names_b = {g.model.name for g in lineage_b}
        shared = names_a & names_b

        ma = self.store.get_model(model_a)
        mb = self.store.get_model(model_b)

        traits_a = ma.traits if ma else {}
        traits_b = mb.traits if mb else {}

        trait_diff = {}
        all_keys = set(traits_a) | set(traits_b)
        for key in all_keys:
            va = traits_a.get(key)
            vb = traits_b.get(key)
            if va != vb:
                trait_diff[key] = {"a": va, "b": vb}

        gen_a = max((g.generation for g in lineage_a), default=0)
        gen_b = max((g.generation for g in lineage_b), default=0)

        return {
            "model_a": model_a,
            "model_b": model_b,
            "generation_gap": abs(gen_a - gen_b),
            "shared_ancestry": sorted(shared),
            "trait_differences": trait_diff,
            "lineage_depth_a": len(lineage_a),
            "lineage_depth_b": len(lineage_b),
        }

    def recommend_breeding(
        self,
        model_name: str,
        criteria: str = "diversity",
        pool: Optional[list[str]] = None,
    ) -> list[dict]:
        """Recommend breeding partners for a model.

        Uses trait complementarity and lineage diversity to suggest
        optimal pairings.

        Args:
            model_name: The model to find partners for.
            criteria: 'diversity' (maximize genetic distance) or
                      'similarity' (find closest relatives).
            pool: Optional candidate pool. Defaults to all known models.

        Returns:
            Sorted list of recommendations with scores and reasoning.
        """
        target = self.store.get_model(model_name)
        if target is None:
            raise ValueError(f"Unknown model: {model_name}")

        target_lineage = {g.model.name for g in self.get_lineage(model_name)}

        candidates = pool if pool is not None else [
            m.name for m in self.store.get_all_models() if m.name != model_name
        ]

        scores: list[dict] = []
        for candidate_name in candidates:
            if candidate_name == model_name:
                continue

            candidate = self.store.get_model(candidate_name)
            if candidate is None:
                continue

            cand_lineage = {g.model.name for g in self.get_lineage(candidate_name)}
            shared = target_lineage & cand_lineage

            # Diversity score: lower overlap = higher score
            union = target_lineage | cand_lineage
            overlap_ratio = len(shared) / len(union) if union else 1.0

            if criteria == "diversity":
                score = 1.0 - overlap_ratio
                reason = f"Low ancestry overlap ({overlap_ratio:.0%})"
            elif criteria == "similarity":
                score = overlap_ratio
                reason = f"High ancestry overlap ({overlap_ratio:.0%})"
            else:
                raise ValueError(f"Unknown criteria: {criteria}")

            # Trait complementarity bonus
            trait_keys = set(target.traits) | set(candidate.traits)
            complementary = 0
            for key in trait_keys:
                tv = target.traits.get(key)
                cv = candidate.traits.get(key)
                if tv is not None and cv is not None and tv != cv:
                    complementary += 1

            if trait_keys:
                score *= 1.0 + 0.1 * (complementary / len(trait_keys))

            scores.append({
                "partner": candidate_name,
                "score": round(score, 4),
                "shared_ancestry": len(shared),
                "reason": reason,
                "complementary_traits": complementary,
            })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores

    def list_models(self) -> list[str]:
        """List all registered model names."""
        return [m.name for m in self.store.get_all_models()]

    def list_breeding_records(self) -> list[BreedingRecord]:
        """List all breeding records."""
        return self.store.get_all_breeding_records()
