#!/usr/bin/env python3
"""
Create project and add all existing issues to it
"""

import os
import sys
import requests
import yaml
import time

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("❌ GITHUB_TOKEN not set")
    sys.exit(1)

headers_rest = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

headers_graphql = {
    'Authorization': f'bearer {token}',
    'Content-Type': 'application/json'
}

graphql_url = "https://api.github.com/graphql"
repo = f"{config['repo_owner']}/{config['repo_name']}"

print("=" * 70)
print(f"🚀 Creating project: {config['project_name']}")
print("=" * 70)

# Get user ID
query = """
query {
  viewer {
    id
    login
  }
}
"""
response = requests.post(graphql_url, headers=headers_graphql, json={"query": query})
user_id = response.json()["data"]["viewer"]["id"]
user_login = response.json()["data"]["viewer"]["login"]
print(f"\n👤 User: {user_login}")

# Create project
print(f"\n📋 Creating project '{config['project_name']}'...")
mutation = """
mutation($ownerId: ID!, $title: String!) {
  createProjectV2(input: {ownerId: $ownerId, title: $title}) {
    projectV2 {
      id
      number
      url
    }
  }
}
"""
variables = {"ownerId": user_id, "title": config['project_name']}
response = requests.post(graphql_url, headers=headers_graphql,
                        json={"query": mutation, "variables": variables})
project_data = response.json()["data"]["createProjectV2"]["projectV2"]
project_id = project_data["id"]
project_number = project_data["number"]
project_url = project_data["url"]

print(f"  ✓ Created project #{project_number}")
print(f"  🔗 {project_url}")

# Get all issues
print(f"\n📥 Fetching issues from {repo}...")
url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100"
response = requests.get(url, headers=headers_rest)
issues = response.json()
print(f"  ✓ Found {len(issues)} issues")

# Add issues to project
print(f"\n➕ Adding issues to project...")
for i, issue in enumerate(issues, 1):
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    variables = {"projectId": project_id, "contentId": issue['node_id']}
    
    try:
        requests.post(graphql_url, headers=headers_graphql,
                     json={"query": mutation, "variables": variables})
        print(f"  ✓ Added #{issue['number']}: {issue['title']}")
        time.sleep(0.2)  # Rate limiting
    except Exception as e:
        print(f"  ✗ Failed to add #{issue['number']}: {e}")

print("\n" + "=" * 70)
print("✅ Project setup complete!")
print("=" * 70)
print(f"\n🔗 View project: {project_url}")
