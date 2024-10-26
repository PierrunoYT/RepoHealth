import requests
from datetime import datetime, timedelta
import os
import time
import argparse
import json
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
BASE_URL = 'https://api.github.com'
MAX_RETRIES = 3
OUTDATED_THRESHOLD_DAYS = 365
BROKEN_THRESHOLD_DAYS = 180
BROKEN_ISSUES_THRESHOLD = 10

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def make_request(url: str, retry_count: int = 0) -> requests.Response:
    """
    Make a GitHub API request with rate limiting and error handling.
    """
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
            if int(response.headers['X-RateLimit-Remaining']) == 0:
                reset_time = int(response.headers['X-RateLimit-Reset'])
                sleep_time = reset_time - int(time.time()) + 1
                print(f"Rate limit reached. Waiting for {sleep_time} seconds...")
                time.sleep(sleep_time)
                return make_request(url)
                
        response.raise_for_status()
        return response
        
    except requests.RequestException as e:
        if retry_count < MAX_RETRIES:
            wait_time = (2 ** retry_count)
            print(f"Request failed. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            return make_request(url, retry_count + 1)
        raise

def search_repos(query: str, sort: str = 'stars', order: str = 'desc',
                per_page: int = 100, max_repos: int = 1000) -> List[Dict[str, Any]]:
    """
    Search for GitHub repositories based on the given query.
    """
    url = f'{BASE_URL}/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}'
    all_repos = []
    page = 1

    while len(all_repos) < max_repos:
        try:
            response = make_request(f"{url}&page={page}")
            repos = response.json()['items']
            
            if not repos:
                break
                
            all_repos.extend(repos)
            page += 1
            
            if len(all_repos) >= max_repos:
                break
                
        except requests.RequestException as e:
            print(f"Error fetching repositories: {e}")
            break

    return all_repos[:max_repos]

def is_repo_outdated(repo_info: Dict[str, Any]) -> bool:
    """
    Check if a repository is outdated based on its last push date.
    """
    if not repo_info or 'pushed_at' not in repo_info:
        return False
    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    return (datetime.utcnow() - last_push) > timedelta(days=OUTDATED_THRESHOLD_DAYS)

def is_repo_broken(repo_info: Dict[str, Any]) -> bool:
    """
    Check if a repository might be broken based on issues and activity.
    """
    if not repo_info or 'pushed_at' not in repo_info:
        return False
    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    has_open_issues = repo_info.get('open_issues_count', 0) > BROKEN_ISSUES_THRESHOLD
    no_recent_commits = (datetime.utcnow() - last_push) > timedelta(days=BROKEN_THRESHOLD_DAYS)
    return has_open_issues and no_recent_commits

def check_repository(repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a repository and compile relevant metrics.
    """
    return {
        "name": repo_info['full_name'],
        "url": repo_info['html_url'],
        "description": repo_info.get('description', ''),
        "stars": repo_info['stargazers_count'],
        "open_issues": repo_info['open_issues_count'],
        "last_push": repo_info['pushed_at'],
        "created_at": repo_info['created_at'],
        "is_outdated": is_repo_outdated(repo_info),
        "is_broken": is_repo_broken(repo_info)
    }

def main(args: argparse.Namespace) -> None:
    """
    Main function to execute the repository analysis.
    """
    if not GITHUB_TOKEN:
        print("Error: GitHub token not found. Please set GITHUB_TOKEN in your environment variables.")
        return

    print(f"Searching repositories matching: {args.query}")
    repos = search_repos(query=args.query, max_repos=args.max_repos)
    results = []
    
    for i, repo in enumerate(repos, 1):
        result = check_repository(repo)
        results.append(result)
        print(f"\nChecked: {result['name']} ({i}/{len(repos)})")
        print(f"  URL: {result['url']}")
        print(f"  Description: {result['description']}")
        print(f"  Stars: {result['stars']}")
        print(f"  Open Issues: {result['open_issues']}")
        print(f"  Created: {result['created_at']}")
        print(f"  Last Push: {result['last_push']}")
        print(f"  Outdated: {'Yes' if result['is_outdated'] else 'No'}")
        print(f"  Potentially Broken: {'Yes' if result['is_broken'] else 'No'}")

    # Sort results by stars
    results.sort(key=lambda x: x['stars'], reverse=True)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Repository Analyzer")
    parser.add_argument("--query", default="stars:>100", help="Search query for repositories")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--max_repos", type=int, default=100,
                      help="Maximum number of repositories to check")
    args = parser.parse_args()
    main(args)
