import React, { useState } from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { MoreDetailsRequestedResponsePropsType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  createErrorToast,
  createSuccessToast,
  toastManager,
} from "@/utils/toasts";
import { api } from "@/lib/api";
import { CaseDeclinePopup } from "../../case_decline_popup";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface MoreDetailsRequestedV1Props {
  timelineData: MoreDetailsRequestedResponsePropsType;
  isLatest?: boolean;
}

export function MoreDetailsRequestedV1({
  timelineData,
  isLatest,
}: MoreDetailsRequestedV1Props) {
  const { action_buttons } = timelineData.meta_data;
  const [isInterestSubmitting, setIsInterestSubmitting] = useState(false);
  const [isDeclineModalOpen, setIsDeclineModalOpen] = useState(false);
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const lawyerId = user.lawyer_id || (localStorage.getItem('navigator_switched_lawyer_id') || null);
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;
  const showToastsWithDelay = async (
    messages: { message: string; success?: boolean }[],
    isSuccess: boolean
  ) => {
    const delay = 400; // ms
    for (let i = 0; i < messages.length; i++) {
      const messageItem = messages[i];
      await new Promise((resolve) => setTimeout(resolve, i === 0 ? 0 : delay));
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

  const handleInterestClick = async () => {
    if (!lawyerId) {
      toastManager.addToast(
        createErrorToast(
          "Authentication Error",
          "Please log in to express interest in this case."
        )
      );
      return;
    }

    setIsInterestSubmitting(true);

    try {
      const response: any = await api.post("/v1/case/interest", {
        case_id: timelineData.case_id,
        lawyer_id: lawyerId,
      });

      if (response.success) {
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Interest Expressed",
            response.message ||
              "Your interest in this case has been successfully submitted."
          );
          toastManager.addToast(toast);
        }
      } else {
        // Handle error case
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Request Failed",
            response.message || "Failed to express interest. Please try again."
          );
          toastManager.addToast(toast);
        }
      }
    } catch (error: any) {
      let errorMessage = "Failed to express interest. Please try again.";
      // Extract error message from API response if available
      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }

      // toastManager.addToast(createErrorToast("Request Failed", errorMessage));
    } finally {
      setIsInterestSubmitting(false);
    }
  };

  const handleDeclineClick = () => {
    setIsDeclineModalOpen(true);
  };

  const handleDeclineModalClose = () => {
    setIsDeclineModalOpen(false);
  };

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-question-circle text-xl"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            More details requested
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          You have requested additional information for case{" "}
          <strong className="text-[#1A1425]">{timelineData.meta_data.case_number}</strong>. Nova
          Navigator will review your request and provide more detailed case
          information to help you make an informed decision.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-clipboard-list text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">Your Request:</span>
          </div>
          <p className="text-sm leading-5 text-novaNeutral-700 italic">
            "{timelineData.meta_data.lawyer_request}"
          </p>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">Next Steps:</span>
          </div>
          <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800 ">•</span>
              <span>Nova Navigator will gather additional case details</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>You'll receive an updated case summary within 24 hours</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>You can then decide to raise interest or decline</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>Case remains available for other Experts in the meantime</span>
            </li>
          </ul>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-lightbulb text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              Ready to Proceed or Decline?
            </span>
          </div>
          <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            If you're ready to move forward with this case, you can express
            your interest now. Alternatively, if you do not wish to proceed,
            you can decline the case below.
          </p>
              {action_buttons?.raise_interest && (
                <FormButton
                  variant="success"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm mr-2 min-h-[38px]"
                  disabled={isInterestSubmitting}
                  onClick={handleInterestClick}
                >
                  {isInterestSubmitting ? (
                    <>
                      <i className="fas fa-spinner fa-spin text-xs sm:text-sm"></i>
                      <span className="">Submitting...</span>
                    </>
                  ) : (
                    <>
                      <i className="fas fa-hand-paper text-xs sm:text-sm"></i>
                      <span className="">Accept</span>
                    </>
                  )}
                </FormButton>
              )}
              {action_buttons?.decline_match && (
                <FormButton
                  variant="outline"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm "
                  onClick={handleDeclineClick}
                >
                  <i className="fas fa-times text-xs sm:text-sm"></i>
                  <span className="">Decline</span>
                </FormButton>
              )}
        </div>

        <p className="text-xs flex items-center mt-4">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timelineData.meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>

      {/* Decline Case Modal */}
      <CaseDeclinePopup
        isOpen={isDeclineModalOpen}
        onClose={handleDeclineModalClose}
        caseId={timelineData.case_id}
      />
    </div>
  );
}

export default MoreDetailsRequestedV1;
