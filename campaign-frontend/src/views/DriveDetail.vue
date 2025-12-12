<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { drivesApi } from '@/services/api'

const route = useRoute()
const router = useRouter()

const drive = ref(null)
const tokens = ref([])
const loading = ref(true)
const showDeployModal = ref(false)
const deploying = ref(false)
const gettingLocation = ref(false)

const deployment = ref({
  latitude: null,
  longitude: null,
  location_description: '',
  deployed_by: ''
})

const statusColors = {
  created: 'bg-gray-100 text-gray-800',
  prepared: 'bg-blue-100 text-blue-800',
  deployed: 'bg-green-100 text-green-800',
  triggered: 'bg-red-100 text-red-800',
  recovered: 'bg-yellow-100 text-yellow-800'
}

onMounted(async () => {
  await loadDrive()
  if (route.query.action === 'deploy') {
    showDeployModal.value = true
  }
})

const loadDrive = async () => {
  loading.value = true
  try {
    const [driveRes, tokensRes] = await Promise.all([
      drivesApi.get(route.params.id),
      drivesApi.tokens(route.params.id)
    ])
    drive.value = driveRes.data
    tokens.value = tokensRes.data
  } catch (error) {
    console.error('Failed to load drive:', error)
    router.push('/drives')
  } finally {
    loading.value = false
  }
}

const prepareDrive = async () => {
  await drivesApi.prepare(drive.value.id)
  await loadDrive()
}

const downloadDrive = async () => {
  const response = await drivesApi.download(drive.value.id)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${drive.value.unique_code}.zip`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const getCurrentLocation = () => {
  if (!navigator.geolocation) {
    alert('Geolocation is not supported by your browser')
    return
  }

  gettingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      deployment.value.latitude = position.coords.latitude
      deployment.value.longitude = position.coords.longitude
      gettingLocation.value = false
    },
    (error) => {
      console.error('Geolocation error:', error)
      alert('Failed to get current location')
      gettingLocation.value = false
    }
  )
}

const deployDrive = async () => {
  if (!deployment.value.latitude || !deployment.value.longitude) {
    alert('Please provide location coordinates')
    return
  }

  deploying.value = true
  try {
    await drivesApi.deploy(drive.value.id, deployment.value)
    showDeployModal.value = false
    await loadDrive()
  } finally {
    deploying.value = false
  }
}

const tokenTypeLabels = {
  dns: 'DNS Token',
  word: 'Word Document',
  excel: 'Excel Spreadsheet',
  pdf: 'PDF Document',
  folder: 'Windows Folder',
  qr: 'QR Code'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div>
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
    </div>

    <div v-else-if="drive">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center space-x-4">
          <router-link to="/drives" class="text-gray-500 hover:text-gray-700">
            &larr; Back to Drives
          </router-link>
        </div>
        <div class="mt-4 flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 font-mono">{{ drive.unique_code }}</h1>
            <p v-if="drive.label" class="mt-1 text-gray-500">{{ drive.label }}</p>
          </div>
          <span :class="[statusColors[drive.status], 'px-3 py-1 text-sm rounded-full']">
            {{ drive.status }}
          </span>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mb-6 flex space-x-4">
        <button
          v-if="drive.status === 'created'"
          @click="prepareDrive"
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Prepare Drive
        </button>
        <button
          v-if="drive.status === 'prepared'"
          @click="downloadDrive"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Download ZIP
        </button>
        <button
          v-if="drive.status === 'prepared'"
          @click="showDeployModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Record Deployment
        </button>
      </div>

      <!-- Drive Info -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium mb-4">Drive Information</h2>
          <dl class="space-y-3">
            <div class="flex justify-between">
              <dt class="text-gray-500">Unique Code</dt>
              <dd class="font-mono">{{ drive.unique_code }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Status</dt>
              <dd>{{ drive.status }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Created</dt>
              <dd>{{ formatDate(drive.created_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Prepared</dt>
              <dd>{{ formatDate(drive.prepared_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Deployed</dt>
              <dd>{{ formatDate(drive.deployed_at) }}</dd>
            </div>
          </dl>
        </div>

        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium mb-4">Deployment Details</h2>
          <div v-if="drive.deployment">
            <dl class="space-y-3">
              <div class="flex justify-between">
                <dt class="text-gray-500">Location</dt>
                <dd>{{ drive.deployment.location_description || 'Not specified' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">Coordinates</dt>
                <dd class="font-mono text-sm">
                  {{ drive.deployment.latitude?.toFixed(6) }}, {{ drive.deployment.longitude?.toFixed(6) }}
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">Deployed By</dt>
                <dd>{{ drive.deployment.deployed_by || '-' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">Deployed At</dt>
                <dd>{{ formatDate(drive.deployment.deployed_at) }}</dd>
              </div>
            </dl>
          </div>
          <div v-else class="text-gray-500">
            Not yet deployed
          </div>
        </div>
      </div>

      <!-- Tokens -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b">
          <h2 class="text-lg font-medium">Tokens ({{ tokens.length }})</h2>
        </div>
        <div class="divide-y">
          <div v-for="token in tokens" :key="token.id" class="px-6 py-4">
            <div class="flex justify-between items-start">
              <div>
                <div class="flex items-center space-x-2">
                  <span class="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">
                    {{ tokenTypeLabels[token.token_type] || token.token_type }}
                  </span>
                  <span class="font-medium">{{ token.filename || 'DNS Token' }}</span>
                </div>
                <div class="mt-1 text-sm text-gray-500">
                  {{ token.memo || 'No description' }}
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm text-gray-500">
                  {{ token.trigger_count || 0 }} triggers
                </div>
              </div>
            </div>
          </div>
          <div v-if="tokens.length === 0" class="px-6 py-8 text-center text-gray-500">
            No tokens created yet. Prepare the drive to generate tokens.
          </div>
        </div>
      </div>
    </div>

    <!-- Deploy Modal -->
    <div v-if="showDeployModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">Record Deployment</h2>
        <form @submit.prevent="deployDrive" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Location</label>
            <div class="mt-1 flex space-x-2">
              <input v-model.number="deployment.latitude" type="number" step="any"
                placeholder="Latitude" required
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md" />
              <input v-model.number="deployment.longitude" type="number" step="any"
                placeholder="Longitude" required
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md" />
            </div>
            <button
              type="button"
              @click="getCurrentLocation"
              :disabled="gettingLocation"
              class="mt-2 text-sm text-primary-600 hover:text-primary-700"
            >
              {{ gettingLocation ? 'Getting location...' : 'Use current location' }}
            </button>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <input v-model="deployment.location_description" type="text"
              placeholder="e.g., Building A lobby, near elevators"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Deployed By</label>
            <input v-model="deployment.deployed_by" type="text"
              placeholder="Your name"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>

          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="showDeployModal = false"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">Cancel</button>
            <button type="submit" :disabled="deploying"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50">
              {{ deploying ? 'Recording...' : 'Record Deployment' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
