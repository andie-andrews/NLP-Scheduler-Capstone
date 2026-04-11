import unittest

from app.llm.orchestration.context_resolution import (
    is_follow_up_employee_query,
    is_self_referential_employee_query,
)


class ContextResolutionTests(unittest.TestCase):
    def test_self_referential_query_detected(self):
        self.assertTrue(is_self_referential_employee_query("when is my next shift"))
        self.assertTrue(is_self_referential_employee_query("how many hours do I work next week"))

    def test_non_self_query_not_marked_self_referential(self):
        self.assertFalse(is_self_referential_employee_query("show jane doe schedule next week"))

    def test_follow_up_query_detected(self):
        self.assertTrue(is_follow_up_employee_query("next week"))
        self.assertTrue(is_follow_up_employee_query("how many hours"))

    def test_non_follow_up_query_not_detected(self):
        self.assertFalse(is_follow_up_employee_query("hello there"))


if __name__ == "__main__":
    unittest.main()
