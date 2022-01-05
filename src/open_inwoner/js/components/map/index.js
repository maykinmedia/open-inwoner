import 'leaflet'

/** @type {NodeListOf<Element>} All the leaflet maps. */
const LEAFLET_MAPS = document.querySelectorAll('.map__leaflet')

/**
 * Renders a (Leaflet) map.
 */
class Map {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    this.node = node
    this.lat = node.dataset.lat || 52
    this.lng = node.dataset.lng || 11
    this.zoom = node.dataset.zoom || 13

    this.map = L.map(this.node).setView([this.lat, this.lng], this.zoom)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(this.map)

    this.addGeoJSON()
  }

  /**
   * Adds geoJSON found in data-geojson-feature-collection.
   */
  addGeoJSON() {
    this.geoJSON = this.node.dataset.geojsonFeatureCollection

    if (!this.geoJSON) {
      return
    }

    const data = JSON.parse(this.geoJSON)
    L.geoJSON(data, {
      onEachFeature: (feature, layer) =>
        layer.bindPopup(this.featureToHTML(feature), {
          maxWidth: 150,
        }),
    }).addTo(this.map)
  }

  /**
   * Renders a feature as html.
   * @param {Object} feature
   * @return {string}
   */
  featureToHTML(feature) {
    const { name, ...properties } = feature.properties
    return `<h4 class="h4">${name}</h4><p class="p">${Object.values(
      properties
    ).join(' ')}</p>`
  }
}

// Start!
;[...LEAFLET_MAPS].forEach((leafletNode) => new Map(leafletNode))
