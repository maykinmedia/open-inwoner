/**
 * Returns whether the browser seems to be a mobile device.
 */
export const isMobile = () => {
  try {
    return window.matchMedia('(max-width: 767px)').matches
  } catch (e) {
    return false
  }
}
