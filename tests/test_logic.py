import unittest
from zoneinfo import ZoneInfo
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from logic import calculate_schedule_changes, generate_notification_message
from models import DaySchedule


class TestLogic(unittest.TestCase):
    def setUp(self):
        self.tz = ZoneInfo("Europe/Kyiv")
        self.queue_id = "4.2"

    def test_calculate_schedule_changes_no_change(self):
        schedule_data = {
            "eventDate": "25.11.2025",
            "queues": {
                "4.2": [
                    {
                        "shutdownHours": "16:30-20:00",
                        "from": "16:30",
                        "to": "20:00",
                        "status": 1,
                    }
                ]
            },
            "createdAt": "24.11.2025 19:52",
            "scheduleApprovedSince": "24.11.2025 19:52",
        }
        schedule = DaySchedule.model_validate(schedule_data)

        changes = calculate_schedule_changes(schedule, schedule, self.queue_id)
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["removed"]), 0)

    def test_calculate_schedule_changes_new_outage(self):
        old_data = {
            "eventDate": "25.11.2025",
            "queues": {"4.2": []},
            "createdAt": "...",
            "scheduleApprovedSince": "...",
        }
        new_data = {
            "eventDate": "25.11.2025",
            "queues": {
                "4.2": [
                    {
                        "shutdownHours": "16:30-20:00",
                        "from": "16:30",
                        "to": "20:00",
                        "status": 1,
                    }
                ]
            },
            "createdAt": "...",
            "scheduleApprovedSince": "...",
        }

        old_schedule = DaySchedule.model_validate(old_data)
        new_schedule = DaySchedule.model_validate(new_data)

        changes = calculate_schedule_changes(old_schedule, new_schedule, self.queue_id)
        self.assertEqual(len(changes["added"]), 1)
        self.assertEqual(len(changes["removed"]), 0)

    def test_generate_notification_message(self):
        # Create a schedule with multiple outages
        schedule_data = {
            "eventDate": "10.02.2026",
            "queues": {
                "6.2": [
                    {"shutdownHours": "...", "from": "14:00", "to": "20:00", "status": 1},
                    {"shutdownHours": "...", "from": "01:30", "to": "05:30", "status": 1},
                    {"shutdownHours": "...", "from": "22:00", "to": "00:00", "status": 1},
                    {"shutdownHours": "...", "from": "07:30", "to": "11:30", "status": 1},
                ]
            },
            "createdAt": "...",
            "scheduleApprovedSince": "...",
        }
        schedule = DaySchedule.model_validate(schedule_data)
        queue_id = "6.2"

        # Simulate that all of these are NEW outages
        outages = schedule.get_outages_for_queue(queue_id, self.tz)
        changes = {
            "added": [(o["start"], o["end"]) for o in outages],
            "removed": []
        }

        # Generate message
        message = generate_notification_message(changes, schedule, queue_id, "10.02.2026")

        self.assertIsNotNone(message)
        
        # Verify Sorting (indirectly via string order)
        # Expected order: 01:30, 07:30, 14:00, 22:00
        pos_1 = message.find("01:30")
        pos_2 = message.find("07:30")
        pos_3 = message.find("14:00")
        pos_4 = message.find("22:00")

        self.assertTrue(pos_1 < pos_2 < pos_3 < pos_4, "Outages are not sorted correctly")

        # Verify Duration Formatting
        self.assertIn("(4h)", message) # for 01:30-05:30 and 07:30-11:30
        self.assertIn("(6h)", message) # for 14:00-20:00
        self.assertIn("(2h)", message) # for 22:00-00:00

        # Verify Total Duration
        # Total = 4 + 4 + 6 + 2 = 16h
        self.assertIn("Total Outage Duration: 16h", message)


if __name__ == "__main__":
    unittest.main()
