import React, { useEffect, useState } from "react";
import { useLocation } from "wouter";
import ResetPasswordForm from "@/components/reset-password/v1/ResetPasswordForm";
import accountSetupBackground from "@/assets/landingpage/accountsetupbackground.webp";

const ResetPasswordPage: React.FC = () => {
  const [, setLocation] = useLocation();
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Extract token from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const extractedToken = urlParams.get("token");

    if (extractedToken) {
      setToken(extractedToken);
    } else {
      // If no token, redirect to home page
      setLocation("/");
    }
    setIsLoading(false);
  }, [setLocation]);

  const handleSuccess = () => {
    // Redirect to home page after successful password reset
    setLocation("/");
  };

  const handleClose = () => {
    // Redirect to home page when user cancels
    setLocation("/");
  };

  if (isLoading) {
    return (
      <div 
        className="min-h-screen flex items-center justify-center bg-black/40"
        style={{
          backgroundImage: `url(${accountSetupBackground})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-novaPrimary-500 mx-auto mb-4"></div>
          <p className="text-novaNeutral-600">Loading reset password form...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div 
        className="min-h-screen flex items-center justify-center bg-black/40"
        style={{
          backgroundImage: `url(${accountSetupBackground})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      >
        <div className="text-center">
          <div className="w-16 h-16 bg-novaCaution-100 rounded-xl flex items-center justify-center mx-auto mb-4">
            <i className="fas fa-exclamation-triangle text-novaCaution-600 text-2xl"></i>
          </div>
          <h2 className="text-2xl font-bold text-novaNeutral-900 mb-2">
            Invalid Reset Link
          </h2>
          <p className="text-novaNeutral-600 mb-6">
            This reset link is invalid or has expired.
          </p>
          <button
            onClick={() => setLocation("/")}
            className="px-4 py-2 bg-novaPrimary-500 text-white rounded-lg hover:bg-novaPrimary-600 transition-colors"
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-black/40"
      style={{
        backgroundImage: `url(${accountSetupBackground})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <div className="max-w-md w-full space-y-8">
        <ResetPasswordForm
          onClose={handleClose}
          onSuccess={handleSuccess}
          token={token}
        />
      </div>
    </div>
  );
};

export default ResetPasswordPage;
