import React from "react";
import { hydrateRoot, createRoot } from "react-dom/client";
import { PageWrapper } from "./PageWrapper";
import App from "../src/App";

export { render };

// Routes that are prerendered as static HTML
const STATIC_ROUTES = [
  "/",
  "/privacy-policy",
  "/user-agreement",
  "/contact-us",
  "/cookie-policy",
  "/become-a-nova-professional",
  "/support-and-guidance",
  "/payment-and-security",
  "/nova-engage",
  "/60-sec-feedback",
  "/divorce-options",
  "/separation-divorce-next-steps",
];

function render(pageContext: any) {
  const { Page } = pageContext;
  const root = document.getElementById("root");
  if (!root) throw new Error("Root not found");

  // Check the ACTUAL browser URL, not the embedded pageContext.
  // When SPA routes fall back to index.html (or 200.html),
  // the pageContext may say "/" but the URL is e.g. "/case-dashboard".
  const currentPath = window.location.pathname;
  const isStaticRoute = STATIC_ROUTES.includes(currentPath);

  if (isStaticRoute && Page && root.innerHTML.trim()) {
    // Static prerendered route: hydrate the server-rendered HTML
    hydrateRoot(root, <PageWrapper><Page /></PageWrapper>);
  } else {
    // SPA route: clear any stale HTML and render the full App
    root.innerHTML = "";
    createRoot(root).render(<PageWrapper><App /></PageWrapper>);
  }
}
