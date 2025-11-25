import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot

# Logic Imports
from logic import (
    calculate_schedule_changes,
    process_schedule_changes,
    process_due_reminders,
    should_check_api,
    cleanup_past_reminders
)
from models import ScheduleRoot, DaySchedule
from database.client import get_db_connection, close_db_connection
from config import settings
from services.power_api import PowerAPIService
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    logger.info(f"CRON Triggered: {datetime.now(ZoneInfo(settings.TIMEZONE))}")

    # Initialize Bot
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    try:
        db = await get_db_connection()
        schedules_collection = db["schedules"]
        reminders_collection = db["reminders"]
        metadata_collection = db["metadata"]

        # --- PHASE 1: NOTIFICATIONS (Runs Every 15 mins) ---
        # Checks DB for reminders that are due NOW
        logger.info("Checking for due reminders...")
        await process_due_reminders(reminders_collection, bot, settings.TELEGRAM_GROUP)

        # --- PHASE 2: API CHECK & SYNC (Runs Every 30 mins) ---
        if await should_check_api(metadata_collection):
            logger.info("30 minutes passed. Fetching API...")

            # Fetch and Parse
            queue_data = PowerAPIService.get_queue_schedule()

            if queue_data:
                schedule_root = ScheduleRoot.model_validate(queue_data)
                queue_id = f"{schedule_root.current.queue}.{schedule_root.current.subQueue}"

                for schedule in schedule_root.schedule:
                    event_date = schedule.eventDate
                    previous_value = await schedules_collection.find_one({"eventDate": event_date})

                    # --- PREPARE DATA ---
                    data_to_save = schedule.model_dump()
                    data_to_save["valid_until"] = datetime.now(ZoneInfo(settings.TIMEZONE)) + timedelta(days=2)

                    # 1. Determine previous state
                    if previous_value:
                        previous_schedule = DaySchedule.model_validate(previous_value)
                    else:
                        previous_schedule = None

                    # 2. Calculate changes
                    changes = calculate_schedule_changes(
                        previous_schedule,
                        schedule,
                        queue_id
                    )

                    # 3. Check for any detected changes
                    has_changes = changes["added"] or changes["removed"]

                    # 4. CONDITIONAL WRITE-BACK LOGIC
                    if previous_schedule is None or has_changes:
                        logger.info(f"Updates detected for {event_date}")

                        # Process Reminders (Deletes old/Inserts new based on 'changes')
                        await process_schedule_changes(
                            changes,
                            reminders_collection,
                            queue_id,
                            bot,
                            settings.TELEGRAM_GROUP,
                            event_date
                        )

                        # Save/Update the Schedule Document itself
                        await schedules_collection.update_one(
                            {"eventDate": event_date},  # Filter
                            {"$set": data_to_save},  # New data
                            upsert=True  # Insert if new
                        )
                    else:
                        logger.info(f"Schedule for {event_date} unchanged.")

                # Update Metadata (Reset the 30 min timer)
                await metadata_collection.update_one(
                    {"_id": "api_status"},
                    {"$set": {"last_api_check": datetime.now(ZoneInfo(settings.TIMEZONE))}},
                    upsert=True
                )
            else:
                logger.warning("WARNING: API returned empty data.")
        else:
            logger.info("API check skipped (Less than 30 mins since last check).")

        # --- PHASE 3: CLEANUP ---
        logger.info("Running cleanup...")
        await cleanup_past_reminders(reminders_collection)

    except Exception as e:
        logger.exception(f"ERROR: An error occurred: {e}")

    finally:
        # Cleanup Resources
        await bot.session.close()
        await close_db_connection()
        logger.info("Script finished.")


if __name__ == "__main__":
    asyncio.run(main())
