import React from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { CustomerTalkToNavigatorTimelineProps } from "@/lib/types";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const CustomerTalkToNavigator: React.FC<CustomerTalkToNavigatorTimelineProps & { isLatest?: boolean }> = ({ timelineData, isLatest }) => {
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
          <i className="fas fa-user-tie text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Customer Requested Nova Navigator Session
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          {meta_data.action_by || 'The customer'} has requested to talk to Nova Navigator for guidance on case-<strong className="text-[#1A1425]">{meta_data.case_number || 'Case'}</strong>. They need assistance with their case.
        </p>
        
        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">Action Required:</span>
          </div>
          <ul className="space-y-2 text-sm text-novaNeutral-700">
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-400">•</span>
              <span>Review the customer's case details</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-400">•</span>
              <span>Prepare guidance materials</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-400">•</span>
              <span>Proceed with the guidance session</span>
            </li>
          </ul>
        </div>
        
        {meta_data.customer_phone && (
          <div className="inline-flex items-center gap-2 mb-4 px-3 py-2 rounded-full bg-novaDarkOrange text-white text-sm w-fit">
            <i className="fa-solid fa-mobile-screen-button text-white"></i>
            <span>{meta_data.customer_phone}</span>
          </div>
        )}
        
        <p className="text-xs text-novaNeutral-500 flex items-center">
          <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default CustomerTalkToNavigator;
