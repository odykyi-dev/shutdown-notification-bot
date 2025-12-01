#!/bin/sh

# Export environment variables for cron
printenv | grep -v "no_proxy" > /etc/environment

# Write cron job
echo "*/15 * * * * . /etc/environment; python3 /app/main.py >> /var/log/cron.log 2>&1" > /etc/crontabs/root

# Set correct permissions
chmod 600 /etc/crontabs/root

# Create log file
touch /var/log/cron.log

echo "Starting crond..."
crond -f -l 2
