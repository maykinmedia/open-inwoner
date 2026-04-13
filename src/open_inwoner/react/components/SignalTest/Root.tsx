import { useComputed, useSignal } from '@preact/signals';
import { type AnyComponent as AC } from 'preact';
import { usePropsOrScriptData } from '@react/lib/json/json';
import { ItemGroup, SignalTestContext } from './context';

interface RootConfig {
  groups: ItemGroup[];
}

export interface RootProps {
  data?: RootConfig;
  dataId?: string;
}

/**
 * oip-sig-root — mirrors oip-filters.
 * Reads config from a JSON script tag or `data` prop,
 * creates shared signal state, provides it via context.
 */
const Root: AC<RootProps> = ({ data, dataId, children }) => {
  const config = usePropsOrScriptData<RootConfig>(data, dataId);

  if (!config) return null;

  const selected = useSignal<Record<string, string[]>>(
    Object.fromEntries(config.groups.map((g) => [g.name, []]))
  );

  const isAnySelected = useComputed(() =>
    Object.values(selected.value).some((v) => v.length > 0)
  );

  const toggle = (group: string, item: string) => {
    const current = selected.value[group] ?? [];
    const next = current.includes(item)
      ? current.filter((i) => i !== item)
      : [...current, item];
    selected.value = { ...selected.value, [group]: next };
  };

  const clear = () => {
    selected.value = Object.fromEntries(
      Object.keys(selected.value).map((k) => [k, []])
    );
  };

  return (
    <SignalTestContext.Provider
      value={{ groups: config.groups, selected, isAnySelected, toggle, clear }}
    >
      {children}
    </SignalTestContext.Provider>
  );
};

export default Root;
