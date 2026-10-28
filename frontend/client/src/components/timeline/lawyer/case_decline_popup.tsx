import React, { useState } from "react";
import { api } from "@/lib/api";
import {toastManager,createErrorToast,createSuccessToast,} from "@/utils/toasts";
import GlobalModalWrapper from "../../modal/GlobalModalWrapper";

interface CaseDeclinePopupProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
}

export function CaseDeclinePopup({isOpen,onClose,caseId,}: CaseDeclinePopupProps) {
  const [selectedReasons, setSelectedReasons] = useState<string[]>([]);
  const [additionalComments, setAdditionalComments] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const lawyerId = user.lawyer_id || (localStorage.getItem('navigator_switched_lawyer_id') || null);

  // Predefined decline reasons
  const declineReasons = [
    "Actual or potential conflict identified",
    "Prospect will struggle to afford likely costs",
    "Level of hostility in case is too high",
    "Prospect's unrealistic expectations too difficult to manage",
    "Anticipated fees too low to be worthwhile",
    "Capacity - I cannot currently accept new clients",
    "I don't cover that area of law",
    "That case sounds too complicated for me",
    "Other reasons",
  ];

  const handleClose = () => {
    if (isSubmitting) return; // Prevent closing during submission
    onClose();
    setSelectedReasons([]);
    setAdditionalComments("");
  };

  const handleReasonToggle = (reason: string) => {
    setSelectedReasons((prev) =>
      prev.includes(reason)
        ? prev.filter((r) => r !== reason)
        : [...prev, reason]
    );
  };

  const handleSubmit = async () => {
    if (selectedReasons.length === 0) {
      toastManager.addToast(
        createErrorToast(
          "Validation Error",
          "Please select at least one reason for declining."
        )
      );
      return;
    }

    if (!lawyerId) {
      toastManager.addToast(
        createErrorToast(
          "Authentication Error",
          "Please log in to decline this case."
        )
      );
      return;
    }

    setIsSubmitting(true);

    // Show all messages as toasts, one after another, with a slight delay
    const showToastsWithDelay = async (
      messages: Array<{ message: string; success?: boolean }>,
      isSuccess: boolean
    ) => {
      const delay = 400; // ms
      for (let i = 0; i < messages.length; i++) {
        const messageItem = messages[i];
        await new Promise((resolve) =>
          setTimeout(resolve, i === 0 ? 0 : delay)
        );

        // Show every message independently (regardless of 'isSuccess')
        if (messageItem.success === true) {
          const toast = createSuccessToast("Success", messageItem.message);
          toastManager.addToast(toast);
        } else if (messageItem.success === false) {
          // const toast = createErrorToast("Error", messageItem.message);
          // toastManager.addToast(toast);
        } else {
          // fallback: use isSuccess to determine type if property missing
          if (isSuccess) {
            const toast = createSuccessToast("Success", messageItem.message);
            toastManager.addToast(toast);
          } else {
            // const toast = createErrorToast("Error", messageItem.message);
            // toastManager.addToast(toast);
          }
        }
      }
    };

    try {
      const response = (await api.post("/v1/case/decline", {
        case_id: caseId,
        lawyer_id: lawyerId,
        decline_reason: {
          reason: selectedReasons,
          reason_other: additionalComments.trim(),
        },
      })) as any;

      // Use response.message (array) for toasts
      if (Array.isArray(response?.message)) {
        await showToastsWithDelay(response.message, response.success === true);
      } else {
        // fallback, single message string
        if (response.success) {
          toastManager.addToast(
            createSuccessToast("Success", response.message || "Success")
          );
        } else {
          // toastManager.addToast(
          //   createErrorToast("Error", response.message || "Request failed")
          // );
        }
      }

      handleClose();
    } catch (error: any) {
      console.error("Error declining case:", error);
      let errorMessage = "Failed to decline case. Please try again.";
      // Extract error message from API response if available
      if (error?.message) {
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // toastManager.addToast(createErrorToast("Request Failed", errorMessage));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <GlobalModalWrapper isOpen={isOpen} onClose={isSubmitting ? () => {} : handleClose}>
      <div
        role="dialog"
        aria-describedby="decline-modal-description"
        aria-labelledby="decline-modal-title"
        className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] rounded-xl border border-gray-200 bg-white p-0 shadow-[0_2px_16px_0_rgba(0,0,0,0.18)]"
        tabIndex={-1}
        style={{ pointerEvents: "auto" }}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={handleClose}
          disabled={isSubmitting}
          className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-30 text-novaNeutral-500 hover:text-novaNeutral-700"
          aria-label="Close"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="lucide lucide-x h-5 w-5"
          >
            <path d="M18 6 6 18"></path>
            <path d="m6 6 12 12"></path>
          </svg>
        </button>

        {/* Header */}
        <div className="px-6 pt-6 pb-2">
          <h2
            id="decline-modal-title"
            className="text-base font-semibold leading-none tracking-tight flex items-center gap-2 mb-1"
          >
            <i className="fas fa-times-circle text-novaCaution-500 text-lg"></i>
            <span>Decline Case</span>
          </h2>
          <p
            id="decline-modal-description"
            className="text-[15px] text-novaNeutral-400"
          >
            Please tell us why the matter was declined. This helps us improve
            our matching process and provides feedback to the client.
          </p>
        </div>

        {/* Content */}
        <div className="px-6 pb-2">
          {/* Reasons Section */}
          <div className="mb-4">
            <label className="block text-[15px] text-novaNeutral-900 mb-2 font-medium">
              Reasons for Declining{" "}
              <span className="text-novaCaution-600">*</span>
            </label>
            <div className="max-h-48 overflow-y-auto border border-novaNeutral-100 rounded-lg p-3 bg-novaNeutral-50">
              {declineReasons.map((reason) => (
                <label
                  key={reason}
                  className="flex items-start gap-2 mb-2 cursor-pointer hover:bg-novaNeutral-100 p-1 rounded"
                >
                  <input
                    type="checkbox"
                    checked={selectedReasons.includes(reason)}
                    onChange={() => handleReasonToggle(reason)}
                    disabled={isSubmitting}
                    className="mt-1 h-4 w-4 border-novaNeutral-300 rounded focus:ring-2"
                  />
                  <span className="text-[14px] text-novaNeutral-500 leading-relaxed">
                    {reason}
                  </span>
                </label>
              ))}
            </div>
            {selectedReasons.length === 0 && (
              <p className="text-xs text-novaNeutral-500 mt-1">
                Please select at least one reason for declining.
              </p>
            )}
          </div>

          {/* Additional Comments Section */}
          <div>
            <label className="block text-[15px] text-novaNeutral-900 mb-2 font-medium">
              Additional Comments (Optional)
            </label>
            <textarea
              placeholder="Please provide any additional details or clarifications..."
              className="w-full px-3 py-2 border border-novaNeutral-300 rounded-lg text-[15px] text-novaNeutral-700 bg-novaNeutral-50 focus:outline-none focus:ring-2 focus:ring-novaCaution-500 focus:border-transparent resize-none"
              rows={4}
              value={additionalComments}
              onChange={(e) => setAdditionalComments(e.target.value)}
              disabled={isSubmitting}
              maxLength={500}
              style={{ minHeight: "90px" }}
            />
            {((additionalComments as string)?.length || 0) >= 500 && (
              <div className="text-xs text-novaCaution-500 mt-1">
                Limit reached
              </div>
            )}
          </div>
        </div>

        {/* Footer Buttons */}
        <div className="flex items-center justify-end gap-2 px-6 pb-6 pt-2">
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="inline-flex items-center justify-center gap-2 rounded-full text-[15px] font-medium border border-novaNeutral-300 bg-white hover:bg-novaBlack hover:text-white hover:border-novaBlack h-10 px-5 py-2 text-novaNeutral-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || selectedReasons.length === 0}
            className={`inline-flex items-center justify-center gap-2 rounded-full text-[15px] font-medium h-10 px-5 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
              isSubmitting || selectedReasons.length === 0
                ? "bg-novaNeutral-200 text-novaNeutral-400 cursor-not-allowed"
                : "bg-novaCaution-500 text-white hover:bg-novaCaution-600"
            }`}
          >
            {isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin mr-1"></i>
                Declining...
              </>
            ) : (
              <>
                <i className="fas fa-times mr-1"></i>
                Decline Case
              </>
            )}
          </button>
        </div>
      </div>
    </GlobalModalWrapper>
  );
}

export default CaseDeclinePopup;
