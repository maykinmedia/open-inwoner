import { useEffect, useRef } from 'preact/hooks';
import { RefObject } from 'preact';

/**
 * Returns a typeahead handler for keyboard-driven option search.
 *
 * Buffers successive keypresses and focuses the first option whose label
 * starts with (or contains) the accumulated query. The buffer resets after
 * 500 ms of inactivity.
 */
export function useTypeahead<T extends HTMLElement>(
  containerRef: RefObject<HTMLElement>,
  getOptions: (container: HTMLElement) => T[],
  focusOption: (el: T) => void,
  getLabelForValue: (value: string) => string
) {
  const buffer = useRef('');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    []
  );

  return (key: string): void => {
    buffer.current += key.toLowerCase();

    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      buffer.current = '';
    }, 500);

    const options = containerRef.current
      ? getOptions(containerRef.current)
      : [];
    const focusedIndex = options.findIndex((el) => el.matches(':focus-within'));
    const startIndex = focusedIndex >= 0 ? focusedIndex + 1 : 0;
    const query = buffer.current;

    for (let i = 0; i < options.length; i++) {
      const index = (startIndex + i) % options.length;
      const label = getLabelForValue(
        options[index].getAttribute('value') ?? ''
      ).toLowerCase();
      if (label.startsWith(query) || label.includes(query)) {
        focusOption(options[index]);
        break;
      }
    }
  };
}
