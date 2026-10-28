import React from "react";
import { TimelineItemType } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface CaseAwardedProps {
  timelineData: TimelineItemType;
  isLatest?: boolean;
}

const CaseAwarded: React.FC<CaseAwardedProps> = ({ timelineData, isLatest }) => {
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
          <i className="fas fa-check-circle text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Case awarded
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          <strong className="text-[#1A1425]">{meta_data.customer_name}</strong> has selected <strong className="text-[#1A1425]">{meta_data.lawyer_name}</strong> to
          represent their case
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fa-solid fa-handshake text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              What This Means for You
            </span>
          </div>
          <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
            {[
              `Case ${meta_data.case_number} has been assigned to ${meta_data.lawyer_name}`,
              "Customer onboarding process initiated",
              "Payment processing will follow onboarding",
              "Case management system updated",
            ].map((item, index) => (
              <li key={index} className="flex items-start gap-6">
                <span className="text-novaNeutral-800">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div className="bg-white sm:p-6 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <i className="fas fa-folder text-novaNeutral-700 text-sm"></i>
              <span className="text-sm text-novaNeutral-500">Case ID</span>
            </div>
            <div className="font-medium text-novaNeutral-900">{meta_data.case_number}</div>
          </div>
          <div className="bg-white sm:p-6 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <i className="fas fa-tag text-novaNeutral-700 text-sm"></i>
              <span className="text-sm text-novaNeutral-500">Category</span>
            </div>
            <div className="font-medium text-novaNeutral-900">{meta_data.case_type}</div>
          </div>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-start gap-2">
            <i className="fa-solid fa-circle-info text-novaNeutral-700 text-sm mt-0.5"></i>
            <span className="text-sm text-novaNeutral-700">
              <span className="font-semibold">Congratulations!</span> The case has been successfully assigned to <strong className="text-[#1A1425]">{meta_data.lawyer_name}</strong>. The customer onboarding and payment process is now in progress.
            </span>
          </div>
        </div>

        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default CaseAwarded;
