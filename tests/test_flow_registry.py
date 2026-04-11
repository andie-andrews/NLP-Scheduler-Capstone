import unittest

from app.llm.orchestration.registry import FlowRegistry


class FlowRegistryTests(unittest.TestCase):
    def test_dispatch_returns_first_non_none_result(self):
        registry = FlowRegistry()
        calls = []

        def first_handler(**kwargs):
            calls.append(("first", kwargs["value"]))
            return None

        def second_handler(**kwargs):
            calls.append(("second", kwargs["value"]))
            return {"ok": True}

        registry.register("first", first_handler)
        registry.register("second", second_handler)

        result = registry.dispatch(value=7)

        self.assertEqual(result, {"ok": True})
        self.assertEqual(calls, [("first", 7), ("second", 7)])

    def test_dispatch_returns_none_when_no_handler_matches(self):
        registry = FlowRegistry()
        registry.register("noop", lambda **kwargs: None)

        result = registry.dispatch(value=3)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
