import { CalendarWidget } from "./CalendarWidget";
import { Link, useLocation } from "wouter";
import { useRole } from "@/contexts/RoleContext";
import { Button } from "@/components/ui/button";
import React, { useState, useEffect } from "react";
import { ENGAGE_STEPS } from "@/config/engageConfig";
import { ENGAGE_ACTIVE_SECTION_EVENT, ENGAGE_NAVIGATE_SECTION_EVENT } from "@/pages/engage/engagePageIds";
import novaLogo from "@/assets/ui/nova_logo.png";
import { TimelineNavigationMenu } from "@/components/timeline/TimelineNavigationMenu";
import { useTimeline } from "@/contexts/TimelineContext";
import { NeedHelpSection } from "./NeedHelpSection";
const CRIB_SHEET_URL = import.meta.env.PUBLIC_ENV__CRIB_SHEET_URL as string;
const PROFESSIONAL_RESOURCES_URL = import.meta.env.PUBLIC_ENV__PROFESSIONAL_RESOURCES_URL as string;

interface SidebarProps {
  onSignInClick: () => void;
  sidebarActions?: React.ReactNode;
  onSidebarClose?: () => void;
}

export function Sidebar({ onSignInClick, sidebarActions, onSidebarClose }: SidebarProps) {
  const [location] = useLocation();
  const { currentRole } = useRole();
  const isGuest = currentRole === "Guest";
  const isCasePage = location.startsWith("/case/");
  const isEngageFormPage =
    location.startsWith("/engage/") || location === "/engage-form" || location.startsWith(sessionStorage.getItem("current_case_id") ? `/engage-form?case_id=${sessionStorage.getItem("current_case_id")}` : "/engage-form?");
  const [engageActiveStep, setEngageActiveStep] = useState(1);
  /** `null` until engage page applies GET: then only these step numbers are clickable. */
  const [engagePresentSteps, setEngagePresentSteps] = useState<number[] | null>(null);
  const showEngageStepsNav = isEngageFormPage && !isGuest;

  useEffect(() => {
    const read = (event: Event) => {
      const ce = event as CustomEvent<{
        section?: number;
        presentEngageSteps?: number[] | null;
      }>;
      const section = ce.detail?.section;
      const present = ce.detail?.presentEngageSteps;
      if (typeof section === "number" && section > 0) {
        setEngageActiveStep(section);
      }
      if (present !== undefined) {
        setEngagePresentSteps(present);
      }
    };
    window.addEventListener(ENGAGE_ACTIVE_SECTION_EVENT, read);
    return () => window.removeEventListener(ENGAGE_ACTIVE_SECTION_EVENT, read);
  }, []);
  
  // Get timeline data and effective role from context (only if available)
  let timelineData: any[] = [];
  let navigateToTimelineType: ((type: string) => void) | null = null;
  let effectiveRoleForTimeline: string = currentRole;
  try {
    const timeline = useTimeline();
    timelineData = timeline.timelineData;
    navigateToTimelineType = timeline.navigateToTimelineType;
    // Use effective role from context if available (for Navigator role switching), otherwise use currentRole
    effectiveRoleForTimeline = timeline.effectiveRole || currentRole;
  } catch (e) {
    // Context not available, that's okay - timeline navigation won't be shown
  }

  return (
    <>
      <div className="sm:w-[19rem] w-78 flex flex-col bg-white min-h-screen h-auto border-r border-novaNeutral-100">
        {/* Sidebar Header */}
        <div
          className="flex items-center justify-between px-8 py-2 border-b border-novaNeutral-100 cursor-pointer"
          // onClick={() => (window.location.href = "/")}
        >
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-opacity-100 rounded-lg flex items-center justify-center">
              <a href="/" className="flex items-center">
                <img src={novaLogo} alt="NovaAI" className="w-18 h-18" />
              </a>
            </div>
          </div>
        </div>

        {/* Navigation Menu - Show teaser for guests */}
        {isGuest ? (
          <div className="p-6 border-b border-novaNeutral-100">
            <div className="bg-novaNeutral-50 rounded-lg p-4 border border-novaNeutral-100">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-8 h-8 bg-novaNeutral-300 rounded-lg flex items-center justify-center">
                  <i className="fas fa-lock text-novaNeutral-500 text-sm"></i>
                </div>
                <div>
                  <p className="text-md text-novaNeutral-500">
                    Sign in to access
                  </p>
                </div>
              </div>

              <div className="space-y-2 opacity-60">
                {/* <div className="flex items-center space-x-3 px-3 py-2 rounded-lg bg-novaNeutral-100">
                  <i className="fas fa-home w-4 text-novaNeutral-400"></i>
                  <span className="text-sm font-medium text-novaNeutral-500">
                    Home
                  </span>
                </div> */}
                <div className="flex items-center space-x-3 px-3 py-2 rounded-full bg-novaNeutral-100">
                  <i className="fas fa-folder-open w-4 text-novaNeutral-400"></i>
                  <span className="text-sm font-medium text-novaNeutral-500">
                    My Cases
                  </span>
                </div>
                <div className="flex items-center space-x-3 px-3 py-2 rounded-full bg-novaNeutral-100">
                  <i className="fas fa-clipboard-list w-4 text-novaNeutral-400"></i>
                  <span className="text-sm font-medium text-novaNeutral-500">
                    Nova Recommendations
                  </span>
                </div>
                {/* <div className="flex items-center space-x-3 px-3 py-2 rounded-lg bg-novaNeutral-100">
                  <i className="fas fa-user-plus w-4 text-novaNeutral-400"></i>
                  <span className="text-sm font-medium text-novaNeutral-500">
                    Engage Sessions
                  </span>
                </div> */}
              </div>

              {/* Sign In Button */}
              <div className="mt-4 pt-3 border-t border-novaNeutral-200">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-sm font-normal shadow-md rounded-full text-novaPrimary-500 border-novaPrimary-700 hover:bg-novaPrimary-500 hover:text-white"
                  onClick={onSignInClick}
                >
                  <i className="fas fa-sign-in-alt mr-2"></i>
                  Sign In to Access
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <nav className="p-6">
              {/* Your steps - Show only on engage-form page; other nav items hidden while this is shown */}
              {showEngageStepsNav && (
                <div className="mb-4">
                  <div
                    className="w-full text-left text-novaNeutral-800 font-semibold px-4 py-2"
                    id="engage-steps-heading"
                  >
                    Your steps
                  </div>
                  <nav
                    id="engage-steps-nav"
                    className="flex flex-col gap-0.5 mt-1"
                    aria-labelledby="engage-steps-heading"
                  >
                    {ENGAGE_STEPS.map((step, idx) => {
                      const stepNum = idx + 1;
                      const isActive = stepNum === engageActiveStep;
                      const isDisabled =
                        engagePresentSteps !== null &&
                        !engagePresentSteps.includes(stepNum);
                      return (
                        <button
                          key={stepNum}
                          type="button"
                          disabled={isDisabled}
                          onClick={() => {
                            if (isDisabled) return;
                            window.dispatchEvent(
                              new CustomEvent(ENGAGE_NAVIGATE_SECTION_EVENT, {
                                detail: { section: stepNum },
                              })
                            );
                            onSidebarClose?.();
                          }}
                          className={`w-full text-left py-2 px-4 rounded-full text-sm transition-colors ${
                            isActive
                              ? "text-white bg-novaDarkOrange"
                              : isDisabled
                                ? "text-novaNeutral-300 cursor-not-allowed"
                                : "text-novaNeutral-700 hover:bg-novaNeutral-100"
                          }`}
                        >
                          {stepNum}. {step.title}
                        </button>
                      );
                    })}
                  </nav>
                </div>
              )}

            {!showEngageStepsNav && (
            <>
            <Link href="/case-dashboard">
                <div
                  className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                    (() => {
                      // For lawyers, check if case was opened from missed-cases or my-matches
                      if (currentRole.toLowerCase() === "lawyer" && location.startsWith("/case/")) {
                        const sourcePage = sessionStorage.getItem("case_source_page");
                        // If source was missed-cases or my-matches, don't highlight My Cases
                        if (sourcePage === "/missed-cases" || sourcePage === "/my-matches") {
                          return false;
                        }
                      }
                      return location === "/case-dashboard" ||
                        location === "/case-dashboard/" ||
                        location === "/case/new" ||
                        location.startsWith("/case/");
                    })()
                      ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white px-4 py-2 font-medium"
                      : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                  }`}
                >
                  <i className="fas fa-folder-open w-4"></i>
                  <span className="text-md">
                    {currentRole.toLowerCase() === "navigator"
                      ? "All Cases"
                      : currentRole.toLowerCase() === "customer"
                        ? "My Nova"
                        : "My Cases"}
                  </span>
                </div>
              </Link>
            <div className="">


              {/* Timeline Navigation - Show only on case pages, above menu items */}
              {isCasePage && !isGuest && timelineData.length > 0 && navigateToTimelineType && currentRole.toLowerCase() !== "navigator"  && currentRole.toLowerCase() !== "lawyer"  && (
                <TimelineNavigationMenu
                  timelineData={timelineData}
                  onNavigate={(type) => {
                    navigateToTimelineType(type);
                    onSidebarClose?.();
                  }}
                  role={effectiveRoleForTimeline}
                  currentUserRole={currentRole}
                  isCollapsible={true}
                  defaultCollapsed={true}
                />
              )}

              {/* <Link href="/dashboard">
                <div
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                    location === "/dashboard"
                      ? "bg-novaPrimary-500 text-white"
                      : "text-novaNeutral-700 hover:bg-novaNeutral-100"
                  }`}
                >
                  <i className="fas fa-home w-4"></i>
                  <span className="text-sm font-medium">Home</span>
                </div>
              </Link> */}
              {currentRole.toLowerCase() === "lawyer" && (
                <Link href="/my-matches">
                  <div
                    className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                      location === "/my-matches" ||
                      location.startsWith("/my-matches") ||
                      (location.startsWith("/case/") && sessionStorage.getItem("case_source_page") === "/my-matches")
                        ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                        : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                  }`}
                >
                    <i className="fa-solid fa-folder-open w-4"></i>
                    <span className="text-md">My Matches</span>
                  </div>
                </Link>
              )}
              
              {currentRole.toLowerCase() === "lawyer" && (
                <>
                  <Link href="/missed-cases">
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                        location === "/missed-cases" ||
                        (location.startsWith("/case/") && sessionStorage.getItem("case_source_page") === "/missed-cases")
                          ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                          : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                      }`}
                    >
                      <i className="fa-solid fa-folder-minus w-4"></i>
                      <span className="text-md">Missed Cases</span>
                    </div>
                  </Link>
                  <div className="border-t border-novaNeutral-100 my-2"></div>
                  <a
                    href={PROFESSIONAL_RESOURCES_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Opens professional resources in new tab"
                  >
                    <div className="flex mt-2 items-center space-x-2 px-4 py-2 rounded-full cursor-pointer transition-all duration-200 text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white">
                      <i className="fas fa-file-alt w-4"></i>
                      <span className="text-md">Professional Resources</span>
                    </div>
                  </a>
                  <div className="border-t border-novaNeutral-100 my-2"></div>
                </>
              )}
              {currentRole.toLowerCase() != "lawyer" && (
                <Link href="/resolve-dashboard">
                  <div
                    className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                      location === "/resolve-dashboard" ||
                      location.startsWith("/resolve")
                        ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                        : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                    }`}
                  >
                    <i className="fas fa-clipboard-list w-4"></i>
                    <span className="text-md whitespace-nowrap">{currentRole.toLowerCase() != "navigator" ? "My Nova Recommendations" : "Nova Recommendations"}</span>
                  </div>
                </Link>
              )}  
              {/* <Link href="/engage-dashboard">
                <div
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                    location === "/engage-dashboard" ||
                    location.startsWith("/engage")
                      ? "bg-novaPrimary-500 text-white"
                      : "text-novaNeutral-700 hover:bg-novaNeutral-100"
                  }`}
                >
                  <i className="fas fa-user-plus w-4"></i>
                  <span className="text-sm font-medium">Engage Sessions</span>
                </div>
              </Link> */}
              {currentRole.toLowerCase() === "navigator" && (
                <>
                  {/* Divider */}
                  <div className="border-t border-novaNeutral-100 my-2"></div>

                  {/* Experts */}
                  <Link href="/experts">
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                        location === "/experts"
                          ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                          : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                      }`}
                    >
                      <i className="fas fa-user-tie w-4"></i>
                      <span className="text-md">Experts</span>
                    </div>
                  </Link>

                  {/* Organisations */}
                  <Link href="/organisations">
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                        location === "/organisations"
                          ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                          : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                      }`}
                    >
                      <i className="fas fa-building w-4"></i>
                      <span className="text-md">Organisations</span>
                    </div>
                  </Link>

                  {/* Navigators */}
                  <Link href="/navigators">
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                        location === "/navigators"
                          ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                          : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                      }`}
                    >
                      <i className="fas fa-user-shield w-4"></i>
                      <span className="text-md">Navigators</span>
                    </div>
                  </Link>

                  {/* Nova Experts */}
                  <Link href="/nova-experts">
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                        location === "/nova-experts"
                          ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                          : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                      }`}
                    >
                      <i className="fas fa-user-graduate w-4"></i>
                      <span className="text-md">Nova Experts</span>
                    </div>
                  </Link>

                  {/* Feedback */}
                  <Link href="/feedback">
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 mb-1 rounded-full cursor-pointer transition-all duration-200 ${
                        location === "/feedback"
                          ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] shadow-md text-white font-medium"
                          : "text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
                      }`}
                    >
                      <i className="fas fa-comment-dots w-4"></i>
                      <span className="text-md">Feedback</span>
                    </div>
                  </Link>

                  {/* Divider */}
                  <div className="border-t border-novaNeutral-100 my-2"></div>

                  {/* Navigator Resources */}
                  <a
                    href={CRIB_SHEET_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Opens crib sheet in new tab"
                  >
                    <div className="flex mt-2 items-center space-x-2 px-4 py-2 rounded-full cursor-pointer transition-all duration-200 text-novaNeutral-700 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white">
                      <i className="fas fa-file-alt w-4"></i>
                      <span className="text-md">Navigator Resources</span>
                    </div>
                  </a>
                  

                  {/* Divider */}
                  <div className="border-t border-novaNeutral-100 my-2"></div>

                  <>{sidebarActions && (
                    <div className="xl:hidden flex flex-col gap-2 mt-2">
                      {sidebarActions}
                    </div>
                  )}</>
                </>
              )}
            </div>
            </>
            )}
          </nav>
        )}

        {/* Need Help Section - Show for customers on case pages or engage-form */}
        {(isCasePage || isEngageFormPage) && !isGuest && currentRole.toLowerCase() === "customer" && (
          <div className="mt-auto pt-6">
            <NeedHelpSection />
          </div>
        )}
        
        {/* Calendar Widget */}
        {/* <CalendarWidget /> Temporarily disabled */}
      </div>
    </>
  );
}
