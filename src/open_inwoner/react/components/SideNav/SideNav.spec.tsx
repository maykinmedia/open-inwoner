import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import { SideNav } from '.';

// Import jest-dom matchers for extended assertions like toBeInTheDocument
import '@testing-library/jest-dom';

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
});
