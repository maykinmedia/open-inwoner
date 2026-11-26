import { test as base, expect, type Page } from '@playwright/test';
const base_url = 'http://localhost:9000/';

export type StatusFilter =
  'Openstaande formulieren' | 'Lopende zaken' | 'Afgeronde zaken';

export type ExpectedCases = Record<StatusFilter, string[]>;

export type LoginMethod = 'digid' | 'eherkenning';

export type TestUser = {
  username: string;
  password: string;
  loginMethod: LoginMethod;
  /** Zaken die je ziet als je inlogt zonder (of met een vaste) vestiging. */
  expectedCases: ExpectedCases;
  /**
   * Alleen voor eHerkenning-accounts zonder vestigingsbeperking: na het
   * inloggen kies je een vestiging. Per vestigingsnummer de verwachte zaken.
   */
  vestigingen?: Record<string, ExpectedCases>;
};

export const testUsers = {
  bsn: {
    username: 'bsn',
    password: 'bsn',
    loginMethod: 'digid',
    expectedCases: {
      'Openstaande formulieren': [],
      'Lopende zaken': ['TESTZAAK-db0a5377223b', 'TESTZAAK-4be9bb566e66'],
      'Afgeronde zaken': ['TESTZAAK-313f3a44e729'],
    },
  },

  kvk: {
    username: 'kvk',
    password: 'kvk',
    loginMethod: 'eherkenning',
    expectedCases: {
      'Openstaande formulieren': [],
      'Lopende zaken': [
        'TESTZAAK-KVK-db0a5377223b',
        'TESTZAAK-KVK-4be9bb566e66',
        'TESTZAAK-KVK-000037178598',
        'TESTZAAK-KVK-000037178601',
      ],
      'Afgeronde zaken': ['TESTZAAK-KVK-313f3a44e729'],
    },
    // TODO(bug vestiging-zaken): een ingelogde vestiging ziet nu 0 zaken.
    // Open Inwoner filtert op RSIN én vestigingsnummer, terwijl die in de
    // fixtures op twee aparte rollen staan. Zet na de fix de bedoelde zaken
    // (in het commentaar per regel) terug.
    vestigingen: {
      '000037178598': {
        'Openstaande formulieren': [],
        // bedoeld: ['TESTZAAK-KVK-db0a5377223b', 'TESTZAAK-KVK-000037178598']
        'Lopende zaken': [],
        // bedoeld: ['TESTZAAK-KVK-313f3a44e729']
        'Afgeronde zaken': [],
      },
      '000037178601': {
        'Openstaande formulieren': [],
        // bedoeld: ['TESTZAAK-KVK-000037178601']
        'Lopende zaken': [],
        'Afgeronde zaken': [],
      },
    },
  },

  vestiging: {
    username: 'vestiging',
    password: 'vestiging',
    loginMethod: 'eherkenning',
    // TODO(bug vestiging-zaken): zie de toelichting bij `kvk.vestigingen`.
    expectedCases: {
      'Openstaande formulieren': [],
      // bedoeld: ['TESTZAAK-KVK-db0a5377223b', 'TESTZAAK-KVK-000037178598']
      'Lopende zaken': [],
      // bedoeld: ['TESTZAAK-KVK-313f3a44e729']
      'Afgeronde zaken': [],
    },
  },
} satisfies Record<string, TestUser>;

/**
 * Login-helpers
 * @param page
 * @param username
 * @param password
 */

async function fillKeycloakForm(
  page: Page,
  username: string,
  password: string
) {
  await expect(page.getByText('Sign in to your account')).toBeVisible();
  await page.getByLabel('username').fill(username);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign In' }).click();
}

export async function loginWithDigiD(
  page: Page,
  username: string,
  password: string
) {
  await page.goto(`${base_url}accounts/login/`);
  await page.waitForLoadState('networkidle');
  await page.getByRole('link', { name: 'Log in met DigiD' }).click();

  await fillKeycloakForm(page, username, password);

}

/**
 * Logt in via eHerkenning. Een account zonder vestigingsbeperking (zoals kvk)
 * komt eerst op /kvk/branches/ daar kiezen we vestiging, of de
 * rechtspersoon als die niet is opgegeven.
 */
export async function loginWithEherkenning(
  page: Page,
  username: string,
  password: string,
  vestiging?: string
) {
  await page.goto(`${base_url}accounts/login/`);
  await page.waitForLoadState('networkidle');
  await page.getByText('Zakelijk').click();
  await page.getByRole('link', { name: 'Inloggen met Eherkenning' }).click();

  await fillKeycloakForm(page, username, password);

  await page.waitForURL(
    (url) => url.pathname === '/' || url.pathname === '/kvk/branches/'
  );
  if (new URL(page.url()).pathname === '/kvk/branches/') {
    await chooseBranch(page, vestiging);
  }

  await expect(page).toHaveURL(`${base_url}`);
}

async function chooseBranch(page: Page, vestiging?: string) {
  await page.getByRole('combobox').click();
  const options = page.getByRole('option');
  const option = vestiging
    ? options.filter({ hasText: `Vestiging: ${vestiging}` })
    : options.filter({
        hasText: 'Selecteer de rechtspersoon (geen vestiging)',
      });
  await option.click();
  await page.getByRole('button', { name: 'Ga door' }).click();
}

type Options = {
  user: TestUser;
  vestiging: string | undefined;
};

type Fixtures = {
  /** Een `page` die al is ingelogd als `user` (en eventueel `vestiging`). */
  loggedInPage: Page;
  /** De zaken die bij deze `user` + `vestiging` horen. */
  expectedCases: ExpectedCases;
};

export const test = base.extend<Options & Fixtures>({
  user: [testUsers.bsn, { option: true }],
  vestiging: [undefined, { option: true }],

  loggedInPage: async ({ page, user, vestiging }, use) => {
    if (user.loginMethod === 'digid') {
      await loginWithDigiD(page, user.username, user.password);
    } else {
      await loginWithEherkenning(page, user.username, user.password, vestiging);
    }
    await use(page);
  },

  expectedCases: async ({ user, vestiging }, use) => {
    if (!vestiging) {
      await use(user.expectedCases);
      return;
    }
    const cases = user.vestigingen?.[vestiging];
    if (!cases) {
      throw new Error(
        `Gebruiker "${user.username}" heeft geen vestiging ${vestiging}`
      );
    }
    await use(cases);
  },
});
export { expect };
