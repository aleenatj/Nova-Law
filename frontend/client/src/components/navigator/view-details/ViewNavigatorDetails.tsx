import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Navigator } from "@/lib/types";
import { api } from "@/lib/api";
import { toastManager, createSuccessToast, createErrorToast } from "@/utils/toasts";
import { formatTimestamp, FormButton } from "@/utils";

interface ViewNavigatorDetailsProps {
  navigatorData: Navigator | null;
  onClose: () => void;
  onEdit: () => void;
  isLoading?: boolean;
}

const ViewNavigatorDetails: React.FC<ViewNavigatorDetailsProps> = ({
  navigatorData,
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
    value?: string | number | null;
  }) => (
    <div className="flex flex-col space-y-1">
      <span className="text-xs font-medium text-novaNeutral-500">{label}</span>
      <span
        className="text-sm text-novaNeutral-900 break-all whitespace-pre-line"
        style={{
          wordBreak: "break-word",
          overflowWrap: "break-word",
        }}
        title={typeof value === "string" && value.length > 24 ? value : undefined}
      >
        {value || "—"}
      </span>
    </div>
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2">
            <i className="fas fa-spinner fa-spin text-novaPrimary-500"></i>
            <span className="text-sm text-novaNeutral-600">
              Loading navigator details...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!navigatorData) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <i className="fas fa-exclamation-triangle text-novaWarning-500 text-2xl mb-2"></i>
            <p className="text-sm text-novaNeutral-600">
              No navigator data available
            </p>
          </div>
        </div>
      </div>
    );
  }

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

  const getFullName = () =>
    `${navigatorData.first_name || ""} ${
      navigatorData.last_name || ""
    }`.trim() || "—";

  return (
    <div className="bg-white rounded-lg border border-novaActive p-8">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-novaNeutral-900">
            Navigator Details
          </h2>
          <p className="mt-1 text-xs text-novaNeutral-500">
            View comprehensive information about this navigator
          </p>
        </div>
        <FormButton
          onClick={onEdit}
          variant="custom"
          className="sm:px-3 sm:py-1.5 px-2 py-1 bg-novaBlack text-sm text-white hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] whitespace-nowrap"
        >
          <i className="fas fa-edit mr-1.5"></i>
          Edit
        </FormButton>
      </div>

      {/* Password Setup Alert */}
      {navigatorData.needs_password_setup && (
        <div className="bg-novaActive border-l-4 border-novaDarkOrange p-4 mb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <p className="text-sm text-novaPrimary-800 flex items-center gap-2">
              <i className="fas fa-exclamation-circle text-novaDarkOrange"></i>
              <span>User has not set up their password</span>
            </p>
            <FormButton
              variant="custom"
              type="button"
              onClick={() => handleResendEmail(navigatorData.id)}
              disabled={isResending}
              className="inline-flex items-center justify-center px-3 py-1.5 bg-novaPrimary-600 hover:bg-novaPrimary-700 text-white text-sm transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <i className={`fas ${isResending ? 'fa-spinner fa-spin' : 'fa-sync-alt'} mr-1.5`}></i>
              {isResending ? "Sending..." : "Resend Setup Email"}
            </FormButton>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Navigator Header */}
        <div className="space-y-3">
          <div className="bg-novaInactive rounded-lg p-6 border border-novaActive">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              {/* Photo Section */}
              <div className="flex-shrink-0">
                <div className="h-20 w-20 rounded-full bg-white border border-novaActive flex items-center justify-center overflow-hidden">
                  {navigatorData.photo_urls?.thumbnail ? (
                    <img
                      src={navigatorData.photo_urls.thumbnail}
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
                  {/* {navigatorData.gender && (
                    <span className="inline-flex items-center px-3 py-1 text-xs font-medium bg-novaPrimary-100 text-novaPrimary-700 rounded-full">
                      <i className="fas fa-user mr-1.5"></i>
                      {navigatorData.gender}
                    </span>
                  )} */}
                  {navigatorData.status && (
                    <span
                      className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full ${
                        navigatorData.status.toLowerCase() === "active"
                          ? "bg-novaSuccess-100 text-novaSuccess-800"
                          : "bg-novaWarning-100 text-novaWarning-600"
                      }`}
                    >
                      {/* <i className="fas fa-check-circle mr-1.5"></i> */}
                      {navigatorData.status}
                    </span>
                  )}
                  {navigatorData.experience && (
                    <span className="inline-flex items-center px-3 py-1 text-xs font-medium bg-novaPrimary-100 text-novaPrimary-700 rounded-full">
                      <i className="fas fa-briefcase mr-1.5"></i>
                      {navigatorData.experience} years experience
                    </span>
                  )}
                </div>
                
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
            <InfoRow label="First Name" value={navigatorData.first_name} />
            <InfoRow label="Last Name" value={navigatorData.last_name} />
            <InfoRow label="Gender" value={navigatorData.gender} />
            {navigatorData.gender === "Other" && navigatorData.gender_other && (
              <InfoRow
                label="Specified Gender"
                value={navigatorData.gender_other}
              />
            )}
            <InfoRow label="Status" value={navigatorData.status} />
          </div>
        </div>

        {/* Contact Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Contact Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">
                Email
              </span>
              {navigatorData.email ? (
                <a
                  href={`mailto:${navigatorData.email}`}
                  className="text-sm text-novaPrimary-600 hover:text-novaPrimary-700 hover:underline break-all"
                  style={{
                    wordBreak: "break-all",
                    overflowWrap: "break-word",
                  }}
                >
                  {navigatorData.email}
                </a>
              ) : (
                <span className="text-sm text-novaNeutral-900">—</span>
              )}
            </div>
            <div className="flex flex-col space-y-1">
              <span className="text-xs font-medium text-novaNeutral-500">
                Phone
              </span>
              {navigatorData.phone ? (
                <a
                  href={`tel:${navigatorData.phone}`}
                  className="text-sm text-novaPrimary-600 hover:text-novaPrimary-700 hover:underline"
                >
                  {navigatorData.phone}
                </a>
              ) : (
                <span className="text-sm text-novaNeutral-900">—</span>
              )}
            </div>
          </div>
        </div>

        {/* Professional Information */}
        {(navigatorData.specialization || navigatorData.experience) && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              Professional Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {navigatorData.specialization && (
                <InfoRow
                  label="Specialisation"
                  value={navigatorData.specialization}
                />
              )}
              {navigatorData.experience && (
                <InfoRow
                  label="Years of Experience"
                  value={navigatorData.experience}
                />
              )}
            </div>
          </div>
        )}

        {/* LinkedIn & URLs */}
        {navigatorData.linkedin_url && (
          <div className="space-y-3">
            <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
              Social & Professional Links
            </h3>
            <div className="grid grid-cols-1 gap-4">
              <div className="flex flex-col space-y-1">
                <span className="text-xs font-medium text-novaNeutral-500">
                  LinkedIn Profile
                </span>
                <a
                  href={navigatorData.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-novaPrimary-600 hover:text-novaPrimary-700 hover:underline break-all"
                >
                  {navigatorData.linkedin_url}
                  <i className="fas fa-external-link-alt ml-1 text-xs"></i>
                </a>
              </div>
            </div>
          </div>
        )}

        {/* No timeline info (joined_at or left_at) available; only created_at and updated_at are present. */}

        {/* Metadata */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            More Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow
              label="Created At"
              value={formatTimestamp(navigatorData.created_at || "")}
            />
            <InfoRow
              label="Updated At"
              value={formatTimestamp(navigatorData.updated_at || "")}
            />
            {navigatorData.user_id && (
              <InfoRow label="User ID" value={navigatorData.user_id} />
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end space-x-2 pt-4 mt-6 border-t border-novaActive">
        <FormButton
          onClick={onClose}
          variant="custom"
          className="px-4 py-2 text-sm border border-novaNeutral-500 bg-white hover:bg-novaBlack text-novaNeutral-700 hover:text-white"
        >
          Close
        </FormButton>
      </div>
    </div>
  );
};

export default ViewNavigatorDetails;
