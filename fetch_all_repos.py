#!/usr/bin/env python3
"""
Script to fetch all public repositories from a GitHub user and export as clone URLs.
This script uses GitHub API v3 to paginate through all repositories.

Usage:
    python3 fetch_all_repos.py <username> [--token YOUR_GITHUB_TOKEN]

Requirements:
    pip install requests
"""

import requests
import json
import sys
import argparse
from typing import List, Dict

class GitHubRepoFetcher:
    def __init__(self, username: str, token: str = None):
        self.username = username
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def fetch_all_repos(self) -> List[Dict]:
        """Fetch all public repositories for the user using pagination."""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/users/{self.username}/repos"
            params = {
                "visibility": "public",
                "sort": "updated",
                "direction": "desc",
                "per_page": per_page,
                "page": page
            }
            
            print(f"[*] Fetching page {page}...")
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                
                page_repos = response.json()
                
                if not page_repos:
                    print(f"[✓] Reached end of repositories at page {page}")
                    break
                
                repos.extend(page_repos)
                print(f"[✓] Page {page}: Found {len(page_repos)} repositories (Total: {len(repos)})")
                page += 1
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 404:
                    print(f"[✗] User '{self.username}' not found!")
                    sys.exit(1)
                else:
                    print(f"[✗] HTTP Error: {response.status_code}")
                    sys.exit(1)
            except requests.exceptions.RequestException as e:
                print(f"[✗] Request Error: {e}")
                sys.exit(1)
        
        return repos
    
    def save_to_file(self, repos: List[Dict], filename: str = "github_repos.txt"):
        """Save repository URLs to a file."""
        with open(filename, "w") as f:
            f.write(f"# GitHub Public Repositories for {self.username}\n")
            f.write(f"# Total Repositories: {len(repos)}\n")
            f.write(f"# Format: repository_name | HTTPS_URL | SSH_URL\n\n")
            
            for idx, repo in enumerate(repos, 1):
                name = repo.get("name", "N/A")
                clone_url = repo.get("clone_url", "N/A")
                ssh_url = repo.get("ssh_url", "N/A")
                description = repo.get("description", "No description")
                stars = repo.get("stargazers_count", 0)
                
                f.write(f"{idx}. {name}\n")
                f.write(f"   HTTPS: {clone_url}\n")
                f.write(f"   SSH:   {ssh_url}\n")
                f.write(f"   Stars: {stars} | Description: {description}\n\n")
        
        print(f"[✓] Saved to {filename}")
    
    def save_clone_commands(self, repos: List[Dict], filename: str = "clone_all_repos.sh"):
        """Generate a bash script with clone commands."""
        with open(filename, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Clone all public repositories for {self.username}\n")
            f.write(f"# Total repositories: {len(repos)}\n")
            f.write(f"# Usage: bash {filename}\n\n")
            
            f.write(f"REPOS_DIR=\"{self.username}_repos\"\n")
            f.write("mkdir -p \"$REPOS_DIR\"\n")
            f.write("cd \"$REPOS_DIR\"\n\n")
            
            for repo in repos:
                name = repo.get("name", "")
                clone_url = repo.get("clone_url", "")
                f.write(f"echo \"[*] Cloning {name}...\"\n")
                f.write(f"git clone {clone_url}\n\n")
            
            f.write("echo \"[✓] All repositories cloned successfully!\"\n")
        
        import os
        os.chmod(filename, 0o755)
        print(f"[✓] Generated clone script: {filename}")
    
    def save_json(self, repos: List[Dict], filename: str = "github_repos.json"):
        """Save repositories data as JSON."""
        with open(filename, "w") as f:
            json.dump(repos, f, indent=2)
        print(f"[✓] Saved JSON to {filename}")
    
    def save_csv(self, repos: List[Dict], filename: str = "github_repos.csv"):
        """Save repositories data as CSV."""
        import csv
        
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Name", "HTTPS URL", "SSH URL", "Stars", "Language", "Description"])
            
            for idx, repo in enumerate(repos, 1):
                writer.writerow([
                    idx,
                    repo.get("name", ""),
                    repo.get("clone_url", ""),
                    repo.get("ssh_url", ""),
                    repo.get("stargazers_count", 0),
                    repo.get("language", ""),
                    repo.get("description", "")
                ])
        
        print(f"[✓] Saved CSV to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch all public repositories from a GitHub user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 fetch_all_repos.py rohanmistry231
  python3 fetch_all_repos.py rohanmistry231 --token YOUR_GITHUB_TOKEN
  python3 fetch_all_repos.py rohanmistry231 --format all
        """
    )
    
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--token", help="GitHub Personal Access Token (optional, for higher rate limits)")
    parser.add_argument(
        "--format",
        choices=["txt", "json", "csv", "bash", "all"],
        default="all",
        help="Output format (default: all)"
    )
    parser.add_argument("--output", help="Output directory (default: current directory)")
    
    args = parser.parse_args()
    
    print(f"[*] Starting fetch for user: {args.username}")
    
    fetcher = GitHubRepoFetcher(args.username, args.token)
    repos = fetcher.fetch_all_repos()
    
    if not repos:
        print("[✗] No public repositories found!")
        sys.exit(1)
    
    print(f"\n[✓] Total repositories found: {len(repos)}\n")
    
    output_dir = args.output or "."
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Save in requested formats
    if args.format in ["txt", "all"]:
        fetcher.save_to_file(repos, f"{output_dir}/github_repos.txt")
    
    if args.format in ["json", "all"]:
        fetcher.save_json(repos, f"{output_dir}/github_repos.json")
    
    if args.format in ["csv", "all"]:
        fetcher.save_csv(repos, f"{output_dir}/github_repos.csv")
    
    if args.format in ["bash", "all"]:
        fetcher.save_clone_commands(repos, f"{output_dir}/clone_all_repos.sh")
    
    print(f"\n[✓] Done! All files saved to {output_dir}")
    print("\nTo clone all repositories, run:")
    print(f"  bash {output_dir}/clone_all_repos.sh")


if __name__ == "__main__":
    main()
