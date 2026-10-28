import React from "react";
import {
  MatchNotificationSentTimelineProps,
  NotifiedLawyersType,
} from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

// Function to parse notified_lawyers data and extract lawyer information
const parseNotifiedLawyers = (
  notifiedLawyersData: NotifiedLawyersType[] | string
): NotifiedLawyersType[] => {
  try {
    // If it's already an array, return it
    if (Array.isArray(notifiedLawyersData)) {
      return notifiedLawyersData;
    }

    // If it's a string, try to parse it
    if (typeof notifiedLawyersData === "string") {
      // If it's a JSON string, parse it
      if (
        notifiedLawyersData.startsWith("[") ||
        notifiedLawyersData.startsWith("{")
      ) {
        const parsed = JSON.parse(notifiedLawyersData);
        return Array.isArray(parsed) ? parsed : [];
      }

      // If it's a comma-separated string of names, convert to lawyer objects
      const names = notifiedLawyersData.split(",").map((name) => name.trim());
      return names.map((name, index) => ({
        id: `lawyer-${index + 1}`,
        name: name,
        photo_url: `/api/placeholder/40/40`, // Default placeholder
      }));
    }

    return [];
  } catch (error) {
    console.error("Error parsing notified lawyers:", error);
    return [];
  }
};

// Main component that accepts timeline data
const MatchNotificationSent: React.FC<MatchNotificationSentTimelineProps & { isLatest?: boolean }> = ({
  timelineData,
  isLatest,
}) => {
  // Extract data from timeline structure with safety checks
  const { meta_data } = timelineData;
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData?.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : timelineData?.action_user_role || DEFAULT_ACTION_BY;

  if (!meta_data) {
    console.error("MatchNotificationSent: meta_data is missing");
    return (
      <div className="timeline-card-border bg-red-50 border-red-200 p-6">
        <p className="text-red-500 text-sm">Error: Missing notification data</p>
      </div>
    );
  }

  const lawyers = parseNotifiedLawyers(meta_data.notified_lawyers || []);

  const lawyerCount = lawyers.length;
  const caseId = meta_data.case_number || "Unknown Case";
  const timestamp = meta_data.timestamp || "Unknown Time";
  // const isDelivered = true; // Assuming successful if we have this data
  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-paper-plane text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Case notifications sent
          </span>
        </div>

        <hr className="block border-t border-novaDarkAmber my-3" />

        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          Case notifications have been successfully sent to{" "}
          <strong className="text-[#1A1425]">{lawyerCount}</strong>{" "}
          <strong className="text-[#1A1425]">qualified experts</strong>{" "}
          for case{" "}
          <strong className="text-[#1A1425]">{caseId}</strong>.
          Each expert has received detailed case information and can now
          express their interest.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-users text-novaNeutral-700 text-sm"></i>
            <span className="text-md font-semibold text-novaNeutral-900">
              Notified Experts:
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {lawyers && lawyers.length > 0 ? (
              lawyers.map((lawyer, index) => (
                <div
                  key={index}
                  className= "text-novaNeutral-900 bg-[#fff1df] px-1 py-1 rounded-full text-sm flex items-center gap-2"
                >
                  {lawyer.photo_url ? (
                    <img
                      src={lawyer.photo_url}
                      alt=""
                      className="w-8 h-8 rounded-full object-cover border border-novaDarkOrange"
                    />
                  ) : (
                    <span
                      className="w-8 h-8 flex items-center justify-center rounded-full border border-novaDarkOrange shrink-0"
                      title={lawyer.name || "Lawyer"}
                    >
                      <i className="fa-solid fa-user text-novaDarkOrange text-sm"></i>
                    </span>
                  )}
                  <span title={lawyer.name} className="text-novaNeutral-900 mr-2 line-clamp-1">{lawyer.name}</span>
                </div>
              ))
            ) : (
              <span className="text-sm text-novaNeutral-400 italic">
                No experts notified
              </span>
            )}
          </div>
        </div>

        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default MatchNotificationSent;
