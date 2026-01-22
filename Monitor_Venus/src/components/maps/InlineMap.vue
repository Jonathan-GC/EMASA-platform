<template>
  <div class="inline-map-wrapper">
    <div class="map-overlay-actions">
      <ion-button class="overlay-button" @click="setCurrentLocation">
        <ion-icon :icon="icons.locate || 'locate'" />
      </ion-button>
      <ion-button class="overlay-button" @click="showManual = !showManual">
        <ion-icon :icon="icons.create || 'create'" />
      </ion-button>
    </div> 
    
    <div ref="mapEl" class="inline-map-container"></div>

    <div v-if="showManual" class="manual-input-container">
      <div class="manual-row">
        <div class="manual-field">
          <label>Latitud</label>
          <input type="number" step="0.000001" :value="lat" @input="e => updatePosition(parseFloat(e.target.value), lng)">
        </div>
        <div class="manual-field">
          <label>Longitud</label>
          <input type="number" step="0.000001" :value="lng" @input="e => updatePosition(lat, parseFloat(e.target.value))">
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, inject, nextTick } from 'vue'
import { IonButton, IonIcon } from '@ionic/vue'
import L from 'leaflet'

// Leaflet icon fix
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const props = defineProps({
  modelValue: {
    type: Object, // { lat, lng }
    default: null
  },
  lat: {
    type: [Number, String],
    default: 0
  },
  lng: {
    type: [Number, String],
    default: 0
  },
  zoom: {
    type: Number,
    default: 13
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'update:lat', 'update:lng'])

const mapEl = ref(null)
const showManual = ref(false)
let map = null
let marker = null
const icons = inject('icons', {})

const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIconRetina,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

function initMap() {
  if (!mapEl.value || map) return

  // Prioritize lat/lng props if available, else modelValue
  let center = [0, 0]
  const hasLat = props.lat !== undefined && props.lat !== null && props.lat !== '';
  const hasLng = props.lng !== undefined && props.lng !== null && props.lng !== '';

  if (hasLat && hasLng) {
    center = [parseFloat(props.lat), parseFloat(props.lng)]
  } else if (props.modelValue && props.modelValue.lat !== undefined) {
    center = [props.modelValue.lat, props.modelValue.lng]
  }

  map = L.map(mapEl.value, { zoomControl: false }).setView(center, props.zoom)
  L.control.zoom({ position: 'bottomright' }).addTo(map)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)

  marker = L.marker(center, { 
    draggable: true,
    icon: DefaultIcon
  }).addTo(map)

  map.on('click', (e) => {
    updatePosition(e.latlng.lat, e.latlng.lng)
  })

  marker.on('dragend', (e) => {
    const p = e.target.getLatLng()
    updatePosition(p.lat, p.lng)
  })

  // Fix for map partially loading in hidden containers/tabs
  setTimeout(() => {
    if (map) map.invalidateSize()
  }, 400)
}

function updatePosition(lat, lng) {
  if (isNaN(lat) || isNaN(lng)) return
  
  const roundedLat = parseFloat(lat.toFixed(6))
  const roundedLng = parseFloat(lng.toFixed(6))
  
  if (marker) marker.setLatLng([roundedLat, roundedLng])
  if (map) map.panTo([roundedLat, roundedLng])
  
  emit('update:modelValue', { lat: roundedLat, lng: roundedLng })
  emit('update:lat', roundedLat)
  emit('update:lng', roundedLng)
  emit('change', { lat: roundedLat, lng: roundedLng })
}

function setCurrentLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
      const { latitude, longitude } = position.coords
      updatePosition(latitude, longitude)
      map.setZoom(16)
    }, (error) => {
      console.error('Error getting location:', error)
      alert('No se pudo obtener la ubicación actual. Intenta mover el marcador manualmente.')
    })
  } else {
    alert('Geolocalización no soportada por su navegador')
  }
}

// Watch for external coordinate updates
watch(() => props.lat, (newLat) => {
  if (map && marker && newLat) {
    const current = marker.getLatLng()
    if (Math.abs(current.lat - parseFloat(newLat)) > 0.0001) {
      marker.setLatLng([parseFloat(newLat), parseFloat(props.lng || 0)])
      map.panTo([parseFloat(newLat), parseFloat(props.lng || 0)])
    }
  }
})

watch(() => props.lng, (newLng) => {
  if (map && marker && newLng) {
    const current = marker.getLatLng()
    if (Math.abs(current.lng - parseFloat(newLng)) > 0.0001) {
      marker.setLatLng([parseFloat(props.lat || 0), parseFloat(newLng)])
      map.panTo([parseFloat(props.lat || 0), parseFloat(newLng)])
    }
  }
})

onMounted(() => {
  nextTick(initMap)
})

onUnmounted(() => {
  if (map) map.remove()
})
</script>

<style scoped>
.inline-map-wrapper {
  width: 100%;
  margin: 10px 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--ion-color-step-200);
  position: relative;
}

.map-overlay-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.overlay-button {
  --background: white;
  --color: #444;
  --border-radius: 4px;
  --box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  --padding-start: 8px;
  --padding-end: 8px;
  margin: 0;
  height: 36px;
  width: 36px;
  border: 1px solid #ccc;
}

.inline-map-container {
  height: 300px;
  width: 100%;
}

.manual-input-container {
  padding: 10px;
  background: white;
  border-top: 1px solid #eee;
}

.manual-row {
  display: flex;
  gap: 10px;
}

.manual-field {
  flex: 1;
}

.manual-field label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.manual-field input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}
</style>
