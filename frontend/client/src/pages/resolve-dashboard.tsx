import React, { useState, useEffect, useRef } from "react";
import { Layout } from "../components";
import {
  DEFAULT_THEME,
  ResolveDashCard,
  STATUS_THEMES,
} from "@/components/resolve/dashboard/ResolveDashboardCard";
import { useLocation } from "wouter";
import { api } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import {
  usePagination,
  Pagination,
  getPageItems,
  PageLoader,
  getFromLocalStorage,
  FormButton,
} from "../utils";
import { useRole } from "@/contexts/RoleContext";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import ResolveDetailsModal from "@/components/timeline/ResolveDetailsModal";
import { createErrorToast, toastManager } from "@/utils/toasts";
import { storeRedirectAfterLogin } from "@/utils/redirectAfterLogin";

interface Customer {
  first_name: string;
  last_name: string;
  email: string;
  id: string;
}

interface ResolveItem {
  title: string | null;
  resolve_id: string;
  case_type: string;
  resolve_status: string;
  start_date: string;
  completed_date: string | null;
  no_of_questions_answered: number;
  customer: Customer | null;
}

interface ApiResponse {
  success: boolean;
  message: any[];
  data: {
    total_count: number;
    records_in_page: number;
    resolves: ResolveItem[];
  };
}


export default function ResolveDashboard() {
  // Configuration variables - easily modifiable
  const API_LIMIT = 12; // Number of items per page
  const DEBOUNCE_DELAY = 500; // Debounce delay in milliseconds
  const [, setLocation] = useLocation();
  const { currentRole } = useRole();
  const { user, isAuthenticated } = useAuth();
  const [resolveItems, setResolveItems] = useState<ResolveItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [itemsPerPage, setItemsPerPage] = useState(API_LIMIT);
  const [noRecordsFound, setNoRecordsFound] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string>("All");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState<string>("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [resolveData, setResolveData] = useState<any>(null);
  const [selectedResolveId, setSelectedResolveId] = useState<string | null>(null);

  const pagination = usePagination(totalCount, itemsPerPage);

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

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, DEBOUNCE_DELAY);

    return () => {
      clearTimeout(timer);
    };
  }, [searchTerm, DEBOUNCE_DELAY]);

  const fetchResolveList = async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      setNoRecordsFound(false);
      // Add page, limit, status, and search parameters to the API call
      const searchParam = debouncedSearchTerm ? `&search=${encodeURIComponent(debouncedSearchTerm)}` : '';
      const response = await api.get<ApiResponse>(
        `/v1/resolve/list?page=${page}&limit=${API_LIMIT}&status=${selectedStatus}${searchParam}`
      );

      if (response.success && response.data) {
        const { resolves, total_count } = response.data;

        setResolveItems(resolves);
        // Only update total count if it's different to prevent unnecessary re-renders
        if (totalCount !== total_count) {
          setTotalCount(total_count);
        }
        // Keep itemsPerPage consistent with API_LIMIT
        setItemsPerPage(API_LIMIT);
      } else {
        setError("Failed to fetch resolve list");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch resolve list"
      );
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when page changes (including initial load) - only when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;
    fetchResolveList(pagination.currentPage);
  }, [isAuthenticated, pagination.currentPage, API_LIMIT, user?.id, currentRole, selectedStatus, debouncedSearchTerm]);

  // Reset to page 1 when debounced search term changes
  useEffect(() => {
    if (pagination.currentPage !== 1) {
      pagination.goToPage(1);
    }
  }, [debouncedSearchTerm]);

  // Handle status change - reset to page 1
  const handleStatusChange = (status: string) => {
    setSelectedStatus(status);
    setIsDropdownOpen(false);
    pagination.goToPage(1);
  };

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  // Handle search clear
  const handleSearchClear = () => {
    setSearchTerm("");
  };

  // Handle card click to open modal
  const handleCardClick = async (resolveId: string) => {
    try {
      setLoading(true);
      setSelectedResolveId(resolveId);
      const encodedResolveId = encodeURIComponent(resolveId);
      const response = await api.get(`/v1/resolve?resolve_id=${encodedResolveId}`);
      setResolveData((response as any).data || {});
      setIsModalOpen(true);
      setLoading(false);
    } catch (error: any) {
      let errorMessage = "Failed to get Resolve details. Please try again.";

      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      const toast = createErrorToast("Error", errorMessage);
      toastManager.addToast(toast);
      setIsModalOpen(false);
      setSelectedResolveId(null);
    }
  };

  // Handle modal close
  const handleModalClose = () => {
    setIsModalOpen(false);
    setResolveData(null);
    setSelectedResolveId(null);
  };

  // Handle new resolve button click
  const handleNewResolveClick = async () => {
    try {
      // Directly call API to create new resolve and redirect to new ID
      // Skip session storage checking - always create a new resolve
      const result = await api.get("/v1/resolve");
      const resolveIdFromResult = (result as any)?.data?.resolve_id;
      if (resolveIdFromResult) {
        window.location.href = `/resolve/${resolveIdFromResult}`;
      } else {
        const toast = createErrorToast("Error", "Failed to create new resolve");
        toastManager.addToast(toast);
      }
    } catch (error: any) {
      console.error("Error creating new resolve:", error);
      const errorMessage = error?.message || "Failed to create new resolve";
      const toast = createErrorToast("Error", errorMessage);
      toastManager.addToast(toast);
    }
  };

  const headerActions = (
    <div className="flex items-center gap-2">
      <FormButton
        size="sm"
        variant="custom"
        className="text-gray-600 hover:text-gray-800 flex items-center justify-center px-2 py-1 text-xs sm:text-sm"
        onClick={() => fetchResolveList(pagination.currentPage)}
        disabled={loading}
      >
        <span className="flex items-center justify-center w-full">
          <i className={`fas fa-refresh ${loading ? 'animate-spin' : ''}`}></i>
          <span className="hidden sm:inline ml-2">Refresh</span>
        </span>
      </FormButton>
      {/* {currentRole === "Customer" && (
        <FormButton
          size="sm"
          className="bg-novaPrimary-500 rounded-full hover:bg-novaPrimary-600 text-white flex items-center px-2 py-0 sm:px-4 sm:py-2 text-xs sm:text-sm whitespace-nowrap min-w-0"
          onClick={handleNewResolveClick}
        >
          <i className="fas fa-plus"></i>
          <span className="ml-1 sm:ml-2">
            <span className="sm:hidden">New</span>
            <span className="hidden sm:inline">New Resolve</span>
          </span>
        </FormButton>
      )} */}
    </div>
  );

  const statusOptions = ["All", "In progress", "Completed", "Moving forward"];

  if (!isAuthenticated) return null;

  // Custom Dropdown Component
  const CustomDropdown = () => {
    const dropdownRef = React.useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
          setIsDropdownOpen(false);
        }
      };

      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }, []);

    return (
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex items-center justify-between w-full min-w-[120px] px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:border-gray-400 focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 outline-none transition-all duration-200"
        >
          <span className="truncate">{selectedStatus}</span>
          <i className={`fas fa-chevron-down ml-2 text-xs text-gray-500 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`}></i>
        </button>

        {isDropdownOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden animate-in fade-in-0 zoom-in-95 duration-200">
            {statusOptions.map((status, index) => (
              <button
                key={status}
                onClick={() => handleStatusChange(status)}
                className={`w-full px-3 py-2 text-sm text-left hover:bg-gray-50 transition-colors duration-150 flex items-center justify-between ${
                  selectedStatus === status 
                    ? 'bg-novaPrimary-50 text-novaPrimary-700 font-medium' 
                    : 'text-gray-700'
                } ${index !== statusOptions.length - 1 ? 'border-b border-gray-100' : ''}`}
              >
                <span>{status}</span>
                {selectedStatus === status && (
                  <i className="fas fa-check text-novaPrimary-600 text-xs"></i>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <Layout headerActions={headerActions}>
      <div className="p-3 sm:p-6 space-y-2 sm:space-y-6">
        {/* Search and Filter Section */}
        <div className="bg-[#f9f9f9] rounded-xl p-3 sm:p-3 timeline-card-border sticky top-0 z-10">
          <div className="flex items-center gap-3">
            {/* Search Field */}
            <div className="relative flex-1 sm:max-w-xs lg:max-w-md">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <i className="fas fa-search text-gray-400 text-sm"></i>
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder="Search recommendations…"
                className="w-full sm:pl-9 pl-7 pr-3 sm:pr-9 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 outline-none transition-all"
              />
              {searchTerm && (
                <button
                  onClick={handleSearchClear}
                  className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label="Clear search"
                >
                  <i className="fas fa-times text-sm"></i>
                </button>
              )}
            </div>

            {/* Mobile Custom Dropdown Filter */}
            {currentRole.toLowerCase() !== "lawyer" && (
              <div className="sm:hidden">
                <CustomDropdown />
              </div>
            )}

            {/* Desktop Button Filters */}
            {currentRole.toLowerCase() !== "lawyer" && (
              <div className="hidden sm:flex items-center gap-2">
                {/* Divider */}
                <div className="w-px h-6 bg-gray-200"></div>
                
                {/* Status Filters */}
                <div className="flex flex-wrap gap-2">
                  {statusOptions.map((status) => {
                    const theme =
                      STATUS_THEMES[status as keyof typeof STATUS_THEMES] ||
                      DEFAULT_THEME;

                    const isActive =
                      selectedStatus === status ||
                      (selectedStatus === "All" && status !== "All");

                    return (
                      <button
                        key={status}
                        onClick={() => handleStatusChange(status)}
                        className="px-3 py-1 rounded-full text-sm transition-all duration-200 whitespace-nowrap border"
                        style={{
                          backgroundColor: isActive
                            ? theme.statusBadgeBg
                            : "rgba(255,255,255,0.8)",
                          color: isActive
                            ? theme.statusBadgeText
                            : "#4B5563",
                          borderColor: isActive ? "transparent" : "#E5E7EB",
                          boxShadow: isActive
                            ? "1px 2px 7px 0 rgba(0, 0, 0, 0.2)"
                            : "none",
                        }}
                      >
                        {status.replace(/_/g, " ")}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading && <PageLoader message="Loading..." />}

        {/* Resolve List */}
        {!loading && (
          <div className="space-y-4">
            {resolveItems.length === 0 ? (
              <DataNotFound
                message={
                  selectedStatus === "All"
                    ? "You do not have any recommendations"
                    : `You do not have any recommendations currently ${selectedStatus.toLowerCase()}`
                }
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2 sm:gap-6 items-start">
                {resolveItems.map((item: ResolveItem) => (
                  <div
                    key={item.resolve_id}
                    className="hover:scale-105 transition-transform duration-200 ease-in-out h-full"
                    style={
                      {
                        "--tw-scale-x": 1.02,
                        "--tw-scale-y": 1.02,
                      } as React.CSSProperties
                    }
                  >
                    <ResolveDashCard item={item} onCardClick={handleCardClick} />
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalCount > 0 && (
              <div className="mt-6">
                <Pagination
                  config={{
                    currentPage: pagination.currentPage,
                    totalPages: pagination.totalPages,
                    totalItems: totalCount,
                    itemsPerPage: itemsPerPage,
                    onPageChange: pagination.goToPage,
                  }}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Resolve Details Modal - rendered outside the card grid */}
      {isModalOpen && resolveData && selectedResolveId && (
        <ResolveDetailsModal
          isOpen={isModalOpen}
          onClose={handleModalClose}
          data={resolveData}
          resolveId={selectedResolveId}
          caseId={resolveData.case?.id}
          showViewCaseButton={true}
        />
      )}
    </Layout>
  );
}
