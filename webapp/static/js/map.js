// ===============================
// #region Constants & Global State
// ===============================
const ZOOM_SIDO = 9;
const ZOOM_SGG = 11;
let mouseLatLng = null;

const icons = {
  차대차: L.icon({ iconUrl: "/static/icons/cvc.svg", iconSize: [32, 32] }),
  차량단독: L.icon({ iconUrl: "/static/icons/cs.svg", iconSize: [32, 32] }),
  차대사람: L.icon({ iconUrl: "/static/icons/cvm.svg", iconSize: [32, 32] })
};

const provinceCache = new Map();
const cityCache = new Map();
const accidentCache = new Map();

// DOM elements
const filterPanel = document.getElementById("filter-panel");
const toggleButton = document.getElementById("toggle-panel");
const modeFilterCheckbox = document.getElementById("mode-filter");
const modeYearCheckbox = document.getElementById("mode-year");
const yearSelectContainer = document.getElementById("yearSelectContainer");
const yearSelect = document.getElementById("yearSelect");
const loadingIndicator = document.getElementById("loading-indicator");
const regionLabel = document.getElementById('visibleRegionInfo');

// ===============================
// #region Map Initialization
// ===============================
const map = L.map("map", {
  minZoom: 7,
  maxZoom: 20,
  maxBounds: [[32.5, 124.0], [39.5, 132.0]],
  maxBoundsViscosity: 1.0
}).setView([36.5, 127.5], 7);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  minZoom: 5,
  maxZoom: 20
}).addTo(map);

const provinceLayer = L.layerGroup().addTo(map);
const cityLayer = L.layerGroup();
const accidentLayer = L.layerGroup();
const filterAccidentLayer = L.markerClusterGroup(); // 필터용

map.on("mousemove", e => {
  mouseLatLng = e.latlng;
});

// ===============================
// #region Utility Functions
// ===============================
function debounce(fn, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), delay);
  };
}

function findNearestMarker(layerGroup) {
  let nearest = null;
  let minDist = Infinity;
  layerGroup.eachLayer(layer => {
    const dist = mouseLatLng ? mouseLatLng.distanceTo(layer.getLatLng()) : Infinity;
    if (dist < minDist) {
      minDist = dist;
      nearest = layer;
    }
  });
  return nearest;
}

async function fetchWithLoading(url) {
  try {
    showLoading();
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } finally {
    hideLoading();
  }
}

function clearAllLayers() {
  provinceLayer.clearLayers();
  cityLayer.clearLayers();
  accidentLayer.clearLayers();         // 연도별 보기용 마커 초기화
  filterAccidentLayer.clearLayers();   // 필터 모드 마커도 초기화
}

// ===============================
// #region Loading Controls
// ===============================
function showLoading() {
  loadingIndicator.style.display = "block";
}

function hideLoading() {
  loadingIndicator.style.display = "none";
}







// ===============================
// #region Year Marker Flow
// ===============================
async function loadYears() {
  const years = await fetchWithLoading('/api/years');
  yearSelect.innerHTML = years.map(y => `<option value="${y}">${y}</option>`).join('');
  currentYear = yearSelect.value;
  yearSelect.addEventListener("change", () => {
    currentYear = yearSelect.value;
    if (currentProvince && currentCity) {
      loadAccidents(currentYear, currentProvince, currentCity);
    } else if (currentProvince) {
      loadCities(currentYear, currentProvince);
    } else {
      loadProvinces(currentYear);
    }
  });
  loadProvinces(currentYear);
}

async function loadProvinces(year) {
  const key = `${year}`;
  if (provinceCache.has(key)) {
    renderProvinces(provinceCache.get(key));
    return;
  }
  const provinces = await fetchWithLoading(`/api/provinces?year=${year}`);
  provinceCache.set(key, provinces);
  renderProvinces(provinces);
}

function renderProvinces(provinces) {
  clearAllLayers();
  updateVisibleRegionLabel();

  map.addLayer(provinceLayer);
  provinces.forEach(prov => {
    const marker = L.marker([prov.lat, prov.lng]).addTo(provinceLayer);
    marker.bindPopup(prov.province);
    marker.bindTooltip(prov.province, { permanent: true, direction: 'top', offset: [-15, 0] }).openTooltip();
    marker.on("click", () => {
      if (currentProvince === prov.province) return;
      currentProvince = prov.province;
      currentCity = null;
      map.flyTo(marker.getLatLng(), ZOOM_SIDO);
      loadCities(currentYear, currentProvince);
    });
  });
}

async function loadCities(year, province) {
  const key = `${year}-${province}`;
  if (cityCache.has(key)) {
    renderCities(cityCache.get(key));
    return;
  }
  const cities = await fetchWithLoading(`/api/cities?year=${year}&province=${province}`);
  cityCache.set(key, cities);
  renderCities(cities);
}

function renderCities(cities) {
  clearAllLayers();
  updateVisibleRegionLabel();

  map.addLayer(cityLayer);
  cities.forEach(city => {
    const marker = L.marker([city.lat, city.lng]).addTo(cityLayer);
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
  const accidents = await fetchWithLoading(`/api/accidents?year=${year}&province=${province}&city=${city}`);
  accidentCache.set(key, accidents);
  renderAccidents(accidents);
}

function renderAccidents(accidents) {
  clearAllLayers();
  updateVisibleRegionLabel();

  map.addLayer(accidentLayer);
  accidents.forEach(acc => {
    const icon = icons[acc.type_major] || icons["차대차"];
    const marker = L.marker([acc.lat, acc.lng], { icon }).addTo(accidentLayer);
    marker.bindPopup(`<b>${acc.date}</b><br/>${acc.desc}`);
  });
}

function updateVisibleRegionLabel() {
  if (currentProvince && currentCity) {
    regionLabel.textContent = `표시 중인 지역: ${currentProvince} ${currentCity}`;
  } else if (currentProvince) {
    regionLabel.textContent = `표시 중인 지역: ${currentProvince}`;
  } else {
    regionLabel.textContent = `표시 중인 지역: 전체`;
  }
}

// ===============================
// #region Zoom Behavior (Year Mode Only)
// ===============================
map.on("zoomend", debounce(() => {
  if (!modeYearCheckbox.checked) return;

  const zoom = map.getZoom();
  if (zoom < ZOOM_SIDO) {
    currentProvince = null;
    currentCity = null;
    loadProvinces(currentYear);
  } else if (zoom < ZOOM_SGG) {
    currentCity = null;
    if (currentProvince) {
      loadCities(currentYear, currentProvince);
    } else {
      const nearest = findNearestMarker(provinceLayer);
      if (nearest) {
        currentProvince = nearest.getPopup()?.getContent();
        map.flyTo(nearest.getLatLng(), ZOOM_SIDO);
        loadCities(currentYear, currentProvince);
      }
    }
  } else {
    if (currentProvince && currentCity) {
      loadAccidents(currentYear, currentProvince, currentCity);
    } else if (currentProvince) {
      const nearest = findNearestMarker(cityLayer);
      if (nearest) {
        currentCity = nearest.getPopup()?.getContent();
        map.flyTo(nearest.getLatLng(), ZOOM_SGG);
        loadAccidents(currentYear, currentProvince, currentCity);
      }
    }
  }
}, 300));

let currentYear = 2012;
let currentProvince = null;
let currentCity = null;

// ===============================
// #region Filter Initialization
// ===============================

// map.js 필터 로딩 함수 추가
async function loadFilterOptions() {
  try {
    const res = await fetchWithLoading("/api/filters");
    const data = await res;

    populateCheckboxes("road_group", data.roads, "road");
    populateCheckboxes("offender_group", data.offenders, "offender");
    populateCheckboxes("victim_group", data.victims, "victim");
    populateCheckboxes("violation_group", data.violations, "violation");
    populateCheckboxes("type_major_group", data.types_major, "major");
    populateCheckboxes("type_minor_group", data.types_minor, "minor");
  } catch (err) {
    console.error("필터 데이터 로딩 실패:", err);
  }
}

function populateCheckboxes(containerId, items, prefix) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  items.forEach((item, index) => {
    const id = `${prefix}_${index}`;
    const div = document.createElement("div");
    div.className = "checkbox-item";
    div.innerHTML = `
      <input type="checkbox" id="${id}" value="${item}" checked>
      <label for="${id}">${item}</label>
    `;
    container.appendChild(div);
  });
}


// ===============================
// #region Filter Marker
// ===============================
async function applyFilters() {
  const start = document.getElementById("startDate").value;
  const end = document.getElementById("endDate").value;
  const day = document.getElementById("day").checked;
  const night = document.getElementById("night").checked;

  const days = [...document.querySelectorAll("#dayOfWeek_group input[type=checkbox]:checked")]
    .map(cb => cb.value);

  const types = [...document.querySelectorAll("#type_major_group input[type=checkbox]:checked")]
    .map(cb => cb.value);
  const typeMinors = [...document.querySelectorAll("#type_minor_group input[type=checkbox]:checked")]
    .map(cb => cb.value);
  const roads = [...document.querySelectorAll("#road_group input[type=checkbox]:checked")]
    .map(cb => cb.value);
  const offenders = [...document.querySelectorAll("#offender_group input[type=checkbox]:checked")]
    .map(cb => cb.value);
  const victims = [...document.querySelectorAll("#victim_group input[type=checkbox]:checked")]
    .map(cb => cb.value);
  const violations = [...document.querySelectorAll("#violation_group input[type=checkbox]:checked")]
    .map(cb => cb.value);

  const query = new URLSearchParams();
  if (start) query.set("start", start);
  if (end) query.set("end", end);
  if (day && !night) query.set("timeofday", "day");
  else if (!day && night) query.set("timeofday", "night");
  else if (!day && !night) return alert("주간/야간 중 하나는 선택되어야 합니다.");

  if (days.length > 0 && days.length < 7) query.set("dayofweek", days.join(","));
  if (types.length > 0) query.set("types", types.join(","));
  if (roads.length > 0) query.set("road", roads.join(","));
  if (offenders.length > 0) query.set("offender", offenders.join(","));
  if (victims.length > 0) query.set("victim", victims.join(","));
  if (violations.length > 0) query.set("violation", violations.join(","));

  const accidents = await fetchWithLoading(`/api/filtered_accidents?${query}`);
  renderFilteredAccidents(accidents);
}

function renderFilteredAccidents(accidents) {
  filterAccidentLayer.clearLayers();
  map.addLayer(filterAccidentLayer);  // accidentLayer → filterAccidentLayer

  accidents.forEach(acc => {
    const icon = icons[acc.type_major] || icons["차대차"];
    const marker = L.marker([acc.lat, acc.lng], { icon });
    marker.bindPopup(`<b>${acc.date}</b><br/>${acc.desc}`);
    filterAccidentLayer.addLayer(marker);
  });

  document.getElementById("filteredCount").innerText = accidents.length.toLocaleString();
}

document.getElementById("applyFilters").addEventListener("click", applyFilters);

// ===============================
// #region View Mode
// ===============================

//Filter Panel Item Toggle
document.querySelectorAll('.filter-section.collapsible h3').forEach(header => {
  header.style.cursor = 'pointer'; // 클릭 가능한 느낌 추가
  header.addEventListener('click', () => {
    const section = header.parentElement;
    section.classList.toggle('open');

    // 아이콘 변경
    const icon = header.querySelector('.toggle-icon');
    if (icon) {
      icon.textContent = section.classList.contains('open') ? '▼' : '▶';
    }
  });
});


/**
 * Toggles the filter panel's collapsed state and updates the toggle button icon.
 */
function toggleFilterPanel() {
  filterPanel.classList.toggle("collapsed");
  toggleButton.textContent = filterPanel.classList.contains("collapsed") ? "▶" : "◀";
  setTimeout(() => map.invalidateSize(), 300);
}

// Bind toggle function
toggleButton.addEventListener("click", toggleFilterPanel);

/**
 * Updates the view mode between Year mode and Filter mode,
 * and collapses/expands the filter panel accordingly.
 */
function updateViewMode() {
  clearAllLayers();

  if (modeYearCheckbox.checked) {
    // Year mode: collapse panel if open
    if (!filterPanel.classList.contains("collapsed")) {
      toggleFilterPanel();
    }
    yearSelectContainer.style.display = "block";
    regionLabel.classList.add('active');
    loadProvinces(currentYear);
  } else {
    // Filter mode: expand panel if collapsed
    if (filterPanel.classList.contains("collapsed")) {
      toggleFilterPanel();
    }
    yearSelectContainer.style.display = "none";
    regionLabel.classList.remove('active');
  }

  setTimeout(() => map.invalidateSize(), 300);
}

modeFilterCheckbox.addEventListener("change", updateViewMode);
modeYearCheckbox.addEventListener("change", updateViewMode);

// ===============================
// #region Initial Load
// ===============================
updateViewMode();
loadYears();
loadFilterOptions();