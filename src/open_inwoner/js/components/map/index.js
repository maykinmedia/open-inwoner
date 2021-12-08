import "leaflet";

const leafletMaps = document.querySelectorAll(".leaflet--map")

class Map {
    constructor(node) {
        const lat = node.dataset.lat || 52;
        const lng = node.dataset.lng || 11;
        const zoom = node.dataset.zoom || 13;

        const map = L.map(node).setView([lat, lng], zoom);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    }
}


[...leafletMaps].forEach((leafletNode) => new Map(leafletNode))
