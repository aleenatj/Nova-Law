import React, { useState } from "react";
import { KYCCompleteResponsePropsType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { createErrorToast, formatTimestamp, FormButton, toastManager } from "@/utils";
import KycForm from "@/components/timeline/KycForm";
import { api } from "@/lib/api";
import { useRole } from "@/contexts/RoleContext";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface KYCCompleteProps {
  timelineData: KYCCompleteResponsePropsType;
}

const KYCComplete: React.FC<KYCCompleteProps> = ({ timelineData }) => {

  const [kycLoading, setKycLoading] = useState(false);
  const [kycData, setKycData] = useState<Record<string, any>>({});
  const [isKycFormOpen, setIsKycFormOpen] = useState(false);
  const userRole = useRole();
  const {
    action_by,
    timestamp,
    status,
    customer_responses,
    action_buttons,
  } = timelineData.meta_data;
  const resolvedActionBy =
    timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : action_by || timelineData.action_user_name || DEFAULT_ACTION_BY;

  const handleViewResponses = async () => {
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

  return (
    <div className="timeline-card-border bg-novaSuccess-50 sm:p-6 p-4">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-start sm:items-center gap-2 flex-wrap mb-1">
          <div className="items-start sm:items-center gap-2 flex-wrap">
              <i className="fas fa-clipboard-check text-sm mr-2"></i>
              <span className="text-lg font-medium text-novaNeutral-900">
                "Alignment Check Form" Submitted Successfully
              </span>
            </div>
            {/* <span className="text-xs bg-novaSuccess-100 text-novaSuccess-700 px-2 py-1 rounded-full">
              {status}
            </span> */}
          </div>
          <hr className="block border-t border-novaDarkAmber my-2" />
          <p className="text-sm leading-6 text-novaNeutral-700 sm:px-0 mb-3">
            Thank you for completing the "Alignment Check Form"! Your responses
            have been submitted and will be reviewed by our legal team. We'll use
            this information to match you with the most suitable Experts.
          </p>
          <div className="bg-white rounded-lg p-3 border border-novaDarkAmber">
            <div className="flex items-start gap-2">
              <i className="hidden sm:flex fas fa-info-circle text-novaDarkOrange text-sm mt-0.5"></i>
              <div className="text-sm leading-5 text-novaNeutral-900">
                <p className="font-medium mb-1">What happens next:</p>
                <ul className="text-xs sm:text-sm space-y-1 list-disc list-inside">
                  {[
                    "Our legal team will review your responses",
                    "We'll identify most suitable Experts for your case",
                    "You'll receive Expert profiles to review",
                    "You can then choose your preferred Expert",
                  ].map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

            <FormButton
              variant="primary"
              className="text-sm mt-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
              onClick={handleViewResponses}
            >
              {kycLoading ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    Loading ...
                  </>
                ) : (
                  <>
                    <i className="fas fa-eye check mr-2"></i>
                    View Response
                  </>
                )}
            </FormButton>
          
          <div className="text-xs text-novaNeutral-500 mt-3 flex items-center gap-1">
            <i className="fas fa-clock text-novaNeutral-500 text-xs"></i>
            <span>Submitted on {formatTimestamp(timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {resolvedActionBy}</span>
          </div>

          <KycForm
            data={kycData}
            isOpen={isKycFormOpen}
            onClose={() => setIsKycFormOpen(false)}
            viewMode={true}
            caseId={timelineData?.case_id}
          />
        </div>
      </div>
    </div>
  );
};

export default KYCComplete;
