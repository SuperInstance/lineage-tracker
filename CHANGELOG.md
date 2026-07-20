# Changelog

All notable changes to `si-lineage-tracker` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.1.3 — 2026-07-20

### Fixed
- **Lineage tracing now handles versioned model references.** When models are referenced by versioned tags (e.g., `model@v1.2.3`), the lineage tracker now correctly resolves and records the specific version in provenance records. Previously, versionless references could cause ambiguity when multiple versions of the same model existed in the breeding program.

## v0.1.2 — 2026-07-20

### Fixed
- **Checksum now includes parent versions for true provenance uniqueness.** The lineage checksum calculation previously only hashed model IDs, which meant two different versions of the same parent produced identical checksums. Now includes parent version information in the hash, ensuring distinct provenance fingerprints for each unique lineage path.

## v0.1.1 — 2026-07-19

### Fixed
- **Audit fixes from code review.** Store validation strengthened; timestamp parsing made more robust; lineage edge cases (cycles, self-references) now properly detected and reported.

## v0.1.0 — 2026-07-18

### Initial Release
- Package: si-lineage-tracker — fine-tune provenance as bloodline records
- Lineage graph, checksum verification, provenance export
- Tests passing
