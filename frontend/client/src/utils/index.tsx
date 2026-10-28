import React from "react";

const renderHtmlContent = (htmlString: string) => {
  // Check if the string contains HTML tags
  const hasHtmlTags = /<[^>]*>/g.test(htmlString);

  if (hasHtmlTags) {
    // Return JSX with dangerouslySetInnerHTML for HTML content
    return <div dangerouslySetInnerHTML={{ __html: htmlString }} />;
  } else {
    // Return plain text for non-HTML content
    return <div>{htmlString}</div>;
  }
};

export { renderHtmlContent };

// Dynamic Component Loading
export {
  DynamicComponentLoader,
  createComponentMap,
  withLazyLoading
} from './dynamicComponentLoader';

// Form Validation
export {
  validateField,
  validateForm,
  isFormValid,
  getFormErrors,
  useFormValidation,
  FormValidator,
  PATTERNS,
  ERROR_MESSAGES,
  type ValidationRule,
  type ValidationResult,
  type FormValidationSchema
} from './formValidator';

// Form Components
export {
  FormInput,
  FormButton,
  FormFieldGroup,
  FormErrorSummary,
  createFieldProps,
  type FormInputProps,
  type FormButtonProps,
  type FormFieldGroupProps,
  type FormErrorSummaryProps
} from './formComponents';

// Alert Messages
export {
  Alert,
  AlertContainer,
  createAlert,
  createSuccessAlert,
  createErrorAlert,
  createWarningAlert,
  createInfoAlert,
  type AlertType,
  type AlertMessage,
  type AlertProps
} from './alerts';

// Toast Messages
export {
  Toast,
  ToastContainer,
  GlobalToastContainer,
  toastManager,
  createToast,
  createSuccessToast,
  createErrorToast,
  createWarningToast,
  createInfoToast,
  COMMON_TOASTS
} from './toasts';

// Offset Pagination
export {
  usePagination,
  Pagination,
  getPageItems,
  getTotalPages,
  type PaginationConfig,
  type PaginationInfo
} from './pagination';

// Storage Helpers
export {
  saveToLocalStorage,
  getFromLocalStorage,
  removeFromLocalStorage,
} from './storage';

// Loader Components
export {
  Loader,
  PageLoader,
  CardLoader,
  FullPageLoader,
  type LoaderProps
} from './loader';

export {
  formatTimestamp
} from './formatedDate';
