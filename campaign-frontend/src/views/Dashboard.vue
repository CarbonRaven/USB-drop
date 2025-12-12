<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi, alertsApi } from '@/services/api'

const stats = ref(null)
const recentAlerts = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [summaryRes, alertsRes] = await Promise.all([
      reportsApi.summary(),
      alertsApi.recent(24)
    ])
    stats.value = summaryRes.data
    recentAlerts.value = alertsRes.data.slice(0, 10)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
    </div>

    <div v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">Total Campaigns</div>
          <div class="mt-2 text-3xl font-bold text-gray-900">{{ stats?.total_campaigns || 0 }}</div>
          <div class="mt-1 text-sm text-green-600">{{ stats?.active_campaigns || 0 }} active</div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">Total Drives</div>
          <div class="mt-2 text-3xl font-bold text-gray-900">{{ stats?.total_drives || 0 }}</div>
          <div class="mt-1 text-sm text-gray-500">
            {{ stats?.drives_by_status?.deployed || 0 }} deployed
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">Total Triggers</div>
          <div class="mt-2 text-3xl font-bold text-red-600">{{ stats?.total_triggers || 0 }}</div>
          <div class="mt-1 text-sm text-gray-500">
            {{ stats?.drives_by_status?.triggered || 0 }} drives triggered
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-500">Ready to Deploy</div>
          <div class="mt-2 text-3xl font-bold text-primary-600">
            {{ stats?.drives_by_status?.prepared || 0 }}
          </div>
          <div class="mt-1 text-sm text-gray-500">prepared drives</div>
        </div>
      </div>

      <!-- Recent Alerts -->
      <div class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-medium text-gray-900">Recent Alerts (24h)</h2>
        </div>
        <div class="divide-y divide-gray-200">
          <div
            v-for="alert in recentAlerts"
            :key="alert.id"
            class="px-6 py-4 hover:bg-gray-50"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-medium text-gray-900">{{ alert.drive_code }}</span>
                <span class="mx-2 text-gray-400">|</span>
                <span class="text-sm text-gray-600">{{ alert.token_type }}</span>
                <span v-if="alert.token_filename" class="text-sm text-gray-500">
                  - {{ alert.token_filename }}
                </span>
              </div>
              <div class="text-right">
                <div class="text-sm text-gray-600">{{ alert.source_ip || 'Unknown IP' }}</div>
                <div class="text-xs text-gray-500">
                  {{ alert.geo_city }}{{ alert.geo_city && alert.geo_country ? ', ' : '' }}{{ alert.geo_country }}
                </div>
              </div>
            </div>
          </div>

          <div v-if="recentAlerts.length === 0" class="px-6 py-8 text-center text-gray-500">
            No alerts in the last 24 hours
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
