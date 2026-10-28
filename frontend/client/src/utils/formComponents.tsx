import React, { useState } from "react";
import { ValidationResult } from "./formValidator";

// Generalized Form Input Component
export interface FormInputProps {
  name: string;
  type?: "text" | "email" | "password" | "tel" | "number" | "textarea";
  label?: string;
  placeholder?: string;
  value: any;
  maxLength?: number;
  min?: number; // Minimum value for number fields
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
  onBlur: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  errors: string[];
  touched: boolean;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  labelClassName?: string;
  errorClassName?: string;
  showPasswordToggle?: boolean; // New prop for password visibility toggle
  autoComplete?: string; // HTML autocomplete attribute for browser autofill
}

export function FormInput({
  name,
  type = "text",
  label,
  placeholder,
  value,
  maxLength,
  min,
  onChange,
  onBlur,
  errors,
  touched,
  required = false,
  disabled = false,
  className = "",
  inputClassName = "",
  labelClassName = "",
  errorClassName = "",
  showPasswordToggle = false,
  autoComplete,
}: FormInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const hasError = touched && errors.length > 0;
  const inputId = `form-input-${name}`;

  // Determine the actual input type
  const actualType =
    type === "password" && showPasswordToggle
      ? showPassword
        ? "text"
        : "password"
      : type;

  const baseInputClasses = `w-full px-3 py-2 border bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-novaPrimary focus:border-transparent transition-colors ${
    hasError
      ? "border-novaCaution-300 focus:ring-novaCaution-500"
      : "border-novaNeutral-300"
  } ${
    disabled ? "bg-novaNeutral-100 cursor-not-allowed" : ""
  } ${inputClassName}`;

  const baseLabelClasses = `block text-sm font-medium text-novaNeutral-700 mb-2 ${labelClassName}`;

  const baseErrorClasses = `mt-1 text-novaCaution-600 text-sm ${errorClassName}`;

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <label htmlFor={inputId} className={baseLabelClasses}>
          {label}
          {required && <span className="text-novaCaution-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        {type === "textarea" ? (
          <textarea
            id={inputId}
            name={name}
            value={value || ""}
            maxLength={maxLength}
            onChange={onChange}
            onBlur={onBlur}
            placeholder={placeholder}
            required={required}
            disabled={disabled}
            autoComplete={autoComplete}
            className={`${baseInputClasses} resize-vertical min-h-[80px]`}
          />
        ) : (
          <input
            id={inputId}
            name={name}
            type={actualType}
            value={value || ""}
            maxLength={maxLength}
            min={min}
            onChange={onChange}
            onBlur={onBlur}
            placeholder={placeholder}
            required={required}
            disabled={disabled}
            autoComplete={autoComplete}
            className={`${baseInputClasses} ${
              showPasswordToggle ? "pr-10" : ""
            }`}
          />
        )}

        {type === "password" && showPasswordToggle && (
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-novaNeutral-400 hover:text-novaNeutral-600 focus:outline-none"
            tabIndex={-1}
          >
            {showPassword ? (
              <i className="fas fa-eye-slash text-sm" title="Hide Password"></i>
            ) : (
              <i className="fas fa-eye text-sm" title="Show Password"></i>
            )}
          </button>
        )}
      </div>

      {hasError && (
        <div className={baseErrorClasses}>
          {errors.map((error, index) => (
            <p key={index}>{error}</p>
          ))}
        </div>
      )}
    </div>
  );
}

// Generalized Form Button Component
export interface FormButtonProps {
  type?: "button" | "submit" | "reset";
  variant?: "primary" | "secondary" | "danger" | "outline" | "success" | "custom" | "tertiary" | "gradient";
  size?: "sm" | "md" | "lg" | "custom";
  disabled?: boolean;
  loading?: boolean;
  loadingText?: string;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
}

export function FormButton({
  type = "button",
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  loadingText = "Loading...",
  children,
  onClick,
  className = "",
  style,
  title,
}: FormButtonProps) {
  const baseClasses =
    "rounded-full focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

  const variantClasses = {
    primary:
      "bg-novaPrimary-600 text-white focus:ring-novaPrimary-500 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F]",
    secondary:
      "bg-novaBlack hover:bg-novaNeutral-500 text-white focus:ring-novaNeutral-500",
    tertiary:
      "bg-novaPrimary-600 text-white focus:ring-novaPrimary-500 hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471]",
    gradient:
      "bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] text-white focus:ring-novaPrimary-500 hover:bg-gradient-to-r hover:from-[#FC3C3F] hover:to-[#FF6A42] disabled:hover:bg-gradient-to-r disabled:hover:from-[#FF6A42] disabled:hover:to-[#FC3C3F]",
    success:
      "bg-novaSuccess-600 hover:bg-novaSuccess-700 text-white focus:ring-novaSuccess-600",
    danger:
      "bg-novaCaution-600 hover:bg-novaCaution-500 text-white focus:ring-novaCaution-500",
    outline:
      "border border-novaPrimary-500 text-novaPrimary-500 hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white hover:border-transparent",
    custom: "",
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-5 py-2.5 text-lg",
    custom: "",
  };

  const buttonClasses = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={buttonClasses}
      style={style}
      title={title}
    >
      {loading ? (
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          {loadingText}
        </div>
      ) : (
        children
      )}
    </button>
  );
}

// Helper function to create form field props
export function createFieldProps(
  fieldName: string,
  formData: Record<string, any>,
  errors: Record<string, ValidationResult>,
  touched: Record<string, boolean>,
  handleChange: (field: string, value: any) => void,
  handleBlur: (field: string) => void
) {
  return {
    value: formData[fieldName] || "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      handleChange(fieldName, e.target.value),
    onBlur: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      handleBlur(fieldName),
    errors: errors[fieldName]?.errors || [],
    touched: touched[fieldName] || false,
  };
}

// Form Field Group Component for better organization
export interface FormFieldGroupProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
}

export function FormFieldGroup({
  children,
  className = "",
  title,
  description,
}: FormFieldGroupProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {title && (
        <div className="border-b border-novaNeutral-200 pb-2">
          <h3 className="text-lg font-medium text-novaNeutral-900">{title}</h3>
          {description && (
            <p className="text-sm text-novaNeutral-600 mt-1">{description}</p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

// Form Error Summary Component
export interface FormErrorSummaryProps {
  errors: Record<string, ValidationResult>;
  className?: string;
}

export function FormErrorSummary({
  errors,
  className = "",
}: FormErrorSummaryProps) {
  const allErrors = Object.values(errors)
    .filter((result) => !result.isValid)
    .flatMap((result) => result.errors);

  if (allErrors.length === 0) return null;

  return (
    <div
      className={`bg-novaCaution-50 border border-novaCaution-200 rounded-lg p-4 ${className}`}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <i className="fas fa-exclamation-triangle text-novaCaution-400"></i>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-novaCaution-800">
            Please correct the following errors:
          </h3>
          <div className="mt-2 text-sm text-novaCaution-700">
            <ul className="list-disc list-inside space-y-1">
              {allErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
