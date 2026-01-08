import { WebComponentLoader } from '@react/lib/web-component';
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/preact';
import { beforeAll, describe, expect, it } from 'vitest';
import { Accordion } from '.';
import { ACCORDION_DEFINITION } from './constants';

describe('Accordion', () => {
  it('renders without crashing', () => {
    render(<Accordion title="Test Accordion" />);
    expect(screen.getByText('Test Accordion')).toBeInTheDocument();
  });

  it('renders title as h2 when subtitle is provided', () => {
    render(<Accordion title="Main Title" subtitle="Subtitle text" />);

    const titleElement = screen.getByText('Main Title');
    expect(titleElement).toBeInTheDocument();
    expect(titleElement.tagName).toBe('H2');
    expect(titleElement).toHaveClass('utrecht-heading-3');
  });

  it('renders title as p when no subtitle is provided', () => {
    render(<Accordion title="Main Title" />);

    const titleElement = screen.getByText('Main Title');
    expect(titleElement).toBeInTheDocument();
    expect(titleElement.tagName).toBe('P');
  });

  it('renders subtitle when provided', () => {
    render(<Accordion title="Main Title" subtitle="Subtitle text" />);

    const subtitleElement = screen.getByText('Subtitle text');
    expect(subtitleElement).toBeInTheDocument();
    expect(subtitleElement.tagName).toBe('P');
    expect(subtitleElement).toHaveClass('utrecht-paragraph');
  });

  it('renders without title or subtitle', () => {
    const { container } = render(<Accordion>Content only</Accordion>);

    expect(screen.getByText('Content only')).toBeInTheDocument();
    const heading = container.querySelector('.accordion__heading');
    expect(heading).toBeInTheDocument();
    expect(heading?.querySelector('h2')).not.toBeInTheDocument();
    expect(heading?.querySelector('p')).not.toBeInTheDocument();
  });

  it('renders children content', () => {
    render(
      <Accordion title="Test">
        <div>Child content</div>
      </Accordion>
    );

    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('is closed by default', () => {
    const { container } = render(<Accordion title="Test Accordion" />);

    const details = container.querySelector('details');
    expect(details).not.toHaveAttribute('open');
  });

  it('is open when initialOpen is true', () => {
    const { container } = render(
      <Accordion title="Test Accordion" initialOpen={true} />
    );

    const details = container.querySelector('details');
    expect(details).toHaveAttribute('open');
  });

  it('toggles open state when clicked', () => {
    const { container } = render(<Accordion title="Test Accordion" />);

    const summary = screen.getByText('Test Accordion');
    const details = container.querySelector('details');

    // Initially closed
    expect(details).not.toHaveAttribute('open');

    // Click to open
    fireEvent.click(summary);
    expect(details).toHaveAttribute('open');

    // Click to close
    fireEvent.click(summary);
    expect(details).not.toHaveAttribute('open');
  });

  // TODO: add @testing-library keyboard support for summary elements
  it.skip('is accessible through keyboard (Space and Enter)', () => {
    // @testing-library does not provide default browser enter/space key bindings for summary.
  });

  it('renders default icon', () => {
    render(<Accordion title="Test Accordion" />);

    expect(screen.getByText('keyboard_arrow_down')).toBeInTheDocument();
  });

  it('renders custom icon when provided', () => {
    render(<Accordion title="Test Accordion" icon="expand_more" />);

    expect(screen.getByText('expand_more')).toBeInTheDocument();
    expect(screen.queryByText('keyboard_arrow_down')).not.toBeInTheDocument();
  });

  it('icon rotation is handled by CSS [open] selector', () => {
    const { container } = render(<Accordion title="Test Accordion" />);

    const icon = container.querySelector('.accordion__icon');
    const details = container.querySelector('details');

    // Icon class is always present, rotation handled by CSS
    expect(icon).toHaveClass('accordion__icon');
    expect(icon).not.toHaveClass('accordion__icon--open');

    // Details element is closed initially
    expect(details).not.toHaveAttribute('open');
  });

  it('uses native details toggle behavior', () => {
    const { container } = render(<Accordion title="Test Accordion" />);

    const details = container.querySelector('details');
    const summary = screen.getByText('Test Accordion');

    expect(details).not.toHaveAttribute('open');

    // Click should trigger native details behavior
    fireEvent.click(summary);

    // The details element should be open
    expect(details).toHaveAttribute('open');
  });

  it('renders with proper semantic structure', () => {
    const { container } = render(
      <Accordion title="Test" subtitle="Subtitle">
        <div>Content</div>
      </Accordion>
    );

    const details = container.querySelector('details');
    const summary = container.querySelector('summary');
    const heading = container.querySelector('.accordion__heading');

    expect(details).toBeInTheDocument();
    expect(summary).toBeInTheDocument();
    expect(heading).toBeInTheDocument();
    expect(details?.contains(summary as Node)).toBe(true);
    expect(summary?.contains(heading as Node)).toBe(true);
  });

  it('applies correct CSS classes', () => {
    const { container } = render(
      <Accordion title="Test" subtitle="Subtitle" />
    );

    const details = container.querySelector('details');
    const summary = container.querySelector('summary');
    const heading = container.querySelector('.accordion__heading');

    expect(details).toHaveClass('accordion');
    expect(summary).toHaveClass('accordion__summary');
    expect(heading).toHaveClass('accordion__heading');
  });

  it('renders multiple accordions independently', () => {
    render(
      <div>
        <Accordion title="First Accordion" />
        <Accordion title="Second Accordion" initialOpen={true} />
      </div>
    );

    const firstAccordion = screen
      .getByText('First Accordion')
      .closest('details');
    const secondAccordion = screen
      .getByText('Second Accordion')
      .closest('details');

    expect(firstAccordion).not.toHaveAttribute('open');
    expect(secondAccordion).toHaveAttribute('open');
  });

  it('handles complex children content', () => {
    render(
      <Accordion title="Test">
        <div className="content">
          <p>Paragraph 1</p>
          <p>Paragraph 2</p>
          <ul>
            <li>Item 1</li>
            <li>Item 2</li>
          </ul>
        </div>
      </Accordion>
    );

    expect(screen.getByText('Paragraph 1')).toBeInTheDocument();
    expect(screen.getByText('Paragraph 2')).toBeInTheDocument();
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      // Register the web component before tests
      await WebComponentLoader.importWebComponent(ACCORDION_DEFINITION.tagName);
    });

    it('renders web component without crashing', () => {
      render(<oip-accordion title="Test Accordion" />);
      expect(screen.getByText('Test Accordion')).toBeInTheDocument();
    });

    it('renders web component with title and subtitle', () => {
      render(<oip-accordion title="Main Title" subtitle="Subtitle text" />);

      expect(screen.getByText('Main Title')).toBeInTheDocument();
      expect(screen.getByText('Subtitle text')).toBeInTheDocument();
    });

    it('renders web component children content', () => {
      render(
        <oip-accordion title="Test">
          <div>Child content</div>
        </oip-accordion>
      );

      expect(screen.getByText('Child content')).toBeInTheDocument();
    });

    it('web component is closed by default', () => {
      const { container } = render(<oip-accordion title="Test Accordion" />);

      const details = container.querySelector('details');
      expect(details).not.toHaveAttribute('open');
    });

    it('web component opens when initialOpen is true', () => {
      const { container } = render(
        <oip-accordion title="Test Accordion" initial-open={true} />
      );

      const details = container.querySelector('details');
      expect(details).toHaveAttribute('open');
    });

    it('web component toggles on click', () => {
      const { container } = render(<oip-accordion title="Test Accordion" />);

      const summary = screen.getByText('Test Accordion');
      const details = container.querySelector('details');

      expect(details).not.toHaveAttribute('open');

      fireEvent.click(summary);
      expect(details).toHaveAttribute('open');

      fireEvent.click(summary);
      expect(details).not.toHaveAttribute('open');
    });

    it('web component renders custom icon', () => {
      render(<oip-accordion title="Test" icon="expand_more" />);

      expect(screen.getByText('expand_more')).toBeInTheDocument();
    });

    it('web component renders multiple instances independently', () => {
      render(
        <div>
          <oip-accordion title="First Accordion" />
          <oip-accordion title="Second Accordion" initial-open={true} />
        </div>
      );

      const firstAccordion = screen
        .getByText('First Accordion')
        .closest('details');
      const secondAccordion = screen
        .getByText('Second Accordion')
        .closest('details');

      expect(firstAccordion).not.toHaveAttribute('open');
      expect(secondAccordion).toHaveAttribute('open');
    });
  });
});
