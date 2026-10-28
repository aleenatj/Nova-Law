import React, { useState } from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface LawyerBadgeProps {
  lawyer: string | { name: string; photo_url?: string };
}

function LawyerBadge({ lawyer }: LawyerBadgeProps) {
  const isObjectFormat = typeof lawyer === 'object';
  const lawyerName = isObjectFormat ? lawyer.name : lawyer;
  const lawyerPhoto = isObjectFormat ? lawyer.photo_url : null;
  const [imageError, setImageError] = useState(false);

  return (
    <span className="text-novaNeutral-900 bg-[#fff1df] px-1 py-1 rounded-full text-sm flex items-center gap-2">
      {isObjectFormat && (
        <>
          {lawyerPhoto && !imageError ? (
            <img 
              src={lawyerPhoto} 
              alt={lawyerName}
              className="w-8 h-8 rounded-full object-cover border border-novaDarkOrange"
              onError={() => setImageError(true)}
            />
          ) : (
            <span
              className="w-8 h-8 flex items-center justify-center rounded-full border border-novaDarkOrange"
              title={lawyerName}
            >
              <i className="fa-solid fa-user text-novaDarkOrange text-sm"></i>
            </span>
          )}
        </>
      )}
      <span className="text-novaNeutral-900 mr-2">{lawyerName}</span>
    </span>
  );
}

interface ExpertNotInterestedV1Props {
  timelineData: {
    action_user_name: string;
    meta_data: {
      case_number: string;
      customer_name: string;
      timestamp: string;
      action_by?: string;
      lawyer_names: string[] | Array<{ name: string; photo_url?: string }>;
      deadline_hours: number;
      action_buttons: {
        view_resolve: boolean;
      };
    };
    created_at: string;
    version: number;
  };
  isLatest?: boolean;
}

export function ExpertNotInterestedV1({ timelineData, isLatest }: ExpertNotInterestedV1Props) {
  const [resolveData, setResolveData] = useState<Record<string, any>>({});
  const [resolveLoading, setResolveLoading] = useState(false);
  const [isResolveDetailsOpen, setIsResolveDetailsOpen] = useState(false);

  const lawyers = (timelineData?.meta_data?.lawyer_names || []);

  const actionBy =
    timelineData?.meta_data?.action_by ||
    timelineData.action_user_name ||
    DEFAULT_ACTION_BY;

  return (
    <>
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          <div className="flex gap-2">
            <i className="fas fa-user-tie text-xl mt-1"></i>
            <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
              Expert not interested
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            The following experts have not expressed interest in supporting {timelineData.meta_data.customer_name} within the required {timelineData.meta_data.deadline_hours}-hour timeframe for case <strong className="text-[#1A1425]">{timelineData.meta_data.case_number}</strong>.
          </p>

          <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
            <div className="flex flex-wrap gap-2">
              {lawyers && lawyers.length > 0 ? (
                lawyers.map((lawyer, index) => (
                  <LawyerBadge key={index} lawyer={lawyer} />
                ))
              ) : (
                <span className="text-sm text-novaNeutral-400 italic">
                  No experts notified
                </span>
              )}
            </div>
          </div>
          <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            You can review the details provided and continue matching with other suitable Nova Experts as needed.
          </p>
          <p className="text-xs flex items-center">
            <i className="fas fa-clock text-xs mr-1"></i>
            <span>{formatTimestamp(timelineData.meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>
        </div>
      </div>
    </>
  );
}

export default ExpertNotInterestedV1;
