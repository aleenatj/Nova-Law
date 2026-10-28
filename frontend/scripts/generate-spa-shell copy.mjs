import { readFile, writeFile, readdir } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

const publicDir = "dist/public";

/**
 * Generates 200.html — a clean SPA shell for non-prerendered routes.
 *
 * Prerendered pages use entry-server-routing (hydration).
 * SPA routes use 200.html which directly imports our client render function
 * and calls it with { Page: null } so it renders <App /> via createRoot.
 */
async function generateSpaShell() {
  const indexHtml = join(publicDir, "index.html");

  if (!existsSync(indexHtml)) {
    console.log("index.html not found. Skipping SPA shell generation.");
    return;
  }

  const html = await readFile(indexHtml, "utf-8");

  // Extract CSS links from <head>
  const cssLinks = [];
  const cssRegex = /<link rel="stylesheet"[^>]*>/g;
  let match;
  while ((match = cssRegex.exec(html)) !== null) {
    cssLinks.push(match[0]);
  }

  // Find the pages_default.page.client module path from modulepreload links
  const clientModuleMatch = html.match(
    /href="(\/assets\/entries\/pages_default\.page\.client\.[^"]+\.js)"/
  );
  const clientModulePath = clientModuleMatch ? clientModuleMatch[1] : null;

  if (!clientModulePath) {
    // Fallback: scan the assets/entries directory for the file
    const entriesDir = join(publicDir, "assets", "entries");
    if (existsSync(entriesDir)) {
      const entries = await readdir(entriesDir);
      const clientEntry = entries.find(
        (f) =>
          f.startsWith("pages_default.page.client.") && f.endsWith(".js")
      );
      if (clientEntry) {
        const resolvedPath = `/assets/entries/${clientEntry}`;
        console.log(`Found client module via directory scan: ${resolvedPath}`);
        generateHtml(cssLinks, resolvedPath);
        return;
      }
    }
    console.error(
      "Could not find pages_default.page.client module. SPA shell not generated."
    );
    process.exit(1);
  }

  await generateHtml(cssLinks, clientModulePath);
}

async function generateHtml(cssLinks, clientModulePath) {
  // Build a clean SPA shell that directly imports our render function
  // This bypasses vite-plugin-ssr's entry-server-routing/entry-client-routing
  // and simply calls render({ Page: null }) which triggers the SPA <App /> path.
  // Filter out the Font Awesome link from cssLinks — we add it manually below
  // along with all the other head elements from client/index.html
  const appCssLinks = cssLinks.filter(
    (link) => !link.includes("cdnjs.cloudflare.com")
  );

  const spaHtml = `<!DOCTYPE html>
<html lang="en">
  <head>
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
    <script type="text/javascript" id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="4392812d-8bc6-4029-82e1-4b26918fb513" data-blockingmode="auto"></script>
${appCssLinks.map((link) => `    ${link}`).join("\n")}
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
      import { render } from '${clientModulePath}';
      render({ Page: null });
    </script>
  </body>
</html>`;

  const spaShellPath = join("dist/public", "200.html");
  await writeFile(spaShellPath, spaHtml, "utf-8");
  console.log(
    `Generated 200.html SPA shell (client module: ${clientModulePath})`
  );

  // Also generate serve.json for local testing with `npx serve dist/public`
  // This configures `serve` to rewrite unmatched routes to 200.html (SPA fallback)
  // while still serving prerendered HTML files via clean URLs.
  // Note: npx serve cannot handle cleanUrls + rewrites together.
  // Use `npm run serve` (scripts/serve-local.mjs) for local testing.
  // On Amplify, redirects in amplify.yml handle routing correctly.
}

generateSpaShell().catch((err) => {
  console.error("Error generating SPA shell:", err);
  process.exit(1);
});
