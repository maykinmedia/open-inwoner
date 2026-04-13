import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import { HomePluginCard } from '.';

describe('HomePluginCardItem', () => {
  it('renders without crashing', () => {
    render(<HomePluginCard title="TEST" detailUrl="/" identificatie="101" />);
    expect(screen.getByText('TEST')).toBeInTheDocument();
  });
});
