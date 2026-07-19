# LineageTracker Audit Report v0.1.1

**Date:** 2026-07-19
**Audited Version:** lineage-tracker (main branch)
**Scope:** Full source audit of `src/lineage_tracker/` and `tests/`

## Executive Summary

This audit identified **5 bugs** in the lineage-tracker package, including correctness issues, deprecated API usage, and parameter handling problems. All bugs have been fixed and regression tests added.

**Severity Breakdown:**
- 2 High (correctness issues affecting core functionality)
- 2 Medium (API behavior issues)
- 1 Low (deprecation warning)

## Bugs Found and Fixed

### Bug #1: get_model Returns Wrong Version (HIGH)

**Location:** `src/lineage_tracker/store.py:50-57`

**Issue:** The `get_model()` method docstring claimed to return "latest version if multiple" but the implementation returned the first match (oldest version by insertion order).

**Impact:** When multiple versions of a model existed, lineage operations would use the oldest version instead of the most recent, potentially causing incorrect ancestry tracking.

**Fix:** Changed iteration from forward to reverse to return the most recently added version:

```python
# Before:
for key, mdata in data["models"].items():
    if key.startswith(f"{name}@"):
        return Model(**mdata)

# After:
for key, mdata in reversed(list(data["models"].items())):
    if key.startswith(f"{name}@"):
        return Model(**mdata)
```

**Regression Test:** `TestBugFixes::test_get_model_returns_latest_version`

---

### Bug #2: @ Character in Model Names Breaks Parsing (HIGH)

**Location:** `src/lineage_tracker/__init__.py:54-62`

**Issue:** The code uses `@` as a separator between model name and version (e.g., "model@version"). If a model name contained `@`, it would create malformed keys like `"model@special@unknown"` that couldn't be properly parsed.

**Impact:** Model names containing `@` would corrupt the internal data structure and break lineage tracing.

**Fix:** Added validation to reject `@` in model names:

```python
if "@" in child_name:
    raise ValueError("Model names cannot contain '@' character")
for pname in parents:
    if "@" in pname:
        raise ValueError("Model names cannot contain '@' character")
```

**Regression Test:** `TestBugFixes::test_reject_at_symbol_in_model_names`

---

### Bug #3: Generation Calculation Incorrect for Root Models (MEDIUM)

**Location:** `src/lineage_tracker/__init__.py:128`

**Issue:** In `_trace_lineage()`, when a model's generation wasn't found in the store, it fell back to using the recursion `depth` parameter. For auto-registered root models (with version="unknown"), this resulted in generation values like 2 or 3 instead of 0.

**Impact:** Lineage tracing would show incorrect generation numbers for root models, making generation gaps and lineage depth calculations incorrect.

**Example:**
```python
# Chain: root -> A -> B
# Expected: root=0, A=1, B=2
# Buggy output: root=2, A=1, B=2
```

**Fix:** Added special handling for auto-registered root models:

```python
gen = self.store.get_generation(model.name, model.version)
if gen is None:
    gen = 0 if model.version == "unknown" else depth
result.append(Generation(model=model, generation=gen))
```

**Regression Test:** `TestBugFixes::test_generation_calculation_for_root_models`

---

### Bug #4: Pool Parameter Not Respected (MEDIUM)

**Location:** `src/lineage_tracker/__init__.py:205`

**Issue:** The `recommend_breeding()` method used `pool or [...]` to select candidates. In Python, an empty list `[]` is falsy, so passing `pool=[]` would incorrectly use the default candidate pool instead of returning no recommendations.

**Impact:** Users couldn't explicitly request an empty recommendation list.

**Fix:** Changed to use `is not None` check:

```python
# Before:
candidates = pool or [m.name for m in self.store.get_all_models() if m.name != model_name]

# After:
candidates = pool if pool is not None else [m.name for m in self.store.get_all_models() if m.name != model_name]
```

**Regression Test:** `TestBugFixes::test_pool_parameter_respects_empty_list`

---

### Bug #5: Deprecated datetime.utcnow() Usage (LOW)

**Location:** `src/lineage_tracker/__init__.py:87`

**Issue:** Used `datetime.utcnow()` which is deprecated as of Python 3.12.

**Impact:** Generated deprecation warnings during operation.

**Fix:** Updated to use timezone-aware datetime:

```python
# Before:
from datetime import datetime
timestamp=datetime.utcnow().isoformat() + "Z"

# After:
from datetime import datetime, timezone
timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
```

**Regression Test:** `TestBugFixes::test_timestamp_format_is_valid`

---

## Testing Results

**Pre-Fix:** 25 tests passed, 44 deprecation warnings
**Post-Fix:** 30 tests passed, 0 warnings (new regression tests added)

All existing tests continue to pass, confirming backward compatibility.

## Files Modified

1. `src/lineage_tracker/__init__.py` - 4 bug fixes applied
2. `src/lineage_tracker/store.py` - 1 bug fix applied
3. `tests/test_lineage.py` - 5 new regression tests added

## Recommendations

1. **Consider Version Comparison**: The current "latest version" logic uses insertion order. For production use, consider implementing semantic version comparison.

2. **Add Integration Tests**: Add end-to-end tests for complex lineage scenarios (multi-generation breeding, merge operations, etc.).

3. **Type Hints**: Consider adding stricter type hints (e.g., `list[str]` → `Sequence[str]`) for better IDE support.

4. **Documentation**: Update the README to document the `@` character restriction in model names.

## Conclusion

The lineage-tracker package is now more robust with all identified bugs fixed and regression tests added. The core functionality is sound and the package is ready for production use with these fixes.
