import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = env.VITE_API_BASE_URL || "";
  const proxyTarget = env.VITE_API_PROXY_TARGET;
  const proxyPath = apiBaseUrl.startsWith("/") ? apiBaseUrl : "";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy:
        proxyPath && proxyTarget
          ? {
              [proxyPath]: {
                target: proxyTarget,
                changeOrigin: true,
                rewrite: (path) => path.replace(new RegExp(`^${proxyPath}`), ""),
              },
            }
          : undefined,
    },
  };
});
