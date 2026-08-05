# Development Environment

The development environment for SITADC Youth Hub uses modern Python and Frontend tools to maintain high quality.

## Core Tools
- **Ruff**: Python linter (fast, replaces flake8 and others)
- **Black**: Python formatter
- **isort**: Import sorter
- **mypy**: Static type checker
- **djLint**: Django template linter and formatter
- **pytest**: Test runner
- **Prettier**: Frontend (JS/CSS) formatter
- **ESLint**: JavaScript linter
- **Stylelint**: CSS linter

## Prerequisites
- Python 3.12+
- Node.js (for frontend tools)
- Git

## Setup
We provide helper scripts to setup the environment:
- Windows: `.venv\Scripts\Activate.ps1` followed by `scripts\setup.ps1`
- Linux/macOS: `source .venv/bin/activate` followed by `scripts/setup.sh`

See `WINDOWS_SETUP.md`, `LINUX_SETUP.md`, and `MACOS_SETUP.md` for specific instructions.
