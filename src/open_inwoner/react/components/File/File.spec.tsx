import { vi, describe, expect, it, beforeEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/preact';
import File from './File';
import '@testing-library/jest-dom';

// Mock useIntl hook to avoid IntlProvider compatibility issues with Preact
vi.mock('react-intl', () => ({
  useIntl: () => ({
    formatMessage: ({ defaultMessage }: any) => defaultMessage,
  }),
}));

describe('File', () => {
  beforeEach(() => {
    cleanup();
    document.documentElement.lang = 'nl';
  });

  it('renders without crashing', () => {
    render(
      <File name="test.pdf" href="/download/123" size="2000" extension="pdf" />
    );
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
  });

  it('renders download link by default', () => {
    render(
      <File name="test.pdf" href="/download/123" size="2000" extension="pdf" />
    );
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/download/123');
  });

  it('renders delete button when showDelete is true', () => {
    render(
      <File
        name="test.pdf"
        href="/download/123"
        size="2000"
        extension="pdf"
        showDelete={true}
        deleteUrl="/delete/123"
      />
    );
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('renders with image icon for image files', () => {
    render(
      <File
        name="photo.jpg"
        href="/download/456"
        size="5000"
        extension="jpg"
        isImage={true}
      />
    );
    expect(screen.getByText('photo.jpg')).toBeInTheDocument();
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/download/456');
  });
});
