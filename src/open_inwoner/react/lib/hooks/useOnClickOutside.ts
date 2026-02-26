import type { RefObject } from 'preact';
import { useEffect } from 'preact/hooks';

/**
 * Hook that triggers callback when clicking outside the referenced element
 *
 * @example
 * ```tsx
 * const ref = useRef<HTMLDivElement>(null);
 * useOnClickOutside(ref, () => setOpen(false), !isOpen);
 *
 * return <div ref={ref}>...</div>;
 * ```
 */
export const useOnClickOutside = (
  ref: RefObject<HTMLElement>,
  onClickOutside: () => void,
  disabled = false
) => {
  useEffect(() => {
    if (disabled) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClickOutside();
      }
    };

    document.addEventListener('click', handleClickOutside);

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [ref, disabled, onClickOutside]);
};
