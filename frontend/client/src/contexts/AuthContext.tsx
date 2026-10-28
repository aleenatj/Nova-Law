import { createContext, useContext, useState, ReactNode, useEffect, useMemo } from "react";
import { useRole } from "./RoleContext";

interface User {
  id: string;
  name: string;
  email: string;
  role_name?: string;
  photo_urls?: {
    thumbnail: string;
    medium: string;
    large: string;
  };
  role: "Guest" | "Customer" | "Lawyer" | "Navigator";
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (userData: User, token: string) => void;
  logout: () => void;
  refreshUserFromStorage: () => void;
}

// Default context value
const defaultAuthContext: AuthContextType = {
  user: null,
  token: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
  refreshUserFromStorage: () => {},
};

const AuthContext = createContext<AuthContextType>(defaultAuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  // Import RoleContext to sync role
  const { setCurrentRole } = useRole();

  // Function to refresh user data from localStorage
  const refreshUserFromStorage = () => {
    const savedUser = localStorage.getItem("user");
    const savedToken = localStorage.getItem("auth_token");

    if (savedUser && savedToken) {
      try {
        const parsedUser = JSON.parse(savedUser);
        
        // Map the user data from localStorage to our User interface
        const mappedUser: User = {
          id: parsedUser.user_id || parsedUser.id || "",
          name: parsedUser.first_name && parsedUser.last_name 
            ? `${parsedUser.first_name} ${parsedUser.last_name}` 
            : parsedUser.name || "Unknown User",
          email: parsedUser.email || "",
          role_name: parsedUser.role_name,
          photo_urls: parsedUser.photo_urls,
          role: "Guest" // Will be set by RoleContext
        };
        
        setUser(mappedUser);
        setToken(savedToken);
        
        // Let RoleContext handle role mapping from localStorage
        setCurrentRole(parsedUser.role_code || parsedUser.role || "Guest");
      } catch (error) {
        console.error("Error parsing saved user data:", error);
        // Clear invalid data
        localStorage.removeItem("user");
        localStorage.removeItem("auth_token");
        setUser(null);
        setToken(null);
        setCurrentRole("Guest");
      }
    } else {
      // No user data, clear auth state
      setUser(null);
      setToken(null);
      setCurrentRole("Guest");
    }
  };

  // Restore from localStorage on app start
  useEffect(() => {
    refreshUserFromStorage();
  }, [setCurrentRole]);

  // Listen for localStorage changes (for cross-tab synchronization)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'user' || e.key === 'auth_token') {
        refreshUserFromStorage();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [setCurrentRole]);

  // Also watch for auth_token changes in this tab (e.g., login/logout in this tab)
  // This handles cases where localStorage is cleared in the same tab
  useEffect(() => {
    const interval = setInterval(() => {
      const currentUser = localStorage.getItem("user");
      const currentToken = localStorage.getItem("auth_token");
      
      // If localStorage has no user/token but our state still has them, clear the state
      if (!currentUser || !currentToken) {
        if (user || token) {
          setUser(null);
          setToken(null);
          setCurrentRole("Guest");
        }
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [user, token, setCurrentRole]);

  const login = (userData: User, authToken: string) => {
    setUser(userData);
    setToken(authToken);

    // Persist in localStorage - note: the actual user data structure from API
    // is already stored by SignInModal, we just need to ensure token consistency
    localStorage.setItem("auth_token", authToken);

    // Update role
    setCurrentRole(userData.role);
  };

  const logout = () => {
    setUser(null);
    setToken(null);

    // Clear all auth-related localStorage items
    localStorage.removeItem("user");
    localStorage.removeItem("auth_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user_role");
    localStorage.removeItem("password_state");

    // Clear dashboard filter keys
    sessionStorage.removeItem("case_dashboard_search");
    sessionStorage.removeItem("case_dashboard_page");
    sessionStorage.removeItem("case_dashboard_status");
    sessionStorage.removeItem("my_matches_search");
    sessionStorage.removeItem("my_matches_page");
    sessionStorage.removeItem("my_matches_status");
    sessionStorage.removeItem("missed_cases_search");
    sessionStorage.removeItem("missed_cases_page");
    
    sessionStorage.removeItem("resolveId");
    sessionStorage.removeItem("resolve_session_data");
    sessionStorage.removeItem("current_case_id");
    sessionStorage.removeItem("password_notification_dismissed");
    // Reset role to guest
    setCurrentRole("Guest");
  };

  // Use useMemo to ensure isAuthenticated updates reactively
  const isAuthenticated = useMemo(() => {
    return !!user && !!token;
  }, [user, token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        login,
        logout,
        refreshUserFromStorage,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Hook for easy usage
export function useAuth() {
  return useContext(AuthContext);
}
