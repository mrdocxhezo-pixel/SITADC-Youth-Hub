# Windows Setup

1. **Install Python 3.12+**: Download from python.org. Make sure to check "Add Python to PATH".
2. **Install Node.js**: Required for formatting and linting JavaScript/CSS.
3. **Open PowerShell** in the project directory.
4. **Run the setup script**:
   ```powershell
   .\scripts\setup.ps1
   ```
   This will create a virtual environment, activate it, install Python dependencies, install npm dependencies, and set up pre-commit hooks.
5. **Start developing**:
   ```powershell
   python manage.py runserver
   ```
