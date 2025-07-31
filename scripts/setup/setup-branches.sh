#!/bin/bash

# Development Branch Setup Script
# This script sets up the initial development branch structure for GrantThrive Platform

echo "Setting up development branch structure for GrantThrive Platform..."

# Ensure we're on the main branch
git checkout main

# Create and push develop branch
echo "Creating develop branch..."
git checkout -b develop
git push -u origin develop

# Create feature branch template
echo "Creating feature branch template..."
git checkout -b feature/initial-setup
git push -u origin feature/initial-setup

# Create additional feature branches for the initial issues
echo "Creating feature branches for initial development issues..."

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

echo "Development branch structure created successfully!"
echo ""
echo "Branch structure:"
echo "- main (production-ready code)"
echo "- develop (integration branch)"
echo "- feature/initial-setup (template branch)"
echo "- feature/project-setup (Issue #1)"
echo "- feature/database-schema (Issue #2)"
echo "- feature/user-authentication (Issue #3)"
echo ""
echo "Next steps:"
echo "1. Configure branch protection rules for 'develop' branch"
echo "2. Set up repository secrets as documented in .github/SECRETS.md"
echo "3. Begin development on feature branches" 