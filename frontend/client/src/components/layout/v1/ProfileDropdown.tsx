import { useState, useRef, useEffect } from "react";
import { useLocation } from "wouter";
import { default as Button } from "@/components/ui/button/v1/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useRole } from "@/contexts/RoleContext";
import { useWebSocket } from "@/contexts/WebSocketContext";
import { tokenManager } from "@/lib/api";

export type ProfileDropdownProps = {
  /** When true, navigate back to the current URL after sign out instead of `/`. */
  preservePathOnSignOut?: boolean;
};

export function ProfileDropdown({ preservePathOnSignOut = false }: ProfileDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { user, logout: authLogout, isAuthenticated } = useAuth();
  const { refreshRoleFromStorage, currentRole } = useRole();
  const { isConnected } = useWebSocket();
  const [location, setLocation] = useLocation();

  // Generate user display data from auth context
  const displayName = user?.name || "Guest User";
  const displayEmail = user?.email || "guest@example.com";
  const displayRoleName = currentRole;
  const displayPhotoUrls = user?.photo_urls;
  const displayInitials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const signOutTargetPath = () => {
    if (
      preservePathOnSignOut &&
      typeof window !== "undefined" &&
      window.location.pathname
    ) {
      return `${window.location.pathname}${window.location.search}${window.location.hash}`;
    }
    return "/";
  };

  const handleLogout = () => {
    const nextPath = signOutTargetPath();
    try {
      // Clear tokens using tokenManager (this also clears user data)
      tokenManager.clearTokens();

      // Clear auth context state
      authLogout();

      // Refresh role context to ensure it's set to guest
      refreshRoleFromStorage();

      // Clear any additional app state if needed
      localStorage.removeItem("nova_app_state");
      sessionStorage.removeItem("resolveId");
      sessionStorage.removeItem("resolve_session_data");
      sessionStorage.removeItem("current_case_id");
      setLocation(nextPath);
      // Close dropdown
      setIsOpen(false);
    } catch (error) {
      console.error("Error during logout:", error);
      // Still attempt to clear everything even if there's an error
      localStorage.clear();
      setLocation(nextPath);
    }
  };

  const handleViewProfile = () => {
    setLocation("/profile");
  };

  // Don't render if user is not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Profile Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="relative h-9 w-9 rounded-full p-0 hover:bg-novaNeutral-100 flex items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:!ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
      >
        {displayPhotoUrls && displayPhotoUrls.thumbnail ? (
          <img
            src={displayPhotoUrls.thumbnail}
            alt={displayName}
            className="h-8 w-8 rounded-full object-cover transition-transform duration-150 hover:scale-110 hover:shadow-lg"
          />
        ) : (
          <div className="h-8 w-8 rounded-full bg-novaPrimary-500 flex items-center justify-center text-white text-sm font-medium">
            {displayInitials}
          </div>
        )}

        {/* Online Status Indicator */}
        <div className={`absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white ${
          isConnected ? "bg-novaSuccess-500" : "bg-novaNeutral-400"
        }`}></div>
      </Button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-novaNeutral-200 z-[100]">
          {/* User Info Section */}
          <div className="p-4 border-b border-novaNeutral-100">
            <div className="flex items-center gap-3">
              {displayPhotoUrls && displayPhotoUrls.thumbnail ? (
                <img
                  src={displayPhotoUrls.thumbnail}
                  alt={displayName}
                  className="h-10 w-10 rounded-full object-cover"
                />
              ) : (
                <div className="h-10 w-10 rounded-full bg-novaPrimary-500 flex items-center justify-center text-white font-medium">
                  {displayInitials}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-1 text-sm">
                  <span className="font-medium text-novaNeutral-900 truncate">
                    {displayName}
                  </span>
                  {(displayRoleName.toLowerCase() === "lawyer" || displayRoleName.toLowerCase() === "navigator") && (
                    <span className="text-novaNeutral-600 font-normal whitespace-nowrap text-xs">
                      ({displayRoleName})
                    </span>
                  )}
                </div>
                <p className="text-xs text-novaNeutral-500 truncate mt-0.5">
                  {displayEmail}
                </p>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="py-2">
            <button
              onClick={handleViewProfile}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-novaNeutral-700 hover:bg-novaNeutral-100 transition-colors"
            >
              <i className="fas fa-user text-novaNeutral-500 w-4"></i>
              <span>Profile</span>
            </button>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            >
              <i className="fas fa-sign-out-alt text-red-500 w-4"></i>
              <span>Sign Out</span>
            </button>
          </div>

          {/* Footer */}
          <div className="border-t border-novaNeutral-100 p-3">
            <div className="flex justify-end">
              <div className="flex items-center gap-1 text-xs text-novaNeutral-400">
                <span className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-novaSuccess-500" : "bg-novaNeutral-400"
                }`} title="WebSocket status"></span>
                <span title="WebSocket">
                  {isConnected ? "Online" : "Offline"}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
