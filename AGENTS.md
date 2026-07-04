# AGENTS.md — blockchain_privacy_platform

## Tech stack
- **Python 3.11.9 + Django 5.0.1** — 7 custom apps under `privacy_platform/`
- **Activate venv** before any Python work: `.\p-venv\Scripts\Activate.ps1`
- **MySQL** (hardcoded in settings.py, uses `p-venv/Scripts/mysql`). SQLite fallback documented but not wired.
- **No npm / JS build tooling** — Bootstrap 5.3.2 via CDN, custom CSS/JS in `static/`

## Setup sequence (order matters)
1. `pip install -r requirements.txt`
2. `python manage.py makemigrations`
3. `python manage.py migrate`
4. `python manage.py load_techniques` — seeds 5 privacy technique rows into DB
5. `python manage.py createsuperuser`

## Dev server
`python manage.py runserver 127.0.0.1:8000`

## Known quirks
- **Two `experiment_runner.py` files**: `experiments/experiment_runner.py` (primary, 812 lines, used by views) and root `experiment_runner.py` (standalone, 496 lines). The views in `experiments/views.py` use **both** — the `PrivacyExperimentRunner` class *and* direct calls to technique classes. Be careful which one you edit.
- **5 privacy techniques** live in `privacy_tools/techniques/`: `ring_signature.py`, `zero_knowledge_proof.py`, `secure_mpc.py`, `trusted_execution.py`, `crypto_mixer.py`. Each uses a different crypto library (ecdsa, py_ecc, cryptography, pycryptodome).
- **Management commands** for batch experiment ops:
  - `python manage.py rerun_all_report --force --out results.csv`
  - `python manage.py rerun_experiments --ids 1,5,10 --force`
  - `python manage.py backfill_metrics`
  - `python manage.py fix_all_accuracy`
- **Hardcoded `SECRET_KEY`** and MySQL password `db_password` in `settings.py` — not production-safe. Use env vars for deployment.
- **Two venv dirs exist**: `p-venv/` (primary) and `env/` (legacy). Only use `p-venv/`.
- **No tests, no linter, no typechecker, no CI** — all `tests.py` files are boilerplate-only.
- **`.gitignore` excludes `*.csv`** — `results.csv` in git will be empty after clone.
- **`__pycache__/` is gitignored** but some may appear in history.
- **`readme.txt`** references Django 3.2+ but `requirements.txt` pins Django 5.0.1 — trust requirements.txt.
