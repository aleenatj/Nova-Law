import React from "react";

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface FormValidationSchema {
  [field: string]: ValidationRule;
}

// Simple validation patterns
export const PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^\+?[0-9\s\(\)\+\-]*$/, // allow +, digits, spaces, parentheses, hyphens
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$/  // PASSWORD pattern: Ensures at least one lowercase letter, one uppercase letter, one digit, and a total length between 8 and 64 characters.
};

// Simple error messages
export const ERROR_MESSAGES = {
  REQUIRED: 'This field is required',
  MIN_LENGTH: (min: number) => `Minimum ${min} characters required`,
  MAX_LENGTH: (max: number) => `Maximum ${max} characters allowed`,
  EMAIL: 'Please enter a valid email',
  PHONE: 'Please enter a valid phone number',
  PASSWORD: 'Password must be at least 8 characters with at least one uppercase, one lowercase, and one number',
  PASSWORDS_MATCH: 'Passwords do not match'
};

// Validate a single field
export function validateField(value: any, rules: ValidationRule): ValidationResult {
  const errors: string[] = [];

  // Convert value to string for validation, handle null/undefined
  const stringValue = value != null ? String(value) : '';
  const trimmedValue = stringValue.trim();

  if (rules.required && (!value || trimmedValue === '')) {
    errors.push(ERROR_MESSAGES.REQUIRED);
  }

  if (trimmedValue && rules.minLength && trimmedValue.length < rules.minLength) {
    errors.push(ERROR_MESSAGES.MIN_LENGTH(rules.minLength));
  }

  if (trimmedValue && rules.maxLength && trimmedValue.length > rules.maxLength) {
    errors.push(ERROR_MESSAGES.MAX_LENGTH(rules.maxLength));
  }

  if (trimmedValue && rules.pattern && !rules.pattern.test(trimmedValue)) {
    if (rules.pattern === PATTERNS.EMAIL) {
      errors.push(ERROR_MESSAGES.EMAIL);
    } else if (rules.pattern === PATTERNS.PHONE) {
      errors.push(ERROR_MESSAGES.PHONE);
    } else if (rules.pattern === PATTERNS.PASSWORD) {
      errors.push(ERROR_MESSAGES.PASSWORD);
    } else {
      errors.push('Invalid format');
    }
  }

  if (value != null && rules.custom) {
    const customError = rules.custom(value);
    if (customError) errors.push(customError);
  }

  return { isValid: errors.length === 0, errors };
}

// Validate entire form
export function validateForm(data: any, schema: FormValidationSchema): Record<string, ValidationResult> {
  const results: Record<string, ValidationResult> = {};
  
  Object.keys(schema).forEach(field => {
    results[field] = validateField(data[field], schema[field]);
  });
  
  return results;
}

// Check if form is valid
export function isFormValid(results: Record<string, ValidationResult>): boolean {
  return Object.values(results).every(result => result.isValid);
}

// Get all form errors
export function getFormErrors(results: Record<string, ValidationResult>): string[] {
  return Object.values(results)
    .filter(result => !result.isValid)
    .flatMap(result => result.errors);
}

// Enhanced React hook for form validation with cross-field validation
export function useFormValidation(schema: FormValidationSchema, crossFieldValidators?: Record<string, (data: any) => string | null>) {
  const [formData, setFormData] = React.useState<Record<string, any>>({});
  const [errors, setErrors] = React.useState<Record<string, ValidationResult>>({});
  const [touched, setTouched] = React.useState<Record<string, boolean>>({});

  // Memoize crossFieldValidators to prevent unnecessary re-renders
  const memoizedCrossFieldValidators = React.useMemo(() => crossFieldValidators, [crossFieldValidators]);

  const validate = React.useCallback(() => {
    const results = validateForm(formData, schema);
    
    // Apply cross-field validators
    if (memoizedCrossFieldValidators) {
      Object.keys(memoizedCrossFieldValidators).forEach(field => {
        const crossFieldError = memoizedCrossFieldValidators[field](formData);
        if (crossFieldError) {
          results[field] = {
            isValid: false,
            errors: [...(results[field]?.errors || []), crossFieldError]
          };
        }
      });
    }
    
    setErrors(results);
    return results;
  }, [formData, schema, memoizedCrossFieldValidators]);

  React.useEffect(() => {
    validate();
  }, [validate]);

  const handleChange = React.useCallback((field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleBlur = React.useCallback((field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  }, []);

  const handleSubmit = React.useCallback((onSubmit: (data: any) => void) => {
    const results = validate();
    if (isFormValid(results)) {
      onSubmit(formData);
    }
  }, [formData, validate]);

  const isValid = isFormValid(errors);

  return {
    formData,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
    setFormData,
    setErrors,
    setTouched
  };
}

// Form Validator Component
export function FormValidator({ 
  schema, 
  onSubmit, 
  children 
}: { 
  schema: FormValidationSchema; 
  onSubmit: (data: any) => void; 
  children: (props: {
    formData: Record<string, any>;
    errors: Record<string, ValidationResult>;
    touched: Record<string, boolean>;
    isValid: boolean;
    handleChange: (field: string, value: any) => void;
    handleBlur: (field: string) => void;
    handleSubmit: () => void;
  }) => React.ReactNode;
}) {
  const {
    formData,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit
  } = useFormValidation(schema);

  const submitHandler = React.useCallback(() => {
    handleSubmit(onSubmit);
  }, [handleSubmit, onSubmit]);

  return (
    <>
      {children({
        formData,
        errors,
        touched,
        isValid,
        handleChange,
        handleBlur,
        handleSubmit: submitHandler
      })}
    </>
  );
}
