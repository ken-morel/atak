"""
Subscribeable and Subscriber classes.

>>> s = Subscriber()
>>> s.subscribe_to(callback_function, subscribeable)

"""

from typing import Callable


class Subscriber:
    """
    Efus Subcriber.

    Subscriber creates a subscriber object to subscribe to another
    `Subscribeable` object.
    """

    _subscribing: "list[tuple[Callable, Subscribeable]]"

    def __init__(self):
        """Initialize the Subscriber with default values."""
        self._subscribing = []

    def subscribe_to(self, callback: Callable, subscribeable: "Subscribeable"):
        """Subscribe to the specified subscribeable object."""
        subscribeable.add_subscriber(callback, self)
        self._subscribing.append((callback, subscribeable))

    def unsubscribe_from(self, subscript: "Subscribeable"):
        """Remove all subscriptions with asscociated Subscribeable."""
        for callback, subscribeable in self._subscribing:
            if subscribeable is subscript:
                pass


class Subscribeable:
    """Subscribeable object."""

    _subscribed: list[tuple[Callable, Subscriber]]

    def __init__(self):
        """Initialize the subscribeable with defaults."""
        self._subscribed = []

    def add_subscriber(self, callback: Callable, subscriber: Subscriber):
        """Add the specified subscriber to subscribers list."""
        self._subscribed.append((callback, subscriber))

    def warn_subscribers(self):
        """Call all callbacks registerd as subscribed."""
        for callback, _ in self._subscribed.copy():
            callback()
