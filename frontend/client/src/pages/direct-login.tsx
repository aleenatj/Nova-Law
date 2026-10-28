import { useEffect, useMemo, useState, useRef } from "react";
import { useLocation } from "wouter";
import { api, ApiError, tokenManager } from "@/lib/api";
import { useRole } from "@/contexts/RoleContext";
import { useModal } from "@/contexts/ModalContext";
import { toastManager, createSuccessToast, createErrorToast } from "@/utils/toasts";
import { getAndClearRedirectAfterLogin } from "@/utils/redirectAfterLogin";

interface LoginWithTokenResponse {
  success: boolean;
  message: string;
  data: {
    // Success case
    access_token?: string;
    password_state?: "can_create" | "can_update" | "not_applicable";
    refresh_token?: string;
    token_type?: string;
    user_data?: Record<string, any>;
    redirect_path?: string;
    case?: {
      id: string;
      case_no: string;
      type: string;
      status: string;
    };
    // Failure case
    email?: string;
    case_id?: string | null;
    resolve_id?: string | null;
    user_id?: string;
  };
}

type LoginStatus = "verifying" | "success" | "error";

const DirectLoginPage = () => {
  const [, setLocation] = useLocation();
  const { setCurrentRole, refreshRoleFromStorage } = useRole();
  const { openModal } = useModal();

  const [status, setStatus] = useState<LoginStatus>("verifying");
  const [message, setMessage] = useState("Verifying your account...");
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [responseData, setResponseData] = useState<LoginWithTokenResponse["data"] | null>(null);
  const [resendSuccess, setResendSuccess] = useState(false);
  const loginInProgressRef = useRef(false);

  const tokenFromUrl = useMemo(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const tokenParam = searchParams.get("token");
    if (tokenParam) {
      return decodeURIComponent(tokenParam.replace(/^"|"$/g, ""));
    }

    // Handle custom format /directlogin&&token=%22abc%22
    const href = window.location.href;
    const tokenMatch = href.match(/(?:[?&]|&&)token=([^&]+)/i);
    if (tokenMatch && tokenMatch[1]) {
      const decoded = decodeURIComponent(tokenMatch[1]);
      return decoded.replace(/^"|"$/g, "");
    }

    return null;
  }, []);

  useEffect(() => {
    if (!tokenFromUrl) {
      setStatus("error");
      setMessage("Invalid or missing login token.");
      setErrorDetail("Please use the link from your email or contact support.");
      return;
    }

    // Prevent multiple simultaneous login requests
    if (loginInProgressRef.current) {
      return;
    }

    loginInProgressRef.current = true;
    const controller = new AbortController();
    let isMounted = true;

    const loginWithToken = async () => {
      try {
        setStatus("verifying");
        setMessage("Verifying your account...");

        const response = await api.post<LoginWithTokenResponse>(
          "/v1/auth/login-with-token",
          { token: tokenFromUrl },
          { signal: controller.signal }
        );

        // Store response.data regardless of success or failure
        const responseData = response?.data;
        if (!responseData) {
          throw new Error("Missing data in response.");
        }
        
        // Store responseData in state for access in button handlers
        setResponseData(responseData);

        // Check if the response indicates failure
        if (!response.success) {
          // Handle failure case - redirect to home and open login modal with expired token data
          if (!isMounted) return;
          setLocation("/");
          openModal("signin", undefined, true, responseData.email, responseData.user_id);
          return;
        }

        // Handle success case - responseData contains access_token, refresh_token, etc.
        const loginData = responseData;
        if (!loginData.access_token || !loginData.refresh_token) {
          throw new Error("Missing login tokens in response.");
        }

        tokenManager.setTokens(
          loginData.access_token,
          loginData.refresh_token,
          loginData.token_type ?? "Bearer"
        );

        if (loginData.user_data) {
          localStorage.setItem("user", JSON.stringify(loginData.user_data));
          
          // Store password state
          if (loginData.password_state) {
            localStorage.setItem("password_state", loginData.password_state);
          }
          
          // Store case.id if present in response
          if (loginData.case?.id) {
            sessionStorage.setItem("current_case_id", loginData.case.id);
          }
          
          if (loginData.user_data.role_code) {
            setCurrentRole(
              typeof loginData.user_data.role_code === "string"
                ? loginData.user_data.role_code.toLowerCase()
                : loginData.user_data.role_code
            );
          } else {
            refreshRoleFromStorage();
          }
        } else {
          localStorage.removeItem("user");
          refreshRoleFromStorage();
        }

        if (!isMounted) return;

        setStatus("success");
        setMessage("Account verified. Redirecting...");

        // Priority: 1. Stored redirect URL (localStorage), 2. API redirect_path, 3. Default dashboard
        const storedRedirect = getAndClearRedirectAfterLogin();
        const apiRedirectPath = loginData.redirect_path && typeof loginData.redirect_path === "string"
          ? loginData.redirect_path
          : null;
        const destination = storedRedirect || apiRedirectPath || "/case-dashboard";

        setTimeout(() => {
          setLocation(destination);
        }, 800);
      } catch (error) {
        if (!isMounted) return;

        let friendlyMessage = "Unable to verify your account.";
        let errorData: LoginWithTokenResponse["data"] | null = null;

        // Try to extract response data from ApiError
        if (error instanceof ApiError) {
          try {
            // The ApiError message format is: "400 Bad Request - {responseText}"
            // Extract the response text after the status and status text
            const match = error.message.match(/\d+ \w+(?:\s+\w+)* - (.+)/);
            if (match && match[1]) {
              const responseText = match[1];
              try {
                const errorResponse = JSON.parse(responseText);
                // If the error response has the expected structure with data field
                if (errorResponse && errorResponse.data) {
                  errorData = errorResponse.data;
                  setResponseData(errorData);
                  friendlyMessage = errorResponse.message || friendlyMessage;
                }
              } catch {
                // If not JSON, ignore
              }
            }
          } catch {
            // Ignore parsing errors
          }
        }
        
        // If we have error data with email/user_id, redirect and open modal with expired token data
        if (errorData && (errorData.email || errorData.user_id)) {
          setLocation("/");
          openModal("signin", undefined, true, errorData.email, errorData.user_id);
        } else {
          setLocation("/");
          openModal("signin", undefined, true);
        }
      }
    };

    loginWithToken();

    return () => {
      isMounted = false;
      loginInProgressRef.current = false;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokenFromUrl]); // Functions from context are stable; ref guard prevents duplicate requests

  const handleGoHome = () => {
    setLocation("/");
  };

  const handleResendMagicLink = async () => {
    // Check for the presence of user_id before making the API call
    if (!responseData?.user_id) {
      const errorMessage = "Unable to resend magic link: User information is missing. Please contact support or try again later.";
      toastManager.addToast(
        createErrorToast("Error", errorMessage)
      );
      setErrorDetail(errorMessage);
      return;
    }

    try {
      const payload = {
        user_name: responseData.user_id,
        case_id: responseData?.case_id || null,
      };

      await api.post("/v1/auth/send-login-link", payload);
      
      // Show success toast
      toastManager.addToast(
        createSuccessToast("Success", "Magic link sent successfully!")
      );
      
      // Update UI message and state
      setResendSuccess(true);
      setMessage("Resend magic link is successful");
      setErrorDetail("Please check your email for the new login link.");
    } catch (error) {
      let errorMessage = "Failed to resend magic link. Please try again.";
      
      if (error instanceof ApiError) {
        try {
          const match = error.message.match(/\d+ \w+(?:\s+\w+)* - (.+)/);
          if (match && match[1]) {
            const responseText = match[1];
            try {
              const errorResponse = JSON.parse(responseText);
              errorMessage = errorResponse.message || errorMessage;
            } catch {
              // If not JSON, use default message
            }
          }
        } catch {
          // Ignore parsing errors
        }
      }
      
      // Show error toast
      toastManager.addToast(
        createErrorToast("Error", errorMessage)
      );
      
      setErrorDetail(errorMessage);
    }
  }

  const isError = status === "error";

  return (
    <div className="min-h-screen bg-novaNeutral-50 flex flex-col items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="mx-auto mb-6 w-16 h-16 rounded-full bg-novaPrimary-50 flex items-center justify-center">
          {isError ? (
            resendSuccess ? (
              <svg className="w-8 h-8 text-novaSuccess-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <span className="text-2xl text-novaCaution-600">!</span>
            )
          ) : (
            <div className="w-8 h-8 border-4 border-novaPrimary-500 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
        <h1 className="text-2xl font-semibold text-novaNeutral-900 mb-3">{message}</h1>
        {isError ? (
          <>
            <p className="text-novaNeutral-600 mb-6">{errorDetail}</p>
            <div className="flex flex-col md:flex-row gap-2">
              <button
                onClick={handleGoHome}
                className="px-4 py-2 rounded-full bg-novaPrimary-500 text-white hover:bg-novaPrimary-600 transition-colors w-full"
              >
                Go to Home
              </button>

              {!resendSuccess && responseData?.user_id && (
                <button
                  onClick={handleResendMagicLink}
                  className="px-4 py-2 rounded-full bg-novaPrimary-500 text-white hover:bg-novaPrimary-600 transition-colors w-full"
                >
                  Resend Link
                </button>
              )}
            </div>
            
          </>
        ) : (
          <p className="text-novaNeutral-600">
            This will only take a moment. Please keep this tab open.
          </p>
        )}
      </div>
    </div>
  );
};

export default DirectLoginPage;


