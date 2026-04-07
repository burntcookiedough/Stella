import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(frontendRoot, "..");

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
    channel: "msedge",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: "python tests/run_e2e_backend.py",
      cwd: repoRoot,
      env: {
        ...process.env,
        STELLA_E2E_PORT: "8100",
      },
      url: "http://127.0.0.1:8100/readyz",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "node scripts/run_e2e_frontend.mjs",
      cwd: frontendRoot,
      url: "http://127.0.0.1:4173",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
