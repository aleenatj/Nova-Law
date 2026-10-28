import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import PhoneCountryCodeSelect from "../ui/phone-country-select/PhoneCountryCodeSelect";
import { parsePhoneNumber, combinePhoneNumber } from "@/utils/phoneUtils";
import { FormButton } from "@/utils/formComponents";

interface PhoneVerificationPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onVerify: (phoneNumber: string) => void;
  lawyerName?: string;
  onAfterVerify?: () => void; // Optional callback after successful verification
}

const PhoneVerificationPopup: React.FC<PhoneVerificationPopupProps> = ({
  isOpen,
  onClose,
  onVerify,
  lawyerName,
  onAfterVerify,
}) => {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState("");
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("GB");
  const [dialCode, setDialCode] = useState<string>("+44");

  // Prepopulate phone number from localStorage if available
  useEffect(() => {
    if (isOpen) {
      let phone = "";
      try {
        const userStr = localStorage.getItem("user");
        if (userStr) {
          const user = JSON.parse(userStr);
          if (user && typeof user.phone === "string") {
            phone = user.phone;
          }
        }
      } catch (e) {
        // ignore parse errors
      }
      
      // Parse phone number to extract country code and phone number separately
      if (phone) {
        const { countryCode, dialCode: parsedDialCode, phoneNumber: parsedPhone } = parsePhoneNumber(phone);
        setSelectedCountryCode(countryCode);
        setDialCode(parsedDialCode);
        setPhoneNumber(parsedPhone);
      } else {
        setPhoneNumber("");
      }
      setError("");
    }
  }, [isOpen]);

  const handlePhoneNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Only allow numbers and spaces
    const numericValue = value.replace(/[^\d\s]/g, '');
    // Limit to 20 characters
    if (numericValue.length <= 14) {
      setPhoneNumber(numericValue);
    }
  };

  // Handler for country code selection
  const handleCountryCodeChange = (countryCode: string, phoneDialCode: string) => {
    setSelectedCountryCode(countryCode);
    setDialCode(phoneDialCode);
  };

  const handleVerify = async () => {
    setError("");
    if (!phoneNumber.trim()) {
      setError("Please enter your phone number");
      return;
    }

    setIsVerifying(true);

    // Simulate verification process
    // In a real implementation, you would send the phone number to your backend
    // and wait for OTP verification
    await new Promise(resolve => setTimeout(resolve, 800));

    setIsVerifying(false);

    // Combine dial code with phone number using utility function
    const fullPhoneNumber = combinePhoneNumber(dialCode, phoneNumber);

    // Close the popup and trigger the callback with phone number
    onClose();
    onVerify(fullPhoneNumber);
    
    // Call the optional callback after verification
    if (onAfterVerify) {
      onAfterVerify();
    }
  };

  const handleClose = () => {
    if (!isVerifying) {
      setPhoneNumber("");
      setError("");
      onClose();
    }
  };

  if (!isOpen) return null;

  const modalContent = (
    <>
      {/* Backdrop Overlay */}
      <div
        className="fixed inset-0 z-[10000] bg-black bg-opacity-60 backdrop-blur-md transition-opacity"
        onClick={isVerifying ? undefined : handleClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-describedby="phone-verification-description"
        aria-labelledby="phone-verification-title"
        aria-modal="true"
        className="fixed left-1/2 top-1/2 z-[10001] w-[92%] max-w-md translate-x-[-50%] translate-y-[-50%] rounded-xl border border-gray-200 bg-white p-0 shadow-[0_2px_16px_0_rgba(0,0,0,0.18)]"
        tabIndex={-1}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={handleClose}
          disabled={isVerifying}
          className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-30 text-novaNeutral-500 hover:text-novaNeutral-700"
          aria-label="Close"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="lucide lucide-x h-5 w-5"
          >
            <path d="M18 6 6 18"></path>
            <path d="m6 6 12 12"></path>
          </svg>
        </button>

        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-novaNeutral-200">
          <h2
            id="phone-verification-title"
            className="text-xl font-semibold text-novaNeutral-900"
          >
            Verify Your Number
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="mb-6">
            <div className="w-16 h-16 bg-novaActive rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="fas fa-phone text-2xl text-novaOrange"></i>
            </div>
            <p
              id="phone-verification-description"
              className="text-center text-sm text-novaNeutral-600 leading-relaxed"
            >
              {lawyerName
                ? <>Please verify your phone number so one of our Nova Navigators can arrange your intro call with <strong className="whitespace-nowrap">{lawyerName}</strong>.</>
                : "Please verify your phone number so one of our Nova Navigators can arrange your intro call"}
            </p>
          </div>

          {/* Phone Number Input */}
          <div className="mb-4">
            <label
              htmlFor="phone-number"
              className="block text-sm font-medium text-novaNeutral-700 mb-2"
            >
              Phone Number
              <span className="ml-1 text-xs text-novaCaution-500">*</span>
            </label>
            <div className="grid grid-cols-[110px_1fr] gap-2">
              <PhoneCountryCodeSelect
                value={selectedCountryCode}
                onChange={handleCountryCodeChange}
                disabled={isVerifying}
                className="h-[42px]"
              />
              <input
                id="phone-number"
                type="tel"
                value={phoneNumber}
                onChange={handlePhoneNumberChange}
                placeholder="Enter your phone number"
                disabled={isVerifying}
                maxLength={14}
                className={`w-full px-2 sm:px-4 py-2.5 border rounded-md text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-novaSuccess-500 disabled:opacity-50 disabled:cursor-not-allowed ${
                  error
                    ? "border-red-500 focus:ring-red-500"
                    : "border-novaNeutral-300"
                }`}
              />
            </div>
            {error && (
              <p className="mt-1 text-xs text-red-600">{error}</p>
            )}
          </div>

          {/* Info Message */}
          <div className="mb-6 p-3 bg-novaInactive border border-novaActive rounded-lg">
            <p className="text-xs text-novaNeutral-700 leading-relaxed">
              <i className="fas fa-info-circle mr-1"></i>
              We'll use this number to connect you with your Nova Expert for the intro call.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 flex-col sm:flex-row">
            <FormButton
              variant="outline"
              onClick={handleClose}
              disabled={isVerifying}
              className="flex-1"
            >
              Cancel
            </FormButton>
            <FormButton
              type="button"
              onClick={handleVerify}
              disabled={isVerifying}
              className="flex-1"
            >
              {isVerifying ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  Verifying...
                </>
              ) : (
                <>
                  Verify & Continue
                </>
              )}
            </FormButton>
          </div>
        </div>
      </div>
    </>
  );

  return createPortal(modalContent, document.body);
};

export default PhoneVerificationPopup;
