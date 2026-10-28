import React, { useState } from "react";
import { createPortal } from "react-dom";
import { TimelineItemType } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

type SummaryItem = {
  title?: string;
  description?: string;
};

type CaseSummaryMetaData = {
  action_by?: string;
  case_number?: string;
  case_type?: string;
  current_case_summary?: SummaryItem[];
  previous_case_summary?: SummaryItem[];
  timestamp?: string;
};

interface CaseSummaryUpdateProps {
  timelineData: TimelineItemType;
  isLatest?: boolean;
}

const renderSummarySection = (items: SummaryItem[]) => {
  if (!items.length) {
    return (
      <p className="text-xs text-novaNeutral-500">
        No summary available.
      </p>
    );
  }

  return (
    <div className="gap-4 flex flex-col">
      {items.map((item, index) => {
        const key = `${item?.title || "summary"}-${index}`;
        return (
          <div key={key} className="bg-white rounded-lg p-3">
            {item?.title && (
              <p className="text-sm font-semibold text-novaNeutral-900 mb-1">
                {item.title}
              </p>
            )}
            {item?.description ? (
              <p className="text-sm text-novaNeutral-700 leading-relaxed whitespace-pre-line">
                {item.description}
              </p>
            ) : (
              <p className="text-xs text-novaNeutral-500">
                No description provided.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
};

const CaseSummaryUpdate: React.FC<CaseSummaryUpdateProps> = ({ timelineData, isLatest }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const metaData: CaseSummaryMetaData = timelineData?.meta_data || {};

  const previousSummary = Array.isArray(metaData.previous_case_summary)
    ? metaData.previous_case_summary
    : [];

  const currentSummary = Array.isArray(metaData.current_case_summary)
    ? metaData.current_case_summary
    : [];

  const actionBy =
    metaData.action_by ||
    timelineData.action_user_name ||
    timelineData.action_user_role ||
    DEFAULT_ACTION_BY;

  const timestamp = metaData.timestamp || timelineData.created_at;

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-file-contract text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Case summary {previousSummary.length > 0 ? "updated" : "created"}
          </span>
        </div>

        <hr className="block border-t border-novaDarkAmber my-3" />

        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          The case summary for <strong className="text-[#1A1425]">{metaData.case_number || "this case"}</strong> has been {previousSummary.length > 0 ? "updated" : "created"}.
        </p>

        <div className="mb-4">
          <FormButton
            variant="primary"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors"
          >
            <i className="fas fa-eye"></i>
            View Summary Details
          </FormButton>
        </div>

        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {previousSummary.length > 0 ? `${actionBy}${timelineData?.action_user_role?.toLowerCase() === "navigator" ? " (Nova Navigator)" : ""}` : DEFAULT_ACTION_BY}</span>
        </p>

        <SummaryModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          previousSummary={previousSummary}
          currentSummary={currentSummary}
        />
      </div>
    </div>
  );
};

export default CaseSummaryUpdate;

const SummaryModal = ({
  isOpen,
  onClose,
  previousSummary,
  currentSummary,
}: {
  isOpen: boolean;
  onClose: () => void;
  previousSummary: SummaryItem[];
  currentSummary: SummaryItem[];
}) => {
  if (!isOpen || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80 px-4">
      <div className="bg-white w-full max-w-3xl rounded-lg shadow-lg p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <i className="fas fa-file-contract text-novaDarkOrange"></i>
            <h4 className="text-base sm:text-lg font-semibold text-novaNeutral-900">
              Summary Details
            </h4>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-novaNeutral-500 hover:text-novaNeutral-700 transition-colors"
            aria-label="Close summary details"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div
          className={
            previousSummary.length > 0
              ? "grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto pr-1"
              : "max-h-[60vh] overflow-y-auto pr-1"
          }
        >
          {previousSummary.length > 0 ? (
            <>
              <div className="space-y-3">
                <p className="sticky top-0 z-10 text-xs font-semibold text-novaNeutral-500 uppercase tracking-wide bg-white py-2">
                  Previous Summary
                </p>
                {renderSummarySection(previousSummary)}
              </div>
              <div className="space-y-3">
                <p className="sticky top-0 z-10 text-xs font-semibold text-novaNeutral-500 uppercase tracking-wide bg-white py-2">
                  Current Summary
                </p>
                {renderSummarySection(currentSummary)}
              </div>
            </>
          ) : (
            <div className="space-y-3">
              <p className="sticky top-0 z-10 text-xs font-semibold text-novaNeutral-500 uppercase tracking-wide bg-white py-2">
                Current Summary
              </p>
              {renderSummarySection(currentSummary)}
            </div>
          )}
        </div>

        <div className="flex justify-end border-t border-novaNeutral-100 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center px-4 py-2 text-sm text-novaNeutral-700 border border-novaNeutral-500 hover:bg-novaPrimary-50 rounded-full transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};


