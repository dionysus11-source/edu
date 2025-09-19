# Repository Guidelines

## Project Structure & Module Organization
- Primary training assets live in the root: `train_code_for_mac.py`, `test_model.py`, and the `enhanced_boxing_dataset.jsonl` corpus.
- Model artifacts land in `boxing-classifier/`, `boxing-classifier-final/`, and `test_dataset/`; treat them as generated outputs when iterating.
- Domain notebooks stay grouped by track: `llm/Src/` for LLM labs, `vision/AI-Application-Specialist-Vision/` for vision work, `rag/` for retrieval exercises, and `recommand/` for recommender practice, each with reference PDFs under matching `Doc/` folders.
- When adding a new module, mirror this pattern (docs in `Doc/`, notebooks in a topical folder) to keep navigation predictable.

## Build, Test, and Development Commands
- `python train_code_for_mac.py`: trains the CodeBERT classifier on `enhanced_boxing_dataset.jsonl`, logging checkpoints under `boxing-classifier/` and exporting the final weights to `boxing-classifier-final/`.
- `python test_model.py`: loads artifacts from `boxing-classifier-final/` (and `test_dataset/` when available) to report accuracy, precision, recall, and a confusion matrix.
- `pip install -r vision/AI-Application-Specialist-Vision/requirements.txt`: installs the shared notebook dependencies; prefer an isolated virtual environment per track.

## Coding Style & Naming Conventions
- Python scripts use 4-space indentation, `snake_case` identifiers, and concise docstrings for helper utilities (see `test_model.py`).
- Keep reusable logic in `.py` modules; notebooks should orchestrate experiments and reference shared functions.
- Version generated weights and datasets with explicit suffixes (for example `boxing-classifier-final-v2/`) to preserve provenance.

## Testing Guidelines
- Re-run `python test_model.py` after any training tweak or dataset change; track weighted accuracy against the last committed run.
- Name exploratory notebooks with the `aas_topic_detail.ipynb` template already used in `llm/Src/` to signal scope and subject.
- For quick manual checks, call the `test_single_text` helper inside `test_model.py` and record confidence outputs alongside predictions.

## Commit & Pull Request Guidelines
- Follow short, imperative commit summaries (`Add ...`, `Update ...`), matching the existing Git history.
- PRs should state the objective, datasets or artifacts touched, and include recent metrics or console snippets from `python test_model.py`.
- Attach large checkpoints via shared storage links rather than committing them directly, and note any environment assumptions in the description.

## Data & Model Handling
- Keep raw JSONL data and exported checkpoints under version control only while they remain lightweight; otherwise add their paths to `.gitignore`.
- Strip secrets or personal data from notebooks before committing; use `jupyter nbconvert --ClearOutputPreprocessor.enabled=True` to reset outputs.
