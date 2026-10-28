# Adding Third-Party Resources (CSS, JS, Scripts, SDKs)

This guide explains where to add new third-party resources in the Nova Law frontend, which uses a **SSR + SPA hybrid** architecture powered by `vite-plugin-ssr`.

---

## Architecture Overview

The production build generates two types of HTML:

| Type | Files | How They're Generated |
|---|---|---|
| **Prerendered (static)** | `index.html`, `privacy-policy.html`, `user-agreement.html`, `cookie-policy.html`, `become-a-nova-professional.html`, `support-and-guidance.html`, `payment-and-security.html`, `nova-engage.html` | `client/pages/_default.page.server.tsx` |
| **SPA shell (dynamic)** | `200.html` | `scripts/generate-spa-shell.mjs` |

- **Prerendered pages** are served directly as static HTML and then hydrated on the client.
- **SPA routes** (e.g. `/case-dashboard`, `/signin`) fall back to `200.html`, which bootstraps the React app client-side.
- `client/index.html` is used **only** by the Vite dev server (`npm run dev`) — it does **not** affect production builds.

---

## Where to Add Resources

### 1. CDN Stylesheets (`<link rel="stylesheet">`)

**Example:** Font Awesome, Google Fonts, Bootstrap CSS

Add to **all three** files:

| File | Location | Purpose |
|---|---|---|
| `client/pages/_default.page.server.tsx` | `sharedHead` constant (top of file) | Prerendered static pages |
| `scripts/generate-spa-shell.mjs` | HTML template in `generateHtml()` inside `<head>` | SPA routes (`200.html`) |
| `client/index.html` | Inside `<head>` | Local development only |

**Example — adding a Google Font:**

```tsx
// In _default.page.server.tsx — add inside the sharedHead template literal:
const sharedHead = `
    ...existing tags...
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter&display=swap" />
    ...existing tags...`;
```

```js
// In generate-spa-shell.mjs — add inside the <head> of the HTML template:
const spaHtml = `<!DOCTYPE html>
<html lang="en">
  <head>
    ...existing tags...
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter&display=swap" />
    ...existing tags...
  </head>
  ...
`;
```

```html
<!-- In client/index.html — add inside <head>: -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter&display=swap" />
```

---

### 2. External `<script>` Tags in `<head>`

**Example:** Cookiebot, analytics scripts, consent managers

Add to **all three** files:

| File | Location | Purpose |
|---|---|---|
| `client/pages/_default.page.server.tsx` | `sharedHead` constant | Prerendered static pages |
| `scripts/generate-spa-shell.mjs` | Inside `<head>` of the HTML template | SPA routes (`200.html`) |
| `client/index.html` | Inside `<head>` | Local development only |

---

### 3. Inline `<script>` Tags in `<body>`

**Example:** Live chat widgets, embedded third-party widgets

Add to **all three** files:

| File | Location | Purpose |
|---|---|---|
| `client/pages/_default.page.server.tsx` | Create a constant (e.g. `bodyScript`), place before `</body>` in both render paths | Prerendered static pages |
| `scripts/generate-spa-shell.mjs` | Before `</body>` in the HTML template | SPA routes (`200.html`) |
| `client/index.html` | Before `</body>` | Local development only |

**Example — adding a new widget:**

```tsx
// In _default.page.server.tsx — add a new constant:
const myWidgetScript = `
    <script src="https://example.com/widget.js" async></script>`;

// Then inject it in both render paths (empty shell and full page) before </body>:
//   ${dangerouslySkipEscape(myWidgetScript)}
```

---

### 4. React-Based SDKs / JS Initialization Code

**Example:** Google Tag Manager (via `react-gtm-module`), custom JS SDK setup

Add to **one file** only:

| File | Location | Purpose |
|---|---|---|
| `client/pages/PageWrapper.tsx` | Inside the `useEffect(() => { ... }, [])` hook | Runs after hydration on **both** static and SPA routes |

This is where the following are currently initialized:
- `initializeAutoRefresh()` — session auto-refresh
- `TagManager.initialize()` — Google Tag Manager
- `initializeCookiebotAccessibility()` — Cookiebot accessibility fixes

**Example — adding a new SDK:**

```tsx
// In PageWrapper.tsx:
useEffect(() => {
  // ...existing initializations...

  // Initialize new SDK
  MySDK.init({ apiKey: "..." });
}, []);
```

---

### 5. `<meta>` Tags (SEO, Open Graph, etc.)

Add to **all three** files:

| File | Location |
|---|---|
| `client/pages/_default.page.server.tsx` | `sharedHead` constant |
| `scripts/generate-spa-shell.mjs` | Inside `<head>` of the HTML template |
| `client/index.html` | Inside `<head>` |

---

## Quick Reference Table

| Resource Type | `_default.page.server.tsx` | `generate-spa-shell.mjs` | `PageWrapper.tsx` | `client/index.html` |
|---|---|---|---|---|
| CDN CSS (`<link>`) | ✅ `sharedHead` | ✅ `<head>` template | — | ✅ (dev only) |
| External `<script>` in head | ✅ `sharedHead` | ✅ `<head>` template | — | ✅ (dev only) |
| Inline `<script>` in body | ✅ constant before `</body>` | ✅ before `</body>` | — | ✅ (dev only) |
| React SDK / JS init | — | — | ✅ `useEffect` | — |
| `<meta>` tags | ✅ `sharedHead` | ✅ `<head>` template | — | ✅ (dev only) |

---

## Key Files

| File | Path |
|---|---|
| SSR renderer | `client/pages/_default.page.server.tsx` |
| Client hydration | `client/pages/_default.page.client.tsx` |
| App wrapper + initialization | `client/pages/PageWrapper.tsx` |
| SPA shell generator | `scripts/generate-spa-shell.mjs` |
| Local test server | `scripts/serve-local.mjs` |
| Dev-only HTML | `client/index.html` |
| Build script | `package.json` → `build:ssg` |
| Amplify config | `amplify.yml` |

---

## Adding a New Prerendered (Static) Route

If you need to add a new static page (e.g. `/about-us`):

1. Create `client/pages/about-us.page.tsx` exporting a `Page` component.
2. Add `"/about-us"` to the `prerender()` array in `client/pages/_default.page.server.tsx`.
3. Add `"/about-us"` to the `STATIC_ROUTES` array in `client/pages/_default.page.client.tsx`.
4. Add a redirect rule in `amplify.yml`:
   ```yaml
   - source: '/about-us'
     target: '/about-us.html'
     status: '200'
   ```
5. Add the same redirect in `client/public/_redirects`:
   ```
   /about-us    /client/about-us.html   200
   ```

---

## Local Testing

**Do NOT use `npx serve`** — it cannot handle clean URLs + SPA fallback together.

Use the custom local server instead:

```bash
npm run build:ssg    # Build production files
npm run serve        # Start local server on port 3000
npm run serve 8080   # Or specify a custom port
```

The local server (`scripts/serve-local.mjs`) mirrors Amplify's behaviour:
- `/privacy-policy` → serves `privacy-policy.html` (clean URL)
- `/case-dashboard` → serves `200.html` (SPA fallback)
- `/assets/...` → serves static files directly

---

## Important Notes

- **Always update all three production files** (`_default.page.server.tsx`, `generate-spa-shell.mjs`, `client/index.html`) when adding head/body resources. Missing one means the resource won't load on some pages.
- **`client/index.html` is dev-only** — it has no effect on the production build, but keeping it in sync ensures a consistent dev experience.
- **Never add browser-only code to `_default.page.server.tsx`** — this file runs in Node.js during prerendering. Use SSR guards (`typeof window !== "undefined"`) in components if needed.
- **Rebuild after changes**: `npm run build:ssg` to regenerate all HTML files.

