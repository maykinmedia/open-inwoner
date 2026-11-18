import { test as base, expect, type Page } from '@playwright/test';
import { loginWithDigiD } from './common';

const test = base.extend<{ digidPage: Page }>({
  // Een `page` die al via DigiD is ingelogd.
  digidPage: async ({ page }, use) => {
    await loginWithDigiD(page, 'bsn', 'bsn');
    await use(page);
  },
});

async function navigateMijnProfiel(page: Page) {
  await page.getByRole('button', { name: 'Test' }).click();
  await page.getByRole('link', { name: 'Mijn profiel' }).click();
  await expect(page).toHaveURL('http://localhost:9000/profile/');
}

test('edit user-email', async ({ digidPage: page }) => {
  await navigateMijnProfiel(page);
  await page.getByLabel('Bewerk persoonsgegevens').click();
  await expect(page).toHaveURL('http://localhost:9000/profile/edit/');
  await page.getByRole('textbox', { name: 'E-mailadres' }).fill('test1@gmail.nl');
  await page.getByLabel('Sla wijzigingen op').click();
  await expect(page).toHaveURL('http://localhost:9000/profile/');
  await expect(page.getByText('test1@gmail.nl (voorkeur)')).toBeVisible();
});

test('add another email', async ({ digidPage: page }) => {
  await navigateMijnProfiel(page);
  await page.getByLabel('Bewerk persoonsgegevens').click();
  await expect(page).toHaveURL('http://localhost:9000/profile/edit/');
  await page.getByLabel('Voeg e-mailadres toe').click();
  const inputs = page.getByRole('textbox', { name: 'E-mailadres' });
  await inputs.last().fill('test2@gmail.com');
  const radios = page.getByText('Stel in als voorkeur');
  await radios.nth(1).click();
  await page.getByLabel('Sla wijzigingen op').click();
  await expect(page).toHaveURL('http://localhost:9000/profile/');
  await expect(page.getByText('test2@gmail.com (voorkeur)')).toBeVisible();
});
