# Git Commands for 247 Exams Project

This document provides basic Git commands and helper scripts to manage your GitHub repository.

## Quick Upload Scripts

### 1. Simple Push Script (`git-push.sh`)
Interactive script that guides you through uploading changes:

```bash
# Make executable (only needed once)
chmod +x git-push.sh

# Usage
./git-push.sh "Your commit message"
# OR run without message to be prompted
./git-push.sh
```

### 2. Git Commands Helper (`git-commands.sh`)
Comprehensive script with multiple Git operations:

```bash
# Make executable (only needed once)
chmod +x git-commands.sh

# Available commands:
./git-commands.sh status              # Check current status
./git-commands.sh add                 # Add all changes
./git-commands.sh commit "message"    # Commit with message
./git-commands.sh push                # Push to GitHub
./git-commands.sh pull                # Pull from GitHub
./git-commands.sh quick "message"     # Quick: add + commit + push
./git-commands.sh log                 # Show recent commits
./git-commands.sh diff                # Show changes
./git-commands.sh help                # Show all commands
```

## Manual Git Commands

### Basic Workflow
```bash
# 1. Check status
git status

# 2. Add all changes
git add .

# 3. Commit changes
git commit -m "Your commit message

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. Push to GitHub
git push origin master
```

### Common Commands
```bash
# View commit history
git log --oneline -10

# See what changed
git diff

# Pull latest changes from GitHub
git pull origin master

# Check remote repository
git remote -v

# View branches
git branch -a

# Create new branch
git checkout -b feature-name

# Switch back to master
git checkout master
```

### Emergency Commands
```bash
# Undo last commit (keeps changes)
git reset --soft HEAD~1

# Discard all local changes (DANGEROUS!)
git reset --hard HEAD

# See what will be committed
git diff --staged

# Unstage files
git reset HEAD filename
```

## Quick Examples

### Upload New Changes
```bash
# Method 1: Using helper script
./git-commands.sh quick "Added user authentication"

# Method 2: Using simple push script
./git-push.sh "Fixed login bug"

# Method 3: Manual commands
git add .
git commit -m "Updated dashboard layout"
git push origin master
```

### Check What Changed
```bash
# See status
./git-commands.sh status

# See detailed changes
./git-commands.sh diff

# See recent commits
./git-commands.sh log
```

### Pull Updates from GitHub
```bash
# If others made changes
./git-commands.sh pull

# Or manually
git pull origin master
```

## Repository Information
- **Repository**: https://github.com/gauri1991/247exams.git  
- **Branch**: master
- **Remote**: origin

## Tips
1. Always commit frequently with meaningful messages
2. Pull before pushing if working with others
3. Use descriptive commit messages
4. Test your code before committing
5. Use `.gitignore` to exclude unnecessary files (already set up)

## Troubleshooting

### Push Rejected
```bash
# Pull first, then push
git pull origin master
git push origin master
```

### Merge Conflicts
```bash
# After pulling, edit conflicted files
# Then add and commit
git add .
git commit -m "Resolved merge conflicts"
git push origin master
```

### Reset Everything
```bash
# DANGER: Loses all changes
./git-commands.sh reset
```