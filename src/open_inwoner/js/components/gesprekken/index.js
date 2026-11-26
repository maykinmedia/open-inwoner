/**
 * Mijn gesprekken: sla de periodieke verversing over zolang de inwoner iets aan het
 * invullen is. Dit staat hier en niet als filter in hx-trigger, omdat OIP
 * htmx.config.allowEval uitzet (filters worden dan niet uitgevoerd en geven htmx:evalDisallowedError).
 */
const bezig = () => {
  const sectie = document.getElementById('gesprekken');
  if (!sectie) return false;
  if (sectie.querySelector('textarea:focus, input:focus, details[open]'))
    return true;
  return [...sectie.querySelectorAll('textarea, input[type=file]')].some(
    (veld) => (veld.value || '').trim() !== ''
  );
};

document.addEventListener('htmx:beforeRequest', (event) => {
  const elt = event.detail && event.detail.elt;
  // Alleen de polling zelf (de sectie); tabs en formulieren gaan altijd door.
  if (elt && elt.id === 'gesprekken' && bezig()) {
    event.preventDefault();
  }
});
