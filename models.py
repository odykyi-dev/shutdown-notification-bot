from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict
from datetime import datetime


class ShutdownSlot(BaseModel):
    shutdownHours: str
    start_time: str = Field(alias="from")
    end_time: str = Field(alias="to")
    status: int

    model_config = ConfigDict(
        populate_by_name=True,
        extra='ignore'
    )


class DaySchedule(BaseModel):
    eventDate: str
    scheduleApprovedSince: str
    queues: Dict[str, List[ShutdownSlot]]

    def get_outages_for_queue(self, queue_id: str, tzinfo: ZoneInfo) -> List[Dict]:
        """
        Parses the raw time strings into timezone-aware datetime objects
        for a specific queue.
        """
        outages = []
        if queue_id not in self.queues:
            return outages

        for slot in self.queues[queue_id]:
            # Use strptime to convert to a naive datetime object
            start_dt = datetime.strptime(f"{self.eventDate} {slot.start_time}", "%d.%m.%Y %H:%M").replace(tzinfo=tzinfo)

            # We don't need the end_dt for the reminder calculation, but we'll include it for completeness.
            end_dt = datetime.strptime(f"{self.eventDate} {slot.end_time}", "%d.%m.%Y %H:%M").replace(tzinfo=tzinfo)

            outages.append({
                "start": start_dt,
                "end": end_dt,
                "raw_hours": slot.shutdownHours
            })
        return outages


class CurrentStatus(BaseModel):
    queue: int
    subQueue: int


class ScheduleRoot(BaseModel):
    schedule: List[DaySchedule]
    current: CurrentStatus


class Reminder(BaseModel):
    chat_id: str
    queue_id: str
    notify_at: datetime
    outage_start: datetime
    outage_end: datetime
    sent: bool = False
    created_at: datetime = datetime.now()


class BotMetadata(BaseModel):
    last_api_check: datetime
    updated_at: datetime = datetime.now()
