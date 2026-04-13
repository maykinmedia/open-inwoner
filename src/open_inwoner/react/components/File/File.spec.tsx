import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/preact';
import File from './File';
import { IntlWrapperNL } from '@react/lib/decorators/web-component';

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
      />,
      { wrapper: IntlWrapperNL }
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
      />,
      { wrapper: IntlWrapperNL }
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
      />,
      { wrapper: IntlWrapperNL }
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
      />,
      { wrapper: IntlWrapperNL }
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
      />,
      { wrapper: IntlWrapperNL }
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
      />,
      { wrapper: IntlWrapperNL }
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
      />,
      { wrapper: IntlWrapperNL }
    );
    expect(screen.getByText(/2 MB/)).toBeInTheDocument();
  });

  it('parses extension from filename when extension prop is not provided', () => {
    render(
      <File
        name="photo.png"
        downloadUrl="/download/789"
        size={String(512 * 1024)}
      />,
      { wrapper: IntlWrapperNL }
    );
    expect(screen.getByText('photo.png')).toBeInTheDocument();
    expect(screen.getByText('(png, 512 KB)')).toBeInTheDocument();
  });

  it('renders no link or button when downloadUrl and deleteUrl are absent', () => {
    render(<File name="voorbeeld-cv.txt" size="13" extension="txt" />, {
      wrapper: IntlWrapperNL,
    });
    expect(screen.getByText('voorbeeld-cv.txt')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
