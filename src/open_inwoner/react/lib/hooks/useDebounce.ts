import { useState, useEffect } from 'react';

/**
 * Custom React hook for debouncing a value.
 * Delays updating the returned value until after the specified delay
 * has elapsed since the last time the input value changed
 *
 * @template T - The type of the value being debounced.
 * @param value - The current value to debounce.
 * @param delay - The debounce delay in milliseconds.
 * @returns The debounced value that only updates after the delay period.
 */

export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);

    // Cleanup timer if value or delay changes before timeout
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}
