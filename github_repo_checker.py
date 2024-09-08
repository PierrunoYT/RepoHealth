import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env Datei
load_dotenv()

# GitHub API Token aus Umgebungsvariablen holen
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# GitHub API Basis-URL
BASE_URL = 'https://api.github.com'

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def search_repos(query, sort='updated', order='asc', per_page=100):
    """Suche nach Repositories basierend auf einer Abfrage"""
    url = f'{BASE_URL}/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}'
    response = requests.get(url, headers=headers)
    return response.json()['items'] if response.status_code == 200 else []

def get_repo_info(owner, repo):
    """Hole Informationen über ein Repository"""
    url = f'{BASE_URL}/repos/{owner}/{repo}'
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def is_repo_outdated(repo_info):
    """Überprüfe, ob ein Repository veraltet ist"""
    if not repo_info:
        return False

    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.utcnow()

    # Repository gilt als veraltet, wenn der letzte Push mehr als 1 Jahr zurückliegt
    return (now - last_push) > timedelta(days=365)

def is_repo_broken(repo_info):
    """Überprüfe, ob ein Repository möglicherweise defekt ist"""
    if not repo_info:
        return False

    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.utcnow()
    has_open_issues = repo_info['open_issues_count'] > 10
    no_recent_commits = (now - last_push) > timedelta(days=180)

    return has_open_issues and no_recent_commits

def check_repository(repo_info):
    """Überprüfe ein Repository auf Veralterung und mögliche Defekte"""
    if is_repo_outdated(repo_info):
        print(f"{repo_info['full_name']} scheint veraltet zu sein. Letzter Push: {repo_info['pushed_at']}")
    
    if is_repo_broken(repo_info):
        print(f"{repo_info['full_name']} könnte defekt sein. Es hat offene Issues, aber keine kürzlichen Commits.")
    
    print(f"  Sterne: {repo_info['stargazers_count']}")
    print(f"  Offene Issues: {repo_info['open_issues_count']}")
    print(f"  URL: {repo_info['html_url']}")
    print()

def main():
    query = 'stars:>100'  # Beispiel: Repos mit mehr als 100 Sternen
    repos = search_repos(query)
    
    for repo in repos:
        check_repository(repo)

if __name__ == "__main__":
    main()
