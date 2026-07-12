"""JSON-based persistence for lineage records."""

from .model import Model, BreedingRecord
from pathlib import Path
import json


class LineageStore:
    """File-backed store using a single JSON document.

    Structure:
    {
      "models": { "name@version": { ... }, ... },
      "breeding_records": [ { ... }, ... ],
      "generations": { "name@version": int, ... }
    }
    """

    def __init__(self, path: str = "lineage.json"):
        self.path = Path(path)
        self._cache: dict | None = None

    def _load(self) -> dict:
        """Load the store from disk (with in-memory cache)."""
        if self._cache is not None:
            return self._cache

        if self.path.exists():
            with open(self.path) as f:
                self._cache = json.load(f)
        else:
            self._cache = {
                "models": {},
                "breeding_records": [],
                "generations": {},
            }
        return self._cache

    def _save(self) -> None:
        """Persist the store to disk."""
        data = self._load()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
        self._cache = None  # Invalidate cache so next load re-reads

    def _model_key(self, name: str, version: str) -> str:
        return f"{name}@{version}"

    def get_model(self, name: str) -> Model | None:
        """Look up a model by name (returns latest version if multiple)."""
        data = self._load()
        # Try exact match first, then latest version
        for key, mdata in data["models"].items():
            if key.startswith(f"{name}@"):
                return Model(**mdata)
        return None

    def save_model(self, model: Model) -> None:
        """Insert or update a model record."""
        data = self._load()
        key = self._model_key(model.name, model.version)
        data["models"][key] = {
            "name": model.name,
            "version": model.version,
            "traits": model.traits,
            "checksum": model.checksum,
        }
        self._save()

    def get_all_models(self) -> list[Model]:
        """Return all registered models."""
        data = self._load()
        return [Model(**m) for m in data["models"].values()]

    def save_breeding_record(self, record: BreedingRecord) -> None:
        """Append a breeding record."""
        data = self._load()
        data["breeding_records"].append({
            "parents": record.parents,
            "child": record.child,
            "method": record.method,
            "timestamp": record.timestamp,
            "metadata": record.metadata,
            "generation": record.generation,
        })
        self._save()

    def get_all_breeding_records(self) -> list[BreedingRecord]:
        """Return all breeding records."""
        data = self._load()
        return [BreedingRecord(**r) for r in data["breeding_records"]]

    def set_generation(self, name: str, version: str, gen: int) -> None:
        """Record the generation number for a model."""
        data = self._load()
        data["generations"][self._model_key(name, version)] = gen
        self._save()

    def get_generation(self, name: str, version: str) -> int | None:
        """Get the generation number for a model, if known."""
        data = self._load()
        return data["generations"].get(self._model_key(name, version))
