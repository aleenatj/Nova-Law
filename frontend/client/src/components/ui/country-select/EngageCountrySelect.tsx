import React, { useEffect, useRef, useState } from "react";
import { ENGAGE_COUNTRY_NAMES } from "@/constants/engageCountryOptions";

interface EngageCountrySelectProps {
  id?: string;
  value: string | null;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}

/**
 * Plain HTML <select> country picker for Engage `input_type: "country_select"`.
 * Uses `ENGAGE_COUNTRY_NAMES` so option values match what the backend stores.
 */
const EngageCountrySelect: React.FC<EngageCountrySelectProps> = ({
  id,
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

  const displayValue = value || "";
  const filteredCountries = ENGAGE_COUNTRY_NAMES.filter((country) =>
    country.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm("");
        setHighlightedIndex(-1);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (country: string) => {
    onChange(country);
    setIsOpen(false);
    setSearchTerm("");
    setHighlightedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen && (e.key === "ArrowDown" || e.key === "Enter")) {
      e.preventDefault();
      if (!disabled) setIsOpen(true);
      return;
    }

    if (!isOpen) return;

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
        setHighlightedIndex(-1);
        break;
    }
  };

  const handleInputClick = () => {
    if (disabled) return;
    setIsOpen((open) => {
      const next = !open;
      if (!next) {
        setSearchTerm("");
        setHighlightedIndex(-1);
      }
      return next;
    });
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setHighlightedIndex(-1);
    if (!isOpen && !disabled) setIsOpen(true);
  };

  return (
    <div className="relative w-full max-w-md" ref={dropdownRef}>
      <div className="relative">
        <input
          id={id}
          ref={inputRef}
          type="text"
          value={isOpen ? searchTerm : displayValue}
          onChange={handleSearchChange}
          onClick={handleInputClick}
          onKeyDown={handleKeyDown}
          placeholder={isOpen ? "Type to search..." : "Select a country"}
          disabled={disabled}
          readOnly={!isOpen}
          aria-invalid={Boolean(error)}
          className={`w-full px-3 py-2 text-sm border rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-novaOrange ${
            error ? "border-novaCaution-300" : "border-novaNeutral-300"
          } ${disabled ? "bg-novaNeutral-100 cursor-not-allowed text-novaNeutral-500" : "bg-white text-novaNeutral-800"}`}
        />

        <div
          className="absolute inset-y-0 right-3 flex items-center pointer-events-none"
          aria-hidden="true"
        >
          <i
            className={`fas fa-chevron-${isOpen ? "up" : "down"} text-novaNeutral-400 text-xs`}
          />
        </div>
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-novaNeutral-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {filteredCountries.length > 0 ? (
            <ul className="py-1">
              {filteredCountries.map((country, index) => {
                const isSelected = value === country;
                const isHighlighted = index === highlightedIndex;
                return (
                  <li
                    key={country}
                    onClick={() => handleSelect(country)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`px-3 py-2 text-sm cursor-pointer transition-colors ${
                      isHighlighted
                        ? "bg-novaDarkOrange text-white"
                        : "text-novaNeutral-700 hover:bg-novaDarkOrange hover:text-white"
                    } ${isSelected ? "font-medium" : ""}`}
                  >
                    <span className="block truncate">{country}</span>
                    {isSelected && (
                      <i className="fas fa-check ml-2 text-white" aria-hidden="true" />
                    )}
                  </li>
                );
              })}
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

export default EngageCountrySelect;

