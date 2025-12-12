<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const navItems = [
  { name: 'Dashboard', path: '/', icon: '📊' },
  { name: 'Campaigns', path: '/campaigns', icon: '📁' },
  { name: 'Profiles', path: '/profiles', icon: '📋' },
  { name: 'Drives', path: '/drives', icon: '💾' },
  { name: 'Map', path: '/map', icon: '🗺️' },
  { name: 'Alerts', path: '/alerts', icon: '🚨' },
  { name: 'Reports', path: '/reports', icon: '📈' },
]

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav v-if="isAuthenticated" class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <!-- Logo -->
            <div class="flex-shrink-0 flex items-center">
              <span class="text-xl font-bold text-primary-600">USB Drop</span>
            </div>
            <!-- Nav links -->
            <div class="hidden sm:ml-6 sm:flex sm:space-x-4">
              <router-link
                v-for="item in navItems"
                :key="item.path"
                :to="item.path"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50 rounded-md"
                active-class="text-primary-600 bg-primary-50"
              >
                <span class="mr-1">{{ item.icon }}</span>
                {{ item.name }}
              </router-link>
            </div>
          </div>
          <!-- User menu -->
          <div class="flex items-center">
            <span class="text-sm text-gray-500 mr-4">{{ authStore.user?.username }}</span>
            <button
              @click="logout"
              class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-md"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <router-view />
    </main>
  </div>
</template>
