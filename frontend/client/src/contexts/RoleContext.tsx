import { createContext, useContext, useState, ReactNode, useEffect } from "react";

// Add "navigator" to UserRole and allow dynamic roles
type UserRole = "Guest" | "Customer" | "Lawyer" | "Navigator" | string;

interface RoleContextType {
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
  refreshRoleFromStorage: () => void;
}

// Provide a default context value to avoid undefined errors
const defaultRoleContext: RoleContextType = {
  currentRole: "Guest",
  setCurrentRole: () => {},
  refreshRoleFromStorage: () => {},
};

const RoleContext = createContext<RoleContextType>(defaultRoleContext);

interface RoleProviderProps {
  children: ReactNode;
}

// Helper function to map role_code/role_name to UserRole
const mapUserRole = (roleCode?: string, roleName?: string): UserRole => {
  if (!roleCode && !roleName) return "Guest";

  // Prefer role_code, fallback to role_name
  const role = (roleCode || roleName || "");

  switch (role) {
    case "Customer":
      return "Customer";
    case "Lawyer":
      return "Lawyer";
    case "System":
    case "Navigator":
      return "Navigator";
    default:
      // If it's a custom role (like "navigator"), return as-is (lowercase)
      return role;
  }
};

export function RoleProvider({ children }: RoleProviderProps) {
  const [currentRole, setCurrentRoleState] = useState<UserRole>("Guest");

  // Function to refresh role from localStorage
  const refreshRoleFromStorage = () => {
    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        const parsedUser = JSON.parse(userData);
        // Accept both role_code and role_name, and allow custom roles like "Navigator"
        const mappedRole = mapUserRole(parsedUser.role_code, parsedUser.role_name);
        setCurrentRoleState(mappedRole);
        // Also persist the mapped role for quick access
        localStorage.setItem('user_role', mappedRole);
      } else {
        // No user data, set to guest
        setCurrentRoleState("Guest");
        localStorage.removeItem('user_role');
      }
    } catch (error) {
      setCurrentRoleState("Guest");
      localStorage.removeItem('user_role');
    }
  };

  // Initialize role from localStorage on mount
  useEffect(() => {
    refreshRoleFromStorage();
  }, []);

  // Listen for localStorage changes (for cross-tab synchronization)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'user' || e.key === 'user_role') {
        refreshRoleFromStorage();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  // Custom setCurrentRole that also persists to localStorage
  const setCurrentRole = (role: UserRole) => {
    setCurrentRoleState(role);
      if (role === "Guest") {
      localStorage.removeItem('user_role');
    } else {
      localStorage.setItem('user_role', role);
    }
  };

  return (
    <RoleContext.Provider value={{
      currentRole,
      setCurrentRole,
      refreshRoleFromStorage
    }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  return useContext(RoleContext);
} 