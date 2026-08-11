# Architecture

## Layers
1. **GitHub API Layer**: Interface for fetching raw data.
2. **Data Acquisition Layer**: Handling pagination, rate limits, and orchestrating fetches.
3. **Data Processing Layer**: Extractor, Filter, Deduplicator, Validator, Enricher. Uses a Pipeline pattern.
4. **Master Dataset Layer**: JSONL flat file representing the clean, single source of truth.
5. **Dataset Builder Layer**: Converts the master dataset into model-ready splits using `StratifiedGroupKFold`.
6. **ML Layer**: Inference, evaluation, and experiment tracking.

## Module Dependency Graph
`main.py` orchestrates the flow. Data flows linearly:
`GitHubClient` -> `RepositoryScraper` -> `ReviewExtractor` -> `QualityFilter` -> `Deduplicator` -> `Validator` -> `MetadataEnricher` -> `DatasetBuilder`.
