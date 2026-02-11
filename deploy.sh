#!/bin/bash

set -e  # Exit on any error

PROJECT_DIR="$HOME/ShutdownNotification"
BRANCH="main"

echo "=== Starting Deployment ==="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: git is not installed!"
    exit 1
fi

# Navigate to project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory $PROJECT_DIR does not exist!"
    exit 1
fi

cd "$PROJECT_DIR"

# Stash any local changes (optional)
echo "Stashing local changes..."
git stash || true

# Pull latest code
echo "Pulling latest changes from $BRANCH..."
git pull origin "$BRANCH"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: Virtual environment not found, creating one..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Restart application
echo "Restarting application..."
# Adjust this based on your setup:

# If using systemd:
if sudo systemctl is-active --quiet your-app.service; then
    sudo systemctl restart your-app.service
    echo "Service restarted successfully"
fi

# If using pm2 or another process manager, add appropriate commands here

echo "=== Deployment Completed Successfully ==="