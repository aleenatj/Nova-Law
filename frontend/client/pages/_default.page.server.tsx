import React from "react";
import { renderToString } from "react-dom/server";
import { escapeInject, dangerouslySkipEscape } from "vite-plugin-ssr/server";
import { getTitleForPath, getDescriptionForPath, getImageForPath, escapeHtmlAttr } from "../src/utils/pageTitle";

export { render };
export { prerender };

// Only prerender these specific static routes
function prerender() {
  return [
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
}

// Shared <head> content matching client/index.html
const sharedHead = `
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/nova_logo.png" />
    <link rel="apple-touch-icon" href="/nova_logo.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta
      name="description"
      content="Nova Law pairs advanced AI with award-winning family law experts to guide you through divorce and separation, offering tailored recommendations, private consultations, and secure case collaboration."
    />
    <meta
      name="keywords"
      content="Nova Law, family law, divorce support, legal technology, AI legal assistant, separation guidance, family lawyers, divorce guidance, divorce, novalaw, nova law uk, nova law co uk"
    />
    <title>Nova Law</title>
    <meta property="og:site_name" content="Nova Law" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://novalaw.co.uk/" />
    <meta property="og:title" content="Nova Law | Intelligent Divorce and Separation Guidance" />
    <meta property="og:description" content="Nova combines revolutionary AI with award-winning legal experts to guide you through separation. Start your free assessment today." />
    <meta property="og:image" content="https://novalaw.co.uk/assets/social-share-nova-image.png" />
    <meta property="og:locale" content="en_GB" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Nova Law | Intelligent Divorce and Separation Guidance" />
    <meta name="twitter:description" content="Nova combines revolutionary AI with award-winning legal experts to guide you through separation. Start your free assessment today." />
    <meta name="twitter:image" content="https://novalaw.co.uk/assets/social-share-nova-image.png" />
    <meta name="twitter:site" content="@Novalawuk" />
    <meta name="twitter:image:alt" content="Nova Law - Lighting your path through divorce and separation" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
    <script type="text/javascript" id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="4392812d-8bc6-4029-82e1-4b26918fb513" data-blockingmode="auto"></script>`;

async function render(pageContext: any) {
  const { Page, urlPathname } = pageContext;

  // Per-page meta for document title and social share previews (OG/Twitter)
  const pageTitle = getTitleForPath(urlPathname);
  const pageDescription = getDescriptionForPath(urlPathname);
  const pageImage = getImageForPath(urlPathname);
  const canonicalUrl = `https://novalaw.co.uk${urlPathname === "/" ? "" : urlPathname}`;

  const safeTitle = escapeHtmlAttr(pageTitle);
  const safeDescription = escapeHtmlAttr(pageDescription);
  const safeImage = escapeHtmlAttr(pageImage);
  const safeUrl = escapeHtmlAttr(canonicalUrl);

  let headContent = sharedHead
    .replace("<title>Nova Law</title>", `<title>${safeTitle}</title>`)
    .replace(
      /<meta\s+name="description"\s+content="[^"]*"\s*\/>/,
      `<meta name="description" content="${safeDescription}" />`
    )
    .replace(
      '<meta property="og:url" content="https://novalaw.co.uk/" />',
      `<meta property="og:url" content="${safeUrl}" />`
    )
    .replace(
      /<meta property="og:title" content="[^"]*" \/>/,
      `<meta property="og:title" content="${safeTitle}" />`
    )
    .replace(
      /<meta property="og:description" content="[^"]*" \/>/,
      `<meta property="og:description" content="${safeDescription}" />`
    )
    .replace(
      /<meta name="twitter:title" content="[^"]*" \/>/,
      `<meta name="twitter:title" content="${safeTitle}" />`
    )
    .replace(
      /<meta name="twitter:description" content="[^"]*" \/>/,
      `<meta name="twitter:description" content="${safeDescription}" />`
    )
    .replace(
      /<meta property="og:image" content="[^"]*" \/>/,
      `<meta property="og:image" content="${safeImage}" />`
    )
    .replace(
      /<meta name="twitter:image" content="[^"]*" \/>/,
      `<meta name="twitter:image" content="${safeImage}" />`
    );

  const canonicalTag = `<link rel="canonical" href="${safeUrl}" />`;

  // Only render if Page exists (prerendered route)
  // For non-prerendered routes, return empty shell for SPA fallback
  if (!Page) {
    const documentHtml = escapeInject`<!DOCTYPE html>
<html lang="en">
  <head>${dangerouslySkipEscape(headContent)}
    ${dangerouslySkipEscape(canonicalTag)}
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>`;
    return { documentHtml };
  }

  // Render ONLY Page component - no PageWrapper, no providers, no App
  // This ensures wouter/ModalProvider never run on server
  const pageHtml = renderToString(<Page />);

  const documentHtml = escapeInject`<!DOCTYPE html>
<html lang="en">
  <head>${dangerouslySkipEscape(headContent)}
    ${dangerouslySkipEscape(canonicalTag)}
  </head>
  <body>
    <div id="root">${dangerouslySkipEscape(pageHtml)}</div>
  </body>
</html>`;

  return { documentHtml };
}
