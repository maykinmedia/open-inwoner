/**
 * Utility function to get JSON data from a <script type="application/json"> tag.
 * Useful for injecting Django-rendered JSON into React components.
 * @param id The HTML id of the script element
 * @returns The parsed JSON data or undefined if not found/invalid
 */
export function getJsonFromScriptTag<T = unknown>(id: string): T | undefined {
  const scriptElement = document.getElementById(id)
  if (!scriptElement?.textContent) {
    return undefined
  }

  return parseJsonSafely<T>(scriptElement.textContent)
}

/**
 * Safely parse JSON string with error handling.
 * @param text The JSON string to parse
 * @returns The parsed JSON data or undefined if parsing fails
 */
export function parseJsonSafely<T = unknown>(
  text: string | null | undefined
): T | undefined {
  if (!text || typeof text !== 'string') {
    return undefined
  }

  try {
    return JSON.parse(text) as T
  } catch (error) {
    console.error(`Failed to parse JSON: ${text}`, error)
    return undefined
  }
}
