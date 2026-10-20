import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = process.env.SATCO_GOLDEN_DEMO_BACKEND ?? "http://127.0.0.1:18080";
if (backend !== "http://127.0.0.1:18080") {
  throw new Error("Golden Demo backend must remain on the fixed loopback boundary");
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 15173,
    strictPort: true,
    proxy: {
      "/demo-api": {
        target: backend,
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/demo-api/, ""),
      },
    },
  },
});
