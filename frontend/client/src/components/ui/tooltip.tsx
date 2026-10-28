import React, { useState } from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  className?: string;
  position?:  'right-mobile' | 'center';
}

export function Tooltip({ content, children, className = "", position = 'center' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  // Position classes based on the position prop
  const getPositionClasses = () => {
    if (position === 'right-mobile') {
      return {
        // Mobile: above trigger (right-aligned). Desktop (md+): to the right of trigger, vertically centered
        tooltip:
          'absolute z-50 w-64 p-2 text-sm text-novaNeutral bg-white rounded-lg shadow-lg ' +
          'bottom-full right-0 mb-1 ' +
          'md:bottom-auto md:right-auto md:left-full md:top-1/2 md:-translate-y-1/2 md:ml-1 md:mb-0',
        // Mobile: arrow below tooltip pointing down. Desktop: arrow on left of tooltip pointing left
        arrow:
          'absolute top-full right-2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-white ' +
          'md:top-1/2 md:right-auto md:left-0 md:-translate-y-1/2 md:-translate-x-full md:border-l-0 md:border-r-4 md:border-t-4 md:border-b-4 md:border-r-white md:border-t-transparent md:border-b-transparent'
      };
    }
    // Default center position
    return {
      tooltip: 'absolute z-50 w-64 p-2 mt-1 text-sm text-novaNeutral bg-white rounded-lg shadow-lg bottom-full left-1/2 transform -translate-x-1/2',
      arrow: 'absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-white'
    };
  };

  const positionClasses = getPositionClasses();

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
        className="z-50"
      >
        {children}
      </div>
      {isVisible && (
        <div className={positionClasses.tooltip}>
          <div className={positionClasses.arrow}></div>
          {content}
        </div>
      )}
    </div>
  );
}
