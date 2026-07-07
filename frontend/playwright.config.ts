import path from 'node:path'
import { defineConfig, devices } from '@playwright/test'

const port = Number(process.env.PLAYWRIGHT_FRONTEND_PORT || 5173)
const artifactRoot = process.env.PLAYWRIGHT_ARTIFACT_ROOT
  ? path.resolve(process.env.PLAYWRIGHT_ARTIFACT_ROOT)
  : path.resolve('..', '.tmp', 'playwright')

export default defineConfig({
  testDir: './tests/visual',
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: path.join(artifactRoot, 'report'), open: 'never' }]],
  outputDir: path.join(artifactRoot, 'test-results'),
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  webServer: {
    command: `npm run dev -- --host 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'desktop-chrome',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 980 },
      },
    },
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
      },
    },
  ],
})
