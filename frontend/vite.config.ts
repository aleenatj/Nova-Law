import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import ssr from "vite-plugin-ssr/plugin";
import path from "path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  const plugins: any[] = [react()];
  if (mode !== "development") {
    plugins.push(
      ssr({
        prerender: {
          partial: true,
          noExtraDir: true,
        },
      })
    );
  }

  return {
    base: "/",
    plugins,
    root: path.resolve(__dirname, "client"),

    resolve: {
      alias: {
        "@": path.resolve(__dirname, "client/src"),
      },
    },

    server: {
      port: 5000,
      historyApiFallback: true,
    },

    build: {
      outDir: "../dist/public",
      emptyOutDir: true,
      assetsDir: "assets",
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          assetFileNames: (assetInfo) => {
            if (assetInfo.name && assetInfo.name.endsWith(".css")) {
              return "assets/static/[name].[hash][extname]";
            }
            return "assets/static/[name].[hash][extname]";
          },
        },
      },
    },

    define: {
      "import.meta.env.BASE_API_URL": JSON.stringify(env.BASE_API_URL),
      "import.meta.env.CRIB_SHEET_URL": JSON.stringify(env.CRIB_SHEET_URL),
      "import.meta.env.PROFESSIONAL_RESOURCES_URL": JSON.stringify(env.PROFESSIONAL_RESOURCES_URL),
      "import.meta.env.WEBSOCKET_URL": JSON.stringify(env.WEBSOCKET_URL),
      "import.meta.env.PUBLIC_ENV__BASE_API_URL": JSON.stringify(env.BASE_API_URL),
      "import.meta.env.PUBLIC_ENV__CRIB_SHEET_URL": JSON.stringify(env.CRIB_SHEET_URL),
      "import.meta.env.PUBLIC_ENV__PROFESSIONAL_RESOURCES_URL": JSON.stringify(env.PROFESSIONAL_RESOURCES_URL),
      "import.meta.env.PUBLIC_ENV__WEBSOCKET_URL": JSON.stringify(env.WEBSOCKET_URL),
      "import.meta.env.VITE_GTM_ID": JSON.stringify(env.VITE_GTM_ID ?? ""),
      "import.meta.env.VITE_CLARITY_PROJECT_ID": JSON.stringify(env.VITE_CLARITY_PROJECT_ID ?? ""),
    },
  };
});
