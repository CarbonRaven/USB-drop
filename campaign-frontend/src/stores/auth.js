import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('accessToken'))
  const refreshToken = ref(localStorage.getItem('refreshToken'))

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    accessToken.value = response.data.access_token
    refreshToken.value = response.data.refresh_token

    localStorage.setItem('accessToken', accessToken.value)
    localStorage.setItem('refreshToken', refreshToken.value)

    await fetchUser()
  }

  async function fetchUser() {
    if (!accessToken.value) return

    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  async function refresh() {
    if (!refreshToken.value) return

    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })

      accessToken.value = response.data.access_token
      refreshToken.value = response.data.refresh_token

      localStorage.setItem('accessToken', accessToken.value)
      localStorage.setItem('refreshToken', refreshToken.value)
    } catch (error) {
      logout()
    }
  }

  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  }

  // Initialize user on store creation
  if (accessToken.value) {
    fetchUser()
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    login,
    logout,
    refresh,
    fetchUser
  }
})
