<script setup>
import { ref, onMounted } from 'vue'
import { campaignsApi } from '@/services/api'

const campaigns = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const newCampaign = ref({ name: '', client_name: '', description: '' })

onMounted(async () => {
  await loadCampaigns()
})

const loadCampaigns = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.list()
    campaigns.value = response.data
  } finally {
    loading.value = false
  }
}

const createCampaign = async () => {
  await campaignsApi.create(newCampaign.value)
  showCreateModal.value = false
  newCampaign.value = { name: '', client_name: '', description: '' }
  await loadCampaigns()
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  completed: 'bg-blue-100 text-blue-800',
  archived: 'bg-yellow-100 text-yellow-800',
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Campaigns</h1>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      >
        New Campaign
      </button>
    </div>

    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Drives</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Triggers</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="campaign in campaigns" :key="campaign.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <router-link :to="`/campaigns/${campaign.id}`" class="text-primary-600 hover:underline">
                {{ campaign.name }}
              </router-link>
            </td>
            <td class="px-6 py-4 text-gray-500">{{ campaign.client_name || '-' }}</td>
            <td class="px-6 py-4">
              <span :class="[statusColors[campaign.status], 'px-2 py-1 text-xs rounded-full']">
                {{ campaign.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-gray-500">{{ campaign.drive_count }}</td>
            <td class="px-6 py-4 text-gray-500">{{ campaign.triggered_count }}</td>
            <td class="px-6 py-4">
              <router-link :to="`/campaigns/${campaign.id}`" class="text-primary-600 hover:underline text-sm">
                View
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">Create Campaign</h2>
        <form @submit.prevent="createCampaign" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Name</label>
            <input v-model="newCampaign.name" type="text" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Client Name</label>
            <input v-model="newCampaign.client_name" type="text"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea v-model="newCampaign.description" rows="3"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"></textarea>
          </div>
          <div class="flex justify-end space-x-3">
            <button type="button" @click="showCreateModal = false"
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
