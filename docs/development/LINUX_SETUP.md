# Linux Setup

1. **Install Python 3.12+**: Use your distribution's package manager.
2. **Install Node.js**: Required for formatting and linting JavaScript/CSS.
3. **Open a terminal** in the project directory.
4. **Run the setup script**:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```
   This will create a virtual environment, install Python dependencies, install npm dependencies, and set up pre-commit hooks.
5. **Activate environment & Start developing**:
   ```bash
   source .venv/bin/activate
   python manage.py runserver
   ```
