# Contributing to vTOC

Thank you for your interest in contributing to vTOC! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a positive environment
- Follow project standards and conventions

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR-USERNAME/vTOC.git
cd vTOC
```

### 2. Set Up Development Environment

```bash
# Copy environment file
cp .env.example .env

# Start development services
docker-compose up -d

# Or for local development
make dev-backend  # Terminal 1
make dev-frontend # Terminal 2
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 4. Keep your branch active

We automatically clean up long-lived feature branches to keep the repository tidy. A scheduled workflow runs every day at 03:00 UTC and deletes branches that:

- Have not received any commits in the last 30 days (the default retention window).
- Are not protected (e.g., `main`, `live`, or `release/*` branches).
- Do not opt out of cleanup.

The retention window and protected branch list can be tuned when running the workflow manually via **Actions → "Cleanup stale branches" → Run workflow**. The scheduled run uses the defaults above.

#### Opt out of automated cleanup

If you need to keep a branch around longer, you have two options:

1. **Use an opt-out prefix.** Branches whose names start with `keep/` or `keep-` are skipped by the cleanup job.
2. **Run the workflow manually** with a longer retention period while your branch remains active.

Please remove the `keep/` or `keep-` prefix once the branch is ready to be cleaned up, so the automation can resume managing it.

## Development Guidelines

### Backend (Python/FastAPI)

**Structure:**
```
backend/
├── app/
│   ├── routers/      # API endpoints
│   ├── models.py     # Database models
│   ├── database.py   # Database configuration
│   └── main.py       # Application entry point
└── tests/            # Test files
```

**Standards:**
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for functions
- Add unit tests for new features
- Use async/await for I/O operations

**Example:**
```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/items/", response_model=List[Item])
async def list_items() -> List[Item]:
    """List all items.
    
    Returns:
        List[Item]: List of all items
    """
    # Implementation
    pass
```

### Frontend (React)

**Structure:**
```
frontend/
├── src/
│   ├── components/   # Reusable components
│   ├── pages/        # Page components
│   ├── services/     # API services
│   └── App.js        # Main app component
└── public/           # Static assets
```

**Standards:**
- Use functional components with hooks
- Follow React best practices
- Use meaningful component names
- Keep components focused and reusable
- Add PropTypes or TypeScript

**Example:**
```javascript
import React, { useState, useEffect } from 'react';

function MyComponent({ data }) {
  const [items, setItems] = useState([]);

  useEffect(() => {
    // Fetch data
  }, []);

  return (
    <div className="my-component">
      {/* Component content */}
    </div>
  );
}

export default MyComponent;
```

### Database Changes

**Migrations:**
```bash
# Create migration
docker-compose exec backend alembic revision -m "Description"

# Apply migration
docker-compose exec backend alembic upgrade head
```

**Guidelines:**
- Always create migrations for schema changes
- Test migrations both up and down
- Document breaking changes

### Automation Agents

**Structure:**
```
agents/
├── modules/          # Agent implementations
├── config/           # Configuration files
└── agent_service.py  # Main service
```

**Guidelines:**
- Create focused, single-purpose agents
- Use proper logging
- Handle errors gracefully
- Document configuration options

## Testing

### Backend Tests

```bash
# Run all tests
make test-backend

# Run specific test
docker-compose exec backend pytest tests/test_operations.py

# With coverage
docker-compose exec backend pytest --cov=app
```

### Frontend Tests

```bash
# Run all tests
make test-frontend

# Run in watch mode
cd frontend && npm test
```

### Integration Tests

Test the full stack:
```bash
# Start services
docker-compose up -d

# Test API
curl http://localhost/api/health

# Test frontend
curl -I http://localhost
```

## Documentation

### Code Documentation

- Add docstrings to Python functions
- Add JSDoc comments to JavaScript functions
- Document complex logic
- Update API documentation when changing endpoints

### User Documentation

Update relevant documentation files:
- `README.md` - Main documentation
- `docs/API.md` - API changes
- `docs/ARCHITECTURE.md` - Architecture changes
- `docs/QUICKSTART.md` - Setup instructions

## Pull Request Process

### 1. Ensure Quality

Before submitting:
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No console errors or warnings
- [ ] Commits are meaningful

### 2. Create Pull Request

**Title Format:**
```
[Type] Brief description

Types: Feature, Fix, Docs, Refactor, Test, Chore
```

**Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How to test the changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] Self-review completed
```

### 3. Review Process

- Address review comments
- Keep discussion professional
- Update PR based on feedback
- Squash commits if needed

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```
feat(backend): Add asset tracking endpoint

Implement new endpoint for tracking asset locations
in real-time using WebSocket connections.

Closes #123
```

```
fix(frontend): Resolve navigation menu rendering issue

The menu was not displaying correctly on mobile devices.
Updated CSS media queries to fix responsive behavior.
```

## Project Structure

```
vTOC/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── agents/           # Automation agents
├── database/         # Database scripts
├── infrastructure/   # IaC (Terraform/Ansible)
├── n8n/              # Workflow configurations
├── traefik/          # Reverse proxy config
├── docs/             # Documentation
└── docker-compose.yml
```

## Useful Commands

```bash
# Start development
make up

# View logs
make logs

# Restart services
make restart

# Run tests
make test-backend
make test-frontend

# Security scan
make security-scan

# Database backup
make backup-db

# Clean up
make clean
```

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating a Release

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create git tag
4. Push tag to trigger CI/CD
5. Create GitHub release

```bash
# Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions
- **Discussions**: General questions and ideas

### Reporting Issues

**Bug Report Template:**
```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Docker version: [e.g., 24.0.0]
- Browser: [e.g., Chrome 120]

## Logs
Relevant error messages or logs
```

**Feature Request Template:**
```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've thought about
```

## Questions?

If you have questions:
1. Check existing documentation
2. Search closed issues
3. Ask in GitHub Discussions
4. Create a new issue

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for contributing to vTOC! 🚀
