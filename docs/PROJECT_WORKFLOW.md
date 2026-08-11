# Project Workflow

## Overview
GitReviewAI follows a straightforward, linear pipeline to transform raw GitHub data into a high-quality dataset, which is then used to fine-tune a model and serve inferences.

## Steps

1. **Scraping**: `repository_scraper.py` reads `config.yaml` to find target repos. It queries the GitHub API to fetch merged PRs, their diffs, and review comments.
2. **Extraction**: `review_extractor.py` converts raw JSON responses into flat records linking a specific code diff to a specific review comment.
3. **Filtering**: `quality_filter.py` drops comments that are too short or contain blocklisted phrases.
4. **Validation & Enrichment**: `validator.py` ensures no missing fields. `metadata_enricher.py` infers the programming language and anonymizes reviewers.
5. **Deduplication**: `deduplicator.py` ensures unique records based on `review_comment + code_diff + pr_number`.
6. **Dataset Building**: `dataset_builder.py` takes the master dataset, groups it by repository using `StratifiedGroupKFold` to prevent data leakage, and outputs `train.jsonl`, `validation.jsonl`, and `test.jsonl`.
7. **Fine-Tuning (Future/Manual)**: The dataset is fed to Unsloth for Qwen2.5 QLoRA fine-tuning.
8. **Inference**: `inference.py` loads the trained weights to review new code diffs.
