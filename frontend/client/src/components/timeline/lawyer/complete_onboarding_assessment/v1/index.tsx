import React, { useState } from "react";
import { LawyerCompleteOnboardingAssessmentTimelineProps } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { api } from "@/lib/api";
import { toastManager, createSuccessToast, createErrorToast } from "@/utils/toasts";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const LawyerCompleteOnboardingAssessment: React.FC<
  LawyerCompleteOnboardingAssessmentTimelineProps & { isLatest?: boolean }
> = ({ timelineData, isLatest }) => {
  const { meta_data } = timelineData;
  const [isSubmitting, setIsSubmitting] = useState(false);
  const actionBy =
    meta_data?.action_by ||
    timelineData.action_user_name ||
    timelineData.action_user_role ||
    DEFAULT_ACTION_BY;
  const showToastsWithDelay = async (
    messages: Array<{ message: string; success?: boolean }>,
    isSuccess: boolean
  ) => {
    const delay = 400; // ms
    for (let i = 0; i < messages.length; i++) {
      const messageItem = messages[i];
      await new Promise((resolve) => setTimeout(resolve, i === 0 ? 0 : delay));

      if (messageItem.success === true) {
        const toast = createSuccessToast("Success", messageItem.message);
        toastManager.addToast(toast);
      } else if (messageItem.success === false) {
        const toast = createErrorToast("Error", messageItem.message);
        toastManager.addToast(toast);
      } else {
        // fallback: use isSuccess if property missing
        if (isSuccess) {
          const toast = createSuccessToast("Success", messageItem.message);
          toastManager.addToast(toast);
        } else {
          const toast = createErrorToast("Error", messageItem.message);
          toastManager.addToast(toast);
        }
      }
    }
  };

  const handleMarkCompleted = async () => {
    setIsSubmitting(true);
    try {
      const response: any = await api.post("/v1/timeline/mark-onboarding-completed", {
        case_id: timelineData?.case_id,
        lawyer_id: localStorage.getItem('navigator_switched_lawyer_id') || (window as any).user?.lawyer_id,
      });

      // Handle array of messages
      if (response?.message && Array.isArray(response.message)) {
        await showToastsWithDelay(response.message, response.success || true);
      } else if (response?.message) {
        // Fallback for single message (backward compatibility)
        const toast = createSuccessToast(
          "Success",
          response.message || "Client onboarding has been marked as completed"
        );
        toastManager.addToast(toast);
      }
    } catch (error) {
      // console.error("Error marking onboarding completed:", error);
      // const toast = createErrorToast(
      //   "Error",
      //   "Failed to mark onboarding as completed"
      // );
      // toastManager.addToast(toast);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-user-edit text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Complete client onboarding assessment
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />

        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          Please review and mark as completed the client onboarding assessment{meta_data?.customer_name ? <> for customer <strong className="text-[#1A1425]">{meta_data.customer_name}</strong></> : ''} in case{" "}
          <strong className="text-[#1A1425]">{meta_data?.case_number}</strong>.
        </p>

        {meta_data?.action_buttons?.mark_onboarding_completed && (
          <div className="mb-4">
            <FormButton 
              variant="primary"
              onClick={handleMarkCompleted}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors"
            >
              {isSubmitting ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  Processing...
                </>
              ) : (
                <>
                  <i className="fas fa-check-circle"></i>
                  Mark Onboarding Completed
                </>
              )}
            </FormButton>
          </div>
        )}

        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data?.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default LawyerCompleteOnboardingAssessment;
