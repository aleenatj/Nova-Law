import React, { useState } from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { api } from "@/lib/api";
import { createErrorToast, toastManager } from "@/utils/toasts";
import { FormButton } from "@/utils/formComponents";
import ResolveDetailsModal from "../../../ResolveDetailsModal";

interface CaseOpenedV1Props {
  timelineData: {
    action_user_name: string;
    meta_data: {
      case_number: string;
      timestamp: string;
      action_by: string;
      resolve_id?: string;
      action_buttons: {
        view_resolve: boolean;
      };
    };
    created_at: string;
    version: number;
  };
  isLatest?: boolean;
}

export function CaseOpenedV1({ timelineData, isLatest }: CaseOpenedV1Props) {
  const [resolveData, setResolveData] = useState<Record<string, any>>({});
  const [resolveLoading, setResolveLoading] = useState(false);
  const [isResolveDetailsOpen, setIsResolveDetailsOpen] = useState(false);
  
  const actionBy =
    timelineData?.meta_data?.action_by ||
    timelineData.action_user_name ||
    DEFAULT_ACTION_BY;

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

  return (
    <>
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          <div className="flex gap-2">
            <i className="fas fa-folder-open text-xl mt-1"></i>
            <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
              New case opened
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            A new case has been created and assigned case number{" "}
            <strong className="text-[#1A1425]">{timelineData.meta_data.case_number}</strong>. The case is now
            in the system and ready for processing. The client will need to
            complete Alignment Check Form to help us understand their case better.
          </p>
          {timelineData?.meta_data?.action_buttons?.view_resolve && (
            <div className="mb-4">
              <FormButton
                variant="primary"
                className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors"
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
          <p className="text-xs flex items-center">
            <i className="fas fa-clock text-xs mr-1"></i>
            <span>{formatTimestamp(timelineData.meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>
        </div>
      </div>

      {/* Resolve Details Modal */}
      <ResolveDetailsModal
        data={resolveData}
        isOpen={isResolveDetailsOpen}
        onClose={() => setIsResolveDetailsOpen(false)}
      />
    </>
  );
}

export default CaseOpenedV1;
