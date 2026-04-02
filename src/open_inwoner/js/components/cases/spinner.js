const notifyLoading = (e) => {
  // Generic: announce loading for any HTMX element with data-spinner-live-region
  const regionId = e.detail.elt && e.detail.elt.dataset.spinnerLiveRegion;
  if (!regionId) return;
  const region = document.getElementById(regionId);
  if (region) region.textContent = 'Gegevens laden...';
};

const dismissNotifyLoading = (e) => {
  // Generic: announce loaded for any HTMX element with data-spinner-live-region
  const regionId = e.detail.elt && e.detail.elt.dataset.spinnerLiveRegion;
  if (!regionId) return;
  const region = document.getElementById(regionId);
  if (region) region.textContent = 'Gegevens zijn geladen.';
};

document.addEventListener('DOMContentLoaded', function () {
  const htmx = window.htmx;

  // Show the spinner before an HTMX request starts
  htmx.on('htmx:beforeRequest', function (e) {
    if (!e.detail) return;

    if (
      e.detail.target.id === 'cases-content' ||
      e.detail.target.id === 'submissions-content'
    ) {
      // Show the spinner
      document
        .getElementById('spinner-container')
        .classList.remove('loader-container--hide');
      // Hide the swappable content
      document
        .getElementById('cases-content')
        .classList.add('cases__spinner--hide');
    }

    notifyLoading(e);
  });

  // Hide the spinner after the content is swapped
  htmx.on('htmx:afterSwap', function (e) {
    if (!e.detail) return;

    if (
      e.detail.target.id === 'cases-content' ||
      e.detail.target.id === 'submissions-content'
    ) {
      // Hide the spinner
      document
        .getElementById('spinner-container')
        .classList.add('loader-container--hide');
      // Show the swappable content
      document
        .getElementById('cases-content')
        .classList.remove('cases__spinner--hide');
    }

    dismissNotifyLoading(e);
  });
});
