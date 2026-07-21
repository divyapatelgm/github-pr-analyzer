# Execution Steps

1. **Milestone 1: Configuration & Setup**
   - Create `.env` from `.env.example` and add `GITHUB_TOKEN`.
   - Update `config/config.yaml` with target repositories.
   - Verification: Running `src.main` with a valid token successfully connects to GitHub API.

2. **Milestone 2: Data Acquisition**
   - Scrape PRs, diffs, and comments.
   - Verification: Raw data is correctly fetched without crashing on rate limits.

3. **Milestone 3: Data Processing & Cleaning**
   - Filter, deduplicate, validate, and enrich the data.
   - Verification: `master_dataset_v1.jsonl` is generated with high-quality, valid records.

4. **Milestone 4: Dataset Generation**
   - Split the master dataset into train, validation, and test sets using group-based logic.
   - Verification: `data/training/v1/` contains the split `.jsonl` files with no cross-repo leakage.

5. **Milestone 5: Fine-Tuning & Evaluation**
   - Train Qwen2.5 on the dataset (external process using Unsloth).
   - Log experiments to `experiments.jsonl` and `evaluation_report.md`.
