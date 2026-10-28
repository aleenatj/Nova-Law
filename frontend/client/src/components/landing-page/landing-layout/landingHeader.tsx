import React, { useContext } from "react";
import NovaLogo from "@/assets/landingpage/Logo.png";
import HeaderGradient from "@/assets/landingpage/header-gradiant.png";
import MenuIcon from "@/assets/landingpage/headerhamburger.svg";
import { ModalContext } from "@/contexts/ModalContext";
import { useAuth } from "@/contexts/AuthContext";
import { ProfileDropdown } from "@/components/layout/v1/ProfileDropdown";
import { useRole } from "@/contexts/RoleContext";
import BackgroundGradientMobile from "@/assets/landingpage/mobilesidebargradient.webp";
import { getResolveUrl } from "@/lib/utils";

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

const LandingHeader: React.FC<LandingHeaderProps> = ({ hidenavs = false, onGetStartedClick }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const [isLawyersDropdownOpen, setIsLawyersDropdownOpen] = React.useState(false);
  const mobileNavRef = React.useRef<HTMLDivElement>(null);
  
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
  
  const toggleMobileMenu = () => setIsMobileMenuOpen((prev) => !prev);
  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  // Remove mobile nav from tab order when closed so Section1 Get started gets focus after header
  React.useEffect(() => {
    const el = mobileNavRef.current;
    if (!el) return;
    if (isMobileMenuOpen) {
      el.removeAttribute("inert");
    } else {
      el.setAttribute("inert", "");
    }
  }, [isMobileMenuOpen]);
  const handleLoginClick = () => {
    if (openModal) {
      openModal("signin");
    }
    closeMobileMenu();
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

  const handleMobileGetStartedClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    closeMobileMenu();
    
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
      className="bg-cover bg-white bg-center bg-no-repeat sticky top-0 z-50"
      style={{ backgroundImage: `url(${HeaderGradient})` }}
    >
      <div className="flex items-center justify-between max-w-[1400px] mx-auto py-2 px-3">
        <div className="flex items-center">
            <a href="/" className="flex items-center">
              <img src={NovaLogo} alt="Nova logo" className="h-[66px]" />
            </a>
            {!hidenavs && <nav className="hidden text-novaBlack md:flex items-center ml-10 gap-2 lg:gap-8" aria-label="Main navigation">
            {navLinks.map(({ label, href }) => (
                <a key={label} href={href}
                className="relative text-novaBlack transition-colors duration-300 ease-in-out
               after:content-[''] after:absolute after:left-0 after:-bottom-1 after:w-0 after:h-[1.5px]
               after:bg-black after:transition-all after:duration-300 hover:after:w-full">
                {label}
                </a>
            ))}
            <div 
              className="relative"
              onMouseEnter={() => setIsLawyersDropdownOpen(true)}
              onMouseLeave={() => setIsLawyersDropdownOpen(false)}
            >
              <button 
                onClick={() => setIsLawyersDropdownOpen(!isLawyersDropdownOpen)}
                className="relative text-novaBlack transition-colors duration-300 ease-in-out
               after:content-[''] after:absolute after:left-0 after:-bottom-1 after:w-0 after:h-[1.5px]
               after:bg-black after:transition-all after:duration-300 hover:after:w-full">
                Nova for Professionals
              </button>
              {isLawyersDropdownOpen && (
                <div 
                  className="absolute top-full left-0 pt-2 bg-transparent"
                  onMouseEnter={() => setIsLawyersDropdownOpen(true)}
                  onMouseLeave={() => setIsLawyersDropdownOpen(false)}
                >
                  <div className="bg-[#fff8f5] border border-[#fee9e1] rounded-lg shadow-lg py-2 min-w-[240px]">
                    <a href="https://novaforprofessionals.novalaw.co.uk/" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 hover:bg-[#fee9e1] cursor-pointer">Nova Engage</a>
                    <a href="/become-a-nova-professional" className="block px-4 py-2 hover:bg-[#fee9e1] cursor-pointer">Become a Nova Professional</a>
                  </div>
                </div>
              )}
            </div>
            </nav>}
        </div>
        <div className="hidden md:flex items-center gap-3">
        {!isAuthenticated && (
          <button
            type="button"
            onClick={() => openModal?.("signin")}
            className="text-novaBlack border border-novaBlack rounded-full px-4 py-1 hover:shadow-lg transition-all duration-300 hover:bg-novaBlack hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
          >
            Log in
          </button>
        )}
          <a
            href={isAuthenticated ? "/case-dashboard" : "#"}
            onClick={handleGetStartedClick}
            onKeyDown={(e) => {
              if (e.key === " ") {
                e.preventDefault();
                (e.currentTarget as HTMLAnchorElement).click();
              }
            }}
            className="text-white bg-novaBlack rounded-full px-4 py-1 hover:shadow-lg transition-all duration-300 hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471] focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
          >
            {!isAuthenticated ? "Get started" : "My Account"}
          </a>
          {isAuthenticated && (
            <ProfileDropdown />
          )}
        </div>
        <div className="md:hidden flex items-center gap-2">
          {isAuthenticated && <ProfileDropdown />}
          <button
            type="button"
            onClick={toggleMobileMenu}
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-nav"
            className="rounded-full p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaViolet-500"
          >
            <img src={MenuIcon} alt="Open menu" className="h-9 w-9" />
          </button>
        </div>
      </div>
      <div
        ref={mobileNavRef}
        id="mobile-nav"
        className={`fixed inset-0 z-[60] flex flex-col gap-16 bg-[#FCF2FF] px-6 py-8 items-center bg-no-repeat transition-all duration-300 ease-in-out ${
          isMobileMenuOpen ? "translate-x-0 opacity-100" : "translate-x-full opacity-0 pointer-events-none"
        }`}
        role="dialog"
        aria-modal={isMobileMenuOpen}
        aria-hidden={!isMobileMenuOpen}
        style={{ backgroundImage: `url(${BackgroundGradientMobile})` }}
      >
        <div className="flex items-center justify-between w-full">
          <img src={NovaLogo} alt="Nova logo" className="h-14" />
          <button
            type="button"
            onClick={closeMobileMenu}
            className="flex h-12 w-12 items-center justify-center rounded-full border border-novaBlack text-lg text-novaBlack focus:outline-none focus-visible:ring-2 focus-visible:ring-novaViolet-500"
            aria-label="Close menu"
          >
            X
          </button>
        </div>
        <nav className="flex flex-col items-center justify-center gap-6 text-center text-lg text-novaBlack" aria-label="Mobile navigation">
          {navLinks.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              onClick={closeMobileMenu}
              className="transition-colors duration-300 ease-in-out hover:text-novaViolet-500"
            >
              {label}
            </a>
          ))}
          <div className="flex flex-col items-center gap-3">
            <div className="text-novaBlack font-medium">Nova for Professionals</div>
            <div className="flex flex-col gap-3">
              <a
                href="https://novaforprofessionals.novalaw.co.uk/"
                target="_blank"
                rel="noopener noreferrer"
                onClick={closeMobileMenu}
                className="text-base transition-colors duration-300 ease-in-out hover:text-novaViolet-500"
              >
                Nova Engage
              </a>
              <a
                href="/become-a-nova-professional"
                onClick={closeMobileMenu}
                className="text-base transition-colors duration-300 ease-in-out hover:text-novaViolet-500"
              >
                Become a Nova Professional
              </a>
            </div>
          </div>
        </nav>
        <div className="flex flex-col items-center gap-4 w-[60%]">
          {!isAuthenticated && (
            <button
              type="button"
              onClick={handleLoginClick}
              className="w-full max-w-xs rounded-full border border-novaBlack px-6 py-2 text-center text-base text-novaBlack hover:bg-novaBlack hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-novaViolet-500 focus-visible:ring-offset-2"
            >
              Log in
            </button>
          )}
          <a
            href="#"
            onClick={handleMobileGetStartedClick}
            onKeyDown={(e) => {
              if (e.key === " ") {
                e.preventDefault();
                (e.currentTarget as HTMLAnchorElement).click();
              }
            }}
            className="w-full max-w-xs rounded-full bg-novaBlack px-6 py-2 text-center text-base font-medium text-white hover:bg-linear-gradient(90deg,#9A00D2 0%, #F41471 100%) focus:outline-none focus-visible:ring-2 focus-visible:ring-novaViolet-500 focus-visible:ring-offset-2"
          >
            {!isAuthenticated ? "Get started" : "My Account"}
          </a>
        </div>
      </div>
    </header>
  );
};

export default LandingHeader;
