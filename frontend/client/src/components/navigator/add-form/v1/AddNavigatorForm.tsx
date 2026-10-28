import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Navigator, NavigatorFormData } from "@/lib/types";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";
import { FormButton } from "@/utils/formComponents";

interface AddNavigatorFormProps {
  mode: "add" | "edit";
  navigatorData?: Navigator;
  onCancel: () => void;
  onSubmit: (data: NavigatorFormData, navigatorId?: string) => Promise<boolean>;
}

const AddNavigatorForm: React.FC<AddNavigatorFormProps> = ({
  mode,
  navigatorData,
  onCancel,
  onSubmit,
}) => {
  const initialFormState: NavigatorFormData = {
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    gender: "",
    gender_other: "",
    status: "Active",
    address_line_1: "",
    address_line_2: "",
    city: "",
    county: "",
    country: "",
    postal_code: "",
    about: "",
    linkedin_url: "",
    specialization: "",
    experience: 0,
  };

  const [formData, setFormData] = useState<NavigatorFormData>(initialFormState);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");

  // Pre-fill form data in edit mode
  useEffect(() => {
    if (mode === "edit" && navigatorData) {
      const statusValue =
        navigatorData.status?.toLowerCase() === "active"
          ? "Active"
          : navigatorData.status?.toLowerCase() === "inactive"
          ? "Inactive"
          : "Active";

      // Parse phone number to extract country code and phone number separately
      const { countryCode, dialCode: parsedDialCode, phoneNumber } = parsePhoneNumber(navigatorData.phone || "");

      setFormData({
        first_name: navigatorData.first_name || "",
        last_name: navigatorData.last_name || "",
        email: navigatorData.email || "",
        phone: phoneNumber,
        gender: navigatorData.gender || "",
        gender_other:
          navigatorData.gender === "Other"
            ? navigatorData.gender_other || ""
            : "",
        status: statusValue,
        address_line_1: "",
        address_line_2: "",
        city: "",
        county: "",
        country: "",
        postal_code: "",
        about: "",
        linkedin_url: navigatorData.linkedin_url || "",
        specialization: navigatorData.specialization || "",
        experience: navigatorData.experience || 0,
      });

      // Set country code and dial code from parsed phone number
      setSelectedCountryCode(countryCode);
      setDialCode(parsedDialCode);
    }
  }, [mode, navigatorData]);

  const [errors, setErrors] = useState<Partial<NavigatorFormData>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fieldLimits: Record<string, number> = {
    first_name: 100,
    last_name: 100,
    email: 255,
    phone: 17,
    gender_other: 50,
  };

  // Shared validation: used on change (with new data) and on submit
  const getValidationErrors = (data: NavigatorFormData): Partial<NavigatorFormData> => {
    const newErrors: Partial<NavigatorFormData> = {};

    if (!data.first_name.trim()) {
      newErrors.first_name = "First name is required";
    } else if (data.first_name.length > fieldLimits.first_name) {
      newErrors.first_name = `Character limit exceeded (max ${fieldLimits.first_name} characters)` as any;
    }

    if (!data.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    } else if (data.last_name.length > fieldLimits.last_name) {
      newErrors.last_name = `Character limit exceeded (max ${fieldLimits.last_name} characters)` as any;
    }

    if (!data.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
      newErrors.email = "Please enter a valid email address";
    } else if (data.email.length > fieldLimits.email) {
      newErrors.email = `Character limit exceeded (max ${fieldLimits.email} characters)`;
    }

    if (data.phone && data.phone.trim()) {
      const allowedCharsRegex = /^\+?[0-9\s()\-]+$/;
      if (!allowedCharsRegex.test(data.phone)) {
        newErrors.phone = "Invalid phone number";
      } else if (data.phone.length > fieldLimits.phone) {
        newErrors.phone = `Character limit exceeded (max ${fieldLimits.phone} characters)`;
      }
    }

    if (!data.status.trim()) {
      newErrors.status = "Status is required" as any;
    }

    if (data.gender_other && data.gender_other.length > fieldLimits.gender_other) {
      newErrors.gender_other = `Character limit exceeded (max ${fieldLimits.gender_other} characters)` as any;
    }

    return newErrors;
  };

  const isMandatoryFieldsFilled = () =>
    formData.first_name.trim() !== "" &&
    formData.last_name.trim() !== "" &&
    formData.email.trim() !== "" &&
    formData.status.trim() !== "";

  const hasValidationErrors = Object.values(errors).some((v) => v != null && v !== "");

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    const newData = { ...formData, [name]: value };
    if (name === "gender" && value !== "Other") newData.gender_other = "";
    setFormData(newData);
    setErrors(getValidationErrors(newData));
  };

  // Handler for country code selection
  const handleCountryCodeChange = (countryCode: string, phoneDialCode: string) => {
    setSelectedCountryCode(countryCode);
    setDialCode(phoneDialCode);
  };

  const validateForm = (): boolean => {
    const newErrors = getValidationErrors(formData);
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm() || hasValidationErrors) {
      return;
    }

    setIsSubmitting(true);
    try {
      // Prepare form data
      const phoneNumber = formData.phone?.trim() ? combinePhoneNumber(dialCode, formData.phone) : "";
      
      const submitData = {
        ...formData,
        phone: phoneNumber, // Always include phone, even if empty (to clear existing value)
        // If gender not selected, pass null (gender is optional)
        gender: formData.gender ? formData.gender : (null as any),
        // Only include gender_other if gender is "Other"
        gender_other:
          formData.gender === "Other" ? formData.gender_other : undefined,
      };

      const success = await onSubmit(submitData, navigatorData?.id);

      if (success && mode === "add") {
        setFormData(initialFormState);
        setErrors({});
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="">
      {/* Header */}
      <div className="py-4 mb-4 bg-white rounded-lg border border-novaActive p-8 text-center">
        <h2 className="text-xl font-semibold text-novaNeutral-900">
          {mode === "edit" ? "Edit Navigator" : "Add New Navigator"}
        </h2>
        <p className="mt-1 text-sm text-novaNeutral-500">
          {mode === "edit"
            ? "Update the navigator details below"
            : "Fill in the details below to add a new navigator"}
        </p>
      </div>
      <div className="bg-white rounded-lg p-8 border border-novaActive">
      {/* Form */}
      <form
          onSubmit={handleSubmit}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.target as HTMLElement).tagName !== "TEXTAREA") {
              e.preventDefault();
            }
          }}
          className="p-6"
        >
        <div className="space-y-4">
          {/* Basic Information */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                First Name <span className="text-novaAlert-600">*</span>
              </label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                maxLength={101}
                className="w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 transition-colors"
                placeholder="John"
              />
              <div className="flex items-center justify-between mt-1">
                {errors.first_name ? (
                  <p className="text-sm text-novaCaution-500">
                    {errors.first_name}
                  </p>
                ) : (
                  <span className="text-sm text-transparent">.</span>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                Last Name <span className="text-novaAlert-600">*</span>
              </label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                maxLength={101}
                className="w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 transition-colors"
                placeholder="Smith"
              />
              <div className="flex items-center justify-between mt-1">
                {errors.last_name ? (
                  <p className="text-sm text-novaCaution-500">
                    {errors.last_name}
                  </p>
                ) : (
                  <span className="text-sm text-transparent">.</span>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                Email <span className="text-novaAlert-600">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                maxLength={256}
                className="w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 transition-colors"
                placeholder="john.smith@example.com"
              />
              <div className="flex items-center justify-between mt-1">
                {errors.email ? (
                  <p className="text-sm text-novaCaution-500">{errors.email}</p>
                ) : (
                  <span className="text-sm text-transparent">.</span>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                Phone
              </label>
              <div className="grid grid-cols-[100px_1fr] gap-2">
                <PhoneCountryCodeSelect
                  className="py-2"
                  value={selectedCountryCode}
                  onChange={handleCountryCodeChange}
                  disabled={isSubmitting}
                />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onInput={(e) => {
                    // Allow only digits and spaces
                    const filtered = e.currentTarget.value.replace(/[^0-9\s]/g, "");
                    e.currentTarget.value = filtered;
                    handleInputChange(e as any);
                  }}
                  maxLength={18}
                  className="w-full px-3 py-1.5 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 transition-colors"
                  placeholder="123 456 7890"
                />
              </div>
              {errors.phone && (
                <p className="mt-1 text-sm text-novaCaution-500">
                  {errors.phone}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                Gender
              </label>
              <CustomSelect
                value={formData.gender}
                onChange={(value) =>
                  handleInputChange({
                    target: { name: "gender", value },
                  } as React.ChangeEvent<HTMLInputElement>)
                }
                options={[
                  { value: "Male", label: "Male" },
                  { value: "Female", label: "Female" },
                  { value: "Other", label: "Other" },
                ]}
                placeholder="Select gender"
                triggerClassName="rounded-md h-[36px]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                Status <span className="text-novaAlert-600">*</span>
              </label>
              <CustomSelect
                value={formData.status}
                onChange={(value) =>
                  handleInputChange({
                    target: { name: "status", value },
                  } as React.ChangeEvent<HTMLInputElement>)
                }
                options={[
                  { value: "Active", label: "Active" },
                  { value: "Inactive", label: "Inactive" },
                ]}
                placeholder="Select status"
                triggerClassName="rounded-md h-[36px]"
              />
              {errors.status && (
                <p className="mt-1 text-sm text-novaCaution-500">
                  {errors.status}
                </p>
              )}
            </div>
          </div>

          {formData.gender === "Other" && (
            <div>
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                Specify Gender
              </label>
              <input
                type="text"
                name="gender_other"
                value={formData.gender_other || ""}
                maxLength={51}
                onChange={handleInputChange}
                className={"w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 transition-colors border-novaNeutral-300 hover:border-novaNeutral-400"}
                placeholder="Please specify"
              />
              <div className="flex items-center justify-between mt-1">
                {errors.gender_other ? (
                  <p className="text-sm text-novaCaution-500">{errors.gender_other}</p>
                ) : (
                  <span className="text-sm text-transparent">.</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-6 mt-10 border-t border-novaActive">
          <FormButton
            type="button"
            variant="custom"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-6 py-2.5 text-sm font-medium border border-novaNeutral-900 text-novaNeutral-700 hover:bg-novaBlack hover:text-white"
          >
            Cancel
          </FormButton>
          <FormButton
            type="submit"
            variant="gradient"
            disabled={isSubmitting || !isMandatoryFieldsFilled() || hasValidationErrors}
            className="px-6 py-2.5 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                {mode === "edit" ? "Saving..." : "Creating..."}
              </>
            ) : (
              <>
                <i className="fas fa-plus mr-2"></i>
                {mode === "edit" ? "Save Changes" : "Create Navigator"}
              </>
            )}
          </FormButton>
        </div>
      </form>
      </div>
    </div>
  );
};

export default AddNavigatorForm;
