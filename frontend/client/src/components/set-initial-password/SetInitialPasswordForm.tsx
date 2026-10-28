import React, { useState, useMemo } from "react";
import { api, ApiError } from "../../lib/api";
import novaLogo from "@/assets/ui/nova_logo.png";
import {
  useFormValidation,
  PATTERNS,
  FormValidationSchema,
  ERROR_MESSAGES,
} from "../../utils/formValidator";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "../../utils/formComponents";
import { toastManager, createErrorToast, createSuccessToast } from "../../utils/toasts";

interface SetInitialPasswordFormProps {
  token?: string;
  onSuccess?: () => void; 
  onError?: () => void;
}

// Password strength calculator
const calculatePasswordStrength = (password: string): { score: number; label: string; color: string; bgColor: string } => {
  if (!password) {
    return { score: 0, label: "", color: "", bgColor: "" };
  }

  let score = 0;
  
  // Length check
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (password.length >= 16) score++;
  
  // Character variety checks
  if (/[a-z]/.test(password)) score++; // lowercase
  if (/[A-Z]/.test(password)) score++; // uppercase
  if (/[0-9]/.test(password)) score++; // numbers
  if (/[^a-zA-Z0-9]/.test(password)) score++; // special characters
  
  // Bonus for having all character types
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[^a-zA-Z0-9]/.test(password);
  
  if (hasLower && hasUpper && hasNumber && hasSpecial) score++;
  
  // Return strength based on score
  if (score <= 2) {
    return { score: 1, label: "Weak", color: "text-red-600", bgColor: "bg-red-500" };
  } else if (score <= 4) {
    return { score: 2, label: "Fair", color: "text-orange-600", bgColor: "bg-orange-500" };
  } else if (score <= 6) {
    return { score: 3, label: "Good", color: "text-yellow-600", bgColor: "bg-yellow-500" };
  } else if (score <= 7) {
    return { score: 4, label: "Strong", color: "text-green-600", bgColor: "bg-green-500" };
  } else {
    return { score: 5, label: "Very Strong", color: "text-green-700", bgColor: "bg-green-600" };
  }
};

// Password Strength Meter Component
const PasswordStrengthMeter: React.FC<{ password: string }> = ({ password }) => {
  const strength = useMemo(() => calculatePasswordStrength(password), [password]);
  
  if (!password) return null;
  
  const widthPercentage = (strength.score / 5) * 100;
  
  return (
    <div className="mt-2 space-y-2">
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${strength.bgColor}`}
          style={{ width: `${widthPercentage}%` }}
        />
      </div>
      
      {/* Strength label */}
      <div className="flex items-center justify-between text-sm">
        <span className={`font-medium ${strength.color}`}>
          Password Strength: {strength.label}
        </span>
        
        {/* Tips for improving password */}
        {strength.score < 4 && (
          <span className="text-xs text-novaNeutral-500">
            {strength.score < 2 ? "Add more characters" : "Add special characters"}
          </span>
        )}
      </div>
      
      {/* Password requirements checklist */}
      <div className="mt-3 space-y-1 text-xs">
        <div className={`flex items-center gap-2 ${password.length >= 8 ? 'text-green-600' : 'text-novaNeutral-400'}`}>
          <i className={`fas ${password.length >= 8 ? 'fa-check-circle' : 'fa-circle'}`}></i>
          <span>At least 8 characters</span>
        </div>
        <div className={`flex items-center gap-2 ${/[A-Z]/.test(password) ? 'text-green-600' : 'text-novaNeutral-400'}`}>
          <i className={`fas ${/[A-Z]/.test(password) ? 'fa-check-circle' : 'fa-circle'}`}></i>
          <span>One uppercase letter</span>
        </div>
        <div className={`flex items-center gap-2 ${/[a-z]/.test(password) ? 'text-green-600' : 'text-novaNeutral-400'}`}>
          <i className={`fas ${/[a-z]/.test(password) ? 'fa-check-circle' : 'fa-circle'}`}></i>
          <span>One lowercase letter</span>
        </div>
        <div className={`flex items-center gap-2 ${/[0-9]/.test(password) ? 'text-green-600' : 'text-novaNeutral-400'}`}>
          <i className={`fas ${/[0-9]/.test(password) ? 'fa-check-circle' : 'fa-circle'}`}></i>
          <span>One number</span>
        </div>
      </div>
    </div>
  );
};

const SetInitialPasswordForm: React.FC<SetInitialPasswordFormProps> = ({
  token,
  onSuccess,
  onError,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Get email from localStorage for Chrome Password Manager
  // Use state with initial value, but allow Chrome to update it
  const [usernameValue, setUsernameValue] = useState(() => {
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const userData = JSON.parse(userStr);
        return userData?.email || "";
      }
    } catch {}
    return "";
  });

  // Define validation schema with useMemo to prevent recreation
  const validationSchema: FormValidationSchema = useMemo(() => ({
    new_password: {
      required: true,
      pattern: PATTERNS.PASSWORD,
    },
    confirm_password: {
      required: true,
    },
  }), []);

  // Cross-field validation for password confirmation with useMemo
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
    setSuccessMessage(null);

      try {
        let response: any;

        if (token) {
          // If token is available, call set-initial-password with token as Bearer authorization
          response = await api.post(
            "/v1/auth/set-initial-password",
            { new_password: data.new_password },
            { headers: { Authorization: `Bearer ${token}` } }
          );
        } else {
          // Otherwise, call create-password (uses stored auth token automatically)
          response = await api.post("/v1/auth/create-password", {
            new_password: data.new_password,
          });
        }

        if (response.success) {
          // Update localStorage: user can now update password
          localStorage.setItem("password_state", "can_update");
          
          // Extract success message from response
          const successMsg =
            response.message?.[0]?.message ||
            response.message ||
            "Your password has been set successfully!";
          toastManager.addToast(createSuccessToast("Password Created", successMsg));
          onSuccess?.();
        } else {
          // Extract error message from response
          const errorMsg =
            response.message?.[0]?.message ||
            response.message ||
            "Failed to create password. Please try again.";
          toastManager.addToast(createErrorToast("Failed to Create Password", errorMsg));
          onError?.();
        }
      } catch (error: any) {
        let errorMessage = "Failed to create password. Please try again.";
        if (error?.message) {
          const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
          if (match && match[1]) {
            errorMessage = match[1];
          }
        }
        // toastManager.addToast(createErrorToast("Error", errorMessage));
        onError?.();
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
    <div className="bg-white rounded-xl shadow-2xl p-8 relative sm:w-[450px] w-full">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-opacity-100 rounded-lg flex items-center justify-center mx-auto mb-4">
          <img src={novaLogo} alt="NovaAI" className="w-16 h-16" />
        </div>
        <h2 className="text-2xl font-bold text-novaNeutral-900 mb-2">
          Set Your Password
        </h2>
        <p className="text-novaNeutral-600">Create a secure password for your account</p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 p-4 bg-novaSuccess-50 border border-novaSuccess-200 rounded-lg">
          <p className="text-novaSuccess-600 text-sm">{successMessage}</p>
        </div>
      )}

      {/* Set Initial Password Form */}
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
        
        <div>
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
          <PasswordStrengthMeter password={formData.new_password || ""} />
        </div>

        <FormInput
          name="confirm_password"
          type="password"
          label="Confirm Password"
          placeholder="Confirm your new password"
          required
          showPasswordToggle={true}
          autoComplete="new-password"
          {...confirmPasswordProps}
        />

        <FormButton
          type="submit"
          variant="primary"
          size="lg"
          disabled={!isValid}
          loading={isSubmitting}
          loadingText="Setting Password..."
          className="w-full bg-novaPrimary-500 text-white hover:bg-novaPrimary-900"
        >
          Set Password
        </FormButton>
      </form>
    </div>
  );
};

export default SetInitialPasswordForm;

