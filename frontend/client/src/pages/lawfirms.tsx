import React, { useState, useEffect } from "react";
import { useRole } from "@/contexts/RoleContext";
import { useLocation } from "wouter";
import { Layout, AddFirmForm, ViewFirmDetails } from "@/components";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { ERROR_TO_EXCLUDE, api } from "@/lib/api";
import { LawFirm, LawFirmApiResponse } from "@/lib/types";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import {
  toastManager,
  createSuccessToast,
  createErrorToast,
} from "@/utils/toasts";
import { Pagination, PaginationConfig } from "@/utils/pagination";
import { FormButton } from "@/utils/formComponents";

type ViewMode = "list" | "add" | "edit" | "view";

interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  recordsPerPage: number;
}

const LawFirmsPage: React.FC = () => {
  const { currentRole } = useRole();
  const [, setLocation] = useLocation();
  const [currentView, setCurrentView] = useState<ViewMode>("list");
  const [selectedFirm, setSelectedFirm] = useState<LawFirm | null>(null);
  const [lawFirms, setLawFirms] = useState<LawFirm[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pagination, setPagination] = useState<PaginationInfo>({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    recordsPerPage: 10,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

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
      loadFirmById(viewId);
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
    fetchLawFirms(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearchTerm, typeFilter]);

  const fetchLawFirms = async (page: number = 1) => {
    setIsLoading(true);
    try {
      const limit = 12;
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(debouncedSearchTerm && { name: debouncedSearchTerm }),
        ...(typeFilter && { law_firm_type: typeFilter }),
      });

      const response = (await api.get(
        `/v1/law-firm?${params}`
      )) as LawFirmApiResponse;

      if (response.success && response.data) {
        const lawFirms = response.data.law_firms || [];
        const totalCount = response.data.total_count || 0;
        const calculatedTotalPages = Math.max(1, Math.ceil(totalCount / limit));
        setLawFirms(lawFirms);
        setPagination({
          currentPage: page,
          totalPages: calculatedTotalPages,
          totalCount: totalCount,
          recordsPerPage: limit,
        });
      } else {
        setLawFirms([]);
        setPagination({
          currentPage: 1,
          totalPages: 1,
          totalCount: 0,
          recordsPerPage: 10,
        });
      }
    } catch (error) {
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

      // Show every message independently (regardless of 'isSuccess')
      if (messageItem.success === true) {
        const toast = createSuccessToast("Success", messageItem.message);
        toastManager.addToast(toast);
      } else if (messageItem.success === false) {
        const toast = createErrorToast("Error", messageItem.message);
        toastManager.addToast(toast);
      } else {
        // fallback: use isSuccess to determine type if property missing
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

  const loadFirmById = async (firmId: string) => {
    try {
      setIsLoading(true);
      const response = await api.get(`/v1/law-firm/${firmId}`);
      if (response && typeof response === "object" && "success" in response) {
        const apiResponse = response as any;
        if (apiResponse.success && apiResponse.data) {
          setSelectedFirm(apiResponse.data);
          setCurrentView("view");
          // if (
          //   Array.isArray(apiResponse.message) &&
          //   apiResponse.message.length > 0
          // ) {
          //   await showToastsWithDelay(apiResponse.message, true);
          // }
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
        // fallback error if response is not as expected
        await showToastsWithDelay(
          [{ message: "Failed to load law firm details", success: false }],
          false
        );
        setCurrentView("list");
      }
    } catch (error: any) {
      const errorMessage =
        (error && error.message) || "Failed to load law firm details";
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
      fetchLawFirms(newPage);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleTypeFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTypeFilter(e.target.value);
  };

  const handleAddClick = () => {
    setCurrentView("add");
    setSelectedFirm(null);
  };

  const handleEditClick = (firm: LawFirm) => {
    setCurrentView("edit");
    setSelectedFirm(firm);
  };

  const handleViewClick = async (firm: LawFirm) => {
    try {
      setIsLoading(true);
      const response = await api.get(`/v1/law-firm/${firm.id}`);
      if (response && typeof response === "object" && "success" in response) {
        const apiResponse = response as any;
        if (apiResponse.success && apiResponse.data) {
          setSelectedFirm(apiResponse.data);
          setCurrentView("view");
        } else {
          toastManager.addToast(
            createErrorToast("Error", "Failed to load law firm details", 3000)
          );
        }
      } else {
        setSelectedFirm(firm);
        setCurrentView("view");
      }
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to load law firm details";
      toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
      setSelectedFirm(firm);
      setCurrentView("view");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToList = () => {
    setCurrentView("list");
    setSelectedFirm(null);
  };

  const handleSubmitFirm = async (
    formData: any,
    firmId?: string
  ): Promise<boolean> => {
    try {
      if (firmId) {
        const updateData = { ...formData, id: firmId };
        const response = (await api.put(`/v1/law-firm`, updateData)) as any;
        if (Array.isArray(response?.message) && response.message.length > 0) {
          await showToastsWithDelay(response.message, !!response.success);
        }
        await fetchLawFirms(pagination.currentPage);
        handleBackToList();
        return !!response?.success;
      } else {
        const response = (await api.post("/v1/law-firm", formData)) as any;
        if (Array.isArray(response?.message) && response.message.length > 0) {
          await showToastsWithDelay(response.message, !!response.success);
        }
        if (response?.success) {
          await fetchLawFirms(pagination.currentPage);
          return true;
        } else {
          return false;
        }
      }
    } catch (error: any) {
      if (
        !ERROR_TO_EXCLUDE.includes(error?.status || error?.response?.status)
      ) {
        const errorMessage = error?.message || "Failed to save law firm";
        toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
      }
      return false;
    }
  };

  const handleDeleteFirm = async (firm: LawFirm) => {
    if (!confirm(`Are you sure you want to delete ${firm.name}?`)) {
      return;
    }

    try {
      await api.delete(`/v1/law-firm/${firm.id}`);
      toastManager.addToast(
        createSuccessToast("Deleted", `${firm.name} has been deleted`, 3000)
      );

      const isLastItemOnPage = lawFirms.length === 1;
      const isNotFirstPage = pagination.currentPage > 1;

      if (isLastItemOnPage && isNotFirstPage) {
        await fetchLawFirms(pagination.currentPage - 1);
      } else {
        await fetchLawFirms(pagination.currentPage);
      }
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to delete law firm";
      toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
    }
  };

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
      headerTitle="Organisations Management"
      headerSubtitle="Manage and oversee organisation partnerships and relationships"
      showBackButton={currentView === "add" || currentView === "edit" || currentView === "view"}
      backButtonLabel="Back to Organisations"
      onBackClick={handleBackToList}
    >
      {/* If not signed in, show DataNotFound inside the Layout */}
      {!currentRole || currentRole.toLowerCase() === "guest" ? (
        <div className="w-full h-full flex items-center justify-center">
          <DataNotFound message="You must be signed in to view organisations." />
        </div>
      ) : (
        <div className="bg-novaInactive h-full flex flex-col">
          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

              {/* Conditional Rendering: Show Add/Edit/View/List */}
              {currentView === "add" && (
                <AddFirmForm
                  mode="add"
                  onCancel={handleBackToList}
                  onSubmit={handleSubmitFirm}
                />
              )}

              {currentView === "edit" && selectedFirm && (
                <AddFirmForm
                  mode="edit"
                  firmData={selectedFirm}
                  onCancel={handleBackToList}
                  onSubmit={handleSubmitFirm}
                />
              )}

              {currentView === "view" && selectedFirm && (
                <ViewFirmDetails
                  firmData={selectedFirm}
                  onClose={handleBackToList}
                  onEdit={() => handleEditClick(selectedFirm)}
                  isLoading={isLoading}
                />
              )}

              {currentView === "list" && (
                <>
                  {/* Stats Cards with Action Button */}
                  <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 flex-1 min-w-[200px]">
                      <div className="bg-white rounded-md border border-novaActive p-3">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-white rounded-md flex items-center justify-center border border-novaActive">
                              <i className="fas fa-building text-novaDarkOrange text-xs"></i>
                            </div>
                          </div>
                          <div className="ml-3">
                            <p className="text-xs font-medium text-novaNeutral-500">
                              Total Organisations
                            </p>
                            <p className="text-lg font-semibold text-novaNeutral-900">
                              {pagination.totalCount}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Add Firm Button */}
                    <FormButton
                      onClick={handleAddClick}
                      variant="gradient"
                      className="bg-novaPrimary-500 hover:bg-novaPrimary-600 text-white px-4 py-2 text-sm transition-colors whitespace-nowrap"
                    >
                      <i className="fas fa-plus mr-1.5"></i>
                      Add Organisation
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
                            placeholder="Search by name"
                            className="w-full pl-8 pr-8 py-2 text-sm border border-novaNeutral-300 rounded-md focus:ring-0 focus:ring-novaPrimary-500 focus:border-novaPrimary-500"
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
                        value={typeFilter}
                        onChange={(value) => {
                          setTypeFilter(value);
                          setPagination((prev) => ({ ...prev, currentPage: 1 }));
                        }}
                        options={[
                          { value: "", label: "All Types" },
                          { value: "Solo practitioner", label: "Solo practitioner" },
                          { value: "Boutique", label: "Boutique" },
                          { value: "Multi-speciality", label: "Multi-speciality" },
                        ]}
                        placeholder="All Types"
                        triggerClassName="min-w-[160px] rounded-md border border-novaActive"
                      />
                    </div>
                  </div>

                  {/* Law Firms Table */}
                  <div className="bg-white rounded-md border border-novaActive overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-novaActive">
                        <thead className="bg-novaActive">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider w-1/4">
                              Name
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider w-1/4">
                              Location
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider w-1/4">
                              Type
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider w-1/4">
                              Status
                            </th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-novaPrimary-600 uppercase tracking-wider w-1/4">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-novaActive">
                          {isLoading ? (
                            <tr>
                              <td
                                colSpan={5}
                                className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                              >
                                <div className="flex justify-center items-center">
                                  <i className="fas fa-spinner fa-spin mr-2"></i>
                                  Loading Organisations...
                                </div>
                              </td>
                            </tr>
                          ) : lawFirms.length === 0 ? (
                            <tr>
                              <td
                                colSpan={5}
                                className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                              >
                                No Organisations found.
                              </td>
                            </tr>
                          ) : (
                            lawFirms.map((firm) => (
                              <tr
                                key={firm.id}
                              onClick={() => handleViewClick(firm)}
                              className="hover:bg-novaInactive cursor-pointer transition-colors"
                              >
                                <td className="px-3 py-2 whitespace-nowrap w-1/4">
                                  <div className="flex items-center gap-2">
                                    <div className="flex-shrink-0 flex h-6 w-6 items-center justify-center">
                                      <div className="h-6 w-6 rounded-full bg-white flex items-center justify-center border border-novaDarkOrange">
                                        {firm.logos?.thumbnail ? (
                                          <img
                                            src={firm.logos?.thumbnail}
                                            alt={`${firm.name} logo`}
                                            className="h-6 w-6 rounded-full object-cover border border-novaDarkOrange"
                                            onError={(e) => {
                                              (
                                                e.currentTarget as HTMLImageElement
                                              ).style.display = "none";
                                            }}
                                          />
                                        ) : (
                                          <i className="fas fa-building text-novaDarkOrange text-xs"></i>
                                        )}
                                      </div>
                                    </div>
                                    <span className="text-[13px] font-medium text-novaNeutral-900 truncate max-w-[200px]">
                                      {firm.name}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-3 py-2 text-[12px] text-novaNeutral-500 w-1/4 max-w-[180px]">
                                  <span className="block truncate" title={[firm.state, firm.country].filter(Boolean).join(", ") || undefined}>
                                    {[firm.state, firm.country]
                                      .filter(Boolean)
                                      .join(", ") || "—"}
                                  </span>
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap w-1/4">
                                  <div className="flex flex-wrap gap-0.5">
                                    <span className="inline-flex px-1.5 py-0.5 text-[11px] font-medium bg-novaInactive text-novaNeutral-900 rounded-full">
                                      {firm.law_firm_type}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-left w-1/4">
                                  <span
                                    className={`inline-flex px-2 py-0.5 text-[11px] font-medium rounded-full ${
                                      firm.status?.toLowerCase() === "active"
                                        ? "bg-novaSuccess-100 text-novaSuccess-800"
                                        : "bg-novaWarning-100 text-novaWarning-600"
                                    }`}
                                  >
                                    {firm.status || "Active"}
                                  </span>
                                </td>
                                <td className="px-4 py-1 whitespace-nowrap text-right text-[12px] font-medium w-1/4">
                                  <div className="flex items-center justify-end gap-2">
                                    {/* View Button */}
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleViewClick(firm);
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
                                        handleEditClick(firm);
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

export default LawFirmsPage;
