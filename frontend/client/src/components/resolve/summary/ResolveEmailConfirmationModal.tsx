import React, { useEffect, useState } from "react";
import { useLocation } from "wouter";
import GlobalModalWrapper from "@/components/modal/GlobalModalWrapper";
import { FormButton } from "@/utils";
import accountSetupBackground from "@/assets/landingpage/accountsetupbackground.webp";
import Diamond from "@/assets/landingpage/intersection.svg";

// Session Storage Keys
const RESOLVE_SESSION_KEY = "resolve_session_data";
const RESOLVE_ID_KEY = "resolveId";

interface ResolveEmailConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  resolveId?: string | null;
  onSendLink?: (email: string) => Promise<void> | void;
  isLoginLinkSent?: boolean;
  email?: string | null;
}

const ResolveEmailConfirmationModal: React.FC<ResolveEmailConfirmationModalProps> = ({
  isOpen,
  onClose,
  resolveId,
  onSendLink,
  isLoginLinkSent = false,
  email,
}) => {
  const [, setLocation] = useLocation();
  const [timer, setTimer] = useState(30);
  
  // Get first name from resolve session data
  const firstName = (() => {
    try {
      const sessionData = sessionStorage.getItem(RESOLVE_SESSION_KEY);
      if (sessionData) {
        const parsed = JSON.parse(sessionData);
        return parsed?.question_data?.["1"]?.answer?.[0]?.value || "User";
      }
    } catch {}
    return "User";
  })();

  // Clear session storage
  const clearResolveSession = () => {
    try {
      sessionStorage.removeItem(RESOLVE_SESSION_KEY);
      sessionStorage.removeItem(RESOLVE_ID_KEY);
    } catch (error) {
      console.warn("Failed to clear resolve session storage:", error);
    }
  };

  // Clear resolve session when login link is sent
  useEffect(() => {
    if (isLoginLinkSent) {
      clearResolveSession();
    }
  }, [isLoginLinkSent]);

  // Timer countdown when login link is sent
  useEffect(() => {
    if (isLoginLinkSent && isOpen) {
      setTimer(30); // Reset timer when modal opens with login link sent
      
      const interval = setInterval(() => {
        setTimer((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            window.location.href = "/";
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isLoginLinkSent, isOpen]);

  const handleContinue = () => {

    // Redirect to stored path if available
    const redirectPath = localStorage.getItem("redirect_path");
    if (redirectPath) {
      localStorage.removeItem("redirect_path");
      setLocation(redirectPath);
    }
    else {
      setLocation("/case-dashboard");
    }
    clearResolveSession();
  };

  return (
    <GlobalModalWrapper
      isOpen={isOpen}
      className="w-full max-w-xl bg-white sm:border-[18px] border-[10px] rounded-[27px] p-8 relative border-[#ffc9a9] my-8"
      backdropClassName="bg-black/40 !items-start sm:items-center overflow-y-auto"
      backdropStyle={{
        backgroundImage: `url(${accountSetupBackground})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
      disableBackdropClose
      onClose={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center"
        aria-label="Close modal"
      >
        <i className="fa-solid fa-xmark text-novaNeutral-300 hover:text-novaNeutral-600 transition-colors"></i>
      </button>

      <div className="text-center">
        <h2 className="text-[40px] md:text-[52px] font-nineties text-novaNeutral-900 leading-[1.2] sm:w-[80%] w-full mx-auto">
          Your next steps with Nova
        </h2>

        {isLoginLinkSent ? (
          <>
          <div className="flex flex-col gap-4 mt-8 border-l border-novaBlack pl-8 pt-3 ml-6">
            <div className="text-[16px] font-roman max-w-md mx-auto text-left">
              <span className="border-b border-novaBlack/10 absolute mt-[10px]" style={{ width: 46, left: "7%" }}></span>
              <img src={Diamond} alt="Diamond" className="absolute left-[42px] w-[30px] h-[30px] mt-[-4px]" />
              An account is already registered on Nova with {email ? `${email},` : "this email,"} and an active matter is currently linked to it. For your convenience, a secure login email has been sent to {email || "this address"}. Please check your inbox to access your account and continue your progress.
            </div>
            <div className="text-[16px] font-roman max-w-md mx-auto text-left">
              <span className="border-b border-novaBlack/10 absolute mt-[10px]" style={{ width: 36, left: "8%" }}></span>
              <img src={Diamond} alt="Diamond" className="absolute left-[42px] w-[30px] h-[30px] mt-[-4px]" />
              If you’ve already completed onboarding, we’ll archive the newly submitted form so you can continue seamlessly with your existing matter.
            </div>
          </div>
          
          {/* Progress bar timer */}
          <div className="mt-8 w-full">
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#9A00D2] to-[#F41471] transition-all duration-1000 ease-linear"
                style={{ width: `${(timer / 30) * 100}%` }}
              />
            </div>
            <div className="text-center mt-2 text-sm text-gray-600">
              Redirecting to home in {timer} seconds
            </div>
          </div>
          </>
        ) : (
          <>
            <div className="flex flex-col gap-4 mt-8 border-l border-novaBlack pl-9 pt-3 pb-3 ml-6">
              <div className="text-[16px] font-roman max-w-md mx-auto text-left">
                <span className="border-b border-novaBlack/10 absolute mt-[10px]" style={{ width: 46, left: "7%" }}></span>
                <img src={Diamond} alt="Diamond" className="absolute left-[42px] w-[30px] h-[30px] mt-[-4px]" />
                You’re almost ready to connect with a regulated family professional.
             </div>
              <div className="text-[16px] font-roman max-w-md mx-auto text-left">
                <span className="border-b border-novaBlack/10 absolute mt-[10px]" style={{ width: 36, left: "8%" }}></span>
                <img src={Diamond} alt="Diamond" className="absolute left-[42px] w-[30px] h-[30px] mt-[-4px]" />
                Before that, we’ll take a moment to complete a short alignment check.
                This helps us match you with a professional who’s available to support you.
                It takes just a few minutes.
              </div>
              <div className="text-[16px] font-roman max-w-md text-left">
                <span className="border-b border-novaBlack/10 absolute mt-[10px]" style={{ width: 36, left: "8%" }}></span>
                <img src={Diamond} alt="Diamond" className="absolute left-[42px] w-[30px] h-[30px] mt-[-4px]" />
                You can continue when you’re ready.
              </div>
            </div>

            <FormButton
              type="button"
              variant="primary"
              size="lg"
              onClick={handleContinue}
              className="px-4 mt-6 hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471] text-[24px] focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
            >
              Continue <i className="fa-solid fa-arrow-right ml-2"></i>
            </FormButton>
          </>
        )}
      </div>
    </GlobalModalWrapper>
  );
};

export default ResolveEmailConfirmationModal;
