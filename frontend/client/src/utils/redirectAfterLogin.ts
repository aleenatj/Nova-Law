/**
 * Utility functions for handling redirect after login
 * Stores the intended destination URL when user is redirected to login,
 * and retrieves it after successful login to redirect user back.
 */

const REDIRECT_AFTER_LOGIN_KEY = "nova_redirect_after_login";
const REDIRECT_EXPIRY_MINUTES = 15; // Redirect URL expires after 15 minutes

interface RedirectData {
  url: string;
  timestamp: number; // Unix timestamp in milliseconds
}

/**
 * Checks if the stored redirect data is expired.
 * 
 * @param data - The redirect data object
 * @returns true if expired, false otherwise
 */
const isRedirectExpired = (data: RedirectData): boolean => {
  const now = Date.now();
  const expiryTime = REDIRECT_EXPIRY_MINUTES * 60 * 1000; // Convert minutes to milliseconds
  return (now - data.timestamp) > expiryTime;
};

/**
 * Gets the current URL from location or window.
 * 
 * @param currentLocation - Optional current location from routing library (e.g., from useLocation hook)
 * @returns The current URL string
 */
const getCurrentUrl = (currentLocation?: string): string => {
  if (currentLocation) {
    // Use location from routing library if provided
    const search = window.location.search;
    const hash = window.location.hash;
    return currentLocation + search + hash;
  }
  // Fallback to window.location
  return window.location.pathname + window.location.search + window.location.hash;
};

/**
 * Stores the current URL as the intended destination after login.
 * Should be called when user is redirected to login page.
 * 
 * @param url - Optional URL to store. If not provided, uses current location.
 * @param currentLocation - Optional current location from routing library (e.g., from useLocation hook)
 */
export const storeRedirectAfterLogin = (url?: string, currentLocation?: string): void => {
  const targetUrl = url || getCurrentUrl(currentLocation);
  // Only store if it's not already a login-related route
  const loginRoutes = ["/login", "/", "/directlogin"];
  const isLoginRoute = loginRoutes.some(route => targetUrl === route || targetUrl.startsWith(route + "/"));
  if (!isLoginRoute) {
    const redirectData: RedirectData = {
      url: targetUrl,
      timestamp: Date.now()
    };
    localStorage.setItem(REDIRECT_AFTER_LOGIN_KEY, JSON.stringify(redirectData));
  }
};

/**
 * Retrieves and clears the stored redirect URL.
 * Should be called after successful login.
 * Automatically clears expired redirect URLs.
 * 
 * @returns The stored URL, or null if none exists or expired.
 */
export const getAndClearRedirectAfterLogin = (): string | null => {
  const storedData = localStorage.getItem(REDIRECT_AFTER_LOGIN_KEY);
  if (storedData) {
    try {
      const redirectData: RedirectData = JSON.parse(storedData);
      
      // Check if expired
      if (isRedirectExpired(redirectData)) {
        localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
        return null;
      }
      
      // Clear and return the URL
      localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
      return redirectData.url;
    } catch (error) {
      // If parsing fails, clear the invalid data
      localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
      return null;
    }
  }
  return null;
};

/**
 * Clears the stored redirect URL without retrieving it.
 * Useful for cleanup scenarios.
 * Also clears expired redirect URLs.
 */
export const clearRedirectAfterLogin = (): void => {
  const storedData = localStorage.getItem(REDIRECT_AFTER_LOGIN_KEY);
  if (storedData) {
    try {
      const redirectData: RedirectData = JSON.parse(storedData);
      // Clear if expired, otherwise just remove
      if (isRedirectExpired(redirectData)) {
        localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
      } else {
        localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
      }
    } catch (error) {
      // If parsing fails, clear the invalid data
      localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
    }
  }
};

/**
 * Gets the stored redirect URL without clearing it.
 * Automatically clears expired redirect URLs.
 * 
 * @returns The stored URL, or null if none exists or expired.
 */
export const getStoredRedirect = (): string | null => {
  const storedData = localStorage.getItem(REDIRECT_AFTER_LOGIN_KEY);
  if (storedData) {
    try {
      const redirectData: RedirectData = JSON.parse(storedData);
      
      // Check if expired
      if (isRedirectExpired(redirectData)) {
        localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
        return null;
      }
      
      return redirectData.url;
    } catch (error) {
      // If parsing fails, clear the invalid data
      localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
      return null;
    }
  }
  return null;
};

/**
 * Checks if there's a stored redirect URL.
 * Automatically clears expired redirect URLs.
 * 
 * @returns true if a redirect URL is stored and not expired, false otherwise.
 */
export const hasStoredRedirect = (): boolean => {
  return getStoredRedirect() !== null;
};

/**
 * Clears the redirect URL if the current page matches the stored redirect URL.
 * This should be called when a page loads successfully after login redirect.
 * Prevents the URL from persisting if it was re-stored after redirect.
 * Also clears expired redirect URLs.
 * 
 * @param currentLocation - Optional current location from routing library (e.g., from useLocation hook)
 */
export const clearRedirectIfOnTargetPage = (currentLocation?: string): void => {
  const storedData = localStorage.getItem(REDIRECT_AFTER_LOGIN_KEY);
  if (storedData) {
    try {
      const redirectData: RedirectData = JSON.parse(storedData);
      
      // Clear if expired
      if (isRedirectExpired(redirectData)) {
        localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
        return;
      }
      
      const currentUrl = getCurrentUrl(currentLocation);
      const currentPathname = currentLocation || window.location.pathname;
      const storedPathname = redirectData.url.split('?')[0].split('#')[0];
      
      // Clear if we're on the target page (exact match or pathname match)
      if (currentUrl === redirectData.url || currentPathname === storedPathname) {
        localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
      }
    } catch (error) {
      // If parsing fails, clear the invalid data
      localStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
    }
  }
};

