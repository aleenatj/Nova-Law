import React from "react";
import { SignInForm } from "../signin";
import { ForgotPasswordForm } from "../forgot-password";
import SignupForm from "../SignupForm";
import GlobalModalWrapper from "./GlobalModalWrapper";
import accountSetupBackground from "@/assets/landingpage/accountsetupbackground.webp";

export type ModalType = "signin" | "forgot-password" | "signup";

interface GlobalModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: ModalType;
  onSuccess: () => void;
  resolveId?: string;
  invalidlink?: boolean;
  email?: string;
  user_id?: string;
}

const GlobalModal: React.FC<GlobalModalProps> = ({
  isOpen,
  onClose,
  type,
  onSuccess,
  resolveId,
  invalidlink,
  email,
  user_id,
}) => {
  // const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
  //   if (e.target === e.currentTarget) {
  //     onClose();
  //   }
  // };

  return (
    <GlobalModalWrapper
      isOpen={isOpen}
      className="bg-white rounded-lg shadow-xl max-w-md w-full sm:p-8 p-6 relative max-h-[95vh] overflow-y-auto"
      backdropClassName="bg-black/60"
      backdropStyle={{
        backgroundImage: `url(${accountSetupBackground})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
      onClose={onClose}
    >
      {/* Dynamic Content Based on Type */}
      {type === "signin" && <SignInForm onClose={onClose} resolveId={resolveId} invalidlink={invalidlink} email={email} user_id={user_id} />}
      {type === "forgot-password" && (
        <ForgotPasswordForm onClose={onClose} onSuccess={onSuccess} />
      )}
      {type === "signup" && (
        <SignupForm onClose={onClose} onSuccess={onSuccess} resolveId={resolveId} />
      )}

      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-novaNeutral-400 hover:text-novaNeutral-600 transition-colors"
      >
        <i className="fas fa-times text-xl"></i>
      </button>
    </GlobalModalWrapper>
  );
};
export default GlobalModal;
