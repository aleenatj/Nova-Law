# Static Page Guide — Nova Law Frontend

This document explains how the static site generation (SSG) pipeline works, how to add a brand-new static page, and how to convert an existing SPA page to a static page.

---

## Table of Contents

1. [How the SSG Pipeline Works](#how-the-ssg-pipeline-works)
2. [Adding a Brand-New Static Page](#adding-a-brand-new-static-page)
3. [Converting an Existing SPA Page to Static](#converting-an-existing-spa-page-to-static)
4. [File Reference](#file-reference)
5. [Important Rules](#important-rules)
6. [Checklist](#checklist)

---

## How the SSG Pipeline Works

When you run `npm run build:ssg`, the following steps execute in order:

```
tsc → vite build → run-prerender.mjs → move-client-files.mjs → generate-spa-shell.mjs
```

1. **`tsc`** — TypeScript type-checking.
2. **`vite build`** — Bundles the app and runs `vite-plugin-ssr` to pre-render routes listed in `_default.page.server.tsx` into static HTML files.
3. **`run-prerender.mjs`** — Additional prerender processing.
4. **`move-client-files.mjs`** — Moves files from `dist/public/client/` to `dist/public/` and strips `/client/` prefixes from `_redirects`.
5. **`generate-spa-shell.mjs`** — Creates `200.html` (the SPA fallback shell for non-static routes).

### Key architecture

- **Static routes** are pre-rendered to individual `.html` files (e.g., `privacy-policy.html`). They are served directly by Amplify and hydrated on the client.
- **SPA routes** (e.g., `/case-dashboard`, `/login`) are served via `200.html` and rendered entirely on the client using React.

---

## Adding a Brand-New Static Page

Suppose you want to add a new static page at the route `/faq`.

### Step 1: Create the page component

Create the page component at `client/src/pages/faq.tsx`:

```tsx
import React from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";
import "@/styles/landingpage.css";

const FaqPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-novaNeutral-50">
      <LandingHeader hidenavs={false} />
      <div className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-8">
            Frequently Asked Questions
          </h1>
          {/* Your content here */}
        </div>
      </div>
      <LandingFooter />
    </div>
  );
};

export default FaqPage;
```

> **Important:** Static pages are rendered on the server during build. Do NOT use `window`, `document`, `localStorage`, or any browser-only APIs directly in the component body. Use `useEffect` for any client-side logic — it only runs after hydration.

### Step 2: Create the page route file

Create `client/pages/faq.page.tsx`:

```tsx
import React from "react";
import FaqPage from "../src/pages/faq";

function Page() {
  return <FaqPage />;
}

export { Page };
```

The filename determines the route: `faq.page.tsx` → `/faq`.

### Step 3: Register the route for pre-rendering

Open `client/pages/_default.page.server.tsx` and add `/faq` to the `prerender()` array:

```tsx
function prerender() {
  return [
    "/",
    "/privacy-policy",
    "/user-agreement",
    "/cookie-policy",
    "/become-a-nova-professional",
    "/support-and-guidance",
    "/payment-and-security",
    "/nova-engage",
    "/faq",               // ← Add here
  ];
}
```

### Step 4: Register the route for client-side hydration

Open `client/pages/_default.page.client.tsx` and add `/faq` to the `STATIC_ROUTES` array:

```tsx
const STATIC_ROUTES = [
  "/",
  "/privacy-policy",
  "/user-agreement",
  "/cookie-policy",
  "/become-a-nova-professional",
  "/support-and-guidance",
  "/payment-and-security",
  "/nova-engage",
  "/faq",               // ← Add here
];
```

### Step 5: Add the redirect rule in `_redirects`

Open `client/public/_redirects` and add the route **above** the `/*` fallback:

```
/faq    /client/faq.html    200
```

> **Note:** Use the `/client/` prefix in the source file. The `move-client-files.mjs` script automatically strips it during the build, so the final `dist/public/_redirects` will have `/faq    /faq.html    200`.

### Step 6: Add the redirect rule in `amplify.yml`

Open `amplify.yml` and add the redirect **above** the `/<*>` fallback:

```yaml
    - source: '/faq'
      target: '/faq.html'
      status: '200'
```

### Step 7: Add to sitemap.xml

Open `client/public/sitemap.xml` and add:

```xml
<url>
  <loc>https://novalaw.co.uk/faq</loc>
  <lastmod>2026-02-20</lastmod>
</url>
```

### Step 8: Build and verify

```bash
npm run build:ssg
```

Verify the output:
- `dist/public/faq.html` exists
- `dist/public/_redirects` contains `/faq    /faq.html    200`
- The HTML contains your rendered page content and a `<link rel="canonical">` tag

---

## Converting an Existing SPA Page to Static

Suppose you have an existing SPA-only page at `/terms-and-conditions` (component at `client/src/pages/terms-and-conditions.tsx`) and want to make it a static page.

### Step 1: Audit the component for SSR compatibility

Open the page component and check for:

- ❌ Direct `window.innerWidth` or `window.location` usage outside `useEffect`
- ❌ `document.getElementById()` or DOM manipulation outside `useEffect`
- ❌ `localStorage` / `sessionStorage` access outside `useEffect`
- ❌ Browser-only APIs like `navigator`, `fetch` in the initial render

**Fix any of these** by moving them inside `useEffect` hooks or using SSR-safe patterns:

| Pattern | SSR-Safe Alternative |
|---------|---------------------|
| `window.innerWidth` check for images | `<picture>` with `<source media="...">` |
| `window.innerWidth` check for background | CSS `@media` query via inline `<style>` |
| `window.location.href` on click | Keep as-is (click handlers only run on client) |
| `useState` + `useEffect` for viewport | CSS media queries or `<picture>` element |

### Step 2: Create the page route file

Create `client/pages/terms-and-conditions.page.tsx`:

```tsx
import React from "react";
import TermsAndConditions from "../src/pages/terms-and-conditions";

function Page() {
  return <TermsAndConditions />;
}

export { Page };
```

### Step 3–7: Same as "Adding a New Static Page"

Follow Steps 3–7 from the section above:

- **Step 3:** Add `/terms-and-conditions` to `prerender()` in `_default.page.server.tsx`
- **Step 4:** Add `/terms-and-conditions` to `STATIC_ROUTES` in `_default.page.client.tsx`
- **Step 5:** Add redirect in `client/public/_redirects`
- **Step 6:** Add redirect in `amplify.yml`
- **Step 7:** Add to `sitemap.xml`

### Step 8: Remove SPA route (if applicable)

If the page was previously routed via `wouter` in `App.tsx`, you can optionally remove it from there. The static route will take priority. However, keeping it won't break anything — it just won't be reached for the static route.

### Step 9: Build and verify

```bash
npm run build:ssg
```

---

## File Reference

| File | Purpose |
|------|---------|
| `client/src/pages/<name>.tsx` | The actual React page component |
| `client/pages/<name>.page.tsx` | vite-plugin-ssr route file — maps URL to component |
| `client/pages/_default.page.server.tsx` | Server-side renderer + `prerender()` route list |
| `client/pages/_default.page.client.tsx` | Client-side hydration + `STATIC_ROUTES` list |
| `client/public/_redirects` | Redirect rules (source file, `/client/` prefixes are stripped at build) |
| `amplify.yml` | AWS Amplify build config + redirect rules |
| `client/public/sitemap.xml` | Sitemap for search engines |
| `client/public/robots.txt` | Crawler directives |
| `scripts/move-client-files.mjs` | Post-build: moves files and strips `/client/` from `_redirects` |
| `scripts/generate-spa-shell.mjs` | Post-build: generates `200.html` SPA fallback |

---

## Important Rules

1. **No browser APIs in render path.** Static pages are rendered on the server at build time. `window`, `document`, `localStorage` do not exist. Use `useEffect` for anything browser-specific.

2. **Route must be registered in 4 places:**
   - `_default.page.server.tsx` → `prerender()` array
   - `_default.page.client.tsx` → `STATIC_ROUTES` array
   - `client/public/_redirects` (with `/client/` prefix)
   - `amplify.yml` → `redirects` section (without `/client/` prefix)

3. **The `_redirects` file uses `/client/` prefixes** in the source. The build script strips them. The `amplify.yml` does NOT use `/client/` prefixes.

4. **SPA fallback must always be last** in both `_redirects` (`/*`) and `amplify.yml` (`/<*>`).

5. **Canonical tags are added automatically** by `_default.page.server.tsx` using the page's URL path.

6. **Filename = route.** `faq.page.tsx` → `/faq`. `privacy-policy.page.tsx` → `/privacy-policy`.

---

## Checklist

Use this checklist when adding or converting a static page:

- [ ] Page component created/audited at `client/src/pages/<name>.tsx`
- [ ] No browser-only APIs in render path (moved to `useEffect`)
- [ ] Route file created at `client/pages/<name>.page.tsx`
- [ ] Route added to `prerender()` in `_default.page.server.tsx`
- [ ] Route added to `STATIC_ROUTES` in `_default.page.client.tsx`
- [ ] Redirect added to `client/public/_redirects` (with `/client/` prefix)
- [ ] Redirect added to `amplify.yml` (without `/client/` prefix)
- [ ] URL added to `client/public/sitemap.xml`
- [ ] `npm run build:ssg` succeeds
- [ ] HTML file exists in `dist/public/<name>.html`
- [ ] Page renders correctly when opened directly

