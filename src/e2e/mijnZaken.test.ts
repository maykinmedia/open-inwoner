import { type Page } from '@playwright/test';
import {
  expect,
  test,
  testUsers,
  type StatusFilter,
  type TestUser,
} from './common';
const scenarios: { name: string; user: TestUser; vestiging?: string }[] = [
  { name: 'bsn (DigiD)', user: testUsers.bsn },
  { name: 'kvk als rechtspersoon', user: testUsers.kvk },
  {
    name: 'kvk met vestiging 000037178598',
    user: testUsers.kvk,
    vestiging: '000037178598',
  },
  {
    name: 'kvk met vestiging 000037178601',
    user: testUsers.kvk,
    vestiging: '000037178601',
  },
  { name: 'vestiging (eHerkenning)', user: testUsers.vestiging },
];

const statusFilters: StatusFilter[] = [
  'Openstaande formulieren',
  'Lopende zaken',
  'Afgeronde zaken',
];

// Alle zaken van alle gebruikers, zodat we ook controleren dat je de zaken
// van een ander níet ziet.
const allCases = [
  ...new Set(
    Object.values(testUsers).flatMap((user: TestUser) => [
      ...Object.values(user.expectedCases).flat(),
      ...Object.values(user.vestigingen ?? {}).flatMap((cases) =>
        Object.values(cases).flat()
      ),
    ])
  ),
];

async function navigateMijnZaken(page: Page) {
  await page.getByRole('link', { name: 'Mijn zaken' }).click();
  await expect(page).toHaveURL('http://localhost:9000/cases/');
}

for (const { name, user, vestiging } of scenarios) {
  test.describe(name, () => {
    test.use({ user, vestiging });

    for (const filterOption of statusFilters) {
      test(`filter "${filterOption}" toont alleen de verwachte zaken`, async ({
        loggedInPage: page,
        expectedCases,
      }) => {
        const expected = expectedCases[filterOption];
        await navigateMijnZaken(page);

        await page.getByRole('button', { name: 'Status' }).click();
        await page.getByText(filterOption, { exact: true }).click();
        await page.getByRole('button', { name: 'Toon resultaten' }).click();

        const caseCards = page.getByRole('link', { name: 'Bekijk zaak' });
        await expect(caseCards).toHaveCount(expected.length);

        for (const zaaknummer of allCases) {
          const zaak = page.getByText(zaaknummer);
          if (expected.includes(zaaknummer)) {
            await expect(zaak).toBeVisible();
          } else {
            await expect(zaak).toHaveCount(0);
          }
        }
      });
    }
  });
}
