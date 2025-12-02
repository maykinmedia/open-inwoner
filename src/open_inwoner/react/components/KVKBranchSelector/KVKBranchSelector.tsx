import { MaterialIcon } from '@react/components/MaterialIcon';
import { usePropsOrScriptData } from '@react/lib/json/getJsonScriptData';
import { useDebounce } from '@react/lib/hooks/useDebounce';
import clsx from 'clsx';
import {
  FC,
  InputEventHandler,
  KeyboardEventHandler,
  MouseEventHandler,
} from 'preact';
import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import { useIntl } from 'react-intl';

export interface ComboBoxItem {
  id: string;
  label: string;
  vestigingInfo?: string;
  rechtspersoonInfo?: string;
  addressInfo?: string;
  cityInfo?: string;
  vestigingsnummer?: string;
  type?: string;
}

export interface KVKBranchSelectorProps {
  id: string;
  label: string;
  name: string;
  branches?: ComboBoxItem[];
  selectedBranchId?: string;
  branchesId?: string;
}

type BranchData = {
  items?: ComboBoxItem[];
  selected_id?: string;
};

/**
 * Accessible combobox component for branch selection with search filtering.
 * Supports keyboard navigation, mouse/touchscreen, and form submission.
 */
const KVKBranchSelector: FC<KVKBranchSelectorProps> = ({
  id,
  label,
  name,
  branches,
  selectedBranchId,
  branchesId,
}) => {
  const intl = useIntl();
  const [query, setQuery] = useState('');
  // Debounce the query to prevent expensive filtering on every keystroke
  // Wait 300ms after user stops typing before filtering results
  const debouncedQuery = useDebounce(query, 300);
  const [isOpen, setIsOpen] = useState(false);

  // Get branches data from props or script tag
  // Script tag format: { items: ComboBoxItem[], selected_id?: string }
  // Props format: ComboBoxItem[]
  const rawData = usePropsOrScriptData<BranchData | ComboBoxItem[]>(
    branches,
    branchesId
  );

  // Normalize data to ComboBoxItem[]
  const data = Array.isArray(rawData)
    ? rawData
    : (rawData as BranchData)?.items;

  // Get selected_id from script tag data if available
  const scriptSelectedId = !Array.isArray(rawData)
    ? (rawData as BranchData)?.selected_id
    : undefined;

  // Lazy initializer with auto-select
  const [selectedId, setSelectedId] = useState<string | undefined>(() => {
    // Priority: selectedBranchId prop > script tag selected_id > auto-select rechtspersoon
    if (selectedBranchId) return selectedBranchId;
    if (scriptSelectedId) return scriptSelectedId;
    // Find rechtspersoon branch and auto-select it
    const rechtspersoonBranch = data?.find((b) => b.id === 'rechtspersoon');
    return rechtspersoonBranch ? 'rechtspersoon' : undefined;
  });
  const [focusedIndex, setFocusedIndex] = useState<number>(0);
  const listRef = useRef<HTMLUListElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Find the selected branch to display its name in the input
  const selectedBranch = useMemo(
    () => data?.find((b) => b.id === selectedId),
    [data, selectedId]
  );

  // Generate display text for selected branch with distinguishing info
  const getDisplayText = (branch: ComboBoxItem): string => {
    if (branch.id === 'rechtspersoon') {
      return `${branch.label} (Rechtspersoon)`;
    }
    // For vestiging, include vestigingsnummer to distinguish from rechtspersoon
    if (branch.vestigingsnummer) {
      return `${branch.label} (${branch.vestigingsnummer})`;
    }
    return branch.label;
  };

  // Check if query matches the selected branch's display text exactly
  const isSelectedBranchDisplayText = useMemo(() => {
    if (!selectedBranch) return false;
    return query.trim() === getDisplayText(selectedBranch).trim();
  }, [query, selectedBranch]);

  // Filter branches based on debounced search query across all text fields
  // This expensive operation only runs after user stops typing for 300ms
  // Split query and make substrings-tolerant search
  const filtered = useMemo(() => {
    // If the query matches the selected branch display text exactly,
    // show all branches (user wants to see options, not search)
    if (isSelectedBranchDisplayText || debouncedQuery.trim() === '') {
      return data;
    }

    return data?.filter((b) => {
      // Combine all searchable fields into one string
      const searchText = [
        b.label,
        b.vestigingInfo,
        b.rechtspersoonInfo,
        b.addressInfo,
        b.cityInfo,
        b.vestigingsnummer,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      // Split query into individual words (ignoring extra spaces)
      const searchWords = debouncedQuery
        .toLowerCase()
        .trim()
        .split(/\s+/)
        .filter(Boolean);

      // Check if all search words appear as substrings somewhere in the combined text
      return searchWords.every((word) => searchText.includes(word));
    });
  }, [data, debouncedQuery, isSelectedBranchDisplayText]);

  // Show clear button when input contains text
  const hasText = query !== '';

  const handleSelect = (id: string) => {
    const branch = data?.find((b) => b.id === id);
    setSelectedId(id);
    // Use display text with distinguishing info
    setQuery(branch ? getDisplayText(branch) : '');
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleClearQuery = () => {
    setQuery('');
    setSelectedId(undefined);
    setFocusedIndex(0);
    setIsOpen(true);
    inputRef.current?.focus();
  };

  const handleToggleDropdown: MouseEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const newIsOpen = !isOpen;
    setIsOpen(newIsOpen);
    if (newIsOpen) {
      setFocusedIndex(0);
      // Only focus input when opening to prevent conflict with close action
      inputRef.current?.focus();
    }
  };

  const handleKeyDown: KeyboardEventHandler<HTMLInputElement> = (e) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        // Always open dropdown and navigate
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex((prev) =>
            prev < (filtered?.length ?? 0) - 1 ? prev + 1 : prev
          );
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        // Always open dropdown and navigate
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
        }
        break;

      case 'Enter':
        e.preventDefault();
        if (isOpen && filtered?.[focusedIndex]) {
          handleSelect(filtered[focusedIndex].id);
        }
        break;

      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        break;

      case 'Tab':
        setIsOpen(false);
        break;
    }
  };

  const handleInputChange: InputEventHandler<HTMLInputElement> = (e) => {
    setQuery((e.target as HTMLInputElement).value);
    setIsOpen(true);
    setFocusedIndex(0);
  };

  const handleInputClick = () => {
    // Always open dropdown when clicking in the input
    setIsOpen(true);
    setFocusedIndex(0);
  };

  const handleInputFocus = () => {
    // Always open dropdown when focusing the input
    setIsOpen(true);
    setFocusedIndex(0);
  };

  // Close dropdown when clicking outside component
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, containerRef]);

  // Initialize input with selected branch name when selection changes
  useEffect(() => {
    if (selectedBranch) {
      setQuery(getDisplayText(selectedBranch));
    }
  }, [selectedId]); // Only run when selectedId changes, not when query changes

  // Scroll focused option into view for keyboard navigation
  useEffect(() => {
    if (isOpen && listRef.current && listRef.current.children[focusedIndex]) {
      const el = listRef.current.children[focusedIndex] as HTMLElement;
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [focusedIndex, isOpen]);

  // Sync selection with hidden form input for Django form submission
  useEffect(() => {
    const form = inputRef.current?.closest('form');
    if (!form) return;

    // Create or update hidden input with selected branch value
    let hiddenInput = form.querySelector<HTMLInputElement>(
      `input[name="${name}"]`
    );
    if (!hiddenInput) {
      hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';
      hiddenInput.name = name;
      form.appendChild(hiddenInput);
    }

    // Map 'rechtspersoon' ID to empty string for Django backend
    if (selectedId !== undefined) {
      hiddenInput.value = selectedId === 'rechtspersoon' ? '' : selectedId;
    }

    // Enable/disable submit button based on selection state
    const submitButton = form.querySelector<HTMLButtonElement>(
      'button[name="submit"]'
    );
    if (submitButton) {
      if (selectedId !== undefined) {
        // When selection is made
        submitButton.disabled = false;
        submitButton.classList.remove('button--disabled');
      } else {
        // Anytime no selection exists
        submitButton.disabled = true;
        submitButton.classList.add('button--disabled');
      }
    }
  }, [selectedId, name]);

  if (!data || data.length === 0) {
    console.error(new Error('[KVKBranchSelector] No branches available'));
    return (
      <div
        className="utrecht-form-field utrecht-form-field--text"
        ref={containerRef}
      >
        <p
          className="utrecht-paragraph"
          style={{ color: 'var(--color-red-notification)' }}
        >
          Er is een probleem opgetreden bij het laden van de vestigingen.
          Probeer de pagina te vernieuwen.
        </p>
      </div>
    );
  }

  if (!data) return <></>;

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
          onClick={handleInputClick}
          onFocus={handleInputFocus}
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

        {isOpen && (filtered?.length ?? 0) > 0 && (
          <div
            className="utrecht-listbox oip-combobox__popover oip-combobox__popover--block-end"
            role="listbox"
            id={`${id}-listbox`}
            aria-label={label}
          >
            <ul className="utrecht-listbox__list" ref={listRef}>
              {filtered?.map((item, i) => (
                <li
                  key={item.id}
                  role="option"
                  aria-selected={selectedId === item.id}
                  className={clsx('utrecht-listbox__option', {
                    'utrecht-listbox__option--selected': selectedId === item.id,
                    'utrecht-listbox__option--active': focusedIndex === i,
                  })}
                  onMouseDown={(e) => {
                    // Use onMouseDown to fire before click-outside handler
                    e.preventDefault();
                    e.stopPropagation();
                    handleSelect(item.id);
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
  );
};

export default KVKBranchSelector;
