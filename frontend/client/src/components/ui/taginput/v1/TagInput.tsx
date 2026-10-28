import React, { useState, KeyboardEvent, useEffect } from "react";

interface TagInputProps {
  label?: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  maxValues?: number;
  onMaxReached?: () => void;
}

export const TagInput: React.FC<TagInputProps> = ({
  label,
  values,
  onChange,
  placeholder = "Type and press Enter",
  maxValues,
  onMaxReached,
}) => {
  const [inputValue, setInputValue] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Clear error message after 3 seconds
  useEffect(() => {
    if (errorMessage) {
      const timer = setTimeout(() => {
        setErrorMessage(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [errorMessage]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputValue.trim() !== "") {
      e.preventDefault();
      e.stopPropagation(); // Prevent event from bubbling up to form handlers
      
      // Check if value already exists
      if (values.includes(inputValue.trim())) {
        setErrorMessage("This value is already added");
        return;
      }
      
      // Check if max values reached
      if (maxValues !== undefined && values.length >= maxValues) {
        setErrorMessage(`Maximum of ${maxValues} values allowed`);
        if (onMaxReached) {
          onMaxReached();
        }
        setInputValue("");
        return;
      }
      
      onChange([...values, inputValue.trim()]);
      setInputValue("");
    }
    if (e.key === "Backspace" && inputValue === "") {
      onChange(values.slice(0, -1));
    }
  };

  const handleRemove = (index: number) => {
    const updated = [...values];
    updated.splice(index, 1);
    onChange(updated);
  };

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="block text-xs font-medium text-novaNeutral-700 mb-1">
          {label}
        </label>
      )}
      <div className={`flex flex-wrap items-center gap-1 border rounded-lg px-2 py-1 focus-within:ring-1 ${
        errorMessage 
          ? "border-novaCaution-300 focus-within:ring-novaCaution-500" 
          : "border-gray-300 focus-within:ring-novaPrimary-500"
      }`}>
        {values.map((tag, i) => (
          <span
            key={i}
            className="flex items-center gap-1 bg-novaAlert-50 text-novaPrimary-700 px-2 py-0.5 rounded-md text-xs"
          >
            {tag}
            <button
              type="button"
              onClick={() => handleRemove(i)}
              className="text-novaPrimary-500 hover:text-novaPrimary-900"
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            // Clear error when user starts typing
            if (errorMessage) {
              setErrorMessage(null);
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 outline-none text-sm py-1 px-1 bg-transparent min-w-[80px]"
        />
      </div>
      {errorMessage && (
        <p className="text-xs text-novaCaution-600 mt-1">
          <i className="fas fa-exclamation-circle mr-1"></i>
          {errorMessage}
        </p>
      )}
    </div>
  );
};
