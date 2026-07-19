"""Tests for the lineage tracker."""

import json
import os
import tempfile
import pytest
from lineage_tracker import LineageTracker
from lineage_tracker.model import Model, Generation, BreedingRecord


@pytest.fixture
def tracker():
    """Create a tracker with a temp file."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)  # Start fresh — no file
    return LineageTracker(path)


@pytest.fixture
def populated_tracker(tracker):
    """Create a tracker with a small lineage tree.

    base-model
        ├── ft-v1 (lora)
        │   └── ft-v2 (full)
        └── ft-alt (distill)
    """
    tracker.record_breeding(
        parents=["base-model"],
        child_name="ft-v1",
        method="lora",
        metadata={"rank": 32},
        child_traits={"accuracy": 0.82},
    )
    tracker.record_breeding(
        parents=["ft-v1"],
        child_name="ft-v2",
        method="full",
        metadata={"epochs": 5},
        child_traits={"accuracy": 0.89},
    )
    tracker.record_breeding(
        parents=["base-model"],
        child_name="ft-alt",
        method="distill",
        metadata={"teacher": "large-model"},
        child_traits={"accuracy": 0.85, "speed": "fast"},
    )
    return tracker


class TestRecordBreeding:
    def test_creates_child_model(self, tracker):
        child = tracker.record_breeding(
            parents=["root-model"],
            child_name="child-1",
            method="lora",
        )
        assert child.name == "child-1"
        assert child.checksum is not None

    def test_auto_registers_unknown_parents(self, tracker):
        tracker.record_breeding(
            parents=["unknown-parent"],
            child_name="child-1",
        )
        assert "unknown-parent" in tracker.list_models()

    def test_records_method_and_metadata(self, tracker):
        tracker.record_breeding(
            parents=["root"],
            child_name="c1",
            method="merge",
            metadata={"strategy": "linear"},
        )
        records = tracker.list_breeding_records()
        assert len(records) == 1
        assert records[0].method == "merge"
        assert records[0].metadata["strategy"] == "linear"

    def test_requires_at_least_one_parent(self, tracker):
        with pytest.raises(ValueError, match="At least one parent"):
            tracker.record_breeding(parents=[], child_name="orphan")

    def test_multi_parent_merge(self, tracker):
        child = tracker.record_breeding(
            parents=["model-a", "model-b"],
            child_name="merged",
            method="merge",
        )
        assert child.name == "merged"
        records = tracker.list_breeding_records()
        assert len(records[-1].parents) == 2

    def test_checksum_is_deterministic(self, tracker):
        """Same inputs → same checksum."""
        c1 = tracker.record_breeding(
            parents=["root"], child_name="child", child_version="1.0"
        )
        # Re-create tracker with fresh store
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(path)
        t2 = LineageTracker(path)
        c2 = t2.record_breeding(
            parents=["root"], child_name="child", child_version="1.0"
        )
        assert c1.checksum == c2.checksum


class TestGetLineage:
    def test_traces_ancestry(self, populated_tracker):
        lineage = populated_tracker.get_lineage("ft-v2")
        names = {g.model.name for g in lineage}
        assert "ft-v2" in names
        assert "ft-v1" in names
        assert "base-model" in names

    def test_root_model_lineage(self, populated_tracker):
        lineage = populated_tracker.get_lineage("base-model")
        assert len(lineage) >= 1
        assert lineage[0].model.name == "base-model"

    def test_no_circular_infinite_loop(self, populated_tracker):
        """Should not loop forever on cyclic refs."""
        lineage = populated_tracker.get_lineage("ft-v2")
        # Should complete without hanging
        assert isinstance(lineage, list)

    def test_unknown_model(self, tracker):
        lineage = tracker.get_lineage("nonexistent")
        assert len(lineage) == 1
        assert lineage[0].model.version == "unknown"


class TestCompareGenerations:
    def test_finds_shared_ancestry(self, populated_tracker):
        diff = populated_tracker.compare_generations("ft-v1", "ft-alt")
        assert "base-model" in diff["shared_ancestry"]

    def test_generation_gap(self, populated_tracker):
        diff = populated_tracker.compare_generations("ft-v1", "ft-v2")
        assert diff["generation_gap"] >= 0

    def test_trait_differences(self, populated_tracker):
        diff = populated_tracker.compare_generations("ft-v1", "ft-alt")
        assert "accuracy" in diff["trait_differences"]

    def test_comparing_same_model(self, populated_tracker):
        diff = populated_tracker.compare_generations("ft-v1", "ft-v1")
        assert diff["generation_gap"] == 0


class TestRecommendBreeding:
    def test_returns_sorted_recommendations(self, populated_tracker):
        recs = populated_tracker.recommend_breeding("ft-v1", criteria="diversity")
        assert len(recs) > 0
        scores = [r["score"] for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_excludes_self(self, populated_tracker):
        recs = populated_tracker.recommend_breeding("ft-v1")
        assert all(r["partner"] != "ft-v1" for r in recs)

    def test_diversity_favors_distant(self, populated_tracker):
        recs = populated_tracker.recommend_breeding("ft-v1", criteria="diversity")
        # ft-alt shares only base-model, ft-v2 shares more lineage
        top = recs[0]["partner"]
        assert top in ("ft-alt", "base-model")

    def test_similarity_criteria(self, populated_tracker):
        recs = populated_tracker.recommend_breeding("ft-v1", criteria="similarity")
        assert len(recs) > 0
        # Most similar should be ft-v2 (direct child, shares ancestors)
        assert recs[0]["partner"] in ("ft-v2", "base-model")

    def test_invalid_criteria(self, populated_tracker):
        with pytest.raises(ValueError, match="Unknown criteria"):
            populated_tracker.recommend_breeding("ft-v1", criteria="magic")

    def test_unknown_model_raises(self, tracker):
        with pytest.raises(ValueError, match="Unknown model"):
            tracker.recommend_breeding("ghost")


class TestPersistence:
    def test_survives_reload(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(path)

        t1 = LineageTracker(path)
        t1.record_breeding(parents=["root"], child_name="c1", method="lora")

        t2 = LineageTracker(path)
        assert "c1" in t2.list_models()
        records = t2.list_breeding_records()
        assert len(records) == 1

    def test_json_structure(self, tracker):
        tracker.record_breeding(parents=["root"], child_name="c1")
        with open(tracker.store.path) as f:
            data = json.load(f)
        assert "models" in data
        assert "breeding_records" in data
        assert "generations" in data


class TestDataclasses:
    def test_model_defaults(self):
        m = Model(name="test")
        assert m.version == "1.0"
        assert m.traits == {}
        assert m.checksum is None

    def test_breeding_record_defaults(self):
        r = BreedingRecord(
            parents=["a"],
            child="b",
            method="lora",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert r.metadata == {}
        assert r.generation == 0

    def test_generation_fields(self):
        m = Model(name="x")
        g = Generation(model=m, generation=3)
        assert g.generation == 3
        assert g.model.name == "x"


class TestBugFixes:
    """Regression tests for bugs found during audit v0.1.1."""

    def test_reject_at_symbol_in_model_names(self, tracker):
        """Bug: @ character in model names broke name@version parsing."""
        with pytest.raises(ValueError, match="cannot contain"):
            tracker.record_breeding(parents=["model@bad"], child_name="child")
        with pytest.raises(ValueError, match="cannot contain"):
            tracker.record_breeding(parents=["parent"], child_name="child@bad")

    def test_pool_parameter_respects_empty_list(self, tracker):
        """Bug: pool=[] used default instead of respecting empty list."""
        tracker.record_breeding(parents=["root"], child_name="A", child_version="1.0")
        tracker.record_breeding(parents=["root"], child_name="B", child_version="1.0")
        # Empty pool should return empty list, not default candidates
        recs = tracker.recommend_breeding("A", pool=[])
        assert len(recs) == 0

    def test_generation_calculation_for_root_models(self, tracker):
        """Bug: auto-registered root models got incorrect generation values."""
        tracker.record_breeding(parents=["root"], child_name="A", child_version="1.0")
        tracker.record_breeding(parents=["A"], child_name="B", child_version="1.0")

        lineage = tracker.get_lineage("B")
        generations = {g.model.name: g.generation for g in lineage}

        # Root should have generation 0 (not 2 which was the bug)
        assert generations.get("root") == 0, f"Expected 0, got {generations.get('root')}"
        assert generations.get("A") == 1
        assert generations.get("B") == 2

    def test_get_model_returns_latest_version(self, tracker):
        """Bug: get_model returned first version instead of latest."""
        tracker.record_breeding(parents=["root"], child_name="model", child_version="1.0")
        tracker.record_breeding(parents=["root"], child_name="model", child_version="2.0")
        tracker.record_breeding(parents=["root"], child_name="model", child_version="3.0")

        model = tracker.store.get_model("model")
        assert model.version == "3.0", "Should return latest (most recently added) version"

    def test_timestamp_format_is_valid(self, tracker):
        """Verify timestamp uses non-deprecated datetime API."""
        tracker.record_breeding(parents=["root"], child_name="A", child_version="1.0")
        records = tracker.list_breeding_records()
        timestamp = records[0].timestamp
        # Should end with Z (UTC marker) not +00:00
        assert timestamp.endswith("Z"), f"Timestamp should end with Z, got {timestamp}"
        # Should be parseable
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None
