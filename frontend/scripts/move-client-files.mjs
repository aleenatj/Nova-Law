import { readdir, copyFile, mkdir, rm, readFile, writeFile } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

const clientDir = "dist/public/client";
const publicDir = "dist/public";

async function copyRecursive(src, dest) {
  const entries = await readdir(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    
    if (entry.isDirectory()) {
      await mkdir(destPath, { recursive: true });
      await copyRecursive(srcPath, destPath);
    } else {
      await copyFile(srcPath, destPath);
    }
  }
}

async function moveFiles() {
  try {
    // Check if client directory exists
    if (!existsSync(clientDir)) {
      console.log(`Directory ${clientDir} does not exist. Skipping file move.`);
      return;
    }

    console.log(`Moving files from ${clientDir} to ${publicDir}...`);

    // Ensure public directory exists
    await mkdir(publicDir, { recursive: true });

    // Copy all files and directories recursively
    await copyRecursive(clientDir, publicDir);

    // Remove the client directory after moving
    await rm(clientDir, { recursive: true, force: true });
    
    // Fix _redirects file to remove /client/ paths
    const redirectsFile = join(publicDir, '_redirects');
    if (existsSync(redirectsFile)) {
      let redirectsContent = await readFile(redirectsFile, 'utf-8');
      const oldContent = redirectsContent;
      // Replace /client/ paths with just /
      redirectsContent = redirectsContent.replace(/\/client\//g, '/');
      if (redirectsContent !== oldContent) {
        await writeFile(redirectsFile, redirectsContent, 'utf-8');
        console.log('Fixed _redirects file: removed /client/ paths');
      }
    }
    
    console.log(`Successfully moved files from ${clientDir} to ${publicDir}`);
  } catch (error) {
    console.error("Error moving files:", error);
    process.exit(1);
  }
}

moveFiles();

