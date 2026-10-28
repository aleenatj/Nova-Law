import React from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { MoreDetailsRequestedResponsePropsType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface MoreDetailsRequestedV1Props {
  timelineData: MoreDetailsRequestedResponsePropsType;
  isLatest?: boolean;
}

export function MoreDetailsRequestedV1({
  timelineData,
  isLatest,
}: MoreDetailsRequestedV1Props) {
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : timelineData.action_user_role || DEFAULT_ACTION_BY;
  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-question-circle text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Expert requested more details
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          <strong className="text-[#1A1425]">{timelineData.meta_data.lawyer_name}</strong> has requested
          additional information for case{" "}
          <strong className="text-[#1A1425]">{timelineData.meta_data.case_number}</strong>. They need
          more details about the case before making a decision on
          representation.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-clipboard-list text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">Expert's Request:</span>
          </div>
          <p className="text-sm text-novaNeutral-700 italic">
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
              <span className="text-novaNeutral-800">•</span>
              <span>Review the case details and provide additional information</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>Contact the client if more information is needed</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>Notify the expert with the additional information</span>
            </li>
          </ul>
        </div>
        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timelineData.meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
}

export default MoreDetailsRequestedV1;
