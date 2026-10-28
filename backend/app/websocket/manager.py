"""
Enhanced WebSocket Manager for Real-time Notifications

This module provides a robust WebSocket management system for real-time notifications
in the event-driven architecture. It combines simplicity with production-ready features
including error handling, connection monitoring, and role-based broadcasting.

Features:
- Simple single-mapping connection storage
- Robust error handling with automatic cleanup
- Role-based message broadcasting
- Connection monitoring and statistics
- Framework-agnostic design (works with FastAPI, but not tied to it)
- Extensible architecture for future enhancements
- Database persistence for connection tracking

Author: Event-Driven Architecture Team
Version: 1.0.0
"""

import json
import logging
import time
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    user_id: str
    connection_id: str
    websocket: Any
    connected_at: float
    last_activity: float
    status: ConnectionStatus
    role_code: str
    message_count: int = 0


class WebSocketManager:
    """
    Enhanced WebSocket manager for handling real-time notifications.
    
    This manager provides a robust, production-ready solution for WebSocket
    connection management with comprehensive error handling, monitoring,
    and broadcasting capabilities.
    
    Key Features:
    - Simple single-mapping connection storage
    - Automatic error handling and connection cleanup
    - Role-based message broadcasting
    - Connection monitoring and statistics
    - Database persistence for connection tracking
    - Extensible architecture
    
    Attributes:
        connections: Dictionary mapping (user_id, connection_id) to ConnectionInfo
        stats: Connection statistics for monitoring
    """
    
    def __init__(self, auto_cleanup: bool = True, max_connections: Optional[int] = None):
        """
        Initialize the WebSocket manager.
        
        Args:
            auto_cleanup: Whether to automatically clean up broken connections
            max_connections: Maximum number of concurrent connections (None for unlimited)
        """
        self.connections: Dict[tuple[str, str], ConnectionInfo] = {}
        self.auto_cleanup = auto_cleanup
        self.max_connections = max_connections
        
        # Statistics tracking
        self.stats = {
            'total_connections': 0,
            'total_disconnections': 0,
            'total_messages_sent': 0,
            'total_errors': 0,
            'start_time': time.time()
        }
        
        logger.info(f"WebSocket manager initialized (auto_cleanup={auto_cleanup}, max_connections={max_connections})")
    
    async def connect(self, user_id: str, connection_id: str, websocket: Any, db_session: Any, role_code: str) -> bool:
        """
        Register a new WebSocket connection for a user.
        
        Args:
            user_id: The user's unique identifier
            connection_id: The connection ID from frontend
            websocket: The WebSocket connection object
            db_session: Database session for persistence
            role_code: The role code of the user
        Returns:
            bool: True if connection was successful, False if rejected
            
        Raises:
            ValueError: If user_id is already connected with same connection_id
            RuntimeError: If maximum connections limit is reached
        """
        connection_key = (user_id, connection_id)
        
        if connection_key in self.connections:
            raise ValueError(f"User {user_id} with connection {connection_id} is already connected")
        
        if self.max_connections and len(self.connections) >= self.max_connections:
            logger.warning(f"Maximum connections limit reached ({self.max_connections})")
            raise RuntimeError("Maximum connections limit reached")
        
        current_time = time.time()
        connection_info = ConnectionInfo(
            user_id=user_id,
            connection_id=connection_id,
            websocket=websocket,
            connected_at=current_time,
            last_activity=current_time,
            status=ConnectionStatus.CONNECTED,
            role_code=role_code
        )
        
        # Store in memory
        self.connections[connection_key] = connection_info
        self.stats['total_connections'] += 1
        
        # Persist to database
        try:
            from app.db.models.websocket_connection import WebSocketConnection
            
            db_connection = WebSocketConnection(
                user_id=int(user_id),
                connection_id=connection_id,
                role_code=role_code
            )
            db_session.add(db_connection)
            db_session.commit()
            
            logger.info(f"User {user_id} connected with connection {connection_id} (total: {len(self.connections)})")
            return True
            
        except Exception as e:
            logger.error(f"Error persisting connection to database: {e}")
            # Rollback memory connection
            del self.connections[connection_key]
            self.stats['total_connections'] -= 1
            db_session.rollback()
            return False
    
    async def disconnect(self, user_id: str, connection_id: str, db_session: Any) -> bool:
        """
        Remove a user's WebSocket connection.
        
        Args:
            user_id: The user's unique identifier
            connection_id: The connection ID from frontend
            db_session: Database session for persistence
            
        Returns:
            bool: True if user was connected and disconnected, False otherwise
        """
        connection_key = (user_id, connection_id)
        
        if connection_key not in self.connections:
            logger.warning(f"Attempted to disconnect user {user_id} with connection {connection_id} who is not connected")
            return False
        
        connection_info = self.connections[connection_key]
        connection_info.status = ConnectionStatus.DISCONNECTED
        
        # Remove from memory
        del self.connections[connection_key]
        self.stats['total_disconnections'] += 1
        
        # Remove from database
        try:
            from app.db.models.websocket_connection import WebSocketConnection
            
            db_connection = db_session.query(WebSocketConnection).filter(
                WebSocketConnection.user_id == int(user_id),
                WebSocketConnection.connection_id == connection_id
            ).first()
            
            if db_connection:
                db_session.delete(db_connection)
                db_session.commit()
            
            logger.info(f"User {user_id} with connection {connection_id} disconnected (total: {len(self.connections)})")
            return True
            
        except Exception as e:
            logger.error(f"Error removing connection from database: {e}")
            db_session.rollback()
            return True  # Still return True since memory cleanup succeeded
    
    async def send_personal_message(self, user_id: str, connection_id: str, message: Dict[str, Any], db_session: Any) -> bool:
        """
        Send a personal message to a specific user via WebSocket.
        
        Args:
            user_id: The recipient user's ID
            connection_id: The connection ID from frontend
            message: The message to send (will be JSON serialized)
            db_session: Database session for persistence
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        connection_key = (user_id, connection_id)
        
        if connection_key not in self.connections:
            logger.warning(f"User {user_id} with connection {connection_id} not connected, cannot send message")
            return False
        
        connection_info = self.connections[connection_key]
        
        try:
            # Send the message
            await connection_info.websocket.send_text(json.dumps(message))
            
            # Update connection info
            current_time = time.time()
            connection_info.last_activity = current_time
            connection_info.message_count += 1
            self.stats['total_messages_sent'] += 1
            
            logger.debug(f"Message sent to user {user_id} with connection {connection_id}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to user {user_id} with connection {connection_id}: {e}")
            self.stats['total_errors'] += 1
            
            if self.auto_cleanup:
                await self._cleanup_broken_connection(user_id, connection_id, connection_info, db_session)
            
            return False
    
    async def broadcast_message(
        self, 
        message: Dict[str, Any], 
        user_connections: Optional[List[tuple[str, str]]] = None,
        exclude_connections: Optional[List[tuple[str, str]]] = None,
        db_session: Any = None
    ) -> Dict[str, int]:
        """
        Broadcast a message to multiple user connections.
        
        Args:
            message: The message to broadcast
            user_connections: Optional list of (user_id, connection_id) tuples to send to. If None, sends to all connected users.
            exclude_connections: Optional list of (user_id, connection_id) tuples to exclude from broadcasting
            db_session: Database session for persistence
            
        Returns:
            Dict with 'sent' and 'failed' counts
        """
        if user_connections is None:
            user_connections = list(self.connections.keys())
        
        if exclude_connections is None:
            exclude_connections = []
        
        # Filter out excluded connections
        target_connections = [conn for conn in user_connections if conn not in exclude_connections]
        
        sent_count = 0
        failed_count = 0
        
        for user_id, connection_id in target_connections:
            success = await self.send_personal_message(user_id, connection_id, message, db_session)
            if success:
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Broadcasted message to {sent_count} connections, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}
    
    def is_connected(self, user_id: str, connection_id: str) -> bool:
        """
        Check if a user is currently connected via WebSocket with specific connection.
        
        Args:
            user_id: The user's ID
            connection_id: The connection ID from frontend
            
        Returns:
            bool: True if the user is connected with this connection, False otherwise
        """
        connection_key = (user_id, connection_id)
        return (connection_key in self.connections and 
                self.connections[connection_key].status == ConnectionStatus.CONNECTED)
    
    def get_connection_info(self, user_id: str, connection_id: str) -> Optional[ConnectionInfo]:
        """
        Get connection information for a specific user and connection.
        
        Args:
            user_id: The user's ID
            connection_id: The connection ID from frontend
            
        Returns:
            ConnectionInfo if user is connected with this connection, None otherwise
        """
        connection_key = (user_id, connection_id)
        return self.connections.get(connection_key)
    
    def get_connected_users(self) -> Set[str]:
        """
        Get the set of currently connected user IDs.
        
        Returns:
            Set of connected user IDs
        """
        return {user_id for (user_id, _), conn_info in self.connections.items() 
                if conn_info.status == ConnectionStatus.CONNECTED}
    
    def get_connection_count(self) -> int:
        """
        Get the number of active WebSocket connections.
        
        Returns:
            Number of active connections
        """
        return len([conn for conn in self.connections.values() 
                   if conn.status == ConnectionStatus.CONNECTED])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive connection statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        current_time = time.time()
        uptime = current_time - self.stats['start_time']
        
        # Calculate average connection duration
        total_duration = sum(
            current_time - conn.connected_at 
            for conn in self.connections.values()
        )
        avg_duration = total_duration / len(self.connections) if self.connections else 0
        
        return {
            'active_connections': self.get_connection_count(),
            'total_connections': self.stats['total_connections'],
            'total_disconnections': self.stats['total_disconnections'],
            'total_messages_sent': self.stats['total_messages_sent'],
            'total_errors': self.stats['total_errors'],
            'uptime_seconds': uptime,
            'average_connection_duration': avg_duration,
            'max_connections': self.max_connections,
            'auto_cleanup_enabled': self.auto_cleanup
        }
    
    async def cleanup_inactive_connections(self, max_idle_time: float = 3600, db_session: Any = None) -> int:
        """
        Clean up connections that have been inactive for too long.
        
        Args:
            max_idle_time: Maximum idle time in seconds before cleanup
            db_session: Database session for persistence
            
        Returns:
            Number of connections cleaned up
        """
        current_time = time.time()
        inactive_connections = []
        
        for (user_id, connection_id), conn_info in self.connections.items():
            if current_time - conn_info.last_activity > max_idle_time:
                inactive_connections.append((user_id, connection_id))
        
        for user_id, connection_id in inactive_connections:
            await self.disconnect(user_id, connection_id, db_session)
            logger.info(f"Cleaned up inactive connection for user {user_id} with connection {connection_id}")
        
        return len(inactive_connections)
    
    async def _cleanup_broken_connection(self, user_id: str, connection_id: str, connection_info: ConnectionInfo, db_session: Any):
        """
        Clean up a broken connection.
        
        Args:
            user_id: The user's ID
            connection_id: The connection ID from frontend
            connection_info: The connection information
            db_session: Database session for persistence
        """
        connection_key = (user_id, connection_id)
        connection_info.status = ConnectionStatus.ERROR
        del self.connections[connection_key]
        self.stats['total_disconnections'] += 1
        
        # Remove from database
        try:
            from app.db.models.websocket_connection import WebSocketConnection
            
            db_connection = db_session.query(WebSocketConnection).filter(
                WebSocketConnection.user_id == int(user_id),
                WebSocketConnection.connection_id == connection_id
            ).first()
            
            if db_connection:
                db_session.delete(db_connection)
                db_session.commit()
                
        except Exception as e:
            logger.error(f"Error removing broken connection from database: {e}")
            db_session.rollback()
        
        logger.warning(f"Cleaned up broken connection for user {user_id} with connection {connection_id}")


# Global WebSocket manager instance
# This singleton pattern ensures consistent WebSocket management across all modules
websocket_manager = WebSocketManager()
