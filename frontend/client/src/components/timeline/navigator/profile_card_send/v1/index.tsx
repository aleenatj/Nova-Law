import React from "react";
import { LawyerProfile, ProfileCardSendTimelineProps } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const ProfileCardSend: React.FC<ProfileCardSendTimelineProps & { isLatest?: boolean }> = ({
  timelineData,
  isLatest,
}) => {
  const { meta_data } = timelineData;
  const { action_by, timestamp, lawyer_profiles, action_buttons } =
    meta_data;
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : action_by || timelineData.action_user_role || DEFAULT_ACTION_BY;
  return (
    <div
      className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}
      aria-label={`Profile cards sent notification from ${action_by}`}
    >
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fa-solid fa-id-card text-xl sm:mt-0 mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Profile cards sent
          </span>
        </div>

        <hr className="block border-t border-novaDarkAmber my-3" />

        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          {action_by} has compiled and sent detailed profile cards of
          interested experts to help you make an informed decision. Each
          profile includes experience, specialisations, client reviews, and
          pricing information.
        </p>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-users text-novaNeutral-700 text-sm"></i>
            <span className="text-md font-semibold text-novaNeutral-900">
              Experts Included:
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {lawyer_profiles && lawyer_profiles.length > 0 ? (
              lawyer_profiles.map(
                (lawyer, index: number) => (
                  <div
                    key={index}
                    className="bg-[#fff1df] text-novaNeutral-900 px-1 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {lawyer.photo_url ? (
                      <img
                        src={lawyer.photo_url}
                        alt=""
                        className="w-8 h-8 rounded-full object-cover border border-novaDarkOrange"
                      />
                    ) : (
                      <span
                        className="w-8 h-8 flex items-center justify-center rounded-full border border-novaDarkOrange text-novaNeutral-900 shrink-0"
                        title={
                          lawyer.name || lawyer.lawyer_name || "Lawyer"
                        }
                      >
                        <i className="fa-solid fa-user text-novaDarkOrange text-sm"></i>
                      </span>
                    )}
                    <span className="text-novaNeutral-900 mr-2 line-clamp-1" title={lawyer.name || lawyer.lawyer_name}>
                      {lawyer.name || lawyer.lawyer_name}
                    </span>
                  </div>
                )
              )
            ) : (
              <span className="text-sm text-novaNeutral-400 italic">
                No experts notified
              </span>
            )}
          </div>
        </div>

        {action_buttons && Object.keys(action_buttons).length > 0 && (
          <div className="flex gap-2 mb-4">
            {Object.entries(action_buttons).map(([label, handler]) => (
              <button
                key={label}
                onClick={handler}
                className="px-4 py-2 text-sm font-medium text-white bg-novaDarkOrange hover:bg-novaDarkAmber rounded-full transition-colors"
              >
                {label}
              </button>
            ))}
          </div>
        )}

        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default ProfileCardSend;
