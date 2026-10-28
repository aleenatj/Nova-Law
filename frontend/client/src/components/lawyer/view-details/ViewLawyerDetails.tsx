import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Lawyer } from "@/lib/types";
import { toastManager, createSuccessToast, createErrorToast } from "@/utils/toasts";
import { api } from "@/lib/api";
import { formatTimestamp, FormButton } from "@/utils";
import { toTitleCase } from "@/lib/utils";

interface ViewLawyerDetailsProps {
  lawyerData: Lawyer | null;
  onClose: () => void;
  onEdit: () => void;
  isLoading?: boolean;
}

const ViewLawyerDetails: React.FC<ViewLawyerDetailsProps> = ({
  lawyerData,
  onClose,
  onEdit,
  isLoading = false,
}) => {
  const [isResending, setIsResending] = useState(false);
  const InfoRow = ({
    label,
    value,
  }: {
    label: string;
    value?: string | number | null | React.ReactNode;
  }) => (
    <div className="flex flex-col space-y-1">
      <span className="text-xs font-medium text-novaNeutral-500">{label}</span>
      <span className="text-sm text-novaNeutral-900 break-words overflow-wrap-anywhere">{value ?? "—"}</span>
    </div>
  );

  const handleLawFirmClick = () => {
    if (lawyerData?.lawfirms?.id) {
      // Open law firm details in a new tab
      window.open(`/organisations?view=${lawyerData.lawfirms.id}`, "_blank");
    }
  };

  const handleResendEmail = async (userId: string) => {
    if (!userId) {
      const toast = createErrorToast(
        "Error",
        "User ID is not available for this navigator"
      );
      toastManager.addToast(toast);
      return;
    }

    setIsResending(true);

    try {
      await api.post("/v1/auth/resend-initial-password", {
        user_id: userId,
      });

      const toast = createSuccessToast(
        "Success",
        "Setup email has been resent successfully"
      );
      toastManager.addToast(toast);
    } finally {
      setIsResending(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2">
            <i className="fas fa-spinner fa-spin text-novaPrimary-500"></i>
            <span className="text-sm text-novaNeutral-600">
              Loading expert details...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!lawyerData) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <i className="fas fa-exclamation-triangle text-novaWarning-500 text-2xl mb-2"></i>
            <p className="text-sm text-novaNeutral-600">
              No expert data available
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getFullName = () => {
    return `${toTitleCase(lawyerData.first_name || "")} ${
      toTitleCase(lawyerData.last_name || "")
    }`.trim();
  };

  const getLocation = () => {
    return (
      [lawyerData.city, lawyerData.county].filter(Boolean).join(", ") || "—"
    );
  };

  return (
    <div className="bg-white rounded-lg border border-novaActive p-8">
      <div className="mb-4 flex items-center justify-between">
        <div className="pb-2">
          <h2 className="text-xl font-semibold text-novaNeutral-900">
            Expert Details
          </h2>
          <p className="text-sm text-novaNeutral-500">
            View comprehensive information about this expert
          </p>
        </div>
        <FormButton
          variant="custom"
          onClick={onEdit}
          className="sm:px-3 sm:py-1.5 px-2 py-1 text-sm bg-novaBlack text-white hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] whitespace-nowrap"
        >
          <i className="fas fa-edit mr-1.5"></i>
          Edit
        </FormButton>
      </div>

      {/* Password Setup Alert */}
      {lawyerData.needs_password_setup && (
        <div className="bg-novaActive border-l-4 border-novaDarkOrange p-3 mb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <p className="text-xs text-novaPrimary-800 flex items-center gap-2">
              <i className="fas fa-exclamation-circle text-novaDarkOrange"></i>
              <span>User has not set up their password</span>
            </p>
            <FormButton
              variant="custom"
              type="button"
              onClick={() => {handleResendEmail(lawyerData.user_id as string);}}
              className="inline-flex items-center justify-center px-3 py-1.5 bg-novaPrimary-600 hover:bg-novaPrimary-700 text-white text-sm transition-colors whitespace-nowrap"
            >
              <i className="fas fa-sync-alt mr-1.5"></i>
              Resend Setup Email
            </FormButton>
          </div>
        </div>
      )}

      <div className="space-y-8">
          <div className="bg-novaInactive rounded-lg p-6 border border-novaActive">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              {/* Photo Section */}
              <div className="flex-shrink-0">
                <div className="h-20 w-20 rounded-full bg-white border border-novaDarkOrange flex items-center justify-center overflow-hidden">
                  {lawyerData.photo_urls?.thumbnail ? (
                    <img
                      src={lawyerData.photo_urls.thumbnail}
                      alt={`${getFullName()} photo`}
                      className="h-24 w-24 object-cover"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                        const parent = e.currentTarget.parentElement;
                        if (parent) {
                          parent.innerHTML =
                            '<i class="fas fa-user text-novaDarkOrange text-3xl"></i>';
                        }
                      }}
                    />
                  ) : (
                    <i className="fas fa-user text-novaDarkOrange text-3xl"></i>
                  )}
                </div>
              </div>

              {/* Navigator Details */}
              <div className="flex-1">
                <h3 className="text-xl font-bold text-novaNeutral-900 mb-2">
                  {getFullName()}
                </h3>
                <div className="flex flex-wrap gap-3 items-center">
                  {lawyerData.status && (
                    <span
                      className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full ${
                        lawyerData.status.toLowerCase() === "active"
                          ? "bg-novaSuccess-100 text-novaSuccess-800"
                          : "bg-novaWarning-100 text-novaWarning-600"
                      }`}
                    >
                      {lawyerData.status === "Active" ? "Active" : "Inactive"}
                    </span>
                  )}
                  {lawyerData.experience && lawyerData.experience !== "Not specified" && (
                    <span className="inline-flex items-center px-3 py-1 text-xs font-medium bg-novaActive text-novaDarkOrange rounded-full">
                      <i className="fas fa-briefcase mr-1.5"></i>
                      {lawyerData.experience} experience
                    </span>
                  )}
                </div>
                
              </div>
            </div>
          </div>
        {/* Basic Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Basic Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Full Name" value={getFullName()} />
            <InfoRow label="Email" value={lawyerData.email} />
            <InfoRow label="Phone" value={lawyerData.phone} />
            <InfoRow label="Gender" value={lawyerData.gender} />
            <InfoRow
              label="Status"
              value={
                <span
                  className={`inline-flex px-2 py-0.5 text-[11px] font-medium rounded-full ${
                    lawyerData.status?.toLowerCase() === "active"
                      ? "bg-novaSuccess-100 text-novaSuccess-800"
                      : "bg-novaWarning-100 text-novaWarning-600"
                  }`}
                >
                  {lawyerData.status === "Active" ? "Active" : "Inactive"}
                </span>
              }
            />
            {lawyerData.experience ? (
              <InfoRow
                label="Experience"
                value={`${lawyerData.experience}`}
              />
            ) : (
              <InfoRow label="Experience" value="—" />
            )}
          </div>
          {lawyerData.about && (
            <div className="mt-3">
              <span className="text-xs font-medium text-novaNeutral-500">
                About
              </span>
              <p className="text-sm text-novaNeutral-900 mt-1 break-words overflow-wrap-anywhere">
                {lawyerData.about}
              </p>
            </div>
          )}
        </div>

        {/* Address Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Address Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Address Line 1" value={lawyerData.address_line_1} />
            <InfoRow label="Address Line 2" value={lawyerData.address_line_2} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="City" value={lawyerData.city} />
            <InfoRow label="County" value={lawyerData.county} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoRow label="Country" value={lawyerData.country} />
          <InfoRow label="Postal Code" value={lawyerData.postal_code} />
          </div>
        </div>

        {/* Professional Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Professional Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="SRA Number" value={lawyerData.sra_number} />
            <InfoRow
              label="Admitted Date (Solicitor)"
              value={formatTimestamp(lawyerData.admitted_date_solicitor || "", true)}
            />
            <InfoRow label="Bar Number" value={lawyerData.bar_number} />
            
            <InfoRow
              label="Called Date (Barrister)"
              value={formatTimestamp(lawyerData.called_date_barrister || "", true)}
            />
            <InfoRow label="Registration Number" value={lawyerData.reg_no} />
            <InfoRow
              label="Admitted Date (CILEX)"
              value={formatTimestamp(lawyerData.admitted_date_cliex || "", true)}
            />
            <InfoRow label="Joined Date" value={formatTimestamp(lawyerData.joined_at || "", true)} />
            <InfoRow label="Left Date" value={formatTimestamp(lawyerData.left_at || "", true)} />
            <InfoRow label="Regulator" value={lawyerData.regulator + (lawyerData.regulator_other ? ` : ${lawyerData.regulator_other}` : "")} />

          </div>
        </div>

        {/* Financial Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Financial Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow
              label="Hourly Rate"
              value={
                lawyerData.hourly_rate
                  ? `£${lawyerData.hourly_rate.toFixed(0)}`
                  : undefined
              }
            />
            <InfoRow
              label="First Consultation Charge"
              value={
                lawyerData.charge_first_consultation
                  ? `£${lawyerData.charge_first_consultation}`
                  : undefined
              }
            />
          </div>
        </div>

        {/* Specializations & Expertise */}
        {(lawyerData.accredited_specialisms && lawyerData.accredited_specialisms?.length > 0 ||
          lawyerData.expert_types?.length ||
          lawyerData.matter_types?.length ||
          lawyerData.relationship_types?.length ||
          lawyerData.dr_preferences?.length) && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              Specialisations & Expertise
            </h3>
            <div className="grid grid-cols-1 gap-4">
              {lawyerData.accredited_specialisms &&
                lawyerData.accredited_specialisms.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Accredited Specialisations
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lawyerData.accredited_specialisms.map((type, index) => (
                        <span
                          key={index}
                          className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {lawyerData.accredited_specialism_other &&
                  Array.isArray(lawyerData.accredited_specialism_other) &&
                  lawyerData.accredited_specialism_other.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Accredited Specialisms Other
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {lawyerData.accredited_specialism_other.filter(Boolean).map((item, i) => (
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
              {lawyerData.expert_types &&
                lawyerData.expert_types.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Expert Types
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lawyerData.expert_types.map((type, index) => (
                        <span
                          key={index}
                          className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              {lawyerData.expert_types_other && (
                <div>
                  <span className="text-xs font-medium text-novaNeutral-500">
                    Expert Types (Other)
                  </span>
                  <div className="mt-1">
                    <span className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded border border-novaWarning-200">
                      {lawyerData.expert_types_other}
                    </span>
                  </div>
                </div>
              )}
              {lawyerData.matter_types &&
                lawyerData.matter_types.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Matter Types
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lawyerData.matter_types.map((type, index) => {
                        // Convert enum name to label if needed (handle both "FINANCIAL_CLAIMS" and "Financial Claims")
                        const matterTypeLabels: Record<string, string> = {
                          "FINANCIAL_CLAIMS": "Financial Claims",
                          "CHILDREN": "Children",
                          "Financial Claims": "Financial Claims",
                          "Children": "Children",
                        };
                        const displayLabel = matterTypeLabels[type] || type;
                        return (
                          <span
                            key={index}
                            className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                          >
                            {displayLabel}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
              {lawyerData.relationship_types &&
                lawyerData.relationship_types.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Relationship Types
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lawyerData.relationship_types.map((type, index) => (
                        <span
                          key={index}
                          className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {lawyerData.expertises && typeof lawyerData.expertises === "object" && (() => {
                  // Helper to format relationship type key to display name
                  const formatRelationshipType = (key: string): string => {
                    return key
                      .split("_")
                      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(" ");
                  };

                  // Structure data by relationship type
                  const expertiseGroups: Array<{
                    relationshipType: string;
                    expertises: string[];
                    otherValues: string[];
                  }> = [];

                  Object.entries(lawyerData.expertises).forEach(([key, value]) => {
                    if (typeof value === "object" && value != null && !Array.isArray(value)) {
                      const expertises: string[] = [];
                      const otherValues: string[] = [];

                      // Type guard for expertise group structure
                      const expertiseGroup = value as { expertises?: string[]; other?: string[] };

                      // Extract expertises (excluding "other" option)
                      // Filter out: "Other", "Other " (with space), enum names like "OTHER_MARRIED_CIVIL_PARTNERS", "OTHER_COHABITEES"
                      if (expertiseGroup.expertises && Array.isArray(expertiseGroup.expertises)) {
                        expertiseGroup.expertises.forEach((item: string) => {
                          if (typeof item === "string") {
                            const trimmedItem = item.trim();
                            // Exclude if it's "Other", starts with "OTHER", or contains "OTHER_"
                            if (
                              trimmedItem &&
                              trimmedItem.toLowerCase() !== "other" &&
                              !trimmedItem.startsWith("OTHER") &&
                              !trimmedItem.includes("OTHER_")
                            ) {
                              expertises.push(trimmedItem);
                            }
                          }
                        });
                      }

                      // Extract other values
                      if (expertiseGroup.other && Array.isArray(expertiseGroup.other)) {
                        expertiseGroup.other.forEach((otherItem: string) => {
                          if (typeof otherItem === "string" && otherItem.trim()) {
                            otherValues.push(otherItem);
                          }
                        });
                      }

                      // Only add group if it has expertises or other values
                      if (expertises.length > 0 || otherValues.length > 0) {
                        expertiseGroups.push({
                          relationshipType: key === "married_civil_partners" ? "Married and Civil Partners" : formatRelationshipType(key),
                          expertises,
                          otherValues,
                        });
                      }
                    }
                  });

                  // Only render if there are any expertise groups
                  if (expertiseGroups.length === 0) {
                    return null;
                  }

                  return (
                    <div>
                      <span className="text-xs font-medium text-novaNeutral-500">
                        Expertises
                      </span>
                      <div className="space-y-3 mt-2">
                        {expertiseGroups.map((group, groupIdx) => (
                          <div 
                            key={groupIdx} 
                            className="bg-novaInactive rounded-lg p-3 border border-novaActive space-y-2"
                          >
                            {/* Relationship Type Group Label */}
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-medium text-novaNeutral-600 uppercase tracking-wide">
                                {group.relationshipType}
                              </span>
                            </div>
                            
                            {/* Expertises List */}
                            {group.expertises.length > 0 && (
                              <div className="flex flex-wrap gap-1.5">
                                {group.expertises.map((expertise, idx) => (
                                  <span
                                    key={`${groupIdx}-expertise-${idx}`}
                                    className="inline-flex px-2.5 py-1 text-xs bg-novaActive text-novaPrimary-700 rounded"
                                  >
                                    {expertise}
                                  </span>
                                ))}
                              </div>
                            )}

                            {/* Other Subheading and Values - Styled as exceptional case */}
                            {group.otherValues.length > 0 && (
                              <div className="space-y-1.5 pt-2 border-t border-novaNeutral-200">
                                <span className="text-xs font-medium text-novaWarning-600 italic">
                                  Other
                                </span>
                                <div className="flex flex-wrap gap-1.5">
                                  {group.otherValues.map((otherValue, idx) => (
                                    <span
                                      key={`${groupIdx}-other-${idx}`}
                                      className="inline-flex px-2.5 py-1 text-xs font-medium bg-novaWarning-50 text-novaWarning-700 rounded border border-novaWarning-200"
                                    >
                                      {otherValue}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}
              {lawyerData.dr_preferences &&
                lawyerData.dr_preferences.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-novaNeutral-500">
                      DR Preferences
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lawyerData.dr_preferences.map((preference, index) => (
                        <span
                          key={index}
                          className="inline-flex px-2 py-1 text-xs bg-novaAlert-50 text-novaPrimary-700 rounded"
                        >
                          {preference}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          </div>
        )}

        {/* Links & Media */}
        {(lawyerData.photo_urls?.medium || lawyerData.linkedin_url) && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              Links & Media
            </h3>
            <div className="grid grid-cols-1 gap-4">
              {lawyerData.linkedin_url && (
                <div className="flex flex-col space-y-1">
                  <span className="text-xs font-medium text-novaNeutral-500">
                    LinkedIn URL
                  </span>
                  <a
                    href={lawyerData.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-novaDarkOrange hover:text-novaDarkOrange hover:underline break-words overflow-wrap-anywhere"
                  >
                    {lawyerData.linkedin_url}
                    <i className="fas fa-external-link-alt ml-1 text-xs"></i>
                  </a>
                </div>
              )}
              {lawyerData.photo_urls?.thumbnail && (
                <div className="flex flex-col space-y-1">
                  <span className="text-xs font-medium text-novaNeutral-500">
                    Profile Photo
                  </span>
                  <div className="flex items-center gap-3">
                    <img
                      src={lawyerData.photo_urls.thumbnail}
                      alt={getFullName()}
                      className="h-12 w-12 rounded-full object-cover border border-novaDarkOrange"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                      }}
                    />
                    <a
                      href={lawyerData.photo_urls.large}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-novaPrimary-600 hover:text-novaPrimary-700 hover:underline"
                    >
                      View Photo
                      <i className="fas fa-external-link-alt ml-1 text-xs"></i>
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {/* Law Firm Information */}
        {lawyerData.lawfirms && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              Organisation Information
            </h3>
            <div
              onClick={handleLawFirmClick}
              className="bg-novaInactive rounded-lg p-4 border border-novaActive cursor-pointer hover:bg-novaActive hover:border-novaActive transition-all duration-200 group"
              role="button"
              tabIndex={0}
              onKeyPress={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  handleLawFirmClick();
                }
              }}
            >
              <div className="flex items-center gap-4">
                {/* Firm Logo */}
                <div className="flex-shrink-0">
                  <div className="h-16 w-16 rounded-lg bg-white border border-novaActive flex items-center justify-center overflow-hidden group-hover:border-novaActive transition-colors">
                    {lawyerData.lawfirms?.logos?.medium ? (
                      <img
                        src={lawyerData.lawfirms?.logos?.medium || ""}
                        alt={`${lawyerData.lawfirms?.name || "Law firm"} logo`}
                        className="h-16 w-16 rounded-lg object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    ) : (
                      <i className="fas fa-building text-novaDarkOrange text-2xl group-hover:text-novaDarkOrange transition-colors"></i>
                    )}
                  </div>
                </div>

                {/* Organisation Name */}
                <div className="flex-1">
                  <div className="flex flex-col space-y-1">
                    <span className="text-xs font-medium text-novaNeutral-500">
                      Organisation Name
                    </span>
                    <span className="text-base font-semibold text-novaPrimary-600 group-hover:text-novaPrimary-700 transition-colors">
                      {lawyerData.lawfirms.name || "—"}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-novaActive text-novaPrimary-700 rounded group-hover:bg-novaInactive transition-colors">
                      <i className="fas fa-briefcase mr-1"></i>
                      Associated
                    </span>
                    <span className="text-xs text-novaNeutral-500 group-hover:text-novaPrimary-600 transition-colors">
                      <i className="fas fa-external-link-alt mr-1"></i>
                      Click to view details
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Additional Information */}
        {(lawyerData.pi_insurance ||
          lawyerData.conflict_level_disinclination ||
          lawyerData.testimonial
          ) && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              Additional Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InfoRow label="PI Insurance" value={lawyerData.pi_insurance} />
              <InfoRow
                label="Conflict Level Disinclination"
                value={lawyerData.conflict_level_disinclination}
              />
            </div>
            {lawyerData.testimonial && (
              <div className="mt-3">
                <span className="text-xs font-medium text-novaNeutral-500">
                  Testimonial
                </span>
                <p className="text-sm text-novaNeutral-900 mt-1 italic break-words overflow-wrap-anywhere">
                  "{lawyerData.testimonial}"
                </p>
              </div>
            )}
          </div>
        )}
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

export default ViewLawyerDetails;
