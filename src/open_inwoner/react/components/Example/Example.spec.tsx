import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/preact';
import { describe, expect, it } from 'vitest';
import { Example, IExampleDataProps } from '.';

const mockdata: IExampleDataProps[] = [
  {
    title: 'Example Title 1',
    description: 'Example Description 2',
    data_url: '/example',
  },
  {
    title: 'Example Title 2',
    description: 'Example Description 2',
    data_url: '/documents',
  },
];

describe('Example', () => {
  it('renders without crashing', () => {
    render(<Example data={mockdata} />);
    expect(screen.getByText('Example Title 1')).toBeInTheDocument();
    expect(screen.getByText('Example Title 2')).toBeInTheDocument();
  });
});
