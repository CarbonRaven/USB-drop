<script setup>
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { reportsApi, campaignsApi } from '@/services/api'

Chart.register(...registerables)

const campaigns = ref([])
const selectedCampaign = ref('')
const report = ref(null)
const loading = ref(true)

const statusChart = ref(null)
const triggerChart = ref(null)
let statusChartInstance = null
let triggerChartInstance = null

onMounted(async () => {
  await loadCampaigns()
})

const loadCampaigns = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.list()
    campaigns.value = response.data
    if (campaigns.value.length > 0) {
      selectedCampaign.value = campaigns.value[0].id
      await loadReport()
    }
  } finally {
    loading.value = false
  }
}

const loadReport = async () => {
  if (!selectedCampaign.value) return

  loading.value = true
  try {
    const response = await reportsApi.campaign(selectedCampaign.value)
    report.value = response.data
    updateCharts()
  } finally {
    loading.value = false
  }
}

const updateCharts = () => {
  // Status distribution chart
  if (statusChartInstance) statusChartInstance.destroy()
  if (statusChart.value && report.value?.status_distribution) {
    statusChartInstance = new Chart(statusChart.value, {
      type: 'doughnut',
      data: {
        labels: Object.keys(report.value.status_distribution),
        datasets: [{
          data: Object.values(report.value.status_distribution),
          backgroundColor: [
            '#9CA3AF', // created - gray
            '#3B82F6', // prepared - blue
            '#10B981', // deployed - green
            '#EF4444', // triggered - red
            '#F59E0B'  // recovered - yellow
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    })
  }

  // Triggers over time chart
  if (triggerChartInstance) triggerChartInstance.destroy()
  if (triggerChart.value && report.value?.triggers_by_day) {
    const days = Object.keys(report.value.triggers_by_day).sort()
    triggerChartInstance = new Chart(triggerChart.value, {
      type: 'line',
      data: {
        labels: days.map(d => new Date(d).toLocaleDateString()),
        datasets: [{
          label: 'Triggers',
          data: days.map(d => report.value.triggers_by_day[d]),
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        }
      }
    })
  }
}

const exportCsv = async () => {
  const response = await reportsApi.exportCsv(selectedCampaign.value)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `campaign-${selectedCampaign.value}-report.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const getCampaignName = (id) => {
  return campaigns.value.find(c => c.id === id)?.name || ''
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Reports</h1>
      <button
        v-if="selectedCampaign"
        @click="exportCsv"
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      >
        Export CSV
      </button>
    </div>

    <!-- Campaign Selector -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="flex items-end gap-4">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-1">Select Campaign</label>
          <select v-model="selectedCampaign" @change="loadReport"
            class="w-full px-3 py-2 border border-gray-300 rounded-md">
            <option v-for="c in campaigns" :key="c.id" :value="c.id">
              {{ c.name }} ({{ c.status }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
    </div>

    <div v-else-if="report">
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Total Drives</div>
          <div class="text-2xl font-bold">{{ report.total_drives }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Deployed</div>
          <div class="text-2xl font-bold text-green-600">{{ report.deployed }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Triggered</div>
          <div class="text-2xl font-bold text-red-600">{{ report.triggered }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Total Triggers</div>
          <div class="text-2xl font-bold">{{ report.total_triggers }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Success Rate</div>
          <div class="text-2xl font-bold">
            {{ report.deployed ? Math.round((report.triggered / report.deployed) * 100) : 0 }}%
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium mb-4">Drive Status Distribution</h2>
          <div class="aspect-square max-w-xs mx-auto">
            <canvas ref="statusChart"></canvas>
          </div>
        </div>

        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium mb-4">Triggers Over Time</h2>
          <canvas ref="triggerChart"></canvas>
        </div>
      </div>

      <!-- Token Type Breakdown -->
      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <h2 class="text-lg font-medium mb-4">Triggers by Token Type</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="(count, type) in report.triggers_by_type" :key="type"
            class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-primary-600">{{ count }}</div>
            <div class="text-sm text-gray-500 capitalize">{{ type }}</div>
          </div>
        </div>
        <div v-if="Object.keys(report.triggers_by_type || {}).length === 0"
          class="text-center text-gray-500 py-4">
          No triggers recorded yet
        </div>
      </div>

      <!-- Top Triggered Drives -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b">
          <h2 class="text-lg font-medium">Top Triggered Drives</h2>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Triggers</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">First Trigger</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="drive in report.top_drives" :key="drive.id" class="hover:bg-gray-50">
              <td class="px-6 py-4">
                <router-link :to="`/drives/${drive.id}`" class="text-primary-600 hover:underline font-mono">
                  {{ drive.unique_code }}
                </router-link>
              </td>
              <td class="px-6 py-4 text-gray-500">{{ drive.label || '-' }}</td>
              <td class="px-6 py-4 text-gray-500">{{ drive.location || '-' }}</td>
              <td class="px-6 py-4 font-medium text-red-600">{{ drive.trigger_count }}</td>
              <td class="px-6 py-4 text-gray-500">
                {{ drive.first_trigger ? new Date(drive.first_trigger).toLocaleString() : '-' }}
              </td>
            </tr>
            <tr v-if="!report.top_drives?.length">
              <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                No triggered drives yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-500">
      <p>Select a campaign to view its report</p>
    </div>
  </div>
</template>
