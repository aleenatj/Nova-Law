import React, { useState } from "react";
import { CompleteOnboardingAssessmentTimelineProps } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { FormButton } from "@/utils/formComponents";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { api } from "@/lib/api";
import { toastManager, createErrorToast } from "@/utils/toasts";
import userplusIcon from "@/assets/ui/UserPlus.svg";
import { useLocation } from "wouter";

const CompleteOnboardingAssessmentCard: React.FC<
  CompleteOnboardingAssessmentTimelineProps & { isLatest?: boolean }
> = ({ timelineData, isLatest }) => {
  const { meta_data } = timelineData;
  const [isLoading, setIsLoading] = useState(false);
  const [, setLocation] = useLocation();

  if (!meta_data) {
    console.error("CompleteOnboardingAssessment: meta_data is missing");
    return (
      <div className="bg-[#FAF7EE] sm:p-6 p-4 rounded-lg">
        <p className="text-novaCaution-600 text-sm">Error: Missing onboarding data</p>
      </div>
    );
  }

  // Check if start_onboarding_assessment action button is enabled
  const canStartAssessment =
    meta_data &&
    meta_data.action_buttons &&
    typeof meta_data.action_buttons.mark_onboarding_completed === "boolean"
      ? meta_data.action_buttons.mark_onboarding_completed
      : false;

  const lawyerName = meta_data.lawyer_name || "your lawyer";
  const actionBy = 
    timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;

  const handleStartAssessment = async () => {
    if (!canStartAssessment || isLoading) return;

    setIsLoading(true);
    try {
      const response = await api.get<{
        data?: { engage_url?: string; enable_engage_auth_url?: boolean };
      }>(`/v1/auth/get-engage-link?case_id=${timelineData.case_id}`);
      const engageUrl = response.data?.engage_url;
      const enableEngageAuthUrl = response.data?.enable_engage_auth_url;
      if (engageUrl) {
        if (enableEngageAuthUrl === false) {
          window.location.href = engageUrl;
        } else {
          window.open(engageUrl, "_blank");
        }
      }
    }
    finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        {/* Header */}
        <div className="flex gap-2">
          <img src={userplusIcon} alt="userplus" className="w-8 h-6 mr-1 mt-1 sm:mt-0" />
          <span className="sm:text-[28px] text-xl font-semibold text-[#1A1425]">
            {isLatest === true ? 'Next step: Complete your consultation preparation with Nova Engage' : 'Complete your consultation preparation with Nova Engage'}
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />

        {/* Description Paragraphs */}
        <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[70%]">
          To help you get the most from your Strategic Advice Consultation with{" "}
          <strong className="text-[#1A1425] break-words">{lawyerName}</strong>, you are invited to complete Nova Engage – our AI-powered dynamic briefing experience.
        </p>

        <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[70%]">
          Nova Engage helps you organise the key information about your situation in advance, so your consultation can focus on what matters most to you, not simply gathering background information.
        </p>

        <div className="text-md leading-6 text-novaNeutral-700 mb-6 w-full bg-white rounded-lg p-4 border border-novaDarkAmber">
          <p className="text-md leading-6 text-novaNeutral-500 mb-4 font-medium w-full lg:w-[70%]">It’s designed to:</p>
          <ul className="text-sm leading-5 text-novaNeutral-700 space-y-1 ml-4 list-disc">
            <li><span>Clarify the important facts and priorities </span></li>
            <li><span>Surface the questions you really need answered</span></li>
            <li><span>Help your Nova Expert prepare properly ahead of the session</span></li>
          </ul>
        </div>
        <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[75%]">
          Nova Engage is included at no cost to you and typically takes around 45-60 minutes to complete. You can take your time, save your progress, and return whenever you need.<br />
          <br />Nova Engage is a detailed deep dive experience. For the best results, we recommend using a desktop or laptop.
        </p>

        {/* Button */}
        {canStartAssessment && (
          <div className="flex gap-2 items-center mb-4">
            <FormButton
              variant="primary"
              className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm px-4 py-2"
              type="button"
              // onClick={() => {
              //   sessionStorage.setItem("current_case_id", timelineData.case_id);
              //   const q = encodeURIComponent(timelineData.case_id);
              //   setLocation(`/engage/${q}`);
              // }}
              onClick={handleStartAssessment}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <i className="fas fa-spinner fa-spin text-xs"></i>
                  Loading...
                </>
              ) : (
                <>
                  <i className="fas fa-play text-xs"></i>
                  Get started now
                </>
              )}
            </FormButton>
          </div>
        )}

        {/* Timestamp */}
        <div className="text-xs flex items-center gap-1">
          <i className="fas fa-clock text-xs"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {DEFAULT_ACTION_BY}</span>
        </div>
      </div>
    </div>
  );
};

export default CompleteOnboardingAssessmentCard;
