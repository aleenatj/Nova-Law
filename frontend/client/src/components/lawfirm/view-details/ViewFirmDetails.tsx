import React from "react";
import { Button } from "@/components/ui/button";
import { LawFirm } from "@/lib/types";
import { FormButton } from "@/utils";

interface ViewFirmDetailsProps {
  firmData: LawFirm | null;
  onClose: () => void;
  onEdit: () => void;
  isLoading?: boolean;
}

const ViewFirmDetails: React.FC<ViewFirmDetailsProps> = ({
  firmData,
  onClose,
  onEdit,
  isLoading = false,
}) => {
  const InfoRow = ({
    label,
    value,
  }: {
    label: string;
    value?: string | null | React.ReactNode;
  }) => (
    <div className="flex flex-col space-y-1">
      <span className="text-xs font-medium text-novaNeutral-500">{label}</span>
      <span className="text-sm text-novaNeutral-900">{value || "—"}</span>
    </div>
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2">
            <i className="fas fa-spinner fa-spin text-novaPrimary-500"></i>
            <span className="text-sm text-novaNeutral-600">
              Loading organisation details...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!firmData) {
    return (
      <div className="bg-white rounded-lg border border-novaNeutral-200 p-4">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <i className="fas fa-exclamation-triangle text-novaWarning-500 text-2xl mb-2"></i>
            <p className="text-sm text-novaNeutral-600">
              No organisation data available
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-novaActive p-8">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-novaNeutral-900">
            Organisation Details
          </h2>
          <p className="mt-1 text-xs text-novaNeutral-500">
            View comprehensive information about this organisation
          </p>
        </div>
        <FormButton
          variant="custom"
          onClick={onEdit}
          className="sm:px-3 sm:py-1.5 px-2 py-1 text-sm bg-novaBlack text-white hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] whitespace-nowrap"        >
          <i className="fas fa-edit mr-1.5"></i>
          Edit
        </FormButton>
      </div>

      <div className="space-y-8">
        {/* Firm Logo & Header */}
        <div className="space-y-3">
          <div className="bg-novaInactive rounded-lg p-6 border border-novaActive">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              {/* Logo Section */}
              <div className="flex-shrink-0">
                <div className="h-24 w-24 rounded-lg bg-white border border-novaActive flex items-center justify-center overflow-hidden">
                  {firmData.logos?.thumbnail ? (
                    <img
                      src={firmData.logos?.thumbnail}
                      alt={`${firmData.name} logo`}
                      className="h-24 w-24 object-contain p-2"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                        const parent = e.currentTarget.parentElement;
                        if (parent) {
                          parent.innerHTML =
                            '<i class="fas fa-building text-novaDarkOrange text-3xl"></i>';
                        }
                      }}
                    />
                  ) : (
                    <i className="fas fa-building text-novaDarkOrange text-3xl"></i>
                  )}
                </div>
              </div>

              {/* Firm Details */}
              <div className="flex-1">
                <h3 className="text-xl font-bold text-novaNeutral-900 mb-2">
                  {firmData.name}
                </h3>
                <div className="flex flex-wrap gap-3 items-center">
                  <span className="inline-flex items-center px-3 py-1 text-xs font-medium bg-novaActive text-novaDarkOrange rounded-full">
                    <i className="fas fa-briefcase mr-1.5"></i>
                    {firmData.law_firm_type}
                  </span>
                  {firmData.status && (
                    <span
                      className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                        firmData.status?.toLowerCase() === "active"
                          ? "bg-novaSuccess-100 text-novaSuccess-800"
                          : "bg-novaWarning-100 text-novaWarning-600"
                      }`}
                    >
                      {firmData.status}
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
            <InfoRow label="Organisation Name" value={firmData.name} />
            <InfoRow label="Organisation Type" value={firmData.law_firm_type} />
            <InfoRow label="Status" value={<span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
              firmData.status?.toLowerCase() === "active"
                ? "bg-novaSuccess-100 text-novaSuccess-800"
                : "bg-novaWarning-100 text-novaWarning-600"
            }`}>{firmData.status}</span>} />
          </div>

          {firmData.about && <InfoRow label="About" value={<p className="text-sm text-novaNeutral-600 leading-relaxed">{firmData.about}</p>} />}
        </div>

        {/* Contact Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Contact Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Contact Person" value={firmData.contact_person} />
            <InfoRow label="Contact Number" value={firmData.contact_no} />
            <InfoRow label="Contact Email" value={<span className="break-words break-all">{firmData.contact_email}</span>} />
          </div>
        </div>

        {/* Address Information */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Address Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Address Line 1" value={firmData.address_line_1} />
            <InfoRow label="Address Line 2" value={firmData.address_line_2} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="City" value={firmData.city} />
            <InfoRow label="County" value={firmData.state} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Postal Code" value={firmData.postal_code} />
            <InfoRow label="Country" value={firmData.country} />
          </div>
        </div>

        {/* Website & URLs */}
        <div className="space-y-3">
          <h3 className="text-base font-medium text-novaNeutral-700 border-b border-novaActive">
            Website & URLs
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {firmData.website_url ? (
              <div className="flex flex-col space-y-1">
                <span className="text-xs font-medium text-novaNeutral-500">
                  Website URL
                </span>
                <a
                  href={firmData.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-novaPrimary-600 hover:text-novaPrimary-700 hover:underline break-all"
                >
                  {firmData.website_url}
                  <i className="fas fa-external-link-alt ml-1 text-xs"></i>
                </a>
              </div>
            ) : (
              <InfoRow label="Website URL" value={null} />
            )}

            {firmData.engage_form_url ? (
              <div className="flex flex-col space-y-1">
                <span className="text-xs font-medium text-novaNeutral-500">
                  Client Id
                </span>
                <span
                >
                  {firmData.engage_form_url}
                </span>
              </div>
            ) : (
              <InfoRow label="Client Id" value={null} />
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

export default ViewFirmDetails;
