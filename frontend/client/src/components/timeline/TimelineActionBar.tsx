import React from "react";
import { CaseDetailsActionButtons } from "@/lib/types";
import { FormButton } from "@/utils/formComponents";
interface TimelineActionBarProps {
  actionButtons?: CaseDetailsActionButtons;
  onActionClick?: (action: string) => void;
  loading?: boolean;
  sidebarVisible?: boolean;
}

export function TimelineActionBar({
  actionButtons,
  onActionClick,
  loading = false,
  sidebarVisible = true,
}: TimelineActionBarProps) {
  // Don't render if no action buttons or all are false/undefined
  if (!actionButtons) return null;

  const activeButtons = Object.entries(actionButtons).filter(
    ([_, value]) => value === true
  );

  if (activeButtons.length === 0) return null;

  const handleClick = (action: string) => {
    if (onActionClick) {
      onActionClick(action);
    }
  };

  const getButtonConfig = (action: string) => {
    switch (action) {
      case "send_to_customer":
        return {
          label: "Review and Send Profiles",
          icon: "users",
          color: "bg-novaBlue-600 hover:bg-novaBlue-700",
        };
      case "review_profiles":
        return {
          label: "Invite Experts",
          icon: "eye",
          color: "bg-novaBlue-500 hover:bg-novaBlue-700",
        };
    //   case "raise_interest":
    //     return {
    //       label: "Raise Interest",
    //       icon: "hand-paper",
    //       color: "bg-novaSuccess-600 hover:bg-novaSuccess-700",
    //     };
      default:
        return {
          label: action.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
          icon: "arrow-right",
          color: "bg-novaNeutral-500 hover:bg-novaNeutral-700",
        };
    }
  };

  return (
    <div className={`fixed bottom-0 left-0 right-0 ${sidebarVisible ? 'xl:right-[24rem]' : ''} z-40 bg-white shadow-[0_-4px_6px_0px_rgba(0,0,0,0.1)] border-novaGray-100`}>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center py-4 gap-4 justify-end">
          <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
            {activeButtons.map(([action]) => {
              const config = getButtonConfig(action);
              return (
                <FormButton
                  key={action}
                  onClick={() => handleClick(action)}
                  disabled={loading}
                  className={`inline-flex items-center px-3 py-2 sm:px-4 sm:py-2 border border-transparent text-xs sm:text-sm shadow-sm text-white ${config.color} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-novaBlue-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {loading ? (
                    <>
                      <i className="fas fa-spinner fa-spin mr-2"></i>
                      <span>Loading...</span>
                    </>
                  ) : (
                    <>
                      <i className={`fas fa-${config.icon} mr-2`}></i>
                      <span>{config.label}</span>
                    </>
                  )}
                </FormButton>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TimelineActionBar;

