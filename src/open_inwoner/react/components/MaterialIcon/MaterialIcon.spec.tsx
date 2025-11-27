import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import { MaterialIcon } from '.';

// Import jest-dom matchers for extended assertions like toBeInTheDocument
import '@testing-library/jest-dom';

describe('MaterialIcon', () => {
  it('renders without crashing', () => {
    render(<MaterialIcon name="mail" />);
    expect(screen.getByText('mail')).toBeInTheDocument();
  });

  it('renders the correct icon name', () => {
    render(<MaterialIcon name="home" />);

    const iconElement = screen.getByText('home');
    expect(iconElement).toBeInTheDocument();
    expect(iconElement).toHaveClass('material-icons-outlined');
  });

  it('has aria-hidden attribute for accessibility', () => {
    render(<MaterialIcon name="star" />);

    const iconElement = screen.getByText('star');
    expect(iconElement).toHaveAttribute('aria-hidden', 'true');
  });

  it('renders different icon names correctly', () => {
    const { rerender } = render(<MaterialIcon name="search" />);
    expect(screen.getByText('search')).toBeInTheDocument();

    rerender(<MaterialIcon name="favorite" />);
    expect(screen.getByText('favorite')).toBeInTheDocument();
    expect(screen.queryByText('search')).not.toBeInTheDocument();
  });

  it('renders as a span element', () => {
    render(<MaterialIcon name="menu" />);

    const iconElement = screen.getByText('menu');
    expect(iconElement.tagName).toBe('SPAN');
  });

  it('renders multiple icons independently', () => {
    render(
      <div>
        <MaterialIcon name="mail" />
        <MaterialIcon name="euro" />
      </div>
    );

    expect(screen.getByText('mail')).toBeInTheDocument();
    expect(screen.getByText('euro')).toBeInTheDocument();
  });
});
