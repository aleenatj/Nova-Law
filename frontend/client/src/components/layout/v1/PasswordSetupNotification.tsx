import React, { useState } from "react";
import { FormButton } from "@/utils";
import GlobalModalWrapper from "@/components/modal/GlobalModalWrapper";
import SetInitialPasswordForm from "@/components/set-initial-password/SetInitialPasswordForm";

interface PasswordSetupNotificationProps {
  /** If true, hides the close button (used on profile page) */
  showCloseButton?: boolean;
}

export function PasswordSetupNotification({ showCloseButton = true }: PasswordSetupNotificationProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Check if we should show the notification
  const shouldShow = () => {
    const passwordState = localStorage.getItem("password_state");
    const user = localStorage.getItem("user");
    
    // If close button is hidden (profile page), always show if user can create password
    if (!showCloseButton) {
      return user && passwordState === "can_create";
    }
    
    // For other pages, check if dismissed in this session
    const isDismissedInSession = sessionStorage.getItem("password_notification_dismissed");
    
    // Show notification if user is logged in, can create password, and not dismissed
    return user && passwordState === "can_create" && !isDismissedInSession;
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handlePasswordCreated = () => {
    // Hide the notification and close modal after password is created
    setIsModalOpen(false);
    setIsVisible(false);
  };

  const handleDismiss = () => {
    // Store dismissal in sessionStorage so it hides on all pages except profile
    sessionStorage.setItem("password_notification_dismissed", "true");
    setIsVisible(false);
  };

  if (!shouldShow()) {
    return null;
  }

  // Get first name from localStorage
  const userName = localStorage.getItem("user");
  const firstName = userName ? JSON.parse(userName).first_name || "" : "";

  return (
    <>
      <div className="bg-[#F6CF9B] relative">
        <div className="sm:px-6 px-3 sm:py-3 py-2.5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
            <p className="text-[14px] flex justify-start sm:justify-center w-full">
              <b>Reminder:</b>
              <span className="ml-1 hidden sm:block">
                Please create a password to secure your account{firstName ? `, ${firstName}` : ""}
              </span>
              <span className="ml-1 block sm:hidden">
                Set a password{firstName ? `, ${firstName}` : ""}
              </span>
            </p>
            
            <div className="flex items-center gap-2 shrink-0">
              <FormButton
                variant="primary"
                size="sm"
                onClick={handleOpenModal}
              >
                <i className="fas fa-lock mr-2"></i>
                <span className="whitespace-nowrap">Create Password</span>
              </FormButton>
              
              {showCloseButton && (
                <button
                  onClick={handleDismiss}
                  className="absolute top-2 right-2 sm:relative sm:top-auto sm:right-auto inline-flex items-center p-1.5 sm:p-2 "
                  aria-label="Dismiss notification"
                >
                  <i className="fas fa-times"></i>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Password Modal - Reusing SetInitialPasswordForm */}
      <GlobalModalWrapper
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        backdropClassName="bg-black/60"
      >
        <div className="relative">
          {/* Close Button */}
          <button
            onClick={handleCloseModal}
            className="absolute top-4 right-4 z-10 text-novaNeutral-400 hover:text-novaNeutral-600 transition-colors"
          >
            <i className="fas fa-times text-xl"></i>
          </button>
          
          <SetInitialPasswordForm
            onSuccess={handlePasswordCreated}
          />
        </div>
      </GlobalModalWrapper>
    </>
  );
}

