import { renderHook } from '@testing-library/preact';
import { afterEach, describe, expect, it } from 'vitest';
import { type AfvalFilterConfig, AfvalFilterTypes, useAfvalFilter } from '..';
import { IntlWrapperNL } from '@react/lib/decorators/web-component';

const wrapper = IntlWrapperNL;

const fullConfig: AfvalFilterConfig = {
  periode: [2024, 2025],
  afval_types: [
    { value: 'rest', label: 'Restafval' },
    { value: 'gft', label: 'GFT' },
  ],
  addresses: ['Kerkstraat 12', 'Dorpslaan 5'],
};

describe('useAfvalFilter', () => {
  afterEach(() => {
    history.pushState({}, '', window.location.pathname);
  });

  describe('filterGroups', () => {
    it('creates a period group from config.period', () => {
      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });
      const periodGroup = result.current.filterGroups.find(
        (g) => g.name === 'periode'
      );

      expect(periodGroup).toBeDefined();
      expect(periodGroup!.label).toBe('Periode');
      expect(periodGroup!.choices).toEqual([
        { label: 'Jaar 2024', value: '2024' },
        { label: 'Jaar 2025', value: '2025' },
      ]);
    });

    it('creates an afval-type group from config.afval_types', () => {
      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });
      const typeGroup = result.current.filterGroups.find(
        (g) => g.name === 'afval-type'
      );

      expect(typeGroup).toBeDefined();
      expect(typeGroup!.label).toBe('Type container');
      expect(typeGroup!.choices).toEqual([
        { value: 'rest', label: 'Restafval' },
        { value: 'gft', label: 'GFT' },
      ]);
    });

    it('creates an adres group from config.addresses', () => {
      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });
      const adresGroup = result.current.filterGroups.find(
        (g) => g.name === 'adres'
      );

      expect(adresGroup).toBeDefined();
      expect(adresGroup!.label).toBe('Adres');
      expect(adresGroup!.choices).toEqual([
        { label: 'Kerkstraat 12', value: 'Kerkstraat 12' },
        { label: 'Dorpslaan 5', value: 'Dorpslaan 5' },
      ]);
    });

    it('omits period group when config.period is undefined', () => {
      const config: AfvalFilterConfig = {
        ...fullConfig,
        periode: undefined as any,
      };
      const { result } = renderHook(() => useAfvalFilter(config), {
        wrapper,
      });

      expect(
        result.current.filterGroups.find((g) => g.name === 'periode')
      ).toBeUndefined();
    });

    it('omits afval-type group when config.afval_types is undefined', () => {
      const config: AfvalFilterConfig = {
        ...fullConfig,
        afval_types: undefined as any,
      };
      const { result } = renderHook(() => useAfvalFilter(config), {
        wrapper,
      });

      expect(
        result.current.filterGroups.find((g) => g.name === 'afval-type')
      ).toBeUndefined();
    });

    it('omits adres group when config.addresses is undefined', () => {
      const config: AfvalFilterConfig = {
        ...fullConfig,
        addresses: undefined as any,
      };
      const { result } = renderHook(() => useAfvalFilter(config), {
        wrapper,
      });

      expect(
        result.current.filterGroups.find((g) => g.name === 'adres')
      ).toBeUndefined();
    });

    it('returns empty filterGroups when all config fields are undefined', () => {
      const config = {} as AfvalFilterConfig;
      const { result } = renderHook(() => useAfvalFilter(config), {
        wrapper,
      });

      expect(result.current.filterGroups).toEqual(
        [] satisfies typeof result.current.filterGroups
      );
    });

    it('preserves group order: period, afval-type, adres', () => {
      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });
      const names = result.current.filterGroups.map((g) => g.name);

      expect(names).toEqual([
        'periode',
        'afval-type',
        'adres',
      ] satisfies AfvalFilterTypes[]);
    });
  });

  describe('initialFilterState', () => {
    it('returns empty arrays when no URL params are present', () => {
      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });

      expect(result.current.initialFilterState).toEqual({
        periode: [],
        adres: [],
        'afval-type': [],
      } satisfies typeof result.current.initialFilterState);
    });

    it('reads period values from URL search params', () => {
      history.pushState({}, '', '?periode=2024');

      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });

      expect(result.current.initialFilterState.periode).toEqual([
        '2024',
      ] satisfies typeof result.current.initialFilterState.periode);
    });

    it('reads adres values from URL search params', () => {
      history.pushState({}, '', '?adres=Kerkstraat+12');

      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });

      expect(result.current.initialFilterState.adres).toEqual([
        'Kerkstraat 12',
      ] satisfies typeof result.current.initialFilterState.adres);
    });

    it('reads afval-type values from URL search params', () => {
      history.pushState({}, '', '?afval-type=rest&afval-type=gft');

      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });

      expect(result.current.initialFilterState['afval-type']).toEqual([
        'rest',
        'gft',
      ] satisfies (typeof result.current.initialFilterState)['afval-type']);
    });

    it('reads multiple filter types from URL simultaneously', () => {
      history.pushState(
        {},
        '',
        '?periode=2025&adres=Dorpslaan+5&afval-type=gft'
      );

      const { result } = renderHook(() => useAfvalFilter(fullConfig), {
        wrapper,
      });

      expect(result.current.initialFilterState).toEqual({
        periode: ['2025'],
        adres: ['Dorpslaan 5'],
        'afval-type': ['gft'],
      } satisfies typeof result.current.initialFilterState);
    });
  });
});
