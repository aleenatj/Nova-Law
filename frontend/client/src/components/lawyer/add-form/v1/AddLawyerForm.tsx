import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Lawyer, LawyerFormData } from "@/lib/types";
import LawFirmSearch from "@/components/lawfirm/firm-search/v1/LawFirmSearch";
import { TagInput } from "@/components/ui/taginput/v1/TagInput";
import { api } from "@/lib/api";
import MultiSelect from "@/components/ui/multi-select/v1/MultiSelect";
import CountrySelect from "@/components/ui/country-select/CountrySelect";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";
import { FormButton } from "@/utils/formComponents";
import { uploadImage } from "@/lib/utils";
import { toastManager, createErrorToast } from "@/utils/toasts";

// Interface for pre-filled data from legal expert onboarding
interface LegalExpertPreFillData {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  gender?: string;
  city?: string;
  postal_code?: string;
  photo_url?: string;
  photo_preview_url?: string;
  about?: string;
  testimonial?: string;
  accredited_specialisations?: string[]; // Changed to array for key-based mapping
  accredited_specialism_other?: string[] | null;
  dr_preferences?: string[]; // Changed to array for key-based mapping
  professional_status?: { values?: string[]; other?: string | null };
  regulator?: string;
  regulator_other?: string | null;
  relationship_types?: string[]; // From service_details.offers
  expertises?: {
    cohabitees?: { expertises?: string[]; other?: string[] };
    married_civil_partners?: { expertises?: string[]; other?: string[] };
  };
  matter_types?: string[]; // If available
  conflict_level_disinclination?: string; // If available
  reference_id?: string;
}

interface AddLawyerFormProps {
  mode: "add" | "edit";
  lawyerData?: Lawyer;
  onCancel: () => void;
  onSubmit: (data: LawyerFormData, lawyerId?: string) => Promise<boolean>;
  preFillData?: LegalExpertPreFillData;
}

const AddLawyerForm: React.FC<AddLawyerFormProps> = ({
  mode,
  lawyerData,
  onCancel,
  onSubmit,
  preFillData,
}) => {
  const initialFormState: LawyerFormData = {
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    gender: null,
    gender_other: null,
    status: "Active",
    address_line_1: null,
    address_line_2: null,
    city: null,
    county: null,
    country: null,
    postal_code: null,
    reg_no: null,
    sra_number: null,
    bar_number: null,
    regulator: null,
    regulator_other: null,
    admitted_date_solicitor: null,
    called_date_barrister: null,
    admitted_date_cliex: null,
    joined_at: null,
    left_at: null,
    about: null,
    photo_url: null,
    linkedin_url: null,
    hourly_rate: null,
    charge_first_consultation: null,
    accredited_specialisms: [],
    accredited_specialism_other: null,
    conflict_level_disinclination: null,
    pi_insurance: null,
    testimonial: null,
    expert_types: [],
    expert_types_other: null,
    relationship_types: [],
    matter_types: [],
    dr_preferences: [],
    lawfirm_id: "",
    reference_id: null,
  };

  const EXPERT_TYPE_OPTIONS = [
    { value: "SOLICITOR", label: "Solicitor" },
    { value: "BARRISTER", label: "Barrister" },
    { value: "CILEX", label: "Cilex" },
    { value: "LAWYER_MEDIATOR", label: "Lawyer-Mediator" },
    { value: "MEDIATOR", label: "Mediator" },
    { value: "ARBITRATOR", label: "Arbitrator" },
    { value: "DIVORCE_COACH", label: "Divorce Coach" },
    { value: "FAMILY_CONSULTANT", label: "Family Consultant" },
    { value: "OTHER", label: "Other" },
  ];

  const ACCREDITED_SPECIALISM_OPTIONS = [
    { value: "RESOLUTION_ACCREDITED_SPECIALIST", label: "Resolution Accredited Specialist" },
    { value: "LAW_SOCIETY_ACCREDITED_SPECIALIST", label: "Law Society Accredited Specialist" },
    { value: "FMC_ACCREDITED_MEDIATOR", label: "FMC Accredited Mediator" },
    { value: "CIARB_ACCREDITED_ARBITRATOR", label: "CIArb Accredited Arbitrator" },
    { value: "OTHER", label: "Other" },
  ];

  const MATTER_TYPE_OPTIONS = [{ value: "FINANCIAL_CLAIMS", label: "Financial Claims" }, { value: "CHILDREN", label: "Children" }];
  const RELATIONSHIP_TYPE_OPTIONS = [{ value: "MARRIED_CIVIL_PARTNERS", label: "Married and Civil Partners" }, { value: "COHABITEES", label: "Cohabitees" }, { value: "PARENTAL_RELATIONSHIPS", label: "Parental relationships" }];

  // Expertise options for each relationship type
  const EXPERTISE_OPTIONS = {
    "Married and Civil Partners": [
      { value: "DIVORCE_AND_SEPARATION", label: "Divorce and Separation" },
      { value: "FINANCIAL_CLAIMS", label: "Financial Claims" },
      { value: "OVERSEAS_FINANCIAL_CLAIMS", label: "Overseas Financial claims" },
      { value: "CHILD_ARRANGEMENTS", label: "Child arrangements" },
      { value: "CHILDREN_DOMESTIC_RELOCATION", label: "Children domestic relocation" },
      { value: "CHILDREN_INTERNATIONAL_RELOCATION", label: "Children international relocation" },
      { value: "INHERITANCE_ACT_CLAIMS", label: "Inheritance Act claims" },
      { value: "PRE_NUPTIAL_PRE_CIVIL_PARTNERSHIP_AGREEMENTS", label: "Pre-nuptial & pre-civil partnership agreements" },
      { value: "POST_NUPTIAL_POST_CIVIL_PARTNERSHIP_AGREEMENTS", label: "Post-nuptial and post-civil partnership agreements" },
      { value: "OTHER_MARRIED_CIVIL_PARTNERS", label: "Other" },
    ],
    "Cohabitees": [
      { value: "SEPARATION_AGREEMENTS", label: "Separation agreements" },
      { value: "COHABITATION_CHILD_ARRANGEMENTS", label: "Cohabitation - Child arrangements" },
      { value: "COHABITATION_CHILDREN_DOMESTIC_RELOCATION", label: "Cohabitation - Children domestic relocation" },
      { value: "COHABITATION_CHILDREN_INTERNATIONAL_RELOCATION", label: "Cohabitation - Children international relocation" },
      { value: "COHABITATION_FINANCIAL_CLAIMS", label: "Cohabitation - Financial Claims" },
      { value: "LIVING_TOGETHER_AGREEMENTS", label: "Living together agreements" },
      { value: "SCHEDULE_I_CLAIMS", label: "Schedule I claims" },
      { value: "COHABITATION_INHERITANCE_ACT_CLAIMS", label: "Cohabitation - Inheritance Act claims" },
      { value: "OTHER_COHABITEES", label: "Other " },
    ],
  };

  const drOptions = [
    { label: "Direct Negotiation", value: "DIRECT_NEGOTIATION" },
    { label: "Mediation", value: "MEDIATION" },
    { label: "One Lawyer One Couple", value: "ONE_LAWYER_ONE_COUPLE" },
    { label: "Collaborative", value: "COLLABORATIVE" },
    { label: "Hybrid Mediation-Support", value: "HYBRID_MEDIATION_SUPPORT", type: "Support", base: "Hybrid Mediation" },
    { label: "Hybrid Mediation-Mediator", value: "HYBRID_MEDIATION_MEDIATOR", type: "Other", base: "Hybrid Mediation" },
    { label: "Lawyer Negotiation", value: "LAWYER_NEGOTIATION" },
    { label: "Early Neutral Evaluation/Private FDR-Support", value: "EARLY_NEUTRAL_EVALUATION_SUPPORT", type: "Support", base: "Early Neutral Evaluation/Private FDR" },
    { label: "Early Neutral Evaluation/Private FDR-Evaluator", value: "EARLY_NEUTRAL_EVALUATION_EVALUATOR", type: "Other", base: "Early Neutral Evaluation/Private FDR" },
    { label: "Arbitration-Support", value: "ARBITRATION_SUPPORT", type: "Support", base: "Arbitration" },
    { label: "Arbitration-Arbitrator", value: "ARBITRATION_ARBITRATOR", type: "Other", base: "Arbitration" },
    { label: "Court", value: "COURT" }
  ];

  const CONFLICT_LEVEL_OPTIONS = [
    { value: "MEDIUM_CONFLICT", label: "Medium conflict" },
    { value: "HIGH_CONFLICT", label: "High Conflict" },
    { value: "IMPLACABLE_HOSTILITY", label: "Implacable hostility" },
  ];

  const REGULATOR_OPTIONS = [
    { value: "BSB", label: "BSB" },
    { value: "SRA", label: "SRA" },
    { value: "CILEX", label: "Cilex Regulation" },
    { value: "OTHER", label: "Other" },
  ];

  // Max length validation (errors show while typing) – same approach as navigator/lawfirm
  const VALIDATION = {
    first_name: 100,
    last_name: 100,
    email: 255,
    postal_code: 20,
    phone: 17,
    pi_insurance: 100,
    testimonial: 500,
    city: 100,
    county: 100,
    reg_no: 100,
    sra_number: 100,
    bar_number: 100,
    address_line_1: 255,
    address_line_2: 255,
    about: 1500,
    linkedin_url: 255,
    hourly_rate: 10,
    charge_first_consultation: 10,
    regulator_other: 255,
    expert_types_other: 255,
  } as const;

  const limitError = (max: number) => `Character limit exceeded (max ${max} characters)`;

  const getMaxLengthError = (fieldName: keyof typeof VALIDATION, value: string | null | undefined): string => {
    const max = VALIDATION[fieldName];
    if (max == null) return "";
    const str = value == null ? "" : String(value);
    if (str.length > max) return limitError(max);
    return "";
  };

  const getPostalCodeError = (value: string | null | undefined): string => {
    const str = value == null ? "" : String(value).trim();
    if (!str) return "";
    if (str.length > VALIDATION.postal_code) return limitError(VALIDATION.postal_code);
    const postcodeRegex =  /^[A-Z0-9\s\-]{3,20}$/i;
    if (!postcodeRegex.test(str)) return "Please enter a valid postal code";
    return "";
  };

  // Utility function to map values using option arrays (key-based mapping)
  const mapValueByOptions = (value: string, options: Array<{ value: string; label: string }>): string | null => {
    if (!value) return null;
    const trimmedValue = value.trim();
    if (!trimmedValue) return null;
    
    // First try exact match on value (enum key) - case insensitive
    const exactMatch = options.find(opt => {
      if (!opt || !opt.value) return false;
      return (
        opt.value === trimmedValue || 
        opt.value === trimmedValue.toUpperCase() ||
        opt.value.toLowerCase() === trimmedValue.toLowerCase()
      );
    });
    if (exactMatch) return exactMatch.value;
    
    // Then try match on label (display text) - case insensitive
    const labelMatch = options.find(opt => {
      if (!opt || !opt.label) return false;
      return (
        opt.label === trimmedValue || 
        opt.label.toLowerCase() === trimmedValue.toLowerCase() ||
        opt.label.trim().toLowerCase() === trimmedValue.toLowerCase()
      );
    });
    if (labelMatch) return labelMatch.value;
    
    return null;
  };

  // Utility function to map array of values using option arrays
  const mapValuesByOptions = (values: string[] | undefined, options: Array<{ value: string; label: string }>): string[] => {
    if (!values || values.length === 0) return [];
    return values
      .map(val => {
        if (!val) return null;
        const mapped = mapValueByOptions(val, options);
        // If mapping succeeds, return the mapped value (enum key)
        if (mapped) return mapped;
        // If mapping fails, check if value is already a valid enum key
        const isValidKey = options.some(opt => 
          opt.value === val || 
          opt.value.toLowerCase() === val.toLowerCase() ||
          opt.value === val.toUpperCase()
        );
        // If it's a valid enum key, preserve it
        if (isValidKey) {
          // Return the correct case version from options
          const matchingOption = options.find(opt => 
            opt.value === val || 
            opt.value.toLowerCase() === val.toLowerCase() ||
            opt.value === val.toUpperCase()
          );
          return matchingOption?.value || val;
        }
        return null;
      })
      .filter((val): val is string => val !== null);
  };

  const [formData, setFormData] = useState<LawyerFormData>(initialFormState);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedLawFirmName, setSelectedLawFirmName] = useState("");
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [uploadTokenResponse, setUploadTokenResponse] = useState<any>(null);
  const [showUploadOption, setShowUploadOption] = useState(false);
  const [hasNewPhotoUpload, setHasNewPhotoUpload] = useState(false);
  const [photoRemoved, setPhotoRemoved] = useState(false);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");
  
  // Expertise state - structured as backend expects
  const [expertises, setExpertises] = useState<{
    married_civil_partners?: { expertises: string[]; other: string[] };
    cohabitees?: { expertises: string[]; other: string[] };
  }>({});

  // Pre-fill form when in edit mode
  useEffect(() => {
    if (mode === "edit" && lawyerData) {
      // Parse phone number to extract country code and phone number separately
      const { countryCode, dialCode: parsedDialCode, phoneNumber } = parsePhoneNumber(lawyerData.phone || "");
      
      setFormData({
        first_name: lawyerData.first_name || "",
        last_name: lawyerData.last_name || "",
        email: lawyerData.email || "",
        phone: phoneNumber,
        gender: lawyerData.gender || "",
        gender_other: lawyerData.gender_other || null,
        status: lawyerData.status || "Active",
        address_line_1: lawyerData.address_line_1 || null,
        address_line_2: lawyerData.address_line_2 || null,
        city: lawyerData.city || null,
        county: lawyerData.county || null,
        country: lawyerData.country || null,
        postal_code: lawyerData.postal_code || null,
        reg_no: lawyerData.reg_no || null,
        sra_number: lawyerData.sra_number || null,
        bar_number: lawyerData.bar_number || null,
        regulator: lawyerData.regulator || null,
        regulator_other: lawyerData.regulator_other || null,
        admitted_date_solicitor: lawyerData.admitted_date_solicitor || null,
        called_date_barrister: lawyerData.called_date_barrister || null,
        admitted_date_cliex: lawyerData.admitted_date_cliex || null,
        joined_at: lawyerData.joined_at || null,
        left_at: lawyerData.left_at || null,
        about: lawyerData.about || null,
        photo_url: lawyerData.photo_urls?.thumbnail || "",
        linkedin_url: lawyerData.linkedin_url || null,
        hourly_rate: lawyerData.hourly_rate || null,
        charge_first_consultation: lawyerData.charge_first_consultation || null,
        accredited_specialisms: lawyerData.accredited_specialisms || [],
        accredited_specialism_other: (() => {
          const raw = (lawyerData as any).accredited_specialism_other ?? lawyerData.accredited_specialism_other;
          if (Array.isArray(raw) && raw.length) return raw;
          if (raw != null && raw !== "") return [String(raw)];
          return null;
        })(),
        conflict_level_disinclination:
          lawyerData.conflict_level_disinclination || null,
        pi_insurance: lawyerData.pi_insurance || null,
        testimonial: lawyerData.testimonial || null,
        expert_types: lawyerData.expert_types || [],
        expert_types_other: lawyerData.expert_types_other || null,
        relationship_types: lawyerData.relationship_types || [],
        matter_types: lawyerData.matter_types ? mapValuesByOptions(lawyerData.matter_types, MATTER_TYPE_OPTIONS) : [],
        dr_preferences: lawyerData.dr_preferences || [],
        lawfirm_id: lawyerData.lawfirms?.id || "",
      });

      // Set country code and dial code from parsed phone number
      setSelectedCountryCode(countryCode);
      setDialCode(parsedDialCode);

      // Set law firm name consistently with lawfirm_id
      setSelectedLawFirmName(lawyerData.lawfirms?.name || "");

      // Initialize expertises from lawyerData
      if (lawyerData.expertises && typeof lawyerData.expertises === "object" && !Array.isArray(lawyerData.expertises)) {
        const expertiseData: typeof expertises = {};
        const expertisesObj = lawyerData.expertises as any;
        
        // Handle married_civil_partners
        if (expertisesObj.married_civil_partners) {
          const mcp = expertisesObj.married_civil_partners;
          expertiseData.married_civil_partners = {
            expertises: mcp.expertises || [],
            other: mcp.other || [],
          };
        }
        
        // Handle cohabitees
        if (expertisesObj.cohabitees) {
          const coh = expertisesObj.cohabitees;
          expertiseData.cohabitees = {
            expertises: coh.expertises || [],
            other: coh.other || [],
          };
        }
        
        setExpertises(expertiseData);
      }

      // Clear any selected image file when switching to edit mode
      setSelectedImageFile(null);
      setImagePreview(null);
      setIsUploadingImage(false);
      setUploadTokenResponse(null);
      setShowUploadOption(false); // Don't show upload option by default in edit mode
      setHasNewPhotoUpload(false); // Reset new photo upload flag in edit mode
      setPhotoRemoved(false); // Reset photo removed flag in edit mode
    } else if (mode === "add") {
      // Clear image file when switching to add mode
      setSelectedImageFile(null);
      setImagePreview(null);
      setIsUploadingImage(false);
      setUploadTokenResponse(null);
      setShowUploadOption(true); // Show upload option by default in add mode
      setHasNewPhotoUpload(false); // Reset new photo upload flag in add mode
      setPhotoRemoved(false); // Reset photo removed flag in add mode
    }
  }, [mode, lawyerData]);

  // Pre-fill form with legal expert data when onboarding
  useEffect(() => {
    if (mode === "add" && preFillData) {
      // Map expert types using key-based mapping
      const expertTypes = mapValuesByOptions(
        preFillData.professional_status?.values,
        EXPERT_TYPE_OPTIONS
      );
      // Handle special case: "Family Consultant or Divorce Coach" maps to both
      if (preFillData.professional_status?.values) {
        preFillData.professional_status.values.forEach((status) => {
          if (status === "Family Consultant or Divorce Coach") {
            const divorceCoach = mapValueByOptions("Divorce Coach", EXPERT_TYPE_OPTIONS);
            const familyConsultant = mapValueByOptions("Family Consultant", EXPERT_TYPE_OPTIONS);
            if (divorceCoach && !expertTypes.includes(divorceCoach)) expertTypes.push(divorceCoach);
            if (familyConsultant && !expertTypes.includes(familyConsultant)) expertTypes.push(familyConsultant);
          }
        });
      }

      // Map regulator using key-based mapping
      const mappedRegulator = preFillData.regulator 
        ? mapValueByOptions(preFillData.regulator, REGULATOR_OPTIONS) || "OTHER"
        : null;
      const mappedRegulatorOther = mappedRegulator === "OTHER" 
        ? (preFillData.regulator_other || (preFillData.regulator && !mapValueByOptions(preFillData.regulator, REGULATOR_OPTIONS) ? preFillData.regulator : null))
        : null;

      // Map DR preferences using key-based mapping
      const drPreferences = mapValuesByOptions(
        preFillData.dr_preferences,
        drOptions
      );

      // Map accredited specialisms using key-based mapping
      // Legal expert stores enum keys, MultiSelect expects enum keys
      let accreditedSpecialisms: string[] = [];
      if (preFillData.accredited_specialisations && preFillData.accredited_specialisations.length > 0) {
        // First try mapping (handles both enum keys and labels)
        accreditedSpecialisms = mapValuesByOptions(preFillData.accredited_specialisations, ACCREDITED_SPECIALISM_OPTIONS);
        // If mapping returns empty but we had values, preserve the original values (they might already be enum keys)
        if (accreditedSpecialisms.length === 0 && preFillData.accredited_specialisations.length > 0) {
          // Check if values are already valid enum keys and preserve them
          accreditedSpecialisms = preFillData.accredited_specialisations
            .map(val => {
              // Find matching option by value (case insensitive)
              const matchingOption = ACCREDITED_SPECIALISM_OPTIONS.find(opt => 
                opt.value === val || 
                opt.value.toLowerCase() === val.toLowerCase() ||
                opt.value === val.toUpperCase()
              );
              return matchingOption ? matchingOption.value : null;
            })
            .filter((val): val is string => val !== null);
        }
      }
      

      // Map relationship types from service_details.offers
      const relationshipTypes = mapValuesByOptions(
        preFillData.relationship_types,
        RELATIONSHIP_TYPE_OPTIONS
      );

      // Map matter types (if available in preFillData)
      const matterTypes = mapValuesByOptions(
        preFillData.matter_types,
        MATTER_TYPE_OPTIONS
      );

      // Map conflict level disinclination (if available)
      // Note: CustomSelect expects enum keys, but formData stores labels
      // We'll convert to label for formData, but CustomSelect can match by label
      const conflictLevelKey = preFillData.conflict_level_disinclination
        ? mapValueByOptions(preFillData.conflict_level_disinclination, CONFLICT_LEVEL_OPTIONS)
        : null;
      const conflictLevel: "Medium conflict" | "High Conflict" | "Implacable hostility" | null = conflictLevelKey
        ? (CONFLICT_LEVEL_OPTIONS.find(opt => opt.value === conflictLevelKey)?.label as "Medium conflict" | "High Conflict" | "Implacable hostility" | undefined) || null
        : null;

      // Map expertises from service_details
      const mappedExpertises: typeof expertises = {};
      if (preFillData.expertises) {
        // Handle married_civil_partners
        if (preFillData.expertises.married_civil_partners) {
          const mcp = preFillData.expertises.married_civil_partners;
          const expertiseOptions = EXPERTISE_OPTIONS["Married and Civil Partners"] || [];
          const mappedExpertisesList = mapValuesByOptions(mcp.expertises, expertiseOptions);
          const otherValues = Array.isArray(mcp.other) ? mcp.other.filter((v: string) => v && v.trim()) : [];
          
          // If there are "other" values, ensure "OTHER_MARRIED_CIVIL_PARTNERS" is in the expertises array
          const otherEnumValue = "OTHER_MARRIED_CIVIL_PARTNERS";
          const hasOther = otherValues.length > 0;
          const hasOtherInExpertises = mappedExpertisesList.includes(otherEnumValue);
          
          mappedExpertises.married_civil_partners = {
            expertises: hasOther && !hasOtherInExpertises 
              ? [...mappedExpertisesList, otherEnumValue]
              : mappedExpertisesList,
            other: otherValues,
          };
        }
        // Handle cohabitees
        if (preFillData.expertises.cohabitees) {
          const coh = preFillData.expertises.cohabitees;
          const expertiseOptions = EXPERTISE_OPTIONS["Cohabitees"] || [];
          const mappedExpertisesList = mapValuesByOptions(coh.expertises, expertiseOptions);
          const otherValues = Array.isArray(coh.other) ? coh.other.filter((v: string) => v && v.trim()) : [];
          
          // If there are "other" values, ensure "OTHER_COHABITEES" is in the expertises array
          const otherEnumValue = "OTHER_COHABITEES";
          const hasOther = otherValues.length > 0;
          const hasOtherInExpertises = mappedExpertisesList.includes(otherEnumValue);
          
          mappedExpertises.cohabitees = {
            expertises: hasOther && !hasOtherInExpertises 
              ? [...mappedExpertisesList, otherEnumValue]
              : mappedExpertisesList,
            other: otherValues,
          };
        }
      }

      // Handle expert_types_other
      const expertTypesOther = preFillData.professional_status?.other || null;

      // Parse phone number from legal expert to extract country code
      const { countryCode, dialCode: parsedDialCode, phoneNumber } = parsePhoneNumber(preFillData.phone || "");
      
      // Set country code and dial code from parsed phone number
      setSelectedCountryCode(countryCode);
      setDialCode(parsedDialCode);

      setFormData((prev) => ({
        ...prev,
        first_name: preFillData.first_name || "",
        last_name: preFillData.last_name || "",
        email: preFillData.email || "",
        phone: phoneNumber, // Use parsed phone number without country code
        gender: preFillData.gender || null,
        city: preFillData.city || null,
        postal_code: preFillData.postal_code || null,
        about: preFillData.about || null,
        testimonial: preFillData.testimonial || null,
        accredited_specialisms: accreditedSpecialisms,
        accredited_specialism_other: preFillData.accredited_specialism_other ?? null,
        regulator: mappedRegulator,
        regulator_other: mappedRegulatorOther,
        expert_types: expertTypes.length > 0 ? expertTypes : [],
        expert_types_other: expertTypesOther,
        dr_preferences: drPreferences.length > 0 ? drPreferences : [],
        relationship_types: relationshipTypes.length > 0 ? relationshipTypes : [],
        matter_types: matterTypes.length > 0 ? matterTypes : [],
        conflict_level_disinclination: conflictLevel,
        reference_id: preFillData.reference_id || null,
      }));

      // Set expertises state
      if (Object.keys(mappedExpertises).length > 0) {
        setExpertises(mappedExpertises);
      }

      // Set image preview if expert has a photo
      if (preFillData.photo_preview_url) {
        setImagePreview(preFillData.photo_preview_url);
        setShowUploadOption(false); // Don't show upload option initially if we have a preview
      }
    }
  }, [mode, preFillData]);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target;
    const requiredFields = [
      "first_name",
      "last_name",
      "email",
      "phone",
      "gender",
      "lawfirm_id",
    ];

    // Enforce 10-char limit for number fields (maxLength is ignored on type="number")
    const numLimitFields = ["hourly_rate", "charge_first_consultation"] as const;
    const isNumLimitField = numLimitFields.includes(name as typeof numLimitFields[number]);
    const cappedValue =
      type === "number" && isNumLimitField && value.length > 11
        ? value.slice(0, 11)
        : value;

    const processedValue =
      type === "number"
        ? cappedValue === ""
          ? null
          : parseFloat(cappedValue)
        : type === "datetime-local"
        ? value === ""
          ? null
          : new Date(value).toISOString()
        : type === "date" && (name === "joined_at" || name === "left_at")
        ? value === ""
          ? null
          : new Date(value + "T00:00:00").toISOString()
        : requiredFields.includes(name)
        ? value
        : value === ""
        ? null
        : value;

    setFormData((prev) => {
      const newData = { ...prev, [name]: processedValue };
      // Clear gender_other when gender changes (no longer needed with new enum)
      if (name === "gender") {
        newData.gender_other = null;
      }
      
      // Validate regulator when it changes
      if (name === "regulator") {
        // Clear regulator_other if regulator is not "OTHER"
        const regulatorValue = typeof processedValue === "string" ? processedValue : String(processedValue);
        const isOther = regulatorValue === "OTHER" || regulatorValue === "Other" || regulatorValue.toLowerCase() === "other";
        if (!isOther) {
          newData.regulator_other = null;
        }
        const validationErrors = validateRegulatorWithExpertTypes(
          prev.expert_types || [], 
          processedValue as string | null
        );
        setErrors((prevErrors) => ({ 
          ...prevErrors, 
          expert_types: validationErrors.expert_types || "",
          regulator: validationErrors.regulator || "",
          regulator_other: "" // Clear regulator_other error when regulator changes
        }));
      }
      
      return newData;
    });
    // Joined/left date range: joined date must not exceed left date
    if (name === "joined_at" || name === "left_at") {
      const joinedVal = name === "joined_at" ? processedValue : formData.joined_at;
      const leftVal = name === "left_at" ? processedValue : formData.left_at;
      const joinedTime = joinedVal ? new Date(joinedVal).getTime() : null;
      const leftTime = leftVal ? new Date(leftVal).getTime() : null;
      const dateRangeError = joinedTime != null && leftTime != null && joinedTime > leftTime
        ? "Joined date cannot be after left date"
        : "";
      setErrors((prev) => ({ ...prev, joined_at: dateRangeError, left_at: dateRangeError }));
    } else if (name === "postal_code") {
      setErrors((prev) => ({ ...prev, [name]: getPostalCodeError(value) }));
    } else if (Object.prototype.hasOwnProperty.call(VALIDATION, name)) {
      setErrors((prev) => ({ ...prev, [name]: getMaxLengthError(name as keyof typeof VALIDATION, value) }));
    } else if (errors[name] && name !== "regulator") {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const handleLawFirmChange = (firm: any) => {
    // Handle empty object (clearing selection)
    const firmId = firm?.id || "";
    const firmName = firm?.name || "";
    
    setFormData((prev) => ({ ...prev, lawfirm_id: firmId }));
    setSelectedLawFirmName(firmName);
    
    // Clear error when a valid firm is selected, keep/set error when cleared
    if (firmId && errors.lawfirm_id) {
      setErrors((prev) => ({ ...prev, lawfirm_id: "" }));
    }
  };

  // Handler for country code selection
  const handleCountryCodeChange = (countryCode: string, phoneDialCode: string) => {
    setSelectedCountryCode(countryCode);
    setDialCode(phoneDialCode);
  };

  // Validate regulator against expert types
  const validateRegulatorWithExpertTypes = (expertTypes: string[], regulator: string | null) => {
    const newErrors: { expert_types?: string; regulator?: string } = {};
    
    if (expertTypes && expertTypes.length > 0 && regulator) {
      const types = expertTypes.map(type => type.toLowerCase());
      const isSolicitor = types.includes("solicitor");
      const isBarrister = types.includes("barrister");
      const isCILEx = types.includes("cilex");
      
      // Check for conflicting expert types
      if ((isSolicitor || isCILEx) && isBarrister) {
        newErrors.expert_types = "A person cannot be both a Solicitor/Cilex and a Barrister (SRA and BSB conflict)";
      }
      
      // Validate regulator matches expert type
      if (isSolicitor && regulator !== "SRA") {
        newErrors.regulator = "Solicitor must be regulated by SRA";
      } else if (isBarrister && regulator !== "BSB") {
        newErrors.regulator = "Barrister must be regulated by BSB";
      } else if (isCILEx && regulator === "BSB") {
        newErrors.regulator = "Cilex cannot be regulated by BSB";
      }
    }
    
    return newErrors;
  };

  // Validate DR preferences for conflicts
  const validateDRPreferences = (drPreferences: string[]): { dr_preferences?: string } => {
    const newErrors: { dr_preferences?: string } = {};
    
    if (drPreferences && drPreferences.length > 0) {
      for (const preference of drPreferences) {
        // Find option by value or label (case-insensitive)
        const option = drOptions.find(
          (opt) =>
            opt.value === preference ||
            opt.label === preference ||
            opt.value?.toLowerCase() === preference?.toLowerCase() ||
            opt.label?.toLowerCase() === preference?.toLowerCase()
        );
        if (option && option.base && option.type) {
          const conflict = drOptions.find(
            (o) =>
              o.base === option.base &&
              o.type !== option.type &&
              o.value !== option.value &&
              o.label !== option.label &&
              (drPreferences.includes(o.value) ||
                drPreferences.includes(o.label) ||
                drPreferences.some(
                  (p) =>
                    p?.toLowerCase() === o.value?.toLowerCase() ||
                    p?.toLowerCase() === o.label?.toLowerCase()
                ))
          );
          if (conflict) {
            newErrors.dr_preferences = `Cannot select both ${option.label} and ${conflict.label}.`;
            break;
          }
        }
      }
    }
    
    return newErrors;
  };

  // Handler for expert types
  const handleExpertTypesChange = (selected: string[]) => {
    // Check if "OTHER" is still selected
    const hasOther = selected.some(
      (type) =>
        type === "OTHER" ||
        type === "Other" ||
        type?.toLowerCase() === "other"
    );
    
    setFormData((prev) => ({
      ...prev,
      expert_types: selected,
      // Clear expert_types_other if "Other" is not selected
      expert_types_other: hasOther ? prev.expert_types_other : null,
    }));
    if (errors.expert_types || errors.expert_types_other) {
      setErrors((prev) => ({ ...prev, expert_types: "", expert_types_other: "" }));
    }
    
    // Clear and re-validate regulator errors
    const validationErrors = validateRegulatorWithExpertTypes(selected, formData.regulator || null);
    setErrors((prev) => ({ 
      ...prev, 
      expert_types: validationErrors.expert_types || "",
      regulator: validationErrors.regulator || ""
    }));
  };

  // Handler for accredited specialisms
  const handleAccreditedSpecialismsChange = (selected: string[]) => {
    const hasOther = (selected || []).some(
      (s) => s === "OTHER" || s === "Other" || String(s).toLowerCase() === "other"
    );
    setFormData((prev) => ({
      ...prev,
      accredited_specialisms: selected,
      // Clear "other" values when "Other" is removed from selection to avoid save errors
      accredited_specialism_other: hasOther ? prev.accredited_specialism_other : null,
    }));
    if (errors.accredited_specialisms || errors.accredited_specialism_other) {
      setErrors((prev) => ({ ...prev, accredited_specialisms: "", accredited_specialism_other: "" }));
    }
  };

  // Handler for matter types
  const handleMatterTypesChange = (selected: string[]) => {
    setFormData((prev) => ({ ...prev, matter_types: selected }));
    if (errors.matter_types) {
      setErrors((prev) => ({ ...prev, matter_types: "" }));
    }
  };

  // Helper to get relationship type key from enum value or label
  const getRelationshipTypeKey = (relType: string): string | null => {
    // Check by enum value first
    if (relType === "MARRIED_CIVIL_PARTNERS" || relType === "Married and Civil Partners") {
      return "married_civil_partners";
    }
    if (relType === "COHABITEES" || relType === "Cohabitees") {
      return "cohabitees";
    }
    return null;
  };

  // Show Expertises heading only when at least one selected relationship type has expertise
  const hasAnyRelationshipTypeWithExpertise = (formData.relationship_types || []).some(
    (rel) => getRelationshipTypeKey(rel) !== null
  );

  // Helper to get relationship type label from enum value
  const getRelationshipTypeLabel = (relType: string): string => {
    const option = RELATIONSHIP_TYPE_OPTIONS.find(
      (opt) =>
        opt.value === relType ||
        opt.label === relType ||
        opt.value?.toLowerCase() === relType?.toLowerCase() ||
        opt.label?.toLowerCase() === relType?.toLowerCase()
    );
    return option?.label || relType;
  };

  // Handler for matter types
  const handleRelationshipTypesChange = (selected: string[]) => {
    setFormData((prev) => ({ ...prev, relationship_types: selected }));
    if (errors.relationship_types) {
      setErrors((prev) => ({ ...prev, relationship_types: "" }));
    }
    
    // Update expertises state when relationship types change
    const updatedExpertises: typeof expertises = {};
    
    selected.forEach((relType) => {
      const key = getRelationshipTypeKey(relType);
      
      if (key) {
        // Keep existing data if it exists, otherwise initialize
        const expertiseKey = key as "married_civil_partners" | "cohabitees";
        updatedExpertises[expertiseKey] = 
          expertises[expertiseKey] || { expertises: [], other: [] };
      }
    });
    
    // Remove expertises for unselected relationship types
    Object.keys(expertises).forEach((key) => {
      const relTypeEnumValue = key === "married_civil_partners" 
        ? "MARRIED_CIVIL_PARTNERS" 
        : "COHABITEES";
      const relTypeLabel = key === "married_civil_partners" 
        ? "Married and Civil Partners" 
        : "Cohabitees";
      // Check if this relationship type is still selected (by enum value or label)
      if (!selected.includes(relTypeEnumValue) && !selected.includes(relTypeLabel)) {
        const expertiseKey = key as "married_civil_partners" | "cohabitees";
        delete updatedExpertises[expertiseKey];
      }
    });
    
    setExpertises(updatedExpertises);
  };
  
  // Max selections for expertises (matching backend validation)
  const MAX_EXPERTISE_SELECTIONS = 5;

  // Helper: check if a value is the "Other" option for a given expertise key
  const isOtherExpertiseOption = (exp: string, expertiseKey: "married_civil_partners" | "cohabitees") => {
    const otherEnumValue = expertiseKey === "married_civil_partners"
      ? "OTHER_MARRIED_CIVIL_PARTNERS"
      : "OTHER_COHABITEES";
    return (
      exp === otherEnumValue ||
      exp === "Other" ||
      exp?.toLowerCase() === "other"
    );
  };

  // Handler for expertise selection
  const handleExpertisesChange = (
    relationshipType: string, // Can be enum value or label
    selectedExpertises: string[]
  ) => {
    const key = getRelationshipTypeKey(relationshipType);
    if (!key) return;
    
    const expertiseKey = key as "married_civil_partners" | "cohabitees";
    
    // Get the "Other" option value to exclude from count
    const otherEnumValue = expertiseKey === "married_civil_partners" 
      ? "OTHER_MARRIED_CIVIL_PARTNERS" 
      : "OTHER_COHABITEES";
    
    // Filter out "Other" option from count (it doesn't count toward max)
    const expertisesWithoutOther = selectedExpertises.filter(exp => 
      !isOtherExpertiseOption(exp, expertiseKey)
    );
    
    // "Other" is only allowed when 4 or fewer non-Other expertises are selected
    let finalExpertises = selectedExpertises;
    let clearOtherValues = false;
    if (expertisesWithoutOther.length >= 5) {
      const hasOther = selectedExpertises.some(exp => isOtherExpertiseOption(exp, expertiseKey));
      if (hasOther) {
        finalExpertises = selectedExpertises.filter(exp => !isOtherExpertiseOption(exp, expertiseKey));
        clearOtherValues = true;
      }
    }
    
    const finalWithoutOther = finalExpertises.filter(exp => !isOtherExpertiseOption(exp, expertiseKey));
    const currentOther = clearOtherValues ? [] : (expertises[expertiseKey]?.other || []);
    const totalSelections = finalWithoutOther.length + currentOther.length;
    
    // Validate max selections
    if (totalSelections > MAX_EXPERTISE_SELECTIONS) {
      const errorKey = `expertises_${key}`;
      setErrors((prev) => ({ 
        ...prev, 
        [errorKey]: `Maximum ${MAX_EXPERTISE_SELECTIONS} selections allowed (including other values)` 
      }));
      return; // Don't update if validation fails
    }
    
    // Clear error if validation passes
    const errorKey = `expertises_${key}`;
    setErrors((prev) => {
      const updated = { ...prev };
      if (updated[errorKey]) {
        delete updated[errorKey];
      }
      return updated;
    });
    
    // Include "Other" in expertises array (backend expects it)
    // Clear "other" values when "Other" is not selected (deselected or stripped)
    const hasOtherInSelection = finalExpertises.some(exp => isOtherExpertiseOption(exp, expertiseKey));
    setExpertises((prev) => ({
      ...prev,
      [expertiseKey]: {
        expertises: finalExpertises,
        other: hasOtherInSelection && !clearOtherValues ? (prev[expertiseKey]?.other || []) : [],
      },
    }));
  };
  
  // Handler for "Other" values (custom text inputs)
  const handleExpertiseOtherChange = (
    relationshipType: string, // Can be enum value or label
    otherValues: string[]
  ) => {
    const key = getRelationshipTypeKey(relationshipType);
    if (!key) return;
    
    const expertiseKey = key as "married_civil_partners" | "cohabitees";
    
    // Get the "Other" option value to exclude from count
    const otherEnumValue = expertiseKey === "married_civil_partners" 
      ? "OTHER_MARRIED_CIVIL_PARTNERS" 
      : "OTHER_COHABITEES";
    
    // Filter out "Other" option from count (it doesn't count toward max)
    const currentExpertises = expertises[expertiseKey]?.expertises || [];
    const expertisesWithoutOther = currentExpertises.filter(exp => 
      exp !== otherEnumValue && 
      exp !== "Other" && 
      exp?.toLowerCase() !== "other"
    );
    
    // Calculate total including expertises (excluding "Other" option itself)
    const totalSelections = expertisesWithoutOther.length + otherValues.length;
    
    // Validate max selections
    if (totalSelections > MAX_EXPERTISE_SELECTIONS) {
      const errorKey = `expertises_${key}`;
      setErrors((prev) => ({ 
        ...prev, 
        [errorKey]: `Maximum ${MAX_EXPERTISE_SELECTIONS} selections allowed (including other values)` 
      }));
      return; // Don't update if validation fails
    }
    
    // Clear error if validation passes
    const errorKey = `expertises_${key}`;
    setErrors((prev) => {
      const updated = { ...prev };
      if (updated[errorKey]) {
        delete updated[errorKey];
      }
      return updated;
    });
    
    setExpertises((prev) => ({
      ...prev,
      [expertiseKey]: {
        expertises: prev[expertiseKey]?.expertises || [],
        other: otherValues,
      },
    }));
  };

  // Handler for DR preferences
  const handleDRPreferencesChange = (selected: string[]) => {
    setFormData((prev) => ({ ...prev, dr_preferences: selected }));
    
    // Validate DR preferences and set errors
    const validationErrors = validateDRPreferences(selected);
    setErrors((prev) => ({ 
      ...prev, 
      dr_preferences: validationErrors.dr_preferences || ""
    }));
  };
  // Handler for image file upload
  const handleImageFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImageFile(file);
      setErrors((prev) => ({ ...prev, photo_url: "" }));
      setIsUploadingImage(true);
      setUploadTokenResponse(null);

      try {
        const result = await uploadImage({
          file,
          entityType: "lawyer_profile",
          maxSizeMB: 5,
          onProgress: (isUploading) => {
            setIsUploadingImage(isUploading);
          },
        });

        setImagePreview(result.previewUrl);
        setUploadTokenResponse({ success: true });
        setFormData((prev) => ({
          ...prev,
          photo_url: result.fileKey,
        }));
        setHasNewPhotoUpload(true);
        setPhotoRemoved(false); // Reset photo removed flag since a new one is uploaded
      } catch (error: any) {
        setErrors((prev) => ({
          ...prev,
          photo_url: error.message || "Failed to upload image. Please try again.",
        }));
        setSelectedImageFile(null);
        setImagePreview(null);
      } finally {
        setIsUploadingImage(false);
      }
    }
  };

  // Handler for removing selected image
  const handleRemoveImage = () => {
    setSelectedImageFile(null);
    setImagePreview(null);
    setFormData((prev) => ({
      ...prev,
      photo_url: null,
    }));
    setErrors((prev) => ({ ...prev, photo_url: "" }));
    setIsUploadingImage(false);
    setUploadTokenResponse(null);
    setShowUploadOption(true); // Show upload option after removing image
    setHasNewPhotoUpload(false); // Reset new photo upload flag
    setPhotoRemoved(true); // Mark photo as explicitly removed
  };

  // Handler for replacing photo (show upload option)
  const handleReplacePhoto = () => {
    setShowUploadOption(true);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.first_name.trim())
      newErrors.first_name = "First name is required";
    else if (formData.first_name.trim().length < 1)
      newErrors.first_name = "First name must be at least 1 character";
    else if (formData.first_name.length > VALIDATION.first_name)
      newErrors.first_name = limitError(VALIDATION.first_name);

    if (!formData.last_name.trim())
      newErrors.last_name = "Last name is required";
    else if (formData.last_name.trim().length < 1)
      newErrors.last_name = "Last name must be at least 1 character";
    else if (formData.last_name.length > VALIDATION.last_name)
      newErrors.last_name = limitError(VALIDATION.last_name);

    if (!formData.email.trim()) newErrors.email = "Email is required";
    else if (formData.email.length > VALIDATION.email)
      newErrors.email = limitError(VALIDATION.email);
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email))
      newErrors.email = "Invalid email";

    if (!formData.lawfirm_id.trim())
      newErrors.lawfirm_id = "Law firm is required";

    if (formData.linkedin_url && formData.linkedin_url.trim()) {
      if ((formData.linkedin_url ?? "").length > VALIDATION.linkedin_url) {
        newErrors.linkedin_url = limitError(VALIDATION.linkedin_url);
      } else {
        try {
          new URL(formData.linkedin_url);
        } catch {
          newErrors.linkedin_url = "Invalid URL";
        }
      }
    }

    // Only validate photo_url as URL if it's not a file_key (file_key doesn't start with http)
    if (
      formData.photo_url &&
      formData.photo_url.trim() &&
      formData.photo_url.startsWith("http")
    ) {
      try {
        new URL(formData.photo_url);
      } catch {
        newErrors.photo_url = "Invalid URL";
      }
    }

    // Postal code: max length and format (UK format: alphanumeric with spaces/hyphens, 3-10 chars)
    const postalCodeErr = getPostalCodeError(formData.postal_code);
    if (postalCodeErr) newErrors.postal_code = postalCodeErr;

    // Max length validations
    const phoneStr = formData.phone ?? "";
    if (phoneStr.length > VALIDATION.phone) newErrors.phone = limitError(VALIDATION.phone);
    if ((formData.pi_insurance ?? "").length > VALIDATION.pi_insurance) newErrors.pi_insurance = limitError(VALIDATION.pi_insurance);
    if ((formData.testimonial ?? "").length > VALIDATION.testimonial) newErrors.testimonial = limitError(VALIDATION.testimonial);
    if ((formData.city ?? "").length > VALIDATION.city) newErrors.city = limitError(VALIDATION.city);
    if ((formData.county ?? "").length > VALIDATION.county) newErrors.county = limitError(VALIDATION.county);
    if ((formData.reg_no ?? "").length > VALIDATION.reg_no) newErrors.reg_no = limitError(VALIDATION.reg_no);
    if ((formData.sra_number ?? "").length > VALIDATION.sra_number) newErrors.sra_number = limitError(VALIDATION.sra_number);
    if ((formData.bar_number ?? "").length > VALIDATION.bar_number) newErrors.bar_number = limitError(VALIDATION.bar_number);
    if ((formData.address_line_1 ?? "").length > VALIDATION.address_line_1) newErrors.address_line_1 = limitError(VALIDATION.address_line_1);
    if ((formData.address_line_2 ?? "").length > VALIDATION.address_line_2) newErrors.address_line_2 = limitError(VALIDATION.address_line_2);
    if ((formData.about ?? "").length > VALIDATION.about) newErrors.about = limitError(VALIDATION.about);
    if ((formData.linkedin_url ?? "").length > VALIDATION.linkedin_url) newErrors.linkedin_url = limitError(VALIDATION.linkedin_url);
    
    if (
      formData.hourly_rate != null &&
      (formData.hourly_rate < 0 || formData.hourly_rate > 10000)
    ) {
      newErrors.hourly_rate = "Must be between 0 and 10000";
    }

    if (
      formData.charge_first_consultation != null &&
      (formData.charge_first_consultation < 0 ||
        formData.charge_first_consultation > 10000)
    ) {
      newErrors.charge_first_consultation = "Must be between 0 and 10000";
    }

    // Expert types is required
    if (!formData.expert_types || formData.expert_types.length === 0) {
      newErrors.expert_types = "At least one expert type is required";
    }

    // Regulator is required
    if (!formData.regulator || !formData.regulator.trim()) {
      newErrors.regulator = "Regulator is required";
    }

    // Validate regulator_other is required when regulator is "OTHER"; max 255 chars
    const regulatorValue = typeof formData.regulator === "string" ? formData.regulator : String(formData.regulator || "");
    const isRegulatorOther = regulatorValue === "OTHER" || regulatorValue === "Other" || regulatorValue.toLowerCase() === "other";
    if (isRegulatorOther) {
      if (!formData.regulator_other || !formData.regulator_other.trim()) {
        newErrors.regulator_other = "Please specify the regulator";
      } else if (formData.regulator_other.length > VALIDATION.regulator_other) {
        newErrors.regulator_other = limitError(VALIDATION.regulator_other);
      }
    }

    // Validate expert_types_other is required when "Other" is selected in expert types; max 255 chars
    const hasExpertTypesOther = (formData.expert_types || []).some(
      (t) => t === "OTHER" || t === "Other" || String(t).toLowerCase() === "other"
    );
    if (hasExpertTypesOther) {
      if (!formData.expert_types_other || !formData.expert_types_other.trim()) {
        newErrors.expert_types_other = "Please specify the other expert type";
      } else if (formData.expert_types_other.length > VALIDATION.expert_types_other) {
        newErrors.expert_types_other = limitError(VALIDATION.expert_types_other);
      }
    }

    // Validate accredited_specialism_other is required when "Other" is selected; each value max 255 chars
    const hasAccreditedSpecialismOther = (formData.accredited_specialisms || []).some(
      (s) => s === "OTHER" || s === "Other" || String(s).toLowerCase() === "other"
    );
    if (hasAccreditedSpecialismOther) {
      const otherValues = formData.accredited_specialism_other ?? [];
      const hasValidOther = Array.isArray(otherValues) && otherValues.some((v) => v && String(v).trim());
      if (!hasValidOther) {
        newErrors.accredited_specialism_other = "Please add at least one other value when 'Other' is selected.";
      } else {
        const overLimit = otherValues.some((v) => v && String(v).length > 255);
        if (overLimit) {
          newErrors.accredited_specialism_other = limitError(255);
        }
      }
    }

    // Validate regulator according to expert type
    if (formData.expert_types && formData.expert_types.length > 0 && formData.regulator) {
      const expertTypes = formData.expert_types.map(type => type.toLowerCase());
      const isSolicitor = expertTypes.includes("Solicitor");
      const isBarrister = expertTypes.includes("Barrister");
      const isCILEx = expertTypes.includes("Cilex");
      
      // Check for conflicting expert types
      if ((isSolicitor || isCILEx) && isBarrister) {
        newErrors.expert_types = "A person cannot be both a Solicitor/Cilex and a Barrister (SRA and BSB conflict)";
      }
      
      // Validate regulator matches expert type
      if (isSolicitor && formData.regulator !== "SRA") {
        newErrors.regulator = "Solicitor must be regulated by SRA";
      } else if (isBarrister && formData.regulator !== "BSB") {
        newErrors.regulator = "Barrister must be regulated by BSB";
      } else if (isCILEx && formData.regulator === "BSB") {
        newErrors.regulator = "Cilex cannot be regulated by BSB";
      }
    }

    // Joined date must not be after left date (and vice versa)
    const joinedAt = formData.joined_at ? new Date(formData.joined_at).getTime() : null;
    const leftAt = formData.left_at ? new Date(formData.left_at).getTime() : null;
    if (joinedAt != null && leftAt != null && joinedAt > leftAt) {
      const dateRangeError = "Joined date cannot be after left date";
      newErrors.joined_at = dateRangeError;
      newErrors.left_at = dateRangeError;
    }

    // Validate DR preferences for conflicts
    const drValidationErrors = validateDRPreferences(formData.dr_preferences || []);
    if (drValidationErrors.dr_preferences) {
      newErrors.dr_preferences = drValidationErrors.dr_preferences;
    }

    // Validate expertises max selections (excluding "Other" option from count)
    if (expertises.married_civil_partners) {
      const expertisesWithoutOther = expertises.married_civil_partners.expertises.filter(exp => 
        exp !== "OTHER_MARRIED_CIVIL_PARTNERS" && 
        exp !== "Other" && 
        exp?.toLowerCase() !== "other"
      );
      const totalMarried = expertisesWithoutOther.length + expertises.married_civil_partners.other.length;
      if (totalMarried > MAX_EXPERTISE_SELECTIONS) {
        newErrors.expertises_married_civil_partners = `Maximum ${MAX_EXPERTISE_SELECTIONS} selections allowed for Married and Civil Partners (including other values)`;
      }
      const hasOtherSelected = expertises.married_civil_partners.expertises.some(exp =>
        exp === "OTHER_MARRIED_CIVIL_PARTNERS" || exp === "Other" || exp?.toLowerCase() === "other"
      );
      if (hasOtherSelected && (!expertises.married_civil_partners.other || expertises.married_civil_partners.other.length === 0) && !newErrors.expertises_married_civil_partners) {
        newErrors.expertises_married_civil_partners = "Please add at least one other expertise value when 'Other' is selected.";
      }
    }
    if (expertises.cohabitees) {
      const expertisesWithoutOther = expertises.cohabitees.expertises.filter(exp => 
        exp !== "OTHER_COHABITEES" && 
        exp.trim() !== "Other" && 
        exp?.toLowerCase().trim() !== "other"
      );
      const totalCohabitees = expertisesWithoutOther.length + expertises.cohabitees.other.length;
      if (totalCohabitees > MAX_EXPERTISE_SELECTIONS) {
        newErrors.expertises_cohabitees = `Maximum ${MAX_EXPERTISE_SELECTIONS} selections allowed for Cohabitees (including other values)`;
      }
      const hasOtherSelected = expertises.cohabitees.expertises.some(exp =>
        exp === "OTHER_COHABITEES" || exp?.trim() === "Other" || exp?.toLowerCase().trim() === "other"
      );
      if (hasOtherSelected && (!expertises.cohabitees.other || expertises.cohabitees.other.length === 0) && !newErrors.expertises_cohabitees) {
        newErrors.expertises_cohabitees = "Please add at least one other expertise value when 'Other' is selected.";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const hasValidationErrors = Object.values(errors).some((v) => v != null && v !== "");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate() || hasValidationErrors) {
      return;
    }

    setIsSubmitting(true);
    try {
      // Prepare form data
      const phoneNumber = formData.phone?.trim() ? combinePhoneNumber(dialCode, formData.phone) : '';
      
      let submitData = { 
        ...formData,
        phone: phoneNumber
      };

      // Convert empty string to null for gender to avoid backend validation error
      if (submitData.gender === "") {
        submitData.gender = null;
      }

      // Handle expert_types_other - ensure it's included and convert empty string to null
      if (submitData.expert_types_other !== undefined) {
        (submitData as any).expert_types_other = submitData.expert_types_other?.trim() || null;
      } else {
        (submitData as any).expert_types_other = null;
      }

      // Handle photo URL submission logic
      if (photoRemoved) {
        // Photo was explicitly removed - pass null
        (submitData as any).photo_url = null;
      } else if (hasNewPhotoUpload) {
        // New photo uploaded - keep the file key already in formData.photo_url
        // No change needed, submitData.photo_url already has the file key
      } else if (mode === "edit" && lawyerData) {
        // No changes to photo - pass the current photo URL
        submitData.photo_url = lawyerData.photo_urls?.thumbnail || null;
      } else if (mode === "add") {
        // In add mode with no photo uploaded
        submitData.photo_url = null;
      }

      // Convert expertises from labels to enum values before submission
      const convertedExpertises: typeof expertises = {};
      
      Object.keys(expertises).forEach((key) => {
        const expertiseGroup = expertises[key as keyof typeof expertises];
        if (expertiseGroup) {
          const relationshipType = key === "married_civil_partners" 
            ? "Married and Civil Partners" 
            : "Cohabitees";
          const expertiseOptions = EXPERTISE_OPTIONS[relationshipType as keyof typeof EXPERTISE_OPTIONS] || [];
          
          // Convert expertises array from labels to enum values
          const convertedExpertisesList = expertiseGroup.expertises.map((exp: string) => {
            const option = expertiseOptions.find(
              (opt) =>
                opt.value === exp ||
                opt.label === exp ||
                opt.value?.toLowerCase() === exp?.toLowerCase() ||
                opt.label?.toLowerCase() === exp?.toLowerCase()
            );
            return option?.value || exp;
          });
          
          convertedExpertises[key as keyof typeof convertedExpertises] = {
            expertises: convertedExpertisesList,
            other: expertiseGroup.other || [],
          };
        }
      });
      
      // Add expertises in the format backend expects
      (submitData as any).expertise = convertedExpertises;

      // Convert enum fields from labels to values before submission
      // Conflict Level Disinclination
      if (submitData.conflict_level_disinclination) {
        const conflictOptions = [
          { value: "MEDIUM_CONFLICT", label: "Medium conflict" },
          { value: "HIGH_CONFLICT", label: "High Conflict" },
          { value: "IMPLACABLE_HOSTILITY", label: "Implacable hostility" },
        ];
        const conflictOption = conflictOptions.find(
          (opt) =>
            opt.value === submitData.conflict_level_disinclination ||
            opt.label === submitData.conflict_level_disinclination ||
            opt.value?.toLowerCase() === submitData.conflict_level_disinclination?.toLowerCase() ||
            opt.label?.toLowerCase() === submitData.conflict_level_disinclination?.toLowerCase()
        );
        if (conflictOption) {
          (submitData as any).conflict_level_disinclination = conflictOption.value;
        }
      }

      // Convert expert_types from labels to values
      if (submitData.expert_types && submitData.expert_types.length > 0) {
        submitData.expert_types = submitData.expert_types.map((type: string) => {
          const option = EXPERT_TYPE_OPTIONS.find(
            (opt) =>
              opt.value === type ||
              opt.label === type ||
              opt.value?.toLowerCase() === type?.toLowerCase() ||
              opt.label?.toLowerCase() === type?.toLowerCase()
          );
          return option?.value || type;
        });
      }

      // Convert relationship_types from labels to values
      if (submitData.relationship_types && submitData.relationship_types.length > 0) {
        submitData.relationship_types = submitData.relationship_types.map((type: string) => {
          const option = RELATIONSHIP_TYPE_OPTIONS.find(
            (opt) =>
              opt.value === type ||
              opt.label === type ||
              opt.value?.toLowerCase() === type?.toLowerCase() ||
              opt.label?.toLowerCase() === type?.toLowerCase()
          );
          return option?.value || type;
        });
      }

      // Convert matter_types from labels to values
      if (submitData.matter_types && submitData.matter_types.length > 0) {
        submitData.matter_types = submitData.matter_types.map((type: string) => {
          const option = MATTER_TYPE_OPTIONS.find(
            (opt) =>
              opt.value === type ||
              opt.label === type ||
              opt.value?.toLowerCase() === type?.toLowerCase() ||
              opt.label?.toLowerCase() === type?.toLowerCase()
          );
          return option?.value || type;
        });
      }

      // Convert dr_preferences from labels to values
      if (submitData.dr_preferences && submitData.dr_preferences.length > 0) {
        submitData.dr_preferences = submitData.dr_preferences.map((pref: string) => {
          const option = drOptions.find(
            (opt) =>
              opt.value === pref ||
              opt.label === pref ||
              opt.value?.toLowerCase() === pref?.toLowerCase() ||
              opt.label?.toLowerCase() === pref?.toLowerCase()
          );
          return option?.value || pref;
        });
      }

      // Convert accredited_specialisms from labels to enum values
      if (submitData.accredited_specialisms && submitData.accredited_specialisms.length > 0) {
        submitData.accredited_specialisms = submitData.accredited_specialisms.map((spec: string) => {
          const option = ACCREDITED_SPECIALISM_OPTIONS.find(
            (opt) =>
              opt.value === spec ||
              opt.label === spec ||
              opt.value?.toLowerCase() === spec?.toLowerCase() ||
              opt.label?.toLowerCase() === spec?.toLowerCase()
          );
          return option?.value || spec;
        });
      }

      // Normalise accredited_specialism_other: trim and send as string[] or null
      const aso = submitData.accredited_specialism_other;
      const asoTrimmed = Array.isArray(aso) ? aso.map((s: string) => s?.trim()).filter(Boolean) : [];
      (submitData as any).accredited_specialism_other = asoTrimmed.length ? asoTrimmed : null;

      // Convert regulator from label to value
      if (submitData.regulator) {
        const regulatorOptions = [
          { value: "BSB", label: "BSB" },
          { value: "SRA", label: "SRA" },
          { value: "CILEX", label: "Cilex Regulation" },
          { value: "OTHER", label: "Other" },
        ];
        const regulatorOption = regulatorOptions.find(
          (opt) =>
            opt.value === submitData.regulator ||
            opt.label === submitData.regulator ||
            opt.value?.toLowerCase() === submitData.regulator?.toLowerCase() ||
            opt.label?.toLowerCase() === submitData.regulator?.toLowerCase()
        );
        if (regulatorOption) {
          submitData.regulator = regulatorOption.value;
          // Clear regulator_other if regulator is not OTHER
          if (regulatorOption.value !== "OTHER") {
            submitData.regulator_other = null;
          } else {
            // Ensure regulator_other is trimmed
            submitData.regulator_other = submitData.regulator_other?.trim() || null;
          }
        }
      } else {
        // Clear regulator_other if regulator is not set
        submitData.regulator_other = null;
      }

      // Convert gender from label to enum value
      if (submitData.gender) {
        const genderOptions = [
          { value: "MALE", label: "Male" },
          { value: "FEMALE", label: "Female" },
          { value: "NON_BINARY", label: "Non-Binary" },
          { value: "PREFER_NOT_TO_SAY", label: "Prefer not to say" },
        ];
        const genderOption = genderOptions.find(
          (opt) =>
            opt.value === submitData.gender ||
            opt.label === submitData.gender ||
            opt.value?.toLowerCase() === submitData.gender?.toLowerCase() ||
            opt.label?.toLowerCase() === submitData.gender?.toLowerCase()
        );
        if (genderOption) {
          submitData.gender = genderOption.label;
        }
      }

      // Ensure expert_types_other is explicitly included (like charge_first_consultation)
      (submitData as any).expert_types_other = formData.expert_types_other?.trim() || null;

      const success = await onSubmit(submitData, lawyerData?.id);
      if (success && mode === "add") {
        setFormData(initialFormState);
        setErrors({});
        setSelectedLawFirmName("");
        setSelectedImageFile(null);
        setImagePreview(null);
        setIsUploadingImage(false);
        setUploadTokenResponse(null);
        setShowUploadOption(true);
        setHasNewPhotoUpload(false);
        setPhotoRemoved(false);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClass = (error?: string) =>
    `w-full px-3 min-h-9 py-1 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 ${
      error ? "border-novaCaution-500" : "border-novaNeutral-300"
    }`;

  return (
    <div>
      <div className="mb-4 bg-white text-center rounded-lg border border-novaActive p-4">
        <h2 className="text-xl font-semibold text-novaNeutral-900">
          {mode === "edit" ? "Edit Expert" : preFillData ? "Onboard Nova Expert" : "Add new Expert"}
        </h2>
        <p className="mt-1 text-sm text-novaNeutral-500">
          {mode === "edit"
            ? "Update the Expert details below"
            : preFillData 
              ? "Review and complete the Expert profile using the Nova Expert's information"
              : "Fill in the details below to add a new Expert"}
        </p>
      </div>
      
      {/* Onboarding Notice Banner */}
      {mode === "add" && preFillData && (
        <div className="mb-4 bg-novaSuccess-50 border border-novaSuccess-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <i className="fas fa-info-circle text-novaSuccess-600 text-lg"></i>
            </div>
            <div>
              <h3 className="text-sm font-medium text-novaSuccess-800">
                Onboarding from Nova Expert Application
              </h3>
              <p className="text-xs text-novaSuccess-700 mt-1">
                The form has been pre-filled with data from the Nova Expert's application. 
                Please review all fields and complete any missing required information (marked with <span className="text-novaCaution-500">*</span>), 
                especially the Law Firm/Chambers field which is required.
              </p>
            </div>
          </div>
        </div>
      )}
    <div className="bg-white rounded-lg border border-novaActive p-10">
      <form onSubmit={handleSubmit}
      onKeyDown={(e) => {
        if (e.key === "Enter" && (e.target as HTMLElement).tagName !== "TEXTAREA") {
          e.preventDefault();
        }
      }}
      className="space-y-4">
        <div className="border-b border-novaActive pb-10">
          <h3 className="text-md font-semibold text-novaNeutral-600 mb-3">
            Personal Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                First Name <span className="text-novaCaution-500">*</span>
              </label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className={inputClass(errors.first_name)}
                placeholder="John"
                maxLength={101}
              />
              {errors.first_name && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.first_name}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Last Name <span className="text-novaCaution-500">*</span>
              </label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className={inputClass(errors.last_name)}
                placeholder="Doe"
                maxLength={101}
              />
              {errors.last_name && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.last_name}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Email <span className="text-novaCaution-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={inputClass(errors.email)}
                placeholder="user@example.com"
                maxLength={256}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Phone
              </label>
              <div className="grid grid-cols-[100px_1fr] gap-2">
                <PhoneCountryCodeSelect
                  className="h-[36px]"
                  value={selectedCountryCode}
                  onChange={handleCountryCodeChange}
                  disabled={isSubmitting}
                />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone || ""}
                  onInput={(e) => {
                    // Only allow numbers and spaces
                    const value = e.currentTarget.value.replace(/[^0-9\s]/g, "");
                    e.currentTarget.value = value;
                    handleChange(e as any);
                  }}
                  className={inputClass(errors.phone)}
                  placeholder="123 456 7890"
                  maxLength={18}
                />
              </div>
              {errors.phone && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.phone}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Gender
              </label>
              <CustomSelect
                value={formData.gender || ""}
                onChange={(value) =>
                  handleChange({
                    target: { name: "gender", value, type: "text" },
                  } as React.ChangeEvent<HTMLInputElement>)
                }
                options={[
                  { value: "MALE", label: "Male" },
                  { value: "FEMALE", label: "Female" },
                  { value: "NON_BINARY", label: "Non-Binary" },
                  { value: "PREFER_NOT_TO_SAY", label: "Prefer not to say" },
                ]}
                placeholder="Select gender"
                error={!!errors.gender}
                triggerClassName="rounded-md h-[36px]"
              />
              {errors.gender && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.gender}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Status
              </label>
              <CustomSelect
                value={formData.status || "Active"}
                onChange={(value) =>
                  handleChange({
                    target: { name: "status", value, type: "text" },
                  } as React.ChangeEvent<HTMLInputElement>)
                }
                options={[
                  { value: "Active", label: "Active" },
                  { value: "Deactive", label: "Inactive" },
                ]}
                placeholder="Select status"
                error={!!errors.status}
                triggerClassName="rounded-md h-[36px]"
              />
            </div>

          </div>
        </div>

        {/* Address Information */}
        <div className="border-b border-novaActive pt-4 py-10">
          <h3 className="text-md font-semibold text-novaNeutral-600 mb-3">
            Address Information
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Address Line 1
              </label>
              <textarea
                name="address_line_1"
                value={formData.address_line_1 || ""}
                onChange={handleChange}
                className={inputClass(errors.address_line_1)}
                placeholder="123 Main Street"
                maxLength={256}
                rows={4}
              />
              {errors.address_line_1 && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.address_line_1}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Address Line 2
              </label>
              <textarea
                name="address_line_2"
                value={formData.address_line_2 || ""}
                onChange={handleChange}
                className={inputClass(errors.address_line_2)}
                placeholder="Suite 100"
                maxLength={256}
                rows={4}
              />
              {errors.address_line_2 && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.address_line_2}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                City
              </label>
              <input
                type="text"
                name="city"
                value={formData.city || ""}
                onChange={handleChange}
                className={inputClass(errors.city)}
                placeholder="London"
                maxLength={101}
              />
              {errors.city && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.city}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                County
              </label>
              <input
                type="text"
                name="county"
                value={formData.county || ""}
                onChange={handleChange}
                className={inputClass(errors.county)}
                placeholder="Greater London"
                maxLength={101}
              />
              {errors.county && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.county}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Country
              </label>
              <CountrySelect
                value={formData.country || null}
                onChange={(value) =>
                  handleChange({
                    target: { name: "country", value, type: "text" },
                  } as React.ChangeEvent<HTMLInputElement>)
                }
                error={errors.country}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Postal Code
              </label>
              <input
                type="text"
                name="postal_code"
                value={formData.postal_code || ""}
                onChange={handleChange}
                className={inputClass(errors.postal_code)}
                placeholder="SW1A 1AA"
                maxLength={21}
              />
              {errors.postal_code && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.postal_code}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Professional Information */}
        <div className="border-b border-novaActive pt-4 py-10">
          <h3 className="text-md font-semibold text-novaNeutral-600 mb-3">
            Professional Information
          </h3>
          <div className="grid grid-cols-1 gap-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4">
            {/* Expert Types - Updated to use MultiSelect */}
            <div >
              <MultiSelect
                label="Expert Types"
                required={true}
                options={EXPERT_TYPE_OPTIONS}
                selected={formData.expert_types || []}
                onChange={handleExpertTypesChange}
                error={errors.expert_types}
                placeholder="Select expert types..."
              />
            </div>

            {/* Expert Types Other - Space always reserved; content shown when "Other" is selected */}
              {formData.expert_types && formData.expert_types.some(
                (type) =>
                  type === "OTHER" ||
                  type === "Other" ||
                  type?.toLowerCase() === "other"
              ) && (
                <div>
                  <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Specify Other Expert Type<span className="text-novaCaution-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="expert_types_other"
                    value={formData.expert_types_other || ""}
                    onChange={handleChange}
                    className={inputClass(errors.expert_types_other)}
                    placeholder="Please specify other expert type"
                    maxLength={256}
                  />
                  {errors.expert_types_other && (
                    <p className="mt-1 text-xs text-novaCaution-500">
                      {errors.expert_types_other}
                    </p>
                  )}
                </div>
              )}

            {/* Accredited Specialisms */}
            <div>
              <MultiSelect
                label="Accredited Specialisms"
                options={ACCREDITED_SPECIALISM_OPTIONS}
                selected={formData.accredited_specialisms || []}
                onChange={handleAccreditedSpecialismsChange}
                error={errors.accredited_specialisms}
                placeholder="Select accredited specialisms..."
              />
            </div>

            {/* Accredited Specialisms Other - Space always reserved; content shown when "Other" is selected */}
              {formData.accredited_specialisms && formData.accredited_specialisms.some(
                (type) =>
                  type === "OTHER" ||
                  type === "Other" ||
                  type?.toLowerCase() === "other"
              ) && (
                <div>
                  <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Specify Other Accredited Specialism <span className="text-novaNeutral-500 text-xs">(Press Enter to add each value)</span><span className="text-novaCaution-500">*</span>
                  </label>
                  <TagInput
                    values={formData.accredited_specialism_other ?? []}
                    onChange={(tags) => {
                      setFormData((prev) => ({
                        ...prev,
                        accredited_specialism_other: tags.length ? tags : null,
                      }));
                      const overLimit = tags.some((t) => t && String(t).length > 255);
                      setErrors((prev) => ({
                        ...prev,
                        accredited_specialism_other: overLimit ? limitError(255) : "",
                      }));
                    }}
                    placeholder="Type and press Enter to add"
                  />
                  {errors.accredited_specialism_other && (
                    <p className="mt-1 text-xs text-novaCaution-500">
                      {errors.accredited_specialism_other}
                    </p>
                  )}
                </div>
              )}

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Regulator <span className="text-novaCaution-500">*</span>
              </label>
              <CustomSelect
                value={formData.regulator || ""}
                onChange={(value) =>
                  handleChange({
                    target: { name: "regulator", value, type: "text" },
                  } as React.ChangeEvent<HTMLInputElement>)
                }
                options={[
                  { value: "BSB", label: "BSB" },
                  { value: "SRA", label: "SRA" },
                  { value: "CILEX", label: "Cilex Regulation" },
                  { value: "OTHER", label: "Other" },
                ]}
                placeholder="Select regulator"
                error={!!errors.regulator}
                triggerClassName="rounded-md h-[36px]"
              />
              {errors.regulator && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.regulator}
                </p>
              )}
            </div>

            {/* Regulator Other - Show when "OTHER" is selected */}
            <div>
            {formData.regulator && (
              formData.regulator === "OTHER" ||
              formData.regulator === "Other" ||
              (typeof formData.regulator === "string" && formData.regulator.toLowerCase() === "other")
            ) && (
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Specify Regulator <span className="text-novaCaution-500">*</span>
                </label>
                <input
                  type="text"
                  name="regulator_other"
                  value={formData.regulator_other || ""}
                  onChange={handleChange}
                  className={inputClass(errors.regulator_other)}
                  placeholder="Please specify other regulator"
                  maxLength={256}
                />
                {errors.regulator_other && (
                  <p className="mt-1 text-xs text-novaCaution-500">
                    {errors.regulator_other}
                  </p>
                )}
              </div>
            )}
            </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-novaActive pt-6">
            {/* Admitted Date CILEx */}
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Admitted Date (Cilex)
              </label>
              <input
                type="date"
                name="admitted_date_cliex"
                value={formData.admitted_date_cliex || ""}
                onChange={handleChange}
                className={inputClass()}
                max={new Date().toISOString().split("T")[0]}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Registration Number
              </label>
              <input
                type="text"
                name="reg_no"
                value={formData.reg_no || ""}
                onChange={handleChange}
                className={inputClass(errors.reg_no)}
                placeholder="REG123456"
                maxLength={101}
              />
              {errors.reg_no && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.reg_no}</p>
              )}
            </div>
            {/* Admitted Date Solicitor */}
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Admitted Date (Solicitor)
              </label>
              <input
                type="date"
                name="admitted_date_solicitor"
                value={formData.admitted_date_solicitor || ""}
                onChange={handleChange}
                className={inputClass()}
                max={new Date().toISOString().split("T")[0]}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                SRA Number
              </label>
              <input
                type="text"
                name="sra_number"
                value={formData.sra_number || ""}
                onChange={handleChange}
                className={inputClass(errors.sra_number)}
                placeholder="SRA123456"
                maxLength={101}
              />
              {errors.sra_number && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.sra_number}</p>
              )}
            </div>

            {/* Called Date Barrister */}
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Called Date (Barrister)
              </label>
              <input
                type="date"
                name="called_date_barrister"
                value={formData.called_date_barrister || ""}
                onChange={handleChange}
                className={inputClass()}
                max={new Date().toISOString().split("T")[0]}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Bar Number
              </label>
              <input
                type="text"
                name="bar_number"
                value={formData.bar_number || ""}
                onChange={handleChange}
                className={inputClass(errors.bar_number)}
                placeholder="BAR123456"
                maxLength={101}
              />
              {errors.bar_number && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.bar_number}</p>
              )}
            </div>

            {/* Joined At */}
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Joined At
              </label>
              <input
                type="date"
                name="joined_at"
                value={
                  formData.joined_at && formData.joined_at !== null
                    ? new Date(formData.joined_at).toISOString().split("T")[0]
                    : ""
                }
                onChange={handleChange}
                className={inputClass(errors.joined_at)}
                max={new Date().toISOString().split("T")[0]}
              />
              {errors.joined_at && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.joined_at}</p>
              )}
            </div>

            {/* Left At */}
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Left At
              </label>
              <input
                type="date"
                name="left_at"
                value={
                  formData.left_at && formData.left_at !== null
                    ? new Date(formData.left_at).toISOString().split("T")[0]
                    : ""
                }
                onChange={handleChange}
                className={inputClass(errors.left_at)}
                max={new Date().toISOString().split("T")[0]}
              />
              {errors.left_at && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.left_at}</p>
              )}
            </div>
           
            <div className="">
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Law Firm/Chambers{" "}
                <span className="text-novaCaution-500">*</span>
              </label>
              <LawFirmSearch
                value={selectedLawFirmName}
                onChange={handleLawFirmChange}
                error={errors.lawfirm_id}
              />
              {errors.lawfirm_id && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.lawfirm_id}
                </p>
              )}
            </div>


            {/* Relationship Types */}
            <div>
              <MultiSelect
                label="Relationship Types"
                options={RELATIONSHIP_TYPE_OPTIONS}
                selected={formData.relationship_types || []}
                onChange={handleRelationshipTypesChange}
                error={errors.relationship_types}
                placeholder="Select Relationship types"
              />
            </div>

            {/* Expertises - Show only when at least one selected relationship type has expertise (hide when only Parental relationships) */}
            {hasAnyRelationshipTypeWithExpertise && (
              <div className="md:col-span-2 space-y-4">
                <div className=" py-4">
                  <h4 className="text-sm font-semibold text-novaNeutral-700 mb-3">
                    Expertises
                  </h4>
                  <div className="space-y-4">
                    {(formData.relationship_types || []).map((relType) => {
                      // Get the key for this relationship type (works with enum value or label)
                      const key = getRelationshipTypeKey(relType);
                      
                      // Only show for Married and Civil Partners or Cohabitees
                      if (!key) {
                        return null;
                      }
                      
                      // Get the label for display
                      const relTypeLabel = getRelationshipTypeLabel(relType);
                      
                      // Get expertise options - use label as key for EXPERTISE_OPTIONS
                      const expertiseOptionsKey = key === "married_civil_partners" 
                        ? "Married and Civil Partners" 
                        : "Cohabitees";
                      const expertiseOptions = EXPERTISE_OPTIONS[expertiseOptionsKey as keyof typeof EXPERTISE_OPTIONS] || [];
                      const expertiseKey = key as "married_civil_partners" | "cohabitees";
                      const currentExpertises = expertises[expertiseKey]?.expertises || [];
                      const currentOther = expertises[expertiseKey]?.other || [];
                      
                      // Check if "Other" is selected in the current expertises
                      const otherEnumValue = key === "married_civil_partners" 
                        ? "OTHER_MARRIED_CIVIL_PARTNERS" 
                        : "OTHER_COHABITEES";
                      const otherInExpertises = currentExpertises.includes("Other") || 
                        currentExpertises.includes(otherEnumValue) ||
                        currentExpertises.some((exp: string) => 
                          exp?.toLowerCase() === "other" || 
                          exp?.toLowerCase() === otherEnumValue?.toLowerCase()
                        );
                      const expertisesWithoutOtherCount = currentExpertises.filter(exp =>
                        !isOtherExpertiseOption(exp, expertiseKey)
                      ).length;
                      const effectiveExpertiseCount = expertisesWithoutOtherCount + currentOther.length;

                      return (
                        <div 
                          key={relType}
                          className="bg-white rounded-lg p-4 border border-novaActive"
                        >
                          <div className="mb-3">
                            <label className="block text-xs font-semibold text-novaNeutral-700 mb-2">
                              {relTypeLabel}
                            </label>
                            <div className="bg-white rounded-md">
                              <MultiSelect
                                label=""
                                options={expertiseOptions}
                                selected={currentExpertises}
                                onChange={(selected) => handleExpertisesChange(relType, selected)}
                                error={errors[`expertises_${key}`]}
                                placeholder={`Select expertises for ${relTypeLabel}...`}
                                maxSelections={MAX_EXPERTISE_SELECTIONS}
                                selectedCount={effectiveExpertiseCount}
                              />
                            </div>
                          </div>
                          
                          {/* Show "Other" input if "Other" is selected */}
                          {(otherInExpertises || currentOther.length > 0) && (
                            <div className="mt-3">
                              <label className="block text-xs font-medium text-novaNeutral-700 mb-2">
                                Other Expertises <span className="text-novaNeutral-500 text-xs">(Press Enter to add each value)</span><span className="text-novaCaution-500">*</span>
                              </label>
                              <div className="bg-white rounded-md">
                                <TagInput
                                  values={currentOther}
                                  onChange={(tags: string[]) => handleExpertiseOtherChange(relType, tags)}
                                  placeholder="Enter other expertises (e.g., Family Law, Divorce) and press Enter to add each value."
                                  maxValues={(() => {
                                    // Exclude "Other" option from count when calculating max values
                                    const expertisesWithoutOther = currentExpertises.filter(exp => 
                                      exp !== otherEnumValue && 
                                      exp !== "Other" && 
                                      exp?.toLowerCase() !== "other"
                                    );
                                    return MAX_EXPERTISE_SELECTIONS - expertisesWithoutOther.length;
                                  })()}
                                />
                              </div>
                              <p className="text-xs text-novaNeutral-500 mt-1">
                                Add custom expertise values.
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Matter Types - Updated to use MultiSelect */}
            <div>
              <MultiSelect
                label="Matter Types"
                options={MATTER_TYPE_OPTIONS}
                selected={formData.matter_types || []}
                onChange={handleMatterTypesChange}
                error={errors.matter_types}
                placeholder="Select matters types..."
              />
            </div>


            {/* DR Preferences */}
            <div>
            <MultiSelect
              label="DR Preferences"
              options={drOptions.map(opt => ({ value: opt.value, label: opt.label }))}
              selected={formData.dr_preferences || []}
              onChange={handleDRPreferencesChange}
              error={errors.dr_preferences}
              placeholder="Select DR preferences..."
            />
          </div>
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Hourly Rate (£)
              </label>
              <input
                type="number"
                name="hourly_rate"
                value={formData.hourly_rate ?? ""}
                onChange={handleChange}
                className={inputClass(errors.hourly_rate)}
                placeholder="150"
                min="0"
                max="10000"
                step="0.01"
                maxLength={11}
              />
              {errors.hourly_rate && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.hourly_rate}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                First Consultation Charge (£)
              </label>
              <input
                type="number"
                name="charge_first_consultation"
                value={formData.charge_first_consultation ?? ""}
                onChange={handleChange}
                className={inputClass(errors.charge_first_consultation)}
                placeholder="50"
                min="0"
                max="10000"
                step="0.01"
                maxLength={11}
              />
              {errors.charge_first_consultation && (
                <p className="mt-1 text-xs text-novaCaution-500">
                  {errors.charge_first_consultation}
                </p>
              )}
            </div>
            </div>
          </div>
        </div>

        {/* Additional Information */}
        <div className="border-b border-novaActive pt-4 py-10">
          <h3 className="text-md font-semibold text-novaNeutral-600 mb-3">
            Additional Information
          </h3>
          <div className="grid grid-cols-1 gap-3">
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                About
              </label>
              <textarea
                name="about"
                value={formData.about || ""}
                onChange={handleChange}
                rows={4}
                maxLength={1501}
                className={inputClass(errors.about)}
                placeholder="Experienced family law specialist with 10+ years of practice"
              />
              {errors.about && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.about}</p>
              )}
            </div>

            {/* Accredited Specialisations */}
            {/* <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Accredited Specialisations
              </label>
              <input
                type="text"
                name="accredited_specialisations"
                value={formData.accredited_specialisations || ""}
                onChange={handleChange}
                className={inputClass()}
                placeholder="Family Law, Divorce, Child Custody"
              />
            </div> */}

            {/* Testimonial */}
            <div>
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                Testimonial
              </label>
              <textarea
                name="testimonial"
                value={formData.testimonial || ""}
                onChange={handleChange}
                rows={4}
                maxLength={501}
                className={inputClass(errors.testimonial)}
                placeholder="Excellent service and professional approach"
              />
              {errors.testimonial && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.testimonial}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Profile Photo
                </label>

                {/* Show existing photo in edit mode OR uploaded/expert image preview */}
                {imagePreview || (formData.photo_url && !showUploadOption) ? (
                  <div className="mb-3">
                    <div className="relative inline-block">
                      <img
                        src={imagePreview || formData.photo_url || ""}
                        alt="Photo preview"
                        className="w-20 h-20 rounded-full object-cover border border-novaDarkOrange"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                      <button
                        type="button"
                        onClick={handleRemoveImage}
                        className="absolute -top-2 -right-2 bg-novaCaution-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-novaCaution-600 transition-colors"
                        title="Remove image"
                      >
                        <i className="fas fa-times"></i>
                      </button>
                    </div>
                    {(mode === "edit" && formData.photo_url && !showUploadOption) ||
                    (mode === "add" && imagePreview && !showUploadOption && preFillData) ? (
                        <div className="mt-2">
                          <button
                            type="button"
                            onClick={handleReplacePhoto}
                            className="text-xs text-novaPrimary-600 hover:text-novaPrimary-700 font-medium"
                          >
                            <i className="fas fa-edit mr-1"></i>
                            Replace Photo
                          </button>
                        </div>
                      ) : null}
                  </div>
                ) : (
                  /* Show upload option when no photo exists or when replacing */
                  <div className="mb-3">
                    <input
                      type="file"
                      id="photo-upload"
                      accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                      onChange={handleImageFileChange}
                      className="hidden"
                      disabled={isUploadingImage}
                    />
                    <label
                      htmlFor="photo-upload"
                      className={`inline-flex items-center px-3 py-2 border rounded-md text-sm font-medium transition-colors ${
                        isUploadingImage
                          ? "border-novaNeutral-300 text-novaNeutral-400 bg-novaNeutral-100 cursor-not-allowed"
                          : "border-novaNeutral-300 text-novaNeutral-700 bg-white hover:bg-novaNeutral-50 cursor-pointer"
                      }`}
                    >
                      {isUploadingImage ? (
                        <>
                          <i className="fas fa-spinner fa-spin mr-2 text-novaPrimary-500"></i>
                          Getting upload token...
                        </>
                      ) : uploadTokenResponse ? (
                        <>
                          <i className="fas fa-check mr-2 text-novaSuccess-500"></i>
                          Upload ready
                        </>
                      ) : (
                        <>
                          <i className="fas fa-upload mr-2 text-novaPrimary-500"></i>
                          Upload Image
                        </>
                      )}
                    </label>
                    <p className="text-xs text-novaNeutral-500 mt-1">
                      JPEG, PNG, GIF, WebP (max 5MB)
                    </p>
                    {isUploadingImage && (
                      <p className="text-xs text-novaPrimary-600 mt-1">
                        <i className="fas fa-info-circle mr-1"></i>
                        Getting upload token...
                      </p>
                    )}
                    {uploadTokenResponse && (
                      <p className="text-xs text-novaSuccess-600 mt-1">
                        <i className="fas fa-check-circle mr-1"></i>
                        Upload token received successfully
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  LinkedIn URL
                </label>
                <input
                  type="url"
                  name="linkedin_url"
                  value={formData.linkedin_url || ""}
                  onChange={handleChange}
                  className={inputClass(errors.linkedin_url)}
                  placeholder="https://linkedin.com/in/lawyer-name"
                  maxLength={256}
                />
                {errors.linkedin_url && (
                  <p className="mt-1 text-xs text-novaCaution-500">
                    {errors.linkedin_url}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Conflict Level Disinclination
                </label>
                <CustomSelect
                  value={formData.conflict_level_disinclination || ""}
                  onChange={(value) => {
                    // CustomSelect passes enum key, but formData stores label
                    // Convert enum key to label
                    const conflictOption = CONFLICT_LEVEL_OPTIONS.find(opt => opt.value === value);
                    const labelValue = conflictOption?.label || value;
                    handleChange({
                      target: { name: "conflict_level_disinclination", value: labelValue, type: "text" },
                    } as React.ChangeEvent<HTMLInputElement>);
                  }}
                  options={CONFLICT_LEVEL_OPTIONS}
                  placeholder="Select conflict level"
                  triggerClassName="rounded-md h-[36px]"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  PI Insurance
                </label>
                <input
                  type="text"
                  name="pi_insurance"
                  value={formData.pi_insurance || ""}
                  onChange={handleChange}
                  className={inputClass(errors.pi_insurance)}
                  placeholder="Policy: PI123456, Expires: 2024-12-31"
                  maxLength={101}
                />
                {errors.pi_insurance && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.pi_insurance}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-2 pt-2">
          <FormButton
            variant="custom"
            type="button"
            onClick={onCancel}
            disabled={isSubmitting || isUploadingImage}
            className="px-4 py-2 text-sm border border-novaNeutral-500 bg-white hover:bg-novaBlack text-novaNeutral-700 hover:text-white"
          >
            Cancel
          </FormButton>
          <FormButton
            type="submit"
            variant="gradient"
            disabled={isSubmitting || isUploadingImage || hasValidationErrors}
            className="px-4 py-2 text-sm"
          >
            {isUploadingImage ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                Uploading image...
              </>
            ) : isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                {mode === "edit" ? "Saving..." : "Creating..."}
              </>
            ) : (
              <>
                <i
                  className={`fas ${
                    mode === "edit" ? "fa-save" : "fa-plus"
                  } mr-2`}
                ></i>
                {mode === "edit" ? "Save Changes" : "Create Expert"}
              </>
            )}
          </FormButton>
        </div>
      </form>
      </div>
    </div>
  );
};

export default AddLawyerForm;
