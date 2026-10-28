"""Authentication and authorization related enums."""

from enum import Enum


class Permission(str, Enum):
    """System permissions."""

    # User Management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"

    # Chat Management
    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"
    CHAT_UPDATE = "chat:update"
    CHAT_DELETE = "chat:delete"
    CHAT_LIST = "chat:list"
    CHAT_SEND_MESSAGE = "chat:send_message"

    # Agent Management
    AGENT_READ = "agent:read"
    AGENT_CREATE = "agent:create"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_LIST = "agent:list"
    AGENT_TEST = "agent:test"

    # System Management
    SYSTEM_STATUS = "system:status"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"

    # Role Management
    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_LIST = "role:list"

    # Admin Only
    ADMIN_ALL = "admin:all"
