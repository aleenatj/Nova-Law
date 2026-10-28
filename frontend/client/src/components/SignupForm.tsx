import React, { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { api, ApiError, tokenManager } from "../lib/api";
import { SignupRequest, SignupResponse, ResolveData } from "../lib/types";
import { useRole } from "../contexts/RoleContext";
import { useFormValidation, ERROR_MESSAGES } from "../utils/formValidator";
import {FormInput,FormButton,createFieldProps,} from "../utils/formComponents";
import { signupValidationSchema } from "../utils/validationSchemas";
import {createErrorToast,createSuccessToast,ToastContainer,} from "../utils/toasts";
import CreateCasePopup from "./case/v1/CreateCasePopup";
import { INPUT_MAX_LENGTH } from "@/lib/constants";
import { useModal } from "@/contexts/ModalContext";
import PhoneCountryCodeSelect from "./ui/phone-country-select/PhoneCountryCodeSelect";
import TagManager from "react-gtm-module";

interface SignupFormProps {
  onClose: () => void;
  onSuccess?: () => void;
  resolveId?: string; // Optional resolve ID for case creation
}

const SignupForm: React.FC<SignupFormProps> = ({onClose,onSuccess,resolveId,}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toasts, setToasts] = useState<any[]>([]);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [createdCaseId, setCreatedCaseId] = useState<string | null>(null);
  const { setCurrentRole, refreshRoleFromStorage } = useRole();
  const [error, setError] = useState<string | null>(null);
  const [, navigate] = useLocation();
  const [resolveData, setResolveData] = useState<ResolveData | null>(null);
  const { switchModal } = useModal();
  const [acceptTerms, setAcceptTerms] = useState<boolean>(false);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB"); // Default to UK (country code)
  const [dialCode, setDialCode] = useState<string>("+44"); // Default to UK dial code
  // Toast management functions
  const addToast = (toast: any) => {
    setToasts((prev) => [...prev, toast]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  // Phone number input handler - max 20 chars, only valid chars (without country code)
  const handlePhoneChange = (field: string, value: string) => {
    // Remove any leading + or 0, and only allow digits and spaces
    const phoneRegex = /^[0-9\s]*$/;
    const cleanValue = value.replace(/^[+0]+/, '');
    if (phoneRegex.test(cleanValue) && cleanValue.length <= 15) {
      handleChange(field, cleanValue);
    }
  };

  // Combine dial code with phone number for API submission
  const getFullPhoneNumber = () => {
    const phone = formData.phone || '';
    if (!phone.trim()) return '';
    // Remove any spaces from the phone number
    const cleanPhone = phone.replace(/\s/g, '');
    return `${dialCode}${cleanPhone}`;
  };

  // Handler for country code selection
  const handleCountryCodeChange = (countryCode: string, phoneDialCode: string) => {
    setSelectedCountryCode(countryCode);
    setDialCode(phoneDialCode);
  };

  // Cross-field validation for password confirmation
  const crossFieldValidators = React.useMemo(
    () => ({
      confirmPassword: (data: any) => {
        if (data.password && data.confirmPassword && data.password !== data.confirmPassword) {
          return ERROR_MESSAGES.PASSWORDS_MATCH;
        }
        return null;
      },
    }),
    []
  );

  const {
    formData,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
  } = useFormValidation(signupValidationSchema, crossFieldValidators);

  // Fetch resolve data when component mounts (if resolveId is provided)
  useEffect(() => {
    const fetchResolveData = async () => {
      if (!resolveId) return;

      try {
        // Try getting from session storage first
        const sessionKey = "resolve_session_data";
        const sessionData = sessionStorage.getItem(sessionKey);

        if (sessionData) {
          const parsedData = JSON.parse(sessionData);
          if (parsedData && parsedData.resolve_id === resolveId) {
            setResolveData(parsedData);
            return;
          }
        }

        // If not in session, fetch from API
        const result = await api.get(`/v1/resolve/${resolveId}`);

        // Handle the response - check if it's wrapped or direct
        let fetchedResolveData: ResolveData;
        if (result && typeof result === "object" && "data" in result) {
          if ((result as any).success) {
            fetchedResolveData = result.data as ResolveData;
          } else {
            console.error("Failed to fetch resolve data");
            return;
          }
        } else if (result && typeof result === "object" && "resolve_id" in result) {
          fetchedResolveData = result as ResolveData;
        } else {
          console.error("Invalid response format");
          return;
        }

        setResolveData(fetchedResolveData);
      } catch (err) {
        console.error("Error fetching resolve data:", err);
      }
    };

    fetchResolveData();
  }, [resolveId]);

  // Pre-fill form fields when resolve data is available
  useEffect(() => {
    if (!resolveData || !resolveData.question_data) return;

    // Extract First Name from question identifier "1"
    const firstNameAnswer = resolveData.question_data["1"]?.answer?.[0]?.value;
    if (firstNameAnswer && firstNameAnswer.trim()) {
      handleChange("firstName", firstNameAnswer.trim());
    }

    // Extract Email from question identifier "21"
    const emailAnswer = resolveData.question_data["21"]?.answer?.[0]?.value;
    if (emailAnswer && emailAnswer.trim()) {
      handleChange("email", emailAnswer.trim());
    }
  }, [resolveData]);

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);
    setError(null);

    // Show response messages as toasts, with a delay between each
    const showToastsWithDelay = async (
      messages: Array<{ message: string; success?: boolean }>,
      isSuccess: boolean
    ) => {
      const delay = 400; // ms
      for (let i = 0; i < messages.length; i++) {
        const messageItem = messages[i];
        await new Promise((resolve) =>
          setTimeout(resolve, i === 0 ? 0 : delay)
        );
        if (messageItem.success === true) {
          const toast = createSuccessToast("Success", messageItem.message);
          addToast(toast);
        } else if (messageItem.success === false) {
          const toast = createErrorToast("Error", messageItem.message);
          addToast(toast);
        } else {
          if (isSuccess) {
            const toast = createSuccessToast("Success", messageItem.message);
            addToast(toast);
          } else {
            const toast = createErrorToast("Error", messageItem.message);
            addToast(toast);
          }
        }
      }
    };

    try {
      // Prepare the request data
      const phoneNumber = getFullPhoneNumber();
      const signupData: SignupRequest = {
        first_name: data.firstName,
        last_name: data.lastName,
        email: data.email,
        password: data.password,
        ...(phoneNumber && { phone: phoneNumber }),
        ...(resolveId && { resolve_id: resolveId }),
      };

      // Make API call
      const response = (await api.post<SignupResponse>("/v1/customer/registration",signupData)) as any;

      if (response && response.data) {
        const responseData = response.data;

        // Store tokens
        tokenManager.setTokens(
          responseData.login_data.access_token,
          responseData.login_data.refresh_token,
          responseData.login_data.token_type
        );

        // Store user data
        localStorage.setItem(
          "user",
          JSON.stringify(responseData.login_data.user_data)
        );
        
        // Store password state
        if (responseData.login_data.password_state) {
          localStorage.setItem("password_state", responseData.login_data.password_state);
        }
        
        // Store case.id or case.case_id if present in response
        if (responseData.case?.id) {
          sessionStorage.setItem("current_case_id", responseData.case.id);
        } else if (responseData.case?.case_id) {
          sessionStorage.setItem("current_case_id", responseData.case.case_id);
        }
        
        sessionStorage.removeItem("resolve_session_data");
        sessionStorage.removeItem("resolveId");
        // Set user role
        if (responseData.login_data.user_data && responseData.login_data.user_data.role_code) {
          setCurrentRole(
            typeof responseData.login_data.user_data.role_code === "string"
              ? responseData.login_data.user_data.role_code.toLowerCase()
              : responseData.login_data.user_data.role_code
          );
        } else {
          refreshRoleFromStorage();
        }

        // --- Correct usage of all array messages before showing the modal ---
        // Check the exact API structure for messages (image shows field is "message" at top-level response)
        if (
          Array.isArray(response.message) &&
          response.message.length > 0
        ) {
          await showToastsWithDelay(response.message, true);
        }

        if (responseData.case && responseData.case.case_id) {
          setCreatedCaseId(responseData.case.case_id);
          setShowSuccessModal(true);
        } else {
          // If no case created, just close after showing toasts
          setTimeout(() => {
            if (onSuccess) {
              onSuccess();
            }
            onClose();
          }, 1500);
        }
      } else {
        setError("Unexpected response from server. Please try again.");
      }
    } catch (err) {
      console.error("Signup error:", err);

      if (err instanceof ApiError) {
        // Try to extract error message(s) from response
        let errorMsg: string | undefined;

        try {
          const match = err.message.match(/\d+ \w+(?:\s+\w+)* - (.+)/);
          if (match && match[1]) {
            const responseText = match[1];
            try {
              const errorData = JSON.parse(responseText);
              if (
                Array.isArray(errorData.messages) &&
                errorData.messages.length > 0
              ) {
                // Show all error messages as toasts
                await showToastsWithDelay(errorData.messages, false);
                // Set first error message in state for UI error block as well
                setError(
                  errorData.messages[0]?.message ||
                    errorData.message ||
                    errorData.error ||
                    errorData.detail ||
                    "Error"
                );
                return;
              }
              errorMsg =
                errorData.message ||
                errorData.detail ||
                errorData.error ||
                errorData.detail?.[0]?.msg;
            } catch {
              // If not JSON, use the raw response text
              errorMsg = responseText;
            }
          } else {
            errorMsg = err.message;
          }
        } catch (parseError) {
          errorMsg = err.message;
        }

        if (errorMsg) {
          setError(errorMsg);
        } else {
          switch (err.status) {
            case 400:
              setError("Invalid data provided. Please check your information.");
              break;
            case 422:
              setError("Please fill in all required fields correctly.");
              break;
            default:
              setError("An unexpected error occurred. Please try again.");
          }
        }
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(onSubmit);
  };

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false);
    setCreatedCaseId(null);
    // Call success callback and close signup modal
    if (onSuccess) {
      onSuccess();
    }
    onClose();
  };

  return (
    <div className="p-2">
      {/* Hide form content when success modal is shown */}
      {!showSuccessModal && (
        <>
          {/* Header */}
          <div>
            <h2 className="text-xl text-center font-bold text-novaNeutral-700 mb-4">
              Create Your Account
            </h2>
            <p className="text-gray-500 text-center text-sm mb-2">
              Create an account to schedule your legal consultation
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-novaCaution-50 border border-novaCaution-200 rounded-lg">
              <p className="text-novaCaution-600 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleFormSubmit} className="space-y-4 mt-4">
            {/* First Name and Last Name Row */}
            <div className="grid grid-cols-2 gap-4">
              <FormInput
                name="firstName"
                type="text"
                label="First Name"
                placeholder="First name"
                maxLength={INPUT_MAX_LENGTH.REGISTER_CUSTOMER_NAME_TEXT}
                required
                autoComplete="given-name"
                {...createFieldProps("firstName",formData,errors,touched,handleChange,handleBlur)}
              />

              <FormInput
                name="lastName"
                type="text"
                label="Last Name"
                placeholder="Last name"
                maxLength={INPUT_MAX_LENGTH.REGISTER_CUSTOMER_NAME_TEXT}
                required
                autoComplete="family-name"
                {...createFieldProps("lastName",formData,errors,touched,handleChange,handleBlur)}
              />
            </div>

            {/* Phone Number with Country Code */}
            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-1">
                Phone Number <span className="text-novaNeutral-400 text-xs">(Optional)</span>
              </label>
              <div className="grid grid-cols-[100px_1fr] gap-2">
                {/* Country Code Selector */}
                <PhoneCountryCodeSelect
                  value={selectedCountryCode}
                  onChange={handleCountryCodeChange}
                  disabled={isSubmitting}
                />
                
                {/* Phone Number Input */}
                <div className="relative">
                  <input
                    name="phone"
                    required={false}
                    type="tel"
                    placeholder="123 456 7890"
                    value={formData.phone || ''}
                    onChange={(e) => handlePhoneChange('phone', e.target.value)}
                    onBlur={() => handleBlur('phone')}
                    disabled={isSubmitting}
                    autoComplete="tel"
                    className={`w-full px-3 py-2.5 text-sm border border-novaNeutral-300 rounded-md focus:outline-none focus:ring-novaPrimary-500 focus:border-novaPrimary-500 
                      ${
                      isSubmitting ? 'bg-novaNeutral-100 cursor-not-allowed' : ''
                      }`
                    }
                  />
                </div>
              </div>
            </div>

            {/* Email Address */}
            <FormInput
              name="email"
              type="email"
              label="Email Address"
              placeholder="Enter your email address"
              required
              autoComplete="email"
              {...createFieldProps("email",formData,errors,touched,handleChange,handleBlur)}
            />

            {/* Password */}
            <FormInput
              name="password"
              type="password"
              label="Password"
              placeholder="Enter your password"
              maxLength={INPUT_MAX_LENGTH.REGISTER_CUSTOMER_PASSWORD_TEXT}
              required
              showPasswordToggle
              autoComplete="new-password"
              {...createFieldProps("password",formData,errors,touched,handleChange,handleBlur)}
            />

            {/* Confirm Password */}
            <FormInput
              name="confirmPassword"
              type="password"
              label="Confirm Password"
              placeholder="Confirm your password"
              maxLength={INPUT_MAX_LENGTH.REGISTER_CUSTOMER_PASSWORD_TEXT}
              required
              showPasswordToggle
              autoComplete="new-password"
              {...createFieldProps("confirmPassword",formData,errors,touched,handleChange,handleBlur)}
            />

            {/* Terms and Conditions Checkbox */}
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="acceptTerms"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                className="h-4 w-4 rounded border border-novaNeutral-300 text-novaPrimary-600"
              />
              <label htmlFor="acceptTerms" className="text-xs text-novaNeutral-700 leading-relaxed">
                I agree to the{" "}
                <a
                   href="/user-agreement"
                   target="_blank"           // ← Opened in new tab
                   rel="noopener noreferrer"
                  className="text-novaPrimary-600 hover:text-novaPrimary-700 underline font-medium"
                >
                  User Agreement
                </a>{" "}
                and{" "}
                <a
                  href="/privacy-policy"
                  target="_blank"           // ← Opened in new tab
                  rel="noopener noreferrer"
                  className="text-novaPrimary-600 hover:text-novaPrimary-700 underline font-medium"
                >
                  Privacy Policy
                </a>
              </label>
            </div>

            {/* Create Account Button */}
            <FormButton
              type="submit"
              variant="success"
              size="lg"
              disabled={!isValid || isSubmitting || !acceptTerms}
              loading={isSubmitting}
              loadingText="Creating Account..."
              className="w-full text-sm text-white"
            >
              Create Account
            </FormButton>
            <div className="flex text-sm items-center justify-center">
              Already have an account?
            <button
              type="button"
              onClick={() => {
                onClose();
                switchModal("signin", resolveId);
              }}
              className="text-sm text-novaPrimary-600 hover:text-legal-navy ml-2"
              >
                Sign In
              </button>
            </div>
          </form>

          {/* Toast Container */}
          <ToastContainer alerts={toasts} onDismiss={removeToast} />
        </>
      )}

      {/* Success Popup */}
      <CreateCasePopup
        isOpen={showSuccessModal}
        onClose={handleSuccessModalClose}
        caseId={createdCaseId || ""}
      />
    </div>
  );
};

export default SignupForm;
