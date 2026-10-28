import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { TimelineItemType } from "@/lib/types";

interface TimelineContextType {
  timelineData: TimelineItemType[];
  setTimelineData: (data: TimelineItemType[]) => void;
  navigateToTimelineType: (type: string) => void;
  setNavigateHandler: (handler: (type: string) => void) => void;
  /** Call to refetch timeline (e.g. after KYC submit). No-op if no handler registered. */
  refreshTimeline: () => void;
  setRefreshTimelineHandler: (handler: (() => void) | null) => void;
  /** Call to refetch case details (e.g. after Review Profiles / Send from card). Updates sticky action bar. */
  refreshCaseDetails: () => void;
  setRefreshCaseDetailsHandler: (handler: (() => void) | null) => void;
  effectiveRole: string;
  setEffectiveRole: (role: string) => void;
}

export const TimelineContext = createContext<TimelineContextType | undefined>(undefined);

export const TimelineProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [timelineData, setTimelineData] = useState<TimelineItemType[]>([]);
  const [navigateHandler, setNavigateHandler] = useState<((type: string) => void) | null>(null);
  const [refreshTimelineHandler, setRefreshTimelineHandlerState] = useState<(() => void) | null>(null);
  const [refreshCaseDetailsHandler, setRefreshCaseDetailsHandlerState] = useState<(() => void) | null>(null);
  const [effectiveRole, setEffectiveRole] = useState<string>("");

  const navigateToTimelineType = useCallback((type: string) => {
    if (navigateHandler) {
      navigateHandler(type);
    }
  }, [navigateHandler]);

  const refreshTimeline = useCallback(() => {
    refreshTimelineHandler?.();
  }, [refreshTimelineHandler]);

  const setRefreshTimelineHandler = useCallback((handler: (() => void) | null) => {
    setRefreshTimelineHandlerState(() => handler);
  }, []);

  const refreshCaseDetails = useCallback(() => {
    refreshCaseDetailsHandler?.();
  }, [refreshCaseDetailsHandler]);

  const setRefreshCaseDetailsHandler = useCallback((handler: (() => void) | null) => {
    setRefreshCaseDetailsHandlerState(() => handler);
  }, []);

  return (
    <TimelineContext.Provider
      value={{
        timelineData,
        setTimelineData,
        navigateToTimelineType,
        setNavigateHandler: (handler) => setNavigateHandler(() => handler),
        refreshTimeline,
        setRefreshTimelineHandler,
        refreshCaseDetails,
        setRefreshCaseDetailsHandler,
        effectiveRole,
        setEffectiveRole,
      }}
    >
      {children}
    </TimelineContext.Provider>
  );
};

export const useTimeline = () => {
  const context = useContext(TimelineContext);
  if (!context) {
    throw new Error("useTimeline must be used within a TimelineProvider");
  }
  return context;
};
