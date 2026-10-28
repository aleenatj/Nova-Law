import { toastManager, createErrorToast } from "../utils/toasts";
import { storeRedirectAfterLogin, getStoredRedirect } from "../utils/redirectAfterLogin";

const BASE_URL = import.meta.env.PUBLIC_ENV__BASE_API_URL as string;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public endpoint: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const ERROR_TO_EXCLUDE = [422, 400, 401, 403, 409];

// URL patterns where 403/409 error handling should be skipped
// Check if pathname matches any pattern in this array (supports exact matches or patterns)
export const EXCLUDED_ERROR_HANDLING_URL_PATTERNS = [
  (pathname: string) => pathname.startsWith("/resolve/")
];

// API endpoints for which 400 error toasts should not be shown (handled by the caller)
const SKIP_400_TOAST_ENDPOINTS = ["/v1/auth/verify-engage-token"];

// Token management utilities
export const tokenManager = {
  getAccessToken: () => localStorage.getItem("auth_token"),
  getRefreshToken: () => localStorage.getItem("refresh_token"),
  setTokens: (accessToken: string, refreshToken: string, tokenType: string = "Bearer") => {
    localStorage.setItem("auth_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("token_type", tokenType);
    startAutoRefresh();
  },
  clearTokens: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user");
    localStorage.removeItem("user_role");
    localStorage.removeItem("password_state");
    stopAutoRefresh();
  }
};

// Refresh token response interface
interface RefreshTokenResponse {
  success: boolean;
  message: string;
  data: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
}

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

// Global function to show sign-in modal on token expiry
let showSignInModal: (() => void) | null = null;

export const setTokenExpiryHandler = (handler: () => void) => {
  showSignInModal = handler;
};

// Auto-refresh timer management
let refreshTimer: number | null = null;
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Starts the automatic token refresh timer.
 * Refreshes tokens every 5 minutes if user is authenticated.
 */
function startAutoRefresh(): void {
  // Clear any existing timer
  stopAutoRefresh();

  // Only start if we have tokens
  if (!tokenManager.getAccessToken() || !tokenManager.getRefreshToken()) {
    return;
  }


  refreshTimer = window.setInterval(async () => {
    try {
      // Only refresh if we still have tokens (user hasn't logged out)
      if (tokenManager.getAccessToken() && tokenManager.getRefreshToken()) {
        await refreshToken();
      } else {
        stopAutoRefresh();
      }
    } catch (error) {
      console.error('Auto-refresh: Failed to refresh tokens:', error);
      // If auto-refresh fails, stop the timer
      stopAutoRefresh();
      // The refreshToken function will have already cleared tokens if it was a 401
    }
  }, REFRESH_INTERVAL);
}

/**
 * Stops the automatic token refresh timer.
 */
function stopAutoRefresh(): void {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

/**
 * Refreshes the access token using the refresh token.
 * Updates localStorage with new tokens and returns the new access token.
 * Throws an error if refresh fails (401 = invalid refresh token, user should be logged out).
 */
export async function refreshToken(): Promise<string> {
  // If already refreshing, return the existing promise
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  const refreshTokenValue = tokenManager.getRefreshToken();
  if (!refreshTokenValue) {
    throw new ApiError("No refresh token available", 401, "/v1/auth/refresh");
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const response = await fetch(`${BASE_URL}/v1/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify({
          refresh_token: refreshTokenValue
        }),
      });

      const responseText = await response.text();

      if (!response.ok) {
        // If refresh token is invalid/expired (401), clear tokens and show sign-in modal
        if (response.status === 401) {
          tokenManager.clearTokens();
          // Store current URL for redirect after login
          storeRedirectAfterLogin();
          // Show sign-in modal instead of throwing error
          if (showSignInModal) {
            showSignInModal();
          }
          throw new ApiError("Refresh token expired or invalid", 401, "/v1/auth/refresh");
        }
        throw new ApiError(
          `${response.status} ${response.statusText || "Error"} - ${responseText}`,
          response.status,
          "/v1/auth/refresh"
        );
      }

      let data: RefreshTokenResponse;
      try {
        data = JSON.parse(responseText);
      } catch {
        throw new ApiError("Invalid JSON response from refresh endpoint", 500, "/v1/auth/refresh");
      }

      if (!data.success || !data.data) {
        throw new ApiError("Invalid response format from refresh endpoint", 500, "/v1/auth/refresh");
      }

      // Update tokens in localStorage (without triggering auto-refresh restart)
      localStorage.setItem("auth_token", data.data.access_token);
      localStorage.setItem("refresh_token", data.data.refresh_token);
      localStorage.setItem("token_type", data.data.token_type);

      return data.data.access_token;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const makeRequest = async (useRefreshedToken: boolean = false): Promise<T> => {
    const url = `${BASE_URL}${endpoint}`;

    // Normalize headers to string:string
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...Object.fromEntries(
        Object.entries(options.headers ?? {}).map(([k, v]) => [k, String(v)])
      ),
    };

    // Attach auth token if available and not already provided
    // Only add the token from localStorage if Authorization header is not already set
    if (!headers["Authorization"]) {
      const token = tokenManager.getAccessToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    // Compose fetch options
    const fetchOptions: RequestInit = {
      ...options,
      headers,
    };

    const response = await fetch(url, fetchOptions);
    const responseText = await response.text();

    if (!response.ok) {
      const statustext = response.statusText || "Error";
      throw new ApiError(
        `${response.status} ${statustext} - ${responseText}`,
        response.status,
        endpoint
      );
    }

    try {
      return JSON.parse(responseText);
    } catch {
      // If not JSON, return as text
      return responseText as unknown as T;
    }
  };

  try {
    // First attempt
    return await makeRequest();
  } catch (error) {
    // If we get a 401 and have a refresh token, try to refresh and retry
    if (
      error instanceof ApiError &&
      error.status === 401 &&
      tokenManager.getRefreshToken() &&
      !isRefreshing
    ) {
      try {
        // Refresh the token
        await refreshToken();
        // Retry the original request with the new token
        return await makeRequest(true);
      } catch (refreshError) {
        // If refresh fails, logout user and show sign-in modal
        logout();
        // Store current URL for redirect after login
        const currentUrl = window.location.pathname + window.location.search + window.location.hash;
        storeRedirectAfterLogin(currentUrl);
        
        // Navigate to login page so URL reflects login state
        // Only navigate if we're not already on /login or / (to avoid unnecessary navigation)
        if (window.location.pathname !== "/login" && window.location.pathname !== "/") {
          // Navigate to /login - this will trigger ModalContext to open modal and redirect to /
          // Note: Navigation is asynchronous, but page will reload, so code after this won't execute
          window.location.href = "/login";
          // Throw error for type safety - navigation will cause page reload anyway
          throw refreshError;
        }
        
        if (showSignInModal) {
          showSignInModal();
        }
        // Still throw the error for proper error handling in components
        throw refreshError;
      }
    }
    
    // Handle any 401 error (unauthorized) - clear tokens and show sign-in modal
    if (error instanceof ApiError && error.status === 401) {
      tokenManager.clearTokens();
      // Only store redirect URL if user is not already authenticated
      // This prevents re-storing the URL after successful login redirect
      const isAuthenticated = !!tokenManager.getAccessToken();
      if (!isAuthenticated) {
        // Get current URL and stored redirect URL
        const currentUrl = window.location.pathname + window.location.search + window.location.hash;
        const storedRedirect = getStoredRedirect();
        
        // If user manually navigated to a different page, update the redirect
        // Only preserve stored redirect if it's the same as current page
        // (This handles the case where the same page gets multiple 401s)
        if (!storedRedirect || storedRedirect !== currentUrl) {
          // Store current URL for redirect after login
          storeRedirectAfterLogin(currentUrl);
        }
        
        // Navigate to login page so URL reflects login state
        // The ModalContext will handle opening the modal when it sees /login route
        // Only navigate if we're not already on /login or / (to avoid unnecessary navigation)
        if (window.location.pathname !== "/login" && window.location.pathname !== "/") {
          // Navigate to /login - this will trigger ModalContext to open modal and redirect to /
          // Setting window.location.href causes immediate navigation and page reload
          // The error is thrown for TypeScript, but navigation happens first
          window.location.href = "/login";
          throw error; // Navigation will cause page reload, this may not execute
        }
      }
      if (showSignInModal) {
        showSignInModal();
      }
      // If we're already on /login or /, still throw the error so components can handle it
      // but the modal should already be showing
      throw error;
    }
    
    // Handle 400 (Bad Request) - show error toast with backend message
    if (error instanceof ApiError && error.status === 400) {
      if (SKIP_400_TOAST_ENDPOINTS.some((ep) => error.endpoint.includes(ep))) {
        throw error;
      }
      // Try to extract the message from the error's message (which may contain JSON)
      const match = error.message.match(/\{.*\}$/);
      let errorMessage = "Invalid request. Please check your input and try again.";
      
      if (match) {
        try {
          const json = JSON.parse(match[0]);
          if (json && typeof json.message === "string") {
            errorMessage = json.message;
          } else if (Array.isArray(json.message)) {
            // Handle array of messages - just use the first one for the toast
            errorMessage = json.message[0]?.message || errorMessage;
          }
        } catch {
          // Ignore JSON parse errors, use default message
        }
      }
      
      // Show error toast
      const toast = createErrorToast("Bad Request", errorMessage);
      toastManager.addToast(toast);
    }
    
    // Handle 403 (Forbidden) - show error toast with backend message
    if (error instanceof ApiError && error.status === 403 || error instanceof ApiError && error.status === 409) {
      // Skip error handling for excluded URL patterns
      const currentPath = window.location.pathname;
      if (EXCLUDED_ERROR_HANDLING_URL_PATTERNS.some(pattern => pattern(currentPath))) {
        throw error;
      }
      
      // Try to extract the actual backend message from the error
      let errorMessage = "";
      const match = error.message.match(/\{.*\}$/);

      if (match) {
        try {
          const json = JSON.parse(match[0]);
          if (json && typeof json.message === "object" && json.message !== null) {
            // Handles message array [{msg: "..."}] or object
            if (Array.isArray(json.message) && json.message[0]?.msg) {
              errorMessage = json.message[0].msg;
            } else if (json.message.msg) {
              errorMessage = json.message.msg;
            }
          } else if (json && typeof json.message === "string") {
            errorMessage = json.message;
          }
        } catch {
          errorMessage = error.message;
        }
      } else {
        errorMessage = error.message;
      }

      // Show error toast with backend message
      const toast = createErrorToast("Access Denied", errorMessage || "Access forbidden.");
      toastManager.addToast(toast);
    }
    
    // Handle 422 (Unprocessable Entity) - show error toast with backend message
    if (error instanceof ApiError && error.status === 422) {
      // Try to extract the actual backend message from the error
      let errorMessage = "";
      const match = error.message.match(/\{.*\}$/);

      if (match) {
        try {
          const json = JSON.parse(match[0]);
          if (json && typeof json.message === "object" && json.message !== null) {
            if (Array.isArray(json.message) && json.message[0]?.msg) {
              errorMessage = json.message[0].msg;
            } else if (json.message.msg) {
              errorMessage = json.message.msg;
            }
          } else if (json && typeof json.message === "string") {
            errorMessage = json.message;
          }
        } catch {
          errorMessage = error.message;
        }
      } else {
        errorMessage = error.message;
      }

      // Show error toast with backend message
      const toast = createErrorToast("Validation Error", errorMessage || "Validation failed.");
      toastManager.addToast(toast);
    }
    
    // If the error is an ApiError and the response body is JSON with a message, extract and throw a cleaner error
    if (error instanceof ApiError) {
      // Try to extract a message from the error's message (which may contain JSON)
      const match = error.message.match(/\{.*\}$/);
      if (match) {
        try {
          const json = JSON.parse(match[0]);
          if (json && typeof json.message === "string") {
            throw new ApiError(json.message, error.status, error.endpoint);
          }
        } catch {
          // Ignore JSON parse errors, fall through to throw original error
        }
      }
    }
    throw error;
  }
}

/**
 * Reusable API methods for common HTTP verbs.
 * Easily extendable for future needs (e.g., PATCH, custom headers, etc).
 */
export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiFetch<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, data?: any, options?: RequestInit) => {
    const isFormData = data instanceof FormData;
    const headers = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    };
    return apiFetch<T>(endpoint, {
      ...options,
      method: "POST",
      body: isFormData ? data : JSON.stringify(data),
      headers,
    });
  },

  put: <T>(endpoint: string, data?: any, options?: RequestInit) => {
    const isFormData = data instanceof FormData;
    const headers = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    };
    return apiFetch<T>(endpoint, {
      ...options,
      method: "PUT",
      body: isFormData ? data : JSON.stringify(data),
      headers,
    });
  },

  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiFetch<T>(endpoint, { ...options, method: "DELETE" }),

  patch: <T>(endpoint: string, data?: any, options?: RequestInit) => {
    const isFormData = data instanceof FormData;
    const headers = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    };
    return apiFetch<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: isFormData ? data : JSON.stringify(data),
      headers,
    });
  },
};

/**
 * Utility function to check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!tokenManager.getAccessToken();
};

export const logout = (): void => {
  tokenManager.clearTokens();
  sessionStorage.removeItem("resolveId");
  sessionStorage.removeItem("resolve_session_data");
  sessionStorage.removeItem("current_case_id");
};

export const initializeAutoRefresh = async (): Promise<void> => {
  // Check if user has tokens and validate the refresh token immediately
  const refreshTokenValue = tokenManager.getRefreshToken();
  
  if (isAuthenticated() && refreshTokenValue) {
    try {
      // Validate refresh token by calling refresh endpoint immediately
      await refreshToken();
      // Start the auto-refresh timer after successful validation
      startAutoRefresh();
    } catch (error) {
      // Token validation failed, clear all tokens
      tokenManager.clearTokens();
    }
  }
};

