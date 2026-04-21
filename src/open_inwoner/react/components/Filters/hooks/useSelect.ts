import { useEffect, useRef, useState } from 'preact/hooks';
import { type IFilterChoice } from '..';

interface UseSelectOptions {
  choices: IFilterChoice[];
  multiple: boolean;
  name: string;
  toggleValue: (name: string, value: string) => void;
  toggleValueRadio: (name: string, value: string) => void;
}

export const useSelect = ({
  choices,
  multiple,
  name,
  toggleValue,
  toggleValueRadio,
}: UseSelectOptions) => {
  const containerRef = useRef<HTMLElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const typeaheadBuffer = useRef('');
  const typeaheadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionRefs = useRef(new Map<string, HTMLElement>());

  const setOptionRef = (value: string, el: HTMLElement | null) => {
    if (el) optionRefs.current.set(value, el);
    else optionRefs.current.delete(value);
  };

  const openDropdown = () => {
    setIsOpen(true);
    setActiveIndex(0);
  };

  const closeDropdown = () => {
    setIsOpen(false);
    setActiveIndex(-1);
  };

  const toggleDropdown = () => setIsOpen((prev) => !prev);

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        if (!isOpen) break;
        e.preventDefault();
        closeDropdown();
        break;

      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) openDropdown();
        else
          setActiveIndex((prev) =>
            prev < choices.length - 1 ? prev + 1 : prev
          );
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (!isOpen) openDropdown();
        else setActiveIndex((prev) => (prev >= 0 ? prev - 1 : prev));
        break;

      case 'Tab':
        closeDropdown();
        break;

      case 'Enter':
      case ' ':
        if (activeIndex >= 0) {
          e.preventDefault();
          const choice = choices[activeIndex];
          if (multiple) toggleValue(name, choice.value);
          else toggleValueRadio(name, choice.value);
        }
        break;

      default:
        if (
          e.key.length === 1 &&
          !e.ctrlKey &&
          !e.metaKey &&
          !e.altKey &&
          !e.isComposing
        ) {
          if (!isOpen) setIsOpen(true);

          typeaheadBuffer.current += e.key.toLowerCase();
          if (typeaheadTimer.current) clearTimeout(typeaheadTimer.current);
          typeaheadTimer.current = setTimeout(() => {
            typeaheadBuffer.current = '';
          }, 500);

          const query = typeaheadBuffer.current;
          const startIndex = activeIndex >= 0 ? activeIndex + 1 : 0;
          for (let i = 0; i < choices.length; i++) {
            const index = (startIndex + i) % choices.length;
            const label = choices[index].label.toLowerCase();
            if (label.startsWith(query) || label.includes(query)) {
              setActiveIndex(index);
              break;
            }
          }
        }
        break;
    }
  };

  useEffect(() => {
    const activeValue = choices[activeIndex]?.value;
    if (!activeValue) return;
    optionRefs.current.get(activeValue)?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  useEffect(() => {
    return () => {
      if (typeaheadTimer.current) clearTimeout(typeaheadTimer.current);
    };
  }, []);

  return {
    containerRef,
    isOpen,
    activeIndex,
    handleKeyDown,
    closeDropdown,
    toggleDropdown,
    setOptionRef,
  };
};
