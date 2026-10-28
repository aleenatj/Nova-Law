import React, { useContext } from "react";
import NovaLogo from "@/assets/landingpage/Logo.png";
import HeaderGradient from "@/assets/landingpage/header-gradiant.png";
import { ModalContext } from "@/contexts/ModalContext";
import { useAuth } from "@/contexts/AuthContext";
import { ProfileDropdown } from "@/components/layout/v1/ProfileDropdown";
import { useRole } from "@/contexts/RoleContext";
import { cn, getResolveUrl } from "@/lib/utils";
import arrowRight from "@/assets/landingpage/arrow-right.webp";
import arrowRightWhite from "@/assets/landingpage/arrow-right-white.webp";
import profileUserIcon from "@/assets/landingpage/profileuser.svg";

const navLinks = [
  { label: "How Nova works", href: "/#how-nova-works" },
  { label: "Our results", href: "/#our-results" },
  { label: "About us", href: "/#about-us" },
  { label: "FAQs", href: "/#faq" },
];

interface LandingHeaderProps {
  hidenavs?: boolean;
  onGetStartedClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void | Promise<void>;
}

interface GetStartedCtaProps {
  isAuthenticated: boolean;
  onClick: (e: React.MouseEvent<HTMLAnchorElement>) => void | Promise<void>;
  className?: string;
  /** When true, guests see "Get started" instead of the long headline (e.g. mobile header). */
  shortGuestLabel?: boolean;
}

const GetStartedCta: React.FC<GetStartedCtaProps> = ({
  isAuthenticated,
  onClick,
  className,
  shortGuestLabel = false,
}) => (
  <a
    href={isAuthenticated ? "/case-dashboard" : "#"}
    onClick={onClick}
    className={cn(
      "group relative inline-flex items-center justify-center overflow-hidden rounded-full px-4 text-black shadow-none transition-shadow duration-300 hover:shadow-lg",
      shortGuestLabel ? "py-2" : "py-3",
      className
    )}
  >
    <span
      className="pointer-events-none absolute inset-0 bg-novaYellow transition-opacity duration-500 ease-in-out group-hover:opacity-0"
      aria-hidden
    />
    <span
      className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#9A00D2] to-[#F41471] opacity-0 transition-opacity duration-500 ease-in-out group-hover:opacity-100"
      aria-hidden
    />
    <span className="relative z-10 inline-flex flex-wrap items-center justify-center gap-2 text-center text-[16px] sm:text-lg transition-colors duration-500 ease-in-out group-hover:text-white">
      {!isAuthenticated
        ? shortGuestLabel
          ? "Get started"
          : "Get my personalised recommendation"
        : "My Account"}
      <span className="relative block h-6 w-6 shrink-0" aria-hidden>
        <img
          src={arrowRight}
          alt=""
          className="pointer-events-none absolute left-1/2 top-1/2 h-6 w-6 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain object-center transition-opacity duration-300 group-hover:opacity-0"
        />
        <img
          src={arrowRightWhite}
          alt=""
          className="pointer-events-none absolute left-1/2 top-1/2 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain object-center opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        />
      </span>
    </span>
  </a>
);

const ConversionHeader: React.FC<LandingHeaderProps> = ({ hidenavs = false, onGetStartedClick }) => {
  const [isLawyersDropdownOpen, setIsLawyersDropdownOpen] = React.useState(false);
  
  // Safely get contexts - may not be available during SSR (no PageWrapper on server)
  let modalContext: any = null;
  let openModal: ((type: string) => void) | undefined = undefined;
  let isAuthenticated = false;
  let currentRole = "Guest";
  
  try {
    modalContext = useContext(ModalContext);
    openModal = modalContext?.openModal;
  } catch {
    // ModalContext not available during SSR
  }
  
  try {
    const authResult = useAuth();
    isAuthenticated = authResult?.isAuthenticated || false;
  } catch {
    // AuthContext not available during SSR
  }
  
  try {
    const roleResult = useRole();
    currentRole = roleResult?.currentRole || "Guest";
  } catch {
    // RoleContext not available during SSR
  }
  
  const handleLoginClick = () => {
    if (openModal) {
      openModal("signin");
    }
  };

  const handleGetStartedClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    
    if (typeof window === "undefined") return;
    
    // Default behavior for non-guest users
    if (currentRole !== "Guest") {
      window.location.href = "/case-dashboard";
      return;
    }
    
    // For guest users: use custom handler if provided, otherwise default behavior
    if (onGetStartedClick) {
      await onGetStartedClick(e);
      return;
    }
    
    // Default behavior for guest users
    const url = await getResolveUrl();
    window.location.href = url;
  };

  return (
    <header
      className="top-0 z-50"
      // style={{ backgroundImage: `url(${HeaderGradient})` }}
    >
      <div className="flex items-center justify-between max-w-[1500px] mx-auto py-2 px-3">
        <div className="flex items-center">
            <a href="/" className="flex items-center">
              <img src={NovaLogo} alt="Nova logo" className="h-[66px]" />
            </a>
        </div>
        <div className="hidden md:flex items-center gap-4">
        {!isAuthenticated && (
          <button
            type="button"
            onClick={() => openModal?.("signin")}
            className="text-novaBlack text-lg px-1 py-[0.2px] transition-all duration-300 border-b border-novaBlack"
          >
            Log in
          </button>
        )}
          <GetStartedCta isAuthenticated={isAuthenticated} onClick={handleGetStartedClick} />
          {isAuthenticated && <ProfileDropdown preservePathOnSignOut />}
        </div>
        <div className="md:hidden flex min-w-0 flex-1 items-center justify-end gap-2 pl-2">
          {!isAuthenticated && (
            // <button
            //   type="button"
            //   onClick={handleLoginClick}
            //   className="shrink-0 rounded-full border border-novaBlack px-6 py-2 text-center text-base text-novaBlack hover:bg-novaBlack hover:text-white"
            // >
            //   Log in
            // </button>
            <>
            <img
              src={profileUserIcon}
              alt=""
              className="h-[17px] w-[15px] shrink-0"
              aria-hidden
            />
            <button
              type="button"
              onClick={handleLoginClick}
              className="text-novaBlack text-[16px] sm:text-lg px-1 py-[0.2px] transition-all duration-300 border-b border-novaBlack"
            >
                Log in
            </button>
            </>
          )}
          <GetStartedCta
            isAuthenticated={isAuthenticated}
            onClick={handleGetStartedClick}
            className="min-w-0 max-w-full shrink"
            shortGuestLabel
          />
          {isAuthenticated && <ProfileDropdown preservePathOnSignOut />}
        </div>
      </div>
    </header>
  );
};

export default ConversionHeader;
