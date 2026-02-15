# Universal GitHub Tracker System

**Local-first task management with bidirectional GitHub sync**

## 🎯 What This Is

A workflow where:
- ✅ `tracker.md` is your single source of truth
- ✅ Edit locally in markdown (you or AI)
- ✅ Run `sync.py` to sync with GitHub
- ✅ Changes on GitHub sync back to local
- ✅ No duplicates, fully automated

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Set GitHub Token

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Get token from: https://github.com/settings/tokens (needs `repo` + `project` scopes)

### 3. Edit `tracker.md`

Add,move, or update tasks:

```markdown
## BACKLOG

- [ ] New feature
  id: feat-101
  type: feature
  priority: p1
  milestone: Milestone 2: Media & Backup
  labels: feature,media
  github:
```

### 4. Sync

```bash
python3 sync.py
```

That's it! ✅

---

## 📝 tracker.md Format

### Sections

```markdown
## BACKLOG        # Not started
## IN_PROGRESS    # Being worked on
## DONE           # Completed
## IDEAS          # Not synced to GitHub
```

### Task Format

```markdown
- [ ] Task title
  id: unique-id
  type: feature|bug|enhancement|testing
  priority: p0|p1|p2|p3
  milestone: milestone-name
  labels: comma,separated,labels
  github: issue_number_or_blank
```

**Rules:**
- `[x]` = closed, `[ ]` = open
- `id` is permanent, never change it
- `github` is auto-filled after creation
- Move tasks between sections to change status
- IDEAS section not synced to GitHub

---

## 🔄 How Sync Works

### Push (Local → GitHub)

1. **New task** (no `github:`) → Creates GitHub issue
2. **Changed title/labels** → Updates GitHub issue
3. **Marked `[x]`** → Closes GitHub issue
4. **Unmarked `[ ]`** → Reopens GitHub issue
5. **Moved section** → Moves project column

### Pull (GitHub → Local)

1. **Issue closed on GitHub** → Marks `[x]` locally
2. **Issue reopened on GitHub** → Marks `[ ]` locally
3. **New issue on GitHub** → Pulls to tracker.md (if configured)

---

## 🎨 Workflows

### Daily Use

```bash
# Edit tracker.md
vim tracker.md

# Sync
python3 sync.py
```

### With AI

```
User: "Add 3 new tasks for media gallery totracker.md"
AI: [edits tracker.md]
User: "Sync"
AI: [runs python3 sync.py]
```

### Marking Done

Change `[ ]` to `[x]` in tracker.md and sync:

```markdown
- [x] Completed task
  id: feat-001
  ...
```

---

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
repo_owner: yallabalaji
repo_name: macos-android-manager
project_name: Android Device Manager v2

sections:
  BACKLOG: Todo
  IN_PROGRESS: In Progress
  DONE: Done

orphan_behavior: pull  # pull | ignore | close
```

**orphan_behavior:**
- `pull`: Sync GitHub-only issues to tracker.md
- `ignore`: Don't touch GitHub-only issues
- `close`: Close GitHub-only issues

---

## 🛡️ Safety

✅ **Idempotent** - Run multiple times safely  
✅ **No duplicates** - tracker-id prevents duplication  
✅ **Atomic updates** - tracker.md written safely  
✅ **Network retry** - Handles transient failures

---

## 🔧 Troubleshooting

### "GITHUB_TOKEN not set"
```bash
export GITHUB_TOKEN="ghp_..."
```

### Sync not working?
Check `tracker.md` format is correct:
- All tasks have unique `id:`
- Fields use correct indentation (2 spaces)
- Section names match config.yaml

### Duplicate issues created?
Run sync again - it will detect existing issues by tracker-id and won't duplicate.

---

## 💡 Tips

### Auto-sync on save

Create a git hook or use a file watcher:

```bash
# .git/hooks/pre-commit
python3 sync.py
```

### Commit tracker.md

```bash
git add tracker.md
git commit -m "Updated tasks"
git push
```

### Review changes

```bash
git diff tracker.md
```

---

## 📊 Example Workflow

```bash
# Start of day
vim tracker.md
# Add new tasks to BACKLOG

# Sync
python3 sync.py
# ✓ Creates GitHub issues, adds to project

# GitHub UI: Someone closes issue #15

# Pull changes
python3 sync.py
# ✓ Marks task feat-015 as [x] in tracker.md

# End of day
git add tracker.md
git commit -m "Daily task updates"
git push
```

---

## 🚀 Benefits

- ✅ **Fast** - Edit markdown locally
- ✅ **Offline** - Work without internet, sync later
- ✅ **Version control** - Git tracks all changes
- ✅ **AI-friendly** - Simple format for AI to edit
- ✅ **Powerful** - Full GitHub integration
- ✅ **Reusable** - One system for all projects

---

## 📦 What's Included

- `sync.py` - Bidirectional sync engine
- `tracker.md` - Your task database (20 tasks migrated)
- `config.yaml` - Project configuration
- `requirements.txt` - Python dependencies
- `README.md` - This file

---

**Ready to use! Your 20 existing issues are already in `tracker.md`.** 🎉
