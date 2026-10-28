// Configuration for timeline card types with their display titles by role
// Order defines the sequence in the navigation menu
import pathwayIcon from "@/assets/ui/Pathway.svg";
import nextStepIcon from "@/assets/ui/NextStep.svg";

export const CUSTOMER_TIMELINE_NAVIGATION = [
  {
    type: "case_pathway_overview_section_2",
    title: "Nova recommendation",
    icon: pathwayIcon,
  },
  {
    type: "case_pathway_overview_section_3",
    title: "Alignment check",
    icon: nextStepIcon,
  },
  {
    type: "your_matched_expert",
    title: "Matching experts",
    icon: "fas fa-users",
  },  
  // {
  //   type: "talk_to_lawyer_requested",
  //   title: "Consultation requested",
  //   icon: "fas fa-comments",
  // },
  {
    type: "customer_engaged_lawyer",
    title: "Chosen expert",
    icon: "fas fa-circle-check",
  },
  {
    type: "initial_payment_requested",
    title: "Payment",
    icon: "fas fa-credit-card",
  },
  // {
  //   type: "payment_receipt",
  //   title: "Payment receipt",
  //   icon: "fas fa-receipt",
  // },
  {
    type: "complete_onboarding_assessment",
    title: "Nova Engage",
    icon: "fas fa-clipboard-list",
  },
  // {
  //   type: "onboarding_assessment_completed",
  //   title: "Assessment completed",
  //   icon: "fas fa-check-circle",
  // },
] as const;

export const LAWYER_TIMELINE_NAVIGATION = [
  {
    type: "match_found",
    title: "Match found",
    icon: "fas fa-search",
  },
  {
    type: "interest_raised",
    title: "Interest raised",
    icon: "fas fa-hand-paper",
  },
  {
    type: "case_declined",
    title: "Case declined",
    icon: "fas fa-times-circle",
  },
  {
    type: "more_details_requested",
    title: "More details requested",
    icon: "fas fa-question-circle",
  },
  {
    type: "case_awarded",
    title: "Case awarded",
    icon: "fas fa-trophy",
  },
  {
    type: "case_awarded_to_other_lawyer",
    title: "Case Missed",
    icon: "fas fa-user-times",
  },
  {
    type: "payment_completed",
    title: "Payment completed",
    icon: "fas fa-credit-card",
  },
  {
    type: "complete_onboarding_assessment",
    title: "Onboarding Assessment",
    icon: "fas fa-clipboard-check",
  },
  {
    type: "client_onboarding_completed",
    title: "Onboarding completed",
    icon: "fas fa-check-circle",
  },
] as const;

export const NAVIGATOR_TIMELINE_NAVIGATION = [
  {
    type: "case_opened",
    title: "Case opened",
    icon: "fas fa-folder-open",
  },
  {
    type: "kyc_completed",
    title: "Alignment Check",
    icon: "fas fa-id-card",
  },
  {
    type: "match_notification_send",
    title: "Lawyers notified",
    icon: "fas fa-bell",
  },
  {
    type: "interest_received",
    title: "Interest received",
    icon: "fas fa-hand-paper",
  },
  {
    type: "lawyer_declined_case",
    title: "Expert declined case",
    icon: "fas fa-times-circle",
  },
  {
    type: "complete_onboarding_assessment",
    title: "Onboarding Assessment",
    icon: "fas fa-clipboard-check",
  },

  {
    type: "client_onboarding_completed",
    title: "Onboarding completed",
    icon: "fas fa-check-circle",
  },
  {
    type: "profile_card_send",
    title: "Profile card sent",
    icon: "fas fa-id-badge",
  },
  
  {
    type: "case_awarded",
    title: "Case awarded",
    icon: "fas fa-trophy",
  },
  {
    type: "payment_completed",
    title: "Payment completed",
    icon: "fas fa-credit-card",
  },
  {
    type: "case_archived",
    title: "Case archived",
    icon: "fas fa-archive",
  },
] as const;

// Create maps for quick lookup by role
export const TIMELINE_NAVIGATION_MAP = {
  customer: CUSTOMER_TIMELINE_NAVIGATION,
  lawyer: LAWYER_TIMELINE_NAVIGATION,
  navigator: NAVIGATOR_TIMELINE_NAVIGATION,
} as const;

// Combined map for all timeline types
type TimelineNavigationItem = {
  readonly type: string;
  readonly title: string;
  readonly icon: string;
};

const ALL_TIMELINE_MAP = new Map<string, TimelineNavigationItem>([
  ...CUSTOMER_TIMELINE_NAVIGATION.map((item) => [item.type, item] as [string, TimelineNavigationItem]),
  ...LAWYER_TIMELINE_NAVIGATION.map((item) => [item.type, item] as [string, TimelineNavigationItem]),
  ...NAVIGATOR_TIMELINE_NAVIGATION.map((item) => [item.type, item] as [string, TimelineNavigationItem]),
]);

// Get navigation items for a specific role
export const getTimelineNavigation = (role: string): Array<{ type: string; title: string; icon: string }> => {
  const roleLower = role.toLowerCase();
  const items = TIMELINE_NAVIGATION_MAP[roleLower as keyof typeof TIMELINE_NAVIGATION_MAP];
  return items ? [...items] : [];
};

// Get title for a timeline type
export const getTimelineTitle = (type: string): string => {
  return ALL_TIMELINE_MAP.get(type)?.title || type;
};

// Get icon for a timeline type
export const getTimelineIcon = (type: string): string => {
  return ALL_TIMELINE_MAP.get(type)?.icon || "fas fa-circle";
};
