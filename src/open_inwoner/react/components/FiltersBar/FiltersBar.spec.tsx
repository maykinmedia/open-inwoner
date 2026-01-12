import '@testing-library/jest-dom';
import { render, fireEvent } from '@testing-library/preact';
import { describe, expect, it } from 'vitest';
import FiltersBar from './FiltersBar';

describe('FiltersBar', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <FiltersBar
        currentUrl="http://localhost:8000/mijn-afval/"
        baseUrl="http://localhost:8000/mijn-afval/"
      />
    );

    expect(
      container.querySelector('.oip-filters-bar--desktop')
    ).toBeInTheDocument();
    expect(
      container.querySelector('.oip-filters-bar--mobile-button')
    ).toBeInTheDocument();
  });

  it('renders desktop and mobile layouts', () => {
    const { container } = render(
      <FiltersBar
        currentUrl="http://localhost:8000/mijn-afval/"
        baseUrl="http://localhost:8000/mijn-afval/"
      />
    );

    const desktopBar = container.querySelector('.oip-filters-bar--desktop');
    const mobileButton = container.querySelector(
      '.oip-filters-bar--mobile-button'
    );
    const form = container.querySelector('.oip-filters-bar__form');

    expect(desktopBar).toBeInTheDocument();
    expect(mobileButton).toBeInTheDocument();
    expect(form).toBeInTheDocument();
  });

  it('shows/hides mobile modal on button click', () => {
    const { container } = render(
      <FiltersBar
        currentUrl="http://localhost:8000/mijn-afval/"
        baseUrl="http://localhost:8000/mijn-afval/"
      />
    );

    const mobileButton = container.querySelector(
      '.oip-filters-bar__open-button'
    );
    expect(mobileButton).toBeInTheDocument();

    // Initially, modal should not be visible
    let backdrop = container.querySelector('.oip-filters-bar__backdrop');
    expect(backdrop).not.toBeInTheDocument();

    // Click to open modal
    fireEvent.click(mobileButton as HTMLElement);
    backdrop = container.querySelector('.oip-filters-bar__backdrop');
    expect(backdrop).toBeInTheDocument();

    // Click close button
    const closeButton = container.querySelector('.oip-filters-bar__close');
    fireEvent.click(closeButton as HTMLElement);
    backdrop = container.querySelector('.oip-filters-bar__backdrop');
    expect(backdrop).not.toBeInTheDocument();
  });

  it('applies correct CSS classes for layout', () => {
    const { container } = render(
      <FiltersBar
        currentUrl="http://localhost:8000/mijn-afval/"
        baseUrl="http://localhost:8000/mijn-afval/"
      />
    );

    const desktopBar = container.querySelector('.oip-filters-bar--desktop');
    const mobileButton = container.querySelector(
      '.oip-filters-bar--mobile-button'
    );
    const form = container.querySelector('.oip-filters-bar__form');

    expect(desktopBar).toHaveClass('oip-filters-bar--desktop');
    expect(mobileButton).toHaveClass('oip-filters-bar--mobile-button');
    expect(form).toHaveClass('form', 'oip-filters-bar__form');
  });

  it('renders filter label text', () => {
    const { container } = render(
      <FiltersBar
        currentUrl="http://localhost:8000/mijn-afval/"
        baseUrl="http://localhost:8000/mijn-afval/"
      />
    );

    const label = container.querySelector('.oip-filters-bar__label');
    expect(label).toHaveTextContent('Filter op:');
  });
});
