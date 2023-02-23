import 'leaflet'
import { RD_CRS } from './rd'
import { isMobile } from '../../lib/device/is-mobile'

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

    const mapOptions = {
      center: L.latLng(this.lat, this.lng),
      zoom: this.zoom,
      crs: RD_CRS,
    }

    const tileConfig = {
      url: `https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png`,
      options: {
        minZoom: 1,
        maxZoom: 13,
        attribution: `
          Kaartgegevens &copy;
            <a href="https://www.kadaster.nl">Kadaster</a> |
            <a href="https://www.verbeterdekaart.nl">Verbeter de kaart</a>
            `,
      },
    }

    this.map = L.map(this.node, mapOptions)
    const tileLayer = L.tileLayer(tileConfig.url, tileConfig.options)
    tileLayer.addTo(this.map)
    this.addGeoJSON()

    if (isMobile()) {
      this.map.dragging.disable()
    }
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
          maxWidth: 300,
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
    const displayName = name ? name : ''
    let finalHTML = ``

    Object.entries(properties).forEach((property) => {
      finalHTML += `<p class="p">${property[1]}</p>`
    })

    return `
        <div class="leaflet-content-name">
          <h4 class="h4">
            ${displayName}
          </h4>
        </div>
        <div class="leaflet-content-details p--no-margin">
          ${finalHTML}
        </div>
    `
  }
}

// Start!
;[...LEAFLET_MAPS].forEach((leafletNode) => new Map(leafletNode))
