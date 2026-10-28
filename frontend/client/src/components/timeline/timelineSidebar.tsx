import React, { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  CaseDetailsData,
  CaseSummaryItem,
} from "@/lib/types";
import { createSuccessToast, createErrorToast, toastManager } from "@/utils/toasts";
import { api } from "@/lib/api";
import { useRole } from "@/contexts/RoleContext";
import { FormButton } from "@/utils";

interface TimelineSidebarProps {
  caseId?: string;
  className?: string;
  caseDetails: CaseDetailsData | null;
  loading?: boolean;
  headerActions?: React.ReactNode;
  caseSummary?: CaseSummaryItem[];
  /** Callback to refetch case details after generating AI summary (navigator only). */
  onCaseDetailsRefresh?: () => void | Promise<void>;
}

export function TimelineSidebar({
  caseId,
  className = "",
  caseDetails,
  loading = false,
  headerActions,
  onCaseDetailsRefresh,
}: TimelineSidebarProps) {

  const { currentRole } = useRole();

  const summaryFromProps = useMemo(
    () => caseDetails?.case_summary?.summary ?? [],
    [caseDetails?.case_summary?.summary]
  );

  const [summaryData, setSummaryData] = useState<CaseSummaryItem[]>(summaryFromProps);
  const [summaryDraft, setSummaryDraft] = useState<CaseSummaryItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [newItemIndices, setNewItemIndices] = useState<Set<number>>(new Set());
  const baselineSummaryRef = useRef<CaseSummaryItem[]>([]);
  const lastInsertedIndexRef = useRef<number | null>(null);
  const inputRefs = useRef<Map<number, HTMLInputElement>>(new Map());

  const areSummariesEqual = (a: CaseSummaryItem[], b: CaseSummaryItem[]) => {
    if (a.length !== b.length) return false;
    return a.every((item, i) => item.title === b[i].title && item.description === b[i].description);
  };

  const hasChanges = useMemo(() => {
    if (!isModalOpen) return false;
    return !areSummariesEqual(summaryDraft, baselineSummaryRef.current);
  }, [summaryDraft, isModalOpen]);

  const isNavigator = currentRole.toLowerCase() === "navigator";
  const isAiSummaryGenerated = caseDetails?.is_ai_summary_generated === true;
  const showEditButton = isNavigator && isAiSummaryGenerated;
  const showReloadButton = isNavigator && caseDetails?.is_ai_summary_generated === false;

  const handleGenerateAiSummary = async () => {
    if (!caseId || !onCaseDetailsRefresh) return;
    setIsGeneratingSummary(true);
    try {
      await api.post("/v1/case/generate-ai-summary", { case_id: caseId });
      toastManager.addToast(
        createSuccessToast("Success", "AI summary generation started. Refreshing case details.")
      );
      await onCaseDetailsRefresh();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: { message?: string } } } })?.response?.data?.detail?.message ||
        "Failed to generate AI summary. Please try again.";
      toastManager.addToast(createErrorToast("Error", message));
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  useEffect(() => {
    if (!isModalOpen && !hasChanges) {
      setSummaryData(summaryFromProps);
    }
  }, [summaryFromProps, isModalOpen, hasChanges]);

  const handleOpenModal = () => {
    const initial = summaryData.length ? summaryData : summaryFromProps;
    setSummaryDraft(initial);
    baselineSummaryRef.current = initial;
    setNewItemIndices(new Set());
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleSummaryChange = (index: number, key: keyof CaseSummaryItem, value: string) => {
    setSummaryDraft((prev) =>
      prev.map((item, idx) => (idx === index ? { ...item, [key]: value } : item))
    );
  };

  const handleAddRow = () => {
    setSummaryDraft((prev) => {
      const next = [...prev, { title: "", description: "" }];
      const newIndex = next.length - 1;
      lastInsertedIndexRef.current = newIndex;
      setNewItemIndices((prevIndices) => new Set(prevIndices).add(newIndex));
      return next;
    });
  };

  const handleDeleteRow = (index: number) => {
    setSummaryDraft((prev) => prev.filter((_, idx) => idx !== index));
    setNewItemIndices((prevIndices) => {
      const newSet = new Set<number>();
      prevIndices.forEach((idx) => {
        if (idx < index) {
          newSet.add(idx);
        } else if (idx > index) {
          newSet.add(idx - 1);
        }
        // Skip the deleted index
      });
      return newSet;
    });
  };

  const isValidSummary = useMemo(() => {
    // Only validate new items that were added in this session
    return Array.from(newItemIndices).every((index) => {
      const item = summaryDraft[index];
      return item && item.title.trim() !== "" && item.description.trim() !== "";
    });
  }, [summaryDraft, newItemIndices]);

  const handleUpdate = async () => {
    setIsSaving(true);
    try {
      const payload = {
        case_id: caseId,
        case_summary: summaryDraft,
      };

      await api.put("/v1/case/summary", payload);

      setSummaryData(summaryDraft);
      setNewItemIndices(new Set());
      setIsModalOpen(false);

      toastManager.addToast(
        createSuccessToast("Success", "Case summary updated successfully.")
      );
    } catch (error) {
      console.error("Error updating case summary:", error);
      // Optionally handle errors, e.g., show a toast or alert
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className={`bg-white sm:space-y-6 space-y-4 p-4 ${className}`}
    >
        {headerActions && <div className="mb-4">{headerActions}</div>}
        {/* Case Summary Card */}
        <div className="rounded-lg p-4 sm:p-6 summary-card-border">
          <div className="flex items-center mb-1 justify-between">
            {/* Document/Summary Icon */}
            <div className="flex items-center">
              <i className="fas fa-file-alt mr-2"></i>
              <h3 className="text-base sm:text-lg font-semibold text-novaNeutral-900">
                Case Summary
              </h3>
            </div>
            {showEditButton && (
              <button
                type="button"
                onClick={handleOpenModal}
                className="flex items-center justify-end transition-colors"
                aria-label="Edit case summary"
              >
                <i className="fas fa-pencil-alt mr-2"></i>
              </button>
            )}
            {showReloadButton && (
              <button
                type="button"
                onClick={handleGenerateAiSummary}
                disabled={isGeneratingSummary}
                className="flex items-center justify-end transition-colors disabled:opacity-60"
                aria-label="Retry case summary"
                title="Retry case summary"
              >
                <i className={`fas fa-arrow-rotate-right ${isGeneratingSummary ? "animate-spin" : ""}`}></i>
              </button>
            )}
          </div>
          
          <hr className="block border-b mb-6" />
          {loading ? (
            <div className="text-xs sm:text-sm text-novaNeutral-600 leading-relaxed">
              Loading case summary...
            </div>
          ) : summaryData && summaryData.length > 0 ? (
            <div className="gap-5 flex flex-col">
              {summaryData.map((item, index) => (
                item.description && (
                  <div key={index} className="">
                    <p className="text-sm font-medium text-novaNeutral-700 mb-1 leading-relaxed">
                      {item.title}
                    </p>
                    <div 
                      className="text-sm text-black leading-relaxed border-l-2 border-novaDarkOrange pl-4 p-1"
                      dangerouslySetInnerHTML={{ __html: item.description }}
                    />
                  </div>
                )
              ))}
            </div>
          ) : (
            <div className="text-xs sm:text-sm text-novaNeutral-600 leading-relaxed">
              No case summary available.
            </div>
          )}
        </div>

      {isModalOpen &&
        typeof document !== "undefined" &&
        createPortal(
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80 px-4 sm:px-6">
            <div className="w-full max-w-2xl overflow-hidden rounded-lg border border-novaDarkAmber bg-white/95 shadow-2xl">
              <div className="flex items-start justify-between border-b border-novaDarkAmber px-5 py-4 sm:px-6">
                <div>
                  <h4 className="text-lg font-semibold text-novaNeutral-900">
                    Edit Case Summary
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full text-novaNeutral-400 transition-colors hover:bg-novaNeutral-100 hover:text-novaNeutral-600"
                  aria-label="Close case summary editor"
                >
                  <i className="fas fa-times text-base"></i>
                </button>
              </div>

              <div className="max-h-[60vh] overflow-y-auto px-5 py-5 sm:px-6 sm:py-6">
                <div className="flex flex-col gap-4 sm:gap-5">
                  {summaryDraft.length > 0 ? (
                    summaryDraft.map((item, index) => (
                      <div
                        key={`summary-row-${index}`}
                        className="group rounded-2xl border border-novaActive bg-novaInactive px-4 py-3 shadow-sm transition  hover:shadow-md"
                      >
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
                          <div className="flex-1">
                            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-novaNeutral-400">
                              Title
                            </label>
                            <input
                              type="text"
                              value={item.title}
                              ref={(element) => {
                                if (element) {
                                  inputRefs.current.set(index, element);
                                  if (index === lastInsertedIndexRef.current) {
                                    element.focus();
                                    lastInsertedIndexRef.current = null;
                                  }
                                } else {
                                  inputRefs.current.delete(index);
                                }
                              }}
                              onChange={(event) =>
                                handleSummaryChange(index, "title", event.target.value)
                              }
                              placeholder="Add a heading"
                              className="w-full rounded-xl border border-novaActive bg-white/80 px-3 py-2 text-sm text-novaNeutral-900 placeholder:text-novaNeutral-300 focus:border-novaPrimary-200 focus:outline-none focus:ring-2 focus:ring-novaPrimary-100"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => handleDeleteRow(index)}
                            className="inline-flex h-10 items-center justify-center gap-2 self-start rounded-full border border-transparent bg-transparent px-3 text-sm font-medium text-novaNeutral-500 transition hover:text-novaNeutral-700"
                            aria-label={`Delete summary entry ${index + 1}`}
                          >
                            <i className="fas fa-trash text-sm text-novaDarkOrange hover:text-novaNeutral-700"></i>
                          </button>
                        </div>
                        <div className="mt-3">
                          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-novaNeutral-400">
                            Description
                          </label>
                          <textarea
                            value={item.description}
                            onChange={(event) =>
                              handleSummaryChange(index, "description", event.target.value)
                            }
                            placeholder="Add a description"
                            rows={5}
                            className="w-full resize-none rounded-xl border border-novaActive bg-white/80 px-3 py-2 text-sm text-novaNeutral-800 placeholder:text-novaNeutral-300 focus:border-novaPrimary-200 focus:outline-none focus:ring-2 focus:ring-novaPrimary-100"
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-2xl border border-dashed border-novaNeutral-200 bg-white/70 px-4 py-6 text-center text-sm text-novaNeutral-500">
                      No summary entries yet. Add your first highlight below.
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-4 border-t border-novaNeutral-100 px-5 py-4 sm:px-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <FormButton 
                  variant="primary"
                  onClick={handleAddRow}
                  >
                    <i className="fas fa-plus mr-2"></i>
                    Add another highlight
                  </FormButton>
                  <div className="flex items-center justify-end gap-2">
                    <FormButton
                      variant="custom"
                      className="text-novaNeutral-500 border border-novaBlack hover:text-novaNeutral-700 hover:bg-novaBlack hover:border-novaBlack hover:text-white"
                      onClick={handleCloseModal}
                    >
                      Cancel
                    </FormButton>
                    <FormButton
                      variant="gradient"
                      onClick={handleUpdate}
                      disabled={isSaving || !hasChanges || (newItemIndices.size > 0 && !isValidSummary)}
                      loadingText={isSaving ? "Saving..." : "Save changes"}
                    >
                      {isSaving ? <><i className="fas fa-spinner fa-spin mr-2"></i>Saving...</> :<><i className="fas fa-save mr-2"></i> Save changes</>}
                    </FormButton>
                  </div>
                </div>
                {hasChanges && newItemIndices.size > 0 && !isValidSummary && (
                  <p className="text-xs text-novaNeutral-500 text-center sm:text-right">
                    <i className="fas fa-exclamation-circle mr-1"></i>
                    Please fill new summary entries to save changes
                  </p>
                )}
              </div>
            </div>
          </div>,
          document.body
        )}

      {/* Resolve Session Card */}
      {/* <div className="bg-white border border-novaNeutral-200 rounded-lg p-3 sm:p-4 shadow-sm">
          <div className="flex flex-col mb-4 space-y-3">
            <div className="flex items-center">
              <div className="w-5 h-5 sm:w-6 sm:h-6 bg-novaSuccess-700 rounded flex text-white items-center justify-center mr-2 sm:mr-3 flex-shrink-0">
              <i className="fas fa-file-alt"></i>
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-novaNeutral-900">
                Resolve Session
              </h3>
            </div>
            <div className="flex flex-col sm:justify-between space-y-2 sm:space-y-4">
              <div className="text-xs sm:text-sm text-novaNeutral-600">
                Current Status
                <span className="ml-2 inline-flex items-center px-2 py-0.5 sm:px-2.5 rounded-full text-xs font-medium bg-novaSuccess-100 text-novaSuccess-800">
                  Submitted
                </span>
              </div>
              <button className="inline-flex w-full justify-center items-center px-2 py-1 sm:px-3 sm:py-1.5 border border-transparent text-xs sm:text-sm font-medium rounded-md shadow-sm text-white bg-novaSuccess-700 hover:bg-novaSuccess-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-novaSuccess-500">
                <i className="fas fa-file-alt mr-2"></i>
                <span>Resolve Details</span>
              </button>
            </div>
          </div>

          <div className="mb-4">
            <h4 className="text-sm sm:text-md font-semibold text-novaNeutral-800 mb-2">
              Session Details
            </h4>
            <p className="text-xs sm:text-sm text-novaNeutral-600 mb-2">Contract Dispute</p>
            <p className="text-xs sm:text-sm text-novaNeutral-600">
              Completion Date: <span className="font-medium">9/28/2025</span>
            </p>
            <p className="text-xs sm:text-sm text-novaNeutral-600">
              Questions Answered:{" "}
              <span className="font-medium">12 questions completed</span>
            </p>
            <p className="text-xs sm:text-sm text-novaNeutral-600">
              Resolve ID: <span className="font-medium">resolve-001</span>
            </p>
          </div>
        </div> */}

      {/* Mini Engage Session Card */}
        {/* <div className="bg-white border border-novaNeutral-200 rounded-lg p-4 shadow-sm">
          <div className="flex flex-col mb-4 space-y-3">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-novaPurple-500 rounded flex text-white items-center justify-center mr-3">
              <i className="fas fa-clipboard-check"></i>
              </div>
              <h3 className="text-lg font-semibold text-novaNeutral-900">
                Mini Engage Session
              </h3>
            </div>
            <div className="flex flex-col sm:justify-between space-y-2 sm:space-y-4">
              <div className="text-sm text-novaNeutral-600">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-novaPurple-100 text-novaPurple-800">
                  Completed
                </span>
              </div>
              <button className="inline-flex w-full justify-center items-center px-2 py-1 sm:px-3 sm:py-1.5 border border-transparent text-xs sm:text-sm font-medium rounded-md shadow-sm text-white bg-novaPurple-600 hover:bg-novaPurple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-novaPurple-500">
                <i className="fas fa-clipboard-check mr-2"></i>
                <span>Mini Engage Details</span>
              </button>
            </div>
          </div>

          <div className="mb-4">
            <h4 className="text-sm sm:text-md font-semibold text-novaNeutral-800 mb-2">
              Session Details
            </h4>
            <p className="text-xs sm:text-sm text-novaNeutral-600 mb-2">Family Law Matter</p>
            <p className="text-xs sm:text-sm text-novaNeutral-600">
              Start Date: <span className="font-medium">10/15/2025</span>
            </p>
            <p className="text-xs sm:text-sm text-novaNeutral-600">
              Progress:{" "}
              <span className="font-medium">3 of 8 questions completed</span>
            </p>
            <p className="text-xs sm:text-sm text-novaNeutral-600">
              Mini Engage ID: <span className="font-medium">221002</span>
            </p>
          </div>
        </div> */}

      {/* Parties Involved Card */}
      <div className="rounded-lg p-3 sm:p-6 mb-6 summary-card-border">
        <div className="flex items-center mb-1">
          {/* Paw Print Icon */}
            {/* <svg
              className="w-3 h-3 sm:w-6 sm:h-6 text-novaPrimary-500 mr-2"
              fill="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path d="M16 11c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 3-1.34 3-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C17 14.17 12.33 13 10 13zm8 0c-.29 0-.62.02-.97.05C17.16 13.41 19 14.28 19 15.5V19h5v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
            </svg> */}
            <i className="fas fa-users mr-2"></i>
          <h3 className="text-base sm:text-lg font-semibold text-novaNeutral-900">
            Parties Involved
          </h3>
        </div>
        <hr className="block border-b mb-6" />
        {loading ? (
          <div className="text-xs sm:text-sm text-novaNeutral-600">
            Loading parties information...
          </div>
        ) : caseDetails?.parties_involved ? (
          <div className="gap-5 flex flex-col">
            {/* Client Section */}
            <div>
              <p className="text-sm font-medium text-novaNeutral-700 mb-1">Client</p>
              <div className="border-l-2 border-novaDarkOrange pl-4 p-1">
              <p className="text-sm text-black">
                {caseDetails.parties_involved.client_name}
              </p>
              <p className="text-sm text-black break-all"
                style={{ wordBreak: 'break-all', overflowWrap: 'anywhere' }}
                title={caseDetails.parties_involved.client_email}
              >
                {caseDetails.parties_involved.client_email}
              </p>
              {caseDetails.parties_involved.client_phone && (
                <p className="text-sm text-black">
                  {caseDetails.parties_involved.client_phone}
                </p>
              )}
              </div>
            </div>
            
            {/* Opposing Party Section */}
            {caseDetails.parties_involved.partner_name && (
              <div>
                <p className="text-sm font-medium text-novaNeutral-700 mb-1">Opposing Party</p>
                <div className="border-l-2 border-novaDarkOrange pl-3 p-2">
                <p className="text-sm text-black">
                  {caseDetails.parties_involved.partner_name}
                </p>
                </div>
              </div>
            )}
            
            {/* Assigned To Section */}
            {caseDetails.parties_involved.lawyer_name && (
              <div>
                <p className="text-sm font-medium text-novaNeutral-700 mb-1">Assigned To</p>
                <div className="border-l-2 border-novaDarkOrange pl-3 p-2">
                <p className="text-sm text-black">
                  {caseDetails.parties_involved.lawyer_name}
                </p>
                <p
                  className="text-sm text-black break-all"
                  style={{ wordBreak: 'break-all', overflowWrap: 'anywhere' }}
                  title={caseDetails.parties_involved.lawyer_email}
                >
                  {caseDetails.parties_involved.lawyer_email}
                </p>
                {caseDetails.parties_involved.lawyer_phone && (
                  <p className="text-sm text-black">
                    {caseDetails.parties_involved.lawyer_phone}
                  </p>
                )}
              </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs sm:text-sm text-novaNeutral-600">
            No parties information available.
          </div>
        )}
      </div>
{/* 
      {caseId && (
        <div className="mb-4 p-3 bg-novaNeutral-50 rounded-lg">
          <p className="text-xs text-novaNeutral-500 mb-1">Case ID</p>
          <p className="text-sm font-mono text-novaNeutral-800">{caseId}</p>
        </div>
      )} */}
    </div>
  );
}

export default TimelineSidebar;
