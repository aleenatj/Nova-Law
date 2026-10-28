import React, { useState, useEffect } from 'react';
import MagicSignInForm from './v1/MagicSignInForm';
import PasswordSignInForm from './v1/SignInForm';

const LOGIN_WITH_PASSWORD_STORAGE_KEY = "nova_loginWithPassword";

interface SignInFormProps {
  onClose: () => void;
  onSwitchModal?: (type: "forgot-password" | "reset-password") => void;
  resolveId?: string;
  invalidlink?: boolean;
  email?: string;
  user_id?: string;
}

const SignInForm: React.FC<SignInFormProps> = (props) => {
  const [showPasswordForm, setShowPasswordForm] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(LOGIN_WITH_PASSWORD_STORAGE_KEY) === "true";
    }
    return false;
  });

  useEffect(() => {
    const checkStorage = () => {
      if (typeof window !== "undefined") {
        const stored = localStorage.getItem(LOGIN_WITH_PASSWORD_STORAGE_KEY);
        setShowPasswordForm(stored === "true");
      }
    };

    // Listen for storage events (cross-tab updates)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === LOGIN_WITH_PASSWORD_STORAGE_KEY) {
        setShowPasswordForm(e.newValue === "true");
      }
    };

    // Listen for custom events (same-tab updates)
    const handleCustomEvent = () => {
      checkStorage();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('loginPreferenceChanged', handleCustomEvent);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('loginPreferenceChanged', handleCustomEvent);
    };
  }, []);

  // Force MagicSignInForm when invalidlink is true or user_id is provided
  // because MagicSignInForm is the only form that handles expired links properly
  if (props.invalidlink || props.user_id) {
    return React.createElement(MagicSignInForm, props);
  }

  if (showPasswordForm) {
    return React.createElement(PasswordSignInForm, props);
  }

  return React.createElement(MagicSignInForm, props);
};

export { SignInForm };