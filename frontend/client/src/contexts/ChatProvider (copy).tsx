import { useEffect, useRef, ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface ChatProviderProps {
  children: ReactNode;
}

/**
 * ChatProvider manages dynamic loading of chat widgets based on authentication status.
 * 
 * For guest users: Loads Zapier Interfaces chatbot
 * For authenticated users: Loads 3CX Live Chat
 * 
 * Automatically reacts to login/logout events through AuthContext.
 */
export function ChatProvider({ children }: ChatProviderProps) {
  const { isAuthenticated } = useAuth();
  const zapierScriptRef = useRef<HTMLScriptElement | null>(null);
  const zapierEmbedRef = useRef<HTMLElement | null>(null);
  const zapierA11yObserverRef = useRef<MutationObserver | null>(null);
  const zapierBodyObserverRef = useRef<MutationObserver | null>(null);
  const zapierDebounceRef = useRef(0);
  const zapierIframeTitleSetRef = useRef(false);
  const tcxScriptRef = useRef<HTMLScriptElement | null>(null);
  const tcxSelectorRef = useRef<HTMLElement | null>(null);

  /**
   * Cleans up Zapier chatbot widgets and scripts.
   */
  const cleanupZapier = () => {
    zapierIframeTitleSetRef.current = false;
    if (zapierA11yObserverRef.current) {
      zapierA11yObserverRef.current.disconnect();
      zapierA11yObserverRef.current = null;
    }
    if (zapierBodyObserverRef.current) {
      zapierBodyObserverRef.current.disconnect();
      zapierBodyObserverRef.current = null;
    }
    if (zapierEmbedRef.current) {
      zapierEmbedRef.current.remove();
      zapierEmbedRef.current = null;
    }
    if (zapierScriptRef.current) {
      zapierScriptRef.current.remove();
      zapierScriptRef.current = null;
    }
  };

  /**
   * Cleans up 3CX live chat widgets and scripts.
   */
  const cleanup3CX = () => {
    if (tcxSelectorRef.current) {
      tcxSelectorRef.current.remove();
      tcxSelectorRef.current = null;
    }
    if (tcxScriptRef.current) {
      tcxScriptRef.current.remove();
      tcxScriptRef.current = null;
    }
  };

  /**
   * Applies embed-only fixes (role + aria-label). Very fast, never blocks.
   */
  const applyZapierEmbedFixes = (embed: HTMLElement, fixes: Set<string>) => {
    if (embed.getAttribute("role") !== "complementary") {
      embed.setAttribute("role", "complementary");
      fixes.add("embed-role");
    }
    if (embed.getAttribute("aria-label") !== "Chat support") {
      embed.setAttribute("aria-label", "Chat support");
      fixes.add("embed-aria-label");
    }
  };

  /**
   * Finds iframe with a cheap lookup (direct + one level of shadow), no full tree walk.
   */
  const findZapierIframe = (embed: HTMLElement): HTMLIFrameElement | null => {
    const root = embed.shadowRoot;
    if (!root) return null;
    const direct = root.querySelector("#zapier-chatbot-embed") as HTMLIFrameElement | null;
    if (direct) return direct;
    for (const el of Array.from(root.children)) {
      if (el.shadowRoot) {
        const inChild = el.shadowRoot.querySelector("#zapier-chatbot-embed") as HTMLIFrameElement | null;
        if (inChild) return inChild;
      }
    }
    return null;
  };

  /**
   * Applies accessibility fixes: embed landmark + iframe title.
   * Uses cheap iframe lookup and skips once iframe title is set to avoid main-thread blocking.
   */
  const applyZapierAccessibilityFixes = () => {
    const embed = document.querySelector(
      "zapier-interfaces-chatbot-embed"
    ) as HTMLElement | null;
    if (!embed) return 0;

    const fixes = new Set<string>();
    applyZapierEmbedFixes(embed, fixes);

    if (!zapierIframeTitleSetRef.current && embed.shadowRoot) {
      const iframe = findZapierIframe(embed);
      if (iframe && iframe.getAttribute("title") !== "Chat support") {
        iframe.setAttribute("title", "Chat support");
        zapierIframeTitleSetRef.current = true;
        fixes.add("iframe");
      } else if (!iframe) {
        // Iframe may be nested deeper; run full walk once in next idle to avoid blocking this handler
        const runOnce = () => {
          if (zapierIframeTitleSetRef.current) return;
          const setTitle = (root: DocumentFragment | ShadowRoot): boolean => {
            const el = root.querySelector("#zapier-chatbot-embed") as HTMLIFrameElement | null;
            if (el && el.getAttribute("title") !== "Chat support") {
              el.setAttribute("title", "Chat support");
              zapierIframeTitleSetRef.current = true;
              return true;
            }
            for (const node of Array.from(root.querySelectorAll("*"))) {
              if (node.shadowRoot && setTitle(node.shadowRoot)) return true;
            }
            return false;
          };
          if (embed.shadowRoot) setTitle(embed.shadowRoot);
        };
        if (typeof requestIdleCallback !== "undefined") {
          requestIdleCallback(runOnce, { timeout: 3000 });
        } else {
          setTimeout(runOnce, 0);
        }
      }
    }

    if (fixes.size > 0 && import.meta.env.DEV) {
      console.log("[Zapier a11y] Applied fixes:", Array.from(fixes));
    }
    return fixes.size;
  };

  /**
   * Schedules applyZapierAccessibilityFixes in idle time to avoid blocking the main thread
   * (prevents "setTimeout handler took Xms" violations and keeps the page responsive).
   */
  const scheduleZapierA11yFix = () => {
    if (typeof requestIdleCallback !== "undefined") {
      requestIdleCallback(() => applyZapierAccessibilityFixes(), {
        timeout: 2000,
      });
    } else {
      setTimeout(() => applyZapierAccessibilityFixes(), 0);
    }
  };

  /**
   * Debounced version of the fix: runs at most once per 150ms to avoid running
   * on every mutation and blocking the main thread.
   */
  const debouncedScheduleFix = () => {
    const lastRun = zapierDebounceRef.current;
    const now = Date.now();
    if (now - lastRun < 150) return;
    zapierDebounceRef.current = now;
    scheduleZapierA11yFix();
  };

  /**
   * Sets up MutationObservers to apply accessibility fixes when Zapier chatbot
   * appears. Uses debouncing and idle scheduling to avoid main-thread violations.
   */
  const observeAndFixZapierAccessibility = () => {
    const tryFix = () => applyZapierAccessibilityFixes();

    tryFix();

    const embed = document.querySelector("zapier-interfaces-chatbot-embed");
    if (embed) {
      const observer = new MutationObserver(debouncedScheduleFix);
      observer.observe(embed, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["id", "class"],
      });
      zapierA11yObserverRef.current = observer;
    }

    const bodyObserver = new MutationObserver(() => {
      if (document.querySelector("zapier-interfaces-chatbot-embed")) {
        debouncedScheduleFix();
        if (!zapierA11yObserverRef.current) {
          const el = document.querySelector("zapier-interfaces-chatbot-embed");
          if (el) {
            const obs = new MutationObserver(debouncedScheduleFix);
            obs.observe(el, {
              childList: true,
              subtree: true,
              attributes: true,
              attributeFilter: ["id", "class"],
            });
            zapierA11yObserverRef.current = obs;
          }
        }
      }
    });
    bodyObserver.observe(document.body, { childList: true, subtree: true });
    zapierBodyObserverRef.current = bodyObserver;

    // Retry at fewer intervals; schedule in idle time so setTimeout handler returns quickly
    [500, 1500, 4000].forEach((ms) =>
      setTimeout(() => scheduleZapierA11yFix(), ms)
    );
    const onInteraction = () => scheduleZapierA11yFix();
    document.addEventListener("click", onInteraction, { once: true });
    document.addEventListener("focusin", onInteraction, { once: true });
  };

  /**
   * Loads Zapier Interfaces chatbot for guest users.
   */
  const loadZapierChatbot = () => {
    // Clean up 3CX if it exists
    cleanup3CX();

    // Check if script is already loaded
    if (zapierScriptRef.current) {
      return;
    }

    // Load Zapier script
    const script = document.createElement("script");
    script.type = "module";
    script.src = "https://interfaces.zapier.com/assets/web-components/zapier-interfaces/zapier-interfaces.esm.js";
    script.onerror = () => {
      console.error("Failed to load Zapier Interfaces script");
    };
    document.head.appendChild(script);
    zapierScriptRef.current = script;

    // Add chatbot embed element with landmark for accessibility
    const embed = document.createElement("zapier-interfaces-chatbot-embed");
    embed.setAttribute("is-popup", "true");
    embed.setAttribute("chatbot-id", "clvtwwsbh003e13mmvmf01bw9");
    embed.setAttribute("role", "complementary");
    embed.setAttribute("aria-label", "Chat support");
    document.body.appendChild(embed);
    zapierEmbedRef.current = embed;

    observeAndFixZapierAccessibility();
  };

  /**
   * Loads 3CX Live Chat for authenticated users.
   */
  const load3CXLiveChat = () => {
    // Clean up Zapier if it exists
    cleanupZapier();

    // Check if script is already loaded
    if (tcxScriptRef.current) {
      return;
    }

    // Add call-us-selector element
    const selector = document.createElement("call-us-selector");
    selector.setAttribute("phonesystem-url", "https://1710.3cx.cloud/");
    selector.setAttribute("party", "LiveChat43787");
    document.body.appendChild(selector);
    tcxSelectorRef.current = selector;

    // Load 3CX script
    const script = document.createElement("script");
    script.defer = true;
    script.src = "https://downloads-global.3cx.com/downloads/livechatandtalk/v1/callus.js";
    script.id = "tcx-callus-js";
    script.charset = "utf-8";
    script.onerror = () => {
      console.error("Failed to load 3CX Live Chat script");
    };
    document.body.appendChild(script);
    tcxScriptRef.current = script;
  };

  // Initialize chat widgets based on authentication status
  // Reacts automatically to isAuthenticated changes from AuthContext
  useEffect(() => {
    if (isAuthenticated) {
      load3CXLiveChat();
    } else {
      loadZapierChatbot();
    }

    // Cleanup on unmount
    return () => {
      cleanupZapier();
      cleanup3CX();
    };
  }, [isAuthenticated]);

  return <>{children}</>;
}

