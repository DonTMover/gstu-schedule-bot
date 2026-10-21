import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from utils import format_minimal_schedule


class MinimalInterfaceTests(unittest.TestCase):
    def test_formats_compact_lesson(self):
        result = format_minimal_schedule(
            [{"startTime": "09:00:00", "endTime": "10:30:00",
              "subject": "Математика", "classrooms": "101", "groups": "АП-11, АП-12"}],
            "Понедельник", "19.10.2026", "ODD",
        )
        self.assertIn("09:00–10:30", result)
        self.assertIn("Математика", result)
        self.assertIn("АП-11, АП-12", result)

    def test_formats_empty_day(self):
        self.assertIn("Занятий нет", format_minimal_schedule([], "Среда", "21.10.2026", "EVEN"))


if __name__ == "__main__":
    unittest.main()
