from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Event:
    name: str
    target: Any


EventListener = Callable[[Event, Any], None]


class Emitter(ABC):
    _events: Dict[str, List[EventListener]]

    def __init__(self):
        self._events = {}

    def on(self, event: str, listener: EventListener):
        if event not in self._events:
            self._events[event] = []

        self._events[event].append(listener)

    def emit(self, event: str, *args) -> bool:
        if event not in self._events:
            return False

        for listener in self._events[event]:
            listener(Event(name=event, target=self), *args)

        return True
