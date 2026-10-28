import React, { useState, useEffect, useRef } from "react";
import { Layout } from "@/components/layout/v1/Layout";
import { api } from "@/lib/api";
import { UserData, UserResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  useFormValidation,
  PATTERNS,
  FormValidationSchema,
  ERROR_MESSAGES,
} from "@/utils/formValidator";
import {
  FormButton,
  FormInput,
  createFieldProps,
} from "@/utils/formComponents";
import { toastManager, createSuccessToast, createErrorToast } from "@/utils/toasts";
import { navigate } from "wouter/use-browser-location";
import { useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import PhoneCountryCodeSelect from "@/components/ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";

export default function ProfilePage() {
  const [, setLocation] = useLocation();
  const { refreshUserFromStorage, logout: authLogout } = useAuth();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLoggedOut, setIsLoggedOut] = useState(false);
  const [editing, setEditing] = useState({
    firstName: false,
    lastName: false,
    email: false,
    phone: false,
  });
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");
  const [isPasswordSubmitting, setIsPasswordSubmitting] = useState(false);
  const isInitialLoad = useRef(true);
  const initialFormData = useRef<{ first_name: string; last_name: string; phone: string } | null>(null);

  // Handle back navigation - go to previous page or default to case-dashboard
  const handleBackClick = () => {
    // Check if there's a previous page in history
    if (window.history.length > 1) {
      window.history.back();
    } else {
      // Fallback to case-dashboard if no history
      setLocation("/case-dashboard");
    }
  };

  // Define validation schema for password fields
  const passwordValidationSchema: FormValidationSchema = React.useMemo(() => ({
    current_password: {
      required: true,
    },
    new_password: {
      required: true,
      pattern: PATTERNS.PASSWORD,
    },
    confirm_new_password: {
      required: true,
    },
  }), []);

  // Cross-field validation for password confirmation
  const crossFieldValidators = React.useMemo(() => ({
    confirm_new_password: (data: any) => {
      if (
        data.new_password &&
        data.confirm_new_password &&
        data.new_password !== data.confirm_new_password
      ) {
        return ERROR_MESSAGES.PASSWORDS_MATCH;
      }
      return null;
    },
  }), []);

  // Use form validation hook for password fields with cross-field validation
  const {
    formData: passwordFormData,
    errors: passwordErrors,
    touched: passwordTouched,
    isValid: isPasswordValid,
    handleChange: handlePasswordFieldChange,
    handleBlur: handlePasswordFieldBlur,
    setFormData: setPasswordFormData,       // Get the setFormData function from hook!
    setErrors: setPasswordErrors,           // And setErrors too, for clearing errors
    setTouched: setPasswordTouched          // And setTouched so "touched" is cleared after reset
  } = useFormValidation(passwordValidationSchema, crossFieldValidators);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await api.get<UserResponse>("/v1/user/me");
        setUserData(response.data);
        const fullPhone = String(response.data.phone || "");
        
        // Parse phone number to extract country code and phone number separately
        const { countryCode, dialCode: parsedDialCode, phoneNumber } = parsePhoneNumber(fullPhone);
        setSelectedCountryCode(countryCode);
        setDialCode(parsedDialCode);
        
        const initialData = {
          first_name: String(response.data.first_name || ""),
          last_name: String(response.data.last_name || ""),
          email: String(response.data.email || ""),
          phone: phoneNumber,
        };
        initialFormData.current = {
          first_name: initialData.first_name,
          last_name: initialData.last_name,
          phone: fullPhone, // Store full phone number for comparison
        };
        setFormData(initialData);
        isInitialLoad.current = false;
      } catch (error: any) {
        console.error("Error fetching user profile:", error);
        // Check if it's an authentication error (401 or 403)
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          setIsLoggedOut(true);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  // Handle profile update on field blur
  const handleProfileUpdate = async () => {
    if (isInitialLoad.current || !initialFormData.current) return;

    // Combine dial code with phone number for comparison and submission
    const fullPhoneNumber = combinePhoneNumber(dialCode, formData.phone);

    // Check if values have actually changed from initial values
    const hasChanged = 
      formData.first_name !== initialFormData.current.first_name ||
      formData.last_name !== initialFormData.current.last_name ||
      fullPhoneNumber !== initialFormData.current.phone;

    if (!hasChanged) return;

    try {
      const response: any = await api.put("/v1/user/profile", {
        first_name: String(formData.first_name || ""),
        last_name: String(formData.last_name || ""),
        phone: fullPhoneNumber,
      });

      if (response.success) {
        // Extract message from response
        let successMessage = "Your profile has been successfully updated.";
        if (Array.isArray(response.message) && response.message.length && response.message[0]?.message) {
          successMessage = response.message[0].message;
        } else if (typeof response.message === 'object' && response.message?.message) {
          successMessage = response.message.message;
        } else if (typeof response.message === 'string') {
          successMessage = response.message;
        }
        
        toastManager.addToast(
          createSuccessToast(
            "Profile Updated",
            successMessage
          )
        );
        
        // Update localStorage
        try {
          const userStr = localStorage.getItem("user");
          if (userStr) {
            const user = JSON.parse(userStr);
            user.first_name = formData.first_name;
            user.last_name = formData.last_name;
            user.phone = fullPhoneNumber || null;
            localStorage.setItem("user", JSON.stringify(user));
            // Refresh AuthContext to reflect changes in ProfileDropdown
            refreshUserFromStorage();
          }
        } catch (e) {
          console.error("Error updating localStorage:", e);
        }
        
        // Update initial values after successful save
        initialFormData.current = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          phone: fullPhoneNumber,
        };
      }
    } catch (error: any) {
      console.error("Error updating profile:", error);
    }
  };

  // Helper to reset password fields and their meta state
  const resetPasswordForm = () => {
    setPasswordFormData({
      current_password: "",
      new_password: "",
      confirm_new_password: "",
    });
    setPasswordErrors({});
    setPasswordTouched({});
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isPasswordValid) {
      toastManager.addToast(
        createErrorToast(
          "Validation Error",
          "Please fill in all required fields correctly."
        )
      );
      return;
    }

    setIsPasswordSubmitting(true);
    
    try {
      const response: any = await api.put("/v1/user/change-password", {
        current_password: passwordFormData.current_password,
        new_password: passwordFormData.new_password,
      });

      if (response.success) {
        // Correctly extract message if array/object/string
        let successMessage = "Your password has been successfully changed.";
        if (Array.isArray(response.message) && response.message.length && response.message[0]?.message) {
          successMessage = response.message[0].message;
        } else if (typeof response.message === 'object' && response.message?.message) {
          successMessage = response.message.message;
        } else if (typeof response.message === 'string') {
          successMessage = response.message;
        }
        toastManager.addToast(
          createSuccessToast(
            "Password Updated",
            successMessage
          )
        );
        // Reset password form (fields + touched/errors) on success
        resetPasswordForm();
      } else {
        const errorMessage = typeof response.message === 'string' 
          ? response.message 
          : "Failed to change password. Please try again.";
        
        toastManager.addToast(
          createErrorToast(
            "Password Change Failed",
            errorMessage
          )
        );
      }
    } catch (error: any) {
      let errorMessage = "Failed to change password. Please try again.";
      
      // Extract error message from API response if available
      if (error?.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      
      // toastManager.addToast(
      //   createErrorToast(
      //     "Password Change Failed",
      //     errorMessage
      //   )
      // );
      
    } finally {
      setIsPasswordSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout
        headerTitle="Account"
        headerSubtitle="Real-time information and activities of your property"
      >
        <div className="bg-gradient-to-br from-novaNeutral-50 to-novaNeutral-100 h-full flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-novaPrimary-200 border-t-novaPrimary-600 rounded-full animate-spin"></div>
            <p className="text-novaNeutral-600 font-medium">Loading your profile...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (isLoggedOut || !userData) {
    return (
      <Layout
        headerTitle="Account"
        headerSubtitle="Real-time information and activities of your property"
      >
        <div className="bg-gradient-to-br from-novaNeutral-50 to-novaNeutral-100 h-full"></div>
      </Layout>
    );
  }

  return (
    <Layout
      headerTitle="Account"
      headerSubtitle="Real-time information and activities of your property"
      showBackButton={true}
      backButtonLabel="Back"
      onBackClick={handleBackClick}
    >
      <div className="bg-gradient-to-br from-novaNeutral-50 to-novaNeutral-100 h-full flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-10">
            <div className="space-y-5 sm:space-y-6 md:grid md:grid-cols-2 md:gap-6 md:space-y-0">
              
              {/* Profile Picture Section */}
              {userData.photo_urls && userData.photo_urls.large && <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 p-6 sm:p-8 md:col-span-2 border border-novaNeutral-100">
                <div className="flex flex-col items-center gap-4">
                  <div className="relative flex-shrink-0 group">
                    <div className="absolute inset-0 bg-gradient-to-br from-novaPrimary-400 to-novaPrimary-600 rounded-full blur-sm opacity-30 group-hover:opacity-50 transition-opacity duration-300"></div>
                    {userData.photo_urls && userData.photo_urls.large ? (
                      <img
                        src={userData.photo_urls.large}
                        alt="Profile"
                        className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-full object-cover border-4 border-white shadow-lg ring-2 ring-novaPrimary-300"
                      />
                    ) : (
                      <div className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-gradient-to-br from-novaPrimary-200 to-novaPrimary-300 flex items-center justify-center text-2xl sm:text-3xl font-bold text-novaPrimary-700 border-4 border-white shadow-lg ring-2 ring-novaPrimary-300">
                        {userData.first_name.charAt(0)}
                        {userData.last_name.charAt(0)}
                      </div>
                    )}
                  </div>
                  <div className="text-center">
                    <h2 className="text-xl sm:text-2xl font-bold text-novaNeutral-900 tracking-tight">
                      {userData.first_name} {userData.last_name}
                    </h2>
                    <p className="text-sm text-novaNeutral-500 mt-1">{userData.email}</p>
                  </div>
                </div>
              </div>}

              {/* Full Name Section */}
              <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 p-5 sm:p-6 border border-novaNeutral-100 md:col-span-2">
                <div className="flex items-center gap-2 mb-5">
                  <div className="w-1 h-6 bg-gradient-to-b from-novaPrimary-500 to-novaPrimary-600 rounded-full"></div>
                  <h3 className="text-lg sm:text-xl font-bold text-novaNeutral-900">Full name</h3>
                </div>
                <form className="grid grid-cols-1 sm:grid-cols-2 gap-5" onSubmit={(e) => e.preventDefault()}>
                  <div>
                    <label className="block text-sm font-semibold text-novaNeutral-700 mb-2">
                      First name
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        name="first_name"
                        maxLength={80}
                        value={formData.first_name || ""}
                        onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                        onBlur={handleProfileUpdate}
                        autoComplete="given-name"
                        className="w-full px-4 py-2.5 text-sm border border-novaNeutral-200 rounded-lg focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 focus:bg-white transition-all duration-200"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-novaNeutral-700 mb-2">
                      Last name
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        name="last_name"
                        maxLength={80}
                        value={formData.last_name || ""}
                        onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                        onBlur={handleProfileUpdate}
                        autoComplete="family-name"
                        className="w-full px-4 py-2.5 text-sm border border-novaNeutral-200 rounded-lg focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 focus:bg-white transition-all duration-200"
                      />
                    </div>
                  </div>
                </form>
              </div>

              {/* Contact Email Section */}
              <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 p-5 sm:p-6 border border-novaNeutral-100">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-1 h-6 bg-gradient-to-b from-novaPrimary-500 to-novaPrimary-600 rounded-full"></div>
                  <h3 className="text-lg sm:text-xl font-bold text-novaNeutral-900">Email</h3>
                </div>
                <div className="relative group">
                  <i className="fas fa-envelope absolute left-4 top-[25%] text-novaNeutral-400 group-hover:text-novaPrimary-500 transition-colors duration-200"></i>
                  <textarea
                    value={formData.email || ""}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    rows={1}
                    ref={el => {
                      if (el) {
                        el.style.height = "auto";
                        el.style.height = el.scrollHeight + "px";
                      }
                    }}
                    style={{
                      overflow: "hidden",
                      resize: "none",
                      minHeight: "2.5rem",
                    }}
                    className="w-full pl-11 pr-4 py-2 text-sm bg-novaNeutral-50 border border-novaNeutral-200 rounded-lg focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 focus:bg-white transition-all duration-200 disabled:bg-novaNeutral-50 disabled:text-novaNeutral-600 disabled:cursor-not-allowed"
                    disabled={true}
                    onInput={e => {
                      const target = e.target as HTMLTextAreaElement;
                      target.style.height = 'auto';
                      target.style.height = target.scrollHeight + 'px';
                    }}
                  />
                </div>
              </div>

              {/* Phone Section */}
              <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 p-5 sm:p-6 border border-novaNeutral-100">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-1 h-6 bg-gradient-to-b from-novaPrimary-500 to-novaPrimary-600 rounded-full"></div>
                  <h3 className="text-lg sm:text-xl font-bold text-novaNeutral-900">Phone number</h3>
                </div>
                <form className="grid grid-cols-[95px_1fr] gap-2" onSubmit={(e) => e.preventDefault()}>
                  {/* Country Code Selector */}
                  <PhoneCountryCodeSelect
                    value={selectedCountryCode}
                    onChange={(countryCode, phoneDialCode) => {
                      setSelectedCountryCode(countryCode);
                      setDialCode(phoneDialCode);
                    }}
                    className="h-[40px] rounded-lg"
                  />
                  
                  {/* Phone Number Input */}
                  <div className="relative group">
                    <i className="fas fa-phone absolute left-4 top-1/2 transform -translate-y-1/2 text-novaNeutral-400 group-hover:text-novaPrimary-500 transition-colors duration-200"></i>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone || ""}
                      maxLength={16}
                      onChange={(e) => {
                        // Only allow digits and spaces
                        const numericValue = e.target.value.replace(/[^\d\s]/g, '');
                        // Limit to 20 characters
                        if (numericValue.length <= 20) {
                          setFormData({ ...formData, phone: numericValue });
                        }
                      }}
                      onBlur={handleProfileUpdate}
                      autoComplete="tel"
                      className="w-full pl-11 pr-4 py-2.5 h-[40px] text-sm border border-novaNeutral-200 rounded-lg focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 focus:bg-white transition-all duration-200"
                      placeholder="123 456 7890"
                    />
                  </div>
                </form>
              </div>

              {localStorage.getItem("password_state") === "can_update" && (
              <>
                  {/* Password Section */}
              <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 p-5 sm:p-6 md:col-span-2 border border-novaNeutral-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1 h-6 bg-gradient-to-b from-novaPrimary-500 to-novaPrimary-600 rounded-full"></div>
                  <h3 className="text-lg sm:text-xl font-bold text-novaNeutral-900">Security</h3>
                </div>
                <p className="text-sm text-novaNeutral-500 mb-6 ml-3">Update your password to keep your account secure</p>
                <form onSubmit={handlePasswordChange}>
                  {/* Hidden email field for password managers (Chrome, etc.) */}
                  <input
                    type="text"
                    name="username"
                    autoComplete="username"
                    value={formData.email || ""}
                    readOnly
                    style={{
                      position: "absolute",
                      left: "-9999px",
                      width: "1px",
                      height: "1px",
                      opacity: 0,
                    }}
                  />
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    <FormInput
                      name="current_password"
                      type="password"
                      label="Current password"
                      placeholder="Enter your current password"
                      required
                      showPasswordToggle={true}
                      inputClassName="text-sm"
                      autoComplete="password"
                      {...createFieldProps(
                        "current_password",
                        passwordFormData,
                        passwordErrors,
                        passwordTouched,
                        handlePasswordFieldChange,
                        handlePasswordFieldBlur
                      )}
                    />
                    {/* Empty spacer for the right half of row 1 on large screens */}
                    <div className="hidden lg:block"></div>
                    <FormInput
                      name="new_password"
                      type="password"
                      label="New password"
                      placeholder="Enter your new password"
                      required
                      showPasswordToggle={true}
                      inputClassName="text-sm"
                      autoComplete="new-password"
                      {...createFieldProps(
                        "new_password",
                        passwordFormData,
                        passwordErrors,
                        passwordTouched,
                        handlePasswordFieldChange,
                        handlePasswordFieldBlur
                      )}
                    />
                    <FormInput
                      name="confirm_new_password"
                      type="password"
                      label="Confirm new password"
                      placeholder="Confirm your new password"
                      required
                      showPasswordToggle={true}
                      inputClassName="text-sm"
                      autoComplete="new-password"
                      {...createFieldProps(
                        "confirm_new_password",
                        passwordFormData,
                        passwordErrors,
                        passwordTouched,
                        handlePasswordFieldChange,
                        handlePasswordFieldBlur
                      )}
                    />
                  </div>
                  <div className="mt-6">
                    <FormButton
                      variant="primary"
                      size="sm"
                      type="submit"
                      disabled={!isPasswordValid || isPasswordSubmitting}
                      className="relative px-5 py-2.5 text-base text-white bg-gradient-to-r from-novaPrimary-600 to-novaPrimary-700 hover:from-novaPrimary-700 hover:to-novaPrimary-800 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:hover:shadow-md group"
                    >
                      {isPasswordSubmitting ? (
                        <span className="flex items-center gap-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Updating...
                        </span>
                      ) : (
                        "Update Password"
                      )}
                    </FormButton>
                  </div>
                </form>
              </div>
              </>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
