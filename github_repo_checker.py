import requests
from datetime import datetime, timedelta
import os
import time
import argparse
import json
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
BASE_URL = 'https://api.github.com'

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def make_request(url):
    """Führe eine API-Anfrage durch und behandle Ratenbegrenzungen"""
    response = requests.get(url, headers=headers)
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
        if int(response.headers['X-RateLimit-Remaining']) == 0:
            reset_time = int(response.headers['X-RateLimit-Reset'])
            sleep_time = reset_time - int(time.time()) + 1
            print(f"API-Limit erreicht. Warte für {sleep_time} Sekunden...")
            time.sleep(sleep_time)
            return make_request(url)
    return response

def search_repos(query, sort='updated', order='desc', per_page=100, max_repos=1000):
    url = f'{BASE_URL}/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}'
    all_repos = []
    page = 1

    while len(all_repos) < max_repos:
        response = make_request(f"{url}&page={page}")
        if response.status_code != 200:
            break
        
        repos = response.json()['items']
        if not repos:
            break
        
        # Filter repositories based on the query date range
        if 'created:' in query or 'pushed:' in query:
            date_range = query.split(':')[-1].split('..')
            start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
            end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
            
            filtered_repos = [
                repo for repo in repos
                if start_date <= datetime.strptime(repo['created_at' if 'created:' in query else 'pushed_at'], '%Y-%m-%dT%H:%M:%SZ') <= end_date
            ]
            
            all_repos.extend(filtered_repos)
        else:
            all_repos.extend(repos)
        
        page += 1
        
        if len(all_repos) >= max_repos:
            break

    return all_repos[:max_repos]

def get_repo_info(owner, repo):
    url = f'{BASE_URL}/repos/{owner}/{repo}'
    response = make_request(url)
    return response.json() if response.status_code == 200 else None

def get_commit_frequency(owner, repo):
    url = f'{BASE_URL}/repos/{owner}/{repo}/stats/commit_activity'
    response = make_request(url)
    if response.status_code == 200:
        data = response.json()
        total_commits = sum(week['total'] for week in data)
        return total_commits / len(data) if len(data) > 0 else 0
    return 0

def is_repo_outdated(repo_info):
    if not repo_info:
        return False
    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    return (datetime.utcnow() - last_push) > timedelta(days=365)

def is_repo_broken(repo_info):
    if not repo_info:
        return False
    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    has_open_issues = repo_info['open_issues_count'] > 10
    no_recent_commits = (datetime.utcnow() - last_push) > timedelta(days=180)
    return has_open_issues and no_recent_commits

def check_repository(repo_info):
    result = {
        "name": repo_info['full_name'],
        "url": repo_info['html_url'],
        "stars": repo_info['stargazers_count'],
        "open_issues": repo_info['open_issues_count'],
        "last_push": repo_info['pushed_at'],
        "is_outdated": is_repo_outdated(repo_info),
        "is_broken": is_repo_broken(repo_info),
        "commit_frequency": get_commit_frequency(repo_info['owner']['login'], repo_info['name'])
    }
    return result

def main(args):
    query = args.query
    repos = search_repos(query, max_repos=args.max_repos)
    results = []
    
    for i, repo in enumerate(repos, 1):
        result = check_repository(repo)
        results.append(result)
        print(f"Überprüft: {result['name']} ({i}/{len(repos)})")
        print(f"  URL: {result['url']}")
        print(f"  Sterne: {result['stars']}")
        print(f"  Offene Issues: {result['open_issues']}")
        print(f"  Letzter Push: {result['last_push']}")
        print(f"  Veraltet: {'Ja' if result['is_outdated'] else 'Nein'}")
        print(f"  Möglicherweise defekt: {'Ja' if result['is_broken'] else 'Nein'}")
        print(f"  Durchschnittliche wöchentliche Commits: {result['commit_frequency']:.2f}")
        print()

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Ergebnisse wurden in {args.output} gespeichert.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Repository Checker")
    parser.add_argument("--query", default="stars:>100", help="Suchabfrage für Repositories")
    parser.add_argument("--output", help="Ausgabedatei für die Ergebnisse (JSON)")
    parser.add_argument("--max_repos", type=int, default=100, help="Maximale Anzahl der zu überprüfenden Repositories")
    args = parser.parse_args()
    main(args)
