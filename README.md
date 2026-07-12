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



## Lineage Tracker vs Pedigree: When to Use Which

Both [Lineage Tracker](https://github.com/SuperInstance/lineage-tracker) and [Pedigree](https://github.com/SuperInstance/pedigree) track model ancestry. They overlap but serve different primary use cases:

| Concern | Lineage Tracker | Pedigree |
|---------|----------------|----------|
| **Primary focus** | Provenance records | Bloodline analysis |
| **Data model** | Flat breeding records with metadata | Genealogical tree with sire/dam |
| **Inbreeding detection** | No (recommendations based on trait diversity) | Yes (Wright's coefficient of relationship) |
| **Visualization** | Programmatic queries | ASCII trees + GraphViz DOT export |
| **Trait comparison** | Yes (compare generations side-by-side) | Limited |
| **Breeding method tracking** | Rich metadata (LoRA rank, LR, epochs, merge strategy) | Basic method tags |
| **Best for** | MLOps: "what happened in this fine-tune chain?" | Research: "is this merge genetically safe?" |

**Use Lineage Tracker when** you need audit trails for production models — what was trained on what, with what hyperparameters, and what the benchmark impact was. The metadata-rich records are designed for compliance and debugging.

**Use Pedigree when** you need genetic analysis — inbreeding coefficients before merging, diversity scoring for outcross recommendations, and publication-quality lineage trees. The sire/dam model maps cleanly to how animal breeders think about bloodlines.

**Use both when** you're running a serious breeding program. Lineage Tracker records the events; Pedigree analyzes the bloodline. Export from one, import to the other.

## Advanced Scenario: Debugging a Capability Regression

```python
from lineage_tracker import LineageTracker

tracker = LineageTracker("lineage.json")

# Your production model suddenly can't do math
# Trace its ancestry to find the culprit
lineage = tracker.get_lineage("prod-model-v7")

print("Ancestry chain:")
for gen in lineage:
    model = gen.model
    gsm8k = model.traits.get("gsm8k", "N/A")
    print(f"  Gen {gen.generation}: {model.name}@{model.version}")
    print(f"    gsm8k: {gsm8k}")
    print(f"    method: {gen.breeding_method if hasattr(gen, 'breeding_method') else 'unknown'}")

# Output reveals:
#   Gen 0: base-llama-3-70b         gsm8k: 82.1  (baseline)
#   Gen 1: instruct-sft-v3          gsm8k: 79.4  (-2.7 after SFT)
#   Gen 2: creative-merge-v1        gsm8k: 71.2  (-8.2 after merge!)  ← CULPRIT
#   Gen 3: prod-model-v7            gsm8k: 68.9  (-2.3 after continued training)

# The merge at Gen 2 caused the regression
# Now check what was merged:
records = [r for r in tracker.get_all_models() if "creative-merge" in r.name]
for r in records:
    print(f"  {r.name}: parents={r.parent_ids}, traits={r.traits}")
```

## Multi-Generation Breeding Program

```python
from lineage_tracker import LineageTracker

tracker = LineageTracker("breeding-program.json")

# Generation 0: Foundation
tracker.record_breeding(
    parents=["llama-3-70b"],
    child_name="domain-base-v1",
    method="continue_pretrain",
    metadata={"dataset": "domain_corpus_v1", "tokens": "5B"},
    child_traits={"mmlu": 80.1, "domain_eval": 72.0},
)

# Generation 1: Specialization
tracker.record_breeding(
    parents=["domain-base-v1"],
    child_name="domain-instruct-v1",
    method="sft",
    metadata={"dataset": "instruct_v2", "epochs": 3, "lr": 2e-5},
    child_traits={"mmlu": 81.2, "domain_eval": 78.5, "if_eval": 84.0},
)

# Generation 1: Alternative specialization (different focus)
tracker.record_breeding(
    parents=["domain-base-v1"],
    child_name="domain-reasoning-v1",
    method="rlhf",
    metadata={"reward_model": "rm-v2", "kl_coef": 0.1},
    child_traits={"mmlu": 82.0, "domain_eval": 75.0, "gsm8k": 85.1},
)

# Generation 2: Merge the best of both specializations
tracker.record_breeding(
    parents=["domain-instruct-v1", "domain-reasoning-v1"],
    child_name="domain-merged-v2",
    method="merge",
    metadata={"strategy": "SLERP", "ratio": "0.5"},
    child_traits={"mmlu": 83.1, "domain_eval": 79.0, "gsm8k": 84.2, "if_eval": 83.5},
)

# Query the full program
print(f"Total models tracked: {len(tracker.get_all_models())}")
for model in tracker.get_all_models():
    print(f"  {model.name}@{model.version}: {model.traits}")
```

## Export for Pedigree Analysis

```python
from lineage_tracker import LineageTracker

tracker = LineageTracker("lineage.json")

# Export to a format Pedigree can consume
import json

models = tracker.get_all_models()
export = {"models": {}, "breeding_records": []}

for model in models:
    export["models"][f"{model.name}@{model.version}"] = {
        "name": model.name,
        "version": model.version,
        "traits": model.traits or {},
        "checksum": getattr(model, "checksum", None),
    }

with open("pedigree_import.json", "w") as f:
    json.dump(export, f, indent=2)

# Then in Pedigree:
# p = Pedigree("pedigree_import.json")
# p.check_inbreeding("domain-instruct-v1", "domain-reasoning-v1")
```

## License

MIT — see [LICENSE](LICENSE).
