import React, { useState, useEffect, useCallback, useRef } from "react";
import { Layout } from "../components";
import { CaseDashCard } from "@/components/case/v1/dashboard/CaseDashboardCard";
import { api } from "../lib/api";
import {
  usePagination,
  Pagination,
  getPageItems,
  PageLoader,
  getFromLocalStorage,
  FormButton,
} from "../utils";
import { Link } from "wouter";
import Button from "@/components/ui/button/v1/Button";
import { useRole } from "@/contexts/RoleContext";
import { useAuth } from "@/contexts/AuthContext";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";

interface Customer {
  first_name: string;
  last_name: string;
  email: string;
  id: string;
}

interface CaseItem {
  id: string;
  case_no: string;
  case_type: string;
  priority: string;
  status: string;
  start_date: string;
  created_at: string;
  title?: string | null;
  customer: Customer | null;
}

interface ApiResponse {
  success: boolean;
  message: any[];
  data: {
    total_count: number;
    records_in_page: number;
    cases: CaseItem[];
  };
}

export default function MissedCases() {
  // Configuration variables - easily modifiable
  const API_LIMIT = 16; // Number of items per page
  const PAGINATION_STORAGE_KEY = "missed_cases_page";
  const SEARCH_STORAGE_KEY = "missed_cases_search";
  const DEBOUNCE_DELAY = 500; // Debounce delay in milliseconds
  
  const [caseItems, setCaseItems] = useState<CaseItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noRecordsFound, setNoRecordsFound] = useState(false);
  const [itemsPerPage, setItemsPerPage] = useState(API_LIMIT);
  const [hasRestoredPage, setHasRestoredPage] = useState(false);

  // Initialize search state from session so first render has correct values (avoids debounce overwriting filter after 500ms)
  const [caseNumberSearch, setCaseNumberSearch] = useState(() => {
    try {
      const s = sessionStorage.getItem(SEARCH_STORAGE_KEY);
      if (s) {
        const { caseNumber } = JSON.parse(s);
        return caseNumber || "";
      }
    } catch {}
    return "";
  });
  const [customerSearch, setCustomerSearch] = useState(() => {
    try {
      const s = sessionStorage.getItem(SEARCH_STORAGE_KEY);
      if (s) {
        const { customer } = JSON.parse(s);
        return customer || "";
      }
    } catch {}
    return "";
  });
  const [debouncedCaseNumber, setDebouncedCaseNumber] = useState(() => {
    try {
      const s = sessionStorage.getItem(SEARCH_STORAGE_KEY);
      if (s) {
        const { caseNumber } = JSON.parse(s);
        return caseNumber || "";
      }
    } catch {}
    return "";
  });
  const [debouncedCustomer, setDebouncedCustomer] = useState(() => {
    try {
      const s = sessionStorage.getItem(SEARCH_STORAGE_KEY);
      if (s) {
        const { customer } = JSON.parse(s);
        return customer || "";
      }
    } catch {}
    return "";
  });
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearchRestoredOrChecked, setHasSearchRestoredOrChecked] = useState(false);

  const pagination = usePagination(totalCount, itemsPerPage);
  const { currentRole } = useRole();
  const { user } = useAuth();

  const prevDebouncedCaseNumberRef = useRef<string>("");
  const prevDebouncedCustomerRef = useRef<string>("");

  // Sync refs and mark ready; clear other dashboards’ filters (navigating to Missed Cases clears My Matches)
  useEffect(() => {
    prevDebouncedCaseNumberRef.current = debouncedCaseNumber;
    prevDebouncedCustomerRef.current = debouncedCustomer;
    sessionStorage.removeItem("my_matches_search");
    sessionStorage.removeItem("my_matches_page");
    sessionStorage.removeItem("case_dashboard_search");
    sessionStorage.removeItem("case_dashboard_page");
    if (currentRole === "Lawyer") {
      sessionStorage.removeItem("case_source_page");
    }
    setHasSearchRestoredOrChecked(true);
  }, [currentRole]);

  const NAVIGATING_TO_CASE_KEY = "navigating_to_case";
  const THIS_PAGE_KEY = "missed_cases";

  // When leaving this page: clear filters unless user is opening a case (so returning back keeps filters)
  useEffect(() => {
    return () => {
      const navigatingToCase = sessionStorage.getItem(NAVIGATING_TO_CASE_KEY) === THIS_PAGE_KEY;
      if (!navigatingToCase) {
        sessionStorage.removeItem(SEARCH_STORAGE_KEY);
        sessionStorage.removeItem(PAGINATION_STORAGE_KEY);
      }
      sessionStorage.removeItem(NAVIGATING_TO_CASE_KEY);
    };
  }, []);

  // Save search to session storage
  useEffect(() => {
    if (caseNumberSearch || customerSearch) {
      sessionStorage.setItem(SEARCH_STORAGE_KEY, JSON.stringify({ caseNumber: caseNumberSearch, customer: customerSearch }));
    } else {
      sessionStorage.removeItem(SEARCH_STORAGE_KEY);
    }
  }, [caseNumberSearch, customerSearch]);

  // Debounce effect for case number search
  useEffect(() => {
    setIsSearching(true);
    const timer = setTimeout(() => {
      setDebouncedCaseNumber(caseNumberSearch);
      setIsSearching(false);
    }, DEBOUNCE_DELAY);

    return () => clearTimeout(timer);
  }, [caseNumberSearch]);

  // Debounce effect for customer search
  useEffect(() => {
    setIsSearching(true);
    const timer = setTimeout(() => {
      setDebouncedCustomer(customerSearch);
      setIsSearching(false);
    }, DEBOUNCE_DELAY);

    return () => clearTimeout(timer);
  }, [customerSearch]);

  // Restore saved page after initial data load
  useEffect(() => {
    if (!loading && !hasRestoredPage && totalCount > 0) {
      const savedPage = sessionStorage.getItem(PAGINATION_STORAGE_KEY);
      if (savedPage) {
        const pageNum = parseInt(savedPage, 10);
        if (pageNum > 1 && pageNum <= pagination.totalPages) {
          pagination.goToPage(pageNum);
        }
        sessionStorage.removeItem(PAGINATION_STORAGE_KEY);
      }
      setHasRestoredPage(true);
    }
  }, [loading, totalCount, hasRestoredPage, pagination]);

  const fetchCaseList = async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      setNoRecordsFound(false);

      // Build query parameters
      const queryParams = new URLSearchParams({
        page: page.toString(),
        limit: API_LIMIT.toString(),
        category: "Missed Cases",
      });

      // Add search parameters if they exist
      if (debouncedCaseNumber.trim()) queryParams.append('case_no', debouncedCaseNumber.trim());
      if (debouncedCustomer.trim()) queryParams.append('search', debouncedCustomer.trim());

      // Make API call with search parameters
      const response = await api.get<ApiResponse>(
        `/v1/case?${queryParams.toString()}`
      );

      if (response.success && response.data) {
        const { cases, total_count } = response.data;

        setCaseItems(cases);
        // Only update total count if it's different to prevent unnecessary re-renders
        if (totalCount !== total_count) {
          setTotalCount(total_count);
        }
        // Keep itemsPerPage consistent with API_LIMIT
        setItemsPerPage(API_LIMIT);
      } else {
        setError("Failed to fetch case list");
      }
    } catch (err: any) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch case list"
      );
      console.error("Error fetching case list:", err);
    } finally {
      setLoading(false);
    }
  };

  // Track search change in progress to avoid double fetch with page effect
  const isSearchChangeInProgress = useRef<boolean>(false);

  // Reset to page 1 and fetch when search terms change
  useEffect(() => {
    const searchChanged =
      prevDebouncedCaseNumberRef.current !== debouncedCaseNumber ||
      prevDebouncedCustomerRef.current !== debouncedCustomer;

    if (searchChanged) {
      isSearchChangeInProgress.current = true;
      prevDebouncedCaseNumberRef.current = debouncedCaseNumber;
      prevDebouncedCustomerRef.current = debouncedCustomer;
      if (pagination.currentPage !== 1) {
        pagination.goToPage(1);
      }
      fetchCaseList(1).finally(() => {
        setTimeout(() => {
          isSearchChangeInProgress.current = false;
        }, 0);
      });
    }
  }, [debouncedCaseNumber, debouncedCustomer, pagination]);

  // Fetch data when page changes, only after search has been restored/checked (avoids unfiltered first fetch on redirect)
  useEffect(() => {
    if (!hasSearchRestoredOrChecked) return;
    if (isSearchChangeInProgress.current) {
      if (pagination.currentPage === 1) {
        isSearchChangeInProgress.current = false;
      }
      return;
    }
    fetchCaseList(pagination.currentPage);
  }, [pagination.currentPage, API_LIMIT, user?.id, currentRole, hasSearchRestoredOrChecked]);

  const headerActions = (
    <div className="flex items-center gap-2">
      <FormButton
        size="sm"
        variant="custom"
        className="text-gray-600 hover:text-gray-800 flex items-center justify-center px-2 py-1 text-xs sm:text-sm"
        onClick={() => fetchCaseList(pagination.currentPage)}
        disabled={loading}
      >
        <span className="flex items-center justify-center w-full">
          <i className={`fas fa-refresh ${loading ? 'animate-spin' : ''} ${window.innerWidth < 640 ? '' : 'mr-2'}`}></i>
          <span className="hidden sm:inline ml-2">Refresh</span>
        </span>
      </FormButton>
      {currentRole === "Customer" && (
      <Link href="/resolve-new">
        <Button
          size="sm"
          className="bg-novaPrimary-500 hover:bg-novaPrimary-600 text-white flex items-center px-2 py-1 text-xs sm:text-sm"
        >
          <i className="fas fa-plus mr-1 sm:mr-2"></i>
          <span>New Case</span>
        </Button>
      </Link>
      )}
    </div>
  );

  type FilterKind = "customer" | "caseNumber";
  const activeFilterItems: { kind: FilterKind; value: string }[] = [
    ...(customerSearch.trim() ? [{ kind: "customer" as const, value: customerSearch.trim() }] : []),
    ...(caseNumberSearch.trim() ? [{ kind: "caseNumber" as const, value: caseNumberSearch.trim() }] : []),
  ];

  const getFilterLabel = (value: string) => value;

  const handleRemoveFilter = useCallback(
    (kind: FilterKind) => {
      if (kind === "customer") {
        setCustomerSearch("");
        setDebouncedCustomer("");
      } else {
        setCaseNumberSearch("");
        setDebouncedCaseNumber("");
      }
      pagination.goToPage(1);
    },
    [pagination]
  );

  const handleClearFilters = useCallback(() => {
    setCustomerSearch("");
    setDebouncedCustomer("");
    setCaseNumberSearch("");
    setDebouncedCaseNumber("");
    sessionStorage.removeItem(SEARCH_STORAGE_KEY);
    pagination.goToPage(1);
  }, [pagination]);

  return (
    <Layout headerActions={headerActions}>
      <div className="p-3 sm:p-4 md:p-6 space-y-3 sm:space-y-4 lg:space-y-6">
        {/* Premium Search Fields */}
        <div className="relative bg-white rounded-lg sticky top-0 z-10 border border-gray-200/50 shadow-lg backdrop-blur-sm">
          {/* Decorative gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-novaPrimary-500/5 via-transparent to-novaPrimary-500/5 pointer-events-none"></div>
          
          <div className="relative p-2 sm:p-3 lg:p-4">
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 lg:gap-5">
              <div className="flex flex-row gap-2 sm:gap-3 lg:gap-5 flex-1">
              {/* Customer Search */}
              <div className="relative flex-1 group">
                <div className="relative">
                  {/* Search Icon */}
                  <div className="absolute left-2 sm:left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-novaPrimary-500 transition-colors duration-300">
                    <i className="fas fa-search text-sm"></i>
                  </div>
                  
                  {/* Input Field */}
                  <input
                    id="customer-search"
                    type="text"
                    placeholder={
                      window.innerWidth < 640
                        ? "Name or email"
                        : "Search for customer name and email"
                    }
                    value={customerSearch}
                    onChange={(e) => setCustomerSearch(e.target.value)}
                    className="w-full pl-7 sm:pl-10 pr-8 sm:pr-12 py-1.5 sm:py-1.5 bg-white border border-gray-400 rounded-md sm:rounded-md shadow-sm text-gray-900 placeholder-gray-400 text-xs sm:text-sm transition-all duration-300 focus:outline-none focus:border-novaPrimary-400 focus:ring-2 sm:focus:ring-4 focus:ring-novaPrimary-100 focus:shadow-xl hover:border-gray-300 hover:shadow-md"
                  />
                  
                  {/* Loading Spinner or Clear Button */}
                  <div className="absolute right-1.5 sm:right-3 top-1/2 transform -translate-y-1/2 flex items-center">
                    {isSearching && customerSearch ? (
                      <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-novaPrimary-500 border-t-transparent"></div>
                    ) : customerSearch ? (
                      <button
                        onClick={() => {
                          setCustomerSearch("");
                          setDebouncedCustomer("");
                        }}
                        className="w-5 h-5 sm:w-7 sm:h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-novaPrimary-100 text-gray-500 hover:text-novaPrimary-600 transition-all duration-200 hover:scale-110 active:scale-95"
                        aria-label="Clear customer search"
                      >
                        <i className="fas fa-times text-[10px] sm:text-xs"></i>
                      </button>
                    ) : null}
                  </div>
                </div>
                
                {/* Focus indicator line */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-novaPrimary-500 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
              </div>

              {/* Case Number Search */}
              <div className="relative flex-1 group">
                <div className="relative">
                  {/* Search Icon */}
                  <div className="absolute left-2 sm:left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-novaPrimary-500 transition-colors duration-300">
                    <i className="fas fa-search text-sm"></i>
                  </div>
                  
                  {/* Input Field */}
                  <input
                    id="case-number-search"
                    type="text"
                    placeholder={
                      window.innerWidth < 640
                        ? "Case number"
                        : "Search for case number"
                    }
                    value={caseNumberSearch}
                    onChange={(e) => {
                      const value = e.target.value;
                      setCaseNumberSearch(value);
                    }}
                    className="w-full pl-7 sm:pl-10 pr-8 sm:pr-12 py-1.5 sm:py-1.5 bg-white border border-gray-400 rounded-md sm:rounded-md shadow-sm text-gray-900 placeholder-gray-400 text-xs sm:text-sm transition-all duration-300 focus:outline-none focus:border-novaPrimary-400 focus:ring-2 sm:focus:ring-4 focus:ring-novaPrimary-100 focus:shadow-xl hover:border-gray-300 hover:shadow-md"
                  />
                  
                  {/* Loading Spinner or Clear Button */}
                  <div className="absolute right-1.5 sm:right-3 top-1/2 transform -translate-y-1/2 flex items-center">
                    {isSearching && caseNumberSearch ? (
                      <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-novaPrimary-500 border-t-transparent"></div>
                    ) : caseNumberSearch ? (
                      <button
                        onClick={() => {
                          setCaseNumberSearch("");
                          setDebouncedCaseNumber("");
                        }}
                        className="w-5 h-5 sm:w-7 sm:h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-novaPrimary-100 text-gray-500 hover:text-novaPrimary-600 transition-all duration-200 hover:scale-110 active:scale-95"
                        aria-label="Clear case number"
                      >
                        <i className="fas fa-times text-[10px] sm:text-xs"></i>
                      </button>
                    ) : null}
                  </div>
                </div>
                
                {/* Focus indicator line */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-novaPrimary-500 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
              </div>
              </div>
            </div>
          </div>
        </div>

        {activeFilterItems.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gray-200 bg-white/70 px-3 py-2 sm:px-4 sm:py-2.5 shadow-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs sm:text-sm font-medium text-gray-500">
                Filters applied
              </span>
              {activeFilterItems.map(({ kind, value }, index) => (
                <span
                  key={`${kind}-${value}-${index}`}
                  className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 pl-3 pr-1.5 py-1 text-xs sm:text-sm text-gray-700"
                >
                  {getFilterLabel(value)}
                  <button
                    type="button"
                    onClick={() => handleRemoveFilter(kind)}
                    className="flex items-center justify-center w-5 h-5 rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
                    aria-label={`Remove ${kind} filter`}
                  >
                    <i className="fas fa-times text-[10px]"></i>
                  </button>
                </span>
              ))}
            </div>
            <button
              onClick={handleClearFilters}
              className="text-xs sm:text-sm font-medium text-novaPrimary-600 hover:text-novaPrimary-700 transition-colors"
            >
              Clear all
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && <PageLoader message="Loading..." />}

        {/* Case List */}
        {!loading && (
          <div className="space-y-4 lg:space-y-6">
            {caseItems.length === 0 ? (
              <DataNotFound message="No cases found" />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 lg:gap-5 xl:gap-6">
                {caseItems.map((item: CaseItem) => (
                  <div
                    key={item.id}
                    className="h-full"
                    onClick={() => {
                      // Mark that we're opening a case so unmount doesn't clear filters (return back keeps filters)
                      sessionStorage.setItem(NAVIGATING_TO_CASE_KEY, THIS_PAGE_KEY);
                      // Save current page before navigating
                      sessionStorage.setItem(PAGINATION_STORAGE_KEY, pagination.currentPage.toString());
                      // Store source page for lawyers (to highlight correct sidebar menu)
                      if (currentRole === "Lawyer") {
                        sessionStorage.setItem("case_source_page", "/missed-cases");
                      }
                    }}
                  >
                    <CaseDashCard item={item} />
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalCount > 0 && (
              <div className="mt-5">
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
    </Layout>
  );
}
