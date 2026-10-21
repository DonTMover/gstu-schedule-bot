import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from utils import get_inline_search_query, handle_group_search, resolve_group_name


class GroupSearchTests(unittest.TestCase):
    def test_resolves_group_code_from_plain_inline_text(self):
        self.assertEqual(resolve_group_name("ап-21"), "АП-21")

    def test_resolves_group_slug(self):
        self.assertEqual(resolve_group_name("ap-21"), "АП-21")

    def test_unknown_group_is_not_selected(self):
        self.assertIsNone(resolve_group_name("unknown-group"))

    def test_group_search_returns_suggestions_for_first_cyrillic_letter(self):
        results = handle_group_search("а")
        self.assertTrue(results)
        self.assertTrue(any(result.title.startswith("Группа: А") for result in results))

    def test_inline_prefix_is_case_insensitive(self):
        self.assertEqual(get_inline_search_query("GROUP: а", "group"), "а")
        self.assertEqual(get_inline_search_query("group:а", "group"), "а")


if __name__ == "__main__":
    unittest.main()
