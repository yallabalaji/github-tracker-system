# How to Use This Tracker for a New Project

This guide shows you how to use the GitHub Tracker System for any project.

---

## 🚀 Quick Setup (5 minutes)

### 1. Clone or Download

```bash
# Option A: Clone for new project
git clone https://github.com/yallabalaji/github-tracker-system.git my-project-tracker
cd my-project-tracker

# Option B: Copy files to existing project
cp -r github-tracker-system/* my-existing-project/
cd my-existing-project
```

---

### 2. Configure for Your Project

**Copy and edit config:**

```bash
cp config.template.yaml config.yaml
vim config.yaml
```

**Update with your project details:**

```yaml
repo_owner: YOUR_GITHUB_USERNAME
repo_name: YOUR_REPO_NAME
project_name: YOUR_PROJECT_NAME
```

Example:
```yaml
repo_owner: yallabalaji
repo_name: my-awesome-app
project_name: My Awesome App
```

---

### 3. Create Your Task List

**Copy template:**

```bash
cp tracker.template.md tracker.md
vim tracker.md
```

**Add your tasks:**

```markdown
## BACKLOG

- [ ] User authentication
  id: feat-001
  type: feature
  priority: p0
  milestone: v1.0
  labels: feature,auth
  github:

- [ ] Database setup  
  id: feat-002
  type: feature
  priority: p0
  milestone: v1.0
  labels: feature,backend
  github:
```

---

### 4. Install Dependencies

```bash
pip3 install -r requirements.txt
```

---

### 5. Set GitHub Token

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Get token from: https://github.com/settings/tokens

**Required scopes:**
- ✅ `repo` (Full control)
- ✅ `project` (Full control)

---

### 6. Run Sync

```bash
python3 sync.py
```

**What happens:**
1. Creates GitHub issues for all tasks
2. Creates project board
3. Adds all issues to project
4. Updates `tracker.md` with issue numbers

---

## 📋 Daily Workflow

### Add New Task

**Edit `tracker.md`:**

```markdown
## BACKLOG

- [ ] Add dark mode
  id: feat-010
  type: feature
  priority: p1
  milestone: v1.1
  labels: feature,ui
  github:
```

**Sync:**

```bash
python3 sync.py
```

✅ Issue created on GitHub!

---

### Mark Task Done

**In `tracker.md`:**

```markdown
- [x] User authentication  # Changed [ ] to [x]
  id: feat-001
  ...
```

**Sync:**

```bash
python3 sync.py
```

✅ Issue closed on GitHub!

---

### Pull GitHub Changes

Someone closed issue #5 on GitHub:

```bash
python3 sync.py
```

✅ `tracker.md` updated with `[x]`!

---

## 🔄 Reusing for Another Project

**Step 1: Copy the system**

```bash
cp -r github-tracker-system my-new-project-tracker
cd my-new-project-tracker
```

**Step 2: Clean existing data**

```bash
rm tracker.md
cp tracker.template.md tracker.md
```

**Step 3: Configure**

```bash
vim config.yaml
# Update repo_owner, repo_name, project_name
```

**Step 4: Add tasks and sync**

```bash
vim tracker.md  # Add your tasks
python3 sync.py
```

**Done!** 🎉

---

## 💡 Pro Tips

### Use with AI

```
"Add 5 features to tracker.md for user dashboard"
→ AI edits tracker.md
→ Run: python3 sync.py
→ All synced to GitHub!
```

### Version Control

```bash
git add tracker.md
git commit -m "Updated tasks"
git push
```

### Multiple Projects

Keep one tracker folder per project:

```
~/projects/
  ├── app1-tracker/
  │   ├── sync.py
  │   ├── tracker.md
  │   └── config.yaml (→ app1 repo)
  ├── app2-tracker/
  │   ├── sync.py
  │   ├── tracker.md
  │   └── config.yaml (→ app2 repo)
```

---

## 🛠️ Advanced Usage

### Create Project First

If you want to create an empty project board first:

```bash
python3 create_project.py
```

This:
- Creates project on GitHub
- Adds all existing issues to it

### Custom Section Names

Edit `config.yaml`:

```yaml
sections:
  BACKLOG: To Do
  IN_PROGRESS: Working On
  DONE: Completed
  REVIEW: In Review  # Add custom sections
```

Then update section names in `tracker.md`:

```markdown
## REVIEW

- [ ] Code review needed
  ...
```

---

## 📚 Example: Full New Project Setup

```bash
# 1. Clone tracker system
git clone https://github.com/yallabalaji/github-tracker-system.git ecommerce-tracker
cd ecommerce-tracker

# 2. Configure
cp config.template.yaml config.yaml
cat > config.yaml << EOF
repo_owner: yallabalaji
repo_name: ecommerce-app
project_name: E-Commerce App
sections:
  BACKLOG: Todo
  IN_PROGRESS: In Progress
  DONE: Done
orphan_behavior: pull
auto_id_prefix: feat-
EOF

# 3. Create tasks
cp tracker.template.md tracker.md
cat >> tracker.md << EOF
## BACKLOG

- [ ] Product catalog
  id: feat-001
  type: feature
  priority: p0
  milestone: v1.0
  labels: feature,backend
  github:

- [ ] Shopping cart
  id: feat-002
  type: feature
  priority: p0
  milestone: v1.0
  labels: feature,frontend
  github:
EOF

# 4. Install and sync
pip3 install -r requirements.txt
export GITHUB_TOKEN="ghp_..."
python3 sync.py

# ✅ Done! Project created with 2 issues
```

---

## 🎯 Summary

**For every new project:**

1. Copy system files
2. Update `config.yaml`
3. Create `tracker.md`
4. Run `sync.py`

**That's it!** You now have:
- ✅ GitHub Issues
- ✅ Project Board
- ✅ Bidirectional Sync
- ✅ Local Task Management

**Use this system for all your projects!** 🚀
