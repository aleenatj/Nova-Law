import React, { useState, useEffect } from "react";
import { useRole } from "@/contexts/RoleContext";
import { useLocation } from "wouter";
import { Layout } from "@/components";
import { EditLegalExpertForm, ViewLegalExpertDetails } from "@/components/legal-expert";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { ERROR_TO_EXCLUDE, api } from "@/lib/api";
import { LegalExpert, LegalExpertSearchApiResponse, LegalExpertFormData } from "@/lib/types";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import {
  toastManager,
  createSuccessToast,
  createErrorToast,
} from "@/utils/toasts";
import { Pagination, PaginationConfig } from "@/utils/pagination";
import { formatTimestamp } from "@/utils";
import { toTitleCase } from "@/lib/utils";

type ViewMode = "list" | "edit" | "view";

interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  recordsPerPage: number;
}

const LegalExpertsPage: React.FC = () => {
  const { currentRole } = useRole();
  const [, setLocation] = useLocation();
  const [currentView, setCurrentView] = useState<ViewMode>("list");
  const [selectedExpert, setSelectedExpert] = useState<LegalExpert | null>(null);
  const [legalExperts, setLegalExperts] = useState<LegalExpert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pagination, setPagination] = useState<PaginationInfo>({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    recordsPerPage: 12,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Redirect if not a Navigator (only after role is loaded)
  useEffect(() => {
    if (
      currentRole &&
      currentRole !== "Guest" &&
      currentRole.toLowerCase() !== "navigator"
    ) {
      setLocation("/dashboard");
    }
  }, [currentRole, setLocation]);

  // Don't render anything if not a Navigator (but allow initial load)
  if (
    currentRole &&
    currentRole !== "Guest" &&
    currentRole.toLowerCase() !== "navigator"
  ) {
    return null;
  }

  // Check for URL parameters on mount to handle direct navigation
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const viewId = params.get("view");

    if (viewId) {
      loadExpertById(viewId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Fetch data when debounced search term or filters change
  useEffect(() => {
    fetchLegalExperts(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearchTerm, statusFilter]);

  const fetchLegalExperts = async (page: number = 1) => {
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
        `/v1/B2C-experts?${params}`
      )) as LegalExpertSearchApiResponse;

      if (response.success && response.data) {
        const experts = response.data.lawyers || [];
        const totalCount = response.data.total_count || 0;
        const calculatedTotalPages = Math.max(1, Math.ceil(totalCount / limit));
        setLegalExperts(experts);
        setPagination({
          currentPage: page,
          totalPages: calculatedTotalPages,
          totalCount: totalCount,
          recordsPerPage: limit,
        });
      } else {
        setLegalExperts([]);
        setPagination({
          currentPage: 1,
          totalPages: 1,
          totalCount: 0,
          recordsPerPage: 12,
        });
      }
    } catch (error) {
      console.error("Error fetching Nova experts:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Show all messages as toasts, one after another, with a slight delay
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

  const loadExpertById = async (expertId: string) => {
    try {
      setIsLoading(true);
      const response = await api.get(`/v1/B2C-experts/${expertId}`);
      if (response && typeof response === "object" && "success" in response) {
        const apiResponse = response as any;
        if (apiResponse.success && apiResponse.data) {
          setSelectedExpert(apiResponse.data);
          setCurrentView("view");
          if (
            Array.isArray(apiResponse.message) &&
            apiResponse.message.length > 0
          ) {
            await showToastsWithDelay(apiResponse.message, true);
          }
        } else {
          if (
            Array.isArray(apiResponse.message) &&
            apiResponse.message.length > 0
          ) {
            await showToastsWithDelay(apiResponse.message, false);
          }
          setCurrentView("list");
        }
      } else {
        await showToastsWithDelay(
          [{ message: "Failed to load Nova expert details", success: false }],
          false
        );
        setCurrentView("list");
      }
    } catch (error: any) {
      const errorMessage =
        (error && error.message) || "Failed to load Nova expert details";
      await showToastsWithDelay(
        [{ message: errorMessage, success: false }],
        false
      );
      setCurrentView("list");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.totalPages) {
      fetchLegalExperts(newPage);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };

  const handleEditClick = async (expert: LegalExpert) => {
    try {
      setIsLoading(true);
      const response = await api.get(`/v1/B2C-experts/${expert.id}`);
      if (response && typeof response === "object" && "success" in response) {
        const apiResponse = response as any;
        if (apiResponse.success && apiResponse.data) {
          setSelectedExpert(apiResponse.data);
          setCurrentView("edit");
        } else {
          // Fallback to using existing data
          setSelectedExpert(expert);
          setCurrentView("edit");
        }
      } else {
        setSelectedExpert(expert);
        setCurrentView("edit");
      }
    } catch (error: any) {
      // Fallback to using existing data if API call fails
      setSelectedExpert(expert);
      setCurrentView("edit");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewClick = async (expert: LegalExpert) => {
    try {
      setIsLoading(true);
      const response = await api.get(`/v1/B2C-experts/${expert.id}`);
      if (response && typeof response === "object" && "success" in response) {
        const apiResponse = response as any;
        if (apiResponse.success && apiResponse.data) {
          setSelectedExpert(apiResponse.data);
          setCurrentView("view");
        } else {
          toastManager.addToast(
            createErrorToast("Error", "Failed to load Nova expert details", 3000)
          );
        }
      } else {
        setSelectedExpert(expert);
        setCurrentView("view");
      }
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to load Nova expert details";
      toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
      setSelectedExpert(expert);
      setCurrentView("view");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToList = () => {
    setCurrentView("list");
    setSelectedExpert(null);
  };

  const handleSubmitExpert = async (
    formData: LegalExpertFormData,
    expertId?: string
  ): Promise<boolean> => {
    try {
      if (expertId) {
        const updateData = { ...formData, id: expertId };
        const response = await api.patch(`/v1/B2C-experts`, updateData);
        
        if (response && typeof response === "object" && "success" in response) {
          const apiResponse = response as any;
          if (apiResponse.success) {
            toastManager.addToast(
              createSuccessToast("Updated", "Nova expert updated successfully", 3000)
            );
            await fetchLegalExperts(pagination.currentPage);
            handleBackToList();
            return true;
          } else {
            const message = apiResponse.message?.[0]?.message || "Failed to update Nova expert";
            toastManager.addToast(createErrorToast("Failed", message, 3000));
            return false;
          }
        }
        return false;
      }
      return false;
    } catch (error: any) {
      if (
        !ERROR_TO_EXCLUDE.includes(error?.status || error?.response?.status)
      ) {
        const errorMessage = error?.message || "Failed to save Nova expert";
        toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
      }
      return false;
    }
  };

  const getFullName = (expert: LegalExpert) =>
    `${expert.first_name || ""} ${expert.last_name || ""}`.trim() || "—";

  const paginationConfig: PaginationConfig = {
    currentPage: Math.max(
      1,
      Math.min(pagination.currentPage, pagination.totalPages)
    ),
    totalPages: Math.max(1, pagination.totalPages),
    totalItems: Math.max(0, pagination.totalCount),
    itemsPerPage: Math.max(1, pagination.recordsPerPage),
    onPageChange: handlePageChange,
  };

  return (
    <Layout
      headerTitle="Nova Experts Management"
      headerSubtitle="Review and manage B2C Nova Experts applications"
      showBackButton={currentView === "edit" || currentView === "view"}
      backButtonLabel="Back to Nova Experts"
      onBackClick={handleBackToList}
    >
      {/* If not signed in, show DataNotFound inside the Layout */}
      {!currentRole || currentRole.toLowerCase() === "guest" ? (
        <div className="w-full h-full flex items-center justify-center">
          <DataNotFound message="You must be signed in to view Nova Experts." />
        </div>
      ) : (
        <div className="bg-novaInactive h-full flex flex-col">
          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

              {/* Conditional Rendering: Show Edit/View/List */}
              {currentView === "edit" && selectedExpert && (
                <EditLegalExpertForm
                  expertData={selectedExpert}
                  onCancel={handleBackToList}
                  onSubmit={handleSubmitExpert}
                />
              )}

              {currentView === "view" && selectedExpert && (
                <ViewLegalExpertDetails
                  expertData={selectedExpert}
                  onClose={handleBackToList}
                  onEdit={() => handleEditClick(selectedExpert)}
                  onStatusUpdate={(updatedExpert) => {
                    setSelectedExpert(updatedExpert);
                    // Refresh the list to reflect the status change
                    fetchLegalExperts(pagination.currentPage);
                  }}
                  isLoading={isLoading}
                />
              )}

              {currentView === "list" && (
                <>
                  {/* Stats Cards */}
                  <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 flex-1 min-w-[200px]">
                      <div className="bg-white rounded-md border border-novaActive p-3">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-white rounded-md flex items-center justify-center border border-novaActive">
                              <i className="fas fa-user text-novaDarkOrange text-xs"></i>
                            </div>
                          </div>
                          <div className="ml-3">
                            <p className="text-xs font-medium text-novaNeutral-500">
                              Total Applications
                            </p>
                            <p className="text-lg font-semibold text-novaNeutral-900">
                              {pagination.totalCount}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
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
                            onChange={handleSearch}
                          />
                          {searchTerm && (
                            <button
                              type="button"
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-novaNeutral-400 hover:text-novaNeutral-600 focus:outline-none"
                              onClick={() => setSearchTerm("")}
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
                          { value: "New", label: "New" },
                          { value: "Review", label: "Review" },
                          { value: "Onboarded", label: "Onboarded" },
                          { value: "Rejected", label: "Rejected" },
                        ]}
                        placeholder="All Status"
                        triggerClassName="min-w-[140px] rounded-md"
                      />
                    </div>
                  </div>

                  {/* Nova Experts Table */}
                  <div className="bg-white rounded-md border border-novaActive overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-novaActive">
                        <thead className="bg-novaActive">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              Name
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              Email
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              City
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              Experience
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              Status
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              Created At
                            </th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-novaActive">
                          {isLoading ? (
                            <tr>
                              <td
                                colSpan={6}
                                className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                              >
                                <div className="flex justify-center items-center">
                                  <i className="fas fa-spinner fa-spin mr-2"></i>
                                  Loading Nova Experts...
                                </div>
                              </td>
                            </tr>
                          ) : legalExperts.length === 0 ? (
                            <tr>
                              <td
                                colSpan={6}
                                className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                              >
                                No Nova Expert applications found.
                              </td>
                            </tr>
                          ) : (
                            legalExperts.map((expert) => (
                              <tr
                                key={expert.id}
                                onClick={() => handleViewClick(expert)}
                                className="hover:bg-novaInactive cursor-pointer transition-colors"
                              >
                                <td className="px-3 py-2 whitespace-nowrap">
                                  <div className="flex items-center gap-2">
                                    <div className="flex-shrink-0 flex h-6 w-6 items-center justify-center">
                                      <div className="h-6 w-6 rounded-full bg-white flex items-center justify-center border border-novaActive">
                                        {expert.photo_url?.thumbnail ? (
                                          <img
                                            src={expert.photo_url?.thumbnail}
                                            alt={`${getFullName(expert)} photo`}
                                            className="h-6 w-6 rounded-full object-cover border border-novaDarkOrange"
                                            onError={(e) => {
                                              (
                                                e.currentTarget as HTMLImageElement
                                              ).style.display = "none";
                                            }}
                                          />
                                        ) : (
                                          <i className="fas fa-user text-novaDarkOrange text-xs"></i>
                                        )}
                                      </div>
                                    </div>
                                    <span className="text-[13px] font-medium text-novaNeutral-900 truncate">
                                      {toTitleCase(getFullName(expert) || "")}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                  {expert.email || "—"}
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                  {expert.city || "—"}
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                  {expert.experience ? `${expert.experience} years` : "—"}
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-left">
                                  <span
                                    className={`inline-flex px-2 py-0.5 text-[11px] font-medium rounded-full ${
                                      expert.status === "Onboarded"
                                        ? "bg-novaSuccess-100 text-novaSuccess-800"
                                        : expert.status === "New"
                                        ? "bg-novaPurple-100 text-novaPurple-800"
                                        : expert.status === "Review"
                                        ? "bg-novaAlert-100 text-novaAlert-800"
                                        : expert.status === "Rejected"
                                        ? "bg-novaCaution-100 text-novaCaution-800"
                                        : "bg-novaWarning-100 text-novaWarning-800"
                                    }`}
                                  >
                                    {expert.status || "New"}
                                  </span>
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                  {expert.created_at
                                    ? formatTimestamp(expert.created_at) : "—"}
                                </td>
                                <td className="px-4 py-1 whitespace-nowrap text-right text-[12px] font-medium">
                                  <div className="flex items-center justify-end gap-2">
                                    {/* View Button */}
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleViewClick(expert);
                                      }}
                                      className="p-1.5 text-novaGray-500 hover:text-novaNeutral-900 hover:bg-novaNeutral-100 rounded transition-colors"
                                      title="View Details"
                                    >
                                      <i className="fa-solid fa-eye text-sm"></i>
                                    </button>

                                    {/* Edit Button */}
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleEditClick(expert);
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
                        <Pagination config={paginationConfig} />
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default LegalExpertsPage;
