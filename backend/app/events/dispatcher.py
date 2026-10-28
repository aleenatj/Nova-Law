"""
Event Dispatcher Module

This module provides the core event dispatching functionality for the Nova Law AI application.
It handles event execution without database persistence, including recursive subscriber dispatching.

The dispatcher supports:
- Event execution without database persistence
- Main event handlers that can modify payload
- Recursive subscriber event dispatching
- Request/response models for each event type
- Flow-based event chains with response collection
- Immediate error propagation to triggering function
- WebSocket integration for real-time updates

Author: Event-Driven Architecture Team
Version: 1.0.0
"""

import asyncio
from collections.abc import Callable
from functools import wraps

from fastapi import HTTPException
from sqlalchemy.orm import Session
from structlog import get_logger

from app.config.events.events import get_subscribers_for_event
from app.enums.events import EventType
from app.schemas.v1.event import Event, EventResponseData
from app.websocket.manager import WebSocketManager

logger = get_logger(__name__)

# Global event handler registry - maps event types to their handler functions
# This allows for dynamic event discovery and execution
EVENT_HANDLER_REGISTRY: dict[str, Callable] = {}


def event(event_type: EventType):
    """
    Decorator to register a function as an event handler.

    This decorator automatically registers the decorated function in the EVENT_HANDLER_REGISTRY.
    The decorated function must have the signature:
    async def event_handler(db: Session, payload: Dict[str, Any], websocket_manager: WebSocketManager) -> Dict[str, Any]

    Args:
        event_type (EventType): The type of event this handler processes

    Returns:
        Callable: The decorated function

    Example:
        @event(EventType.PASSWORD_RESET_REQUESTED)
        async def handle_password_reset_requested(
            db: Session,
            payload: Dict[str, Any],
            websocket_manager: WebSocketManager
        ) -> Dict[str, Any]:
            # Event handler implementation
            pass
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Error in event handler {func.__name__} for event {event_type.value}: {e}"
                )
                raise

        # Register the event handler function in the global registry by event type
        EVENT_HANDLER_REGISTRY[event_type.value] = wrapper
        return wrapper

    return decorator


class EventDispatcher:
    """
    Central orchestrator for the Nova Law AI event system.

    Supports:
    - Main event handler execution (with optional payload modification)
    - Recursive execution of subscriber events
    - Sync, async, and ordered dispatch modes
    - WebSocket support for real-time notifications
    """

    def __init__(self):
        self.websocket_manager = None

    def set_websocket_manager(self, manager: WebSocketManager) -> None:
        """Attach a WebSocket manager for real-time notifications."""
        self.websocket_manager = manager

    async def _execute_subscriber_with_recursion(
        self,
        db: Session,
        event_data: Event,
        event_handler: Callable,
        event_type: EventType,
        parent_event_type: EventType = None,
    ) -> dict[str, EventResponseData]:
        """
        Helper method to execute a subscriber handler and dispatch its subscribers recursively.
        """
        responses = {}

        try:
            if parent_event_type and not event_data.parent_event_type:
                event_data.parent_event_type = parent_event_type
            result = await event_handler(db, event_data, self.websocket_manager)
            responses[event_type.value] = result

        except Exception as e:
            logger.exception(
                f"Error in subscriber event handler for {event_type.value}: {e}"
            )
            responses[event_type.value] = EventResponseData(
                success=False, message=f"{e}", data={}
            )
            return responses

        child_events = get_subscribers_for_event(event_type.value)
        for child_event in child_events:
            handler = EVENT_HANDLER_REGISTRY.get(child_event.value)
            if handler:
                child_responses = await self._execute_subscriber_with_recursion(
                    db, event_data, handler, child_event
                )
                responses.update(child_responses)

        return responses

    async def dispatch_event(self, db: Session, event_data: Event) -> None:
        """
        Asynchronously dispatch an event and recursively trigger all subscribers.
        """
        handler = EVENT_HANDLER_REGISTRY.get(event_data.event_type.value)
        main_event_type = event_data.event_type
        if handler:
            try:
                main_response = await handler(db, event_data, self.websocket_manager)
                event_data.response[event_data.event_type.value] = main_response

            except ValueError as e1:
                logger.exception(f"Main event handler failed (ValueError): {e1}")
                result = EventResponseData(success=False, message=f"{e1}", data={})
                event_data.response[event_data.event_type.value] = result
                raise
            except HTTPException as e2:
                logger.exception(f"Main event handler failed (HTTPException): {e2}")
                result = EventResponseData(success=False, message=f"{e2}", data={})
                event_data.response[event_data.event_type.value] = result
                raise
            except Exception as e:
                logger.exception(f"Main event handler failed (Exception): {e}")
                result = EventResponseData(success=False, message=f"{e}", data={})
                event_data.response[event_data.event_type.value] = result
                raise

        subscriber_events = get_subscribers_for_event(event_data.event_type.value)
        tasks = []

        for sub_event in subscriber_events:
            sub_handler = EVENT_HANDLER_REGISTRY.get(sub_event.value)
            if sub_handler:
                task = asyncio.create_task(
                    self._execute_subscriber_with_recursion(
                        db, event_data, sub_handler, sub_event, main_event_type
                    )
                )
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    response = EventResponseData(
                        success=False, message=f"{result}", data={}
                    )
                    event_data.response[sub_event.value] = response
                    continue

                for key, value in result.items():
                    event_data.response[key] = value

        return

    async def dispatch_event_sync(self, db: Session, event_data: Event) -> None:
        """
        Synchronously dispatch an event and recursively trigger all subscribers in series.
        """

        handler = EVENT_HANDLER_REGISTRY.get(event_data.event_type.value)
        if handler:
            try:
                main_response = await handler(db, event_data, self.websocket_manager)
                event_data.response[event_data.event_type.value] = main_response
            except Exception as e:
                logger.exception(f"Main handler failed: {e}")
                result = EventResponseData(success=False, message=f"{e}", data={})
                event_data.response[event_data.event_type.value] = result
                return

        async def run_subscribers(event_type: EventType):
            subscriber_events = get_subscribers_for_event(event_type.value)
            for sub_event in subscriber_events:
                sub_handler = EVENT_HANDLER_REGISTRY.get(sub_event.value)
                if sub_handler:
                    try:
                        result = await sub_handler(
                            db, event_data, self.websocket_manager
                        )
                        event_data.response[sub_event.value] = result
                        await run_subscribers(sub_event)
                    except Exception as e:
                        logger.exception(
                            f"Subscriber handler {sub_event.value} failed: {e}"
                        )
                        result = EventResponseData(
                            success=False, message=f"{e}", data={}
                        )
                        event_data.response[sub_event.value] = result
                        return

        await run_subscribers(event_data.event_type)

        return

    async def dispatch_event_ordered(
        self, db: Session, event_data: Event, stop_on_failure: bool = True
    ) -> None:
        """
        Dispatch event and execute subscribers in order with optional early stopping on failure.
        """

        handler = EVENT_HANDLER_REGISTRY.get(event_data.event_type.value)
        if handler:
            try:
                main_response = await handler(db, event_data, self.websocket_manager)
                event_data.response[event_data.event_type.value] = main_response
            except Exception as e:
                logger.exception(f"Main handler failed: {e}")
                result = EventResponseData(success=False, message=f"{e}", data={})
                event_data.response[event_data.event_type.value] = result
                if stop_on_failure:
                    return

        async def run_ordered_subscribers(event_type: EventType):
            subscriber_events = get_subscribers_for_event(event_type.value)
            for sub_event in subscriber_events:
                sub_handler = EVENT_HANDLER_REGISTRY.get(sub_event.value)
                if sub_handler:
                    try:
                        result = await sub_handler(
                            db, event_data, self.websocket_manager
                        )
                        event_data.response[sub_event.value] = result
                        await run_ordered_subscribers(sub_event)
                    except Exception as e:
                        logger.exception(f"Handler failed for {sub_event.value}: {e}")
                        result = EventResponseData(
                            success=False, message=f"{e}", data={}
                        )
                        event_data.response[sub_event.value] = result
                        if stop_on_failure:
                            return

        await run_ordered_subscribers(event_data.event_type)

        return


# Global event dispatcher instance - used throughout the application
# This singleton pattern ensures consistent event handling across all modules
event_dispatcher = EventDispatcher()
