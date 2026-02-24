import { render, screen } from '@testing-library/preact';
import { describe, it, expect, vi } from 'vitest';
import clsx from 'clsx';
import { HomePluginCard } from '.';

/**
 * Now uses @nl-design-system-candidate/paragraph-react, which is React-only and incompatible with
 * the Preact + JSDOM test environment.
 *
 * TODO: Refactor this once shadow DOM PR #2310 is merged
 */
vi.mock('@nl-design-system-candidate/paragraph-react', () => ({
  Paragraph: ({ children, className, purpose }: any) => (
    <p
      class={clsx(
        'nl-paragraph',
        purpose === 'lead' ? 'nl-paragraph--lead' : '',
        className
      )}
    >
      {purpose === 'lead' ? (
        <b class="nl-paragraph__lead">{children}</b>
      ) : (
        children
      )}
    </p>
  ),
}));

describe('HomePluginCardItem', () => {
  it('renders without crashing', () => {
    render(<HomePluginCard title="TEST" detailUrl="/" identificatie="101" />);
    expect(screen.getByText('TEST')).toBeInTheDocument();
  });
});
