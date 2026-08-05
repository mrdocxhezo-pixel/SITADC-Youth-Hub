import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:8000';
const port = new URL(baseURL).port || '8000';

export default defineConfig({
    testDir: './browser-tests',
    fullyParallel: true,
    reporter: 'list',
    use: {
        baseURL,
        trace: 'retain-on-failure',
        ...devices['Desktop Chrome']
    },
    webServer: {
        command: `py -3.13 manage.py runserver 127.0.0.1:${port} --noreload`,
        url: `${baseURL}/`,
        reuseExistingServer: true,
        timeout: 120000
    }
});
