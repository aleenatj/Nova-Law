import React, { useState, useEffect } from "react";
import { useRole } from "@/contexts/RoleContext";
import { useLocation } from "wouter";
import { Layout, AddLawyerForm, ViewLawyerDetails } from "@/components";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { ERROR_TO_EXCLUDE, api } from "@/lib/api";
import { Lawyer, LawyerSearchApiResponse, LawyerFormData } from "@/lib/types";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import {toastManager, createSuccessToast, createErrorToast,} from "@/utils/toasts";
import { Pagination, PaginationConfig } from "@/utils/pagination";
import { FormButton } from "@/utils/formComponents";

type ViewMode = "list" | "add" | "edit" | "view";

interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  recordsPerPage: number;
}

// Interface for pre-filled data from legal expert onboarding
interface LegalExpertPreFillData {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  gender?: string;
  city?: string;
  postal_code?: string;
  photo_url?: string;
  photo_preview_url?: string;
  about?: string;
  testimonial?: string;
  accredited_specialisations?: string[]; // Changed to array for key-based mapping
  accredited_specialism_other?: string[] | null;
  dr_preferences?: string[]; // Changed to array for key-based mapping
  professional_status?: { values?: string[]; other?: string | null };
  regulator?: string;
  regulator_other?: string | null;
  relationship_types?: string[]; // From service_details.offers
  expertises?: {
    cohabitees?: { expertises?: string[]; other?: string[] };
    married_civil_partners?: { expertises?: string[]; other?: string[] };
  };
  matter_types?: string[]; // If available
  conflict_level_disinclination?: string; // If available
  legal_expert_id?: string;
  reference_id?: string;
}

const LawyersPage: React.FC = () => {
  const { currentRole } = useRole();
  const [, setLocation] = useLocation();
  const [currentView, setCurrentView] = useState<ViewMode>("list");
  const [selectedLawyer, setSelectedLawyer] = useState<Lawyer | null>(null);
  const [lawyers, setLawyers] = useState<Lawyer[]>([]);
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
  const [preFillData, setPreFillData] = useState<LegalExpertPreFillData | null>(null);

  // Check for onboard_from_expert query parameter on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isOnboarding = params.get("onboard_from_expert");

    if (isOnboarding === "true") {
      // Retrieve pre-fill data from sessionStorage
      const storedData = sessionStorage.getItem("legal_expert_onboard_data");
      if (storedData) {
        try {
          const parsedData = JSON.parse(storedData) as LegalExpertPreFillData;
          setPreFillData(parsedData);
          setCurrentView("add");
          // Clean up sessionStorage after retrieving
          sessionStorage.removeItem("legal_expert_onboard_data");
          // Clean up URL parameter
          window.history.replaceState({}, "", "/experts");
        } catch (error) {
          console.error("Failed to parse legal expert onboard data:", error);
        }
      }
    }
  }, []);

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearchTerm(searchTerm), 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Fetch data when debounced search term or status filter changes
  useEffect(() => {
    fetchLawyers(1);
  }, [debouncedSearchTerm, statusFilter]);

  const fetchLawyers = async (page: number = 1) => {
    setIsLoading(true);
    try {
      const limit = 12;
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(debouncedSearchTerm && { search_term: debouncedSearchTerm }),
        // Lawyer grid: filter by lawyer status only (Active/Deactive), not user status
        ...(statusFilter && { lawyer_status: statusFilter }),
      });

      const response = (await api.get(
        `/v1/lawyer?${params}`
      )) as LawyerSearchApiResponse;

      if (response.success && response.data) {
        const lawyers = response.data.items || [];

        // Fetch law firm names for lawyers that don't have them
        const lawyersWithFirmNames = await Promise.all(
          lawyers.map(async (lawyer) => {
            if (
              lawyer.lawfirm_id &&
              (!lawyer.lawfirms || !lawyer.lawfirms.name)
            ) {
              try {
                const firmResponse = (await api.get(
                  `/v1/law-firm/${lawyer.lawfirm_id}`
                )) as any;
                if (firmResponse?.success && firmResponse.data) {
                  return {
                    ...lawyer,
                    lawfirms: {
                      id: lawyer.lawfirm_id,
                      name: firmResponse.data.name || "N/A",
                      logos: firmResponse.data.logos || null,
                    },
                  };
                }
              } catch (error) {
                console.warn(
                  `Failed to fetch law firm for lawyer ${lawyer.id}:`,
                  error
                );
              }
            }
            return lawyer;
          })
        );

        setLawyers(lawyersWithFirmNames);
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
        setLawyers([]);
        setPagination({
          currentPage: 1,
          totalPages: 1,
          totalCount: 0,
          recordsPerPage: 12,
        });
      }
    } catch (error) {
    } finally {
      setIsLoading(false);
    }
  };

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

  // If not signed in (Guest), render DataNotFound inside Layout like lawfirms page
  if (currentRole.toLowerCase() === "guest" || !currentRole) {
    return (
      <Layout
        headerTitle="Experts Management"
        headerSubtitle="Manage and oversee experts profiles and information"
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

  // If not a navigator, block direct access and redirect (do not render content)
  if (
    currentRole &&
    currentRole !== "Guest" &&
    currentRole.toLowerCase() !== "navigator"
  ) {
    return null;
  }

  const handleAddClick = () => {
    setCurrentView("add");
    setSelectedLawyer(null);
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

  const handleEditClick = async (lawyer: Lawyer) => {
    try {
      setIsLoading(true);
      let lawyerData = lawyer;

      // Fetch law firm name if not present
      if (lawyer.lawfirm_id && (!lawyer.lawfirms || !lawyer.lawfirms.name)) {
        try {
          const firmResponse = (await api.get(
            `/v1/law-firm/${lawyer.lawfirm_id}`
          )) as any;
          if (firmResponse?.success && firmResponse.data) {
            lawyerData = {
              ...lawyer,
              lawfirms: {
                id: lawyer.lawfirm_id,
                name: firmResponse.data.name || "N/A",
                logos: firmResponse.data.logos || null,
              },
            };
          }
        } catch (error) {
          console.warn(
            `Failed to fetch law firm for lawyer ${lawyer.id}:`,
            error
          );
        }
      }

      setSelectedLawyer(lawyerData);
      setCurrentView("edit");
    } catch (error) {
      console.warn(`Failed to prepare lawyer for editing:`, error);
      setSelectedLawyer(lawyer);
      setCurrentView("edit");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewClick = async (lawyer: Lawyer) => {
    try {
      setIsLoading(true);
      const response = (await api.get(`/v1/lawyer/${lawyer.id}`)) as any;
      if (response?.success && response.data) {
        let lawyerData = response.data;

        // Fetch law firm name if not present
        if (
          lawyerData.lawfirm_id &&
          (!lawyerData.lawfirms || !lawyerData.lawfirms.name)
        ) {
          try {
            const firmResponse = (await api.get(
              `/v1/law-firm/${lawyerData.lawfirm_id}`
            )) as any;
            if (firmResponse?.success && firmResponse.data) {
              lawyerData = {
                ...lawyerData,
                lawfirms: {
                  id: lawyerData.lawfirm_id,
                  name: firmResponse.data.name || "N/A",
                  logos: firmResponse.data.logos || null,
                },
              };
            }
          } catch (error) {
            console.warn(
              `Failed to fetch law firm for expert ${lawyer.id}:`,
              error
            );
          }
        }

        setSelectedLawyer(lawyerData);
        setCurrentView("view");
      } else {
        toastManager.addToast(
          createErrorToast("Error", "Failed to load expert details", 2000)
        );
      }
    } catch (error: any) {
      toastManager.addToast(
        createErrorToast(
          "Error",
          error?.message || "Failed to load expert details",
          2000
        )
      );
      setSelectedLawyer(lawyer);
      setCurrentView("view");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToList = () => {
    setCurrentView("list");
    setSelectedLawyer(null);
    setPreFillData(null); // Clear pre-fill data when going back
  };

  const handleSubmitLawyer = async (
    formData: LawyerFormData,
    lawyerId?: string
  ): Promise<boolean> => {
    try {
      if (lawyerId) {
        const response = (await api.put(`/v1/lawyer`, {
          ...formData,
          id: lawyerId,
        })) as any;
        if (Array.isArray(response?.message) && response.message.length > 0) {
          await showToastsWithDelay(response.message, !!response.success);
        }
        await fetchLawyers(pagination.currentPage);
        handleBackToList();
        return !!response.success;
      } else {
        const response = (await api.post("/v1/lawyer", formData)) as any;
        if (Array.isArray(response?.message) && response.message.length > 0) {
          await showToastsWithDelay(response.message, !!response.success);
        }
        if (response?.success) {
          await fetchLawyers(pagination.currentPage);
          return true;
        } else {
          return false;
        }
      }
    } catch (error: any) {
      if (!ERROR_TO_EXCLUDE.includes(error?.status || error?.response?.status)) {
        await showToastsWithDelay(
          [{ message: error?.message || "Failed to save lawyer", success: false }],
          false
        );
      }
      return false;
    }
  };

  const getFullName = (lawyer: Lawyer) =>
    `${lawyer.first_name || ""} ${lawyer.last_name || ""}`.trim() || "—";

  const getLocation = (lawyer: Lawyer) =>
    [lawyer.city, lawyer.county].filter(Boolean).join(", ") || "—";

  return (
    <Layout
      headerTitle="Experts Management"
      headerSubtitle="Manage and oversee experts profiles and information"
      showBackButton={currentView === "add" || currentView === "edit" || currentView === "view"}
      backButtonLabel="Back to Experts"
      onBackClick={handleBackToList}
    >
      <div className="bg-novaInactive h-full flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

            {currentView === "add" && (
              <AddLawyerForm
                mode="add"
                onCancel={handleBackToList}
                onSubmit={handleSubmitLawyer}
                preFillData={preFillData || undefined}
              />
            )}

            {currentView === "edit" && selectedLawyer && (
              <AddLawyerForm
                mode="edit"
                lawyerData={selectedLawyer}
                onCancel={handleBackToList}
                onSubmit={handleSubmitLawyer}
              />
            )}

            {currentView === "view" && (
              <ViewLawyerDetails
                lawyerData={selectedLawyer}
                onClose={handleBackToList}
                onEdit={() => selectedLawyer && handleEditClick(selectedLawyer)}
                isLoading={isLoading}
              />
            )}

            {currentView === "list" && (
              <>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 flex-1">
                    <div className="bg-white rounded-md border border-novaActive p-3">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="w-6 h-6 bg-white rounded-md flex items-center justify-center border border-novaActive">
                            <i className="fas fa-user-tie text-novaDarkOrange text-xs"></i>
                          </div>
                        </div>
                        <div className="ml-3">
                          <p className="text-xs font-medium text-novaNeutral-500">
                            Total Experts
                          </p>
                          <p className="text-lg font-semibold text-novaNeutral-900">
                            {pagination.totalCount}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <FormButton
                    variant="gradient"
                    size="sm"
                    onClick={handleAddClick}
                    className="bg-novaPrimary-500 hover:bg-novaPrimary-600 text-white px-4 py-2 text-sm transition-colors whitespace-nowrap"
                  >
                    <i className="fas fa-plus mr-1.5"></i>
                    Add Expert
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
                          className="w-full pl-8 pr-8 py-2 text-sm border border-novaNeutral-300 rounded-md focus:ring-0 focus:ring-novaPrimary-500 focus:border-novaPrimary-500"
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
                        { value: "Deactive", label: "Inactive" },
                      ]}
                      placeholder="All Status"
                      triggerClassName="min-w-[140px] rounded-md"
                    />
                  </div>
                </div>

                {/* Lawyers Table */}
                <div className="bg-white rounded-md shadow-sm border border-novaActive overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-novaActive">
                      <thead className="bg-novaActive">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                            Name
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                            Location
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                            Law Firm/Chambers
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                            Gender
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                            Hourly Rate
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider">
                            Status
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
                              colSpan={7}
                              className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                            >
                              <div className="flex justify-center items-center">
                                <i className="fas fa-spinner fa-spin mr-2"></i>
                                Loading experts...
                              </div>
                            </td>
                          </tr>
                        ) : lawyers.length === 0 ? (
                          <tr>
                            <td
                              colSpan={7}
                              className="px-3 py-4 text-center text-sm text-novaNeutral-500"
                            >
                              No experts found.
                            </td>
                          </tr>
                        ) : (
                          lawyers.map((lawyer) => (
                            <tr
                              key={lawyer.id}
                              onClick={() => handleViewClick(lawyer)}
                              className="hover:bg-novaInactive cursor-pointer transition-colors"
                            >
                              <td className="px-3 py-2 whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  <div className="h-6 w-6 rounded-full bg-white flex items-center justify-center border border-novaDarkOrange">
                                    {lawyer.photo_urls ? (
                                      <img
                                        src={lawyer.photo_urls.thumbnail}
                                        alt={getFullName(lawyer)}
                                        className="h-6 w-6 rounded-full border border-novaDarkOrange object-cover"
                                        onError={(e) => {
                                          (
                                            e.currentTarget as HTMLImageElement
                                          ).style.display = "none";
                                        }}
                                      />
                                    ) : (
                                      <i className="fas fa-user-tie text-novaDarkOrange text-xs"></i>
                                    )}
                                  </div>
                                  <span
                                    className="text-[13px] font-medium text-novaNeutral-900 truncate max-w-[200px]"
                                    title={getFullName(lawyer)}
                                  >
                                    {/* Truncate name if too long and show "…" */}
                                    {getFullName(lawyer)}
                                  </span>
                                </div>
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500 truncate max-w-[200px]"
                                title={getLocation(lawyer)}
                              >
                                {getLocation(lawyer)}
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                {lawyer.lawfirms?.name || "—"}
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                {lawyer.gender || "—"}
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-[12px] text-novaNeutral-500">
                                {lawyer.hourly_rate &&
                                typeof lawyer.hourly_rate === "number"
                                  ? `£${lawyer.hourly_rate.toFixed(0)}`
                                  : "—"}
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-left">
                                <span
                                  className={`inline-flex px-2 py-0.5 text-[11px] font-medium rounded-full ${
                                    lawyer.status?.toLowerCase() === "active"
                                      ? "bg-novaSuccess-100 text-novaSuccess-800"
                                      : "bg-novaWarning-100 text-novaWarning-600"
                                  }`}
                                >
                                  {lawyer.status === "Active" ? "Active" : "Inactive"}
                                </span>
                              </td>
                              <td className="px-4 py-1 whitespace-nowrap text-right text-[12px] font-medium">
                                <div className="flex items-center justify-end gap-2">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleViewClick(lawyer);
                                    }}
                                    className="p-1.5 text-novaGray-500 hover:text-novaNeutral-900 hover:bg-novaNeutral-100 rounded transition-colors"
                                    title="View Details"
                                  >
                                    <i className="fa-solid fa-eye text-sm"></i>
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleEditClick(lawyer);
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
                            fetchLawyers(newPage),
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

export default LawyersPage;
