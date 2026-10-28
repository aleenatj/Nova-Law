import React, { useState, useEffect, useCallback } from "react";
import { Button } from "../../../../ui/button";
import { CaseOpenedResponsePropsType } from "../../../../../lib/types";
import { createErrorToast, formatTimestamp, FormButton, renderHtmlContent, toastManager } from "../../../../../utils";
import { api } from "../../../../../lib/api";
import KycFormNew from "../../../KycFormNew";
import ResolveDetailsModal from "../../../ResolveDetailsModal";
import { useParams } from "wouter";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { useTimeline } from "@/contexts/TimelineContext";

interface CaseOpenedProps {
  timelineData?: CaseOpenedResponsePropsType;
}

const CaseOpened: React.FC<CaseOpenedProps> = ({
  timelineData,
}) => {
  const { refreshTimeline } = useTimeline();
  const [showPopup, setShowPopup] = useState(false);
  const [kycData, setKycData] = useState<any>(null);
  const params = useParams();
  const caseId = params.id;
  const [resolveData, setResolveData] = useState<any>({});
  const [resolveLoading, setResolveLoading] = useState(false);
  const [isResolveDetailsOpen, setIsResolveDetailsOpen] = useState(false);

  // Helper function to remove kycForm parameter from URL
  const removeKycFormParam = useCallback(() => {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.delete("kycForm");
    const newUrl = urlParams.toString()
      ? `${window.location.pathname}?${urlParams.toString()}`
      : window.location.pathname;
    window.history.replaceState({}, "", newUrl);
  }, []);

  const handleKycFormClick = useCallback(async (fromUrlParam?: boolean) => {
    try {
      const encodedCaseId = encodeURIComponent(caseId || '');
      const response = await api.get(`/v1/customer/kyc?case_id=${encodedCaseId}`);
      setKycData((response as any).data);
      setShowPopup(true);
      // Remove URL param only after popup successfully opens (if triggered by URL param)
      if (fromUrlParam) {
        removeKycFormParam();
      }
    } catch (error) {
      // Use hardcoded data as 
    }
  }, [caseId, removeKycFormParam]);

  // Check for kycForm query parameter in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const kycFormParam = urlParams.get("kycForm");
    
    if (kycFormParam === "true" && caseId) {
      handleKycFormClick(true); // Pass true to indicate it's from URL param
    }
  }, [caseId, handleKycFormClick]);
  
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
      const toast = createErrorToast("Error", errorMessage);
      toastManager.addToast(toast);
      setIsResolveDetailsOpen(false);
    } finally {
      setResolveLoading(false);
    }
  };

  // Check if timelineData exists and has meta_data
  if (!timelineData?.meta_data) {
    return (
      <div className="timeline-card-border bg-novaCaution-50 border-novaCaution-200 p-6">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-start sm:items-center gap-2 flex-wrap">
              <i className="fas fa-exclamation-triangle text-novaCaution-600 text-sm"></i>
              <span className="text-sm font-medium text-novaNeutral-900">
                No case data available
              </span>
            </div>
            <div className="h-px bg-novaCaution-200 my-2"></div>
            <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
              Unable to load case information at this time.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const data = timelineData.meta_data;
  const actionBy = timelineData.action_user_name || timelineData.action_user_role || DEFAULT_ACTION_BY;

  return (
    <div className="timeline-card-border bg-novaSuccess-50 timeline-cardborder border-novaSuccess-200 sm:p-6 p-4">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="items-start sm:items-center gap-2 flex-wrap mb-2">
            <i className="fas fa-folder-open text-md mr-2"></i>
            <span className="text-lg font-medium text-novaNeutral-900">
              Welcome! Your Case Has Been Opened
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-2" />
          <p className="text-sm leading-7 text-novaNeutral-700 sm:px-0 mb-1">
            Hello! We're excited to help you with your legal matter. Your case{" "}
            <strong>{data.case_number}</strong> has been successfully created.
          </p>
          <div className="mt-3 bg-white rounded-md sm:px-5 p-3 ">
            <div className="flex flex-row gap-4">
              <div className="">
                <div className="mb-1">
                  <span className="text-sm font-semibold text-novaNeutral-600">
                    Next Step:
                  </span>
                </div>
                <div>
                  <div className="text-sm text-novaNeutral-900">
                    {data.next_steps}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-3 bg-white rounded-md sm:px-5 p-3">
            <div className="mb-1">
              <span className="text-sm font-semibold">Case Summary:</span>
            </div>
            <div className="text-sm whitespace-pre-line leading-7">
              {(typeof data.summary === 'object' && 
                Array.isArray((data.summary as any)?.summary)) ? (
                <div className="flex flex-col gap-2">
                  {(data.summary as any).summary.map((item: any, idx: number) => (
                    <div key={idx} className="mb-1">
                      <div className="font-semibold text-novaNeutral-800">
                        {item.question}
                      </div>
                      <div className="ml-2 text-novaNeutral-700">
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
                  ))}
                </div>
              ) : (
                renderHtmlContent(data.summary) ||
                "No additional summary available at this time."
              )}
            </div>
          </div>

          <div className="flex flex-row gap-2">
            {/* Action Button */}
            {data.action_buttons?.kyc_form && (
              <div className="mt-3">
                <FormButton
                  variant="primary"
                  className="flex text-sm"
                  onClick={handleKycFormClick}
                >
                  <i className="fas fa-clipboard-list text-white mt-0.5 mr-2"></i>
                  <span className="hidden lg:inline">Alignment Check Form</span>
                  <span className="inline lg:hidden">Alignment Check</span>
                </FormButton>
              </div>
            )}
            {timelineData?.meta_data?.action_buttons?.view_resolve && (
              <div className="mt-3">
                <FormButton
                  variant="outline"
                  className="w-full inline-flex items-center justify-center gap-2 whitespace-nowrap ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border bg-background hover:text-accent-foreground border-green-600 text-green-600 hover:bg-green-50 text-sm px-4 py-2"
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
          </div>
          
          <p className="text-xs text-novaNeutral-500 mt-2 flex items-center">
            <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
            <span>{formatTimestamp(data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2"> • {actionBy}</span>
          </p>
        </div>
      </div>

      {/* KYC Form Popup */}
      {kycData && (
        <KycFormNew
          data={kycData}
          isOpen={showPopup}
          onClose={() => {
            setShowPopup(false);
            // Remove kycForm parameter from URL when closing
            removeKycFormParam();
          }}
          onSubmit={() => {
            removeKycFormParam();
            refreshTimeline();
          }}
          caseId={caseId}
          viewMode={false}
        />
      )}

      {/* Resolve Details Modal */}
      <ResolveDetailsModal
        data={resolveData}
        isOpen={isResolveDetailsOpen}
        onClose={() => setIsResolveDetailsOpen(false)}
        caseId={caseId}
        showViewCaseButton={false}
      />
    </div>
  );
};

export default CaseOpened;
