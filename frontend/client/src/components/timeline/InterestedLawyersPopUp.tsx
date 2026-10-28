import React, { useState, useRef, useEffect } from "react";
import InterestedLawyerDetailsCard from "./InterestedLawyerDetailsCard";
import { InterestedLawyerType, InterestedLawyersModalProps } from "@/lib/types";
import {
  toastManager,
  createSuccessToast,
  createErrorToast,
} from "@/utils/toasts";
import { api } from "@/lib/api";
import GlobalModalWrapper from "../modal/GlobalModalWrapper";
import { FormButton } from "@/utils";

interface ApiResponse {
  success: boolean;
  message?: string;
}

// Helper function to map API response to InterestedLawyerType
const mapInterestedLawyerToDetails = (
  lawyer: any,
  caseId?: string
): InterestedLawyerType => {
  // Extract user data from nested user object
  const user = lawyer.user || {};

  return {
    id: lawyer.id,
    first_name: user.first_name || lawyer.first_name || "",
    last_name: user.last_name || lawyer.last_name || "",
    expert_types:lawyer.expert_types || [],
    accredited_specialisms:lawyer.accredited_specialisms || [],
    about: lawyer.about || null,
    city: lawyer.city || null,
    county: lawyer.county || null,
    experience_years: lawyer.experience_years || 0,
    hours_to_interested: lawyer.hours_to_interested || "Unknown",
    photo_url: lawyer.photo_url || null,
    photo_urls: lawyer.photo_urls || null,
    case_id: caseId || lawyer.case_id,
  };
};

const InterestedLawyersPopUp: React.FC<InterestedLawyersModalProps> = ({
  isOpen = true,
  onClose,
  onSend,
  interestedLawyers = [],
  caseId,
}) => {
  // Map the interested lawyers to details format
  let lawyers =
    Array.isArray(interestedLawyers) && interestedLawyers.length > 0
      ? interestedLawyers.map((lawyer) =>
          mapInterestedLawyerToDetails(lawyer, caseId)
        )
      : [];

  // Maximum number of lawyers that can be selected
  const MAX_SELECTION = 3;
  
  // Keep selected lawyer IDs in an array state variable
  const [selectedLawyerIds, setSelectedLawyerIds] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);
  const selectAllCheckboxRef = useRef<HTMLInputElement>(null);

  const selectedCount = selectedLawyerIds.length;
  const isMaxReached = selectedCount >= MAX_SELECTION;

  const toggle = (id: string) => {
    setSelectedLawyerIds((prev) => {
      const exists = prev.includes(id);

      if (exists) {
        // Always allow deselection
        return prev.filter((lawyerId) => lawyerId !== id);
      } else {
        // Prevent selecting more than MAX_SELECTION
        if (prev.length >= MAX_SELECTION) {
          return prev;
        }
        return [...prev, id];
      }
    });
  };

  const allLawyerIds = lawyers.map((l) => l.id);
  const allSelected =
    lawyers.length > 0 &&
    allLawyerIds.every((id) => selectedLawyerIds.includes(id));
  const someSelected = selectedCount > 0;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedLawyerIds([]);
    } else {
      setSelectedLawyerIds(allLawyerIds.slice(0, MAX_SELECTION));
    }
  };

  useEffect(() => {
    const el = selectAllCheckboxRef.current;
    if (!el) return;
    el.indeterminate = someSelected && !allSelected;
  }, [someSelected, allSelected]);

  const handleSend = async () => {
    if (selectedLawyerIds.length === 0) return;

    setIsSending(true);
    try {
      // Use the case_id from props
      if (!caseId) {
        toastManager.addToast(
          createErrorToast(
            "Missing Case ID",
            "No case ID provided. Cannot send lawyers to customer."
          )
        );
        return;
      }

      // Prepare the payload for the API
      const payload = {
        case_id: caseId,
        lawyers: selectedLawyerIds,
      };

      // Call the API
      const response = (await api.post(
        "/v1/timeline/send-lawyer-to-customer",
        payload
      )) as ApiResponse;

      // Helper to show toasts with delay (copied from ReviewProfilesModal)
      const showToastsWithDelay = async (
        messages: any[],
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
            } else {
              const toast = createErrorToast("Error", messageItem.message);
              toastManager.addToast(toast);
            }
          } else {
            const toast = createErrorToast("Error", messageItem.message);
            toastManager.addToast(toast);
          }
        }
      };

      if (response.success) {
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          const toast = createSuccessToast(
            "Success",
            response.message || "Experts sent to customer"
          );
          toastManager.addToast(toast);
        }
      } else {
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Error",
            response.message || "Failed to send experts to customer"
          );
          toastManager.addToast(toast);
        }
      }

      // Call the onSend callback with the selected lawyers (for backward compatibility)
      if (onSend) {
        const selectedLawyers = lawyers.filter((lawyer) =>
          selectedLawyerIds.includes(lawyer.id)
        );
        onSend(selectedLawyers);
      }
    } catch (error: any) {
      let errorMessage =
        "Failed to send lawyers to customer. Please try again.";

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
    } finally {
      setIsSending(false);
    }
  };

  return (
    <GlobalModalWrapper isOpen={isOpen} onClose={onClose}>
      <div className="relative z-10 bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[85vh] flex flex-col py-4 px-6">
        {/* Header */}
        <div className="flex flex-col space-y-1.5 text-center sm:text-left">
          <h2 className="text-lg font-semibold flex pr-10 items-center gap-2">
            <i className="fas fa-gavel pb-8 md:pb-0 text-novaRed text-lg" />
            Interested Experts - Review &amp; Send to Customer
          </h2>
        </div>

        {/* Actions */}
        {lawyers.length > 0 && (
        <div className="flex items-center justify-between mb-4 mt-2 pb-3 border-b border-novaActive">
          {(lawyers.length >= 2 && lawyers.length <= MAX_SELECTION) ? (
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                ref={selectAllCheckboxRef}
                type="checkbox"
                checked={allSelected}
                onChange={handleSelectAll}
                className="h-4 w-4 rounded-sm border-2 border-novaDarkOrange accent-[var(--nova-red)] cursor-pointer"
                aria-label="Select all experts"
              />
              <span className="text-sm text-novaTextGray">
                Select all
              </span>
              <span className="text-sm text-novaTextGray">
                ({selectedCount}/{lawyers.length})
              </span>
            </label>
          ) : (
            <span />
          )}

          <FormButton
            variant="gradient"
            disabled={selectedCount === 0 || isSending}
            onClick={handleSend}
            className={`
              inline-flex items-center justify-center gap-2 whitespace-nowrap ring-offset-background transition-colors
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
              disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0
              h-10 text-sm px-4 py-2 bg-novaDarkOrange hover:bg-novaDarkOrange/80 text-white
              relative
            `}
            style={
              selectedCount === 0
                ? {
                    position: "relative",
                    overflow: "hidden",
                  }
                : undefined
            }
          >
            {isSending ? (
              <>
                <i className="fas fa-spinner fa-spin mr-1" />
                Sending...
              </>
            ) : (
              <>
                <i className="fas fa-paper-plane mr-1" />
                Send to Customer
              </>
            )}
            {selectedCount === 0 && (
              <span
                className="absolute inset-0 bg-white/40 pointer-events-none"
                aria-hidden="true"
              />
              )}
            </FormButton>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {lawyers.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {lawyers.map((lawyer) => {
                const isSelected = selectedLawyerIds.includes(lawyer.id);
                // Disable unselected lawyers when max is reached
                const isDisabled = !isSelected && isMaxReached;
                return (
                  <InterestedLawyerDetailsCard
                    key={lawyer.id}
                    lawyer={lawyer}
                    isSelected={isSelected}
                    onSelect={toggle}
                    isDisabled={isDisabled}
                  />
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-4">
              <div className="w-16 h-16 bg-novaNeutral-100 rounded-full flex items-center justify-center mb-4">
                <i className="fas fa-gavel text-novaNeutral-400 text-2xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-novaNeutral-900 mb-2">
                No Interested Experts
              </h3>
              <p className="text-sm text-novaNeutral-600 text-center max-w-md">
                There are currently no experts who have expressed interest in this case. 
                Experts will appear here once they show interest in taking on your case.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-3 border-t-2 border-novaGray-200 text-xs text-novaTextGray flex flex-col gap-1">
          <div>
            <i className="fas fa-info-circle text-novaTextGray pr-2"></i>
            <span>
              Selected profiles will be sent to customer for final expert
              selection
            </span>
          </div>
          <div>
            <i className="fas fa-exclamation-triangle text-novaCaution-500 pr-2"></i>
            <span>
              Maximum {MAX_SELECTION} experts can be selected at a time
            </span>
          </div>
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-novaGray-500 text-xl hover:text-novaGray-700"
        >
          ✕
        </button>
      </div>
    </GlobalModalWrapper>
  );
};

export default InterestedLawyersPopUp;
