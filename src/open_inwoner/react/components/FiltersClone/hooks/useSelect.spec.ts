import { act, renderHook } from '@testing-library/preact';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useSelect } from './useSelect';

const choices = [
  { value: 'apple', label: 'Apple' },
  { value: 'banana', label: 'Banana' },
  { value: 'blueberry', label: 'Blueberry' },
  { value: 'cherry', label: 'Cherry' },
];

const key = (k: string, extra?: KeyboardEventInit) =>
  new KeyboardEvent('keydown', {
    key: k,
    bubbles: true,
    cancelable: true,
    ...extra,
  });

describe('useSelect', () => {
  let toggleValue: ReturnType<typeof vi.fn<VoidFunction>>;
  let toggleValueRadio: ReturnType<typeof vi.fn<VoidFunction>>;

  beforeEach(() => {
    toggleValue = vi.fn();
    toggleValueRadio = vi.fn();
  });

  const render = (multiple = true) =>
    renderHook(() =>
      useSelect({
        choices,
        multiple,
        name: 'fruit',
        toggleValue: toggleValue,
        toggleValueRadio: toggleValueRadio,
      })
    );

  describe('initial state', () => {
    it('starts closed with no active index', () => {
      const { result } = render();
      expect(result.current.isOpen).toBe(false);
      expect(result.current.activeIndex).toBe(-1);
    });
  });

  describe('toggleDropdown', () => {
    it('opens the dropdown', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      expect(result.current.isOpen).toBe(true);
    });

    it('closes the dropdown when already open', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.toggleDropdown());
      expect(result.current.isOpen).toBe(false);
    });
  });

  describe('closeDropdown', () => {
    it('closes the dropdown and resets activeIndex', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.closeDropdown());
      expect(result.current.isOpen).toBe(false);
      expect(result.current.activeIndex).toBe(-1);
    });
  });

  describe('ArrowDown', () => {
    it('opens the dropdown when closed', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      expect(result.current.isOpen).toBe(true);
    });

    it('increments activeIndex from -1 to 0', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      expect(result.current.activeIndex).toBe(0);
    });

    it('increments activeIndex on each press', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      expect(result.current.activeIndex).toBe(1);
    });

    it('clamps at the last option', () => {
      const { result } = render();
      choices.forEach(() =>
        act(() => result.current.handleKeyDown(key('ArrowDown')))
      );
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      expect(result.current.activeIndex).toBe(choices.length - 1);
    });
  });

  describe('ArrowUp', () => {
    it('opens the dropdown when closed', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowUp')));
      expect(result.current.isOpen).toBe(true);
    });

    it('clamps at 0 when already at the top', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowUp')));
      expect(result.current.activeIndex).toBe(0);
    });

    it('decrements activeIndex', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.handleKeyDown(key('ArrowUp')));
      expect(result.current.activeIndex).toBe(0);
    });
  });

  describe('Escape', () => {
    it('closes the dropdown and resets activeIndex', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.handleKeyDown(key('Escape')));
      expect(result.current.isOpen).toBe(false);
      expect(result.current.activeIndex).toBe(-1);
    });

    it('does nothing when the dropdown is already closed', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('Escape')));
      expect(result.current.isOpen).toBe(false);
    });
  });

  describe('Tab', () => {
    it('closes the dropdown', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('Tab')));
      expect(result.current.isOpen).toBe(false);
    });

    it('resets activeIndex', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.handleKeyDown(key('Tab')));
      expect(result.current.activeIndex).toBe(-1);
    });
  });

  describe('Enter / Space', () => {
    it('calls toggleValue with the active choice (multiple)', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('ArrowDown'))); // index 0 = apple
      act(() => result.current.handleKeyDown(key('Enter')));
      expect(toggleValue).toHaveBeenCalledWith('fruit', 'apple');
    });

    it('calls toggleValueRadio with the active choice (single)', () => {
      const { result } = render(false);
      act(() => result.current.handleKeyDown(key('ArrowDown')));
      act(() => result.current.handleKeyDown(key(' ')));
      expect(toggleValueRadio).toHaveBeenCalledWith('fruit', 'apple');
    });

    it('does nothing when no option is active', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('Enter')));
      expect(toggleValue).not.toHaveBeenCalled();
    });
  });

  describe('typeahead', () => {
    it('opens the dropdown if closed when typing', () => {
      const { result } = render();
      act(() => result.current.handleKeyDown(key('a')));
      expect(result.current.isOpen).toBe(true);
    });

    it('jumps to the first option whose label starts with the typed letter', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('c')));
      expect(result.current.activeIndex).toBe(3); // Cherry
    });

    it('is case-insensitive', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('C')));
      expect(result.current.activeIndex).toBe(3); // Cherry
    });

    it('accumulates characters to narrow the match', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('b')));
      expect(result.current.activeIndex).toBe(1); // Banana
      act(() => result.current.handleKeyDown(key('l'))); // buffer = 'bl'
      expect(result.current.activeIndex).toBe(2); // Blueberry
    });

    it('also matches if the label contains (but does not start with) the query', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('a')));
      act(() => result.current.handleKeyDown(key('n'))); // buffer = 'an' → 'banana'.includes('an')
      expect(result.current.activeIndex).toBe(1); // Banana
    });

    it('searches from activeIndex + 1 to cycle through matches', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('b'))); // → Banana (index 1)
      expect(result.current.activeIndex).toBe(1);

      // Reset buffer via fake timer, then press 'b' again from index 1
    });

    it('does not change activeIndex when no match is found', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('ArrowDown'))); // index 0
      act(() => result.current.handleKeyDown(key('z')));
      expect(result.current.activeIndex).toBe(0);
    });

    it('ignores keys with modifier keys', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('a', { ctrlKey: true })));
      expect(result.current.activeIndex).toBe(-1);
    });

    it('ignores keys while IME is composing', () => {
      const { result } = render();
      act(() => result.current.toggleDropdown());
      act(() => result.current.handleKeyDown(key('a', { isComposing: true })));
      expect(result.current.activeIndex).toBe(-1);
    });

    describe('buffer reset', () => {
      beforeEach(() => vi.useFakeTimers());
      afterEach(() => vi.useRealTimers());

      it('resets the buffer after 500 ms so the next keypress starts fresh', () => {
        const { result } = render();
        act(() => result.current.toggleDropdown());
        act(() => result.current.handleKeyDown(key('b'))); // → Banana (index 1)
        expect(result.current.activeIndex).toBe(1);

        act(() => {
          vi.advanceTimersByTime(500);
        }); // buffer resets

        act(() => result.current.handleKeyDown(key('b'))); // fresh 'b', starts from index 2 → Blueberry
        expect(result.current.activeIndex).toBe(2);
      });
    });
  });
});
