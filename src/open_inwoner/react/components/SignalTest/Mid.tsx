import { type AnyComponent as AC } from 'preact';
import { useSignalTest } from './context';

export interface ListProps {
  name: string;
  checkbox?: boolean;
}

/**
 * oip-sig-list — mirrors oip-filter.
 * Looks up its group by `name` from context.
 * Renders checkboxes and writes to the shared signal on change.
 * If oip-sig-summary updates when these are clicked, cross-shadow signals work.
 */
const List: AC<ListProps> = ({ name, checkbox = true }) => {
  const { groups, selected, toggle } = useSignalTest();
  const group = groups.find((g) => g.name === name);

  if (!group) return <p>Unknown group: {name}</p>;

  const selectedItems = selected.value[name] ?? [];

  return (
    <fieldset style="border: 2px solid steelblue; padding: 8px; margin: 4px 0;">
      <legend>{name}</legend>
      {group.items.map((item) => (
        <label key={item} style="display: block; cursor: pointer;">
          <input
            type={checkbox ? 'checkbox' : 'radio'}
            checked={selectedItems.includes(item)}
            name={name}
            onChange={() => toggle(name, item)}
          />
          {item}
        </label>
      ))}
    </fieldset>
  );
};

export default List;
