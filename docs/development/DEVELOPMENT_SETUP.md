# Development Setup Guide

This guide provides step-by-step instructions for setting up the GrantThrive Platform development environment.

## Prerequisites

Before starting, ensure you have the following installed:
- **Git** (latest version)
- **Node.js** (18+)
- **Python** (3.9+)
- **PostgreSQL** (13+)
- **Docker** (optional, for containerized development)

## Initial Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/grantthrive-platform.git
cd grantthrive-platform

# Run the branch setup script
# For Windows:
./scripts/setup/setup-branches.ps1
# For Unix/Linux:
./scripts/setup/setup-branches.sh
```

### 2. Configure Repository Secrets

1. Go to your GitHub repository
2. Navigate to **Settings > Secrets and variables > Actions**
3. Add the required secrets as documented in `.github/SECRETS.md`

### 3. Set Up Branch Protection

1. Go to **Settings > Branches**
2. Add branch protection rule for `develop` branch
3. Configure as outlined in `.github/BRANCH_PROTECTION.md`

## Development Workflow

### Starting Development

1. **Checkout the develop branch**:
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes and commit**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

4. **Push and create pull request**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

### Code Quality Checks

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run manually (optional)
pre-commit run --all-files
```

## Project Structure

```
grantthrive-platform/
├── frontend/                 # React TypeScript application
│   ├── src/
│   ├── public/
│   ├── tests/
│   └── package.json
├── backend/                  # Python FastAPI application
│   ├── src/
│   ├── tests/
│   ├── config/
│   └── requirements.txt
├── database/                 # Database migrations and seeds
│   ├── migrations/
│   ├── seeds/
│   └── schemas/
├── docs/                     # Documentation
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   └── user-guides/
├── scripts/                  # Development and deployment scripts
│   ├── setup/
│   ├── deployment/
│   └── maintenance/
└── .github/                  # GitHub configuration
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

## Development Issues

The initial development backlog includes three high-priority issues:

### Issue #1: Project Setup and Configuration
- **Branch**: `feature/project-setup`
- **Estimated Effort**: 7-11 hours
- **Dependencies**: None (foundational)

### Issue #2: Database Schema Design
- **Branch**: `feature/database-schema`
- **Estimated Effort**: 8-13 hours
- **Dependencies**: Issue #1

### Issue #3: User Authentication System
- **Branch**: `feature/user-authentication`
- **Estimated Effort**: 14-20 hours
- **Dependencies**: Issues #1 and #2

## Local Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Database Setup

```bash
# Create database
createdb grantthrive_dev

# Run migrations (when available)
cd backend
alembic upgrade head

# Seed data (when available)
python scripts/seed_data.py
```

## Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd backend
pytest
```

### End-to-End Tests
```bash
npm run test:e2e  # When configured
```

## Deployment

### Staging Deployment
- Automatic deployment on push to `develop` branch
- Available at: [staging URL]

### Production Deployment
- Manual deployment from `main` branch
- Available at: [production URL]

## Troubleshooting

### Common Issues

1. **Pre-commit hooks failing**:
   - Run `pre-commit run --all-files` to see specific errors
   - Fix code quality issues before committing

2. **Database connection issues**:
   - Verify PostgreSQL is running
   - Check database URL in environment variables
   - Ensure database exists and is accessible

3. **Frontend build issues**:
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check for TypeScript errors: `npm run type-check`

4. **Backend import errors**:
   - Activate virtual environment
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python path and imports

### Getting Help

- Check existing issues in the repository
- Review documentation in `/docs/`
- Contact the development team
- Create a new issue with detailed information

## Contributing

1. Follow the established branch naming convention
2. Use conventional commit messages
3. Ensure all tests pass before submitting PR
4. Update documentation as needed
5. Follow the code style guidelines

## Next Steps

After completing the initial setup:

1. **Begin with Issue #1**: Project Setup and Configuration
2. **Set up local development environment**
3. **Configure IDE/editor for the project**
4. **Familiarize yourself with the codebase structure**
5. **Start development on assigned issues** 