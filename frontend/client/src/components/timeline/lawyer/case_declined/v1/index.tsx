import React, { useState } from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { CaseDeclinedResponsePropsType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { createErrorToast, createSuccessToast, toastManager } from "@/utils/toasts";
import { api } from "@/lib/api";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface CaseDeclinedV1Props {
  timelineData: CaseDeclinedResponsePropsType;
  isLatest?: boolean;
}

export function CaseDeclinedV1({ timelineData, isLatest }: CaseDeclinedV1Props) {
  const { action_buttons } = timelineData.meta_data;
  const [isInterestSubmitting, setIsInterestSubmitting] = useState(false);
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const lawyerId = user.lawyer_id || (localStorage.getItem('navigator_switched_lawyer_id') || null);
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
    timelineData.action_user_name ||
    timelineData.action_user_role ||
    DEFAULT_ACTION_BY;

  // Show all messages as toasts, one after another, with a slight delay
  const showToastsWithDelay = async (messages: any[], isSuccess: boolean) => {
    const delay = 400; // ms
    for (let i = 0; i < messages.length; i++) {
      const messageItem = messages[i];
      await new Promise((resolve) => setTimeout(resolve, i === 0 ? 0 : delay));

      // Handle different message formats
      let messageText = "";
      let isMessageSuccess = isSuccess;

      if (typeof messageItem === "string") {
        messageText = messageItem;
      } else if (typeof messageItem === "object" && messageItem !== null) {
        messageText =
          messageItem.message ||
          messageItem.text ||
          JSON.stringify(messageItem);
        isMessageSuccess = messageItem.success !== false && isSuccess;
      } else {
        messageText = String(messageItem);
      }

      if (isMessageSuccess) {
        const toast = createSuccessToast("Success", messageText);
        toastManager.addToast(toast);
      } else {
        // const toast = createErrorToast("Error", messageText);
        // toastManager.addToast(toast);
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
      const response = (await api.post("/v1/case/interest", {
        case_id: timelineData.case_id,
        lawyer_id: lawyerId,
      })) as any;

      if (Array.isArray(response.message)) {
        await showToastsWithDelay(response.message, response.success === true);
      } else {
        // fallback if message array missing, try message string
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

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-times text-2xl"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Case declined successfully
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          You have successfully declined to represent case{" "}
          <strong className="text-[#1A1425]">{timelineData.meta_data.case_number}</strong>. Nova
          Navigator has been notified and will continue searching for other
          qualified attorneys for this case.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-list text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              Selected Reasons:
            </span>
          </div>
          <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
            {timelineData.meta_data.reasons?.map(
              (reason: string, index: number) => (
                <li key={index} className="flex items-start gap-6">
                  <span className="text-novaNeutral-800">•</span>
                  <span>{reason}</span>
                </li>
              )
            )}
          </ul>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-comment text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              Additional Comments:
            </span>
          </div>
          <p className="text-sm leading-5 text-novaNeutral-700 italic">
            "{timelineData.meta_data.reason_other || "No additional comments"}"
          </p>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-lightbulb text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              Change of Mind?
            </span>
          </div>
          <p className="text-sm leading-6 text-novaNeutral-700 mb-4">
            You can still raise interest on the case if you've reconsidered
            your decision.
          </p>
              {action_buttons?.raise_interest && (
                <FormButton
                  variant="success"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 h-10 px-2 sm:px-3 lg:px-2 xl:px-4 py-2 text-white disabled:bg-novaNeutral-400 disabled:hover:bg-novaNeutral-400"
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
        </div>

        <p className="text-xs flex items-center mt-4">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timelineData.meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
}

export default CaseDeclinedV1;
