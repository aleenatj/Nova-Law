// Centralized country data
// Using country-flag-icons package for bundled SVG flags (no external requests)
import GB from "country-flag-icons/string/3x2/GB";
import US from "country-flag-icons/string/3x2/US";
import CA from "country-flag-icons/string/3x2/CA";
import AU from "country-flag-icons/string/3x2/AU";
import DE from "country-flag-icons/string/3x2/DE";
import FR from "country-flag-icons/string/3x2/FR";
import IT from "country-flag-icons/string/3x2/IT";
import ES from "country-flag-icons/string/3x2/ES";
import IN from "country-flag-icons/string/3x2/IN";
import CN from "country-flag-icons/string/3x2/CN";
import JP from "country-flag-icons/string/3x2/JP";
import BR from "country-flag-icons/string/3x2/BR";
import RU from "country-flag-icons/string/3x2/RU";
import ZA from "country-flag-icons/string/3x2/ZA";
import NL from "country-flag-icons/string/3x2/NL";
import MX from "country-flag-icons/string/3x2/MX";
import TR from "country-flag-icons/string/3x2/TR";
import SE from "country-flag-icons/string/3x2/SE";
import CH from "country-flag-icons/string/3x2/CH";
import SG from "country-flag-icons/string/3x2/SG";

// Map of country codes to their SVG strings
const FLAG_SVG_MAP: Record<string, string> = {
  GB, US, CA, AU, DE, FR, IT, ES, IN, CN, JP, BR, RU, ZA, NL, MX, TR, SE, CH, SG,
};

export interface CountryData {
  name: string;
  code: string;
  dialCode: string;
}

// Single source of truth for all country data
export const COUNTRIES: CountryData[] = [
  { name: "United Kingdom", code: "GB", dialCode: "+44" },
  { name: "United States", code: "US", dialCode: "+1" },
  { name: "Canada", code: "CA", dialCode: "+1" },
  { name: "Australia", code: "AU", dialCode: "+61" },
  { name: "Germany", code: "DE", dialCode: "+49" },
  { name: "France", code: "FR", dialCode: "+33" },
  { name: "Italy", code: "IT", dialCode: "+39" },
  { name: "Spain", code: "ES", dialCode: "+34" },
  { name: "India", code: "IN", dialCode: "+91" },
  { name: "China", code: "CN", dialCode: "+86" },
  { name: "Japan", code: "JP", dialCode: "+81" },
  { name: "Brazil", code: "BR", dialCode: "+55" },
  { name: "Russia", code: "RU", dialCode: "+7" },
  { name: "South Africa", code: "ZA", dialCode: "+27" },
  { name: "Netherlands", code: "NL", dialCode: "+31" },
  { name: "Mexico", code: "MX", dialCode: "+52" },
  { name: "Turkey", code: "TR", dialCode: "+90" },
  { name: "Sweden", code: "SE", dialCode: "+46" },
  { name: "Switzerland", code: "CH", dialCode: "+41" },
  { name: "Singapore", code: "SG", dialCode: "+65" },
];

// Export just country names for simple country selects
export const COUNTRY_NAMES = COUNTRIES.map((country) => country.name);

// Helper function to get flag SVG string by country code
export function getFlagSvg(code: string): string {
  return FLAG_SVG_MAP[code] || "";
}

// Helper function to get country by code
export function getCountryByCode(code: string): CountryData | undefined {
  return COUNTRIES.find((c) => c.code === code);
}

// Helper function to get country by name
export function getCountryByName(name: string): CountryData | undefined {
  return COUNTRIES.find((c) => c.name === name);
}

