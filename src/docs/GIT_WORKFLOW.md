# Git Workflow Best Practices

This document outlines the recommended Git workflow for contributing to the WebexRegressShield project.

## Table of Contents

- [Overview](#overview)
- [Feature Branch Workflow](#feature-branch-workflow)
- [Step-by-Step Guide](#step-by-step-guide)
- [Branch Management](#branch-management)
- [Common Scenarios](#common-scenarios)
- [Best Practices Summary](#best-practices-summary)

## Overview

We follow the **Feature Branch Workflow** to maintain code quality and enable smooth collaboration. The core principle is:

- **`main` branch**: Always stays clean and synced with remote
- **Feature branches**: Used for all development work
- **Pull Requests**: Required for merging changes into `main`

## Feature Branch Workflow

```
Remote main (origin/main)
    ↓ git pull
Local main (clean, read-only)
    ↓ git checkout -b feature-branch
Local feature branch
    ↓ develop & commit
    ↓ git push origin feature-branch
Remote feature branch
    ↓ Create Pull Request
Remote main (after PR merge)
    ↓ git pull
Local main (updated)
```

## Step-by-Step Guide

### 1. Start New Work

Always start from the latest `main` branch:

```bash
# Switch to main branch
git checkout main

# Pull latest changes from remote
git pull origin main

# Create and switch to new feature branch
git checkout -b gt-feature
```

**In VS Code:**
1. Click branch name in bottom status bar
2. Select "Create new branch from..."
3. Choose `main` as base branch
4. Enter new branch name: `gt-feature`

### 2. Develop on Feature Branch

Make changes and commit regularly:

```bash
# Check current branch
git branch

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new control locator functionality"

# Push to remote feature branch
git push origin gt-feature
```

**In VS Code:**
1. Open Source Control panel (`Ctrl+Shift+G`)
2. Stage changes by clicking `+` next to files
3. Enter commit message
4. Click `✓ Commit` button
5. Click `↑ Push` or "Sync Changes"

### 3. Keep Feature Branch Updated

Regularly sync with remote `main` to avoid conflicts:

```bash
# Method 1: Merge (preserves history)
git pull origin main

# Method 2: Rebase (linear history)
git pull origin main --rebase
```

**In VS Code:**
1. Press `Ctrl+Shift+P`
2. Type and select: `Git: Pull from...`
3. Select `origin`
4. Select `main`

### 4. Create Pull Request

Once feature is complete:

```bash
# Ensure all changes are pushed
git push origin gt-feature
```

Then:
1. Go to GitHub/GitLab
2. Navigate to repository
3. Click "New Pull Request"
4. Set base: `main`, compare: `gt-feature`
5. Add description and reviewers
6. Submit PR

### 5. After PR is Merged

Clean up and update local repository:

```bash
# Switch back to main
git checkout main

# Pull merged changes
git pull origin main

# Delete local feature branch
git branch -d gt-feature

# Optional: Delete remote feature branch
git push origin --delete gt-feature
```

**In VS Code:**
1. Switch to `main` branch (click branch name in status bar)
2. Pull changes (Sync button or `Ctrl+Shift+P` → `Git: Pull`)
3. Right-click feature branch in Source Control → Delete Branch

## Branch Management

### Branch Naming Convention

Use descriptive names with prefixes:

- `feat/` - New features: `feat/control-locator`
- `fix/` - Bug fixes: `fix/navigation-error`
- `docs/` - Documentation: `docs/update-readme`
- `refactor/` - Code refactoring: `refactor/cleanup-handlers`
- `test/` - Test additions: `test/add-unit-tests`

### Branch Lifecycle

| Branch Type | Lifetime | Purpose |
|------------|----------|---------|
| **main** | Permanent | Stable production code |
| **Feature branches** | Temporary | Active development |
| **Release branches** | Temporary | Prepare releases (if used) |

## Common Scenarios

### Scenario 1: Fix Your Current Workflow

If you've been developing on local `main` and pushing to remote feature branch:

```bash
# 1. Ensure feature branch has all changes
git checkout gt-feature
git add .
git commit -m "Your changes"
git push origin gt-feature

# 2. Reset local main to match remote
git checkout main
git reset --hard origin/main

# 3. Continue development on feature branch
git checkout gt-feature
```

### Scenario 2: Handle Submodule Changes

When `src/test_space` submodule is modified:

```bash
# Stage submodule change
git add src/test_space

# Commit the submodule update
git commit -m "Update test_space submodule"

# Push to feature branch
git push origin gt-feature
```

**In VS Code:**
- Submodule changes appear as "modified" in Source Control
- Stage and commit like regular files

### Scenario 3: Resolve Merge Conflicts

When pulling `main` into feature branch causes conflicts:

```bash
# Attempt to pull
git pull origin main

# If conflicts occur, resolve them manually
# Edit conflicted files, remove conflict markers
# <<<<<<<, =======, >>>>>>>

# Stage resolved files
git add .

# Complete the merge
git commit -m "Merge main into gt-feature"
```

**In VS Code:**
1. Conflicts highlighted in Source Control
2. Click file to open merge editor
3. Choose changes (Accept Current/Incoming/Both)
4. Save and stage resolved files
5. Commit merge

### Scenario 4: Switching Between Branches

```bash
# Save current work (if uncommitted)
git stash

# Switch to another branch
git checkout main

# Switch back and restore work
git checkout gt-feature
git stash pop
```

**In VS Code:**
1. Click branch name in status bar
2. Select target branch
3. If uncommitted changes exist, VS Code will prompt to stash

## Best Practices Summary

### ✅ DO

- **Keep local `main` clean**: Only pull, never commit directly
- **Use descriptive branch names**: Follow naming conventions
- **Commit frequently**: Small, logical commits with clear messages
- **Pull `main` regularly**: Keep feature branch updated
- **Write good commit messages**: Use conventional commit format
  - `feat: add new feature`
  - `fix: resolve bug in navigation`
  - `docs: update README`
- **Review before pushing**: Check staged changes
- **Delete merged branches**: Clean up after PR merge

### ❌ DON'T

- **Don't commit to `main` directly**: Always use feature branches
- **Don't push without pulling**: May cause conflicts
- **Don't use vague commit messages**: "update" or "changes" are not helpful
- **Don't leave branches unmerged**: Complete or abandon feature branches
- **Don't force push to shared branches**: Use `--force` with caution

### Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring without functionality change
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, configuration, etc.)

**Examples:**

```bash
feat(locator): add fuzzy matching for Tree items

- Implement fuzzy_match_tree_item() method
- Handle multiple state words (expanded/collapsed/Selected)
- Support position-agnostic matching
- Update regex pattern to ignore state variations

Closes #123
```

```bash
fix(navigation): resolve window focus issue

The Settings window was not being focused correctly when
navigating from popup menus. Added explicit window search
and improved timing control.

Fixes #456
```

### Quick Reference Commands

| Task | Command |
|------|---------|
| **Check current branch** | `git branch` |
| **Create new branch** | `git checkout -b branch-name` |
| **Switch branch** | `git checkout branch-name` |
| **Pull latest main** | `git pull origin main` |
| **Push to feature branch** | `git push origin feature-branch` |
| **Check status** | `git status` |
| **View commit history** | `git log --oneline` |
| **Stage changes** | `git add .` |
| **Commit changes** | `git commit -m "message"` |
| **Delete local branch** | `git branch -d branch-name` |
| **Delete remote branch** | `git push origin --delete branch-name` |

### VS Code Shortcuts

| Task | Shortcut |
|------|----------|
| **Open Source Control** | `Ctrl+Shift+G` |
| **Open Command Palette** | `Ctrl+Shift+P` |
| **Commit** | `Ctrl+Enter` (in commit message box) |
| **Quick Open** | `Ctrl+P` |
| **Search** | `Ctrl+Shift+F` |

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [VS Code Git Integration](https://code.visualstudio.com/docs/editor/versioncontrol)

---

For questions or clarifications, contact the development team or refer to the project's main [README](../../README.md).
