import React, { useEffect } from "react";
import { createPortal } from "react-dom";

interface FullScreenModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

/**
 * FullScreenModal - A simple full-screen modal using React Portal
 * 
 * Features:
 * - Full-screen on mobile, centered modal on desktop
 * - Renders using React Portal to escape parent container constraints
 * - Prevents body scroll when open
 * - High z-index to ensure it's always on top
 * 
 * Usage:
 * ```tsx
 * <FullScreenModal isOpen={isOpen} onClose={onClose}>
 *   <div>Your content here</div>
 * </FullScreenModal>
 * ```
 */
const FullScreenModal: React.FC<FullScreenModalProps> = ({
  isOpen,
  onClose,
  children,
}) => {
  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      className="fixed inset-0 z-[9999] bg-black/80 flex items-start sm:items-center justify-start sm:justify-center p-0 sm:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="relative w-full h-screen sm:h-auto sm:max-w-xl sm:rounded-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Navigation Buttons */}
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4">
          {/* Back Button */}
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors duration-200"
            aria-label="Go back"
          >
            <i className="fas fa-arrow-left h-5 w-5 text-novaNeutral-600" />
          </button>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors duration-200"
            aria-label="Close modal"
          >
            <i className="fas fa-times h-5 w-5 text-novaNeutral-600" />
          </button>
        </div>

        {children}
      </div>
    </div>
  );

  // Render modal at document root level using portal
  return createPortal(modalContent, document.body);
};

export default FullScreenModal;

