# Contributing to AI Native Books Interaction

Thank you for your interest in contributing! This document provides guidelines and instructions for developers.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Common Tasks](#common-tasks)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Google API key (for Gemini 2.0 Flash)
- Code editor (VS Code recommended)

### First Time Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/panaversity/ai-native-books-interaction.git
   cd ai-native-books-interaction
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file in api/ directory
   copy .env.example .env  # Windows
   # or
   cp .env.example .env  # Linux/Mac
   ```

   Then edit `.env` and add your credentials:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   LOG_LEVEL=INFO
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

5. **Run the development server**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify installation**
   - Open http://localhost:8000/docs for API documentation
   - Check health endpoint: http://localhost:8000/health

## Development Setup

### Recommended VS Code Extensions

- Python
- Pylance
- Python Debugger
- Ruff (linter and formatter)
- REST Client or Thunder Client
- GitLens

### Development Dependencies

For development, install additional tools:
```bash
pip install ruff pytest pytest-asyncio black isort mypy
```

## Project Structure

```
ai-native-books-interaction/
├── api/                          # Backend API service
│   ├── src/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models for request/response
│   │   ├── routers/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── summarize.py     # Summarization endpoints
│   │   │   └── personalize.py   # Personalization endpoints
│   │   └── services/
│   │       └── openai_agent.py  # OpenAI Agents SDK integration
│   ├── tests/                   # Test files
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment template
│   └── README.md               # API documentation
├── .gitignore
├── README.md                    # Project overview
└── CONTRIBUTING.md             # This file
```

### Key Files

- **`main.py`**: FastAPI app initialization, middleware, router registration
- **`schemas.py`**: Data models for API requests and responses
- **`routers/`**: API endpoint definitions organized by feature
- **`services/`**: Business logic and external service integrations
- **`openai_agent.py`**: AI agent configuration and streaming logic

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 100 characters max
- **Imports**: Use absolute imports, organize with `isort`
- **Type hints**: Use type annotations for function parameters and returns
- **Docstrings**: Use Google-style docstrings for all public functions

### Example Code Style

```python
"""
Module-level docstring describing the file's purpose
"""
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MyModel(BaseModel):
    """Model representing XYZ."""
    
    name: str
    age: Optional[int] = None


async def process_data(
    content: str,
    max_length: int = 500
) -> AsyncGenerator[str, None]:
    """
    Process data and yield results.
    
    Args:
        content: The input content to process
        max_length: Maximum length of output (default: 500)
        
    Yields:
        Processed data chunks
        
    Raises:
        ValueError: If content is empty
    """
    if not content:
        raise ValueError("Content cannot be empty")
    
    # Implementation here
    yield "result"
```

### Code Formatting

Before committing, format your code:

```bash
# Format with black
black src/

# Sort imports
isort src/

# Lint with ruff
ruff check src/
```

### Type Checking

Run type checks with mypy:
```bash
mypy src/ --strict
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_summarize.py

# Run with verbose output
pytest -v
```

### Writing Tests

Place tests in the `tests/` directory with `test_` prefix:

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await some_async_function()
    assert result is not None
```

## Pull Request Process

### Branch Naming

- Feature: `feature/description-here`
- Bug fix: `bugfix/description-here`
- Hotfix: `hotfix/description-here`
- Documentation: `docs/description-here`

### Commit Messages

Follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

Example:
```
feat(summarize): add support for custom summary length

- Added max_words parameter to summarization endpoint
- Updated OpenAI agent to respect length limits
- Added validation for parameter ranges

Closes #123
```

### PR Checklist

Before submitting a PR:

- [ ] Code follows the style guide
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with development
- [ ] No merge conflicts
- [ ] Environment variables documented

### Review Process

1. Create PR against `development` branch
2. Fill out PR template
3. Wait for automated checks
4. Address review comments
5. Get approval from maintainer
6. Squash and merge

## Common Tasks

### Adding a New API Endpoint

1. **Define schema** in `models/schemas.py`:
   ```python
   class MyRequest(BaseModel):
       field: str
   ```

2. **Create router** in `routers/my_feature.py`:
   ```python
   from fastapi import APIRouter
   router = APIRouter()
   
   @router.post("/my-endpoint")
   async def my_endpoint(request: MyRequest):
       return {"result": "success"}
   ```

3. **Register router** in `main.py`:
   ```python
   from src.routers import my_feature
   app.include_router(my_feature.router, prefix="/api/v1", tags=["my-feature"])
   ```

4. **Add tests** in `tests/test_my_feature.py`

### Adding a New Service

1. Create file in `services/` directory
2. Implement service class or functions
3. Add type hints and docstrings
4. Import in router
5. Write unit tests

### Updating Dependencies

1. Edit `requirements.txt`
2. Test compatibility
3. Update documentation
4. Create PR with changes

### Working with Streaming Responses

Example SSE endpoint:
```python
from fastapi.responses import StreamingResponse
import json

@router.get("/stream")
async def stream_data():
    async def event_stream():
        for i in range(10):
            data = json.dumps({"count": i})
            yield f"data: {data}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

### Debugging

1. **Use logging**:
   ```python
   logger.debug(f"Processing {len(items)} items")
   logger.error(f"Error occurred: {str(e)}")
   ```

2. **Set log level** in `.env`:
   ```env
   LOG_LEVEL=DEBUG
   ```

3. **Use VS Code debugger**: Add breakpoints and run in debug mode

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions in GitHub Discussions
- Check existing issues and PRs before creating new ones
- Review API documentation at `/docs` endpoint

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's coding standards

Thank you for contributing! 🚀
