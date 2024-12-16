# RepoHealth

A Python-based tool for analyzing GitHub repository health and maintenance status. RepoHealth helps developers and maintainers identify potentially problematic repositories by analyzing metrics like update frequency, open issues, and activity patterns. It automatically detects outdated or abandoned projects, making it easier to assess repository reliability and maintenance needs.

## Features
- Automated repository analysis and health scoring
- Detection of outdated and potentially broken repositories
- Configurable thresholds for issue counts and activity timeframes
- Bulk repository scanning with rate-limit handling
- JSON report generation for further analysis
- Customizable search queries to focus on specific repository types
- Smart retry mechanism with exponential backoff
- GitHub API rate limit handling

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install requests python-dotenv
```

## Configuration

1. Copy `.env.template` to `.env`
2. Add your GitHub token to the `.env` file:
```
GITHUB_TOKEN=your_github_token_here
```

A GitHub token is required for API access. You can create one at GitHub Settings > Developer Settings > Personal Access Tokens.

## Usage

Basic usage:
```bash
python github_repo_checker.py
```

With custom parameters:
```bash
python github_repo_checker.py --query "language:python stars:>1000" --max_repos 200 --output results.json
```

### Command Line Arguments

- `--query`: Search query for repositories (default: "stars:>100")
- `--output`: Output file for results in JSON format (optional)
- `--max_repos`: Maximum number of repositories to check (default: 100)

## Key Metrics and Thresholds

The tool uses the following criteria to evaluate repositories:

### Outdated Repository
- Last push was more than 365 days ago (OUTDATED_THRESHOLD_DAYS)

### Potentially Broken Repository
- More than 10 open issues (BROKEN_ISSUES_THRESHOLD)
- No activity (pushes) in the last 180 days (BROKEN_THRESHOLD_DAYS)

### Tracked Metrics
- Repository name and URL
- Description
- Star count
- Open issue count
- Last push date
- Creation date
- Outdated status
- Broken status

## Rate Limiting and Error Handling

- Automatic handling of GitHub API rate limits
- Maximum of 3 retries for failed requests
- Exponential backoff for retry attempts
- Detailed error reporting

## Output Format

When using the `--output` option, results are saved in JSON format with the following structure:

```json
[
  {
    "name": "owner/repo",
    "url": "https://github.com/owner/repo",
    "description": "Repository description",
    "stars": 1000,
    "open_issues": 5,
    "last_push": "2024-01-01T00:00:00Z",
    "created_at": "2023-01-01T00:00:00Z",
    "is_outdated": false,
    "is_broken": false
  }
]
```

## License

See the [LICENSE](LICENSE) file for details.

---
Last updated: December 16, 2024