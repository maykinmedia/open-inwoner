/**
 * Utility function to get JSON data from a <script type="application/json"> tag.
 * Useful for injecting Django-rendered JSON into React components.
 * @param id The HTML id of the script element
 * @returns The parsed JSON data or undefined if not found/invalid
 */
export function getJsonFromScriptTag<T = unknown>(id: string): T | undefined {
  const scriptElement = document.getElementById(id);
  if (!scriptElement?.textContent) {
    return undefined;
  }

  try {
    return JSON.parse(scriptElement.textContent) as T;
  } catch (error) {
    console.error('Failed to parse JSON:', scriptElement.textContent, error);
    return undefined;
  }
}

/**
 * Simple utility to get JSON data from either props or a script tag.
 * Follows the Single Responsibility Principle - only handles data retrieval.
 *
 * @param data Direct data from props
 * @param id HTML id of a script tag containing JSON
 * @returns The data or null if no data is available
 *
 * @example
 * // Get data from props or script tag
 * const rawItems = getDataFromPropOrJsonScript(props.items, props.itemsId);
 * if (!rawItems) return null;
 *
 * // Then transform it explicitly
 * const normalized = Array.isArray(rawItems[0]) ? rawItems : [rawItems];
 */
export function usePropsOrScriptData<T>(data?: T, id?: string): T | null {
  if (!id && !data) return null;
  return id ? (getJsonFromScriptTag<T>(id) ?? null) : (data ?? null);
}
