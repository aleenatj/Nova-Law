import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  createSuccessToast,
  createErrorToast,
  toastManager,
} from "@/utils/toasts";
import LawyerDetailsCard from "./LawyerDetailsCard";
import { api } from "@/lib/api";
import {
  LawyerDetailsDisplayCardType,
  LawyerSearchApiResponseItem,
  LawyerSearchApiResponse,
  ReviewProfilesModalProps,
} from "@/lib/types";
import GlobalModalWrapper from "../modal/GlobalModalWrapper";
import { FormButton } from "@/utils/formComponents";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";

interface MessageItem {
  success: boolean;
  message: string;
}

interface ApiResponse {
  success: boolean;
  message?: MessageItem[];
  data?: any[];
}

const ReviewProfilesModal: React.FC<ReviewProfilesModalProps> = ({
  isOpen,
  onClose,
  onConfirmSuccess,
  lawyers = [],
  caseId,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedMatterType, setSelectedMatterType] = useState<string>("");
  const [selectedRelationshipType, setSelectedRelationshipType] = useState<string>("");
  const [selectedLawyers, setSelectedLawyers] = useState<
    LawyerDetailsDisplayCardType[]
  >([]);
  const [searchResults, setSearchResults] = useState<
    LawyerDetailsDisplayCardType[]
  >([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  
  // Filter options
  const MATTER_TYPE_OPTIONS = [
    { value: "FINANCIAL_CLAIMS", label: "Financial Claims" },
    { value: "CHILDREN", label: "Children" },
  ];
  const RELATIONSHIP_TYPE_OPTIONS = [
    { value: "MARRIED_CIVIL_PARTNERS", label: "Married and Civil Partners" },
    { value: "COHABITEES", label: "Cohabitees" },
    { value: "PARENTAL_RELATIONSHIPS", label: "Parental relationships" },
  ];

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [loadMoreLoading, setLoadMoreLoading] = useState(false);
  const [loadPreviousLoading, setLoadPreviousLoading] = useState(false);
  const [originalSelectedLawyers, setOriginalSelectedLawyers] = useState<
    LawyerDetailsDisplayCardType[]
  >([]);
  
  // Use ref to track selectedLawyers without causing re-renders
  const selectedLawyersRef = useRef<LawyerDetailsDisplayCardType[]>([]);
  // Track if initial load has been done
  const initialLoadDoneRef = useRef<boolean>(false);
  
  // Keep ref in sync with state
  useEffect(() => {
    selectedLawyersRef.current = selectedLawyers;
  }, [selectedLawyers]);

  // Convert lawyer data to LawyerDetailsDisplayCardType
  const convertLawyerToDisplayType = (
    lawyer: any
  ): LawyerDetailsDisplayCardType => {
    // Check if it's already in LawyerDetailsDisplayCardType format (from matched lawyers API)
    if (lawyer.expert_types) {
      // Try different possible ID fields and create a fallback
      let lawyerId =
        lawyer.id || lawyer.lawyer_id || lawyer.user_id || lawyer.lawyerId;

      // If no ID found, create one based on name and email for consistency
      if (!lawyerId) {
        const namePart = (lawyer.first_name || "") + (lawyer.last_name || "");
        const emailPart = lawyer.email || "";
        lawyerId = `${namePart}_${emailPart}_${Date.now()}`.replace(
          /[^a-zA-Z0-9_]/g,
          ""
        );
      }

      return {
        id: lawyerId,
        lawyer_id: lawyerId,
        user_id: lawyerId,
        first_name: lawyer.first_name || "",
        last_name: lawyer.last_name || "",
        email: lawyer.email || "",
        phone_number: lawyer.phone_number || lawyer.phone || "",
        phone: lawyer.phone || lawyer.phone_number || "",
        gender: lawyer.gender || null,
        gender_other: lawyer.gender_other || null,
        address_line_1: lawyer.address_line_1 || null,
        address_line_2: lawyer.address_line_2 || null,
        city: lawyer.city || null,
        county: lawyer.county || null,
        country: lawyer.country || null,
        postal_code: lawyer.postal_code || null,
        reg_no: lawyer.reg_no || null,
        regulator: lawyer.regulator || null,
        sra_number: lawyer.sra_number || null,
        bar_number: lawyer.bar_number || null,
        admitted_date_solicitor: lawyer.admitted_date_solicitor || null,
        called_date_barrister: lawyer.called_date_barrister || null,
        admitted_date_cliex: lawyer.admitted_date_cliex || null,
        joined_at: lawyer.joined_at || null,
        left_at: lawyer.left_at || null,
        about: lawyer.about || null,
        photo_url: lawyer.photo_url || null,
        photo_urls: lawyer.photo_urls || null,
        linkedin_url: lawyer.linkedin_url || null,
        lawyer_status: lawyer.lawyer_status || lawyer.status,
        status: lawyer.status || lawyer.lawyer_status,
        experience:lawyer.experience || null,
        hourly_rate: lawyer.hourly_rate || null,
        charge_first_consultation: lawyer.charge_first_consultation || null,
        expert_types_all: lawyer.expert_types_all || [],
        accredited_specialisms: lawyer.accredited_specialisms || [],
        conflict_level_disinclination:
          lawyer.conflict_level_disinclination || null,
        expert_types: lawyer.expert_types || [],
        relationship_types: lawyer.relationship_types || [],
        matter_types: lawyer.matter_types || [],
        pi_insurance: lawyer.pi_insurance || null,
        testimonial: lawyer.testimonial || null,
        accreditations: lawyer.accreditations || [],
        expertises_all: lawyer.expertises_all || [],
        lawfirms: lawyer.lawfirms || null,
        created_at: lawyer.created_at || new Date().toISOString(),
        updated_at: lawyer.updated_at || null,
        is_sent: lawyer.is_sent ?? false,
      };
    } else {
      // Handle LawyerProfileDisplayType format (from search API)
      let lawyerId =
        lawyer.id || lawyer.lawyer_id || lawyer.user_id || lawyer.lawyerId;

      // If no ID found, create one based on name and email for consistency
      if (!lawyerId) {
        const namePart = (lawyer.first_name || "") + (lawyer.last_name || "");
        const emailPart = lawyer.email || "";
        lawyerId = `${namePart}_${emailPart}_${Date.now()}`.replace(
          /[^a-zA-Z0-9_]/g,
          ""
        );
      }

      return {
        id: lawyerId,
        lawyer_id: lawyerId,
        user_id: lawyerId,
        first_name: lawyer.first_name || "",
        last_name: lawyer.last_name || "",
        email: lawyer.email || "",
        phone_number: lawyer.phone || "",
        phone: lawyer.phone || "",
        gender: lawyer.gender || null,
        gender_other: null,
        address_line_1: null,
        address_line_2: null,
        city: lawyer.location ? lawyer.location.split(",")[0]?.trim() : null,
        county: lawyer.location ? lawyer.location.split(",")[1]?.trim() : null,
        country: null,
        postal_code: null,
        reg_no: null,
        regulator: null,
        sra_number: null,
        bar_number: null,
        admitted_date_solicitor: null,
        called_date_barrister: null,
        admitted_date_cliex: null,
        joined_at: null,
        left_at: null,
        about: lawyer.about || null,
        photo_url: lawyer.image,
        linkedin_url: null,
        lawyer_status: lawyer.status,
        status: lawyer.status,
        experience:lawyer.experience || null,
        hourly_rate: lawyer.rate,
        charge_first_consultation: null,
        expert_types_all: lawyer.expert_types_all || [],
        accredited_specialisms: lawyer.accredited_specialisms || [],
        conflict_level_disinclination: null,
        expert_types: lawyer.expert_types || [],
        relationship_types: [],
        matter_types: [],
        pi_insurance: null,
        testimonial: null,
        lawfirms: null,
        created_at: lawyer.created_at || new Date().toISOString(),
        updated_at: lawyer.updated_at || null,
        is_sent: lawyer.is_sent ?? false,
      };
    }
  };

  // Initialize selected lawyers when modal opens with new data
  useEffect(() => {
    if (isOpen && lawyers.length > 0) {
      const convertedLawyers = lawyers.map(convertLawyerToDisplayType);

      setSelectedLawyers(convertedLawyers);
      setOriginalSelectedLawyers(convertedLawyers);
    }
  }, [isOpen, lawyers]);

  // Clear search and reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSearchTerm("");
      setSelectedMatterType("");
      setSelectedRelationshipType("");
      setSearchResults([]);
      setSearchLoading(false);
      // Reset pagination state
      setCurrentPage(1);
      setTotalCount(0);
      setLoadMoreLoading(false);
      setLoadPreviousLoading(false);
      // Reset selected lawyers to original state
      setSelectedLawyers([]);
      setOriginalSelectedLawyers([]);
      // Reset initial load flag
      initialLoadDoneRef.current = false;
    }
  }, [isOpen]);

  // Convert API search response to display type
  const mapApiToDisplay = (
    lawyer: LawyerSearchApiResponseItem
  ): LawyerDetailsDisplayCardType => {
    // Use the same conversion logic for consistency
    return convertLawyerToDisplayType(lawyer);
  };

  const RECORDS_PER_PAGE = 4;

  // Helper function to fetch lawyers with pagination
  const fetchLawyers = async (
    query: string,
    page: number,
    append: boolean = false,
    matterType: string = "",
    relationshipType: string = ""
  ) => {
    try {
      // Build query parameters
      const params = new URLSearchParams({
        page: page.toString(),
        limit: RECORDS_PER_PAGE.toString(),
        status: "Active",
      });
      
      if (query.trim().length >= 3) {
        params.append("search_term", query);
      }
      
      // Add matter type filter
      if (matterType) {
        params.append("matter_type", matterType);
      }
      
      // Add relationship type filter
      if (relationshipType) {
        params.append("relationship_type", relationshipType);
      }
      
      const response: LawyerSearchApiResponse = await api.get(
        `/v1/lawyer?${params.toString()}`
      );

      // Handle the structured API response
      if (response?.success && response?.data?.items) {
        const lawyersData: LawyerSearchApiResponseItem[] = response.data.items;

        // Update pagination metadata
        if (response.data.total_count !== undefined) {
          setTotalCount(response.data.total_count);
        }

        // Check if API indicates 0 records found
        if (lawyersData.length === 0) {
          if (!append) {
            setSearchResults([]);
          }
          return [];
        }

        // Map API response to display type
        return lawyersData.map(mapApiToDisplay);
      } else {
        // Fallback for unexpected response structure
        console.warn("Unexpected API response structure:", response);
        return [];
      }
    } catch (err) {
      console.error("Error searching lawyers:", err);
      return [];
    }
  };

  const searchLawyers = useCallback(
    async (query: string, matterType: string = "", relationshipType: string = "") => {
      // Only require search term if it's less than 3 characters and no filters
      // Allow fetching without search term or filters to show all lawyers by default
      if (query.trim().length > 0 && query.trim().length < 3 && !matterType && !relationshipType) {
        setSearchResults([]);
        setCurrentPage(1);
        setTotalCount(0);
        return;
      }

      setSearchLoading(true);
      setCurrentPage(1); // Reset to first page for new search

      const results = await fetchLawyers(query, 1, false, matterType, relationshipType);

      // Selected lawyers will be shown as disabled with "Added" button
      setSearchResults(results);
      setSearchLoading(false);
    },
    [RECORDS_PER_PAGE]
  );

  const loadMoreLawyers = async () => {
    // Allow loading more even without search term or filters (for default view)

    setLoadMoreLoading(true);
    const nextPage = currentPage + 1;
    const results = await fetchLawyers(searchTerm, nextPage, false, selectedMatterType, selectedRelationshipType);

    if (results.length > 0) {
      // Show all results including selected ones
      // Selected lawyers will be shown as disabled with "Added" button
      setSearchResults(results);
      setCurrentPage(nextPage);
    }

    setLoadMoreLoading(false);
  };

  const loadPreviousLawyers = async () => {
    // Allow loading previous even without search term or filters (for default view)

    setLoadPreviousLoading(true);
    let prevPage = currentPage - 1;
    
    // Keep trying previous pages until we find one with data
    while (prevPage >= 1) {
      const results = await fetchLawyers(searchTerm, prevPage, false, selectedMatterType, selectedRelationshipType);

      if (results.length > 0) {
        // Show all results including selected ones
        // Selected lawyers will be shown as disabled with "Added" button
        setSearchResults(results);
        setCurrentPage(prevPage);
        break;
      }
      
      // If this page has no results, try the page before it
      prevPage--;
    }
    
    // If we couldn't find any previous page with data, stay on current page
    // (searchResults and currentPage remain unchanged)

    setLoadPreviousLoading(false);
  };

  // Load lawyers by default when modal opens and on search/filter changes
  useEffect(() => {
    if (!isOpen) return;

    const isInitialLoad = !initialLoadDoneRef.current && searchTerm === "" && selectedMatterType === "" && selectedRelationshipType === "";
    const shouldSkip = searchTerm.trim().length > 0 && searchTerm.trim().length < 3 && !selectedMatterType && !selectedRelationshipType;

    const id = setTimeout(() => {
      // Allow loading without search term or filters (for default view)
      // Only prevent if search term is 1-2 characters without filters
      if (shouldSkip) {
        return;
      }
      searchLawyers(searchTerm, selectedMatterType, selectedRelationshipType);
      if (isInitialLoad) {
        initialLoadDoneRef.current = true;
      }
    }, isInitialLoad ? 0 : 500); // Immediate load on first open, debounce subsequent changes
    
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, searchTerm, selectedMatterType, selectedRelationshipType]); // Trigger on modal open or search/filter changes

  const handleRemoveLawyer = (lawyer: LawyerDetailsDisplayCardType) => {
    // Safety check - if no ID, don't proceed
    if (!lawyer.id) {
      console.error("Cannot remove lawyer: No ID found", lawyer);
      return;
    }

    // Remove from selected lawyers
    setSelectedLawyers((prev) => {
      const filtered = prev.filter((l) => l.id !== lawyer.id);
      return filtered;
    });

    // Lawyer will remain in search results and become enabled again
    // The display logic will automatically update the button state
  };

  const handleAddLawyer = async (lawyer: LawyerDetailsDisplayCardType) => {
    // Add to selected lawyers
    setSelectedLawyers((prev) => [...prev, lawyer]);

    // Keep lawyer in search results - it will be shown as disabled with "Added" button
    // The display logic will automatically update the button state
  };

  const handleConfirmLawyers = async () => {
    if (selectedLawyers.length === 0) return;

    setConfirmLoading(true);
    try {
      // Prepare the request body as per API documentation
      const requestBody = {
        case_id: caseId || "", // Use provided caseId or fallback
        lawyers: selectedLawyers.map((lawyer) => lawyer.id),
      };

      const response = (await api.post(
        "/v1/timeline/lawyer-match",
        requestBody
      )) as ApiResponse;

      // Helper to show toasts with delay
      const showToastsWithDelay = async (
        messages: MessageItem[],
        isSuccess: boolean
      ) => {
        const delay = 400; // ms
        for (let i = 0; i < messages.length; i++) {
          const messageItem = messages[i];
          await new Promise((resolve) =>
            setTimeout(resolve, i === 0 ? 0 : delay)
          );
          if (isSuccess) {
            if (messageItem.success) {
              const toast = createSuccessToast("Success", messageItem.message);
              toastManager.addToast(toast);
            }
          }
        }
      };

      if (response.success) {
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Success",
            response.message || "Confirmed Experts"
          );
          toastManager.addToast(toast);
        }
        // Notify parent so it can refetch case details
        onConfirmSuccess?.();
        // Close modal on success
        setConfirmLoading(false);
        onClose();
      } else {
        // Handle error case
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        }
        setConfirmLoading(false);
      }
    } catch (error: any) {
      let errorMessage = "Failed to confirm lawyers. Please try again.";

      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // const toast = createErrorToast("Error", errorMessage);
      // toastManager.addToast(toast);
      setConfirmLoading(false);
    }
  };

  return (
    <GlobalModalWrapper isOpen={isOpen} onClose={onClose}>
      <div className="fixed left-1/2 top-1/2 z-50 flex flex-col p-2 translate-x-[-50%] translate-y-[-50%] shadow-lg bg-white duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] rounded-lg sm:rounded-lg w-[calc(100vw-2rem)] sm:max-w-4xl max-h-[90vh] sm:max-h-[80vh]">
        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {/* Header */}
        <div className="flex flex-row items-start justify-between text-center sm:text-left w-full">
          <div className="flex flex-col space-y-1.5 flex-1 min-w-0">
            <h2 className="text-lg font-semibold leading-none tracking-6">
              Review Expert Profiles
            </h2>
            <p className="hidden sm:block text-sm text-novaNeutral-500">
              Review the AI-matched experts and add/remove them from the
              notification list. You can also search for additional experts to
              add to the list.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-novaNeutral-500 hover:text-novaNeutral-600 ml-4"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Selected Lawyers */}
        <div>
          <div className="flex items-center my-3">
            <h3 className="text-md font-medium text-gray-900">
              Selected Experts ({selectedLawyers.length})
            </h3>
            <span className="text-sm text-novaSuccess-600 ml-2">
              ✓ Confirmed
            </span>
          </div>
          <div className="space-y-3">
            {selectedLawyers.map((lawyer, index) => (
              <LawyerDetailsCard
                key={lawyer.id}
                lawyer={lawyer}
                variant="selected"
                buttonConfig={{
                  text: lawyer.is_sent ? "Case Notified" : "Remove",
                  type: "Remove",
                  onClick: () => handleRemoveLawyer(lawyer),
                  icon: lawyer.is_sent ? "" : "×",
                  disabled: lawyer.is_sent,
                }}
              />
            ))}
          </div>

          {/* Add More Lawyers */}
          <div className="py-2">
            <h3 className="text-lg font-medium text-novaNeutral-900 my-3">
              Add More Experts
            </h3>
            <div className="relative">
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 pr-10 border border-novaNeutral-300 rounded-lg text-sm focus:outline-none focus:border-novaPrimary-400 focus:ring-0 focus:ring-novaPrimary-100"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-novaNeutral-500 hover:text-novaNeutral-700 p-1"
                  title="Clear search"
                  type="button"
                >
                  <i className="fas fa-times"></i>
                </button>
              )}
            </div>
            
            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              {/* Matter Type Filter */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-sm font-medium text-novaNeutral-700">
                    Matter Type
                  </label>
                  {selectedMatterType && (
                    <button
                      onClick={() => setSelectedMatterType("")}
                      className="text-novaNeutral-500 hover:text-novaNeutral-700 text-xs font-medium flex items-center gap-1"
                      title="Clear filter"
                    >
                      <i className="fas fa-times"></i>
                      Clear
                    </button>
                  )}
                </div>
                <CustomSelect
                  value={selectedMatterType}
                  onChange={setSelectedMatterType}
                  options={MATTER_TYPE_OPTIONS}
                  placeholder="Select matter type..."
                  triggerClassName="rounded-lg h-10 mb-2"
                />
              </div>
              
              {/* Relationship Type Filter */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-sm font-medium text-novaNeutral-700">
                    Relationship Type
                  </label>
                  {selectedRelationshipType && (
                    <button
                      onClick={() => setSelectedRelationshipType("")}
                      className="text-novaNeutral-500 hover:text-novaNeutral-700 text-xs font-medium flex items-center gap-1"
                      title="Clear filter"
                    >
                      <i className="fas fa-times"></i>
                      Clear
                    </button>
                  )}
                </div>
                <CustomSelect
                  value={selectedRelationshipType}
                  onChange={setSelectedRelationshipType}
                  options={RELATIONSHIP_TYPE_OPTIONS}
                  placeholder="Select relationship type..."
                  triggerClassName="rounded-lg h-10 mb-2"
                />
              </div>
            </div>

            {/* Scrollable Search Results Area */}
            <div className="space-y-4 max-h-100 overflow-y-auto mt-4 pb-4 pt-6 border-t border-novaGray-100">
              {searchLoading && (
                <div className="text-center py-8 text-novaNeutral-500">
                  Loading...
                </div>
              )}
              {!searchLoading &&
                (searchTerm.length >= 3 || selectedMatterType || selectedRelationshipType || searchResults.length > 0) &&
                searchResults.length === 0 && (
                  <div className="text-center py-8 text-novaNeutral-500">
                    <div className="text-sm font-medium">0 records found</div>
                    <div className="text-xs text-novaNeutral-400 mt-1">
                      {searchTerm.length >= 3
                        ? `No experts found matching "${searchTerm}"`
                        : "No experts found with the selected filters"}
                    </div>
                  </div>
                )}
              {!searchLoading &&
                searchTerm.length > 0 &&
                searchTerm.length < 3 &&
                !selectedMatterType &&
                !selectedRelationshipType &&
                searchResults.length === 0 && (
                  <div className="text-center py-8 text-novaNeutral-500">
                    Please enter at least 3 characters to search, or select filters
                  </div>
                )}
              {!searchLoading &&
                searchResults.map((lawyer) => {
                  const isSelected = selectedLawyers.some((selected) => selected.id === lawyer.id);
                  return (
                    <LawyerDetailsCard
                      key={lawyer.id}
                      lawyer={lawyer}
                      variant="search"
                      buttonConfig={{
                        text: isSelected ? "Added" : "Add",
                        type: "Add",
                        onClick: () => handleAddLawyer(lawyer),
                        icon: isSelected ? "" : "+",
                        disabled: isSelected,
                      }}
                    />
                  );
                })}
            </div>

            {/* Pagination Controls - At the bottom */}
            {!searchLoading && searchResults.length > 0 && (
              <div className="flex items-center justify-between">
                {/* Pagination Info */}
                <div className="text-xs text-novaNeutral-500">
                  Page {currentPage} of{" "}
                  {Math.ceil(totalCount / RECORDS_PER_PAGE)} pages
                </div>

                {/* Navigation Buttons */}
                <div className="flex gap-2">
                  {/* Previous Button */}
                  <button
                    onClick={loadPreviousLawyers}
                    disabled={currentPage <= 1 || loadPreviousLoading}
                    className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium border border-novaGray-200 bg-white hover:bg-novaGray-50 h-8 px-3 py-1 disabled:opacity-50 disabled:cursor-not-allowed text-novaGray-700"
                    title="Previous Page"
                  >
                    {loadPreviousLoading ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <i className="fas fa-chevron-left"></i>
                    )}
                  </button>

                  {/* Next Button */}
                  <button
                    onClick={loadMoreLawyers}
                    disabled={
                      currentPage >= Math.ceil(totalCount / RECORDS_PER_PAGE) ||
                      loadMoreLoading
                    }
                    className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium border border-novaGray-200 bg-white hover:bg-novaGray-50 h-8 px-3 py-1 disabled:opacity-50 disabled:cursor-not-allowed text-novaGray-700"
                    title="Next Page"
                  >
                    {loadMoreLoading ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <i className="fas fa-chevron-right"></i>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
        </div>

        {/* Footer - Sticky at bottom with top border */}
        <div className="sticky bg-white border-t border-novaGray-100 p-4 sm:p-6 pt-4 mt-auto rounded-b-lg">
          <div className="flex flex-col sm:flex-row sm:justify-end sm:items-center gap-3">
            {/* Mobile: Text above buttons, Desktop: Text on left close to buttons */}
            <div className="text-sm text-novaNeutral-600 order-1 sm:order-1 text-right sm:text-left w-full sm:w-auto">
              <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-0">
                {selectedLawyers.length > 0 && (
                  <span className="text-novaSuccess-600 sm:ml-2">
                    ✓ Ready to confirm
                  </span>
                )}
              </div>
            </div>

            {/* Mobile: Buttons below text, Desktop: Buttons on right */}
            <div className="flex gap-2 justify-end order-2 sm:order-2 w-full sm:w-auto">
              <FormButton
                variant="outline"
                className="border border-novaGray-200 bg-background hover:bg-accent h-10 px-4 py-2 text-sm"
                onClick={onClose}
                disabled={confirmLoading}
              >
                Cancel
              </FormButton>
              <FormButton
                className="h-10 px-4 py-2 text-sm bg-novaBlue-500 hover:bg-novaBlue-600 text-white disabled:bg-novaGray-400 disabled:cursor-not-allowed"
                onClick={handleConfirmLawyers}
                disabled={selectedLawyers.length === 0 || confirmLoading}
              >
                {confirmLoading ? "Confirming..." : "Confirm"}
              </FormButton>
            </div>
          </div>
        </div>
      </div>
    </GlobalModalWrapper>
  );
};

export default ReviewProfilesModal;
