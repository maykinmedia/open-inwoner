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
      <File
        name="test.pdf"
        downloadUrl="/download/123"
        size={String(2000 * 1024)}
        extension="pdf"
      />
    );
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
  });

  it('renders download link by default', () => {
    render(
      <File
        name="test.pdf"
        downloadUrl="/download/123"
        size={String(2000 * 1024)}
        extension="pdf"
      />
    );
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/download/123');
  });

  it('renders delete button when showDelete is true', () => {
    render(
      <File
        name="test.pdf"
        downloadUrl="/download/123"
        size={String(2000 * 1024)}
        extension="pdf"
        showDelete={true}
        deleteUrl="/delete/123"
      />
    );
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('renders delete button when removableLabel is not provided', () => {
    render(
      <File
        name="test.pdf"
        downloadUrl="/download/123"
        size={String(2000 * 1024)}
        extension="pdf"
        showDelete={true}
        deleteUrl="/delete/123"
      />
    );
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('renders delete button with custom removableLabel when provided', () => {
    render(
      <File
        name="test.pdf"
        downloadUrl="/download/123"
        size={String(2000 * 1024)}
        extension="pdf"
        showDelete={true}
        deleteUrl="/delete/123"
        removableLabel="Verwijderen"
      />
    );
    expect(screen.getByText('Verwijderen')).toBeInTheDocument();
  });

  it('renders with image icon for image files', () => {
    render(
      <File
        name="photo.jpg"
        downloadUrl="/download/456"
        size={String(5000 * 1024)}
        extension="jpg"
        isImage={true}
      />
    );
    expect(screen.getByText('photo.jpg')).toBeInTheDocument();
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/download/456');
  });

  it('formats file size from bytes to MB for large files', () => {
    render(
      <File
        name="test.pdf"
        downloadUrl="/download/123"
        size={String(2 * 1024 * 1024)}
        extension="pdf"
      />
    );
    expect(screen.getByText(/2 MB/)).toBeInTheDocument();
  });

  it('parses extension from filename when extension prop is not provided', () => {
    render(
      <File
        name="photo.png"
        downloadUrl="/download/789"
        size={String(512 * 1024)}
      />
    );
    expect(screen.getByText('photo.png')).toBeInTheDocument();
    expect(screen.getByText('(png, 512 KB)')).toBeInTheDocument();
  });

  it('renders no link or button when downloadUrl and deleteUrl are absent', () => {
    render(<File name="voorbeeld-cv.txt" size="13" extension="txt" />);
    expect(screen.getByText('voorbeeld-cv.txt')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
