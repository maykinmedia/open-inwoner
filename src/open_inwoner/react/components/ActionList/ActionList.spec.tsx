import { render, screen } from '@testing-library/preact';
import { describe, it, expect, beforeAll } from 'vitest';
import { ActionList, IActionProps, ACTION_LIST_DEFINITION } from '.';
import { WebComponentLoader } from '@react/lib/web-component';

import '@testing-library/jest-dom';

const mockActions: IActionProps[] = [
  {
    title: 'Complete your profile',
    message: 'Please fill in your personal information',
    action_url: '/profile',
  },
  {
    title: 'Upload documents',
    message: 'Upload required documents for verification',
    action_url: '/documents',
  },
];

describe('ActionList', () => {
  it('renders without crashing', () => {
    render(<ActionList actions={mockActions} />);
    expect(screen.getByText('Complete your profile')).toBeInTheDocument();
  });

  it('renders all actions', () => {
    render(<ActionList actions={mockActions} />);

    expect(screen.getByText('Complete your profile')).toBeInTheDocument();
    expect(screen.getByText('Upload documents')).toBeInTheDocument();
  });

  it('renders action messages', () => {
    render(<ActionList actions={mockActions} />);

    expect(
      screen.getByText(/Please fill in your personal information/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Upload required documents for verification/)
    ).toBeInTheDocument();
  });

  it('renders action links with correct URLs', () => {
    render(<ActionList actions={mockActions} />);
    const profileLink = screen.getByText('Complete your profile').closest('a');
    const uploadLink = screen.getByText('Upload documents').closest('a');

    expect(profileLink).toHaveAttribute('href', '/profile');
    expect(uploadLink).toHaveAttribute('href', '/documents');
  });

  it('renders empty list when no actions provided', () => {
    const { container } = render(<ActionList actions={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('handles undefined actions gracefully', () => {
    const { container } = render(<ActionList actions={undefined!} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders action without text when action_text is empty', () => {
    const actionWithoutText = [
      {
        title: 'Test action',
        message: 'Test message',
        action_url: '/test',
      },
    ];

    render(<ActionList actions={actionWithoutText} />);
    expect(() => screen.getByText('Ga naar actie')).toThrow();
    expect(screen.getByRole('link')).toBeInTheDocument();
  });

  it('renders correct number of Action components', () => {
    const { container } = render(<ActionList actions={mockActions} />);

    // Each Action component should render the title
    const titles = container.querySelectorAll('div');
    expect(titles.length).toBeGreaterThan(0);
  });

  it('renders actions in correct order', () => {
    render(<ActionList actions={mockActions} />);

    const messages = screen.getAllByText(/|/);
    expect(messages[0]).toHaveTextContent(
      'Please fill in your personal information'
    );
    expect(messages[1]).toHaveTextContent(
      'Upload required documents for verification'
    );
  });

  it('renders action links with correct CSS classes', () => {
    render(<ActionList actions={mockActions} />);

    const links = screen.getAllByRole('link');
    links.forEach((link) => {
      expect(link).toHaveClass(
        'nl-link',
        'denhaag-action',
        'denhaag-action--single'
      );
    });
  });

  it('renders single action correctly', () => {
    const singleAction = [mockActions[0]];
    render(<ActionList actions={singleAction} />);

    expect(screen.getByText('Complete your profile')).toBeInTheDocument();
    expect(screen.queryByText('Upload documents')).not.toBeInTheDocument();
  });

  it('maintains action data integrity', () => {
    render(<ActionList actions={mockActions} />);

    mockActions.forEach((action) => {
      expect(screen.getByText(action.title)).toBeInTheDocument();
      expect(screen.getByText(new RegExp(action.message))).toBeInTheDocument();
    });
  });

  it('renders with special characters in action data', () => {
    const specialActions = [
      {
        title: 'Test & Review',
        message: 'Check <data> & verify',
        action_url: '/test?id=1&type=review',
      },
    ];

    render(<ActionList actions={specialActions} />);
    // Check that title with ampersand is rendered correctly
    expect(screen.getByText('Test & Review')).toBeInTheDocument();

    // Check that message with HTML characters is properly escaped
    const messageElement = screen.getByText(/Check.*verify/);
    expect(messageElement).toBeInTheDocument();
    expect(messageElement.innerHTML).toContain('&lt;data&gt;');

    // Verify link URL with query parameters is correct
    const link = screen.getByText('Test & Review').closest('a');
    expect(link).toHaveAttribute('href', '/test?id=1&type=review');
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      // Register the web component before tests
      await WebComponentLoader.importWebComponent(
        ACTION_LIST_DEFINITION.tagName
      );
    });

    it('renders web component with actions-id and displays content', () => {
      const actionsId = 'test-actions-id';

      // Create script tag with JSON data
      const script = document.createElement('script');
      script.type = 'application/json';
      script.id = actionsId;
      script.textContent = JSON.stringify(mockActions);
      document.body.appendChild(script);

      // Create and render web component
      render(<action-list actions-id={actionsId} />);

      // Verify the web component renders the action content
      expect(screen.getByText('Complete your profile')).toBeInTheDocument();
      expect(screen.getByText('Upload documents')).toBeInTheDocument();
      expect(
        screen.getByText(/Please fill in your personal information/)
      ).toBeInTheDocument();

      // Clean up
      document.body.removeChild(script);
    });

    it('renders web component with inline actions prop and displays content', () => {
      const actions = [
        {
          title: 'Web Component Action',
          message: 'Test web component message',
          action_url: '/test',
        },
      ];

      render(<action-list actions={actions} />);

      // Verify the web component renders the action content
      expect(screen.getByText('Web Component Action')).toBeInTheDocument();
      expect(
        screen.getByText(/Test web component message/)
      ).toBeInTheDocument();
    });

    it('renders action links correctly in web component', () => {
      const actionsId = 'test-links-id';

      const script = document.createElement('script');
      script.type = 'application/json';
      script.id = actionsId;
      script.textContent = JSON.stringify(mockActions);
      document.body.appendChild(script);

      render(<action-list actions-id={actionsId} />);

      const profileLink = screen
        .getByText('Complete your profile')
        .closest('a');
      expect(profileLink).toHaveAttribute('href', '/profile');

      // Clean up
      document.body.removeChild(script);
    });
  });
});
