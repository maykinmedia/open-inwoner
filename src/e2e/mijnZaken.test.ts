import { test, expect, type Page } from '@playwright/test';

test.beforeEach(async ({ context }) => {
  await context.addCookies([
    {
      name: 'cookieBannerAccepted',
      value: 'false',
      url: 'http://localhost:9000',
    },
  ]);
});

async function loginWithDigiD(page: Page) {
  await page.goto('http://localhost:9000/accounts/login/');

  await page.waitForLoadState('networkidle');
  await page.getByRole('link', { name: 'Log in met DigiD' }).click();

  await expect(page.getByText('Sign in to your account')).toBeVisible();
  await page.getByLabel('username').fill('testuser');
  await page.getByLabel('Password', { exact: true }).fill('testuser');
  await page.getByRole('button', { name: 'Sign In' }).click();

  await expect(page).toHaveURL('http://localhost:9000/');
}

async function navigateMijnZaken(page: Page) {
  await page.getByRole('link', { name: 'Mijn zaken' }).click();
  await expect(page).toHaveURL('http://localhost:9000/cases/');
}

const statusFilterCases = [
  { status: 'Openstaande formulieren', expectedCases: [] },
  {
    status: 'Lopende zaken',
    expectedCases: ['TESTZAAK-4be9bb566e66', 'TESTZAAK-db0a5377223b'],
  },
  { status: 'Afgeronde zaken', expectedCases: ['TESTZAAK-313f3a44e729'] },
];

const allCases = statusFilterCases.flatMap(
  ({ expectedCases }) => expectedCases
);

statusFilterCases.forEach(({ status, expectedCases }) => {
  test(`filter "${status}" toont alleen de verwachte zaken`, async ({
    page,
  }) => {
    await loginWithDigiD(page);
    await navigateMijnZaken(page);

    await page.getByRole('button', { name: 'Status' }).click();
    await page.getByText(status).click();
    await page.getByRole('button', { name: 'Toon resultaten' }).click();

    const caseCards = page.getByRole('link', { name: 'Bekijk zaak' });
    await expect(caseCards).toHaveCount(expectedCases.length);

    for (const zaaknummer of allCases) {
      const zaak = page.getByText(zaaknummer);
      if (expectedCases.includes(zaaknummer)) {
        await expect(zaak).toBeVisible();
      } else {
        await expect(zaak).toHaveCount(0);
      }
    }
  });
});
