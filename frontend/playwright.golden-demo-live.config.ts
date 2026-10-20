import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e-live",
  timeout: 60_000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:15173",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "webkit", use: { browserName: "webkit" } },
    { name: "firefox", use: { browserName: "firefox" } },
  ],
});
