import React from "react";
import CalendarIcon from "@/assets/ui/calendar.svg";
import UserIcon from "@/assets/ui/user.svg";
import { useRole } from "@/contexts/RoleContext";
import { Link } from "wouter";
import { formatTimestamp } from "@/utils/formatedDate";

interface Customer {
  first_name: string;
  last_name: string;
  email: string;
  id: string;
}

interface CaseItem {
  id: string;
  case_no: string;
  case_type: string;
  priority: string;
  status: string;
  start_date: string;
  created_at: string;
  title?: string | null;
  customer: Customer | null;
  tags?: string[] | null;
}

interface CaseDashCardProps {
  item: CaseItem;
}

export const CaseDashCard: React.FC<CaseDashCardProps> = ({ item }) => {
  const { currentRole } = useRole();

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "open":
        return "bg-novaSuccess-50 text-novaSuccess-700 border border-novaSuccess-50";
      case "closed":
        return "bg-novaGray-50 text-novaGray-700 border border-novaGray-50";
      case "in progress":
        return "bg-novaPrimary-50 text-novaPrimary-700 border border-novaPrimary-50";
      case "pending":
        return "bg-novaWarning-50 text-novaWarning-700 border border-novaWarning-50";
      case "archived":
        return "bg-novaViolet-50 text-novaViolet-700 border border-novaViolet-50";
      default:
        return "bg-novaGray-50 text-novaGray-700 border border-novaGray-50";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "high":
        return "bg-novaCaution-50 text-novaCaution-700 border border-novaCaution-50";
      case "medium":
        return "bg-novaAlert-50 text-novaAlert-700 border border-novaAlert-50";
      case "low":
        return "bg-novaSuccess-50 text-novaSuccess-700 border border-novaSuccess-50";
      default:
        return "bg-novaGray-50 text-novaGray-700 border border-novaGray-50";
    }
  };

  const getTagColor = (tag: string) => {
    switch (tag.toLowerCase()) {
      case "kyc_completed":
        return "bg-novaBlue-50 text-novaBlue-700";
      case "match_confirmed":
        return "bg-novaSuccess-50 text-novaSuccess-700";
      case "lawyer_assigned":
        return "bg-novaPurple-50 text-novaPurple-700";
      case "initial_payment_completed":
        return "bg-novaAccent-50 text-novaAccent-700";
      case "onboarding_completed":
        return "bg-novaViolet-50 text-novaViolet-700";
      case "profile_card_sent":
        return "bg-novaActive text-novaDarkOrange";
      default:
        return "bg-novaGray-50 text-novaGray-700";
    }
  };

  const formatTagLabel = (tag: string) => {
    if (tag.toLowerCase() === "kyc_completed") {
      return "Alignment Check";
    } else if (tag.toLowerCase() === "lawyer_assigned") {
      return "Expert Assigned";
    }
    return tag
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const showStatus = item.status.toLowerCase() !== "open";
  const showPriority = item.priority.toLowerCase() !== "high";

  return (
    <Link href={`/case/${item.id}`} className="h-full block">
      <div className="h-full group relative rounded-xl bg-white overflow-hidden transition-all duration-500 ease-out hover:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.12)] shadow-[0_2px_8px_rgb(0,0,0,0.04)] hover:-translate-y-2 hover:scale-[1.02] border border-novaGray-100 hover:border-novaPrimary-200">
        {/* Subtle accent bar */}
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-novaPrimary-400 via-novaPrimary-500 to-novaPrimary-600 opacity-0 group-hover:opacity-100 transition-all duration-500" />

        <div className="h-full p-4 sm:p-5 flex flex-col">
          {/* Header Section */}
          <div className="flex flex-row items-start justify-between mb-3 gap-3 flex-wrap">
            <div className="flex-1 min-w-0">
              <h3 className="font-bold m-0 p-0 break-words text-novaGray-900 group-hover:text-novaPrimary-600 transition-all duration-500 tracking-tight leading-tight mb-1.5 text-base sm:text-md">
                <span
                  className="block truncate"
                  style={{ whiteSpace: "normal" }}
                  title={
                    item.customer && item.customer.first_name
                      ? `${item.customer.first_name} ${item.customer.last_name}`
                      : item.title
                      ? item.title
                      : item.case_no
                  }
                >
                  {item.customer && item.customer.first_name
                    ? `${item.customer.first_name
                        .charAt(0)
                        .toUpperCase()}${item.customer.first_name
                        .slice(1)
                        .toLowerCase()} ${
                        item.customer.last_name
                          ? item.customer.last_name
                              .charAt(0)
                              .toUpperCase() +
                            item.customer.last_name
                              .slice(1)
                              .toLowerCase()
                          : ""
                      }`
                    : item.title
                    ? item.title
                    : item.case_no}
                </span>
              </h3>
            </div>

            {/* Status and Priority Section - Top Right */}
            <div className="flex flex-col gap-1.5 text-right ml-2 flex-shrink-0 items-end justify-start">
              {showStatus && (
                <span
                  className={`
                    inline-flex items-center px-1.5 py-1 max-w-fit rounded-full text-[10px] font-semibold tracking-wide uppercase
                    ${getStatusColor(item.status)}
                  `}
                > 
                  {item.status.toLowerCase()}
                </span>
              )}
              {showPriority && (
                <span
                  className={`
                    inline-flex items-center px-2.5 py-1 max-w-fit rounded-full text-[10px] font-semibold tracking-wide uppercase
                    ${getPriorityColor(item.priority)}
                  `}
                >
                  {item.priority.toLowerCase()} priority
                </span>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="space-y-3 mb-3 flex-grow">
            {/* Tags Section */}
            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {item.tags.map((tag, index) => (
                  <span
                    key={`${tag}-${index}`}
                    className={`
                      inline-flex items-center px-3 py-1 rounded-full text-xs
                      ${getTagColor(tag)}
                    `}
                  >
                    {formatTagLabel(tag)}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Footer Section */}
          <div className="flex flex-row items-center justify-between gap-2 pt-3 border-t border-novaGray-100 mt-auto">
            <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
              {/* Minimal case number */}
              <span className="text-novaGray-400 text-xs ml-2 whitespace-nowrap">
                {/* {new Date(item.created_at).toLocaleDateString("en-GB", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })} */}
                {formatTimestamp(item.created_at)}
              </span>
            </div>
            {/* Always render the arrow icon on the right */}
            <div className="flex-shrink-0 ml-auto">
            <span className="text-novaGray-700 font-medium text-xs whitespace-nowrap">
                {typeof item.case_no === "string" && item.case_no.startsWith("CASE-")
                  ? item.case_no.slice(5)
                  : item.case_no}
              </span>
              {/* <svg
                className="w-5 h-5 text-novaGray-400 opacity-60 group-hover:opacity-100 group-hover:text-novaPrimary-600 group-hover:translate-x-1 transition-all duration-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M9 5l7 7-7 7"
                />
              </svg> */}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
};
