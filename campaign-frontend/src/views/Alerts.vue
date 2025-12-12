<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { alertsApi, campaignsApi } from '@/services/api'

const alerts = ref([])
const campaigns = ref([])
const stats = ref(null)
const loading = ref(true)
const autoRefresh = ref(true)
let refreshInterval = null

const filters = ref({
  campaign_id: '',
  hours: 24
})

const hourOptions = [
  { value: 1, label: 'Last hour' },
  { value: 6, label: 'Last 6 hours' },
  { value: 24, label: 'Last 24 hours' },
  { value: 72, label: 'Last 3 days' },
  { value: 168, label: 'Last 7 days' },
  { value: 720, label: 'Last 30 days' }
]

onMounted(async () => {
  await Promise.all([loadCampaigns(), loadAlerts()])
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

const startAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshInterval = setInterval(loadAlerts, 30000) // 30 seconds
  }
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const [alertsRes, statsRes] = await Promise.all([
      alertsApi.recent(filters.value.hours),
      alertsApi.stats(filters.value.campaign_id || undefined)
    ])

    let data = alertsRes.data
    if (filters.value.campaign_id) {
      data = data.filter(a => a.campaign_id === filters.value.campaign_id)
    }
    alerts.value = data
    stats.value = statsRes.data
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  loadAlerts()
}

const formatTime = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return date.toLocaleString()
}

const getTokenTypeColor = (type) => {
  const colors = {
    dns: 'bg-purple-100 text-purple-800',
    word: 'bg-blue-100 text-blue-800',
    excel: 'bg-green-100 text-green-800',
    pdf: 'bg-red-100 text-red-800',
    folder: 'bg-yellow-100 text-yellow-800',
    qr: 'bg-gray-100 text-gray-800'
  }
  return colors[type] || 'bg-gray-100 text-gray-800'
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Alerts</h1>
      <div class="flex items-center space-x-4">
        <button
          @click="toggleAutoRefresh"
          :class="[
            'flex items-center px-3 py-1 text-sm rounded-full',
            autoRefresh ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          ]"
        >
          <span :class="['w-2 h-2 rounded-full mr-2', autoRefresh ? 'bg-green-500 animate-pulse' : 'bg-gray-400']"></span>
          {{ autoRefresh ? 'Live' : 'Paused' }}
        </button>
        <button @click="loadAlerts" class="text-primary-600 hover:text-primary-700">
          Refresh
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">Total Triggers</div>
        <div class="text-2xl font-bold text-red-600">{{ stats?.total || 0 }}</div>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">Today</div>
        <div class="text-2xl font-bold">{{ stats?.today || 0 }}</div>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">This Week</div>
        <div class="text-2xl font-bold">{{ stats?.this_week || 0 }}</div>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">Unique IPs</div>
        <div class="text-2xl font-bold">{{ stats?.unique_ips || 0 }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
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
          <label class="block text-sm font-medium text-gray-700 mb-1">Time Range</label>
          <select v-model="filters.hours"
            class="px-3 py-2 border border-gray-300 rounded-md">
            <option v-for="opt in hourOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <button @click="applyFilters"
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
          Apply
        </button>
      </div>
    </div>

    <!-- Alerts List -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div class="divide-y divide-gray-200">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          class="p-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <router-link :to="`/drives/${alert.drive_id}`"
                  class="font-mono font-medium text-primary-600 hover:underline">
                  {{ alert.drive_code }}
                </router-link>
                <span :class="[getTokenTypeColor(alert.token_type), 'px-2 py-0.5 text-xs rounded-full']">
                  {{ alert.token_type }}
                </span>
                <span v-if="alert.token_filename" class="text-sm text-gray-500">
                  {{ alert.token_filename }}
                </span>
              </div>

              <div class="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-600">
                <div class="flex items-center">
                  <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                  {{ alert.source_ip || 'Unknown IP' }}
                </div>
                <div v-if="alert.geo_city || alert.geo_country" class="flex items-center">
                  <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {{ alert.geo_city }}{{ alert.geo_city && alert.geo_country ? ', ' : '' }}{{ alert.geo_country }}
                </div>
                <div v-if="alert.user_agent" class="flex items-center max-w-xs truncate" :title="alert.user_agent">
                  <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span class="truncate">{{ alert.user_agent }}</span>
                </div>
              </div>
            </div>

            <div class="text-right ml-4">
              <div class="text-sm font-medium text-gray-900">{{ formatTime(alert.triggered_at) }}</div>
              <div class="text-xs text-gray-500">{{ new Date(alert.triggered_at).toLocaleString() }}</div>
            </div>
          </div>
        </div>

        <div v-if="alerts.length === 0" class="p-8 text-center text-gray-500">
          <svg class="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <p>No alerts in the selected time range</p>
        </div>
      </div>
    </div>
  </div>
</template>
