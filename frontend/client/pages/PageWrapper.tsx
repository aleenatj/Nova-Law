import React, { useEffect } from "react";
import "../src/index.css";
import { RoleProvider } from "../src/contexts/RoleContext";
import { AuthProvider } from "../src/contexts/AuthContext";
import { ChatProvider } from "../src/contexts/ChatProvider";
import { ModalProvider } from "../src/contexts/ModalContext";
import { WebSocketProvider } from "../src/contexts/WebSocketContext";
import { TimelineProvider } from "../src/contexts/TimelineContext";
import { GlobalToastContainer } from "../src/utils/toasts";
import App from "../src/App";
import { initializeAutoRefresh } from "../src/lib/api";
import TagManager from "react-gtm-module";
import { initializeCookiebotAccessibility } from "../src/utils/cookiebotAccessibility";

export function PageWrapper({ children }: { children?: React.ReactNode }) {
  // Initialize app-wide functionality after hydration
  useEffect(() => {
    // Initialize auto-refresh for existing sessions
    initializeAutoRefresh();
    
    // Initialize Google Tag Manager
    const gtmId = (import.meta.env.VITE_GTM_ID as string | undefined) ?? "";
    if (gtmId) {
      const tagManagerArgs = {
        gtmId,
      };
      TagManager.initialize(tagManagerArgs);
    }
    
    // Initialize Cookiebot accessibility fixes
    initializeCookiebotAccessibility();

    // Microsoft Clarity – official snippet with queue + dynamic project ID from env
    const clarityId = (import.meta.env.VITE_CLARITY_PROJECT_ID as string | undefined) ?? "";
    if (clarityId && !(window as unknown as { clarity?: unknown }).clarity) {
      const script = document.createElement("script");
      script.type = "text/javascript";
      script.textContent = `(function(c,l,a,r,i,t,y){ c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)}; t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i; y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y); })(window, document, "clarity", "script", "${clarityId.replace(/"/g, '\\"')}");`;
      document.head.appendChild(script);
    }
  }, []);

  return (
    <RoleProvider>
      <AuthProvider>
        <ChatProvider>
          <ModalProvider>
            <WebSocketProvider>
              <TimelineProvider>
                {children || <App />}
                <GlobalToastContainer />
              </TimelineProvider>
            </WebSocketProvider>
          </ModalProvider>
        </ChatProvider>
      </AuthProvider>
    </RoleProvider>
  );
}
