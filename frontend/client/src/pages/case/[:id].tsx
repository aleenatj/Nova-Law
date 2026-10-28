import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParams, useLocation } from "wouter";
import { Layout } from "../../components";
import { useRole } from "../../contexts/RoleContext";
import { useAuth } from "../../contexts/AuthContext";
import { TimelineSidebar } from "../../components/timeline/timelineSidebar";
import { TimelineActionBar } from "../../components/timeline/TimelineActionBar";
import InterestedLawyersPopUp from "../../components/timeline/InterestedLawyersPopUp";
import ReviewProfilesModal from "../../components/timeline/ReviewProfilesModal";
import { useTimeline } from "@/contexts/TimelineContext";
import { CustomSelect } from "../../components/ui/select";
import { api, ApiError } from "../../lib/api";
import {
  TimelineItemType,
  CaseDetailsActionButtons,
  InterestedLawyerType,
  LawyerProfileDisplayType,
  CaseDetailsData,
  CaseDetailsApiResponse,
} from "../../lib/types";
import { useWebSocket } from "@/contexts/WebSocketContext";
import {
  toastManager,
  createSuccessToast,
  createErrorToast,
  createWarningToast,
  createInfoToast,
} from "@/utils/toasts";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import { FormButton } from "@/utils/formComponents";
import { formatCaseNumberForTitle } from "@/utils/pageTitle";
import { storeRedirectAfterLogin } from "@/utils/redirectAfterLogin";

// Types for API response
interface TimelineApiResponse {
  success: boolean;
  message: string;
  data: {
    timeline_data: TimelineItemType[];
    total_count: number;
  };
}

// Import all timeline components using import.meta.glob
const timelineComponents = import.meta.glob(
  "../../components/timeline/**/v*/index.tsx",
  { eager: true }
);

// Dynamic component loader hook
function useDynamicComponent(role: string, type: string, version: number) {
  const [Component, setComponent] = useState<React.ComponentType<any> | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadComponent = () => {
      try {
        setLoading(true);
        setError(null);

        // Construct the import path based on role, type, and version
        const importPath = `../../components/timeline/${role.toLowerCase()}/${type}/v${version}/index.tsx`;

        // Find the component in the globbed modules
        const module = timelineComponents[importPath] as any;

        if (!module) {
          throw new Error(
            `Timeline component not found: ${role}/${type}/v${version}`
          );
        }

        setComponent(() => module.default);
        setLoading(false);
      } catch (err) {
        setError(`Timeline component not found: ${role}/${type}/v${version}`);
        setLoading(false);
      }
    };

    loadComponent();
  }, [role, type, version]);

  return { Component, loading, error };
}

// Extracted outside CaseDetail to prevent unmount/remount on parent re-render (fixes popup-closing bug)
function TimelineItem({
  item,
  isLatest,
  effectiveRole,
}: {
  item: TimelineItemType;
  isLatest: boolean;
  effectiveRole: string;
}) {
  const { Component, loading, error } = useDynamicComponent(
    effectiveRole,
    item.timeline_type_name,
    item.version
  );

  if (loading) {
    return (
      <div className="p-4 bg-novaNeutral-50 rounded-lg border border-novaNeutral-200 animate-pulse">
        <div className="h-4 bg-novaNeutral-200 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-novaNeutral-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (error || !Component) {
    return null;
  }

  return <Component timelineData={item} isLatest={isLatest} />;
}

export default function CaseDetail() {
  const params = useParams();
  const caseNo = params.id;
  const [, setLocation] = useLocation();
  const { currentRole } = useRole();
  const { user, isAuthenticated } = useAuth();
  const { subscribe } = useWebSocket();
  const { setTimelineData: setContextTimelineData, setNavigateHandler, setRefreshTimelineHandler, setRefreshCaseDetailsHandler, setEffectiveRole: setContextEffectiveRole } = useTimeline();

  // State for timeline data
  const [timelineData, setTimelineData] = useState<TimelineItemType[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [caseNumber, setCaseNumber] = useState<string | null>(null);

  // Redirect logged-out users to /login immediately (after brief delay so auth can restore from localStorage)
  const isAuthRef = useRef(isAuthenticated);
  isAuthRef.current = isAuthenticated;
  useEffect(() => {
    const t = setTimeout(() => {
      if (!isAuthRef.current) {
        storeRedirectAfterLogin();
        setLocation("/login");
      }
    }, 100);
    return () => clearTimeout(t);
  }, [isAuthenticated, setLocation]);

  // Set document title to case number when loaded (e.g. "Nova Case - #YQWCCV3")
  useEffect(() => {
    document.title = formatCaseNumberForTitle(caseNumber);
  }, [caseNumber]);

  // Pagination state
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const pageSize = 25;

  // State for case details and action buttons
  const [caseDetails, setCaseDetails] = useState<CaseDetailsData | null>(null);
  const [actionButtons, setActionButtons] =
    useState<CaseDetailsActionButtons | null>(null);
  const [caseDetailsLoading, setCaseDetailsLoading] = useState<boolean>(false);

  // State for modals
  const [showInterestedLawyersModal, setShowInterestedLawyersModal] =
    useState(false);
  const [interestedLawyers, setInterestedLawyers] = useState<
    InterestedLawyerType[]
  >([]);
  const [showReviewProfilesModal, setShowReviewProfilesModal] = useState(false);
  const [lawyers, setLawyers] = useState<LawyerProfileDisplayType[]>([]);
  const [modalLoading, setModalLoading] = useState(false);

  // State for role switching (Navigator feature)
  const [selectedRoleCode, setSelectedRoleCode] = useState<string | null>(null);
  const [selectedLawyerId, setSelectedLawyerId] = useState<string | null>(null);
  const [matchedLawyers, setMatchedLawyers] = useState<Array<{ lawyer_id: string; lawyer_name: string }>>([]);

  // Ref for the main timeline container
  const timelineContainerRef = useRef<HTMLDivElement>(null);
  
  // Refs for timeline items by type for scroll navigation
  const timelineItemRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Track last data source update (to distinguish between websocket and API pagination)
  const lastUpdateSource = useRef<"websocket" | "api" | null>(null);

  // --- SCROLL: Track if it's the initial timeline fetch for autoscroll
  const isInitialLoadDone = useRef<boolean>(false);

  // State for refresh loading
  const [refreshing, setRefreshing] = useState(false);

  // Determine the effective role for rendering components
  // If Navigator has switched role, use the selected role; otherwise use current role
  const effectiveRole = currentRole === "Navigator" && selectedRoleCode 
    ? selectedRoleCode 
    : currentRole;

  // Compute the latest timeline item ID based on created_at timestamp
  const latestItemId = useMemo(() => {
    if (timelineData.length === 0) return null;
    return timelineData.reduce((latest, item) => {
      const latestTime = new Date(latest.created_at).getTime();
      const currentTime = new Date(item.created_at).getTime();
      return currentTime > latestTime ? item : latest;
    }, timelineData[0]).id;
  }, [timelineData]);

  // Check if action bar should be visible
  const hasActionButtons =
    actionButtons &&
    Object.values(actionButtons).some((value) => value === true);

  // Check if sidebar is displayed
  const isSidebarVisible = 
    currentRole.toLowerCase() !== "customer" && 
    currentRole.toLowerCase() !== "lawyer" &&
    selectedRoleCode?.toLowerCase() !== "customer" &&
    selectedRoleCode?.toLowerCase() !== "lawyer";

  // Handler for fetching interested lawyers
  const handleFetchInterestedLawyers = async () => {
    setModalLoading(true);
    try {
      const encodedCaseId = encodeURIComponent(caseNo || "");
      const response = (await api.get(
        `/v1/timeline/interested-lawyers?case_id=${encodedCaseId}`
      )) as any;

      if (response?.data) {
        let lawyers = [];
        if (Array.isArray(response.data.lawyers)) {
          lawyers = response.data.lawyers;
        } else if (Array.isArray(response.data)) {
          lawyers = response.data;
        } else if (Array.isArray(response.data.data)) {
          lawyers = response.data.data;
        } else {
          console.warn(
            "No valid lawyers array found in response:",
            response.data
          );
          lawyers = [];
        }

        setInterestedLawyers(lawyers);
        setShowInterestedLawyersModal(true);
      }
    } catch (error) {
      console.error("Error fetching interested lawyers:", error);
      const toast = createErrorToast(
        "Error",
        "Failed to fetch interested lawyers"
      );
      toastManager.addToast(toast);
    } finally {
      setModalLoading(false);
    }
  };

  // Handler for reviewing profiles
  const handleReviewProfiles = async () => {
    setModalLoading(true);
    try {
      const encodedCaseId = encodeURIComponent(caseNo || "");
      const response = await api.get(
        `/v1/timeline/matching-lawyers?case_id=${encodedCaseId}`
      );
      const isCaseNotified = Boolean((response as any)?.is_case_notified);
      const lawyers = Array.isArray((response as any)?.data)
        ? (response as any).data.map((lawyer: any) => ({
            ...lawyer,
            is_sent: isCaseNotified,
          }))
        : [];
      setLawyers(lawyers);
      setShowReviewProfilesModal(true);
    } catch (error) {
      console.error("Error fetching lawyers:", error);
      const toast = createErrorToast(
        "Error",
        "Failed to fetch lawyer profiles"
      );
      toastManager.addToast(toast);
    } finally {
      setModalLoading(false);
    }
  };
  const handleSendLawyers = (selectedLawyers: any[]) => {
    // TODO: Implement API call to send selected lawyers to customer
    setShowInterestedLawyersModal(false);
    fetchCaseDetails();
  };

  // Clear localStorage on mount and unmount
  useEffect(() => {
    // Clear on mount
    localStorage.removeItem('navigator_switched_lawyer_id');
    
    // Clear on unmount
    return () => {
      localStorage.removeItem('navigator_switched_lawyer_id');
    };
  }, []);

  // Only store in localStorage when Lawyer role is selected
  useEffect(() => {
    if (selectedRoleCode?.toLowerCase() === "lawyer" && selectedLawyerId) {
      localStorage.setItem('navigator_switched_lawyer_id', selectedLawyerId);
    } else {
      localStorage.removeItem('navigator_switched_lawyer_id');
    }
  }, [selectedLawyerId, selectedRoleCode]);

  // Auto-select first lawyer when Lawyer role is selected
  useEffect(() => {
    if (selectedRoleCode?.toLowerCase() === "lawyer" && matchedLawyers.length > 0 && !selectedLawyerId) {
      // Automatically select the first lawyer in the list
      setSelectedLawyerId(matchedLawyers[0].lawyer_id);
    }
  }, [selectedRoleCode, matchedLawyers, selectedLawyerId]);

  // Reset role selection if Lawyer role was selected but matched lawyers become empty
  useEffect(() => {
    if (selectedRoleCode?.toLowerCase() === "lawyer" && matchedLawyers.length === 0) {
      setSelectedRoleCode(null);
      setSelectedLawyerId(null);
    }
  }, [matchedLawyers, selectedRoleCode]);

  // Handler for role switching (Navigator feature)
  const handleRoleSwitch = (roleCode: string) => {
    setSelectedRoleCode(roleCode);
    // Reset lawyer selection when switching away from lawyer role
    if (roleCode.toLowerCase() !== "lawyer") {
      setSelectedLawyerId(null);
    }
    // Clear any previous error messages
    setError(null);
  };

  // Handler for lawyer selection
  const handleLawyerSelect = (lawyerId: string) => {
    setSelectedLawyerId(lawyerId);
    // Clear error when lawyer is selected
    setError(null);
  };

  // Handler for action button clicks
  const handleActionClick = async (action: string) => {

    switch (action) {
      case "send_to_customer":
        await handleFetchInterestedLawyers();
        break;
      case "review_profiles":
        await handleReviewProfiles();
        break;
      case "raise_interest":
        break;
      default:
    }
  };

  // Handle WebSocket messages for timeline updates
  useEffect(() => {
    const unsubscribe = subscribe((message) => {
      if (message && message.data) {
        const messageData = message.data;

        // Check if this message is for the current case
        if (messageData.case_id === caseNo) {
          // Extract role from component field (e.g., "navigator" from "timeline/navigator/interest_received/v1")
          let componentRole: string | null = null;
          if (message.component) {
            const componentParts = message.component.split('/');
            // Component format: "timeline/{role}/{timeline_type_name}/v{version}"
            if (componentParts.length >= 2 && componentParts[0] === 'timeline') {
              componentRole = componentParts[1];
            }
          }

          // Determine the role to match against (use selectedRoleCode if available, otherwise currentRole)
          const roleToMatch = selectedRoleCode || currentRole;

          // Check if the component role matches the selected role
          const roleMatches = componentRole && 
            componentRole.toLowerCase() === roleToMatch.toLowerCase();

          // Only proceed if role matches (or if component field is not present, for backward compatibility)
          if (!componentRole || roleMatches) {
            // Update timeline data using functional update to avoid dependency issues
            setTimelineData((prevData) => {
              // Check if this timeline item already exists
              const existingItemIndex = prevData.findIndex(
                (item) => item.id === messageData.id
              );

              if (existingItemIndex !== -1) {
                // Update existing timeline item
                const newData = [...prevData];
                newData[existingItemIndex] = messageData;
                return newData;
              } else {
                // Add new timeline item
                setTotalRecords((prev) => prev + 1);
                return [...prevData, messageData];
              }
            });
            lastUpdateSource.current = "websocket";
          }
        }
      }
    });

    // Cleanup subscription on unmount
    return () => {
      unsubscribe();
    };
  }, [subscribe, caseNo, currentRole, selectedRoleCode]);

  // Combined scroll effect for both websocket and initial load
  useEffect(() => {
    const shouldScroll =
      !loading &&
      timelineData.length > 0 &&
      timelineContainerRef.current &&
      (lastUpdateSource.current === "websocket" || isInitialLoadDone.current === false);

    // Reset websocket flag immediately before scrolling logic
    const wasWebsocketUpdate = lastUpdateSource.current === "websocket";
    if (wasWebsocketUpdate) {
      lastUpdateSource.current = null;
    }

    if (shouldScroll) {
      const timer = setTimeout(() => {
        if (timelineContainerRef.current) {
          // Scroll to bottom when multiple cards (all roles); only on lawyers page with single card, scroll to top
          const isSingleCard = timelineData.length <= 1;
          const isLawyersPage = (currentRole === "Navigator" && selectedRoleCode?.toLowerCase() === "lawyer") || currentRole === "Lawyer";
          if (isLawyersPage && isSingleCard) {
            timelineContainerRef.current.scrollTo({ top: 0, behavior: "auto" });
          } else {
            timelineContainerRef.current.scrollTo({
              top: timelineContainerRef.current.scrollHeight,
              behavior: "auto",
            });
          }
        }
        
        // Mark initial load as done
        if (isInitialLoadDone.current === false) {
          isInitialLoadDone.current = true;
        }
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [loading, timelineData, currentRole, selectedRoleCode]);

  // Fetch case details (sidebar data and action buttons)
  const fetchCaseDetails = useCallback(async () => {
    if (!caseNo) return;

    setCaseDetailsLoading(true);
    try {
      const result = await api.get<CaseDetailsApiResponse>(
        `/v1/case/details?case_id=${caseNo}`
      );

      if (result.success && result.data) {
        setCaseDetails(result.data);
        setActionButtons(result.data.action_buttons);
      } else {
        throw new Error(result.message || "Failed to fetch case details");
      }
    } catch (err) {
      console.error("Error fetching case details:", err);
      setCaseDetails(null);
      setActionButtons(null);
    } finally {
      setCaseDetailsLoading(false);
    }
  }, [caseNo]);

  // --- Extract timeline data fetch to callback for reuse (and refresh button)
  const fetchTimelineData = useCallback(
    async ({
      scrollToBottom = false,
      afterRefresh = false,
    }: { scrollToBottom?: boolean; afterRefresh?: boolean } = {}) => {
      // Don't fetch if Navigator has selected Lawyer role but hasn't selected a lawyer yet
      if (currentRole === "Navigator" && selectedRoleCode?.toLowerCase() === "lawyer" && !selectedLawyerId) {
        setLoading(false);
        setTimelineData([]);
        setTotalRecords(0);
        setHasMore(false);
        setError(null);
        return;
      }

      if (afterRefresh) setRefreshing(true);
      setLoading(!afterRefresh);
      setError(null);
      const encodedCaseId = encodeURIComponent(caseNo || "");

      let queryParams = `page=1&limit=${pageSize}&order_by=created_at&order_dir=desc&case_id=${encodedCaseId}`;
      if (currentRole === "Navigator" && selectedRoleCode) {
        queryParams += `&role_code=${encodeURIComponent(selectedRoleCode)}`;
        if (selectedRoleCode.toLowerCase() === "lawyer" && selectedLawyerId) {
          queryParams += `&lawyer_id=${encodeURIComponent(selectedLawyerId)}`;
        }
      }

      try {
        const response: TimelineApiResponse = await api.get(
          `/v1/timeline?${queryParams}`
        );
        if (response.success && response.data) {
          const reversedData = [
            ...(response.data.timeline_data || []),
          ].reverse();
          setTimelineData(reversedData);
          setTotalRecords(response.data.total_count || 0);
          setCurrentPage(1);

          // Store matched lawyers if available (for Navigator role switching)
          if ((response.data as any).matched_lawyers) {
            setMatchedLawyers((response.data as any).matched_lawyers);
          }

          if((response.data as any).case_number) {
            setCaseNumber((response.data as any).case_number);
          }

          // --- Reset initial load state on every new case or refresh
          isInitialLoadDone.current = false;

          // Check if there are more items to load
          setHasMore((response.data.total_count || 0) > pageSize);

          // Scroll to bottom when multiple cards (all roles); only on lawyers page with single card, scroll to top
          if (scrollToBottom && timelineContainerRef.current) {
            const isSingleCard = (response.data.timeline_data || []).length <= 1;
            const isLawyersPage = (currentRole === "Navigator" && selectedRoleCode?.toLowerCase() === "lawyer") || currentRole === "Lawyer";
            setTimeout(() => {
              if (timelineContainerRef.current) {
                if (isLawyersPage && isSingleCard) {
                  timelineContainerRef.current.scrollTo({ top: 0, behavior: "auto" });
                } else {
                  timelineContainerRef.current.scrollTo({
                    top: timelineContainerRef.current.scrollHeight,
                    behavior: "auto",
                  });
                }
              }
            }, 100);
          }
        } else {
          setTimelineData([]);
          setTotalRecords(0);
          setHasMore(false);
          setError(response.message || "Failed to fetch timeline data.");
          isInitialLoadDone.current = false;
        }
      } catch (err: any) {
        // Don't redirect to case-dashboard if it's a 401 error
        // Let the apiFetch 401 handler manage the redirect to /login
        if (err instanceof ApiError && err.status === 401) {
          // The apiFetch function will handle navigation to /login
          // Just set the error state and let the 401 handler do its job
          setTimelineData([]);
          setTotalRecords(0);
          setHasMore(false);
          setError(
            err?.message || "An error occurred while fetching timeline data."
          );
          isInitialLoadDone.current = false;
          return; // Exit early, don't redirect
        }
        
        // For non-401 errors, redirect to case-dashboard
        window.location.href = "/case-dashboard";
        setTimelineData([]);
        setTotalRecords(0);
        setHasMore(false);
        setError(
          err?.message || "An error occurred while fetching timeline data."
        );
        isInitialLoadDone.current = false;
      } finally {
        setLoading(false);
        if (afterRefresh) setRefreshing(false);
      }
    },
    [
      currentRole,
      selectedRoleCode,
      selectedLawyerId,
      caseNo,
      user?.id,
      pageSize,
    ]
  );

  // Fetch timeline data and case details from API (only when authenticated)
  useEffect(() => {
    if (!isAuthenticated) return;
    fetchTimelineData();
    fetchCaseDetails();
  }, [isAuthenticated, caseNo, user?.id, currentRole, selectedRoleCode, selectedLawyerId, fetchTimelineData, fetchCaseDetails]);

  // Load more timeline items (older items)
  const handleLoadMore = async () => {
    if (isLoadingMore || !hasMore) return;

    // Don't fetch if Navigator has selected Lawyer role but hasn't selected a lawyer yet
    if (currentRole === "Navigator" && selectedRoleCode?.toLowerCase() === "lawyer" && !selectedLawyerId) {
      return;
    }

    setIsLoadingMore(true);
    const encodedCaseId = encodeURIComponent(caseNo || "");

    // Store current scroll position and height before loading
    const container = timelineContainerRef.current;
    const previousScrollHeight = container?.scrollHeight || 0;
    const previousScrollTop = container?.scrollTop || 0;

    try {
      const nextPage = currentPage + 1;

      // Build query parameters
      let queryParams = `page=${nextPage}&limit=${pageSize}&order_by=created_at&order_dir=desc&case_id=${encodedCaseId}`;
      
      // Add role switching parameters for Navigator
      if (currentRole === "Navigator" && selectedRoleCode) {
        queryParams += `&role_code=${encodeURIComponent(selectedRoleCode)}`;
        
        // Add lawyer_id if Lawyer role is selected
        if (selectedRoleCode.toLowerCase() === "lawyer" && selectedLawyerId) {
          queryParams += `&lawyer_id=${encodeURIComponent(selectedLawyerId)}`;
        }
      }

      // Fetch older items (desc order, next page)
      const response: TimelineApiResponse = await api.get(
        `/v1/timeline?${queryParams}`
      );

      if (response.success && response.data) {
        // Reverse the array to maintain chronological order
        const reversedData = [...(response.data.timeline_data || [])].reverse();

        // Prepend older items to the top
        lastUpdateSource.current = "api";
        setTimelineData((prevData) => [...reversedData, ...prevData]);
        setCurrentPage(nextPage);

        // Update hasMore based on total loaded vs total records
        const totalLoaded = timelineData.length + reversedData.length;
        setHasMore(totalLoaded < (response.data.total_count || 0));

        // Restore scroll position after DOM update (to top, NOT to bottom)
        // Wait for next frame to ensure DOM has updated
        requestAnimationFrame(() => {
          if (container) {
            const newScrollHeight = container.scrollHeight;
            const heightDifference = newScrollHeight - previousScrollHeight;
            // Maintain scroll position by adding the height difference
            container.scrollTop = previousScrollTop + heightDifference;
          }
        });
      }
    } catch (error) {
      console.error("Error loading more timeline items:", error);
      const toast = createErrorToast(
        "Error",
        "Failed to load more timeline items"
      );
      toastManager.addToast(toast);
    } finally {
      setIsLoadingMore(false);
      // DO NOT set lastUpdateSource to websocket here
    }
  };

  // Role Switcher UI for Navigator
  const roleSwitcherOptions = [
    { value: "Navigator", label: "Navigator", icon: "fas fa-user-shield" },
    { value: "Customer", label: "Customer", icon: "fas fa-user" },
    ...(matchedLawyers.length > 0 
      ? [{ value: "Lawyer", label: "Expert", icon: "fas fa-balance-scale" }] 
      : []
    ),
  ];

  // ---- REFRESH BUTTON ----
  const handleRefreshClick = useCallback(() => {
    fetchTimelineData({ scrollToBottom: true, afterRefresh: true });
    fetchCaseDetails();
  }, [fetchTimelineData, fetchCaseDetails]);

  // Handle timeline navigation (scroll to specific timeline type)
  const handleTimelineNavigate = useCallback((timelineType: string) => {
    // Use a small delay to ensure DOM is updated
    setTimeout(() => {
      // Check if this is a section-specific navigation (e.g., case_pathway_overview_section_2)
      const sectionMatch = timelineType.match(/^(.+)_section_([23])$/);
      
      if (sectionMatch) {
        // This is a section-specific navigation
        const baseType = sectionMatch[1]; // e.g., "case_pathway_overview"
        const sectionNumber = sectionMatch[2]; // "2" or "3"
        const sectionId = `case-pathway-overview-section-${sectionNumber}`;
        
        // First, find the timeline item with the base type
        const timelineItem = timelineItemRefs.current.get(baseType);
        if (timelineItem && timelineContainerRef.current) {
          // Then find the specific section within that timeline item
          const sectionElement = timelineItem.querySelector(`#${sectionId}`);
          if (sectionElement) {
            const container = timelineContainerRef.current;
            const elementRect = sectionElement.getBoundingClientRect();
            const containerRect = container.getBoundingClientRect();
            const elementTopRelativeToContainer = elementRect.top - containerRect.top + container.scrollTop;
            
            // Calculate scroll position to scroll to the top of the element with some padding
            const scrollPosition = elementTopRelativeToContainer - 20;
            
            container.scrollTo({
              top: Math.max(0, scrollPosition),
              behavior: "smooth",
            });
            return;
          }
        }
      }
      
      // Default behavior: scroll to the timeline type element
      const element = timelineItemRefs.current.get(timelineType);
      if (element && timelineContainerRef.current) {
        const container = timelineContainerRef.current;
        const elementRect = element.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const elementTopRelativeToContainer = elementRect.top - containerRect.top + container.scrollTop;
        
        // Calculate scroll position to scroll to the top of the element with some padding
        const scrollPosition = elementTopRelativeToContainer - 20;
        
        container.scrollTo({
          top: Math.max(0, scrollPosition),
          behavior: "smooth",
        });
      }
    }, 50);
  }, []);

  // Update context with timeline data, navigation handler, and effective role
  useEffect(() => {
    setContextTimelineData(timelineData);
  }, [timelineData, setContextTimelineData]);

  // Register timeline refresh so timeline cards (e.g. after KYC submit) can refetch
  useEffect(() => {
    setRefreshTimelineHandler(fetchTimelineData);
    return () => setRefreshTimelineHandler(null);
  }, [fetchTimelineData, setRefreshTimelineHandler]);

  // Register case details refresh so card modals (Review Profiles / Review and Send from card) update sticky action bar
  useEffect(() => {
    setRefreshCaseDetailsHandler(fetchCaseDetails);
    return () => setRefreshCaseDetailsHandler(null);
  }, [fetchCaseDetails, setRefreshCaseDetailsHandler]);

  useEffect(() => {
    setNavigateHandler(handleTimelineNavigate);
    return () => {
      setNavigateHandler(() => {});
    };
  }, [handleTimelineNavigate, setNavigateHandler]);

  // Update effective role in context when it changes
  useEffect(() => {
    setContextEffectiveRole(effectiveRole);
  }, [effectiveRole, setContextEffectiveRole]);

  // Update refs when timeline data changes
  useEffect(() => {
    // Re-populate refs from DOM after a short delay to ensure elements are rendered
    if (timelineData.length > 0 && timelineContainerRef.current) {
      const timer = setTimeout(() => {
        const container = timelineContainerRef.current;
        if (container) {
          const elements = container.querySelectorAll('[data-timeline-type]');
          elements.forEach((el) => {
            const timelineType = el.getAttribute('data-timeline-type');
            if (timelineType) {
              // Always update to get the first occurrence (topmost in timeline)
              const existingRef = timelineItemRefs.current.get(timelineType);
              if (!existingRef || el.compareDocumentPosition(existingRef) & Node.DOCUMENT_POSITION_FOLLOWING) {
                // Update if no existing ref or if current element is before existing one
                timelineItemRefs.current.set(timelineType, el as HTMLDivElement);
              }
            }
          });
        }
      }, 150);
      
      return () => clearTimeout(timer);
    }
  }, [timelineData, caseNo]);

  // Action buttons component for header (desktop)
  const ActionButtons = ({ className = "" }: { className?: string }) => (
    <div className={`flex items-center gap-2 ${className}`}>
      {currentRole === "Navigator" && (
        <>
      <FormButton
        size="sm"
        variant="custom"
        className="text-novaNeutral-600 hover:text-novaNeutral-800 flex items-center justify-center text-xs sm:text-sm focus:ring-0 active:ring-0 active:ring-offset-0 focus:border-transparent"
        onClick={handleRefreshClick}
        disabled={caseDetailsLoading}
      >
        <i className={`fas fa-refresh ${caseDetailsLoading ? 'animate-spin' : ''}`}></i>
      </FormButton>
          {/* Lawyer Selector Dropdown - Only shown when Lawyer role is selected */}
          {selectedRoleCode?.toLowerCase() === "lawyer" && matchedLawyers.length > 0 && (
            <CustomSelect
              value={selectedLawyerId || ""}
              onChange={handleLawyerSelect}
              options={matchedLawyers.map(lawyer => ({
                value: lawyer.lawyer_id,
                label: lawyer.lawyer_name,
              }))}
              placeholder="Select Expert..."
              icon="fas fa-gavel"
              className="w-[110px] sm:w-[140px] lg:w-[160px]"
              triggerClassName="border-none hover:border-none hover:shadow-none hover:text-novaPrimary-800 focus:ring-transparent active:ring-0 active:ring-offset-0 focus:outline-none"
            />
          )}
          {/* Role Selector Dropdown */}
          <CustomSelect
            value={selectedRoleCode || "Navigator"}
            onChange={handleRoleSwitch}
            options={roleSwitcherOptions}
            placeholder="Switch Role"
            icon="fas fa-user-shield"
            className="maxw-[100px] sm:w-[120px] lg:w-[135px]"
            triggerClassName="border-none hover:border-none hover:shadow-none hover:text-novaPrimary-800 focus:ring-0 focus:border-transparent"
          />
        </>
      )}
    </div>
  );

  // Sidebar action buttons (mobile-friendly full width)
  const SidebarActionButtons = () => (
    <>
      {currentRole === "Navigator" && (
        <>
          {/* Dropdowns Row - Side by Side */}
          <div className="md:flex flex-col">
            {/* Role Selector Dropdown */}
            <CustomSelect
              value={selectedRoleCode || "Navigator"}
              onChange={handleRoleSwitch}
              options={roleSwitcherOptions}
              placeholder="Switch Role"
              icon="fas fa-user-shield"
              className="flex-1 [&_button]:!py-2 [&_button_span]:!text-sm mb-2"
              triggerClassName="rounded-full border-novaPrimary-500 font-medium text-novaPrimary-600"
            />
            
            {/* Lawyer Selector Dropdown - Only shown when Lawyer role is selected */}
            {selectedRoleCode?.toLowerCase() === "lawyer" && matchedLawyers.length > 0 && (
              <CustomSelect
                value={selectedLawyerId || ""}
                onChange={handleLawyerSelect}
                options={matchedLawyers.map(lawyer => ({
                  value: lawyer.lawyer_id,
                  label: lawyer.lawyer_name,
                }))}
                placeholder="Select lawyer..."
                icon="fas fa-gavel"
                className="flex-1 [&_button]:!py-2 [&_button_span]:!text-sm"
                triggerClassName="rounded-full border-novaPrimary-500 font-medium"
              />
            )}
          </div>

          {/* Refresh Button */}
          <FormButton
            size="sm"
            variant="custom"
            onClick={handleRefreshClick}
            className={`w-full inline-flex items-center justify-center text-sm px-3 py-2 transition text-novaNeutral-600 focus:ring-0 active:ring-0 active:ring-offset-0 focus:border-transparent${
              refreshing ? "opacity-50 pointer-events-none" : ""
            }`}
            type="button"
            aria-label="Refresh Timeline"
          >
            {refreshing ? (
              <i className="fa-solid fa-arrows-rotate text-novaPrimary-600 fa-spin animate-spin mr-2"></i>
            ) : (
              <i className="fa-solid fa-arrows-rotate text-novaPrimary-600 mr-2"></i>
            )}
            <span>Refresh Timeline</span>
          </FormButton>
        </>
      )}
    </>
  );

  // Header actions - only visible on xl screens
  const headerActions = (
    <div className="hidden xl:flex">
      <ActionButtons />
    </div>
  );

  if (!isAuthenticated) return null;

  return (
    <Layout 
      headerActions={headerActions}
      sidebarActions={<SidebarActionButtons />}
      caseNumber={caseNumber || ""}
    >
      {/* Top bar toggle for sidebar on small screens */}
      {(() => {
        const [sidebarOpen, setSidebarOpen] = React.useState(false);
        const [sidebarVisible, setSidebarVisible] = React.useState(false);
        const sidebarTransitionDuration = 200;

        const openSidebar = React.useCallback(() => {
          setSidebarVisible(true);
          if (typeof window !== "undefined" && window.requestAnimationFrame) {
            window.requestAnimationFrame(() => setSidebarOpen(true));
          } else {
            setTimeout(() => setSidebarOpen(true), 0);
          }
        }, []);

        const closeSidebar = React.useCallback(() => {
          setSidebarOpen(false);
        }, []);

        React.useEffect(() => {
          if (!sidebarOpen && sidebarVisible) {
            const timeout = window.setTimeout(() => {
              setSidebarVisible(false);
            }, sidebarTransitionDuration);

            return () => window.clearTimeout(timeout);
          }
        }, [sidebarOpen, sidebarVisible, sidebarTransitionDuration]);

        // @ts-ignore
        window.__setSidebarOpen = (isOpen: boolean) => {
          if (isOpen) {
            openSidebar();
          } else {
            closeSidebar();
          }
        };

        return (
          <>
            {/* Floating tray button for opening case summary on small screens */}
            { currentRole.toLowerCase() !== "customer" && 
              currentRole.toLowerCase() !== "lawyer" &&
              selectedRoleCode?.toLowerCase() !== "customer" &&
              selectedRoleCode?.toLowerCase() !== "lawyer" &&
              !sidebarVisible && (
              <button
                className="fixed right-0 z-40 flex xl:hidden items-center justify-center w-6 h-12 bg-novaPrimary-100 text-white rounded-l-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-novaPrimary-300"
                onClick={openSidebar}
                type="button"
                aria-label="Open case summary"
              >
                <i className="fa-solid fa-angle-left text-lg"></i>
              </button>
            )}
            {/* Sidebar drawer for small screens */}
            {sidebarVisible && (
              <div
                className={`fixed inset-0 z-50 flex xl:hidden transition-opacity duration-200 ${
                  sidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"
                }`}
              >
                {/* Overlay */}
                <div
                  className="fixed inset-0 bg-black bg-opacity-30"
                  onClick={closeSidebar}
                  aria-label="Close sidebar"
                />
                {/* Sidebar */}
                <div
                  className={`relative w-80 max-w-full bg-white h-full shadow-xl ml-auto flex flex-col transform transition-transform duration-200 ease-out ${
                    sidebarOpen ? "translate-x-0" : "translate-x-full"
                  }`}
                >
                  <button
                    className="absolute top-3 right-3 flex items-center justify-center w-7 h-7 rounded-full bg-white/20 backdrop-blur-sm text-novaNeutral-500 hover:text-novaNeutral-900 transition p-0"
                    onClick={closeSidebar}
                    aria-label="Close"
                    type="button"
                  >
                    <i className="fas fa-times text-base"></i>
                  </button>
                  {/* Make sidebar scrollable on small screens */}
                  <div className="flex-1 overflow-y-auto pt-3">
                    <TimelineSidebar
                      caseId={caseNo}
                      className=""
                      caseDetails={caseDetails}
                      loading={caseDetailsLoading}
                      onCaseDetailsRefresh={fetchCaseDetails}
                    />
                  </div>
                </div>
              </div>
            )}
          </>
        );
      })()}

      {/* 
        To ensure the sidebar and main content scroll independently, 
        use a flex container with min-h-0 and h-[calc(100vh-0px)] (or h-screen if you prefer).
        Each child (main and sidebar) must have overflow-y-auto and min-h-0.
      */}
      <div
        className="flex h-[calc(100vh-0px)] min-h-0 bg-white justify-center items-center"
        style={{ minHeight: 0 }}
      >
        {/* Main timeline area with its own scroll */}
        <div
          ref={timelineContainerRef}
          className={`gap-6 sm:gap-8 w-full min-h-0 overflow-y-auto bg-white pt-4 pb-4 ${
            !isSidebarVisible ? "px-4 md:px-[60px] lg:px-[100px] 2xl:px-[180px]" : "px-4"
          } ${
            hasActionButtons ? "mb-4" : ""
          }`}
          style={{
            height: hasActionButtons ? "calc(100% - 64px)" : "100%",
            scrollbarWidth: "thin", // For Firefox
            scrollbarColor: "#e4e5e9 transparent", // For Firefox: lighter thumb color
          }}
        >
          <style>
            {`
              /* Custom thin and light scrollbar for timeline area */
              .w-full::-webkit-scrollbar {
                width: 8px;
              }
              .w-full::-webkit-scrollbar-thumb {
                background: #e4e5e9;
                border-radius: 8px;
              }
              .w-full::-webkit-scrollbar-track {
                background: transparent;
              }
              @media (min-width: 1280px) {
                .xl\\:w-4\\/5::-webkit-scrollbar {
                  width: 8px;
                }
              }
              /* Timeline card background colors based on latest status */
              .timeline-card-latest .timeline-card-border {
                background-color: var(--nova-active) !important;
              }
              .timeline-card-normal .timeline-card-border {
                background-color: var(--nova-inactive) !important;
              }
            `}
          </style>
          {loading ? (
            <div className="space-y-4">
              {/* Show multiple loading skeletons */}
              {Array.from({ length: 5 }, (_, index) => (
                <div key={index} className="p-4">
                  <div className="bg-novaNeutral-50 rounded-lg border border-novaNeutral-200 animate-pulse">
                    <div className="p-4 space-y-3">
                      <div className="h-4 bg-novaNeutral-200 rounded w-3/4"></div>
                      <div className="h-3 bg-novaNeutral-200 rounded w-1/2"></div>
                      <div className="h-3 bg-novaNeutral-200 rounded w-2/3"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : timelineData.length === 0 ? (
            <div className="space-y-4">
              <DataNotFound message="No timeline data found." />
            </div>
          ) : (
            <>
              {/* Load More Button - WhatsApp Style */}
              {hasMore && (
                <div className="flex justify-center mb-4">
                  <FormButton
                    variant="outline"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                    className="flex items-center justify-center ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border bg-white hover:text-novaNeutral-900 h-10 border-novaPrimary-300 text-novaPrimary-600 hover:bg-novaPrimary-50 text-sm px-3 py-1"
                  >
                    {isLoadingMore ? (
                      <>
                        <i className="fa-solid fa-spinner fa-spin animate-spin"></i>
                        <span className="ml-2">Loading...</span>
                      </>
                    ) : (
                      <>
                        <i className="fa-solid fa-angles-up mr-2"></i>
                        <span>Load More</span>
                      </>
                    )}
                  </FormButton>
                </div>
              )}

              {/* Timeline Items */}
              {(() => {
                const renderedIds = new Set<string>();
                return timelineData.map((item) => {
                  if (renderedIds.has(item.id)) {
                    return null; // Skip duplicate
                  }
                  renderedIds.add(item.id);
                  const isLatest = item.id === latestItemId;

                  return (
                    <div
                      ref={(el) => {
                        if (el && item.timeline_type_name) {
                          // Store ref for the first occurrence of each timeline type
                          if (!timelineItemRefs.current.has(item.timeline_type_name)) {
                            timelineItemRefs.current.set(item.timeline_type_name, el);
                          }
                        }
                      }}
                      data-timeline-type={item.timeline_type_name}
                      className={`sm:mb-6 mb-4 rounded-lg ${isLatest ? 'timeline-card-latest' : 'timeline-card-normal'}`}
                      key={item.id}
                    >
                      <TimelineItem item={item} isLatest={isLatest} effectiveRole={effectiveRole} />
                    </div>
                  );
                });
              })()}
            </>
          )}
        </div>

        {/* Right sidebar for large screens with its own scroll */}
        {currentRole.toLowerCase() !== "customer" && 
         currentRole.toLowerCase() !== "lawyer" &&
         selectedRoleCode?.toLowerCase() !== "customer" &&
         selectedRoleCode?.toLowerCase() !== "lawyer" && <div
          className="w-96 flex-shrink-0 hidden xl:block min-h-0 overflow-y-auto"
          style={{
            height: "100%",
          }}
        >
          <TimelineSidebar
            caseId={caseNo}
            className=""
            caseDetails={caseDetails}
            loading={caseDetailsLoading}
            onCaseDetailsRefresh={fetchCaseDetails}
          />
        </div>}
      </div>

      {/* Action Bar - Sticky at bottom */}
      <TimelineActionBar
        actionButtons={actionButtons || undefined}
        onActionClick={handleActionClick}
        loading={modalLoading}
        sidebarVisible={
          currentRole.toLowerCase() !== "customer" && 
          currentRole.toLowerCase() !== "lawyer" &&
          selectedRoleCode?.toLowerCase() !== "customer" &&
          selectedRoleCode?.toLowerCase() !== "lawyer"
        }
      />

      {/* Modals */}
      {showInterestedLawyersModal && (
        <InterestedLawyersPopUp
          isOpen={showInterestedLawyersModal}
          onClose={() => setShowInterestedLawyersModal(false)}
          onSend={handleSendLawyers}
          interestedLawyers={interestedLawyers}
          caseId={caseNo}
        />
      )}
      {showReviewProfilesModal && (
        <ReviewProfilesModal
          isOpen={showReviewProfilesModal}
          onClose={() => setShowReviewProfilesModal(false)}
          onConfirmSuccess={fetchCaseDetails}
          lawyers={lawyers}
          caseId={caseNo}
        />
      )}
    </Layout>
  );
}
