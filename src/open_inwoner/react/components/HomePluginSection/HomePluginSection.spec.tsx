import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import { HomePluginSection } from '.';

describe('HomePluginSection', () => {
  it('renders without crashing', () => {
    render(<HomePluginSection title="TEST" columns={2} />);
    expect(screen.getByText('TEST')).toBeInTheDocument();
  });
});
