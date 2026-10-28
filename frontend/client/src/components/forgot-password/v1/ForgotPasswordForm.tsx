import React, { useState, useMemo } from "react";
import { api, ApiError } from "../../../lib/api";
import { useModal } from "@/contexts/ModalContext";
import {
  useFormValidation,
  PATTERNS,
  FormValidationSchema,
} from "../../../utils/formValidator";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "../../../utils/formComponents";
import passwordIcon from "@/assets/ui/Password.png";
const LOGIN_WITH_PASSWORD_STORAGE_KEY = "nova_loginWithPassword";

interface ForgotPasswordFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({
  onClose,
  onSuccess,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const { switchModal } = useModal();

  // Define validation schema (memoized to prevent infinite re-renders)
  const validationSchema: FormValidationSchema = useMemo(() => ({
    email: {
      required: true,
      pattern: PATTERNS.EMAIL,
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

  // Use form validation hook
  const {
    formData,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
  } = useFormValidation(validationSchema);

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = (await api.post("/v1/auth/forgot-password", {
        email: data.email,
      })) as any;

      if (response.success) {
        setSuccessMessage("Password reset link sent to your email!");
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 4000);
      } else {
        const errorMsg =
          response.message?.[0]?.message ||
          "Failed to send reset link. Please try again.";
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
              "Failed to send reset link. Please try again.";
            setError(errorMsg);
          } else {
            setError("Failed to send reset link. Please try again.");
          }
        } catch (parseError) {
          console.error("JSON parse error:", parseError);
          setError("Failed to send reset link. Please try again.");
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

  // Create field props for email
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
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4">
          <img src={passwordIcon} alt="Password" className="w-12 h-16" />
        </div>
        <h2 className="text-2xl font-bold text-novaNeutral-900 mb-2">
          Forgot Password?
        </h2>
        <p className="text-novaNeutral-600 w-[80%] mx-auto">
          Enter your email address below to receive a reset link.
        </p>
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

      {/* Forgot Password Form */}
      <form onSubmit={handleFormSubmit} className="space-y-6">
        <FormInput
          name="email"
          type="email"
          label="Email Address"
          placeholder="Enter your email address"
          required
          autoComplete="email"
          {...emailProps}
        />

        <div className="flex space-x-3">
          <FormButton
            type="button"
            variant="outline"
            onClick={() => switchModal("signin")}
            className="flex-1"
          >
            Back to Sign In
          </FormButton>
          <FormButton
            type="submit"
            variant="primary"
            disabled={!isValid}
            loading={isSubmitting}
            loadingText="Sending..."
            className="flex-1 text-white"
          >
            Send Reset Link
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
    </>
  );
};

export default ForgotPasswordForm;
