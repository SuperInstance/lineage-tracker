# The Lineage Tracker

> Fine-tune provenance as bloodline records.

Track the lineage of fine-tuned models like a breeder tracks bloodlines. Every checkpoint, every merge, every fine-tune — recorded as a breeding record with full provenance.

## Features

- **Breeding Records** — Log every fine-tune event with parent(s), child, method, and metadata
- **Lineage Queries** — Trace any model's ancestry back through generations
- **Generation Comparison** — Diff capabilities across model generations
- **Breeding Recommendations** — Suggest optimal parent pairings based on traits and diversity

## Install

```bash
pip install lineage-tracker
```

## Quick Start

```python
from lineage_tracker import LineageTracker

tracker = LineageTracker("lineage.json")

# Record a breeding (fine-tune) event
child = tracker.record_breeding(
    parents=["base-llama-3-70b"],
    child_name="my-ft-v1",
    method="lora",
    metadata={"rank": 64, "dataset": "instruct-v2", "epochs": 3}
)

# Query lineage
lineage = tracker.get_lineage("my-ft-v1")
for gen in lineage:
    print(f"Generation {gen.generation}: {gen.model.name}")

# Compare generations
diff = tracker.compare_generations("my-ft-v1", "my-ft-v2")

# Get breeding recommendations
recs = tracker.recommend_breeding("my-ft-v1", criteria="diversity")
```

## Data Model

```
Model ──< BreedingRecord >── Model
  │                              │
  │ name                         │ timestamp
  │ version                      │ method (lora, full, merge, ...)
  │ traits                       │ metadata
  │ checksum                     │
```

## License

MIT
