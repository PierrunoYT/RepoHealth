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

    # Ein Repository gilt als möglicherweise defekt, wenn es offene Issues hat,
    # aber keine Commits in den letzten 6 Monaten
    last_push = datetime.strptime(repo_info['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.utcnow()
    has_open_issues = repo_info['open_issues_count'] > 0
    no_recent_commits = (now - last_push) > timedelta(days=180)

    return has_open_issues and no_recent_commits

def check_repository(owner, repo):
    """Überprüfe ein Repository auf Veralterung und mögliche Defekte"""
    repo_info = get_repo_info(owner, repo)
    if not repo_info:
        print(f"Konnte keine Informationen für {owner}/{repo} abrufen.")
        return

    if is_repo_outdated(repo_info):
        print(f"{owner}/{repo} scheint veraltet zu sein. Letzter Push: {repo_info['pushed_at']}")
    
    if is_repo_broken(repo_info):
        print(f"{owner}/{repo} könnte defekt sein. Es hat offene Issues, aber keine kürzlichen Commits.")

def main():
    # Beispiel-Verwendung
    check_repository('octocat', 'Hello-World')
    check_repository('microsoft', 'vscode')
    # Fügen Sie hier weitere Repositories hinzu, die Sie überprüfen möchten

if __name__ == "__main__":
    main()
