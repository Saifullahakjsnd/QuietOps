import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', fullyParallel: false, workers: 1, timeout: 240000,
  expect: {timeout:15000}, reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:3002', browserName: 'chromium', channel:'msedge', viewport:{width:1440,height:1000}, reducedMotion:'reduce', screenshot:'only-on-failure', trace:'retain-on-failure' },
});
