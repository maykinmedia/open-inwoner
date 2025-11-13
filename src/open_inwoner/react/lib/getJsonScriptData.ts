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
