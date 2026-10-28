import React, { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { Layout } from "@/components/layout/v1/Layout";
import SetInitialPasswordForm from "@/components/set-initial-password/SetInitialPasswordForm";
import { useModal } from "@/contexts/ModalContext";
import accountSetupBackground from "@/assets/landingpage/accountsetupbackground.webp";

const SetInitialPasswordPage: React.FC = () => {
  const [, setLocation] = useLocation();
  const { openModal } = useModal();
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    // Extract token from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const extractedToken = urlParams.get("token");

    if (extractedToken) {
      setToken(extractedToken);
      setShowModal(true);
    } else {
      // If no token, redirect to home page
      setLocation("/");
    }
    setIsLoading(false);
  }, [setLocation]);

  const handleSuccess = () => {
    // Redirect to home page and open login modal after successful password setup
    setShowModal(false);
    setLocation("/");
    
    // Open login modal after a short delay to allow navigation to complete
    setTimeout(() => {
      openModal("signin");
    }, 100);
  };

  const handleError = () => {
    // Stay on the page when there's an error
    // Error will be shown via toast
  };

  return (
    <>
      {/* Modal */}
      {showModal && (
        <div className="min-h-screen flex items-center justify-center bg-black/40"
        style={{
          backgroundImage: `url(${accountSetupBackground})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}>
          <SetInitialPasswordForm
            token={token || undefined}
            onSuccess={handleSuccess}
            onError={handleError}
          />
        </div>
      )}
    </>
  );
};

export default SetInitialPasswordPage;
