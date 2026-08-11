# Architecture Decisions (ADR)

## ADR 1: Data Storage Format
- **Decision:** Use JSONL instead of CSV for both master and training datasets.
- **Reason:** Multiline code diffs and complex characters are difficult to reliably escape in CSVs. JSONL natively handles nested objects and multiline strings and is supported by Hugging Face.

## ADR 2: Train/Val/Test Split Strategy
- **Decision:** Group-based split at the `repo_name` level using `StratifiedGroupKFold`.
- **Reason:** Standard random splitting causes cross-split leakage where the model memorizes repository-specific coding styles. Grouping prevents this, providing a more robust evaluation, despite resulting in fewer distinct repos per split.

## ADR 3: Experiment Tracking
- **Decision:** File-based tracking (`experiments.jsonl` and `evaluation_report.md`).
- **Reason:** Reduces infrastructure dependencies and keeps the project standalone and easily portable.
