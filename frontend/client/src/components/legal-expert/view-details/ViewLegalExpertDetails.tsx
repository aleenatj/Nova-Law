import React, { useState, useEffect } from "react";
import { LegalExpert, LegalExpertStatus, ValuesWithOther } from "@/lib/types";
import { formatTimestamp, FormButton } from "@/utils";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { api } from "@/lib/api";
import { toastManager, createSuccessToast, createErrorToast } from "@/utils/toasts";
import { useLocation } from "wouter";
import { lawyerSignupConfig } from "@/config/lawyer-signup-config";
import { toTitleCase } from "@/lib/utils";

// Helper function to get field by ID from config
const getFieldById = (fieldId: number): any | null => {
  for (const section of lawyerSignupConfig.sections) {
    for (const field of section.fields) {
      if ((field as any).id === fieldId) {
        return field;
      }
    }
  }
  return null;
};

// Helper function to normalize options format
const normalizeOptions = (options: any[]): Array<{ value: string; label: string }> => {
  if (!options || !Array.isArray(options)) return [];
  
  const normalized: Array<{ value: string; label: string }> = [];
  
  options.forEach((option) => {
    // Handle string format (backward compatibility)
    if (typeof option === "string") {
      normalized.push({ value: option, label: option });
    }
    // Handle object with value and label
    else if (option && typeof option === "object" && option.value && option.label) {
      normalized.push({ value: option.value, label: option.label });
    }
    // Handle nested object structure
    else if (option && typeof option === "object" && !option.value) {
      Object.keys(option).forEach((key) => {
        const nestedOption = option[key];
        if (nestedOption && nestedOption.value && nestedOption.label) {
          normalized.push({ value: nestedOption.value, label: nestedOption.label });
        }
      });
    }
  });
  
  return normalized;
};

// Get options from config for all fields
const professionalStatusField = getFieldById(23);
const regulatorField = getFieldById(40);
const accreditedSpecialistField = getFieldById(19);
const ncdrMagicField = getFieldById(18);
const marriedCouplesField = getFieldById(9);
const cohabiteesField = getFieldById(29);
const clientTypesField = getFieldById(27);

const PROFESSIONAL_STATUS_OPTIONS = normalizeOptions(professionalStatusField?.options || []);
const REGULATOR_OPTIONS = normalizeOptions(regulatorField?.options || []);
const ACCREDITED_SPECIALIST_OPTIONS = normalizeOptions(accreditedSpecialistField?.options || []);
const NCDR_MAGIC_OPTIONS = normalizeOptions(ncdrMagicField?.options || []);
const MARRIED_COUPLES_OPTIONS = normalizeOptions(marriedCouplesField?.options || []);
const COHABITEES_OPTIONS = normalizeOptions(cohabiteesField?.options || []);
const CLIENT_TYPES_OPTIONS = normalizeOptions(clientTypesField?.options || []);

// Matter Types mapping (from backend enum)
const MATTER_TYPES_MAP: Record<string, string> = {
  "FINANCIAL_CLAIMS": "Financial Claims",
  "CHILDREN": "Children",
};

// Helper function to map enum keys to display values
const getProfessionalStatusLabel = (key: string): string => {
  const option = PROFESSIONAL_STATUS_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

const getRegulatorLabel = (key: string): string => {
  const option = REGULATOR_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

const getAccreditedSpecialistLabel = (key: string): string => {
  const option = ACCREDITED_SPECIALIST_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

const getNcdrMagicLabel = (key: string): string => {
  const option = NCDR_MAGIC_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

const getMarriedCouplesExpertiseLabel = (key: string): string => {
  const option = MARRIED_COUPLES_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

const getCohabiteesExpertiseLabel = (key: string): string => {
  const option = COHABITEES_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

const getMatterTypeLabel = (key: string): string => {
  return MATTER_TYPES_MAP[key] || key;
};

const getClientTypeLabel = (key: string): string => {
  const option = CLIENT_TYPES_OPTIONS.find(
    (opt) => opt.value === key || opt.value.toUpperCase() === key.toUpperCase()
  );
  return option?.label || key;
};

interface ViewLegalExpertDetailsProps {
  expertData: LegalExpert | null;
  onClose: () => void;
  onEdit: () => void;
  onStatusUpdate?: (updatedExpert: LegalExpert) => void;
  isLoading?: boolean;
}

const STATUS_OPTIONS = [
  { value: "New", label: "New" },
  { value: "Review", label: "Review" },
  { value: "Onboarded", label: "Onboarded" },
  { value: "Rejected", label: "Rejected" },
];

const ViewLegalExpertDetails: React.FC<ViewLegalExpertDetailsProps> = ({
  expertData,
  onClose,
  onEdit,
  onStatusUpdate,
  isLoading = false,
}) => {
  const [, setLocation] = useLocation();
  const [selectedStatus, setSelectedStatus] = useState<LegalExpertStatus>("New");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  // Handle onboard click - navigate to lawyers page with pre-filled data
  const handleOnboardClick = () => {
    if (!expertData) return;

    // Map legal expert data to lawyer form data structure
    const lawyerPreFillData = {
      first_name: expertData.first_name || "",
      last_name: expertData.last_name || "",
      email: expertData.email || "",
      phone: expertData.phone || "",
      gender: expertData.gender || "",
      city: expertData.city || "",
      postal_code: expertData.post_code || "",
      photo_url: expertData.photo_url?.thumbnail || "",
      photo_preview_url: expertData.photo_url?.large || expertData.photo_url?.medium || expertData.photo_url?.thumbnail || "",
      about: expertData.ncdr_description || "",
      testimonial: expertData.compelling_quote || "",
      // Store as arrays for key-based mapping
      accredited_specialisations: expertData.accredited_specialist?.values || [],
      accredited_specialism_other: (() => {
        const val = expertData.accredited_specialism_other;
        if (val && Array.isArray(val) && val.length > 0) {
          return val.filter(Boolean);
        }
        return null;
      })(),
      dr_preferences: expertData.ncdr_magic?.values || [],
      // Store professional status info for expert_types mapping
      professional_status: expertData.professional_status,
      // Store regulator info - handle "OTHER" case properly
      // Legal expert form uses: "SRA", "BSB", "CILEX", "OTHER"
      regulator: (() => {
        const regulatorValue = expertData.regulator?.values?.[0];
        // If the value is "OTHER", return "OTHER"
        if (regulatorValue === "OTHER" || regulatorValue === "Other") {
          return "OTHER";
        }
        // If there's a value and it's not "OTHER", return it (SRA, BSB, CILEX)
        if (regulatorValue) {
          return regulatorValue;
        }
        // If no value but there's an "other" field, it means it's a custom regulator
        if (expertData.regulator?.other) {
          return "OTHER";
        }
        return "";
      })(),
      // Store regulator_other - only set if regulator is "OTHER"
      regulator_other: (() => {
        const regulatorValue = expertData.regulator?.values?.[0];
        // If the value is "OTHER" or "Other", use the other field
        if (regulatorValue === "OTHER" || regulatorValue === "Other") {
          return expertData.regulator?.other || null;
        }
        // If no value but there's an "other" field, use it (edge case)
        if (!regulatorValue && expertData.regulator?.other) {
          return expertData.regulator.other;
        }
        return null;
      })(),
      // Map relationship types from service_details.offers
      relationship_types: expertData.service_details?.offers || [],
      // Map expertises from service_details (cohabitees and married_civil_partners)
      // Handle both old format (arrays) and new format (objects with expertises and other)
      expertises: expertData.service_details ? {
        cohabitees: (() => {
          const coh = expertData.service_details?.cohabitees;
          if (!coh) return undefined;
          // If it's an object with expertises and other fields
          if (typeof coh === "object" && !Array.isArray(coh) && ("expertises" in coh || "other" in coh)) {
            return {
              expertises: (coh as any).expertises || [],
              other: (coh as any).other || [],
            };
          }
          // If it's an array (old format), treat as expertises only
          if (Array.isArray(coh)) {
            return {
              expertises: coh,
              other: [],
            };
          }
          return undefined;
        })(),
        married_civil_partners: (() => {
          const mcp = expertData.service_details?.married_civil_partners;
          if (!mcp) return undefined;
          // If it's an object with expertises and other fields
          if (typeof mcp === "object" && !Array.isArray(mcp) && ("expertises" in mcp || "other" in mcp)) {
            return {
              expertises: (mcp as any).expertises || [],
              other: (mcp as any).other || [],
            };
          }
          // If it's an array (old format), treat as expertises only
          if (Array.isArray(mcp)) {
            return {
              expertises: mcp,
              other: [],
            };
          }
          return undefined;
        })(),
      } : undefined,
      // Store matter types for pre-fill
      // Handle both formats: { values: [...] } or plain array
      matter_types: (() => {
        if (!expertData.matter_types) return [];
        // If it's an object with values property
        if (typeof expertData.matter_types === "object" && !Array.isArray(expertData.matter_types) && "values" in expertData.matter_types) {
          return (expertData.matter_types as any).values || [];
        }
        // If it's a plain array
        if (Array.isArray(expertData.matter_types)) {
          return expertData.matter_types;
        }
        return [];
      })(),
      // Store the legal expert ID for reference (both as legal_expert_id and reference_id)
      legal_expert_id: expertData.id,
      reference_id: expertData.id, // Reference ID from legal expert onboarding
    };

    // Store in sessionStorage for the lawyers page to retrieve
    sessionStorage.setItem("legal_expert_onboard_data", JSON.stringify(lawyerPreFillData));

    // Navigate to lawyers page with onboard flag
    setLocation("/experts?onboard_from_expert=true");
  };

  // Sync status with expertData
  useEffect(() => {
    if (expertData?.status) {
      setSelectedStatus(expertData.status);
    }
  }, [expertData?.status]);

  const InfoRow = ({
    label,
    value,
  }: {
    label: string;
    value?: string | number | null;
  }) => (
    <div className="flex flex-col space-y-1">
      <span className="text-xs font-medium text-novaNeutral-500">{label}</span>
      <span className="text-sm text-novaNeutral-900 break-words overflow-wrap-anywhere">{value || "—"}</span>
    </div>
  );

  // Helper to format ValuesWithOther type data
  // If "Other" is in values and there's an other text, show "Other - {value}"
  const formatValuesWithOther = (data: ValuesWithOther | null | undefined): string => {
    if (!data) return "—";
    const parts: string[] = [];
    if (data.values && data.values.length > 0) {
      data.values.forEach((val) => {
        if (val === "Other" && data.other) {
          parts.push(`Other - ${data.other}`);
        } else {
          parts.push(val);
        }
      });
    }
    return parts.length > 0 ? parts.join(", ") : "—";
  };

  // Helper to format service details (category -> options mapping)
  const formatServiceDetails = (data: any): React.ReactNode => {
    if (!data || (typeof data !== 'object')) {
      return <span className="text-sm text-novaNeutral-500">—</span>;
    }

    // Handle new format with offers, cohabitees, married_civil_partners
    if (data.offers !== undefined || data.cohabitees !== undefined || data.married_civil_partners !== undefined) {
      return (
        <div className="space-y-3">
          {/* Cohabitees */}
          {data.cohabitees && (
            <div>
              <span className="text-xs font-medium text-novaNeutral-600">Cohabitees:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {data.cohabitees.expertises && Array.isArray(data.cohabitees.expertises) && 
                  data.cohabitees.expertises.map((expertise: string, index: number) => (
                    <span
                      key={`cohab-expertise-${index}`}
                      className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                    >
                      {getCohabiteesExpertiseLabel(expertise)}
                    </span>
                  ))
                }
              </div>
              {/* Other values on new line with heading */}
              {data.cohabitees.other && Array.isArray(data.cohabitees.other) && data.cohabitees.other.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs font-medium text-novaNeutral-600">Other:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {data.cohabitees.other.map((other: string, index: number) => (
                      <span
                        key={`cohab-other-${index}`}
                        className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                      >
                        {other}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Married Civil Partners */}
          {data.married_civil_partners && (
            <div>
              <span className="text-xs font-medium text-novaNeutral-600">Married Couples and Civil Partners:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {data.married_civil_partners.expertises && Array.isArray(data.married_civil_partners.expertises) && 
                  data.married_civil_partners.expertises.map((expertise: string, index: number) => (
                    <span
                      key={`married-expertise-${index}`}
                      className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                    >
                      {getMarriedCouplesExpertiseLabel(expertise)}
                    </span>
                  ))
                }
              </div>
              {/* Other values on new line with heading */}
              {data.married_civil_partners.other && Array.isArray(data.married_civil_partners.other) && data.married_civil_partners.other.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs font-medium text-novaNeutral-600">Other:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {data.married_civil_partners.other.map((other: string, index: number) => (
                      <span
                        key={`married-other-${index}`}
                        className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                      >
                        {other}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      );
    }

    // Handle old format (backward compatibility)
    if (typeof data === 'object' && !Array.isArray(data)) {
      return (
        <div className="space-y-3">
          {Object.entries(data).map(([category, options]) => {
            if (!Array.isArray(options)) return null;
            return (
              <div key={category}>
                <span className="text-xs font-medium text-novaNeutral-600">{category}:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {options.map((option, index) => (
                    <span
                      key={index}
                      className="inline-flex px-2 py-1 text-xs font-medium bg-novaPrimary-100 text-novaPrimary-700 rounded"
                    >
                      {option}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    return <span className="text-sm text-novaNeutral-500">—</span>;
  };

  // Helper to render tags
  const renderTags = (values: string[] | undefined, colorClass: string = "bg-novaInactive text-novaNeutral-600 mr-1"): React.ReactNode => {
    if (!values || values.length === 0) return <span className="text-sm text-novaWarning-600">—</span>;
    
    return (
      <div className="flex flex-wrap gap-1">
        {values.map((value, index) => (
          <span
            key={index}
            className={`inline-flex px-2 py-1 text-xs font-medium rounded ${colorClass}`}
          >
            {value}
          </span>
        ))}
      </div>
    );
  };

  const handleStatusUpdate = async () => {
    if (!expertData?.id || selectedStatus === expertData.status) {
      return;
    }

    setIsUpdatingStatus(true);
    try {
      const updateData = {
        id: expertData.id,
        status: selectedStatus,
      };

      const response = await api.patch(`/v1/B2C-experts`, updateData);

      if (response && typeof response === "object" && "success" in response) {
        const apiResponse = response as any;
        if (apiResponse.success) {
          toastManager.addToast(
            createSuccessToast("Updated", "Status updated successfully", 3000)
          );
          // Call the callback to update the parent state
          if (onStatusUpdate && apiResponse.data) {
            onStatusUpdate(apiResponse.data);
          }
        } else {
          const message = apiResponse.message?.[0]?.message || "Failed to update status";
          toastManager.addToast(createErrorToast("Failed", message, 3000));
        }
      }
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to update status";
      toastManager.addToast(createErrorToast("Error", errorMessage, 3000));
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2">
            <i className="fas fa-spinner fa-spin text-novaPrimary-500"></i>
            <span className="text-sm text-novaNeutral-600">
              Loading legal expert details...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!expertData) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <i className="fas fa-exclamation-triangle text-novaWarning-500 text-2xl mb-2"></i>
            <p className="text-sm text-novaNeutral-600">
              No legal expert data available
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getFullName = () => {
    return `${expertData.first_name || ""} ${
      expertData.last_name || ""
    }`.trim();
  };

  const getStatusBadgeClass = (status: string | null | undefined) => {
    switch (status) {
      case "Onboarded":
        return "bg-novaSuccess-100 text-novaSuccess-800";
      case "New":
        return "bg-novaPurple-100 text-novaPurple-800";
      case "Review":
        return "bg-novaAlert-100 text-novaAlert-800";
      case "Rejected":
        return "bg-novaCaution-100 text-novaCaution-800";
      default:
        return "bg-novaNeutral-100 text-novaNeutral-700";
    }
  };

  const hasStatusChanged = selectedStatus !== expertData.status;

  return (
    <div className="bg-white rounded-lg p-8 border border-novaActive">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-novaNeutral-900">
            Nova Expert Application Details
          </h2>
          <p className="mt-1 text-sm text-novaNeutral-500">
            View comprehensive information about this Nova Expert application
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Onboard Button - Only show when status is not Onboarded */}
          {expertData.status !== "Onboarded" && (
            <FormButton
              variant="gradient"
              onClick={handleOnboardClick}
              className="px-3 py-1.5 whitespace-nowrap text-sm"
            >
              <i className="fas fa-user-plus mr-1.5"></i>
              Convert to Lawyer
            </FormButton>
          )}
          <FormButton
            variant="custom"
            onClick={onEdit}
            className="px-3 py-1.5 bg-novaBlack text-sm text-white hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] whitespace-nowrap"
          >
            <i className="fas fa-edit mr-1.5"></i>
            Edit
          </FormButton>
        </div>
      </div>

      <div className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-novaInactive rounded-lg p-4 border border-novaActive">
            <div className="flex items-center gap-4">
              {expertData.photo_url?.medium ? (
                <img
                  src={expertData.photo_url.medium}
                  alt={getFullName()}
                  className="h-16 w-16 rounded-full object-cover border border-novaDarkOrange"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              ) : (
                <div className="h-16 w-16 rounded-full bg-white flex items-center justify-center border border-novaActive">
                  <i className="fas fa-user text-novaDarkOrange text-2xl"></i>
                </div>
              )}
              <div>
                <p className="text-lg font-semibold text-novaNeutral-900">{toTitleCase(getFullName() || "")}</p>
                <span
                  className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${getStatusBadgeClass(expertData.status)}`}
                >
                  {expertData.status || "New"}
                </span>
              </div>
            </div>
          </div>
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Basic Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <InfoRow label="Email" value={expertData.email} />
            <InfoRow label="Phone" value={expertData.phone} />
            <InfoRow label="Gender" value={expertData.gender} />
          </div>
        </div>

        {/* Location & Work Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Location & Work Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="City" value={expertData.city} />
            <InfoRow label="Post Code" value={expertData.post_code} />
            <InfoRow label="Work Status" value={expertData.work_status} />
            <InfoRow label="Organisation Name" value={expertData.firm_name} />
          </div>
        </div>

        {/* Professional Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Professional Information
          </h3>
          <div className="space-y-4">
            <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">Professional Status</span>
              {expertData.professional_status?.values && expertData.professional_status.values.length > 0 ? (
                <div>
                  {/* Regular values (excluding OTHER) - map keys to display values */}
                  <div className="flex flex-wrap gap-1 mt-1">
                    {expertData.professional_status.values
                      .filter((val) => val !== "OTHER" && val !== "Other")
                      .map((val, idx) => (
                        <span
                          key={idx}
                          className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                        >
                          {getProfessionalStatusLabel(val)}
                        </span>
                      ))}
                    {/* Show OTHER tag if OTHER is in values */}
                    {expertData.professional_status.values.some((val) => val === "OTHER" || val === "Other") && (
                      <span className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded">
                        Other
                      </span>
                    )}
                  </div>
                  {/* Other value on new line with heading */}
                  {expertData.professional_status.other && (
                    <div className="mt-2">
                      <span className="text-xs font-medium text-novaNeutral-600">Other:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        <span className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded">
                          {expertData.professional_status.other}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <span className="text-sm text-novaNeutral-500">—</span>
              )}
            </div>

            <InfoRow
              label="Experience"
              value={expertData.experience ? `${expertData.experience} years` : null}
            />

            <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">Regulator</span>
              {expertData.regulator ? (
                <span className="text-sm text-novaNeutral-900">
                  {expertData.regulator.values && expertData.regulator.values.length > 0 && expertData.regulator.values[0] !== "OTHER" 
                    ? getRegulatorLabel(expertData.regulator.values[0])
                    : expertData.regulator.other 
                      ? `Other: ${expertData.regulator.other}`
                      : expertData.regulator.values?.[0] ? getRegulatorLabel(expertData.regulator.values[0]) : "—"}
                </span>
              ) : (
                <span className="text-sm text-novaNeutral-500">—</span>
              )}
            </div>

            <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">Accredited Specialist</span>
              {expertData.accredited_specialist?.values && expertData.accredited_specialist.values.length > 0 ? (
                <div className="flex flex-wrap gap-1 mt-1">
                  {expertData.accredited_specialist.values.map((val, idx) => (
                    <span
                      key={idx}
                      className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                    >
                      {getAccreditedSpecialistLabel(val)}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-sm text-novaNeutral-500">—</span>
              )}
            </div>

            {expertData.accredited_specialism_other && Array.isArray(expertData.accredited_specialism_other) && expertData.accredited_specialism_other.length > 0 && (
              <div className="flex flex-col space-y-1">
                <span className="text-xs font-medium text-novaNeutral-500">Accredited Specialism Other</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {expertData.accredited_specialism_other.filter(Boolean).map((item, i) => (
                    <span
                      key={i}
                      className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <InfoRow label="Remote Consultation" value={expertData.remote_consultation} />

            {/* <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">Consultation Offers</span>
              {expertData.consultation_offers?.values && expertData.consultation_offers.values.length > 0 ? (
                <div className="flex flex-wrap gap-1 mt-1">
                  {renderTags(expertData.consultation_offers.values)}
                </div>
              ) : (
                <span className="text-sm text-novaNeutral-500">—</span>
              )}
            </div> */}

            <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">Matter Types</span>
              {(() => {
                // Handle both formats: { values: [...] } or plain array
                let matterTypesArray: string[] = [];
                if (expertData.matter_types) {
                  if (typeof expertData.matter_types === "object" && !Array.isArray(expertData.matter_types) && "values" in expertData.matter_types) {
                    matterTypesArray = (expertData.matter_types as any).values || [];
                  } else if (Array.isArray(expertData.matter_types)) {
                    matterTypesArray = expertData.matter_types;
                  }
                }
                return matterTypesArray.length > 0 ? (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {matterTypesArray.map((val, idx) => (
                      <span
                        key={idx}
                        className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                      >
                        {getMatterTypeLabel(val)}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-sm text-novaNeutral-500">—</span>
                );
              })()}
            </div>

            {/* Service Details */}
            {expertData.service_details && Object.keys(expertData.service_details).length > 0 && (
              <div className="space-y-3">
                <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
                  Service Details
                </h3>
                {/* Client Types */}
                {expertData.service_details.offers && Array.isArray(expertData.service_details.offers) && expertData.service_details.offers.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Who do you offer services to?
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {expertData.service_details.offers.map((clientType: string) => (
                        <span
                          key={clientType}
                          className="px-2 py-0.5 bg-novaAlert-50 text-novaPrimary-700 text-xs rounded"
                        >
                          {getClientTypeLabel(clientType)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {/* Service Details by Category */}
                {formatServiceDetails(expertData?.service_details || {})}
              </div>
            )}
          </div>
        </div>

        {/* NCDR & Additional Information */}
        {(expertData.ncdr_magic || expertData.ncdr_description || expertData.compelling_quote) && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              NCDR & Additional Information
            </h3>
            {expertData.ncdr_magic && expertData.ncdr_magic.values && expertData.ncdr_magic.values.length > 0 && (
              <div>
                <span className="text-xs font-medium text-novaNeutral-500">
                  NCDR Magic (What makes them special)
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {expertData.ncdr_magic.values.map((val, idx) => (
                    <span
                      key={idx}
                      className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                    >
                      {getNcdrMagicLabel(val)}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {expertData.ncdr_description && (
              <div className="mt-3">
                <span className="text-xs font-medium text-novaNeutral-500">
                  NCDR Description
                </span>
                <p className="text-sm text-novaNeutral-900 mt-1 break-words overflow-wrap-anywhere">
                  {expertData.ncdr_description}
                </p>
              </div>
            )}
            {expertData.compelling_quote && (
              <div className="mt-3">
                <span className="text-xs font-medium text-novaNeutral-500">
                  Compelling Quote
                </span>
                <p className="text-sm text-novaNeutral-900 mt-1 break-words overflow-wrap-anywhere">
                  {expertData.compelling_quote}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Timestamps */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Record Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Created At" value={formatTimestamp(expertData.created_at || "")} />
            <InfoRow label="Updated At" value={formatTimestamp(expertData.updated_at || "")} />
          </div>
        </div>

        {/* Application Status Section - Inline Edit */}
        <div className="space-y-4 bg-novaInactive rounded-lg p-4 border border-novaActive">
          <div>
            <h3 className="text-sm font-medium text-novaNeutral-700">
              Update Application Status
            </h3>
            <p className="text-xs text-novaNeutral-500 mt-1">
              Change the status to approve, reject, or mark for review
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
            <div className="w-full sm:w-64">
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Status
              </label>
              <CustomSelect
                value={selectedStatus}
                onChange={(value) => setSelectedStatus(value as LegalExpertStatus)}
                options={STATUS_OPTIONS}
                placeholder="Select status"
                triggerClassName="rounded-md bg-white"
              />
            </div>
            <FormButton
              variant="custom"
              onClick={handleStatusUpdate}
              disabled={isUpdatingStatus || !hasStatusChanged}
              className={`px-4 py-2 inline-flex items-center justify-center gap-2 text-sm rounded-md transition-colors ${
                hasStatusChanged
                  ? "bg-novaPrimary-500 hover:bg-novaPrimary-600 text-white"
                  : "bg-novaNeutral-200 text-novaNeutral-400 cursor-not-allowed"
              }`}
            >
              {isUpdatingStatus ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  Updating...
                </>
              ) : (
                <>
                  <i className="fas fa-save"></i>
                  Save Status
                </>
              )}
            </FormButton>
          </div>
          
          {hasStatusChanged && (
            <p className="text-xs text-novaWarning-600">
              <i className="fas fa-info-circle mr-1"></i>
              Status will change from "{expertData.status || "New"}" to "{selectedStatus}"
            </p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end space-x-2 pt-4 mt-6 border-t border-novaActive">
        <FormButton
          variant="custom"
          onClick={onClose}
          className="px-4 py-2 text-sm border border-novaNeutral-500 bg-white hover:bg-novaBlack text-novaNeutral-700 hover:text-white"
        >
          Close
        </FormButton>
      </div>
    </div>
  );
};

export default ViewLegalExpertDetails;
