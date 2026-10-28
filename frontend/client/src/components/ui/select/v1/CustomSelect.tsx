import React, { useState, useRef, useEffect } from "react";

interface SelectOption {
  value: string;
  label: string;
  icon?: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  icon?: string;
  className?: string;
  triggerClassName?: string;
  disabled?: boolean;
  error?: boolean;
}

const CustomSelect: React.FC<CustomSelectProps> = ({
  value,
  onChange,
  options,
  placeholder = "Select...",
  icon,
  className = "",
  triggerClassName = "",
  disabled = false,
  error = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    // Use click event instead of mousedown to avoid conflicts with option selection
    // Add listener in next tick to ensure option clicks are processed first
    const timeoutId = setTimeout(() => {
      document.addEventListener("click", handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener("click", handleClickOutside);
    };
  }, [isOpen]);

  const selectedOption = options.find((opt) => {
    if (!opt || typeof opt.label !== 'string') return false;
    return opt.value === value || (value && opt.label.toLowerCase() === value.toLowerCase());
  });
  const displayLabel = selectedOption?.label || placeholder;
  const displayIcon = selectedOption?.icon || icon; // Use selected option's icon or fallback to default icon

  const handleSelect = (optionValue: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full max-w-full min-w-0 flex items-center justify-between gap-2
          px-2 sm:px-3 py-2 text-sm ${displayIcon ? "lg:pl-9" : ""}
          border bg-white
          transition-all duration-200
          ${
            error
              ? "border-novaCaution-500"
              : isOpen
              ? "border-novaPrimary-400 ring-2 ring-novaPrimary-100"
              : "border-novaNeutral-300"
          }
          ${
            disabled
              ? "opacity-50 cursor-not-allowed"
              : "cursor-pointer hover:border-novaPrimary-300 hover:shadow-sm"
          }
          focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white
        ${triggerClassName}
        `}
        style={{
          minHeight: "28px", // minimum for button
        }}
      >
        {/* Icon - hidden on screens smaller than lg */}
        {displayIcon && (
          <div className="hidden lg:block absolute left-3 top-1/2 transform -translate-y-1/2 mr-1">
            <i className={`${displayIcon} ${isOpen ? 'text-novaPrimary-600' : 'text-novaPrimary-500'} text-sm transition-colors`}></i>
          </div>
        )}

        {/* Selected Value */}
        <span title={displayLabel} className={`truncate min-w-0 max-w-[180px] sm:max-w-[220px] text-xs sm:text-sm ${value ? 'text-novaNeutral-900' : 'text-novaNeutral-500'}`}>
          {displayLabel}
        </span>

        {/* Chevron */}
        <i
          className={`fas fa-chevron-down text-xs transition-all duration-200 flex-shrink-0 text-novaPrimary-600 ${
            isOpen ? "rotate-180" : ""
          }`}
        ></i>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 py-1 bg-white border border-novaNeutral-200 rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
          {options
            .filter((option) => {
              // Filter out invalid options to prevent errors
              return option && 
                     typeof option === 'object' && 
                     typeof option.label === 'string' && 
                     typeof option.value === 'string' &&
                     option.value;
            })
            .map((option) => {
              // Safe comparison - check if option is selected
              const isSelected = value === option.value || 
                (value && 
                 option.label && 
                 typeof option.label === 'string' && 
                 typeof value === 'string' &&
                 value.toLowerCase() === option.label.toLowerCase());
              
              return (
                <button
                  key={option.value}
                  type="button"
                  title={option.label}
                  onClick={(e) => handleSelect(option.value, e)}
                  className={`
                    w-full flex items-center gap-2.5 px-2 py-0.5 sm:px-3 sm:py-2 text-left text-sm
                    transition-all duration-150
                    ${
                      isSelected
                        ? "bg-novaPrimary-50 text-novaPrimary-800 font-semibold"
                        : "text-novaNeutral-700 hover:bg-novaNeutral-50 hover:text-novaNeutral-900"
                    }
                  `}
                  style={{
                    minHeight: "26px", // minimum for option
                  }}
                >
                  {/* Option Icon - hidden on screens smaller than lg */}
                  {option.icon && (
                    <i className={`hidden lg:inline-block ${option.icon} text-sm w-4 flex-shrink-0 ${
                      isSelected ? 'text-novaPrimary-600' : 'text-novaNeutral-400'
                    }`}></i>
                  )}
                  
                  {/* Option Label */}
                  <span className="flex-1 min-w-0 text-xs sm:text-sm line-clamp-2">{option.label}</span>
                  
                  {/* Check Icon for Selected */}
                  {value === option.value && (
                    <i className="fas fa-check text-novaPrimary-600 text-xs flex-shrink-0"></i>
                  )}
                </button>
              );
            })}
        </div>
      )}
    </div>
  );
};

export default CustomSelect;
