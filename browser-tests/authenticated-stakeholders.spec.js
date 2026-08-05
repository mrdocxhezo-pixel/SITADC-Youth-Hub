import { expect, test } from '@playwright/test';

test.setTimeout(120_000);

test('authenticated stakeholder directory handles repeated and concurrent reads', async ({
    browser
}) => {
    const username = process.env.E2E_USERNAME;
    const password = process.env.E2E_PASSWORD;
    test.skip(!username || !password, 'Set E2E_USERNAME and E2E_PASSWORD to run this test.');

    const context = await browser.newContext();
    try {
        const loginPage = await context.newPage();
        await loginPage.goto('/accounts/login/');
        await loginPage.locator("input[name='username']").fill(username);
        await loginPage.locator("input[name='password']").fill(password);
        await loginPage.locator("button[type='submit']").click();
        await expect(loginPage).not.toHaveURL(/\/accounts\/login\//);

        const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:8000';
        const cookies = await context.cookies();
        const cookieHeader = cookies.map(({ name, value }) => `${name}=${value}`).join('; ');
        const readDirectory = () =>
            fetch(`${baseURL}/stakeholders/directory/`, {
                headers: { Cookie: cookieHeader }
            });

        const repeatedStatuses = [];
        for (let index = 0; index < 50; index += 1) {
            const response = await readDirectory();
            repeatedStatuses.push(response.status);
        }
        expect(repeatedStatuses).toEqual(Array(50).fill(200));

        const concurrentResponses = await Promise.all(
            Array.from({ length: 10 }, () => readDirectory())
        );
        expect(concurrentResponses.map((response) => response.status)).toEqual(Array(10).fill(200));
    } finally {
        await context.close();
    }
});
