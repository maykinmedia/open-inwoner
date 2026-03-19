/**
 * Formats a file size given in bytes into a human-readable string.
 *
 * Input:
 *   - size: number or string representing the file size in bytes.
 *           (As provided by Django's File.size or Filer, i.e., an integer in bytes.)
 *           If the string contains thousand separators (e.g., "1.322.028"),
 *           they will be removed automatically.
 *
 * Output:
 *   - Human-readable string with units: Bytes, KB, MB, GB, etc.
 *     Rounded to two decimal places.
 *
 * Examples:
 *   formatFileSize(1322028)      -> "1.26 MB"
 *   formatFileSize("1.322.028")  -> "1.26 MB"
 *   formatFileSize(13)            -> "13 Bytes"
 */
export const formatFileSize = (size: string | number): string => {
  // Convert string with thousand separators into a number
  let bytes = typeof size === 'string' ? Number(size.replace(/\./g, '')) : size;
  if (isNaN(bytes)) return String(size);

  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  let i = 0;

  // Divide bytes by 1024 until we find the right unit
  while (bytes >= 1024 && i < sizes.length - 1) {
    bytes /= 1024;
    i++;
  }

  // Round to 2 decimals and append unit
  return `${Math.round(bytes * 100) / 100} ${sizes[i]}`;
};
