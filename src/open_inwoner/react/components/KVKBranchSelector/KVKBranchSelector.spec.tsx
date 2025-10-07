import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { IntlProvider } from 'react-intl'
import { KVKBranchSelector } from './KVKBranchSelector'
import '@testing-library/jest-dom'

// Mock MaterialIcon component
vi.mock('@react/components/MaterialIcon', () => ({
  MaterialIcon: ({ name }: { name: string }) => (
    <span data-testid="material-icon">{name}</span>
  ),
}))

// Mock scrollIntoView since jsdom doesn't support it
Element.prototype.scrollIntoView = vi.fn()

// Translation messages for IntlProvider
const messages = {
  'kvkbranchselector.placeholder': 'Vul naam, adres of vestigingsnummer in...',
  'kvkbranchselector.clear': 'Wissen',
  'kvkbranchselector.toggle': 'Toggle dropdown',
}

// Helper to wrap component with IntlProvider
const renderWithIntl = (ui: React.ReactElement) => {
  return render(
    <IntlProvider locale="nl" messages={messages}>
      {ui}
    </IntlProvider>
  )
}

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
]

describe('KVKBranchSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders combobox with label', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('Select Branch')).toBeInTheDocument()
  })

  it('opens dropdown and displays all branch options', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    const input = screen.getByRole('combobox')
    fireEvent.focus(input)

    expect(screen.getByRole('listbox')).toBeInTheDocument()
    expect(screen.getAllByRole('option')).toHaveLength(3)
    expect(screen.getByText('(Rechtspersoon)')).toBeInTheDocument()
    expect(
      screen.getByText('Vestiging: 12345 (Hoofdvestiging)')
    ).toBeInTheDocument()
  })

  it('toggles dropdown with button click', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    // Component auto-selects rechtspersoon, so clear button is shown initially
    const clearButton = screen.getByLabelText(/wissen/i)
    expect(clearButton).toBeInTheDocument()

    // Click clear to remove selection
    fireEvent.click(clearButton)

    // Now toggle button should appear
    const toggleButton = screen.getByLabelText(/toggle dropdown/i)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true')

    // Close dropdown
    fireEvent.click(toggleButton)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false')

    // Open again
    fireEvent.click(toggleButton)
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true')
  })

  it('filters branches based on search query', async () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'Rotterdam' } })

    // Wait for debounce to complete
    await waitFor(
      () => {
        const options = screen.getAllByRole('option')
        expect(options).toHaveLength(1)
      },
      { timeout: 500 }
    )

    expect(screen.getByText('Test Company Branch 2')).toBeInTheDocument()
  })

  it('shows clear button when typing and clears on click', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    const input = screen.getByRole('combobox') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'test' } })

    const clearButton = screen.getByLabelText(/wissen/i)
    expect(clearButton).toBeInTheDocument()

    fireEvent.click(clearButton)
    expect(input.value).toBe('')
  })

  it('selects branch when option is clicked', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    const input = screen.getByRole('combobox') as HTMLInputElement
    fireEvent.focus(input)

    const option = screen.getByText('Test Company Branch 2')
    fireEvent.mouseDown(option)

    expect(input.value).toBe('Test Company Branch 2')
  })

  it('navigates with keyboard and selects with Enter', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    const input = screen.getByRole('combobox') as HTMLInputElement
    fireEvent.focus(input)
    fireEvent.keyDown(input, { key: 'ArrowDown' })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(input.value).toBe('Test Company')
  })

  it('closes dropdown on Escape key', () => {
    renderWithIntl(
      <KVKBranchSelector
        id="test-combobox"
        label="Select Branch"
        name="branch"
        branches={mockBranches}
      />
    )

    const input = screen.getByRole('combobox')
    fireEvent.focus(input)
    expect(screen.getByRole('listbox')).toBeInTheDocument()

    fireEvent.keyDown(input, { key: 'Escape' })
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('creates hidden input with correct value for form submission', () => {
    const { container } = renderWithIntl(
      <form>
        <KVKBranchSelector
          id="test-combobox"
          label="Select Branch"
          name="branch_number"
          branches={mockBranches}
          selectedBranchId="12345"
        />
      </form>
    )

    const hiddenInput = container.querySelector(
      'input[type="hidden"][name="branch_number"]'
    ) as HTMLInputElement

    expect(hiddenInput).toBeInTheDocument()
    expect(hiddenInput.value).toBe('12345')
  })

  it('maps rechtspersoon ID to empty string in hidden input', () => {
    const { container } = renderWithIntl(
      <form>
        <KVKBranchSelector
          id="test-combobox"
          label="Select Branch"
          name="branch_number"
          branches={mockBranches}
          selectedBranchId="rechtspersoon"
        />
      </form>
    )

    const hiddenInput = container.querySelector(
      'input[type="hidden"][name="branch_number"]'
    ) as HTMLInputElement

    expect(hiddenInput.value).toBe('')
  })
})
