import { expect, test } from '@playwright/test';
import { createRequire } from 'node:module';

test.setTimeout(120_000);

const require = createRequire(import.meta.url);
const axeScript = require.resolve('axe-core/axe.min.js');

async function expectNoAxeViolations(page) {
    await page.addScriptTag({ path: axeScript });
    const results = await page.evaluate(() => window.axe.run(document));
    expect(results.violations).toEqual([]);
}

test('public home page has no axe violations', async ({ page }) => {
    await page.goto('/');
    await expectNoAxeViolations(page);
});

test('login page has no axe violations', async ({ page }) => {
    await page.goto('/accounts/login/');
    await expectNoAxeViolations(page);
});

test('stakeholder access boundary denies anonymous users', async ({ page }) => {
    const response = await page.goto('/stakeholders/');
    expect([200, 403, 404]).toContain(response?.status());
    if (response?.status() === 200) {
        expect(page.url()).toContain('/accounts/login/');
    }
    await expectNoAxeViolations(page);
});

test('public layout remains usable at mobile and desktop widths', async ({ page }) => {
    for (const width of [375, 768, 1280]) {
        await page.setViewportSize({ width, height: 900 });
        await page.goto('/');
        const layout = await page.evaluate(() => ({
            hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
            activeElementVisible: (() => {
                const element = document.activeElement;
                if (!element || element === document.body) return false;
                const rect = element.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            })()
        }));
        expect(layout.hasHorizontalOverflow).toBe(false);

        const focusable = page.locator(
            "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex='0']"
        );
        const focusableCount = await focusable.count();
        expect(focusableCount).toBeGreaterThan(0);

        for (let index = 0; index < Math.min(3, focusableCount); index += 1) {
            await focusable.nth(index).focus();
            const focusVisible = await page.evaluate(() => {
                const element = document.activeElement;
                if (!element || element === document.body) return false;
                const rect = element.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            });
            expect(focusVisible).toBe(true);
        }
    }
});
