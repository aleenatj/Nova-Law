import React from "react";
import { Button } from "../button";

interface DataNotFoundProps {
  userName?: string; // Optional user name for personalization
  caseNo?: string; // Optional case number for personalization
  message?: string; // Custom message override
  hint?: string; // Optional extra line of guidance
  illustration?: React.ReactNode; // Optional SVG/icon/placeholder
  buttonText?: string; // Optional CTA text (e.g., "Refresh" / "Go Back")
  onButtonClick?: () => void; // Optional CTA handler
  className?: string;
}

/**
 * DataNotFound
 *
 * Displays a friendly, consistent, and responsive message when no data is available.
 * - Personalizes message with user name or case number if provided
 * - Uses design system colors and spacing
 * - Responsive and centered
 * - Optional illustration, hint, and CTA button
 */
const DataNotFound: React.FC<DataNotFoundProps> = ({
  userName,
  caseNo,
  message,
  hint,
  illustration,
  buttonText,
  onButtonClick,
  className = "",
}) => {
  // Build a friendly, dynamic message
  let displayMessage = "No data available.";
  if (message) {
    displayMessage = message;
  } else if (userName && caseNo) {
    displayMessage = `No data available for ${userName} (Case #${caseNo}).`;
  } else if (userName) {
    displayMessage = `No data available for ${userName}.`;
  } else if (caseNo) {
    displayMessage = `No data available for Case #${caseNo}.`;
  }

  return (
    <div
      role="region"
      aria-label="no data available"
      className={`flex flex-1 h-full min-h-[300px] items-center justify-center px-8 py-12 ${className}`}
    >
      <div className="w-full text-center">
        {/* Optional Illustration */}
        {illustration && (
          <div className="flex justify-center mb-6">{illustration}</div>
        )}

        {/* Main Message */}
        <h2
          id="notfound-title"
          className="text-2xl md:text-3xl font-bold text-novaNeutral-800 mb-2"
        >
          {displayMessage}
        </h2>

        {/* Optional Hint */}
        {hint && <p className="text-base text-novaNeutral-500 mb-4">{hint}</p>}

        {/* Dotted Divider */}
        <div className="mx-auto my-4 w-24 border-t border-dotted border-novaNeutral-300" />

        {/* Optional CTA Button */}
        {buttonText && onButtonClick && (
          <span>
            Please{"  "}
            <Button
              variant="ghost"
              className="inline hover:text-novaPrimary-700 p-0 text-base align-baseline text-novaPrimary-500"
              onClick={onButtonClick}
              style={{
                display: "inline",
                background: "none",
                boxShadow: "none",
              }}
            >
              {buttonText}
            </Button>
          </span>
        )}
      </div>
    </div>
  );
};

export default DataNotFound;
