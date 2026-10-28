import React from "react";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { CaseArchivedTimelineProps } from "@/lib/types";
import { FormButton } from "@/utils/formComponents";

export function CaseArchived({ timelineData, isLatest }: CaseArchivedTimelineProps & { isLatest?: boolean }) {
  const actionBy = DEFAULT_ACTION_BY;
  const timestamp = timelineData.meta_data.timestamp || timelineData.created_at;
  const caseNumber = timelineData.meta_data.case_number || "N/A";
  const customerName = timelineData.meta_data.customer_name || "Unknown Customer";

  const setLocation = (newCaseId: string) => {
    window.location.href = `/case/${newCaseId}`;
  }

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fa-solid fa-file-arrow-down text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Case archived
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          Case <strong className="text-[#1A1425]">{caseNumber}</strong> for <strong className="text-[#1A1425]">{customerName}</strong> has been archived following the initiation of a new case without completion of the requisite Alignment Check process for this matter. Accordingly, this case has been designated inactive and preserved in the archive.
        </p>
        <div className="mb-4">
          <FormButton
            variant="primary"
            onClick={() => setLocation(timelineData.meta_data.new_case_id || "")}
            className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors"
          >
            <i className="fas fa-eye"></i>
            View New Case
          </FormButton>
        </div>
        <p className="text-xs text-novaNeutral-500 flex items-center">
          <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
          <span>{formatTimestamp(timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
}

export default CaseArchived;

