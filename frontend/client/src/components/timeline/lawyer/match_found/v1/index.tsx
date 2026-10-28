import React, { useState } from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { MatchFoundResponsePropsType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toastManager, createErrorToast, createSuccessToast } from "@/utils/toasts";
import { useAuth } from "@/contexts/AuthContext";
import { CaseDeclinePopup } from "../../case_decline_popup";
import ResolveDetailsModal from "../../../ResolveDetailsModal";
import KycForm from "../../../KycForm";
import GlobalModalWrapper from "../../../../modal/GlobalModalWrapper";
import { INPUT_MAX_LENGTH } from "@/lib/constants";
import { FormButton } from "@/utils";

interface MatchFoundV1Props {
  timelineData: MatchFoundResponsePropsType;
  isLatest?: boolean;
}

export function MatchFoundV1({ timelineData, isLatest }: MatchFoundV1Props) {
  const { action_buttons } = timelineData.meta_data;
  const metaData = timelineData.meta_data;
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [detailsText, setDetailsText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isInterestSubmitting, setIsInterestSubmitting] = useState(false);
  const [isDeclineModalOpen, setIsDeclineModalOpen] = useState(false);
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const lawyerId = user.lawyer_id || (localStorage.getItem('navigator_switched_lawyer_id') || null);
  const [kycData, setKycData] = useState<Record<string, any>>({});
  const [kycLoading, setKycLoading] = useState(false);
  const [isKycFormOpen, setIsKycFormOpen] = useState(false);

  const [resolveData, setResolveData] = useState<Record<string, any>>({});
  const [resolveLoading, setResolveLoading] = useState(false);
  const [isResolveDetailsOpen, setIsResolveDetailsOpen] = useState(false);
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : metaData?.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        "Nova AI";

  const showToastsWithDelay = async (messages: any[], isSuccess: boolean) => {
    const delay = 400; // ms
    for (let i = 0; i < messages.length; i++) {
      const messageItem = messages[i];
      await new Promise((resolve) => setTimeout(resolve, i === 0 ? 0 : delay));

      // Handle different message formats
      let messageText = "";
      let isMessageSuccess = isSuccess;

      if (typeof messageItem === "string") {
        messageText = messageItem;
      } else if (typeof messageItem === "object" && messageItem !== null) {
        messageText =
          messageItem.message ||
          messageItem.text ||
          JSON.stringify(messageItem);
        isMessageSuccess = messageItem.success !== false && isSuccess;
      } else {
        messageText = String(messageItem);
      }

      if (isMessageSuccess) {
        const toast = createSuccessToast("Success", messageText);
        toastManager.addToast(toast);
      } else {
        const toast = createErrorToast("Error", messageText);
        toastManager.addToast(toast);
      }
    }
  };

  const handleInterestClick = async () => {
    if (!lawyerId) {
      toastManager.addToast(
        createErrorToast(
          "Authentication Error",
          "Please log in to express interest in this case."
        )
      );
      return;
    }

    setIsInterestSubmitting(true);

    try {
      const response: any = await api.post("/v1/case/interest", {
        case_id: timelineData.case_id,
        lawyer_id: lawyerId,
      });

      if (response.success) {
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Interest Expressed",
            response.message ||
              "Your interest in this case has been successfully submitted."
          );
          toastManager.addToast(toast);
        }
      } else {
        // Handle error case
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          // const toast = createErrorToast(
          //   "Request Failed",
          //   response.message || "Failed to express interest. Please try again."
          // );
          // toastManager.addToast(toast);
        }
      }
    } catch (error: any) {
      let errorMessage = "Failed to express interest. Please try again.";
      // Extract error message from API response if available
      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }

      // toastManager.addToast(createErrorToast("Request Failed", errorMessage));
    } finally {
      setIsInterestSubmitting(false);
    }
  };

  const handleAskMoreDetailsClick = () => {
    setIsModalOpen(true);
  };

  const handleDeclineClick = () => {
    setIsDeclineModalOpen(true);
  };

  const handleDeclineModalClose = () => {
    setIsDeclineModalOpen(false);
  };

  const handleViewResolveClick = async () => {
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

  const handleViewKycClick = async () => {
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

  const handleModalClose = () => {
    if (isSubmitting) return; // Prevent closing during submission
    setIsModalOpen(false);
    setDetailsText("");
  };

  const renderHtmlContent = (htmlString: string) => {
    // Check if the string contains HTML tags
    const hasHtmlTags = /<[^>]*>/g.test(htmlString);

    if (hasHtmlTags) {
      // Return JSX with dangerouslySetInnerHTML for HTML content
      return <div dangerouslySetInnerHTML={{ __html: htmlString }} />;
    } else {
      // Return plain text for non-HTML content
      return <div>{htmlString}</div>;
    }
  };

  const handleSubmitRequest = async () => {
    if (!detailsText.trim()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const caseId = timelineData.case_id;

      await api.post("/v1/case/more-details", {
        case_id: caseId,
        query_text: detailsText.trim(),
        lawyer_id: lawyerId,
      });

      handleModalClose();
    } catch (error: any) {
      console.error("Error submitting more details request:", error);
      let errorMessage = "Failed to submit your request. Please try again.";
      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // toastManager.addToast(createErrorToast("Request Failed", errorMessage));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          <div className="flex gap-2">
            <i className="fas fa-folder-open text-xl"></i>
            <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
              Case match found
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            Nova AI has identified your profile as an excellent match for case{" "}
            <strong className="text-[#1A1425]">{metaData.case_number}</strong>. This family law case
            aligns perfectly with your expertise and experience. Please review
            the case details below and consider expressing your interest to
            represent this client.
          </p>
          <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
            <div className="flex items-center gap-2 mb-3">
              <i className="fas fa-clipboard-list text-novaNeutral-700 text-sm"></i>
              <span className="text-sm font-semibold text-novaNeutral-900">
                Case Summary:
              </span>
            </div>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-sm leading-5">
                  <div className="flex-1">
                    {typeof metaData.case_summary === "object" &&
                    Array.isArray(
                      (metaData.case_summary as any)?.summary
                    ) ? (
                      <div className="flex flex-col gap-2">
                        {(metaData.case_summary as any).summary
                          .length > 0 ? (
                          (
                            metaData.case_summary as any
                          ).summary.map((item: any, idx: number) => (
                            <div key={idx} className="mb-1  border-l-2 border-novaDarkAmber pl-2">
                              <div className="italic text-novaNeutral-400">
                                {item.question}
                              </div>
                              <div className="text-novaNeutral-700">
                                {Array.isArray(item.answer) ? (
                                  item.answer.length > 0 ? (
                                    <ul className="list-disc ml-4">
                                      {item.answer.map(
                                        (ans: string, i: number) => (
                                          <li key={i}>{ans}</li>
                                        )
                                      )}
                                    </ul>
                                  ) : (
                                    <span className="italic text-novaNeutral-700">
                                      No answer provided.
                                    </span>
                                  )
                                ) : item.answer && item.answer.trim() !== "" ? (
                                  item.answer
                                ) : (
                                  <span className="italic text-novaNeutral-700">
                                    No answer provided.
                                  </span>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <span className="italic text-novaNeutral-400">
                            No summary available.
                          </span>
                        )}
                      </div>
                    ) : (
                    <span className="text-novaNeutral-700">
                      {renderHtmlContent(metaData.case_summary) || (
                          <span className="italic text-novaNeutral-400">
                            No summary available.
                          </span>
                        )}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5 gap-2 sm:gap-3 mt-4">
              {action_buttons?.raise_interest && (
                <FormButton
                  variant="primary"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm h-10"
                  disabled={isInterestSubmitting}
                  onClick={handleInterestClick}
                >
                  {isInterestSubmitting ? (
                    <>
                      <i className="fas fa-spinner fa-spin text-xs sm:text-sm"></i>
                      <span className="">Submitting...</span>
                    </>
                  ) : (
                    <>
                      <i className="fas fa-hand-paper text-xs sm:text-sm"></i>
                      <span className="">I'm Interested</span>
                    </>
                  )}
                </FormButton>
              )}
              {action_buttons?.decline_match && (
                <FormButton
                  variant="outline"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm h-10"
                  onClick={handleDeclineClick}
                >
                  <i className="fas fa-times text-xs sm:text-sm"></i>
                  <span className="">Decline</span>
                </FormButton>
              )}
              {action_buttons?.ask_more_details && (
                <FormButton
                  variant="outline"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm h-10"
                  onClick={handleAskMoreDetailsClick}
                >
                  <i className="fas fa-question-circle text-xs sm:text-sm"></i>
                  <span className="hidden 2xl:inline">Ask More Details</span>
                  <span className="inline 2xl:hidden">More Details</span>
                </FormButton>
              )}
              {action_buttons?.view_resolve && (
                <FormButton
                  variant="outline"
                  size="custom"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm h-10"
                  disabled={resolveLoading}
                  onClick={handleViewResolveClick}
                >
                  {resolveLoading ? (
                    <>
                      <i className="fas fa-spinner fa-spin text-xs sm:text-sm"></i>
                      <span className="">Loading...</span>
                    </>
                  ) : (
                    <>
                      <i className="fas fa-eye text-xs sm:text-sm"></i>
                      <span className="">Recommendation Details</span>
                    </>
                  )}
                </FormButton>
              )}
              {action_buttons?.view_kyc && (
                <FormButton
                  variant="outline"
                  size="custom"
                  className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-xs sm:text-sm h-10"
                  disabled={kycLoading}
                  onClick={handleViewKycClick}
                >
                  {kycLoading ? (
                    <>
                      <i className="fas fa-spinner fa-spin text-xs sm:text-sm"></i>
                      <span className="">Loading...</span>
                    </>
                  ) : (
                    <>
                      <i className="fas fa-clipboard-check text-xs sm:text-sm"></i>
                      <span className="inline lg:hidden xl:inline">
                        Alignment Check Details
                      </span>
                      <span className="hidden lg:inline xl:hidden">Alignment Check</span>
                    </>
                  )}
                </FormButton>
              )}
            </div>
          <p className="text-xs flex items-center mt-4">
            <i className="fas fa-clock text-xs mr-1"></i>
            <span>{formatTimestamp(metaData.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>
        </div>
      </div>

      {/* Modal for Request More Details */}
      <GlobalModalWrapper
        isOpen={isModalOpen}
        onClose={isSubmitting ? () => {} : handleModalClose}
      >
        <div
          role="dialog"
          aria-describedby="modal-description"
          aria-labelledby="modal-title"
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] rounded-xl border border-gray-200 bg-white p-0 shadow-[0_2px_16px_0_rgba(0,0,0,0.18)]"
          tabIndex={-1}
          style={{ pointerEvents: "auto" }}
        >
          {/* Close Button */}
          <button
            type="button"
            onClick={handleModalClose}
            disabled={isSubmitting}
            className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-30 text-novaNeutral-600 hover:text-novaNeutral-700"
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-x h-5 w-5"
            >
              <path d="M18 6 6 18"></path>
              <path d="m6 6 12 12"></path>
            </svg>
          </button>

          {/* Header */}
          <div className="px-6 pt-6 pb-2">
            <h2
              id="modal-title"
              className="text-base font-semibold leading-none tracking-tight flex items-center gap-2 mb-1"
            >
              <i className="fas fa-question-circle text-novaAlert-500 text-lg"></i>
              <span>Request More Details</span>
            </h2>
            <p
              id="modal-description"
              className="text-[15px] text-novaNeutral-500"
            >
              Please specify what additional information you need about this
              case to help you make an informed decision.
            </p>
          </div>

          {/* Content */}
          <div className="px-6 pb-2">
            <label className="block text-[15px] text-novaNeutral-900 mb-2 mt-2">
              What would you like to know more about?
            </label>
            <textarea
              placeholder="e.g., I need more information about the financial assets involved, timeline of events, or specific legal documents..."
              className="w-full px-3 py-2 border border-novaNeutral-300 rounded-lg text-[15px] text-novaNeutral-700 bg-novaNeutral-50 focus:outline-none focus:ring-2 focus:ring-novaAlert-500 focus:border-transparent resize-none"
              rows={4}
              value={detailsText}
              maxLength={INPUT_MAX_LENGTH.LAWYER_MORE_DETAILS_TEXT}
              onChange={(e) => setDetailsText(e.target.value)}
              disabled={isSubmitting}
              style={{ minHeight: "90px" }}
            />
            {((detailsText as string)?.length || 0) >=
              INPUT_MAX_LENGTH.LAWYER_MORE_DETAILS_TEXT && (
              <div className="text-xs text-novaCaution-500 mt-1">
                Limit reached
              </div>
            )}
          </div>

          {/* Footer Buttons */}
          <div className="flex items-center justify-end gap-2 px-6 pb-6 pt-2">
            <FormButton
              variant="custom"
              size="custom"
              onClick={handleModalClose}
              disabled={isSubmitting}
              className="inline-flex items-center justify-center gap-2 text-[15px] border border-novaNeutral-300 bg-white hover:bg-novaNeutral-50 hover:text-novaNeutral-900 h-10 px-5 py-2 text-novaNeutral-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
            >
              Cancel
            </FormButton>
            <FormButton
              variant="custom"
              size="custom"
              onClick={handleSubmitRequest}
              disabled={isSubmitting || !detailsText.trim()}
              className={`inline-flex items-center justify-center gap-2 text-[15px] h-10 px-5 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                isSubmitting || !detailsText.trim()
                  ? "bg-novaNeutral-200 text-novaNeutral-400 cursor-not-allowed"
                  : "bg-novaAlert-500 text-white hover:bg-novaAlert-600"
              }`}
            >
              {isSubmitting ? (
                <>
                  <i className="fas fa-spinner fa-spin mr-2"></i>
                  Submitting...
                </>
              ) : (
                <>
                  <i className="fa-solid fa-paper-plane text-white"></i> Submit
                  Request
                </>
              )}
            </FormButton>
          </div>
        </div>
      </GlobalModalWrapper>

      {/* Decline Case Modal */}
      <CaseDeclinePopup
        isOpen={isDeclineModalOpen}
        onClose={handleDeclineModalClose}
        caseId={timelineData.case_id}
      />

      {isKycFormOpen && (
        <KycForm
          data={kycData}
          isOpen={isKycFormOpen}
          onClose={() => setIsKycFormOpen(false)}
          caseId={timelineData.case_id}
          viewMode={true}
        />
      )}

      {isResolveDetailsOpen && (
        <ResolveDetailsModal
          isOpen={isResolveDetailsOpen}
          onClose={() => setIsResolveDetailsOpen(false)}
          data={resolveData}
          resolveId={timelineData.meta_data.resolve_id}
        />
      )}
    </>
  );
}

export default MatchFoundV1;
