import { readFile, writeFile, readdir, stat } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

const publicDir = "dist/public";

async function fixHtmlEntries() {
  try {
    if (!existsSync(publicDir)) {
      console.log(`Directory ${publicDir} does not exist. Skipping HTML fix.`);
      return;
    }

    console.log(`Fixing HTML entry points in ${publicDir}...`);

    // Read all HTML files in the public directory
    const files = await readdir(publicDir);
    const htmlFiles = files.filter(file => file.endsWith('.html'));

    let fixedCount = 0;

    for (const htmlFile of htmlFiles) {
      const filePath = join(publicDir, htmlFile);
      let content = await readFile(filePath, 'utf-8');

      // Replace server-routing entry with client-routing entry
      const serverRoutingPattern = /entry-server-routing\.([a-zA-Z0-9_-]+)\.js/g;
      
      // First, find the latest client-routing entry filename from assets
      const assetsDir = join(publicDir, 'assets', 'entries');
      if (existsSync(assetsDir)) {
        const entries = await readdir(assetsDir);
        const clientEntries = entries.filter(f => f.startsWith('entry-client-routing.') && f.endsWith('.js'));
        
        if (clientEntries.length > 0) {
          // Use the latest client-routing entry by modification time
          const clientEntryStats = await Promise.all(
            clientEntries.map(async (f) => {
              const stats = await stat(join(assetsDir, f));
              return { name: f, mtime: stats.mtime };
            })
          );
          const clientEntry = clientEntryStats.sort((a, b) => b.mtime - a.mtime)[0].name;
          
          // Replace any server-routing entry with client-routing entry
          const oldContent = content;
          content = content.replace(
            serverRoutingPattern,
            clientEntry
          );
          
          if (content !== oldContent) {
            await writeFile(filePath, content, 'utf-8');
            console.log(`Fixed ${htmlFile}: replaced server-routing with ${clientEntry}`);
            fixedCount++;
          }
        }
      }
    }

    console.log(`Successfully fixed ${fixedCount} HTML file(s)`);
  } catch (error) {
    console.error("Error fixing HTML entries:", error);
    process.exit(1);
  }
}

fixHtmlEntries();

