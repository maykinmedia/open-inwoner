import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/preact';
import { describe, expect, it } from 'vitest';
import FilterTag from './FilterTag';

describe('FilterTag', () => {
  it('renders null when no filters are in URL', () => {
    const { container } = render(
      <FilterTag currentUrl="http://localhost:8000/mijn-afval/" />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders filter tags from URL parameters', () => {
    render(
      <FilterTag currentUrl="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A&type-container=GFT" />
    );

    expect(screen.getByText('Hoofdweg 45A')).toBeInTheDocument();
    expect(screen.getByText('GFT')).toBeInTheDocument();
  });

  it('renders multiple values for the same parameter', () => {
    render(
      <FilterTag currentUrl="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A&adres=Kerkstraat%2012" />
    );

    expect(screen.getByText('Hoofdweg 45A')).toBeInTheDocument();
    expect(screen.getByText('Kerkstraat 12')).toBeInTheDocument();
  });

  it('skips query parameter', () => {
    render(
      <FilterTag currentUrl="http://localhost:8000/mijn-afval/?query=test&adres=Hoofdweg%2045A" />
    );

    expect(screen.getByText('Hoofdweg 45A')).toBeInTheDocument();
    expect(screen.queryByText('test')).not.toBeInTheDocument();
  });

  it('renders with proper semantic structure', () => {
    const { container } = render(
      <FilterTag currentUrl="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A" />
    );

    const tagContainer = container.querySelector('.oip-filter-tags');
    const tagButton = container.querySelector('.oip-filter-tag');
    const tagLabel = container.querySelector('.oip-filter-tag__label');

    expect(tagContainer).toBeInTheDocument();
    expect(tagButton).toBeInTheDocument();
    expect(tagLabel).toBeInTheDocument();
    expect(tagLabel).toHaveTextContent('Hoofdweg 45A');
  });

  it('renders MaterialIcon for close button', () => {
    const { container } = render(
      <FilterTag currentUrl="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A" />
    );

    const icon = container.querySelector('.oip-filter-tag__close');
    expect(icon).toBeInTheDocument();
  });
});
