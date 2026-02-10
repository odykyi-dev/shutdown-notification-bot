cat run.sh
#!/bin/bash

# --- CONFIGURATION ---
PROJECT_DIR="~/ShutdownNotification"
# ---------------------

# 1. Navigate to the project root directory
cd "$PROJECT_DIR" || { echo "Error: Cannot CD to $PROJECT_DIR"; exit 1; }

# 2. Load all environment variables from the .env file
# 'set -a' exports all sourced variables to the environment.
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "CRITICAL ERROR: .env file not found in $PROJECT_DIR"
    exit 1
fi

# 3. CRITICAL: Add the 'src' directory to Python's path
# This allows Python to resolve internal imports (e.g., from src.services import X)
export PYTHONPATH=$PYTHONPATH:$PROJECT_DIR/src

# 4. Execute python using the interpreter inside the virtual environment
# Output is appended to cron.log for monitoring
./venv/bin/python src/main.py >> cron.log 2>&1