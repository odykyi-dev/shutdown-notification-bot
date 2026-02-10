from datetime import timedelta, datetime, timezone
from typing import List, Tuple, Dict, Set, Optional
from zoneinfo import ZoneInfo
from aiogram import Bot
from models import DaySchedule, Reminder
from services.telegram import send_group_message
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

OutageTuple = Tuple[datetime, datetime]
tzinfo = ZoneInfo(settings.TIMEZONE)


def calculate_schedule_changes(
    old_schedule: DaySchedule | None, new_schedule: DaySchedule, queue_id: str
) -> Dict[str, List[OutageTuple]]:
    """
    Compares old and new schedules to find what exactly changed.
    Returns a dict with 'added' and 'removed' lists.
    """
    old_set: Set[OutageTuple] = set()
    if old_schedule:
        for item in old_schedule.get_outages_for_queue(queue_id, tzinfo):
            old_set.add((item["start"], item["end"]))

    new_set: Set[OutageTuple] = set()
    for item in new_schedule.get_outages_for_queue(queue_id, tzinfo):
        new_set.add((item["start"], item["end"]))

    # Items in New but not in Old
    added_outages = list(new_set - old_set)

    # Items in Old but not in New
    removed_outages = list(old_set - new_set)

    return {"added": added_outages, "removed": removed_outages}


def generate_reminders_from_schedule(
    schedule: DaySchedule, queue_id: str, chat_id: str
) -> List[Reminder]:
    """
    Converts a DaySchedule into a list of specific Reminders.
    """
    new_reminders = []

    outages = schedule.get_outages_for_queue(queue_id, tzinfo)

    for outage in outages:
        start_time = outage["start"]
        end_time = outage["end"]

        notify_time = start_time - timedelta(minutes=15)
        alert = Reminder(
            chat_id=chat_id,
            queue_id=queue_id,
            notify_at=notify_time,
            outage_start=start_time,
            outage_end=end_time,
            sent=False,
        )

        new_reminders.append(alert)

    return new_reminders


def generate_notification_message(
    changes: Dict[str, List[OutageTuple]],
    schedule: DaySchedule,
    queue_id: str,
    event_date: str,
) -> Optional[str]:
    """
    Generates the notification message for schedule changes.
    """
    notifications = []

    # Sort outages by start time
    removed_sorted = sorted(changes["removed"], key=lambda x: x[0])
    added_sorted = sorted(changes["added"], key=lambda x: x[0])

    # 1. Cancellations
    for start_time, end_time in removed_sorted:
        notifications.append(
            f"✅ <b>CANCELLATION:</b> Outage at "
            f"<b>{start_time.strftime('%H:%M')}</b> has been REMOVED."
        )

    # 2. New Outages
    for start_time, end_time in added_sorted:
        duration = end_time - start_time
        hours, remainder = divmod(duration.seconds, 3600)
        minutes = remainder // 60
        duration_str = f"{hours}h {minutes}m" if minutes else f"{hours}h"

        notifications.append(
            f"⚠️ <b>NEW OUTAGE:</b> Off from <b>{start_time.strftime('%H:%M')}</b> to "
            f"<b>{end_time.strftime('%H:%M')}</b> ({duration_str})."
        )

    if not notifications:
        return None

    # 3. Total Daily Duration
    total_duration = timedelta()
    daily_outages = schedule.get_outages_for_queue(queue_id, tzinfo)
    for item in daily_outages:
        # Check against removed to avoid double counting if schedule object isn't fully updated yet?
        # The schedule passed in IS the new schedule, so it should be correct.
        total_duration += item["end"] - item["start"]

    total_hours, total_remainder = divmod(total_duration.seconds, 3600)
    total_minutes = total_remainder // 60
    total_str = (
        f"{total_hours}h {total_minutes}m" if total_minutes else f"{total_hours}h"
    )

    header = f"⚡ <b>SCHEDULE UPDATE</b> for Queue {queue_id} on <b>{event_date}</b>:\n\n"
    footer = f"\n\n<b>Total Outage Duration: {total_str}</b>"
    
    return header + "\n".join(notifications) + footer


async def process_schedule_changes(
    changes: dict,
    reminders_collection,
    queue_id: str,
    bot: Bot,
    chat_id: str,
    event_date: str,
    schedule: DaySchedule,
):
    """
    Executes the database I/O based on the calculated schedule differences.
    """
    # 1. DB Cleanup for removed outages
    for start_time, end_time in changes["removed"]:
        logger.info(f"Deleting reminder for cancelled outage at: {start_time}")
        await reminders_collection.delete_many(
            {"chat_id": chat_id, "queue_id": queue_id, "outage_start": start_time}
        )

    # 2. DB Insert for new outages
    for start_time, end_time in changes["added"]:
        logger.info(f"Adding new reminder for outage at: {start_time}")

        notify_time = start_time - timedelta(minutes=15)
        new_alert = Reminder(
            chat_id=chat_id,
            queue_id=queue_id,
            notify_at=notify_time,
            outage_start=start_time,
            outage_end=end_time,
        )

        await reminders_collection.update_one(
            {"chat_id": chat_id, "outage_start": start_time},
            {"$set": new_alert.model_dump()},
            upsert=True,
        )

    # 3. Generate and Send Notification
    message = generate_notification_message(changes, schedule, queue_id, event_date)
    if message:
        await send_group_message(chat_id, message, bot)


async def process_due_reminders(reminders_col, bot: Bot, group_id: str):
    """
    Checks for reminders that are due NOW (or slightly in the past) and not sent.
    """
    now = datetime.now(timezone.utc)
    # We look back 20 minutes just in case the Cron was slightly delayed
    time_window = now - timedelta(minutes=20)

    cursor = reminders_col.find(
        {"sent": False, "notify_at": {"$lte": now, "$gte": time_window}}
    )

    count = 0
    async for reminder in cursor:
        # convert to correct TZ from UTC
        start_time = (
            reminder["outage_start"].replace(tzinfo=timezone.utc).astimezone(tzinfo)
        )
        end_time = (
            reminder["outage_end"].replace(tzinfo=timezone.utc).astimezone(tzinfo)
        )

        msg = (
            f"⚠️ <b>REMINDER:</b> Power outage starts in <b>15 minutes</b>!\n"
            f"🕒 <b>Time: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}</b>"
        )

        await send_group_message(group_id, msg, bot)

        # Mark as sent
        await reminders_col.update_one(
            {"_id": reminder["_id"]}, {"$set": {"sent": True}}
        )
        count += 1

    if count > 0:
        logger.info(f"Sent {count} due reminders.")


async def should_check_api(metadata_col) -> bool:
    """
    Returns True if 30 minutes have passed since the last API check. 
    """
    doc = await metadata_col.find_one({"_id": "api_status"})

    if not doc:
        return True

    last_check = doc["last_api_check"].replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - last_check
    # here is diff for 25 mins because can be twice skip for API
    return diff > timedelta(minutes=25)


async def cleanup_past_reminders(reminders_collection):
    """
    Deletes reminders where the 'notify_at' time is older than 2 hours.
    This keeps the database size small and efficient.
    """
    threshold_time = datetime.now(tzinfo) - timedelta(hours=2)
    try:
        result = await reminders_collection.delete_many(
            {"notify_at": {"$lt": threshold_time}}
        )
        if result.deleted_count > 0:
            logger.info(
                f"Cleanup: Removed {result.deleted_count} old reminders from DB."
            )
    except Exception as e:
        logger.error(f"ERROR: during cleanup: {e}")
