<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { drivesApi, campaignsApi, profilesApi } from '@/services/api'

const router = useRouter()
const drives = ref([])
const campaigns = ref([])
const profiles = ref([])
const loading = ref(true)
const showCreateModal = ref(false)

const filters = ref({
  campaign_id: '',
  status: ''
})

const newDrive = ref({
  campaign_id: '',
  profile_id: '',
  label: ''
})

const statusColors = {
  created: 'bg-gray-100 text-gray-800',
  prepared: 'bg-blue-100 text-blue-800',
  deployed: 'bg-green-100 text-green-800',
  triggered: 'bg-red-100 text-red-800',
  recovered: 'bg-yellow-100 text-yellow-800'
}

onMounted(async () => {
  await Promise.all([
    loadDrives(),
    loadCampaigns(),
    loadProfiles()
  ])
})

const loadDrives = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.campaign_id) params.campaign_id = filters.value.campaign_id
    if (filters.value.status) params.status = filters.value.status

    const response = await drivesApi.list(params)
    drives.value = response.data
  } finally {
    loading.value = false
  }
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
}

const loadProfiles = async () => {
  const response = await profilesApi.list()
  profiles.value = response.data
}

const createDrive = async () => {
  await drivesApi.create(newDrive.value)
  showCreateModal.value = false
  resetForm()
  await loadDrives()
}

const prepareDrive = async (id) => {
  await drivesApi.prepare(id)
  await loadDrives()
}

const downloadDrive = async (id) => {
  const response = await drivesApi.download(id)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `drive-${id}.zip`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const resetForm = () => {
  newDrive.value = {
    campaign_id: '',
    profile_id: '',
    label: ''
  }
}

const applyFilters = () => {
  loadDrives()
}

const clearFilters = () => {
  filters.value = { campaign_id: '', status: '' }
  loadDrives()
}

const getCampaignName = (id) => {
  const campaign = campaigns.value.find(c => c.id === id)
  return campaign?.name || '-'
}

const getProfileName = (id) => {
  const profile = profiles.value.find(p => p.id === id)
  return profile?.name || '-'
}

const filteredDrives = computed(() => {
  return drives.value
})
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">USB Drives</h1>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      >
        New Drive
      </button>
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
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select v-model="filters.status"
            class="px-3 py-2 border border-gray-300 rounded-md">
            <option value="">All Statuses</option>
            <option value="created">Created</option>
            <option value="prepared">Prepared</option>
            <option value="deployed">Deployed</option>
            <option value="triggered">Triggered</option>
            <option value="recovered">Recovered</option>
          </select>
        </div>

        <button @click="applyFilters"
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
          Filter
        </button>
        <button @click="clearFilters"
          class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
          Clear
        </button>
      </div>
    </div>

    <!-- Drives Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Campaign</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Profile</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tokens</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="drive in filteredDrives" :key="drive.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <router-link :to="`/drives/${drive.id}`" class="text-primary-600 hover:underline font-mono">
                {{ drive.unique_code }}
              </router-link>
            </td>
            <td class="px-6 py-4 text-gray-700">{{ drive.label || '-' }}</td>
            <td class="px-6 py-4 text-gray-500">{{ getCampaignName(drive.campaign_id) }}</td>
            <td class="px-6 py-4 text-gray-500">{{ getProfileName(drive.profile_id) }}</td>
            <td class="px-6 py-4">
              <span :class="[statusColors[drive.status], 'px-2 py-1 text-xs rounded-full']">
                {{ drive.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-gray-500">{{ drive.token_count || 0 }}</td>
            <td class="px-6 py-4">
              <div class="flex space-x-3">
                <button
                  v-if="drive.status === 'created'"
                  @click="prepareDrive(drive.id)"
                  class="text-sm text-primary-600 hover:text-primary-700"
                >
                  Prepare
                </button>
                <button
                  v-if="drive.status === 'prepared'"
                  @click="downloadDrive(drive.id)"
                  class="text-sm text-green-600 hover:text-green-700"
                >
                  Download
                </button>
                <router-link
                  v-if="drive.status === 'prepared'"
                  :to="`/drives/${drive.id}?action=deploy`"
                  class="text-sm text-blue-600 hover:text-blue-700"
                >
                  Deploy
                </router-link>
                <router-link :to="`/drives/${drive.id}`"
                  class="text-sm text-gray-600 hover:text-gray-700">
                  View
                </router-link>
              </div>
            </td>
          </tr>
          <tr v-if="drives.length === 0">
            <td colspan="7" class="px-6 py-8 text-center text-gray-500">
              No drives found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">Create Drive</h2>
        <form @submit.prevent="createDrive" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Campaign</label>
            <select v-model="newDrive.campaign_id" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="" disabled>Select a campaign</option>
              <option v-for="c in campaigns" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Profile</label>
            <select v-model="newDrive.profile_id" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="" disabled>Select a profile</option>
              <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Label (optional)</label>
            <input v-model="newDrive.label" type="text"
              placeholder="e.g., HR Payroll Q4"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>

          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="showCreateModal = false; resetForm()"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">Cancel</button>
            <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
