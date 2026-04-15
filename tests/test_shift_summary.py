import unittest
from datetime import datetime, timedelta

from app.llm.orchestration.summary import summarize_shifts


class ShiftSummaryTests(unittest.TestCase):
    def _future_shift(self, days: int, hours: int):
        start = (datetime.now() + timedelta(days=days)).replace(microsecond=0).isoformat()
        return {"start": start, "durationHours": hours}

    def test_next_shift_summary_for_self_uses_expected_text_and_hides_total_hours(self):
        shifts = [self._future_shift(1, 8), self._future_shift(2, 6)]

        summary = summarize_shifts(shifts, "when is my next shift")

        self.assertTrue(summary["summary"].startswith("Your next shift is"))
        self.assertNotIn("totalHours", summary)

    def test_next_shift_summary_for_named_employee_uses_possessive_name(self):
        shifts = [self._future_shift(1, 8)]

        summary = summarize_shifts(shifts, "when is jane scheduled next", employee_full_name="Jane Doe")

        self.assertTrue(summary["summary"].startswith("Jane Doe's next shift is"))


if __name__ == "__main__":
    unittest.main()
