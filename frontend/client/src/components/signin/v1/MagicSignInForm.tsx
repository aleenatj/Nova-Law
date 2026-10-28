import React, { useState, useEffect, useCallback, useRef } from "react";
import { api, ApiError } from "../../../lib/api";
import { useAuth } from "../../../contexts/AuthContext";
import novaLogo from "@/assets/ui/nova_logo.png";
import {
  useFormValidation,
  FormValidationSchema,
  PATTERNS,
} from "../../../utils/formValidator";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "../../../utils/formComponents";
import { createSuccessToast, createErrorToast, toastManager } from "../../../utils/toasts";

// Email validation schema - defined outside component for better performance
const magicLinkValidationSchema: FormValidationSchema = {
  email: {
    required: true,
    pattern: PATTERNS.EMAIL,
  },
};

// Constants
const SUCCESS_MESSAGE = "A sign-in link has been sent to your email address. Please check your inbox.";
const TOAST_SUCCESS_TITLE = "Email Sent!";
const TOAST_SUCCESS_MESSAGE = "Please check your email for the sign-in link.";
const TOAST_DURATION = 5000; 
const DEFAULT_ERROR_MESSAGE = "Failed to send sign-in link. Please try again.";
const LOGIN_WITH_PASSWORD_STORAGE_KEY = "nova_loginWithPassword";

interface MagicSignInContentProps {
  onClose: () => void;
  onSwitchModal?: (type: "forgot-password" | "reset-password") => void;
  resolveId?: string;
  invalidlink?: boolean;
  email?: string;
  user_id?: string;
}

// Helper function to extract error message from ApiError
const extractErrorMessage = (err: ApiError): string => {
  try {
    const match = err.message.match(/\d+ \w+(?:\s+\w+)* - (.+)/);
    if (match && match[1]) {
      const responseText = match[1];
      try {
        const errorData = JSON.parse(responseText);
        return errorData.message || errorData.detail || errorData.error || errorData.detail?.[0]?.msg || DEFAULT_ERROR_MESSAGE;
      } catch {
        return responseText;
      }
    }
    return err.message;
  } catch {
    return err.message || DEFAULT_ERROR_MESSAGE;
  }
};

const SignInForm: React.FC<MagicSignInContentProps> = ({
  onClose,
  resolveId,
  invalidlink,
  email: expiredEmail,
  user_id,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showSuccessScreen, setShowSuccessScreen] = useState(false);
  const [loginWithPassword, setLoginWithPassword] = useState(() => {
    // Initialize from localStorage
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(LOGIN_WITH_PASSWORD_STORAGE_KEY);
      return stored === "true";
    }
    return false;
  });
  const { isAuthenticated, user } = useAuth();
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Check if user is already authenticated and close modal automatically
  useEffect(() => {
    if (isAuthenticated && user) {
      onClose();
    }
  }, [isAuthenticated, user, onClose]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Save loginWithPassword to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(LOGIN_WITH_PASSWORD_STORAGE_KEY, String(loginWithPassword));
      // Dispatch custom event to notify other components
      window.dispatchEvent(new CustomEvent('loginPreferenceChanged'));
    }
  }, [loginWithPassword]);

  // Use form validation hook
  const {
    formData,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
  } = useFormValidation(magicLinkValidationSchema);

  const onSubmit = useCallback(async (data: any) => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    setShowSuccessScreen(false);

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    try {
      const payload = {
        user_name: user_id || data.email,
        ...(resolveId ? { case_id: resolveId } : {}),
      };

      const response = (await api.post("/v1/auth/send-login-link", payload)) as any;

      if (response?.success) {
        // Handle backend response messages (could be string or array)
        const messagesArray: Array<{ success: boolean; message: string }> = Array.isArray(response?.message)
          ? response.message
          : response?.message
          ? [{ success: response.success, message: String(response.message) }]
          : [];

        // Show toast messages from backend response
        if (messagesArray.length > 0) {
          messagesArray.forEach((msg) => {
            if (msg.success) {
              toastManager.addToast(
                createSuccessToast("Success", msg.message, TOAST_DURATION)
              );
            } else {
              toastManager.addToast(
                createErrorToast("Error", msg.message)
              );
            }
          });
        } else {
          // Fallback to default success message if no messages from backend
          toastManager.addToast(
            createSuccessToast(TOAST_SUCCESS_TITLE, TOAST_SUCCESS_MESSAGE, TOAST_DURATION)
          );
        }

        // Determine success message to show in UI
        const successMsg = messagesArray.find((msg) => msg.success)?.message || SUCCESS_MESSAGE;
        setSuccessMessage(successMsg);
        setShowSuccessScreen(true);
      } else {
        // Handle error response messages
        const messagesArray: Array<{ success: boolean; message: string }> = Array.isArray(response?.message)
          ? response.message
          : response?.message
          ? [{ success: false, message: String(response.message) }]
          : [];

        const errorMsg = messagesArray.find((msg) => !msg.success)?.message || response?.message || DEFAULT_ERROR_MESSAGE;
        setError(errorMsg);

        // Show error toast from backend response
        if (messagesArray.length > 0) {
          messagesArray.forEach((msg) => {
            if (!msg.success) {
              toastManager.addToast(
                createErrorToast("Error", msg.message)
              );
            }
          });
        } else if (errorMsg) {
          toastManager.addToast(
            createErrorToast("Error", errorMsg)
          );
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        const errorMsg = extractErrorMessage(err);
        setError(errorMsg);
        toastManager.addToast(
          createErrorToast("Error", errorMsg)
        );
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [resolveId, onClose, user_id]);

  const handleFormSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(onSubmit);
  }, [handleSubmit, onSubmit]);

  const handleResendLink = useCallback(() => {
    setError(null);
    if (user_id) {
      // When user_id is available, call onSubmit directly with user_id
      onSubmit({ email: user_id });
    } else {
      handleSubmit(onSubmit);
    }
  }, [handleSubmit, onSubmit, user_id]);

  // Create field props for email field
  const emailProps = createFieldProps(
    "email",
    formData,
    errors,
    touched,
    handleChange,
    handleBlur
  );

  return (
    <>
      {/* Header */}
      <div className="text-center mb-8" style={{ marginBottom: invalidlink ? "20px" : "30px" }}>
        <div className="w-[100px] h-[100px] rounded-xl flex items-center justify-center mx-auto mb-4">
          <img src={novaLogo} alt="Nova" className="w-[90px] h-[90px]" />
        </div>
        {!showSuccessScreen && <>
        <h2 className="text-2xl font-bold text-novaNeutral-900 mb-2">
          {user_id ? "Link expired" : "Sign in to your Nova account"}
        </h2>
        <p className="text-novaNeutral-600 text-base">
          {user_id 
            ? (
              <>
                Your login link has expired{expiredEmail && ` for ${expiredEmail}`}. Click the button below to receive a new magic link.
              </>
            )
            : "Welcome back! Enter your email address below to receive a magic link to access your account."}
        </p>
        </>}
      </div>

      {invalidlink && !showSuccessScreen && !user_id && (
        <div className="mb-6 px-4 text-center">
          <p className="text-novaCaution-800 text-md">
            Link expired - please resend your email address.
          </p>
        </div>
      )}

      {showSuccessScreen ? (
        /* Success Screen */
        <div className="text-center space-y-6">
          <h2 className="text-2xl font-bold text-novaNeutral-900">
            Sign-in link is on its way
          </h2>
          <p className="text-novaNeutral-600 text-base">
            Our email should be in your inbox now, then just click the magic link within to access your account.
          </p>
          <div className="pt-4">
            <p className="text-novaNeutral-600 text-base mb-2">Nothing arrived?</p>
            <button
              onClick={handleResendLink}
              disabled={isSubmitting}
              className="text-novaPurple-600 hover:text-novaPurple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Resend magic link
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-novaCaution-50 border border-novaCaution-200 rounded-lg">
              <p className="text-novaCaution-600 text-sm">{error}</p>
            </div>
          )}

          {/* Show resend button only when user_id is available (expired token case) */}
          {user_id ? (
            <div className="space-y-6">
              <FormButton
                type="button"
                variant="primary"
                size="lg"
                onClick={handleResendLink}
                disabled={isSubmitting}
                loading={isSubmitting}
                loadingText="Sending link..."
                className="w-full bg-novaNeutral-800 text-white hover:bg-novaNeutral-900 font-semibold"
              >
                Resend Link
              </FormButton>
            </div>
          ) : (
            /* Magic Link Sign In Form */
            <form onSubmit={handleFormSubmit} className="space-y-6">
              <FormInput
                name="email"
                type="email"
                label="Email address"
                placeholder="Enter your email address"
                required
                {...emailProps}
              />

              <FormButton
                type="submit"
                variant="primary"
                size="lg"
                disabled={!isValid || isSubmitting}
                loading={isSubmitting}
                loadingText="Sending link..."
                className="w-full bg-novaNeutral-800 text-white hover:bg-novaNeutral-900 font-semibold"
              >
                Get magic link
              </FormButton>

              <div className="flex items-center mt-2 justify-center">
                <button
                  type="button"
                  onClick={() => setLoginWithPassword(true)}
                  className="text-novaPurple-600 hover:text-novaPurple-700 text-sm select-none"
                >
                  Sign in with password
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </>
  );
};

export default SignInForm;
