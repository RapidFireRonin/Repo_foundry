import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:5274",
  },
  webServer: {
    command: "pnpm run dev",
    url: "http://127.0.0.1:5274/chrono-rift.html",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
