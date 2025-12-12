<script setup>
import { ref, onMounted } from 'vue'
import { profilesApi } from '@/services/api'

const profiles = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showPreviewModal = ref(false)
const previewData = ref(null)
const newProfile = ref({
  name: '',
  description: '',
  scenario_type: 'hr',
  theme: 'corporate',
  file_structure: [],
  token_config: { types: ['dns', 'word'] },
  ai_prompts: {},
  label_suggestions: []
})

const scenarioTypes = [
  { value: 'hr', label: 'HR / Payroll' },
  { value: 'it', label: 'IT / Technical' },
  { value: 'executive', label: 'Executive / Financial' },
  { value: 'marketing', label: 'Marketing / Sales' },
  { value: 'legal', label: 'Legal / Compliance' },
  { value: 'generic', label: 'Generic / Mixed' }
]

const tokenTypes = [
  { value: 'dns', label: 'DNS Token' },
  { value: 'word', label: 'Word Document' },
  { value: 'excel', label: 'Excel Spreadsheet' },
  { value: 'pdf', label: 'PDF Document' },
  { value: 'folder', label: 'Windows Folder' },
  { value: 'qr', label: 'QR Code' }
]

onMounted(async () => {
  await loadProfiles()
})

const loadProfiles = async () => {
  loading.value = true
  try {
    const response = await profilesApi.list()
    profiles.value = response.data
  } finally {
    loading.value = false
  }
}

const createProfile = async () => {
  await profilesApi.create(newProfile.value)
  showCreateModal.value = false
  resetForm()
  await loadProfiles()
}

const deleteProfile = async (id) => {
  if (confirm('Are you sure you want to delete this profile?')) {
    await profilesApi.delete(id)
    await loadProfiles()
  }
}

const previewProfile = async (id) => {
  const response = await profilesApi.preview(id)
  previewData.value = response.data
  showPreviewModal.value = true
}

const resetForm = () => {
  newProfile.value = {
    name: '',
    description: '',
    scenario_type: 'hr',
    theme: 'corporate',
    file_structure: [],
    token_config: { types: ['dns', 'word'] },
    ai_prompts: {},
    label_suggestions: []
  }
}

const toggleTokenType = (type) => {
  const types = newProfile.value.token_config.types
  const index = types.indexOf(type)
  if (index === -1) {
    types.push(type)
  } else {
    types.splice(index, 1)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">USB Profiles</h1>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
      >
        New Profile
      </button>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
      >
        <div class="p-6">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-lg font-medium text-gray-900">{{ profile.name }}</h3>
              <span class="inline-block mt-1 px-2 py-1 text-xs rounded-full bg-primary-100 text-primary-800">
                {{ profile.scenario_type }}
              </span>
            </div>
          </div>

          <p class="mt-3 text-sm text-gray-500 line-clamp-2">
            {{ profile.description || 'No description' }}
          </p>

          <div class="mt-4">
            <div class="text-xs text-gray-500 mb-2">Token Types:</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="type in profile.token_config?.types || []"
                :key="type"
                class="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
              >
                {{ type }}
              </span>
            </div>
          </div>

          <div class="mt-4 pt-4 border-t flex justify-between">
            <button
              @click="previewProfile(profile.id)"
              class="text-sm text-primary-600 hover:text-primary-700"
            >
              Preview
            </button>
            <button
              @click="deleteProfile(profile.id)"
              class="text-sm text-red-600 hover:text-red-700"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <div v-if="profiles.length === 0" class="col-span-full text-center py-12 text-gray-500">
        No profiles yet. Create your first one!
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-medium mb-4">Create Profile</h2>
        <form @submit.prevent="createProfile" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Name</label>
            <input v-model="newProfile.name" type="text" required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Scenario Type</label>
            <select v-model="newProfile.scenario_type"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
              <option v-for="type in scenarioTypes" :key="type.value" :value="type.value">
                {{ type.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea v-model="newProfile.description" rows="2"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Token Types</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="type in tokenTypes"
                :key="type.value"
                type="button"
                @click="toggleTokenType(type.value)"
                :class="[
                  'px-3 py-1 text-sm rounded-full border transition-colors',
                  newProfile.token_config.types.includes(type.value)
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400'
                ]"
              >
                {{ type.label }}
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Label Suggestions (comma-separated)</label>
            <input
              type="text"
              :value="newProfile.label_suggestions.join(', ')"
              @input="newProfile.label_suggestions = $event.target.value.split(',').map(s => s.trim()).filter(Boolean)"
              placeholder="Payroll Q4, HR Confidential, ..."
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            />
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

    <!-- Preview Modal -->
    <div v-if="showPreviewModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-lg">
        <h2 class="text-lg font-medium mb-4">Profile Preview</h2>

        <div v-if="previewData" class="space-y-4">
          <div>
            <div class="text-sm font-medium text-gray-700">File Structure:</div>
            <pre class="mt-1 p-3 bg-gray-50 rounded text-sm overflow-auto max-h-48">{{ JSON.stringify(previewData.files, null, 2) }}</pre>
          </div>

          <div>
            <div class="text-sm font-medium text-gray-700">Token Types:</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <span v-for="type in previewData.tokens" :key="type"
                class="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">
                {{ type }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-6 flex justify-end">
          <button @click="showPreviewModal = false"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
