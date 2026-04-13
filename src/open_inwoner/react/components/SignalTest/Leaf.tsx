import { type AnyComponent as AC } from 'preact';
import { useSignalTest } from './context';

/**
 * oip-sig-summary — mirrors oip-filter-chips.
 * Purely a reader: shows what's selected across ALL groups
 * and has a "clear" button.
 * This component lives in its own shadow root — if it updates
 * when oip-sig-list checkboxes are clicked, cross-shadow signals work.
 */
const Summary: AC<{}> = () => {
  const { groups, selected, isAnySelected, clear } = useSignalTest();

  return (
    <div style="border: 2px dashed tomato; padding: 8px; margin: 4px 0;">
      <strong>Summary</strong>
      {!isAnySelected.value ? (
        <p>Nothing selected</p>
      ) : (
        <>
          <ul>
            {groups.map((g) => {
              const items = selected.value[g.name] ?? [];
              if (!items.length) return null;
              return (
                <li key={g.name}>
                  <strong>{g.name}:</strong> {items.join(', ')}
                </li>
              );
            })}
          </ul>
          <button type="button" onClick={clear}>
            Clear all
          </button>
        </>
      )}
    </div>
  );
};

export default Summary;
