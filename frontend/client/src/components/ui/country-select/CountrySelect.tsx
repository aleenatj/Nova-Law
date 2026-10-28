import React, { useState, useRef, useEffect } from "react";
import { COUNTRY_NAMES } from "@/constants/countries";

interface CountrySelectProps {
  value: string | null;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}

const CountrySelect: React.FC<CountrySelectProps> = ({
  value,
  onChange,
  error,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check if current value is in the list
  const isValueInList = value ? COUNTRY_NAMES.includes(value) : false;
  const displayValue = value || "";

  // Filter countries based on search term
  const filteredCountries = COUNTRY_NAMES.filter((country) =>
    country.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen && (e.key === "ArrowDown" || e.key === "Enter")) {
      e.preventDefault();
      setIsOpen(true);
      return;
    }

    if (isOpen) {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < filteredCountries.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case "Enter":
          e.preventDefault();
          if (highlightedIndex >= 0 && highlightedIndex < filteredCountries.length) {
            handleSelect(filteredCountries[highlightedIndex]);
          }
          break;
        case "Escape":
          e.preventDefault();
          setIsOpen(false);
          setSearchTerm("");
          break;
      }
    }
  };

  const handleSelect = (country: string) => {
    onChange(country);
    setIsOpen(false);
    setSearchTerm("");
    setHighlightedIndex(-1);
  };

  const handleInputClick = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
      if (!isOpen) {
        setSearchTerm("");
      }
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setHighlightedIndex(-1);
    if (!isOpen) {
      setIsOpen(true);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={isOpen ? searchTerm : displayValue}
          onChange={handleSearchChange}
          onClick={handleInputClick}
          onKeyDown={handleKeyDown}
          placeholder={isOpen ? "Type to search..." : "Select a country"}
          disabled={disabled}
          className={`w-full px-3 py-2 text-sm border rounded-md focus:border-novaPrimary-500 ${
            error ? "border-novaCaution-300" : "border-novaNeutral-300"
          } ${disabled ? "bg-novaNeutral-100 cursor-not-allowed" : "cursor-pointer"}`}
          readOnly={!isOpen}
        />
        <div
          className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none"
          aria-hidden="true"
        >
          <i
            className={`fas fa-chevron-${isOpen ? "up" : "down"} text-novaNeutral-400 text-xs`}
          ></i>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-novaNeutral-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {filteredCountries.length > 0 ? (
            <ul className="py-1">
              {filteredCountries.map((country, index) => (
                <li
                  key={country}
                  onClick={() => handleSelect(country)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  className={`px-3 py-2 text-sm cursor-pointer transition-colors ${
                    index === highlightedIndex
                      ? "bg-novaPrimary-50 text-novaPrimary-700"
                      : "text-novaNeutral-700 hover:bg-novaNeutral-50"
                  } ${
                    value === country
                      ? "bg-novaPrimary-100 font-medium"
                      : ""
                  }`}
                >
                  {country}
                  {value === country && (
                    <i className="fas fa-check ml-2 text-novaPrimary-600"></i>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-3 py-2 text-sm text-novaNeutral-500 text-center">
              No countries found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CountrySelect;

