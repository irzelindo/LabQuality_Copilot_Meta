import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests", workers: 1, fullyParallel: false, timeout: 60000,
  reporter: [["list"], ["json", { outputFile: "test-results/report.json" }]],
  use: { baseURL: "http://127.0.0.1:3100", viewport: { width: 1440, height: 1000 },
         launchOptions: process.env.LQ_BROWSER_EXECUTABLE ? { executablePath: process.env.LQ_BROWSER_EXECUTABLE, args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote"] } : {},
         trace: "retain-on-failure" },
  webServer: [
    { command: "node scripts/e2e-api.cjs", url: "http://127.0.0.1:18000/api/health", timeout: 60000, reuseExistingServer: false },
    { command: "node scripts/start-production.cjs", url: "http://127.0.0.1:3100", timeout: 60000, reuseExistingServer: false,
      env: { PORT: "3100", LQ_WEB_HOST: "127.0.0.1", LQ_API_URL: "http://127.0.0.1:18000" } }
  ]
});
