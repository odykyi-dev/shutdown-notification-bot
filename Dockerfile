FROM --platform=linux/arm/v6 balenalib/rpi-alpine-python:3.11

# Install cron + tzdata (Alpine)
RUN apk add --no-cache \
    dcron \
    tzdata

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
