import React, { useState, useEffect } from "react";

interface GlobalModalWrapperProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  backdropClassName?: string;
  backdropStyle?: React.CSSProperties;
  disableBackdropClose?: boolean;
}

/**
 * GlobalModalWrapper - A reusable modal wrapper with smart backdrop click handling
 * 
 * Features:
 * - Only closes when both mousedown and mouseup happen on the backdrop
 * - Prevents accidental closes when dragging from inside modal and releasing outside
 * - Customizable styling via className and backdropClassName props
 * 
 * Usage:
 * ```tsx
 * <GlobalModalWrapper isOpen={isOpen} onClose={onClose}>
 *   <div className="bg-white rounded-lg p-6">
 *     Your modal content here
 *   </div>
 * </GlobalModalWrapper>
 * ```
 */
const GlobalModalWrapper: React.FC<GlobalModalWrapperProps> = ({
  isOpen,
  onClose,
  children,
  className = "",
  backdropClassName = "",
  backdropStyle,
  disableBackdropClose = false,
}) => {
  // Track where mouse interaction started to prevent accidental backdrop closes
  const [mouseDownTarget, setMouseDownTarget] = useState<EventTarget | null>(null);

  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      // Save the current scroll position
      const scrollY = window.scrollY;
      // Disable body scroll
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.width = '100%';
      document.body.style.overflow = 'hidden';

      return () => {
        // Re-enable body scroll when modal closes
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        document.body.style.overflow = '';
        // Restore scroll position instantly (no animation)
        // Using behavior: 'instant' prevents smooth scrolling from CSS or browser settings
        window.scrollTo({ top: scrollY, left: 0, behavior: 'instant' });
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Handle backdrop click - only close if both mousedown and mouseup happened on backdrop
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (disableBackdropClose) return;
    if (e.target === e.currentTarget && mouseDownTarget === e.currentTarget) {
      onClose();
    }
    setMouseDownTarget(null); // Reset after click
  };

  // Track where mousedown occurred
  const handleBackdropMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (disableBackdropClose) return;
    if (e.target === e.currentTarget) {
      setMouseDownTarget(e.currentTarget);
    }
  };

  return (
    <div
      className={`fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 ${backdropClassName}`}
      style={backdropStyle}
      onMouseDown={handleBackdropMouseDown}
      onClick={handleBackdropClick}
    >
      <div
        className={className}
        onMouseDown={(e) => e.stopPropagation()} // Prevent backdrop mousedown tracking when clicking inside modal
      >
        {children}
      </div>
    </div>
  );
};

export default GlobalModalWrapper;

