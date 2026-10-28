import React, { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { COUNTRIES, getFlagSvg } from "@/constants/countries";
import { cn } from "@/lib/utils";

// Component to render SVG flag from string
const FlagIcon: React.FC<{ code: string; className?: string }> = ({ code, className = "" }) => {
  const svgString = getFlagSvg(code);
  if (!svgString) return null;
  
  return (
    <span
      className={`inline-block ${className}`}
      dangerouslySetInnerHTML={{ __html: svgString }}
    />
  );
};

interface PhoneCountryCodeSelectProps {
  value: string; // Country code (e.g., "GB", "US")
  onChange: (countryCode: string, dialCode: string) => void;
  disabled?: boolean;
  className?: string;
}

const PhoneCountryCodeSelect: React.FC<PhoneCountryCodeSelectProps> = ({
  value,
  onChange,
  disabled = false,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0, openAbove: false, maxHeight: 300 });

  // Find the selected country by country code
  const selectedCountry = COUNTRIES.find((c) => c.code === value) || COUNTRIES[0];

  // Filter countries based on search term
  const filteredCountries = COUNTRIES.filter(
    (country) =>
      country.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      country.dialCode.includes(searchTerm) ||
      country.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Calculate dropdown position when opening
  // Note: position:fixed uses viewport coords, so use rect values directly (no scroll offset)
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const dropdownHeight = 250;
      const viewportHeight = window.innerHeight;
      const spaceBelow = viewportHeight - rect.bottom;
      const spaceAbove = rect.top;
      
      // Open above if there's not enough space below but enough above
      const shouldOpenAbove = spaceBelow < dropdownHeight && spaceAbove > spaceBelow;
      
      // Calculate the max height based on available space
      const availableSpace = shouldOpenAbove ? spaceAbove : spaceBelow;
      const maxDropdownHeight = Math.min(dropdownHeight, availableSpace - 16); // 16px padding from edges
      
      setDropdownPosition({
        top: shouldOpenAbove 
          ? rect.top // Will use transform to position above
          : rect.bottom + 4,
        left: rect.left,
        width: rect.width,
        openAbove: shouldOpenAbove,
        maxHeight: maxDropdownHeight,
      });
    }
  }, [isOpen]);

  // Close dropdown when clicking outside or scrolling
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    const handleScroll = (event: Event) => {
      // Don't close if scrolling within the dropdown itself
      if (dropdownRef.current && dropdownRef.current.contains(event.target as Node)) {
        return;
      }
      // Close dropdown when page is scrolled
      setIsOpen(false);
      setSearchTerm("");
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      // Listen for scroll on window and any scrollable parent
      window.addEventListener("scroll", handleScroll, true);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
        window.removeEventListener("scroll", handleScroll, true);
      };
    }
  }, [isOpen]);

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

  const handleSelect = (country: typeof COUNTRIES[0]) => {
    onChange(country.code, country.dialCode);
    setIsOpen(false);
    setSearchTerm("");
    setHighlightedIndex(-1);
  };

  const handleToggle = () => {
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

  const dropdownContent = isOpen ? (
    <div
      ref={dropdownRef}
      className="fixed z-[10002] sm:w-72 w-68 bg-white border border-novaNeutral-300 rounded-lg shadow-lg flex flex-col"
      style={{
        top: `${dropdownPosition.top}px`,
        left: `${dropdownPosition.left}px`,
        maxHeight: `${dropdownPosition.maxHeight}px`,
        ...(dropdownPosition.openAbove && {
          transform: 'translateY(-100%) translateY(-4px)',
        }),
      }}
    >
      {/* Search input */}
      <div className="p-2 border-b border-novaNeutral-200 flex-shrink-0">
        <div className="relative">
          <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-novaNeutral-400 text-xs"></i>
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearchChange}
            placeholder="Search country..."
            className="w-full pl-8 pr-3 py-2 text-sm border border-novaNeutral-300 rounded-md focus:outline-none focus:ring-novaPrimary-500 focus:border-novaPrimary-500"
            autoFocus
          />
        </div>
      </div>

      {/* Countries list */}
      <div className="flex-1 overflow-auto min-h-0">
        {filteredCountries.length > 0 ? (
          <ul className="py-1">
            {filteredCountries.map((country, index) => (
              <li
                key={country.code}
                onClick={() => handleSelect(country)}
                onMouseEnter={() => setHighlightedIndex(index)}
                className={`px-3 py-2 text-sm cursor-pointer transition-colors flex items-center justify-between ${
                  index === highlightedIndex
                    ? "bg-novaPrimary-50 text-novaPrimary-700"
                    : "text-novaNeutral-700 hover:bg-novaNeutral-50"
                } ${
                  value === country.code
                    ? "bg-novaPrimary-100 font-medium"
                    : ""
                }`}
              >
                <div className="flex items-center gap-2">
                  <FlagIcon code={country.code} className="w-5 h-auto rounded-sm overflow-hidden" />
                  <span>{country.name}</span>
                </div>
                <span className="text-novaNeutral-500 font-mono">{country.dialCode}</span>
                {value === country.code && (
                  <i className="fas fa-check ml-2 text-novaPrimary-600"></i>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-3 py-4 text-sm text-novaNeutral-500 text-center">
            No countries found
          </div>
        )}
      </div>
    </div>
  ) : null;

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={cn(
          "w-full px-3 text-sm border rounded-md py-1.5 focus:outline-none focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 flex items-center justify-between bg-white border-novaNeutral-300",
          disabled ? "bg-novaNeutral-100 cursor-not-allowed opacity-50" : "cursor-pointer hover:bg-novaNeutral-50",
          className
        )}
      >
        <span className="flex items-center gap-2 font-medium text-novaNeutral-700">
          <FlagIcon code={selectedCountry.code} className="w-5 h-auto rounded-sm overflow-hidden" />
          <span>{selectedCountry.dialCode}</span>
        </span>
        <i className={`fas fa-chevron-${isOpen ? "up" : "down"} text-novaNeutral-400 text-xs`}></i>
      </button>

      {/* Dropdown rendered via portal */}
      {isOpen && typeof document !== 'undefined' && createPortal(dropdownContent, document.body)}
    </div>
  );
};

export default PhoneCountryCodeSelect;

