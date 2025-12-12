<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { alertsApi, campaignsApi } from '@/services/api'

const route = useRoute()
const mapContainer = ref(null)
const map = ref(null)
const campaigns = ref([])
const mapData = ref([])
const loading = ref(true)

const filters = ref({
  campaign_id: route.query.campaign_id || '',
  type: 'both' // 'deployments', 'triggers', 'both'
})

// Fix for default marker icons in Leaflet with bundlers
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const deploymentIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const triggerIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

L.Marker.prototype.options.icon = defaultIcon

onMounted(async () => {
  await loadCampaigns()
  initMap()
  await loadMapData()
})

watch(filters, async () => {
  await loadMapData()
}, { deep: true })

const initMap = () => {
  map.value = L.map(mapContainer.value).setView([39.8283, -98.5795], 4)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map.value)
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
}

const loadMapData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.campaign_id) {
      params.campaign_id = filters.value.campaign_id
    }

    const response = await alertsApi.map(params)
    mapData.value = response.data
    updateMarkers()
  } finally {
    loading.value = false
  }
}

const updateMarkers = () => {
  // Clear existing markers
  map.value.eachLayer((layer) => {
    if (layer instanceof L.Marker) {
      map.value.removeLayer(layer)
    }
  })

  const bounds = []

  // Add deployment markers
  if (filters.value.type === 'deployments' || filters.value.type === 'both') {
    mapData.value.deployments?.forEach((d) => {
      if (d.latitude && d.longitude) {
        const marker = L.marker([d.latitude, d.longitude], { icon: deploymentIcon })
          .addTo(map.value)
          .bindPopup(`
            <div class="text-sm">
              <div class="font-bold">Deployed: ${d.drive_code}</div>
              <div>${d.location_description || 'No description'}</div>
              <div class="text-gray-500">${new Date(d.deployed_at).toLocaleString()}</div>
            </div>
          `)
        bounds.push([d.latitude, d.longitude])
      }
    })
  }

  // Add trigger markers
  if (filters.value.type === 'triggers' || filters.value.type === 'both') {
    mapData.value.triggers?.forEach((t) => {
      if (t.geo_latitude && t.geo_longitude) {
        const marker = L.marker([t.geo_latitude, t.geo_longitude], { icon: triggerIcon })
          .addTo(map.value)
          .bindPopup(`
            <div class="text-sm">
              <div class="font-bold text-red-600">Triggered: ${t.drive_code}</div>
              <div>${t.token_type} - ${t.filename || 'DNS'}</div>
              <div>${t.geo_city || ''}${t.geo_city && t.geo_country ? ', ' : ''}${t.geo_country || ''}</div>
              <div class="text-gray-500">IP: ${t.source_ip || 'Unknown'}</div>
              <div class="text-gray-500">${new Date(t.triggered_at).toLocaleString()}</div>
            </div>
          `)
        bounds.push([t.geo_latitude, t.geo_longitude])
      }
    })
  }

  // Fit map to markers
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [20, 20] })
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold text-gray-900">Map View</h1>
    </div>

    <!-- Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-4">
      <div class="flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Campaign</label>
          <select v-model="filters.campaign_id"
            class="px-3 py-2 border border-gray-300 rounded-md">
            <option value="">All Campaigns</option>
            <option v-for="c in campaigns" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Show</label>
          <select v-model="filters.type"
            class="px-3 py-2 border border-gray-300 rounded-md">
            <option value="both">Deployments & Triggers</option>
            <option value="deployments">Deployments Only</option>
            <option value="triggers">Triggers Only</option>
          </select>
        </div>

        <div class="flex items-center space-x-4 text-sm">
          <div class="flex items-center">
            <span class="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
            <span>Deployment</span>
          </div>
          <div class="flex items-center">
            <span class="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
            <span>Trigger</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Map -->
    <div class="flex-1 bg-white shadow rounded-lg overflow-hidden relative">
      <div v-if="loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
      <div ref="mapContainer" class="h-full min-h-[500px]"></div>
    </div>

    <!-- Stats -->
    <div class="mt-4 grid grid-cols-2 gap-4">
      <div class="bg-white shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">Deployments Shown</div>
        <div class="text-xl font-bold text-blue-600">
          {{ mapData.deployments?.length || 0 }}
        </div>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">Triggers Shown</div>
        <div class="text-xl font-bold text-red-600">
          {{ mapData.triggers?.length || 0 }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaflet-container {
  font-family: inherit;
}
</style>
