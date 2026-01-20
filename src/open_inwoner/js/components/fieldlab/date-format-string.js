/**
 * Date Formatter Utility
 * Finds all oip-card elements and formats ISO 8601 dates in .card__footer-text
 * Converts: "2025-08-11T11:54:09.418689+02:00" to "11 Aug 2025"
 */

(function formatCardDates() {
  /**
   * Format ISO 8601 date string to readable format (e.g., "11 Aug 2025")
   * @param {string} isoDate - ISO 8601 formatted date string
   * @returns {string} - Formatted date string
   */
  function formatISODate(isoDate) {
    try {
      const date = new Date(isoDate);

      // Check if date is valid
      if (isNaN(date.getTime())) {
        return isoDate;
      }

      // Format options: day month year
      const options = {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      };

      return date.toLocaleDateString('en-US', options);
    } catch (error) {
      console.error('Error formatting date:', isoDate, error);
      return isoDate;
    }
  }

  /**
   * Extract and format ISO dates from text
   * Handles formats like:
   * - "Aanvraagdatum: 2025-08-11T11:54:09.418689+02:00"
   * - "Created: 2025-08-11T11:54:09Z"
   * @param {string} text - Text containing ISO date
   * @returns {string} - Text with formatted date
   */
  function formatDateInText(text) {
    // Regex to match ISO 8601 dates
    // Matches: YYYY-MM-DDTHH:MM:SS with optional milliseconds and timezone
    const isoDateRegex =
      /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?/g;

    return text.replace(isoDateRegex, function (match) {
      return formatISODate(match);
    });
  }

  /**
   * Initialize date formatting for all oip-card elements
   * Runs when DOM is ready and also watches for dynamically added cards
   */
  function initializeCardDateFormatting() {
    // Select all oip-card elements
    const cards = document.querySelectorAll('oip-card');

    cards.forEach((card) => {
      // Find all .card__footer-text elements within the card
      const footerTexts = card.querySelectorAll('.card__footer-text');

      footerTexts.forEach((footerText) => {
        const originalText = footerText.textContent;
        const formattedText = formatDateInText(originalText);

        // Only update if text changed
        if (formattedText !== originalText) {
          footerText.textContent = formattedText;
        }
      });
    });
  }

  /**
   * Run initialization when DOM is ready
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCardDateFormatting);
  } else {
    // DOM is already loaded
    initializeCardDateFormatting();
  }

  /**
   * Watch for dynamically added cards (optional)
   * Uses MutationObserver to handle cards added after page load
   */
  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.addedNodes.length) {
        // Re-run formatting on any newly added nodes
        initializeCardDateFormatting();
      }
    });
  });

  // Start observing the document for changes
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
})();
