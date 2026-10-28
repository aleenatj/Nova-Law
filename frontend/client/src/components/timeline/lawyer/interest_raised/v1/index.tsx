import React from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { InterestRaisedTimelineProps } from "@/lib/types";
import { useRole } from "@/contexts/RoleContext";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const InterestRaised: React.FC<InterestRaisedTimelineProps & { isLatest?: boolean }> = ({
  timelineData,
  isLatest,
}) => {
  // Extract data from timeline structure with safety checks
  const { meta_data } = timelineData;
  const userRole = useRole();
  if (!meta_data) {
    console.error("InterestRaised: meta_data is missing");
    return (
      <div className="timeline-card-border bg-novaAlert-50 border-novaAlert-200 p-6">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-start sm:items-center gap-2 flex-wrap">
              <i className="fa-solid fa-circle-exclamation text-novaAlert-600 text-sm"></i>
              <span className="text-sm font-medium text-novaNeutral-900">
                Error: Missing interest data
              </span>
            </div>
            <div className="h-px bg-novaAlert-200 my-2"></div>
            <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
              We could not load the interest details for this event. Please try
              refreshing the timeline.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const caseNumber = meta_data.case_number || "Unknown Case";
  const timestamp = meta_data.timestamp || "Unknown Time";
  const resolvedActionBy =
    timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;
  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-hand text-xl"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            {/* Interest sent successfully */}
            Interest registered
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />

        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          {/* You have successfully expressed interest in representing case{" "}
          <strong className="text-[#1A1425]">{caseNumber}</strong>. Nova Navigator has been notified and
          will review your profile against other interested attorneys. You
          will be contacted if selected as the client's preferred
          representation. */}
          You’ve registered interest in case{" "} <strong className="text-[#1A1425]">{caseNumber}</strong>.
        </p>
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          Your profile will now be reviewed by the Nova Navigator team alongside other interested Nova Experts. If chosen by the client, you’ll be notified within 1–2 working days.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              {/* Next Steps: */}
              What happens next:
            </span>
          </div>

          <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              {/* <span>Nova Navigator will review your profile and experience</span> */}
              <span>The Nova Navigator team reviews interested Nova Experts</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              {/* <span>Client will be notified of your interest</span> */}
              <span>Shortlisted Nova Experts are shared with the client</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              {/* <span>You'll be contacted within 24-48 hours if selected</span> */}
              <span>Selection is confirmed by the client</span>
            </li>
            <li className="flex items-start gap-6">
              <span className="text-novaNeutral-800">•</span>
              {/* <span>Case details will be shared upon selection</span> */}
              <span>The chosen Nova Expert receives full case access</span>
            </li>
          </ul>
        </div>

        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {resolvedActionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default InterestRaised;
