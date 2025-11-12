import { describe, expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import Count from './Count';
import { IntlProvider } from 'react-intl';
import { getIntlProviderProps } from '@react/i18n/i18n';

describe('Count component', () => {
  test('should render the component onto the screen', async () => {
    // Create a new component so we can manupulate the state.
    let count = 0;

    const intlProps = await getIntlProviderProps();

    render(
      <IntlProvider {...intlProps}>
        <Count count={count} />
      </IntlProvider>
    );

    expect(screen.getByTestId('count').textContent).toBe('0');
  });
});
