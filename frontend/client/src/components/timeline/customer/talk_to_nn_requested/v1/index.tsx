import React, { useState } from "react";
import { MatchConfirmedLawyerType, TalkToNavigatorRequestedTimelineProps } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { formatTimestamp } from "@/utils/formatedDate";
import { api } from "@/lib/api";
import ChooseAnotherLawyerPopUp from "@/components/timeline/ChooseAnotherLawyerPopUp";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const TalkToNavigatorRequestedCard: React.FC<TalkToNavigatorRequestedTimelineProps & { isLatest?: boolean }> = ({ timelineData, isLatest }) => {
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

  const handleEngageWithLawyer = async () => {
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
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} timeline-card-border bg-novaBlue-50 border-novaBlue-200 sm:p-6 p-4`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-start sm:items-center gap-2 mb-1">
            <i className="fas fa-headset text-sm"></i>
            <span className="sm:text-[28px] text-xl font-semibold text-[#1A1425]">
              Talk to Nova Navigator Requested
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
            You've requested to talk to Nova Navigator for guidance on{" "}
            <strong>{meta_data.case_number}</strong>. Nova Navigator has been
            notified and will send you available meeting slots shortly.
          </p>
          <div className="bg-white rounded-lg p-3 mt-3 border border-novaDarkAmber">
            <div className="text-sm leading-5 text-novaNeutral-700">
              <div className="flex items-start sm:items-center gap-2 mb-1 flex-wrap">
                <i className="fas fa-clock text-novaDarkOrange text-sm"></i>
                <span className="font-medium text-novaNeutral-900">What happens next:</span>
              </div>
              <ul className="text-sm leading-5 text-novaNeutral-700 space-y-1 ml-4 list-disc">
                <li>Nova Navigator will review your request</li>
                <li>You will be informed once the next steps have been confirmed</li>
                <li>Meeting will be scheduled automatically</li>
              </ul>
            </div>
          </div>

          {meta_data.action_buttons?.choose_another_lawyer && (
            <div className="mt-4">
              <FormButton
                onClick={handleEngageWithLawyer}
                variant="primary"
                className="text-sm px-4 py-2"
              >
                <i className="fas fa-handshake mr-2"></i>
                Engage with a Lawyer
              </FormButton>
            </div>
          )}
          <div className="text-xs text-novaNeutral-500 mt-3 flex items-center gap-1">
            <i className="fas fa-clock text-novaNeutral-500 text-xs"></i>
            <span>{formatTimestamp(meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </div>
        </div>
      </div>
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

export default TalkToNavigatorRequestedCard;
