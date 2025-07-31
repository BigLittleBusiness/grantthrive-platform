# Branch Protection Configuration

This document outlines the branch protection rules that should be configured for the `develop` branch to ensure code quality and proper review processes.

## Branch Protection Rules for `develop`

### Required Status Checks
- **Require status checks to pass before merging**
  - `ci-cd` (from CI/CD workflow)
  - `code-quality` (from quality checks workflow)

### Required Pull Request Reviews
- **Require a pull request before merging**
- **Require approvals**: 1 (minimum)
- **Dismiss stale PR approvals when new commits are pushed**
- **Require review from code owners** (if code owners are configured)

### Restrictions
- **Restrict pushes that create files that cannot be deleted**
- **Require linear history** (optional, for cleaner git history)
- **Require deployments to succeed before merging** (if deployment workflows are configured)

### Additional Settings
- **Allow force pushes**: Disabled
- **Allow deletions**: Disabled
- **Require conversation resolution before merging**: Enabled

## Configuration Steps

1. **Navigate to Repository Settings**
   - Go to your GitHub repository
   - Click on "Settings" tab
   - Select "Branches" from the left sidebar

2. **Add Branch Protection Rule**
   - Click "Add rule" or "Add branch protection rule"
   - In "Branch name pattern", enter: `develop`

3. **Configure Protection Settings**
   - Check "Require a pull request before merging"
   - Check "Require approvals" and set to 1
   - Check "Dismiss stale PR approvals when new commits are pushed"
   - Check "Require status checks to pass before merging"
   - Add the required status checks: `ci-cd`, `code-quality`
   - Check "Require branches to be up to date before merging"

4. **Save the Rule**
   - Click "Create" or "Save changes"

## Code Owners Configuration (Optional)

Create `.github/CODEOWNERS` file to automatically request reviews from specific team members:

```markdown
# Global code owners
* @project-admin

# Frontend specific
/frontend/ @frontend-team

# Backend specific
/backend/ @backend-team

# Documentation
/docs/ @docs-team
```

## Workflow Integration

The branch protection rules work with the CI/CD workflows defined in `.github/workflows/`:

- **ci-cd.yml**: Main build and test workflow
- **code-quality.yml**: Code quality checks (ESLint, Flake8, etc.)
- **deploy-staging.yml**: Staging deployment workflow

## Benefits

1. **Code Quality**: Ensures all code passes tests and quality checks
2. **Review Process**: Enforces pull request reviews
3. **History Integrity**: Prevents direct pushes to protected branches
4. **Deployment Safety**: Ensures deployments succeed before merging
5. **Team Collaboration**: Encourages proper code review practices

## Troubleshooting

### Common Issues
- **Status checks not appearing**: Ensure workflows are properly configured and running
- **Approvals not counting**: Check that reviewers are not the same as the PR author
- **Branch protection blocking merges**: Verify all requirements are met before merging

### Override (Emergency Situations)
In emergency situations, repository administrators can:
1. Temporarily disable branch protection
2. Merge the required changes
3. Re-enable branch protection immediately

**Note**: This should only be used in true emergencies and should be documented. 