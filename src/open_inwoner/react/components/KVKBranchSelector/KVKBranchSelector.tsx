import {
  ChangeEventHandler,
  FC,
  KeyboardEventHandler,
  MouseEventHandler,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { useIntl } from 'react-intl'
import { useDebounce } from '@react/lib/hooks/useDebounce'
import clsx from 'clsx'
import { MaterialIcon } from '@react/components/MaterialIcon'

export interface ComboBoxItem {
  id: string
  label: string
  vestigingInfo?: string
  rechtspersoonInfo?: string
  addressInfo?: string
  cityInfo?: string
  vestigingsnummer?: string
  type?: string
}

interface KVKBranchSelectorProps {
  id: string
  label: string
  name: string
  branches: ComboBoxItem[]
  selectedBranchId?: string
}

/**
 * Accessible combobox component for branch selection with search filtering.
 * Supports keyboard navigation, mouse/touchscreen, and form submission.
 */
export const KVKBranchSelector: FC<KVKBranchSelectorProps> = ({
  id,
  label,
  name,
  branches,
  selectedBranchId,
}) => {
  const intl = useIntl()
  const [query, setQuery] = useState('')
  // Debounce the query to prevent expensive filtering on every keystroke
  // Wait 300ms after user stops typing before filtering results
  const debouncedQuery = useDebounce(query, 300)
  const [isOpen, setIsOpen] = useState(false)
  // Lazy initializer with auto-select
  const [selectedId, setSelectedId] = useState<string | undefined>(() => {
    if (selectedBranchId) return selectedBranchId
    // Find rechtspersoon branch and auto-select it
    const rechtspersoonBranch = branches.find((b) => b.id === 'rechtspersoon')
    return rechtspersoonBranch ? 'rechtspersoon' : undefined
  })
  const [focusedIndex, setFocusedIndex] = useState<number>(0)
  const listRef = useRef<HTMLUListElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Find the selected branch to display its name in the input
  const selectedBranch = useMemo(
    () => branches.find((b) => b.id === selectedId),
    [branches, selectedId]
  )

  // Filter branches based on debounced search query across all text fields
  // This expensive operation only runs after user stops typing for 300ms
  // Split query and make substrings-tolerant search
  const filtered = useMemo(
    () =>
      branches.filter((b) => {
        // Combine all searchable fields into one string
        const searchText = [
          b.label,
          b.vestigingInfo,
          b.rechtspersoonInfo,
          b.addressInfo,
          b.cityInfo,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()

        // Split query into individual words (ignoring extra spaces)
        const searchWords = debouncedQuery
          .toLowerCase()
          .trim()
          .split(/\s+/)
          .filter(Boolean)

        // Check if all search words appear as substrings somewhere in the combined text
        return searchWords.every((word) => searchText.includes(word))
      }),
    [branches, debouncedQuery]
  )

  // Show clear button when input contains text
  const hasText = query !== ''

  const handleSelect = (id: string) => {
    const branch = branches.find((b) => b.id === id)
    setSelectedId(id)
    setQuery(branch?.label || '')
    setIsOpen(false)
    inputRef.current?.focus()
  }

  const handleClearQuery = () => {
    setQuery('')
    setSelectedId(undefined)
    setFocusedIndex(0)
    setIsOpen(true)
    inputRef.current?.focus()
  }

  const handleToggleDropdown: MouseEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault()
    e.stopPropagation()
    const newIsOpen = !isOpen
    setIsOpen(newIsOpen)
    if (newIsOpen) {
      setFocusedIndex(0)
      // Only focus input when opening to prevent conflict with close action
      inputRef.current?.focus()
    }
  }

  const handleKeyDown: KeyboardEventHandler<HTMLInputElement> = (e) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        if (!isOpen) {
          setIsOpen(true)
          setFocusedIndex(0)
        } else {
          setFocusedIndex((prev) =>
            prev < filtered.length - 1 ? prev + 1 : prev
          )
        }
        break

      case 'ArrowUp':
        e.preventDefault()
        if (!isOpen) {
          setIsOpen(true)
          setFocusedIndex(0)
        } else {
          setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0))
        }
        break

      case 'Enter':
        e.preventDefault()
        if (isOpen && filtered[focusedIndex]) {
          handleSelect(filtered[focusedIndex].id)
        }
        break

      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        break

      case 'Tab':
        setIsOpen(false)
        break
    }
  }

  const handleInputChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    setQuery(e.target.value)
    setIsOpen(true)
    setFocusedIndex(0)
  }

  // Close dropdown when clicking outside component
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, containerRef])

  // Initialize input with selected branch name
  useEffect(() => {
    if (selectedBranch && !query) {
      setQuery(selectedBranch.label)
    }
  }, [selectedBranch, query])

  // Scroll focused option into view for keyboard navigation
  useEffect(() => {
    if (isOpen && listRef.current && listRef.current.children[focusedIndex]) {
      const el = listRef.current.children[focusedIndex] as HTMLElement
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [focusedIndex, isOpen])

  // Sync selection with hidden form input for Django form submission
  useEffect(() => {
    const form = inputRef.current?.closest('form')
    if (!form) return

    // Create or update hidden input with selected branch value
    let hiddenInput = form.querySelector<HTMLInputElement>(
      `input[name="${name}"]`
    )
    if (!hiddenInput) {
      hiddenInput = document.createElement('input')
      hiddenInput.type = 'hidden'
      hiddenInput.name = name
      form.appendChild(hiddenInput)
    }

    // Map 'rechtspersoon' ID to empty string for Django backend
    if (selectedId !== undefined) {
      hiddenInput.value = selectedId === 'rechtspersoon' ? '' : selectedId
    }

    // Enable/disable submit button based on selection state
    const submitButton = form.querySelector<HTMLButtonElement>(
      'button[name="submit"]'
    )
    if (submitButton) {
      if (selectedId !== undefined) {
        // When selection is made
        submitButton.disabled = false
        submitButton.classList.remove('button--disabled')
      } else {
        // Anytime no selection exists
        submitButton.disabled = true
        submitButton.classList.add('button--disabled')
      }
    }
  }, [selectedId, name])

  return (
    <div
      className="utrecht-form-field utrecht-form-field--text"
      ref={containerRef}
    >
      <label htmlFor={id} className="utrecht-form-label">
        {label}
      </label>

      <div className="oip-combobox">
        <input
          ref={inputRef}
          id={id}
          className="utrecht-textbox oip-combobox__input"
          type="text"
          role="combobox"
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            setIsOpen(true)
            setFocusedIndex(0)
          }}
          onKeyDown={handleKeyDown}
          aria-expanded={isOpen}
          aria-controls={`${id}-listbox`}
          placeholder={intl.formatMessage({
            id: 'kvkbranchselector.placeholder',
            description: 'Placeholder text for branch search input',
            defaultMessage: 'Enter name, address or branch number...',
          })}
          autoComplete="off"
        />

        {/* TODO: Replace with NLDS Buttons once available */}
        {hasText ? (
          <button
            type="button"
            className="button button__icon-close button--textless button--icon oip-combobox__icon"
            onClick={handleClearQuery}
            aria-label={intl.formatMessage({
              id: 'kvkbranchselector.clear',
              description: 'Clear search button label',
              defaultMessage: 'Clear',
            })}
          >
            <MaterialIcon name="close" />
          </button>
        ) : (
          <button
            type="button"
            className="button button--textless button--icon oip-combobox__icon"
            onClick={handleToggleDropdown}
            aria-label={intl.formatMessage({
              id: 'kvkbranchselector.toggle',
              description: 'Toggle dropdown button label',
              defaultMessage: 'Toggle dropdown',
            })}
            aria-expanded={isOpen}
            aria-controls={`${id}-listbox`}
          >
            <MaterialIcon name="keyboard_arrow_down" />
          </button>
        )}

        {isOpen && filtered.length > 0 && (
          <div
            className="utrecht-listbox oip-combobox__popover oip-combobox__popover--block-end"
            role="listbox"
            id={`${id}-listbox`}
            aria-label={label}
          >
            <ul className="utrecht-listbox__list" ref={listRef}>
              {filtered.map((item, i) => (
                <li
                  key={item.id}
                  role="option"
                  aria-selected={selectedId === item.id}
                  className={clsx('utrecht-listbox__option', {
                    'utrecht-listbox__option--selected': selectedId === item.id,
                    'utrecht-listbox__option--active': focusedIndex === i,
                  })}
                  onMouseDown={(e) => {
                    // After selection, close popover
                    e.preventDefault()
                    e.stopPropagation()
                    handleSelect(item.id)
                  }}
                  onMouseEnter={() => setFocusedIndex(i)}
                >
                  <div className="utrecht-listbox__content">
                    <div className="utrecht-listbox__heading">
                      {item.label}
                      {selectedId === item.id && <MaterialIcon name="check" />}
                    </div>
                    {item.rechtspersoonInfo && (
                      <div className="utrecht-listbox__p">
                        {item.rechtspersoonInfo}
                      </div>
                    )}
                    {item.vestigingInfo && (
                      <div className="utrecht-listbox__p">
                        {item.vestigingInfo}
                      </div>
                    )}
                    {item.addressInfo && (
                      <div className="utrecht-listbox__p">
                        {item.addressInfo}
                      </div>
                    )}
                    {item.cityInfo && (
                      <div className="utrecht-listbox__p">{item.cityInfo}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
