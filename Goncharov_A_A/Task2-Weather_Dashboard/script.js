const tower = document.getElementById("tower");
const floorCounter = document.getElementById("floor-counter");
const overlay = document.getElementById("event-overlay");
const layerLabel = document.getElementById("layer-label");
const locationLabel = document.getElementById("location-label");
const weatherPanel = document.getElementById("weather-panel");
const weatherTemp = document.getElementById("weather-temp");
const weatherDesc = document.getElementById("weather-desc");
const weatherIcon = document.getElementById("weather-icon");

const FLOOR_WINDOW_RADIUS = 50;
const MIN_EVENT_GAP = 12;
const MAX_EVENT_GAP = 160;
const MIN_SEGMENT = 200;
const MAX_SEGMENT = 500;

let maxGeneratedFloor = 0;
let scheduledEventFloor = 1;
let lastKnownFloor = 1;
let activeTheme = "";
let overlayTimeout;
let themeTimeout;
let currentSegmentIndex = 0;
let segmentEndFloor = MAX_SEGMENT;
let hasReachedMurino = false;
let weatherCache = {};
const renderedFloors = new Map();
let topSpacer;
let bottomSpacer;
let currentWindowMin = 1;
let currentWindowMax = 1;
let floorUnit = window.innerHeight || 1;

const layers = [
  { name: "ядро Земли", threshold: 80, className: "is-core" },
  { name: "нижняя мантия", threshold: 220, className: "is-mantle" },
  { name: "верхняя мантия", threshold: 400, className: "is-mantle" },
  { name: "кора", threshold: 600, className: "is-surface" },
  { name: "атмосфера", threshold: 900, className: "is-stratosphere" },
  { name: "экзосфера", threshold: 1200, className: "is-exosphere" },
  { name: "космос", threshold: Infinity, className: "is-space" }
];

const journeySegments = [
  { label: "Экватор", coords: { lat: 0.1, lon: 15.0 } },
  { label: "Каир", coords: { lat: 30.0444, lon: 31.2357 } },
  { label: "Москва", coords: { lat: 55.7558, lon: 37.6176 } },
  { label: "Санкт-Петербург", coords: { lat: 59.9311, lon: 30.3609 } },
  { label: "Мурино", coords: { lat: 60.0501, lon: 30.4419 } }
];

const EVENT_POOL = [
  { type: "theme", payload: "theme-night" },
  { type: "theme", payload: "theme-neon" },
  { type: "overlay", payload: { message: "не своди глаз", variant: "ghost" } },
  { type: "overlay", payload: { message: "обернись", variant: "alert" } }
];

async function init() {
  await loadEnvKey();
  segmentEndFloor = selectNextSegmentEnd(0);
  scheduledEventFloor = computeNextEventFloor(1);
  setupTowerSpacers();
  ensureGeneratedUpTo(1 + FLOOR_WINDOW_RADIUS);
  maintainFloorWindow(1);
  updateFloorIndicator(1);
  updateLayerLabel(1);
  updateJourneyInfo();
  await updateWeather();
  window.addEventListener("scroll", handleScroll, { passive: true });
  window.addEventListener("resize", handleScroll);
}

async function loadEnvKey() {
  if (window.OPEN_WEATHER_KEY !== undefined) {
    return;
  }
  try {
    const response = await fetch("./.env", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to fetch env file with status ${response.status}`);
    }
    const text = await response.text();
    const apiKey = parseEnv(text).OPEN_WEATHER_KEY;
    if (!apiKey) {
      console.warn("OpenWeather API key not provided. Weather updates disabled.");
    }
    window.OPEN_WEATHER_KEY = apiKey;
  } catch (error) {
    console.warn("Unable to load .env for OpenWeather", error);
    const manualKey = window.prompt("Введите OpenWeather API ключ (он останется только в этой сессии)");
    window.OPEN_WEATHER_KEY = manualKey ? manualKey.trim() : null;
  }
}

function parseEnv(raw) {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"))
    .reduce((acc, line) => {
      const eqIndex = line.indexOf("=");
      if (eqIndex === -1) {
        return acc;
      }
      const key = line.slice(0, eqIndex).trim();
      const value = line.slice(eqIndex + 1).trim();
      if (!key) {
        return acc;
      }
      acc[key] = value;
      return acc;
    }, {});
}

function applyLayerClass(floorElement, floorNumber) {
  const layerConfig = getLayerForFloor(floorNumber);
  if (!layerConfig) return null;
  if (layerConfig.className) {
    floorElement.classList.add(layerConfig.className);
  }
  return layerConfig;
}

function getLayerForFloor(floorNumber) {
  return layers.find((layer) => floorNumber <= layer.threshold) ?? layers[layers.length - 1];
}

function updateLayerLabel(floorNumber) {
  const layerConfig = getLayerForFloor(floorNumber);
  if (layerConfig) {
    layerLabel.textContent = `Слой: ${layerConfig.name}`;
  }
}

function selectNextSegmentEnd(currentFloor) {
  const delta = Math.floor(Math.random() * (MAX_SEGMENT - MIN_SEGMENT + 1)) + MIN_SEGMENT;
  return currentFloor + delta;
}

function computeNextEventFloor(fromFloor) {
  const offset = Math.floor(Math.random() * (MAX_EVENT_GAP - MIN_EVENT_GAP + 1)) + MIN_EVENT_GAP;
  return fromFloor + offset;
}

async function handleScroll() {
  const currentFloor = detectCurrentFloor(lastKnownFloor);
  maintainFloorWindow(currentFloor);
  if (currentFloor !== lastKnownFloor) {
    lastKnownFloor = currentFloor;
    updateFloorIndicator(currentFloor);
    updateLayerLabel(currentFloor);
  }
  if (!hasReachedMurino && currentFloor >= scheduledEventFloor) {
    triggerRandomEvent(currentFloor);
    scheduledEventFloor = computeNextEventFloor(currentFloor);
  }
}

function detectCurrentFloor(fallback) {
  const viewportHeight = window.innerHeight || floorUnit || 1;
  const centerY = window.scrollY + viewportHeight / 2;
  const unit = floorUnit || viewportHeight || 1;
  const approxFloor = Math.max(1, Math.floor(centerY / unit) + 1);
  if (Number.isNaN(approxFloor)) {
    return fallback;
  }
  return approxFloor;
}

function updateFloorIndicator(floor) {
  floorCounter.textContent = String(floor);
}

function ensureGeneratedUpTo(targetFloor) {
  while (!hasReachedMurino && maxGeneratedFloor < targetFloor) {
    maxGeneratedFloor += 1;
    if (!hasReachedMurino && maxGeneratedFloor >= segmentEndFloor) {
      advanceSegment(maxGeneratedFloor);
    }
    if (hasReachedMurino) {
      break;
    }
  }
}

function maintainFloorWindow(currentFloor) {
  const desiredMinFloor = Math.max(1, currentFloor - FLOOR_WINDOW_RADIUS);
  const desiredMaxFloorCandidate = hasReachedMurino
    ? Math.min(currentFloor + FLOOR_WINDOW_RADIUS, maxGeneratedFloor)
    : currentFloor + FLOOR_WINDOW_RADIUS;

  ensureGeneratedUpTo(desiredMaxFloorCandidate);
  const effectiveMaxFloor = Math.max(
    desiredMinFloor,
    Math.min(desiredMaxFloorCandidate, maxGeneratedFloor)
  );

  const toRemove = [];
  renderedFloors.forEach((_element, floorNumber) => {
    if (floorNumber < desiredMinFloor || floorNumber > effectiveMaxFloor) {
      toRemove.push(floorNumber);
    }
  });

  for (const floorNumber of toRemove) {
    const element = renderedFloors.get(floorNumber);
    if (element && element.parentElement === tower) {
      tower.removeChild(element);
    }
    renderedFloors.delete(floorNumber);
  }

  for (let floorNumber = desiredMinFloor; floorNumber <= effectiveMaxFloor; floorNumber += 1) {
    if (!renderedFloors.has(floorNumber)) {
      const floorElement = buildFloorElement(floorNumber);
      insertFloorElement(floorNumber, floorElement);
      renderedFloors.set(floorNumber, floorElement);
    }
  }

  currentWindowMin = desiredMinFloor;
  currentWindowMax = effectiveMaxFloor;
  const sampleFloor =
    renderedFloors.get(currentFloor) ??
    renderedFloors.get(currentWindowMin) ??
    (() => {
      const iterator = renderedFloors.values().next();
      return iterator.done ? null : iterator.value;
    })();
  if (sampleFloor) {
    const measured = sampleFloor.getBoundingClientRect().height;
    if (measured) {
      floorUnit = measured;
    }
  }
  updateTowerSpacers();
}

function buildFloorElement(floorNumber) {
  const floor = document.createElement("section");
  floor.className = "floor";
  floor.dataset.floor = String(floorNumber);
  const layerConfig = applyLayerClass(floor, floorNumber);
  if (layerConfig) {
    floor.dataset.layer = layerConfig.name;
  }
  return floor;
}

function insertFloorElement(floorNumber, floorElement) {
  let offset = 1;
  while (offset <= FLOOR_WINDOW_RADIUS * 2 + 1) {
    const previous = renderedFloors.get(floorNumber - offset);
    if (previous && previous.parentElement === tower) {
      tower.insertBefore(floorElement, previous.nextSibling);
      return;
    }
    const next = renderedFloors.get(floorNumber + offset);
    if (next && next.parentElement === tower) {
      tower.insertBefore(floorElement, next);
      return;
    }
    offset += 1;
  }
  if (bottomSpacer && bottomSpacer.parentElement === tower) {
    tower.insertBefore(floorElement, bottomSpacer);
  } else {
    tower.appendChild(floorElement);
  }
}

function setupTowerSpacers() {
  if (topSpacer && bottomSpacer) {
    return;
  }
  topSpacer = document.createElement("div");
  topSpacer.id = "tower-spacer-top";
  topSpacer.className = "tower__spacer";
  bottomSpacer = document.createElement("div");
  bottomSpacer.id = "tower-spacer-bottom";
  bottomSpacer.className = "tower__spacer";
  tower.prepend(topSpacer);
  tower.appendChild(bottomSpacer);
  updateTowerSpacers();
}

function updateTowerSpacers() {
  if (!topSpacer || !bottomSpacer) {
    return;
  }
  const unit = floorUnit || window.innerHeight || 1;
  const topHeight = Math.max(0, currentWindowMin - 1) * unit;
  const bottomHeight = Math.max(0, maxGeneratedFloor - currentWindowMax) * unit;
  topSpacer.style.height = `${topHeight}px`;
  bottomSpacer.style.height = `${bottomHeight}px`;
}

function triggerRandomEvent(currentFloor) {
  const eventConfig = EVENT_POOL[Math.floor(Math.random() * EVENT_POOL.length)];
  if (eventConfig.type === "theme") {
    applyTransientTheme(eventConfig.payload);
  } else if (eventConfig.type === "overlay") {
    flashOverlay(eventConfig.payload.message, eventConfig.payload.variant);
  }
}

function applyTransientTheme(themeClass) {
  if (themeTimeout) {
    clearTimeout(themeTimeout);
  }
  if (activeTheme) {
    document.body.classList.remove(activeTheme);
  }
  activeTheme = themeClass;
  document.body.classList.add(themeClass);
  themeTimeout = setTimeout(() => {
    document.body.classList.remove(themeClass);
    if (activeTheme === themeClass) {
      activeTheme = "";
    }
  }, 7000);
}

function flashOverlay(message, variant) {
  if (overlayTimeout) {
    clearTimeout(overlayTimeout);
  }
  document.body.classList.remove("is-shaking");
  void document.body.offsetWidth;
  overlay.textContent = message;
  overlay.className = `overlay overlay-${variant} active`;
  document.body.classList.add("is-shaking");
  overlayTimeout = setTimeout(() => {
    overlay.className = "overlay";
    overlay.textContent = "";
    document.body.classList.remove("is-shaking");
  }, 2400);
}

function advanceSegment(currentFloor) {
  currentSegmentIndex += 1;
  if (currentSegmentIndex >= journeySegments.length - 1) {
    reachMurino();
    return;
  }
  segmentEndFloor = selectNextSegmentEnd(currentFloor);
  updateJourneyInfo();
  updateWeather();
}

function reachMurino() {
  currentSegmentIndex = journeySegments.length - 1;
  hasReachedMurino = true;
  updateJourneyInfo();
  updateWeather();
  showEnding();
}

function showEnding() {
  document.body.classList.remove("theme-night", "theme-neon");
  document.body.classList.add("theme-night");
  overlay.textContent = "ЖМУРИНО";
  overlay.className = "overlay overlay-ending active";
}

function updateJourneyInfo() {
  const segment = journeySegments[currentSegmentIndex];
  locationLabel.textContent = `Погода: ${segment.label}`;
}

async function updateWeather() {
  const apiKey = window.OPEN_WEATHER_KEY;
  const segment = journeySegments[currentSegmentIndex];
  if (!apiKey || !segment) {
    weatherTemp.textContent = "--°C";
    weatherDesc.textContent = "нет данных";
    weatherIcon.hidden = true;
    return;
  }

  const cacheKey = `${segment.coords.lat.toFixed(2)}_${segment.coords.lon.toFixed(2)}`;
  if (weatherCache[cacheKey] && Date.now() - weatherCache[cacheKey].timestamp < 10 * 60 * 1000) {
    applyWeather(weatherCache[cacheKey].data);
    return;
  }

  try {
    const url = new URL("https://api.openweathermap.org/data/2.5/weather");
    url.searchParams.set("lat", segment.coords.lat);
    url.searchParams.set("lon", segment.coords.lon);
    url.searchParams.set("appid", apiKey);
    url.searchParams.set("units", "metric");
    url.searchParams.set("lang", "ru");

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`OpenWeather responded with ${response.status}`);
    }
    const data = await response.json();
    weatherCache[cacheKey] = { data, timestamp: Date.now() };
    applyWeather(data);
  } catch (error) {
    console.error("Failed to load weather:", error);
    weatherTemp.textContent = "--°C";
    weatherDesc.textContent = "ошибка погоды";
    weatherIcon.hidden = true;
  }
}

function applyWeather(data) {
  const temp = Math.round(data.main?.temp ?? 0);
  weatherTemp.textContent = `${temp}°C`;
  weatherDesc.textContent = data.weather?.[0]?.description ?? "нет данных";
  const iconCode = data.weather?.[0]?.icon;
  if (iconCode) {
    const iconUrl = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
    weatherIcon.src = iconUrl;
    weatherIcon.hidden = false;
  } else {
    weatherIcon.hidden = true;
  }
}

document.addEventListener("DOMContentLoaded", init);
