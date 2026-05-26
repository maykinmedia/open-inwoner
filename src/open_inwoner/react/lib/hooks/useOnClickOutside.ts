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
  ref: RefObject<HTMLElement | undefined>,
  onClickOutside: () => void,
  disabled = false
) => {
  useEffect(() => {
    if (disabled) return;

    const handleClickOutside = (e: MouseEvent) => {
      // Use composedPath() instead of contains() so clicks on slotted children
      // (light DOM nodes projected into a shadow root via <slot>) are correctly
      // treated as "inside" the container — contains() only walks the flat DOM
      // tree and returns false for slotted/shadow-DOM nodes.
      if (ref.current && !e.composedPath().includes(ref.current)) {
        onClickOutside();
      }
    };

    document.addEventListener('click', handleClickOutside);

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [ref, disabled, onClickOutside]);
};
