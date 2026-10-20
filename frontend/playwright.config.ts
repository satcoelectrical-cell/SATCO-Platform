import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: "http://127.0.0.1:4173", trace: "retain-on-failure" },
  projects: [{ name: "firefox", use: { browserName: "firefox" } }],
  webServer: [
    {
      command: "VITE_API_BASE_URL=http://127.0.0.1:4011 npm run build && node e2e/mock-api.mjs",
      port: 4173,
      reuseExistingServer: false,
    },
  ],
});
