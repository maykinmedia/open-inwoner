import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import { HomePluginSection } from '.';
import '@testing-library/jest-dom';

describe('HomePluginSection', () => {
  it('renders without crashing', () => {
    render(<HomePluginSection title="TEST" columns={2} />);
    expect(screen.getByText('TEST')).toBeInTheDocument();
  });
});
