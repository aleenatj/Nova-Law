import React from "react";
import { TimelineItemType } from "../../../../../lib/types";
import { formatTimestamp } from "../../../../../utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import puzzlematch from "@/assets/ui/PuzzleMatch.svg";

// Metadata structure for Customer KYC Submitted
interface CustomerKycSubmittedMetaData {
  first_name: string;
  timestamp: string;
}

interface CustomerKycSubmittedProps {
  timelineData?: TimelineItemType & { meta_data?: CustomerKycSubmittedMetaData };
  isLatest?: boolean;
}

const CustomerKycSubmitted: React.FC<CustomerKycSubmittedProps> = ({
  timelineData,
  isLatest,
}) => {
  // Get data from timeline metadata
  const metaData = timelineData?.meta_data;
  const customerName = metaData?.first_name || "there";
  const actionBy = timelineData?.action_user_role?.toLowerCase() === "navigator"
  ? "Nova Navigator"
  : metaData?.action_by || timelineData?.action_user_name || DEFAULT_ACTION_BY;

  // Check if timelineData exists
  if (!timelineData?.meta_data) {
    return (
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-start sm:items-center gap-2 flex-wrap">
              <i className="fas fa-exclamation-triangle text-novaCaution-600 text-sm"></i>
              <span className="text-sm font-medium text-novaNeutral-900">
                No data available
              </span>
            </div>
            <div className="h-px bg-novaCaution-200 my-2"></div>
            <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
              Unable to load Alignment Check submission information at this time.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        {/* Header */}
        <div className="flex gap-2">
          <img src={puzzlematch} alt="" className="w-8 h-8 mr-2" />
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            {isLatest === true ? 'Next step: Matching with Nova Experts' : 'Matching with Nova Experts'}
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />

        {/* Description */}
        <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full">
          Thanks for telling us more about your circumstances {customerName}. Our
          specialist team of Nova Navigators is currently reviewing your responses to identify
          the Nova Experts best suited to progress your case.
        </p>

        {/* Next steps card */}
        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              Next steps:
            </span>
          </div>
          <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>
                You’ll receive an email with your personalised selection of expert profiles to
                review – please look out for a notification in your inbox
              </span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              <span>
                You can then decide if you wish to move forward with one of them
                and book an initial consultation when you feel ready
              </span>
            </li>
          </ul>
        </div>

        {/* Timestamp */}
        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>Submitted on {formatTimestamp(metaData?.timestamp || "")}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {DEFAULT_ACTION_BY}</span>
        </p>
      </div>
    </div>
  );
};

export default CustomerKycSubmitted;
