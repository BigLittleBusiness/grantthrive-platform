# Development Branch Setup Script for Windows
# This script sets up the initial development branch structure for GrantThrive Platform

Write-Host "Setting up development branch structure for GrantThrive Platform..." -ForegroundColor Green

# Ensure we're on the main branch
git checkout main

# Create and push develop branch
Write-Host "Creating develop branch..." -ForegroundColor Yellow
git checkout -b develop
git push -u origin develop

# Create feature branch template
Write-Host "Creating feature branch template..." -ForegroundColor Yellow
git checkout -b feature/initial-setup
git push -u origin feature/initial-setup

# Create additional feature branches for the initial issues
Write-Host "Creating feature branches for initial development issues..." -ForegroundColor Yellow

# Branch for project setup
git checkout develop
git checkout -b feature/project-setup
git push -u origin feature/project-setup

# Branch for database schema
git checkout develop
git checkout -b feature/database-schema
git push -u origin feature/database-schema

# Branch for authentication system
git checkout develop
git checkout -b feature/user-authentication
git push -u origin feature/user-authentication

# Return to develop branch
git checkout develop

Write-Host "Development branch structure created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Branch structure:" -ForegroundColor Cyan
Write-Host "- main (production-ready code)" -ForegroundColor White
Write-Host "- develop (integration branch)" -ForegroundColor White
Write-Host "- feature/initial-setup (template branch)" -ForegroundColor White
Write-Host "- feature/project-setup (Issue #1)" -ForegroundColor White
Write-Host "- feature/database-schema (Issue #2)" -ForegroundColor White
Write-Host "- feature/user-authentication (Issue #3)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure branch protection rules for 'develop' branch" -ForegroundColor White
Write-Host "2. Set up repository secrets as documented in .github/SECRETS.md" -ForegroundColor White
Write-Host "3. Begin development on feature branches" -ForegroundColor White 