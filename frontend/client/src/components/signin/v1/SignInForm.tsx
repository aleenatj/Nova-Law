import React, { useState, useEffect } from "react";
import { api, ApiError, tokenManager } from "../../../lib/api";
import { useRole } from "../../../contexts/RoleContext";
import { useAuth } from "../../../contexts/AuthContext";
import { useModal } from "@/contexts/ModalContext";
import { getAndClearRedirectAfterLogin } from "@/utils/redirectAfterLogin";
import novaLogo from "@/assets/ui/nova_logo.png";
import {
  useFormValidation,
} from "../../../utils/formValidator";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "../../../utils/formComponents";
import { signInValidationSchema } from "../../../utils/validationSchemas";
import CreateCasePopup from "../../case/v1/CreateCasePopup";
import { createSuccessToast, ToastContainer } from "../../../utils/toasts";

const LOGIN_WITH_PASSWORD_STORAGE_KEY = "nova_loginWithPassword";

interface SignInContentProps {
  onClose: () => void;
  onSwitchModal?: (type: "forgot-password" | "reset-password") => void;
  resolveId?: string;
}

const SignInForm: React.FC<SignInContentProps> = ({
  onClose,
  onSwitchModal,
  resolveId,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<any[]>([]);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [createdCaseId, setCreatedCaseId] = useState<string | null>(null);
  const [loginWithPassword, setLoginWithPassword] = useState(() => {
    // Initialize from localStorage
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(LOGIN_WITH_PASSWORD_STORAGE_KEY);
      return stored === "true";
    }
    return true; // Default to password form
  });
  const { setCurrentRole, refreshRoleFromStorage } = useRole();
  const { user, isAuthenticated } = useAuth();
  const { switchModal } = useModal();

  // Toast management functions
  const addToast = (toast: any) => {
    setToasts(prev => [...prev, toast]);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  // Check if user is already authenticated and close modal automatically
  useEffect(() => {
    if (isAuthenticated && user) {
      onClose();
    }
  }, [isAuthenticated, user, onClose]);

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
  } = useFormValidation(signInValidationSchema);

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const formdata = new FormData();
      formdata.append("username", data.username);
      formdata.append("password", data.password);
      if (resolveId) {
        formdata.append("resolve_id", resolveId);
      }

      const response = (await api.post("/v1/auth/login", formdata)) as any;

      if (response && response.data) {
        const responseData = response.data;
        tokenManager.setTokens(
          responseData.access_token,
          responseData.refresh_token,
          responseData.token_type
        );
        localStorage.setItem("user", JSON.stringify(responseData.user_data));
        
        // Store password state
        if (responseData.password_state) {
          localStorage.setItem("password_state", responseData.password_state);
        }
        
        // Store case.id if present in response
        if (responseData.case?.id) {
          sessionStorage.setItem("current_case_id", responseData.case.id);
        }
        
        sessionStorage.removeItem("resolve_session_data");
        sessionStorage.removeItem("resolveId");

        if (responseData.user_data && responseData.user_data.role_code) {
          setCurrentRole(
            typeof responseData.user_data.role_code === "string"
              ? responseData.user_data.role_code.toLowerCase()
              : responseData.user_data.role_code
          );
        } else {
          refreshRoleFromStorage();
        }

        // Handle different sign-in contexts
        if ((window as any).isTokenExpirySignIn) {
          // Token expiry sign-in - reload current page to refetch data with new auth
          (window as any).isTokenExpirySignIn = false;
          window.location.reload();
          return;
        }

        // Check if a case was created from resolve
        if (responseData.case && responseData.case.case_id) {
          setCreatedCaseId(responseData.case.case_id);
          setShowSuccessModal(true);
          addToast(createSuccessToast(
            "Sign In Successful!",
            `You've been signed in and case ${responseData.case.case_no} has been created.`,
            3000
          ));
          return;
        }

        // Priority: 1. Stored redirect URL (localStorage), 2. API redirect_path, 3. Default dashboard
        const storedRedirect = getAndClearRedirectAfterLogin();
        const apiRedirectPath = responseData.redirect_path && typeof responseData.redirect_path === "string"
          ? responseData.redirect_path
          : null;
        const destination = storedRedirect || apiRedirectPath || "/case-dashboard";
        window.location.href = destination;
        return;
      } else {
        setError("Unexpected response from server. Please try again.");
        return;
      }
    } catch (err) {
      if (err instanceof ApiError) {
        // Try to extract error message from response for all error types
        let errorMsg: string | undefined;
        
        try {
          // The ApiError message format is: "400 Bad Request - {responseText}"
          // Extract the response text after the status and status text
          const match = err.message.match(/\d+ \w+(?:\s+\w+)* - (.+)/);
          if (match && match[1]) {
            const responseText = match[1];
            
            // Try to parse as JSON first
            try {
              const errorData = JSON.parse(responseText);
              errorMsg = errorData.message || errorData.detail || errorData.error || errorData.detail?.[0]?.msg;
            } catch {
              // If not JSON, use the raw response text
              errorMsg = responseText;
            }
          } else {
            // Fallback: use the entire message
            errorMsg = err.message;
          }
        } catch (parseError) {
          // If all parsing fails, use the raw message
          errorMsg = err.message;
        }

        // Use extracted error message or fallback based on status
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
    onClose();
  };

  // Create field props for form fields
  const usernameProps = createFieldProps(
    "username",
    formData,
    errors,
    touched,
    handleChange,
    handleBlur
  );
  const passwordProps = createFieldProps(
    "password",
    formData,
    errors,
    touched,
    handleChange,
    handleBlur
  );

  return (
    <>
      {/* Hide form content when success modal is shown */}
      {!showSuccessModal && (
        <>
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-[100px] h-[100px] rounded-xl flex items-center justify-center mx-auto mb-4">
              <img src={novaLogo} alt="NovaAI" className="w-[90px] h-[90px]" />
            </div>
            <h2 className="text-2xl font-bold text-novaNeutral-900 mb-2">
              Sign in to your Nova account
            </h2>
            <p className="text-novaNeutral-600">Enter your email address and password below to access your account. </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-novaCaution-50 border border-novaCaution-200 rounded-lg">
              <p className="text-novaCaution-600 text-sm">{error}</p>
            </div>
          )}

          {/* Sign In Form */}
          <form onSubmit={handleFormSubmit} className="space-y-6">
        <FormInput
          name="username"
          type="email"
          label="Email Address"
          placeholder="Enter your email address"
          required
          autoComplete="email"
          {...usernameProps}
        />

        <FormInput
          name="password"
          type="password"
          label="Password"
          placeholder="Enter your password"
          required
          showPasswordToggle={true}
          autoComplete="current-password"
          {...passwordProps}
        />

        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={() => switchModal("forgot-password")}
            className="text-sm text-novaPurple-600 hover:text-novaPurple-700"
          >
            Forgot password?
          </button>
        </div>

        <FormButton
          type="submit"
          variant="primary"
          size="lg"
          disabled={!isValid}
          loading={isSubmitting}
          loadingText="Signing In..."
          className="w-full bg-novaPrimary-500 text-white hover:bg-novaPrimary-900"
        >
          Sign In
        </FormButton>
        <div className="flex items-center mt-2 justify-center">
          <button
            type="button"
            onClick={() => setLoginWithPassword(false)}
            className="text-novaPurple-600 hover:text-novaPurple-700 text-sm select-none"
          >
            Sign in without password
          </button>
        </div>

        {/* Only show signup link if we have a resolveId (switched from signup form) */}
        {resolveId && (
          <div className="flex text-sm items-center justify-center">
            Don't have an account?
            <button
              type="button"
              onClick={() => {
                switchModal("signup", resolveId);
              }}
              className="text-sm text-novaPrimary-600 hover:text-legal-navy ml-2"
            >
              Sign Up
            </button>
          </div>
        )}
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
    </>
  );
};

export default SignInForm;
