import React, { useState, useEffect, useMemo } from "react";
import { FormButton, FormInput } from "@/utils";
import { useFormValidation, PATTERNS, FormValidationSchema } from "@/utils/formValidator";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";
import { COUNTRIES } from "@/constants/countries";
import { uploadImage } from "@/lib/utils";
import { TagInput } from "@/components/ui/taginput/v1/TagInput";

export type Option = {
  value: string;
  label: string;
  type?: string;
  group?: string;
};

export type FieldOption =
  | string
  | Option
  | Record<string, Option>;

interface Field {
  id: number;
  label: string;
  type: string;
  required?: boolean;
  options?: FieldOption[];
  fields?: string[];
  confirmation?: boolean;
  format?: string;
  maxLength?: number | { [key: string]: number }; // Support both single number and object for nested fields
  maxLengthMessage?: string;
  minLength?: number;
  min?: number; // Minimum value for number fields
  maxSize?: string;
  allowedTypes?: string[];
  maxSelections?: number;
  description?: string;
  contextualHelp?: string;
  showIf?: {
    field: number;
    values?: string[];
    value?: string;
    contains?: string;
  };
}

interface Section {
  id: number;
  title: string;
  fields: Field[];
}

interface FormData {
  formTitle: string;
  eligibility: string[];
  sections: Section[];
  notifications?: {
    admin: string[];
    userConfirmation: string;
  };
  confirmationMessage?: string;
  privacyNote?: string;
}

interface LawyerSignupQuestionCardProps {
  section: Section;
  sectionIndex: number;
  totalSections: number;
  formData: Record<string, any>;
  onFieldChange: (fieldId: number | string, value: any) => void;
  onNext: () => void;
  onPrevious?: () => void;
  formConfig?: any;
  entityType?: string; // Entity type for file uploads (e.g., "lawyer_profile")
  isSubmitting?: boolean; // Loading state during form submission
  introContent?: React.ReactNode; // Optional intro content to display below progress bar
}

export function LawyerSignupQuestionCard({
  section,
  sectionIndex,
  totalSections,
  formData,
  onFieldChange,
  onNext,
  onPrevious,
  formConfig,
  entityType = "b2c_expert_profile", // Default to "lawyer_profile" if not provided
  isSubmitting = false,
  introContent,
}: LawyerSignupQuestionCardProps) {
  const [localFormData, setLocalFormData] = useState<Record<string, any>>(formData);
  // Store country codes for phone fields (key: fieldId, value: countryCode)
  const [phoneCountryCodes, setPhoneCountryCodes] = useState<Record<string, string>>({});
  // Store upload state for file fields (key: fieldId, value: { isUploading, previewUrl, error })
  const [fileUploadStates, setFileUploadStates] = useState<Record<string, { isUploading: boolean; previewUrl: string | null; error: string | null }>>({});
  // Store "other" values for Practice Areas fields (key: fieldId, value: string[])
  const [practiceAreaOtherValues, setPracticeAreaOtherValues] = useState<Record<string, string[]>>({});

  // Sync localFormData with prop formData when section changes
  useEffect(() => {
    setLocalFormData(formData);
    
    // Parse phone numbers and extract country codes
    section.fields.forEach((field) => {
      if (field.type === "phone" && formData[field.id]) {
        const phoneValue = formData[field.id];
        if (typeof phoneValue === "string") {
          const { countryCode, dialCode, phoneNumber } = parsePhoneNumber(phoneValue);
          setPhoneCountryCodes((prev) => ({
            ...prev,
            [field.id]: countryCode,
          }));
        }
      }
    });
    
    // Initialize practice area other values from formData if they exist
    section.fields.forEach((field) => {
      if ((field.id === 9 || field.id === 29) && formData[`${field.id}_other`]) {
        const otherValue = formData[`${field.id}_other`];
        if (Array.isArray(otherValue)) {
          setPracticeAreaOtherValues((prev) => ({
            ...prev,
            [field.id]: otherValue,
          }));
        }
      }
    });
  }, [section.id, formData, section.fields]);

  // Create validation schema from section fields
  const validationSchema = useMemo<FormValidationSchema>(() => {
    const schema: FormValidationSchema = {};
    section.fields.forEach((field) => {
      if (field.type === "email") {
        schema[field.id] = {
          required: field.required || false,
          pattern: PATTERNS.EMAIL,
          maxLength: typeof field.maxLength === "number" ? field.maxLength : undefined,
        };
        if (field.confirmation) {
          schema[`${field.id}_confirm`] = {
            required: field.required || false,
            pattern: PATTERNS.EMAIL,
            maxLength: typeof field.maxLength === "number" ? field.maxLength : undefined,
          };
        }
      } else if (field.type === "phone") {
        schema[field.id] = {
          required: field.required || false,
          pattern: PATTERNS.PHONE,
        };
      } else if (field.type === "text" || field.type === "textarea") {
        schema[field.id] = {
          required: field.required || false,
          maxLength: typeof field.maxLength === "number" ? field.maxLength : undefined,
        };
      } else if (field.type === "number") {
        const maxLen = typeof field.maxLength === "number" ? field.maxLength : undefined;
        const minValue = field.min;
        const customMessage = field.maxLengthMessage;
        schema[field.id] = {
          required: field.required || false,
          // Use custom validator if there's a custom message, otherwise use maxLength
          ...(customMessage && maxLen ? {
            custom: (value: any) => {
              if (value && String(value).length > maxLen) {
                return customMessage;
              }
              // Check min value
              if (minValue !== undefined && value !== null && value !== "") {
                const numValue = Number(value);
                if (!isNaN(numValue) && numValue < minValue) {
                  return `Value must be at least ${minValue}`;
                }
              }
              return null;
            }
          } : {
            maxLength: maxLen,
            ...(minValue !== undefined && {
              custom: (value: any) => {
                if (value !== null && value !== "") {
                  const numValue = Number(value);
                  if (!isNaN(numValue) && numValue < minValue) {
                    return `Value must be at least ${minValue}`;
                  }
                }
                return null;
              }
            }),
          }),
        };
      } else if (field.type === "name") {
        if (field.fields?.includes("firstName")) {
          schema[`${field.id}_firstName`] = {
            required: field.required || false,
            maxLength: (field.maxLength as any)?.firstName,
          };
        }
        if (field.fields?.includes("lastName")) {
          schema[`${field.id}_lastName`] = {
            required: field.required || false,
            maxLength: (field.maxLength as any)?.lastName,
          };
        }
      } else if (field.type === "address") {
        if (field.fields?.includes("city")) {
          schema[`${field.id}_city`] = {
            required: field.required || false,
            maxLength: (field.maxLength as any)?.city,
          };
        }
        if (field.fields?.includes("postcode")) {
          schema[`${field.id}_postcode`] = {
            required: field.required || false,
            pattern: /^[A-Z0-9\s\-]{3,10}$/i,
            maxLength: (field.maxLength as any)?.postcode,
          };
        }
      } else if (field.required) {
        // For other field types, just mark as required if needed
        schema[field.id] = {
          required: true,
        };
      }
    });
    return schema;
  }, [section.fields, localFormData]);

  // Prepare data for validation (flatten nested objects)
  const flattenedData = useMemo(() => {
    const flat: Record<string, any> = {};
    Object.keys(localFormData).forEach((key) => {
      const value = localFormData[key];
      if (value && typeof value === "object" && !Array.isArray(value) && !(value instanceof File)) {
        // Handle nested objects like name and address
        Object.keys(value).forEach((subKey) => {
          flat[`${key}_${subKey}`] = value[subKey];
        });
      } else {
        flat[key] = value;
      }
    });
    return flat;
  }, [localFormData]);

  // Use form validation hook with cross-field validators for email confirmation
  const crossFieldValidators = useMemo(() => {
    const validators: Record<string, (data: any) => string | null> = {};
    section.fields.forEach((field) => {
      if (field.type === "email" && field.confirmation) {
        validators[`${field.id}_confirm`] = (data: any) => {
          const email = data[field.id];
          const confirmEmail = data[`${field.id}_confirm`];
          if (email && confirmEmail && email !== confirmEmail) {
            return "Emails do not match";
          }
          return null;
        };
      }
    });
    return validators;
  }, [section.fields]);

  // Use form validation hook
  const {
    errors,
    touched,
    handleChange: validationHandleChange,
    handleBlur: validationHandleBlur,
    setFormData: setValidationFormData,
  } = useFormValidation(validationSchema, crossFieldValidators);

  // Sync validation formData with localFormData when section changes
  useEffect(() => {
    setValidationFormData(flattenedData);
  }, [section.id, flattenedData, setValidationFormData]);

  const handleFieldChange = (fieldId: number | string, value: any) => {
    const newData = { ...localFormData, [fieldId]: value };
    setLocalFormData(newData);
    
    // Update validation data
    if (value && typeof value === "object" && !Array.isArray(value) && !(value instanceof File)) {
      // Handle nested objects
      Object.keys(value).forEach((subKey) => {
        validationHandleChange(`${fieldId}_${subKey}`, value[subKey]);
      });
    } else {
      validationHandleChange(String(fieldId), value);
    }
    
    onFieldChange(fieldId, value);
  };

  const handleFieldBlur = (fieldId: number | string) => {
    validationHandleBlur(String(fieldId));
  };

  // Utility function to normalize text to key format (spaces to underscores)
  const normalizeToKey = (text: string): string => {
    return text.replace(/\s+/g, '_');
  };

  // Helper function to normalize options format
  // Handles: strings, objects with {value, label}, and nested object structures
   // Normalize options: strings → { value, label }; Option[] or OptionRecord[] → Option[]
   const normalizeOptions = (options: FieldOption[] | undefined): Option[] => {
    const list = Array.isArray(options) ? options : [];
    const isOption = (o: unknown): o is Option =>
      !!o && typeof (o as Option).value === "string" && typeof (o as Option).label === "string";

    return list.flatMap((opt) => {
      if (typeof opt === "string") return [{ value: opt, label: opt }];
      if (isOption(opt)) return [opt];
      return Object.values(opt).filter(isOption);
    });
  };

  const shouldShowField = (field: Field): boolean => {
    if (!field.showIf) return true;
    
    const { field: parentFieldId, values, value, contains } = field.showIf;
    const parentValue = localFormData[parentFieldId];
    
    // Helper to get all possible values from parent field options (both value and label)
    const getParentFieldOptionValues = (): string[] => {
      if (!formConfig?.sections) return [];
      
      const parentField = formConfig.sections
        .flatMap((s: any) => s.fields || [])
        .find((f: any) => f.id === parentFieldId);
      
      if (parentField?.options) {
        const normalizedOptions = normalizeOptions(parentField.options);
        // Return both values and labels for matching
        return normalizedOptions.flatMap(opt => [opt.value, opt.label]);
      }
      return [];
    };
    
    // Helper to normalize and compare values
    const matchesValue = (pv: any, checkValue: string): boolean => {
      const pvStr = String(pv || "").toLowerCase();
      const checkStr = checkValue.toLowerCase();
      
      // Direct match (case-insensitive)
      if (pvStr === checkStr) {
        return true;
      }
      
      // Check against parent field's option values/labels
      const parentOptionValues = getParentFieldOptionValues();
      const pvMatches = parentOptionValues.some(optVal => optVal.toLowerCase() === pvStr);
      const checkMatches = parentOptionValues.some(optVal => optVal.toLowerCase() === checkStr);
      
      // If both match the same option (by value or label), they're equivalent
      if (pvMatches && checkMatches) {
        // Check if they're from the same option
        const normalizedOptions = normalizeOptions(
          formConfig?.sections
            ?.flatMap((s: any) => s.fields || [])
            .find((f: any) => f.id === parentFieldId)?.options || []
        );
        const pvOption = normalizedOptions.find(opt => 
          opt.value.toLowerCase() === pvStr || opt.label.toLowerCase() === pvStr
        );
        const checkOption = normalizedOptions.find(opt => 
          opt.value.toLowerCase() === checkStr || opt.label.toLowerCase() === checkStr
        );
        if (pvOption && checkOption && pvOption.value === checkOption.value) {
          return true;
        }
      }
      
      // Normalized key comparison (spaces to underscores)
      const normalizedPv = normalizeToKey(String(pv || "")).toLowerCase();
      const normalizedCheck = normalizeToKey(checkValue).toLowerCase();
      return normalizedPv === normalizedCheck;
    };
    
    if (values && Array.isArray(parentValue)) {
      return values.some((v: string) => parentValue.some((pv: any) => matchesValue(pv, v)));
    }
    if (values) {
      return values.some((v: string) => matchesValue(parentValue, v));
    }
    if (value !== undefined) {
      // If parent value is an array (checkbox field), check if the value is in the array
      if (Array.isArray(parentValue)) {
        return parentValue.some((pv: any) => matchesValue(pv, String(value)));
      }
      return matchesValue(parentValue, String(value));
    }
    if (contains) {
      if (Array.isArray(parentValue)) {
        return parentValue.some((pv: any) => matchesValue(pv, contains));
      }
      return matchesValue(parentValue, contains);
    }
    return true;
  };

  const isFieldValid = (field: Field): boolean => {
    const value = localFormData[field.id];
    
    // Check validation errors first (applies to both required and optional fields)
    const fieldErrors = errors[String(field.id)];
    if (fieldErrors && !fieldErrors.isValid) {
      return false;
    }
    
    // For non-required fields, if there are no validation errors, it's valid
    if (!field.required) return true;
    
    if (Array.isArray(value)) {
      return value.length > 0;
    }
    
    // For name fields, check sub-fields
    if (field.type === "name") {
      if (field.fields?.includes("firstName")) {
        const firstNameErrors = errors[`${field.id}_firstName`];
        if (firstNameErrors && !firstNameErrors.isValid) return false;
        if (!value?.firstName) return false;
      }
      if (field.fields?.includes("lastName")) {
        const lastNameErrors = errors[`${field.id}_lastName`];
        if (lastNameErrors && !lastNameErrors.isValid) return false;
        if (!value?.lastName) return false;
      }
      return true;
    }
    
    // For address fields, check sub-fields
    if (field.type === "address") {
      if (field.fields?.includes("city")) {
        const cityErrors = errors[`${field.id}_city`];
        if (cityErrors && !cityErrors.isValid) return false;
        if (!value?.city) return false;
      }
      if (field.fields?.includes("postcode")) {
        const postcodeErrors = errors[`${field.id}_postcode`];
        if (postcodeErrors && !postcodeErrors.isValid) return false;
        if (!value?.postcode) return false;
      }
      return true;
    }
    
    // For email with confirmation
    if (field.type === "email" && field.confirmation) {
      const confirmErrors = errors[`${field.id}_confirm`];
      if (confirmErrors && !confirmErrors.isValid) return false;
      const confirmValue = localFormData[`${field.id}_confirm`];
      if (value !== confirmValue) return false;
    }
    
    // For Practice Areas fields (9 and 29) with maxSelections, validate total count
    if ((field.id === 9 || field.id === 29) && field.maxSelections) {
      const selectedOptions = Array.isArray(value) 
        ? value.filter((v: string) => {
            // Filter out "Other" option values
            const normalizedOptions = normalizeOptions(field.options || []);
            const otherOption = normalizedOptions.find(opt => opt.label === "Other" || opt.value.includes("OTHER"));
            return otherOption ? v !== otherOption.value : true;
          })
        : [];
      const otherValues = practiceAreaOtherValues[field.id] || [];
      const totalCount = selectedOptions.length + otherValues.length;
      
      // If field is required, must have at least one selection
      if (field.required && totalCount === 0) {
        return false;
      }
      
      // Check max selections (options + other values)
      if (totalCount > field.maxSelections) {
        return false;
      }
    }
    
    return value !== undefined && value !== null && value !== "";
  };

  const canProceed = section.fields
    .filter(f => shouldShowField(f))
    .every(f => isFieldValid(f));

  // Handle keyboard Enter to proceed to next section
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Only trigger on Enter key, not during submission, and when form is valid
    if (e.key === "Enter" && canProceed && !isSubmitting) {
      // Don't trigger for textarea fields (allow multiline input)
      const target = e.target as HTMLElement;
      if (target.tagName === "TEXTAREA") {
        return;
      }
      e.preventDefault();
      onNext();
    }
  };

  const renderField = (field: Field) => {
    if (!shouldShowField(field)) return null;

    const fieldValue = localFormData[field.id];

    switch (field.type) {
      case "name":
        return (
          <div>
            <label className="block text-base font-medium text-novaNeutral-900 mb-3">
              {field.label} {field.required && <span className="text-novaCaution-500">*</span>}
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {field.fields?.includes("firstName") && (
                <FormInput
                  name={`${field.id}_firstName`}
                  type="text"
                  label="First name"
                  value={fieldValue?.firstName || ""}
                  onChange={(e) => {
                    const maxLen = (field.maxLength as any)?.firstName;
                    const newValue = maxLen && e.target.value.length > maxLen 
                      ? e.target.value.slice(0, maxLen) 
                      : e.target.value;
                    handleFieldChange(field.id, { ...fieldValue, firstName: newValue });
                  }}
                  onBlur={() => handleFieldBlur(`${field.id}_firstName`)}
                  errors={errors[`${field.id}_firstName`]?.errors || []}
                  touched={touched[`${field.id}_firstName`] || false}
                  required={field.required}
                  maxLength={(field.maxLength as any)?.firstName}
                  inputClassName="px-3 py-2.5"
                  labelClassName="text-sm text-novaNeutral-600 mb-1.5"
                />
              )}
              {field.fields?.includes("lastName") && (
                <FormInput
                  name={`${field.id}_lastName`}
                  type="text"
                  label="Last name"
                  value={fieldValue?.lastName || ""}
                  onChange={(e) => {
                    const maxLen = (field.maxLength as any)?.lastName;
                    const newValue = maxLen && e.target.value.length > maxLen 
                      ? e.target.value.slice(0, maxLen) 
                      : e.target.value;
                    handleFieldChange(field.id, { ...fieldValue, lastName: newValue });
                  }}
                  onBlur={() => handleFieldBlur(`${field.id}_lastName`)}
                  errors={errors[`${field.id}_lastName`]?.errors || []}
                  touched={touched[`${field.id}_lastName`] || false}
                  required={field.required}
                  maxLength={(field.maxLength as any)?.lastName}
                  inputClassName="px-3 py-2.5"
                  labelClassName="text-sm text-novaNeutral-600 mb-1.5"
                />
              )}
            </div>
          </div>
        );

      case "email":
        return (
          <div className="space-y-4">
            <FormInput
              name={String(field.id)}
              type="email"
              label={field.label}
              value={fieldValue || ""}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
              onBlur={() => handleFieldBlur(field.id)}
              errors={errors[String(field.id)]?.errors || []}
              touched={touched[String(field.id)] || false}
              required={field.required}
              maxLength={typeof field.maxLength === "number" ? field.maxLength : undefined}
              inputClassName="px-4 py-3"
            />
            {field.confirmation && (
              <FormInput
                name={`${field.id}_confirm`}
                type="email"
                label={`Confirm ${field.label}`}
                value={localFormData[`${field.id}_confirm`] || ""}
                onChange={(e) => handleFieldChange(`${field.id}_confirm`, e.target.value)}
                onBlur={() => handleFieldBlur(`${field.id}_confirm`)}
                errors={errors[`${field.id}_confirm`]?.errors || []}
                touched={touched[`${field.id}_confirm`] || false}
                required={field.required}
                maxLength={typeof field.maxLength === "number" ? field.maxLength : undefined}
                inputClassName="px-4 py-3"
              />
            )}
          </div>
        );

      case "phone":
        const countryCode = phoneCountryCodes[field.id] || "GB";
        const { phoneNumber: parsedPhoneNumber } = parsePhoneNumber(fieldValue || "");
        
        const handlePhoneCountryChange = (newCountryCode: string, dialCode: string) => {
          setPhoneCountryCodes((prev) => ({
            ...prev,
            [field.id]: newCountryCode,
          }));
          // Combine the new country code with existing phone number
          const combined = combinePhoneNumber(dialCode, parsedPhoneNumber || "");
          handleFieldChange(field.id, combined);
          
          // Focus back to the phone input after country code selection
          setTimeout(() => {
            const phoneInput = document.getElementById(`phone-input-${field.id}`);
            if (phoneInput) {
              phoneInput.focus();
            }
          }, 0);
        };

        const handlePhoneNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
          // Allow only digits and spaces
          const filtered = e.target.value.replace(/[^0-9\s]/g, "");
          const dialCode = COUNTRIES.find((c) => c.code === countryCode)?.dialCode || "+44";
          const combined = combinePhoneNumber(dialCode, filtered);
          handleFieldChange(field.id, combined);
        };

        return (
          <div>
            <label className="block text-base font-medium text-novaNeutral-900 mb-3">
              {field.label} {field.required && <span className="text-novaCaution-500">*</span>}
            </label>
            <div className="grid grid-cols-[95px_1fr] gap-2">
              <PhoneCountryCodeSelect
                className="h-[50px] rounded-lg"
                value={countryCode}
                onChange={handlePhoneCountryChange}
              />
              <div className="relative">
                <input
                  id={`phone-input-${field.id}`}
                  type="tel"
                  value={parsedPhoneNumber || ""}
                  onChange={handlePhoneNumberChange}
                  onBlur={() => handleFieldBlur(field.id)}
                  maxLength={typeof field.maxLength === "number" ? field.maxLength : 20}
                  placeholder="123 456 7890"
                  className={`w-full h-[50px] px-3 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                    errors[String(field.id)]?.errors?.length > 0 && touched[String(field.id)]
                      ? "focus:ring-novaPrimary focus:border-transparent transition-colors border-novaCaution-300"
                      : "border-novaNeutral-300 focus:ring-novaPrimary-500 focus:border-novaPrimary-500"
                  }`}
                  required={field.required}
                />
              </div>
            </div>
            {errors[String(field.id)]?.errors?.length > 0 && touched[String(field.id)] && (
              <div className="mt-1 text-novaCaution-600 text-sm">
                {errors[String(field.id)].errors.map((error, index) => (
                  <p key={index}>{error}</p>
                ))}
              </div>
            )}
          </div>
        );

      case "text":
        return (
          <div>
            <label className="block text-sm font-medium text-novaNeutral-700 mb-1">
              {field.label} {field.required && <span className="text-novaCaution-500">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-novaNeutral-600 mb-2">{field.description}</p>
            )}
            <FormInput
              name={String(field.id)}
              type="text"
              // label={field.label}
              value={fieldValue || ""}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
              onBlur={() => handleFieldBlur(field.id)}
              errors={errors[String(field.id)]?.errors || []}
              touched={touched[String(field.id)] || false}
              required={field.required}
              maxLength={typeof field.maxLength === "number" ? field.maxLength : undefined}
              inputClassName="px-3 py-2.5"
              labelClassName="text-base font-medium text-novaNeutral-900 mb-3"
            />
          </div>
        );

      case "textarea":
        return (
          <div>
            <div className="relative">
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                {field.label} {field.required && <span className="text-novaCaution-500">*</span>}{field.contextualHelp && (
                <span className="ml-2 cursor-pointer group inline-block align-middle">
                  <i className="fas fa-question-circle text-novaPrimary-400 group-hover:text-novaPrimary-600 transition-colors"></i>
                  <div className="absolute z-50 left-0 right-0 top-full mt-1 hidden group-hover:block bg-white border border-novaNeutral-200 rounded-md px-4 py-3 shadow-lg text-xs text-novaNeutral-700">
                    <div
                      dangerouslySetInnerHTML={{ __html: field.contextualHelp }}
                    />
                  </div>
                </span>
              )}
              </label>
            </div>
            {field.description && (
              <p className="text-sm text-novaNeutral-600 mb-2">{field.description}</p>
            )}
            <textarea
              value={fieldValue || ""}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
              maxLength={typeof field.maxLength === "number" ? field.maxLength : undefined}
              className="w-full px-4 py-3 border border-novaNeutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-novaPrimary-500 min-h-[100px]"
              required={field.required}
            />
            {typeof field.maxLength === "number" && (
              <p className="text-xs text-novaNeutral-500 mt-1">
                {(fieldValue?.length || 0)} / {field.maxLength} characters
              </p>
            )}
          </div>
        );

      case "number":
        return (
          <FormInput
            name={String(field.id)}
            type="number"
            label={field.label.replace(
              "{firstName}",
              (localFormData[1]?.firstName || "")
                .toLowerCase()
                .split(" ")
                .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ")
            )}
            value={fieldValue || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            onBlur={() => handleFieldBlur(field.id)}
            errors={errors[String(field.id)]?.errors || []}
            touched={touched[String(field.id)] || false}
            required={field.required}
            maxLength={typeof field.maxLength === "number" ? field.maxLength : undefined}
            min={field.min}
            inputClassName="px-4 py-3"
          />
        );

      case "radio":
        const radioOptions = normalizeOptions(field.options || []);
        return (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-novaNeutral-700 mb-3">
              {field.label.replace(
              "{firstName}",
              (localFormData[1]?.firstName || "")
                .toLowerCase()
                .split(" ")
                .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ")
            )} {field.required && <span className="text-novaCaution-500">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-novaNeutral-600 mb-2">{field.description}</p>
            )}
            <div className="space-y-2">
              {radioOptions.map((option, idx) => (
                <label
                  key={idx}
                  className={`flex items-start p-4 min-h-[48px] border rounded-lg cursor-pointer transition-colors ${
                    fieldValue === option.value
                      ? "bg-[#FFF4E6] border-[#FF9A50]"
                      : "bg-white border-novaNeutral-300 hover:bg-novaNeutral-50"
                  }`}
                >
                  <input
                    type="radio"
                    name={`field_${field.id}`}
                    value={option.value}
                    checked={fieldValue === option.value}
                    onChange={(e) => handleFieldChange(field.id, e.target.value)}
                    className="sr-only"
                  />
                  <span className="text-[16px] text-novaNeutral-900 leading-snug">{option.label}</span>
                </label>
              ))}
            </div>
          </div>
        );

      case "checkbox":
        const selectedValues = Array.isArray(fieldValue) ? fieldValue : [];
        const checkboxOptions = normalizeOptions(field.options || []);
        
        // Check if this is a Practice Areas field (9 or 29) with "Other" option
        const isPracticeAreaField = field.id === 9 || field.id === 29;
        const otherOption = checkboxOptions.find(opt => 
          opt.label === "Other" || opt.label === "Other " || opt.value.includes("OTHER")
        );
        const isOtherSelected = otherOption ? selectedValues.includes(otherOption.value) : false;
        const otherValues = practiceAreaOtherValues[field.id] || [];
        
        // Calculate available slots for Practice Areas fields
        const getAvailableSlots = () => {
          if (!isPracticeAreaField || !field.maxSelections) return null;
          const selectedNonOther = selectedValues.filter(v => v !== otherOption?.value);
          const usedSlots = selectedNonOther.length + otherValues.length;
          return field.maxSelections - usedSlots;
        };
        const availableSlots = getAvailableSlots();
        
        return (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-novaNeutral-700 mb-1">
            {(
              field.label.replace("{firstName}", (localFormData[1]?.firstName || "")
              .toLowerCase()
              .split(" ")
              .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
              .join(" "))                
            )} {field.required && <span className="text-novaCaution-500">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-novaNeutral-600 mb-2">{field.description}</p>
            )}
            {field.maxSelections && (
              <p className="text-sm text-novaNeutral-600 mb-2">
                {isPracticeAreaField 
                  ? `You can select up to ${field.maxSelections} total (options + other values)`
                  : `You can select up to ${field.maxSelections}`
                }
                {isPracticeAreaField && availableSlots !== null && (
                  <span className="ml-1 text-novaPrimary-600">
                    ({availableSlots} {availableSlots === 1 ? 'slot' : 'slots'} remaining)
                  </span>
                )}
              </p>
            )}
            <div className="space-y-2">
              {checkboxOptions.map((option, idx) => {
                const isChecked = selectedValues.includes(option.value);
                const isOtherOption = otherOption && option.value === otherOption.value;
                
                // For Practice Areas fields, calculate canSelect based on total count
                let canSelect = true;
                if (isPracticeAreaField && field.maxSelections) {
                  const selectedNonOther = selectedValues.filter(v => v !== otherOption?.value);
                  const usedSlots = selectedNonOther.length + otherValues.length;
                  
                  if (isOtherOption) {
                    // "Other" can be selected if there are slots available (considering other values count)
                    // Disable if max selections reached with non-other options
                    canSelect = isChecked || selectedNonOther.length < field.maxSelections;
                  } else {
                    // For regular options, check if we have slots available
                    canSelect = isChecked || usedSlots < field.maxSelections;
                  }
                } else {
                  // For non-Practice Areas fields, use original logic
                  canSelect = !field.maxSelections || selectedValues.length < field.maxSelections || isChecked;
                }
                  
                  return (
                    <label
                      key={idx}
                      className={`flex items-start gap-3 p-3 min-h-[48px] border rounded-lg cursor-pointer transition-colors ${
                        isChecked
                          ? "bg-[#FFF4E6] border-[#FF9A50]"
                          : canSelect
                          ? "bg-white border-novaNeutral-300 hover:bg-novaNeutral-50"
                          : "bg-novaNeutral-100 border-novaNeutral-200 opacity-50 cursor-not-allowed"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (!canSelect && !isChecked) return;
                          const newValues = e.target.checked
                            ? [...selectedValues, option.value]
                            : selectedValues.filter(v => v !== option.value);
                          handleFieldChange(field.id, newValues);
                          
                          // If "Other" is deselected, clear other values
                          if (isOtherOption && !e.target.checked) {
                            setPracticeAreaOtherValues(prev => {
                              const updated = { ...prev };
                              delete updated[field.id];
                              return updated;
                            });
                            handleFieldChange(`${field.id}_other`, null);
                          }
                        }}
                        disabled={!canSelect && !isChecked}
                        className="sr-only"
                      />
                      <span className={`flex h-5 w-5 flex-shrink-0 mt-0.5 items-center justify-center rounded border ${
                        isChecked ? "bg-white border-[#FF9A50]" : "border-novaNeutral-300"
                      }`}>
                        {isChecked && <span className="block h-3 w-3 rounded-full bg-[#FF9A50]" />}
                      </span>
                      <span className="text-[16px] text-novaNeutral-900 leading-snug">{option.label}</span>
                    </label>
                  );
                })}
            </div>
            
            {/* Show "Other" input if "Other" is selected for Practice Areas fields */}
            {isPracticeAreaField && isOtherSelected && (
              <div 
                className="mt-3 pt-3 border-t border-novaNeutral-200"
                onKeyDown={(e) => {
                  // Prevent Enter key from bubbling up to form's handleKeyDown
                  // This allows TagInput to handle Enter for adding tags
                  if (e.key === "Enter") {
                    e.stopPropagation();
                  }
                }}
              >
                <label className="block text-xs font-medium text-novaNeutral-700 mb-2">
                  Other Practice Areas <span className="text-novaNeutral-500 text-xs">(Press Enter to add each value)</span>
                </label>
                <TagInput
                  values={otherValues}
                  onChange={(tags) => {
                    // Limit total count (selected options + other values) to maxSelections
                    const selectedNonOther = selectedValues.filter(v => v !== otherOption?.value);
                    const maxOtherValues = field.maxSelections 
                      ? Math.max(0, field.maxSelections - selectedNonOther.length)
                      : tags.length;
                    const limitedTags = tags.slice(0, maxOtherValues);
                    
                    setPracticeAreaOtherValues(prev => ({
                      ...prev,
                      [field.id]: limitedTags,
                    }));
                    handleFieldChange(`${field.id}_other`, limitedTags);
                  }}
                  maxValues={field.maxSelections 
                    ? (() => {
                        const selectedNonOther = selectedValues.filter(v => v !== otherOption?.value);
                        return Math.max(0, field.maxSelections - selectedNonOther.length);
                      })()
                    : undefined}
                  placeholder="Enter other practice areas (e.g., Family Law, Divorce) (Press Enter to add each value)"
                />
                <p className="text-xs text-novaNeutral-500 mt-1">
                  Add custom practice area values. Press Enter to add each value.
                </p>
                {field.maxSelections && availableSlots !== null && availableSlots <= 0 && otherValues.length > 0 && (
                  <p className="text-xs text-novaCaution-600 mt-1">
                    Maximum of {field.maxSelections} total selections reached. Remove some selections to add more.
                  </p>
                )}
              </div>
            )}
          </div>
        );

      case "address":
        return (
          <div>
            <label className="block text-sm font-medium text-novaNeutral-700 mb-1">
              {field.label}
            </label>
            {field.description && (
              <p className="text-sm text-novaNeutral-600 mb-2">{field.description}</p>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {field.fields?.includes("city") && (
                <FormInput
                  name={`${field.id}_city`}
                  type="text"
                  label="City or main town"
                  value={fieldValue?.city || ""}
                  onChange={(e) => {
                    const maxLen = (field.maxLength as any)?.city;
                    const newValue = maxLen && e.target.value.length > maxLen 
                      ? e.target.value.slice(0, maxLen) 
                      : e.target.value;
                    handleFieldChange(field.id, { ...fieldValue, city: newValue });
                  }}
                  onBlur={() => handleFieldBlur(`${field.id}_city`)}
                  errors={errors[`${field.id}_city`]?.errors || []}
                  touched={touched[`${field.id}_city`] || false}
                  required={field.required}
                  maxLength={(field.maxLength as any)?.city}
                  inputClassName="px-4 py-3"
                />
              )}
              {field.fields?.includes("postcode") && (
                <FormInput
                  name={`${field.id}_postcode`}
                  type="text"
                  label="Postcode"
                  value={fieldValue?.postcode || ""}
                  onChange={(e) => {
                    const maxLen = (field.maxLength as any)?.postcode;
                    const newValue = maxLen && e.target.value.length > maxLen 
                      ? e.target.value.slice(0, maxLen) 
                      : e.target.value;
                    handleFieldChange(field.id, { ...fieldValue, postcode: newValue });
                  }}
                  onBlur={() => handleFieldBlur(`${field.id}_postcode`)}
                  errors={errors[`${field.id}_postcode`]?.errors || []}
                  touched={touched[`${field.id}_postcode`] || false}
                  required={field.required}
                  maxLength={(field.maxLength as any)?.postcode}
                  inputClassName="px-4 py-3"
                />
              )}
            </div>
          </div>
        );

      case "file":
        const isImageFile = field.allowedTypes?.some(type => 
          ['jpeg', 'jpg', 'png', 'gif', 'webp'].includes(type.toLowerCase())
        ) || false;
        
        const uploadState = fileUploadStates[field.id] || { isUploading: false, previewUrl: null, error: null };
        const maxSizeMB = field.maxSize 
          ? parseFloat(field.maxSize.replace(/[^0-9.]/g, '')) 
          : 5;
        
        // Show image preview if uploaded (similar to AddLawyerForm)
        const hasUploadedImage = isImageFile && (uploadState.previewUrl || fieldValue);

        return (
          <div>
            <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
              {field.label} {field.required && <span className="text-novaCaution-500">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-novaNeutral-600 my-2">{field.description}</p>
            )}
            
            {/* Show image preview when uploaded (similar to AddLawyerForm) */}
            {hasUploadedImage && !uploadState.isUploading ? (
              <div className="mb-3">
                <div className="relative inline-block">
                  <img
                    src={uploadState.previewUrl || fieldValue || ""}
                    alt="Upload preview"
                    className="w-20 h-20 rounded-full object-cover border-2 border-novaNeutral-200"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setFileUploadStates(prev => ({
                        ...prev,
                        [field.id]: { isUploading: false, previewUrl: null, error: null }
                      }));
                      handleFieldChange(field.id, null);
                    }}
                    className="absolute -top-2 -right-2 bg-novaCaution-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-novaCaution-600 transition-colors"
                    title="Remove image"
                  >
                    <i className="fas fa-times"></i>
                  </button>
                </div>
                <p className="text-xs text-novaSuccess-600 mt-2">
                  <i className="fas fa-check-circle mr-1"></i>
                  Image uploaded successfully
                </p>
              </div>
            ) : (
              <>
                {uploadState.isUploading && (
                  <p className="text-xs text-novaPrimary-600 mb-2">
                    <i className="fas fa-spinner fa-spin mr-1"></i>
                    Uploading image...
                  </p>
                )}
                {uploadState.error && (
                  <p className="text-xs text-novaCaution-600 mb-2">
                    <i className="fas fa-exclamation-circle mr-1"></i>
                    {uploadState.error}
                  </p>
                )}
                <input
                  type="file"
                  accept={field.allowedTypes?.map(t => `.${t}`).join(",")}
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      if (isImageFile) {
                        // Update state for this field
                        setFileUploadStates(prev => ({
                          ...prev,
                          [field.id]: { isUploading: true, previewUrl: null, error: null }
                        }));

                        try {
                          const result = await uploadImage({
                            file,
                            entityType: entityType,
                            maxSizeMB: maxSizeMB,
                            allowedTypes: field.allowedTypes?.map(t => `image/${t.toLowerCase()}`),
                            onProgress: (isUploading) => {
                              setFileUploadStates(prev => ({
                                ...prev,
                                [field.id]: { 
                                  ...prev[field.id], 
                                  isUploading,
                                  error: isUploading ? null : prev[field.id]?.error || null
                                }
                              }));
                            },
                          });
                          // Store both fileKey and previewUrl properly (like AddLawyerForm)
                          setFileUploadStates(prev => ({
                            ...prev,
                            [field.id]: { isUploading: false, previewUrl: result.previewUrl, error: null }
                          }));
                          // Store the fileKey in formData (this is what gets submitted)
                          handleFieldChange(field.id, result.fileKey);
                        } catch (error: any) {
                          const errorMsg = error.message || "Failed to upload image";
                          setFileUploadStates(prev => ({
                            ...prev,
                            [field.id]: { isUploading: false, previewUrl: null, error: errorMsg }
                          }));
                          handleFieldChange(field.id, null);
                        }
                      } else {
                        // For non-image files, store the File object as before
                        handleFieldChange(field.id, file);
                      }
                    }
                  }}
                  className="w-full px-4 py-3 border border-novaNeutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-novaPrimary-500"
                  required={field.required}
                  disabled={uploadState.isUploading}
                />
              </>
            )}
            {field.maxSize && (
              <p className="text-sm text-novaNeutral-600 my-2">
                Max size: {field.maxSize}
              </p>
            )}
            {field.allowedTypes && (
              <p className="text-sm text-novaNeutral-600 mb-2">
                Accepted file types: {field.allowedTypes.join(", ")}
              </p>
            )}
          </div>
        );

      default:
        return (
          <FormInput
            name={String(field.id)}
            type="text"
            label={field.label}
            value={fieldValue || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            onBlur={() => handleFieldBlur(field.id)}
            errors={errors[String(field.id)]?.errors || []}
            touched={touched[String(field.id)] || false}
            required={field.required}
            inputClassName="px-4 py-3"
          />
        );
    }
  };

  return (
    <div className="w-full max-w-4xl" onKeyDown={handleKeyDown}>
      <div className="bg-white rounded-lg p-2 md:p-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-2 font-nineties text-left">
            {formConfig?.formTitle || "Become a Nova Professional"}
          </h1>
          <div className="flex items-center justify-between mb-4">
            <p className="text-base text-novaNeutral-500">
              Step {sectionIndex + 1} of {totalSections}
            </p>
            <p className="text-sm text-novaNeutral-500">
              {Math.round(((sectionIndex + 1) / totalSections) * 100)}%
            </p>
          </div>
          <div className="w-full bg-novaNeutral-200 rounded-full h-2 mb-6">
            <div
              className="bg-novaBlack h-2 rounded-full transition-all duration-300"
              style={{ width: `${((sectionIndex + 1) / totalSections) * 100}%` }}
            />
          </div>
        </div>

        {/* Intro Content (if provided) */}
        {introContent}

        {/* Section Title */}
        <h2 className="text-xl font-semibold text-novaNeutral-900 mb-6">
          {section.title}
        </h2>

        <div className="space-y-6 mt-6">
          {section.fields.map((field) => (
            <div key={field.id}>
              {renderField(field)}
            </div>
          ))}
        </div>

        <div className="mt-8 flex justify-start gap-4">
          {onPrevious && sectionIndex > 0 && (
            <FormButton
              type="button"
              variant="outline"
              size="md"
              onClick={onPrevious}
              className="whitespace-nowrap"
            >
              <i className="fas fa-arrow-left mr-2"></i>
              Previous
            </FormButton>
          )}
          <FormButton
            type="button"
            variant="primary"
            size="md"
            onClick={onNext}
            disabled={!canProceed || isSubmitting}
            className="hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471] whitespace-nowrap"
          >
            {isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                Submitting...
              </>
            ) : (
              <>
                {sectionIndex === totalSections - 1 ? "Submit" : "Next"}
                <i className="fas fa-arrow-right ml-2"></i>
              </>
            )}
          </FormButton>
        </div>
      </div>
    </div>
  );
}

