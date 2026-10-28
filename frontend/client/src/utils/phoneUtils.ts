// Phone number utility functions
import { COUNTRIES } from "@/constants/countries";

/**
 * Parses a phone number and extracts the country code and phone number
 * @param fullPhoneNumber - Full phone number with country code (e.g., "+44123456789")
 * @returns Object containing countryCode, dialCode, and phoneNumber (without country code)
 */
export function parsePhoneNumber(fullPhoneNumber: string): {
  countryCode: string;
  dialCode: string;
  phoneNumber: string;
} {
  // Default values
  const defaultResult = {
    countryCode: "GB",
    dialCode: "+44",
    phoneNumber: fullPhoneNumber || "",
  };

  if (!fullPhoneNumber || typeof fullPhoneNumber !== 'string') {
    return defaultResult;
  }

  // Trim the phone number
  const trimmedPhone = fullPhoneNumber.trim();

  // If phone doesn't start with +, return as is
  if (!trimmedPhone.startsWith("+")) {
    return {
      ...defaultResult,
      phoneNumber: trimmedPhone,
    };
  }

  // Sort country codes by dial code length (longest first) to match correctly
  // This ensures +1 doesn't match before checking for longer codes
  const sortedCountryCodes = [...COUNTRIES].sort(
    (a, b) => b.dialCode.length - a.dialCode.length
  );

  // Try to match the phone number with a known country code
  for (const country of sortedCountryCodes) {
    if (trimmedPhone.startsWith(country.dialCode)) {
      // Extract the phone number without the dial code
      const phoneWithoutCode = trimmedPhone
        .substring(country.dialCode.length)
        .trim();

      return {
        countryCode: country.code,
        dialCode: country.dialCode,
        phoneNumber: phoneWithoutCode,
      };
    }
  }

  // If no match found, return the original number
  return {
    ...defaultResult,
    phoneNumber: trimmedPhone,
  };
}

/**
 * Combines a dial code and phone number into a full phone number
 * @param dialCode - Country dial code (e.g., "+44")
 * @param phoneNumber - Phone number without country code
 * @returns Full phone number with country code
 */
export function combinePhoneNumber(dialCode: string, phoneNumber: string): string {
  if (!phoneNumber || !phoneNumber.trim()) {
    return "";
  }
  // Remove any spaces from the phone number
  const cleanPhone = phoneNumber.replace(/\s/g, "");
  return `${dialCode}${cleanPhone}`;
}

