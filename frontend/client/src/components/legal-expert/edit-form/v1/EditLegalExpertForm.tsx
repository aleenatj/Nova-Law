import React, { useState, useEffect } from "react";
import { LegalExpert, LegalExpertFormData, LegalExpertStatus } from "@/lib/types";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import MultiSelect from "@/components/ui/multi-select/v1/MultiSelect";
import { FormButton } from "@/utils/formComponents";
import { lawyerSignupConfig } from "@/config/lawyer-signup-config";
import { uploadImage } from "@/lib/utils";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";
import { TagInput } from "@/components/ui/taginput/v1/TagInput";

interface EditLegalExpertFormProps {
  expertData: LegalExpert;
  onCancel: () => void;
  onSubmit: (data: LegalExpertFormData, expertId?: string) => Promise<boolean>;
}

// Type for config fields (since the config doesn't export types)
interface ConfigField {
  id: number;
  label: string;
  type: string;
  options?: string[];
  maxLength?: number | { [key: string]: number };
  maxSelections?: number;
  required?: boolean;
  [key: string]: unknown;
}

// Helper function to get field by ID from config
const getFieldById = (fieldId: number): ConfigField | null => {
  for (const section of lawyerSignupConfig.sections) {
    for (const field of section.fields) {
      if (field.id === fieldId) {
        return field as ConfigField;
      }
    }
  }
  return null;
};

// Extract options from config
const workStatusField = getFieldById(39);
const genderField = getFieldById(31);
const professionalStatusField = getFieldById(23);
const regulatorField = getFieldById(40);
const accreditedSpecialistField = getFieldById(19);
const remoteConsultationField = getFieldById(37);
const consultationOffersField = getFieldById(36);
const ncdrMagicField = getFieldById(18);
const clientTypesField = getFieldById(27);
const marriedCouplesField = getFieldById(9);
const cohabiteesField = getFieldById(29);
const ncdrDescriptionField = getFieldById(11);
const compellingQuoteField = getFieldById(14);
const firmNameField = getFieldById(38);
const cityField = getFieldById(34);
const firstNameField = getFieldById(1);
const emailField = getFieldById(20);
const phoneField = getFieldById(21);
const regulatorOtherField = getFieldById(46);
const professionalStatusOtherField = getFieldById(3);

// Helper function to normalize options format
// Handles: strings, objects with {value, label}, and nested object structures
const normalizeOptions = (options: any[]): Array<{ value: string; label: string }> => {
  if (!options || !Array.isArray(options)) return [];
  
  const normalized: Array<{ value: string; label: string }> = [];
  
  options.forEach((option) => {
    // Handle string format (backward compatibility)
    if (typeof option === "string") {
      normalized.push({ value: option, label: option });
    }
    // Handle object with value and label
    else if (option && typeof option === "object" && option.value && option.label) {
      normalized.push({ value: option.value, label: option.label });
    }
    // Handle nested object structure (like NCDR Services - array with one object containing multiple keys)
    else if (option && typeof option === "object" && !option.value) {
      // This is a nested object structure - extract all values
      Object.keys(option).forEach((key) => {
        const nestedOption = option[key];
        if (nestedOption && nestedOption.value && nestedOption.label) {
          normalized.push({ value: nestedOption.value, label: nestedOption.label });
        }
      });
    }
  });
  
  return normalized;
};

// Convert options to select format
const toSelectOptions = (options: string[] | undefined) => 
  (options || []).map(opt => ({ value: opt, label: opt }));

// Get options from config
const WORK_STATUS_OPTIONS = toSelectOptions(workStatusField?.options);
const GENDER_OPTIONS = toSelectOptions(genderField?.options);
const PROFESSIONAL_STATUS_OPTIONS = normalizeOptions(professionalStatusField?.options || []);
const REGULATOR_OPTIONS = normalizeOptions(regulatorField?.options || []);
const ACCREDITED_SPECIALIST_OPTIONS = normalizeOptions(accreditedSpecialistField?.options || []);
const REMOTE_CONSULTATION_OPTIONS = toSelectOptions(remoteConsultationField?.options);
// const CONSULTATION_OFFERS_OPTIONS = normalizeOptions(consultationOffersField?.options || []);
const NCDR_MAGIC_OPTIONS = normalizeOptions(ncdrMagicField?.options || []);
const CLIENT_TYPES_OPTIONS = normalizeOptions(clientTypesField?.options || []);
const MARRIED_COUPLES_OPTIONS = normalizeOptions(marriedCouplesField?.options || []);
const COHABITEES_OPTIONS = normalizeOptions(cohabiteesField?.options || []);

// Expertise options for each relationship type (matching lawyer page structure)
const EXPERTISE_OPTIONS = {
  "Married and Civil Partners": MARRIED_COUPLES_OPTIONS,
  "Cohabitees": COHABITEES_OPTIONS,
};

// Matter Types mapping (from backend enum)
const MATTER_TYPES_MAP: Record<string, string> = {
  "FINANCIAL_CLAIMS": "Financial Claims",
  "CHILDREN": "Children",
};

// Helper function to map matter type keys to display values
const getMatterTypeLabel = (key: string): string => {
  return MATTER_TYPES_MAP[key] || key;
};

// Manual max length limits (same approach as navigator/lawfirm/lawyer forms)
const VALIDATION = {
  firstName: { maxLength: 100 },
  lastName: { maxLength: 100 },
  email: { maxLength: 255 },
  phone: { maxLength: 17 },
  firmName: { maxLength: 100 },
  city: { maxLength: 100 },
  postCode: { maxLength: 20 },
  ncdrDescription: { maxLength: 1500 },
  compellingQuote: { maxLength: 500 },
  workStatus: { maxLength: 100 },
  regulatorOther: { maxLength: 255 },
  professionalStatusOther: { maxLength: 255 },
  experience: { maxLength: 10 },
  marriedCouplesServices: { maxSelections: marriedCouplesField?.maxSelections || 5 },
  cohabiteesServices: { maxSelections: cohabiteesField?.maxSelections || 5 },
};

// Shared limit error message (same as navigator/lawfirm/lawyer forms)
const limitError = (max: number) => `Character limit exceeded (max ${max} characters)`;

const STATUS_OPTIONS = [
  { value: "New", label: "New" },
  { value: "Review", label: "Review" },
  { value: "Onboarded", label: "Onboarded" },
  { value: "Rejected", label: "Rejected" },
];

const EditLegalExpertForm: React.FC<EditLegalExpertFormProps> = ({
  expertData,
  onCancel,
  onSubmit,
}) => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    work_status: "",
    firm_name: "",
    city: "",
    post_code: "",
    gender: "",
    photo_url: "",
    professional_status_values: [] as string[],
    professional_status_other: "",
    experience: null as number | null,
    regulator_value: "",
    regulator_other: "",
    accredited_specialist: [] as string[],
    accredited_specialism_other: [] as string[],
    remote_consultation: "",
    // consultation_offers: [] as string[],
    ncdr_magic: [] as string[],
    ncdr_description: "",
    compelling_quote: "",
    client_types: [] as string[],
    married_couples_services: [] as string[],
    married_couples_other: [] as string[],
    cohabitees_services: [] as string[],
    cohabitees_other: [] as string[],
    status: "New" as LegalExpertStatus,
  });
  // Expertises state (matching lawyer page structure)
  const [expertises, setExpertises] = useState<{
    married_civil_partners?: { expertises: string[]; other: string[] };
    cohabitees?: { expertises: string[]; other: string[] };
  }>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Phone country code states
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");
  
  // Photo upload states
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [uploadTokenResponse, setUploadTokenResponse] = useState<any>(null);
  const [showUploadOption, setShowUploadOption] = useState(false);
  const [hasNewPhotoUpload, setHasNewPhotoUpload] = useState(false);

  // Pre-fill form with expert data
  useEffect(() => {
    if (expertData) {
      // Parse phone number to extract country code and phone number separately
      const { countryCode, dialCode: parsedDialCode, phoneNumber } = parsePhoneNumber(expertData.phone || "");
      
      setFormData({
        first_name: expertData.first_name || "",
        last_name: expertData.last_name || "",
        email: expertData.email || "",
        phone: phoneNumber,
        work_status: expertData.work_status || "",
        firm_name: expertData.firm_name || "",
        city: expertData.city || "",
        post_code: expertData.post_code || "",
        gender: expertData.gender || "",
        photo_url: expertData.photo_url?.thumbnail || "",
        professional_status_values: (() => {
          const values = expertData.professional_status?.values || [];
          // Map "OTHER" to the option value from PROFESSIONAL_STATUS_OPTIONS
          const mappedValues = values.map((v: string) => {
            if (v === "OTHER" || v === "Other") {
              // Find the "Other" option in normalized options
              const otherOption = PROFESSIONAL_STATUS_OPTIONS.find(opt => 
                opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
              );
              return otherOption?.value || "Other";
            }
            // Try to find matching option
            const matchingOption = PROFESSIONAL_STATUS_OPTIONS.find(opt => 
              opt.value === v || opt.label === v
            );
            return matchingOption?.value || v;
          });
          // If there's an "other" value but "Other" is not in the values, add it
          if (expertData.professional_status?.other) {
            const otherOption = PROFESSIONAL_STATUS_OPTIONS.find(opt => 
              opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
            );
            const otherValue = otherOption?.value || "Other";
            if (!mappedValues.includes(otherValue)) {
              return [...mappedValues, otherValue];
            }
          }
          return mappedValues;
        })(),
        professional_status_other: expertData.professional_status?.other || "",
        experience: expertData.experience || null,
        regulator_value: (() => {
          const regulatorVal = expertData.regulator?.values?.[0];
          // If there's an "other" value, prioritize finding "Other" option
          if (expertData.regulator?.other) {
            const otherOption = REGULATOR_OPTIONS.find(opt => 
              opt.value === "OTHER" || 
              opt.value === "Other" || 
              opt.label === "Other" ||
              (typeof opt.value === 'string' && opt.value.toLowerCase() === "other") ||
              (typeof opt.label === 'string' && opt.label.toLowerCase() === "other")
            );
            if (otherOption) {
              return otherOption.value;
            }
          }
          // Map "OTHER" to the correct option value from REGULATOR_OPTIONS
          if (regulatorVal === "OTHER" || regulatorVal === "Other") {
            const otherOption = REGULATOR_OPTIONS.find(opt => 
              opt.value === "OTHER" || 
              opt.value === "Other" || 
              opt.label === "Other" ||
              (typeof opt.value === 'string' && opt.value.toLowerCase() === "other") ||
              (typeof opt.label === 'string' && opt.label.toLowerCase() === "other")
            );
            return otherOption?.value || regulatorVal;
          }
          if (regulatorVal) {
            // Try to find matching option by value or label (case-insensitive)
            const matchingOption = REGULATOR_OPTIONS.find(opt => 
              opt.value === regulatorVal || 
              opt.label === regulatorVal ||
              (typeof opt.value === 'string' && typeof regulatorVal === 'string' && opt.value.toLowerCase() === regulatorVal.toLowerCase()) ||
              (typeof opt.label === 'string' && typeof regulatorVal === 'string' && opt.label.toLowerCase() === regulatorVal.toLowerCase())
            );
            return matchingOption?.value || regulatorVal;
          }
          return "";
        })(),
        regulator_other: expertData.regulator?.other || "",
        accredited_specialist: expertData.accredited_specialist?.values || [],
        accredited_specialism_other: (expertData.accredited_specialism_other && Array.isArray(expertData.accredited_specialism_other))
          ? expertData.accredited_specialism_other
          : [],
        remote_consultation: expertData.remote_consultation || "",
        // consultation_offers: expertData.consultation_offers?.values || [],
        ncdr_magic: (() => {
          const values = expertData.ncdr_magic?.values || [];
          // Map values to option values from normalized options
          return values.map((val: string) => {
            const matchingOption = NCDR_MAGIC_OPTIONS.find(opt => 
              opt.value === val || 
              opt.label === val ||
              (typeof opt.value === 'string' && typeof val === 'string' && opt.value.toLowerCase() === val.toLowerCase()) ||
              (typeof opt.label === 'string' && typeof val === 'string' && opt.label.toLowerCase() === val.toLowerCase())
            );
            return matchingOption?.value || val;
          });
        })(),
        ncdr_description: expertData.ncdr_description || "",
        compelling_quote: expertData.compelling_quote || "",
        // Derive client_types from service_details (handle both old and new format)
        client_types: (() => {
          // New format with offers array
          if (expertData.service_details?.offers && Array.isArray(expertData.service_details.offers)) {
            return expertData.service_details.offers.map((offer: string) => {
              // Map enum values to display names
              if (offer === "MARRIED_CIVIL_PARTNERS") return "Married and civil partners";
              if (offer === "COHABITEES") return "Cohabitees";
              if (offer === "PARENTAL_RELATIONSHIPS") return "Parental relationships";
              return offer;
            });
          }
          // Old format (backward compatibility)
          const types: string[] = [];
          if (expertData.service_details?.["Married and civil partners"]?.length) {
            types.push("Married and civil partners");
          }
          if (expertData.service_details?.["Cohabitees"]?.length) {
            types.push("Cohabitees");
          }
          return types;
        })(),
        married_couples_services: [] as string[], // Keep for backward compatibility but will use expertises state
        married_couples_other: [] as string[], // Keep for backward compatibility but will use expertises state
        cohabitees_services: [] as string[], // Keep for backward compatibility but will use expertises state
        cohabitees_other: [] as string[], // Keep for backward compatibility but will use expertises state
        status: expertData.status || "New",
      });
      
      // Initialize expertises state from service_details
      const initialExpertises: typeof expertises = {};
      
      // Married couples expertises
      if (expertData.service_details?.married_civil_partners && typeof expertData.service_details.married_civil_partners === 'object' && !Array.isArray(expertData.service_details.married_civil_partners)) {
        const marriedData = expertData.service_details.married_civil_partners as { expertises?: string[]; other?: string[] };
        const expertisesData = marriedData.expertises || [];
        const otherData = marriedData.other || [];
        // Map enum values to option values from normalized options
        const mappedExpertises = expertisesData.map((val: string) => {
          const matchingOption = MARRIED_COUPLES_OPTIONS.find(opt => 
            opt.value === val || 
            opt.label === val ||
            (typeof opt.value === 'string' && typeof val === 'string' && opt.value.toLowerCase() === val.toLowerCase()) ||
            (typeof opt.label === 'string' && typeof val === 'string' && opt.label.toLowerCase() === val.toLowerCase())
          );
          return matchingOption?.value || val;
        });
        initialExpertises.married_civil_partners = {
          expertises: mappedExpertises,
          other: otherData,
        };
      } else if (expertData.service_details?.["Married couples and civil partners"]) {
        // Old format (backward compatibility)
        const oldValues = expertData.service_details["Married couples and civil partners"] || [];
        const mappedExpertises = oldValues.map((val: string) => {
          const matchingOption = MARRIED_COUPLES_OPTIONS.find(opt => 
            opt.value === val || 
            opt.label === val ||
            (typeof opt.value === 'string' && typeof val === 'string' && opt.value.toLowerCase() === val.toLowerCase()) ||
            (typeof opt.label === 'string' && typeof val === 'string' && opt.label.toLowerCase() === val.toLowerCase())
          );
          return matchingOption?.value || val;
        });
        initialExpertises.married_civil_partners = {
          expertises: mappedExpertises,
          other: [],
        };
      }
      
      // Cohabitees expertises
      if (expertData.service_details?.cohabitees && typeof expertData.service_details.cohabitees === 'object' && !Array.isArray(expertData.service_details.cohabitees)) {
        const cohabiteesData = expertData.service_details.cohabitees as { expertises?: string[]; other?: string[] };
        const expertisesData = cohabiteesData.expertises || [];
        const otherData = cohabiteesData.other || [];
        // Map enum values to option values from normalized options
        const mappedExpertises = expertisesData.map((val: string) => {
          const matchingOption = COHABITEES_OPTIONS.find(opt => 
            opt.value === val || 
            opt.label === val ||
            (typeof opt.value === 'string' && typeof val === 'string' && opt.value.toLowerCase() === val.toLowerCase()) ||
            (typeof opt.label === 'string' && typeof val === 'string' && opt.label.toLowerCase() === val.toLowerCase())
          );
          return matchingOption?.value || val;
        });
        initialExpertises.cohabitees = {
          expertises: mappedExpertises,
          other: otherData,
        };
      } else if (expertData.service_details?.["Cohabitees"]) {
        // Old format (backward compatibility)
        const oldValues = expertData.service_details["Cohabitees"] || [];
        const mappedExpertises = oldValues.map((val: string) => {
          const matchingOption = COHABITEES_OPTIONS.find(opt => 
            opt.value === val || 
            opt.label === val ||
            (typeof opt.value === 'string' && typeof val === 'string' && opt.value.toLowerCase() === val.toLowerCase()) ||
            (typeof opt.label === 'string' && typeof val === 'string' && opt.label.toLowerCase() === val.toLowerCase())
          );
          return matchingOption?.value || val;
        });
        initialExpertises.cohabitees = {
          expertises: mappedExpertises,
          other: [],
        };
      }
      
      setExpertises(initialExpertises);

      // Set country code and dial code from parsed phone number
      setSelectedCountryCode(countryCode);
      setDialCode(parsedDialCode);

      // Reset photo upload states for edit mode
      setSelectedImageFile(null);
      setImagePreview(null);
      setIsUploadingImage(false);
      setUploadTokenResponse(null);
      setShowUploadOption(false); // Don't show upload option by default in edit mode
      setHasNewPhotoUpload(false);
    }
  }, [expertData]);

  // Field name -> max length (must match VALIDATION.*.maxLength for each field)
  const fieldLimits: Record<string, number> = {
    first_name: VALIDATION.firstName.maxLength,
    last_name: VALIDATION.lastName.maxLength,
    email: VALIDATION.email.maxLength,
    phone: VALIDATION.phone.maxLength,
    firm_name: VALIDATION.firmName.maxLength,
    city: VALIDATION.city.maxLength,
    post_code: VALIDATION.postCode.maxLength,
    ncdr_description: VALIDATION.ncdrDescription.maxLength,
    compelling_quote: VALIDATION.compellingQuote.maxLength,
    professional_status_other: VALIDATION.professionalStatusOther.maxLength,
    regulator_other: VALIDATION.regulatorOther.maxLength,
    experience: VALIDATION.experience.maxLength,
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    // Enforce 10-char limit for experience (maxLength ignored on type="number")
    const experienceLimit = 10;
    const cappedValue =
      type === "number" && name === "experience" && typeof value === "string" && value.length > experienceLimit
        ? value.slice(0, experienceLimit)
        : value;
    const processedValue = type === "number" ? (cappedValue === "" ? null : parseFloat(String(cappedValue))) : value;
    setFormData((prev) => ({ ...prev, [name]: processedValue }));
    const max = fieldLimits[name];
    if (max !== undefined) {
      const str = typeof value === "string" ? value : String(value ?? "");
      setErrors((prev) => ({ ...prev, [name]: str.length > max ? limitError(max) : "" }));
    } else if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  // Helper to get relationship type key from enum value or label
  const getRelationshipTypeKey = (relType: string): string | null => {
    // Check by enum value first
    if (relType === "MARRIED_CIVIL_PARTNERS" || relType === "Married couples and civil partners" || relType === "Married and Civil Partners" || relType === "Married and civil partners") {
      return "married_civil_partners";
    }
    if (relType === "COHABITEES" || relType === "Cohabitees") {
      return "cohabitees";
    }
    return null;
  };

  // Show Expertises and Matter Types only when at least one selected client type has expertise
  const hasAnyRelationshipTypeWithExpertise = (formData.client_types || []).some(
    (rel) => getRelationshipTypeKey(rel) !== null
  );

  // Helper to get relationship type label from enum value
  const getRelationshipTypeLabel = (relType: string): string => {
    const option = CLIENT_TYPES_OPTIONS.find(
      (opt) =>
        opt.value === relType ||
        opt.label === relType ||
        opt.value?.toLowerCase() === relType?.toLowerCase() ||
        opt.label?.toLowerCase() === relType?.toLowerCase()
    );
    return option?.label || relType;
  };

  // Handler for relationship types change (client types)
  const handleRelationshipTypesChange = (selected: string[]) => {
    setFormData((prev) => ({ ...prev, client_types: selected }));
    if (errors.client_types) {
      setErrors((prev) => ({ ...prev, client_types: "" }));
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
        ? "Married couples and civil partners" 
        : "Cohabitees";
      // Check if this relationship type is still selected (by enum value or label)
      if (!selected.includes(relTypeEnumValue) && !selected.includes(relTypeLabel) && !selected.includes("Married and Civil Partners") && !selected.includes("Married and civil partners")) {
        const expertiseKey = key as "married_civil_partners" | "cohabitees";
        delete updatedExpertises[expertiseKey];
      }
    });
    
    setExpertises(updatedExpertises);
  };

  // Helper: check if a value is the "Other" option for a given expertise key (excluded from total count)
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
    const maxSelections = expertiseKey === "married_civil_partners" 
      ? VALIDATION.marriedCouplesServices.maxSelections 
      : VALIDATION.cohabiteesServices.maxSelections;
    const errorKey = expertiseKey === "married_civil_partners" 
      ? "married_couples_services" 
      : "cohabitees_services";
    
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
    
    if (totalSelections > maxSelections) {
      setErrors((prev) => ({ 
        ...prev, 
        [errorKey]: `Maximum ${maxSelections} selections allowed (including other values)` 
      }));
      return;
    }
    
    setErrors((prev) => ({ ...prev, [errorKey]: "" }));
    
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
    const maxSelections = expertiseKey === "married_civil_partners" 
      ? VALIDATION.marriedCouplesServices.maxSelections 
      : VALIDATION.cohabiteesServices.maxSelections;
    const errorKey = expertiseKey === "married_civil_partners" 
      ? "married_couples_services" 
      : "cohabitees_services";
    
    // Filter out "Other" option from count (it doesn't count toward max)
    const currentExpertises = expertises[expertiseKey]?.expertises || [];
    const expertisesWithoutOther = currentExpertises.filter(exp => 
      !isOtherExpertiseOption(exp, expertiseKey)
    );
    const totalSelections = expertisesWithoutOther.length + otherValues.length;
    
    if (totalSelections > maxSelections) {
      setErrors((prev) => ({ 
        ...prev, 
        [errorKey]: `Maximum ${maxSelections} selections allowed (including other values)` 
      }));
      return;
    }
    
    setErrors((prev) => ({ ...prev, [errorKey]: "" }));
    
    setExpertises((prev) => ({
      ...prev,
      [expertiseKey]: {
        expertises: prev[expertiseKey]?.expertises || [],
        other: otherValues,
      },
    }));
  };

  // Handler for country code selection
  const handleCountryCodeChange = (countryCode: string, phoneDialCode: string) => {
    setSelectedCountryCode(countryCode);
    setDialCode(phoneDialCode);
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
          entityType: "b2c_expert_profile",
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
      photo_url: "",
    }));
    setErrors((prev) => ({ ...prev, photo_url: "" }));
    setIsUploadingImage(false);
    setUploadTokenResponse(null);
    setShowUploadOption(true);
    setHasNewPhotoUpload(false);
  };

  // Handler for replacing photo (show upload option)
  const handleReplacePhoto = () => {
    setShowUploadOption(true);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields
    if (!formData.first_name.trim()) newErrors.first_name = "First name is required";
    if (!formData.last_name.trim()) newErrors.last_name = "Last name is required";
    if (!formData.email.trim()) newErrors.email = "Email is required";
    if (!formData.phone.trim()) newErrors.phone = "Phone is required";
    if (!formData.work_status) newErrors.work_status = "Work status is required";
    // Firm name is required when work status is not freelance
    if (formData.work_status && !formData.work_status.toLowerCase().includes("freelance") && !formData.firm_name.trim()) {
      newErrors.firm_name = "Organisation name is required";
    }
    if (!formData.city.trim()) newErrors.city = "City is required";
    if (!formData.post_code.trim()) newErrors.post_code = "Post code is required";

    // Max length validations (same message as other forms)
    if (formData.first_name.length > VALIDATION.firstName.maxLength) {
      newErrors.first_name = limitError(VALIDATION.firstName.maxLength);
    }
    if (formData.last_name.length > VALIDATION.lastName.maxLength) {
      newErrors.last_name = limitError(VALIDATION.lastName.maxLength);
    }
    if (formData.email.length > VALIDATION.email.maxLength) {
      newErrors.email = limitError(VALIDATION.email.maxLength);
    }
    if (formData.phone.length > VALIDATION.phone.maxLength) {
      newErrors.phone = limitError(VALIDATION.phone.maxLength);
    }
    if (formData.firm_name.length > VALIDATION.firmName.maxLength) {
      newErrors.firm_name = limitError(VALIDATION.firmName.maxLength);
    }
    if (formData.city.length > VALIDATION.city.maxLength) {
      newErrors.city = limitError(VALIDATION.city.maxLength);
    }
    if (formData.post_code.length > VALIDATION.postCode.maxLength) {
      newErrors.post_code = limitError(VALIDATION.postCode.maxLength);
    }
    if (formData.ncdr_description.length > VALIDATION.ncdrDescription.maxLength) {
      newErrors.ncdr_description = limitError(VALIDATION.ncdrDescription.maxLength);
    }
    if (formData.compelling_quote.length > VALIDATION.compellingQuote.maxLength) {
      newErrors.compelling_quote = limitError(VALIDATION.compellingQuote.maxLength);
    }
    if (formData.professional_status_other.length > VALIDATION.professionalStatusOther.maxLength) {
      newErrors.professional_status_other = limitError(VALIDATION.professionalStatusOther.maxLength);
    }
    if (formData.regulator_other.length > VALIDATION.regulatorOther.maxLength) {
      newErrors.regulator_other = limitError(VALIDATION.regulatorOther.maxLength);
    }
    if (formData.experience != null && String(formData.experience).length > VALIDATION.experience.maxLength) {
      newErrors.experience = limitError(VALIDATION.experience.maxLength);
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Postal code format validation
    const postcodeRegex = /^[A-Z0-9\s\-]{3,20}$/i;
    if (formData.post_code && !postcodeRegex.test(formData.post_code.trim())) {
      newErrors.post_code = "Please enter a valid postal code";
    }

    // Max selections validations for expertises (exclude "Other" option from count; require at least one custom value when "Other" selected)
    if (expertises.married_civil_partners) {
      const expertisesWithoutOther = expertises.married_civil_partners.expertises.filter(exp =>
        exp !== "OTHER_MARRIED_CIVIL_PARTNERS" && exp !== "Other" && exp?.toLowerCase() !== "other"
      );
      const totalMarried = expertisesWithoutOther.length + (expertises.married_civil_partners.other?.length || 0);
      if (totalMarried > VALIDATION.marriedCouplesServices.maxSelections) {
        newErrors.married_couples_services = `Maximum ${VALIDATION.marriedCouplesServices.maxSelections} selections allowed (including other values)`;
      }
      const hasOtherSelected = expertises.married_civil_partners.expertises.some(exp =>
        exp === "OTHER_MARRIED_CIVIL_PARTNERS" || exp === "Other" || exp?.toLowerCase() === "other"
      );
      if (hasOtherSelected && (!expertises.married_civil_partners.other || expertises.married_civil_partners.other.length === 0) && !newErrors.married_couples_services) {
        newErrors.married_couples_services = "Please add at least one other expertise value when 'Other' is selected.";
      }
    }
    if (expertises.cohabitees) {
      const expertisesWithoutOther = expertises.cohabitees.expertises.filter(exp =>
        exp !== "OTHER_COHABITEES" && exp?.trim() !== "Other" && exp?.toLowerCase().trim() !== "other"
      );
      const totalCohabitees = expertisesWithoutOther.length + (expertises.cohabitees.other?.length || 0);
      if (totalCohabitees > VALIDATION.cohabiteesServices.maxSelections) {
        newErrors.cohabitees_services = `Maximum ${VALIDATION.cohabiteesServices.maxSelections} selections allowed (including other values)`;
      }
      const hasOtherSelected = expertises.cohabitees.expertises.some(exp =>
        exp === "OTHER_COHABITEES" || exp?.trim() === "Other" || exp?.toLowerCase().trim() === "other"
      );
      if (hasOtherSelected && (!expertises.cohabitees.other || expertises.cohabitees.other.length === 0) && !newErrors.cohabitees_services) {
        newErrors.cohabitees_services = "Please add at least one other expertise value when 'Other' is selected.";
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
      // Build service_details in new format with offers, cohabitees, and married_civil_partners
      const service_details: {
        offers: string[];
        cohabitees?: { expertises: string[]; other: string[] };
        married_civil_partners?: { expertises: string[]; other: string[] };
      } = {
        offers: formData.client_types.map((type: string) => {
          // Map display names to enum values
          if (type === "Married and civil partners") return "MARRIED_CIVIL_PARTNERS";
          if (type === "Cohabitees") return "COHABITEES";
          if (type === "Parental relationships") return "PARENTAL_RELATIONSHIPS";
          return type;
        }),
      };

      // Process expertises from expertises state (matching lawyer page structure)
      if (expertises.married_civil_partners) {
        const marriedOtherOptionValue = "OTHER_MARRIED_CIVIL_PARTNERS";
        const expertisesList = expertises.married_civil_partners.expertises.filter((s: string) => s !== marriedOtherOptionValue);
        const other = expertises.married_civil_partners.other || [];
        // Only add if there are expertises or other values
        if (expertisesList.length > 0 || other.length > 0) {
          service_details.married_civil_partners = {
            expertises: expertisesList,
            other: other,
          };
        }
      }

      if (expertises.cohabitees) {
        const cohabiteesOtherOptionValue = "OTHER_COHABITEES";
        const expertisesList = expertises.cohabitees.expertises.filter((s: string) => s !== cohabiteesOtherOptionValue);
        const other = expertises.cohabitees.other || [];
        // Only add if there are expertises or other values
        if (expertisesList.length > 0 || other.length > 0) {
          service_details.cohabitees = {
            expertises: expertisesList,
            other: other,
          };
        }
      }

      // Build professional_status - map "Other" back to "OTHER" and handle other field
      const professional_status = {
        values: formData.professional_status_values.map((v: string) => v === "Other" ? "OTHER" : v),
        Other: formData.professional_status_other || "",
      };

      // Build regulator - map "Other" to "OTHER" in values if other is provided
      const regulator = (() => {
        // Check if "Other" is selected (by value or by finding the option)
        const otherOption = REGULATOR_OPTIONS.find(opt => 
          opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
        );
        const isOtherSelected = otherOption && (
          formData.regulator_value === otherOption.value ||
          formData.regulator_value === "OTHER" ||
          formData.regulator_value === "Other"
        );
        
        if (isOtherSelected && formData.regulator_other) {
          return {
            values: ["OTHER"],
            other: formData.regulator_other,
          };
        }
        if (isOtherSelected && !formData.regulator_other) {
          return null; // Don't save if "Other" selected but no custom value
        }
        return {
          values: formData.regulator_value ? [formData.regulator_value] : [],
          other: null,
        };
      })();

      // Combine phone number with dial code
      const phoneNumber = formData.phone?.trim() ? combinePhoneNumber(dialCode, formData.phone) : null;
      
      // Handle remote_consultation - send null if empty instead of empty string
      const remoteConsultation = formData.remote_consultation === "Yes" || formData.remote_consultation === "No" 
        ? formData.remote_consultation 
        : null;

      const submitData: LegalExpertFormData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        phone: phoneNumber,
        work_status: formData.work_status,
        firm_name: formData.firm_name || null,
        city: formData.city,
        post_code: formData.post_code,
        gender: formData.gender || null,
        professional_status: professional_status,
        experience: formData.experience,
        regulator: regulator,
        accredited_specialist: { values: formData.accredited_specialist },
        accredited_specialism_other: formData.accredited_specialism_other?.length
          ? formData.accredited_specialism_other.map((s) => s.trim()).filter(Boolean)
          : null,
        remote_consultation: remoteConsultation,
        // consultation_offers: { values: formData.consultation_offers },
        ncdr_magic: { values: formData.ncdr_magic },
        ncdr_description: formData.ncdr_description || null,
        compelling_quote: formData.compelling_quote || null,
        service_details: Object.keys(service_details).length > 0 ? (service_details as any) : null,
        status: formData.status,
      };

      // Handle photo URL submission logic
      if (hasNewPhotoUpload) {
        // Only include photo_url if a new photo was uploaded
        submitData.photo_url = formData.photo_url;
      }
      // If no new photo uploaded, don't include photo_url to preserve existing photo

      await onSubmit(submitData, expertData?.id);
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClass = (error?: string) => 
    `w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 ${
      error ? "border-novaCaution-500" : "border-novaNeutral-300"
    }`;

  return (
    <div>
      <div className="mb-4 bg-white text-center rounded-lg border border-novaActive p-4">
        <h2 className="text-xl font-semibold text-novaNeutral-900">
          Edit Nova Expert
        </h2>
        <p className="mt-1 text-sm text-novaNeutral-500">
          Update all information for this Nova Expert
        </p>
      </div>

      <div className="bg-white rounded-lg p-8 border border-novaActive">
        <form onSubmit={handleSubmit}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.target as HTMLElement).tagName !== "TEXTAREA") {
            e.preventDefault();
          }
        }}
        className="space-y-6">
          
          {/* Personal Information */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">Personal Information</h3>
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
                  maxLength={VALIDATION.firstName.maxLength + 1}
                />
                {errors.first_name && <p className="mt-1 text-xs text-novaCaution-500">{errors.first_name}</p>}
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
                  maxLength={VALIDATION.lastName.maxLength + 1}
                />
                {errors.last_name && <p className="mt-1 text-xs text-novaCaution-500">{errors.last_name}</p>}
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
                  maxLength={VALIDATION.email.maxLength + 1}
                />
                {errors.email && <p className="mt-1 text-xs text-novaCaution-500">{errors.email}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Phone <span className="text-novaCaution-500">*</span>
                </label>
                <div className="grid grid-cols-[100px_1fr] gap-2">
                  <PhoneCountryCodeSelect
                    value={selectedCountryCode}
                    className="py-2"
                    onChange={handleCountryCodeChange}
                    disabled={isSubmitting}
                  />
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onInput={(e) => {
                      // Only allow numbers and spaces
                      const value = e.currentTarget.value.replace(/[^0-9\s]/g, "");
                      e.currentTarget.value = value;
                      handleChange(e as any);
                    }}
                    className={inputClass(errors.phone)}
                    placeholder="123 456 7890"
                    maxLength={VALIDATION.phone.maxLength + 1}
                  />
                </div>
                {errors.phone && <p className="mt-1 text-xs text-novaCaution-500">{errors.phone}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Gender
                </label>
                <CustomSelect
                  value={formData.gender}
                  onChange={(value) => setFormData((prev) => ({ ...prev, gender: value }))}
                  options={GENDER_OPTIONS}
                  placeholder="Select gender"
                  triggerClassName="rounded-md h-[36px]"
                />
              </div>
            </div>
          </div>

          {/* Work Information */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">Work Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Work Status <span className="text-novaCaution-500">*</span>
                </label>
                <CustomSelect
                  value={formData.work_status}
                  onChange={(value) => setFormData((prev) => ({ ...prev, work_status: value }))}
                  options={WORK_STATUS_OPTIONS}
                  placeholder="Select work status"
                  triggerClassName="rounded-md h-[36px]"
                  error={!!errors.work_status}
                />
                {errors.work_status && <p className="mt-1 text-xs text-novaCaution-500">{errors.work_status}</p>}
              </div>
              {/* Show Firm Name only when work status is not freelance */}
              {formData.work_status && !formData.work_status.toLowerCase().includes("freelance") && (
                <div className="md:col-span-1">
                  <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Organisation Name <span className="text-novaCaution-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="firm_name"
                    value={formData.firm_name}
                    onChange={handleChange}
                    className={inputClass(errors.firm_name)}
                    placeholder="Enter your organisation name"
                    maxLength={VALIDATION.firmName.maxLength + 1}
                  />
                  {errors.firm_name && <p className="mt-1 text-xs text-novaCaution-500">{errors.firm_name}</p>}
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  City <span className="text-novaCaution-500">*</span>
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  className={inputClass(errors.city)}
                  maxLength={VALIDATION.city.maxLength + 1}
                />
                {errors.city && <p className="mt-1 text-xs text-novaCaution-500">{errors.city}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Post Code <span className="text-novaCaution-500">*</span>
                </label>
                <input
                  type="text"
                  name="post_code"
                  value={formData.post_code}
                  onChange={handleChange}
                  className={inputClass(errors.post_code)}
                  maxLength={VALIDATION.postCode.maxLength + 1}
                />
                {errors.post_code && <p className="mt-1 text-xs text-novaCaution-500">{errors.post_code}</p>}
              </div>
            </div>
          </div>

          {/* Professional Qualifications */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">Professional Qualifications</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="">
                <MultiSelect
                  label="Professional Status"
                  options={PROFESSIONAL_STATUS_OPTIONS}
                  selected={formData.professional_status_values}
                  onChange={(values) => {
                    // Check if "Other" option is selected (by value or by finding the option)
                    const otherOption = PROFESSIONAL_STATUS_OPTIONS.find(opt => 
                      opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
                    );
                    const isOtherSelected = otherOption && (
                      values.includes(otherOption.value) || 
                      values.some(v => v === "OTHER" || v === "Other")
                    );
                    
                    setFormData((prev) => ({ 
                      ...prev, 
                      professional_status_values: values,
                      // Clear professional_status_other when "Other" is deselected
                      professional_status_other: isOtherSelected ? prev.professional_status_other : ""
                    }));
                  }}
                  placeholder="Select professional status..."
                />
                {(() => {
                  // Check if "Other" is selected
                  const otherOption = PROFESSIONAL_STATUS_OPTIONS.find(opt => 
                    opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
                  );
                  const isOtherSelected = otherOption && (
                    formData.professional_status_values.includes(otherOption.value) ||
                    formData.professional_status_values.includes("OTHER") ||
                    formData.professional_status_values.includes("Other")
                  );
                  
                  return isOtherSelected ? (
                    <>
                      <label className="block text-xs font-medium text-novaNeutral-700 mt-4">
                        Other Professional Status
                      </label>
                      <input
                        type="text"
                        name="professional_status_other"
                        value={formData.professional_status_other}
                        onChange={handleChange}
                        className={`${inputClass(errors.professional_status_other)} mt-1`}
                        placeholder="Please specify your professional status..."
                        maxLength={VALIDATION.professionalStatusOther.maxLength + 1}
                      />
                      {errors.professional_status_other && (
                        <p className="mt-1 text-xs text-novaCaution-500">{errors.professional_status_other}</p>
                      )}
                    </>
                  ) : null;
                })()}
              </div>

              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Experience (Years)
                </label>
                <input
                  type="number"
                  name="experience"
                  value={formData.experience ?? ""}
                  onChange={handleChange}
                  className={inputClass(errors.experience)}
                  maxLength={11}
                />
                {errors.experience && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.experience}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Regulator
                </label>
                <CustomSelect
                  value={formData.regulator_value}
                  onChange={(value) => {
                    // Check if "Other" option is selected
                    const otherOption = REGULATOR_OPTIONS.find(opt => 
                      opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
                    );
                    const isOtherSelected = otherOption && (
                      value === otherOption.value ||
                      value === "OTHER" ||
                      value === "Other"
                    );
                    
                    setFormData((prev) => ({ 
                      ...prev, 
                      regulator_value: value,
                      // Clear regulator_other when a non-Other option is selected
                      regulator_other: isOtherSelected ? prev.regulator_other : ""
                    }));
                  }}
                  options={REGULATOR_OPTIONS}
                  placeholder="Select regulator"
                  triggerClassName="rounded-md h-[36px]"
                />
                {(() => {
                  // Check if "Other" is selected
                  const otherOption = REGULATOR_OPTIONS.find(opt => 
                    opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
                  );
                  const isOtherSelected = otherOption && (
                    formData.regulator_value === otherOption.value ||
                    formData.regulator_value === "OTHER" ||
                    formData.regulator_value === "Other"
                  );
                  
                  return isOtherSelected ? (
                    <>
                      <input
                        type="text"
                        name="regulator_other"
                        value={formData.regulator_other}
                        onChange={handleChange}
                        maxLength={VALIDATION.regulatorOther.maxLength + 1}
                        className={`${inputClass(errors.regulator_other)} mt-2`}
                        placeholder="Please specify your regulator..."
                      />
                      {errors.regulator_other && (
                        <p className="mt-1 text-xs text-novaCaution-500">{errors.regulator_other}</p>
                      )}
                    </>
                  ) : null;
                })()}
              </div>

              <div className="">
                <MultiSelect
                  label="Accredited Specialist"
                  options={ACCREDITED_SPECIALIST_OPTIONS}
                  selected={formData.accredited_specialist}
                  onChange={(values) => {
                    const hasOther = (values || []).some(
                      (v) => v === "OTHER" || v === "Other" || String(v).toLowerCase() === "other"
                    );
                    setFormData((prev) => ({
                      ...prev,
                      accredited_specialist: values,
                      // Clear "other" values when "Other" is removed from selection to avoid save errors
                      accredited_specialism_other: hasOther ? prev.accredited_specialism_other : [],
                    }));
                  }}
                  placeholder="Select accreditations..."
                />
                {(() => {
                  // Check if "Other" is selected
                  const otherOption = ACCREDITED_SPECIALIST_OPTIONS.find(opt => 
                    opt.value === "OTHER" || opt.value === "Other" || opt.label === "Other"
                  );
                  const isOtherSelected = otherOption && (
                    formData.accredited_specialist.includes(otherOption.value) ||
                    formData.accredited_specialist.includes("OTHER") ||
                    formData.accredited_specialist.includes("Other")
                  );
                  
                  return isOtherSelected ? (
                    <div className="mt-2">
                      <TagInput
                        values={formData.accredited_specialism_other}
                        onChange={(tags) => {
                          setFormData((prev) => ({ ...prev, accredited_specialism_other: tags }));
                          if (errors.accredited_specialism_other) {
                            setErrors((prev) => ({ ...prev, accredited_specialism_other: "" }));
                          }
                        }}
                        placeholder="Type and press Enter to add"
                      />
                      {errors.accredited_specialism_other && (
                        <p className="mt-1 text-xs text-novaCaution-500">
                          {errors.accredited_specialism_other}
                        </p>
                      )}
                    </div>
                  ) : null;
                })()}
              </div>

              {/* Accredited Specialisms Other - Space always reserved; content shown when "Other" is selected */}
              {/* <div className="">
                {formData.accredited_specialist && formData.accredited_specialist.some(
                  (type) =>
                    type === "OTHER" ||
                    type === "Other" ||
                    type?.toLowerCase() === "other"
                ) && (
                  <>
                    <input
                      type="text"
                      name="accredited_specialism_other"
                      value={formData.accredited_specialism_other || ""}
                      onChange={handleChange}
                      className={inputClass(errors.accredited_specialism_other)}
                      placeholder="Please specify other accredited specialism"
                      maxLength={255}
                    />
                    {errors.accredited_specialism_other && (
                      <p className="mt-1 text-xs text-novaCaution-500">
                        {errors.accredited_specialism_other}
                      </p>
                    )}
                  </>
                )}
              </div> */}

            </div>
          </div>

          {/* Service Details */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">Service Details</h3>
            
            <div className="grid grid-cols-1 gap-4">
              {/* Client Types Selection */}
              <MultiSelect
                label="Who do you offer services to?"
                options={CLIENT_TYPES_OPTIONS}
                selected={formData.client_types}
                onChange={handleRelationshipTypesChange}
                placeholder="Select client types..."
              />

              {/* Expertises - Show only when at least one selected client type has expertise (hide when only Parental relationships) */}
              {hasAnyRelationshipTypeWithExpertise && (
                <div className="md:col-span-2 space-y-4">
                  <div className="">
                    <h4 className="text-sm font-semibold text-novaNeutral-700 mb-3">
                      Expertises
                    </h4>
                    <div className="space-y-4">
                      {(formData.client_types || []).map((relType) => {
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
                        const expertiseOptions: Array<{ value: string; label: string }> = EXPERTISE_OPTIONS[expertiseOptionsKey as keyof typeof EXPERTISE_OPTIONS] || [];
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
                        
                        const maxSelections = expertiseKey === "married_civil_partners" 
                          ? VALIDATION.marriedCouplesServices.maxSelections 
                          : VALIDATION.cohabiteesServices.maxSelections;
                        const errorKey = expertiseKey === "married_civil_partners" 
                          ? "married_couples_services" 
                          : "cohabitees_services";
                        // Exclude "Other" option from count when calculating max custom values
                        const expertisesWithoutOtherCount = currentExpertises.filter(exp =>
                          !isOtherExpertiseOption(exp, expertiseKey)
                        ).length;
                        const effectiveExpertiseCount = expertisesWithoutOtherCount + currentOther.length;

                        return (
                          <div 
                            key={relType}
                            className="bg-novaNeutral-50 rounded-lg p-4 border border-novaNeutral-200"
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
                                error={errors[errorKey]}
                                placeholder={`Select expertises for ${relTypeLabel}...`}
                                maxSelections={maxSelections}
                                selectedCount={effectiveExpertiseCount}
                              />
                              </div>
                            </div>
                            
                            {/* Show "Other" input if "Other" is selected */}
                            {(otherInExpertises || currentOther.length > 0) && (
                              <div className="mt-3">
                                <label className="block text-xs font-medium text-novaNeutral-700 mb-2">
                                  Other Expertises <span className="text-novaNeutral-500 text-xs">( Press Enter to add each value.)</span>
                                </label>
                                <div className="bg-white rounded-md">
                                <TagInput
                                  values={currentOther}
                                  onChange={(tags: string[]) => handleExpertiseOtherChange(relType, tags)}
                                  placeholder="Enter other expertises (e.g., Family Law, Divorce) and press Enter to add each value."
                                  maxValues={maxSelections - expertisesWithoutOtherCount}
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

              {/* Legacy code - keeping for reference but not used */}
              {false && formData.client_types.includes("Married and civil partners") && (
                <div>
                  <MultiSelect
                    label={`Services for Married and Civil Partners (max ${VALIDATION.marriedCouplesServices.maxSelections})`}
                    options={MARRIED_COUPLES_OPTIONS}
                    selected={formData.married_couples_services}
                    onChange={(values) => {
                      const maxSelections = VALIDATION.marriedCouplesServices.maxSelections;
                      const totalSelections = values.length + formData.married_couples_other.length;
                      if (totalSelections > maxSelections) {
                        setErrors((prev) => ({ ...prev, married_couples_services: `Maximum ${maxSelections} selections allowed (including other values)` }));
                        return;
                      }
                      setErrors((prev) => ({ ...prev, married_couples_services: "" }));
                      setFormData((prev) => ({ ...prev, married_couples_services: values }));
                    }}
                    placeholder="Select services for married couples..."
                    error={errors.married_couples_services}
                  />
                  {/* Check if "Other" is selected */}
                  {(formData.married_couples_services.includes("OTHER_MARRIED_CIVIL_PARTNERS") || formData.married_couples_other.length > 0) && (
                    <div className="mt-3 pt-3 border-t border-novaNeutral-200">
                      <label className="block text-xs font-medium text-novaNeutral-700 mb-2">
                        Other Expertises <span className="text-novaNeutral-500 text-xs">( Press Enter to add each value.)</span>
                      </label>
                      <TagInput
                        values={formData.married_couples_other}
                        onChange={(tags) => {
                          const maxSelections = VALIDATION.marriedCouplesServices.maxSelections;
                          const totalSelections = formData.married_couples_services.length + tags.length;
                          if (totalSelections > maxSelections) {
                            setErrors((prev) => ({ ...prev, married_couples_services: `Maximum ${maxSelections} selections allowed (including other values)` }));
                            return;
                          }
                          setErrors((prev) => ({ ...prev, married_couples_services: "" }));
                          setFormData((prev) => ({ ...prev, married_couples_other: tags }));
                        }}
                        placeholder="Enter other expertises (e.g., Family Law, Divorce) and press Enter to add each value."
                        maxValues={VALIDATION.marriedCouplesServices.maxSelections - formData.married_couples_services.length}
                      />
                      <p className="text-xs text-novaNeutral-500 mt-1">
                        Add custom expertise values.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Show Cohabitees services only when that client type is selected */}
              {/* {formData.client_types.includes("Cohabitees") && (
                <div>
                  <MultiSelect
                    label={`Services for Cohabitees (max ${VALIDATION.cohabiteesServices.maxSelections})`}
                    options={COHABITEES_OPTIONS}
                    selected={formData.cohabitees_services}
                    onChange={(values) => {
                      const maxSelections = VALIDATION.cohabiteesServices.maxSelections;
                      const totalSelections = values.length + formData.cohabitees_other.length;
                      if (totalSelections > maxSelections) {
                        setErrors((prev) => ({ ...prev, cohabitees_services: `Maximum ${maxSelections} selections allowed (including other values)` }));
                        return;
                      }
                      setErrors((prev) => ({ ...prev, cohabitees_services: "" }));
                      setFormData((prev) => ({ ...prev, cohabitees_services: values }));
                    }}
                    placeholder="Select services for cohabitees..."
                    error={errors.cohabitees_services}
                  />
                  {/ * Check if "Other" is selected * /}
                  {(formData.cohabitees_services.includes("OTHER_COHABITEES") || formData.cohabitees_other.length > 0) && (
                    <div className="mt-3 pt-3 border-t border-novaNeutral-200">
                      <label className="block text-xs font-medium text-novaNeutral-700 mb-2">
                        Other Expertises <span className="text-novaNeutral-500 text-xs">(comma-separated)</span>
                      </label>
                      <TagInput
                        values={formData.cohabitees_other}
                        onChange={(tags) => {
                          const maxSelections = VALIDATION.cohabiteesServices.maxSelections;
                          const totalSelections = formData.cohabitees_services.length + tags.length;
                          if (totalSelections > maxSelections) {
                            setErrors((prev) => ({ ...prev, cohabitees_services: `Maximum ${maxSelections} selections allowed (including other values)` }));
                            return;
                          }
                          setErrors((prev) => ({ ...prev, cohabitees_services: "" }));
                          setFormData((prev) => ({ ...prev, cohabitees_other: tags }));
                        }}
                        placeholder="Enter other expertises (e.g., Family Law, Divorce)"
                        maxValues={VALIDATION.cohabiteesServices.maxSelections - formData.cohabitees_services.length}
                      />
                      <p className="text-xs text-novaNeutral-500 mt-1">
                        Add custom expertise values. Press Enter to add each value.
                      </p>
                    </div>
                  )}
                </div>
              )} */}
            </div>
          </div>

          {/* NCDR & Consultation */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">NCDR Services & Consultation</h3>
            
            <div className="grid grid-cols-1 gap-4">
              <MultiSelect
                label="NCDR Magic (What can you offer?)"
                options={NCDR_MAGIC_OPTIONS}
                selected={formData.ncdr_magic}
                onChange={(values) => setFormData((prev) => ({ ...prev, ncdr_magic: values }))}
                placeholder="Select NCDR services..."
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Remote Consultation
                  </label>
                  <CustomSelect
                    value={formData.remote_consultation}
                    onChange={(value) => setFormData((prev) => ({ ...prev, remote_consultation: value }))}
                    options={REMOTE_CONSULTATION_OPTIONS}
                    placeholder="Select option"
                    triggerClassName="rounded-md"
                  />
                </div>
              </div>

              {/* <MultiSelect
                label="Consultation Offers"
                options={CONSULTATION_OFFERS_OPTIONS}
                selected={formData.consultation_offers}
                onChange={(values) => setFormData((prev) => ({ ...prev, consultation_offers: values }))}
                placeholder="Select consultation offers..."
              /> */}

              {/* Matter Types - Read Only Display */}
              {(() => {
                // Handle both formats: { values: [...] } or plain array
                let matterTypesArray: string[] = [];
                if (expertData.matter_types) {
                  if (typeof expertData.matter_types === "object" && !Array.isArray(expertData.matter_types) && "values" in expertData.matter_types) {
                    matterTypesArray = (expertData.matter_types as any).values || [];
                  } else if (Array.isArray(expertData.matter_types)) {
                    matterTypesArray = expertData.matter_types;
                  }
                }
                return matterTypesArray.length > 0 ? (
                  <div>
                    <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                      Matter Types <span className="text-novaNeutral-400 text-xs">(Read Only)</span>
                    </label>
                    <div className="flex flex-wrap gap-1 mt-1 p-2 border border-novaNeutral-200 rounded-md bg-novaNeutral-50">
                      {matterTypesArray.map((matterType: string, index: number) => (
                        <span
                          key={index}
                          className="inline-flex px-2 py-1 text-xs font-medium bg-novaPrimary-100 text-novaPrimary-700 rounded"
                        >
                          {getMatterTypeLabel(matterType)}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null;
              })()}
            </div>
          </div>

          {/* Profile Information */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">Profile Information</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  NCDR Description
                </label>
                <textarea
                  name="ncdr_description"
                  value={formData.ncdr_description}
                  onChange={handleChange}
                  rows={3}
                  className={inputClass(errors.ncdr_description)}
                  placeholder="What should potential clients know about you?"
                  maxLength={VALIDATION.ncdrDescription.maxLength + 1}
                />
                <div className="flex justify-between mt-1">
                  {errors.ncdr_description ? (
                    <p className="text-xs text-novaCaution-500">{errors.ncdr_description}</p>
                  ) : (
                    <span></span>
                  )}
                  <p className="text-xs text-novaNeutral-400">
                    {formData.ncdr_description.length}/{VALIDATION.ncdrDescription.maxLength}
                  </p>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Compelling Quote
                </label>
                <textarea
                  name="compelling_quote"
                  value={formData.compelling_quote}
                  onChange={handleChange}
                  rows={2}
                  className={inputClass(errors.compelling_quote)}
                  placeholder="A quote from one of your clients..."
                  maxLength={VALIDATION.compellingQuote.maxLength + 1}
                />
                <div className="flex justify-between mt-1">
                  {errors.compelling_quote ? (
                    <p className="text-xs text-novaCaution-500">{errors.compelling_quote}</p>
                  ) : (
                    <span></span>
                  )}
                  <p className="text-xs text-novaNeutral-400">
                    {formData.compelling_quote.length}/{VALIDATION.compellingQuote.maxLength}
                  </p>
                </div>
              </div>
              {/* Profile Photo */}
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Profile Photo
                </label>

                {/* Show existing photo in edit mode OR uploaded photo */}
                {(formData.photo_url && !showUploadOption) ||
                (imagePreview && showUploadOption) ? (
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
                    {formData.photo_url &&
                      !showUploadOption && (
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
                      )}
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
                          Uploading...
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
                        Uploading image...
                      </p>
                    )}
                    {uploadTokenResponse && (
                      <p className="text-xs text-novaSuccess-600 mt-1">
                        <i className="fas fa-check-circle mr-1"></i>
                        Image uploaded successfully
                      </p>
                    )}
                    {errors.photo_url && (
                      <p className="mt-1 text-xs text-novaCaution-500">{errors.photo_url}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Application Status */}
          <div className="pb-4">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">Application Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Status <span className="text-novaCaution-500">*</span>
                </label>
                <CustomSelect
                  value={formData.status}
                  onChange={(value) => setFormData((prev) => ({ ...prev, status: value as LegalExpertStatus }))}
                  options={STATUS_OPTIONS}
                  placeholder="Select status"
                  triggerClassName="rounded-md"
                />
                <p className="text-xs text-novaNeutral-400 mt-1">
                  Change the status to approve, reject, or mark for review
                </p>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-novaActive">
            <FormButton
              type="button"
              variant="custom"
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
                  Saving...
                </>
              ) : (
                <>
                  <i className="fas fa-save mr-2"></i>
                  Save Changes
                </>
              )}
            </FormButton>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditLegalExpertForm;
