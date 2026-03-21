import { test, expect } from '@playwright/test';

test.describe('SafecurityAI Critical Flows', () => {

    test.beforeAll(() => {
    });

    test.afterAll(() => {
    });

    test('should visit Analysis, Reports and Suggestions', async ({ page }) => {
        await page.goto('/');
        await expect(page.locator('aside')).toContainText('SAFECURITY.AI');

        // Test Navigation: Go to Reports directly
        await page.getByRole('link', { name: /audit reports/i }).click();
        await expect(page).toHaveURL(/\/reports/);
        await expect(page.getByRole('heading', { name: /forensic reports/i })).toBeVisible();

        // Test Navigation: Go to Suggestions
        await page.getByRole('link', { name: /suggestions/i }).click();
        await expect(page.getByText(/AGENT FEATURE SUGGESTIONS/i)).toBeVisible();
    });

    test('should handle multi-tab PDF opening', async ({ page, context }) => {
        // Scenario: Open an existing report and verify that it opens in a new tab
        await page.goto('/reports');

        // Wait for Backend to load the reports
        const downloadBtn = page.getByRole('button', { name: /download/i }).first();
        await downloadBtn.click();

        // ReportListItem component goes to state 'processing' -> 'Open PDF'
        const openPdfBtn = page.getByRole('button', { name: /open pdf/i });

        // Promise to capture the new tab
        const pagePromise = context.waitForEvent('page');
        await openPdfBtn.click();

        const newTab = await pagePromise;
        await newTab.waitForLoadState();

        // Verify that the new tab has PDF in its title
        expect(await newTab.title()).toContain('.pdf');
    });

    test('should display error recovery UI when backend is unreachable', async ({ page }) => {
        // Intercept API call and force a 500 Internal Server Error
        await page.route('**/api/features', route => {
            route.fulfill({ status: 500, contentType: 'application/json', body: '{"error": "Fatal Error"}' });
        });

        await page.goto('/suggestions');

        // Verify fallback UI and retry mechanism
        await expect(page.getByText(/failed to retrieve suggestions/i)).toBeVisible();

        const retryBtn = page.getByRole('button', { name: /retry connection/i });
        await expect(retryBtn).toBeVisible();
    });

    test('should trigger error recovery UI when analysis WebSocket is unreachable', async ({ page }) => {
        // Intercept navigator API
        await page.addInitScript(() => {
            const OriginalWebSocket = window.WebSocket;
            // Override global WebSocket constructor
            // @ts-expect-error - testing purposes
            window.WebSocket = function (url, protocols) {
                if (url.toString().includes('/analyze')) {
                    // Redirect to a dead port (65534) to force "Connection Refused"
                    return new OriginalWebSocket('ws://127.0.0.1:65534/blackhole', protocols);
                }
                return new OriginalWebSocket(url, protocols);
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
            } as any;
        });

        await page.goto('/');

        // Initiate audit
        await page.getByRole('button', { name: /initiate audit/i }).click();

        // When trying to connect to the dead port, it fails instantly triggering socket.onerror
        const resetBtn = page.getByRole('button', { name: /reset connection/i });
        await expect(resetBtn).toBeVisible();

        // Verify the terminal UI explicitly indicates an error state to the user
        const statusIndicator = page.locator('.text-cyber-error').filter({ hasText: 'error' });
        await expect(statusIndicator).toBeVisible();
    });

    test('should copy suggestion content to clipboard', async ({ page, context }) => {
        // Grant browser permissions required for headless clipboard interaction
        // await context.grantPermissions(['clipboard-read', 'clipboard-write']);

        // Mock clipboard API
        await page.addInitScript(() => {
            let mockClipboard = '';
            Object.defineProperty(navigator, 'clipboard', {
                value: {
                    writeText: async (text) => { mockClipboard = text; },
                    readText: async () => mockClipboard,
                },
                writable: true,
                configurable: true
            });
        });

        await page.goto('/suggestions');

        // Locate first suggestion card and trigger copy action
        const firstCard = page.locator('.group.bg-cyber-card').first();
        await firstCard.waitFor();
        await firstCard.click();

        // Assert clipboard content matches expected template
        const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
        expect(clipboardText).toContain('Feature:');
        expect(clipboardText).toContain('Reason:');

        // Verify visual feedback (Check icon replaces Copy icon)
        const checkIcon = firstCard.locator('svg.text-green-500');
        await expect(checkIcon).toBeVisible();
    });
});     