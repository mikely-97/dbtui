# Commit Pending Macro Work

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Commit the pending macro test additions before starting feature work.

**Architecture:** N/A — housekeeping only.

---

### Task 1: Commit pending files

- [ ] **Step 1: Verify tests pass**

```bash
pytest tests/ -q
```
Expected: all pass (currently 196 passing).

- [ ] **Step 2: Add test fixtures**

```bash
git add tests/testing/macros/clean_string.sql
git add tests/testing/macros/format_date.sql
git add tests/testing/vanilla/stg/v_macro_user.sql
```

- [ ] **Step 3: Add test files**

```bash
git add tests/test_macros.py
git add tests/test_files.py
git add tests/test_graph.py
```

- [ ] **Step 4: Commit**

```bash
git commit -m "test: add macro test suite and fixtures"
```
