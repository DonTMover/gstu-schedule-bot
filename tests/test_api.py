import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from api import get_proxy, merge_schedule_groups


class ScheduleGroupsTests(unittest.TestCase):
    def test_merges_all_groups_without_changing_subgroup_items(self):
        selected = {
            "data": {
                "scheduleItems": [{
                    "dayOfWeek": "MONDAY",
                    "lessonNumber": 1,
                    "startTime": "09:00:00",
                    "endTime": "10:30:00",
                    "startDate": "2026-10-19",
                    "endDate": "2026-12-31",
                    "subject": {"id": 7, "name": "Math"},
                    "lessonType": {"id": 1, "name": "Lecture"},
                    "groups": [{"name": "АП-11"}],
                }]
            }
        }
        full = {
            "data": {
                "scheduleItems": [{
                    **selected["data"]["scheduleItems"][0],
                    "groups": [{"name": "АП-11"}, {"name": "АП-12"}],
                }]
            }
        }

        result = merge_schedule_groups(selected, full)

        self.assertEqual(
            result["data"]["scheduleItems"][0]["groups"],
            [{"name": "АП-11"}, {"name": "АП-12"}],
        )
        self.assertEqual(selected["data"]["scheduleItems"][0]["groups"], [{"name": "АП-11"}])

    def test_empty_proxy_disables_proxy(self):
        with patch.dict(os.environ, {"PROXY": "   "}):
            self.assertIsNone(get_proxy())

    def test_configured_proxy_is_preserved(self):
        with patch.dict(os.environ, {"PROXY": " http://proxy:8080 "}):
            self.assertEqual(get_proxy(), "http://proxy:8080")


if __name__ == "__main__":
    unittest.main()
