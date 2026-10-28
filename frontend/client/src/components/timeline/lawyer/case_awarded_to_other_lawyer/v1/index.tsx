import React from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

type MatchedStatus = "Pending" | "Interested" | "Declined";

interface CaseOpenedV1Props {
  timelineData: {
    action_user_name: string;
    meta_data: {
      case_number: string;
      timestamp: string;
      action_by: string;
      match_status?: MatchedStatus;
    };
    created_at: string;
    version: number;
  };
  isLatest?: boolean;
}

const STATUS_DESCRIPTIONS: Record<
  MatchedStatus,
  { title: string; heading: string; description: string;}
> = {
  // Pending: {
  //   heading: "Update on the Case You Were Notified About",
  //   description:
  //     "We wanted to inform you that the case recently shared with you on Nova has now been awarded to another Expert, as chosen by the client. Since you had not yet expressed interest in this case, no further action is required from your end. New cases are posted regularly, and we encourage you to check your dashboard for upcoming opportunities that may better suit your availability and expertise. Thank you for being part of the Nova network.",
  // },
  // Interested: {
  //   heading: "Update on Your Case Application",
  //   description:
  //     "We wanted to let you know that the client has decided to proceed with another Expert for this particular case. We truly appreciate your time and willingness to take it up. Please note that new cases are added regularly on Nova, and we encourage you to keep an eye out for upcoming opportunities that match your expertise. Thank you once again for being a valued part of the Nova network.",
  // },
  // Declined: {
  //   heading: "Update on the Case You Were Notified About",
  //   description:
  //     "We wanted to inform you that the case recently shared with you on Nova has now been awarded to another Expert, as chosen by the client. Since you had not yet expressed interest in this case, no further action is required from your end. New cases are posted regularly, and we encourage you to check your dashboard for upcoming opportunities that may better suit your availability and expertise. Thank you for being part of the Nova network.",
  // },
  Pending: {
    title: "Case case_number has been awarded to another Nova Expert.",
    heading: "Update on the Case You Were Notified About",
    description:
      "As you did not register interest, no action is required. Nova releases new matters on an ongoing basis. You’ll be notified when opportunities aligned with your profile become available.",
  },
  Interested: {
    title: "The client has selected a different Nova Expert for case case_number.",
    heading: "Update on Your Case Application",
    description:
      "Thank you for registering interest in this case. Nova releases new matters on an ongoing basis. You’ll be notified when opportunities aligned with your profile become available.",
  },
  Declined: {
    title: "Case case_number has been awarded to another Nova Expert.",
    heading: "Update on the Case You Were Notified About",
    description:
      "As you did not register interest, no action is required. Nova releases new matters on an ongoing basis. You’ll be notified when opportunities aligned with your profile become available.",
  },
};

function renderWithStrong(text: string, key: string, value: string) {
  return text.split(key).map((part, index, arr) => (
    <>
      {part}
      {index < arr.length - 1 && <strong key={index} className="text-[#1A1425]">{value}</strong>}
    </>
  ));
}

export function CaseOpenedV1({ timelineData, isLatest }: CaseOpenedV1Props) {
  const { meta_data } = timelineData;
  const matchedStatus: MatchedStatus =
    meta_data.match_status || "Pending";
  const statusDetails = STATUS_DESCRIPTIONS[matchedStatus];

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-user-times text-xl"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            {/* Case assigned to another Expert        */}
            Case awarded to another Nova Expert
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          {/* The case <strong className="text-[#1A1425]">{meta_data.case_number}</strong> has been awarded to a different Expert. You're no longer assigned to represent the client on this matter. */}
          {renderWithStrong(statusDetails.title, "case_number", meta_data.case_number)}
        </p>
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">{statusDetails.description}</p>
        {/* <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">
              {statusDetails.heading}
            </span>
          </div>
          <p className="text-sm text-novaNeutral-700">{statusDetails.description}</p>
        </div> */}
        <p className="text-xs text-novaNeutral-500 flex items-center">
          <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {DEFAULT_ACTION_BY}</span>
        </p>
      </div>
    </div>
  );
}

export default CaseOpenedV1;
