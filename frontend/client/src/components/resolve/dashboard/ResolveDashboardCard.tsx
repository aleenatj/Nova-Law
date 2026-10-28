import { formatTimestamp } from "@/utils/formatedDate";
import React from "react";

interface Customer {
  first_name: string;
  last_name: string;
  email: string;
  id: string;
}

interface ResolveItem {
  title: string | null;
  resolve_id: string;
  case_type: string;
  resolve_status: string;
  start_date: string;
  completed_date: string | null;
  no_of_questions_answered: number;
  customer: Customer | null;
  created_at?: string | "Time not available";
}

interface ResolveDashCardProps {
  item: ResolveItem;
  onCardClick?: (resolveId: string) => void;
}

export const DEFAULT_THEME = {
  cardBg: "#FFFFFF",
  cardBorder: "#E5E7EB",
  statusBadgeBg: "#eeeeef",
  statusBadgeText: "#26262e",
  statusBadgeBorder: "#aaaaaf",
  accentFrom: "#CBD5F5",
  accentTo: "#6B728E",
  footerBorder: "#E5E7EB",
};

export const STATUS_THEMES: Record<string, typeof DEFAULT_THEME> = {
  Completed: {
    cardBg: "#e8f2ff",
    cardBorder: "transparent",
    statusBadgeBg: "#D4E6FF",
    statusBadgeText: "#4269cf",
    statusBadgeBorder: "#aec4ff",
    accentFrom: "#e5f3ff",
    accentTo: "#447EE8",
    footerBorder: "#BBD8FF",
  },
  "Moving forward": {
    cardBg: "#effff0",
    cardBorder: "transparent",
    statusBadgeBg: "#D3F0D7",
    statusBadgeText: "#206A3B",
    statusBadgeBorder: "#92d1a3",
    accentFrom: "#dcf7e3",
    accentTo: "#3B9F63",
    footerBorder: "#c0f5ce",
  },
  "In progress": {
    cardBg: "#fff9ee",
    cardBorder: "transparent",
    statusBadgeBg: "#fbf3d9d6",
    statusBadgeText: "#bd8911",
    statusBadgeBorder: "#F2D082",
    accentFrom: "#fff8c5",
    accentTo: "#ebcc5b",
    footerBorder: "#F6DE9D",
  },
};

export const ResolveDashCard: React.FC<ResolveDashCardProps> = ({ item, onCardClick }) => {
  const statusTheme = STATUS_THEMES[item.resolve_status] ?? DEFAULT_THEME;
  const formattedStartDate = new Date(item.start_date).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const formattedCompletedDate = item.completed_date
    ? new Date(item.completed_date).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  const handleCardClick = () => {
    if (onCardClick) {
      onCardClick(item.resolve_id);
    }
  };

  // Mobile: status line with date, status, answers
  const MobileStatusLine = () => (
    <div className="flex sm:hidden flex-row items-center gap-2 mt-1 text-[11px] text-novaGray-600">
      {/* <div className="flex items-center gap-1">
        <i className="fas fa-calendar-alt w-3 h-3 opacity-60 text-[10px]" />
        <span className="font-medium">{formattedStartDate}</span>
      </div> */}
      <span
        className="inline-flex items-center px-2 py-0.5 rounded-full font-semibold"
        style={{
          backgroundColor: statusTheme.statusBadgeBg,
          color: statusTheme.statusBadgeText,
          borderColor: statusTheme.statusBadgeBorder,
          textTransform: "none",
          fontSize: "10px",
          paddingTop: "2px",
          paddingBottom: "2px",
        }}
      >
        {item.resolve_status}
      </span>
      <div className="flex items-center gap-1">
        <i className="fas fa-question-circle w-3 h-3 opacity-60 text-[10px]" />
        <span className="font-medium whitespace-nowrap">
          {item.no_of_questions_answered} answered
        </span>
      </div>
    </div>
  );

  // Desktop: right column details
  const DesktopStatusDetail = () => (
    <div className="flex-col gap-1.5 text-right ml-2 flex-shrink-0 items-end justify-start hidden sm:flex">
      {/* <div className="flex items-center gap-1 text-novaGray-500">
        <i className="fas fa-calendar-alt w-3 h-3 opacity-60 text-[11px]" />
        <span className="text-[10px] font-medium">
          {formattedStartDate}
        </span>
      </div> */}
      <span
        className="inline-flex items-center px-2 py-0 max-w-fit rounded-full font-semibold text-[10px] tracking-wide border"
        style={{
          backgroundColor: statusTheme.statusBadgeBg,
          color: statusTheme.statusBadgeText,
          borderColor: statusTheme.statusBadgeBorder,
          textTransform: "none",
        }}
      >
        {item.resolve_status}
      </span>
      <div className="flex items-center gap-1 text-novaGray-500">
        <i className="fas fa-question-circle w-3 h-3 opacity-60 text-[11px]" />
        <span className="text-[10px] font-medium whitespace-nowrap">
          {item.no_of_questions_answered} answered
        </span>
      </div>
    </div>
  );

  return (
    <div
      onClick={handleCardClick}
      className="h-full group relative rounded-xl overflow-hidden transition-all duration-500 ease-out hover:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.12)] hover:-translate-y-2 hover:scale-[1.02] timeline-card-border cursor-pointer"
      style={{
        backgroundColor: statusTheme.cardBg,
        borderColor: statusTheme.cardBorder,
      }}
    >
        {/* Subtle accent bar */}
        <div
          className="absolute left-0 top-0 bottom-0 w-1 opacity-0 group-hover:opacity-100 transition-all duration-500"
          style={{
            background: `linear-gradient(180deg, ${statusTheme.accentFrom} 0%, ${statusTheme.accentTo} 100%)`,
          }}
        />
        <div className="h-full p-4 sm:p-5 flex flex-col">
          {/* Header Section */}
          <div className="flex flex-row items-start justify-between mb-3 gap-3 flex-wrap">
            <div className="flex-1 min-w-0">
              <h3 className="text-base sm:text-md font-bold m-0 p-0 break-words text-novaGray-900 group-hover:text-novaPrimary-600 transition-all duration-500 tracking-tight leading-tight mb-1.5">
                {item.title ? (
                  <span>Recommended pathway:{item.title}</span>
                ) : (
                  <span className="text-novaGray-400">No Title Available</span>
                )}
              </h3>
              {/* Show customer email below the title, if available */}
              {/* Email is now shown near name in footer */}
            </div>
            {/* Desktop (not mobile): show date/status/answered at top right */}
            <DesktopStatusDetail />
          </div>

          {/* Main Content */}
          <div className="space-y-3 mb-3 flex-grow">
            {item.created_at && <div className="flex items-center gap-1.5 text-xs text-novaBlack">
              <i className="fas fa-calendar-alt flex-shrink-0" />
              <span className="break-words">{formatTimestamp(item.created_at)}</span>
            </div>}
            {item.completed_date ? (
              <div className="flex flex-col gap-1">
                {/* Completed date message */}
                <div className="flex items-center gap-1.5 text-xs text-novaSuccess-600">
                  <i className="fas fa-check-circle w-3.5 h-3.5 flex-shrink-0" />
                  <span className="break-words font-medium">
                    Completed {formattedCompletedDate}
                  </span>
                </div>
                {/* On mobile: show row with details under the completed line */}
                <MobileStatusLine />
              </div>
            ) : null}
          </div>

          {/* Non-completed: show details just above the horizontal bar for mobile */}
          {!item.completed_date && (
            <div className="block sm:hidden mb-2">
              <MobileStatusLine />
            </div>
          )}

          {/* Non-completed: also show details above footer bar for desktop (sm+) if not already shown */}
          {/* details already shown at top right for desktop - NO need to duplicate */}

          {/* Footer Section */}
          <div
            className="flex flex-row items-center justify-between gap-2 pt-3 border-t mt-auto"
            style={{ borderColor: statusTheme.footerBorder }}
          >
            {item.customer ? (
              <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
                <div className="flex items-center justify-center w-5 h-5 rounded-full bg-novaGray-100 flex-shrink-0">
                  <i className="fas fa-user w-3 h-3 opacity-60 text-[12px]" />
                </div>
                <div className="flex flex-col min-w-0 overflow-hidden">
                  <span
                    className="overflow-hidden text-ellipsis inline-block font-medium text-novaGray-700 text-sm capitalize truncate"
                    title={`${item.customer.first_name} ${item.customer.last_name}`}
                  >
                    {item.customer.first_name} {item.customer.last_name}
                  </span>
                  <span
                    className="overflow-hidden text-ellipsis inline-block text-novaGray-500 text-[12px] truncate"
                    title={item.customer.email}
                  >
                    {item.customer.email}
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
                <div className="flex items-center justify-center w-5 h-5 rounded-full bg-novaGray-100 flex-shrink-0">
                  <i className="fas fa-user w-3 h-3 opacity-20 text-[12px]" />
                </div>
                <span className="text-novaGray-300 text-xs italic truncate">No customer assigned</span>
              </div>
            )}
            {/* Always render the arrow icon on the right */}
            <div className="flex-shrink-0 ml-auto">
              <i className="fas fa-chevron-right w-5 h-5 text-novaGray-400 opacity-60 group-hover:opacity-100 group-hover:text-novaPrimary-600 group-hover:translate-x-1 transition-all duration-500" />
            </div>
          </div>
        </div>
      </div>
  );
};