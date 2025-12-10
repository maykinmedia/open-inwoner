import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import { HomePluginCard } from '.';
import '@testing-library/jest-dom';

describe('HomePluginCardItem', () => {
  it('renders without crashing', () => {
    render(<HomePluginCard title="TEST" detailUrl="/" identificatie="101" />);
    expect(screen.getByText('TEST')).toBeInTheDocument();
  });
});
