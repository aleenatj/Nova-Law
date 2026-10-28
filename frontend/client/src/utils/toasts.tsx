import React from "react";
import { AlertType, AlertMessage, AlertProps } from "./alerts";
import checkCircleIcon from "@/assets/landingpage/check-circle.svg";
import closeCircleIcon from "@/assets/landingpage/close-circle.svg";

// Global toast state
let toasts: AlertMessage[] = [];
let setToasts: React.Dispatch<React.SetStateAction<AlertMessage[]>> | null =
  null;

// Global toast manager
export const toastManager = {
  setState: (
    stateSetter: React.Dispatch<React.SetStateAction<AlertMessage[]>>
  ) => {
    setToasts = stateSetter;
  },

  addToast: (toast: AlertMessage) => {
    toasts = [...toasts, toast];
    if (setToasts) {
      setToasts(toasts);
    }
  },

  removeToast: (id: string) => {
    toasts = toasts.filter((toast) => toast.id !== id);
    if (setToasts) {
      setToasts(toasts);
    }
  },
};

// Toast icon size (matches previous text-2xl ~24px)
const TOAST_ICON_CLASS = "w-6 h-6 flex-shrink-0";

const TOAST_BOX_SHADOW = "0 1.5px 6px 0 rgba(0,0,0,0.1), 0 4px 24px 0 rgba(0,0,0,0.18)";

// Simple Toast component (mobile minimal, right side only, <50% width)
export function Toast({ alert, onDismiss, hideShadow }: AlertProps & { hideShadow?: boolean }) {
  // Get title color based on type
  const getTitleColor = (type: AlertType) => {
    switch (type) {
      case "success":
        return "text-novaSuccess-500";
      case "error":
        return "text-novaCaution-500";
      case "warning":
        return "text-novaWarning-500";
      case "info":
        return "text-novaPrimary-500";
      default:
        return "text-novaNeutral-700";
    }
  };

  // Get icon based on type (success/error use landing page SVGs; others use Font Awesome)
  const getIcon = (type: AlertType) => {
    switch (type) {
      case "success":
        return <img src={checkCircleIcon} alt="" className={TOAST_ICON_CLASS} aria-hidden />;
      case "error":
        return <img src={closeCircleIcon} alt="" className={TOAST_ICON_CLASS} aria-hidden />;
      case "warning":
        return <i className={`fa-regular fa-triangle-exclamation text-novaWarning-500 text-2xl ${TOAST_ICON_CLASS}`} />;
      case "info":
        return <i className={`fa-regular fa-circle-info text-novaPrimary-500 text-2xl ${TOAST_ICON_CLASS}`} />;
      default:
        return <i className={`fa-regular fa-circle-info text-novaNeutral-500 text-2xl ${TOAST_ICON_CLASS}`} />;
    }
  };

  return (
    <div
      className={`
        bg-white
        rounded-xl
        px-4 py-3
        w-[58vw] max-w-[90vw] min-w-0
        sm:w-[340px] sm:min-w-[340px] sm:max-w-[340px]
        transition-all
        duration-300
        relative
        flex items-start gap-3
        break-words
      `}
      style={{
        boxShadow: hideShadow ? "none" : TOAST_BOX_SHADOW,
      }}
    >
      {/* Icon */}
      <div className="mt-0.5">
        {getIcon(alert.type)}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={`font-medium text-sm sm:text-base ${getTitleColor(alert.type)}`}>
          {alert.title}
        </p>
        <p className="text-sm text-novaNeutral-600 break-words mt-0.5">
          {typeof alert.message === 'string' 
            ? alert.message 
            : typeof alert.message === 'object' && alert.message !== null
              ? (alert.message as any).message || JSON.stringify(alert.message)
              : String(alert.message)
          }
        </p>
      </div>

      {/* Close button */}
      {alert.dismissible && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDismiss(alert.id);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onDismiss(alert.id);
            }
          }}
          className="text-novaBlack/70 -mt-2 rounded-lg -mr-3 hover:text-novaNeutral-600 w-8 h-8 focus:text-novaNeutral-600 text-sm leading-none flex items-center justify-center hover:bg-novaNeutral-100 focus:bg-novaNeutral-100 focus:outline-none transition-colors flex-shrink-0"
          aria-label="Close notification"
          tabIndex={0}
        >
          <i className="fas fa-x" />
        </button>
      )}
    </div>
  );
}

const MAX_VISIBLE_TOASTS = 4;
const STACK_OFFSET_PX = 10;
const SCALE_STEP = 0.02; // 1, 0.98, 0.96, 0.94
const OPACITY_STEP = 0.12; // 1, 0.88, 0.76, 0.64
const PEEK_HEIGHT_PX = 120; // Height of visible top strip for toasts behind

const EXIT_DURATION_MS = 280;
const TOAST_FULL_MAX_HEIGHT = 320;
const PROMOTE_TO_FRONT_MS = 320;

// Stacked toast wrapper - vertical stack at bottom center, first (oldest) on top, latest at back
function StackedToastWrapper({
  alerts,
  onDismiss,
}: {
  alerts: AlertMessage[];
  onDismiss: (id: string) => void;
}) {
  const prevCountRef = React.useRef(alerts.length);
  const justAddedIdRef = React.useRef<string | null>(null);
  const previousFrontIdRef = React.useRef<string | null>(null);
  const previousStackIdsRef = React.useRef<string[]>([]);
  const [exitingIds, setExitingIds] = React.useState<Set<string>>(new Set());

  if (alerts.length > prevCountRef.current) {
    const latest = alerts[alerts.length - 1];
    justAddedIdRef.current = latest?.id ?? null;
  } else if (alerts.length < prevCountRef.current) {
    justAddedIdRef.current = null;
  }
  prevCountRef.current = alerts.length;

  const handleDismiss = React.useCallback(
    (id: string) => {
      setExitingIds((prev) => new Set(prev).add(id));
      setTimeout(() => {
        onDismiss(id);
        setExitingIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      }, EXIT_DURATION_MS);
    },
    [onDismiss]
  );

  // First (oldest) at index 0 = front/top; latest at end = back
  const visibleStack = alerts.slice(-MAX_VISIBLE_TOASTS);
  const frontToast = visibleStack[0];
  const isJustAdded = (id: string) => id === justAddedIdRef.current;

  // Detect toast that just became front (was at index 1, now at 0 after previous front closed)
  const justBecameFrontId =
    frontToast &&
    previousStackIdsRef.current.length > 0 &&
    previousStackIdsRef.current[0] !== frontToast.id &&
    previousStackIdsRef.current.indexOf(frontToast.id) > 0
      ? frontToast.id
      : null;

  React.useEffect(() => {
    previousFrontIdRef.current = frontToast?.id ?? null;
    previousStackIdsRef.current = visibleStack.map((a) => a.id);
  });

  // Auto-close front toast after its duration (same exit animation as manual close)
  React.useEffect(() => {
    if (
      !frontToast ||
      exitingIds.has(frontToast.id) ||
      !frontToast.duration ||
      frontToast.duration <= 0
    ) {
      return;
    }
    const t = setTimeout(() => {
      handleDismiss(frontToast.id);
    }, frontToast.duration);
    return () => clearTimeout(t);
  }, [frontToast?.id, frontToast?.duration, exitingIds, handleDismiss]);

  React.useEffect(() => {
    if (!justAddedIdRef.current) return;
    const t = setTimeout(() => {
      justAddedIdRef.current = null;
    }, 450);
    return () => clearTimeout(t);
  }, [alerts.length]);

  return (
    <div className="fixed bottom-1/2 right-8 z-[9999] flex flex-col-reverse items-center gap-0 w-[58vw] sm:w-[340px] max-w-[90vw]">
      {visibleStack.map((alert, index) => {
        const isFront = index === 0;
        const isExiting = exitingIds.has(alert.id);
        const scale = 1 - index * SCALE_STEP;
        const opacity = isExiting ? 0 : 1 - index * OPACITY_STEP;
        const translateY = isExiting ? -24 : -index * STACK_OFFSET_PX;
        const runEnterAnimation = isJustAdded(alert.id) && !isExiting;
        const runPromoteToFrontAnimation = isFront && alert.id === justBecameFrontId;

        return (
          <div
            key={alert.id}
            className={isExiting ? "toast-exit" : "toast-stack-item"}
            style={{
              transform: `translateY(${translateY}px) scale(${scale})`,
              transformOrigin: "center bottom",
              opacity,
              transition: "transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.35s ease-out",
              zIndex: visibleStack.length - index,
              pointerEvents: isFront && !isExiting ? "auto" : "none",
              marginBottom: index === 0 ? 0 : -(PEEK_HEIGHT_PX - 5),
            }}
          >
            {isFront ? (
              runPromoteToFrontAnimation ? (
                <div
                  className="rounded-xl overflow-visible"
                  style={{ boxShadow: TOAST_BOX_SHADOW }}
                >
                  <div className="toast-promote-to-front">
                    <Toast alert={alert} onDismiss={handleDismiss} hideShadow />
                  </div>
                </div>
              ) : (
                <div className={runEnterAnimation ? "toast-enter" : ""}>
                  <Toast alert={alert} onDismiss={handleDismiss} />
                </div>
              )
            ) : (
              <div
                className="overflow-hidden rounded-t-xl"
                style={{ height: PEEK_HEIGHT_PX }}
              >
                <Toast alert={alert} onDismiss={handleDismiss} />
              </div>
            )}
          </div>
        );
      })}

      <style>{`
        .toast-enter {
          animation: toastEnter 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
        .toast-promote-to-front {
          overflow: hidden;
          max-height: ${PEEK_HEIGHT_PX}px;
          box-sizing: border-box;
          animation: toastPromoteToFront ${PROMOTE_TO_FRONT_MS}ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
        .toast-exit {
          transition: transform ${EXIT_DURATION_MS}ms ease-in, opacity ${EXIT_DURATION_MS}ms ease-in !important;
        }
        @keyframes toastEnter {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.94);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        @keyframes toastPromoteToFront {
          from {
            max-height: ${PEEK_HEIGHT_PX + 48}px;
          }
          to {
            max-height: ${TOAST_FULL_MAX_HEIGHT + 48}px;
          }
        }
      `}</style>
    </div>
  );
}

// Toast container - stacked view showing only the latest toast
export function ToastContainer({
  alerts,
  onDismiss,
}: {
  alerts: AlertMessage[];
  onDismiss: (id: string) => void;
}) {
  if (alerts.length === 0) return null;
  
  return <StackedToastWrapper alerts={alerts} onDismiss={onDismiss} />;
}

// Global toast container that manages its own state - stacked view
export function GlobalToastContainer() {
  const [toastList, setToastList] = React.useState<AlertMessage[]>([]);

  React.useEffect(() => {
    // Connect the global toast manager to this component's state
    toastManager.setState(setToastList);
  }, []);

  if (toastList.length === 0) return null;

  return <StackedToastWrapper alerts={toastList} onDismiss={toastManager.removeToast} />;
}

// Simple toast creators
export function createToast(
  type: AlertType,
  title: string,
  message: string,
  duration = 3000 // 3 seconds
): AlertMessage {
  return {
    id: Date.now().toString(),
    type,
    title,
    message,
    duration: 3000, // 3 seconds
    dismissible: true,
  };
}

export function createSuccessToast(
  title: string,
  message: string,
  duration?: number
) {
  return createToast("success", title, message, duration);
}

export function createErrorToast(
  title: string,
  message: string,
  duration?: number
) {
  return createToast("error", title, message, duration);
}

export function createWarningToast(
  title: string,
  message: string,
  duration?: number
) {
  return createToast("warning", title, message, duration);
}

export function createInfoToast(
  title: string,
  message: string,
  duration?: number
) {
  return createToast("info", title, message, duration);
}

// Common toasts
export const COMMON_TOASTS = {
  SUCCESS: {
    SAVED: createSuccessToast("Success", "Data saved"),
    UPDATED: createSuccessToast("Updated", "Data updated"),
    DELETED: createSuccessToast("Deleted", "Data deleted"),
  },
  ERROR: {
    SAVE_FAILED: createErrorToast("Error", "Failed to save"),
    NETWORK_ERROR: createErrorToast("Network Error", "Check connection"),
  },
  WARNING: {
    UNSAVED_CHANGES: createWarningToast("Warning", "Unsaved changes"),
  },
  INFO: {
    LOADING: createInfoToast("Loading", "Please wait..."),
  },
};
