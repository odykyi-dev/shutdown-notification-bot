import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from logic import calculate_schedule_changes
from models import DaySchedule


class TestLogic(unittest.TestCase):
    def setUp(self):
        self.tz = ZoneInfo("Europe/Kyiv")
        self.queue_id = "4.2"

    def test_calculate_schedule_changes_no_change(self):
        schedule_data = {
            "eventDate": "25.11.2025",
            "queues": {
                "4.2": [{"shutdownHours": "16:30-20:00", "from": "16:30", "to": "20:00", "status": 1}]
            },
            "createdAt": "24.11.2025 19:52",
            "scheduleApprovedSince": "24.11.2025 19:52"
        }
        schedule = DaySchedule.model_validate(schedule_data)
        
        changes = calculate_schedule_changes(schedule, schedule, self.queue_id)
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["removed"]), 0)

    def test_calculate_schedule_changes_new_outage(self):
        old_data = {
            "eventDate": "25.11.2025",
            "queues": {"4.2": []},
            "createdAt": "...", "scheduleApprovedSince": "..."
        }
        new_data = {
            "eventDate": "25.11.2025",
            "queues": {
                "4.2": [{"shutdownHours": "16:30-20:00", "from": "16:30", "to": "20:00", "status": 1}]
            },
            "createdAt": "...", "scheduleApprovedSince": "..."
        }
        
        old_schedule = DaySchedule.model_validate(old_data)
        new_schedule = DaySchedule.model_validate(new_data)
        
        changes = calculate_schedule_changes(old_schedule, new_schedule, self.queue_id)
        self.assertEqual(len(changes["added"]), 1)
        self.assertEqual(len(changes["removed"]), 0)

if __name__ == '__main__':
    unittest.main()
