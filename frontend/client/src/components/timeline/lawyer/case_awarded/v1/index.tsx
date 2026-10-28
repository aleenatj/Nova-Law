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
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fa-solid fa-trophy text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            {/* Case awarded to you */}
            Case awarded to you
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          {/* <strong className="text-[#1A1425]">{meta_data.customer_name}</strong> has selected you to 
          represent their case. */}
          <strong className="text-[#1A1425]">{meta_data.customer_name}</strong> has chosen you as their Nova Expert for this case.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fa-solid fa-handshake text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              {/* What This Means for You */}
              Next steps:
            </span>
          </div>
          {/* [
              "You are now the primary attorney for this case",
              "Customer will complete the onboarding assessment",
              "Payment processing will begin shortly",
              "Direct communication will be established",
            ]           */}
          <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
            {[
              "You are now the chosen Nova Expert for this case",
              "The client pays an initial deposit to secure their Strategic Advice Consultation with you",
              "The client completes Nova Engage and their information is shared with you",
              "The FLP operations team arrange the date and time of the Strategic Advice Consultation",
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
            <div className="font-medium text-novaNeutral-900">
              {meta_data.case_number}
            </div>
          </div>
          <div className="bg-white sm:p-6 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <i className="fas fa-tag text-novaNeutral-700 text-sm"></i>
              <span className="text-sm text-novaNeutral-500">Category</span>
            </div>
            <div className="font-medium text-novaNeutral-900">
              {meta_data.case_type}
            </div>
          </div>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-start gap-2">
            <i className="fa-solid fa-circle-info text-novaNeutral-700 text-sm mt-0.5"></i>
            <div className="text-sm leading-5 text-novaNeutral-700">
              <span className="font-semibold">Congratulations!</span> You
              have been selected to represent this client. The customer will
              complete their payment before case work begins.
            </div>
          </div>
        </div>

        <p className="text-xs flex items-center">
          <i className="fa-solid fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default CaseAwarded;
