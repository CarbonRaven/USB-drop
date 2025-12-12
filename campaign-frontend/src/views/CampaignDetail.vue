<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { campaignsApi, drivesApi, reportsApi } from '@/services/api'

const route = useRoute()
const router = useRouter()

const campaign = ref(null)
const drives = ref([])
const stats = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const editForm = ref({})

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  completed: 'bg-blue-100 text-blue-800',
  archived: 'bg-yellow-100 text-yellow-800'
}

const driveStatusColors = {
  created: 'bg-gray-100 text-gray-800',
  prepared: 'bg-blue-100 text-blue-800',
  deployed: 'bg-green-100 text-green-800',
  triggered: 'bg-red-100 text-red-800',
  recovered: 'bg-yellow-100 text-yellow-800'
}

onMounted(async () => {
  await loadCampaign()
})

const loadCampaign = async () => {
  loading.value = true
  try {
    const [campaignRes, statsRes] = await Promise.all([
      campaignsApi.get(route.params.id),
      campaignsApi.stats(route.params.id)
    ])
    campaign.value = campaignRes.data
    stats.value = statsRes.data
    drives.value = campaign.value.drives || []

    editForm.value = {
      name: campaign.value.name,
      client_name: campaign.value.client_name,
      description: campaign.value.description,
      status: campaign.value.status
    }
  } catch (error) {
    console.error('Failed to load campaign:', error)
    router.push('/campaigns')
  } finally {
    loading.value = false
  }
}

const updateCampaign = async () => {
  await campaignsApi.update(campaign.value.id, editForm.value)
  showEditModal.value = false
  await loadCampaign()
}

const deleteCampaign = async () => {
  if (confirm('Are you sure you want to delete this campaign? This cannot be undone.')) {
    await campaignsApi.delete(campaign.value.id)
    router.push('/campaigns')
  }
}

const exportCsv = async () => {
  const response = await reportsApi.exportCsv(campaign.value.id)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `campaign-${campaign.value.id}-report.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div>
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
    </div>

    <div v-else-if="campaign">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center space-x-4">
          <router-link to="/campaigns" class="text-gray-500 hover:text-gray-700">
            &larr; Back to Campaigns
          </router-link>
        </div>
        <div class="mt-4 flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ campaign.name }}</h1>
            <p v-if="campaign.client_name" class="mt-1 text-gray-500">
              Client: {{ campaign.client_name }}
            </p>
          </div>
          <div class="flex items-center space-x-3">
            <span :class="[statusColors[campaign.status], 'px-3 py-1 text-sm rounded-full']">
              {{ campaign.status }}
            </span>
            <button @click="showEditModal = true"
              class="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border rounded-md">
              Edit
            </button>
          </div>
        </div>
        <p v-if="campaign.description" class="mt-3 text-gray-600">
          {{ campaign.description }}
        </p>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Total Drives</div>
          <div class="text-2xl font-bold">{{ stats?.total_drives || 0 }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Deployed</div>
          <div class="text-2xl font-bold text-green-600">{{ stats?.deployed || 0 }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Triggered</div>
          <div class="text-2xl font-bold text-red-600">{{ stats?.triggered || 0 }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Success Rate</div>
          <div class="text-2xl font-bold">
            {{ stats?.deployed ? Math.round((stats.triggered / stats.deployed) * 100) : 0 }}%
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mb-6 flex space-x-4">
        <router-link :to="`/drives?campaign_id=${campaign.id}`"
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
          View All Drives
        </router-link>
        <router-link :to="`/map?campaign_id=${campaign.id}`"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          View on Map
        </router-link>
        <button @click="exportCsv"
          class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          Export CSV
        </button>
      </div>

      <!-- Drives Table -->
      <div class="bg-white shadow rounded-lg overflow-hidden">
        <div class="px-6 py-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-medium">Drives</h2>
          <router-link :to="`/drives?action=new&campaign_id=${campaign.id}`"
            class="text-sm text-primary-600 hover:text-primary-700">
            + Add Drive
          </router-link>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tokens</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Triggers</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="drive in drives" :key="drive.id" class="hover:bg-gray-50">
              <td class="px-6 py-4">
                <router-link :to="`/drives/${drive.id}`" class="text-primary-600 hover:underline font-mono">
                  {{ drive.unique_code }}
                </router-link>
              </td>
              <td class="px-6 py-4 text-gray-500">{{ drive.label || '-' }}</td>
              <td class="px-6 py-4">
                <span :class="[driveStatusColors[drive.status], 'px-2 py-1 text-xs rounded-full']">
                  {{ drive.status }}
                </span>
              </td>
              <td class="px-6 py-4 text-gray-500">{{ drive.token_count || 0 }}</td>
              <td class="px-6 py-4 text-gray-500">{{ drive.trigger_count || 0 }}</td>
            </tr>
            <tr v-if="drives.length === 0">
              <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                No drives in this campaign yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">Edit Campaign</h2>
        <form @submit.prevent="updateCampaign" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Name</label>
            <input v-model="editForm.name" type="text" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Client Name</label>
            <input v-model="editForm.client_name" type="text"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Status</label>
            <select v-model="editForm.status"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea v-model="editForm.description" rows="3"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"></textarea>
          </div>
          <div class="flex justify-between pt-4">
            <button type="button" @click="deleteCampaign"
              class="px-4 py-2 text-red-600 hover:bg-red-50 rounded-md">Delete</button>
            <div class="space-x-3">
              <button type="button" @click="showEditModal = false"
                class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">Cancel</button>
              <button type="submit"
                class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
                Save
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
