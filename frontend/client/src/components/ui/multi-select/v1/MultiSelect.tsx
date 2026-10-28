import React, { useState, useRef, useEffect } from "react";
import { MultiSelectProps } from "@/lib/types";

const MultiSelect: React.FC<MultiSelectProps> = ({
  label,
  required,
  options,
  selected,
  onChange,
  error,
  placeholder = "Select options...",
  maxSelections,
  selectedCount,
}) => {
  const effectiveCount = selectedCount ?? selected.length;
  const atMaxSelections = typeof maxSelections === "number" && effectiveCount >= maxSelections;
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Helper to check if an option is selected (by value or label)
  const isOptionSelected = (option: { value: string; label: string }): boolean => {
    return selected.some(
      (item) =>
        item === option.value ||
        item === option.label ||
        item?.toLowerCase() === option.value?.toLowerCase() ||
        item?.toLowerCase() === option.label?.toLowerCase()
    );
  };

  // Helper to find option by value or label
  const findOption = (searchValue: string): { value: string; label: string } | undefined => {
    return options.find(
      (opt) =>
        opt.value === searchValue ||
        opt.label === searchValue ||
        opt.value?.toLowerCase() === searchValue?.toLowerCase() ||
        opt.label?.toLowerCase() === searchValue?.toLowerCase()
    );
  };

  const toggleOption = (optionValue: string) => {
    const option = findOption(optionValue);
    if (!option) return;

    const isSelected = isOptionSelected(option);
    // When at max, only allow deselecting (disabling adding)
    if (!isSelected && atMaxSelections) return;

    if (isSelected) {
      // Remove by matching value or label
      onChange(
        selected.filter(
          (item) =>
            item !== option.value &&
            item !== option.label &&
            item?.toLowerCase() !== option.value?.toLowerCase() &&
            item?.toLowerCase() !== option.label?.toLowerCase()
        )
      );
    } else {
      // Always add the value (not label) to maintain consistency
      onChange([...selected, option.value]);
    }
  };

  const removeOption = (optionValue: string) => {
    const option = findOption(optionValue);
    if (!option) {
      // If not found, try to remove directly
      onChange(selected.filter((item) => item !== optionValue));
      return;
    }

    // Remove by matching value or label
    onChange(
      selected.filter(
        (item) =>
          item !== option.value &&
          item !== option.label &&
          item?.toLowerCase() !== option.value?.toLowerCase() &&
          item?.toLowerCase() !== option.label?.toLowerCase()
      )
    );
  };

  // Helper to get label for a value (can be value or label)
  const getLabel = (value: string): string => {
    const option = findOption(value);
    return option?.label || value;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
        {label} {required && <span className="text-novaCaution-500">*</span>}
      </label>

      {/* Selected tags */}
      <div
        className={`min-h-10 px-2 py-1 border rounded-md cursor-pointer flex flex-wrap gap-1 items-center ${
          error ? "border-novaCaution-500" : "border-novaNeutral-300"
        } ${
          isOpen ? "border-novaPrimary-500" : ""
        }`}
        onClick={() => setIsOpen(!isOpen)}
      >
        {selected.length === 0 ? (
          <span className="text-novaNeutral-500 text-sm">{placeholder}</span>
        ) : (
          selected.map((optionValue) => (
            <span
              key={optionValue}
              className="inline-flex items-center px-2 py-0.5 rounded-md text-xs bg-novaAlert-50 text-novaPrimary-800"
            >
              {getLabel(optionValue)}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeOption(optionValue);
                }}
                className="ml-1 hover:text-novaPrimary-900"
              >
                ×
              </button>
            </span>
          ))
        )}
      </div>

      {/* Dropdown options */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-novaNeutral-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {options
            .filter((option) => option && option.value && option.label)
            .map((option) => {
              const isSelected = isOptionSelected(option);
              const isDisabled = atMaxSelections && !isSelected;
              return (
                <div
                  key={option.value}
                  className={`px-3 py-2 text-sm ${
                    isDisabled
                      ? "cursor-not-allowed opacity-50 bg-novaNeutral-50 text-novaNeutral-400"
                      : `cursor-pointer hover:bg-novaNeutral-100 ${isSelected ? "bg-novaPrimary-50 text-novaPrimary-800" : ""}`
                  }`}
                  onClick={() => !isDisabled && toggleOption(option.value)}
                >
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      disabled={isDisabled}
                      onChange={() => !isDisabled && toggleOption(option.value)}
                      className="mr-2 rounded border-novaNeutral-300 text-novaPrimary-500 focus:ring-novaPrimary-500 disabled:cursor-not-allowed"
                    />
                    {option.label}
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {error && <p className="mt-1 text-xs text-novaCaution-500">{error}</p>}
    </div>
  );
};

export default MultiSelect;
