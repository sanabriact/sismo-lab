from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Subject(Generic[T]):

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # Create a subject with no registered listeners
    def __init__(self):
        self._listeners: list[Callable[[T], None]] = []

    # -------------------------------------------------------------------------
    # Subscription management
    # -------------------------------------------------------------------------

    # Register a listener and return a function that removes it
    def subscribe(self, listener: Callable[[T], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        # The guard makes calling unsubscribe more than once safe
        def unsubscribe():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    # -------------------------------------------------------------------------
    # Notification
    # -------------------------------------------------------------------------

    # Send a payload to every listener without letting one failure stop the rest
    def notify(self, payload: T) -> None:
        # Iterate over a copy so listeners can unsubscribe during notification
        for listener in list(self._listeners):
            try:
                listener(payload)
            except Exception as error:
                print(f"Subject listener failed: {error}")