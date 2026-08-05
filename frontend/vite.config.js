import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var _b;
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    var apiBaseUrl = env.VITE_API_BASE_URL || "";
    var proxyTarget = env.VITE_API_PROXY_TARGET;
    var proxyPath = apiBaseUrl.startsWith("/") ? apiBaseUrl : "";
    return {
        plugins: [react()],
        server: {
            port: 5173,
            proxy: proxyPath && proxyTarget
                ? (_b = {},
                    _b[proxyPath] = {
                        target: proxyTarget,
                        changeOrigin: true,
                        rewrite: function (path) { return path.replace(new RegExp("^".concat(proxyPath)), ""); },
                    },
                    _b) : undefined,
        },
    };
});
