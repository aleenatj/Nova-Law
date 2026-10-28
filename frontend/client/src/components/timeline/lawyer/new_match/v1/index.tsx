import React, { useState } from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { LawyerMatchFoundResponsePropsType, LawyerMatchCaseSummaryItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toastManager, createErrorToast, createSuccessToast } from "@/utils/toasts";
import { useAuth } from "@/contexts/AuthContext";
import { CaseDeclinePopup } from "../../case_decline_popup";
import ResolveDetailsModal from "../../../ResolveDetailsModal";
import KycForm from "../../../KycForm";
import GlobalModalWrapper from "../../../../modal/GlobalModalWrapper";
import { DEFAULT_ACTION_BY, INPUT_MAX_LENGTH } from "@/lib/constants";
import { FormButton } from "@/utils";
import { formatCurrency, replacePlaceholders } from "@/lib/utils";

interface MatchFoundV1Props {
  timelineData: LawyerMatchFoundResponsePropsType;
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
  const [caseSummaryTab, setCaseSummaryTab] = useState<"snapshot" | "overview">("snapshot");
  const actionBy =
    timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : metaData?.action_by ||
      timelineData.action_user_name ||
      timelineData.action_user_role ||
      "Nova AI";

  const clientName = metaData.customer_first_name || metaData.customer_name || "";
  const partnerName = metaData.partner_first_name || metaData.partner_name || "your partner";

  // Normalize to string[]: new API sends array; legacy sends comma-separated string
  const casePriorityDataItems: string[] = (() => {
    const raw = metaData.case_priority_data;
    if (Array.isArray(raw)) return raw.map((s) => (typeof s === "string" ? s.trim() : String(s))).filter(Boolean);
    if (typeof raw === "string") return raw.split(",").map((s) => s.trim()).filter(Boolean);
    return [];
  })();
  const matterTypeKycItems: string[] = (() => {
    const raw = metaData.matter_type_kyc;
    if (Array.isArray(raw)) return raw.map((s) => (typeof s === "string" ? s.trim() : String(s))).filter(Boolean);
    if (typeof raw === "string") return raw.split(",").map((s) => s.trim()).filter(Boolean);
    return [];
  })();

  const overviewItems = (() => {
    const raw = metaData.case_ai_summary;
    if (Array.isArray(raw)) return raw.map((i: { title?: string; description?: string }) => ({ title: i?.title ?? "", description: i?.description ?? "" }));
    if (typeof raw === "string") {
      try {
        const p = JSON.parse(raw) as { title?: string; description?: string } | { title?: string; description?: string }[];
        const a = Array.isArray(p) ? p : p ? [p] : [];
        return a.map((i) => ({ title: i?.title ?? "", description: i?.description ?? "" }));
      } catch {
        return [];
      }
    }
    return [];
  })();

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
    if (metaData.match_status !== "Pending") {
      return;
    }

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
    if (metaData.match_status !== "Pending") {
      return;
    }

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

      const response: any = await api.post("/v1/case/more-details", {
        case_id: caseId,
        query_text: detailsText.trim(),
        lawyer_id: lawyerId,
      });

      if (response.success) {
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Success",
            response.message || "Your request has been submitted successfully."
          );
          toastManager.addToast(toast);
        }
      } else {
        // Handle error case
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Request Failed",
            response.message || "Failed to submit your request. Please try again."
          );
          toastManager.addToast(toast);
        }
      }

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
      toastManager.addToast(createErrorToast("Request Failed", errorMessage));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          <div className="flex gap-2">
            <i className="fas fa-folder-open text-xl mt-1"></i>
            <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
              {metaData.customer_first_name || "User"} wants you to represent them
              {metaData.case_priority === "URGENT" && (
                <i className="fas fa-exclamation-triangle text-novaCaution-500 ml-2"></i>
              )}
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <div className="bg-white sm:p-6 p-4 rounded-lg mb-4 w-full grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mt-1">
            <div className={`flex flex-col border-l-2 border-novaDarkAmber pl-2 ${metaData.case_priority === "URGENT" ? "text-novaCaution-500" : "text-novaSuccess-900"} font-semibold col-span-3`}>
              Priority : {metaData.case_priority || "Normal"}
              {metaData.case_priority === "URGENT" && casePriorityDataItems.length > 0 && (
                <ul className="text-[14px] font-normal text-novaCaution-500 pl-4 list-disc">
                  {casePriorityDataItems.map((item, idx) => (
                    <li className="text-[14px] font-normal text-novaCaution-500" key={idx}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
            <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 sm:col-span-1 col-span-3">
              <span className="text-[14px] font-semibold">Client name</span>
              <span className="text-[14px]">{metaData.customer_name || "Client name"}</span>
            </div>
            <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 sm:col-span-2 col-span-3">
              <span className="text-[14px] font-semibold">Partner's name</span>
              <span className="text-[14px]">{metaData.partner_name || "Partner's name"}</span>
            </div>
            <div className="flex flex-col">
              <div className="flex flex-col items-start pl-2 border-l-2 border-novaDarkAmber sm:col-span-1 col-span-3">
                <span className="text-[14px] font-semibold">Relationship type</span>
                <span className="text-[14px]">{metaData.relationship_type || "Relationship type"}</span>
              </div>
            </div>
            <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 sm:col-span-2 col-span-3">
              <span className="text-[14px] font-semibold">Case type</span>
              <ul className="text-[14px] list-disc pl-5">
                {matterTypeKycItems.map((item, idx) => (
                  <li key={idx}>{replacePlaceholders(item, clientName, partnerName)}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="max-w-full 2xl:max-w-[65%] md:max-w-[70%]">
            {/* <p className="text-[16px] leading-6 text-novaNeutral-700 mb-4">
              {metaData.customer_first_name || "User"} would like you to advise them with regards to "{metaData.matter_type_kyc || "legal matters"}" in their {metaData.relationship_type || "relationship"} with {metaData.partner_name || "their partner"}.
            </p> */}
            <p className="text-[16px] leading-6 text-novaNeutral-700 mb-4">
              Please let us know within one working day if you’d like to accept {metaData.customer_first_name || "client"}'s request to book a consultation or if you’re not interested in this case. Their case summary and details are included below.
            </p>
          </div>

          <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
            <div className="text-[24px] font-semibold text-[#1A1425]">
              {metaData.customer_first_name || "User"} & {metaData.partner_first_name || "Partner"}
            </div>

            <div className="text-[16px] text-[#3A3B40] mt-1 mb-4">
              {metaData.resolve_title || "Resolve title"}
            </div>

            {/* Rate section: Consultation fee*/}
             {metaData.strategic_advice_consultation && (
              <div className="flex-1 pl-2 border-l-2 border-novaDarkAmber">
                <div className="text-[16px] font-medium text-novaNeutral-600">Strategic Advice Consultation</div>
                <div className="text-[16px] text-novaNeutral-500 mt-0.5">
                  {metaData.strategic_advice_consultation
                    ? formatCurrency("pound", metaData.strategic_advice_consultation)
                    : "—"} (inc VAT & disbursements)
                </div>
              </div>
            )}
            <div className="flex flex-col sm:flex-row gap-2 mt-4">
              <FormButton
                variant="custom"
                className={
                  `min-h-[52px] min-w-[230px] transition-colors duration-150 ` +
                  (metaData.match_status === "Declined"
                    ? "bg-novaNeutral-300 text-novaNeutral-500 cursor-not-allowed"
                    : metaData.match_status !== "Pending" ? "bg-novaSuccess-900 text-white cursor-not-allowed font-medium" : "bg-novaSuccess-900 text-white font-medium")
                }
                disabled={metaData.match_status === "Declined" || isInterestSubmitting || (metaData.action_buttons.raise_interest === false && metaData.match_status === "Pending")}
                onClick={handleInterestClick}
              >
                {isInterestSubmitting ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-1"></i>
                    Loading...
                  </>
                ) : (
                  <>
                    {metaData.match_status === "Interested" ? 
                      <i className="fas fa-clipboard-check mr-2"></i> : 
                      <i className="fa-solid  fa-hand-paper mr-2"></i>
                    }
                    {metaData.match_status === "Interested" ? "Accepted" : "Accept"}
                  </>
                )}
              </FormButton>
              <FormButton
                variant="custom"
                className={
                  `min-h-[52px] min-w-[230px] transition-colors duration-150 ` +
                  (metaData.match_status === "Interested"
                    ? "bg-novaNeutral-300 text-novaNeutral-500 cursor-not-allowed font-medium"
                    : metaData.match_status === "Declined"
                      ? "bg-novaDarkOrange text-white border-none cursor-not-allowed font-medium"
                      : "bg-transparent border-2 border-novaDarkOrange text-novaDarkOrange font-medium")
                }
                disabled={metaData.match_status === "Interested" || (metaData.action_buttons.decline_match === false && metaData.match_status === "Pending")}
                onClick={handleDeclineClick}
              >
                <i
                  className={`fas fa-times mr-2 ${
                    metaData.match_status === "Interested"
                      ? "text-novaNeutral-500"
                      : metaData.match_status === "Declined"
                        ? "text-white"
                        : "text-novaDarkOrange group-hover:text-white"
                  }`}
                ></i>
                {metaData.match_status === "Declined" ? "Declined" : "Decline"}
              </FormButton>
            </div>

            <div className="text-xs text-novaNeutral-500 mt-3">
              Submitted {formatTimestamp(metaData.timestamp)} – Response required within one working day
            </div>

            <div className="flex flex-col md:flex-row-reverse pt-2 mr-0 3xl:mr-16 mb-4 gap-2">
              <div className="w-full md:w-[70%] 2xl:-mt-10 mt-4 gap-2">
                {/* Tabs: Snapshot | Overview */}
                <div className="flex gap-2 mb-3 sm:justify-end justify-center">
                  <button
                    type="button"
                    onClick={() => setCaseSummaryTab("snapshot")}
                    className={`px-6 py-2 text-sm rounded-full border border-novaBlack transition-colors ${
                      caseSummaryTab === "snapshot"
                        ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] text-white border-transparent"
                        : "border border-novaPrimary-500 text-novaPrimary-500 sm:hover:bg-gradient-to-r sm:hover:from-[#FF6A42] sm:hover:to-[#FC3C3F] sm:hover:text-white sm:hover:border-transparent"
                    }`}
                  >
                    Snapshot
                  </button>
                  <button
                    type="button"
                    onClick={() => setCaseSummaryTab("overview")}
                    className={`px-6 py-2 text-sm rounded-full border border-novaBack transition-colors ${
                      caseSummaryTab === "overview"
                        ? "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] text-white border-transparent"
                        : "border border-novaPrimary-500 text-novaPrimary-500 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white hover:border-transparent"
                    }`}
                  >
                    Overview
                  </button>
                </div>

                {/* Tab content: Snapshot = two-column table (question | answer) from case_summary array */}
                {caseSummaryTab === "snapshot" && (
                  <div className="rounded-lg border border-novaDarkAmber overflow-hidden bg-white">
                    {(() => {
                      const raw = metaData.case_summary;
                      let items: LawyerMatchCaseSummaryItem[] = [];

                      if (Array.isArray(raw)) {
                        items = raw.map((item) => ({
                          question: item.question ?? "",
                          answer: item.answer ?? "",
                        }));
                      } else if (typeof raw === "string") {
                        try {
                          const parsed = JSON.parse(raw) as LawyerMatchCaseSummaryItem[];
                          if (Array.isArray(parsed)) {
                            items = parsed.map((item) => ({
                              question: item.question ?? "",
                              answer: item.answer ?? "",
                            }));
                          }
                        } catch {
                          // ignore
                        }
                      }

                      if (items.length === 0) {
                        return (
                          <p className="text-sm text-novaNeutral-500 py-4 text-center">
                            No snapshot available.
                          </p>
                        );
                      }

                      const renderAnswer = (answer: string | string[] | undefined): React.ReactNode => {
                        if (answer === "" || answer == null) return "—";
                        if (Array.isArray(answer)) {
                          const filtered = answer.filter((s): s is string => typeof s === "string" && s.length > 0);
                          return filtered.length === 0 ? "—" : filtered.join(", ");
                        }
                        return typeof answer === "string" ? answer : String(answer);
                      };

                      return (
                        <table className="w-full border-collapse">
                          <thead>
                            <tr className="bg-novaInactive border-b border-novaDarkAmber">
                              <th className="text-left text-[14px] font-semibold text-novaNeutral-900 p-3 border-r border-novaDarkAmber w-[40%]">
                                Question
                              </th>
                              <th className="text-left text-[14px] font-semibold text-novaNeutral-900 p-3">
                                Answer
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {items.map((item, idx) => (
                              <tr key={idx} className="border-b border-novaDarkAmber last:border-b-0">
                                <td className="text-[14px] font-semibold text-novaNeutral-900 p-3 border-r border-novaDarkAmber align-top">
                                  {replacePlaceholders(item.question, clientName, partnerName)}
                                </td>
                                <td className="text-[14px] text-novaNeutral-700 p-3 align-top">
                                  {renderAnswer(item.answer)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      );
                    })()}
                  </div>
                )}

                {/* Tab content: Overview = title/description from case_ai_summary */}
                {caseSummaryTab === "overview" && (
                  overviewItems.length === 0 ? (
                    <p className="text-sm text-novaNeutral-500 py-4 text-center">No overview available.</p>
                  ) : (
                    <div className="flex flex-col">
                      {overviewItems.map((item, idx) => (
                        <div key={idx} className="flex flex-col">
                          <span className="text-[16px] font-semibold">{item.title}</span>
                          <span className="text-[15px] text-novaNeutral-700 mt-1 mb-6">{item.description}</span>
                        </div>
                      ))}
                    </div>
                  )
                )}
              </div>
              <div className="w-full sm:w-[50%] md:w-[40%] mt-3 gap-2">
                <span className="text-[16px] font-semibold">Client details</span>
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Reference number</span>
                  <span className="text-[14px]">{metaData.case_number || "N/A"}</span>
                </div>
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Consultation type</span>
                  <span className="text-[14px]">{metaData.preferred_consultation_method || "N/A"}</span>
                </div>
                {/* <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Current court proceedings</span>
                  <span className="text-[14px]">{metaData.current_court_proceedings || "Court proceedings"}</span>
                </div> */}
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Income before tax</span>
                  <span className="text-[14px]">{metaData.income_before_tax || "Income not available"}</span>
                </div>
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Additional support required?</span>
                  <span className="text-[14px]">{metaData.additional_support || "N/A"}</span>
                </div>
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Email address</span>
                  <span className="text-[14px] w-full break-words">{metaData.email_address || "N/A"}</span>
                </div>
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Gender</span>
                  <span className="text-[14px]">{metaData.gender || "N/A"}</span>
                </div>

                {/* <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Features relevant to children</span>
                  {metaData.features_relevant_to_children?.includes("|") ? (
                    <ul className="list-disc pl-5 text-[14px]">
                      {metaData.features_relevant_to_children.split("|").map((item, idx) => (
                        <li key={idx}>{item.trim()}</li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-[14px]">{metaData.features_relevant_to_children || "Features not available"}</span>
                  )}
                </div> */}
                {/* <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Features relevant to relationship</span>
                  {metaData.features_relevant_to_relationship?.includes("|") ? (
                    <ul className="list-disc pl-5 text-[14px]">
                      {metaData.features_relevant_to_relationship.split("|").map((item, idx) => (
                        <li key={idx}>{item.trim()}</li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-[14px]">{metaData.features_relevant_to_relationship || "Features not available"}</span>
                  )}
                </div>
                <div className="flex flex-col border-l-2 border-novaDarkAmber pl-2 mt-3">
                  <span className="text-[14px] font-semibold">Relationship activities</span>
                  {metaData.relationship_activities?.includes("|") ? (
                    <ul className="list-disc pl-5 text-[14px]">
                      {metaData.relationship_activities.split("|").map((item, idx) => (
                        <li key={idx}>{item.trim()}</li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-[14px]">{metaData.relationship_activities || "Activities not available"}</span>
                  )}
                </div> */}

                <div className="flex flex-col gap-2 mt-3 md:max-w-[250px]">
                  {action_buttons?.ask_more_details && (
                    <FormButton
                      variant="outline"
                      className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-sm h-10"
                      onClick={handleAskMoreDetailsClick}
                    >
                      <i className="fas fa-question-circle text-sm"></i>
                      <span>Request more info</span>
                    </FormButton>
                  )}
                  {action_buttons?.view_resolve && (
                    <FormButton
                      variant="outline"
                      size="custom"
                      className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-sm h-10"
                      disabled={resolveLoading}
                      onClick={handleViewResolveClick}
                    >
                      {resolveLoading ? (
                        <>
                          <i className="fas fa-spinner fa-spin text-sm"></i>
                          <span className="">Loading...</span>
                        </>
                      ) : (
                        <>
                          <i className="fas fa-eye text-sm"></i>
                          <span className="">Recommendation Details</span>
                        </>
                      )}
                    </FormButton>
                  )}
                  {action_buttons?.view_kyc && (
                    <FormButton
                      variant="outline"
                      size="custom"
                      className="inline-flex items-center justify-center gap-1 sm:gap-2 whitespace-nowrap text-sm h-10"
                      disabled={kycLoading}
                      onClick={handleViewKycClick}
                    >
                      {kycLoading ? (
                        <>
                          <i className="fas fa-spinner fa-spin text-sm"></i>
                          <span className="">Loading...</span>
                        </>
                      ) : (
                        <>
                          <i className="fas fa-clipboard-check text-sm"></i>
                          <span className="inline lg:hidden xl:inline">
                            Alignment Check Details
                          </span>
                          <span className="hidden lg:inline xl:hidden">Alignment Check</span>
                        </>
                      )}
                    </FormButton>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
        <p className="text-xs text-novaNeutral-500 flex items-center">
            <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
            <span>{formatTimestamp(metaData.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>

      {/* Modal for Request More Details */}
      <GlobalModalWrapper
        isOpen={isModalOpen}
        onClose={isSubmitting ? () => { } : handleModalClose}
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
              className="inline-flex items-center justify-center gap-2 text-[15px] border border-novaNeutral-300 bg-white hover:border-novaBlack hover:bg-novaBlack hover:text-white h-10 px-5 py-2 text-novaNeutral-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
            >
              Cancel
            </FormButton>
            <FormButton
              variant="custom"
              size="custom"
              onClick={handleSubmitRequest}
              disabled={isSubmitting || !detailsText.trim()}
              className={`inline-flex items-center justify-center gap-2 text-[15px] h-10 px-5 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${isSubmitting || !detailsText.trim()
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
