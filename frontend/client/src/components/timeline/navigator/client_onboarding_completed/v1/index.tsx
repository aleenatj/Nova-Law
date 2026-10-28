import React from "react";
import { NavigatorClientOnboardingCompletedTimelineProps } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const NavigatorClientOnboardingCompleted: React.FC<
  NavigatorClientOnboardingCompletedTimelineProps & { isLatest?: boolean }
> = ({ timelineData, isLatest }) => {
  const { meta_data } = timelineData;
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : timelineData.action_user_role || DEFAULT_ACTION_BY;

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-user-check text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Client onboarding completed
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          <strong className="text-[#1A1425]">{meta_data.customer_name}</strong> has successfully
          completed the onboarding process with{" "}
          <strong className="text-[#1A1425]">{meta_data.lawyer_name}</strong>. The client has provided
          all necessary information and is ready to proceed with the case.
        </p>
        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-clipboard-check text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              Onboarding Details:
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm leading-5 text-novaNeutral-700">
            <div>
              <span className="text-novaNeutral-500">Client:</span>
              <div className="font-medium text-novaNeutral-900">{meta_data.customer_name}</div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Assigned Expert:</span>
              <div className="font-medium text-novaNeutral-900">{meta_data.lawyer_name}</div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Case Type:</span>
              <div className="font-medium text-novaNeutral-900">{meta_data.case_type}</div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Status:</span>
              <div className="font-medium pt-1">
                <span className="px-2 py-1 rounded-full text-xs font-normal bg-novaDarkOrange text-white">
                  {meta_data.status}
                </span>
              </div>
            </div>
          </div>
        </div>
        <p className="text-xs text-novaNeutral-500 flex items-center">
          <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default NavigatorClientOnboardingCompleted;
