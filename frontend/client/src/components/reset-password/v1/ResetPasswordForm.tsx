import React, { useState, useMemo } from "react";
import { api, ApiError } from "../../../lib/api";
import {
  useFormValidation,
  PATTERNS,
  FormValidationSchema,
  ERROR_MESSAGES,
} from "../../../utils/formValidator";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "../../../utils/formComponents";
import { useModal } from "@/contexts/ModalContext";
import passwordIcon from "@/assets/ui/Password.png";
const LOGIN_WITH_PASSWORD_STORAGE_KEY = "nova_loginWithPassword";

interface ResetPasswordFormProps {
  onClose: () => void;
  onSuccess?: () => void;
  token?: string;
}

const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({
  onClose,
  onSuccess,
  token,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const { switchModal } = useModal();
  
  // Get email from localStorage for Chrome Password Manager
  const [usernameValue] = useState(() => {
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const userData = JSON.parse(userStr);
        return userData?.email || "";
      }
    } catch {}
    return "";
  });
  
  // Define validation schema (memoized to prevent infinite re-renders)
  const validationSchema: FormValidationSchema = useMemo(() => ({
    new_password: {
      required: true,
      pattern: PATTERNS.PASSWORD,
    },
    confirm_password: {
      required: true,
    },
  }), []);
  
  // Handle switching to magic link sign-in
  const handleSwitchToMagicLink = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem(LOGIN_WITH_PASSWORD_STORAGE_KEY, "false");
      window.dispatchEvent(new CustomEvent('loginPreferenceChanged'));
      switchModal("signin");
    }
  };
  
  // Cross-field validation for password confirmation (memoized to prevent infinite re-renders)
  const crossFieldValidators = useMemo(() => ({
    confirm_password: (data: any) => {
      if (
        data.new_password &&
        data.confirm_password &&
        data.new_password !== data.confirm_password
      ) {
        return ERROR_MESSAGES.PASSWORDS_MATCH;
      }
      return null;
    },
  }), []);

  // Use form validation hook with cross-field validation
  const {
    formData,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
  } = useFormValidation(validationSchema, crossFieldValidators);

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    if (!token) {
      setError("Reset token is missing. Please use the link from your email.");
      setIsSubmitting(false);
      return;
    }

    try {
      const response = (await api.post(
        "/v1/auth/reset-password",
        { new_password: data.new_password },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )) as any;

      if (response.success) {
        setSuccessMessage("Password reset successfully! You can now sign in.");
        setTimeout(() => {
          onSuccess?.();
          window.location.href = "/";
        }, 2000);
      } else {
        // Simple error handling - just show the first error message
        const errorMsg =
          response.message?.[0]?.message ||
          "Failed to reset password. Please try again.";
        setError(errorMsg);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        // Extract JSON from the error message
        try {
          // Try different regex patterns
          let jsonMatch = err.message.match(/\d+ \w+ - (.+)/);

          if (!jsonMatch) {
            // Try alternative pattern
            jsonMatch = err.message.match(/\d+ \w+(?:\s+\w+)* - (.+)/);
          }

          if (!jsonMatch) {
            // Try finding JSON directly
            const jsonStart = err.message.indexOf("{");
            if (jsonStart !== -1) {
              const jsonPart = err.message.substring(jsonStart);
              jsonMatch = ["", jsonPart] as RegExpMatchArray;
            }
          }

          if (jsonMatch && jsonMatch[1]) {
            const errorData = JSON.parse(jsonMatch[1]);
            const errorMsg =
              errorData.message?.[0]?.message ||
              "Failed to reset password. Please try again.";
            setError(errorMsg);
          } else {
            setError("Failed to reset password. Please try again.");
          }
        } catch {
          setError("Failed to reset password. Please try again.");
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

  // Create field props for form fields
  const newPasswordProps = createFieldProps(
    "new_password",
    formData,
    errors,
    touched,
    handleChange,
    handleBlur
  );
  const confirmPasswordProps = createFieldProps(
    "confirm_password",
    formData,
    errors,
    touched,
    handleChange,
    handleBlur
  );

  return (
    <div className="bg-white py-8 px-6 shadow rounded-lg sm:px-10">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4">
          <img src={passwordIcon} alt="Password" className="w-12 h-16" />
        </div>
        <h2 className="text-2xl font-bold text-novaNeutral-900 mb-2">
          Reset your password
        </h2>
        <p className="text-novaNeutral-600">Enter your new password below</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-novaCaution-50 border border-novaCaution-200 rounded-lg">
          <p className="text-novaCaution-600 text-sm">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 p-4 bg-novaSuccess-50 border border-novaSuccess-200 rounded-lg">
          <p className="text-novaSuccess-600 text-sm">{successMessage}</p>
        </div>
      )}

      {/* Reset Password Form */}
      <form onSubmit={handleFormSubmit} className="space-y-6">
        <input
          type="text"
          name="username"
          autoComplete="username"
          value={usernameValue}
          readOnly
          style={{
            position: "absolute",
            left: "-9999px",
            width: "1px",
            height: "1px",
            opacity: 0,
          }}
        />
        
        <FormInput
          name="new_password"
          type="password"
          label="New Password"
          placeholder="Enter your new password"
          required
          showPasswordToggle={true}
          autoComplete="new-password"
          {...newPasswordProps}
        />

        <FormInput
          name="confirm_password"
          type="password"
          label="Confirm New Password"
          placeholder="Confirm your new password"
          required
          showPasswordToggle={true}
          autoComplete="new-password"
          {...confirmPasswordProps}
        />

        <div className="flex space-x-3">
          <FormButton
            type="button"
            variant="outline"
            onClick={onClose}
            className="flex-1"
          >
            Cancel
          </FormButton>
          <FormButton
            type="submit"
            variant="primary"
            disabled={!isValid}
            loading={isSubmitting}
            loadingText="Resetting..."
            className="flex-1 text-white"
          >
            Reset Password
          </FormButton>
        </div>
        <div className="flex items-center justify-center">
          <button
            type="button"
            onClick={handleSwitchToMagicLink}
            className="text-sm text-novaPurple-600 hover:text-novaPurple-700"
          >
            Sign in without password
          </button>
        </div>
      </form>
    </div>
  );
};

export default ResetPasswordForm;
