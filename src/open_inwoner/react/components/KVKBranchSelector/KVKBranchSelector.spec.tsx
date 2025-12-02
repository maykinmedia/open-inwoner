import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/preact';
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { KVKBranchSelector, KVK_BRANCH_SELECTOR_DEFINITION } from '.';
import { WebComponentLoader } from '@react/lib/web-component';

// Mock useIntl hook to avoid IntlProvider compatibility issues with Preact
vi.mock('react-intl', () => ({
  useIntl: () => ({
    formatMessage: ({ id }: { id: string }) => {
      const messages: Record<string, string> = {
        'kvkbranchselector.placeholder':
          'Vul naam, adres of vestigingsnummer in...',
        'kvkbranchselector.clear': 'Wissen',
        'kvkbranchselector.toggle': 'Toggle dropdown',
      };
      return messages[id] || id;
    },
  }),
}));

// Mock scrollIntoView since jsdom doesn't support it
Element.prototype.scrollIntoView = vi.fn();

const mockBranches = [
  {
    id: 'rechtspersoon',
    label: 'Test Company',
    rechtspersoonInfo: '(Rechtspersoon)',
  },
  {
    id: '12345',
    label: 'Test Company',
    vestigingInfo: 'Vestiging: 12345 (Hoofdvestiging)',
    addressInfo: 'Teststraat 1',
    cityInfo: 'Amsterdam',
  },
  {
    id: '67890',
    label: 'Test Company Branch 2',
    vestigingInfo: 'Vestiging: 67890',
    addressInfo: 'Branchweg 10',
    cityInfo: 'Rotterdam',
  },
];

describe('KVKBranchSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders combobox with label', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Select Branch')).toBeInTheDocument();
  });

  it('opens dropdown and displays all branch options', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    // Clear the auto-selected rechtspersoon to open dropdown
    fireEvent.click(screen.getByLabelText(/wissen/i));

    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(screen.getAllByRole('option')).toHaveLength(3);
    expect(screen.getByText('(Rechtspersoon)')).toBeInTheDocument();
    expect(
      screen.getByText('Vestiging: 12345 (Hoofdvestiging)')
    ).toBeInTheDocument();
  });

  it('toggles dropdown with button click', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    // Component auto-selects rechtspersoon, so clear button is shown initially
    const clearButton = screen.getByLabelText(/wissen/i);
    expect(clearButton).toBeInTheDocument();

    // Click clear to remove selection
    fireEvent.click(clearButton);

    // Now toggle button should appear
    const toggleButton = screen.getByLabelText(/toggle dropdown/i);
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true');

    // Close dropdown
    fireEvent.click(toggleButton);
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

    // Open again
    fireEvent.click(toggleButton);
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
  });

  it('filters branches based on search query', async () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'Rotterdam' } });

    // Wait for debounce to complete
    await waitFor(
      () => {
        const options = screen.getAllByRole('option');
        expect(options).toHaveLength(1);
      },
      { timeout: 500 }
    );

    expect(screen.getByText('Test Company Branch 2')).toBeInTheDocument();
  });

  it('shows clear button when typing and clears on click', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    const input = screen.getByRole('combobox') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'test' } });

    const clearButton = screen.getByLabelText(/wissen/i);
    expect(clearButton).toBeInTheDocument();

    fireEvent.click(clearButton);
    expect(input.value).toBe('');
  });

  it('selects branch when option is clicked', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    const input = screen.getByRole('combobox') as HTMLInputElement;
    // Clear to open dropdown
    fireEvent.click(screen.getByLabelText(/wissen/i));

    const option = screen.getByText('Test Company Branch 2');
    fireEvent.mouseDown(option);

    expect(input.value).toBe('Test Company Branch 2');
  });

  it('navigates with keyboard and selects with Enter', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    const input = screen.getByRole('combobox') as HTMLInputElement;
    fireEvent.focus(input);
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    // Component auto-selects rechtspersoon, so expect that value
    expect(input.value).toBe('Test Company (Rechtspersoon)');
  });

  it('closes dropdown on Escape key', () => {
    render(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    );

    const input = screen.getByRole('combobox');
    // Clear to open dropdown
    fireEvent.click(screen.getByLabelText(/wissen/i));
    expect(screen.getByRole('listbox')).toBeInTheDocument();

    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('creates hidden input with correct value for form submission', () => {
    const { container } = render(
      <form>
        <KVKBranchSelector
          id="test-combobox"
          label="Select Branch"
          name="branch_number"
          branches={mockBranches}
          selectedBranchId="12345"
        />
      </form>
    );

    const hiddenInput = container.querySelector(
      'input[type="hidden"][name="branch_number"]'
    ) as HTMLInputElement;

    expect(hiddenInput).toBeInTheDocument();
    expect(hiddenInput.value).toBe('12345');
  });

  it('maps rechtspersoon ID to empty string in hidden input', () => {
    const { container } = render(
      <form>
        <KVKBranchSelector
          id="test-combobox"
          label="Select Branch"
          name="branch_number"
          branches={mockBranches}
          selectedBranchId="rechtspersoon"
        />
      </form>
    );

    const hiddenInput = container.querySelector(
      'input[type="hidden"][name="branch_number"]'
    ) as HTMLInputElement;

    expect(hiddenInput.value).toBe('');
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      // Register the web component before tests
      await WebComponentLoader.importWC(KVK_BRANCH_SELECTOR_DEFINITION.tagName);
    });

    it('can be rendered as a web component with branches-id', () => {
      const branchesId = 'test-branches-id';

      // Create script tag with JSON data
      const script = document.createElement('script');
      script.type = 'application/json';
      script.id = branchesId;
      script.textContent = JSON.stringify(mockBranches);
      document.body.appendChild(script);

      // Create and render web component
      const { container } = render(
        <kvk-branch-selector
          id="test-kvk"
          label="Select Branch"
          name="branch"
          branches-id={branchesId}
        />
      );

      // Verify element is in the DOM
      const webComponent = container.querySelector('kvk-branch-selector');
      expect(webComponent).toBeInTheDocument();
      expect(webComponent?.getAttribute('branches-id')).toBe(branchesId);

      // Clean up
      document.body.removeChild(script);
    });

    it('renders web component with inline branches prop', () => {
      const branches = [
        {
          id: 'test-1',
          label: 'Test Branch',
          vestigingInfo: 'Vestiging: test-1',
        },
      ];

      const { container } = render(
        <kvk-branch-selector
          id="test-selector"
          label="Branch Selector"
          name="branch_selector"
          branches={branches}
        />
      );

      const webComponent = container.querySelector('kvk-branch-selector');
      expect(webComponent).toBeInTheDocument();
    });
  });
});
