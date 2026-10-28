import React from "react";
import { useRole } from "@/contexts/RoleContext";
import { getResolveUrl } from "@/lib/utils";

const LandingButtons: React.FC = () => {
  // useRole may not be available during SSR (no PageWrapper on server)
  let currentRole = "Guest";
  try {
    const roleResult = useRole();
    currentRole = roleResult?.currentRole || "Guest";
  } catch {
    currentRole = "Guest";
  }
  
  const handleGetStartedClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (typeof window !== "undefined") {
      if (currentRole !== "Guest") {
        window.location.href = "/case-dashboard";
        return;
      }
      const url = await getResolveUrl();
      window.location.href = url;
    }
  };

  return (
    <div>
      <a 
        href="#"
        onClick={handleGetStartedClick}
        onKeyDown={(e) => {
          if (e.key === " ") {
            e.preventDefault();
            (e.currentTarget as HTMLAnchorElement).click();
          }
        }}
        className="bg-novaBlack text-white px-4 py-2 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-novaViolet-500 focus-visible:ring-offset-2"
      >
        Get started
      </a>
    </div>
  );
};

export default LandingButtons;