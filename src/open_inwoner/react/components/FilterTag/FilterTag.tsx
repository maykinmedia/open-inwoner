import { AnyComponent as AC } from 'preact';
import { MaterialIcon } from '../MaterialIcon';
import './FilterTag.scss';

export interface IFilterTagProps {
  currentUrl?: string;
  baseUrl?: string;
}

const FilterTag: AC<IFilterTagProps> = ({ currentUrl = '', baseUrl = '' }) => {
  console.log(
    'FilterTag: Component mounted, currentUrl:',
    currentUrl,
    'baseUrl:',
    baseUrl
  );

  const parseActiveTags = () => {
    console.log('FilterTag: parseActiveTags called');

    // Use window.location if currentUrl is empty
    const urlToUse = currentUrl || window.location.href;
    console.log('FilterTag: Using URL:', urlToUse);

    if (!urlToUse) {
      console.log('FilterTag: No URL available');
      return [];
    }

    try {
      const url = new URL(urlToUse);
      console.log('FilterTag: URL parsed:', url.toString());
      console.log('FilterTag: Search params:', url.search);

      const params = new URLSearchParams(url.search);
      console.log('FilterTag: URLSearchParams created');

      const active: Array<{ key: string; value: string; index: number }> = [];

      // Log all params
      params.forEach((value, key) => {
        console.log(`FilterTag: Found param: ${key}=${value}`);
      });

      // Now extract active filters
      const seenKeys: Record<string, number> = {};
      params.forEach((value, key) => {
        console.log(`FilterTag: Processing param: key=${key}, value=${value}`);

        // Skip non-filter params
        if (key === 'query') {
          console.log('FilterTag: Skipping query param');
          return;
        }

        if (!seenKeys[key]) {
          seenKeys[key] = 0;
        }

        active.push({ key, value, index: seenKeys[key] });
        console.log(
          `FilterTag: Added tag: ${key}=${value} (index ${seenKeys[key]})`
        );
        seenKeys[key]++;
      });

      console.log('FilterTag: Total active tags:', active.length, active);
      return active;
    } catch (error) {
      console.error('FilterTag: Error parsing URL:', error);
      return [];
    }
  };

  const handleRemoveTag = (filterKey: string, filterValue: string) => {
    console.log(
      `FilterTag: handleRemoveTag called: ${filterKey}=${filterValue}`
    );

    // Use current window location, not baseUrl
    const currentUrl = window.location.href;
    const url = new URL(currentUrl);
    const params = new URLSearchParams(url.search);

    const allValues = params.getAll(filterKey);
    console.log(`FilterTag: All values for ${filterKey}:`, allValues);

    // Remove the key entirely first
    params.delete(filterKey);

    // Re-add all values except the one we're removing
    allValues.forEach((val) => {
      if (val !== filterValue) {
        params.append(filterKey, val);
      }
    });

    // Build new URL keeping pathname, changing only search params
    const newUrl = params.toString()
      ? `${url.pathname}?${params.toString()}`
      : url.pathname;

    console.log(`FilterTag: Current URL:`, currentUrl);
    console.log(`FilterTag: New URL:`, newUrl);
    window.history.pushState({}, '', newUrl);
    window.location.reload();
  };

  const activeTags = parseActiveTags();

  console.log('FilterTag: Rendering with', activeTags.length, 'tags');

  if (activeTags.length === 0) {
    console.log('FilterTag: No active tags, returning null');
    return null;
  }

  console.log('FilterTag: Rendering', activeTags.length, 'tag buttons');

  return (
    <div class="oip-filter-tags">
      {activeTags.map(({ key, value }) => {
        console.log(`FilterTag: Rendering tag button for ${key}=${value}`);
        return (
          <button
            key={`${key}-${value}`}
            class="oip-filter-tag"
            onClick={() => handleRemoveTag(key, value)}
            title={`Verwijder filter: ${value}`}
            type="button"
          >
            <span class="oip-filter-tag__label">{value}</span>
            <MaterialIcon
              name="close"
              extraClassName={['oip-filter-tag__close']}
              aria-hidden="true"
            />
          </button>
        );
      })}
    </div>
  );
};

export default FilterTag;
