import GlobalModal, { ModalType } from "@/components/modal/GlobalModal";
import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
  useCallback,
  useMemo,
} from "react";
import { setTokenExpiryHandler, tokenManager } from "@/lib/api";
import { useRole } from "./RoleContext";
import { useLocation } from "wouter";
import { clearRedirectAfterLogin, storeRedirectAfterLogin } from "@/utils/redirectAfterLogin";
import { useAuth } from "./AuthContext";

interface ModalContextType {
  openModal: (type: ModalType, resolveId?: string, invalidlink?: boolean, email?: string, user_id?: string) => void;
  closeModal: () => void;
  switchModal: (type: ModalType, resolveId?: string, invalidlink?: boolean, email?: string, user_id?: string) => void;
  isOpen: boolean;
  currentType: ModalType;
  resolveId?: string;
  invalidlink?: boolean;
  email?: string;
  user_id?: string;
}

export const ModalContext = createContext<ModalContextType | undefined>(undefined);

// Pages that are accessible to guest users (without authentication)
const GUEST_ACCESSIBLE_ROUTES = [
  "/",
  "/resolve",
  "/resolve-new",
];

// Check if a path is guest accessible
const isGuestAccessiblePage = (pathname: string): boolean => {
  // Check exact matches
  if (GUEST_ACCESSIBLE_ROUTES.includes(pathname)) {
    return true;
  }
  
  // Check if it's a resolve detail page (/resolve/:id)
  if (pathname.startsWith("/resolve/") || pathname.startsWith("/resolve-new")) {
    return true;
  }
  
  return false;
};

export function ModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentType, setCurrentType] = useState<ModalType>("signin");
  const [resolveId, setResolveId] = useState<string | undefined>(undefined);
  const [invalidlink, setInvalidlink] = useState<boolean | undefined>(undefined);
  const [email, setEmail] = useState<string | undefined>(undefined);
  const [user_id, setUser_id] = useState<string | undefined>(undefined);
  const { refreshRoleFromStorage } = useRole();
  const [location, setLocation] = useLocation();
  const { isAuthenticated } = useAuth();

  const openModal = useCallback((type: ModalType, resolveIdParam?: string, state?: boolean, emailParam?: string, user_idParam?: string) => {
    setCurrentType(type);
    setResolveId(resolveIdParam);
    setInvalidlink(state);
    setEmail(emailParam);
    setUser_id(user_idParam);
    setIsOpen(true);
    
    // Store current URL for redirect after login if opening signin modal
    // Only store if user is not authenticated (prevents re-storing after successful login)
    if (type === "signin" && !isAuthenticated) {
      storeRedirectAfterLogin(undefined, location);
    }
  }, [isAuthenticated]);

  const closeModal = useCallback(() => {
    setIsOpen(false);
    setInvalidlink(undefined);
    setEmail(undefined);
    setUser_id(undefined);
    
    // If this was a token expiry sign-in and user closed without signing in
    if ((window as any).isTokenExpirySignIn && !tokenManager.getAccessToken()) {
      const currentPath = window.location.pathname;
      
      // Only redirect if the current page requires authentication
      if (!isGuestAccessiblePage(currentPath)) {
        // User closed the modal without signing in - redirect to home page
        (window as any).isTokenExpirySignIn = false;
        // Clear the stored redirect URL since user closed without logging in
        clearRedirectAfterLogin();
        window.location.href = "/";
        return;
      }
      
      // Current page is guest-accessible, just clear the flag and stay
      (window as any).isTokenExpirySignIn = false;
      // Clear the stored redirect URL since user closed without logging in
      clearRedirectAfterLogin();
      refreshRoleFromStorage();
      return;
    }
    
    // Clear the flag if user successfully signed in
    (window as any).isTokenExpirySignIn = false;

    // Clear the stored redirect URL if:
    // 1. The modal being closed is the signin modal AND
    // 2. User is NOT authenticated (they closed without logging in)
    // If user is authenticated, the redirect URL will be cleared in SignInForm after successful redirect
    if (currentType === "signin" && !isAuthenticated) {
      clearRedirectAfterLogin();
    }
    
    // Refresh role state when modal is closed to ensure UI reflects current auth state
    refreshRoleFromStorage();
  }, [refreshRoleFromStorage, currentType, isAuthenticated]);

  const switchModal = useCallback((type: ModalType, resolveIdParam?: string, state?: boolean, emailParam?: string, user_idParam?: string) => {
    setCurrentType(type);
    if (resolveIdParam !== undefined) {
      setResolveId(resolveIdParam);
    }
    if (state !== undefined) {
      setInvalidlink(state);
    }
    if (emailParam !== undefined) {
      setEmail(emailParam);
    }
    if (user_idParam !== undefined) {
      setUser_id(user_idParam);
    }
    setIsOpen(true); // Ensure modal stays open when switching
  }, []);

  // Handle /login route - open modal and remove /login from URL
  useEffect(() => {
    if (location === "/login" || location === "/login/") {
      // Store redirect URL if user came from another page (check referrer or query param)
      const urlParams = new URLSearchParams(window.location.search);
      const redirectUrl = urlParams.get("redirect");
      if (redirectUrl) {
        storeRedirectAfterLogin(redirectUrl);
      }
      // Open the login modal
      openModal("signin");
      // Remove /login from URL by redirecting to home
      setLocation("/");
    }
  }, [location, openModal, setLocation]);

  // Register token expiry handler
  useEffect(() => {
    setTokenExpiryHandler(() => {
      (window as any).isTokenExpirySignIn = true;
      // Store current URL before opening modal (openModal will also store, but this ensures it's stored even if modal is already open)
      // Use current location from routing library
      storeRedirectAfterLogin(undefined, location);
      
      // Navigate to login page so URL reflects login state
      // Only navigate if we're not already on /login or / (to avoid unnecessary navigation)
      if (location !== "/login" && location !== "/") {
        window.location.href = "/login";
        return; // Exit early since we're navigating away
      }
      
      openModal("signin");
    });

    // Listen for test events
    const handleTokenExpired = () => {
      (window as any).isTokenExpirySignIn = true;
      // Store current URL before opening modal
      // Use current location from routing library
      storeRedirectAfterLogin(undefined, location);
      
      // Navigate to login page so URL reflects login state
      // Only navigate if we're not already on /login or / (to avoid unnecessary navigation)
      if (location !== "/login" && location !== "/") {
        window.location.href = "/login";
        return; // Exit early since we're navigating away
      }
      
      openModal("signin");
    };

    window.addEventListener("tokenExpired", handleTokenExpired);

    return () => {
      window.removeEventListener("tokenExpired", handleTokenExpired);
    };
  }, [openModal, location]);

  const contextValue = useMemo(
    () => ({ openModal, closeModal, switchModal, isOpen, currentType, resolveId, invalidlink, email, user_id }),
    [openModal, closeModal, switchModal, isOpen, currentType, resolveId, invalidlink, email, user_id]
  );

  return (
    <ModalContext.Provider value={contextValue}>
      {children}
      <GlobalModal
        isOpen={isOpen}
        onClose={closeModal}
        type={currentType}
        onSuccess={closeModal}
        resolveId={resolveId}
        invalidlink={invalidlink}
        email={email}
        user_id={user_id}
      />
    </ModalContext.Provider>
  );
}

export function useModal() {
  const context = useContext(ModalContext);
  if (!context) throw new Error("useModal must be used within ModalProvider");
  return context;
}
