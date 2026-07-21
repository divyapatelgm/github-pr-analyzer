# Dataset Card

- **Description**: A dataset of code diffs and corresponding human review comments from GitHub PRs.
- **Collection Method**: Scraped via GitHub REST API from closed PRs of selected repositories.
- **Language Distribution**: Balances major languages based on source repos.
- **Ethical Considerations**: PII (reviewer usernames) are SHA-256 hashed to protect privacy.
- **Limitations**: Only contains data from explicitly targeted open-source repositories. May contain biases inherent to those specific communities.
