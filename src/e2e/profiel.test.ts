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

async function navigateMijnProfiel(page: Page) {
  await page.getByRole('button', { name: 'Test' }).click();
  await page.getByRole('link', { name: 'Mijn profiel' }).click();
  await expect(page).toHaveURL('http://localhost:9000/profile/');
}

test('edit user-email', async ({ page }) => {
  await loginWithDigiD(page);
  await navigateMijnProfiel(page)
  await page.getByLabel('Bewerk persoonsgegevens').click()
  await expect(page).toHaveURL('http://localhost:9000/profile/edit/');
  await page.getByRole('textbox', { name: 'E-mailadres' }).fill('test1@gmail.nl')
  await page.getByLabel('Sla wijzigingen op').click();;
  await expect(page).toHaveURL('http://localhost:9000/profile/');
  await expect(page.getByText('test1@gmail.nl (voorkeur)')).toBeVisible();
})

test('add another email', async({ page })=> {
  await loginWithDigiD(page);
  await navigateMijnProfiel(page);
  await page.getByLabel('Bewerk persoonsgegevens').click();
  await expect(page).toHaveURL('http://localhost:9000/profile/edit/');
  await page.getByLabel('Voeg e-mailadres toe').click();
  const inputs = page.getByRole('textbox', { name: 'E-mailadres' });
  await inputs.last().fill('test2@gmail.com');
  const radios = page.getByText('Stel in als voorkeur');
  await radios.nth(1).click()
  await page.getByLabel('Sla wijzigingen op').click();
  await expect(page).toHaveURL('http://localhost:9000/profile/');
  await expect(page.getByText('test2@gmail.com (voorkeur)')).toBeVisible();
})



