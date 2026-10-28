export interface CaseAwardResponsePropsType {
  action_by: string;
  timestamp: string;
  case_number: string;
  customer_name: string;
  case_type: string;
}

// Base timeline item structure
export interface TimelineItemType {
  action_user_id: string;
  action_user_name: string;
  action_user_role: string;
  case_id: string;
  created_at: string;
  id: string;
  meta_data: any;
  notify_user_id: string;
  notify_user_name: string;
  timeline_type_id: string;
  timeline_type_name: string;
  updated_at: string;
  version: number;
}

// KYC specific meta data structure
export interface KYCMetaDataType {
  action_by: string;
  timestamp: string;
  status: string;
  customer_responses: Record<string, string>;
  kyc_id?: string;
  action_buttons: {
    approve: boolean;
    reject: boolean;
    escalate: boolean;
  };
}

// Updated KYC response type that matches the actual data structure
export interface KYCCompleteResponsePropsType extends TimelineItemType {
  meta_data: KYCMetaDataType;
}

// Profile card send specific meta data structure
export interface LawyerProfile {
  lawyer_name: string;
  name?: string;
  lawyer_photo_url: string;
  photo_url?: string;
  photo_urls?: {
    thumbnail: string;
    medium: string;
    large: string;
  };
  experience: string | number;
  about?: string;
  lawyer_about?: string;
  city?: string;
  county?: string;
  country?: string;
  accredited_specialisations?: string;
  accredited_specialisms?: string[];
  expert_types?: string[];
  expertises?: string[];
  relationship_types?: string[];
  matter_types?: string[];
  hourly_rate?: number;
  charge_first_consultation?: number;
  lawfirms?: Array<{
    id: string;
    name: string;
  }>;
}

export interface ProfileCardSendMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_profiles: LawyerProfile[];
  action_buttons: Record<string, any>;
}

export interface ProfileCardSendResponsePropsType extends TimelineItemType {
  meta_data: ProfileCardSendMetaDataType;
}

export interface ProfileCardSendTimelineProps {
  timelineData: ProfileCardSendResponsePropsType;
}

// Case Opened specific meta data structure
export interface CaseOpenedMetaDataType {
  status: string;
  case_number: string;
  resolve_id: string;
  case_type: string;
  next_steps: string;
  detailed_summary: string;
  summary: string;
  timestamp: string;
  action_buttons: {
    kyc_form: boolean;
    view_resolve: boolean;
  };
}

// Law Firm Types
export interface LawFirm {
  id: string;
  name: string;
  contact_person: string;
  contact_no: string;
  contact_email: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  logo: string;
  logos?: {
    thumbnail: string;
    medium: string;
    large: string;
  };
  about: string;
  website_url: string;
  engage_form_url: string;
  law_firm_type: "Solo practitioner" | "Boutique" | "Multi-speciality";
  status?: "Active" | "Inactive";
  created_at: string;
  updated_at: string;
}

export interface LawFirmFormData {
  name: string;
  contact_person: string;
  contact_no?: string;
  contact_email: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  logo: string;
  about: string;
  website_url: string;
  engage_form_url: string;
  law_firm_type: string;
  status?: "Active" | "Inactive";
}

export interface LawFirmApiResponse {
  success: boolean;
  message: string[];
  data: {
    law_firms: LawFirm[];
    records_in_page: number;
    total_count: number;
  };
}

// Lawyer Types - Aligned with API schemas
export interface Lawyer {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  gender: string;
  gender_other?: string;
  status: "Active" | "Inactive";
  address_line_1?: string;
  address_line_2?: string;
  city?: string;
  county?: string;
  country?: string;
  postal_code?: string;
  reg_no?: string;
  sra_number?: string;
  bar_number?: string;
  regulator?: string;
  regulator_other?: string | null;
  admitted_date_solicitor?: string;
  called_date_barrister?: string;
  admitted_date_cliex?: string;
  joined_at?: string;
  left_at?: string;
  about?: string;
  photo_urls?: {
    large: string;
    medium: string;
    thumbnail: string;
  };
  linkedin_url?: string;
  hourly_rate?: number;
  charge_first_consultation?: number;
  accredited_specialisms?: string[];
  accreditations?: string[];
  accredited_specialism_other?: string[] | null;
  conflict_level_disinclination?: "Medium conflict" | "High Conflict" | "Implacable hostility";
  pi_insurance?: string;
  testimonial?: string;
  expert_types?: string[];
  expert_types_all?: string[];
  expert_types_other?: string | null;
  relationship_types?: string[];
  expertises?: string[];
  expertises_all?: string[];
  matter_types?: string[];
  dr_preferences?: string[];
  user_id?: string;
  experience?: string;
  created_at?: string;
  updated_at?: string;
  lawfirm_id?: string;
  needs_password_setup?: boolean;
  lawfirms?: {
    id: string;
    name: string;
    logos?: {
      large: string;
      medium: string;
      thumbnail: string;
    }
  } | null;
}

// Form data for creating/editing lawyers
export interface LawyerFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  gender?: string | null;
  gender_other?: string | null;
  status: "Active" | "Inactive";
  address_line_1?: string | null;
  address_line_2?: string | null;
  city?: string | null;
  county?: string | null;
  country?: string | null;
  postal_code?: string | null;
  reg_no?: string | null;
  sra_number?: string | null;
  bar_number?: string | null;
  regulator?: string | null;
  regulator_other?: string | null;
  admitted_date_solicitor?: string | null;
  called_date_barrister?: string | null;
  admitted_date_cliex?: string | null;
  joined_at?: string | null;
  left_at?: string | null;
  about?: string | null;
  photo_url?: string | null;
  linkedin_url?: string | null;
  hourly_rate?: number | null;
  charge_first_consultation?: number | null;
  accredited_specialisms?: string[] | null;
  accredited_specialism_other?: string[] | null;
  conflict_level_disinclination?: "Medium conflict" | "High Conflict" | "Implacable hostility" | null;
  pi_insurance?: string | null;
  testimonial?: string | null;
  expert_types?: string[];
  expert_types_other?: string | null;
  relationship_types?: string[];
  expertises?: string[];
  matter_types?: string[];
  dr_preferences?: string[];
  lawfirm_id: string;
  reference_id?: string | null;
}

//MultiSelect Component
export interface MultiSelectProps {
  label: string;
  required?: boolean;
  options: Array<{ value: string; label: string }>;
  selected: string[];
  onChange: (selected: string[]) => void;
  error?: string;
  placeholder?: string;
  maxSelections?: number;
  selectedCount?: number;
}

export interface LawyerSearchApiResponse {
  success: boolean;
  message: string;
  data: {
    items: Lawyer[];
    total_count: number;
    records_in_page: number;
  };
}

export interface LawyerApiResponse {
  success: boolean;
  message: string;
  data: Lawyer;
}

// Legacy types for backward compatibility
export type LawyerSearchApiResponseItem = Lawyer;

// New display type for lawyer details card.
export interface LawyerDetailsDisplayCardType {
  // Basic identification fields
  id: string;
  lawyer_id?: string;
  user_id?: string;
  
  // Personal information
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  phone?: string;
  gender?: string | null;
  gender_other?: string | null;
  
  // Address information
  address_line_1?: string | null;
  address_line_2?: string | null;
  city?: string | null;
  county?: string | null;
  country?: string | null;
  postal_code?: string | null;
  
  // Professional registration
  reg_no?: string | null;
  regulator?: string | null;
  sra_number?: string | null;
  bar_number?: string | null;
  
  // Professional dates
  admitted_date_solicitor?: string | null;
  called_date_barrister?: string | null;
  admitted_date_cliex?: string | null;
  joined_at?: string | null;
  left_at?: string | null;
  
  // Professional information
  about?: string | null;
  photo_url?: string | null;
  photo_urls?: {
    thumbnail: string;
    medium: string;
    large: string;
  } | null;
  linkedin_url?: string | null;
  lawyer_status?: string;
  status?: string;
  experience?: string | null;
  
  // Financial information
  hourly_rate?: number | null;
  charge_first_consultation?: number | null;
  
  // Specializations and expertise
  expert_types_all?: string[];
  accredited_specialisms?:string[];
  conflict_level_disinclination?: string | null;
  expert_types?: string[];
  relationship_types?: string[];
  matter_types?: string[];
  accreditations?: string[];
  expertises_all?: string[];
  
  // Insurance and additional info
  pi_insurance?: string | null;
  testimonial?: string | null;
  
  // Law firm information
  lawfirms?: Array<{
    id: string;
    name: string;
  }> | null;
  
  // Timestamps
  created_at: string;
  updated_at?: string | null;
  is_sent?: boolean;
}

// Lawyer Profile Interface
export interface LawyerProfileDisplayType {
  id: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  gender?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  image?: string | null; // Profile image URL
  rate?: number | null; // Hourly or flat rate (optional)
  experience?: string | null; // e.g., "8 years", "5+ years"
  specialization?: string | null; // Area of law or expertise
  location?: string | null; // City, region, or address
  about?: string | null; // Short bio or description
  name?: string; // Computed from first_name + last_name
  is_sent?: boolean;
  hourly_rate?: number | null;
  lawyer_id?: string;
  lawyer_name?: string;
  lawyer_photo_url?: string;
  lawyer_photo_urls?: {
    thumbnail: string;
    medium: string;
    large: string;
  };
  lawyer_experience?: string;
  lawyer_expert_types?: string[];
  lawyer_expertises?: string[];
  about_lawyer?: string;
  lawyer_location?: string;
  lawyer_specialization?: string;
  lawyer_accreditations?: string[];
  lawyer_testimonial?: string;
  lawyer_rate?: number;
  lawyer_about?: string;
}

// Lawyer Details Card Button Configuration
export interface LawyerDetailsCardButtonConfig {
  text: string;
  type: "Remove" | "Add";
  onClick: () => void;
  icon?: string;
}

// Navigator Types - Aligned with API schemas
export interface Navigator {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  gender: string | null;
  gender_other?: string;
  status: string;
  needs_password_setup?: boolean;
  // address_line_1?: string;
  // address_line_2?: string;
  // city?: string;
  // county?: string;
  // country?: string;
  // postal_code?: string;
  // joined_at?: string;
  // left_at?: string;
  // about?: string;
  photo_urls?: {
    large: string;
    medium: string;
    thumbnail: string;
  };
  linkedin_url?: string;
  specialization?: string;
  experience?: number;
  user_id?: string;
  created_at: string;
  updated_at: string;
}

// Form data for creating/editing navigators
export interface NavigatorFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  gender: string;
  gender_other?: string | null;
  status: "Active" | "Inactive";
  address_line_1?: string;
  address_line_2?: string;
  city?: string;
  county?: string;
  country?: string;
  postal_code?: string;
  joined_at?: string;
  left_at?: string;
  about?: string;
  linkedin_url?: string;
  specialization?: string;
  experience?: number;
  user_id?: string;
}

export interface NavigatorSearchApiResponse {
  success: boolean;
  message: Array<{
    success: boolean;
    message: string;
  }>;
  data: {
    total_count: number;
    records_in_page: number;
    users: Navigator[];
  };
}

export interface NavigatorApiResponse {
  success: boolean;
  message: string;
  data: Navigator;
}

// Lawyer Details Card Props
export interface LawyerDetailsCardProps {
  lawyer: LawyerProfileDisplayType;
  buttonConfig?: LawyerDetailsCardButtonConfig;
  onRemove?: (lawyer: LawyerProfileDisplayType) => void;
  variant?: "selected" | "search";
}

// Review Profiles Modal Props
export interface ReviewProfilesModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Called after confirm lawyers succeeds (before closing). Use to refetch case details. */
  onConfirmSuccess?: () => void;
  lawyers?: LawyerProfileDisplayType[];
  caseId?: string;
}

export interface InterestedLawyersModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSend: (selected: InterestedLawyerType[]) => void;
  interestedLawyers?: InterestedLawyerType[];
  caseId?: string;
}

// Search State Interface
export interface SearchState {
  searchTerm: string;
  searchResults: LawyerProfileDisplayType[];
  searchLoading: boolean;
}

export interface NotifiedLawyersType {
  id: string;
  name: string;
  photo_url: string;
}

// Complete Onboarding Assessment specific meta data structure
export interface CompleteOnboardingAssessmentMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_name: string;
  customer_name: string;
  engage_url: string;
  case_type: string;
  action_buttons: {
    mark_onboarding_completed: boolean;
  };
}

// OnBoarding Assessment Completed specific meta data structure
export interface OnBoardingAssessmentCompletedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  case_type: string;
  lawyer_name: string;
  amount_requested: string;
  customer_first_name: string;
  action_buttons: {
    make_payment: boolean;
  };
}

export interface TalkToLawyerRequestedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_name: string;
  action_buttons: {
    choose_another_lawyer: boolean;
  };
}

export interface TalkToNavigatorRequestedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  action_buttons: {
    choose_another_lawyer: boolean;
  };
}

export interface CustomerTalkToLawyerMetaDataType {
  "action_by": string,
  "timestamp": string,
  "case_number": string,
  "lawyer_name": string,
  "lawyer_email": string,
  "customer_name": string,
  "customer_email": string,
  "customer_phone": string,
  "action_buttons":{
  }
}

export interface CustomerTalkToNavigatorMetaDataType {
  "action_by": string,
  "timestamp": string,
  "case_number": string,
  "customer_name": string,
  "customer_email": string,
  "customer_phone": string,
  "action_buttons":{
  }
}

// Navigator Client Onboarding Completed specific meta data structure
export interface NavigatorClientOnboardingCompletedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_name: string;
  customer_name: string;
  case_type: string;
  status: string;
  action_buttons: {};
}

// Lawyer Client Onboarding Completed specific meta data structure
export interface LawyerClientOnboardingCompletedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  customer_name: string;
  case_type: string;
  status: string;
  action_buttons: {};
}

// Lawyer Complete Onboarding Assessment specific meta data structure
export interface LawyerCompleteOnboardingAssessmentMetaDataType {
  action_by: string | null;
  timestamp: string;
  case_number: string;
  customer_name?: string;
  action_buttons?: {
    mark_onboarding_completed?: boolean;
  };
}

// Navigator Complete Onboarding Assessment specific meta data structure
export interface NavigatorCompleteOnboardingAssessmentMetaDataType {
  action_by: string | null;
  timestamp: string;
  case_number: string;
  customer_name?: string;
  action_buttons?: {
    mark_onboarding_completed?: boolean;
  };
}

// Match confirmed lawyers type
export interface MatchConfirmedLawyerType {
  lawyer_about: string;
  lawyer_experience: number;
  lawyer_expert_type: string[];
  lawyer_id: string;
  lawyer_location: string;
  lawyer_name: string;
  lawyer_photo_url: string;
  lawyer_photo_urls?: {
    thumbnail: string;
    medium: string;
    large: string;
  };
  lawyer_specialization: string;
}

export interface InterestedLawyerType {
    id: string;
    expert_types?: string[];
    accredited_specialisms?: string[];
    about: string;
    city: string;
    county: string;
    experience_years: string;
    hours_to_interested: string;
    photo_url?: string;
    photo_urls?: {
      thumbnail: string;
      medium: string;
      large: string;
    };
    first_name: string;
    last_name: string;
    case_id?: string;
}

// Navigator Interest Received specific meta data structure
export interface NavigatorInterestReceivedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_name: string;
  about_lawyer: string;
  interest_message: string;
  action_buttons: {
    send_reviewed_profiles: boolean;
  };
}

// Customer Initial Payment Requested specific meta data structure
export interface CustomerInitialPaymentRequestedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  case_type: string;
  lawyer_name: string;
  amount_requested: string;
  status?: string;
  payment_id?: string;
  action_buttons: {
    make_payment: boolean;
    view_failed_attempts?: boolean;
  };
  invoice_id?: string;
  failed_attempts?: Array<{
    reason: string;
    transaction_id: string;
    created_at: string;
  }>;
}

// Customer Initial Payment Requested response type that matches the actual data structure
export interface CustomerInitialPaymentRequestedResponsePropsType extends TimelineItemType {
  meta_data: CustomerInitialPaymentRequestedMetaDataType;
  id: string;
}

// Component props type for CustomerInitialPaymentRequested component (for timeline rendering)
export interface CustomerInitialPaymentRequestedTimelineProps {
  timelineData: CustomerInitialPaymentRequestedResponsePropsType;
}

// Navigator Interest Received response type that matches the actual data structure
export interface NavigatorInterestReceivedResponsePropsType extends TimelineItemType {
  meta_data: NavigatorInterestReceivedMetaDataType;
}

// Component props type for NavigatorInterestReceived component (for timeline rendering)
export interface NavigatorInterestReceivedTimelineProps {
  timelineData: NavigatorInterestReceivedResponsePropsType;
}

// Lawyer Client Onboarding Completed response type that matches the actual data structure
export interface LawyerClientOnboardingCompletedResponsePropsType extends TimelineItemType {
  meta_data: LawyerClientOnboardingCompletedMetaDataType;
}

// Component props type for LawyerClientOnboardingCompleted component (for timeline rendering)
export interface LawyerClientOnboardingCompletedTimelineProps {
  timelineData: LawyerClientOnboardingCompletedResponsePropsType;
}

// Navigator Client Onboarding Completed response type that matches the actual data structure
export interface NavigatorClientOnboardingCompletedResponsePropsType extends TimelineItemType {
  meta_data: NavigatorClientOnboardingCompletedMetaDataType;
}

// Component props type for NavigatorClientOnboardingCompleted component (for timeline rendering)
export interface NavigatorClientOnboardingCompletedTimelineProps {
  timelineData: NavigatorClientOnboardingCompletedResponsePropsType;
}

export interface NavigatorCompleteOnboardingAssessmentResponsePropsType extends TimelineItemType {
  meta_data: NavigatorCompleteOnboardingAssessmentMetaDataType;
}

// Component props type for NavigatorCompleteOnboardingAssessment component (for timeline rendering)
export interface NavigatorCompleteOnboardingAssessmentTimelineProps {
  timelineData: NavigatorCompleteOnboardingAssessmentResponsePropsType;
}

export interface LawyerCompleteOnboardingAssessmentResponsePropsType extends TimelineItemType {
  meta_data: LawyerCompleteOnboardingAssessmentMetaDataType;
}

// Component props type for CompleteOnboardingAssessment component (for timeline rendering)
export interface LawyerCompleteOnboardingAssessmentTimelineProps {
  timelineData: LawyerCompleteOnboardingAssessmentResponsePropsType;
}
// Complete Onboarding Assessment response type that matches the actual data structure
export interface CompleteOnboardingAssessmentResponsePropsType extends TimelineItemType {
  meta_data: CompleteOnboardingAssessmentMetaDataType;
}

// Component props type for CompleteOnboardingAssessment component (for timeline rendering)
export interface CompleteOnboardingAssessmentTimelineProps {
  timelineData: CompleteOnboardingAssessmentResponsePropsType;
}

// OnBoarding Assessment Completed response type that matches the actual data structure
export interface OnBoardingAssessmentCompletedResponsePropsType extends TimelineItemType {
  meta_data: OnBoardingAssessmentCompletedMetaDataType;
}

// Component props type for OnBoardingAssessmentCompleted component (for timeline rendering)
export interface OnBoardingAssessmentCompletedTimelineProps {
  timelineData: OnBoardingAssessmentCompletedResponsePropsType;
}

export interface TalkToLawyerRequestedResponsePropsType extends TimelineItemType {
  meta_data: TalkToLawyerRequestedMetaDataType;
}

export interface TalkToLawyerRequestedTimelineProps {
  timelineData: TalkToLawyerRequestedResponsePropsType;
  isLatest?: boolean;
}

export interface TalkToNavigatorRequestedResponsePropsType extends TimelineItemType {
  meta_data: TalkToNavigatorRequestedMetaDataType;
}

export interface TalkToNavigatorRequestedTimelineProps {
  timelineData: TalkToNavigatorRequestedResponsePropsType;
}

export interface CustomerTalkToLawyerResponsePropsType extends TimelineItemType {
  meta_data: CustomerTalkToLawyerMetaDataType;
}

export interface CustomerTalkToLawyerTimelineProps {
  timelineData: CustomerTalkToLawyerResponsePropsType;
}

export interface CustomerTalkToNavigatorResponsePropsType extends TimelineItemType {
  meta_data: CustomerTalkToNavigatorMetaDataType;
}

export interface CustomerTalkToNavigatorTimelineProps {
  timelineData: CustomerTalkToNavigatorResponsePropsType;
}

// Case Notification Sent specific meta data structure
export interface MatchNotificationSentMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  notified_lawyers: NotifiedLawyersType[]; // JSON string or comma-separated names
  message: string;
  action_buttons: {};
}

export interface LawyerProfileDetailsType {
  lawyer_name: string;
  lawyer_about: string;
  lawyer_photo_url: string;
  lawyer_experience: string;
  lawyer_expert_types: string[];
  lawyer_rate: string;
  lawyer_location: string;
  lawyer_specialization: string;
}

export interface CustomerEngagedLawyerMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_profile: LawyerProfileDetailsType;
  action_buttons: {

  }
}

export interface CustomerEngagedLawyerResponsePropsType extends TimelineItemType {
  meta_data: CustomerEngagedLawyerMetaDataType;
}

export interface CustomerEngagedLawyerTimelineProps {
  timelineData: CustomerEngagedLawyerResponsePropsType;
}

// Case Notification Sent response type that matches the actual data structure
export interface MatchNotificationSentResponsePropsType extends TimelineItemType {
  meta_data: MatchNotificationSentMetaDataType;
}

// Component props type for MatchNotificationSent component (for timeline rendering)
export interface MatchNotificationSentTimelineProps {
  timelineData: MatchNotificationSentResponsePropsType;
}

// Selected Lawyers State Interface
export interface SelectedLawyersState {
  selectedLawyers: LawyerProfileDisplayType[];
  originalSelectedLawyers: LawyerProfileDisplayType[];
}

// Case Opened response type that matches the actual data structure
export interface CaseOpenedResponsePropsType extends TimelineItemType {
  meta_data: CaseOpenedMetaDataType;
}

// Case Archived specific meta data structure
export interface CaseArchivedMetaDataType {
  case_number: string;
  timestamp: string;
  customer_name: string;
  action_by?: string;
  new_case_number?: string;
  new_case_id?: string;
}

// Case Archived response type that matches the actual data structure
export interface CaseArchivedResponsePropsType extends TimelineItemType {
  meta_data: CaseArchivedMetaDataType;
}

// Component props type for CaseArchived component (for timeline rendering)
export interface CaseArchivedTimelineProps {
  timelineData: CaseArchivedResponsePropsType;
}

// Match Found specific meta data structure
export interface MatchFoundMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  customer_name: string;
  partner_name: string;
  case_summary: string;
  resolve_id?: string;
  action_buttons: {
    raise_interest?: boolean;
    decline_match?: boolean;
    ask_more_details?: boolean;
    view_resolve?: boolean;
    view_kyc?: boolean;
  };
}

// Snapshot item: one row in the case summary table (answer can be string or array of strings)
export interface LawyerMatchCaseSummaryItem {
  question: string;
  answer?: string | string[];
}

// Match Found specific meta data structure
export interface LawyerMatchFoundMetaDataType {
  action_by: string;
  timestamp: string;
  case_priority?: string;
  case_number: string;
  resolve_id?: string;
  resolve_title?: string;
  current_court_proceedings?: string;
  income_before_tax?: string;
  features_relevant_to_children?: string;
  features_relevant_to_relationship?: string;
  relationship_activities?: string;
  customer_name?: string;
  customer_first_name?:string;
  partner_name?:string;
  partner_first_name?:string;
  hourly_rate?:string;
  strategic_advice_consultation?: string;
  /** Array of { question, answer }. Legacy: string (JSON). No nested summary. */
  case_summary: LawyerMatchCaseSummaryItem[] | string;
  /** Array of { title, description } for Overview tab. Legacy: string (JSON). */
  case_ai_summary?:
    | string
    | Array<{ title: string; description: string }>;
  /** Urgent priority reasons. New: string[]. Legacy: comma-separated string. */
  case_priority_data?: string | string[];
  preferred_consultation_method?: string;
  additional_support?: string;
  email_address?: string;
  gender?: string;
  kyc_id?:string;
  /** Case types; may contain {partner_name} placeholder. New: string[]. Legacy: comma-separated string. */
  matter_type_kyc?: string | string[];
  relationship_type?: string;
  match_status?:string;
  action_buttons: {
    raise_interest?: boolean;
    decline_match?: boolean;
    ask_more_details?: boolean;
    view_resolve?: boolean;
    view_kyc?: boolean;
  };
}

// Match Found response type that matches the actual data structure
export interface MatchFoundResponsePropsType extends TimelineItemType {
  meta_data: MatchFoundMetaDataType;
}

export interface LawyerMatchFoundResponsePropsType extends TimelineItemType {
  meta_data: LawyerMatchFoundMetaDataType;
}

// Interest Raised specific meta data structure
export interface InterestRaisedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  action_buttons: {};
}

// Interest Raised response type that matches the actual data structure
export interface InterestRaisedResponsePropsType extends TimelineItemType {
  meta_data: InterestRaisedMetaDataType;
}

// Component props type for InterestRaised component (for timeline rendering)
export interface InterestRaisedTimelineProps {
  timelineData: InterestRaisedResponsePropsType;
}

// Case Declined specific meta data structure
export interface CaseDeclinedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  reasons: string[];
  reason_other: string;
  lawyer_name: string;
  action_buttons: {
    raise_interest?: boolean;
  };
}

// Case Declined response type that matches the actual data structure
export interface CaseDeclinedResponsePropsType extends TimelineItemType {
  meta_data: CaseDeclinedMetaDataType;
}

// More Details Requested specific meta data structure
export interface MoreDetailsRequestedMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_name: string;
  lawyer_request: string;
  action_buttons: {
    raise_interest?: boolean;
    decline_match?: boolean;
  };
}

// More Details Requested response type that matches the actual data structure
export interface MoreDetailsRequestedResponsePropsType extends TimelineItemType {
  meta_data: MoreDetailsRequestedMetaDataType;
}

// Signup API Types
export interface SignupRequest {
  first_name: string;
  last_name: string;
  phone?: string;
  email: string;
  password: string;
  resolve_id?: string;
}

export interface SignupResponse {
  success: boolean;
  message: string;
  data: {
    customer: {
      first_name: string;
      last_name: string;
      email: string;
      customer_id: string;
    };
    case: {
      case_id: string;
      case_no: string;
      case_type: string;
      priority: string;
      start_date: string;
      status: string;
      created_at: string;
      updated_at: string;
    };
    login_data: {
      access_token: string;
      refresh_token: string;
      token_type: string;
      user_data: {
        first_name: string;
        last_name: string;
        email: string;
        phone: string;
        gender: string;
        user_id: string;
        role_code: string;
        role_name: string;
      };
    };
  };
}

// Matched Experts specific meta data structure
export interface MatchedExpertsMetaDataType {
  action_by: string;
  timestamp: string;
  case_number: string;
  lawyer_profiles: LawyerProfileDisplayType[];
  first_name?: string;
  action_buttons: {
    engage_with: boolean;
    talk_to_nn: boolean;
    talk_to_lawyer: boolean;
  };
}

// Matched Experts response type that matches the actual data structure
export interface MatchedExpertsResponsePropsType extends TimelineItemType {
  meta_data: MatchedExpertsMetaDataType;
}

// Component props type for MatchedExperts component (for timeline rendering)
export interface MatchedExpertsTimelineProps {
  timelineData: MatchedExpertsResponsePropsType;
  isLatest?: boolean;
}

// Resolve Question Types
export interface QuestionOption {
  [key: string]: {
    value: string;
    tooltip?: string | null;
    additional_description?: string | null;
    additional_title?: string | null;
  };
}

export interface QuestionAnswer {
  value: string;
}

export interface QuestionRule {
  identifier: string;
  operator: string;
  value: string;
}

export interface QuestionData {
  question_type: string;
  variant: string;
  title: string;
  description: string;
  placeholder: string | null;
  question: string;
  options: QuestionOption[];
  required: boolean;
  input_type: "text" | "number" | "radio" | "checkbox" | "textarea";
  rules: QuestionRule[];
  question_order: number;
  answer_type: string;
  answer: QuestionAnswer[];
  question_status: string;
  version: string;
}

export interface ResolveResult {
  result_type: string;
  title: string;
  summary: string;
  version: string;
  affordability?: string;
  recommendations?: {
    Communication?: string;
    Conflict?: string;
    Finances?: string;
    Understanding?: string;
    Trust?: string;
    Complexity?: string;
    Confidence?: string;
  };
}

export interface ResolveData {
  resolve_id: string;
  title: string;
  questions_answered: number;
  resolve_status: string;
  result?: ResolveResult | null;
  info: string | null;
  question_data: Record<string, QuestionData>;
  lawyers?: LawyerSearchApiResponseItem[];
}

export interface ResolveApiResponse {
  success: boolean;
  message: Array<{
    success: boolean;
    message: string;
  }>;
  data: ResolveData;
}

export interface SaveAnswerResponse {
  success: boolean;
  message: Array<{
    success: boolean;
    message: string;
  }>;
  data: {
    resolve_id: string;
    error_list: any;
  };
}

export interface CompleteResolveResponse {
  success: boolean;
  message: Array<{
    success: boolean;
    message: string;
  }>;
  data: {
    resolve_id: string;
    result: ResolveResult;
    resolve_status: string;
    lawyers?: LawyerSearchApiResponseItem[];
  };
}

export interface AnswerRequest {
  answer: QuestionAnswer[];
  question_identifier: string;
  version: string;
}

export interface SaveAnswerRequest {
  resolve_id: string;
  answers: AnswerRequest[];
}

export interface AnsweredQuestion {
  questionId: string;
  questionTitle: string;
  questionNumber: number;
  answer: string;
  timestamp: string;
  isCompleted: boolean;
}

// Case Details API Types
export interface CaseSummaryItem {
  title: string;
  description: string;
}

export interface CaseSummary {
  summary: CaseSummaryItem[];
}

export interface CaseDetailsPartiesInvolved {
  client_name: string;
  client_email: string;
  client_phone: string | null;
  lawyer_name: string;
  lawyer_email: string;
  lawyer_phone: string | null;
  partner_name: string;
}

export interface CaseDetailsActionButtons {
  send_to_customer?: boolean;
  raise_interest?: boolean;
  review_profiles?: boolean;
}

export interface CaseDetailsData {
  case_summary: CaseSummary;
  is_ai_summary_generated?: boolean | null;
  parties_involved: CaseDetailsPartiesInvolved;
  action_buttons: CaseDetailsActionButtons;
}

export interface CaseDetailsApiResponse {
  success: boolean;
  message: string;
  data: CaseDetailsData;
}

// User Profile Types
export interface UserData {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  gender: string;
  gender_other: string;
  status: string;
  created_at: string;
  updated_at: string;
  photo_urls:{
    thumbnail: string;
    medium: string;
    large: string;
  }
}

export interface UserResponse {
  success: boolean;
  message: string;
  data: UserData;
}

// Legal Expert Types (B2C Experts)
export type LegalExpertStatus = "New" | "Review" | "Onboarded" | "Rejected";

export interface ValuesWithOther {
  values?: string[];
  other?: string | null;
}

export interface LegalExpert {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  work_status?: string | null;
  firm_name?: string | null;
  city?: string | null;
  post_code?: string | null;
  gender?: string | null;
  photo_url?: {
    thumbnail: string;
    medium: string;
    large: string;
  } | null;
  professional_status?: ValuesWithOther | null;
  experience?: number | null;
  service_details?: Record<string, string[]> | null;
  ncdr_magic?: { values?: string[] } | null;
  accredited_specialist?: { values?: string[] } | null;
  accredited_specialism_other?: string[] | null;
  regulator?: ValuesWithOther | null;
  ncdr_description?: string | null;
  compelling_quote?: string | null;
  remote_consultation?: "Yes" | "No" | null;
  // consultation_offers?: { values?: string[] } | null;
  matter_types?: { values?: string[] } | null;
  status?: LegalExpertStatus | null;
  created_at?: string;
  updated_at?: string;
}

export interface LegalExpertFormData {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string | null;
  work_status?: string | null;
  firm_name?: string | null;
  city?: string | null;
  post_code?: string | null;
  gender?: string | null;
  photo_url?: string | null;
  professional_status?: ValuesWithOther | null;
  experience?: number | null;
  service_details?: Record<string, string[]> | null;
  ncdr_magic?: { values?: string[] } | null;
  accredited_specialist?: { values?: string[] } | null;
  accredited_specialism_other?: string[] | null;
  regulator?: ValuesWithOther | null;
  ncdr_description?: string | null;
  compelling_quote?: string | null;
  remote_consultation?: "Yes" | "No" | null;
  consultation_offers?: { values?: string[] } | null;
  status?: LegalExpertStatus | null;
}

export interface LegalExpertSearchApiResponse {
  success: boolean;
  message: Array<{ success: boolean; message: string }>;
  data: {
    lawyers: LegalExpert[];
    total_count: number;
    records_in_page: number;
  };
}

export interface LegalExpertApiResponse {
  success: boolean;
  message: Array<{ success: boolean; message: string }>;
  data: LegalExpert;
}