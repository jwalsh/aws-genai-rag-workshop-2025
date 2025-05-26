# mise-en-place

Clean up and organize the repository at the end of a working session.

## What it does

This command ensures the repository is in a clean, well-organized state by:

1. **Repository cleanliness**
   - Checking git status for uncommitted changes
   - Ensuring all work is properly committed
   - Verifying no untracked files are left behind

2. **GitHub issues maintenance**
   - Reviewing open issues for outdated content
   - Closing completed issues
   - Updating issue descriptions with current status
   - Removing stale labels or milestones

3. **Documentation consistency**
   - Ensuring README references only `make` commands (not raw shell/terminal commands)
   - Verifying Makefile targets are documented in help
   - Checking that scripts are executable and documented
   - Updating any outdated examples or instructions

4. **Code organization**
   - Verifying tangled code matches org sources
   - Ensuring test files are up to date
   - Checking that generated files are properly gitignored

## Checklist

```markdown
## Repository Status
- [ ] Git status is clean (no uncommitted changes)
- [ ] All feature branches are merged or have open PRs
- [ ] No untracked files that should be committed

## GitHub Issues
- [ ] All completed work has corresponding closed issues
- [ ] Open issues have accurate descriptions
- [ ] Labels are current and meaningful
- [ ] Milestones reflect actual timeline

## Documentation
- [ ] README uses only `make` commands (e.g., `make test`, not `pytest`)
- [ ] Makefile help is comprehensive (`make help`)
- [ ] All scripts in scripts/ are documented
- [ ] Installation instructions are current

## Code Quality
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Tangled code is up to date (`make tangle`)

## Final Steps
- [ ] Run `make clean` to remove temporary files
- [ ] Create summary commit if multiple small changes
- [ ] Push all changes to remote
- [ ] Update project board if applicable
```

## Usage examples

End of session cleanup:
```bash
# Check repository status
git status

# Review and update issues
gh issue list
gh issue close <completed-issues>

# Verify documentation
grep -r "python\|pytest\|uv run" README.org  # Should use make commands instead

# Run quality checks
make lint
make test

# Clean and commit
make clean
git add -A
git commit -m "chore: end of session cleanup"
```

## Common fixes

### Replace direct commands with make targets

Instead of:
```markdown
Run tests with: `uv run pytest tests/`
```

Use:
```markdown
Run tests with: `make test`
```

### Update stale issues

```bash
gh issue edit <number> --body "Updated description..."
gh issue close <number> --comment "Completed in PR #X"
```

### Ensure scripts are executable

```bash
chmod +x scripts/*.sh
git add scripts/
git commit -m "fix: make scripts executable"
```