let map = L.map("map", {
  minZoom: 7,
  maxZoom: 20,
  maxBounds: [
    [32.5, 124.0],
    [39.5, 132.0]
  ],
  maxBoundsViscosity: 1.0
}).setView([36.5, 127.5], 7);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  minZoom: 5,
  maxZoom: 20
}).addTo(map);

const ZOOM_SIDO = 9;
const ZOOM_SGG = 11;

const icons = {
  차대차: L.icon({ iconUrl: "/static/icons/cvc.svg", iconSize: [32, 32] }),
  차량단독: L.icon({ iconUrl: "/static/icons/cs.svg", iconSize: [32, 32] }),
  차대사람: L.icon({ iconUrl: "/static/icons/cvm.svg", iconSize: [32, 32] })
};

let layerGroup = L.layerGroup().addTo(map);
let mouseLatLng = map.getCenter();

let currentYear = 2012;
let currentProvince = null;
let currentCity = null;

const provinceCache = new Map();
const cityCache = new Map();
const accidentCache = new Map();

function debounce(fn, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}

async function loadYears() {
  let res = await fetch('/api/years');
  let years = await res.json();
  let select = document.getElementById("yearSelect");
  select.innerHTML = years.map(y => `<option value="${y}">${y}</option>`).join('');
  select.addEventListener("change", () => {
    currentYear = select.value;
    if (currentProvince && currentCity) {
      loadAccidents(currentYear, currentProvince, currentCity);
    } else if (currentProvince) {
      loadCities(currentYear, currentProvince);
    } else {
      loadProvinces(currentYear);
    }
  });

  loadProvinces(select.value);
}

async function loadProvinces(year) {
  const key = `${year}`;
  if (provinceCache.has(key)) {
    renderProvinces(provinceCache.get(key));
    return;
  }
  let provinces = await fetchWithLoading(`/api/provinces?year=${year}`);
  provinceCache.set(key, provinces);
  renderProvinces(provinces);
}

function renderProvinces(provinces) {
  layerGroup.clearLayers();
  provinces.forEach(prov => {
    let marker = L.marker([prov.lat, prov.lng]).addTo(layerGroup);
    marker.bindPopup(prov.province);
    marker.bindTooltip(prov.province, { permanent: true, direction: 'top', offset: [-15, 0] }).openTooltip();
    marker.on("click", () => {
      currentProvince = prov.province;
      currentCity = null;
      map.flyTo(marker.getLatLng(), ZOOM_SIDO);
      loadCities(currentYear, prov.province);
    });
  });
}

async function loadCities(year, province) {
  const key = `${year}-${province}`;
  if (cityCache.has(key)) {
    renderCities(cityCache.get(key));
    return;
  }
  let cities = await fetchWithLoading(`/api/cities?year=${year}&province=${province}`);
  cityCache.set(key, cities);
  renderCities(cities);
}

function renderCities(cities) {
  layerGroup.clearLayers();
  cities.forEach(city => {
    let marker = L.marker([city.lat, city.lng]).addTo(layerGroup);
    marker.bindPopup(city.city);
    marker.bindTooltip(city.city, { permanent: true, direction: 'top', offset: [-10, -10] }).openTooltip();
    marker.on("click", () => {
      currentCity = city.city;
      map.flyTo(marker.getLatLng(), ZOOM_SGG);
      loadAccidents(currentYear, currentProvince, currentCity);
    });
  });
}

async function loadAccidents(year, province, city) {
  const key = `${year}-${province}-${city}`;
  if (accidentCache.has(key)) {
    renderAccidents(accidentCache.get(key));
    return;
  }
  let accidents = await fetchWithLoading(`/api/accidents?year=${year}&province=${province}&city=${city}`);
  accidentCache.set(key, accidents);
  renderAccidents(accidents);
}

function renderAccidents(accidents) {
  layerGroup.clearLayers();
  accidents.forEach(acc => {
    let icon = icons[acc.type_major] || icons["차대차"];
    let marker = L.marker([acc.lat, acc.lng], { icon }).addTo(layerGroup);
    marker.bindPopup(`<b>${acc.date}</b><br/>${acc.desc}`);
  });
}

loadYears();

map.on("mousemove", (e) => {
  mouseLatLng = e.latlng;
});

map.on("zoomend", debounce(() => {
  const zoom = map.getZoom();
  if (zoom < ZOOM_SIDO) {
    currentProvince = null;
    currentCity = null;
    loadProvinces(currentYear);
  } else if (zoom < ZOOM_SGG && zoom >= ZOOM_SIDO) {
    currentCity = null;
    if (currentProvince) {
      loadCities(currentYear, currentProvince);
    } else {
      let nearest = findNearestMarker();
      if (nearest) {
        const prov = nearest.getPopup()?.getContent();
        if (prov) {
          currentProvince = prov;
          loadCities(currentYear, currentProvince);
          map.flyTo(nearest.getLatLng(), ZOOM_SIDO);
        }
      }
    }
  } else if (zoom >= ZOOM_SGG) {
    if (currentProvince && currentCity) {
      loadAccidents(currentYear, currentProvince, currentCity);
    } else if (currentProvince) {
      let nearest = findNearestMarker();
      if (nearest) {
        const city = nearest.getPopup()?.getContent();
        if (city) {
          currentCity = city;
          loadAccidents(currentYear, currentProvince, currentCity);
          map.flyTo(nearest.getLatLng(), ZOOM_SGG);
        }
      }
    }
  }
}, 300));

function findNearestMarker() {
  let nearest = null;
  let minDist = Infinity;
  layerGroup.eachLayer(layer => {
    const dist = mouseLatLng.distanceTo(layer.getLatLng());
    if (dist < minDist) {
      minDist = dist;
      nearest = layer;
    }
  });
  return nearest;
}

const filterPanel = document.getElementById("filter-panel");
const toggleButton = document.getElementById("toggle-panel");

toggleButton.addEventListener("click", () => {
  filterPanel.classList.toggle("collapsed");
  toggleButton.textContent = filterPanel.classList.contains("collapsed") ? "▶" : "◀";
  setTimeout(() => map.invalidateSize(), 300);
});

const loadingIndicator = document.getElementById("loading-indicator");

function showLoading() {
  loadingIndicator.style.display = "block";
}

function hideLoading() {
  loadingIndicator.style.display = "none";
}

async function fetchWithLoading(url) {
  try {
    showLoading();
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    return data;
  } finally {
    hideLoading();
  }
}
