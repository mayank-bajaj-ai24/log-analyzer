# Contributing Guide — Team 57

This document explains exactly how to contribute to this project as a team.

---

## Step-by-step workflow for every task

### 1. Get the latest code
Always do this before starting any new work:
```bash
git checkout dev
git pull origin dev
```

### 2. Create your branch
Name your branch using your name and what you're building:
```bash
git checkout -b riya/streaming-generator
git checkout -b chinmayi/drain3-integration
git checkout -b roshan/isolation-forest
git checkout -b mayank/streamlit-dashboard
```

### 3. Write your code and tests
- Write code in the relevant file under `pipeline/` or `dashboard/`
- Add or update the matching test in `tests/`
- Test locally before pushing:
```bash
pytest tests/
```

### 4. Commit your changes
```bash
git add .
git commit -m "[ingestion] add generator-based chunk reader"
```

Commit message format: `[module] short description`

Valid module tags: `ingestion`, `parser`, `dedup`, `anomaly`, `storage`, `dashboard`, `evaluation`, `tests`, `docs`, `config`

### 5. Push and open a Pull Request
```bash
git push origin your-branch-name
```
Then go to GitHub → open a Pull Request into `dev` (NOT into `main`).

### 6. Get a review
- Tag one other team member to review
- Address any feedback
- Once approved, merge into `dev`

### 7. Merging to main
Only the team lead or mentors merge `dev` → `main` after a working milestone.

---

## What NOT to commit

- `.log` files (large, not useful in git)
- `.parquet` files (generated output)
- `venv/` folder
- Your personal `.env` files
- Jupyter notebook output cells (clear outputs before committing)

These are all in `.gitignore` already.

---

## Module ownership

| Module | File | Owner |
|--------|------|-------|
| Streaming Ingestion | `backend/pipeline/ingestion.py` | Riya |
| Log Parsing | `backend/pipeline/parser.py` | Chinmayi |
| Deduplication | `backend/pipeline/deduplication.py` | Chinmayi |
| Feature Extraction | `backend/pipeline/feature_extraction.py` | Roshan |
| Anomaly Detection | `backend/pipeline/anomaly_detector.py` | Roshan |
| Storage | `backend/pipeline/storage.py` | Mayank |
| Dashboard | `frontend/` | Mayank |
| Evaluation / Benchmarking | `backend/evaluation/` | Riya |
| Tests | `backend/tests/` | Everyone (write tests for your own module) |

---

## Running tests

```bash
# Run all tests
pytest tests/

# Run tests for one module
pytest tests/test_ingestion.py -v

# Run with coverage report
pytest tests/ --cov=pipeline
```

---

## If you get a merge conflict

1. Don't panic
2. Pull the latest dev:
   ```bash
   git pull origin dev
   ```
3. Open the conflicting file — look for `<<<<<<<` markers
4. Resolve manually, keeping both changes where needed
5. Stage the resolved file:
   ```bash
   git add the_file.py
   git commit -m "resolve merge conflict in the_file.py"
   ```
6. If unsure, ask a teammate before force-pushing anything
