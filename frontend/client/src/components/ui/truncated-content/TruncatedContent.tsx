import React, { useState, useRef, useEffect, useCallback } from "react";

const DEFAULT_CONTENT_CLASS =
  "text-sm text-novaNeutral-900 min-h-[3.5rem] leading-5";
const DEFAULT_BUTTON_CLASS =
  "text-xs text-novaDarkOrange font-normal mt-0 hover:underline focus:outline-none bg-transparent";
// const DEFAULT_MAX_HEIGHT = "5.5rem";

const DEFAULT_SPLIT = /\s*,\s*|\n/;

export interface TruncatedContentProps {
  /** Text to display. Split by comma or newline and shown with space-y-1. Use "N/A" for empty state (no See more will show). */
  content: string;
  /** Class for the content wrapper div */
  contentClassName?: string;
  /** Class for the See more / See less button */
  buttonClassName?: string;
  /** Label when collapsed */
  seeMoreLabel?: string;
  /** Label when expanded */
  seeLessLabel?: string;
  /** Max height when collapsed (e.g. "5.5rem") */
  maxHeightCollapsed?: string;
  /** Separator to split content into items (default: comma and/or newline). Pass false to disable splitting. */
  split?: RegExp | string | false;
  /** When true, show toggle when content is truncated. When false, only vertical scroll is used (no See more/See less). */
  disableSeeMore?: boolean;
}

export const TruncatedContent: React.FC<TruncatedContentProps> = ({
  content,
  contentClassName = DEFAULT_CONTENT_CLASS,
  buttonClassName = DEFAULT_BUTTON_CLASS,
  seeMoreLabel = "... See more",
  seeLessLabel = "See less",
  maxHeightCollapsed,
  split = DEFAULT_SPLIT,
  disableSeeMore = true,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [truncated, setTruncated] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const rawItems =
    split === false
      ? [content]
      : content === "N/A"
        ? ["N/A"]
        : content
            .split(split)
            .map((s) => s.trim())
            .filter(Boolean);
  const items = rawItems.length > 0 ? rawItems : ["N/A"];
  const hasContent = items.length > 0 && items[0] !== "N/A";

  const checkTruncation = useCallback(() => {
    if (!hasContent) {
      setTruncated(false);
      return;
    }
    const el = contentRef.current;
    if (!el || expanded) {
      setTruncated(false);
      return;
    }
    setTruncated(el.scrollHeight > el.clientHeight);
  }, [hasContent, expanded]);

  useEffect(() => {
    const id = setTimeout(checkTruncation, 0);
    return () => clearTimeout(id);
  }, [checkTruncation, content]);

  useEffect(() => {
    window.addEventListener("resize", checkTruncation);
    return () => window.removeEventListener("resize", checkTruncation);
  }, [checkTruncation]);

  const showToggle = hasContent && (truncated || expanded) && !disableSeeMore;

  return (
    <>
      <div
        ref={contentRef}
        className={`space-y-2 ${contentClassName} ${
          !expanded
          ? !disableSeeMore
              ? "overflow-hidden"
              : "overflow-y-auto [scrollbar-width:thin] [&::-webkit-scrollbar]:w-[4px] [&::-webkit-scrollbar-thumb]:bg-novaNeutral-200 [&::-webkit-scrollbar-thumb]:rounded-full pr-2"
            : ""
        }`}
        style={!expanded ? { maxHeight: maxHeightCollapsed } : undefined}
      >
        {items.map((item, i) => (
          <div key={i}>{item}</div>
        ))}
      </div>
      {showToggle && (
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className={buttonClassName}
        >
          {expanded ? seeLessLabel : seeMoreLabel}
        </button>
      )}
    </>
  );
};

export default TruncatedContent;
