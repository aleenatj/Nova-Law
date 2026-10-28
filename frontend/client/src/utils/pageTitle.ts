/**
 * Single source of truth for document title and social share meta by path.
 * Used by the server (SSR) and client so titles are correct on first paint and after navigation.
 */

/** Default title when no path matches */
const DEFAULT_TITLE = "Nova Law";

/** Default OG/Twitter description for social share previews (homepage and fallback) */
export const DEFAULT_OG_DESCRIPTION =
  "Nova combines revolutionary AI with award-winning legal experts to guide you through separation. Start your free assessment today.";

/** Base URL for OG/Twitter images (no trailing slash). */
const OG_IMAGE_BASE = "https://novalaw.co.uk/assets";

/** Default OG/Twitter image URL (absolute). Used for homepage and any path not in PATH_IMAGES. */
export const DEFAULT_OG_IMAGE_URL = `${OG_IMAGE_BASE}/social-share-nova-image.png`;

/** Per-path OG/Twitter image URL. Each route uses a different share image; add files to client/public/assets/. */
const PATH_IMAGES: Record<string, string> = {
  "/privacy-policy": `${OG_IMAGE_BASE}/privacy-policy.webp`,
  "/user-agreement": `${OG_IMAGE_BASE}/user-agreement.webp`,
  "/contact-us": `${OG_IMAGE_BASE}/contact-us.webp`,
  "/cookie-policy": `${OG_IMAGE_BASE}/cookie-policy.webp`,
  "/become-a-nova-professional": `${OG_IMAGE_BASE}/become-nova-lawyer.webp`,
  "/support-and-guidance": `${OG_IMAGE_BASE}/support-and-guidance.webp`,
  "/payment-and-security": `${OG_IMAGE_BASE}/payment-and-security.webp`,
  "/60-sec-feedback": `${OG_IMAGE_BASE}/60-sec-feedback.webp`,
  "/divorce-options": `${OG_IMAGE_BASE}/landing-page.webp`,
  "/separation-divorce-next-steps": `${OG_IMAGE_BASE}/landing-page.webp`,
};

/** Per-path social share description (optional). Missing paths use DEFAULT_OG_DESCRIPTION. */
const PATH_DESCRIPTIONS: Record<string, string> = {
  "/": DEFAULT_OG_DESCRIPTION,
  "/privacy-policy": "Read Nova Law's privacy policy. We explain how we collect, use and protect your data.",
  "/user-agreement": "Nova Law user agreement and terms of use for our divorce and separation guidance platform.",
  "/contact-us": "Get in touch with Nova Law. Send us a message and we'll get back to you.",
  "/cookie-policy": "How Nova Law uses cookies and similar technologies. Manage your preferences.",
  "/become-a-nova-professional": "Join Nova Law as a family law professional. Offer tailored guidance and grow your practice.",
  "/support-and-guidance": "Support and guidance for your separation journey. Resources and help from Nova Law.",
  "/payment-and-security": "How Nova Law handles payments and keeps your information secure.",
  "/nova-engage": "Nova Engage – share your situation and receive a personalised recommendation from Nova Law.",
  "/60-sec-feedback": "Share quick feedback with Nova Law to help us improve your experience.",
  "/divorce-options":
    "Explore divorce options with Nova Law. Get a clear, personalised recommendation on the best way forward.",
  "/separation-divorce-next-steps":
    "Not sure what to do next in separation or divorce? Take your next steps with Nova Law’s free assessment.",
};

const PATH_TITLES: Record<string, string> = {
  "/": DEFAULT_TITLE,
  "/privacy-policy": "Privacy Policy",
  "/user-agreement": "User Agreement",
  "/contact-us": "Contact Us",
  "/cookie-policy": "Cookie Policy",
  "/case-dashboard": "Case Dashboard",
  "/resolve-dashboard": "Nova Recommendations",
  "/become-a-nova-professional": "Become a Nova Professional",
  "/support-and-guidance": "Support and Guidance",
  "/payment-and-security": "Payment and Security",
  "/60-sec-feedback": "60 Sec Feedback",
  "/nova-engage": "Nova Engage",
  "/organisations": "Organisations",
  "/experts": "Experts",
  "/navigators": "Navigators",
  "/nova-experts": "Nova Experts",
  "/profile": "Profile",
  "/missed-cases": "Missed Cases",
  "/my-matches": "My Matches",
  "/feedback": "Engage Feedback",
  "/divorce-options": "Divorce Options",
  "/separation-divorce-next-steps": "Separation and Divorce Next Steps",
};

/** Match /case/:id — title shows "Nova Case" until case page sets it to case_number from API */
const CASE_DETAIL_REGEX = /^\/case\/[^/]+$/;

/** Match /resolve/:id (e.g. /resolve/15c370b9ef1f14582ef101e7af42aa7d) — title is "Resolve" */
const RESOLVE_DETAIL_REGEX = /^\/resolve\/[^/]+$/;

export function getTitleForPath(pathname: string): string {
  const normalized = pathname.replace(/\/$/, "") || "/";
  if (PATH_TITLES[normalized] !== undefined) {
    return PATH_TITLES[normalized];
  }
  if (CASE_DETAIL_REGEX.test(normalized)) {
    return "Nova Case";
  }
  if (RESOLVE_DETAIL_REGEX.test(normalized)) {
    return "Resolve";
  }
  return DEFAULT_TITLE;
}

/** Description for OG/Twitter share preview by path. Falls back to DEFAULT_OG_DESCRIPTION. */
export function getDescriptionForPath(pathname: string): string {
  const normalized = pathname.replace(/\/$/, "") || "/";
  return PATH_DESCRIPTIONS[normalized] ?? DEFAULT_OG_DESCRIPTION;
}

/** Image URL for OG/Twitter share preview by path. Falls back to DEFAULT_OG_IMAGE_URL. */
export function getImageForPath(pathname: string): string {
  const normalized = pathname.replace(/\/$/, "") || "/";
  return PATH_IMAGES[normalized] ?? DEFAULT_OG_IMAGE_URL;
}

/** Escape for HTML attribute value (e.g. content="...") so & and " are safe. */
export function escapeHtmlAttr(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Format case number for document title (e.g. "YQWCCV3" → "#YQWCCV3") */
export function formatCaseNumberForTitle(caseNumber: string | null | undefined): string {
  if (!caseNumber?.trim()) return "Nova Case";
  const ref = caseNumber.trim();
  const refDisplay = ref.startsWith("#") ? ref : `#${ref}`;
  return `Nova Case - ${refDisplay}`;
}
