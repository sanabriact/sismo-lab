from typing import Callable, Generic, TypeVar
T = TypeVar("T")

class Subject(Generic[T]):
    def __init__(self):
        self._listeners: list[Callable[[T], None]] = []
    
    def subscribe(self, listener: Callable[[T], None]) -> Callable[[], None]:
        self._listeners.append(listener)
    
        def unsubscribe():
            if listener in self._listeners:
                self._listeners.remove(listener)
        
        return unsubscribe
    
    def notify(self, payload: T) -> None:
        for listener in list(self._listeners):
            try:
                listener(payload)
            except Exception as error:
                print(f"Subject listener failed: {error}")