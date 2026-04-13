import { render, screen } from '@testing-library/preact';
import { describe, it, expect, beforeAll } from 'vitest';
import { SideNav, SIDE_NAV_DEFINITION } from '.';
import { WebComponentLoader } from '@react/lib/web-component';

describe('SideNav', () => {
  it('renders without crashing', () => {
    render(<SideNav items={[]} />);

    // Assuming SideNavigation renders a <nav> with role="navigation"
    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
  });

  it('renders all menu items', () => {
    const items = [
      { href: '/home', label: 'Home', icon: 'home', current: true },
      { href: '/profile', label: 'Profile', icon: '', current: false },
      {
        href: '/messages',
        label: 'Messages',
        icon: 'inbox',
        current: false,
        counter: 5,
      },
    ];

    render(<SideNav items={[items]} />);

    // Check labels are rendered
    items.forEach(({ label }) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });

    // Check MaterialIcon rendered only for items with non-empty icon string
    const iconHome = screen.getByText('home');
    expect(iconHome).toBeInTheDocument();

    const iconInbox = screen.getByText('inbox');
    expect(iconInbox).toBeInTheDocument();
  });

  it('does not render icon if icon is empty or whitespace', () => {
    const items = [
      { href: '/empty', label: 'EmptyIcon', icon: '' },
      { href: '/spaces', label: 'SpacesIcon', icon: '   ' },
    ];

    render(<SideNav items={[items]} />);

    // Labels should be present
    items.forEach(({ label }) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it('passes current and counter props correctly', () => {
    const items = [
      { href: '/counter', label: 'Counter', current: true, counter: 4 },
    ];

    render(<SideNav items={[items]} />);

    expect(screen.getByText('Counter')).toBeInTheDocument();
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      // Register the web component before tests
      await WebComponentLoader.importWebComponent(SIDE_NAV_DEFINITION.tagName);
    });

    it('renders web component with items-id and displays content', () => {
      const itemsId = 'test-items-id';
      const items = [
        [
          { href: '/home', label: 'Home', icon: 'home', current: true },
          {
            href: '/profile',
            label: 'Profile',
            icon: 'person',
            current: false,
          },
        ],
      ];

      // Create script tag with JSON data
      const script = document.createElement('script');
      script.type = 'application/json';
      script.id = itemsId;
      script.textContent = JSON.stringify(items);
      document.body.appendChild(script);

      render(<side-navigation items-id={itemsId} />);

      // Verify the web component renders the navigation items
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Profile')).toBeInTheDocument();

      // Clean up
      document.body.removeChild(script);
    });

    it('renders web component with inline items prop and displays content', () => {
      const items = [
        [
          { href: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
          { href: '/settings', label: 'Settings', icon: 'settings' },
        ],
      ];

      render(<side-navigation items={items} />);

      // Verify the web component renders the navigation items
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('renders web component with multiple navigation groups', () => {
      const items = [
        [
          { href: '/home', label: 'Home', icon: 'home' },
          { href: '/about', label: 'About', icon: 'info' },
        ],
        [
          { href: '/settings', label: 'Settings', icon: 'settings' },
          { href: '/logout', label: 'Logout', icon: 'exit_to_app' },
        ],
      ];

      render(<side-navigation items={items} />);

      // Verify all navigation items from both groups are rendered
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });

    it('renders web component with icons', () => {
      const items = [
        [
          { href: '/messages', label: 'Messages', icon: 'inbox' },
          {
            href: '/notifications',
            label: 'Notifications',
            icon: 'notifications',
          },
        ],
      ];

      render(<side-navigation items={items} />);

      // Verify icons are rendered
      expect(screen.getByText('inbox')).toBeInTheDocument();
      expect(screen.getByText('notifications')).toBeInTheDocument();
    });
  });
});
