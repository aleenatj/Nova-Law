import React, { useState } from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";
import { api, ApiError, ERROR_TO_EXCLUDE } from "@/lib/api";
import { createErrorToast, createSuccessToast, toastManager } from "@/utils/toasts";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { combinePhoneNumber } from "@/utils/phoneUtils";
import { PATTERNS, validateField } from "@/utils/formValidator";

interface ContactUsResponse {
  success: boolean;
  message: Array<{ success: boolean; message: string }>;
  data: Record<string, unknown>;
}

interface FormState {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  message: string;
}

type FormErrors = Partial<Record<keyof FormState, string>>;

const initialFormState: FormState = {
  first_name: "",
  last_name: "",
  phone: "",
  email: "",
  message: "",
};

const MAX_FIRST_NAME = 100;
const MAX_LAST_NAME = 100;
const MAX_PHONE = 17;
const MAX_EMAIL = 255;
const MAX_MESSAGE = 500;

/** Capitalise first letter of each word; e.g. "hannah graham" -> "Hannah Graham" */
function titleCase(str: string): string {
  return str
    .split(/\s+/)
    .map((word) =>
      word ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase() : word
    )
    .join(" ");
}

const ContactUsPage: React.FC = () => {
  const [form, setForm] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  /** Only show validation errors after the user has attempted to submit at least once */
  const [hasAttemptedSubmit, setHasAttemptedSubmit] = useState(false);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");

  const validate = (state: FormState): FormErrors => {
    const newErrors: FormErrors = {};

    if (!state.first_name.trim()) {
      newErrors.first_name = "First name is required";
    } else if (state.first_name.length > MAX_FIRST_NAME) {
      newErrors.first_name = `First name must be at most ${MAX_FIRST_NAME} characters`;
    }

    if (!state.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    } else if (state.last_name.length > MAX_LAST_NAME) {
      newErrors.last_name = `Last name must be at most ${MAX_LAST_NAME} characters`;
    }

    const phoneResult = validateField(state.phone, {
      required: true,
      pattern: PATTERNS.PHONE,
      maxLength: MAX_PHONE,
    });
    if (!phoneResult.isValid) {
      newErrors.phone = phoneResult.errors[0];
    }

    const emailResult = validateField(state.email, {
      required: true,
      pattern: PATTERNS.EMAIL,
      maxLength: MAX_EMAIL,
    });
    if (!emailResult.isValid) {
      newErrors.email = emailResult.errors[0];
    }

    if (!state.message.trim()) {
      newErrors.message = "Message is required";
    } else if (state.message.length > MAX_MESSAGE) {
      newErrors.message = `Message must be at most ${MAX_MESSAGE} characters`;
    }

    return newErrors;
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    const isFirstNameOrLastName = name === "first_name" || name === "last_name";
    const displayValue = isFirstNameOrLastName ? titleCase(value) : value;
    const next = {
      ...form,
      [name]: displayValue,
    } as FormState;
    setForm(next);
    // Only update errors after the user has tried to submit; then live feedback as they fix fields
    if (hasAttemptedSubmit) {
      setErrors(validate(next));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setHasAttemptedSubmit(true);

    const validationErrors = validate(form);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setSubmitting(true);
    try {
      const fullPhone = form.phone.trim()
        ? combinePhoneNumber(dialCode, form.phone.trim())
        : "";
      await api.post<ContactUsResponse>("/v1/contact-us", {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: fullPhone,
        email: form.email.trim(),
        message: form.message.trim(),
      });

      toastManager.addToast(
        createSuccessToast("Message sent", "Your contact request has been submitted successfully.")
      );

      setForm(initialFormState);
      setErrors({});
      setHasAttemptedSubmit(false);
      setSelectedCountryCode("GB");
      setDialCode("+44");
    } catch (error) {
      // API layer already shows a toast for 400, 403, 409, 422 — show generic toast only for other errors
      const alreadyHandled =
        error instanceof ApiError && ERROR_TO_EXCLUDE.includes(error.status);
      if (!alreadyHandled) {
        toastManager.addToast(
          createErrorToast("Error", "Failed to submit your request. Please try again.")
        );
      }
      // eslint-disable-next-line no-console
      console.error("Contact us submission failed:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = (hasError: boolean) =>
    `w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 ${
      hasError ? "border-novaCaution-500" : "border-novaNeutral-300"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <LandingHeader hidenavs={false} />
      <main id="main-content" role="main" className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-6 text-center font-nineties tracking-wide">
            Contact Us
          </h1>
          <p className="text-center text-novaNeutral-600 max-w-2xl mx-auto mb-10">
          {/* Nova Navigators respond within one business day. Live support is available Monday–Friday, 9.00am–7.00pm (UK business days). */}
          Nova Navigators are Nova’s client support team, helping people use the platform and connect with the right experts at the right time. They respond within one business day.
          You can submit an enquiry at any time, and messages received outside these hours will be responded to the next business day.
          </p>

          <div className="bg-white border border-novaActive rounded-xl shadow-sm p-6 sm:p-8">
            <form
              onSubmit={handleSubmit}
              className="space-y-5"
              noValidate
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="contact-first_name" className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    First name <span className="text-novaCaution-500">*</span>
                  </label>
                  <input
                    id="contact-first_name"
                    type="text"
                    name="first_name"
                    value={form.first_name}
                    onChange={handleChange}
                    maxLength={MAX_FIRST_NAME + 1}
                    className={inputClass(!!errors.first_name)}
                    placeholder=""
                    autoComplete="given-name"
                  />
                  {errors.first_name && (
                    <p className="mt-1 text-xs text-novaCaution-500" role="alert">{errors.first_name}</p>
                  )}
                </div>
                <div>
                  <label htmlFor="contact-last_name" className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Last name <span className="text-novaCaution-500">*</span>
                  </label>
                  <input
                    id="contact-last_name"
                    type="text"
                    name="last_name"
                    value={form.last_name}
                    onChange={handleChange}
                    maxLength={MAX_LAST_NAME + 1}
                    className={inputClass(!!errors.last_name)}
                    placeholder=""
                    autoComplete="family-name"
                  />
                  {errors.last_name && (
                    <p className="mt-1 text-xs text-novaCaution-500" role="alert">{errors.last_name}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="contact-phone" className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Phone <span className="text-novaCaution-500">*</span>
                  </label>
                  <div className="grid grid-cols-[100px_1fr] gap-2">
                    <PhoneCountryCodeSelect
                      className="py-2"
                      value={selectedCountryCode}
                      onChange={(countryCode: string, phoneDialCode: string) => {
                        setSelectedCountryCode(countryCode);
                        setDialCode(phoneDialCode);
                      }}
                      disabled={submitting}
                    />
                    <input
                      id="contact-phone"
                      type="tel"
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      onInput={(e) => {
                        const value = e.currentTarget.value.replace(/[^0-9\s()\-]/g, "");
                        e.currentTarget.value = value;
                        handleChange(e as React.ChangeEvent<HTMLInputElement>);
                      }}
                      className={inputClass(!!errors.phone)}
                      placeholder="123 456 7890"
                      autoComplete="tel"
                    />
                  </div>
                  {errors.phone && (
                    <p className="mt-1 text-xs text-novaCaution-500" role="alert">{errors.phone}</p>
                  )}
                </div>
                <div>
                  <label htmlFor="contact-email" className="block text-xs font-medium text-novaNeutral-700 mb-1">
                    Email <span className="text-novaCaution-500">*</span>
                  </label>
                  <input
                    id="contact-email"
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    maxLength={MAX_EMAIL + 1}
                    className={inputClass(!!errors.email)}
                    placeholder="you@example.com"
                    autoComplete="email"
                  />
                  {errors.email && (
                    <p className="mt-1 text-xs text-novaCaution-500" role="alert">{errors.email}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="contact-message" className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Message <span className="text-novaCaution-500">*</span>
                </label>
                <textarea
                  id="contact-message"
                  name="message"
                  value={form.message}
                  onChange={handleChange}
                  rows={5}
                  maxLength={MAX_MESSAGE + 1}
                  className={`${inputClass(!!errors.message)} resize-y min-h-[120px]`}
                  placeholder="Tell us how we can help..."
                />
                <div className="mt-1 flex items-center justify-between text-[11px] text-novaNeutral-500">
                  <span>{errors.message && <span className="text-novaCaution-500">{errors.message}</span>}</span>
                  <span>
                    {form.message.length}/{MAX_MESSAGE} characters
                  </span>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-md bg-novaPrimary-600 text-white hover:bg-novaPrimary-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
                >
                  {submitting ? (
                    <>
                      <i className="fas fa-spinner fa-spin mr-2" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-paper-plane mr-2" />
                      Send message
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
};

export default ContactUsPage;

