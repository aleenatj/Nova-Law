import React, { useState } from "react";
import ReviewProfilesModal from "../../../ReviewProfilesModal";
import KycForm from "../../../KycForm";
import ResolveDetailsModal from "../../../ResolveDetailsModal";
import { api } from "../../../../../lib/api";
import { LawyerProfileDisplayType } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { createErrorToast, toastManager } from "@/utils/toasts";
import { FormButton, renderHtmlContent } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { useTimeline } from "@/contexts/TimelineContext";

interface MiniEngageCompletedCardProps {
  timelineData?: any;
  isLatest?: boolean;
}

const MiniEngageCompletedCard: React.FC<MiniEngageCompletedCardProps> = ({
  timelineData,
  isLatest,
}) => {
  const { refreshCaseDetails, refreshTimeline } = useTimeline();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [lawyers, setLawyers] = useState<LawyerProfileDisplayType[]>([]);
  const [loading, setLoading] = useState(false);

  // KYC Form state
  const [isKycFormOpen, setIsKycFormOpen] = useState(false);
  const [kycData, setKycData] = useState<Record<string, any>>({});
  const [kycLoading, setKycLoading] = useState(false);

  const [resolveData, setResolveData] = useState<Record<string, any>>({});
  const [resolveLoading, setResolveLoading] = useState(false);
  const [isResolveDetailsOpen, setIsResolveDetailsOpen] = useState(false);
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData?.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : timelineData?.action_user_role || DEFAULT_ACTION_BY;

  const handleMiniEngageDetails = async () => {
    try {
      setKycLoading(true);
      // Get case ID from timelineData or use a default one for demonstration
      const caseId = timelineData?.case_id || "";
      const encodedCaseId = encodeURIComponent(caseId);
      const response = await api.get(
        `/v1/customer/kyc?case_id=${encodedCaseId}`
      );
      // Set the KYC data and open the form
      setKycData((response as any).data || {});
      setIsKycFormOpen(true);
    } catch (error: any) {
      let errorMessage = "Failed to get KYC details. Please try again.";

      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // const toast = createErrorToast("Error", errorMessage);
      // toastManager.addToast(toast);
      setIsKycFormOpen(false);
    } finally {
      setKycLoading(false);
    }
  };

  const handleResolveDetails = async () => {
    try {
      setResolveLoading(true);
      const response = await api.get(
        `/v1/resolve?resolve_id=${timelineData?.meta_data?.resolve_id}`
      );
      setResolveData((response as any).data || {});
      setIsResolveDetailsOpen(true);
    } catch (error: any) {
      let errorMessage = "Failed to get Resolve details. Please try again.";

      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // const toast = createErrorToast("Error", errorMessage);
      // toastManager.addToast(toast);
      setIsResolveDetailsOpen(false);
    } finally {
      setResolveLoading(false);
    }
  };

  // Dummy data for selected lawyers
  // No mapping needed - API response is already in the correct format

  const handleFetchLawyers = async () => {
    setLoading(true);
    try {
      const encodedCaseId = encodeURIComponent(timelineData?.case_id || "");
      const response = await api.get(
        `/v1/timeline/matching-lawyers?case_id=${encodedCaseId}`
      );
      const isCaseNotified = Boolean((response as any)?.is_case_notified);
      const apiLawyers = Array.isArray((response as any).data)
        ? (response as any).data.map((lawyer: any) => ({
            ...lawyer,
            is_sent: isCaseNotified,
          }))
        : [];

      // Use API response directly - no mapping needed

      setLawyers(apiLawyers);
      setIsModalOpen(true);
    } catch (error) {
      console.error("Error loading experts:", error);
      setLawyers([]);
      setIsModalOpen(true);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-chart-line text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Alignment Check completed
          </span>
        </div>

        <hr className="block border-t border-novaDarkAmber my-3" />
  
        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-file-alt text-novaNeutral-700 text-sm"></i>
            <span className="text-md font-semibold text-novaNeutral-900">Case Summary:</span>
          </div>
          <div className="flex flex-col gap-2 sm:gap-3 text-md text-novaNeutral-700">
            {Array.isArray(timelineData.meta_data.case_summary?.summary) ? (
              timelineData.meta_data.case_summary.summary.length > 0 ? (
                timelineData.meta_data.case_summary.summary.map((item: any, idx: number) => (
                  <div key={idx} className="px-2 border-l-2 border-novaDarkAmber text-novaNeutral-400">
                    <div className="italic">
                      {item.question}
                    </div>
                    <div className="text-novaNeutral-700 italic">
                      {Array.isArray(item.answer)
                        ? item.answer.length > 0
                          ? (
                            <ul className="list-disc ml-4">
                              {item.answer.map((ans: string, i: number) => (
                                <li key={i}>{ans}</li>
                              ))}
                            </ul>
                          )
                          : <span className="italic text-novaNeutral-400">No answer provided.</span>
                        : (item.answer && item.answer.trim() !== "")
                          ? item.answer
                          : <span className="italic text-novaNeutral-400">No answer provided.</span>
                      }
                    </div>
                  </div>
                ))
              ) : (
                <span className="italic text-novaNeutral-400">No summary available.</span>
              )
            ) : (
              renderHtmlContent(timelineData.meta_data.case_summary) ||
              <span className="italic text-novaNeutral-400">No summary available.</span>
            )}
          </div>
        </div>

        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-clipboard-list text-novaNeutral-700 text-sm"></i>
            <span className="text-md font-semibold text-novaNeutral-900">
              Matched Experts:
            </span>
          </div>
          <div className="flex flex-wrap gap-2 sm:gap-4">
            {timelineData?.meta_data?.matched_lawyers &&
            Array.isArray(timelineData.meta_data.matched_lawyers) &&
            timelineData.meta_data.matched_lawyers.length > 0 ? (
              timelineData.meta_data.matched_lawyers.map(
                (lawyer: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 bg-[#fff1df] text-novaNeutral-900 rounded-full p-1"
                  >
                    {lawyer.photo_url ? (
                      <img
                        src={lawyer.photo_url}
                        alt=""
                        className="w-8 h-8 rounded-full object-cover border border-novaDarkOrange"
                      />
                    ) : (
                      <span className="w-8 h-8 flex items-center justify-center rounded-full border border-novaDarkOrange shrink-0">
                        <i className="fas fa-user text-novaDarkOrange text-sm"></i>
                      </span>
                    )}
                    <span title={lawyer.name} className="text-sm text-novaNeutral-900 mr-2 min-w-[64px] line-clamp-1">
                      {lawyer.name}
                    </span>
                  </div>
                )
              )
            ) : (
              <span className="italic text-novaNeutral-400 text-sm">
                No matched experts found.
              </span>
            )}
          </div>
        </div>
        <div className="flex flex-col gap-3 mb-4 sm:flex-row sm:gap-4 sm:flex-wrap">
          {timelineData?.meta_data?.action_buttons?.review_profiles && (
            <div>
              <FormButton
                variant="primary"
                onClick={handleFetchLawyers}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors"
              >
                <i className="fas fa-eye"></i>
                {loading ? "Fetching experts..." : "Invite Experts"}
              </FormButton>
            </div>
          )}
          {timelineData?.meta_data?.action_buttons?.resolve_details && (
            <div>
              <FormButton
                variant="outline"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm"
                onClick={handleResolveDetails}
                disabled={resolveLoading}
              >
                {resolveLoading ? (
                  <>
                    <i className="fas fa-spinner fa-spin"></i>
                    Loading Details...
                  </>
                ) : (
                  <>
                    <i className="fas fa-file-alt"></i>
                    Recommendation Details
                  </>
                )}
              </FormButton>
            </div>
          )}
          {timelineData?.meta_data?.action_buttons?.kyc_details && (
            <div>
              <FormButton
                variant="outline"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm"
                onClick={handleMiniEngageDetails}
                disabled={kycLoading}
              >
                {kycLoading ? (
                  <>
                    <i className="fas fa-spinner fa-spin"></i>
                    Loading Details...
                  </>
                ) : (
                  <>
                    <i className="fas fa-clipboard-check"></i>
                    Alignment Check Details
                  </>
                )}
              </FormButton>
            </div>
          )}
        </div>
        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timelineData?.meta_data?.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>

        {/* Review Profiles Modal - Only render when lawyers data is available */}
        <ReviewProfilesModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onConfirmSuccess={() => {
            refreshCaseDetails();
            refreshTimeline();
          }}
          lawyers={lawyers}
          caseId={timelineData?.case_id}
        />

        {/* KYC Form Modal */}
        <KycForm
          data={kycData}
          isOpen={isKycFormOpen}
          onClose={() => setIsKycFormOpen(false)}
          viewMode={true}
          caseId={timelineData?.case_id}
        />

        {/* Resolve Details Modal */}
        <ResolveDetailsModal
          isOpen={isResolveDetailsOpen}
          onClose={() => setIsResolveDetailsOpen(false)}
          caseId={timelineData?.case_id}
          data={resolveData}
          resolveId={timelineData?.meta_data?.resolve_id}
        />
      </div>
    </div>
  );
};

export default MiniEngageCompletedCard;
