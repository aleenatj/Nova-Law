import React, { useMemo, useState } from "react";
import { TimelineItemType } from "@/lib/types";
import { getTimelineNavigation } from "@/config/timelineNavigation";

interface TimelineNavigationMenuProps {
  timelineData: TimelineItemType[];
  onNavigate: (timelineType: string) => void;
  role: string;
  currentUserRole?: string;
  className?: string;
  isCollapsible?: boolean;
  defaultCollapsed?: boolean;
}

export const TimelineNavigationMenu: React.FC<TimelineNavigationMenuProps> = ({
  timelineData,
  onNavigate,
  role,
  currentUserRole,
  className = "",
  isCollapsible = false,
  defaultCollapsed = true,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  // Get navigation items for the current role
  const navigationItems = useMemo(() => {
    const items = getTimelineNavigation(role);
    return Array.isArray(items) ? items : [];
  }, [role]);

  // Get unique timeline types present in the data
  const presentTimelineTypes = useMemo(() => {
    const types = new Set<string>();
    timelineData.forEach((item) => {
      if (item.timeline_type_name) {
        types.add(item.timeline_type_name);
        // Also add section-specific types if the base type is case_pathway_overview
        if (item.timeline_type_name === "case_pathway_overview") {
          types.add("case_pathway_overview_section_2");
          types.add("case_pathway_overview_section_3");
        }
      }
    });
    return types;
  }, [timelineData]);

  // Check if navigation items array is empty
  if (!navigationItems || navigationItems.length === 0) {
    return null;
  }

  const isCustomer = role.toLowerCase() === "customer";
  const isLawyer = role.toLowerCase() === "lawyer";
  const isNavigator = currentUserRole?.toLowerCase() === "navigator";
  
  // If navigator is viewing as customer or lawyer, make it toggleable
  const shouldBeToggleable = isNavigator && (isCustomer || isLawyer);
  const shouldShowCollapsible = (isCollapsible || shouldBeToggleable) && !(isCustomer && !shouldBeToggleable);
  const shouldShowItems = !shouldShowCollapsible || !isCollapsed;

  return (
    <div className={`${className}`}>
      <style>
        {`
          .timeline-nav-menu::-webkit-scrollbar {
            width: 6px;
          }
          .timeline-nav-menu::-webkit-scrollbar-thumb {
            background: #e4e5e9;
            border-radius: 6px;
          }
          .timeline-nav-menu::-webkit-scrollbar-track {
            background: transparent;
          }
        `}
      </style>
      <div className="border-b border-novaNeutral-100 pb-2 mb-2">
        {/* Collapsible Header - Hide for customers */}
        {shouldShowCollapsible && (
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="w-full flex items-center justify-between px-5 py-2 text-sm font-medium text-novaNeutral-700 hover:bg-novaNeutral-50 rounded-md transition-colors"
          >
            <span>Timeline Navigation</span>
            <i
              className={`fas fa-chevron-${isCollapsed ? "down" : "up"} text-xs transition-transform`}
            ></i>
          </button>
        )}

        {/* Navigation Items - Always visible for customers */}
        {shouldShowItems && (
          <nav className={`space-y-1 ${shouldShowCollapsible ? "px-2" : ""} timeline-nav-menu`} style={{ maxHeight: shouldShowCollapsible ? "none  " : "none", overflowY: shouldShowCollapsible ? "auto" : "visible" }}>
            {navigationItems.map((item) => {
              const isPresent = presentTimelineTypes.has(item.type);
              return (
                <button
                  key={item.type}
                  onClick={() => isPresent && onNavigate(item.type)}
                  disabled={!isPresent}
                  className={`
                    w-full min-h-10 text-left px-5 py-2 rounded-full text-xs transition-colors
                    flex items-center gap-2
                    ${
                      isPresent
                        ? "text-novaNeutral-600 hover:text-novaBlack hover:bg-novaNeutral-50 cursor-pointer group"
                        : "text-novaNeutral-400 cursor-not-allowed opacity-50"
                    }
                  `}
                  title={isPresent ? `Navigate to ${item.title}` : `${item.title} - Not yet available`}
                >
                  {item.icon.startsWith('fas ') || item.icon.startsWith('fa ') ? (
                    <i
                      className={`
                        ${item.icon} text-sm w-3 flex-shrink-0 
                        ${isPresent ? 'text-novaPrimary-600 group-hover:text-novaBlack' : ''}
                        transition-colors mr-2
                      `}
                    ></i>
                  ) : (
                    <img 
                      src={item.icon} 
                      alt="" 
                      className={`text-sm w-4 h-4 flex-shrink-0 mr-1 object-contain transition-all ${
                        isPresent 
                          ? 'opacity-100 group-hover:text-novaBlack' 
                          : 'opacity-50'
                      }`}
                    />
                  )}
                  <span className="truncate text-[14px]">{item.title}</span>
                </button>
              );
            })}
          </nav>
        )}
      </div>
    </div>
  );
};
