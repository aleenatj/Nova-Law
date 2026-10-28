import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { LawFirm, LawFirmFormData } from "@/lib/types";
import { FormButton, FormInput, createFieldProps } from "@/utils/formComponents";
import CountrySelect from "@/components/ui/country-select/CountrySelect";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { api } from "@/lib/api";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";

interface AddFirmFormProps {
  mode: "add" | "edit";
  firmData?: LawFirm;
  onCancel: () => void;
  onSubmit: (data: LawFirmFormData, firmId?: string) => Promise<boolean>;
}

const AddFirmForm: React.FC<AddFirmFormProps> = ({
  mode,
  firmData,
  onCancel,
  onSubmit,
}) => {
  const initialFormState: LawFirmFormData = {
    name: "",
    contact_person: "",
    contact_no: "",
    contact_email: "",
    address_line_1: "",
    address_line_2: "",
    city: "",
    state: "",
    postal_code: "",
    country: "",
    logo: "",
    about: "",
    website_url: "",
    engage_form_url: "",
    law_firm_type: "",
    status: "Active",
  };

  const [formData, setFormData] = useState<LawFirmFormData>(initialFormState);
  const [errors, setErrors] = useState<Partial<LawFirmFormData>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Image upload states
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [uploadTokenResponse, setUploadTokenResponse] = useState<any>(null);
  const [showUploadOption, setShowUploadOption] = useState(false);
  const [hasNewLogoUpload, setHasNewLogoUpload] = useState(false);
  const [logoRemoved, setLogoRemoved] = useState(false);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");

  // Pre-fill form data in edit mode
  useEffect(() => {
    if (mode === "edit" && firmData) {
      // Parse phone number to extract country code and phone number separately
      const { countryCode, dialCode: parsedDialCode, phoneNumber } = parsePhoneNumber(firmData.contact_no || "");
      
      setFormData({
        name: firmData.name || "",
        contact_person: firmData.contact_person || "",
        contact_no: phoneNumber,
        contact_email: firmData.contact_email || "",
        address_line_1: firmData.address_line_1 || "",
        address_line_2: firmData.address_line_2 || "",
        city: firmData.city || "",
        state: firmData.state || "",
        postal_code: firmData.postal_code || "",
        country: firmData.country || "",
        logo: firmData.logos?.thumbnail || firmData.logo || "",
        about: firmData.about || "",
        website_url: firmData.website_url || "",
        engage_form_url: firmData.engage_form_url || "",
        law_firm_type: firmData.law_firm_type || "",
        status: firmData.status || "Active" as "Active" | "Inactive",
      });

      // Set country code and dial code from parsed phone number
      setSelectedCountryCode(countryCode);
      setDialCode(parsedDialCode);
      
      // Clear any selected image file when switching to edit mode
      setSelectedImageFile(null);
      setImagePreview(null);
      setIsUploadingImage(false);
      setUploadTokenResponse(null);
      setShowUploadOption(false); // Don't show upload option by default in edit mode
      setHasNewLogoUpload(false); // Reset new logo upload flag in edit mode
      setLogoRemoved(false); // Reset logo removed flag in edit mode
    } else if (mode === "add") {
      // Clear image file when switching to add mode
      setSelectedImageFile(null);
      setImagePreview(null);
      setIsUploadingImage(false);
      setUploadTokenResponse(null);
      setShowUploadOption(true); // Show upload option by default in add mode
      setHasNewLogoUpload(false); // Reset new logo upload flag in add mode
      setLogoRemoved(false); // Reset logo removed flag in add mode
    }
  }, [mode, firmData]);

  const fieldLimits: Record<string, number> = {
    name: 100,
    contact_person: 100,
    contact_email: 255,
    contact_no: 17,
    address_line_1: 255,
    address_line_2: 255,
    city: 100,
    state: 100,
    postal_code: 20,
    about: 1500,
    website_url: 255,
    engage_form_url: 255,
  };

  const limitError = (max: number) => `Character limit exceeded (max ${max} characters)`;

  // Shared validation: used on change (with new data) and on submit
  const getValidationErrors = (data: LawFirmFormData): Partial<LawFirmFormData> => {
    const newErrors: Partial<LawFirmFormData> = {};

    if (!data.name.trim()) {
      newErrors.name = "Organisation name is required";
    } else if (data.name.length > fieldLimits.name) {
      newErrors.name = limitError(fieldLimits.name);
    }

    if (!data.contact_person.trim()) {
      newErrors.contact_person = "Contact person is required";
    } else if (data.contact_person.length > fieldLimits.contact_person) {
      newErrors.contact_person = limitError(fieldLimits.contact_person);
    }

    if (!data.contact_email.trim()) {
      newErrors.contact_email = "Contact email is required";
    } else if (data.contact_email.length > fieldLimits.contact_email) {
      newErrors.contact_email = limitError(fieldLimits.contact_email);
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.contact_email)) {
      newErrors.contact_email = "Please enter a valid email address";
    }

    if (!data.law_firm_type.trim()) {
      newErrors.law_firm_type = "Organisation type is required";
    }

    if (data.contact_no && data.contact_no.trim()) {
      const allowedCharsRegex = /^\+?[0-9\s()\-]+$/;
      if (!allowedCharsRegex.test(data.contact_no)) {
        newErrors.contact_no = "Invalid contact number";
      } else if (data.contact_no.length > fieldLimits.contact_no) {
        newErrors.contact_no = limitError(fieldLimits.contact_no);
      }
    }

    if (data.address_line_1 && data.address_line_1.length > fieldLimits.address_line_1) {
      newErrors.address_line_1 = limitError(fieldLimits.address_line_1);
    }
    if (data.address_line_2 && data.address_line_2.length > fieldLimits.address_line_2) {
      newErrors.address_line_2 = limitError(fieldLimits.address_line_2);
    }
    if (data.city && data.city.length > fieldLimits.city) {
      newErrors.city = limitError(fieldLimits.city);
    }
    if (data.state && data.state.length > fieldLimits.state) {
      newErrors.state = limitError(fieldLimits.state);
    }
    if (data.postal_code && data.postal_code.trim()) {
      const postalCodeRegex = /^[A-Z0-9\s\-]{3,20}$/i;
      if (data.postal_code.length > fieldLimits.postal_code) {
        newErrors.postal_code = limitError(fieldLimits.postal_code);
      } else if (!postalCodeRegex.test(data.postal_code)) {
        newErrors.postal_code = "Please enter a valid postal code";
      }
    }
    if (data.about && data.about.length > fieldLimits.about) {
      newErrors.about = limitError(fieldLimits.about);
    }

    if (data.website_url && data.website_url.trim()) {
      try {
        new URL(data.website_url);
      } catch {
        newErrors.website_url = "Please enter a valid URL (e.g., https://example.com)";
      }
    }

    if (data.logo && data.logo.trim() && data.logo.startsWith("http")) {
      try {
        new URL(data.logo);
      } catch {
        newErrors.logo = "Please enter a valid URL (e.g., https://example.com/logo.png)";
      }
    }

    if (data.website_url && data.website_url.length > fieldLimits.website_url) {
      newErrors.website_url = limitError(fieldLimits.website_url);
    }
    if (data.engage_form_url && data.engage_form_url.length > fieldLimits.engage_form_url) {
      newErrors.engage_form_url = limitError(fieldLimits.engage_form_url);
    }

    return newErrors;
  };

  const isMandatoryFieldsFilled = () =>
    formData.name.trim() !== "" &&
    formData.law_firm_type.trim() !== "" &&
    formData.contact_person.trim() !== "" &&
    formData.contact_email.trim() !== "";

  const hasValidationErrors = Object.values(errors).some((v) => v != null && v !== "");

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    const newData = { ...formData, [name]: value };
    setFormData(newData);
    setErrors(getValidationErrors(newData));
  };

  // Handler for country code selection
  const handleCountryCodeChange = (countryCode: string, phoneDialCode: string) => {
    setSelectedCountryCode(countryCode);
    setDialCode(phoneDialCode);
  };

  // Handler for logo image file upload
  const handleImageFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
      ];
      if (!allowedTypes.includes(file.type)) {
        setErrors((prev) => ({
          ...prev,
          logo: "Please select a valid image file (JPEG, PNG, GIF, or WebP)",
        }));
        return;
      }

      // Validate file size (max 5MB)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        setErrors((prev) => ({
          ...prev,
          logo: "Image file size must be less than 5MB",
        }));
        return;
      }

      setSelectedImageFile(file);
      setErrors((prev) => ({ ...prev, logo: undefined }));
      setIsUploadingImage(true);
      setUploadTokenResponse(null);

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      // Get file extension
      const fileExtension = file.name.split(".").pop()?.toLowerCase() || "";

      try {
        // Call the upload token API
        const params = new URLSearchParams({
          extension: fileExtension,
          entity_type: "law_firm_logo",
        });

        const response = (await api.get(
          `/v1/upload/get-file-upload-token?${params}`
        )) as any;

        setUploadTokenResponse(response);

        // If we have a valid upload_url, do the PUT to S3
        if (
          response &&
          response.data &&
          response.data.upload_url &&
          response.data.file_key
        ) {
          // Do the PUT request to S3
          const uploadUrl = response.data.upload_url;
          const putResult = await fetch(uploadUrl, {
            method: "PUT",
            headers: {
              "Content-Type": file.type,
            },
            body: file,
          });

          if (!putResult.ok) {
            throw new Error("Failed to upload image to storage.");
          }

          // Store the file_key in logo for form submission
          setFormData((prev) => ({
            ...prev,
            logo: response.data.file_key,
          }));
          setHasNewLogoUpload(true); // Mark that a new logo has been uploaded
          setLogoRemoved(false); // Reset logo removed flag since a new one is uploaded
        } else {
          throw new Error("Invalid upload token response.");
        }
      } catch (error) {
        console.error("Failed to upload image:", error);
        setErrors((prev) => ({
          ...prev,
          logo: "Failed to upload image. Please try again.",
        }));
      } finally {
        setIsUploadingImage(false);
      }
    }
  };

  // Handler for removing selected image
  const handleRemoveImage = () => {
    setSelectedImageFile(null);
    setImagePreview(null);
    setFormData((prev) => ({
      ...prev,
      logo: "",
    }));
    setErrors((prev) => ({ ...prev, logo: undefined }));
    setIsUploadingImage(false);
    setUploadTokenResponse(null);
    setShowUploadOption(true); // Show upload option after removing image
    setHasNewLogoUpload(false); // Reset new logo upload flag
    setLogoRemoved(true); // Mark logo as explicitly removed
  };

  // Handler for replacing logo (show upload option)
  const handleReplaceLogo = () => {
    setShowUploadOption(true);
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
      const contactNumber = formData.contact_no?.trim() ? combinePhoneNumber(dialCode, formData.contact_no) : '';
      
      let submitData: any = { 
        ...formData,
        contact_no: contactNumber,
        // Handle engage_form_url: pass null if empty, otherwise the current value
        engage_form_url: formData.engage_form_url?.trim() ? formData.engage_form_url.trim() : null,
      };

      // Handle logo submission logic
      if (logoRemoved) {
        // Logo was explicitly removed - pass null
        (submitData as any).logo = null;
      } else if (hasNewLogoUpload) {
        // New logo uploaded - keep the file key already in formData.logo
        // No change needed, submitData.logo already has the file key
      } else if (mode === "edit" && firmData) {
        // No changes to logo - pass the current logo URL
        submitData.logo = firmData.logos?.thumbnail || firmData.logo || "";
      } else if (mode === "add") {
        // In add mode with no logo uploaded
        submitData.logo = "";
      }

      const success = await onSubmit(submitData, firmData?.id);

      if (success && mode === "add") {
        setFormData(initialFormState);
        setErrors({});
        setSelectedImageFile(null);
        setImagePreview(null);
        setIsUploadingImage(false);
        setUploadTokenResponse(null);
        setShowUploadOption(true);
        setHasNewLogoUpload(false);
        setLogoRemoved(false);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClass = (error?: string) =>
    `w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 ${
      error ? "border-novaCaution-500" : "border-novaNeutral-300"
    }`;

  return (
    <div className="">
      <div className="py-4 mb-4 bg-white rounded-lg border border-novaActive p-8 text-center">
        <h2 className="text-xl font-semibold text-novaNeutral-900">
          {mode === "edit" ? "Edit Organisation" : "Add New Organisation"}
        </h2>
        <p className="mt-1 text-sm text-novaNeutral-500">
          {mode === "edit"
            ? "Update the organisation details below"
            : "Fill in the details below to add a new organisation"}
        </p>
      </div>

      <div className="bg-white rounded-lg border border-novaActive p-8">
        <form
          onSubmit={handleSubmit}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.target as HTMLElement).tagName !== "TEXTAREA") {
              e.preventDefault();
            }
          }}
          className="space-y-6"
        >
          {/* Section 1: Personal Info */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">
              Personal Info
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Organisation Name <span className="text-novaCaution-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  maxLength={101}
                  className={inputClass(errors.name)}
                  placeholder="Example Organisation"
                />
                {errors.name && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.name}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Organisation Type <span className="text-novaCaution-500">*</span>
                </label>
                <CustomSelect
                  value={formData.law_firm_type}
                  onChange={(value) =>
                    handleInputChange({
                      target: { name: "law_firm_type", value },
                    } as React.ChangeEvent<HTMLInputElement>)
                  }
                  options={[
                    { value: "Solo practitioner", label: "Solo practitioner" },
                    { value: "Boutique", label: "Boutique" },
                    { value: "Multi-speciality", label: "Multi-speciality" },
                  ]}
                  triggerClassName="rounded-md h-[36px]"
                />
                {errors.law_firm_type && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.law_firm_type}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Contact Person <span className="text-novaCaution-500">*</span>
                </label>
                <input
                  type="text"
                  name="contact_person"
                  value={formData.contact_person}
                  onChange={handleInputChange}
                  maxLength={101}
                  className={inputClass(errors.contact_person)}
                  placeholder="John Smith"
                />
                {errors.contact_person && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.contact_person}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Contact Email <span className="text-novaCaution-500">*</span>
                </label>
                <input
                  type="email"
                  name="contact_email"
                  value={formData.contact_email}
                  onChange={handleInputChange}
                  maxLength={256}
                  className={inputClass(errors.contact_email)}
                  placeholder="contact@example.com"
                />
                {errors.contact_email && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.contact_email}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Contact Number
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
                    name="contact_no"
                    value={formData.contact_no}
                    onInput={(e) => {
                      const value = e.currentTarget.value.replace(/[^0-9\s]/g, "");
                      e.currentTarget.value = value;
                      handleInputChange(e as any);
                    }}
                    maxLength={18}
                    className={inputClass(errors.contact_no)}
                    placeholder="123 456 7890"
                  />
                </div>
                {errors.contact_no && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.contact_no}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Status
                </label>
                <CustomSelect
                  value={formData.status || "Active"}
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
                  error={!!errors.status}
                  triggerClassName="rounded-md h-[36px]"
                />
                {errors.status && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.status}</p>
                )}
              </div>
            </div>
          </div>

          {/* Section 2: Address & details */}
          <div className="border-b border-novaActive pb-6">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">
              Address & details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Address Line 1
                </label>
                <input
                  type="text"
                  name="address_line_1"
                  value={formData.address_line_1}
                  onChange={handleInputChange}
                  maxLength={256}
                  className={inputClass(errors.address_line_1)}
                  placeholder="123 Main Street"
                />
                {errors.address_line_1 && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.address_line_1}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Address Line 2
                </label>
                <input
                  type="text"
                  name="address_line_2"
                  value={formData.address_line_2}
                  onChange={handleInputChange}
                  maxLength={256}
                  className={inputClass(errors.address_line_2)}
                  placeholder="Suite 100"
                />
                {errors.address_line_2 && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.address_line_2}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  City
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  maxLength={101}
                  className={inputClass(errors.city)}
                  placeholder="New York"
                />
                {errors.city && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.city}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  County
                </label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  maxLength={101}
                  onChange={handleInputChange}
                  className={inputClass(errors.state)}
                  placeholder="NY"
                />
                {errors.state && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.state}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Postal Code
                </label>
                <input
                  type="text"
                  name="postal_code"
                  value={formData.postal_code}
                  onChange={handleInputChange}
                  maxLength={21}
                  className={inputClass(errors.postal_code)}
                  placeholder="10001"
                />
                {errors.postal_code && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.postal_code}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Country
                </label>
                <CountrySelect
                  value={formData.country}
                  onChange={(value) =>
                    handleInputChange({
                      target: { name: "country", value },
                    } as React.ChangeEvent<HTMLInputElement>)
                  }
                  error={errors.country}
                />
                {errors.country && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.country}</p>
                )}
              </div>
            </div>
          </div>

          <div className="">
            <h3 className="text-md font-semibold text-novaNeutral-700 mb-4">
              Additional Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Website URL
                </label>
                <input
                  type="url"
                  name="website_url"
                  value={formData.website_url}
                  onChange={handleInputChange}
                  className={inputClass(errors.website_url)}
                  maxLength={256}
                  placeholder="https://example.com"
                />
                {errors.website_url && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.website_url}</p>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                  Client ID
                </label>
                <input
                  type="text"
                  name="engage_form_url"
                  value={formData.engage_form_url}
                  onChange={handleInputChange}
                  className={inputClass(errors.engage_form_url)}
                  maxLength={256}
                  placeholder="https://example.com/engage"
                />
                {errors.engage_form_url && (
                  <p className="mt-1 text-xs text-novaCaution-500">{errors.engage_form_url}</p>
                )}
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
                About the Organisation
              </label>
              <textarea
                name="about"
                value={formData.about}
                onChange={handleInputChange}
                rows={4}
                maxLength={1501}
                className={inputClass(errors.about)}
                placeholder="Brief description of the organisation's specialties..."
              />
              {errors.about && (
                <p className="mt-1 text-xs text-novaCaution-500">{errors.about}</p>
              )}
            </div>

          {/* Logo Upload */}
          <div className="mt-4">
            <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
              Logo
            </label>

          {/* Show existing logo in edit mode OR uploaded logo */}
          {(formData.logo && !showUploadOption) ||
          (imagePreview && showUploadOption) ? (
            <div className="mb-3">
              <div className="relative inline-block">
                <img
                  src={imagePreview || formData.logo || ""}
                  alt="Logo preview"
                  className="w-20 h-20 object-contain border-2 border-novaNeutral-200 rounded-md bg-white p-1"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="absolute -top-2 -right-2 bg-novaCaution-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-novaCaution-600 transition-colors"
                  title="Remove image"
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
              {mode === "edit" &&
                formData.logo &&
                !showUploadOption && (
                  <div className="mt-2">
                    <button
                      type="button"
                      onClick={handleReplaceLogo}
                      className="text-xs text-novaPrimary-600 hover:text-novaPrimary-700 font-medium"
                    >
                      <i className="fas fa-edit mr-1"></i>
                      Replace Logo
                    </button>
                  </div>
                )}
            </div>
          ) : (
            /* Show upload option when no logo exists or when replacing */
            <div className="mb-3">
              <input
                type="file"
                id="logo-upload"
                accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                onChange={handleImageFileChange}
                className="hidden"
                disabled={isUploadingImage}
              />
              <label
                htmlFor="logo-upload"
                className={`inline-flex items-center px-3 py-2 border rounded-md text-sm font-medium transition-colors ${
                  isUploadingImage
                    ? "border-novaNeutral-300 text-novaNeutral-400 bg-novaNeutral-100 cursor-not-allowed"
                    : "border-novaNeutral-300 text-novaNeutral-700 bg-white hover:bg-novaNeutral-50 cursor-pointer"
                }`}
              >
                {isUploadingImage ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2 text-novaPrimary-500"></i>
                    Uploading...
                  </>
                ) : uploadTokenResponse ? (
                  <>
                    <i className="fas fa-check mr-2 text-novaSuccess-500"></i>
                    Upload ready
                  </>
                ) : (
                  <>
                    <i className="fas fa-upload mr-2 text-novaPrimary-500"></i>
                    Upload Logo
                  </>
                )}
              </label>
              <p className="text-xs text-novaNeutral-500 mt-1">
                JPEG, PNG, GIF, WebP (max 5MB)
              </p>
              {isUploadingImage && (
                <p className="text-xs text-novaPrimary-600 mt-1">
                  <i className="fas fa-info-circle mr-1"></i>
                  Uploading logo...
                </p>
              )}
              {uploadTokenResponse && (
                <p className="text-xs text-novaSuccess-600 mt-1">
                  <i className="fas fa-check-circle mr-1"></i>
                  Logo uploaded successfully
                </p>
              )}
            </div>
          )}
          {errors.logo && (
            <p className="mt-1 text-xs text-novaCaution-500">{errors.logo}</p>
          )}
        </div>
        </div>

        {/* Form Actions - Compact */}
        <div className="flex justify-end space-x-2 pt-8 mt-10 border-t border-novaActive">
          <FormButton
            variant="custom"
            type="button"
            onClick={onCancel}
            disabled={isSubmitting || isUploadingImage}
            className="px-4 py-2 text-sm border border-novaNeutral-500 bg-white hover:bg-novaBlack text-novaNeutral-700 hover:text-white"
          >
            Cancel
          </FormButton>
          <FormButton 
            variant="gradient"
            type="submit"
            disabled={isSubmitting || isUploadingImage || !isMandatoryFieldsFilled() || hasValidationErrors}
            className="px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploadingImage ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                Uploading logo...
              </>
            ) : isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                {mode === "edit" ? "Saving..." : "Creating..."}
              </>
            ) : (
              <>
                <i
                  className={`fas ${
                    mode === "edit" ? "fa-save" : "fa-plus"
                  } mr-2`}
                ></i>
                {mode === "edit" ? "Save Changes" : "Create Organisation"}
              </>
            )}
          </FormButton>
        </div>
      </form>
      </div>
    </div>
  );
};

export default AddFirmForm;
