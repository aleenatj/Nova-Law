import React, { useCallback, useEffect, useState } from "react";
import { Layout } from "@/components";
import { useRole } from "@/contexts/RoleContext";
import { useLocation } from "wouter";
import DataNotFound from "@/components/ui/data-not-found/DataNotFound";
import { api, tokenManager } from "@/lib/api";
import { createErrorToast, toastManager } from "@/utils/toasts";

const BASE_API_URL = import.meta.env.PUBLIC_ENV__BASE_API_URL as string;
import { Pagination } from "@/utils/pagination";
import { FormButton } from "@/utils/formComponents";
import { formatTimestamp } from "@/utils/formatedDate";
import { engageFeedbackContent } from "@/config/engageFeedbackContent";

interface EngageFeedbackItem {
  id: string;
  time_value_feedback: string | null;
  completion_time: string | null;
  session_count: string | null;
  help_level: string | null;
  helper_type: string[] | null;
  help_reason: string[] | null;
  preparedness_level: string | null;
  age_range: string | null;
  gender: string | null;
  gender_other: string | null;
  overall_experience: string | null;
  improvement_feedback: string | null;
  recommendation_score: string | null;
  created_at: string;
}

/** Get detail row label from engageFeedbackContent (full question title + optional subtitle), or fixed labels for non-questions. */
function getDetailLabel(key: string): string {
  if (key === "created_at") return "Created At";
  if (key === "improvement_feedback") {
    const withImprovement = engageFeedbackContent.questions.find(
      (q) => q.showImprovementTextArea && (q.improvementPromptPositive || q.improvementPromptNegative)
    );
    if (withImprovement?.improvementPromptPositive)
      return withImprovement.improvementPromptPositive;
    if (withImprovement?.improvementPromptNegative)
      return withImprovement.improvementPromptNegative;
    return "Improvement feedback";
  }
  const q = engageFeedbackContent.questions.find((question) => question.id === key);
  if (!q) return key;
  return q.subtitle ? `${q.title} (${q.subtitle})` : q.title;
}

/** Left table keys (created_at first, then first half of questions in order). */
const DETAIL_KEYS_LEFT: (keyof EngageFeedbackItem)[] = [
  "created_at",
  "time_value_feedback",
  "completion_time",
  "session_count",
  "help_level",
  "helper_type",
  "help_reason",
];

/** Right table keys (second half of questions in order, then updated_at). */
const DETAIL_KEYS_RIGHT: (keyof EngageFeedbackItem)[] = [
  "preparedness_level",
  "age_range",
  "gender",
  "overall_experience",
  "recommendation_score",
  "improvement_feedback",
];

function getDetailValue(row: EngageFeedbackItem, key: keyof EngageFeedbackItem): string {
  const v = row[key];
  if (v == null) return "—";
  if (Array.isArray(v)) return v.length ? v.join(", ") : "—";
  if (key === "created_at") return formatTimestamp(v as string) || "—";
  return String(v);
}

interface EngageFeedbackListResponse {
  success: boolean;
  message: unknown[];
  data: {
    total_count: number;
    records_in_page: number;
    items: EngageFeedbackItem[];
  };
}

const LIMIT = 12;

export default function EngageFeedbackListPage() {
  const [items, setItems] = useState<EngageFeedbackItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [endDate, setEndDate] = useState<string>(() =>
    new Date().toISOString().slice(0, 10)
  );
  const [exporting, setExporting] = useState(false);
  const { currentRole } = useRole();
  const [, setLocation] = useLocation();

  const today = new Date().toISOString().slice(0, 10);

  const fetchFeedback = useCallback(
    async (page: number = 1) => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: LIMIT.toString(),
          order_by: "created_at",
          order_dir: "desc",
        });
        if (startDate) params.set("start_date", startDate);
        if (endDate) params.set("end_date", endDate);
        const response = (await api.get(
          `/v1/engage-feedback?${params}`
        )) as EngageFeedbackListResponse;

        if (response?.success && response?.data) {
          setItems(response.data.items ?? []);
          setTotalCount(response.data.total_count ?? 0);
          setTotalPages(
            Math.max(1, Math.ceil((response.data.total_count ?? 0) / LIMIT))
          );
          setCurrentPage(page);
        } else {
          setItems([]);
          setTotalCount(0);
          setTotalPages(1);
        }
      } catch (err) {
        console.error("Error fetching engage feedback:", err);
        toastManager.addToast(
          createErrorToast("Error", "Failed to load feedback list")
        );
        setItems([]);
        setTotalCount(0);
        setTotalPages(1);
      } finally {
        setLoading(false);
      }
    },
    [startDate, endDate]
  );

  useEffect(() => {
    if (currentRole && currentRole.toLowerCase() === "navigator") {
      fetchFeedback(1);
    }
  }, [currentRole, fetchFeedback]);

  useEffect(() => {
    if (
      currentRole &&
      currentRole !== "Guest" &&
      currentRole.toLowerCase() !== "navigator"
    ) {
      setLocation("/case-dashboard");
    }
  }, [currentRole, setLocation]);

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      fetchFeedback(page);
    }
  };

  const handleApplyDateFilter = () => {
    fetchFeedback(1);
  };

  const handleClearDateFilter = () => {
    setStartDate("");
    setEndDate("");
  };

  const hasDateFilter = startDate || endDate;

  const handleExportCsv = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams({
        order_by: "created_at",
        order_dir: "desc",
      });
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      const token = tokenManager.getAccessToken();
      const url = `${BASE_API_URL}/v1/engage-feedback/export?${params}`;
      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Export failed (${response.status})`);
      }
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      // Use same filename as backend: engage-feedback plus selected date range
      let downloadFilename = "engage-feedback.csv";
      if (startDate && endDate) {
        downloadFilename = `engage-feedback-${startDate}-to-${endDate}.csv`;
      } else if (startDate) {
        downloadFilename = `engage-feedback-${startDate}-to.csv`;
      } else if (endDate) {
        downloadFilename = `engage-feedback-to-${endDate}.csv`;
      }
      a.download = downloadFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Export CSV failed:", err);
      toastManager.addToast(
        createErrorToast("Export failed", err instanceof Error ? err.message : "Could not export CSV")
      );
    } finally {
      setExporting(false);
    }
  };

  const toggleRowExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  if (currentRole?.toLowerCase() === "guest" || !currentRole) {
    return (
      <Layout
        headerTitle="Engage Feedback"
        headerSubtitle="View 60-second feedback submissions"
      >
        <div className="py-16">
          <DataNotFound
            message="Data Not Found"
            hint="You must be signed in to view this page."
          />
        </div>
      </Layout>
    );
  }

  const headerActions = (
    <FormButton
      size="sm"
      variant="custom"
      className="text-gray-600 hover:text-gray-800 flex items-center justify-center px-2 py-1 text-xs sm:text-sm"
      onClick={() => fetchFeedback(currentPage)}
      disabled={loading}
    >
      <span className="flex items-center justify-center w-full">
        <i className={`fas fa-refresh ${loading ? "animate-spin" : ""}`}></i>
        <span className="hidden sm:inline ml-2">Refresh</span>
      </span>
    </FormButton>
  );

  return (
    <Layout
      headerTitle="Engage Feedback"
      headerSubtitle="View 60-second feedback submissions from users"
      headerActions={headerActions}
    >
      <div className="bg-novaInactive h-full flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 flex-1 w-full">
                <div className="bg-white rounded-md border border-novaActive p-3 w-full">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-6 h-6 bg-white rounded-md flex items-center justify-center border border-novaActive">
                        <i className="fas fa-comment-dots text-novaDarkOrange text-xs"></i>
                      </div>
                    </div>
                    <div className="ml-3">
                      <p className="text-xs font-medium text-novaNeutral-500">
                        Total feedback
                      </p>
                      <p className="text-lg font-semibold text-novaNeutral-900 break-words">
                        {totalCount}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Date filter - stacked on mobile so native date picker aligns correctly */}
            <div className="bg-white rounded-md border border-novaActive p-3 mb-3 overflow-visible">
              <p className="text-sm font-medium text-novaNeutral-700 mb-2">
                Filter by submission date
              </p>
              <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-end gap-3">
                <div className="flex flex-col gap-1 w-full sm:w-auto sm:min-w-[140px]">
                  <label htmlFor="feedback-start-date" className="text-xs text-novaNeutral-600">
                    From date
                  </label>
                  <input
                    id="feedback-start-date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    max={endDate || today}
                    className="w-full min-w-0 px-3 py-1.5 !text-novaBlack text-sm border border-novaNeutral-300 rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 [&::-webkit-datetime-edit]:!text-novaBlack [&::-webkit-datetime-edit-year-field]:!text-novaBlack"
                  />
                </div>
                <div className="flex flex-col gap-1 w-full sm:w-auto sm:min-w-[140px]">
                  <label htmlFor="feedback-end-date" className="text-xs text-novaNeutral-600">
                    To date
                  </label>
                  <input
                    id="feedback-end-date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || undefined}
                    max={today}
                    className="w-full min-w-0 px-3 py-1.5 !text-novaBlack text-sm border border-novaNeutral-300 rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 [&::-webkit-datetime-edit]:!text-novaBlack [&::-webkit-datetime-edit-year-field]:!text-novaBlack"
                  />
                </div>
                <div className="flex-1 min-w-0 hidden sm:block" aria-hidden="true" />
                <div className="flex flex-col gap-1 w-full sm:w-auto">
                  <span className="text-xs text-transparent select-none" aria-hidden="true">
                    &nbsp;
                  </span>
                  <div className="flex gap-2">
                    {/* {hasDateFilter && (
                      <FormButton
                        type="button"
                        size="sm"
                        variant="outline"
                        className="px-3 py-1.5 text-sm rounded-md border border-novaNeutral-300 text-novaNeutral-700 hover:bg-novaNeutral-50"
                        onClick={handleClearDateFilter}
                        disabled={loading}
                      >
                        Clear dates
                      </FormButton>
                    )} */}
                    {currentRole?.toLowerCase() === "navigator" && (
                      <FormButton
                        type="button"
                        size="sm"
                        variant="gradient"
                        className="text-white px-3 py-1.5 text-sm"
                        onClick={handleExportCsv}
                        disabled={exporting || loading}
                      >
                        <span className="flex items-center justify-center gap-1.5">
                          <i className={`fas fa-download ${exporting ? "animate-pulse" : ""}`}></i>
                          {exporting ? "Exporting…" : "Export"}
                        </span>
                      </FormButton>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-md border border-novaActive overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-novaActive">
                  <thead className="bg-novaActive">
                    <tr>
                      <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[110px]">
                        created at
                      </th>
                      <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[90px]">
                        completion time
                      </th>
                      <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[90px]">
                        Preparedness level
                      </th>
                      <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[90px]">
                        Age range
                      </th>
                      <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[110px]">
                        overall experience
                      </th>
                      <th className="px-2 sm:px-3 py-2 text-left text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[90px]">
                        recommendation score
                      </th>
                      <th className="px-2 sm:px-3 py-2 text-right text-xs font-medium text-novaPrimary-600 uppercase tracking-wider min-w-[70px]">
                        More details
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-novaActive">
                    {loading ? (
                      <tr>
                        <td
                          colSpan={8}
                          className="px-3 py-8 text-center text-sm text-novaNeutral-500"
                        >
                          <div className="flex items-center justify-center">
                            <i className="fas fa-spinner fa-spin mr-2"></i>
                            Loading feedback...
                          </div>
                        </td>
                      </tr>
                    ) : items.length === 0 ? (
                      <tr>
                        <td
                          colSpan={8}
                          className="px-3 py-8 text-center text-sm text-novaNeutral-500"
                        >
                          No feedback found.
                        </td>
                      </tr>
                    ) : (
                      items.map((row) => (
                        <React.Fragment key={row.id}>
                          <tr
                            role="button"
                            tabIndex={0}
                            onClick={() => toggleRowExpand(row.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                toggleRowExpand(row.id);
                              }
                            }}
                            className="hover:bg-novaInactive transition-colors cursor-pointer"
                            aria-expanded={expandedId === row.id}
                          >
                            <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-700 whitespace-nowrap">
                              {formatTimestamp(row.created_at) || "—"}
                            </td>
                            <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-600">
                              {row.completion_time ?? "—"}
                            </td>
                            <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-600">
                              {row.preparedness_level ?? "—"}
                            </td>
                            <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-600">
                              {row.age_range ?? "—"}
                            </td>
                            <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-600">
                              {row.overall_experience ?? "—"}
                            </td>
                            <td className="px-2 sm:px-3 py-2 text-[12px] text-novaNeutral-600">
                              {row.recommendation_score ?? "—"}
                            </td>
                            <td className="px-2 sm:px-3 py-2 text-right">
                              <i
                                className={`fas fa-chevron-${expandedId === row.id ? "up" : "down"} text-sm text-novaPrimary-500`}
                                aria-hidden
                              />
                            </td>
                          </tr>
                          {expandedId === row.id && (
                            <tr className="bg-white">
                              <td colSpan={8} className="px-3 sm:px-4 py-4 border-t border-novaActive">
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                  <div className="bg-white rounded-md border border-novaActive overflow-hidden shadow-sm">
                                    <table className="min-w-full min-h-full divide-y divide-novaActive">
                                      <tbody className="divide-y divide-novaActive">
                                        {DETAIL_KEYS_LEFT.map((key) => (
                                          <tr key={key}>
                                            <th className="px-3 py-2 text-left text-xs font-medium text-novaNeutral-600 bg-novaInactive w-[45%] min-w-[140px] align-top whitespace-normal">
                                              {getDetailLabel(key)}
                                            </th>
                                            <td className="px-3 py-2 text-sm text-novaNeutral-700 bg-white align-top">
                                              {key === "gender"
                                                ? (row.gender_other
                                                  ? `${getDetailValue(row, key)} (${row.gender_other})`
                                                  : getDetailValue(row, key))
                                                : getDetailValue(row, key)}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                  <div className="bg-white rounded-md border border-novaActive overflow-hidden shadow-sm">
                                    <table className="min-w-full min-h-full divide-y divide-novaActive">
                                      <tbody className="divide-y divide-novaActive">
                                        {DETAIL_KEYS_RIGHT.map((key) => (
                                          <tr key={key}>
                                            <th className="px-3 py-2 text-left text-xs font-medium text-novaNeutral-600 bg-novaInactive w-[45%] min-w-[140px] align-top whitespace-normal">
                                              {getDetailLabel(key)}
                                            </th>
                                            <td className="px-3 py-2 text-sm text-novaNeutral-700 bg-white align-top">
                                              {key === "gender"
                                                ? (row.gender_other
                                                  ? `${getDetailValue(row, key)} (${row.gender_other})`
                                                  : getDetailValue(row, key))
                                                : getDetailValue(row, key)}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {totalCount > 0 && (
                <div className="bg-white px-4 py-3 border-t border-novaActive">
                  <Pagination
                    config={{
                      currentPage: Math.max(1, Math.min(currentPage, totalPages)),
                      totalPages: Math.max(1, totalPages),
                      totalItems: Math.max(0, totalCount),
                      itemsPerPage: LIMIT,
                      onPageChange: handlePageChange,
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
