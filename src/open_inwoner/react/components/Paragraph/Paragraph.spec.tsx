import { describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/preact';
import '@testing-library/jest-dom';
import clsx from 'clsx';
import Paragraph from './Paragraph';

/**
 * @nl-design-system-candidate/paragraph-react is React-only and incompatible with
 * the Preact + JSDOM test environment.
 *
 * TODO: Refactor this once shadow DOM PR #2310 is merged
 *
 * For now: Paragraph.tsx renders <slot /> instead of {children} so slotted content is
 * never present in the JSDOM tree, therefore these tests query by class and DOM structure
 * instead of by text content.
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

describe('Paragraph', () => {
  it('renders a paragraph element without crashing', () => {
    const { container } = render(<Paragraph />);
    expect(container.querySelector('p')).toBeInTheDocument();
  });

  it('renders with nl-paragraph class', () => {
    const { container } = render(<Paragraph />);
    expect(container.querySelector('p')).toHaveClass('nl-paragraph');
  });

  it('renders lead paragraph with nl-paragraph--lead class', () => {
    const { container } = render(<Paragraph purpose="lead" />);
    expect(container.querySelector('p')).toHaveClass('nl-paragraph--lead');
  });

  it('renders lead paragraph with bold wrapper element', () => {
    const { container } = render(<Paragraph purpose="lead" />);
    const bold = container.querySelector('b');
    expect(bold).toBeInTheDocument();
    expect(bold).toHaveClass('nl-paragraph__lead');
  });

  it('does not render lead class when purpose is not set', () => {
    const { container } = render(<Paragraph />);
    expect(container.querySelector('p')).not.toHaveClass('nl-paragraph--lead');
  });

  it('applies className alongside the base nl-paragraph class', () => {
    const { container } = render(
      <Paragraph className="nl-paragraph--oip-muted" />
    );
    const p = container.querySelector('p');
    expect(p).toHaveClass('nl-paragraph');
    expect(p).toHaveClass('nl-paragraph--oip-muted');
  });
});
