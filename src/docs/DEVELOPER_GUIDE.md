# Developer Guide

This guide provides comprehensive information for developers contributing to the WebexRegressShield project.

## Table of Contents

- [Repository Setup](#repository-setup)
  - [Clone with Submodules](#clone-with-submodules)
  - [First-Time Setup](#first-time-setup)
- [Working with Git](#working-with-git)
  - [Recommended Workflow](#recommended-workflow)
  - [Git Best Practices](#git-best-practices)
- [Test Case Development](#test-case-development)
  - [Working with Test Cases](#working-with-test-cases)
  - [Test Case Structure](#test-case-structure)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Repository Setup

### Clone with Submodules

The test cases are managed in a separate repository as a Git submodule for better team collaboration and modularity.

**Repositories:**
- **Main Repository**: `git@sqbu-github.cisco.com:binbiwan/webex-regress-shield.git`
- **Test Space Submodule**: `git@sqbu-github.cisco.com:binbiwan/wrs_test_space.git`

### First-Time Setup

**Clone with submodules in one command:**

```bash
git clone --recurse-submodules git@sqbu-github.cisco.com:binbiwan/webex-regress-shield.git
cd webex-regress-shield
```

**Or if you already cloned without submodules:**

```bash
git clone git@sqbu-github.cisco.com:binbiwan/webex-regress-shield.git
cd webex-regress-shield
git submodule update --init --recursive
```

**Verify submodule is loaded:**

```bash
ls src/test_space
# Should show test case files and directories
```

## Working with Git

### Recommended Workflow

We follow the **Feature Branch Workflow**. For detailed Git workflow best practices, see [Git Workflow Guide](GIT_WORKFLOW.md).

**Complete Best Practice Workflow:**

```bash
# ========================================
# 1. START: Create Feature Branch
# ========================================
git checkout main
git pull origin main                    # Ensure local main is up-to-date
git checkout -b feat/your-feature       # Create feature branch from main

# ========================================
# 2. DEVELOPMENT: Daily Work & Sync
# ========================================
# Make your changes...
git add .
git commit -m "feat: add your feature"

# Option A: Direct sync (Recommended for simplicity)
git pull origin main                    # Sync main updates to feature branch

# Option B: Standard merge approach (Recommended for clarity)
git checkout main
git pull origin main                    # Update local main
git checkout feat/your-feature
git merge main                          # Merge main into feature branch

# Option C: Rebase approach (Recommended for clean history)
git checkout main
git pull origin main
git checkout feat/your-feature
git rebase main                         # Rebase feature branch on main

# Resolve conflicts if any
git add .
git commit -m "fix: resolve merge conflicts with main"

# ========================================
# 3. BEFORE PUSH: Final Sync
# ========================================
git checkout main
git pull origin main                    # Ensure main is latest
git checkout feat/your-feature
git merge main                          # Final merge before push
# Resolve any conflicts
git add .
git commit -m "fix: resolve conflicts"

# ========================================
# 4. PUSH: Submit Your Work
# ========================================
git push origin feat/your-feature       # Push feature branch to remote

# Common mistake to AVOID:
# ❌ git push origin main:feat/your-feature  # This pushes main to feat/your-feature!
# ✅ git push origin feat/your-feature       # This pushes current branch

# ========================================
# 5. CREATE PR: Code Review
# ========================================
# Create Pull Request on GitHub/GitLab
# Wait for review and approval

# ========================================
# 6. CLEANUP: After PR Merge
# ========================================
git checkout main
git pull origin main                    # Get merged changes
git branch -d feat/your-feature         # Delete local branch
git push origin --delete feat/your-feature  # Delete remote branch (optional)
```

**Quick Reference for Daily Development:**

```bash
# Morning: Start work
git checkout feat/your-feature
git pull origin main                    # Sync with main updates

# During day: Commit changes
git add .
git commit -m "feat: implement feature X"

# Afternoon: Sync again
git pull origin main                    # Stay updated

# End of day: Push work
git push origin feat/your-feature
```

### Git Best Practices

#### Do's ✅

- **Keep local `main` branch clean**: Only pull, never commit directly to main
- **Use descriptive branch names**: Use prefixes like `feat/`, `fix/`, `docs/`
  - Example: `feat/add-chatbot-gui`, `fix/token-refresh`, `docs/update-readme`
- **Write clear commit messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation changes
  - `refactor:` Code restructuring
  - `test:` Adding tests
- **Sync `main` regularly**: Pull main updates frequently to avoid large conflicts
  - Recommended: At least once daily during active development
  - Before every push: Ensure you have latest main changes
- **Resolve conflicts early**: Sync often to catch conflicts when they're small
- **Use correct push command**: `git push origin your-branch` (not `main:your-branch`)

#### Don'ts ❌

- **Don't commit directly to `main`**: Always use feature branches
- **Don't push without syncing first**: Always `git pull origin main` before pushing
- **Don't let feature branches diverge too far**: Sync with main frequently
- **Don't force push without discussion**: Use `--force` only when necessary
- **Don't ignore merge conflicts**: Resolve them properly, don't just accept all changes

#### Why Sync Main Regularly?

1. **Early conflict detection**: Conflicts are easier to resolve when small
2. **Stay up-to-date**: Your feature is based on latest code
3. **Easier PR review**: Reviewers see clean diffs without merge noise
4. **Avoid big surprises**: No massive merge conflicts at the end

**For complete Git workflow details, see [GIT_WORKFLOW.md](GIT_WORKFLOW.md)**

## Test Case Development

### Working with Test Cases

Test cases are located in the `src/test_space` directory, which is a Git submodule.

**Pull latest test cases:**

```bash
# From project root
git pull
git submodule update --remote --merge
```

**Modify test cases:**

```bash
# 1. Navigate to test_space submodule
cd src/test_space

# 2. Create feature branch for test changes
git checkout -b feat/add-new-test

# 3. Make changes to test files
# Edit YAML files in src/test_space/test_cases/

# 4. Commit changes to submodule
git add .
git commit -m "feat: add new test case for feature X"
git push origin feat/add-new-test

# 5. Create PR for test_space repository

# 6. After PR merge, update main repo to reference new submodule commit
cd ../..  # Back to project root
git add src/test_space
git commit -m "Update test_space submodule to include new test"
git push origin your-feature-branch
```

**Add submodule** (for new repository setup only):

```bash
git submodule add git@sqbu-github.cisco.com:binbiwan/wrs_test_space.git src/test_space
```

### Test Case Structure

Test cases are defined in YAML format under `src/test_space/test_cases/`:

```text
src/test_space/
├── test_cases/
│   ├── app_core/          # Core app functionality
│   │   ├── sign_in.yaml
│   │   └── sign_out.yaml
│   ├── meetings/          # Meeting features
│   │   ├── video/
│   │   │   ├── vbg_static.yaml
│   │   │   └── vbg_dynamic.yaml
│   │   └── audio/
│   └── ...
├── test_suites/           # Test suite configurations
│   ├── smoke.yaml
│   ├── video_vbg.yaml
│   └── ...
└── datasets/              # Test data and control datasets
```

**Example test case structure:**

```yaml
# test_cases/meetings/video/vbg_static.yaml
test_case:
  name: vbg_static
  description: Verify static virtual background functionality
  category: meetings
  sub_category: video
  
  steps:
    - action: click_control
      control: "Video options"
    - action: select_background
      background: "Office"
    - action: verify
      expected: "Background applied successfully"
```

## Installation

WebexRegressShield requires Python 3.10.11 or later and uses UV for package management.

**Install UV:**

```bash
pip install uv
```

**Install project dependencies:**

```bash
# From project root
uv sync
```

**Setup environment variables:**

Create a `.env` file in the project root (copy from `.env.example` if available):

```bash
PYTHONPATH=C:\path\to\webex-regress-shield
# Add other required environment variables
```

## Running Tests

### Test Execution Modes

#### Test Suite Mode

Run a collection of test cases for comprehensive feature validation:

```bash
# Run video virtual background test suite
uv run python src/run_test_case_job.py --test_suite "video_vbg"

# Run with OpenAI for screen reader validation
uv run python src/run_test_case_job.py --test_suite "video_vbg" --openai
```

#### Test Case Mode

Run a single test case in isolation:

```bash
# Run specific test case
uv run python src/run_test_case_job.py --test_case "vbg_static"

# Run with OpenAI features
uv run python src/run_test_case_job.py --test_case "vbg_static" --openai

# Run stress test with keep app option
uv run python src/run_test_case_job.py --test_case "stress/test_stress" --keepApp
```

#### Test Batch Mode

Run multiple independent test cases:

```bash
# Run batch of video tests
uv run python src/run_test_case_job.py --test_batch "video_vbg_batch"
```

#### Performance Testing

Run performance and stress tests:

```bash
# Basic performance test
uv run python src/run_test_case_job.py --test_case "performance/baseline"

# Stress test with specific configuration
uv run python src/run_test_case_job.py --test_case "stress/test_stress" --keepApp
```

### Common Test Options

| Option | Description |
|--------|-------------|
| `--test_suite <name>` | Run a test suite |
| `--test_case <name>` | Run a single test case |
| `--test_batch <name>` | Run a batch of test cases |
| `--openai` | Enable OpenAI features (screen reader, localization) |
| `--keepApp` | Keep application open after test completion |
| `--platform <platform>` | Specify platform (windows/mac/web) |

## Project Structure

```text
webex-regress-shield/
├── src/
│   ├── run_test_case_job.py      # Main test runner
│   ├── run_locator.py             # Control locator tool
│   ├── config/                    # Configuration files
│   ├── core/                      # Core framework
│   │   ├── explorer_base.py
│   │   ├── suite_case_runner.py
│   │   └── test_case_runner.py
│   ├── common/                    # Common utilities
│   ├── db/                        # Database modules
│   ├── functions/                 # Test step functions
│   ├── docs/                      # Documentation
│   │   ├── GIT_WORKFLOW.md       # Git workflow guide
│   │   └── DEVELOPER_GUIDE.md    # This file
│   └── test_space/                # Test cases (submodule)
│       ├── test_cases/
│       ├── test_suites/
│       └── datasets/
├── .env                           # Environment variables
├── pyproject.toml                 # Project dependencies
└── README.md                      # Project overview
```

## Contributing

### Before You Start

1. Read the [Git Workflow Guide](GIT_WORKFLOW.md)
2. Familiarize yourself with test case structure
3. Set up your development environment

### Contribution Process

1. **Create an issue**: Describe the bug or feature
2. **Create a feature branch**: `git checkout -b feat/your-feature`
3. **Make changes**: Follow code style and conventions
4. **Write tests**: Add or update test cases as needed
5. **Commit changes**: Use conventional commit messages
6. **Push and create PR**: Get code reviewed
7. **Address feedback**: Make requested changes
8. **Merge**: Once approved, merge to main

### Code Style

- **Python**: Follow PEP 8 style guide
- **YAML**: Use 2-space indentation
- **Comments**: Write clear, concise comments
- **Documentation**: Update docs for new features

### Testing

Before submitting a PR:

```bash
# Run smoke tests
uv run python src/run_test_case_job.py --test_suite "smoke"

# Run affected test cases
uv run python src/run_test_case_job.py --test_case "your_test"

# Verify no regressions
```

### Pull Request Guidelines

- **Title**: Use conventional commit format
  - `feat: add new feature`
  - `fix: resolve bug`
  - `docs: update documentation`
- **Description**: Explain what and why
- **Tests**: Include test results
- **Screenshots**: For UI changes
- **Reviewers**: Tag relevant team members

## Additional Resources

- [Git Workflow Best Practices](GIT_WORKFLOW.md)
- [Control Locator Documentation](../test_space/datasets/README_LOCATOR.md)
- [Test Case Documentation](../test_space/README.md)
- [Project README](../../README.md)

## Getting Help

- **Issues**: Report bugs or request features on GitHub
- **Questions**: Contact the development team
- **Documentation**: Check docs in `src/docs/`

---

**Happy coding! 🚀**
