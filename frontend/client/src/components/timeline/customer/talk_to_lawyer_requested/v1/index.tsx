import React, { useState } from "react";
import {
  MatchConfirmedLawyerType,
  TalkToLawyerRequestedTimelineProps,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { formatTimestamp } from "@/utils/formatedDate";
import ChooseAnotherLawyerPopUp from "@/components/timeline/ChooseAnotherLawyerPopUp";
import { api } from "@/lib/api";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const TalkToLawyerRequestedCard: React.FC<
  TalkToLawyerRequestedTimelineProps
> = ({ timelineData, isLatest }) => {
  const { meta_data } = timelineData;
  const [showChooseLawyerModal, setShowChooseLawyerModal] = useState(false);
  const [availableLawyers, setAvailableLawyers] = useState<
    MatchConfirmedLawyerType[]
  >([]);
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;

  const handleFetchMatchedLawyers = async () => {
    try {
      const encodedCaseId = encodeURIComponent(timelineData?.case_id || "");
      const response = await api.get(
        `/v1/timeline/match_confirmed_lawyers?case_id=${encodedCaseId}`
      );

      // Extract lawyers from the correct response structure
      let apiLawyers: MatchConfirmedLawyerType[] = [];

      if (response && typeof response === "object") {
        const responseData = (response as any).data;

        // Check if response.data has match_confirmed_lawyers array
        if (
          responseData &&
          Array.isArray(responseData.match_confirmed_lawyers)
        ) {
          apiLawyers = responseData.match_confirmed_lawyers;
        }
        // Fallback: check if response.data is directly an array
        else if (Array.isArray(responseData)) {
          apiLawyers = responseData;
        }
      }

      setAvailableLawyers(apiLawyers);
      setShowChooseLawyerModal(true);
    } catch (error) {
      setAvailableLawyers([]);
      setShowChooseLawyerModal(true);
    } finally {
      // setLoading(false);
    }
  };

  const handleCloseModal = () => {
    setShowChooseLawyerModal(false);
  };

  return (
    <div className="timeline-card-border bg-novaSuccess-50 sm:p-6 p-4">
      <div className="flex items-start gap-3">

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start gap-2">
            <i className="fas fa-comments text-[#1A1425] text-xl"></i>
            <span className="sm:text-[28px] sm:items-center text-xl font-semibold items-center text-[#1A1425]">
              {isLatest ? `A call with ${timelineData.meta_data.lawyer_name} is being arranged for you` : `A call with ${timelineData.meta_data.lawyer_name} arranged for you`}
            </span>
            {/* <span className="text-xs bg-novaBlue-100 text-novaBlue-700 px-2 py-1 rounded-full">
              Pending
            </span>  Commented out for now, status after MVP implementation*/}
          </div>
          <hr className="block border-t border-novaDarkAmber my-[14px]" />

          {/* Description */}
          <p className="text-[16px] leading-5 text-novaNeutral-700 mb-3">
            We’ll email you shortly with some available times so you can talk things through with {meta_data.lawyer_name}. 
          </p>

          {/* <div className="mt-4 flex gap-2 mb-3">
            <FormButton
              variant="primary"
              onClick={handleFetchMatchedLawyers}
              className="text-sm px-4 py-2"
              disabled={!meta_data.action_buttons.choose_another_lawyer}
            >
              <i className="fas fa-user-plus"></i>
              Engage with a Lawyer
            </FormButton>
          </div> */}

          {/* Timestamp */}
          <div className="text-xs flex items-center gap-1">
            <i className="fas fa-clock text-xs"></i>
            <span>{formatTimestamp(meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </div>
        </div>
      </div>

      {/* Choose Another Lawyer Modal */}
      {showChooseLawyerModal && (
        <ChooseAnotherLawyerPopUp
          caseId={timelineData.case_id}
          isOpen={showChooseLawyerModal}
          onClose={handleCloseModal}
          lawyers={availableLawyers}
          // onEngageLawyer={handleEngageLawyer}
        />
      )}
    </div>
  );
};

export default TalkToLawyerRequestedCard;
