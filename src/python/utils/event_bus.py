# src/python/utils/event_bus.py

from PySide6.QtCore import QObject, Signal
from typing import Callable, Any
from functools import wraps

from .events import Events
from .logger import get_logger

logger = get_logger(__name__)

def receiver(topic: str, once: bool = False):
    """
    Decorator to mark a method as an event subscriber.

    Methods decorated with this function are flagged with metadata that allows 
    the :class:`EventBus` to automatically register them using 
    :meth:`EventBus.register_instance`.

    :param topic: The event topic string or member of the :class:`Events` enum 
                  to subscribe to.
    :type topic: str
    :param once: If True, the subscription will be removed after the first 
                 time the event is received. Defaults to False.
    :type once: bool, optional

    :return: A decorator function that adds ``_event_subscriptions`` metadata 
             to the method.
    :rtype: Callable

    .. note::
        This decorator does not subscribe the method to the :class:`EventBus` 
        immediately. Subscription occurs when :meth:`EventBus.register_instance` 
        is called on the object containing the decorated method.

    **Example:**

    .. code-block:: python

        class MyController:
            def __init__(self):
                bus.register_instance(self)

            @receiver("file.saved")
            def on_save(self, data):
                print(f"File saved with data: {data}")
    """
    def decorator(func):
        if not hasattr(func, '_event_subscriptions'):
            func._event_subscriptions = []
        func._event_subscriptions.append((topic, once))
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        # Ensure the wrapper carries the metadata too
        wrapper._event_subscriptions = func._event_subscriptions
        return wrapper
    return decorator

class EventBus(QObject):
    """
    Centralized event bus for application-wide communication.
    
    Simple topic-based pub/sub system using Qt signals.
    
    Usage:
        # Subscribe
        bus.subscribe(Events.SAVE_REQUESTED, my_callback)
        
        # Publish
        bus.publish(Events.SAVE_REQUESTED, data={'editor': editor, 'view': view})
        
        # Unsubscribe
        bus.unsubscribe(Events.SAVE_REQUESTED, my_callback)
    """
    
    # Core signal that carries all events
    event_occurred = Signal(str, object)
    
    _instance = None
    
    def __new__(cls):
        """
        Singleton pattern to ensure one event bus instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initialize the event bus (only once due to singleton)
        """
        if self._initialized:
            return
        
        super().__init__()
        
        # Track subscriptions for each topic: {topic: [callback1, callback2, ...]}
        self._subscribers: dict[str, list[Callable]] = {}
        
        # One-time subscriptions
        self._once_subscribers: dict[str, list[Callable]] = {}
        
        # Event history for debugging (can be disabled in production)
        self._history: list[tuple[str, object]] = []
        self._max_history = 100
        self._history_enabled = __debug__  # Automatically disabled in optimized mode
        
        # Connect the Qt signal to our dispatcher
        self.event_occurred.connect(self._dispatch)
        
        self._initialized = True
        logger.info("EventBus initialized")
    
    def publish(self, topic: str | Events, data: Any = None) -> None:
        """
        Publish an event to all subscribers of a topic.
        
        :param topic: Event topic (use Events enum for type safety)
        :type topic: str or Events
        :param data: Event payload (can be any type)
        :type data: Any

        :rtype: None
        """
        topic_str = topic.value if isinstance(topic, Events) else topic
        
        # Add to history
        if self._history_enabled:
            self._history.append((topic_str, data))
            if len(self._history) > self._max_history:
                self._history.pop(0)
        
        logger.debug(f"Event published: {topic_str}")
        
        # Emit via Qt signal (thread-safe)
        self.event_occurred.emit(topic_str, data)
    
    def subscribe(self, topic: str | Events, callback: Callable[[object], None]) -> None:
        """
        Subscribe to an event topic.
        
        :param topic: Event topic to listen for
        :type topic: str or Events
        :param callback: Function to call when event occurs (receives data payload)
        :type callback: Callable[[object], None]

        :rtype: None
        """
        topic_str = topic.value if isinstance(topic, Events) else topic
        
        if topic_str not in self._subscribers:
            self._subscribers[topic_str] = []
        
        if callback not in self._subscribers[topic_str]:
            self._subscribers[topic_str].append(callback)
            logger.debug(f"Subscribed {callback.__qualname__} to '{topic_str}'")
    
    def subscribe_once(self, topic: str | Events, callback: Callable[[object], None]) -> None:
        """
        Subscribe to an event topic for a single execution.
        
        :param topic: Event topic to listen for
        :type topic: str or Events
        :param callback: Function to call once when event occurs
        :type callback: Callable[[object], None]

        :rtype: None
        """
        topic_str = topic.value if isinstance(topic, Events) else topic
        
        if topic_str not in self._once_subscribers:
            self._once_subscribers[topic_str] = []
        
        if callback not in self._once_subscribers[topic_str]:
            self._once_subscribers[topic_str].append(callback)
            logger.debug(f"Subscribed (once) {callback.__qualname__} to '{topic_str}'")
    
    def unsubscribe(self, topic: str | Events, callback: Callable[[object], None]) -> None:
        """
        Unsubscribe from an event topic.
        
        :param topic: Event topic to unsubscribe from
        :type topic: str or Events
        :param callback: The callback function to remove
        :type callback: Callable[[object], None]

        :rtype: None
        """
        topic_str = topic.value if isinstance(topic, Events) else topic
        
        if topic_str in self._subscribers and callback in self._subscribers[topic_str]:
            self._subscribers[topic_str].remove(callback)
            logger.debug(f"Unsubscribed {callback.__qualname__} from '{topic_str}'")
    
    def unsubscribe_all(self, topic: str | Events = None) -> None:
        """
        Unsubscribe all callbacks from a topic, or clear all subscriptions.
        
        :param topic: Optional topic to clear (if None, clears everything)
        :type topic: str or Events

        :rtype: None
        """
        if topic is None:
            self._subscribers.clear()
            self._once_subscribers.clear()
            logger.info("Cleared all event subscriptions")
        else:
            topic_str = topic.value if isinstance(topic, Events) else topic
            self._subscribers.pop(topic_str, None)
            self._once_subscribers.pop(topic_str, None)
            logger.debug(f"Cleared all subscriptions for '{topic_str}'")

    def register_instance(self, obj: Any) -> None:
        """
        Scans an object for methods decorated with @receiver and subscribes them.

        :param obj: The object for methods.
        :type: obj: Any

        :rtype: Any
        """
        for attr_name in dir(obj):
            attr = getattr(obj, attr_name)
            if hasattr(attr, '_event_subscriptions'):
                for topic, once in attr._event_subscriptions:
                    if once:
                        self.subscribe_once(topic, attr)
                    else:
                        self.subscribe(topic, attr)

    def unregister_instance(self, obj: Any) -> None:
        """
        Removes all subscriptions where the callback is a method belonging to 'obj'.
        
        :param obj: The object to remove all subscriptions for.
        :type obj: Any

        :rtype: None
        """
        for topic in self._subscribers:
            new_callbacks = []
            for cb in self._subscribers[topic]:
                # Check if it's a standard bound method
                callback_self = getattr(cb, '__self__', None)
                
                # If it's a decorated method, we might need to look deeper
                if callback_self is None and hasattr(cb, '__closure__') and cb.__closure__:
                    # This logic depends on your specific decorator structure
                    pass 

                if callback_self is not obj:
                    new_callbacks.append(cb)
        
            self._subscribers[topic] = new_callbacks
    
    def _dispatch(self, topic: str, data: object) -> None:
        """
        Internal dispatcher called via Qt signal.
        Delivers events to all registered callbacks.
        
        :param topic: Event topic string
        :type topic: str
        :param data: Event payload
        :type data: object

        :rtype: None
        """
        # Regular subscribers
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(
                        f"Error in subscriber {callback.__qualname__} "
                        f"for topic '{topic}': {e}",
                        exc_info=True
                    )
        
        # One-time subscribers
        if topic in self._once_subscribers:
            callbacks = self._once_subscribers[topic].copy()
            self._once_subscribers[topic].clear()
            
            for callback in callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(
                        f"Error in one-time subscriber {callback.__qualname__} "
                        f"for topic '{topic}': {e}",
                        exc_info=True
                    )
    
    def get_history(self, topic: str | Events = None, limit: int = 20) -> list[tuple[str, object]]:
        """
        Get event history for debugging.
        
        :param topic: Optional filter by topic
        :type topic: str or Events
        :param limit: Maximum number of events to return. Default 20.
        :type limit: int

        :return: List of (topic, data) tuples
        :rtype: list[tuple[str, object]]
        """
        if not self._history_enabled:
            logger.warning("Event history is disabled")
            return []
        
        history = self._history
        
        if topic:
            topic_str = topic.value if isinstance(topic, Events) else topic
            history = [(t, d) for t, d in history if t == topic_str]
        
        return history[-limit:] if limit else history
    
    def print_history(self, topic: str | Events = None, limit: int = 20) -> None:
        """
        Print event history to console (for debugging).
        
        :param topic: Optional filter by topic
        :type: str or Events
        :param limit: Maximum number of events to print
        :type limit: 20

        :rtype: None
        """
        history = self.get_history(topic, limit)
        
        if not history:
            print("No event history available")
            return
        
        print(f"\n=== Event History (last {len(history)} events) ===")
        for i, (topic, data) in enumerate(history, 1):
            print(f"{i}. {topic}")
            if data is not None:
                print(f"   Data: {data}")
        print("=" * 50 + "\n")
    
    def get_subscribers(self, topic: str | Events = None) -> dict[str, int]:
        """
        Get count of subscribers for each topic (debugging helper).
        
        :param topic: Optional specific topic to query
        :type topic: str or Events

        :return: Dictionary of {topic: subscriber_count}
        :rtype: dict[str, int]
        """
        if topic:
            topic_str = topic.value if isinstance(topic, Events) else topic
            regular = len(self._subscribers.get(topic_str, []))
            once = len(self._once_subscribers.get(topic_str, []))
            return {topic_str: regular + once}
        
        result = {}
        all_topics = set(self._subscribers.keys()) | set(self._once_subscribers.keys())
        
        for t in all_topics:
            regular = len(self._subscribers.get(t, []))
            once = len(self._once_subscribers.get(t, []))
            result[t] = regular + once
        
        return result


# Global singleton instance
bus = EventBus()