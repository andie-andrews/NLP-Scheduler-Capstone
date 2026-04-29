from typing import Protocol, Any


class FlowHandler(Protocol):
    def __call__(self, **kwargs) -> Any:
        ...
