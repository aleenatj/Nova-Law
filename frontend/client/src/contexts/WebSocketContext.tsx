import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { toastManager, createToast } from "@/utils/toasts";
import { AlertType } from "@/utils/alerts";
import { useRole } from "@/contexts/RoleContext";
import { useAuth } from "@/contexts/AuthContext";
import { TimelineContext } from "@/contexts/TimelineContext";
import { useRoute } from "wouter";
type MessageListener = (message: any) => void;

interface WebSocketContextType {
  lastMessage: any;
  isConnected: boolean;
  subscribe: (listener: MessageListener) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

function getAuthToken() {
  return localStorage.getItem("auth_token");
}

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [hasToken, setHasToken] = useState<boolean>(() => !!getAuthToken());
  const { currentRole } = useRole();
  const { user } = useAuth();

  const [isCaseRoute, caseParams] = useRoute("/case/:caseId");
  
  // Get effective role from TimelineContext if available (for role switching)
  // useContext returns undefined if context is not available (doesn't throw)
  const timelineContext = useContext(TimelineContext);
  const effectiveRole = timelineContext?.effectiveRole || currentRole;
  
  // Use a ref to store effective role so we can access it in the message handler
  const effectiveRoleRef = useRef<string>(effectiveRole);
  
  // Use a ref to store current user ID so we can access it in the message handler
  const currentUserIdRef = useRef<string | null>(user?.id || null);

  const caseRouteRef = useRef<{
    isOnTimelinePage: boolean;
    caseId: string | null;
  }>({
    isOnTimelinePage: false,
    caseId: null
  });

  // Update ref when effectiveRole changes
  useEffect(() => {
    effectiveRoleRef.current = effectiveRole;
  }, [effectiveRole]);
  
  // Update ref when user changes
  useEffect(() => {
    currentUserIdRef.current = user?.id || null;
  }, [user?.id]);
  
  useEffect(() => {
    caseRouteRef.current = {
      isOnTimelinePage: isCaseRoute,
      caseId: isCaseRoute ? caseParams.caseId : null
    };
  }, [isCaseRoute, caseParams?.caseId]);

  const socketRef = useRef<WebSocket | null>(null);
  const lastMessageRef = useRef<any>(null);
  const listenersRef = useRef<Set<MessageListener>>(new Set());
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // Start with 1 second

  // Listen for auth_token changes in localStorage (e.g., login/logout in other tabs)
  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.key === "auth_token") {
        const tokenExists = !!getAuthToken();
        setHasToken(tokenExists);
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  // Also watch for auth_token changes in this tab (e.g., login/logout in this tab)
  // Only track presence, not the actual token value to avoid reconnects on refresh
  useEffect(() => {
    const interval = setInterval(() => {
      const tokenExists = !!getAuthToken();
      setHasToken(prev => prev !== tokenExists ? tokenExists : prev);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Handle page visibility changes to reconnect WebSocket when user returns
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && hasToken && !isConnected) {
        // Trigger reconnection by updating hasToken (this will cause useEffect to run)
        setHasToken(prev => !prev);
        setTimeout(() => setHasToken(true), 100);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [hasToken, isConnected]);

  // Reconnection logic with exponential backoff
  const attemptReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);

    reconnectTimeoutRef.current = window.setTimeout(() => {
      if (hasToken && getAuthToken()) {
        setHasToken(false);
        setTimeout(() => setHasToken(true), 100);
        reconnectAttemptsRef.current++;
      }
    }, delay);
  }, [hasToken]);

  useEffect(() => {
    // Clear any existing reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (!hasToken) {
      setIsConnected(false);
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      reconnectAttemptsRef.current = 0; // Reset attempts when no token
      return;
    }

    // Get the current token (we still need it for the URL, but won't reconnect on token refresh)
    const currentToken = getAuthToken();
    if (!currentToken) return;

    // Build WebSocket URL
    const WEBSOCKET_URL = import.meta.env.PUBLIC_ENV__WEBSOCKET_URL as string;
    const WS_URL = `${WEBSOCKET_URL}/?auth_token=${currentToken}`;

    // Close previous socket if any
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    // Create connection
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      reconnectAttemptsRef.current = 0; // Reset attempts on successful connection
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        lastMessageRef.current = data;
        
        // Notify all subscribers
        listenersRef.current.forEach(listener => {
          try {
            listener(data);
          } catch (error) {
          }
        });
        
        // Display toast if message has message_type and message fields
        if (data.message_type && data.message) {
          const { isOnTimelinePage, caseId } = caseRouteRef.current;
          const currentCaseIdFromRoute = isOnTimelinePage ? caseId : null;       
          
          // Get current user ID from ref
          const currentUserId = currentUserIdRef.current;

          // Extract case_id from message data
          // The structure is: data.data.case_id (where data.data is the timeline event data)
          const messageCaseId = data.data?.case_id || null;
          const messageActionUserId = data.data?.action_user_id || null;

          let shouldDiscard = false;

          if (isOnTimelinePage) {
            if (messageCaseId === currentCaseIdFromRoute && messageActionUserId === currentUserId) {
              shouldDiscard = true;
            }
          }

          if (!shouldDiscard) {
            const messageType = data.message_type as AlertType;
            const toast = createToast(
              messageType,
              messageType.charAt(0).toUpperCase() + messageType.slice(1), // Capitalize first letter
              data.message
            );
            toastManager.addToast(toast);
          }
        }
      } catch {
        lastMessageRef.current = event.data;
        // Notify subscribers even for non-JSON messages
        listenersRef.current.forEach(listener => {
          try {
            listener(event.data);
          } catch (error) {
            console.error("[WebSocket] Error in message listener:", error);
          }
        });
      }
    };

    socket.onclose = (event) => {
      setIsConnected(false);
      
      // Only attempt reconnection if the close wasn't intentional (code 1000) and we have a token
      if (event.code !== 1000 && hasToken && getAuthToken()) {
        attemptReconnect();
      }
    };

    socket.onerror = (error) => {
      setIsConnected(false);
    };

    // Cleanup on unmount or hasToken change (login/logout only, not refresh)
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [hasToken, attemptReconnect]);

  // Subscribe to WebSocket messages
  const subscribe = useCallback((listener: MessageListener) => {
    listenersRef.current.add(listener);
    // Return unsubscribe function
    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close(1000, "Component unmounting");
        socketRef.current = null;
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ 
      lastMessage: lastMessageRef.current, 
      isConnected,
      subscribe 
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) throw new Error("useWebSocket must be used within a WebSocketProvider");
  return context;
};