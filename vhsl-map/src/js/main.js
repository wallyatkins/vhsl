// Optimized JavaScript file for VHSL Map Website
import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import {fromLonLat} from 'ol/proj';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import {Circle as CircleStyle, Fill, Stroke, Style, Text} from 'ol/style';
import {defaults as defaultControls} from 'ol/control';
import Overlay from 'ol/Overlay';
import GeoJSON from 'ol/format/GeoJSON';

// Global variables
let map;
let schoolsSource;
let schoolsLayer;
let currentView = 'all';
let activeFilters = {
  classes: [],
  regions: [],
  districts: []
};
let hoveredFeature = null;
let schoolLookup = null;
let schoolListElements = [];
let debounceTimer;
let visibleSchoolsCount = 0;
let allRegions = new Set();
let allDistricts = new Set();

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  // Show loading indicator
  showLoadingIndicator();
  
  try {
    // Load GeoJSON data directly from GitHub to avoid bundling large files
    const rawBase =
      'https://raw.githubusercontent.com/wallyatkins/vhsl/refs/heads/main/';

    const regionBase = `${rawBase}geojson/vhsl_regions/schools_by_region/`;

    // Generate URLs for all region files (Classes 1-6, Regions A-D)
    const regionUrls = [];
    for (let cls = 1; cls <= 6; cls++) {
      for (const letter of ['A', 'B', 'C', 'D']) {
        const file = `Region ${cls}${letter}.geojson`;
        regionUrls.push(regionBase + encodeURIComponent(file));
      }
    }

    const lookupUrl = `${rawBase}vhsl-map/data/geojson/school_lookup.json`;

    const [regionsData, lookupData] = await Promise.all([
      Promise.all(regionUrls.map((url) => fetchData(url))),
      fetchData(lookupUrl),
    ]);

    // Combine all region features into a single FeatureCollection
    const schoolsGeoJSON = { type: 'FeatureCollection', features: [] };
    regionsData.forEach((data) => {
      if (data?.features) {
        schoolsGeoJSON.features.push(...data.features);
      }
    });
    
    if (!schoolsGeoJSON || !lookupData) {
      throw new Error('Failed to load required GeoJSON data');
    }
    
    // Store school lookup globally for faster access
    schoolLookup = lookupData;
    
    // Enrich schools GeoJSON with class data from lookup
    enrichSchoolsData(schoolsGeoJSON, schoolLookup);
    
    // Initialize map
    initMap(schoolsGeoJSON);
    
    // Initialize UI components
    initUI();
    
    // Populate filters based on school data
    populateFilters(schoolLookup);
    
    // Populate school list
    populateSchoolList(schoolLookup);
    
    // Initialize event listeners
    initEventListeners();
    
    // Add hover interaction
    addHoverInteraction();
    
    // Create filter status indicator
    createFilterStatusIndicator();
    
    // Update filter status with initial count
    updateFilterStatus();
    
    // Initialize global search
    initGlobalSearch();
    
    // Hide loading indicator
    hideLoadingIndicator();
    
    // Preload map tiles for common zoom levels
    preloadMapTiles();
  } catch (error) {
    console.error('Error initializing application:', error);
    document.body.innerHTML = `<div style="text-align: center; padding: 2rem;">
      <h1>Error Loading Data</h1>
      <p>${error.message}</p>
      <p>Please try refreshing the page.</p>
    </div>`;
  }
});

// Initialize global search functionality
function initGlobalSearch() {
  const searchInput = document.getElementById('global-search');
  const searchButton = document.getElementById('search-button');
  const searchResults = document.getElementById('search-results');
  
  if (!searchInput || !searchButton || !searchResults) {
    console.error('Search elements not found');
    return;
  }
  
  // Extract all regions and districts for search
  extractRegionsAndDistricts();
  
  // Search input event listener with debounce
  searchInput.addEventListener('input', debounce((e) => {
    const searchTerm = e.target.value.trim().toLowerCase();
    
    if (searchTerm.length < 2) {
      searchResults.classList.add('hidden');
      return;
    }
    
    // Perform search
    const results = performSearch(searchTerm);
    
    // Display results
    displaySearchResults(results, searchTerm);
  }, 200));
  
  // Search button click
  searchButton.addEventListener('click', () => {
    const searchTerm = searchInput.value.trim().toLowerCase();
    
    if (searchTerm.length < 2) {
      return;
    }
    
    // Perform search
    const results = performSearch(searchTerm);
    
    // Display results
    displaySearchResults(results, searchTerm);
  });
  
  // Close search results when clicking outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && 
        !searchButton.contains(e.target) && 
        !searchResults.contains(e.target)) {
      searchResults.classList.add('hidden');
    }
  });
  
  // Show results when input is focused
  searchInput.addEventListener('focus', () => {
    const searchTerm = searchInput.value.trim().toLowerCase();
    if (searchTerm.length >= 2) {
      const results = performSearch(searchTerm);
      displaySearchResults(results, searchTerm);
    }
  });
}

// Extract all regions and districts for search
function extractRegionsAndDistricts() {
  allRegions.clear();
  allDistricts.clear();
  
  // Extract from school lookup
  Object.values(schoolLookup).forEach(school => {
    if (school.region) allRegions.add(school.region);
    if (school.district) allDistricts.add(school.district);
  });
  
  console.log(`Extracted ${allRegions.size} regions and ${allDistricts.size} districts for search`);
}

// Perform search across schools, regions, and districts
function performSearch(searchTerm) {
  const results = {
    schools: [],
    regions: [],
    districts: []
  };
  
  // Search schools
  Object.values(schoolLookup).forEach(school => {
    if (school.name.toLowerCase().includes(searchTerm)) {
      results.schools.push(school);
    }
  });
  
  // Search regions
  Array.from(allRegions).forEach(region => {
    if (region.toLowerCase().includes(searchTerm)) {
      results.regions.push(region);
    }
  });
  
  // Search districts
  Array.from(allDistricts).forEach(district => {
    if (district.toLowerCase().includes(searchTerm)) {
      results.districts.push(district);
    }
  });
  
  // Sort results
  results.schools.sort((a, b) => a.name.localeCompare(b.name));
  results.regions.sort();
  results.districts.sort();
  
  // Limit results for performance
  results.schools = results.schools.slice(0, 10);
  results.regions = results.regions.slice(0, 5);
  results.districts = results.districts.slice(0, 5);
  
  return results;
}

// Display search results
function displaySearchResults(results, searchTerm) {
  const searchResults = document.getElementById('search-results');
  
  // Clear previous results
  searchResults.innerHTML = '';
  
  // Check if we have any results
  const hasResults = results.schools.length > 0 || 
                     results.regions.length > 0 || 
                     results.districts.length > 0;
  
  if (!hasResults) {
    searchResults.innerHTML = `
      <div class="search-no-results">
        No results found for "${searchTerm}"
      </div>
    `;
    searchResults.classList.remove('hidden');
    return;
  }
  
  // Create results HTML
  let resultsHTML = '';
  
  // Schools section
  if (results.schools.length > 0) {
    resultsHTML += `
      <div class="search-result-group">
        <h4>Schools</h4>
        <div class="search-result-items">
    `;
    
    results.schools.forEach(school => {
      const schoolClass = school.class || '';
      const schoolRegion = school.region || '';
      const schoolDistrict = school.district || '';
      
      resultsHTML += `
        <div class="search-result-item" data-type="school" data-name="${school.name}">
          <div class="search-result-info">
            <div class="search-result-name">${school.name}</div>
            <div class="search-result-meta">${schoolClass} | ${schoolRegion} | ${schoolDistrict}</div>
          </div>
          <div class="search-result-actions">
            <button class="search-action-button" data-action="jump" data-name="${school.name}">Jump</button>
          </div>
        </div>
      `;
    });
    
    resultsHTML += `
        </div>
      </div>
    `;
  }
  
  // Regions section
  if (results.regions.length > 0) {
    resultsHTML += `
      <div class="search-result-group">
        <h4>Regions</h4>
        <div class="search-result-items">
    `;
    
    results.regions.forEach(region => {
      resultsHTML += `
        <div class="search-result-item" data-type="region" data-name="${region}">
          <div class="search-result-info">
            <div class="search-result-name">${region}</div>
          </div>
          <div class="search-result-actions">
            <button class="search-action-button" data-action="filter" data-type="region" data-name="${region}">Filter</button>
          </div>
        </div>
      `;
    });
    
    resultsHTML += `
        </div>
      </div>
    `;
  }
  
  // Districts section
  if (results.districts.length > 0) {
    resultsHTML += `
      <div class="search-result-group">
        <h4>Districts</h4>
        <div class="search-result-items">
    `;
    
    results.districts.forEach(district => {
      resultsHTML += `
        <div class="search-result-item" data-type="district" data-name="${district}">
          <div class="search-result-info">
            <div class="search-result-name">${district}</div>
          </div>
          <div class="search-result-actions">
            <button class="search-action-button" data-action="filter" data-type="district" data-name="${district}">Filter</button>
          </div>
        </div>
      `;
    });
    
    resultsHTML += `
        </div>
      </div>
    `;
  }
  
  // Update search results
  searchResults.innerHTML = resultsHTML;
  searchResults.classList.remove('hidden');
  
  // Add event listeners to action buttons
  const actionButtons = searchResults.querySelectorAll('.search-action-button');
  actionButtons.forEach(button => {
    button.addEventListener('click', handleSearchAction);
  });
  
  // Add event listeners to result items for jumping to schools
  const schoolItems = searchResults.querySelectorAll('.search-result-item[data-type="school"]');
  schoolItems.forEach(item => {
    item.addEventListener('click', (e) => {
      if (!e.target.classList.contains('search-action-button')) {
        const schoolName = item.dataset.name;
        jumpToSchool(schoolName);
      }
    });
  });
}

// Handle search action (jump or filter)
function handleSearchAction(e) {
  const button = e.target;
  const action = button.dataset.action;
  const type = button.dataset.type;
  const name = button.dataset.name;
  
  if (action === 'jump' && type === 'school') {
    jumpToSchool(name);
  } else if (action === 'filter') {
    if (type === 'region') {
      filterByRegion(name);
    } else if (type === 'district') {
      filterByDistrict(name);
    }
  }
  
  // Hide search results
  document.getElementById('search-results').classList.add('hidden');
  
  // Clear search input
  document.getElementById('global-search').value = '';
}

// Jump to a school on the map
function jumpToSchool(schoolName) {
  // Find the feature for this school
  const features = schoolsSource.getFeatures();
  const feature = features.find(f => f.get('name') === schoolName);
  
  if (feature) {
    // Center map on school
    map.getView().animate({
      center: feature.getGeometry().getCoordinates(),
      zoom: 12,
      duration: 500
    });
    
    // Show info panel
    showSchoolInfo(feature);
    
    // Close sidebar on mobile
    if (window.innerWidth < 768) {
      document.getElementById('sidebar').classList.remove('active');
      document.querySelector('.sidebar-overlay')?.classList.remove('active');
      document.getElementById('sidebar-toggle')?.classList.remove('active');
    }
  }
}

// Filter by region
function filterByRegion(regionName) {
  // Reset filters
  resetFilters();
  
  // Set region filter
  activeFilters.regions.push(regionName);
  
  // Update UI
  document.querySelectorAll('#region-filters .filter-options input[type="checkbox"]').forEach(checkbox => {
    if (checkbox.value === regionName) {
      checkbox.checked = true;
    }
  });
  
  // Apply filters
  filterSchools();
  
  // Switch to regions view
  updateMapView('regions');
  
  // Update active navigation
  document.querySelectorAll('#main-nav a').forEach(link => {
    link.classList.remove('active');
    if (link.dataset.view === 'regions') {
      link.classList.add('active');
    }
  });
}

// Filter by district
function filterByDistrict(districtName) {
  // Reset filters
  resetFilters();
  
  // Set district filter
  activeFilters.districts.push(districtName);
  
  // Update UI
  document.querySelectorAll('#district-filters .filter-options input[type="checkbox"]').forEach(checkbox => {
    if (checkbox.value === districtName) {
      checkbox.checked = true;
    }
  });
  
  // Apply filters
  filterSchools();
  
  // Switch to districts view
  updateMapView('districts');
  
  // Update active navigation
  document.querySelectorAll('#main-nav a').forEach(link => {
    link.classList.remove('active');
    if (link.dataset.view === 'districts') {
      link.classList.add('active');
    }
  });
}

// Create filter status indicator
function createFilterStatusIndicator() {
  const statusIndicator = document.createElement('div');
  statusIndicator.id = 'filter-status';
  statusIndicator.className = 'filter-status';
  statusIndicator.innerHTML = '<span id="filter-description">Showing all schools</span> (<span id="schools-count">0</span> schools)';
  
  // Add to map container
  document.getElementById('map-container').appendChild(statusIndicator);
}

// Update filter status indicator
function updateFilterStatus() {
  const statusElement = document.getElementById('filter-description');
  const countElement = document.getElementById('schools-count');
  
  if (!statusElement || !countElement) return;
  
  // Count visible schools
  visibleSchoolsCount = countVisibleSchools();
  
  // Update count
  countElement.textContent = visibleSchoolsCount;
  
  // Update description based on active filters
  let description = 'Showing all schools';
  
  if (activeFilters.classes.length > 0 || 
      activeFilters.regions.length > 0 || 
      activeFilters.districts.length > 0) {
    
    const filterParts = [];
    
    if (activeFilters.classes.length > 0) {
      filterParts.push(`Classes: ${activeFilters.classes.join(', ')}`);
    }
    
    if (activeFilters.regions.length > 0) {
      filterParts.push(`Regions: ${activeFilters.regions.join(', ')}`);
    }
    
    if (activeFilters.districts.length > 0) {
      filterParts.push(`Districts: ${activeFilters.districts.join(', ')}`);
    }
    
    description = `Filtered by ${filterParts.join('; ')}`;
  }
  
  statusElement.textContent = description;
}

// Count visible schools
function countVisibleSchools() {
  // Count visible features on the map
  const features = schoolsSource.getFeatures();
  let count = 0;
  
  features.forEach(feature => {
    // If the feature has no style or a non-empty style, it's visible
    const style = feature.getStyle();
    if (!style || (style && style.getImage && style.getImage())) {
      count++;
    }
  });
  
  return count;
}

// Preload map tiles for common zoom levels
function preloadMapTiles() {
  // Force rendering of tiles at common zoom levels
  const view = map.getView();
  const currentZoom = view.getZoom();
  const currentCenter = view.getCenter();
  
  // Temporarily change zoom to preload tiles
  [7, 8, 9].forEach(zoom => {
    if (zoom !== currentZoom) {
      view.setZoom(zoom);
      // Wait a moment for tiles to load
      setTimeout(() => {
        view.setZoom(currentZoom);
        view.setCenter(currentCenter);
      }, 100);
    }
  });
}

// Enrich schools GeoJSON with class data from lookup - optimized version
function enrichSchoolsData(schoolsGeoJSON, schoolLookup) {
  if (!schoolsGeoJSON?.features || !schoolLookup) {
    console.error('Invalid data for enrichment');
    return;
  }
  
  let enrichedCount = 0;
  
  schoolsGeoJSON.features.forEach(feature => {
    const props = feature.properties;
    const schoolName = props.name;
    
    if (schoolName && schoolLookup[schoolName]) {
      // Update size and class properties
      if (schoolLookup[schoolName].size) {
        props.size = schoolLookup[schoolName].size;
        enrichedCount++;
      }
      
      if (schoolLookup[schoolName].class) {
        props.class = schoolLookup[schoolName].class;
      }
      
      // Update region and district if missing
      if (!props.region && schoolLookup[schoolName].region) {
        props.region = schoolLookup[schoolName].region;
      }
      
      if (!props.district && schoolLookup[schoolName].district) {
        props.district = schoolLookup[schoolName].district;
      }
    }
  });
  
  console.log(`Enriched ${enrichedCount} schools with class data`);
}

// Show loading indicator
function showLoadingIndicator() {
  const loadingIndicator = document.createElement('div');
  loadingIndicator.id = 'loading-indicator';
  loadingIndicator.innerHTML = '<div class="spinner"></div><p>Loading VHSL data...</p>';
  document.body.appendChild(loadingIndicator);
}

// Hide loading indicator
function hideLoadingIndicator() {
  const loadingIndicator = document.getElementById('loading-indicator');
  if (loadingIndicator) {
    loadingIndicator.style.opacity = '0';
    setTimeout(() => {
      loadingIndicator.remove();
    }, 500);
  }
}

// Fetch data from JSON files with caching
async function fetchData(url) {
  try {
    // Add cache busting for development only
    const cacheBuster = process.env.NODE_ENV === 'development' ? `?_=${Date.now()}` : '';
    const response = await fetch(url + cacheBuster);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching data from ${url}:`, error);
    return null;
  }
}

// Initialize the OpenLayers map with GeoJSON data - optimized version
function initMap(schoolsGeoJSON) {
  // Create vector source for school markers from GeoJSON
  schoolsSource = new VectorSource({
    features: new GeoJSON().readFeatures(schoolsGeoJSON, {
      featureProjection: 'EPSG:3857'
    })
  });
  
  // Create style cache for better performance
  const styleCache = {};
  
  // Create vector layer for school markers with style function using cache
  schoolsLayer = new VectorLayer({
    source: schoolsSource,
    style: function(feature) {
      const size = feature.get('size') || 0;
      const highlight = feature === hoveredFeature;
      const styleKey = `${size}-${highlight ? 'highlight' : 'normal'}-${map.getView().getZoom() > 10 ? 'text' : 'notext'}`;
      
      if (!styleCache[styleKey]) {
        styleCache[styleKey] = createSchoolStyle(feature, highlight);
      }
      
      return styleCache[styleKey];
    },
    updateWhileAnimating: false, // Improve animation performance
    updateWhileInteracting: false, // Improve interaction performance
    zIndex: 10
  });
  
  // Create the map with optimized settings
  map = new Map({
    target: 'map',
    layers: [
      new TileLayer({
        source: new OSM({
          // Use a closer tile server if available
          // url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          crossOrigin: null,
          preload: 4, // Preload more tiles
          wrapX: false // Disable wrapping for better performance
        }),
        preload: Infinity
      }),
      schoolsLayer
    ],
    view: new View({
      center: fromLonLat([-79.5, 37.8]), // Center of Virginia
      zoom: 7,
      minZoom: 6,
      maxZoom: 18,
      constrainResolution: true
    }),
    controls: defaultControls({
      zoom: false,
      rotate: false
    }),
    pixelRatio: 1, // Use 1 for better performance, especially on high-DPI displays
    loadTilesWhileAnimating: true,
    loadTilesWhileInteracting: true
  });
  
  // Create popup overlay
  const popup = document.createElement('div');
  popup.className = 'ol-popup';
  popup.id = 'popup';
  
  const popupOverlay = new Overlay({
    element: popup,
    positioning: 'bottom-center',
    stopEvent: false,
    offset: [0, -10]
  });
  
  map.addOverlay(popupOverlay);
  
  // Add click interaction to show school info - with debounce
  map.on('click', function(evt) {
    const feature = map.forEachFeatureAtPixel(evt.pixel, function(feature) {
      return feature;
    });
    
    if (feature && feature.get('name')) {
      showSchoolInfo(feature);
    } else {
      document.getElementById('info-panel').classList.add('hidden');
    }
  });
}

// Initialize UI components - optimized version
function initUI() {
  // Mobile menu toggle
  const menuToggle = document.getElementById('menu-toggle');
  const mainNav = document.getElementById('main-nav');
  
  menuToggle.addEventListener('click', () => {
    menuToggle.classList.toggle('active');
    mainNav.classList.toggle('active');
  });
  
  // Create sidebar toggle for mobile
  const sidebarToggle = document.createElement('button');
  sidebarToggle.id = 'sidebar-toggle';
  sidebarToggle.innerHTML = '<span></span><span></span><span></span>';
  sidebarToggle.setAttribute('aria-label', 'Toggle sidebar');
  document.querySelector('main').appendChild(sidebarToggle);
  
  // Create sidebar close button for mobile
  const sidebarClose = document.createElement('button');
  sidebarClose.id = 'sidebar-close';
  sidebarClose.innerHTML = '×';
  sidebarClose.setAttribute('aria-label', 'Close sidebar');
  document.getElementById('sidebar').appendChild(sidebarClose);
  
  // Create overlay for mobile sidebar
  const sidebarOverlay = document.createElement('div');
  sidebarOverlay.className = 'sidebar-overlay';
  document.querySelector('main').appendChild(sidebarOverlay);
  
  // Sidebar toggle functionality
  sidebarToggle.addEventListener('click', () => {
    document.getElementById('sidebar').classList.add('active');
    sidebarOverlay.classList.add('active');
    sidebarToggle.classList.add('active');
  });
  
  // Sidebar close functionality
  sidebarClose.addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('active');
    sidebarOverlay.classList.remove('active');
    sidebarToggle.classList.remove('active');
  });
  
  // Close sidebar when clicking overlay
  sidebarOverlay.addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('active');
    sidebarOverlay.classList.remove('active');
    sidebarToggle.classList.remove('active');
  });
  
  // Map controls with debounce
  document.getElementById('zoom-in').addEventListener('click', debounce(() => {
    const view = map.getView();
    const zoom = view.getZoom();
    view.animate({
      zoom: zoom + 1,
      duration: 250
    });
  }, 250));
  
  document.getElementById('zoom-out').addEventListener('click', debounce(() => {
    const view = map.getView();
    const zoom = view.getZoom();
    view.animate({
      zoom: zoom - 1,
      duration: 250
    });
  }, 250));
  
  document.getElementById('reset-view').addEventListener('click', debounce(() => {
    map.getView().animate({
      center: fromLonLat([-79.5, 37.8]),
      zoom: 7,
      duration: 500
    });
  }, 250));
  
  // Close info panel
  document.getElementById('close-info').addEventListener('click', () => {
    document.getElementById('info-panel').classList.add('hidden');
  });
  
  // Add legend
  createLegend();
}

// Debounce function to limit how often a function can be called
function debounce(func, wait) {
  return function() {
    const context = this;
    const args = arguments;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      func.apply(context, args);
    }, wait);
  };
}

// Create color legend - optimized version
function createLegend() {
  const legend = document.createElement('div');
  legend.id = 'map-legend';
  
  // Use document fragment for better performance
  const fragment = document.createDocumentFragment();
  
  const title = document.createElement('h3');
  title.textContent = 'VHSL Classes';
  fragment.appendChild(title);
  
  // Class colors
  const classColors = {
    1: '#ffff33', // Class 1
    2: '#ff7f00', // Class 2
    3: '#984ea3', // Class 3
    4: '#4daf4a', // Class 4
    5: '#377eb8', // Class 5
    6: '#e41a1c'  // Class 6
  };
  
  // Create legend items
  for (let i = 1; i <= 6; i++) {
    const item = document.createElement('div');
    item.className = 'legend-item';
    
    const colorSpan = document.createElement('span');
    colorSpan.className = 'legend-color';
    colorSpan.style.backgroundColor = classColors[i];
    
    const textSpan = document.createElement('span');
    textSpan.textContent = `Class ${i}`;
    
    item.appendChild(colorSpan);
    item.appendChild(textSpan);
    fragment.appendChild(item);
  }
  
  legend.appendChild(fragment);
  document.getElementById('map-container').appendChild(legend);
  
  // Add toggle button for legend
  const legendToggle = document.createElement('button');
  legendToggle.id = 'legend-toggle';
  legendToggle.innerHTML = 'Legend';
  legendToggle.setAttribute('aria-label', 'Toggle legend');
  document.getElementById('map-controls').appendChild(legendToggle);
  
  legendToggle.addEventListener('click', () => {
    legend.classList.toggle('active');
  });
}

// Populate filter options based on school data - optimized version
function populateFilters(schoolLookup) {
  // Extract unique classes, regions, and districts
  const classes = new Set();
  const regions = new Set();
  const districts = new Set();
  
  Object.values(schoolLookup).forEach(school => {
    if (school.class) classes.add(school.class);
    if (school.region) regions.add(school.region);
    if (school.district) districts.add(school.district);
  });
  
  // Use document fragments for better performance
  const classFragment = document.createDocumentFragment();
  const regionFragment = document.createDocumentFragment();
  const districtFragment = document.createDocumentFragment();
  
  // Populate class filters
  Array.from(classes).sort().forEach(className => {
    const label = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = className;
    checkbox.dataset.filterType = 'classes';
    
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(` ${className}`));
    classFragment.appendChild(label);
  });
  
  // Populate region filters
  Array.from(regions).sort().forEach(region => {
    const label = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = region;
    checkbox.dataset.filterType = 'regions';
    
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(` ${region}`));
    regionFragment.appendChild(label);
  });
  
  // Populate district filters
  Array.from(districts).sort().forEach(district => {
    const label = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = district;
    checkbox.dataset.filterType = 'districts';
    
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(` ${district}`));
    districtFragment.appendChild(label);
  });
  
  // Append all fragments at once
  document.querySelector('#class-filters .filter-options').appendChild(classFragment);
  document.querySelector('#region-filters .filter-options').appendChild(regionFragment);
  document.querySelector('#district-filters .filter-options').appendChild(districtFragment);
}

// Populate school list from lookup data - optimized version
function populateSchoolList(schoolLookup) {
  const schoolList = document.getElementById('school-list');
  
  // Sort schools alphabetically
  const sortedSchools = Object.values(schoolLookup).sort((a, b) => 
    a.name.localeCompare(b.name)
  );
  
  // Use document fragment for better performance
  const fragment = document.createDocumentFragment();
  
  // Add each school to the list
  sortedSchools.forEach(school => {
    const listItem = document.createElement('li');
    listItem.textContent = school.name;
    listItem.dataset.name = school.name;
    listItem.dataset.class = school.class || '';
    listItem.dataset.region = school.region || '';
    listItem.dataset.district = school.district || '';
    
    listItem.addEventListener('click', () => {
      // Find the feature for this school
      const features = schoolsSource.getFeatures();
      const feature = features.find(f => f.get('name') === school.name);
      
      if (feature) {
        // Center map on school
        map.getView().animate({
          center: feature.getGeometry().getCoordinates(),
          zoom: 12,
          duration: 500
        });
        
        // Show info panel
        showSchoolInfo(feature);
        
        // Close sidebar on mobile
        if (window.innerWidth < 768) {
          document.getElementById('sidebar').classList.remove('active');
          document.querySelector('.sidebar-overlay').classList.remove('active');
          document.getElementById('sidebar-toggle').classList.remove('active');
        }
      }
    });
    
    fragment.appendChild(listItem);
    schoolListElements.push(listItem); // Store reference for faster filtering
  });
  
  schoolList.appendChild(fragment);
}

// Show school information in the info panel - optimized version
function showSchoolInfo(feature) {
  const infoPanel = document.getElementById('info-panel');
  const infoContent = document.getElementById('info-content');
  
  // Get properties from feature
  const name = feature.get('name');
  const size = feature.get('size');
  const region = feature.get('region');
  const district = feature.get('district');
  
  // Use innerHTML for better performance when replacing all content
  infoContent.innerHTML = `
    <h2>${name}</h2>
    <p><strong>Class:</strong> ${size ? `Class ${size}` : 'N/A'}</p>
    <p><strong>Region:</strong> ${region || 'N/A'}</p>
    <p><strong>District:</strong> ${district || 'N/A'}</p>
    <p><a href="https://www.vhsl.org" target="_blank" rel="noopener noreferrer">View on VHSL website</a></p>
  `;
  
  // Show the panel
  infoPanel.classList.remove('hidden');
}

// Create style for school markers - optimized with style caching
function createSchoolStyle(feature, highlight = false) {
  // Different colors for different classes
  const classColors = {
    1: '#ffff33', // Class 1
    2: '#ff7f00', // Class 2
    3: '#984ea3', // Class 3
    4: '#4daf4a', // Class 4
    5: '#377eb8', // Class 5
    6: '#e41a1c'  // Class 6
  };
  
  const size = parseInt(feature.get('size')) || 0;
  const color = classColors[size] || '#999999';
  
  return new Style({
    image: new CircleStyle({
      radius: highlight ? 8 : 6,
      fill: new Fill({
        color: color
      }),
      stroke: new Stroke({
        color: highlight ? '#000000' : '#ffffff',
        width: highlight ? 3 : 2
      })
    }),
    // Only show text at higher zoom levels or when highlighted
    text: (map.getView().getZoom() > 10 || highlight) ? new Text({
      text: feature.get('name'),
      offsetY: -15,
      font: highlight ? 'bold 14px Calibri,sans-serif' : '12px Calibri,sans-serif',
      fill: new Fill({
        color: '#000'
      }),
      stroke: new Stroke({
        color: '#fff',
        width: 3
      })
    }) : null
  });
}

// Add hover interaction - optimized version
function addHoverInteraction() {
  // Add pointer cursor when hovering over features
  map.on('pointermove', debounce(function(evt) {
    if (evt.dragging) {
      return;
    }
    
    const pixel = map.getEventPixel(evt.originalEvent);
    const hit = map.hasFeatureAtPixel(pixel);
    
    map.getTargetElement().style.cursor = hit ? 'pointer' : '';
    
    // Handle hover styling
    const feature = map.forEachFeatureAtPixel(pixel, function(feature) {
      return feature;
    });
    
    if (feature !== hoveredFeature) {
      if (hoveredFeature) {
        hoveredFeature.setStyle(null); // Reset to default style
      }
      
      hoveredFeature = feature;
      
      if (hoveredFeature) {
        hoveredFeature.setStyle(createSchoolStyle(hoveredFeature, true));
        
        // Update popup
        const popup = document.getElementById('popup');
        popup.innerHTML = `<div>${hoveredFeature.get('name')}</div>`;
        popup.style.display = 'block';
        
        const overlay = map.getOverlays().getArray()[0];
        if (overlay) {
          overlay.setPosition(hoveredFeature.getGeometry().getCoordinates());
        }
      } else {
        document.getElementById('popup').style.display = 'none';
      }
    }
  }, 50)); // Small debounce for smoother interaction
}

// Initialize event listeners - optimized version
function initEventListeners() {
  // Navigation view changes
  document.querySelectorAll('#main-nav a').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Update active link
      document.querySelectorAll('#main-nav a').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      
      // Update current view
      currentView = link.dataset.view;
      
      // Reset filters
      resetFilters();
      
      // Update map based on view
      updateMapView(currentView);
      
      // Close mobile menu
      document.getElementById('main-nav').classList.remove('active');
      document.getElementById('menu-toggle').classList.remove('active');
    });
  });
  
  // Filter checkboxes - use event delegation for better performance
  document.querySelectorAll('.filter-container').forEach(container => {
    container.addEventListener('change', (e) => {
      if (e.target.type === 'checkbox') {
        const filterType = e.target.dataset.filterType;
        const value = e.target.value;
        
        if (e.target.checked) {
          activeFilters[filterType].push(value);
        } else {
          const index = activeFilters[filterType].indexOf(value);
          if (index > -1) {
            activeFilters[filterType].splice(index, 1);
          }
        }
        
        filterSchools();
      }
    });
  });
  
  // Map zoom change - update styles to show/hide text
  map.getView().on('change:resolution', debounce(() => {
    schoolsLayer.changed();
  }, 100));
  
  // Window resize - update layout with debounce
  window.addEventListener('resize', debounce(() => {
    map.updateSize();
    
    // Close sidebar on resize to desktop
    if (window.innerWidth >= 768) {
      document.getElementById('sidebar').classList.remove('active');
      const overlay = document.querySelector('.sidebar-overlay');
      if (overlay) overlay.classList.remove('active');
      const toggle = document.getElementById('sidebar-toggle');
      if (toggle) toggle.classList.remove('active');
    }
  }, 250));
}

// Reset all filters - optimized version
function resetFilters() {
  // Uncheck all checkboxes
  document.querySelectorAll('.filter-options input[type="checkbox"]').forEach(checkbox => {
    checkbox.checked = false;
  });
  
  // Clear active filters
  activeFilters.classes = [];
  activeFilters.regions = [];
  activeFilters.districts = [];
  
  // Reset school list - use cached elements for better performance
  schoolListElements.forEach(item => {
    item.style.display = 'block';
  });
  
  // Show all schools - batch update for better performance
  const features = schoolsSource.getFeatures();
  features.forEach(feature => {
    feature.setStyle(null); // Use default style
  });
  
  // Force redraw
  schoolsLayer.changed();
  
  // Update filter status
  updateFilterStatus();
}

// Update map view based on selected category - optimized version
function updateMapView(view) {
  // Reset map view to show all of Virginia
  map.getView().animate({
    center: fromLonLat([-79.5, 37.8]),
    zoom: 7,
    duration: 500
  });
  
  // Show all schools initially - batch update for better performance
  const features = schoolsSource.getFeatures();
  features.forEach(feature => {
    feature.setStyle(null); // Use default style
  });
  
  // Force redraw
  schoolsLayer.changed();
  
  // Hide info panel
  document.getElementById('info-panel').classList.add('hidden');
  
  // Update filters based on view - use display property for better performance
  const classFilters = document.getElementById('class-filters');
  const regionFilters = document.getElementById('region-filters');
  const districtFilters = document.getElementById('district-filters');
  
  if (view === 'classes') {
    classFilters.style.display = 'block';
    regionFilters.style.display = 'none';
    districtFilters.style.display = 'none';
  } else if (view === 'regions') {
    classFilters.style.display = 'none';
    regionFilters.style.display = 'block';
    districtFilters.style.display = 'none';
  } else if (view === 'districts') {
    classFilters.style.display = 'none';
    regionFilters.style.display = 'none';
    districtFilters.style.display = 'block';
  } else {
    // All view - show all filters
    classFilters.style.display = 'block';
    regionFilters.style.display = 'block';
    districtFilters.style.display = 'block';
  }
  
  // Update filter status
  updateFilterStatus();
}

// Filter schools based on active filters - optimized version
function filterSchools() {
  // Use batch processing for better performance
  const features = schoolsSource.getFeatures();
  const invisibleFeatures = [];
  const hasClassFilters = activeFilters.classes.length > 0;
  const hasRegionFilters = activeFilters.regions.length > 0;
  const hasDistrictFilters = activeFilters.districts.length > 0;
  
  // Process map features
  features.forEach(feature => {
    let visible = true;
    
    // Check class filters
    if (hasClassFilters) {
      const schoolClass = feature.get('size') ? `Class ${feature.get('size')}` : '';
      if (!activeFilters.classes.includes(schoolClass)) {
        visible = false;
      }
    }
    
    // Check region filters
    if (visible && hasRegionFilters) {
      if (!activeFilters.regions.includes(feature.get('region'))) {
        visible = false;
      }
    }
    
    // Check district filters
    if (visible && hasDistrictFilters) {
      if (!activeFilters.districts.includes(feature.get('district'))) {
        visible = false;
      }
    }
    
    // Collect invisible features for batch update
    if (!visible) {
      invisibleFeatures.push(feature);
    } else {
      // Reset style for visible features
      feature.setStyle(null);
    }
  });
  
  // Apply empty style to invisible features
  const emptyStyle = new Style({});
  invisibleFeatures.forEach(feature => {
    feature.setStyle(emptyStyle);
  });
  
  // Force redraw
  schoolsLayer.changed();
  
  // Update school list - use cached elements for better performance
  schoolListElements.forEach(item => {
    let visible = true;
    
    // Check class filters
    if (hasClassFilters) {
      if (!activeFilters.classes.includes(item.dataset.class)) {
        visible = false;
      }
    }
    
    // Check region filters
    if (visible && hasRegionFilters) {
      if (!activeFilters.regions.includes(item.dataset.region)) {
        visible = false;
      }
    }
    
    // Check district filters
    if (visible && hasDistrictFilters) {
      if (!activeFilters.districts.includes(item.dataset.district)) {
        visible = false;
      }
    }
    
    // Set visibility
    item.style.display = visible ? 'block' : 'none';
  });
  
  // Update filter status
  updateFilterStatus();
}
