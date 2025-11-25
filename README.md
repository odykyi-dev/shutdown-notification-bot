# Shutdown Notification Bot ⚡️

A Telegram bot that notifies users about scheduled power outages in Ivano-Frankivsk region (Ukraine). It fetches data from the power company's API, tracks changes, and sends reminders 15 minutes before a scheduled shutdown.

## Features

- 🕒 **Automatic Monitoring**: Checks for schedule updates every 30 minutes.
- 🔔 **Smart Reminders**: Sends a notification 15 minutes before the power goes out.
- 📅 **Schedule Tracking**: Detects changes in the schedule (new outages or cancellations) and notifies immediately.
- 🐳 **Dockerized**: Ready for deployment on Google Cloud Run.
- ☁️ **Cloud Native**: Uses MongoDB Atlas and Google Cloud Logging.

## Prerequisites

- Python 3.11+
- MongoDB (Atlas or local)
- Telegram Bot Token
- Google Cloud Project (for deployment)

## Configuration

Create a `.env` file in the root directory:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_GROUP=your_group_chat_id
ACCOUNT_NUMBER=your_account_number
MONGODB_URI=your_mongodb_connection_string
LOG_LEVEL=INFO
```

## Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the bot**:
   ```bash
   python main.py
   ```

## Deployment

The project is configured for **Google Cloud Run** (Jobs).

1. **GitHub Actions**:
   - The workflow is triggered when you push a tag (e.g., `1.0.0`).
   - It builds the Docker image and pushes it to Google Artifact Registry.
   - It deploys the image as a Cloud Run Job.

2. **Secrets**:
   Ensure the following secrets are set in your GitHub repository:
   - `GCP_PROJECT_ID`
   - `GCP_CREDENTIALS` (JSON service account key)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
