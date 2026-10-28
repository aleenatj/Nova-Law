import { useState, ReactNode, useContext } from "react";
import { Sidebar } from "@/components/sidebar/v1/Sidebar";
import { default as Button } from "@/components/ui/button/v1/Button";
import { Link, useLocation } from "wouter";
import { ProfileDropdown } from "./ProfileDropdown";
import { useRole } from "@/contexts/RoleContext";
import { ModalContext } from "@/contexts/ModalContext";
import { FormButton } from "@/utils/formComponents";
import { PasswordSetupNotification } from "./PasswordSetupNotification";

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  headerTitle?: string | ReactNode;
  headerSubtitle?: string;
  headerActions?: ReactNode;
  sidebarActions?: ReactNode;
  showBackButton?: boolean;
  backButtonLabel?: string;
  backButtonLink?: string;
  onBackClick?: () => void;
  caseNumber?: string;
}

export function Layout({
  children,
  showSidebar = true,
  headerTitle,
  headerSubtitle,
  headerActions,
  sidebarActions,
  showBackButton = false,
  backButtonLabel = "Back",
  backButtonLink,
  onBackClick,
  caseNumber,
}: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [location] = useLocation();
  const { currentRole } = useRole();
  
  // Safely access modal context - use useContext directly to avoid throwing error
  // if context is not available (e.g., during navigation or page transitions)
  const modalContext = useContext(ModalContext);
  const openModal = modalContext?.openModal as ((type: "signin" | "signup", resolveId?: string) => void) | undefined;

  const handleSignInClick = () => {
    if (openModal) {
      openModal("signin");
    } else {
      // Fallback: redirect to home page if modal context not available
      window.location.href = "/";
    }
  };

  const getDefaultTitle = () => {
    if (location.startsWith("/case-dashboard")) return "Cases";
    if (location.startsWith("/missed-cases")) return "Missed Cases";
    if (location.startsWith("/my-matches")) return "My Matches";
    if (location === "/case/new") return "New Case";
    if (location.startsWith("/case/")) return "Reference number";
    if (location.startsWith("/resolve-dashboard")) return "My Nova Recommendations";
    if (location.startsWith("/resolve")) return "Case Resolution";
    if (location === "/engage-dashboard") return "Engage Dashboard";
    if(location.startsWith("/engage/")) return "Nova Engage";
    if (location === "/engage-form") return "Nova Engage";
    if (location === "/organisations") return "Organisations Management";
    if (location === "/experts") return "Experts Management";
    return "NovaAI";
  };

  const getDefaultSubtitle = () => {
    if (location.startsWith("/case-dashboard"))
      return "Track and manage your legal case submissions";
    if (location.startsWith("/missed-cases")) return "View the cases that you have missed";
    if (location.startsWith("/my-matches")) return "View your matched cases";
    if (location === "/case/new") return "Submit a new legal case for review";
    if (location.startsWith("/case/")) return "";
    if (location.startsWith("/resolve-dashboard"))
      return "View your personalised guidance and the information you shared with us";
    if (location.startsWith("/resolve"))
      return "Answer questions to get legal guidance";
    if (location === "/engage-form")
      return "Complete your consultation preparation";
    if (location.startsWith("/engage/"))
      return "Complete your consultation preparation";
    if (location === "/organisations")
      return "Manage and oversee law firm partnerships and relationships";
    if (location === "/experts")
      return "Manage and oversee experts profiles and information";
    return "Your AI-powered legal assistant";
  };

  // Hide sidebar and profile dropdown for guests
  const isGuest = currentRole === "Guest";

  return (
    <>
      <div className="h-screen bg-novaNeutral-50 flex overflow-hidden">
        {showSidebar && (
          <>
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
              <div
                className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
                onClick={() => setSidebarOpen(false)}
              />
            )}

            {/* Sidebar */}
            <div
              className={`fixed inset-y-0 left-0 z-50 sm:w-[19rem] w-78 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 lg:flex-shrink-0 overflow-x-hidden overflow-y-auto ${
                sidebarOpen ? "translate-x-0" : "-translate-x-full"
              }`}
            >
              <Sidebar 
                onSignInClick={handleSignInClick} 
                sidebarActions={sidebarActions}
                onSidebarClose={() => setSidebarOpen(false)}
              />
            </div>
          </>
        )}

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Global Header */}
          <header className="bg-white border-b border-novaNeutral-100 px-1 py-2 sm:py-3 lg:px-6 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center sm:space-x-2 space-x-1">
                {showSidebar && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="lg:hidden"
                    onClick={() => setSidebarOpen(true)}
                  >
                    <i className="fas fa-bars text-xl"></i>
                  </Button>
                )}

                {/* Back button for specific pages */}
                {location.startsWith("/case/") && location !== "/case" && (() => {
                  // Hide back button if customer has a stored case.id (redirected from login)
                  const storedCaseId = sessionStorage.getItem("current_case_id");
                  if (storedCaseId && currentRole.toLowerCase() === "customer") {
                    return false;
                  }
                  return true;
                })() && (
                  <>
                    <Link 
                      href={(() => {
                        // For lawyers, check if case was opened from missed-cases or my-matches
                        if (currentRole === "Lawyer") {
                          const sourcePage = sessionStorage.getItem("case_source_page");
                          if (sourcePage === "/missed-cases") return "/missed-cases";
                          if (sourcePage === "/my-matches") return "/my-matches";
                          return "/case-dashboard";
                        }
                        return "/case-dashboard";
                      })()} 
                      className="lg:hidden"
                    >
                      <FormButton
                        variant="custom"
                        size="sm"
                        className="text-novaNeutral-600 focus:ring-0 focus:ring-offset-0 focus:outline-none hover:text-novaBlue-800 hover:underline"
                      >
                        <i className="fas fa-arrow-left"></i>
                      </FormButton>
                    </Link>
                    <Link 
                      href={(() => {
                        // For lawyers, check if case was opened from missed-cases or my-matches
                        if (currentRole === "Lawyer") {
                          const sourcePage = sessionStorage.getItem("case_source_page");
                          if (sourcePage === "/missed-cases") return "/missed-cases";
                          if (sourcePage === "/my-matches") return "/my-matches";
                          return "/case-dashboard";
                        }
                        return "/case-dashboard";
                      })()} 
                      className="hidden lg:block"
                    >
                      <FormButton
                        variant="custom"
                        size="sm"
                        className="text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none hover:text-novaBlue-800 hover:underline"
                      >
                        <i className="fas fa-arrow-left sm:mr-2 mr-2"></i>
                        Back
                      </FormButton>
                    </Link>
                  </>
                )}

                {/* Custom back button */}
                {showBackButton && backButtonLink && (
                  <>
                    <Link href={backButtonLink} className="lg:hidden">
                      <FormButton
                        variant="custom"
                        size="sm"
                        className="text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none hover:text-novaBlue-800 hover:underline"
                        onClick={onBackClick}
                      >
                        <i className="fas fa-arrow-left"></i>
                      </FormButton>
                    </Link>
                    <Link href={backButtonLink} className="hidden lg:block">
                    <FormButton
                        variant="custom"
                        size="sm"
                        onClick={onBackClick}
                        className="text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none hover:text-novaBlue-800 hover:underline"
                      >
                        <i className="fas fa-arrow-left mr-2"></i>
                        {backButtonLabel}
                      </FormButton>
                    </Link>
                  </>
                )}

                {/* Custom back button without link (uses onClick only) */}
                {currentRole !== "Guest" && showBackButton && !backButtonLink && onBackClick && (
                  <>
                    <FormButton
                      variant="custom"
                      size="sm"
                      className="lg:hidden text-novaNeutral-600 hover:text-novaBlue-800"
                      onClick={onBackClick}
                    >
                      <i className="fas fa-arrow-left"></i>
                    </FormButton>
                    <FormButton
                        variant="custom"
                        size="sm"
                        className="hidden lg:block text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none hover:text-novaBlue-800 hover:underline"
                        onClick={onBackClick}
                      >
                        <i className="fas fa-arrow-left mr-2"></i>
                      {backButtonLabel}
                    </FormButton>
                  </>
                )}

                <div
                  className={`flex flex-col xl:flex-row xl:items-center xl:gap-2 min-h-[2.5rem] sm:gap-0 gap-0
                    ${caseNumber ? "justify-center items-center" : "justify-start items-start"}`}
                >
                  <div className="flex flex-row items-center min-h-[2.5rem]">
                    <h1 className="sm:text-[16px] text-xs font-normal leading-tight whitespace-nowrap flex items-center py-0">
                      {headerTitle || getDefaultTitle()}
                    </h1>
                    {caseNumber && (
                      <div className="inline-block rounded px-2 py-[2px] sm:text-[16px] text-xs font-semibold text-novaNeutral-500">
                        {caseNumber}
                      </div>
                    )}
                  </div>
                  <span className="hidden sm:inline text-sm text-novaNeutral-500 font-normal">
                    {headerSubtitle || getDefaultSubtitle()}
                  </span>
                </div>
              </div>

              {location && location.startsWith("/case") && currentRole.toLowerCase() === "customer" && <div className="hidden sm:block font-semibold text-[16px] mr-[16%]">
                My Nova
              </div>}

              <div className="flex items-center gap-2">
                {/* Mobile Navigation Icons */}
                <div className="flex items-center gap-1 lg:hidden">
                  {location === "/case" && !isGuest && (
                    <Link href="/resolve">
                      <Button
                        size="sm"
                        className="bg-novaPrimary-500 hover:bg-novaPrimary-600 text-white px-2 py-1 text-xs"
                      >
                        <i className="fas fa-plus"></i>
                      </Button>
                    </Link>
                  )}
                </div>

                {/* Custom header actions */}
                {headerActions}

                {/* Profile Dropdown - only show for non-guests */}
                {!isGuest && <ProfileDropdown />}
              </div>
            </div>
          </header>

          {/* Password Setup Notification - hide close button on profile page */}
          <PasswordSetupNotification showCloseButton={!location.startsWith("/profile")} />

          {/* Page Content */}
          <main className="flex-1 flex flex-col min-h-0 bg-white overflow-y-auto overflow-x-visible"> {/* style={{ scrollbarGutter: 'stable' }} */}
            {children}
          </main>
        </div>
      </div>

    </>
  );
}
