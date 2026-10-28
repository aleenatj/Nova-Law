import { createServer } from "http";
import { readFile, stat } from "fs/promises";
import { join, extname } from "path";

const publicDir = join(process.cwd(), "dist", "public");
const port = parseInt(process.argv[2] || "3000", 10);

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".xml": "text/xml; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".webmanifest": "application/manifest+json",
};

async function fileExists(filePath) {
  try {
    const s = await stat(filePath);
    return s.isFile();
  } catch {
    return false;
  }
}

async function serveFile(res, filePath) {
  const content = await readFile(filePath);
  const ext = extname(filePath);
  res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "application/octet-stream" });
  res.end(content);
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${port}`);
    let pathname = decodeURIComponent(url.pathname);

    // Remove trailing slash (except for root)
    if (pathname !== "/" && pathname.endsWith("/")) {
      pathname = pathname.slice(0, -1);
    }

    const filePath = join(publicDir, pathname);

    // 1. Try exact file (for assets, images, etc.)
    if (extname(pathname) && (await fileExists(filePath))) {
      return await serveFile(res, filePath);
    }

    // 2. Try directory index (e.g., / → /index.html)
    if (pathname === "/") {
      const indexPath = join(publicDir, "index.html");
      if (await fileExists(indexPath)) {
        return await serveFile(res, indexPath);
      }
    }

    // 3. Try clean URL (e.g., /privacy-policy → /privacy-policy.html)
    const htmlPath = filePath + ".html";
    if (await fileExists(htmlPath)) {
      return await serveFile(res, htmlPath);
    }

    // 4. SPA fallback → 200.html
    const spaPath = join(publicDir, "200.html");
    if (await fileExists(spaPath)) {
      return await serveFile(res, spaPath);
    }

    // 5. 404
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
  } catch (err) {
    console.error(err);
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Internal server error");
  }
});

server.listen(port, () => {
  console.log(`\n  Local server running at:\n`);
  console.log(`  http://localhost:${port}\n`);
  console.log(`  Static pages → prerendered HTML (cleanUrls)`);
  console.log(`  SPA routes   → 200.html fallback\n`);
});

