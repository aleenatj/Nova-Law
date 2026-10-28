import React, { useState } from "react";
import { Button } from "..";
import MatchedLawyerDetailsCard from "./MatchedLawyerDetailsCard";
import { MatchConfirmedLawyerType } from "@/lib/types";
import { api } from "@/lib/api";
import {
  createErrorToast,
  createSuccessToast,
  toastManager,
} from "@/utils/toasts";
import { FormButton } from "@/utils";

interface ChooseAnotherLawyerPopUpProps {
  caseId: string;
  isOpen: boolean;
  onClose: () => void;
  lawyers?: MatchConfirmedLawyerType[];
  onEngageLawyer?: (lawyerId: string) => void;
}

interface ApiResponse {
  success: boolean;
  message?: string;
}

const ChooseAnotherLawyerPopUp: React.FC<ChooseAnotherLawyerPopUpProps> = ({
  isOpen,
  caseId,
  onClose,
  lawyers,
  onEngageLawyer,
}) => {
  const [selectedLawyerId, setSelectedLawyerId] = useState<string>(
    lawyers && lawyers.length > 0 ? lawyers[0].lawyer_id : ""
  );

  const handleLawyerSelect = (lawyerId: string) => {
    setSelectedLawyerId(lawyerId);

    // Find and log the selected expert details
    const selectedLawyer = lawyers?.find(
      (lawyer) => lawyer.lawyer_id === lawyerId
    );
  };

  const handleEngageClick = () => {
    if (selectedLawyerId && onEngageLawyer) {
      onEngageLawyer(selectedLawyerId);
    }
  };

  const handleEngageSelectedLawyer = async () => {
    try {
      // Prepare the request body as per API documentation
      const requestBody = {
        case_id: caseId || "",
        lawyer_id: selectedLawyerId,
      };

      const response = (await api.post(
        "/v1/timeline/accept-lawyer",
        requestBody
      )) as ApiResponse;

      // Helper to show toasts with delay (for array of messages)
      const showToastsWithDelay = async (
        messages: { message: string; success?: boolean }[],
        isSuccess: boolean
      ) => {
        const delay = 400; // ms
        for (let i = 0; i < messages.length; i++) {
          const messageItem = messages[i];
          await new Promise((resolve) =>
            setTimeout(resolve, i === 0 ? 0 : delay)
          );
          if (isSuccess) {
            if (messageItem.success !== false) {
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
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Success",
            response.message || "Expert accepted"
          );
          toastManager.addToast(toast);
        }
        // Close modal on success
        onClose();
      } else {
        // Handle error case
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Error",
            response.message || "Failed to accept lawyer"
          );
          toastManager.addToast(toast);
        }
      }
    } catch (error: any) {
      let errorMessage = "Failed to accept lawyer. Please try again.";

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
    }
  };
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-3 pb-0 sm:p-8 sm:pb-8">
          <div className="flex flex-col space-y-1.5 text-center sm:text-left mb-3 sm:mb-8">
            <div className="flex items-center text-xl relative">
              <div className="w-10 h-10 bg-novaBlue-100 rounded-full flex items-center justify-center">
                <i className="fas fa-users text-novaBlue-500 text-lg"></i>
              </div>
              <div className="ml-3">
                <div className="text-xl font-semibold text-left">Engage an Expert</div>
                <div className="text-sm font-semibold text-novaTextGray mt-1 text-left">
                  Choose from your matched Nova Experts
                </div>
              </div>
              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute right-0 top-1/5 -translate-y-1/2 text-novaGray-500 text-xl hover:text-novaGray-700"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <i className="fas fa-user-tie text-novaBlue-500 text-sm"></i>
                <span className="text-sm font-medium ">
                  Select Expert to Engage
                </span>
              </div>

              {/* Lawyers List */}
              <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto">
                {lawyers &&
                  lawyers.length > 0 &&
                  lawyers.map((lawyer) => (
                    <MatchedLawyerDetailsCard
                      key={lawyer.lawyer_id}
                      lawyer={lawyer}
                      isSelected={selectedLawyerId === lawyer.lawyer_id}
                      onClick={handleLawyerSelect}
                    />
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-novaGray-50 px-3 sm:px-8 py-3 sm:py-6 border-t-2 border-novaGray-100">
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 gap-4">
            <FormButton
              variant="custom"
              onClick={onClose}
              className="hidden sm:inline-flex items-center justify-center gap-2 whitespace-nowrap border bg-white hover:bg-novaGray-50 h-10 border-novaPrimary-400 text-novaGray-700 px-4 py-2"
            >
              <i className="fas fa-times"></i>
              Cancel
            </FormButton>
            <FormButton
              variant="custom"
              onClick={handleEngageSelectedLawyer}
              disabled={!selectedLawyerId}
              className="inline-flex items-center justify-center gap-2 whitespace-nowrap h-10 bg-novaBlue-500 hover:bg-novaBlue-700 text-white px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <i className="fas fa-handshake"></i>
              Engage Selected Expert
            </FormButton>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChooseAnotherLawyerPopUp;
