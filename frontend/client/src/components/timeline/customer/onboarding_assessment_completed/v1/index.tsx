import React from "react";
import { OnBoardingAssessmentCompletedTimelineProps } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";

const OnBoardingAssessmentCompletedCard: React.FC<
  OnBoardingAssessmentCompletedTimelineProps
> = ({ timelineData }) => {
  const { meta_data } = timelineData;

  if (!meta_data) {
    console.error("OnBoardingAssessmentCompleted: meta_data is missing");
    return (
      <div className="timeline-card-border bg-red-50 border-red-200 p-6">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-start sm:items-center gap-2 flex-wrap">
              <i className="fas fa-exclamation-circle text-sm"></i>
              <span className="text-lg font-medium text-novaNeutral-900">
                Error: Missing onboarding data
              </span>
            </div>
            <div className="h-px bg-red-200 my-2"></div>
            <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
              Unable to load onboarding assessment information at this time.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Use make_payment boolean to control button enabled/disabled
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        "Nova AI";

  return (
      <div className="timeline-card-border bg-novaSuccess-50 border-novaSuccess-200 sm:p-6 p-4">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-start sm:items-center gap-2">
            <i className="fas fa-check-circle text-xl"></i>
            <span className="sm:text-[28px] text-xl font-semibold text-[#1A1425]">
              Onboarding assessment completed
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-md leading-6 text-novaNeutral-700 mb-3 w-full lg:w-[60%]">
            Your Nova Expert has received your Nova Engage submission.  We have emailed  a copy directly to you (unlocked with your memorable word).
          </p>
          <div className="bg-white rounded-lg p-4 border border-novaDarkAmber">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-start sm:items-center gap-2 flex-wrap mb-3">
                  {/* <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
                  <h4 className="text-sm font-medium text-novaNeutral-900">
                    Next steps:
                  </h4> */}
                  <p className="text-base leading-5 text-novaNeutral-700 space-y-1 ml-2">
                   Here is what happens next, {meta_data.customer_first_name}.  Your Nova Expert or their team will:
                  </p>
                </div>
                <ul className="text-sm leading-5 text-novaNeutral-700 space-y-3 ml-2">
                  {[
                    "Contact you by telephone or your other preferred means of communication to arrange a convenient date and time for your Strategic Advice Consultation;",
                    "Carry out identity and money laundering checks (this is not something to worry about, regulated professionals are required by law to do this with every new client).",
                    "Email you to confirm the date and time of your consultation;",
                    "Your Nova Expert will prepare for your Strategic Advice Consultation by studying all of the information you have helpfully provided so you benefit from advice tailored to your unique circumstances."
                  ].map((item, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-novaNeutral-800 mt-1 mr-4">•</span>
                      <span className="text-sm leading-6 text-novaNeutral-700 text-left break-words items-center">
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          <p className="text-base leading-6 text-novaNeutral-700 mb-3 w-full lg:w-[80%] my-4">
          Your Nova Expert will now guide your next steps, {meta_data.customer_first_name}. In the meantime, you can return to your My Nova dashboard at any time to revisit the information you have provided us, view your Personal Recommendation & Nova Expert details, access Support & Guidance, or contact the Nova Navigator team if you have any questions. We’re here to support you at every stage.
          </p>
          <div className="text-xs text-novaNeutral-500 mt-3 flex items-center gap-1">
            <i className="fa-solid fa-clock text-novaNeutral-500 text-xs"></i>
            <span>{formatTimestamp(meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnBoardingAssessmentCompletedCard;
