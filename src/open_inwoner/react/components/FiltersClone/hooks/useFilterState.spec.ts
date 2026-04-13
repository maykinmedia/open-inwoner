import { act, renderHook } from '@testing-library/preact';
import { describe, expect, it } from 'vitest';
import { FilterState, useFilterState } from '..';

const emptyState: FilterState = {
  color: [],
  size: [],
};

const prefilledState: FilterState = {
  color: ['red'],
  size: ['small', 'large'],
};

describe('useFilterState', () => {
  describe('initial state', () => {
    it('returns the initial filter state as selectedFilters', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      expect(result.current.selectedFilters.value).toEqual(emptyState);
    });

    it('returns pre-filled initial state correctly', () => {
      const { result } = renderHook(() => useFilterState(prefilledState));

      expect(result.current.selectedFilters.value).toEqual(prefilledState);
    });

    it('is not dirty when no changes have been made', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      expect(result.current.isDirty.value).toBe(false);
    });
  });

  describe('toggleValue', () => {
    it('adds a value to an empty group', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      act(() => {
        result.current.toggleValue('color', 'red');
      });

      expect(result.current.selectedFilters.value.color).toEqual(['red']);
    });

    it('removes a value that is already selected (toggle off)', () => {
      const { result } = renderHook(() => useFilterState(prefilledState));

      act(() => {
        result.current.toggleValue('color', 'red');
      });

      expect(result.current.selectedFilters.value.color).toEqual([]);
    });

    it('adds a second value to a group with an existing selection', () => {
      const { result } = renderHook(() =>
        useFilterState({ ...emptyState, color: ['red'] })
      );

      act(() => {
        result.current.toggleValue('color', 'blue');
      });

      expect(result.current.selectedFilters.value.color).toEqual([
        'red',
        'blue',
      ]);
    });

    it('does not affect other groups', () => {
      const { result } = renderHook(() => useFilterState(prefilledState));

      act(() => {
        result.current.toggleValue('color', 'red');
      });

      expect(result.current.selectedFilters.value.size).toEqual([
        'small',
        'large',
      ]);
    });

    it('handles toggling a value for a non-existent group', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      act(() => {
        result.current.toggleValue('unknown', 'value');
      });

      expect(result.current.selectedFilters.value.unknown).toEqual(['value']);
    });
  });

  describe('clearAllFilters', () => {
    it('clears all selected filters', () => {
      const { result } = renderHook(() => useFilterState(prefilledState));

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.selectedFilters.value).toEqual({
        color: [],
        size: [],
      });
    });

    it('is a no-op when all filters are already empty', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.selectedFilters.value).toEqual(emptyState);
    });
  });

  describe('isDirty', () => {
    it('becomes true after toggling a value', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      act(() => {
        result.current.toggleValue('color', 'red');
      });

      expect(result.current.isDirty.value).toBe(true);
    });

    it('becomes false when toggled back to initial state', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      act(() => {
        result.current.toggleValue('color', 'red');
      });
      expect(result.current.isDirty.value).toBe(true);

      act(() => {
        result.current.toggleValue('color', 'red');
      });
      expect(result.current.isDirty.value).toBe(false);
    });

    it('becomes true after clearing pre-filled filters', () => {
      const { result } = renderHook(() => useFilterState(prefilledState));

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.isDirty.value).toBe(true);
    });

    it('is not dirty when clearing already-empty filters', () => {
      const { result } = renderHook(() => useFilterState(emptyState));

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.isDirty.value).toBe(false);
    });
  });
});
