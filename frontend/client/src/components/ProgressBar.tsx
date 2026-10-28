import React from "react";

interface ProgressBarProps {
  current: number;
  total: number;
  showPercentage?: boolean;
  showLabel?: boolean;
  label?: string;
  className?: string;
  barClassName?: string;
  labelClassName?: string;
  height?: "sm" | "md" | "lg";
}

export function ProgressBar({
  current,
  total,
  showPercentage = true,
  showLabel = true,
  label,
  className = "",
  barClassName = "",
  labelClassName = "",
  height = "md",
}: ProgressBarProps) {
  const percentage = total > 0 ? (current / total) * 100 : 0;
  const displayLabel = label || `${current} of ${total} questions answered`;

  // Responsive height classes - smaller on mobile, larger on desktop
  const heightClasses = {
    sm: "h-0.5 sm:h-1",
    md: "h-1 sm:h-2",
    lg: "h-1.5 sm:h-3",
  };

  return (
    <div className={`space-y-1 sm:space-y-2 ${className}`}>
      {/* Progress Bar */}
      <div
        className={`w-full bg-white rounded-full ${heightClasses[height]}`}
      >
        <div
          className={`bg-novaPrimary-600 rounded-full transition-all duration-300 ${heightClasses[height]} ${barClassName}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>

      {/* Label and Percentage */}
      {showLabel && (
        <div className="flex justify-between items-center gap-2">
          <p className={`text-[10px] sm:text-xs text-novaNeutral-500 truncate ${labelClassName}`}>
            {displayLabel}
          </p>
          {showPercentage && (
            <p className={`text-[10px] sm:text-xs text-novaNeutral-500 whitespace-nowrap flex-shrink-0 ${labelClassName}`}>
              {Math.round(percentage)}%
            </p>
          )}
        </div>
      )}
    </div>
  );
}
