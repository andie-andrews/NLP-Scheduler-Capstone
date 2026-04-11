from collections.abc import Callable


class FlowRegistry:
    def __init__(self):
        self._handlers: list[tuple[str, Callable]] = []

    def register(self, name: str, handler: Callable):
        self._handlers.append((name, handler))

    def dispatch(self, **kwargs):
        for _, handler in self._handlers:
            result = handler(**kwargs)
            if result is not None:
                return result
        return None
