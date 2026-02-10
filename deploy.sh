#!/bin/bash

# Navigate to the project directory
cd ~/ShutdownNotification || exit

# Pull the latest changes
git pull origin main

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

# Ensure run.sh is executable
chmod +x run.sh

echo "Deployment completed successfully."
