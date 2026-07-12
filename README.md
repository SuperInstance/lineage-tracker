# The Lineage Tracker

> Fine-tune provenance as bloodline records. Every checkpoint, every merge, every fine-tune — traceable like a breeder's studbook.

[![Python](https://img.shields.io/python/required-version-toml?toml=pyproject.toml)](https://python.org)
[![License](https://img.shields.io/github/license/SuperInstance/lineage-tracker)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

Every model has a family tree. Base models beget fine-tunes. Fine-tunes beget merges. Merges beget quantizations. After three layers of adaptation, nobody remembers who descended from whom — or whether that merge you're about to deploy has a known-broken checkpoint in its ancestry. Lineage Tracker treats this seriously, recording every fine-tune event as a structured breeding record with full provenance, checksums, and trait tracking.

## What It Does

Lineage Tracker maintains a JSON-backed registry of models and their breeding history. Every fine-tune, merge, distillation, or continued pre-training is recorded as a `BreedingRecord` that links parents to children with method metadata (LoRA rank, dataset, epochs, merge strategy). Models carry traits (benchmark scores, capabilities, known limitations) and checksums for identity verification.

The tracker supports lineage queries — walk any model's ancestry back through generations, compare capabilities across sibling checkpoints, and get breeding recommendations for diversity. This matters because blind fine-tuning is how capability regressions sneak into production. If your customer-facing model suddenly can't do math, you need to know: was it the merge? The adapter? The base model upgrade? Lineage tracking turns that detective work into a single query.

The core equation from Working Animal Architecture is **γ + η = C** (genome + nurture = capability). Lineage tracking is the **γ** — the genome, the bloodline record that makes selective breeding possible. Without it, you're doing random mutations and hoping for the best.

## Install

```bash
pip install lineage-tracker
```

For development:

```bash
git clone https://github.com/SuperInstance/lineage-tracker.git
cd lineage-tracker
pip install -e ".[dev]"
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
    metadata={
        "rank": 64,
        "dataset": "instruct-v2",
        "epochs": 3,
        "learning_rate": 2e-4,
    },
    child_traits={
        "mmlu": 82.3,
        "human_eval": 71.5,
        "gsm8k": 78.1,
    },
)

# Query lineage — walk ancestry back through generations
lineage = tracker.get_lineage("my-ft-v1")
for gen in lineage:
    print(f"Generation {gen.generation}: {gen.model.name} (v{gen.model.version})")
    if gen.model.traits:
        print(f"  Traits: {gen.model.traits}")

# Compare two siblings
diff = tracker.compare_generations("my-ft-v1", "my-ft-v2")
print(diff.summary)

# Get breeding recommendations based on trait diversity
recs = tracker.recommend_breeding("my-ft-v1", criteria="diversity")
for rec in recs[:3]:
    print(f"  Pair with: {rec.model_name} (diversity: {rec.score:.2f})")
```

## Data Model

```
Model                    BreedingRecord
├── name                 ├── parents: list[str]
├── version              ├── child: str
├── traits: dict         ├── method: str (lora|full|merge|distill|...)
├── checksum: str        ├── timestamp: str
                         ├── metadata: dict
Generation               └── generation: int
├── model: Model
└── generation: int
```

### JSON Store Structure

```json
{
  "models": {
    "my-ft-v1@1.0": {
      "name": "my-ft-v1",
      "version": "1.0",
      "traits": {"mmlu": 82.3, "human_eval": 71.5},
      "checksum": "a1b2c3d4e5f6g7h8"
    }
  },
  "breeding_records": [
    {
      "parents": ["base-llama-3-70b"],
      "child": "my-ft-v1",
      "method": "lora",
      "timestamp": "2026-07-12T14:30:00Z",
      "metadata": {"rank": 64, "dataset": "instruct-v2"},
      "generation": 1
    }
  ],
  "generations": {
    "my-ft-v1@1.0": 1
  }
}
```

## API Reference

### `LineageTracker`

```python
class LineageTracker:
    def __init__(self, path: str = "lineage.json")

    # Recording
    def record_breeding(
        self,
        parents: list[str],
        child_name: str,
        method: str = "full",
        metadata: dict | None = None,
        child_version: str = "1.0",
        child_traits: dict | None = None,
    ) -> Model

    # Querying
    def get_lineage(self, name: str) -> list[Generation]
    def get_model(self, name: str) -> Model | None
    def get_all_models(self) -> list[Model]
    def compare_generations(self, a: str, b: str) -> GenerationDiff
    def recommend_breeding(self, name: str, criteria: str = "diversity") -> list[Recommendation]
```

### Breeding Methods

| Method | Description |
|--------|-------------|
| `full` | Full-parameter fine-tuning |
| `lora` | LoRA / QLoRA adapter training |
| `merge` | Model merging (SLERP, DARE, TIES, linear) |
| `distill` | Knowledge distillation from teacher to student |
| `continue_pretrain` | Continued pre-training on new domain data |
| `rlhf` | Reinforcement learning from human feedback |
| `sft` | Supervised fine-tuning |

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v

# Run specific test modules
pytest tests/test_tracker.py -v
pytest tests/test_store.py -v
```

## Philosophy

Selective breeding changed civilization. The ability to record lineage, track traits across generations, and make informed pairing decisions is what separated agriculture from hunting-gathering. Lineage Tracker brings that same leap to AI — transforming model development from ad-hoc experimentation into a disciplined breeding program.

This is the γ (genome) half of γ + η = C. Without lineage records, you can't do selective breeding — you're just hoping each fine-tune is better than the last. With lineage records, you can identify which breeding strategies produce the best offspring, avoid reinforcing known weaknesses, and build a structured improvement program.

For more on the breeding paradigm in AI, see [AI-Writings](https://github.com/SuperInstance/AI-Writings).

## Ecosystem

| Repo | Role |
|------|------|
| **[lineage-tracker](https://github.com/SuperInstance/lineage-tracker)** | **This repo** — provenance tracking |
| [pedigree](https://github.com/SuperInstance/pedigree) | Bloodline tracking with inbreeding coefficients and visualization |
| [breed-registry](https://github.com/SuperInstance/breed-registry) | Breed assessment and task matching |
| [baton](https://github.com/SuperInstance/baton) | Generational handoff (carries lessons between lineage generations) |
| [vetcheck](https://github.com/SuperInstance/vetcheck) | Health monitoring for registered models |

## License

MIT — see [LICENSE](LICENSE).
