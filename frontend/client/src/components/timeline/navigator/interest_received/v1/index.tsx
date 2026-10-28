import React, { useState } from "react";
import {
  NavigatorInterestReceivedTimelineProps,
  InterestedLawyerType,
} from "@/lib/types";
import { Button } from "@/components";
import InterestedLawyersPopUp from "@/components/timeline/InterestedLawyersPopUp";
import { api } from "@/lib/api";
import { formatTimestamp } from "@/utils/formatedDate";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { useTimeline } from "@/contexts/TimelineContext";

const NavigatorInterestReceived: React.FC<
  NavigatorInterestReceivedTimelineProps & { isLatest?: boolean }
> = ({ timelineData, isLatest }) => {
  const { refreshCaseDetails, refreshTimeline } = useTimeline();
  const { meta_data } = timelineData;
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData?.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : timelineData?.action_user_role || DEFAULT_ACTION_BY;

  const [showPopup, setShowPopup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [interestedLawyers, setInterestedLawyers] = useState<
    InterestedLawyerType[]
  >([]);

  const handleClosePopup = () => setShowPopup(false);

  const handleSendLawyers = (selectedLawyers: any[]) => {
    setShowPopup(false);
    refreshCaseDetails();
    refreshTimeline();
  };

  const handleFetchInterestedLawyers = async () => {
    setLoading(true);
    try {
      const caseId = timelineData?.case_id || "";
      const encodedCaseId = encodeURIComponent(caseId);
      const response = (await api.get(
        `/v1/timeline/interested-lawyers?case_id=${encodedCaseId}`
      )) as any;

      // Display the response to console as requested
      if (response?.data) {
        // Extract interested lawyers from the response
        let lawyers = [];
        if (Array.isArray(response.data.lawyers)) {
          lawyers = response.data.lawyers;
        } else if (Array.isArray(response.data)) {
          lawyers = response.data;
        } else if (Array.isArray(response.data.data)) {
          lawyers = response.data.data;
        } else {
          console.warn(
            "No valid lawyers array found in response:",
            response.data
          );
          lawyers = [];
        }

        setInterestedLawyers(lawyers);
        setShowPopup(true);
      }
    } catch (error) {
      console.error("Error fetching interested lawyers:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          <div className="flex gap-2">
            <i className="fas fa-hand-paper text-xl mt-1"></i>
            <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
              Interest received
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            <strong className="text-[#1A1425]">{meta_data.lawyer_name}</strong> has expressed interest in
            taking on your case.
          </p>
          {meta_data.interest_message || meta_data.about_lawyer && (
            <div className="bg-white sm:p-6 p-4 rounded-lg mb-4 border-l-4 border-novaDarkAmber">
              <p className="text-md text-novaNeutral-700 italic">
                {meta_data.interest_message || meta_data.about_lawyer}
              </p>
            </div>
          )}
          {meta_data.action_buttons?.send_reviewed_profiles && (
            <div className="mb-4">
              <FormButton
                variant="primary"
                className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors"
                type="button"
                aria-haspopup="dialog"
                aria-expanded={showPopup}
                aria-controls="radix-:r37:"
                data-state={showPopup ? "open" : "closed"}
                onClick={handleFetchInterestedLawyers}
                disabled={loading}
              >
                <i className="fas fa-users"></i>
                {loading ? "Fetching Experts..." : "Review & Send Profiles"}
              </FormButton>
            </div>
          )}
          <p className="text-xs flex items-center">
            <i className="fas fa-clock text-xs mr-1"></i>
            <span>{formatTimestamp(meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>
        </div>
      </div>
      {showPopup && (
        <InterestedLawyersPopUp
          isOpen={showPopup}
          onClose={handleClosePopup}
          onSend={handleSendLawyers}
          interestedLawyers={interestedLawyers}
          caseId={timelineData?.case_id}
        />
      )}
    </>
  );
};

export default NavigatorInterestReceived;
