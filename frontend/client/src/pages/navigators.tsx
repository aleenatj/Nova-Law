import React, { useEffect, useState, useCallback } from "react";
import { Layout } from "@/components";
import { AddNavigatorForm, ViewNavigatorDetails } from "@/components/navigator";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { useAuth } from "@/contexts/AuthContext";
import { useRole } from "@/contexts/RoleContext";
import { useLocation } from "wouter";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import {
  Navigator,
  NavigatorFormData,
  NavigatorSearchApiResponse,
} from "@/lib/types";
import { api, ERROR_TO_EXCLUDE } from "@/lib/api";
import {
  toastManager,
  createSuccessToast,
  createErrorToast,
} from "@/utils/toasts";
import { Pagination, PaginationConfig } from "@/utils/pagination";
import { FormButton } from "@/utils/formComponents";

const getName = (navigator: Navigator) =>
  `${navigator.first_name || ""} ${navigator.last_name || ""}`.trim() || "—";

type ViewMode = "list" | "add" | "edit" | "view";

interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  recordsPerPage: number;
}

const NavigatorsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [currentView, setCurrentView] = useState<ViewMode>("list");
  const [selectedNavigator, setSelectedNavigator] = useState<Navigator | null>(
    null
  );
  const [navigators, setNavigators] = useState<Navigator[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [pagination, setPagination] = useState<PaginationInfo>({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    recordsPerPage: 12,
  });
  const { currentRole } = useRole();
  const { refreshUserFromStorage } = useAuth();
  const [, setLocation] = useLocation();

  // Fetch navigators from API
  const fetchNavigators = useCallback(
    async (page: number = 1) => {
      setIsLoading(true);
      try {
        const limit = 12;
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString(),
          ...(debouncedSearchTerm && { search_term: debouncedSearchTerm }),
          ...(statusFilter && { status: statusFilter }),
        });

        const response = (await api.get(
          `/v1/navigator?${params}`
        )) as NavigatorSearchApiResponse;

        if (response.success) {
          setNavigators(response.data.users);
          setPagination({
            currentPage: page,
            totalPages: Math.max(
              1,
              Math.ceil((response.data.total_count || 0) / limit)
            ),
            totalCount: response.data.total_count || 0,
            recordsPerPage: limit,
          });
        } else {
          toastManager.addToast(
            createErrorToast("Failed to fetch navigators", "error")
          );
          setNavigators([]);
          setPagination({
            currentPage: 1,
            totalPages: 1,
            totalCount: 0,
            recordsPerPage: 12,
          });
        }
      } catch (error) {
        console.error("Error fetching navigators:", error);
        toastManager.addToast(
          createErrorToast("Failed to fetch navigators", "error")
        );
        setNavigators([]);
        setPagination({
          currentPage: 1,
          totalPages: 1,
          totalCount: 0,
          recordsPerPage: 12,
        });
      } finally {
        setIsLoading(false);
      }
    },
    [debouncedSearchTerm, statusFilter]
  );

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearchTerm(searchTerm), 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Fetch data when debounced search term or status filter changes
  useEffect(() => {
    fetchNavigators(1);
  }, [debouncedSearchTerm, statusFilter, fetchNavigators]);

  // Redirect if not a Navigator
  useEffect(() => {
    if (
      currentRole &&
      currentRole !== "Guest" &&
      currentRole.toLowerCase() !== "navigator"
    ) {
      setLocation("/dashboard");
    }
  }, [currentRole, setLocation]);

  // Fetch navigators on component mount
  useEffect(() => {
    if (currentRole && currentRole.toLowerCase() === "navigator") {
      fetchNavigators(1);
    }
  }, [currentRole]);

  // If not signed in (Guest), render DataNotFound inside Layout like lawfirms page
  if (currentRole.toLowerCase() === "guest" || !currentRole) {
    return (
      <Layout
        headerTitle="Navigators Management"
        headerSubtitle="Manage and oversee Nova Navigators"
      >
        <div className="py-16">
          <DataNotFound
            message="Data Not Found"
            hint="You must be signed in to view this page."
          />
        </div>
      </Layout>
    );
  }

  // Handler functions
  const handleBackToList = () => {
    setCurrentView("list");
    setSelectedNavigator(null);
  };

  const handleAddNavigator = () => {
    setCurrentView("add");
  };

  const handleEditNavigator = async (navigator: Navigator) => {
    try {
      setIsLoading(true);
      const response = (await api.get(`/v1/navigator/${navigator.id}`)) as any;
      if (response?.success && response.data) {
        setSelectedNavigator(response.data);
        setCurrentView("edit");
      } else {
        toastManager.addToast(
          createErrorToast("Error", "Failed to load navigator details", 2000)
        );
        // Fallback to using the navigator from the list
        setSelectedNavigator(navigator);
        setCurrentView("edit");
      }
    } catch (error: any) {
      console.warn(`Failed to fetch navigator details for editing:`, error);
      toastManager.addToast(
        createErrorToast(
          "Error",
          error?.message || "Failed to load navigator details",
          2000
        )
      );
      // Fallback to using the navigator from the list
      setSelectedNavigator(navigator);
      setCurrentView("edit");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewClick = async (navigator: Navigator) => {
    try {
      setIsLoading(true);
      const response = (await api.get(`/v1/navigator/${navigator.id}`)) as any;
      if (response?.success && response.data) {
        setSelectedNavigator(response.data);
        setCurrentView("view");
      } else {
        toastManager.addToast(
          createErrorToast("Error", "Failed to load navigator details", 2000)
        );
      }
    } catch (error: any) {
      toastManager.addToast(
        createErrorToast(
          "Error",
          error?.message || "Failed to load navigator details",
          2000
        )
      );
      setSelectedNavigator(navigator);
      setCurrentView("view");
    } finally {
      setIsLoading(false);
    }
  };

  const showToastsWithDelay = async (
    messages: Array<{ message: string; success?: boolean }>,
    isSuccess: boolean
  ) => {
    const delay = 400; // ms
    for (let i = 0; i < messages.length; i++) {
      const messageItem = messages[i];
      await new Promise((resolve) => setTimeout(resolve, i === 0 ? 0 : delay));

      if (messageItem.success === true) {
        const toast = createSuccessToast("Success", messageItem.message);
        toastManager.addToast(toast);
      } else if (messageItem.success === false) {
        const toast = createErrorToast("Error", messageItem.message);
        toastManager.addToast(toast);
      } else {
        // fallback: use isSuccess if property missing
        if (isSuccess) {
          const toast = createSuccessToast("Success", messageItem.message);
          toastManager.addToast(toast);
        } else {
          const toast = createErrorToast("Error", messageItem.message);
          toastManager.addToast(toast);
        }
      }
    }
  };

  const handleSubmitNavigator = async (
    data: NavigatorFormData,
    navigatorId?: string
  ): Promise<boolean> => {
    try {
      if (navigatorId) {
        // Update existing navigator
        const response = (await api.put(`/v1/navigator`, {
          ...data,
          user_id: navigatorId,
        })) as any;
        if (Array.isArray(response?.message) && response.message.length > 0) {
          await showToastsWithDelay(response.message, !!response.success);
        }
        if (response?.success) {
          // If the updated navigator is the current user, sync auth/profile so header and Profile page show new name
          try {
            const savedUser = localStorage.getItem("user");
            if (savedUser) {
              const parsed = JSON.parse(savedUser);
              const currentUserId = parsed.user_id || parsed.id || "";
              if (currentUserId && String(currentUserId) === String(navigatorId)) {
                parsed.first_name = data.first_name ?? parsed.first_name;
                parsed.last_name = data.last_name ?? parsed.last_name;
                localStorage.setItem("user", JSON.stringify(parsed));
                refreshUserFromStorage();
              }
            }
          } catch (e) {
            console.error("Error syncing current user after navigator update:", e);
          }
        }
        await fetchNavigators(pagination.currentPage);
        handleBackToList();
        return !!response.success;
      } else {
        // Create new navigator
        const response = (await api.post("/v1/navigator", data)) as any;
        if (Array.isArray(response?.message) && response.message.length > 0) {
          await showToastsWithDelay(response.message, !!response.success);
        }
        if (response?.success) {
          await fetchNavigators(pagination.currentPage);
          return true;
        } else {
          return false;
        }
      }
    } catch (error: any) {
      if (!ERROR_TO_EXCLUDE.includes(error?.status || error?.response?.status)) {
        const errorMessage = error?.message || "Failed to save navigator";
        toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
      }
      return false;
    }
  };

  return (
    <Layout
      headerTitle="Navigators Management"
      headerSubtitle="Manage and oversee navigator profiles and information"
      showBackButton={currentView === "add" || currentView === "edit" || currentView === "view"}
      backButtonLabel="Back to Navigators"
      onBackClick={handleBackToList}
    >
      <div className="bg-novaInactive h-full flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-6">

            {currentView === "view" && (
              <ViewNavigatorDetails
                navigatorData={selectedNavigator}
                onClose={handleBackToList}
                onEdit={() =>
                  selectedNavigator && handleEditNavigator(selectedNavigator)
                }
                isLoading={isLoading}
              />
            )}

            {currentView === "add" && (
              <AddNavigatorForm
                mode="add"
                onCancel={handleBackToList}
                onSubmit={handleSubmitNavigator}
              />
            )}

            {currentView === "edit" && selectedNavigator && (
              <AddNavigatorForm
                mode="edit"
                navigatorData={selectedNavigator}
                onCancel={handleBackToList}
                onSubmit={handleSubmitNavigator}
              />
            )}

            {currentView === "list" && (
              <>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 flex-1 w-full">
                    <div className="bg-white rounded-md border border-novaActive p-3 w-full">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="w-6 h-6 bg-white rounded-md flex items-center justify-center border border-novaActive">
                            <i className="fas fa-user-friends text-novaDarkOrange text-xs"></i>
                          </div>
                        </div>
                        <div className="ml-3">
                          <p className="text-xs font-medium text-novaNeutral-500">
                            Total Navigators
                          </p>
                          <p className="text-lg font-semibold text-novaNeutral-900 break-words">
                            {pagination.totalCount}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <FormButton
                    onClick={handleAddNavigator}
                    variant="gradient"
                    className="w-full sm:w-auto text-white px-4 py-2 text-sm transition-colors whitespace-nowrap mt-3 sm:mt-0"
                  >
                    <i className="fas fa-plus mr-1.5"></i>
                    Add Navigator
                  </FormButton>
                </div>

                {/* Filters and Search */}
                <div className="bg-white rounded-md border border-novaActive p-3 mb-3">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                      <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-novaNeutral-400 pointer-events-none">
                          <i className="fas fa-search text-xs"></i>
                        </span>
                        <input
                          type="text"
                          placeholder="Search by name or email"
                          className="w-full pl-8 pr-8 py-2 text-sm border border-novaNeutral-300 rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        {searchTerm && (
                          <button
                            type="button"
                            onClick={() => setSearchTerm("")}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-novaNeutral-400 hover:text-novaNeutral-600 focus:outline-none"
                            tabIndex={-1}
                            aria-label="Clear search"
                          >
                            <i className="fas fa-times text-xs"></i>
                          </button>
                        )}
                      </div>
                    </div>
                    <CustomSelect
                      value={statusFilter}
                      onChange={(value) => {
                        setStatusFilter(value);
                        setPagination((prev) => ({ ...prev, currentPage: 1 }));
                      }}
                      options={[
                        { value: "", label: "All Status" },
                        { value: "Active", label: "Active" },
                        { value: "Inactive", label: "Inactive" },
                      ]}
                      placeholder="All Status"
                      triggerClassName="min-w-[140px] rounded-md"
                    />
                  </div>
                </div>

                {/* Navigators Table */}
                <div className="bg-white rounded-md border border-novaActive overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-novaActive">
                      <thead className="bg-novaActive">
                        <tr>
                          <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[95px]">
                            Name
                          </th>
                          <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[120px]">
                            Email
                          </th>
                          <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[80px]">
                            Phone
                          </th>
                          <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[75px]">
                            Gender
                          </th>
                          <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[70px]">
                            Status
                          </th>
                          <th className="px-2 sm:px-3 py-2 text-right text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[55px]">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-novaActive">
                        {isLoading ? (
                          <tr>
                            <td
                              colSpan={6}
                              className="px-3 py-8 text-center text-sm text-novaNeutral-500"
                            >
                              <div className="flex items-center justify-center">
                                <i className="fas fa-spinner fa-spin mr-2"></i>
                                Loading navigators...
                              </div>
                            </td>
                          </tr>
                        ) : navigators.length === 0 ? (
                          <tr>
                            <td
                              colSpan={6}
                              className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                            >
                              No navigators found.
                            </td>
                          </tr>
                        ) : (
                          navigators.map((navigator) => (
                            <tr
                              key={navigator.id}
                              onClick={() => handleViewClick(navigator)}
                              className="hover:bg-novaInactive cursor-pointer transition-colors"
                            >
                              <td className="px-2 sm:px-3 py-2">
                                <div className="flex items-center gap-2 min-w-0">
                                  <div className="h-6 w-6 rounded-full bg-white flex items-center justify-center flex-shrink-0 border border-novaActive">
                                    <i className="fas fa-user text-novaDarkOrange text-xs"></i>
                                  </div>
                                  <span
                                    className="text-[13px] font-medium text-novaNeutral-900 truncate block max-w-[85vw] sm:max-w-[180px] md:max-w-[220px] lg:max-w-[320px]"
                                    title={getName(navigator)}
                                  >
                                    {getName(navigator)}
                                  </span>
                                </div>
                              </td>
                              <td
                                className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-500 max-w-[60vw] sm:max-w-[140px] truncate"
                                title={navigator.email}
                              >
                                {navigator.email}
                              </td>
                              <td
                                className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-500 max-w-[27vw] sm:max-w-[80px] truncate"
                                title={navigator.phone || "—"}
                              >
                                {navigator.phone || "—"}
                              </td>
                              <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-500 whitespace-nowrap">
                                {navigator.gender || "—"}
                              </td>
                              <td className="px-2 sm:px-3 py-2 text-left">
                                <span
                                  className={`inline-flex px-2 py-0.5 text-[11px] font-medium rounded-full ${
                                    navigator.status?.toLowerCase() === "active"
                                      ? "bg-novaSuccess-100 text-novaSuccess-800"
                                      : "bg-novaWarning-100 text-novaWarning-600"
                                  }`}
                                >
                                  {navigator.status || "—"}
                                </span>
                              </td>
                              <td className="px-2 sm:px-4 py-1 text-right text-[12px] font-medium">
                                <div className="flex items-center justify-end gap-2">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleViewClick(navigator);
                                    }}
                                    className="p-1.5 text-novaGray-500 hover:text-novaNeutral-900 hover:bg-novaNeutral-100 rounded transition-colors"
                                    title="View Details"
                                  >
                                    <i className="fa-solid fa-eye text-sm"></i>
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleEditNavigator(navigator);
                                    }}
                                    className="p-1.5 text-novaPrimary-500 hover:text-novaNeutral-900 hover:bg-novaNeutral-100 rounded transition-colors"
                                    title="Edit"
                                  >
                                    <i className="fas fa-edit text-sm"></i>
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {pagination.totalCount > 0 && (
                    <div className="bg-white px-4 py-3 border-t border-novaActive">
                      <Pagination
                        config={{
                          currentPage: Math.max(
                            1,
                            Math.min(
                              pagination.currentPage,
                              pagination.totalPages
                            )
                          ),
                          totalPages: Math.max(1, pagination.totalPages),
                          totalItems: Math.max(0, pagination.totalCount),
                          itemsPerPage: Math.max(1, pagination.recordsPerPage),
                          onPageChange: (newPage) =>
                            newPage >= 1 &&
                            newPage <= pagination.totalPages &&
                            fetchNavigators(newPage),
                        }}
                      />
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default NavigatorsPage;
