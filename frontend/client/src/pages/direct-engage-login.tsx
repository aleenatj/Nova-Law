import { useEffect, useMemo, useState, useRef } from "react";
import { useLocation, useParams } from "wouter";
import { api } from "@/lib/api";
import { useModal } from "@/contexts/ModalContext";
import { useAuth } from "@/contexts/AuthContext";

interface VerifyEngageTokenResponse {
  success: boolean;
  message: string;
  data: {
    case_id?: string;
    engage_url?: string;
  };
}

type Status = "verifying" | "success" | "error";

const DirectEngageLoginPage = () => {
  const [, setLocation] = useLocation();
  const params = useParams<{ token?: string }>();
  const { openModal } = useModal();
  const { isAuthenticated } = useAuth();

  const [status, setStatus] = useState<Status>("verifying");
  const [message, setMessage] = useState("Verifying your link...");
  const inProgressRef = useRef(false);

  const tokenFromUrl = useMemo(() => {
    // Token from path: /directengagelogin/<token>
    if (params?.token) {
      return decodeURIComponent(params.token.replace(/^"|"$/g, ""));
    }
    // Token from query: ?token=...
    const searchParams = new URLSearchParams(window.location.search);
    const tokenParam = searchParams.get("token");
    if (tokenParam) {
      return decodeURIComponent(tokenParam.replace(/^"|"$/g, ""));
    }
    return null;
  }, [params?.token]);

  useEffect(() => {
    if (!tokenFromUrl) {
      setStatus("error");
      setMessage("Invalid or missing token.");
      if (isAuthenticated) {
        setLocation("/case-dashboard");
      } else {
        setLocation("/");
        openModal("signin");
      }
      return;
    }

    if (inProgressRef.current) {
      return;
    }

    inProgressRef.current = true;
    const controller = new AbortController();
    let isMounted = true;

    const runFlow = async () => {
      try {
        setStatus("verifying");
        setMessage("Verifying your link...");

        const verifyResponse = await api.post<VerifyEngageTokenResponse>(
          "/v1/auth/verify-engage-token",
          { token: tokenFromUrl },
          { signal: controller.signal }
        );

        if (!verifyResponse?.success || !verifyResponse?.data?.engage_url) {
          if (isMounted) {
            if (isAuthenticated) {
              setLocation("/case-dashboard");
            } else {
              setLocation("/");
              openModal("signin");
            }
          }
          return;
        }

        if (!isMounted) return;

        setStatus("success");
        setMessage("Redirecting to Engage...");

        const engageUrl = verifyResponse.data.engage_url;
        window.location.href = engageUrl;
      } catch {
        if (!isMounted) return;
        if (isAuthenticated) {
          setLocation("/case-dashboard");
        } else {
          setLocation("/");
          openModal("signin");
        }
      }
    };

    runFlow();

    return () => {
      isMounted = false;
      inProgressRef.current = false;
      controller.abort();
    };
  }, [tokenFromUrl, setLocation, openModal, isAuthenticated]);

  return (
    <div className="min-h-screen bg-novaNeutral-50 flex flex-col items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="mx-auto mb-6 w-16 h-16 rounded-full bg-novaPrimary-50 flex items-center justify-center">
          {status === "error" ? (
            <span className="text-2xl text-novaCaution-600">!</span>
          ) : (
            <div className="w-8 h-8 border-4 border-novaPrimary-500 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
        <h1 className="text-2xl font-semibold text-novaNeutral-900 mb-3">{message}</h1>
        {status !== "error" && (
          <p className="text-novaNeutral-600">Please keep this tab open.</p>
        )}
      </div>
    </div>
  );
};

export default DirectEngageLoginPage;
