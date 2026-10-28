import React from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { CustomerTalkToLawyerTimelineProps } from "@/lib/types";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const CustomerTalkToLawyer: React.FC<CustomerTalkToLawyerTimelineProps & { isLatest?: boolean }> = ({ timelineData, isLatest }) => {
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
            Customer requested talk to Expert
          </span>
        </div>

        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          {meta_data.action_by || 'A customer'} has requested a 15-minute conversation with <strong className="text-[#1A1425]">{meta_data.lawyer_name || 'Expert'}</strong> regarding case <strong className="text-[#1A1425]">{meta_data.case_number || 'Case'}</strong>. The Expert has not been informed, please review and proceed.
        </p>
        {meta_data.customer_phone && (
          <div className="inline-flex items-center mb-4 px-3 py-4 rounded-md border-l-4 border-[#f6cf9B] bg-white text-novaNeutral-700 text-sm w-full">
            <div className="flex items-center gap-2 w-fit bg-[#fff1df] rounded-full px-3 py-2">
            <i className="fa-solid fa-mobile-screen-button text-novaNeutral-700"></i>
            <span>{meta_data.customer_phone}</span>
            <button
              type="button"
              className=" p-1 rounded"
              title="Copy phone"
              aria-label="Copy phone"
              onClick={() => {
                if (navigator?.clipboard) {
                  navigator.clipboard.writeText(meta_data.customer_phone);
                } else {
                  // fallback for older browsers
                  const tempInput = document.createElement('input');
                  tempInput.value = meta_data.customer_phone;
                  document.body.appendChild(tempInput);
                  tempInput.select();
                  document.execCommand('copy');
                  document.body.removeChild(tempInput);
                }
              }}
            >
              <i className="fa-regular fa-copy text-novaNeutral-700 hover:text-novaDarkOrange"></i>
            </button>
            </div>
          </div>
        )}
        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default CustomerTalkToLawyer;
