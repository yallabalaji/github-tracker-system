#!/usr/bin/env python3
"""
Universal Local-First GitHub Tracker System
Bidirectional sync between tracker.md and GitHub Issues + Projects
"""

import os
import re
import sys
import json
import time
from typing import Dict, List, Optional, Tuple
import requests
import yaml

# Configuration
TRACKER_FILE = "tracker.md"
CONFIG_FILE = "config.yaml"

class GitHubAPI:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.graphql_headers = {
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_issues(self) -> List[Dict]:
        """Fetch all issues (open + closed)"""
        issues = []
        page = 1
        while True:
            url = f"{self.base_url}/issues?state=all&page={page}&per_page=100"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            issues.extend(batch)
            page += 1
        return issues
    
    def get_labels(self) -> List[Dict]:
        """Fetch all labels"""
        url = f"{self.base_url}/labels"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_milestones(self) -> List[Dict]:
        """Fetch all milestones"""
        url = f"{self.base_url}/milestones?state=all"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_issue(self, title: str, body: str, labels: List[str], 
                     milestone: Optional[int] = None) -> Dict:
        """Create a new issue"""
        data = {
            "title": title,
            "body": body,
            "labels": labels
        }
        if milestone:
            data["milestone"] = milestone
        
        url = f"{self.base_url}/issues"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_issue(self, number: int, title: Optional[str] = None,
                     body: Optional[str] = None, labels: Optional[List[str]] = None,
                     milestone: Optional[int] = None, state: Optional[str] = None):
        """Update an existing issue"""
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if labels is not None:
            data["labels"] = labels
        if milestone is not None:
            data["milestone"] = milestone
        if state:
            data["state"] = state
        
        url = f"{self.base_url}/issues/{number}"
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_user_id(self) -> str:
        """Get user ID for GraphQL"""
        query = """
        query {
          viewer {
            id
            login
          }
        }
        """
        response = requests.post(self.graphql_url, headers=self.graphql_headers, 
                                json={"query": query})
        response.raise_for_status()
        return response.json()["data"]["viewer"]["id"]
    
    def create_project(self, title: str) -> Tuple[str, int]:
        """Create a new project (ProjectsV2)"""
        user_id = self.get_user_id()
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
        variables = {"ownerId": user_id, "title": title}
        response = requests.post(self.graphql_url, headers=self.graphql_headers,
                                json={"query": mutation, "variables": variables})
        response.raise_for_status()
        data = response.json()["data"]["createProjectV2"]["projectV2"]
        return data["id"], data["number"]
    
    def add_issue_to_project(self, project_id: str, issue_node_id: str):
        """Add issue to project"""
        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item {
              id
            }
          }
        }
        """
        variables = {"projectId": project_id, "contentId": issue_node_id}
        response = requests.post(self.graphql_url, headers=self.graphql_headers,
                                json={"query": mutation, "variables": variables})
        response.raise_for_status()


class TrackerParser:
    TASK_PATTERN = r'^- \[([ x])\] (.+?)$'
    FIELD_PATTERN = r'^\s+(\w+):\s*(.*)$'
    SECTION_PATTERN = r'^## (.+)$'
    
    @staticmethod
    def parse(content: str) -> List[Dict]:
        """Parse tracker.md"""
        tasks = []
        lines = content.split('\n')
        current_section = None
        current_task = None
        
        for line in lines:
            # Section header
            if match := re.match(TrackerParser.SECTION_PATTERN, line):
                current_section = match.group(1).strip()
                continue
            
            # Task line
            if match := re.match(TrackerParser.TASK_PATTERN, line):
                if current_task:
                    tasks.append(current_task)
                
                current_task = {
                    'checked': match.group(1) == 'x',
                    'title': match.group(2).strip(),
                    'section': current_section,
                    'metadata': {},
                    'raw_lines': [line]
                }
                continue
            
            # Metadata field
            if current_task and (match := re.match(TrackerParser.FIELD_PATTERN, line)):
                key, value = match.groups()
                current_task['metadata'][key] = value.strip()
                current_task['raw_lines'].append(line)
                continue
            
            # Empty line or unknown - add to current task if exists
            if current_task and line.strip() == '':
                current_task['raw_lines'].append(line)
        
        # Don't forget last task
        if current_task:
            tasks.append(current_task)
        
        return tasks
    
    @staticmethod
    def extract_tracker_id(body: str) -> Optional[str]:
        """Extract tracker-id from issue body"""
        if match := re.search(r'<!-- tracker-id: (.+?) -->', body):
            return match.group(1)
        return None


class Sync:
    def __init__(self, config: Dict, github: GitHubAPI):
        self.config = config
        self.github = github
        self.project_id = None
        self.milestone_map = {}  # title -> number
    
    def run(self):
        """Main sync logic"""
        print("=" * 70)
        print("🔄 GitHub Tracker Sync")
        print("=" * 70)
        
        # Phase 1: Pull GitHub state
        print("\n📥 Phase 1: Pulling GitHub state...")
        github_data = self.pull_github_state()
        
        # Phase 2: Parse tracker.md
        print("\n📖 Phase 2: Parsing tracker.md...")
        local_tasks = self.parse_tracker()
        
        # Phase 3: Compute diff
        print("\n🔍 Phase 3: Computing diff...")
        changes = self.compute_diff(local_tasks, github_data)
        
        # Phase 4: Push to GitHub
        print("\n📤 Phase 4: Pushing changes to GitHub...")
        self.push_changes(changes, github_data)
        
        # Phase 5: Pull UI changes
        print("\n⬇️  Phase 5: Pulling GitHub UI changes...")
        ui_changes = self.detect_ui_changes(github_data, local_tasks)
        
        # Phase 6: Update tracker.md
        if ui_changes:
            print("\n💾 Phase 6: Updating tracker.md...")
            self.update_tracker(ui_changes)
        
        print("\n" + "=" * 70)
        print("✅ Sync complete!")
        print("=" * 70)
    
    def pull_github_state(self) -> Dict:
        """Pull all data from GitHub"""
        issues = self.github.get_issues()
        milestones = self.github.get_milestones()
        
        # Build milestone map
        for ms in milestones:
            self.milestone_map[ms['title']] = ms['number']
        
        # Build tracker-id map
        tracker_map = {}
        for issue in issues:
            if tracker_id := TrackerParser.extract_tracker_id(issue.get('body', '')):
                tracker_map[tracker_id] = {
                    'number': issue['number'],
                    'title': issue['title'],
                    'state': issue['state'],
                    'labels': [l['name'] for l in issue.get('labels', [])],
                    'milestone': issue.get('milestone', {}).get('title') if issue.get('milestone') else None,
                    'node_id': issue['node_id']
                }
        
        print(f"  ✓ Found {len(issues)} issues ({len(tracker_map)} with tracker-id)")
        return {
            'issues': issues,
            'tracker_map': tracker_map,
            'milestones': milestones
        }
    
    def parse_tracker(self) -> List[Dict]:
        """Parse tracker.md file"""
        if not os.path.exists(TRACKER_FILE):
            print(f"  ✗ {TRACKER_FILE} not found!")
            return []
        
        with open(TRACKER_FILE, 'r') as f:
            content = f.read()
        
        tasks = TrackerParser.parse(content)
        print(f"  ✓ Parsed {len(tasks)} tasks")
        return tasks
    
    def compute_diff(self, local_tasks: List[Dict], github_data: Dict) -> List[Dict]:
        """Compute what needs to change"""
        changes = []
        tracker_map = github_data['tracker_map']
        
        for task in local_tasks:
            # Skip IDEAS section
            if task['section'] == 'IDEAS':
                continue
            
            task_id = task['metadata'].get('id', '')
            github_num = task['metadata'].get('github', '').strip()
            
            # Case 1: No tracker ID - skip or auto-generate
            if not task_id:
                print(f"  ⚠️  Task '{task['title']}' has no ID, skipping")
                continue
            
            # Case 2: Has ID but no GitHub number - create
            if not github_num:
                changes.append({
                    'action': 'create',
                    'task': task,
                    'task_id': task_id
                })
                continue
            
            # Case 3: Has both - check for updates
            github_issue = tracker_map.get(task_id)
            if not github_issue:
                print(f"  ⚠️  Task {task_id} has github:{github_num} but not found in GitHub")
                continue
            
            # Compare fields
            needs_update = {}
            
            if task['title'] != github_issue['title']:
                needs_update['title'] = task['title']
            
            local_labels = set(task['metadata'].get('labels', '').split(','))
            github_labels = set(github_issue['labels'])
            if local_labels != github_labels:
                needs_update['labels'] = list(local_labels)
            
            local_milestone = task['metadata'].get('milestone', '')
            if local_milestone != github_issue.get('milestone', ''):
                needs_update['milestone'] = local_milestone
            
            # State changes
            should_be_closed = task['checked']
            is_closed = github_issue['state'] == 'closed'
            
            if should_be_closed and not is_closed:
                needs_update['state'] = 'closed'
            elif not should_be_closed and is_closed:
                needs_update['state'] = 'open'
            
            if needs_update:
                changes.append({
                    'action': 'update',
                    'task_id': task_id,
                    'github_number': github_issue['number'],
                    'updates': needs_update
                })
        
        print(f"  ✓ Found {len(changes)} changes")
        return changes
    
    def push_changes(self, changes: List[Dict], github_data: Dict):
        """Push changes to GitHub"""
        if not changes:
            print("  ✓ No changes to push")
            return
        
        # Ensure project exists
        if not self.project_id:
            print("  📋 Creating new project...")
            self.project_id, project_num = self.github.create_project(
                self.config['project_name']
            )
            print(f"  ✓ Created project #{project_num}")
        
        for change in changes:
            if change['action'] == 'create':
                self.create_issue_on_github(change, github_data)
                time.sleep(0.2)  # Rate limiting
            elif change['action'] == 'update':
                self.update_issue_on_github(change)
                time.sleep(0.2)
    
    def create_issue_on_github(self, change: Dict, github_data: Dict):
        """Create a new issue on GitHub"""
        task = change['task']
        task_id = change['task_id']
        
        # Build issue body with tracker-id
        body = f"""<!-- tracker-id: {task_id} -->

**Epic**: {task['metadata'].get('epic', 'N/A')}
**Type**: {task['metadata'].get('type', 'task')}
**Priority**: {task['metadata'].get('priority', 'p2')}

{task['metadata'].get('description', '')}
"""
        
        # Get milestone number
        milestone_name = task['metadata'].get('milestone', '')
        milestone_num = self.milestone_map.get(milestone_name)
        
        # Get labels
        labels = [l.strip() for l in task['metadata'].get('labels', '').split(',') if l.strip()]
        
        print(f"  ➕ Creating: {task['title']}")
        issue = self.github.create_issue(
            title=task['title'],
            body=body,
            labels=labels,
            milestone=milestone_num
        )
        
        # Add to project
        if self.project_id:
            self.github.add_issue_to_project(self.project_id, issue['node_id'])
        
        # Update tracker.md with issue number
        self.update_tracker_github_field(task_id, issue['number'])
        
        print(f"    ✓ Created #{issue['number']}")
    
    def update_issue_on_github(self, change: Dict):
        """Update an existing issue on GitHub"""
        updates = change['updates']
        number = change['github_number']
        
        print(f"  📝 Updating #{number}: {', '.join(updates.keys())}")
        
        # Prepare update data
        milestone_num = None
        if 'milestone' in updates:
            milestone_name = updates['milestone']
            milestone_num = self.milestone_map.get(milestone_name)
        
        self.github.update_issue(
            number=number,
            title=updates.get('title'),
            labels=updates.get('labels'),
            milestone=milestone_num,
            state=updates.get('state')
        )
        print(f"    ✓ Updated")
    
    def detect_ui_changes(self, github_data: Dict, local_tasks: List[Dict]) -> List[Dict]:
        """Detect changes made on GitHub UI"""
        ui_changes = []
        tracker_map = github_data['tracker_map']
        
        for task in local_tasks:
            task_id = task['metadata'].get('id', '')
            if not task_id or task['section'] == 'IDEAS':
                continue
            
            github_issue = tracker_map.get(task_id)
            if not github_issue:
                continue
            
            # Check if closed on GitHub but not locally
            if github_issue['state'] == 'closed' and not task['checked']:
                ui_changes.append({
                    'task_id': task_id,
                    'action': 'mark_done'
                })
            # Check if reopened on GitHub
            elif github_issue['state'] == 'open' and task['checked']:
                ui_changes.append({
                    'task_id': task_id,
                    'action': 'mark_todo'
                })
        
        if ui_changes:
            print(f"  ✓ Found {len(ui_changes)} UI changes")
        else:
            print("  ✓ No UI changes detected")
        
        return ui_changes
    
    def update_tracker(self, ui_changes: List[Dict]):
        """Update tracker.md based on GitHub UI changes"""
        with open(TRACKER_FILE, 'r') as f:
            lines = f.readlines()
        
        # Apply changes
        current_id = None
        for i, line in enumerate(lines):
            # Detect ID line
            if match := re.match(r'\s+id:\s*(.+)$', line):
                current_id = match.group(1).strip()
            
            # Check if this task needs update
            for change in ui_changes:
                if change['task_id'] == current_id:
                    # Find task line (search backwards)
                    for j in range(i-1, -1, -1):
                        if re.match(TrackerParser.TASK_PATTERN, lines[j]):
                            if change['action'] == 'mark_done':
                                lines[j] = lines[j].replace('[ ]', '[x]')
                                print(f"  ✓ Marked {current_id} as done")
                            elif change['action'] == 'mark_todo':
                                lines[j] = lines[j].replace('[x]', '[ ]')
                                print(f"  ✓ Marked {current_id} as todo")
                            break
        
        # Write atomically
        temp_file = TRACKER_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            f.writelines(lines)
        os.replace(temp_file, TRACKER_FILE)
        print(f"  ✓ Updated {TRACKER_FILE}")
    
    def update_tracker_github_field(self, task_id: str, issue_number: int):
        """Update the github: field in tracker.md"""
        with open(TRACKER_FILE, 'r') as f:
            lines = f.readlines()
        
        current_id = None
        for i, line in enumerate(lines):
            if match := re.match(r'\s+id:\s*(.+)$', line):
                current_id = match.group(1).strip()
            
            if current_id == task_id:
                # Find github: line
                for j in range(i, min(i+10, len(lines))):
                    if re.match(r'\s+github:\s*', lines[j]):
                        lines[j] = f"  github: {issue_number}\n"
                        break
                break
        
        # Write
        temp_file = TRACKER_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            f.writelines(lines)
        os.replace(temp_file, TRACKER_FILE)


def main():
    # Load config
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: {CONFIG_FILE} not found")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get GitHub token
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Initialize
    github = GitHubAPI(token, config['repo_owner'], config['repo_name'])
    sync = Sync(config, github)
    
    # Run sync
    try:
        sync.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
