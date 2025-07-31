/**
 * Utility function to get JSON data from a <script type="application/json"> tag.
 * Useful for injecting Django-rendered JSON into React.
 */
export function getJsonScriptData<T extends unknown>(id: string): T[] {
  const scriptElement = document.getElementById(id)

  if (scriptElement?.textContent) {
    try {
      return JSON.parse(scriptElement.textContent) as T[]
    } catch (e) {
      console.error(`Failed to parse JSON from <script id="${id}">`, e)
    }
  }

  return []
}
